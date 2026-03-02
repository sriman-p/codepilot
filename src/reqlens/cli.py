"""ReqLens CLI entrypoint."""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path
from statistics import mean
from typing import Optional

import typer

from reqlens.compat import model_dump, model_validate
from reqlens.config import load_config
from reqlens.exceptions import ReqLensError, StageExecutionError
from reqlens.models.schemas import (
    EvaluationMetrics,
    ExperimentRunResult,
    GapEntry,
    GenerationArtifacts,
    TraceabilityEntry,
)
from reqlens.pipeline.code_analyzer import analyze_code
from reqlens.pipeline.critique import critique_tests
from reqlens.pipeline.mapper import map_requirements_to_code
from reqlens.pipeline.requirements_parser import parse_requirements
from reqlens.pipeline.test_generator import generate_tests
from reqlens.providers import create_provider

_STRATEGIES = {"zero_shot", "few_shot", "chain_of_thought"}
_CONTEXTS = {"code_only", "requirements_only", "requirements_plus_code"}
_REQ_ID_PATTERN = re.compile(r"\b([A-Za-z]{2,}-[A-Za-z0-9_.-]+)\b")

app = typer.Typer(help="ReqLens: requirement-aware test generation and evaluation")


@app.command()
def generate(
    requirements: Path = typer.Option(..., exists=True, help="Path to requirements (.md/.txt/.csv)"),
    code_dir: Path = typer.Option(..., exists=True, file_okay=False, help="Python code directory"),
    output_dir: Path = typer.Option(Path("out"), help="Artifact output directory"),
    config: Path = typer.Option(Path("configs/default.yaml"), help="YAML config path"),
    provider: Optional[str] = typer.Option(None, help="Provider selector, e.g. mock or openai:gpt-4o-mini"),
    strategy: str = typer.Option("zero_shot", help="zero_shot|few_shot|chain_of_thought"),
    context: str = typer.Option("requirements_plus_code", help="code_only|requirements_only|requirements_plus_code"),
) -> None:
    """Run the full 5-stage generation pipeline."""
    _validate_strategy_and_context(strategy, context)

    started = time.perf_counter()
    cfg = load_config(config)
    llm = create_provider(cfg, selector=provider)

    reqs = parse_requirements(requirements)
    code = analyze_code(code_dir)
    maps = map_requirements_to_code(reqs, code, confidence_threshold=cfg.pipeline.mapping_confidence_threshold)
    tests = generate_tests(reqs, maps, code, llm, strategy=strategy, context_mode=context)
    revised_tests, critiques = critique_tests(tests, threshold=cfg.pipeline.critique_threshold, auto_revise=True)

    traceability = _build_traceability(revised_tests)
    gaps = _build_gaps(reqs, traceability)

    output_dir.mkdir(parents=True, exist_ok=True)
    tests_path = output_dir / cfg.io.tests_filename
    trace_path = output_dir / cfg.io.traceability_filename
    gap_path = output_dir / cfg.io.gap_report_filename
    full_path = output_dir / "generation_artifacts.json"

    _write_tests_file(tests_path, revised_tests)
    _write_traceability(trace_path, traceability)
    gap_path.write_text(json.dumps([model_dump(g) for g in gaps], indent=2), encoding="utf-8")

    artifacts = GenerationArtifacts(
        requirements=reqs,
        code_elements=code,
        mappings=maps,
        tests=revised_tests,
        critiques=critiques,
        traceability=traceability,
        gaps=gaps,
        metadata={
            "provider": f"{llm.name}:{llm.model}",
            "strategy": strategy,
            "context": context,
            "duration_seconds": round(time.perf_counter() - started, 4),
            "estimated_cost": llm.estimated_cost,
        },
    )
    full_path.write_text(json.dumps(model_dump(artifacts), indent=2), encoding="utf-8")

    typer.echo(f"Generated tests: {tests_path}")
    typer.echo(f"Traceability: {trace_path}")
    typer.echo(f"Gap report: {gap_path}")


