from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from reqlens.cli import app


def test_generate_and_evaluate(tmp_path: Path) -> None:
    runner = CliRunner()
    req = Path("tests/fixtures/requirements.md")
    code_dir = Path("tests/fixtures/sample_app")

    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "generate",
            "--requirements",
            str(req),
            "--code-dir",
            str(code_dir),
            "--config",
            "configs/default.yaml",
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.stdout

    artifacts = out_dir / "generation_artifacts.json"
    tests_file = out_dir / "test_generated.py"
    traceability = out_dir / "traceability.csv"
    gaps = out_dir / "gap_report.json"
    assert artifacts.exists()
    assert tests_file.exists()
    assert traceability.exists()
    assert gaps.exists()

    eval_file = out_dir / "evaluation.json"
    eval_result = runner.invoke(
        app,
        [
            "evaluate",
            "--artifacts",
            str(artifacts),
            "--output",
            str(eval_file),
            "--ground-truth-tests",
            "tests/fixtures/ground_truth_tests.py",
        ],
    )
    assert eval_result.exit_code == 0, eval_result.stdout
    metrics = json.loads(eval_file.read_text(encoding="utf-8"))
    assert metrics["requirement_coverage"] >= 1.0
    assert metrics["correctness_rate"] > 0


def test_generate_requirements_only_omits_code_refs(tmp_path: Path) -> None:
    runner = CliRunner()
    out_dir = tmp_path / "out_req_only"
    result = runner.invoke(
        app,
        [
            "generate",
            "--requirements",
            "tests/fixtures/requirements.md",
            "--code-dir",
            "tests/fixtures/sample_app",
            "--context",
            "requirements_only",
            "--config",
            "configs/default.yaml",
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.stdout
    generated_test = (out_dir / "test_generated.py").read_text(encoding="utf-8")
    assert "assert True" in generated_test
