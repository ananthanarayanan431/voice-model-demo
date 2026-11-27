# VoiceAgents

A FastAPI voice agent (Claude + Vartaloop TTS) and a React web app that talks
to it.

The first use case is the **Sunrise Hospitals patient assistant** (a demo on
sample data): a patient talks to it in the browser to book an appointment with a
doctor or ask about their prescribed medicines. Their words appear on screen as
they speak, and the assistant answers out loud.

| Piece           | What does it                                                          |
| --------------- | --------------------------------------------------------------------- |
| Live transcript | The browser's speech recognition (Chrome or Edge)                     |
| Conversation    | Claude with clinic tools: doctors, free slots, booking, prescriptions |
| Voice           | Vartaloop TTS (`saanvi`, Ogg/Opus), proxied by the agent              |

## Run it

```bash
cp agents/voice_agent/.env.example agents/voice_agent/.env   # add VARTALOOP_API_KEY and ANTHROPIC_API_KEY
make -C infra stack-up                                       # Docker: open http://localhost:8080
```

Or without Docker: `./agents/voice_agent/run.sh` and `pnpm install && pnpm dev`,
then open http://localhost:5173. Sample patients for the medicine questions:
9876543210 and 9123456780.

## Layout

```
.
├── agents/voice_agent/       # FastAPI agent: Claude + clinic tools + Vartaloop TTS (Python, uv)
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
