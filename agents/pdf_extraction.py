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
                return self._clean(raw_text, source)
            except Exception as e:
                print(f"  Failed ({e}), trying next source...")

        raise ValueError("All CONFIRMED sources failed PDF extraction.")

    def _download_and_extract(self, url: str) -> str:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        response.raise_for_status()

        reader = pypdf.PdfReader(io.BytesIO(response.content))
        pages = reader.pages[:_MAX_PAGES]
        return "\n\n".join(page.extract_text() or "" for page in pages)

    def _clean(self, raw_text: str, source: SourceRecord) -> str:
        prompt = f"""You are preparing a historical African text for audiobook narration.

Source: "{source.title}" by {source.author} ({source.year}), {source.region}

The text below was extracted from a PDF and may contain OCR artifacts, page numbers,
headers, footnotes, or garbled characters. Clean it into readable, continuous prose
that preserves the original voice and meaning faithfully.

Rules:
- Remove page numbers, headers, footers, and footnotes
- Fix obvious OCR errors (e.g. "l" mistaken for "1", broken words)
- Preserve all proper names, place names, and culturally specific terms exactly
- Do not summarize or paraphrase — keep the full content
- Return only the cleaned text, no commentary

Raw text:
{raw_text[:8000]}"""

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
