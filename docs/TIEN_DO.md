# Tiến độ

File này ghi lại việc đã xong, việc đang dở, lệnh để chạy lại và việc tiếp theo. Cập nhật sau mỗi phiên việc. Lịch sử trước 27/10/2026 xem `docs/AI_USAGE.md` và các báo cáo trong `docs/giai-doan/`.

## 02/11/2026: nhánh `phuc-music`, Harmony Lab chế độ Bài hát (Bước 0 → 5)

**Đã xong** (báo cáo `docs/phuc-music/BAO_CAO_CAU_TRUC_BAI_HAT.md`, ADR-013 đề xuất, sổ tay `docs/backing-track/CAU_TRUC_BAI_HAT.md`)
- Backend `POST /api/v1/composition/song`: 9 loại đoạn, năng lượng 1–5, chuyển đoạn (fill, snare dồn, drop, stop-time, riser, cymbal ngược), 1–3 bất ngờ theo seed, 4 kiểu kết, hook, chuyển giọng điệp khúc cuối (mặc định tắt), độ dài Ngắn/Vừa/Đầy đủ, đề xuất vòng B/C. Cột `composition_projects.form` (migration `b8d5e6f7a9c1`).
- Frontend: phát theo khối, automation âm lượng/bộ lọc/reverb, ritardando, kênh Hook, dòng thời gian kéo thả.
- Thu 10 bài: Chorus − Verse +2,3…+3,6 LU (9/9 bài có Verse/Chorus), đỉnh ≤ −1,2 dBTP, 0 mẫu vỡ. Trang nghe: https://claude.ai/artifact/N3pQphRxJiQ2SLkyWYcWD9
- Sửa lỗi thu offline làm mọi bản "sau" của ADR-012 gần như im lặng; thu lại 18 cặp.

**Đang dở / chờ**
- Nhóm nghe mù 10 bài (đích ≥ 4/5, đoán đúng Chorus ≥ 80%) và chấm lại phòng nghe ADR-012 trên bản thu mới.
- Thắng duyệt ADR-013. Phúc chọn: Outro funk/jazz giữ năng lượng cao (kết lớn) hay hạ để Intro/Outro nhỏ nhất.
- Máy Phúc: sao lưu `harmonymentor_dev.db` rồi `cd backend && alembic -c alembic.ini upgrade head`.

**Lệnh chạy lại**
```bash
cd backend && python -m pytest -q                      # 592 passed + 21 skipped
cd frontend && npm test && npm run build               # 258 test
node scripts/backing-track/thu_bai_hat.mjs && python3 scripts/backing-track/tao_trang_bai_hat.py   # cần uvicorn :8000 + npm run dev
```

## 02/11/2026: nhánh `phuc-music`, backing track "ban nhạc thật" (Bước 0 → 5)

**Đã xong** (báo cáo `docs/phuc-music/BAO_CAO_BACKING_TRACK.md`, ADR-012 đề xuất)
- 610 mẫu thu thật CC0/CC BY (piano Salamander, Rhodes/clavi FM của VCSL, bass Growlybass, upright, guitar Gretsch, trống Big Rusty, bộ gõ VCSL), ghi công ở `frontend/public/samples/CREDITS.md`.
- Bộ phối 9 phong cách ở backend (`/api/v1/composition/arrangement`), dẫn giọng, walking bass, fill, crash, tô màu qua Engine; frontend chỉ humanize theo seed (±30 ms).
- Bàn trộn bus/send, cân mức theo LUFS đo thật; 36 bản thu sau: −14,7..−19,6 LUFS, 0 mẫu vỡ (bản cũ 162–2 190).
- Giao diện: Năng lượng 1–3, kênh Guitar, fader từng kênh, Tạo bản khác, thanh tải mẫu, tự về synth khi mẫu lỗi. Migration `a7c4d5e6f8b9` (seed, energy, mix, arrangement_version; nới `ck_drum_kind`).
- Trang nghe mù 18 cặp (claude.ai + `docs/backing-track/nghe-thu/index.html`), `PHONG_CACH.md` 9 phong cách có nguồn.

**Đang dở / chờ**
- 3 bạn nghe và chấm ở trang nghe mù (đích ≥ 4/5, không phong cách nào < 3). Claude không nghe được nên chưa thể nói "nghe đạt".
- Thắng duyệt ADR-012 (cột mới + 23 mã trống lệch ERD Bảng 8).
- Chưa có bộ `.m4a` cho Safari; jazz chưa lên 180 BPM (CHECK tempo 160).

