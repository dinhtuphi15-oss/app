"""Pexels Videos API — cần PEXELS_API_KEY (miễn phí, đăng ký tại pexels.com/api)."""
from __future__ import annotations

import requests

from ..config import SETTINGS
from .base import Candidate, SourceAdapter

SEARCH_URL = "https://api.pexels.com/videos/search"


class PexelsAdapter(SourceAdapter):
    name = "pexels"
    requires_key = True

    def available(self) -> bool:
        return bool(SETTINGS.pexels_api_key)

    def search(self, query: str, limit: int = 5) -> list[Candidate]:
        if not self.available():
            return []
        try:
            resp = requests.get(
                SEARCH_URL,
                params={"query": query, "per_page": limit, "orientation": "landscape"},
                headers={"Authorization": SETTINGS.pexels_api_key},
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            videos = resp.json().get("videos", [])
        except Exception:
            return []

        candidates: list[Candidate] = []
        for v in videos:
            files = sorted(
                (f for f in v.get("video_files", []) if f.get("link")),
                key=lambda f: (f.get("width") or 0),
                reverse=True,
            )
            best = next((f for f in files if 1000 <= (f.get("width") or 0) <= 1920), None)
            best = best or (files[0] if files else None)
            if best is None:
                continue
            candidates.append(
                Candidate(
                    source=self.name,
                    source_id=str(v.get("id")),
                    title=f"Pexels video #{v.get('id')} ({v.get('user', {}).get('name', '')})",
                    page_url=v.get("url", ""),
                    media_url=best.get("link"),
                    thumbnail_url=v.get("image"),
                    duration_s=v.get("duration"),
                    width=best.get("width"),
                    height=best.get("height"),
                    license="stock-free",
                    query=query,
                    notes="Pexels License: miễn phí thương mại, không cần credit.",
                )
            )
        return candidates
