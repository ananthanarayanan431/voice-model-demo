#!/usr/bin/env bash
# Run the voice agent in this terminal.
#
#   ./run.sh [api]   the API with reload on :8000
#
# Reads .env (copy .env.example), or the
# environment if there is none.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "$(dirname "$SELF")"

usage() {
    sed -n '2,7p' "$SELF" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

load_env() {
    if [ -f .env ]; then
        set -a
        # shellcheck source=/dev/null
        . ./.env
        set +a
    fi
    # Warn, don't stop: the SDK can also use `ant auth login`, and the app runs
    # without Vartaloop (replies then show as text only).
    [ -n "${ANTHROPIC_API_KEY:-}" ] || echo "Note: ANTHROPIC_API_KEY is not set; using the SDK's own credentials." >&2
    [ -n "${VARTALOOP_API_KEY:-}" ] || echo "Note: VARTALOOP_API_KEY is not set; replies will not be spoken." >&2
}

run_api() {
    uv sync --locked
    exec uv run --locked uvicorn voice_agent.main:app --reload \
        --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --no-access-log
}

case "${1:-api}" in
    api) load_env; run_api ;;
    -h | --help | help) usage ;;
    *) usage 1 ;;
esac
