# Chạy và kiểm lại nhánh `frontend-soi-loi` trên Windows

Dành cho máy Phúc (`D:\aptech\Music Tutor v1`). Mọi lệnh gõ trong **PowerShell**. Nhánh này chỉ đổi `frontend/` và `docs/`, nên backend, cơ sở dữ liệu và khóa Gemini giữ nguyên như bản `phuc-music`.

## 1. Lấy code

```powershell
cd "D:\aptech\Music Tutor v1\hm-phuc-music"
git fetch origin frontend-soi-loi
git switch frontend-soi-loi      # lần đầu: git switch -c frontend-soi-loi origin/frontend-soi-loi
git log --oneline -3             # dòng đầu phải bắt đầu bằng "FE-" hoặc "docs(soi-loi)"
```

Muốn quay về bản cũ để so sánh: `git switch phuc-music`.

## 2a. Chạy bằng Docker (giống lúc nộp)

```powershell
# Trước khi build: tắt "HTTPS scanning" của Avast, nếu không npm ci sẽ lỗi chứng chỉ.
docker compose up --build -d web
docker compose ps                # api, db, redis, web đều "healthy"/"running"
start http://localhost:5173
```

Chỉ `web` cần build lại vì nhánh này không đổi backend. Docker kẹt file thì chạy `D:\DockerData\mo-docker.bat` rồi thử lại. Máy 8 GB đã giới hạn WSL 4 GB trong `.wslconfig`, không cần đổi.

## 2b. Chạy nhanh không Docker (chỉ để xem giao diện)

```powershell
# Cửa sổ 1: backend dùng SQLite dev
cd "D:\aptech\Music Tutor v1\hm-phuc-music\backend"
python -m uvicorn app.main:app --port 8000

# Cửa sổ 2: frontend
cd "D:\aptech\Music Tutor v1\hm-phuc-music\frontend"
npm ci
npm run build
npx vite preview --port 4173     # mở http://localhost:4173
```

Python trên máy từng lỗi SSL khi tải gói. Nếu `pip install` lỗi thì dùng cách 2a.

## 3. Kiểm tra tự động

```powershell
cd "D:\aptech\Music Tutor v1\hm-phuc-music\frontend"
npx tsc -b          # không in gì là đạt
npm test            # Vitest, mong đợi 277 passed
npm run build       # mong đợi "built in …"
```

## 4. Việc chỉ làm được trên máy thật (cloud không nghe được tiếng)

Mở DevTools (F12) → Toggle device toolbar (Ctrl+Shift+M) → chọn kích thước 390 × 844 rồi kiểm:

| ID | Thao tác | Mong đợi |
|---|---|---|
| FE-001 | Vào một bài học, bấm nút tròn **AI**, gõ một câu hỏi | Nút tròn biến mất khi khung mở; nút **Gửi** và nút **×** bấm được |
| FE-004 | Trong Bài 1 bấm **Bước tiếp →** | Màn hình dừng ở thẻ "Bước x/18", nội dung bước nằm ngay dưới |
| FE-005 | Trang Luyện tập, gõ `C E G#` rồi **Kiểm tra** | Ô "✗ Chưa đúng" tự hiện trong màn hình |
| FE-006 | Harmony Lab | Ba nút Phát / Tạo bản khác / Lưu vòng này nằm trên một dòng, nút AI không đè |
| FE-007 | Bấm Tab qua thanh bên tối | Vòng focus màu xanh ngọc nhìn rõ |
| Âm thanh | Harmony Lab, bấm **Phát** lần đầu | Ghi lại số giây từ lúc bấm tới khi có tiếng (cloud đo 4,1 s chỉ để tải 221 mẫu âm, chưa tính giải mã trên máy yếu) |
| Âm thanh | Trang chủ, bật âm thanh rồi cuộn qua cảnh khuông nhạc và vòng C–G–Am–F | Không rè, không chồng tiếng khi cuộn nhanh |

Ghi kết quả vào cột "Kiểm trên máy Phúc" trong `docs/SOI_LOI_FRONTEND.md`.

## 5. Chụp lại ảnh như trên cloud (không bắt buộc)

Script chụp nằm ở `docs/soi-loi-frontend/script/`. Cần Node 22 và Playwright:

```powershell
cd "D:\aptech\Music Tutor v1\hm-phuc-music\docs\soi-loi-frontend\script"
npm init -y; npm i playwright@1.63.0; npx playwright install chromium
$env:BASE="http://localhost:5173"; node shoot.js ..\may-phuc
```
