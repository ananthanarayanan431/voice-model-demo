# Voice Agent

> FastAPI service and LangGraph agent. Skeleton only: every module below exists
> as an empty placeholder until its logic is written.

## Quick Reference

| Item       | Value                                                             |
| ---------- | ----------------------------------------------------------------- |
| Port       | 8000                                                              |
| Entry      | `uvicorn voice_agent.main:app` (or `./run.sh`, which adds reload) |
| Health     | `GET /health` (liveness), `GET /ready` (MongoDB ping)             |
| API prefix | `/api/v1` (`routes/v1`)                                           |
| Module     | `voice_agent`; Python from the root `.python-version`             |
| Contract   | `libs/voice-agent-contracts` (`make openapi`)                     |

## Layout

| Path                             | Purpose                                                               |
| -------------------------------- | --------------------------------------------------------------------- |
| `voice_agent/server.py`          | App factory and lifespan (builds shared services once)                |
| `voice_agent/main.py`            | Uvicorn entry point                                                   |
| `voice_agent/export_openapi.py`  | The OpenAPI document the web contract is generated from               |
| `voice_agent/routes/`            | `health.py` (unversioned) and `v1/` (one module per area)             |
| `voice_agent/schemas/`           | Request and response bodies (`common`, `health`, `v1/*`)              |
| `voice_agent/config/`            | `settings.<group>.<FIELD>`, one module per group                      |
| `voice_agent/core/`              | Composition root, dependencies, errors, logging, request ctx, tracing |
| `voice_agent/chat/`              | The LangGraph graph: state, nodes, edges, tools, chains, model        |
| `voice_agent/prompts/`           | Every model prompt, one module each                                   |
| `voice_agent/services/`          | Use cases (one turn of a conversation, ...)                           |
| `voice_agent/db/`                | Mongo client and indexes                                              |
| `voice_agent/rag/`               | Extractors, splitter, embeddings, retriever, memory                   |
| `voice_agent/integrations/`      | Third-party clients, built only by `factory.py`                       |
| `voice_agent/models/`            | Domain models                                                         |
| `voice_agent/evals/`             | Dataset generation, upload and evaluation                             |
| `tests/unit/`, `tests/contract/` | Module tests; the HTTP/WebSocket API as clients see it                |
| `tests/fakes.py`                 | Scripted chat model, in-memory checkpointer and services              |

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
- No side effects at import time; never construct a `MongoClient` directly
  (use `db.client.get_mongo_client()`).
- Entry points (`main.py`, `server.py`, `export_openapi.py`) stay at the package
  top: uvicorn, Docker, `run.sh`, the Makefile and CI call them by path.
- Third-party services live in `integrations/`, one module per provider, each
  behind a protocol, built only through `IntegrationFactory`.
- Secrets are `SecretStr`; never log them, prompts or retrieved documents.
- Tests never touch the network or a real database: use `tests/fakes.py`.

## Commands

`make` in this directory lists every shortcut. MongoDB runs from `infra/`.

```bash
make -C ../../infra up     # MongoDB
make env                   # create .env, then fill in the API keys
./run.sh                   # API with reload on :8000
make fmt                   # ruff format + safe fixes
make test                  # = scripts/ci/python-checks.sh agents/voice_agent unit
make audit                 # = scripts/ci/python-checks.sh agents/voice_agent audit
make openapi               # refresh libs/voice-agent-contracts after an API change
make docker-up             # the agent in Docker, on the infra network
```

Coverage must stay at or above `fail_under` in `pyproject.toml`; raise it when
you add tests. After changing dependencies, run `uv lock` and `make audit`.
