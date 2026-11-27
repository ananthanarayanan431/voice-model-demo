"""The hospital's sample schedule, bookings and prescriptions, kept in memory.

Bookings live for the life of the process: this is a demo store, not a record
system. Every method validates its input and raises ``ClinicError`` with a
message fit to read back to a patient.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta
from itertools import count
from typing import TYPE_CHECKING

from voice_agent.core.errors import ClinicError
from voice_agent.models import Appointment, ClinicData, Doctor, Medicine, Patient, RefillRequest

if TYPE_CHECKING:
    from pathlib import Path

BOOKING_WINDOW_DAYS = 14
MAX_SLOTS_LISTED = 8


def normalise_phone(phone: str) -> str:
    """The last 10 digits of an Indian mobile number, or ``ClinicError``."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) != 10:
        msg = "A phone number needs 10 digits."
        raise ClinicError(msg)
    return digits


class ClinicStore:
    def __init__(self, data: ClinicData) -> None:
        self._data = data
        self._doctors = {doctor.id: doctor for doctor in data.doctors}
        self._patients = {patient.phone: patient for patient in data.patients}
        self._appointments: list[Appointment] = []
        self._refills: list[RefillRequest] = []
        self._ids = count(1001)

    @classmethod
    def from_file(cls, path: Path) -> ClinicStore:
        return cls(ClinicData.model_validate(json.loads(path.read_text(encoding="utf-8"))))

    # --- doctors and slots -------------------------------------------------

    def doctors(self, specialty: str | None = None) -> list[Doctor]:
        if not specialty:
            return list(self._data.doctors)
        wanted = specialty.casefold()
        return [d for d in self._data.doctors if wanted in d.specialty.casefold()]

    def doctor(self, doctor_id: str) -> Doctor:
        doctor = self._doctors.get(doctor_id)
        if doctor is None:
            msg = f"There is no doctor with id {doctor_id}."
            raise ClinicError(msg)
        return doctor

    def open_slots(self, doctor_id: str, day: date, today: date) -> list[time]:
        doctor = self.doctor(doctor_id)
        self._check_bookable_day(doctor, day, today)
        taken = {a.start for a in self._appointments if a.doctor_id == doctor_id and a.day == day}
        step = timedelta(minutes=self._data.slot_minutes)
        slot = datetime.combine(day, doctor.start)
        end = datetime.combine(day, doctor.end)
        free: list[time] = []
        while slot + step <= end:
            if slot.time() not in taken:
                free.append(slot.time())
            slot += step
        return free

    def _check_bookable_day(self, doctor: Doctor, day: date, today: date) -> None:
        if day < today:
            msg = "That date has already passed."
            raise ClinicError(msg)
        if day > today + timedelta(days=BOOKING_WINDOW_DAYS):
            msg = f"Bookings open only {BOOKING_WINDOW_DAYS} days ahead."
            raise ClinicError(msg)
        if day.weekday() not in doctor.days:
            msg = f"{doctor.name} is not in the hospital on {day:%A}."
            raise ClinicError(msg)

    # --- appointments ------------------------------------------------------

    def book(
        self, doctor_id: str, day: date, start: time, patient_name: str, phone: str, today: date
    ) -> Appointment:
        doctor = self.doctor(doctor_id)
        if not patient_name.strip():
            msg = "The patient's name is needed to book."
            raise ClinicError(msg)
        phone = normalise_phone(phone)
        if start not in self.open_slots(doctor_id, day, today):
            msg = f"{start:%H:%M} on {day:%d %B} is not free for {doctor.name}."
            raise ClinicError(msg)
        appointment = Appointment(
            id=f"SH-{next(self._ids)}",
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            specialty=doctor.specialty,
            day=day,
            start=start,
            patient_name=patient_name.strip(),
            phone=phone,
        )
        self._appointments.append(appointment)
        return appointment

    def appointments(self, phone: str) -> list[Appointment]:
        phone = normalise_phone(phone)
        return [a for a in self._appointments if a.phone == phone]

    # --- prescriptions -----------------------------------------------------

    def patient(self, phone: str) -> Patient:
        patient = self._patients.get(normalise_phone(phone))
        if patient is None:
            msg = "No prescription is on file for that phone number."
            raise ClinicError(msg)
        return patient

    def request_refill(self, phone: str, medicine_name: str) -> tuple[RefillRequest, Medicine]:
        patient = self.patient(phone)
        wanted = medicine_name.casefold()
        medicine = next((m for m in patient.medicines if wanted in m.name.casefold()), None)
        if medicine is None:
            msg = f"{medicine_name} is not on this patient's prescription."
            raise ClinicError(msg)
        if medicine.refills_left <= 0:
            msg = f"No refills are left for {medicine.name}; the doctor has to renew it."
            raise ClinicError(msg)
        medicine.refills_left -= 1
        refill = RefillRequest(
            id=f"RX-{next(self._ids)}", phone=patient.phone, medicine=medicine.name
        )
        self._refills.append(refill)
        return refill, medicine
