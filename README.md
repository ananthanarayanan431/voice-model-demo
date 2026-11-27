# VoiceAgents

A FastAPI + LangGraph voice agent (Vartaloop TTS), and a React web app that
talks to it.

> Status: skeleton. The repository layout, tooling, CI and Docker setup are in
> place; the agent and web logic are still to be written.

## Layout

```
.
├── agents/voice_agent/       # FastAPI + LangGraph service (Python, uv)
├── web/                      # React 19 + Vite app (pnpm workspace)
├── libs/voice-agent-contracts/  # TypeScript types generated from the agent's OpenAPI
├── infra/                    # docker compose: agent, web
├── scripts/ci/               # the Python quality gate CI runs
├── docs/                     # ideas, specs, plans
├── .claude/                  # Claude Code agents, skills and references
├── .githooks/                # commit-msg and pre-commit hooks
└── .github/                  # CI, labels, dependabot
```

## Quick start

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and conventions.

```bash
git config core.hooksPath .githooks
make -C agents/voice_agent install env
pnpm install && pnpm dev
```

## License

[MIT](LICENSE)
