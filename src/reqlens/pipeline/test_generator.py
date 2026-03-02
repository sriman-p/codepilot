"""Test generation stage."""

from __future__ import annotations

import re
from typing import Iterable

from reqlens.models.schemas import CodeElement, GeneratedTestCase, Requirement, RequirementCodeMapping
from reqlens.providers.base import LLMProvider


_IDENTIFIER = re.compile(r"[^a-zA-Z0-9_]+")


def generate_tests(
    requirements: Iterable[Requirement],
    mappings: Iterable[RequirementCodeMapping],
    code_elements: Iterable[CodeElement],
    provider: LLMProvider,
    strategy: str,
    context_mode: str,
) -> list[GeneratedTestCase]:
    req_by_id = {req.id: req for req in requirements}
    code_by_id = {element.id: element for element in code_elements}

    test_cases: list[GeneratedTestCase] = []
    for mapping in mappings:
        requirement = req_by_id.get(mapping.requirement_id)
        if requirement is None:
            continue
        primary_element = code_by_id.get(mapping.code_element_ids[0]) if mapping.code_element_ids else None

        body = provider.generate_test(
            requirement=requirement,
            code_element=primary_element,
            strategy=strategy,
            context_mode=context_mode,
        )
        test_id = f"test_{_safe_name(requirement.id)}"
        test_cases.append(
            GeneratedTestCase(
                test_id=test_id,
                requirement_ids=[requirement.id],
                acceptance_criteria_refs=list(requirement.acceptance_criteria),
                code_refs=list(mapping.code_element_ids),
                body=body,
            )
        )

    return test_cases


def _safe_name(value: str) -> str:
    return _IDENTIFIER.sub("_", value.lower()).strip("_") or "unnamed"
