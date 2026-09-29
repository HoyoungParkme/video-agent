# backend 이미지 — python + ffmpeg + yt-dlp + deno (INFRA C8). docker-compose.yml의 api
FROM python:3.12.14-slim-trixie

# ffmpeg · ffprobe는 배포판 것. deno는 yt-dlp가 YouTube 서명을 풀 때 부른다(INFRA C7)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*
COPY --from=denoland/deno:bin-2.9.7 /deno /usr/local/bin/deno
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /app

# 의존성 먼저 — 코드만 바뀌면 이 층을 다시 쓰지 않는다. yt-dlp도 여기서 깔린다
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ ./

# 호스트 사용자(보통 1000)와 같은 번호 — 마운트한 data/ · .env에 쓰고, 만든 파일을 호스트에서 지울 수 있게
RUN useradd --uid 1000 --create-home app
USER app

# 시작할 때 마이그레이션을 올리고 서버를 띄운다
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