@app.command()
def evaluate(
    artifacts: Path = typer.Option(..., exists=True, help="Path to generation_artifacts.json"),
    output: Path = typer.Option(Path("out/evaluation.json"), help="Output metrics JSON"),
    ground_truth_tests: Optional[Path] = typer.Option(None, exists=True, help="Optional human-written tests"),
) -> None:
    """Evaluate generated artifacts and optionally compare to human tests."""

    data = json.loads(artifacts.read_text(encoding="utf-8"))
    requirements = data.get("requirements", [])
    tests = data.get("tests", [])
    traceability = data.get("traceability", [])
    critiques = data.get("critiques", [])

    req_ids = {r.get("id") for r in requirements if r.get("id")}
    covered = {t_req for t in tests for t_req in t.get("requirement_ids", [])}

    correctness_hits = 0
    for test in tests:
        body = test.get("body", "")
        if "def test_" in body and "assert " in body and "pass" not in body:
            correctness_hits += 1
    correctness_rate = (correctness_hits / len(tests)) if tests else 0.0

    trace_links = sum(1 for t in traceability if t.get("requirement_id") and t.get("test_id"))
    traceability_accuracy = (trace_links / len(traceability)) if traceability else 0.0

    if ground_truth_tests is not None:
        generated_ids = set(covered)
        gt_ids = _extract_requirement_ids(ground_truth_tests.read_text(encoding="utf-8"))
        if gt_ids:
            traceability_accuracy = len(generated_ids.intersection(gt_ids)) / len(gt_ids)

    scores = [c.get("score", 0.0) for c in critiques]
    critique_quality_stats = {
        "mean": round(mean(scores), 4) if scores else 0.0,
        "min": round(min(scores), 4) if scores else 0.0,
        "max": round(max(scores), 4) if scores else 0.0,
    }

    metrics = EvaluationMetrics(
        correctness_rate=round(correctness_rate, 4),
        requirement_coverage=round((len(covered.intersection(req_ids)) / len(req_ids)) if req_ids else 0.0, 4),
        traceability_accuracy=round(traceability_accuracy, 4),
        critique_quality_stats=critique_quality_stats,
        cost=data.get("metadata", {}).get("estimated_cost"),
        duration_seconds=data.get("metadata", {}).get("duration_seconds"),
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(model_dump(metrics), indent=2), encoding="utf-8")
    typer.echo(f"Evaluation written: {output}")


