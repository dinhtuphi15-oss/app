# newsclip — tự động tìm B-roll từ file SRT và dựng sẵn timeline CapCut

Công cụ dành cho kênh YouTube tin tức: sau khi có **voice** + **file phụ đề
.srt**, tool sẽ tự đọc từng câu, nhận diện sự kiện/địa danh/khí tài được nhắc
tới, tìm video tư liệu (B-roll) liên quan trên nhiều nguồn, tải về, cắt đúng
độ dài từng đoạn, và **dựng sẵn một project CapCut** với clip đã nằm đúng vị
trí trên timeline theo timecode khớp với voice.

## Vì sao làm theo cách này

- File SRT có sẵn timecode → tool biết chính xác mỗi đoạn cần bao nhiêu giây
  B-roll, không cần bạn tự đo.
- Tên riêng trong tin chiến sự (địa danh, lãnh đạo, khí tài) thường bị phiên
  âm/viết sai khi tạo phụ đề tự động → tool dùng Claude API để chuẩn hoá về
  tên gốc quốc tế trước khi tìm kiếm (vd "Pô-crốp-xcơ" → "Pokrovsk"), vì các
  nguồn video hầu hết được index bằng tiếng Anh/tên gốc, không phải tiếng Việt.
- Mỗi clip được gắn rõ **license** (CC0, CC-BY, public-domain, stock-free,
  editorial, unknown) và xếp hạng ưu tiên license an toàn trước, để bạn giảm
  rủi ro bản quyền/Content ID khi đăng video.

## Cài đặt trên Windows (tự động, không cần gõ lệnh)

1. Tải/clone repo này về máy, giải nén (nếu tải zip) rồi mở thư mục ra.
2. **Double-click `1-cai-dat.bat`** — script sẽ tự cài Python, ffmpeg (qua
   winget) và toàn bộ thư viện cần thiết. Chỉ cần chạy **một lần**.
3. (Khuyến nghị) Mở file `.env` vừa được tạo ra bằng Notepad, dán
   `ANTHROPIC_API_KEY=...` vào (lấy tại console.anthropic.com).
4. Từ lần sau, **double-click `2-chay.bat`** mỗi khi muốn tìm B-roll — script
   sẽ hỏi bạn đường dẫn file `.srt`, file voice, tên project, rồi tự tải clip
   và dựng sẵn project CapCut (tự tìm thư mục drafts của CapCut nếu có).

> Hai script này gọi PowerShell bên trong (`1-cai-dat.ps1`, `2-chay.ps1`) —
> chưa được test trên máy Windows thật, chỉ được kiểm tra cú pháp thủ công.
> Nếu gặp lỗi, gửi lại nguyên văn thông báo lỗi hiện trên màn hình để sửa.

Nếu winget báo lỗi hoặc máy bạn chưa có winget (Windows cũ), cài "App
Installer" từ Microsoft Store rồi chạy lại `1-cai-dat.bat`.

## Cài đặt thủ công (macOS/Linux, hoặc khi muốn tự kiểm soát)

```bash
pip install -r requirements.txt
```

Cần có **ffmpeg** trong PATH (dùng để cắt/chuẩn hoá clip):

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg
# macOS
brew install ffmpeg
```

Copy `.env.example` thành `.env` và điền API key (tất cả đều **tuỳ chọn**,
không có key nào tool vẫn chạy được với nguồn miễn phí Wikimedia Commons +
Internet Archive, nhưng chất lượng truy vấn kém hơn nhiều nếu thiếu
`ANTHROPIC_API_KEY`):

```bash
cp .env.example .env
```

| Biến | Bắt buộc? | Dùng để làm gì | Lấy ở đâu |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Khuyến nghị mạnh | Chuẩn hoá tên riêng, trích thực thể, sinh truy vấn tiếng Anh chất lượng cao | console.anthropic.com |
| `PEXELS_API_KEY` | Tuỳ chọn | Mở nguồn video stock miễn phí Pexels | pexels.com/api |
| `PIXABAY_API_KEY` | Tuỳ chọn | Mở nguồn video stock miễn phí Pixabay | pixabay.com/api/docs |
| `YOUTUBE_API_KEY` | Tuỳ chọn | Tìm video gắn nhãn Creative Commons trên YouTube | Google Cloud Console → bật "YouTube Data API v3" |

Không có `ANTHROPIC_API_KEY`, tool tự chuyển sang chế độ heuristic (dò từ
viết hoa kiểu tên riêng + từ khoá tần suất cao) — vẫn chạy được nhưng kém
chính xác hơn nhiều, đặc biệt với phụ đề tiếng Việt.

## Dùng thử nhanh (không cần key nào)

```bash
python -m newsclip.cli find \
  --srt sample/sample.srt \
  --project-name demo_chien_su \
  --out-dir ./output \
  --sources wikimedia,archive_org
