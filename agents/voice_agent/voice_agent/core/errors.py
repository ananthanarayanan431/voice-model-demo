"""Application errors. Each carries its HTTP status and a stable ``code`` the
client can branch on; ``core.responses`` renders them as the error envelope."""

from __future__ import annotations

from typing import ClassVar


class VoiceAgentError(Exception):
    status_code: ClassVar[int] = 500
    code: ClassVar[str] = "internal_error"
    default_message: ClassVar[str] = "Something went wrong. Please try again."

    def __init__(
        self, message: str | None = None, *, headers: dict[str, str] | None = None
    ) -> None:
        self.message = message or self.default_message
        self.headers = headers or {}
        super().__init__(self.message)


class UnauthorizedError(VoiceAgentError):
    status_code = 401
    code = "unauthorized"
    default_message = "Missing or invalid X-API-Key."


class NotFoundError(VoiceAgentError):
    status_code = 404
    code = "not_found"
    default_message = "Not found."


class RateLimitedError(VoiceAgentError):
    status_code = 429
    code = "rate_limited"
    default_message = "Too many requests. Please wait a moment and try again."


class UpstreamError(VoiceAgentError):
    """A third-party service (Claude, Vartaloop) failed."""

    status_code = 502
    code = "upstream_error"
    default_message = "A service the assistant depends on failed. Please try again."


class NotConfiguredError(VoiceAgentError):
    """A required key is missing, so the feature cannot run."""

    status_code = 503
    code = "not_configured"
    default_message = "This feature is not configured on the server."


class ClinicError(VoiceAgentError):
    """A booking or prescription request the clinic cannot fulfil. Raised inside
    tools, where it becomes an error result Claude explains to the patient."""

    status_code = 422
    code = "clinic_rule"
