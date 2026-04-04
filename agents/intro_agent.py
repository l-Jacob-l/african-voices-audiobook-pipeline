from agents.base_agent import BaseAgent
from core.config import GPT_MODEL
from pipeline.models import SourceRecord


class IntroAgent(BaseAgent):
    """Generates a spoken introduction covering author, time period, setting, and context."""

    def run(self, source: SourceRecord, excerpt: str) -> str:
        prompt = f"""You are writing a short spoken introduction for an audiobook narration.

Source details:
- Title: {source.title}
- Author: {source.author}
- Year: {source.year}
- Region: {source.region}

Opening lines of the text:
{excerpt[:1500]}

Write a spoken introduction of 3-5 sentences that covers:
1. Who the author is — their identity, background, and significance
2. When this was written or when the events took place — the time period and historical moment
3. Where — the geographic setting and cultural world the story inhabits
4. What the reader is about to hear — the tone and subject of this account

Rules:
- Write in warm, spoken prose — this will be read aloud
- Do NOT use bullet points, headers, or markdown
- Do NOT say "In this audiobook" or "Welcome to" — open with the author or the world
- Keep it under one hundred words
- End with a natural transition into the text, like "This is his account." or "In his own words."

Return only the introduction text, nothing else."""

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
