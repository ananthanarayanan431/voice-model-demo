"""Application and HTTP settings."""

from __future__ import annotations

from pydantic import SecretStr

from voice_agent.config.base import SettingsGroup


class AppSettings(SettingsGroup):
    PROJECT_NAME: str = "VoiceAgents"
    APP_VERSION: str = "0.1.0"
    # When set, every /api/v1 call must send it as the X-API-Key header.
    API_KEY: SecretStr | None = None
    # Comma or semicolon separated, for a web app served from another origin.
    ADDITIONAL_CORS_ORIGINS: str = ""
    # Hospital time zone: "today" for bookings is a date in this zone.
    TIMEZONE: str = "Asia/Kolkata"

    def cors_origins(self) -> list[str]:
        raw = self.ADDITIONAL_CORS_ORIGINS.replace(";", ",")
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
