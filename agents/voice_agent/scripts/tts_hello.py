"""One Vartaloop TTS call: POST /v1/tts and save the streamed Ogg/Opus to hello.ogg.

    uv run python scripts/tts_hello.py

Reads VARTALOOP_API_KEY from agents/voice_agent/.env (git-ignored). Docs:
https://docs.vartaloop.ai/api/tts/
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

API_URL = "https://api.vartaloop.ai/v1/tts"
AGENT_DIR = Path(__file__).resolve().parent.parent
OUT_FILE = AGENT_DIR / "hello.ogg"
TEXT = "नमस्ते! Vartaloop से यह पहली आवाज़ है."


def main() -> int:
    load_dotenv(AGENT_DIR / ".env")
    api_key = os.environ.get("VARTALOOP_API_KEY", "").strip()
    if not api_key:
        sys.stderr.write("VARTALOOP_API_KEY is not set. Paste it into agents/voice_agent/.env\n")
        return 1

    body = {"text": TEXT, "voice": "saanvi", "format": "opus"}
    headers = {"x-api-key": api_key}
    with httpx.stream("POST", API_URL, json=body, headers=headers, timeout=60) as response:
        if response.is_error:
            response.read()
            sys.stderr.write(f"HTTP {response.status_code}: {response.text}\n")
            return 1
        with OUT_FILE.open("wb") as out:
            for chunk in response.iter_bytes():
                out.write(chunk)
        request_id = response.headers.get("x-request-id", "?")

    size = OUT_FILE.stat().st_size
    sys.stdout.write(f"Saved {OUT_FILE.name} ({size} bytes), request id {request_id}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