@app.command()
def experiment(
    requirements: Path = typer.Option(..., exists=True),
    code_dir: Path = typer.Option(..., exists=True, file_okay=False),
    output_dir: Path = typer.Option(Path("out/experiments")),
    config: Path = typer.Option(Path("configs/default.yaml")),
    provider: Optional[str] = typer.Option(None),
) -> None:
    """Run the 3x3 strategy/context matrix across repeated runs."""

    cfg = load_config(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[ExperimentRunResult] = []

    for repeat in range(1, cfg.experiments.repeats + 1):
        for strategy in cfg.experiments.strategies:
            for context in cfg.experiments.contexts:
                _validate_strategy_and_context(strategy, context)
                run_dir = output_dir / f"{strategy}__{context}__r{repeat}"
                run_dir.mkdir(parents=True, exist_ok=True)
                started = time.perf_counter()
                try:
                    cfg_provider = create_provider(cfg, selector=provider)
                    reqs = parse_requirements(requirements)
                    code = analyze_code(code_dir)
                    maps = map_requirements_to_code(reqs, code, cfg.pipeline.mapping_confidence_threshold)
                    tests = generate_tests(reqs, maps, code, cfg_provider, strategy, context)
                    revised_tests, critiques = critique_tests(tests, threshold=cfg.pipeline.critique_threshold)
                    traceability = _build_traceability(revised_tests)
                    gaps = _build_gaps(reqs, traceability)
                    artifacts = GenerationArtifacts(
                        requirements=reqs,
                        code_elements=code,
                        mappings=maps,
                        tests=revised_tests,
                        critiques=critiques,
                        traceability=traceability,
                        gaps=gaps,
                        metadata={
                            "strategy": strategy,
                            "context": context,
                            "repeat": repeat,
                            "estimated_cost": cfg_provider.estimated_cost,
                            "duration_seconds": round(time.perf_counter() - started, 4),
                        },
                    )
                    art_path = run_dir / "generation_artifacts.json"
                    art_path.write_text(json.dumps(model_dump(artifacts), indent=2), encoding="utf-8")

                    eval_path = run_dir / "evaluation.json"
                    evaluate(artifacts=art_path, output=eval_path)
                    metrics = model_validate(EvaluationMetrics, json.loads(eval_path.read_text(encoding="utf-8")))
                    rows.append(
                        ExperimentRunResult(
                            model=f"{cfg_provider.name}:{cfg_provider.model}",
                            strategy=strategy,
                            context=context,
                            repeat_index=repeat,
                            status="ok",
                            metrics=metrics,
                            cost=cfg_provider.estimated_cost,
                            duration_seconds=round(time.perf_counter() - started, 4),
                            artifacts={"run_dir": str(run_dir)},
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    rows.append(
                        ExperimentRunResult(
                            model=(provider or cfg.llm.default_provider),
                            strategy=strategy,
                            context=context,
                            repeat_index=repeat,
                            status="failed",
                            error=str(exc),
                        )
                    )

    results_path = output_dir / "results.json"
    results_path.write_text(json.dumps([model_dump(r) for r in rows], indent=2), encoding="utf-8")
    typer.echo(f"Experiment results: {results_path}")


@app.command()
def report(
    results: Path = typer.Option(Path("out/experiments/results.json"), exists=True),
) -> None:
    """Create human-readable summaries from experiment results."""

    runs = json.loads(results.read_text(encoding="utf-8"))
    successful = [r for r in runs if r.get("status") == "ok"]
    if not successful:
        typer.echo("No successful runs in results.")
        raise typer.Exit(code=1)

    by_key: dict[tuple[str, str], list[dict]] = {}
    for run in successful:
        key = (run["strategy"], run["context"])
        by_key.setdefault(key, []).append(run)

    typer.echo("ReqLens experiment summary")
    typer.echo("=" * 60)
    for (strategy, context), group in sorted(by_key.items()):
        corr = [g["metrics"]["correctness_rate"] for g in group if g.get("metrics")]
        cov = [g["metrics"]["requirement_coverage"] for g in group if g.get("metrics")]
        trc = [g["metrics"]["traceability_accuracy"] for g in group if g.get("metrics")]
        typer.echo(
            f"{strategy:18s} | {context:24s} | "
            f"correctness={mean(corr):.3f} coverage={mean(cov):.3f} traceability={mean(trc):.3f}"
        )


@app.callback()
def main() -> None:
    """ReqLens command group."""


def _validate_strategy_and_context(strategy: str, context: str) -> None:
    if strategy not in _STRATEGIES:
        raise StageExecutionError("cli", f"Unsupported strategy '{strategy}'.")
    if context not in _CONTEXTS:
        raise StageExecutionError("cli", f"Unsupported context mode '{context}'.")


def _extract_requirement_ids(text: str) -> set[str]:
    return {m.group(1) for m in _REQ_ID_PATTERN.finditer(text)}


def _build_traceability(tests: list) -> list[TraceabilityEntry]:
    return [
        TraceabilityEntry(
            requirement_id=test.requirement_ids[0],
            test_id=test.test_id,
            covered_acceptance_criteria=list(test.acceptance_criteria_refs),
            confidence=1.0,
        )
        for test in tests
        if test.requirement_ids
    ]


def _build_gaps(requirements: list, traceability: list[TraceabilityEntry]) -> list[GapEntry]:
    covered = {t.requirement_id for t in traceability}
    return [
        GapEntry(
            requirement_id=req.id,
            reason="No test generated for requirement",
            suggested_followup="Review mapping threshold/prompt strategy or improve requirement clarity.",
        )
        for req in requirements
        if req.id not in covered
    ]


def _write_tests_file(path: Path, tests: list) -> None:
    lines = [
        '"""Auto-generated by ReqLens."""',
        "",
        "import importlib.util",
        "",
        "def _load_symbol(file_path: str, symbol: str):",
        "    spec = importlib.util.spec_from_file_location('reqlens_target', file_path)",
        "    if spec is None or spec.loader is None:",
        "        raise RuntimeError(f'Unable to load module from {file_path}')",
        "    module = importlib.util.module_from_spec(spec)",
        "    spec.loader.exec_module(module)",
        "    return getattr(module, symbol)",
        "",
    ]
    for test in tests:
        lines.append(test.body.rstrip())
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_traceability(path: Path, traceability: list[TraceabilityEntry]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["requirement_id", "test_id", "covered_acceptance_criteria", "confidence"])
        for row in traceability:
            writer.writerow(
                [
                    row.requirement_id,
                    row.test_id,
                    "; ".join(row.covered_acceptance_criteria),
                    row.confidence,
                ]
            )


if __name__ == "__main__":
    try:
        app()
    except (ReqLensError, StageExecutionError) as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc
