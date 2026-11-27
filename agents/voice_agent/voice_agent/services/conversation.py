"""One patient turn: send the transcript to Claude, run its tool calls, return
the reply to speak. Conversations live in memory per session id and are
forgotten after ``SESSION_TTL_SECONDS`` idle."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast
from zoneinfo import ZoneInfo

from loguru import logger

from voice_agent.chat.tools import TOOLS, ClinicTools
from voice_agent.prompts.base import system_prompt

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from anthropic.types.beta import (
        BetaContentBlockParam,
        BetaMessageParam,
        BetaToolResultBlockParam,
    )

    from voice_agent.chat.llm import ChatModel
    from voice_agent.models import Appointment
    from voice_agent.services.clinic import ClinicStore

FALLBACK_REPLY = "Sorry, I could not finish that just now. Could you say it again?"
REFUSAL_REPLY = "I can't help with that on this line. The front desk will call you back."


@dataclass
class TurnResult:
    reply: str
    appointments: list[Appointment] = field(default_factory=list[Any])


@dataclass
class _Session:
    messages: list[BetaMessageParam] = field(default_factory=list[Any])
    last_used: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class ConversationService:
    def __init__(
        self,
        model: ChatModel,
        store: ClinicStore,
        *,
        timezone: str,
        max_tool_rounds: int,
        session_ttl_seconds: float,
        max_sessions: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._model = model
        self._store = store
        self._zone = ZoneInfo(timezone)
        self._max_rounds = max_tool_rounds
        self._ttl = session_ttl_seconds
        self._max_sessions = max_sessions
        self._clock = clock
        self._sessions: OrderedDict[str, _Session] = OrderedDict()

    def today(self) -> date:
        return datetime.now(self._zone).date()

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def reply(self, session_id: str, text: str) -> TurnResult:
        session = self._session(session_id)
        async with session.lock:
            return await self._turn(session_id, session, text)

    async def _turn(self, session_id: str, session: _Session, text: str) -> TurnResult:
        # Work on a copy: a failed turn must not leave half a tool exchange behind.
        messages: list[BetaMessageParam] = [*session.messages, {"role": "user", "content": text}]
        today = self.today()
        tools = ClinicTools(self._store, today)
        system = system_prompt(today)

        for _ in range(self._max_rounds):
            response = await self._model.create(system, messages, TOOLS)
            # Append the full content, thinking blocks included, unchanged.
            content = cast("list[BetaContentBlockParam]", response.content)
            messages.append({"role": "assistant", "content": content})

            if response.stop_reason == "refusal":
                logger.info("Turn declined for session {}", session_id)
                return TurnResult(REFUSAL_REPLY)
            if response.stop_reason != "tool_use":
                reply = " ".join(b.text for b in response.content if b.type == "text").strip()
                session.messages = messages
                return TurnResult(reply or FALLBACK_REPLY, list(tools.booked))

            results: list[BetaToolResultBlockParam] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                outcome = tools.run(block.name, cast("dict[str, Any]", block.input))
                logger.info("Tool {} error={}", block.name, outcome.is_error)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": outcome.content,
                        "is_error": outcome.is_error,
                    }
                )
            messages.append({"role": "user", "content": results})

        logger.warning("Tool round limit reached for session {}", session_id)
        session.messages = messages
        return TurnResult(FALLBACK_REPLY, list(tools.booked))

    def _session(self, session_id: str) -> _Session:
        now = self._clock()
        self._expire(now)
        session = self._sessions.get(session_id)
        if session is None:
            session = _Session()
            self._sessions[session_id] = session
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)
        else:
            self._sessions.move_to_end(session_id)
        session.last_used = now
        return session

    def _expire(self, now: float) -> None:
        # Sessions are kept in last-used order, so the idle ones are at the front.
        while self._sessions:
            oldest_id, oldest = next(iter(self._sessions.items()))
            if now - oldest.last_used < self._ttl or oldest.lock.locked():
                break
            del self._sessions[oldest_id]
