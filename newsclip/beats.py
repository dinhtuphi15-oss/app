"""Gom các dòng subtitle (Cue) thành các 'beat' (cảnh cần B-roll)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .srt_parser import Cue

_SENTENCE_END = (".", "!", "?", "…", "。", "!", "?")


@dataclass
class Beat:
    beat_id: int
    start_ms: int
    end_ms: int
    text: str
    cues: list[Cue] = field(default_factory=list)

    entities: dict = field(default_factory=dict)
    queries: list[str] = field(default_factory=list)
    candidates: list = field(default_factory=list)
    chosen: object | None = None
    local_clip_path: str | None = None

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    @property
    def duration_s(self) -> float:
        return self.duration_ms / 1000.0


def group_into_beats(
    cues: list[Cue],
    min_beat_s: float = 6.0,
    max_beat_s: float = 15.0,
    max_gap_ms: int = 1200,
) -> list[Beat]:
    """Gom các cue liền kề thành beat theo độ dài mục tiêu và ranh giới câu.

    Quy tắc: gộp cue tiếp theo vào beat hiện tại nếu:
      - khoảng cách thời gian với cue trước < max_gap_ms, VÀ
      - beat hiện tại chưa đạt max_beat_s.
    Beat được "chốt" khi câu vừa gộp kết thúc bằng dấu câu và đã đạt
    min_beat_s, hoặc khi bắt buộc phải chốt vì sắp vượt max_beat_s.
    """
    if not cues:
        return []

    beats: list[Beat] = []
    current: list[Cue] = [cues[0]]

    def flush(chunk: list[Cue]) -> None:
        if not chunk:
            return
        text = " ".join(c.text for c in chunk).strip()
        beats.append(
            Beat(
                beat_id=len(beats) + 1,
                start_ms=chunk[0].start_ms,
                end_ms=chunk[-1].end_ms,
                text=text,
                cues=list(chunk),
            )
        )

    for prev, cue in zip(cues, cues[1:]):
        gap = cue.start_ms - prev.end_ms
        cur_duration_s = (current[-1].end_ms - current[0].start_ms) / 1000.0
        ends_sentence = prev.text.rstrip().endswith(_SENTENCE_END)

        must_break = gap > max_gap_ms or cur_duration_s >= max_beat_s
        should_break = ends_sentence and cur_duration_s >= min_beat_s

        if must_break or should_break:
            flush(current)
            current = [cue]
        else:
            current.append(cue)

    flush(current)
    return beats
