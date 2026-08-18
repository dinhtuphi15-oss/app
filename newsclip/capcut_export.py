"""Dựng project CapCut (.draft) sẵn timeline từ các beat đã có clip B-roll."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pyJianYingDraft as draft

from .beats import Beat

US_PER_MS = 1000  # microsecond = ms * 1000 (đơn vị nội bộ của CapCut là microsecond)


def _probe_duration_s(path: str) -> float | None:
    if shutil.which("ffprobe") is None:
        return None
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json", path,
            ],
            capture_output=True, text=True, timeout=20,
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return None


def build_capcut_draft(
    project_name: str,
    beats: list[Beat],
    *,
    drafts_root: str,
    voice_path: str | None = None,
    srt_path: str | None = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    allow_replace: bool = True,
) -> Path:
    """Tạo draft CapCut trong `drafts_root/project_name/`.

    `drafts_root` nên trỏ thẳng tới thư mục drafts thật của CapCut
    (vd `~/Movies/CapCut/User Data/Projects/com.lveditor.draft` trên macOS,
    hoặc `%LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft`
    trên Windows) nếu chạy ngay trên máy có cài CapCut. Nếu chạy ở môi
    trường khác, cứ tạo ra thư mục project bình thường rồi copy thủ công
    vào thư mục drafts của CapCut sau.
    """
    Path(drafts_root).mkdir(parents=True, exist_ok=True)
    folder = draft.DraftFolder(drafts_root)
    script = folder.create_draft(
        project_name, width, height, fps, allow_replace=allow_replace
    )

    broll_track = script.append_track(draft.TrackSpec(draft.TrackType.video, name="broll"))

    placed = 0
    for beat in beats:
        if not beat.local_clip_path:
            continue
        clip_duration_s = _probe_duration_s(beat.local_clip_path) or beat.duration_s
        use_duration_s = min(clip_duration_s, beat.duration_s)
        try:
            material = draft.VideoMaterial(beat.local_clip_path)
            segment = draft.VideoSegment(
                material,
                draft.Timerange(
                    start=beat.start_ms * US_PER_MS,
                    duration=round(use_duration_s * 1_000_000),
                ),
            )
            script.add_segment(segment, track=broll_track)
            placed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[capcut_export] Bỏ qua beat #{beat.beat_id}: {exc}")

    if voice_path:
        voice_track = script.append_track(draft.TrackSpec(draft.TrackType.audio, name="voice"))
        voice_duration_s = _probe_duration_s(voice_path)
        total_s = voice_duration_s or (beats[-1].end_ms / 1000.0 if beats else 0)
        audio_material = draft.AudioMaterial(voice_path)
        audio_segment = draft.AudioSegment(
            audio_material,
            draft.Timerange(start=0, duration=round(total_s * 1_000_000)),
        )
        script.add_segment(audio_segment, track=voice_track)

    if srt_path:
        try:
            script.import_srt(srt_path, "phu_de")
        except Exception as exc:  # noqa: BLE001
            print(f"[capcut_export] Không import được SRT vào track text: {exc}")

    script.save()
    print(f"[capcut_export] Đã đặt {placed}/{len(beats)} clip lên timeline.")
    return Path(drafts_root) / project_name
