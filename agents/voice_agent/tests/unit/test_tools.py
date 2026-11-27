"""Tool calls from Claude, run against the clinic."""

from __future__ import annotations

import json
from datetime import date

from tests.fakes import clinic
from voice_agent.chat.tools import TOOLS, ClinicTools

MONDAY = date(2026, 11, 30)


def test_every_tool_is_strict_with_a_closed_schema() -> None:
    for tool in TOOLS:
        assert tool.get("strict") is True
        assert tool["input_schema"].get("additionalProperties") is False


def test_find_slots_lists_at_most_eight_and_says_there_are_more() -> None:
    outcome = ClinicTools(clinic(), MONDAY).run(
        "find_slots", {"doctor_id": "dr-kavya-rao", "date": "2026-11-30"}
    )
    data = json.loads(outcome.content)
    assert data["free"][:2] == ["10:00", "10:20"]
    assert len(data["free"]) == 8
    assert data["more"] is True


def test_booking_is_recorded_on_the_tools() -> None:
    tools = ClinicTools(clinic(), MONDAY)
    outcome = tools.run(
        "book_appointment",
        {
            "doctor_id": "dr-kavya-rao",
            "date": "2026-11-30",
            "time": "11:00",
            "patient_name": "Asha",
            "phone": "9876543210",
        },
    )
    assert not outcome.is_error
    assert [a.id for a in tools.booked] == [json.loads(outcome.content)["id"]]


def test_clinic_errors_become_error_results_not_exceptions() -> None:
    outcome = ClinicTools(clinic(), MONDAY).run(
        "find_slots", {"doctor_id": "dr-kavya-rao", "date": "2026-12-02"}
    )
    assert outcome.is_error
    assert "Wednesday" in json.loads(outcome.content)["error"]


def test_malformed_date_is_an_error_result() -> None:
    outcome = ClinicTools(clinic(), MONDAY).run(
        "find_slots", {"doctor_id": "dr-kavya-rao", "date": "next monday"}
    )
    assert outcome.is_error


def test_unknown_tool_is_an_error_result() -> None:
    assert ClinicTools(clinic(), MONDAY).run("delete_records", {}).is_error


def test_prescription_and_refill() -> None:
    tools = ClinicTools(clinic(), MONDAY)
    patient = json.loads(tools.run("get_prescription", {"phone": "9123456780"}).content)
    assert patient["name"] == "Ravi Kumar"
    refill = json.loads(
        tools.run("request_refill", {"phone": "9123456780", "medicine": "pantoprazole"}).content
    )
    assert refill["refills_left"] == 0
