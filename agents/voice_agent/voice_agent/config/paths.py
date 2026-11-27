"""Filesystem locations: the agent folder (``/app`` in the image) and its data."""

from __future__ import annotations

import os
from pathlib import Path

# The package lives in site-packages inside the image, so the agent folder comes
# from VOICE_AGENT_DIR there; locally it is two levels above this file.
AGENT_DIR = Path(os.environ.get("VOICE_AGENT_DIR", Path(__file__).resolve().parents[2]))
DATA_DIR = AGENT_DIR / "data"
ENV_FILE = AGENT_DIR / ".env"
