from agents.base_agent import BaseAgent
from core.config import GPT_MODEL


class ScriptFormatterAgent(BaseAgent):
    def run(self, text: str) -> str:
        prompt = f"""Convert this text into a narration-friendly script for audio/text-to-speech.

Rules:
- Add natural pauses using "..." where a speaker would breathe or pause
- Break long sentences into shorter, speakable phrases
- Spell out abbreviations and numbers (e.g. "3" -> "three", "Dr." -> "Doctor")
- Remove or rewrite anything that doesn't read well aloud (bullet points, tables, etc.)
- Keep the meaning and tone intact

Text:
{text}

Return only the formatted script, no commentary."""

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
