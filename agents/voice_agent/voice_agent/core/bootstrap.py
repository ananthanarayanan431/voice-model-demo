"""Composition root: builds the shared services once, at startup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from voice_agent.chat.llm import ChatModel, ClaudeChatModel
from voice_agent.config.paths import DATA_DIR
from voice_agent.integrations.vartaloop import VartaloopTTS
from voice_agent.services.clinic import ClinicStore
from voice_agent.services.conversation import ConversationService

if TYPE_CHECKING:
    import httpx

    from voice_agent.config import Settings

CLINIC_DATA_FILE = DATA_DIR / "sunrise_demo.json"


@dataclass
class Services:
    clinic: ClinicStore
    conversation: ConversationService
    tts: VartaloopTTS


def build_services(
    settings: Settings, http: httpx.AsyncClient, model: ChatModel | None = None
) -> Services:
    clinic = ClinicStore.from_file(CLINIC_DATA_FILE)
    conversation = ConversationService(
        model or ClaudeChatModel(settings.anthropic),
        clinic,
        timezone=settings.app.TIMEZONE,
        max_tool_rounds=settings.anthropic.MAX_TOOL_ROUNDS,
    )
    return Services(clinic, conversation, VartaloopTTS(settings.vartaloop, http))
