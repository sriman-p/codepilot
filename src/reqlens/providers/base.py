"""Base interface for LLM providers."""

from __future__ import annotations

import abc
from typing import Optional

from reqlens.models.schemas import CodeElement, Requirement


class LLMProvider(abc.ABC):
    def __init__(
        self,
        name: str,
        model: str,
        token_price_input: Optional[float] = None,
        token_price_output: Optional[float] = None,
    ):
        self.name = name
        self.model = model
        self.token_price_input = token_price_input
        self.token_price_output = token_price_output
        self.prompt_tokens_total = 0
        self.completion_tokens_total = 0

    @abc.abstractmethod
    def generate_test(
        self,
        requirement: Requirement,
        code_element: Optional[CodeElement],
        strategy: str,
        context_mode: str,
    ) -> str:
        raise NotImplementedError

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens_total += max(prompt_tokens, 0)
        self.completion_tokens_total += max(completion_tokens, 0)

    @property
    def estimated_cost(self) -> Optional[float]:
        if self.token_price_input is None or self.token_price_output is None:
            return None
        return round(
            self.prompt_tokens_total * self.token_price_input
            + self.completion_tokens_total * self.token_price_output,
            6,
        )

    def build_prompt(
        self,
        requirement: Requirement,
        code_element: Optional[CodeElement],
        strategy: str,
        context_mode: str,
    ) -> str:
        steps = ""
        if strategy == "chain_of_thought":
            steps = "Think through edge cases before writing the final test code."
        elif strategy == "few_shot":
            steps = (
                "Example:\n"
                "Requirement: REQ-EXAMPLE user can add two numbers\n"
                "Test:\n"
                "def test_req_example():\n"
                "    assert add(2, 3) == 5\n"
            )

        code_context = "No code context available."
        if code_element is not None:
            code_context = (
                f"Symbol: {code_element.qualified_name}\n"
                f"Type: {code_element.symbol_type}\n"
                f"Signature: {code_element.signature}\n"
                f"File: {code_element.file_path}"
            )

        return (
            "Write a pytest test function for the requirement below.\n"
            f"Strategy: {strategy}\n"
            f"Context mode: {context_mode}\n"
            f"Requirement ID: {requirement.id}\n"
            f"Requirement text: {requirement.text}\n"
            f"Acceptance criteria: {requirement.acceptance_criteria}\n"
            f"Code context:\n{code_context}\n"
            f"{steps}\n"
            "Return only Python code."
        )
