"""Print the API's OpenAPI document, the contract the web app is typed from.

    uv run python -m voice_agent.export_openapi > ../../libs/voice-agent-contracts/openapi.json

(or ``make openapi``, which also regenerates the TypeScript types). CI exports it
again and fails if the committed snapshot differs.
"""

from __future__ import annotations

import json
import sys
from importlib.metadata import version

from voice_agent.server import create_app


def openapi_document() -> dict[str, object]:
    """``info`` is fixed so the export is the same on every machine."""
    document = create_app().openapi()
    document["info"] = {"title": "VoiceAgents voice agent", "version": version("voice-agent")}
    return document


def main() -> None:
    sys.stdout.write(json.dumps(openapi_document(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
