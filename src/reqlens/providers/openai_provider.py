"""OpenAI provider implementation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from reqlens.exceptions import ProviderError
from reqlens.models.schemas import CodeElement, Requirement
from reqlens.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        model: str,
        api_key_env: str = "OPENAI_API_KEY",
        api_base: str = "https://api.openai.com/v1",
        token_price_input: float | None = None,
        token_price_output: float | None = None,
    ):
        super().__init__(
            name="openai",
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
            "messages": [
                {"role": "system", "content": "You are a Python test generation assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            url=f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ProviderError(f"OpenAI HTTP error {exc.code}: {detail}") from exc
        except Exception as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except Exception as exc:
            raise ProviderError(f"Unexpected OpenAI response format: {body}") from exc

        usage = body.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or max(len(prompt) // 4, 1))
        completion_tokens = int(usage.get("completion_tokens") or max(len(content) // 4, 1))
        self.record_usage(prompt_tokens, completion_tokens)
        return str(content).strip()
