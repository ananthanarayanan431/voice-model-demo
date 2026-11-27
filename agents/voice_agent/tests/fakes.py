"""Test doubles: a scripted Claude and helpers to build its responses."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

from anthropic.types.beta import BetaMessage, BetaTextBlock, BetaToolUseBlock

from voice_agent.config.paths import DATA_DIR
from voice_agent.services.clinic import ClinicStore

if TYPE_CHECKING:
    from anthropic.types.beta import BetaMessageParam, BetaToolParam

CLINIC_FILE = DATA_DIR / "sunrise_demo.json"


def clinic() -> ClinicStore:
    return ClinicStore.from_file(CLINIC_FILE)


def text_reply(text: str, stop_reason: str = "end_turn") -> BetaMessage:
    return BetaMessage.model_construct(
        content=[BetaTextBlock.model_construct(type="text", text=text)],
        stop_reason=stop_reason,
    )


def tool_call(name: str, args: dict[str, Any], call_id: str = "toolu_1") -> BetaMessage:
    return BetaMessage.model_construct(
        content=[
            BetaToolUseBlock.model_construct(type="tool_use", id=call_id, name=name, input=args)
        ],
        stop_reason="tool_use",
    )


class ScriptedChatModel:
    """Returns the scripted responses in order and records what it was sent."""

    def __init__(self, *responses: BetaMessage) -> None:
        self._responses = list(responses)
        self.calls: list[list[BetaMessageParam]] = []

    def add(self, *responses: BetaMessage) -> None:
        self._responses.extend(responses)

    async def create(
        self, system: str, messages: list[BetaMessageParam], tools: list[BetaToolParam]
    ) -> BetaMessage:
        del system, tools
        self.calls.append(copy.deepcopy(messages))
        if not self._responses:
            msg = "ScriptedChatModel ran out of responses"
            raise AssertionError(msg)
        return self._responses.pop(0)
