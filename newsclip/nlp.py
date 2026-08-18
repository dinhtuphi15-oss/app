"""Trích thực thể + sinh truy vấn tìm kiếm cho từng beat.

Có 2 chế độ:
  - LLM (khuyến nghị): dùng Claude API để chuẩn hoá tên riêng (vd, phiên âm
    tiếng Việt "Pô-crốp-xcơ" -> "Pokrovsk"), trích địa danh/đơn vị/khí tài,
    và sinh truy vấn tiếng Anh (ngôn ngữ mà đa số nguồn video được index).
  - Fallback không cần key: heuristic đơn giản dựa trên từ viết hoa kiểu
    tên riêng (thường các địa danh/tên khí tài trong tin chiến sự vẫn được
    giữ nguyên dạng Latin ngay trong câu tiếng Việt) + loại bỏ stopword.
"""
from __future__ import annotations

import json
import os
import re

from .beats import Beat
from .config import SETTINGS

DEFAULT_MODEL = os.environ.get("NEWSCLIP_ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

_BATCH_SIZE = 12

_SYSTEM_PROMPT = """Bạn hỗ trợ một tool dựng video tin tức tìm B-roll (video tư liệu) minh hoạ.
Với mỗi đoạn kịch bản (beat), hãy:
1. Chuẩn hoá mọi tên riêng (địa danh, người, tổ chức, khí tài quân sự) về dạng
   gốc/quốc tế thường dùng trên báo chí và YouTube (vd "Pô-crốp-xcơ" -> "Pokrovsk",
   "Xê-len-xki" -> "Zelensky", "tên lửa Ha-mát" -> "HIMARS").
2. Trích các thực thể: locations, organizations, people, weapons (mảng string, có thể rỗng).
3. Xác định event_type ngắn gọn bằng tiếng Anh (vd "drone strike", "tank column",
   "press conference", "protest", "flooding").
4. Sinh 3-6 truy vấn tìm kiếm video BẰNG TIẾNG ANH, xếp từ cụ thể đến chung
   chung (ưu tiên có thể tìm thấy thật trên YouTube/kho video), không thêm
   dấu ngoặc kép.

Trả lời DUY NHẤT một JSON array, không thêm text nào khác, đúng theo schema:
[{"id": <int>, "entities": {"locations": [...], "organizations": [...],
"people": [...], "weapons": [...], "event_type": "..."}, "queries": [...]}]
"""

_VI_EN_STOPWORDS = {
    "là", "và", "của", "cho", "các", "một", "những", "đã", "sẽ", "này", "đó",
    "khi", "để", "với", "trong", "trên", "theo", "tại", "về", "như", "vào",
    "ra", "có", "không", "được", "bị", "vẫn", "còn", "rất", "the", "a", "an",
    "of", "in", "on", "at", "to", "and", "for", "is", "are", "was", "were",
    "that", "this", "with", "by", "as", "it", "its", "has", "have", "had",
}


def analyze_beats(beats: list[Beat], use_llm: bool = True) -> str:
    """Điền beat.entities và beat.queries. Trả về 'llm' hoặc 'heuristic' báo
    chế độ thực sự đã dùng."""
    if use_llm and SETTINGS.anthropic_api_key:
        try:
            _analyze_with_llm(beats)
            return "llm"
        except Exception as exc:  # noqa: BLE001 - fallback an toàn
            print(f"[nlp] Lỗi khi gọi Claude API ({exc}); dùng heuristic thay thế.")
    _analyze_heuristic(beats)
    return "heuristic"


def _analyze_with_llm(beats: list[Beat]) -> None:
    import anthropic  # import trễ để không bắt buộc cài nếu không dùng LLM

    client = anthropic.Anthropic(api_key=SETTINGS.anthropic_api_key)

    for start in range(0, len(beats), _BATCH_SIZE):
        chunk = beats[start : start + _BATCH_SIZE]
        payload = [{"id": b.beat_id, "text": b.text} for b in chunk]
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", "") == "text"
        )
        data = _parse_json_array(text)
        by_id = {item["id"]: item for item in data if "id" in item}
        for beat in chunk:
            item = by_id.get(beat.beat_id)
            if not item:
                continue
            beat.entities = item.get("entities", {})
            beat.queries = [q for q in item.get("queries", []) if q]


def _parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"Không parse được JSON từ phản hồi LLM: {text[:200]!r}")


_PROPER_NOUN_RE = re.compile(r"\b[A-Z][A-Za-z0-9\-]{2,}\b")


def _analyze_heuristic(beats: list[Beat]) -> None:
    for beat in beats:
        proper_nouns = sorted(set(_PROPER_NOUN_RE.findall(beat.text)))
        words = re.findall(r"[\wÀ-ỹ]+", beat.text.lower())
        keywords = [w for w in words if w not in _VI_EN_STOPWORDS and len(w) > 2]
        top_keywords = _top_by_freq(keywords, n=4)

        beat.entities = {
            "locations": [],
            "organizations": [],
            "people": [],
            "weapons": [],
            "event_type": "",
            "_heuristic_terms": proper_nouns,
        }

        queries: list[str] = []
        if proper_nouns:
            queries.append(" ".join(proper_nouns[:3]))
            for noun in proper_nouns[:3]:
                queries.append(noun)
        if top_keywords:
            queries.append(" ".join(top_keywords))
        if not queries:
            queries.append(beat.text[:60])
        # loại trùng, giữ thứ tự
        seen: set[str] = set()
        beat.queries = [q for q in queries if not (q in seen or seen.add(q))]


def _top_by_freq(words: list[str], n: int) -> list[str]:
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:n]]
