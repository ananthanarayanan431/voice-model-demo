# Voice Agent

FastAPI service and LangGraph agent for VoiceAgents. Skeleton only; see
[CLAUDE.md](CLAUDE.md) for the package layout and rules.

```bash
make install env         # venv and .env
./run.sh                 # API with reload on :8000
uv run python scripts/tts_hello.py   # one Vartaloop TTS call -> hello.ogg
```
