# Agent Skills Reference

## ScriptFormatterAgent
**File:** `agents/script_formatter.py`  
**Input:** Raw text (string)  
**Output:** Narration-ready script (string)  
**What it does:** Adds pauses, spells out numbers/abbreviations, removes non-speakable formatting  

---

## VoicePlanningAgent
**File:** `agents/voice_planner.py`  
**Input:** Text (string)  
**Output:** `VoiceConfig` model  
**What it does:** Analyzes the text and decides the best voice, tone, speed, and accent  

**VoiceConfig fields:**
| Field   | Type  | Example                    |
|---------|-------|----------------------------|
| voice   | str   | "elder_male"               |
| tone    | str   | "wise, slow, storytelling" |
| speed   | float | 0.85                       |
| accent  | str   | "West African"             |

**Available voice options:** `elder_male`, `elder_female`, `storyteller_male`, `storyteller_female`, `calm_male`, `calm_female`

---

## TTSAgent
**File:** `agents/tts_agent.py`  
**Input:** Script (string), VoiceConfig, output filename (string)  
**Output:** Path to generated `.mp3` file  
**What it does:** Maps voice config to an OpenAI TTS voice and generates audio  

**Voice mapping:**
| Config voice         | OpenAI voice |
|----------------------|--------------|
| elder_male           | onyx         |
| elder_female         | nova         |
| storyteller_male     | fable        |
| storyteller_female   | shimmer      |
| calm_male            | echo         |
| calm_female          | alloy        |

---

---

## Skill: African First-Hand History Discovery, Validation & Audiobook Preparation

### Overview
Enables an AI agent to discover, validate, and process publicly available African first-hand historical accounts—especially PDF documents—and prepare them for conversion into high-quality audiobooks.

Goal: Preserve authentic African voices and narratives by prioritizing primary, first-hand sources and minimizing colonial or interpretive bias.

---

### Core Responsibilities

1. Discover publicly available sources (especially PDFs)
2. Verify accessibility and legitimacy of sources
3. Evaluate authenticity and authorship
4. Extract and clean text
5. Summarize historical narratives
6. Prepare content for narration (audiobook format)

---

### Key Principles

- Prioritize **African-authored, first-hand accounts**
- Avoid colonial reinterpretations or heavily mediated narratives
- Do not fabricate sources, links, or metadata
- Only use **publicly accessible documents**
- Prefer **academic, archival, or cultural institution sources**
- Maintain **historical accuracy and respect for cultural context**

---

### Task 1: Source Discovery (PDF-Focused)

Search queries:
- "African oral history PDF"
- "first-hand African narrative PDF"
- "African memoir history PDF"
- "oral tradition Africa transcript PDF"
- "translated African oral account PDF"

**Preferred source types:** University archives, digital libraries, research institutions, cultural preservation organizations, UNESCO/government archives

**Output format:**
```json
[
  {
    "title": "",
    "author": "",
    "year": "",
    "region": "",
    "source": "",
    "pdf_link": "",
    "access": "CONFIRMED | UNCERTAIN"
  }
]
```

---

### Agent Mapping

| Responsibility            | Agent                    | Status  |
|---------------------------|--------------------------|---------|
| Source discovery          | `SourceDiscoveryAgent`   | Planned |
| Access/legitimacy check   | `SourceValidationAgent`  | Planned |
| PDF text extraction       | `PDFExtractionAgent`     | Planned |
| Narration script prep     | `ScriptFormatterAgent`   | Exists  |
| Voice planning            | `VoicePlanningAgent`     | Exists  |
| Audio generation          | `TTSAgent`               | Exists  |

---

## Adding a New Agent
1. Create `agents/your_agent.py`
2. Inherit from `BaseAgent` and implement `run()`
3. Export it in `agents/__init__.py`
4. Wire it into `pipeline/pipeline.py`
