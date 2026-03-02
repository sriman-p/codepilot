# ReqLens

ReqLens is a Python CLI tool that generates requirement-traceable pytest tests from requirements and source code.

It provides:
- A **5-stage pipeline** (requirements parse → code analysis → mapping → generation → critique).
- Test outputs that explicitly reference requirement IDs.
- A traceability matrix and a gap report.
- Experiment orchestration for 3×3 strategy/context comparisons with repeats.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
reqlens --help
```

## Commands

- `reqlens generate` — run full pipeline and write artifacts.
- `reqlens evaluate` — compute evaluation metrics from generated artifacts.
- `reqlens experiment` — execute matrix experiments with repeats.
- `reqlens report` — print experiment summaries.

## Default config

A sample config is provided at `configs/default.yaml`.

## Example

```bash
reqlens generate \
  --requirements requirements.md \
  --code-dir src \
  --output-dir out \
  --config configs/default.yaml

reqlens evaluate --artifacts out/generation_artifacts.json --output out/evaluation.json
reqlens experiment --requirements requirements.md --code-dir src --output-dir out/experiments
reqlens report --results out/experiments/results.json
```
