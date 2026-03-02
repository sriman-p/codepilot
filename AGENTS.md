# AGENTS.md

## Cursor Cloud specific instructions

**ReqLens** is a Python CLI tool that generates requirement-traceable pytest tests. It is a single-package Python project (not a monorepo).

### Quick reference

| Task | Command |
|------|---------|
| Install deps | `source .venv/bin/activate && pip install -e ".[dev]"` |
| Run tests | `source .venv/bin/activate && pytest -v` |
| CLI help | `source .venv/bin/activate && reqlens --help` |
| Generate (mock) | `source .venv/bin/activate && reqlens generate --requirements requirements.md --code-dir src --output-dir out --config configs/default.yaml` |
| Evaluate | `source .venv/bin/activate && reqlens evaluate --artifacts out/generation_artifacts.json --output out/evaluation.json` |

### Non-obvious caveats

- **Virtual environment**: The project uses a `.venv` at the repo root. Always activate it before running commands: `source .venv/bin/activate`.
- **Mock provider**: The default LLM provider is `mock` (configured in `configs/default.yaml`). Tests and local development work fully offline without API keys.
- **No lint tool configured**: The project has no linter (flake8/ruff/mypy) in `pyproject.toml` or as dev dependencies. Only `pytest` is available for automated checks.
- **src layout**: Source code lives under `src/reqlens/`. The `pythonpath = ["src"]` is set in `[tool.pytest.ini_options]` in `pyproject.toml`.
- **No external services**: No database, Docker, or background processes are required. The entire tool runs as a local CLI.
