# CodePilot (ReqLens)

CodePilot (ReqLens) is a Python CLI tool that generates requirement-traceable pytest tests from requirements and source code.

It provides:
- A **5-stage pipeline** (requirements parse → code analysis → mapping → generation → critique).
- Test outputs that explicitly reference requirement IDs.
- A traceability matrix and a gap report.
- Experiment orchestration for 3×3 strategy/context comparisons with repeats.

## Architecture Diagram

```mermaid
flowchart TD
    U[User / CI] --> CLI[reqlens CLI\n(generate | evaluate | experiment | report)]
    CLI --> CFG[Config Loader\nconfigs/default.yaml]

    subgraph Pipeline[Generation Pipeline]
        RP[1. Requirements Parser\nrequirements_parser.py]
        CA[2. Code Analyzer\ncode_analyzer.py]
        MP[3. Requirement↔Code Mapper\nmapper.py]
        TG[4. Test Generator\ntest_generator.py]
        CR[5. Critique & Revision\ncritique.py]

        RP --> MP
        CA --> MP
        MP --> TG
        TG --> CR
    end

    CLI --> RP
    CLI --> CA

    TG --> PF[Provider Factory\nproviders/__init__.py]
    PF --> MOCK[Mock Provider]
    PF --> OA[OpenAI Provider]
    PF --> AN[Anthropic Provider]

    CR --> ART[Artifacts\n- test_generated.py\n- traceability.csv\n- gap_report.json\n- generation_artifacts.json]

    CLI --> EV[Evaluation\n(requirement coverage,\ncorrectness, traceability)]
    EV --> REP[Experiment Report Summary]

    ART --> EV
```

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
