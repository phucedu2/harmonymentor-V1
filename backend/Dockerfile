# API FastAPI cho docker compose (SRS 10.2).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Không chạy bằng root trong container.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Chạy migration trước, rồi mới mở API (seed nội dung chạy trong lifespan khi SEED_DEMO_CONTENT=1).
# Tắt access log của uvicorn vì middleware đã ghi log JSON (có thời gian xử lý, request id).
CMD ["sh", "-c", "alembic -c alembic.ini upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log"]
