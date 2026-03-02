"""Deterministic mock provider for offline development and tests."""

from __future__ import annotations

import re

from reqlens.models.schemas import CodeElement, Requirement
from reqlens.providers.base import LLMProvider

_IDENTIFIER = re.compile(r"[^a-zA-Z0-9_]+")


class MockProvider(LLMProvider):
    def __init__(self, model: str = "mock-v1"):
        super().__init__(name="mock", model=model, token_price_input=0.0, token_price_output=0.0)

    def generate_test(
        self,
        requirement: Requirement,
        code_element: CodeElement | None,
        strategy: str,
        context_mode: str,
    ) -> str:
        prompt = self.build_prompt(requirement, code_element, strategy, context_mode)

        req_slug = _safe(requirement.id)
        lines = [f"def test_{req_slug}():"]
        lines.append(f"    \"\"\"Requirement {requirement.id}: {requirement.text}\"\"\"")

        if code_element is not None:
            symbol_name = code_element.qualified_name.split(".")[-1]
            file_path = code_element.file_path.replace("\\", "\\\\")
            lines.append(f"    symbol = _load_symbol(r\"{file_path}\", \"{symbol_name}\")")
            lines.append("    assert callable(symbol)")
            if _looks_numeric(requirement.text):
                lines.append("    try:")
                lines.append("        assert symbol(2, 3) == 5")
                lines.append("    except TypeError:")
                lines.append("        assert True")
        else:
            lines.append("    assert True")

        self.record_usage(prompt_tokens=max(len(prompt) // 4, 1), completion_tokens=max(len("\n".join(lines)) // 4, 1))
        return "\n".join(lines)


def _safe(value: str) -> str:
    return _IDENTIFIER.sub("_", value.lower()).strip("_") or "generated"


def _looks_numeric(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ["add", "sum", "subtract", "multiply", "divide"])
