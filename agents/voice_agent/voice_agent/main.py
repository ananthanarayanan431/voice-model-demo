"""Uvicorn entry point: ``uvicorn voice_agent.main:app`` (``./run.sh`` adds reload)."""

from __future__ import annotations

from voice_agent.server import create_app

app = create_app()
