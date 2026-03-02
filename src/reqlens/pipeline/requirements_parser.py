"""Requirements parsing for markdown, text, and CSV formats."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from reqlens.exceptions import StageExecutionError
from reqlens.models.schemas import Requirement

_ID_LINE = re.compile(r"^([A-Za-z]{2,}-[A-Za-z0-9_.-]+)\s*[:|-]\s*(.+)$")
_TABLE_ROW = re.compile(r"^\|\s*([A-Za-z]{2,}-[A-Za-z0-9_.-]+)\s*\|(.+)$")


def parse_requirements(path: str | Path) -> list[Requirement]:
    req_path = Path(path)
    if not req_path.exists():
        raise StageExecutionError("requirements_parser", f"File not found: {req_path}")

    suffix = req_path.suffix.lower()
    if suffix == ".csv":
        return _parse_csv(req_path)
    if suffix in {".md", ".markdown", ".txt"}:
        return _parse_textual(req_path)

    raise StageExecutionError(
        "requirements_parser",
        f"Unsupported requirements format '{suffix}'. Use .md, .txt, or .csv.",
    )


def _parse_csv(path: Path) -> list[Requirement]:
    requirements: list[Requirement] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for idx, row in enumerate(reader, start=1):
                req_id = (row.get("id") or row.get("requirement_id") or f"REQ-{idx:03d}").strip()
                text = (row.get("text") or row.get("description") or "").strip()
                if not text:
                    continue
                ac = _split_multi(row.get("acceptance_criteria", ""))
                deps = _split_multi(row.get("dependencies", ""))
                requirements.append(
                    Requirement(
                        id=req_id,
                        text=text,
                        acceptance_criteria=ac,
                        priority=(row.get("priority") or "").strip() or None,
                        dependencies=deps,
                    )
                )
    except Exception as exc:
        raise StageExecutionError("requirements_parser", f"Failed to parse CSV {path}: {exc}") from exc

    if not requirements:
        raise StageExecutionError("requirements_parser", f"No requirements found in {path}")
    return requirements


def _parse_textual(path: Path) -> list[Requirement]:
    lines = path.read_text(encoding="utf-8").splitlines()

    requirements = _parse_markdown_tables(lines)
    if requirements:
        return requirements

    requirements = _parse_blocks(lines)
    if requirements:
        return requirements

    return _parse_fallback_paragraphs(lines)


def _parse_markdown_tables(lines: list[str]) -> list[Requirement]:
    requirements: list[Requirement] = []
    for line in lines:
        if not _TABLE_ROW.match(line.strip()):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        req_id = cells[0]
        if req_id.upper() == "ID" or set(req_id) == {"-"}:
            continue
        if len(cells) >= 3:
            text = " ".join(c for c in [cells[1], cells[2]] if c)
        else:
            text = cells[1]
        if not req_id or not text:
            continue
        requirements.append(Requirement(id=req_id, text=text))
    return requirements


def _parse_blocks(lines: list[str]) -> list[Requirement]:
    requirements: list[Requirement] = []
    current: Requirement | None = None

    def flush_current() -> None:
        nonlocal current
        if current and current.text.strip():
            requirements.append(current)
        current = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        match = _ID_LINE.match(line)
        if match:
            flush_current()
            current = Requirement(id=match.group(1).strip(), text=match.group(2).strip())
            continue

        if current is None:
            continue

        if line.startswith("-"):
            item = line.lstrip("- ").strip()
            lowered = item.lower()
            if lowered.startswith("ac:") or lowered.startswith("acceptance"):
                value = item.split(":", 1)[1].strip() if ":" in item else item
                if value:
                    current.acceptance_criteria.append(value)
            elif lowered.startswith("priority") and ":" in item:
                current.priority = item.split(":", 1)[1].strip() or None
            elif lowered.startswith("depends") and ":" in item:
                deps = _split_multi(item.split(":", 1)[1])
                current.dependencies.extend(deps)
            else:
                current.acceptance_criteria.append(item)
        else:
            current.text = f"{current.text} {line}".strip()

    flush_current()
    return requirements


def _parse_fallback_paragraphs(lines: list[str]) -> list[Requirement]:
    paragraphs = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    requirements: list[Requirement] = []
    counter = 1
    for paragraph in paragraphs:
        if len(paragraph) < 12:
            continue
        requirements.append(Requirement(id=f"REQ-{counter:03d}", text=paragraph))
        counter += 1

    if not requirements:
        raise StageExecutionError("requirements_parser", "No requirements found in file")
    return requirements


def _split_multi(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;,]", value) if item.strip()]
