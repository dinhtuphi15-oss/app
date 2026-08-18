"""Đọc cấu hình / API key từ biến môi trường hoặc file .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(Path.cwd() / ".env")
_load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Settings:
    anthropic_api_key: str | None = os.environ.get("ANTHROPIC_API_KEY")
    pexels_api_key: str | None = os.environ.get("PEXELS_API_KEY")
    pixabay_api_key: str | None = os.environ.get("PIXABAY_API_KEY")
    youtube_api_key: str | None = os.environ.get("YOUTUBE_API_KEY")

    request_timeout: int = int(os.environ.get("NEWSCLIP_HTTP_TIMEOUT", "20"))
    user_agent: str = os.environ.get(
        "NEWSCLIP_USER_AGENT",
        "newsclip-broll-finder/0.1 (personal news-editing tool; contact: user)",
    )


SETTINGS = Settings()
