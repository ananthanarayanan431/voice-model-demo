"""Settings, read as ``get_settings().<group>.<FIELD>``."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from voice_agent.config.app import AppSettings
from voice_agent.config.integrations import VartaloopSettings
from voice_agent.config.llm import AnthropicSettings

API_V1_PREFIX = "/api/v1"


@dataclass(frozen=True)
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    anthropic: AnthropicSettings = field(default_factory=AnthropicSettings)
    vartaloop: VartaloopSettings = field(default_factory=VartaloopSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["API_V1_PREFIX", "Settings", "get_settings"]
