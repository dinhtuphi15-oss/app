"""Internet Archive: kho video tin tức/tư liệu, không cần API key."""
from __future__ import annotations

import requests

from ..config import SETTINGS
from .base import Candidate, SourceAdapter

SEARCH_URL = "https://archive.org/advancedsearch.php"
METADATA_URL = "https://archive.org/metadata/{identifier}"
DOWNLOAD_URL = "https://archive.org/download/{identifier}/{filename}"

_VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".webm")


class ArchiveOrgAdapter(SourceAdapter):
    name = "archive_org"
    requires_key = False

    def available(self) -> bool:
        return True

    def search(self, query: str, limit: int = 5) -> list[Candidate]:
        headers = {"User-Agent": SETTINGS.user_agent}
        try:
            resp = requests.get(
                SEARCH_URL,
                params={
                    "q": f'({query}) AND mediatype:(movies)',
                    "fl[]": ["identifier", "title", "licenseurl", "date"],
                    "rows": limit,
                    "output": "json",
                },
                headers=headers,
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            docs = resp.json().get("response", {}).get("docs", [])
        except Exception:
            return []

        candidates: list[Candidate] = []
        for doc in docs:
            identifier = doc.get("identifier")
            if not identifier:
                continue
            cand = self._build_candidate(identifier, doc, query, headers)
            if cand:
                candidates.append(cand)
        return candidates

    def _build_candidate(
        self, identifier: str, doc: dict, query: str, headers: dict
    ) -> Candidate | None:
        try:
            resp = requests.get(
                METADATA_URL.format(identifier=identifier),
                headers=headers,
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            meta = resp.json()
        except Exception:
            return None

        video_file = None
        for f in meta.get("files", []):
            name = f.get("name", "")
            if name.lower().endswith(_VIDEO_EXTS) and f.get("source") == "original":
                video_file = f
                break
        if video_file is None:
            for f in meta.get("files", []):
                if f.get("name", "").lower().endswith(_VIDEO_EXTS):
                    video_file = f
                    break
        if video_file is None:
            return None

        license_url = doc.get("licenseurl", "") or meta.get("metadata", {}).get(
            "licenseurl", ""
        )
        license_label = "public-domain" if "publicdomain" in license_url else (
            "CC-BY" if "creativecommons" in license_url else "unknown"
        )

        duration = None
        try:
            duration = float(video_file.get("length")) if video_file.get("length") else None
        except (TypeError, ValueError):
            duration = None

        return Candidate(
            source=self.name,
            source_id=identifier,
            title=doc.get("title", identifier),
            page_url=f"https://archive.org/details/{identifier}",
            media_url=DOWNLOAD_URL.format(
                identifier=identifier, filename=video_file["name"]
            ),
            thumbnail_url=f"https://archive.org/services/img/{identifier}",
            duration_s=duration,
            width=int(video_file["width"]) if video_file.get("width") else None,
            height=int(video_file["height"]) if video_file.get("height") else None,
            license=license_label,
            published=doc.get("date"),
            query=query,
        )
