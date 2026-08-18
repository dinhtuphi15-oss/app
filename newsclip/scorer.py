"""Chấm điểm & xếp hạng candidate cho mỗi beat."""
from __future__ import annotations

import re

from .beats import Beat
from .sources.base import Candidate

_LICENSE_WEIGHT = {
    "cc0": 1.0,
    "public-domain": 1.0,
    "government-work": 0.95,
    "cc-by": 0.85,
    "cc-by-sa": 0.8,
    "stock-free": 0.75,
    "editorial": 0.4,
    "unknown": 0.3,
}


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[\wÀ-ỹ]+", text.lower()))


def score_candidate(beat: Beat, candidate: Candidate) -> float:
    query_tokens = _tokenize(candidate.query or "")
    title_tokens = _tokenize(candidate.title or "")
    beat_tokens = _tokenize(beat.text)

    relevance = 0.0
    if query_tokens and title_tokens:
        overlap = len(query_tokens & title_tokens)
        relevance += overlap / max(len(query_tokens), 1) * 0.6
    if beat_tokens and title_tokens:
        overlap2 = len(beat_tokens & title_tokens)
        relevance += min(overlap2 / max(len(beat_tokens), 1), 1.0) * 0.4

    license_score = _LICENSE_WEIGHT.get(candidate.license.lower(), 0.3)

    duration_score = 0.5
    if candidate.duration_s:
        if candidate.duration_s >= beat.duration_s:
            duration_score = 1.0
        else:
            duration_score = max(candidate.duration_s / max(beat.duration_s, 0.1), 0.1)

    resolution_score = 0.5
    if candidate.width and candidate.height:
        resolution_score = min(candidate.width / 1920, 1.0) * 0.5 + min(
            candidate.height / 1080, 1.0
        ) * 0.5

    score = (
        relevance * 0.45
        + license_score * 0.25
        + duration_score * 0.2
        + resolution_score * 0.1
    )
    return round(score, 4)


def rank_candidates(beat: Beat, candidates: list[Candidate]) -> list[Candidate]:
    for c in candidates:
        c.score = score_candidate(beat, c)
    return sorted(candidates, key=lambda c: c.score, reverse=True)


def dedup_by_source_id(candidates: list[Candidate], used: set[tuple[str, str]]) -> list[Candidate]:
    """Loại các candidate đã được chọn ở beat khác (tránh lặp cùng 1 clip)."""
    return [c for c in candidates if (c.source, c.source_id) not in used]
