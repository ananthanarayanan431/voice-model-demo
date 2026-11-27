# Voice Agent

> FastAPI service behind the Sunrise Hospitals patient assistant (demo, sample
> data). A patient turn goes to Claude with clinic tools (doctors, slots,
> booking, prescriptions, refills); replies are spoken with Vartaloop TTS.

## Quick Reference

| Item       | Value                                                                   |
| ---------- | ----------------------------------------------------------------------- |
| Port       | 8000                                                                    |
| Entry      | `uvicorn voice_agent.main:app` (or `./run.sh`, which adds reload)       |
| Health     | `GET /health` (liveness), `GET /ready` (dependency checks)              |
| API prefix | `/api/v1`: `POST /chat`, `POST /chat/reset`, `GET /tts`, `GET /doctors` |
| Module     | `voice_agent`; Python from the root `.python-version`                   |
| Contract   | `libs/voice-agent-contracts` (`make openapi`)                           |

## Layout

| Path                                    | Purpose                                                          |
| --------------------------------------- | ---------------------------------------------------------------- |
| `voice_agent/server.py`                 | App factory and lifespan; `create_app(model, http)` takes fakes  |
| `voice_agent/core/bootstrap.py`         | Composition root: clinic store, conversation service, TTS client |
| `voice_agent/routes/v1/voice.py`        | `/chat` (one patient turn), `/chat/reset`, `/tts` (audio stream) |
| `voice_agent/routes/v1/clinic.py`       | `/doctors` for the web app's side panel                          |
| `voice_agent/services/conversation.py`  | The turn loop: Claude, tool calls, per-session history           |
| `voice_agent/services/clinic.py`        | Sample schedule, booking rules, prescriptions (in memory)        |
| `voice_agent/chat/tools.py`             | Tool schemas (strict) and the code that runs them                |
| `voice_agent/chat/llm.py`               | `ChatModel` protocol and the Claude adapter (fallbacks on)       |
| `voice_agent/prompts/base.py`           | System prompt: voice style, booking, medicine and safety rules   |
| `voice_agent/integrations/vartaloop.py` | Streams `POST /v1/tts` (Opus) from Vartaloop                     |
| `voice_agent/config/`                   | `get_settings().<group>.<FIELD>`: app, anthropic, vartaloop      |
| `data/sunrise_demo.json`                | Sample doctors, hours and patients (illustrative, not real)      |
| `scripts/tts_hello.py`                  | One Vartaloop call -> `hello.ogg`, to check the key              |
| `tests/fakes.py`                        | `ScriptedChatModel` and response builders                        |
| `tests/unit/`, `tests/contract/`        | Clinic, tools, turn loop; the HTTP API with fakes                |

## Rules

- Every module starts with `from __future__ import annotations`. Type-only
  imports go under `if TYPE_CHECKING:`, except in Pydantic models, FastAPI
  routes and dependencies, which read annotations at runtime.
- New routes go in `routes/v1/` with their bodies in `schemas/v1/`. After any
  route or schema change run `make openapi` and commit both contract files.
- Pyright runs in **strict** mode. Fix types instead of ignoring them. An ignore
  names its rule and says why: `# pyright: ignore[reportPrivateUsage]`.
- Raise `VoiceAgentError` subclasses, named `*Error`. Put the message in a
  variable before `raise`. No `assert` outside tests.
- `except Exception` only at a real boundary, with the traceback logged and
  `# noqa: BLE001 - <why>`. Otherwise catch the specific exception.
- Log with loguru and arguments, never f-strings: `logger.info("Loaded {}", n)`.
- No side effects at import time: no clients or connections at module level.
- Entry points (`main.py`, `server.py`, `export_openapi.py`) stay at the package
  top: uvicorn, Docker, `run.sh`, the Makefile and CI call them by path.
- Third-party services live in `integrations/`, one module per provider, built
  in `core/bootstrap.py`. Claude sits behind the `ChatModel` protocol.
- The assistant never gives medical advice: medicine answers come only from the
  prescription on file, and emergencies go to 108. Keep those rules in the prompt
  and in `test_system_prompt_carries_the_safety_and_language_rules`.
- Secrets are `SecretStr`; never log them, prompts or retrieved documents.
- Tests never touch the network: use `tests/fakes.py` and `httpx.MockTransport`.

## Commands

`make` in this directory lists every shortcut.

```bash
make env                   # create .env, then fill in the API keys
uv run python scripts/tts_hello.py  # one Vartaloop TTS call -> hello.ogg
./run.sh                   # API with reload on :8000
make fmt                   # ruff format + safe fixes
make test                  # = scripts/ci/python-checks.sh agents/voice_agent unit
make audit                 # = scripts/ci/python-checks.sh agents/voice_agent audit
make openapi               # refresh libs/voice-agent-contracts after an API change
make docker-up             # the agent in Docker, on the infra network
```

Coverage must stay at or above `fail_under` in `pyproject.toml`; raise it when
you add tests. After changing dependencies, run `uv lock` and `make audit`.
