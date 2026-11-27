"""Request and response bodies for /api/v1."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    message: str = Field(min_length=1, max_length=1000)


class AppointmentOut(BaseModel):
    id: str
    doctor_name: str
    specialty: str
    day: date
    start: time
    patient_name: str


class ChatResponse(BaseModel):
    reply: str
    appointments: list[AppointmentOut]


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class DoctorOut(BaseModel):
    id: str
    name: str
    specialty: str
    days: list[str]
    hours: str
