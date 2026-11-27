"""Request context: an id on every request, response and log line; one timing
log per request; CORS. Errors no handler caught are rendered here, so even a
crash returns the envelope with its request id."""

from __future__ import annotations

import re
import time
import uuid
from typing import TYPE_CHECKING

from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from voice_agent.core.responses import unexpected_error_response

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import FastAPI, Request, Response

    from voice_agent.config.app import AppSettings

REQUEST_ID_HEADER = "X-Request-ID"
# Reuse an upstream id (load balancer, nginx) only if it is safe to log and echo.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming if _SAFE_REQUEST_ID.match(incoming) else str(uuid.uuid4())
    request.state.request_id = request_id

    with logger.contextualize(request_id=request_id):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 - last boundary: render the envelope, logged inside
            response = await unexpected_error_response(request, exc)
        # Path only: query strings never reach the logs.
        logger.info(
            "{} {} -> {} in {:.0f}ms",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - start) * 1000,
        )
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


def install_middleware(app: FastAPI, settings: AppSettings) -> None:
    if origins := settings.cors_origins():
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "X-API-Key", REQUEST_ID_HEADER],
            expose_headers=[REQUEST_ID_HEADER],
        )
    app.middleware("http")(request_context_middleware)
