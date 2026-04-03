from agents.script_formatter import ScriptFormatterAgent
from agents.voice_planner import VoicePlanningAgent
from agents.tts_agent import TTSAgent
from agents.source_discovery import SourceDiscoveryAgent
from agents.source_validation import SourceValidationAgent
from agents.pdf_extraction import PDFExtractionAgent
from pipeline.models import PipelineResult, HistoryPipelineResult


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
