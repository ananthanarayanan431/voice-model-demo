"""App factory and lifespan."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voice_agent.config import get_settings
from voice_agent.core.bootstrap import build_services
from voice_agent.core.errors import register_error_handlers
from voice_agent.routes import health
from voice_agent.routes.v1 import router as v1_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from voice_agent.chat.llm import ChatModel


def create_app(model: ChatModel | None = None, http: httpx.AsyncClient | None = None) -> FastAPI:
    """``model`` and ``http`` let tests swap Claude and Vartaloop for fakes."""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        client = http or httpx.AsyncClient()
        services = build_services(settings, client, model)
        app.state.clinic = services.clinic
        app.state.conversation = services.conversation
        app.state.tts = services.tts
        try:
            yield
        finally:
            if http is None:
                await client.aclose()

    app = FastAPI(
        title=settings.app.PROJECT_NAME, version=settings.app.APP_VERSION, lifespan=lifespan
    )
    register_error_handlers(app)
    if origins := settings.app.cors_origins():
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "X-API-Key"],
        )
    app.include_router(health.router)
    app.include_router(v1_router)
    return app
