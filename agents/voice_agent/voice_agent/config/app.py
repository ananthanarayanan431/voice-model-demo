"""Application, HTTP and operational settings."""

from __future__ import annotations

from typing import Literal

from pydantic import SecretStr

from voice_agent.config.base import SettingsGroup

Environment = Literal["local", "test", "staging", "production"]
LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class AppSettings(SettingsGroup):
    PROJECT_NAME: str = "VoiceAgents"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = "local"
    LOG_LEVEL: LogLevel = "INFO"
    # One JSON object per line, for log shippers in deployed environments.
    LOG_JSON: bool = False
    # When set, every /api/v1 call must send it as the X-API-Key header.
    API_KEY: SecretStr | None = None
    # Comma or semicolon separated, for a web app served from another origin.
    ADDITIONAL_CORS_ORIGINS: str = ""
    # Hospital time zone: "today" for bookings is a date in this zone.
    TIMEZONE: str = "Asia/Kolkata"
    # Patient turns allowed per client IP per minute (each one calls Claude).
    CHAT_RATE_LIMIT_PER_MINUTE: int = 30
    # A conversation idle this long is forgotten.
    SESSION_TTL_SECONDS: int = 1800
    MAX_SESSIONS: int = 500
    # How long a reply's audio link stays playable.
    SPEECH_TTL_SECONDS: int = 300

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def cors_origins(self) -> list[str]:
        raw = self.ADDITIONAL_CORS_ORIGINS.replace(";", ",")
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
