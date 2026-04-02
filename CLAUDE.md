# Audio Narration Pipeline — Claude Code Context

## Project Purpose
Convert raw text into culturally respectful, high-quality audio narration using a three-agent AI pipeline.

## Architecture
Three sequential agents, each with a single responsibility:

```
raw text
  → ScriptFormatterAgent   (formats text for TTS)
  → VoicePlanningAgent     (decides voice style, speed, accent)
  → TTSAgent               (generates .mp3 via OpenAI TTS)
```

## Project Structure
```
audio-narration-pipeline/
├── CLAUDE.md
├── .env                  # OPENAI_API_KEY — never commit
├── requirements.txt
├── main.py               # Entry point
├── agents/
│   ├── base_agent.py     # Abstract base all agents inherit from
│   ├── script_formatter.py
│   ├── voice_planner.py
│   └── tts_agent.py
├── core/
│   ├── client.py         # Single shared OpenAI client instance
│   └── config.py         # Loads .env, exposes settings
├── pipeline/
│   ├── models.py         # Pydantic models: VoiceConfig, PipelineResult
│   └── pipeline.py       # Chains the three agents
├── docs/
│   └── skills.md         # Agent contracts and extension guide
└── output/               # Generated .mp3 files land here
```

## Conventions
- All agents inherit from `BaseAgent` and implement `run()`
- The shared OpenAI client lives in `core/client.py` — never instantiate `OpenAI()` elsewhere
- `load_dotenv()` is called once in `core/config.py` — never call it in agents
- Audio output always goes to the `output/` folder
- Voice config is always passed as a `VoiceConfig` Pydantic model, never a raw dict

## Key Files to Know
- Add a new agent → create a file in `agents/`, inherit `BaseAgent`, wire it into `pipeline/pipeline.py`
- Change TTS voice mapping → edit `agents/tts_agent.py` `VOICE_MAP`
- Change GPT model → edit `core/config.py`
