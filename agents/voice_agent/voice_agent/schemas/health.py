"""Health and readiness payloads."""

from __future__ import annotations

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str


class ReadyStatus(BaseModel):
    status: str
    speech_enabled: bool
    llm_model: str
