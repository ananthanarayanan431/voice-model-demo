# Voice Agent

FastAPI service behind the Sunrise Hospitals patient assistant demo; see
[CLAUDE.md](CLAUDE.md) for the package layout and rules.

```bash
make install env         # venv and .env
./run.sh                 # API with reload on :8000
uv run python scripts/tts_hello.py   # one Vartaloop TTS call -> hello.ogg
```
