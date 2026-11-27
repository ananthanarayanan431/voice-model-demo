"""Composition root: builds the shared services once, at startup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from voice_agent.chat.llm import ChatModel, ClaudeChatModel
from voice_agent.config.paths import DATA_DIR
from voice_agent.core.rate_limit import RateLimiter
from voice_agent.integrations.vartaloop import VartaloopTTS
from voice_agent.services.clinic import ClinicStore
from voice_agent.services.conversation import ConversationService
from voice_agent.services.speech import SpeechCache

if TYPE_CHECKING:
    import httpx

    from voice_agent.config import Settings

CLINIC_DATA_FILE = DATA_DIR / "sunrise_demo.json"


@dataclass
class Services:
    clinic: ClinicStore
    conversation: ConversationService
    tts: VartaloopTTS
    speech_cache: SpeechCache
    chat_limiter: RateLimiter


def build_services(
    settings: Settings, http: httpx.AsyncClient, model: ChatModel | None = None
) -> Services:
    app = settings.app
    clinic = ClinicStore.from_file(CLINIC_DATA_FILE)
    conversation = ConversationService(
        model or ClaudeChatModel(settings.anthropic),
        clinic,
        timezone=app.TIMEZONE,
        max_tool_rounds=settings.anthropic.MAX_TOOL_ROUNDS,
        session_ttl_seconds=app.SESSION_TTL_SECONDS,
        max_sessions=app.MAX_SESSIONS,
    )
    return Services(
        clinic=clinic,
        conversation=conversation,
        tts=VartaloopTTS(settings.vartaloop, http),
        speech_cache=SpeechCache(app.SPEECH_TTL_SECONDS),
        chat_limiter=RateLimiter(app.CHAT_RATE_LIMIT_PER_MINUTE),
    )
