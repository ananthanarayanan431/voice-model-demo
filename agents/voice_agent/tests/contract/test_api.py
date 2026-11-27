"""The HTTP API as the web app sees it, with Claude and Vartaloop faked."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.fakes import ScriptedChatModel, text_reply
from voice_agent.server import create_app

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

SESSION = "session-123"
OGG = b"OggS\x00fake-opus-pages"


def vartaloop(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def ok_audio(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=OGG, headers={"x-request-id": "req-1"})


@pytest.fixture
def model() -> ScriptedChatModel:
    return ScriptedChatModel()


@pytest.fixture
def client(model: ScriptedChatModel) -> Iterator[TestClient]:
    with TestClient(create_app(model=model, http=vartaloop(ok_audio))) as test_client:
        yield test_client


def test_health_and_ready(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    ready = client.get("/ready").json()
    assert ready["tts_configured"] is False
    assert ready["llm_model"] == "claude-opus-5-5"


def test_chat_returns_the_reply(client: TestClient, model: ScriptedChatModel) -> None:
    model.add(text_reply("Namaste! Which doctor would you like to see?"))
    response = client.post("/api/v1/chat", json={"session_id": SESSION, "message": "Hello"})
    assert response.status_code == 200
    assert response.json() == {
        "reply": "Namaste! Which doctor would you like to see?",
        "appointments": [],
    }


@pytest.mark.parametrize(
    "body",
    [
        {"session_id": SESSION, "message": ""},
        {"session_id": "short", "message": "hi"},
        {"session_id": "bad id with spaces!", "message": "hi"},
        {"session_id": SESSION, "message": "x" * 1001},
    ],
)
def test_chat_rejects_invalid_bodies(client: TestClient, body: dict[str, str]) -> None:
    assert client.post("/api/v1/chat", json=body).status_code == 422


def test_reset_returns_204(client: TestClient) -> None:
    assert client.post("/api/v1/chat/reset", json={"session_id": SESSION}).status_code == 204


def test_doctors_lists_the_sample_roster(client: TestClient) -> None:
    doctors = client.get("/api/v1/doctors").json()
    assert doctors[0] == {
        "id": "dr-kavya-rao",
        "name": "Dr. Kavya Rao",
        "specialty": "Orthopaedics",
        "days": ["Mon", "Tue", "Thu", "Fri"],
        "hours": "10:00-16:00",
    }


def test_tts_without_a_key_is_503(client: TestClient) -> None:
    response = client.get("/api/v1/tts", params={"text": "Namaste"})
    assert response.status_code == 503
    assert "VARTALOOP_API_KEY" in response.json()["detail"]


def test_tts_streams_vartaloop_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARTALOOP_API_KEY", "vt_live_test")
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return ok_audio(request)

    with TestClient(create_app(model=ScriptedChatModel(), http=vartaloop(handler))) as client:
        response = client.get("/api/v1/tts", params={"text": "Namaste, aap kaise hain?"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/ogg"
    assert response.content == OGG
    assert str(sent[0].url) == "https://api.vartaloop.ai/v1/tts"
    assert sent[0].headers["x-api-key"] == "vt_live_test"
    assert json.loads(sent[0].content) == {
        "text": "Namaste, aap kaise hain?",
        "voice": "saanvi",
        "format": "opus",
    }


def test_tts_upstream_error_is_502(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARTALOOP_API_KEY", "vt_live_test")

    def busy(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, json={"error": "out of credits"})

    with TestClient(create_app(model=ScriptedChatModel(), http=vartaloop(busy))) as client:
        response = client.get("/api/v1/tts", params={"text": "Namaste"})
    assert response.status_code == 502
    assert "402" in response.json()["detail"]


def test_api_key_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "secret-key")
    with TestClient(create_app(model=ScriptedChatModel(), http=vartaloop(ok_audio))) as client:
        assert client.get("/api/v1/doctors").status_code == 401
        assert client.get("/api/v1/doctors", headers={"X-API-Key": "secret-key"}).status_code == 200
        assert client.get("/health").status_code == 200
