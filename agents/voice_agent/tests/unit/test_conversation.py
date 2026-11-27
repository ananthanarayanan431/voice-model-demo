"""The conversation loop: tool rounds, memory per session, refusals, limits."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from tests.fakes import ScriptedChatModel, clinic, text_reply, tool_call
from voice_agent.services.conversation import (
    FALLBACK_REPLY,
    REFUSAL_REPLY,
    ConversationService,
)

MONDAY = date(2026, 11, 30)


def service(model: ScriptedChatModel, max_rounds: int = 6) -> ConversationService:
    svc = ConversationService(model, clinic(), timezone="Asia/Kolkata", max_tool_rounds=max_rounds)
    svc.today = lambda: MONDAY  # type: ignore[method-assign]
    return svc


async def test_plain_reply_is_returned_and_remembered() -> None:
    model = ScriptedChatModel(text_reply("Namaste! How can I help?"), text_reply("Sure."))
    svc = service(model)
    first = await svc.reply("session-1", "Hello")
    assert first.reply == "Namaste! How can I help?"
    await svc.reply("session-1", "Book me in")
    # The second call carries the first exchange.
    sent: list[Any] = list(model.calls[1])
    assert [m["role"] for m in sent] == ["user", "assistant", "user"]
    assert sent[0]["content"] == "Hello"


async def test_tool_round_trip_books_and_reports_the_appointment() -> None:
    booking = {
        "doctor_id": "dr-kavya-rao",
        "date": "2026-11-30",
        "time": "11:00",
        "patient_name": "Asha",
        "phone": "9876543210",
    }
    model = ScriptedChatModel(
        tool_call("book_appointment", booking), text_reply("Booked for eleven.")
    )
    result = await service(model).reply("session-1", "Yes, book it")
    assert result.reply == "Booked for eleven."
    assert [a.doctor_name for a in result.appointments] == ["Dr. Kavya Rao"]
    last: Any = model.calls[1][-1]
    tool_result = last["content"][0]
    assert tool_result["type"] == "tool_result"
    assert tool_result["tool_use_id"] == "toolu_1"
    assert tool_result["is_error"] is False


async def test_sessions_are_separate() -> None:
    model = ScriptedChatModel(text_reply("one"), text_reply("two"))
    svc = service(model)
    await svc.reply("session-a", "first")
    await svc.reply("session-b", "second")
    assert len(model.calls[1]) == 1


async def test_reset_forgets_the_conversation() -> None:
    model = ScriptedChatModel(text_reply("one"), text_reply("two"))
    svc = service(model)
    await svc.reply("session-1", "first")
    svc.reset("session-1")
    await svc.reply("session-1", "again")
    assert len(model.calls[1]) == 1


async def test_refusal_gets_a_safe_reply_and_is_not_kept() -> None:
    model = ScriptedChatModel(text_reply("", stop_reason="refusal"), text_reply("ok"))
    svc = service(model)
    assert (await svc.reply("session-1", "something")).reply == REFUSAL_REPLY
    await svc.reply("session-1", "next")
    assert len(model.calls[1]) == 1


async def test_endless_tool_calls_stop_at_the_round_limit() -> None:
    call = tool_call("list_doctors", {"specialty": ""})
    model = ScriptedChatModel(call, call)
    result = await service(model, max_rounds=2).reply("session-1", "loop")
    assert result.reply == FALLBACK_REPLY
    assert len(model.calls) == 2


async def test_empty_text_reply_falls_back() -> None:
    model = ScriptedChatModel(text_reply("   "))
    assert (await service(model).reply("session-1", "hm")).reply == FALLBACK_REPLY


@pytest.mark.parametrize("phrase", ["108", "National Highway 65", "Devanagari"])
def test_system_prompt_carries_the_safety_and_language_rules(phrase: str) -> None:
    from voice_agent.prompts.base import system_prompt

    assert phrase in system_prompt(MONDAY)
    assert "Monday, 30 November 2026" in system_prompt(MONDAY)
