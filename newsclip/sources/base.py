from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Candidate:
    source: str
    source_id: str
    title: str
    page_url: str
    media_url: Optional[str]  # URL tải trực tiếp; None => cần yt-dlp trên page_url
    thumbnail_url: Optional[str]
    duration_s: Optional[float]
    width: Optional[int]
    height: Optional[int]
    license: str  # vd: "CC0", "CC-BY", "public-domain", "editorial", "unknown"
    published: Optional[str] = None
    query: str = ""
    score: float = 0.0
    notes: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def is_safe_license(self) -> bool:
        return self.license.lower() in {
            "cc0",
            "cc-by",
            "cc-by-sa",
            "public-domain",
            "government-work",
        }


class SourceAdapter:
    name = "base"
    requires_key = False

    def available(self) -> bool:
        return True

    def search(self, query: str, limit: int = 5) -> list[Candidate]:
        raise NotImplementedError
