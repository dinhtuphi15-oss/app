"""Tải candidate đã chọn về, cắt đúng độ dài beat, chuẩn hoá codec, đặt tên rõ ràng."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import requests

from .beats import Beat
from .config import SETTINGS
from .srt_parser import ms_to_timecode
from .sources.base import Candidate

_BUFFER_S = 1.5  # tải dư một chút để ffmpeg có margin khi cắt


def slugify(text: str, max_len: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:max_len] or "clip"


def clip_filename(beat: Beat, candidate: Candidate) -> str:
    start_tc = ms_to_timecode(beat.start_ms)
    end_tc = ms_to_timecode(beat.end_ms)
    slug = slugify(candidate.query or candidate.title)
    return f"{beat.beat_id:03d}_{start_tc}_to_{end_tc}_{candidate.source}_{slug}.mp4"


def download_and_trim(
    beat: Beat,
    candidate: Candidate,
    out_dir: Path,
    strip_audio: bool = True,
) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = out_dir / clip_filename(beat, candidate)
    if final_path.exists():
        return final_path

    with tempfile.TemporaryDirectory(prefix="newsclip_") as tmp:
        raw_path = Path(tmp) / "raw_input"
        try:
            if candidate.media_url:
                ok = _download_direct(candidate.media_url, raw_path)
            elif candidate.source == "youtube":
                raw_path = raw_path.with_suffix(".mp4")
                ok = _download_youtube(candidate.page_url, raw_path, beat.duration_s)
            else:
                ok = False
        except Exception as exc:  # noqa: BLE001
            print(f"[downloader] Lỗi tải beat #{beat.beat_id} ({candidate.source}): {exc}")
            ok = False

        if not ok or not raw_path.exists() or raw_path.stat().st_size == 0:
            return None

        return _trim_and_encode(raw_path, final_path, beat.duration_s, strip_audio)


def _download_direct(url: str, dest: Path) -> bool:
    headers = {"User-Agent": SETTINGS.user_agent}
    with requests.get(url, headers=headers, stream=True, timeout=SETTINGS.request_timeout * 3) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    return dest.exists() and dest.stat().st_size > 0


def _download_youtube(page_url: str, dest: Path, needed_duration_s: float) -> bool:
    import yt_dlp
    from yt_dlp.utils import download_range_func

    end = needed_duration_s + _BUFFER_S
    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(dest.with_suffix("")) + ".%(ext)s",
        "download_ranges": download_range_func(None, [(0, end)]),
        "force_keyframes_at_cuts": True,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([page_url])

    if dest.exists():
        return True
    candidates = list(dest.parent.glob(dest.stem + ".*"))
    if candidates:
        candidates[0].rename(dest)
        return True
    return False


def _trim_and_encode(raw_path: Path, final_path: Path, duration_s: float, strip_audio: bool) -> Path | None:
    if shutil.which("ffmpeg") is None:
        shutil.copy(raw_path, final_path)
        return final_path

    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_path),
        "-t", f"{duration_s:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-vf", "scale='min(1920,iw)':'-2'",
    ]
    if strip_audio:
        cmd += ["-an"]
    else:
        cmd += ["-c:a", "aac", "-b:a", "128k"]
    cmd += [str(final_path)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not final_path.exists():
        print(f"[downloader] ffmpeg lỗi: {result.stderr[-500:]}")
        return None
    return final_path
