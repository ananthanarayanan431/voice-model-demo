"""The in-memory rate limiter and the short-lived speech links."""

from __future__ import annotations

import pytest

from voice_agent.core.errors import RateLimitedError
from voice_agent.core.rate_limit import RateLimiter
from voice_agent.services.speech import SpeechCache


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_limit_applies_per_client_within_the_window() -> None:
    clock = Clock()
    limiter = RateLimiter(2, clock)
    limiter.check("a")
    limiter.check("a")
    limiter.check("b")
    with pytest.raises(RateLimitedError) as caught:
        limiter.check("a")
    assert caught.value.headers["Retry-After"] == "61"
    clock.now = 60
    limiter.check("a")


def test_zero_disables_the_limit() -> None:
    limiter = RateLimiter(0)
    for _ in range(100):
        limiter.check("a")


def test_speech_links_expire() -> None:
    clock = Clock()
    cache = SpeechCache(ttl_seconds=10, clock=clock)
    speech_id = cache.put("Namaste")
    assert len(speech_id) >= 16
    assert cache.get(speech_id) == "Namaste"
    clock.now = 10
    assert cache.get(speech_id) is None
    assert cache.get("unknown") is None
