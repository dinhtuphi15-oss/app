"""CLI: SRT -> tìm B-roll -> tải clip -> dựng sẵn timeline CapCut.

Ví dụ:
    python -m newsclip.cli find \\
        --srt kichban.srt \\
        --project-name "ChienSu_NgaUA_20260818" \\
        --voice voice.mp3 \\
        --out-dir ./output
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import capcut_export, nlp, report
from .beats import group_into_beats
from .downloader import download_and_trim
from .scorer import rank_candidates
from .sources import ALL_ADAPTERS
from .srt_parser import parse_srt

_DEFAULT_SOURCE_NAMES = [a.name for a in ALL_ADAPTERS]


def _build_adapters(names: list[str]):
    by_name = {a.name: a for a in ALL_ADAPTERS}
    adapters = []
    for n in names:
        cls = by_name.get(n)
        if cls is None:
            print(f"[cli] Bỏ qua nguồn không tồn tại: {n}", file=sys.stderr)
            continue
        adapter = cls()
        if adapter.available():
            adapters.append(adapter)
        elif adapter.requires_key:
            print(f"[cli] Nguồn '{n}' cần API key, đang bỏ qua (xem README/.env.example).")
    return adapters


def cmd_find(args: argparse.Namespace) -> int:
    srt_path = Path(args.srt)
    if not srt_path.exists():
        print(f"Không tìm thấy file SRT: {srt_path}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir) / args.project_name
    clips_dir = out_dir / "clips"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/6] Đọc SRT: {srt_path}")
    cues = parse_srt(str(srt_path))
    print(f"   -> {len(cues)} dòng phụ đề")

    print("[2/6] Gom thành beat (cảnh cần B-roll)...")
    beats = group_into_beats(cues, min_beat_s=args.min_beat, max_beat_s=args.max_beat)
    print(f"   -> {len(beats)} beat")

    print("[3/6] Trích thực thể + sinh truy vấn tìm kiếm...")
    mode = nlp.analyze_beats(beats, use_llm=not args.no_llm)
    print(f"   -> chế độ: {mode}"
          + ("" if mode == "llm" else " (đặt ANTHROPIC_API_KEY để có kết quả tốt hơn nhiều)"))

    source_names = args.sources.split(",") if args.sources else _DEFAULT_SOURCE_NAMES
    adapters = _build_adapters(source_names)
    if not adapters:
        print("Không có nguồn nào khả dụng (thiếu API key?). Dừng lại.", file=sys.stderr)
        return 1
    print(f"[4/6] Tìm kiếm trên {len(adapters)} nguồn: {[a.name for a in adapters]}")

    used: set[tuple[str, str]] = set()
    for beat in beats:
        candidates = []
        for query in beat.queries[: args.queries_per_beat]:
            for adapter in adapters:
                try:
                    candidates.extend(adapter.search(query, limit=args.candidates_per_source))
                except Exception as exc:  # noqa: BLE001
                    print(f"   ! lỗi nguồn {adapter.name} với query '{query}': {exc}")
        beat.candidates = rank_candidates(beat, candidates)
        for cand in beat.candidates:
            if (cand.source, cand.source_id) not in used:
                beat.chosen = cand
                used.add((cand.source, cand.source_id))
                break
        status = beat.chosen.source if beat.chosen else "KHÔNG TÌM THẤY"
        print(f"   beat #{beat.beat_id:03d} ({beat.duration_s:4.1f}s): {status}")

    if args.dry_run:
        report_path = report.write_report(beats, out_dir / "report.html", title=args.project_name)
        print(f"[5/6] (dry-run) Bỏ qua tải clip / dựng CapCut.")
        print(f"[6/6] Báo cáo: {report_path}")
        return 0

    print("[5/6] Tải & cắt clip...")
    for beat in beats:
        ranked = beat.candidates
        for cand in ranked:
            path = download_and_trim(beat, cand, clips_dir, strip_audio=not args.keep_audio)
            if path:
                beat.chosen = cand
                beat.local_clip_path = str(path)
                print(f"   beat #{beat.beat_id:03d}: OK -> {path.name}")
                break
        else:
            print(f"   beat #{beat.beat_id:03d}: tải thất bại tất cả candidate, bỏ trống.")

    n_ok = sum(1 for b in beats if b.local_clip_path)
    print(f"   -> {n_ok}/{len(beats)} beat có clip.")

    print("[6/6] Dựng project CapCut + báo cáo HTML...")
    drafts_root = args.capcut_drafts_dir or str(out_dir / "capcut_draft")
    project_dir = capcut_export.build_capcut_draft(
        args.project_name,
        beats,
        drafts_root=drafts_root,
        voice_path=args.voice,
        srt_path=str(srt_path) if args.embed_subtitles else None,
        width=args.width,
        height=args.height,
        fps=args.fps,
    )
    report_path = report.write_report(beats, out_dir / "report.html", title=args.project_name)

    print()
    print("Xong.")
    print(f"  Clip đã tải : {clips_dir}")
    print(f"  Báo cáo HTML: {report_path}")
    print(f"  Project CapCut: {project_dir}")
    if not args.capcut_drafts_dir:
        print(
            "  (Chưa chỉ định --capcut-drafts-dir nên project được tạo trong thư mục output.\n"
            "   Copy cả thư mục này vào thư mục drafts thật của CapCut để mở, vd:\n"
            "   macOS : ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/\n"
            "   Windows: %LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft\\)"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="newsclip", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("find", help="Tìm & dựng B-roll từ file SRT")
    f.add_argument("--srt", required=True, help="Đường dẫn file phụ đề .srt")
    f.add_argument("--project-name", required=True, help="Tên project (cũng là tên thư mục output)")
    f.add_argument("--out-dir", default="./output", help="Thư mục output gốc")
    f.add_argument("--voice", default=None, help="File audio voice để đặt vào track thoại")
    f.add_argument(
        "--capcut-drafts-dir",
        default=None,
        help="Thư mục drafts thật của CapCut trên máy bạn. "
        "Nếu bỏ trống sẽ tạo project trong thư mục output để bạn tự copy.",
    )
    f.add_argument("--min-beat", type=float, default=6.0, help="Độ dài tối thiểu mỗi beat (giây)")
    f.add_argument("--max-beat", type=float, default=15.0, help="Độ dài tối đa mỗi beat (giây)")
    f.add_argument("--queries-per-beat", type=int, default=3, help="Số truy vấn thử cho mỗi beat")
    f.add_argument("--candidates-per-source", type=int, default=5, help="Số kết quả lấy mỗi nguồn/truy vấn")
    f.add_argument(
        "--sources", default=None,
        help=f"Danh sách nguồn, phân tách bởi dấu phẩy. Mặc định tất cả: {','.join(_DEFAULT_SOURCE_NAMES)}",
    )
    f.add_argument("--no-llm", action="store_true", help="Không dùng Claude API, chỉ heuristic")
    f.add_argument("--keep-audio", action="store_true", help="Giữ lại audio gốc của clip B-roll")
    f.add_argument("--embed-subtitles", action="store_true", help="Thêm track phụ đề từ SRT gốc vào project")
    f.add_argument("--width", type=int, default=1920)
    f.add_argument("--height", type=int, default=1080)
    f.add_argument("--fps", type=int, default=30)
    f.add_argument("--dry-run", action="store_true", help="Chỉ tìm & xuất báo cáo, không tải/không dựng CapCut")
    f.set_defaults(func=cmd_find)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
