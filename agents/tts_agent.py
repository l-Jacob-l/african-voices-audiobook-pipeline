import os
from agents.base_agent import BaseAgent
from core.config import TTS_MODEL, OUTPUT_DIR
from pipeline.models import VoiceConfig

VOICE_MAP = {
    "elder_male":         "onyx",
    "elder_female":       "nova",
    "storyteller_male":   "fable",
    "storyteller_female": "shimmer",
    "calm_male":          "echo",
    "calm_female":        "alloy",
}


class TTSAgent(BaseAgent):
    def run(self, script: str, voice_config: VoiceConfig, output_name: str = "output_audio") -> str:
        voice = VOICE_MAP.get(voice_config.voice, "fable")

        response = self.client.audio.speech.create(
            model=TTS_MODEL,
            voice=voice,
            input=script,
            speed=voice_config.speed
        )

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"{output_name}.mp3")

        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path
