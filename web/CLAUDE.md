# VoiceAgents web app

> React 19 + Vite app: the Sunrise Hospitals patient assistant call screen. The
> browser's speech recognition shows the patient's words live; each final
> sentence goes to `POST /api/v1/chat`, and the reply plays from `GET /api/v1/tts`.

## Quick Reference

| Item     | Value                                                                              |
| -------- | ---------------------------------------------------------------------------------- |
| Package  | `@voiceagent/web` in the root pnpm workspace                                       |
| Dev      | `pnpm dev` on :5173 (proxies `/api` to the agent on :8000)                         |
| Node     | root `.nvmrc`; install with `pnpm install` at the root (`--frozen-lockfile` in CI) |
| Tests    | Vitest + Testing Library, jsdom                                                    |
| Lint     | oxlint (`.oxlintrc.json`); Prettier from the root `.prettierrc`                    |
| Contract | REST types from `@voiceagent/voice-agent-contracts` (generated)                    |
| Serving  | nginx in Docker (`nginx.conf.template`, `security-headers.conf`)                   |

## Key Files

| File                                       | Purpose                                                       |
| ------------------------------------------ | ------------------------------------------------------------- |
| `src/features/voice/voice-page.tsx`        | The call screen: transcript, live words, controls, side panel |
| `src/features/voice/use-voice-call.ts`     | Mic -> agent -> audio -> mic; the mic is off while replying   |
| `src/features/voice/call-state.ts`         | Pure reducer for the call (tested without a browser)          |
| `src/features/voice/speech-recognition.ts` | Types and helpers for the Web Speech API (Chrome, Edge)       |
| `src/lib/api.ts`                           | REST client; every failure becomes an `ApiError`              |

## Rules

- Layout: `app/` is the shell, `components/` is UI shared by features,
  `features/<name>/` holds everything one feature needs (page, components, hooks,
  state, tests), `lib/` is framework-free helpers. File names are kebab-case.
- Imports across folders use `@/` (`src/`); imports within a folder stay relative.
- Never declare REST request or response shapes by hand: import them from the
  contract. If the agent's API changes, run `make -C agents/voice_agent openapi`.
- Colours are semantic tokens defined in `src/app/globals.css` (`bg-canvas`,
  `text-ink`). No raw palette steps such as `bg-zinc-800` in components.
- Protocol logic goes in pure reducers and is tested there, not as component state.
- No side effects inside React state updaters (they must stay pure).
- Wrap every `localStorage` access; the app must work when it throws.

## Commands

```bash
pnpm install        # at the repo root
pnpm dev            # dev server (or ./run.sh, make dev, here)
pnpm format         # prettier --write over the repo
pnpm check          # everything CI runs: format, lint, typecheck, test, build
make docker-up      # the nginx image on the infra network
```
