from agents.base_agent import BaseAgent
from core.config import GPT_MODEL


class ScriptFormatterAgent(BaseAgent):
    def run(self, text: str) -> str:
        prompt = f"""You are preparing a historical document for text-to-speech narration.

Your ONLY job is light formatting for speech. You must NOT change, summarize, rephrase, or omit any words.
Every sentence from the original must appear in your output, word for word.

Allowed changes only:
- Spell out numbers (e.g. "3" -> "three", "1745" -> "seventeen forty-five")
- Spell out abbreviations (e.g. "Dr." -> "Doctor", "Vol." -> "Volume", "viz." -> "namely")
- Replace symbols with words (e.g. "&" -> "and", "%" -> "percent")
- Add "..." after commas or between long clauses where a natural breath would occur
- Remove page numbers, running headers, and archive watermarks only

Do NOT:
- Summarize, condense, or paraphrase anything
- Add any words, labels, or commentary of your own
- Skip any sentences or paragraphs
- Reorder or restructure anything
- Modernize or simplify the language — preserve the original voice exactly

Text:
{text}

Return only the lightly formatted text, nothing else."""

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
