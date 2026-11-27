"""FastAPI dependencies: shared services from app state, and the API-key gate."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from voice_agent.config import Settings, get_settings
from voice_agent.integrations.vartaloop import VartaloopTTS
from voice_agent.services.clinic import ClinicStore
from voice_agent.services.conversation import ConversationService

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


def require_api_key(
    settings: Annotated[Settings, Depends(settings_dep)],
    sent: Annotated[str | None, Security(_api_key_header)],
) -> None:
    """When API_KEY is set, every /api/v1 call must send it as X-API-Key."""
    expected = settings.app.API_KEY
    if expected is None or not expected.get_secret_value():
        return
    if sent is None or not secrets.compare_digest(sent, expected.get_secret_value()):
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")
