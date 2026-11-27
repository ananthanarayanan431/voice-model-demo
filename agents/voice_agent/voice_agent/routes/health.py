"""Unversioned liveness and readiness checks."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from voice_agent.config import Settings
from voice_agent.core.dependencies import settings_dep, tts_dep
from voice_agent.integrations.vartaloop import VartaloopTTS
from voice_agent.schemas.health import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready")
async def ready(
    settings: Annotated[Settings, Depends(settings_dep)],
    tts: Annotated[VartaloopTTS, Depends(tts_dep)],
) -> ReadyResponse:
    return ReadyResponse(
        status="ok",
        tts_configured=tts.configured,
        llm_model=settings.anthropic.ANTHROPIC_LLM_MODEL,
    )
