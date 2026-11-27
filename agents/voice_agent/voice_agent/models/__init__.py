"""Domain models for the hospital demo: doctors, appointments, prescriptions."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel


class Doctor(BaseModel):
    id: str
    name: str
    specialty: str
    # Weekdays the doctor is in-house: Monday is 0.
    days: list[int]
    start: time
    end: time


class Medicine(BaseModel):
    name: str
    dose: str
    timing: str
    instructions: str
    refills_left: int


class Patient(BaseModel):
    phone: str
    name: str
    medicines: list[Medicine]


class Appointment(BaseModel):
    id: str
    doctor_id: str
    doctor_name: str
    specialty: str
    day: date
    start: time
    patient_name: str
    phone: str


class RefillRequest(BaseModel):
    id: str
    phone: str
    medicine: str


class ClinicData(BaseModel):
    slot_minutes: int
    doctors: list[Doctor]
    patients: list[Patient]
