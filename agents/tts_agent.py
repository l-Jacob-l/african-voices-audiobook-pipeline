import os
import base64
from agents.base_agent import BaseAgent
from core.config import TTS_MODEL, TTS_AUDIO_MODEL, OUTPUT_DIR
from pipeline.models import VoiceConfig
from agents.voice_planner import AFRICAN_VOICE_PROFILES

# Base OpenAI voice for each profile (used by gpt-4o-audio-preview)
# The instructions handle the accent/style; the base voice sets the timbre.
def _base_voice(voice_key: str) -> str:
    profile = AFRICAN_VOICE_PROFILES.get(voice_key, {})
    return profile.get("base_voice", "fable")


class TTSAgent(BaseAgent):
    def run(self, script: str, voice_config: VoiceConfig, output_name: str = "output_audio") -> str:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"{output_name}.mp3")

        if voice_config.instructions:
            audio_bytes = self._generate_with_instructions(script, voice_config)
        else:
            audio_bytes = self._generate_standard(script, voice_config)

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        return output_path

    def _generate_with_instructions(self, script: str, voice_config: VoiceConfig) -> bytes:
        """Use gpt-4o-audio-preview for culturally instructed delivery."""
        base_voice = _base_voice(voice_config.voice)

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
                    "content": script,
                },
            ],
        )
        return base64.b64decode(response.choices[0].message.audio.data)

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
