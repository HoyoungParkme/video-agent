/**
 * E2E — 가짜 OpenAI · api · web을 따로 띄우고 와이어프레임 요소 번호(data-el)로 누른다(VA-CODE-001 A · B1).
 * 포트는 개발 서버와 겹치지 않게 8190 · 8100 · 3100. web은 E2E 전용으로 빌드한다(넘길 api 주소가 다르다).
 * yt-dlp · ffmpeg도 가짜다(e2e/fake-ytdlp.mjs · fake-ffmpeg.mjs). inbox는 시작 때 만드는 임시 폴더다.
 * 테스트 DB(va_test)를 시작 때 비운다 — pytest와 함께 돌리지 않는다.
 */
import path from "node:path";

import { defineConfig } from "@playwright/test";

const FAKE = 8190;
const API = 8100;
const WEB = 3100;
const TMP = path.join(__dirname, "e2e", ".tmp");
const q = (p: string) => JSON.stringify(p);

export default defineConfig({
  testDir: "e2e",
  workers: 1,
  use: { baseURL: `http://127.0.0.1:${WEB}`, trace: "retain-on-failure" },
  webServer: [
    {
      command: `node e2e/fake-openai.mjs ${FAKE}`,
      url: `http://127.0.0.1:${FAKE}/health`,
    },
    {
      // 빈 .env와 빈 테스트 DB로 시작한다 — 키도 영상도 없는 첫 실행
      // 경로는 따옴표로 — 저장소 경로에 공백이 있어도 엉뚱한 폴더를 지우지 않게
      command: [
        `rm -rf ${q(TMP)} && mkdir -p ${q(TMP)}`,
        `node e2e/fake-ffmpeg.mjs --make-inbox ${q(path.join(TMP, "inbox"))}`,
        "cd ../backend",
        "uv run alembic downgrade base",
        "uv run alembic upgrade head",
        `uv run uvicorn app.main:app --host 127.0.0.1 --port ${API}`,
      ].join(" && "),
      url: `http://127.0.0.1:${API}/health`,
      env: {
        ENV_PATH: path.join(TMP, "e2e.env"),
        DATA_DIR: path.join(TMP, "data"),
        OPENAI_BASE_URL: `http://127.0.0.1:${FAKE}/v1`,
        // YouTube에 닿지 않게 — 정해 둔 정보와 자막을 주는 가짜
        YTDLP_BIN: path.join(__dirname, "e2e", "fake-ytdlp.mjs"),
        // 음성 추출 · 무음 · 자르기도 가짜 — inbox 파일과 조각은 길이를 담은 JSON이다
        FFMPEG_BIN: path.join(__dirname, "e2e", "fake-ffmpeg.mjs"),
        FFPROBE_BIN: path.join(__dirname, "e2e", "fake-ffmpeg.mjs"),
        INBOX_DIR: path.join(TMP, "inbox"),
        DATABASE_URL: "postgresql+asyncpg://va:va@127.0.0.1:5433/va_test",
        INBOX_DISPLAY_PATH: "~/video-agent/inbox",
      },
      timeout: 60_000,
    },
    {
      // 이미지(Dockerfile.web)와 같게 standalone 서버로 — 정적 파일을 곁에 복사한다
      command: [
        "npx next build",
        "cp -r public .next-e2e/standalone/",
        "cp -r .next-e2e/static .next-e2e/standalone/.next-e2e/",
        "node .next-e2e/standalone/server.js",
      ].join(" && "),
      url: `http://127.0.0.1:${WEB}`,
      env: {
        API_URL: `http://127.0.0.1:${API}`,
        NEXT_DIST_DIR: ".next-e2e",
        NEXT_TELEMETRY_DISABLED: "1",
        HOSTNAME: "127.0.0.1",
        PORT: String(WEB),
      },
      timeout: 240_000,
    },
  ],
});
