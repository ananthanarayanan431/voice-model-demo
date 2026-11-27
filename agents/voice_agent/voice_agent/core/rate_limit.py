"""A per-client sliding-window rate limit, kept in memory.

It suits the single-process deployment this service runs as (conversations are
in memory too). Behind several workers or replicas, move it to a shared store.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import TYPE_CHECKING

from voice_agent.core.errors import RateLimitedError

if TYPE_CHECKING:
    from collections.abc import Callable

WINDOW_SECONDS = 60.0


class RateLimiter:
    def __init__(self, limit: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._limit = limit
        self._clock = clock
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def check(self, client: str) -> None:
        """Count one request from ``client``, or raise ``RateLimitedError``."""
        if self._limit <= 0:
            return
        now = self._clock()
        hits = self._hits[client]
        while hits and now - hits[0] >= WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self._limit:
            retry_after = max(1, int(WINDOW_SECONDS - (now - hits[0])) + 1)
            raise RateLimitedError(headers={"Retry-After": str(retry_after)})
        hits.append(now)
        if len(self._hits) > 10_000:
            self._forget_idle(now)

    def _forget_idle(self, now: float) -> None:
        idle = [
            key for key, hits in self._hits.items() if not hits or now - hits[-1] >= WINDOW_SECONDS
        ]
        for key in idle:
            del self._hits[key]
