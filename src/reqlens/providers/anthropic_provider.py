"""Anthropic provider implementation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from reqlens.exceptions import ProviderError
from reqlens.models.schemas import CodeElement, Requirement
from reqlens.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        model: str,
        api_key_env: str = "ANTHROPIC_API_KEY",
        api_base: str = "https://api.anthropic.com/v1",
        token_price_input: float | None = None,
        token_price_output: float | None = None,
    ):
        super().__init__(
            name="anthropic",
            model=model,
            token_price_input=token_price_input,
            token_price_output=token_price_output,
        )
        self.api_key_env = api_key_env
        self.api_base = api_base.rstrip("/")

    def generate_test(
        self,
        requirement: Requirement,
        code_element: CodeElement | None,
        strategy: str,
        context_mode: str,
    ) -> str:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise ProviderError(f"Environment variable '{self.api_key_env}' is not set")

        prompt = self.build_prompt(requirement, code_element, strategy, context_mode)
        payload = {
            "model": self.model,
            "max_tokens": 600,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
        }

        req = urllib.request.Request(
            url=f"{self.api_base}/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ProviderError(f"Anthropic HTTP error {exc.code}: {detail}") from exc
        except Exception as exc:
            raise ProviderError(f"Anthropic request failed: {exc}") from exc

        try:
            content_block = body["content"][0]
            content = content_block["text"]
        except Exception as exc:
            raise ProviderError(f"Unexpected Anthropic response format: {body}") from exc

        usage = body.get("usage") or {}
        prompt_tokens = int(usage.get("input_tokens") or max(len(prompt) // 4, 1))
        completion_tokens = int(usage.get("output_tokens") or max(len(content) // 4, 1))
        self.record_usage(prompt_tokens, completion_tokens)
        return str(content).strip()
