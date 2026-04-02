# African Voices Audiobook Pipeline

> *"Until the lion learns to write, every story will glorify the hunter."*

An AI pipeline that discovers, validates, and narrates African first-hand historical accounts — preserving authentic voices as high-quality audiobooks.

---

## What It Does

Most of African history has been told through colonial filters. This project flips that.

It automatically:

1. **Discovers** publicly available African first-hand texts — memoirs, oral histories, autobiographies, and translated oral traditions — from open digital archives
2. **Validates** that sources are real and accessible
3. **Extracts** text directly from PDFs
4. **Formats** the script for natural spoken narration
5. **Plans** a culturally appropriate voice — elder, storyteller, West African accent, measured pace
6. **Generates** a professional `.mp3` audiobook using OpenAI TTS

---

## Sample Output

The pipeline discovered and narrated an excerpt from a study of **Anukili Ugama**, an Igbo epic — sourced directly from the Internet Archive.

The voice planner chose:

```json
{
  "voice": "elder_male",
  "tone": "wise, slow, storytelling",
  "speed": 0.85,
  "accent": "West African"
}
```

> *"To truly grasp the significance and impact of Anukili Ugama within the Igbo culture and community... one must explore the narrative through its historical context and societal functions. This approach offers insight into how the story mirrors the communal values and identity of the Igbo people..."*

---

## Architecture

```
Internet Archive (PDF)
        ↓
SourceDiscoveryAgent     — finds real, accessible PDFs via AI + archive search
SourceValidationAgent    — confirms each PDF is genuinely downloadable
PDFExtractionAgent       — downloads, parses, and cleans the text
ScriptFormatterAgent     — rewrites for natural spoken delivery
VoicePlanningAgent       — picks voice, tone, speed, and cultural accent
TTSAgent                 — generates the final .mp3
```

Each agent is a single Python class with one job. Easy to extend, swap, or improve.

---

## Quickstart

```bash
git clone https://github.com/l-Jacob-l/african-voices-audiobook-pipeline
cd african-voices-audiobook-pipeline
pip install -r requirements.txt
```

Create a `.env` file:

```
OPENAI_API_KEY=your_key_here
```

Run the full pipeline:

```python
from pipeline import run_history_pipeline

result = run_history_pipeline(region_hint="West Africa", output_name="my_narration")
print(f"Audio saved to: {result.audio_path}")
```

Or narrate your own text directly:

```python
from pipeline import run_pipeline

result = run_pipeline("Your text here...", output_name="custom")
```

---

## Project Structure

```
audio-narration-pipeline/
├── agents/
│   ├── source_discovery.py   # Finds African texts on Internet Archive
│   ├── source_validation.py  # Verifies PDF accessibility
│   ├── pdf_extraction.py     # Downloads + cleans PDF text
│   ├── script_formatter.py   # TTS-optimized narration script
│   ├── voice_planner.py      # Culturally aware voice selection
│   └── tts_agent.py          # OpenAI TTS → .mp3
├── pipeline/
│   ├── models.py             # Pydantic models
│   └── pipeline.py           # Orchestrates all agents
├── core/
│   ├── client.py             # Shared OpenAI client
│   └── config.py             # Environment config
├── docs/
│   └── skills.md             # Agent contracts + skill definitions
└── output/                   # Generated .mp3 files
```

---

## Why This Matters

Thousands of African first-hand accounts — oral histories, memoirs, indigenous epics — exist as scanned PDFs in digital archives, largely inaccessible to people who don't read academic papers.

This pipeline makes them listenable.

The goal is to eventually produce full audiobooks of works like:
- *The Interesting Narrative of Olaudah Equiano* (1789)
- *Sundiata: An Epic of Old Mali*
- *Facing Mount Kenya* by Jomo Kenyatta
- *Chaka* by Thomas Mofolo
- Hundreds of oral tradition transcripts from university archives

---

## How to Help

This project needs **API credits** to scale from excerpts to full books. A single full audiobook costs roughly $15–40 in TTS tokens.

If you want to contribute:
- **Sponsor via GitHub Sponsors** *(coming soon)*
- **Open a PR** — add a new agent, improve source discovery, or expand the voice map
- **Share this project** — visibility helps attract support from AI labs and cultural institutions
- **Suggest sources** — open an issue with a title and archive link

---

## Voice Options

| Config Key          | Character          | OpenAI Voice |
|---------------------|--------------------|--------------|
| `elder_male`        | Wise elder         | onyx         |
| `elder_female`      | Elder matriarch    | nova         |
| `storyteller_male`  | Griot storyteller  | fable        |
| `storyteller_female`| Female griot       | shimmer      |
| `calm_male`         | Scholar narrator   | echo         |
| `calm_female`       | Calm narrator      | alloy        |

---

## Requirements

- Python 3.10+
- OpenAI API key (with access to `gpt-4o` and `tts-1`)
- Internet connection (for Archive.org PDF discovery)

---

## License

MIT — use it, fork it, build on it. Just keep the voices authentic.
