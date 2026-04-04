import os
import re
import requests
from bs4 import BeautifulSoup
from agents.script_formatter import ScriptFormatterAgent
from agents.voice_planner import VoicePlanningAgent
from agents.tts_agent import TTSAgent
from agents.source_discovery import SourceDiscoveryAgent
from agents.source_validation import SourceValidationAgent
from agents.pdf_extraction import PDFExtractionAgent
from agents.intro_agent import IntroAgent
from agents.transcript_sync_agent import TranscriptSyncAgent
from agents.talking_head_agent import TalkingHeadAgent
from pipeline.models import PipelineResult, HistoryPipelineResult, AudiobookResult, SourceRecord


def _slug(text: str) -> str:
    safe = re.sub(r"[^\w\s-]", "", text.encode("ascii", "replace").decode())
    return re.sub(r"\s+", "_", safe.strip())[:80] or "audiobook"


def run_audiobook_from_url(
    url: str,
    author: str,
    title: str,
    year: str,
    region: str,
    max_chars: int = 8000,
) -> AudiobookResult:
    source = SourceRecord(
        title=title, author=author, year=year, region=region,
        source="URL", pdf_link=url, access="CONFIRMED",
    )
    output_name = _slug(title)
    os.makedirs("output", exist_ok=True)

    print("STEP 1 — Fetching text...")
    resp = requests.get(url, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["nav", "header", "footer", "script", "style", "img"]):
        tag.decompose()
    raw = soup.get_text(separator="\n", strip=True)
    # Strip Gutenberg boilerplate
    for marker in ["CHAPTER I.", "CHAPTER 1.", "PREFACE", "INTRODUCTION"]:
        idx = raw.find(marker)
        if idx != -1:
            raw = raw[idx:]
            break
    end = raw.find("End of the Project Gutenberg")
    if end != -1:
        raw = raw[:end]
    excerpt = raw[:max_chars]
    print(f"  {len(excerpt)} chars fetched")

    print("\nSTEP 2 — Generating introduction...")
    intro_text = IntroAgent().run(source, excerpt)
    print(f"  {intro_text[:120]}...")

    print("\nSTEP 3 — Formatting script...")
    body_script = ScriptFormatterAgent().run(excerpt)
    full_script = intro_text + "\n\n" + body_script

    script_path = f"output/{output_name}.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(full_script)
    print(f"  Script saved to: {script_path}")

    print("\nSTEP 4 — Planning voice...")
    voice_config = VoicePlanningAgent().run(excerpt)
    print(voice_config.model_dump_json(indent=2))

    print("\nSTEP 5 — Generating audio...")
    audio_path = TTSAgent().run(full_script, voice_config, output_name)
    print(f"  Audio saved to: {audio_path}")

    print("\nSTEP 6 — Generating subtitles (Whisper)...")
    srt_path = f"output/{output_name}.srt"
    TranscriptSyncAgent().run(audio_path, srt_path)
    print(f"  SRT saved to: {srt_path}")

    print("\nSTEP 7 — Generating talking head video...")
    video_path = TalkingHeadAgent().run(
        author=author, region=region, year=year,
        audio_path=audio_path, srt_path=srt_path,
        output_name=output_name,
    )
    print(f"  Video saved to: {video_path}")

    return AudiobookResult(
        intro=intro_text,
        script=full_script,
        audio_path=audio_path,
        srt_path=srt_path,
        video_path=video_path,
    )


def run_history_pipeline(region_hint: str = "", output_name: str = "history_narration") -> HistoryPipelineResult:
    print("STEP 1 — Discovering sources...")
    sources = SourceDiscoveryAgent().run(region_hint=region_hint)
    for s in sources:
        title = s.title.encode("ascii", "replace").decode()
        author = s.author.encode("ascii", "replace").decode()
        print(f"  [{s.access}] {title} - {author}")

    print("\nSTEP 2 — Validating sources...")
    validated = SourceValidationAgent().run(sources)
    confirmed_count = sum(1 for s in validated if s.access == "CONFIRMED")
    print(f"  {confirmed_count}/{len(validated)} sources confirmed accessible")

    print("\nSTEP 3 — Extracting PDF text...")
    extracted_text = PDFExtractionAgent().run(validated)
    print(f"  Extracted {len(extracted_text)} characters")

    print("\nSTEP 4 — Formatting script...")
    script = ScriptFormatterAgent().run(extracted_text)
    print(script[:300] + "..." if len(script) > 300 else script)

    print("\nSTEP 5 — Planning voice...")
    voice_config = VoicePlanningAgent().run(extracted_text)
    print(voice_config.model_dump_json(indent=2))

    script_path = f"output/{output_name}.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"\nScript saved to: {script_path}")

    print("\nSTEP 6 — Generating audio...")
    audio_path = TTSAgent().run(script, voice_config, output_name)
    print(f"  Audio saved to: {audio_path}")

    return HistoryPipelineResult(
        sources=sources,
        validated_sources=validated,
        extracted_text=extracted_text,
        script=script,
        voice_config=voice_config,
        audio_path=audio_path,
    )


def run_pipeline(text: str, output_name: str = "output_audio") -> PipelineResult:
    print("STEP 1 — Formatting script...")
    script = ScriptFormatterAgent().run(text)
    print(script)

    print("\nSTEP 2 — Planning voice...")
    voice_config = VoicePlanningAgent().run(text)
    print(voice_config.model_dump_json(indent=2))

    print("\nSTEP 3 — Generating audio...")
    audio_path = TTSAgent().run(script, voice_config, output_name)
    print(f"Audio saved to: {audio_path}")

    return PipelineResult(script=script, voice_config=voice_config, audio_path=audio_path)