```

Xem kết quả tại `output/demo_chien_su/report.html` trước khi tải clip thật
bằng cách thêm `--dry-run`.

## Dùng thật

```bash
python -m newsclip.cli find \
  --srt kichban.srt \
  --project-name "ChienSu_NgaUA_20260818" \
  --voice voice.mp3 \
  --out-dir ./output \
  --capcut-drafts-dir "$HOME/Movies/CapCut/User Data/Projects/com.lveditor.draft"
```

Sau khi chạy xong:

1. Mở CapCut → project `ChienSu_NgaUA_20260818` đã có sẵn track B-roll đặt
   đúng timecode, track voice (nếu truyền `--voice`), và track phụ đề (nếu
   thêm `--embed-subtitles`).
2. Xem `output/.../report.html` để kiểm tra/đổi lại clip nào chưa ưng ý —
   file được chấm điểm và ghi rõ license từng clip.
3. Clip gốc đã tải nằm ở `output/.../clips/`, đặt tên rõ ràng dạng
   `<số beat>_<timecode bắt đầu>_to_<timecode kết thúc>_<nguồn>_<từ khoá>.mp4`
   để bạn dễ tra lại thủ công nếu cần.

### Nếu không chạy trực tiếp trên máy có cài CapCut

Bỏ qua `--capcut-drafts-dir`, tool sẽ tạo project trong
`output/<project>/capcut_draft/<project>/`. Copy nguyên thư mục
`<project>` đó vào thư mục drafts thật của CapCut:

- macOS: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`
- Windows: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\`

## Các tuỳ chọn CLI chính

| Cờ | Ý nghĩa |
|---|---|
| `--min-beat` / `--max-beat` | Độ dài mục tiêu mỗi "beat" (cảnh B-roll), mặc định 6–15s |
| `--sources` | Giới hạn nguồn tìm kiếm, vd `wikimedia,pexels` |
| `--queries-per-beat` | Số truy vấn thử cho mỗi beat (mặc định 3) |
| `--no-llm` | Tắt Claude API, chỉ dùng heuristic |
| `--keep-audio` | Giữ tiếng gốc của clip B-roll thay vì mute |
| `--embed-subtitles` | Thêm track phụ đề gốc vào project CapCut |
| `--dry-run` | Chỉ tìm kiếm + xuất báo cáo, chưa tải/chưa dựng CapCut |

## Kiến trúc / cách mở rộng thêm nguồn

```
newsclip/
  srt_parser.py     parse .srt -> Cue (timecode + text)
  beats.py          gom Cue -> Beat (cảnh 6–15s)
  nlp.py            Beat -> entities + queries (Claude API / heuristic)
  sources/          adapter cho từng nguồn video, cắm thêm dễ dàng
    base.py         interface Candidate / SourceAdapter
    wikimedia.py     Wikimedia Commons (free, không cần key)
    archive_org.py   Internet Archive (free, không cần key)
    pexels.py        Pexels (cần key, free)
    pixabay.py       Pixabay (cần key, free)
    youtube.py       YouTube Data API, lọc license Creative Commons
  scorer.py          chấm điểm candidate: độ khớp từ khoá + license + độ dài + độ phân giải
  downloader.py      tải (requests / yt-dlp) + cắt + chuẩn hoá bằng ffmpeg
  capcut_export.py   dựng project CapCut qua pyJianYingDraft
  report.py          báo cáo HTML để duyệt trước khi dùng
  cli.py             gộp toàn bộ pipeline
```

Thêm nguồn mới: tạo file trong `sources/`, kế thừa `SourceAdapter`, cài
`available()` và `search(query, limit) -> list[Candidate]`, rồi thêm vào
`ALL_ADAPTERS` trong `sources/__init__.py`.

Nguồn tốt nên cân nhắc thêm sau: Telegram (kênh OSINT chiến sự, qua
Telethon), RSS các báo lớn + scrape thẻ video, Reuters/AP/AFP archive (trả
phí, license rõ ràng nhất).

## Lưu ý bản quyền

Tool ưu tiên xếp hạng clip theo license an toàn (CC0/public-domain/CC-BY/
stock-free) lên trên, nhưng **bạn vẫn nên tự kiểm tra lại** trang mô tả gốc
(`page_url` trong báo cáo) trước khi đăng, đặc biệt với clip từ Wikimedia
Commons (license đôi khi ghi ở cấp trang chi tiết, không chuẩn hoá 100%) và
video "editorial"/"unknown" — những clip này bị chấm điểm thấp nhưng không
bị loại tự động.
