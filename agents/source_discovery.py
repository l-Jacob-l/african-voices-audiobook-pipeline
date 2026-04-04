import json
import requests
from typing import List, Optional
from agents.base_agent import BaseAgent
from core.config import GPT_MODEL
from pipeline.models import SourceRecord

_IA_SEARCH = "https://archive.org/advancedsearch.php"
_IA_META = "https://archive.org/metadata/{identifier}/files"
_IA_DOWNLOAD = "https://archive.org/download/{identifier}/{filename}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AudioNarrationBot/1.0)"}
_MAX_PDF_BYTES = 10_000_000  # 10MB cap — prefer small, fast PDFs


class SourceDiscoveryAgent(BaseAgent):
    """Two-phase discovery: GPT suggests titles/authors, Internet Archive resolves real PDF URLs."""

    def run(self, region_hint: str = "") -> List[SourceRecord]:
        suggestions = self._get_suggestions(region_hint)
        sources = []
        for suggestion in suggestions:
            record = self._search_archive(suggestion)
            if record:
                sources.append(record)
        return sources

    def _get_suggestions(self, region_hint: str) -> List[dict]:
        region_clause = f"Focus on sources from: {region_hint}." if region_hint else ""
        prompt = f"""You are a specialist in African oral history and archival research.

Suggest 8 well-known, publicly available African first-hand historical texts.
Prioritize: memoirs, oral history transcripts, autobiographies, slave narratives,
or translated oral tradition texts authored by African individuals.
{region_clause}

Return a JSON array. Each object must have exactly:
- "title": the known title of the work
- "author": the author's full name
- "year": year as a string
- "region": African region or country of origin
- "search_query": a short search string to find it on archive.org (2-4 words)

Return only the JSON array."""

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content or ""
        start = content.find("[")
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON array in response:\n{content}")
        return json.loads(content[start:end])

    def _search_archive(self, suggestion: dict) -> Optional[SourceRecord]:
        query = suggestion.get("search_query", suggestion.get("title", ""))
        try:
            resp = requests.get(
                _IA_SEARCH,
                params={"q": f"{query} AND mediatype:texts", "output": "json", "rows": 8},
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            docs = resp.json().get("response", {}).get("docs", [])
        except Exception:
            return None

        for doc in docs:
            if doc.get("mediatype") != "texts":
                continue
            identifier = doc.get("identifier", "")
            record = self._resolve_pdf(identifier, suggestion)
            if record:
                return record
        return None

    def _resolve_pdf(self, identifier: str, suggestion: dict) -> Optional[SourceRecord]:
        """Look up the item's file manifest and find the smallest non-encrypted PDF."""
        try:
            resp = requests.get(
                _IA_META.format(identifier=identifier),
                headers=_HEADERS,
                timeout=10,
            )
            files = resp.json().get("result", [])
        except Exception:
            return None

        pdfs = [
            (f["name"], int(f.get("size", 0)))
            for f in files
            if f.get("name", "").endswith(".pdf")
            and "encrypt" not in f.get("name", "").lower()
            and int(f.get("size", 0)) < _MAX_PDF_BYTES
        ]
        if not pdfs:
            return None

        filename, size = min(pdfs, key=lambda x: x[1])
        url = _IA_DOWNLOAD.format(identifier=identifier, filename=filename)

        if not self._is_real_pdf(url):
            return None

        return SourceRecord(
            title=suggestion.get("title", ""),
            author=suggestion.get("author", ""),
            year=str(suggestion.get("year", "")),
            region=suggestion.get("region", ""),
            source=f"Internet Archive ({identifier})",
            pdf_link=url,
            access="CONFIRMED",
        )

    def _is_real_pdf(self, url: str) -> bool:
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=15, stream=True)
            if resp.status_code != 200:
                resp.close()
                return False
            chunk = next(resp.iter_content(8), b"")
            resp.close()
            return chunk[:4] == b"%PDF"
        except Exception:
            return False