**Lệnh chạy lại**
```bash
cd backend && python -m pytest -q                      # 459 passed + 21 skipped
cd frontend && npm test && npm run build               # 240 test
python3 scripts/samples/build_samples.py --cache /tmp/src   # dựng lại mẫu (cần git + ffmpeg)
node scripts/backing-track/thu_nghe_thu.mjs --wav-dir /tmp/wav && python3 scripts/backing-track/tao_trang_nghe.py
node scripts/backing-track/do_hieu_nang.mjs            # cần uvicorn :8000 và npm run dev :5173
```

## 01/11/2026: nhánh `phuc-music`, sửa theo báo cáo đối chiếu nội dung học (v0.5.3 / main / phuc-music)

**Đã xong**
- Chú giải thuật ngữ: "Quãng tám" nói đúng là *tần số* gấp đôi; "Nửa cung" bỏ cách nói "khoảng cách nhỏ nhất giữa hai phím kề nhau"; thêm ví dụ cho m3, P5, d5. Test khóa số nửa cung và số tên chữ cái khớp mã quãng.
- 3 thẻ ôn tự diễn đạt **nháp** (L01-F09, L03-F09, L04-F09) cho ba ý đã chuyển sang trắc nghiệm (L01-Q05, L03-Q05, L04-Q06), trong `draft_specs.DRAFT_REVIEW_ITEMS`. Không seed vào `review_items` (bảng chưa có trạng thái nháp); chỉ hiện thành khối nháp `-BTHE` khi bật `SHOW_DRAFT_CONTENT`.
- ADR-011 (đề xuất): giữ lộ trình đi thẳng theo Bảng 7, đề nghị sửa câu "rẽ vào một trong ba nhánh" ở SRS 4.1.
- Luyện tập: mức Khó gợi ý mở sau L03 (trước là L04, nay là Bài 6).
- CI: mức pytest 409 → 410 (sửa luôn tên bước còn ghi 355).

**Đang dở / chờ**
- Đạt/Astra duyệt 3 thẻ nháp; duyệt xong chép nguyên mục từ `DRAFT_REVIEW_ITEMS` vào `review_items` của bài trong `curriculum_specs.py`.
- Nhóm duyệt ADR-011 và câu sửa SRS 4.1; sửa slide/demo còn gọi ii–V–I là "Bài 4" (nay là Bài 6).
- Lời giải nghĩa thuật ngữ vẫn nằm ở frontend (`TermText.tsx`), ngoài quy trình duyệt nội dung.

**Lệnh chạy lại**
```bash
cd backend && DATABASE_URL=sqlite:///$TMP/t.db AUTO_CREATE_SCHEMA=1 python -m pytest -q -m "not postgres"   # 410 passed
cd frontend && npm test && npm run build   # 227 test
```

## 01/11/2026: nhánh `phuc-music`, logo chính thức + piano trang chủ

