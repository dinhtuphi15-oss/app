"""Pixabay Video API — cần PIXABAY_API_KEY (miễn phí, đăng ký tại pixabay.com/api/docs)."""
from __future__ import annotations

import requests

from ..config import SETTINGS
from .base import Candidate, SourceAdapter

SEARCH_URL = "https://pixabay.com/api/videos/"


class PixabayAdapter(SourceAdapter):
    name = "pixabay"
    requires_key = True

    def available(self) -> bool:
        return bool(SETTINGS.pixabay_api_key)

    def search(self, query: str, limit: int = 5) -> list[Candidate]:
        if not self.available():
            return []
        try:
            resp = requests.get(
                SEARCH_URL,
                params={
                    "key": SETTINGS.pixabay_api_key,
                    "q": query,
                    "per_page": max(limit, 3),  # API yêu cầu tối thiểu 3
                    "video_type": "film",
                },
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", [])[:limit]
        except Exception:
            return []

        candidates: list[Candidate] = []
        for v in hits:
            videos = v.get("videos", {})
            best = videos.get("large") or videos.get("medium") or videos.get("small")
            if not best or not best.get("url"):
                continue
            candidates.append(
                Candidate(
                    source=self.name,
                    source_id=str(v.get("id")),
                    title=f"Pixabay video #{v.get('id')} (tags: {v.get('tags', '')})",
                    page_url=v.get("pageURL", ""),
                    media_url=best.get("url"),
                    thumbnail_url=(videos.get("tiny") or {}).get("thumbnail"),
                    duration_s=v.get("duration"),
                    width=best.get("width"),
                    height=best.get("height"),
                    license="stock-free",
                    query=query,
                    notes="Pixabay License: miễn phí thương mại, không cần credit.",
                )
            )
        return candidates
