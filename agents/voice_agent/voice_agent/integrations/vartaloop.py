"""Vartaloop text-to-speech: POST /v1/tts, streamed back as Ogg/Opus.

https://docs.vartaloop.ai/api/tts/ - errors are decided before any audio is
sent, so a non-2xx status is the whole story and a 200 always carries audio.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import httpx
from loguru import logger

from voice_agent.core.errors import NotConfiguredError, UpstreamError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from voice_agent.config.integrations import VartaloopSettings

OPUS_MEDIA_TYPE = "audio/ogg"
_MAX_RETRY_WAIT_SECONDS = 2.0


class SpeechStream:
    """An open TTS response: iterate ``chunks()``, then ``aclose()``."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.request_id = response.headers.get("x-request-id", "")

    def chunks(self) -> AsyncIterator[bytes]:
        return self._response.aiter_bytes()

    async def aclose(self) -> None:
        await self._response.aclose()


class VartaloopTTS:
    def __init__(self, settings: VartaloopSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    def _key(self) -> str:
        key = self._settings.VARTALOOP_API_KEY
        return key.get_secret_value().strip() if key else ""

    @property
    def configured(self) -> bool:
        return bool(self._key())

    async def open_stream(self, text: str) -> SpeechStream:
        key = self._key()
        if not key:
            msg = "VARTALOOP_API_KEY is not set in agents/voice_agent/.env."
            raise NotConfiguredError(msg)
        response = await self._send(key, text)
        if response.status_code == 503:
            # Busy: nothing was billed. Retry once after the advertised wait.
            await response.aclose()
            wait = _retry_after(response.headers.get("retry-after"))
            logger.info("Vartaloop busy; retrying in {}s", wait)
            await asyncio.sleep(wait)
            response = await self._send(key, text)
        if response.is_error:
            await response.aread()
            await response.aclose()
            logger.warning("Vartaloop returned {}", response.status_code)
            msg = f"Text-to-speech failed (Vartaloop {response.status_code})."
            raise UpstreamError(msg)
        return SpeechStream(response)

    async def _send(self, key: str, text: str) -> httpx.Response:
        request = self._client.build_request(
            "POST",
            f"{self._settings.VARTALOOP_API_URL}/v1/tts",
            headers={"x-api-key": key},
            json={"text": text, "voice": self._settings.VARTALOOP_VOICE, "format": "opus"},
            timeout=self._settings.VARTALOOP_TIMEOUT_SECONDS,
        )
        try:
            return await self._client.send(request, stream=True)
        except httpx.HTTPError as exc:
            msg = "Could not reach Vartaloop."
            raise UpstreamError(msg) from exc


def _retry_after(value: str | None) -> float:
    try:
        return min(max(float(value or 1), 0.0), _MAX_RETRY_WAIT_SECONDS)
    except ValueError:
        return 1.0