**Đã xong**
- Gộp logo "Cuộn I–IV–V–I" (PR #16, ADR-007) vào `phuc-music` bằng merge, giữ nguyên commit của PR #16. `<Logo inverted />` trên khung khu học tối dùng bản tối của logo (`data-theme="dark"` theo vùng; sửa trong `_nguon/gen_react.js` rồi dựng lại).
- Piano "Bấm thử một hợp âm" ở trang chủ hết đen kịt: `Piano.tsx` dùng token `@theme` thay cho các biến đã mất khi bỏ `styles.css` ở Bước 3. Thêm `tests/cssVars.test.ts` bắt mọi `var(--x)` chưa định nghĩa.

**Đang dở / chờ**
- PR #16 vẫn mở vào `main`; gộp PR #16 trước hay sau PR #18 đều không xung đột lại vì cùng commit.
- ADR-007 ghi "màu chính của app vẫn là bảng cũ": trên `phuc-music` đã là Đồng & Gỉ (Bước 3), cập nhật ADR khi gộp.
- Chữ "HarmonyMentor" ở chân khung khu học (`HarmonyMentor v0.5.4-dev`) chưa đổi thành "Harmony Mentor", để nhóm quyết (ADR-007).

**Lệnh chạy lại**
```bash
cd frontend && npm test && npm run build   # 226 test
cd docs/thuong-hieu/_nguon && npm install && bash fetch_fonts.sh && REPO_OUT=../../../frontend/src/components/brand node gen_react.js
```

## 31/10/2026: nhánh `phuc-music`, Bước 4 (Harmony Lab tối thiểu)

**Đã xong** (Draft PR #18, chưa gộp; báo cáo `docs/phuc-music/BAO_CAO_BUOC_4.md`)
- Composition Engine `backend/app/composition/`: gợi ý 5 luật, độ lạ 0–3, phân tích + cảnh báo, 4 mẫu nền. Chưa có AI (`ai_used: false`).
- Bảng `composition_projects`, `chord_events`, `drum_events` (migration `f6a2b3c4d5e7`), API `/projects`. ADR-010 (đề xuất) chờ Thắng.
- Trang `/app/composition`: lưới 4–8 ô, Tone.js, VexFlow, gợi ý Nghe/Dùng/Bỏ qua, phân tích, lưu/mở/xóa.
- Q3 Bước 3: thuật ngữ chỉ chú giải ở bài đầu tiên người học gặp.

**Đang dở / chờ**
- Phúc duyệt Bước 4 (Q3 nghe thử mẫu nền). Thắng: ADR-009, ADR-010. Đạt/Astra: kiểm 5 luật và lời giải thích.

**Lệnh chạy lại**
```bash
cd backend && python -m pytest -q          # 409 passed, 21 skipped
cd frontend && npm ci && npm test && npm run build   # 225 test
node scripts/phuc-music/luong_buoc4_harmony_lab.cjs docs/phuc-music/anh/buoc-4
```

## 31/10/2026: nhánh `phuc-music`, Bước 3 (giao diện "Đồng & Gỉ")

**Đã xong** (Draft PR #18, chưa gộp; báo cáo `docs/phuc-music/BAO_CAO_BUOC_3.md`)
- Token màu/font/12 màu nốt trong `@theme` (`frontend/src/index.css`). Bỏ `legacy-page` và `styles.css`; khu học dùng Tailwind + `components/ui/Page.tsx`.
- Chú giải thuật ngữ lần đầu xuất hiện, có nút nghe (nốt từ Music Engine). Lời giải nghĩa chờ Astra/Đạt duyệt.
- axe-core: 0 vi phạm WCAG 2.1 AA trên 15 màn × 2 cỡ; ảnh trước/sau ở `docs/phuc-music/anh/buoc-3/`.

**Đang dở / chờ**
- Phúc duyệt Bước 3 lúc 13:27 (Q1 đồng ý, Q2 duyệt, Q3 chỉ chú giải ở bài đầu tiên).

**Lệnh chạy lại**
```bash
cd backend && python -m pytest -q          # 371 passed, 21 skipped
cd frontend && npm ci && npm test && npm run build   # 219 test
node scripts/phuc-music/anh_moi_trang.cjs docs/phuc-music/anh/buoc-3 sau
AXE_PATH=<đường dẫn axe.min.js> node scripts/phuc-music/kiem_tra_wcag.cjs
```

## 31/10/2026: nhánh `phuc-music`, Bước 2 (logic và nội dung)

**Đã xong** (Draft PR #18, chưa gộp; báo cáo `docs/phuc-music/BAO_CAO_BUOC_2.md`)
- Gộp PR #12. Bài 1 lấy quãng/hợp âm từ API Music Engine. Piano hiện D#/Eb.
- Luyện tập: máy chủ chấm, ghi `practice_attempts`, trang có lịch sử + thống kê. ADR-009 (đề xuất) chờ Thắng.
- Lộ trình theo SRS Bảng 7; nháp L09–L12 và mục "Dùng vào sáng tác" L01–L04, chỉ hiện khi `SHOW_DRAFT_CONTENT=1`.

**Đang dở / chờ**
- Phúc: đã chọn Bảng 7 + nhãn A/B (12:53); còn Q1–Q2 trong báo cáo. Thắng: ADR-009, L-1/L-2/L-5/L-6 (kiểm tra đầu vào, EMA). Đạt/Astra: duyệt nháp.
- Phúc duyệt Bước 2 lúc 12:55 (Q1 không, Q2 để Claude quyết).

**Lệnh chạy lại**
```bash
cd backend && pytest -q                    # 371 passed, 21 skipped
cd frontend && npm ci && npm test && npm run build   # 195 test
node scripts/phuc-music/luong_buoc2_luyentap.cjs docs/phuc-music/anh/buoc-2
node scripts/phuc-music/luong_buoc2_lotrinh.cjs docs/phuc-music/anh/buoc-2 nguoi-hoc   # SHOW_DRAFT_CONTENT=1 thì đổi hậu tố che-do-nhap
```

## 31/10/2026: nhánh `phuc-music`, Bước 0–1 (gộp khu học v0.5.3)

**Đã xong** (nhánh `phuc-music`, Draft PR #18, chưa gộp)
- Bước 0: khảo sát `docs/phuc-music/00_KHAO_SAT.md`. Main đã chứa khu học của v0.5.3; backend không cần khôi phục.
- Bước 1: khung khu học tối kiểu v0.5.3 (`AppLayout.tsx`), nút "Từng bước / Xem cả bài" (`LessonRunner.tsx`), token `--color-shell-*`, phiên bản lấy từ `package.json`. Nhật ký `docs/phuc-music/01_NHAT_KY_GOP.md`, báo cáo `BAO_CAO_BUOC_1.md`.

**Đang dở / chờ**
- Phúc đã duyệt Bước 1 (31/10).

**Lệnh chạy lại**
```bash
cd backend && pytest -q                    # 325 passed, 21 skipped
cd frontend && npm ci && npm run build
node scripts/phuc-music/luong_buoc1.cjs anh/   # cần backend :8000 và frontend :5173 đang chạy
```

## 30/10/2026: logo chính thức "Cuộn I–IV–V–I"

**Đã xong** (nhánh `claude/project-thread-82ijft`, PR vào `main`, chưa gộp)
- Thay logo ♪ bằng logo nhóm chọn (ADR-007): `frontend/src/components/brand/HarmonyMentorLogo.tsx`, `Logo.tsx` giữ nguyên prop `to`.
- Favicon SVG/ICO, apple-touch-icon, icon 192/512, `site.webmanifest` trong `frontend/public/`; tiêu đề tab "Harmony Mentor".
- `docs/thuong-hieu/`: BRAND_NOTE, file logo SVG, script dựng lại. Ảnh trước/sau trong `docs/minh-chung/anh/logo-*.png`.

**Việc tiếp theo**
- Nhóm quyết có đổi các chữ "HarmonyMentor" còn lại sang "Harmony Mentor" không, và khi nào áp bảng màu Đồng & Gỉ cho toàn app.

**Lệnh chạy lại**
```bash
cd frontend && npm ci && npm run build
cd docs/thuong-hieu/_nguon && npm install && bash build.sh   # dựng lại logo (cần Python: fonttools, cairosvg, pillow)
```

## 30/10/2026: gom tài liệu phase vào `docs/giai-doan/`

**Đã xong** (nhánh `claude/project-thread-ng2frm`, PR vào `main`, chưa gộp)
- Theo góp ý của thầy: 10 file `PHASE_*.md`, 7 file `VERIFICATION_PHASE_*.txt` và 2 bản kiểm định chuyển bằng `git mv` vào `docs/giai-doan/<giai đoạn>/`, giữ nguyên tên. Mục lục `docs/giai-doan/README.md`.
- Sửa mọi đường dẫn cũ trong CLAUDE.md, README, AI_USAGE, ADR-003, `docs/prompts/`, `PROMPT_CLAUDE_CODE.md`, 1 test backend và 2 comment frontend. Không đổi code chạy.

**Việc tiếp theo**
- Giai đoạn mới đặt báo cáo + kiểm chứng vào `docs/giai-doan/<giai đoạn>/` và thêm một dòng vào mục lục.

## 28/10/2026: HM-001 / NL-L01-01, ký âm và MIDI cho B#/Cb ở Bài 1

**Đã xong** (nhánh `claude/project-thread-qdcaej`, Draft PR #12, chưa gộp)
- `toScientificInterval/toScientificTriad` tính quãng tám theo chữ cái; `scientificToMidi` không quy về pitch class. Engine không đổi.
- Vitest (182 test) so 17 nốt gốc × 5 quãng + 4 hợp âm với bảng do Music Engine sinh (`scripts/sinh_bang_l01_engine.py`); 5 pytest giữ bảng khớp Engine; CI thêm bước `npm test`, mức SQLite 330.
- Chứng minh đỏ trước/xanh sau: CI run 40734235986 đỏ ở `npm test` trên commit chỉ có test. Ảnh và log MIDI trước/sau trên giao diện: `docs/minh-chung/anh/hm001/`, `docs/minh-chung/hm001/`. Báo cáo `docs/bao-cao/HM-001.md`.

**Đang dở / chờ**
- Astra và nhóm review PR #12. Không merge tự động.
- Lỗi lân cận tách ticket riêng: `pitchClassesToAscendingNotes` đổi Eb → D# trước khi phát (chỉ sai tên, cao độ đúng).

**Lệnh chạy lại**
```bash
cd frontend && npm ci && npm test && npm run build   # 182 passed, build đạt
cd backend && pytest -q                              # 330 passed, 21 skipped
python scripts/sinh_bang_l01_engine.py && git diff --exit-code frontend/tests/fixtures
```

## 27/10/2026: PR-3, bảo vệ phiên bản câu hỏi (HM-003)

**Đã xong** (nhánh `claude/project-thread-3z96i1`, Draft PR, chưa gộp)
- Migration `d3a7f1c2e905` (nối vào `b2c4e6f80a13`): ảnh chụp đề/lựa chọn/loại câu/cách chấm trên `exercise_versions`, `status` draft/published, `content_hash`, `snapshot_origin`, `exercises.deleted_at`; khôi phục ảnh chụp bản cũ từ git khi khớp nguồn; trigger PostgreSQL; `downgrade` từ chối chạy.
- Seed không ghi đè, không tự tăng version, báo `SeedConflictError` và rollback; `q(status=, retired=)`; `SHOW_DRAFT_CONTENT`.
- Chấm theo ảnh chụp của phiên bản; nộp vào bản cũ trả 409 `EXERCISE_VERSION_SUPERSEDED`; frontend tải lại bài.
- 50 test mới: 38 chạy trên SQLite, 12 chỉ chạy trên PostgreSQL (bị bỏ qua khi không có TEST_DATABASE_URL). ADR-006. Báo cáo `docs/bao-cao/PR3_IMPLEMENTATION_REPORT.md`.

**Đang dở / chờ**
- Nhóm duyệt Draft PR. Thắng ký D-2, D-4; Đạt ký D-1, D-3 (ADR-006).
- SQLite dev cũ (`backend/harmonymentor_dev.db`) thiếu cột mới: xóa file để tạo lại. CSDL Docker: `alembic upgrade head` tự chạy khi khởi động; nên `pg_dump` trước.

**Lệnh chạy lại**
```bash
cd backend && pytest -q                                   # 325 passed, 21 skipped
TEST_DATABASE_URL=postgresql+psycopg://hm_ci:ci_only_not_secret@127.0.0.1:5432/harmony_test pytest -m postgres   # 21 passed
alembic -c alembic.ini upgrade head && alembic -c alembic.ini check
cd frontend && npm ci && npm run build
```

**Việc tiếp theo**
- PR-4 (14 nhóm kỹ năng + 12 bài), PR-5 (mastery EMA đọc `attempts.correct` đã lưu, không chấm lại), PR-6 (câu nháp `status="draft"`).

## 27/10/2026: PR-2, CI GitHub Actions

**Đã xong**
- `.github/workflows/ci.yml` có 3 job: backend SQLite (281 test, 0 skip), backend PostgreSQL 16 + pgvector (`alembic upgrade head` + `alembic check` + 9 test đồng thời HM-010, 0 skip), frontend (`npm ci` + `npm run build`). Chi tiết ở `docs/CI.md`.
- `scripts/ci/kiem_junit.py`: báo đỏ khi có skip, vì pytest trả mã 0 khi mọi test bị skip.
- Đã chứng minh CI báo đỏ bằng một PR phụ (#10), sau đó đã đóng PR này.
- Báo cáo: `docs/bao-cao/PR2_CI_REPORT.md`.

**Đang dở / chờ**
- Chờ Phúc và Astra duyệt PR #9 (Draft). Chưa gộp.
- Sau khi gộp, Phúc bật "Require status checks" cho `main` (hướng dẫn trong `docs/CI.md`).

**Lệnh chạy lại**
```bash
cd backend && pytest -q -m "not postgres"        # 281 passed
TEST_DATABASE_URL=postgresql+psycopg://hm_ci:ci_only_not_secret@127.0.0.1:55432/harmony_test pytest -m postgres   # 9 passed
cd frontend && npm ci && npm run build
```

**Việc tiếp theo (chờ Phúc duyệt từng PR)**
- PR-3 trở đi theo kế hoạch sửa đổi 26/10: ExerciseVersion (HM-003), mastery EMA, hệ gợi ý CP2.
