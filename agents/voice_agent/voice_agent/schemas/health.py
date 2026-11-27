"""Health and readiness bodies."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    tts_configured: bool
    llm_model: str
