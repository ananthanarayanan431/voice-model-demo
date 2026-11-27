"""The HTTP API as the web app sees it, with Claude and Vartaloop faked.

Every JSON response is the envelope: ``{success, data, request_id}`` or
``{success, error: {code, message, fields}, request_id}``.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.fakes import ScriptedChatModel, text_reply
from voice_agent.server import create_app

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    # TestClient responses come from httpx2, the httpx fork the Anthropic SDK uses.
    import httpx2

SESSION = "session-123"
OGG = b"OggS\x00fake-opus-pages"


def vartaloop(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def ok_audio(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=OGG)


def app_client(
    model: ScriptedChatModel | None = None,
    handler: Callable[[httpx.Request], httpx.Response] = ok_audio,
) -> TestClient:
    return TestClient(create_app(model=model or ScriptedChatModel(), http=vartaloop(handler)))


def assert_error(response: httpx2.Response, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == code
    assert body["request_id"] == response.headers["X-Request-ID"]
    return body


@pytest.fixture
def model() -> ScriptedChatModel:
    return ScriptedChatModel()


@pytest.fixture
def client(model: ScriptedChatModel) -> Iterator[TestClient]:
    with app_client(model) as test_client:
        yield test_client


def test_success_envelope_carries_the_request_id(client: TestClient) -> None:
    response = client.get("/health")
    body = response.json()
    assert body == {"success": True, "data": {"status": "ok"}, "request_id": body["request_id"]}
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_a_safe_incoming_request_id_is_reused(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "lb-trace-42"})
    assert response.json()["request_id"] == "lb-trace-42"
    unsafe = client.get("/health", headers={"X-Request-ID": "bad id\nwith newline"})
    assert unsafe.json()["request_id"] != "bad id\nwith newline"


def test_ready_reports_features(client: TestClient) -> None:
    data = client.get("/ready").json()["data"]
    assert data == {"status": "ok", "speech_enabled": False, "llm_model": "claude-opus-5-5"}


def test_chat_returns_the_reply(client: TestClient, model: ScriptedChatModel) -> None:
    model.add(text_reply("Namaste! Which doctor would you like to see?"))
    response = client.post("/api/v1/chat", json={"session_id": SESSION, "message": "Hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {
        "reply": "Namaste! Which doctor would you like to see?",
        "appointments": [],
        "audio_url": None,
    }


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"session_id": SESSION, "message": ""}, "body.message"),
        ({"session_id": "short", "message": "hi"}, "body.session_id"),
        ({"session_id": "bad id with spaces!", "message": "hi"}, "body.session_id"),
        ({"session_id": SESSION, "message": "x" * 1001}, "body.message"),
    ],
)
def test_invalid_input_names_the_field(
    client: TestClient, body: dict[str, str], field: str
) -> None:
    error = assert_error(client.post("/api/v1/chat", json=body), 422, "validation_error")
    assert [f["field"] for f in error["error"]["fields"]] == [field]


def test_unknown_route_is_an_error_envelope(client: TestClient) -> None:
    assert_error(client.get("/api/v1/nope"), 404, "not_found")
    assert_error(client.delete("/api/v1/doctors"), 405, "method_not_allowed")


def test_reset(client: TestClient) -> None:
    response = client.post("/api/v1/chat/reset", json={"session_id": SESSION})
    assert response.json()["data"] == {"session_id": SESSION}


def test_doctors_lists_the_sample_roster(client: TestClient) -> None:
    doctors = client.get("/api/v1/doctors").json()["data"]
    assert doctors[0] == {
        "id": "dr-kavya-rao",
        "name": "Dr. Kavya Rao",
        "specialty": "Orthopaedics",
        "days": ["Mon", "Tue", "Thu", "Fri"],
        "hours": "10:00-16:00",
    }


def test_missing_credentials_are_a_503_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoKeyModel(ScriptedChatModel):
        async def create(self, *args: Any, **kwargs: Any) -> Any:
            from voice_agent.core.errors import NotConfiguredError

            msg = "No Anthropic credentials: set ANTHROPIC_API_KEY."
            raise NotConfiguredError(msg)

    with app_client(NoKeyModel()) as client:
        response = client.post("/api/v1/chat", json={"session_id": SESSION, "message": "hi"})
    body = assert_error(response, 503, "not_configured")
    assert "ANTHROPIC_API_KEY" in body["error"]["message"]


def test_unexpected_errors_are_a_500_envelope_without_details() -> None:
    class BrokenModel(ScriptedChatModel):
        async def create(self, *args: Any, **kwargs: Any) -> Any:
            msg = "secret internal detail"
            raise RuntimeError(msg)

    with app_client(BrokenModel()) as client:
        response = client.post("/api/v1/chat", json={"session_id": SESSION, "message": "hi"})
    body = assert_error(response, 500, "internal_error")
    assert "secret" not in json.dumps(body)


def test_chat_is_rate_limited_per_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_MINUTE", "2")
    model = ScriptedChatModel(text_reply("one"), text_reply("two"))
    with app_client(model) as client:
        for _ in range(2):
            client.post("/api/v1/chat", json={"session_id": SESSION, "message": "hi"})
        response = client.post("/api/v1/chat", json={"session_id": SESSION, "message": "hi"})
    assert_error(response, 429, "rate_limited")
    assert int(response.headers["Retry-After"]) > 0


def test_speech_link_streams_the_reply_from_vartaloop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARTALOOP_API_KEY", "vt_live_test")
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return ok_audio(request)

    model = ScriptedChatModel(text_reply("Dr. Rao is in on Monday."))
    with app_client(model, handler) as client:
        chat = client.post("/api/v1/chat", json={"session_id": SESSION, "message": "ortho?"})
        audio_url = chat.json()["data"]["audio_url"]
        assert audio_url.startswith("/api/v1/speech/")
        audio = client.get(audio_url)

    assert audio.status_code == 200
    assert audio.headers["content-type"] == "audio/ogg"
    assert audio.content == OGG
    assert str(sent[0].url) == "https://api.vartaloop.ai/v1/tts"
    assert sent[0].headers["x-api-key"] == "vt_live_test"
    assert json.loads(sent[0].content) == {
        "text": "Dr. Rao is in on Monday.",
        "voice": "saanvi",
        "format": "opus",
    }


def test_unknown_speech_link_is_404(client: TestClient) -> None:
    assert_error(client.get("/api/v1/speech/" + "x" * 24), 404, "not_found")


def test_speech_upstream_error_is_502(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARTALOOP_API_KEY", "vt_live_test")

    def out_of_credits(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, json={"error": "out of credits"})

    model = ScriptedChatModel(text_reply("Hello"))
    with app_client(model, out_of_credits) as client:
        audio_url = client.post(
            "/api/v1/chat", json={"session_id": SESSION, "message": "hi"}
        ).json()["data"]["audio_url"]
        response = client.get(audio_url)
    body = assert_error(response, 502, "upstream_error")
    assert "402" in body["error"]["message"]


def test_vartaloop_busy_is_retried_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARTALOOP_API_KEY", "vt_live_test")
    replies = [httpx.Response(503, headers={"retry-after": "0"}), httpx.Response(200, content=OGG)]

    def busy_then_ok(_request: httpx.Request) -> httpx.Response:
        return replies.pop(0)

    model = ScriptedChatModel(text_reply("Hello"))
    with app_client(model, busy_then_ok) as client:
        audio_url = client.post(
            "/api/v1/chat", json={"session_id": SESSION, "message": "hi"}
        ).json()["data"]["audio_url"]
        assert client.get(audio_url).content == OGG
    assert replies == []


def test_api_key_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "secret-key")
    with app_client() as client:
        assert_error(client.get("/api/v1/doctors"), 401, "unauthorized")
        assert client.get("/api/v1/doctors", headers={"X-API-Key": "secret-key"}).status_code == 200
        assert client.get("/health").status_code == 200


def test_docs_are_off_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    with app_client() as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
