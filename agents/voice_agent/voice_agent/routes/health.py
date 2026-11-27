"""Unversioned liveness and readiness checks."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from voice_agent.config import Settings
from voice_agent.core.dependencies import settings_dep, tts_dep
from voice_agent.core.responses import success
from voice_agent.integrations.vartaloop import VartaloopTTS
from voice_agent.schemas.common import SuccessResponse
from voice_agent.schemas.health import HealthStatus, ReadyStatus

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> SuccessResponse[HealthStatus]:
    """Liveness: the process is up."""
    return success(request, HealthStatus(status="ok"))


@router.get("/ready")
async def ready(
    request: Request,
    settings: Annotated[Settings, Depends(settings_dep)],
    tts: Annotated[VartaloopTTS, Depends(tts_dep)],
) -> SuccessResponse[ReadyStatus]:
    """Readiness, and which optional features are on (the web app reads this)."""
    status = ReadyStatus(
        status="ok",
        speech_enabled=tts.configured,
        llm_model=settings.anthropic.ANTHROPIC_LLM_MODEL,
    )
    return success(request, status)
