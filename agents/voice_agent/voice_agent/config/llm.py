"""Claude settings for the conversation agent."""

from __future__ import annotations

from typing import Literal

from pydantic import SecretStr

from voice_agent.config.base import SettingsGroup

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class AnthropicSettings(SettingsGroup):
    # Blank: the SDK resolves credentials itself (ANTHROPIC_AUTH_TOKEN, `ant auth login`).
    ANTHROPIC_API_KEY: SecretStr | None = None
    ANTHROPIC_LLM_MODEL: str = "claude-opus-5-5"
    # Spoken replies are short; low effort keeps the wait before the voice short too.
    ANTHROPIC_EFFORT: Effort = "low"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TIMEOUT_SECONDS: float = 60
    # Tool round trips allowed in one patient turn (guards against loops).
    MAX_TOOL_ROUNDS: int = 6
