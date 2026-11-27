"""App factory and lifespan: shared resources are built once and torn down here."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import httpx
from fastapi import FastAPI
from loguru import logger

from voice_agent.config import get_settings
from voice_agent.core.bootstrap import build_services
from voice_agent.core.logs import configure_logging
from voice_agent.core.request_context import install_middleware
from voice_agent.core.responses import install_error_handlers
from voice_agent.routes import health
from voice_agent.routes.v1 import router as v1_router
from voice_agent.routes.v1 import speech_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from voice_agent.chat.llm import ChatModel


def create_app(model: ChatModel | None = None, http: httpx.AsyncClient | None = None) -> FastAPI:
    """``model`` and ``http`` let tests swap Claude and Vartaloop for fakes."""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        configure_logging(settings.app)
        client = http or httpx.AsyncClient()
        services = build_services(settings, client, model)
        app.state.clinic = services.clinic
        app.state.conversation = services.conversation
        app.state.tts = services.tts
        app.state.speech_cache = services.speech_cache
        app.state.chat_limiter = services.chat_limiter
        logger.info(
            "Started {} ({}); speech {}",
            settings.app.PROJECT_NAME,
            settings.app.ENVIRONMENT,
            "on" if services.tts.configured else "off",
        )
        try:
            yield
        finally:
            if http is None:
                await client.aclose()

    # Interactive docs only outside production.
    docs = not settings.app.is_production
    app = FastAPI(
        title=settings.app.PROJECT_NAME,
        version=settings.app.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    install_error_handlers(app)
    install_middleware(app, settings.app)
    app.include_router(health.router)
    app.include_router(v1_router)
    app.include_router(speech_router)
    return app
