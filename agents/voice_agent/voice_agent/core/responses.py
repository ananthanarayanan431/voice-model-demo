"""Builders for the response envelope, and the handlers that render every error
(ours, validation, routing, unexpected) in the same shape."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from voice_agent.core.errors import VoiceAgentError
from voice_agent.schemas.common import ErrorDetail, ErrorResponse, FieldError, SuccessResponse

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from fastapi import FastAPI, Request

_HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    429: "rate_limited",
}


def request_id_of(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) else str(uuid.uuid4())


def success[T](request: Request, data: T) -> SuccessResponse[T]:
    return SuccessResponse[T](data=data, request_id=request_id_of(request))


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    fields: list[FieldError] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, fields=fields or []),
        request_id=request_id_of(request),
    )
    return JSONResponse(
        body.model_dump(mode="json"),
        status_code=status_code,
        headers=dict(headers) if headers else None,
    )


async def _app_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, VoiceAgentError):
        return await _unexpected(request, exc)
    if exc.status_code >= 500:
        logger.warning("{} on {}: {}", exc.code, request.url.path, exc.message)
    return error_response(request, exc.status_code, exc.code, exc.message, headers=exc.headers)


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    errors: Sequence[Any] = exc.errors() if isinstance(exc, RequestValidationError) else []
    fields = [
        FieldError(field=".".join(str(part) for part in error["loc"]), message=error["msg"])
        for error in errors
    ]
    return error_response(request, 422, "validation_error", "The request is invalid.", fields)


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        return await _unexpected(request, exc)
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    return error_response(request, exc.status_code, code, str(exc.detail), headers=exc.headers)


async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.opt(exception=exc).error("Unhandled error on {} {}", request.method, request.url.path)
    return error_response(request, 500, "internal_error", VoiceAgentError.default_message)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(VoiceAgentError, _app_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)


async def unexpected_error_response(request: Request, exc: Exception) -> JSONResponse:
    """For the request-context middleware: errors no handler caught."""
    return await _unexpected(request, exc)
