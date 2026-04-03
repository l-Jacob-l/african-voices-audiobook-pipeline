import io
import requests
import pypdf
from typing import List
from agents.base_agent import BaseAgent
from core.config import GPT_MODEL
from pipeline.models import SourceRecord

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AudioNarrationBot/1.0)"}
_TIMEOUT = 30
_MAX_PAGES = 20  # cap extraction to keep token usage reasonable


class PDFExtractionAgent(BaseAgent):
    """Downloads the first CONFIRMED source PDF and extracts clean text.

    Falls back to GPT-based cleaning to remove OCR artifacts and non-speakable
    characters before the text enters the narration pipeline.
    """

    def run(self, sources: List[SourceRecord]) -> str:
        confirmed = [s for s in sources if s.access == "CONFIRMED"]
        if not confirmed:
            raise ValueError("No CONFIRMED sources available for extraction.")

        for source in confirmed:
            print(f"  Extracting: {source.title} ({source.pdf_link})")
            try:
                raw_text = self._download_and_extract(source.pdf_link)
                if not self._is_english(raw_text):
                    print(f"  Skipping — text is not in English")
                    continue
                return self._clean(raw_text, source)
            except Exception as e:
                print(f"  Failed ({e}), trying next source...")

        raise ValueError("All CONFIRMED sources failed PDF extraction.")

    # Common non-English function words — presence of several strongly indicates non-English
    _NON_ENGLISH_MARKERS = [
        "est ", "les ", "des ", "une ", "dans ", "pour ", "que ", "qui ",  # French
        "der ", "die ", "das ", "und ", "ein ", "ist ", "nicht ",          # German
        "los ", "las ", "una ", "del ", "por ", "que ", "con ",            # Spanish
        "della ", "degli ", "nella ", "sono ", "questo ",                  # Italian
        "de ", "het ", "een ", "van ", "niet ", "met ",                    # Dutch
    ]

    def _is_english(self, text: str) -> bool:
        sample = text[:1000].lower()
        hits = sum(1 for marker in self._NON_ENGLISH_MARKERS if marker in sample)
        return hits < 4

    def _download_and_extract(self, url: str) -> str:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        response.raise_for_status()

        reader = pypdf.PdfReader(io.BytesIO(response.content))
        pages = reader.pages[:_MAX_PAGES]
        return "\n\n".join(page.extract_text() or "" for page in pages)

    _REFUSAL_MARKERS = [
        "i'm unable", "i am unable", "i cannot", "i'm sorry",
        "i apologize", "would you like", "instead?", "however,",
        "as an ai", "i don't have access",
    ]

    def _clean(self, raw_text: str, source: SourceRecord) -> str:
        prompt = f"""You are a text editor preparing a raw PDF extract for audiobook narration.

Your ONLY job is to clean the raw text below. You must output the cleaned text and nothing else.
Do NOT comment, refuse, summarize, explain, or add any words of your own.
Do NOT say "I'm unable" or anything similar — just clean and return the text.

Cleaning rules:
- Remove page numbers, headers, footers, and footnotes
- Fix obvious OCR errors (broken words, "l" mistaken for "1", etc.)
- Preserve all proper names, place names, and culturally specific terms exactly
- Do not summarize or paraphrase — reproduce the full content faithfully
- Output continuous readable prose only

Source: "{source.title}" by {source.author} ({source.year}), {source.region}

Raw text:
{raw_text[:8000]}"""

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        cleaned = response.choices[0].message.content or ""

        # If GPT refused or gave a meta-response, fall back to raw text
        cleaned_lower = cleaned.lower()
        if any(marker in cleaned_lower for marker in self._REFUSAL_MARKERS):
            return raw_text.strip()

        return cleaned
