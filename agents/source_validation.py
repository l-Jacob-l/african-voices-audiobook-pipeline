from typing import List
import requests
from agents.base_agent import BaseAgent
from pipeline.models import SourceRecord

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AudioNarrationBot/1.0)"}
_TIMEOUT = 10


class SourceValidationAgent(BaseAgent):
    """Verifies each source's PDF link is reachable and updates its access field."""

    def run(self, sources: List[SourceRecord]) -> List[SourceRecord]:
        validated = []
        for source in sources:
            access = self._check(source.pdf_link)
            validated.append(source.model_copy(update={"access": access}))
        return validated

    def _check(self, url: str) -> str:
        if not url or not url.startswith("http"):
            return "UNCERTAIN"
        try:
            # Always verify actual bytes — URL extension and Content-Type can lie
            get_resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, stream=True)
            chunk = next(get_resp.iter_content(8), b"")
            get_resp.close()
            return "CONFIRMED" if chunk[:4] == b"%PDF" else "UNCERTAIN"
        except Exception:
            return "UNCERTAIN"
