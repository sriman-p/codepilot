"""Requirement-to-code mapping stage."""

from __future__ import annotations

import re
from typing import Iterable

from reqlens.models.schemas import CodeElement, Requirement, RequirementCodeMapping

_TOKEN_SPLIT = re.compile(r"[^a-zA-Z0-9_]+")


def map_requirements_to_code(
    requirements: Iterable[Requirement],
    code_elements: Iterable[CodeElement],
    confidence_threshold: float = 0.1,
    top_k: int = 3,
) -> list[RequirementCodeMapping]:
    element_list = list(code_elements)
    mappings: list[RequirementCodeMapping] = []

    for requirement in requirements:
        req_tokens = _tokens(" ".join([requirement.text] + requirement.acceptance_criteria))
        scored: list[tuple[CodeElement, float]] = []
        for element in element_list:
            hay = f"{element.qualified_name} {element.signature} {element.symbol_type}"
            score = _jaccard(req_tokens, _tokens(hay))
            scored.append((element, score))
        scored.sort(key=lambda x: x[1], reverse=True)

        selected = [item for item in scored[:top_k] if item[1] >= confidence_threshold]
        if selected:
            code_ids = [item[0].id for item in selected]
            confidence = selected[0][1]
            rationale = "Top lexical overlap between requirement text and symbol names/signatures."
        else:
            code_ids = []
            confidence = 0.0
            rationale = "No code element crossed the confidence threshold."

        mappings.append(
            RequirementCodeMapping(
                requirement_id=requirement.id,
                code_element_ids=code_ids,
                confidence=round(confidence, 4),
                rationale=rationale,
            )
        )

    return mappings


def _tokens(text: str) -> set[str]:
    pieces = [p.strip().lower() for p in _TOKEN_SPLIT.split(text) if p.strip()]
    return {p for p in pieces if len(p) > 1}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    inter = len(left.intersection(right))
    union = len(left.union(right))
    if union == 0:
        return 0.0
    return inter / union
