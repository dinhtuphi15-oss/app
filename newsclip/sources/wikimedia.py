"""Wikimedia Commons: video tư liệu public domain / CC, không cần API key."""
from __future__ import annotations

import requests

from ..config import SETTINGS
from .base import Candidate, SourceAdapter

API_URL = "https://commons.wikimedia.org/w/api.php"


class WikimediaAdapter(SourceAdapter):
    name = "wikimedia"
    requires_key = False

    def available(self) -> bool:
        return True

    def search(self, query: str, limit: int = 5) -> list[Candidate]:
        headers = {"User-Agent": SETTINGS.user_agent}
        try:
            resp = requests.get(
                API_URL,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": f"{query} filetype:video",
                    "srnamespace": 6,
                    "srlimit": limit,
                    "format": "json",
                },
                headers=headers,
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            hits = resp.json().get("query", {}).get("search", [])
        except Exception:
            return []

        candidates: list[Candidate] = []
        for hit in hits:
            title = hit.get("title", "")
            if not title.startswith("File:"):
                continue
            info = self._get_imageinfo(title, headers)
            if info is None:
                continue
            candidates.append(
                Candidate(
                    source=self.name,
                    source_id=title,
                    title=title.removeprefix("File:"),
                    page_url=info.get("descriptionurl", ""),
                    media_url=info.get("url"),
                    thumbnail_url=info.get("thumburl"),
                    duration_s=info.get("duration"),
                    width=info.get("width"),
                    height=info.get("height"),
                    license="public-domain",  # phần lớn media Commons là PD/CC, vẫn cần kiểm tra trang mô tả
                    query=query,
                    notes="Kiểm tra lại license cụ thể trên trang mô tả trước khi dùng.",
                )
            )
        return candidates

    def _get_imageinfo(self, title: str, headers: dict) -> dict | None:
        try:
            resp = requests.get(
                API_URL,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime|duration",
                    "iiurlwidth": 480,
                    "format": "json",
                },
                headers=headers,
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                infos = page.get("imageinfo")
                if infos:
                    return infos[0]
        except Exception:
            return None
        return None
