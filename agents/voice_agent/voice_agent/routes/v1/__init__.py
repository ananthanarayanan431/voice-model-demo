"""Every /api/v1 route. All but the audio links sit behind the API-key gate."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from voice_agent.config import API_V1_PREFIX
from voice_agent.core.dependencies import require_api_key
from voice_agent.routes.v1 import clinic, voice
from voice_agent.schemas.common import ERROR_RESPONSES

router = APIRouter(
    prefix=API_V1_PREFIX, dependencies=[Depends(require_api_key)], responses=ERROR_RESPONSES
)
router.include_router(voice.router)
router.include_router(clinic.router)

speech_router = voice.speech_router
