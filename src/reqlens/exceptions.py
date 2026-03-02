"""Domain exceptions for ReqLens."""


class ReqLensError(Exception):
    """Base exception for ReqLens."""


class ConfigError(ReqLensError):
    """Raised when config is invalid or missing."""


class StageExecutionError(ReqLensError):
    """Raised when a pipeline stage fails."""

    def __init__(self, stage: str, message: str):
        self.stage = stage
        super().__init__(f"[{stage}] {message}")


class ProviderError(ReqLensError):
    """Raised when an LLM provider fails."""
