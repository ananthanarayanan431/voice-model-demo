"""FastAPI dependencies: shared services from app state, the API-key gate and
the chat rate limit."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader

from voice_agent.config import Settings, get_settings
from voice_agent.core.errors import UnauthorizedError
from voice_agent.core.rate_limit import RateLimiter
from voice_agent.integrations.vartaloop import VartaloopTTS
from voice_agent.services.clinic import ClinicStore
from voice_agent.services.conversation import ConversationService
from voice_agent.services.speech import SpeechCache

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def settings_dep() -> Settings:
    return get_settings()


def conversation_dep(request: Request) -> ConversationService:
    service: ConversationService = request.app.state.conversation
    return service


def clinic_dep(request: Request) -> ClinicStore:
    store: ClinicStore = request.app.state.clinic
    return store


def tts_dep(request: Request) -> VartaloopTTS:
    tts: VartaloopTTS = request.app.state.tts
    return tts


def speech_cache_dep(request: Request) -> SpeechCache:
    cache: SpeechCache = request.app.state.speech_cache
    return cache


def require_api_key(
    settings: Annotated[Settings, Depends(settings_dep)],
    sent: Annotated[str | None, Security(_api_key_header)],
) -> None:
    """When API_KEY is set, every /api/v1 call must send it as X-API-Key."""
    expected = settings.app.API_KEY
    if expected is None or not expected.get_secret_value():
        return
    if sent is None or not secrets.compare_digest(sent, expected.get_secret_value()):
        raise UnauthorizedError


def chat_rate_limit(request: Request) -> None:
    limiter: RateLimiter = request.app.state.chat_limiter
    limiter.check(request.client.host if request.client else "unknown")
