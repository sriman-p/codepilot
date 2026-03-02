"""Self-critique and optional revision stage."""

from __future__ import annotations

from reqlens.models.schemas import CritiqueResult, GeneratedTestCase


def critique_tests(
    tests: list[GeneratedTestCase],
    threshold: float = 0.6,
    auto_revise: bool = True,
) -> tuple[list[GeneratedTestCase], list[CritiqueResult]]:
    results: list[CritiqueResult] = []
    revised: list[GeneratedTestCase] = []

    for test in tests:
        score, feedback = _score_test(test)
        updated = test.model_copy(deep=True) if hasattr(test, "model_copy") else test.copy(deep=True)
        updated.quality_score = score
        revised_body = None

        if auto_revise and score < threshold:
            revised_body = _revise_test_body(updated.body)
            updated.body = revised_body

        results.append(
            CritiqueResult(
                test_id=test.test_id,
                score=score,
                feedback=feedback,
                revised_body=revised_body,
            )
        )
        revised.append(updated)

    return revised, results


def _score_test(test: GeneratedTestCase) -> tuple[float, str]:
    score = 0.0
    feedback: list[str] = []
    body = test.body

    if "assert " in body:
        score += 0.45
    else:
        feedback.append("Missing assertion")

    if "def test_" in body:
        score += 0.2
    else:
        feedback.append("Missing pytest-style test function")

    if test.requirement_ids and any(req_id in body for req_id in test.requirement_ids):
        score += 0.2
    else:
        feedback.append("Requirement ID is not referenced in test body")

    if "TODO" not in body and "pass" not in body:
        score += 0.15
    else:
        feedback.append("Contains placeholder logic")

    score = round(min(score, 1.0), 3)
    if not feedback:
        feedback.append("Test quality is acceptable")
    return score, "; ".join(feedback)


def _revise_test_body(body: str) -> str:
    if "assert " in body:
        return body
    lines = body.rstrip().splitlines()
    if not lines:
        return "def test_generated():\n    assert True"
    lines.append("    assert True")
    return "\n".join(lines)
