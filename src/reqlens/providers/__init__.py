"""Provider factory and exports."""

from __future__ import annotations

from typing import Optional

from reqlens.models.schemas import AppConfig, ProviderConfig
from reqlens.providers.anthropic_provider import AnthropicProvider
from reqlens.providers.base import LLMProvider
from reqlens.providers.mock_provider import MockProvider
from reqlens.providers.openai_provider import OpenAIProvider


def create_provider(config: AppConfig, selector: str | None = None) -> LLMProvider:
    target = selector or config.llm.default_provider or "mock"
    provider_name, model_override = _parse_selector(target)
    provider_cfg = _find_provider_cfg(config, provider_name)

    if provider_name == "mock":
        model = model_override or (provider_cfg.model if provider_cfg else "mock-v1")
        return MockProvider(model=model)

    if provider_name == "openai":
        if provider_cfg is None:
            provider_cfg = ProviderConfig(name="openai", model=model_override or "gpt-4o-mini")
        return OpenAIProvider(
            model=model_override or provider_cfg.model,
            api_key_env=provider_cfg.api_key_env or "OPENAI_API_KEY",
            api_base=provider_cfg.api_base or "https://api.openai.com/v1",
            token_price_input=provider_cfg.token_price_input,
            token_price_output=provider_cfg.token_price_output,
        )

    if provider_name == "anthropic":
        if provider_cfg is None:
            provider_cfg = ProviderConfig(name="anthropic", model=model_override or "claude-3-haiku-20240307")
        return AnthropicProvider(
            model=model_override or provider_cfg.model,
            api_key_env=provider_cfg.api_key_env or "ANTHROPIC_API_KEY",
            api_base=provider_cfg.api_base or "https://api.anthropic.com/v1",
            token_price_input=provider_cfg.token_price_input,
            token_price_output=provider_cfg.token_price_output,
        )

    return MockProvider(model=model_override or "mock-v1")


def _parse_selector(selector: str) -> tuple[str, Optional[str]]:
    if ":" in selector:
        left, right = selector.split(":", 1)
        return left.strip().lower(), right.strip()
    return selector.strip().lower(), None


def _find_provider_cfg(config: AppConfig, name: str) -> ProviderConfig | None:
    for provider in config.llm.providers:
        if provider.enabled and provider.name.strip().lower() == name:
            return provider
    return None


__all__ = [
    "LLMProvider",
    "MockProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "create_provider",
]
