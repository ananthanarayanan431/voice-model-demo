"""The one call the agent makes to Claude, behind a protocol so tests can fake it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import anthropic

from voice_agent.core.errors import NotConfiguredError, UpstreamError

if TYPE_CHECKING:
    from anthropic.types.beta import BetaMessage, BetaMessageParam, BetaToolParam

    from voice_agent.config.llm import AnthropicSettings


class ChatModel(Protocol):
    async def create(
        self, system: str, messages: list[BetaMessageParam], tools: list[BetaToolParam]
    ) -> BetaMessage: ...


class ClaudeChatModel:
    """Claude through the Anthropic SDK. The client is built on first use, so the
    app starts (and /health answers) without a key."""

    def __init__(self, settings: AnthropicSettings) -> None:
        self._settings = settings
        self._client: anthropic.AsyncAnthropic | None = None

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            key = self._settings.ANTHROPIC_API_KEY
            self._client = anthropic.AsyncAnthropic(
                api_key=key.get_secret_value() if key else None,
                timeout=self._settings.ANTHROPIC_TIMEOUT_SECONDS,
            )
        return self._client

    async def create(
        self, system: str, messages: list[BetaMessageParam], tools: list[BetaToolParam]
    ) -> BetaMessage:
        try:
            return await self._get_client().beta.messages.create(
                model=self._settings.ANTHROPIC_LLM_MODEL,
                max_tokens=self._settings.ANTHROPIC_MAX_TOKENS,
                system=system,
                messages=messages,
                tools=tools,
                output_config={"effort": self._settings.ANTHROPIC_EFFORT},
                # On a policy decline, re-run the request on the model's default
                # fallback; a model without fallbacks simply runs alone.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except TypeError as exc:
            # The SDK raises a plain TypeError when it finds no credentials at all.
            if "authentication" not in str(exc):
                raise
            msg = "No Anthropic credentials: set ANTHROPIC_API_KEY in agents/voice_agent/.env."
            raise NotConfiguredError(msg) from exc
        except anthropic.AuthenticationError as exc:
            msg = "Claude rejected the API key. Check ANTHROPIC_API_KEY in agents/voice_agent/.env."
            raise UpstreamError(msg) from exc
        except anthropic.RateLimitError as exc:
            msg = "Claude is rate limiting requests; try again in a moment."
            raise UpstreamError(msg) from exc
        except anthropic.APIStatusError as exc:
            msg = f"Claude returned an error ({exc.status_code})."
            raise UpstreamError(msg) from exc
        except anthropic.APIConnectionError as exc:
            msg = "Could not reach Claude."
            raise UpstreamError(msg) from exc
