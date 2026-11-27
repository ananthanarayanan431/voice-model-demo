"""The Claude adapter turns SDK failures into errors the API can render."""

from __future__ import annotations

from typing import Any

import pytest

from voice_agent.chat.llm import ClaudeChatModel
from voice_agent.config.llm import AnthropicSettings
from voice_agent.core.errors import NotConfiguredError


class _RaisingMessages:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def create(self, **_kwargs: Any) -> Any:
        raise self._exc


class _FakeClient:
    def __init__(self, exc: Exception) -> None:
        self.beta = type("Beta", (), {"messages": _RaisingMessages(exc)})()


def model_raising(exc: Exception) -> ClaudeChatModel:
    model = ClaudeChatModel(AnthropicSettings())
    model._client = _FakeClient(exc)  # type: ignore[assignment]  # pyright: ignore[reportPrivateUsage]
    return model


async def test_missing_credentials_become_a_not_configured_error() -> None:
    sdk_error = TypeError("Could not resolve authentication method. Expected one of api_key")
    with pytest.raises(NotConfiguredError, match="ANTHROPIC_API_KEY"):
        await model_raising(sdk_error).create("system", [], [])


async def test_other_type_errors_are_not_hidden() -> None:
    with pytest.raises(TypeError, match="unexpected keyword"):
        await model_raising(TypeError("unexpected keyword argument")).create("system", [], [])
