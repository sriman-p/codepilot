# ReqLens

ReqLens is a Python CLI tool that generates requirement-traceable pytest tests from requirements and source code.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
reqlens --help
```

## Commands

- `reqlens generate`
- `reqlens evaluate`
- `reqlens experiment`
- `reqlens report`

## Default config

A sample config is provided at `configs/default.yaml`.
