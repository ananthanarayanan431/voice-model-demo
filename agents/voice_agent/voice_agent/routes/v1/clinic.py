"""Read-only views of the sample hospital, for the web app's side panel."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from voice_agent.core.dependencies import clinic_dep
from voice_agent.core.responses import success
from voice_agent.schemas.common import SuccessResponse
from voice_agent.schemas.v1 import DoctorOut
from voice_agent.services.clinic import ClinicStore

router = APIRouter(tags=["clinic"])

_DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@router.get("/doctors")
async def doctors(
    request: Request, store: Annotated[ClinicStore, Depends(clinic_dep)]
) -> SuccessResponse[list[DoctorOut]]:
    roster = [
        DoctorOut(
            id=d.id,
            name=d.name,
            specialty=d.specialty,
            days=[_DAY_NAMES[i] for i in d.days],
            hours=f"{d.start:%H:%M}-{d.end:%H:%M}",
        )
        for d in store.doctors()
    ]
    return success(request, roster)
