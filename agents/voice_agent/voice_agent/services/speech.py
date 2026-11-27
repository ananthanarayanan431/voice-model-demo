"""Short-lived links to a reply's audio.

``/chat`` stores the reply text here and returns ``/api/v1/speech/<id>``; the
browser's <audio> element fetches that URL. So patient-facing text never sits in
a URL (or an access log), and the speech endpoint can only speak replies the
agent itself wrote, never arbitrary text.
"""

from __future__ import annotations

import secrets
import time
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

MAX_ENTRIES = 1000


class SpeechCache:
    def __init__(self, ttl_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, str]] = OrderedDict()

    def put(self, text: str) -> str:
        self._expire()
        speech_id = secrets.token_urlsafe(18)
        self._entries[speech_id] = (self._clock() + self._ttl, text)
        while len(self._entries) > MAX_ENTRIES:
            self._entries.popitem(last=False)
        return speech_id

    def get(self, speech_id: str) -> str | None:
        self._expire()
        entry = self._entries.get(speech_id)
        return entry[1] if entry else None

    def _expire(self) -> None:
        now = self._clock()
        while self._entries:
            speech_id, (expires, _) = next(iter(self._entries.items()))
            if expires > now:
                break
            del self._entries[speech_id]
