"""The sample clinic: open slots, booking rules and prescriptions."""

from __future__ import annotations

from datetime import date, time

import pytest

from tests.fakes import clinic
from voice_agent.core.errors import ClinicError
from voice_agent.services.clinic import normalise_phone

# A Monday: Dr. Kavya Rao (orthopaedics) is in 10:00-16:00 on Mon/Tue/Thu/Fri.
MONDAY = date(2026, 11, 30)
ORTHO = "dr-kavya-rao"


def test_slots_cover_the_doctors_hours_in_20_minute_steps() -> None:
    slots = clinic().open_slots(ORTHO, MONDAY, today=MONDAY)
    assert slots[0] == time(10, 0)
    assert slots[1] == time(10, 20)
    assert slots[-1] == time(15, 40)
    assert len(slots) == 18


def test_booking_takes_the_slot_and_returns_an_id() -> None:
    store = clinic()
    appointment = store.book(ORTHO, MONDAY, time(11, 0), "Asha", "+91 98765 43210", today=MONDAY)
    assert appointment.id.startswith("SH-")
    assert appointment.phone == "9876543210"
    assert time(11, 0) not in store.open_slots(ORTHO, MONDAY, today=MONDAY)
    assert store.appointments("9876543210") == [appointment]


def test_a_slot_cannot_be_booked_twice() -> None:
    store = clinic()
    store.book(ORTHO, MONDAY, time(11, 0), "Asha", "9876543210", today=MONDAY)
    with pytest.raises(ClinicError, match="not free"):
        store.book(ORTHO, MONDAY, time(11, 0), "Ravi", "9123456780", today=MONDAY)


@pytest.mark.parametrize(
    ("day", "message"),
    [
        (date(2026, 11, 29), "already passed"),
        (date(2027, 1, 4), "14 days"),
        (date(2026, 12, 2), "not in the hospital on Wednesday"),
    ],
)
def test_days_outside_the_rules_are_refused(day: date, message: str) -> None:
    with pytest.raises(ClinicError, match=message):
        clinic().open_slots(ORTHO, day, today=MONDAY)


def test_unknown_doctor_is_refused() -> None:
    with pytest.raises(ClinicError, match="no doctor"):
        clinic().doctor("dr-nobody")


def test_specialty_filter_is_case_insensitive_and_partial() -> None:
    names = [d.name for d in clinic().doctors("cardio")]
    assert names == ["Dr. Vikram Reddy"]


@pytest.mark.parametrize("raw", ["98765 43210", "+91-9876543210", "919876543210"])
def test_phone_numbers_normalise_to_ten_digits(raw: str) -> None:
    assert normalise_phone(raw) == "9876543210"


def test_short_phone_number_is_refused() -> None:
    with pytest.raises(ClinicError, match="10 digits"):
        normalise_phone("12345")


def test_refill_uses_one_refill_and_stops_at_zero() -> None:
    store = clinic()
    refill, medicine = store.request_refill("9876543210", "metformin")
    assert refill.medicine == "Metformin 500 mg"
    assert medicine.refills_left == 1
    with pytest.raises(ClinicError, match="No refills"):
        store.request_refill("9876543210", "amlodipine")


def test_unknown_patient_has_no_prescription() -> None:
    with pytest.raises(ClinicError, match="No prescription"):
        clinic().patient("9000000000")
