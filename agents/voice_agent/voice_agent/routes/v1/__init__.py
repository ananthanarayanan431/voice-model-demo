"""Every /api/v1 route, behind the optional API-key gate."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from voice_agent.config import API_V1_PREFIX
from voice_agent.core.dependencies import require_api_key
from voice_agent.routes.v1 import clinic, voice

router = APIRouter(prefix=API_V1_PREFIX, dependencies=[Depends(require_api_key)])
router.include_router(voice.router)
router.include_router(clinic.router)
