import os
import re
import base64
from agents.base_agent import BaseAgent
from core.config import TTS_MODEL, TTS_AUDIO_MODEL, OUTPUT_DIR
from pipeline.models import VoiceConfig
from agents.voice_planner import AFRICAN_VOICE_PROFILES

# Each chunk gets its own API call so instructions reset and accent stays thick.
# Smaller chunks = more consistent accent. ~400 chars ≈ 2-3 sentences.
_CHUNK_SIZE = 400


def _base_voice(voice_key: str) -> str:
    profile = AFRICAN_VOICE_PROFILES.get(voice_key, {})
    return profile.get("base_voice", "fable")


def _split_sentences(text: str, max_chars: int) -> list[str]:
    """Split on sentence boundaries, grouping into chunks under max_chars."""
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

        if voice_config.instructions:
            audio_bytes = self._generate_chunked(script, voice_config)
        else:
            audio_bytes = self._generate_standard(script, voice_config)

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        return output_path

    def _generate_chunked(self, script: str, voice_config: VoiceConfig) -> bytes:
        """Split script into short chunks and call the API fresh for each.

        This forces the model to re-read the accent instructions every few sentences,
        preventing drift back to a neutral accent mid-narration.
        """
        base_voice = _base_voice(voice_config.voice)
        chunks = _split_sentences(script, _CHUNK_SIZE)
        print(f"  Generating {len(chunks)} audio chunks...")

        parts: list[bytes] = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i}/{len(chunks)}: {chunk[:60]}...")
            response = self.client.chat.completions.create(
                model=TTS_AUDIO_MODEL,
                modalities=["text", "audio"],
                audio={"voice": base_voice, "format": "mp3"},
                messages=[
                    {
                        "role": "system",
                        "content": voice_config.instructions,
                    },
                    {
                        "role": "user",
                        "content": chunk,
                    },
                ],
            )
            parts.append(base64.b64decode(response.choices[0].message.audio.data))

        # Raw MP3 frames concatenate cleanly
        return b"".join(parts)

    def _generate_standard(self, script: str, voice_config: VoiceConfig) -> bytes:
        """Fallback: OpenAI tts-1 without cultural instructions."""
        base_voice = _base_voice(voice_config.voice)
        response = self.client.audio.speech.create(
            model=TTS_MODEL,
            voice=base_voice,
            input=script,
            speed=voice_config.speed,
        )
        return response.content
