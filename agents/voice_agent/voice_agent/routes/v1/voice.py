"""The voice loop: a patient turn in, the reply text out, and its audio."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from voice_agent.config import Settings
from voice_agent.core.dependencies import conversation_dep, settings_dep, tts_dep
from voice_agent.integrations.vartaloop import OPUS_MEDIA_TYPE, VartaloopTTS
from voice_agent.schemas.v1 import AppointmentOut, ChatRequest, ChatResponse, ResetRequest
from voice_agent.services.conversation import ConversationService

router = APIRouter(tags=["voice"])


@router.post("/chat")
async def chat(
    body: ChatRequest,
    conversation: Annotated[ConversationService, Depends(conversation_dep)],
) -> ChatResponse:
    """One patient turn: the final transcript in, the assistant's reply out."""
    result = await conversation.reply(body.session_id, body.message.strip())
    return ChatResponse(
        reply=result.reply,
        appointments=[
            AppointmentOut.model_validate(a, from_attributes=True) for a in result.appointments
        ],
    )


@router.post("/chat/reset", status_code=204)
async def reset(
    body: ResetRequest,
    conversation: Annotated[ConversationService, Depends(conversation_dep)],
) -> None:
    """Forget a conversation (the "New call" button)."""
    conversation.reset(body.session_id)


@router.get(
    "/tts",
    response_class=StreamingResponse,
    responses={200: {"content": {OPUS_MEDIA_TYPE: {}}, "description": "Ogg/Opus audio"}},
)
async def tts(
    text: Annotated[str, Query(min_length=1, max_length=2000)],
    tts: Annotated[VartaloopTTS, Depends(tts_dep)],
    settings: Annotated[Settings, Depends(settings_dep)],
) -> StreamingResponse:
    """Speak ``text`` with Vartaloop. A GET, so an <audio> element can play it as
    it streams; the key stays on the server."""
    spoken = text.strip()[: settings.vartaloop.VARTALOOP_MAX_CHARS]
    stream = await tts.open_stream(spoken)
    return StreamingResponse(
        stream.chunks(),
        media_type=OPUS_MEDIA_TYPE,
        headers={"Cache-Control": "no-store", "X-Request-Id": stream.request_id},
        background=BackgroundTask(stream.aclose),
    )
