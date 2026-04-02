import json
from agents.base_agent import BaseAgent
from core.config import GPT_MODEL
from pipeline.models import VoiceConfig


class VoicePlanningAgent(BaseAgent):
    def run(self, text: str) -> VoiceConfig:
        prompt = f"""You are a voice director. Read this text and decide the best voice settings for narrating it.

Return a JSON object with exactly these fields:
- "voice": one of "elder_male", "elder_female", "storyteller_male", "storyteller_female", "calm_male", "calm_female"
- "tone": short description like "wise, slow, storytelling" or "calm, clear, serious"
- "speed": a float between 0.75 and 1.1 (0.85 = slower, 1.0 = normal)
- "accent": a cultural accent hint like "West African", "British", "Neutral American", "Caribbean", etc.

Text:
{text}

Return only the JSON object, nothing else."""

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return VoiceConfig(**data)
