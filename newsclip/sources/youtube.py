"""YouTube Data API v3 — cần YOUTUBE_API_KEY. Chỉ tìm video gắn nhãn Creative Commons
để giảm rủi ro bản quyền; việc tải thực tế do downloader.py xử lý qua yt-dlp."""
from __future__ import annotations

import requests

from ..config import SETTINGS
from .base import Candidate, SourceAdapter

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeAdapter(SourceAdapter):
    name = "youtube"
    requires_key = True

    def available(self) -> bool:
        return bool(SETTINGS.youtube_api_key)

    def search(self, query: str, limit: int = 5) -> list[Candidate]:
        if not self.available():
            return []
        try:
            resp = requests.get(
                SEARCH_URL,
                params={
                    "key": SETTINGS.youtube_api_key,
                    "q": query,
                    "part": "snippet",
                    "type": "video",
                    "videoLicense": "creativeCommon",
                    "maxResults": limit,
                    "safeSearch": "none",
                    "relevanceLanguage": "en",
                },
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception:
            return []

        video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
        durations = self._fetch_durations(video_ids)

        candidates: list[Candidate] = []
        for it in items:
            vid = it.get("id", {}).get("videoId")
            if not vid:
                continue
            snippet = it.get("snippet", {})
            thumb = (
                snippet.get("thumbnails", {}).get("high")
                or snippet.get("thumbnails", {}).get("default")
                or {}
            )
            candidates.append(
                Candidate(
                    source=self.name,
                    source_id=vid,
                    title=snippet.get("title", vid),
                    page_url=f"https://www.youtube.com/watch?v={vid}",
                    media_url=None,  # tải qua yt-dlp
                    thumbnail_url=thumb.get("url"),
                    duration_s=durations.get(vid),
                    width=None,
                    height=None,
                    license="CC-BY",  # videoLicense=creativeCommon => CC BY theo YouTube ToS
                    published=snippet.get("publishedAt"),
                    query=query,
                    notes=f"Kênh: {snippet.get('channelTitle', '')}",
                )
            )
        return candidates

    def _fetch_durations(self, video_ids: list[str]) -> dict[str, float]:
        if not video_ids:
            return {}
        try:
            resp = requests.get(
                VIDEOS_URL,
                params={
                    "key": SETTINGS.youtube_api_key,
                    "id": ",".join(video_ids),
                    "part": "contentDetails",
                },
                timeout=SETTINGS.request_timeout,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception:
            return {}
        out: dict[str, float] = {}
        for it in items:
            vid = it.get("id")
            dur_iso = it.get("contentDetails", {}).get("duration")
            if vid and dur_iso:
                out[vid] = _iso8601_duration_to_seconds(dur_iso)
        return out


def _iso8601_duration_to_seconds(iso: str) -> float:
    import re

    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0.0
    h, mnt, s = (int(g) if g else 0 for g in m.groups())
    return float(h * 3600 + mnt * 60 + s)
