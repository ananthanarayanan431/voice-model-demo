"""scripts/tts_hello.py refuses to call the API without a key."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from types import ModuleType

    import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "tts_hello.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("tts_hello", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_key_exits_without_calling_the_api(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Present but empty: load_dotenv does not override it, so a real .env is ignored.
    monkeypatch.setenv("VARTALOOP_API_KEY", "")

    def no_network(*_args: object, **_kwargs: object) -> None:
        msg = "the API must not be called without a key"
        raise AssertionError(msg)

    monkeypatch.setattr(httpx, "stream", no_network)

    assert load_script().main() == 1
    assert "VARTALOOP_API_KEY is not set" in capsys.readouterr().err
