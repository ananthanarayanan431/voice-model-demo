# VoiceAgents

> A FastAPI + LangGraph voice agent (Vartaloop TTS), and a React web app that
> talks to it. This repo is currently a skeleton: the layout, tooling and gates
> are in place, the logic is not.

| Part         | Where                        | Port | Agent notes                                                  |
| ------------ | ---------------------------- | ---- | ------------------------------------------------------------ |
| Voice agent  | `agents/voice_agent`         | 8000 | [agents/voice_agent/CLAUDE.md](agents/voice_agent/CLAUDE.md) |
| Web app      | `web/`                       | 5173 | [web/CLAUDE.md](web/CLAUDE.md)                               |
| API contract | `libs/voice-agent-contracts` |      | [libs/README.md](libs/README.md)                             |
| Docker stack | `infra/`                     |      | `make -C infra help`                                         |

Human-facing docs: [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md).

## Layout rules

- A Python service is an agent: `agents/<name>_agent/` with a flat package of the
  same name, its own `pyproject.toml`, `uv.lock`, `Dockerfile`, `Makefile`,
  `run.sh`, `.env.example` and `CLAUDE.md`. Lint, type and test rules live only
  in the root `pyproject.toml`; never add `[tool.ruff]`, `[tool.pyright]` or
  `[tool.pytest.ini_options]` to an agent.
- TypeScript lives in the pnpm workspace: `web/` and `libs/*`. Scripts run from
  the root `package.json`.
- Compose files live in `infra/`; every image builds from the repo root
  (`docker build -f <dir>/Dockerfile .`).
- An API change in an agent is not done until `make -C agents/<agent> openapi` has
  refreshed its contract in `libs/` (CI diffs it).

## Rules for every change

- **Conventional Commits**, enforced by `.githooks/commit-msg`:
  `<type>(<scope>): <imperative summary>`, at most 72 characters. Types: `feat`,
  `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, `build`, `style`,
  `revert`. Scopes: `agent`, `web`, `infra`, `ci`, `deps`.
- **No em or en dashes and no AI attribution** in commit messages. The hook
  rejects the dashes and strips AI trailers.
- **Never skip hooks** (`--no-verify`). Activate them once per clone with
  `git config core.hooksPath .githooks`.
- **Run the gates before saying a change works**:
  `scripts/ci/python-checks.sh agents/voice_agent all` and `pnpm check`.
  CI runs exactly these.
- Never commit `.env` files or secrets; only `.env.example` files are tracked.

## Commands

```bash
scripts/ci/python-checks.sh <agent-dir> [unit|audit|all]  # Python gate (ruff, pyright strict, pytest + coverage, pip-audit)
pnpm check                                                # web gate (prettier, oxlint, tsc, vitest, build)
pnpm format                                               # prettier --write over the repo
make -C infra stack-up                                    # agent and web app in Docker
```
