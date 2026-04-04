import os
import re
from agents.base_agent import BaseAgent
from core.config import TTS_MODEL, OUTPUT_DIR
from pipeline.models import VoiceConfig
from agents.voice_planner import AFRICAN_VOICE_PROFILES

# tts-1 reads text verbatim — no paraphrasing, no improvisation.
# Chunks keep requests under the 4096 char API limit.
_CHUNK_SIZE = 4000


def _base_voice(voice_key: str) -> str:
    profile = AFRICAN_VOICE_PROFILES.get(voice_key, {})
    return profile.get("base_voice", "fable")


def _split_sentences(text: str, max_chars: int) -> list[str]:
    sentences = re.split(r'(?<=[.!?…])\s+', text.strip())
    chunks = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current:
        chunks.append(current.strip())
    return chunks


class TTSAgent(BaseAgent):
    def run(self, script: str, voice_config: VoiceConfig, output_name: str = "output_audio") -> str:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"{output_name}.mp3")

        chunks = _split_sentences(script, _CHUNK_SIZE)
        print(f"  Generating {len(chunks)} audio chunks...")

        parts: list[bytes] = []
        base_voice = _base_voice(voice_config.voice)
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i}/{len(chunks)}: {chunk[:60]}...")
            response = self.client.audio.speech.create(
                model=TTS_MODEL,
                voice=base_voice,
                input=chunk,
                speed=voice_config.speed,
            )
            parts.append(response.content)

        with open(output_path, "wb") as f:
            f.write(b"".join(parts))

        return output_path
