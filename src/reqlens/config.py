"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from reqlens.compat import model_validate
from reqlens.exceptions import ConfigError
from reqlens.models.schemas import AppConfig


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    try:
        raw: dict[str, Any] = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file {config_path}: {exc}") from exc

    try:
        return model_validate(AppConfig, raw)
    except Exception as exc:
        raise ConfigError(f"Config validation failed for {config_path}: {exc}") from exc
