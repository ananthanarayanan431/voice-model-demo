"""Logging: loguru everywhere, configured once at start-up.

Log with arguments, never f-strings: ``logger.info("Booked {}", booking_id)``.
Never log secrets, prompts, transcripts or replies: they carry patient data.
Standard ``logging`` records (uvicorn, httpx) are routed into loguru so every
line shares one format; ``LOG_JSON`` switches to one JSON object per line.
"""

from __future__ import annotations

import inspect
import logging
import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Record

    from voice_agent.config.app import AppSettings

_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
)
_QUIET_LOGGERS = ("httpx", "httpcore", "anthropic")


def _format(record: Record) -> str:
    extra = " | {extra}" if record["extra"] else ""
    return _FORMAT + extra + "\n{exception}"


class InterceptHandler(logging.Handler):
    """Forward stdlib ``logging`` records to loguru, keeping the caller's location."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(settings: AppSettings) -> None:
    """Configure the process-wide logger. Safe to call more than once."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        serialize=settings.LOG_JSON,
        format=_format,
        colorize=not settings.LOG_JSON,
        # Variable values in tracebacks can include secrets and patient data.
        backtrace=not settings.is_production,
        diagnose=not settings.is_production,
        enqueue=True,
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    # The request-context middleware logs each request once, without its query string.
    logging.getLogger("uvicorn.access").disabled = True
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
