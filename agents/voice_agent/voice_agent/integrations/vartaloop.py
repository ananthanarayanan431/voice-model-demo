"""Vartaloop text-to-speech: POST /v1/tts, streamed back as Ogg/Opus.

https://docs.vartaloop.ai/api/tts/ - errors are decided before any audio is
sent, so a non-2xx status is the whole story and a 200 always carries audio.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from voice_agent.core.errors import NotConfiguredError, UpstreamError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from voice_agent.config.integrations import VartaloopSettings

OPUS_MEDIA_TYPE = "audio/ogg"


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
        request = self._client.build_request(
            "POST",
            f"{self._settings.VARTALOOP_API_URL}/v1/tts",
            headers={"x-api-key": key},
            json={"text": text, "voice": self._settings.VARTALOOP_VOICE, "format": "opus"},
            timeout=self._settings.VARTALOOP_TIMEOUT_SECONDS,
        )
        try:
            response = await self._client.send(request, stream=True)
        except httpx.HTTPError as exc:
            msg = "Could not reach Vartaloop."
            raise UpstreamError(msg) from exc
        if response.is_error:
            await response.aread()
            await response.aclose()
            msg = f"Vartaloop returned {response.status_code}: {response.text[:200]}"
            raise UpstreamError(msg)
        return SpeechStream(response)
