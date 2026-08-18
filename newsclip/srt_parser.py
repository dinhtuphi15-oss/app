"""Parse file phụ đề .srt thành danh sách Cue (mốc thời gian + text)."""
from __future__ import annotations

import re
from dataclasses import dataclass

_TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


@dataclass
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


def _to_ms(h: str, m: str, s: str, ms: str) -> int:
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def parse_srt(path: str) -> list[Cue]:
    raw = open(path, encoding="utf-8-sig").read()
    blocks = re.split(r"\r?\n\r?\n+", raw.strip())
    cues: list[Cue] = []
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip() != ""]
        if not lines:
            continue
        time_line_idx = None
        for i, line in enumerate(lines):
            if _TIME_RE.search(line):
                time_line_idx = i
                break
        if time_line_idx is None:
            continue
        m = _TIME_RE.search(lines[time_line_idx])
        assert m is not None
        start_ms = _to_ms(*m.groups()[0:4])
        end_ms = _to_ms(*m.groups()[4:8])
        text_lines = lines[time_line_idx + 1 :]
        text = " ".join(l.strip() for l in text_lines).strip()
        text = re.sub(r"<[^>]+>", "", text)  # bỏ thẻ định dạng <b>, <i>...
        if not text:
            continue
        try:
            index = int(lines[0]) if time_line_idx == 1 else len(cues) + 1
        except ValueError:
            index = len(cues) + 1
        cues.append(Cue(index=index, start_ms=start_ms, end_ms=end_ms, text=text))
    return cues


def ms_to_timecode(ms: int) -> str:
    h, rem = divmod(max(ms, 0), 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms_ = divmod(rem, 1_000)
    return f"{h:02d}-{m:02d}-{s:02d}-{ms_:03d}"
