"""The voice loop: a patient turn in, the reply and its audio link out."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from voice_agent.config import API_V1_PREFIX, Settings
from voice_agent.core.dependencies import (
    chat_rate_limit,
    conversation_dep,
    settings_dep,
    speech_cache_dep,
    tts_dep,
)
from voice_agent.core.errors import NotFoundError
from voice_agent.core.responses import success
from voice_agent.integrations.vartaloop import OPUS_MEDIA_TYPE, VartaloopTTS
from voice_agent.schemas.common import ERROR_RESPONSES, SuccessResponse
from voice_agent.schemas.v1 import AppointmentOut, ChatReply, ChatRequest, ResetRequest, ResetResult
from voice_agent.services.conversation import ConversationService
from voice_agent.services.speech import SpeechCache

router = APIRouter(tags=["voice"])
# The audio link is a capability URL (unguessable, short-lived): an <audio>
# element cannot send headers, so it sits outside the API-key gate.
speech_router = APIRouter(prefix=API_V1_PREFIX, tags=["voice"], responses=ERROR_RESPONSES)


@router.post("/chat", dependencies=[Depends(chat_rate_limit)])
async def chat(
    body: ChatRequest,
    request: Request,
    conversation: Annotated[ConversationService, Depends(conversation_dep)],
    tts: Annotated[VartaloopTTS, Depends(tts_dep)],
    speech: Annotated[SpeechCache, Depends(speech_cache_dep)],
    settings: Annotated[Settings, Depends(settings_dep)],
) -> SuccessResponse[ChatReply]:
    """One patient turn: the final transcript in, the assistant's reply out."""
    result = await conversation.reply(body.session_id, body.message.strip())
    audio_url = None
    if tts.configured and result.reply:
        spoken = result.reply[: settings.vartaloop.VARTALOOP_MAX_CHARS]
        audio_url = f"{API_V1_PREFIX}/speech/{speech.put(spoken)}"
    reply = ChatReply(
        reply=result.reply,
        appointments=[
            AppointmentOut.model_validate(a, from_attributes=True) for a in result.appointments
        ],
        audio_url=audio_url,
    )
    return success(request, reply)


@router.post("/chat/reset")
async def reset(
    body: ResetRequest,
    request: Request,
    conversation: Annotated[ConversationService, Depends(conversation_dep)],
) -> SuccessResponse[ResetResult]:
    """Forget a conversation (the "New call" button)."""
    conversation.reset(body.session_id)
    return success(request, ResetResult(session_id=body.session_id))


@speech_router.get(
    "/speech/{speech_id}",
    response_class=StreamingResponse,
    responses={200: {"content": {OPUS_MEDIA_TYPE: {}}, "description": "Ogg/Opus audio"}},
)
async def speech_audio(
    speech_id: Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{16,64}$")],
    tts: Annotated[VartaloopTTS, Depends(tts_dep)],
    speech: Annotated[SpeechCache, Depends(speech_cache_dep)],
) -> StreamingResponse:
    """Stream a reply's audio from Vartaloop as it is synthesised."""
    text = speech.get(speech_id)
    if text is None:
        msg = "This audio link has expired."
        raise NotFoundError(msg)
    stream = await tts.open_stream(text)
    return StreamingResponse(
        stream.chunks(),
        media_type=OPUS_MEDIA_TYPE,
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(stream.aclose),
    )
