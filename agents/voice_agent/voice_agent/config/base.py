"""Base class for every settings group: reads the environment, then ``.env``."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from voice_agent.config.paths import ENV_FILE


class SettingsGroup(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
