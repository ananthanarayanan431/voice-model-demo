"""Shared fixtures. Keys are cleared so a developer's real .env never leaks in."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from voice_agent.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in (
        "VARTALOOP_API_KEY",
        "ANTHROPIC_API_KEY",
        "API_KEY",
        "ADDITIONAL_CORS_ORIGINS",
        "ENVIRONMENT",
    ):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
