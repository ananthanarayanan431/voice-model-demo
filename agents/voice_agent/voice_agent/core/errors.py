"""Errors the agent raises, and the handlers that render them as JSON."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import FastAPI, Request


class VoiceAgentError(Exception):
    """Base class: ``status_code`` decides the HTTP status it renders as."""

    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotConfiguredError(VoiceAgentError):
    """A required key is missing, so the feature cannot run."""

    status_code = 503


class UpstreamError(VoiceAgentError):
    """A third-party service (Claude, Vartaloop) failed."""

    status_code = 502


class ClinicError(VoiceAgentError):
    """A booking or prescription request the clinic cannot fulfil."""

    status_code = 400


def register_error_handlers(app: FastAPI) -> None:
    async def handle(_request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, VoiceAgentError):
            return JSONResponse({"detail": exc.message}, status_code=exc.status_code)
        return JSONResponse({"detail": "Internal error"}, status_code=500)

    app.add_exception_handler(VoiceAgentError, handle)
