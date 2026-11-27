"""The response envelope every JSON endpoint returns.

Success: ``{"success": true, "data": ..., "request_id": "..."}``
Failure: ``{"success": false, "error": {"code", "message", "fields"}, "request_id": "..."}``
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

# Restricted alphabet: session ids are dictionary keys and appear in logs.
SessionId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{8,64}$")]


class SuccessResponse[T](BaseModel):
    success: Literal[True] = True
    data: T
    request_id: str


class FieldError(BaseModel):
    field: str = Field(description="Dotted location of the invalid input, e.g. body.message")
    message: str


class ErrorDetail(BaseModel):
    code: str = Field(description="Stable machine-readable code, e.g. rate_limited")
    message: str = Field(description="Human-readable, safe to show to a user")
    fields: list[FieldError] = Field(default_factory=list[FieldError])


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail
    request_id: str


ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    status: {"model": ErrorResponse, "description": description}
    for status, description in (
        (401, "Missing or invalid API key"),
        (404, "Not found, or an expired audio link"),
        (422, "Invalid input"),
        (429, "Rate limited"),
        (500, "Unexpected error"),
        (502, "Claude or Vartaloop failed"),
        (503, "A required key is not configured"),
    )
}
