"""Xuất báo cáo HTML tự chứa để duyệt nhanh candidate của từng beat."""
from __future__ import annotations

import html
from pathlib import Path

from .beats import Beat
from .srt_parser import ms_to_timecode

_LICENSE_COLOR = {
    "cc0": "#0a7d2c", "public-domain": "#0a7d2c", "government-work": "#0a7d2c",
    "cc-by": "#1a7fd6", "cc-by-sa": "#1a7fd6", "stock-free": "#1a7fd6",
    "editorial": "#c77700", "unknown": "#b02a2a",
}

_CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:980px;margin:0 auto;
  padding:24px;background:#fafafa;color:#1a1a1a;}
h1{font-size:22px;} h2{font-size:16px;margin:0 0 4px;}
.beat{border:1px solid #ddd;border-radius:10px;padding:14px 16px;margin-bottom:16px;background:#fff;}
.meta{color:#666;font-size:13px;margin-bottom:6px;}
.text{font-size:15px;margin-bottom:8px;}
.queries{font-size:12px;color:#555;margin-bottom:10px;}
.queries code{background:#f0f0f0;padding:1px 5px;border-radius:4px;margin-right:4px;}
.cands{display:flex;flex-wrap:wrap;gap:10px;}
.cand{width:200px;border:1px solid #e2e2e2;border-radius:8px;overflow:hidden;font-size:12px;}
.cand.chosen{border:2px solid #0a7d2c;box-shadow:0 0 0 2px #d7f2df;}
.cand img{width:100%;height:110px;object-fit:cover;background:#eee;display:block;}
.cand .body{padding:8px;}
.badge{display:inline-block;padding:1px 6px;border-radius:4px;color:#fff;font-size:10px;}
.score{color:#333;font-weight:600;}
.nowarn{color:#999;font-style:italic;font-size:13px;}
.chosen-tag{background:#0a7d2c;color:#fff;font-size:10px;padding:1px 6px;border-radius:4px;}
a{color:#1a5fd6;text-decoration:none;}
"""


def build_report(beats: list[Beat], title: str = "Báo cáo B-roll") -> str:
    parts = [
        "<!doctype html><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title><style>{_CSS}</style>",
        f"<h1>{html.escape(title)}</h1>",
        f"<p class='meta'>{len(beats)} beat &middot; "
        f"{sum(1 for b in beats if b.local_clip_path)} đã có clip B-roll</p>",
    ]

    for beat in beats:
        start_tc = ms_to_timecode(beat.start_ms).replace("-", ":")
        end_tc = ms_to_timecode(beat.end_ms).replace("-", ":")
        parts.append("<div class='beat'>")
        parts.append(
            f"<h2>Beat #{beat.beat_id} &nbsp;"
            f"<span class='meta'>{start_tc} → {end_tc} "
            f"({beat.duration_s:.1f}s)</span></h2>"
        )
        parts.append(f"<div class='text'>{html.escape(beat.text)}</div>")
        if beat.queries:
            q_html = " ".join(f"<code>{html.escape(q)}</code>" for q in beat.queries)
            parts.append(f"<div class='queries'>Truy vấn: {q_html}</div>")

        if not beat.candidates:
            parts.append("<div class='nowarn'>Không tìm thấy candidate nào.</div>")
        else:
            parts.append("<div class='cands'>")
            for cand in beat.candidates[:6]:
                is_chosen = beat.chosen is not None and (
                    cand.source == beat.chosen.source and cand.source_id == beat.chosen.source_id
                )
                license_color = _LICENSE_COLOR.get(cand.license.lower(), "#b02a2a")
                thumb = cand.thumbnail_url or ""
                cls = "cand chosen" if is_chosen else "cand"
                parts.append(f"<div class='{cls}'>")
                if thumb:
                    parts.append(f"<img src='{html.escape(thumb)}' loading='lazy'>")
                parts.append("<div class='body'>")
                if is_chosen:
                    parts.append("<span class='chosen-tag'>ĐÃ CHỌN</span> ")
                parts.append(
                    f"<span class='badge' style='background:{license_color}'>"
                    f"{html.escape(cand.license)}</span> "
                    f"<span class='score'>{cand.score:.2f}</span><br>"
                )
                title_short = (cand.title or "")[:70]
                parts.append(
                    f"<a href='{html.escape(cand.page_url)}' target='_blank'>"
                    f"{html.escape(title_short)}</a><br>"
                )
                parts.append(f"<span class='meta'>nguồn: {html.escape(cand.source)}</span>")
                if cand.duration_s:
                    parts.append(f" &middot; {cand.duration_s:.0f}s")
                parts.append("</div></div>")
            parts.append("</div>")
        parts.append("</div>")

    return "".join(parts)


def write_report(beats: list[Beat], out_path: Path, title: str = "Báo cáo B-roll") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_report(beats, title=title), encoding="utf-8")
    return out_path
