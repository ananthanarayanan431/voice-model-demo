"""The tools Claude can call, and the code that runs them against the clinic.

Each tool returns a JSON string. A ``ClinicError`` becomes an error result the
model reads and explains to the patient, instead of failing the turn.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, time
from typing import TYPE_CHECKING, Any

from voice_agent.core.errors import ClinicError

if TYPE_CHECKING:
    from anthropic.types.beta import BetaToolParam

    from voice_agent.models import Appointment
    from voice_agent.services.clinic import ClinicStore


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_PHONE = {"type": "string", "description": "The patient's 10-digit mobile number."}
_DATE = {"type": "string", "description": "Date as YYYY-MM-DD."}

TOOLS: list[BetaToolParam] = [
    {
        "name": "list_doctors",
        "description": (
            "List the hospital's doctors with their specialty and in-house days and hours. "
            "Pass a specialty (e.g. 'ortho', 'cardio') to filter, or an empty string for all."
        ),
        "input_schema": _schema({"specialty": {"type": "string"}}, ["specialty"]),
        "strict": True,
    },
    {
        "name": "find_slots",
        "description": "Free appointment times for one doctor on one date.",
        "input_schema": _schema(
            {"doctor_id": {"type": "string"}, "date": _DATE}, ["doctor_id", "date"]
        ),
        "strict": True,
    },
    {
        "name": "book_appointment",
        "description": (
            "Book a slot. Only call after the patient has confirmed the doctor, date, time, "
            "their name and their phone number."
        ),
        "input_schema": _schema(
            {
                "doctor_id": {"type": "string"},
                "date": _DATE,
                "time": {"type": "string", "description": "Start time as HH:MM, 24-hour."},
                "patient_name": {"type": "string"},
                "phone": _PHONE,
            },
            ["doctor_id", "date", "time", "patient_name", "phone"],
        ),
        "strict": True,
    },
    {
        "name": "get_prescription",
        "description": "The medicines currently prescribed to the patient with this phone number.",
        "input_schema": _schema({"phone": _PHONE}, ["phone"]),
        "strict": True,
    },
    {
        "name": "request_refill",
        "description": "Ask the pharmacy to refill one prescribed medicine. Uses one refill.",
        "input_schema": _schema(
            {"phone": _PHONE, "medicine": {"type": "string"}}, ["phone", "medicine"]
        ),
        "strict": True,
    },
]


@dataclass
class ToolOutcome:
    content: str
    is_error: bool = False
    appointment: Appointment | None = None


@dataclass
class ClinicTools:
    store: ClinicStore
    today: date
    booked: list[Appointment] = field(default_factory=list[Any])

    def run(self, name: str, args: dict[str, Any]) -> ToolOutcome:
        try:
            outcome = self._dispatch(name, args)
        except ClinicError as exc:
            return ToolOutcome(json.dumps({"error": exc.message}), is_error=True)
        except (KeyError, ValueError) as exc:
            return ToolOutcome(json.dumps({"error": f"Invalid input: {exc}"}), is_error=True)
        if outcome.appointment is not None:
            self.booked.append(outcome.appointment)
        return outcome

    def _dispatch(self, name: str, args: dict[str, Any]) -> ToolOutcome:
        if name == "list_doctors":
            doctors = self.store.doctors(str(args.get("specialty", "")))
            return ToolOutcome(
                json.dumps([d.model_dump(mode="json") for d in doctors], ensure_ascii=False)
            )
        if name == "find_slots":
            slots = self.store.open_slots(
                str(args["doctor_id"]), date.fromisoformat(str(args["date"])), self.today
            )
            listed = [f"{s:%H:%M}" for s in slots[:8]]
            return ToolOutcome(json.dumps({"free": listed, "more": len(slots) > len(listed)}))
        if name == "book_appointment":
            appointment = self.store.book(
                str(args["doctor_id"]),
                date.fromisoformat(str(args["date"])),
                time.fromisoformat(str(args["time"])),
                str(args["patient_name"]),
                str(args["phone"]),
                self.today,
            )
            return ToolOutcome(appointment.model_dump_json(), appointment=appointment)
        if name == "get_prescription":
            patient = self.store.patient(str(args["phone"]))
            return ToolOutcome(patient.model_dump_json())
        if name == "request_refill":
            refill, medicine = self.store.request_refill(str(args["phone"]), str(args["medicine"]))
            return ToolOutcome(
                json.dumps(
                    {
                        "refill_id": refill.id,
                        "medicine": medicine.name,
                        "refills_left": medicine.refills_left,
                        "next_step": "The pharmacy will call the patient when it is ready.",
                    }
                )
            )
        msg = f"Unknown tool {name}"
        raise ClinicError(msg)
