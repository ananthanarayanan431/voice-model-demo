"""Vartaloop text-to-speech settings (https://docs.vartaloop.ai)."""

from __future__ import annotations

from pydantic import SecretStr

from voice_agent.config.base import SettingsGroup


class VartaloopSettings(SettingsGroup):
    VARTALOOP_API_KEY: SecretStr | None = None
    VARTALOOP_API_URL: str = "https://api.vartaloop.ai"
    VARTALOOP_VOICE: str = "saanvi"
    # A spoken reply is a few sentences; this caps what one /tts call can bill.
    VARTALOOP_MAX_CHARS: int = 800
    VARTALOOP_TIMEOUT_SECONDS: float = 60
