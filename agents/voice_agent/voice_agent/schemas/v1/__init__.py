"""Request bodies and response ``data`` payloads for /api/v1."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field

from voice_agent.schemas.common import SessionId


class ChatRequest(BaseModel):
    session_id: SessionId
    message: str = Field(min_length=1, max_length=1000)


class ResetRequest(BaseModel):
    session_id: SessionId


class AppointmentOut(BaseModel):
    id: str
    doctor_name: str
    specialty: str
    day: date
    start: time
    patient_name: str


class ChatReply(BaseModel):
    reply: str
    appointments: list[AppointmentOut] = Field(description="Booked during this turn")
    audio_url: str | None = Field(
        description="Short-lived link to the spoken reply; null when speech is off"
    )


class ResetResult(BaseModel):
    session_id: str


class DoctorOut(BaseModel):
    id: str
    name: str
    specialty: str
    days: list[str]
    hours: str
