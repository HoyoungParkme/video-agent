/** E2E 공용 — 요소 번호로 찾기 · 키 저장 · 가짜 OpenAI 조절 · 결과 화면 열기 · 장면 지우기. */
import { execFileSync } from "node:child_process";
import { rmSync } from "node:fs";
import path from "node:path";

import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const GOOD_KEY = "sk-e2e-good-000000000000000000"; // e2e/fake-openai.mjs와 같은 값
// E2E api의 데이터 폴더(playwright.config.ts의 DATA_DIR) — 내보낸 파일 · 임시 폴더를 본다
export const DATA = path.join(__dirname, ".tmp", "data");
// E2E inbox(playwright.config.ts의 INBOX_DIR) — 파일을 넣고 지워 본다
export const INBOX = path.join(__dirname, ".tmp", "inbox");
const FAKE = "http://127.0.0.1:8190";
const BACKEND = path.join(__dirname, "..", "..", "backend");
// playwright.config.ts의 DATABASE_URL과 같은 테스트 DB
const TEST_DB = "postgresql+asyncpg://va:va@127.0.0.1:5433/va_test";
const FORGET_FRAMES = `
import asyncio, sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main(url, video_id):
    engine = create_async_engine(url)
    async with engine.begin() as c:
        await c.execute(
            text("DELETE FROM chapter_frames WHERE chapter_id IN "
                 "(SELECT id FROM chapters WHERE video_id = :v)"),
            {"v": video_id},
        )
    await engine.dispose()

asyncio.run(main(sys.argv[1], int(sys.argv[2])))
`;

export const el = (page: Page, no: string) => page.locator(`[data-el="${no}"]`);

/** 다이얼로그 안의 요소 — UI-2는 UI-1 위에 떠서 요소 번호가 겹친다(UI-1 6.1 · UI-2 6.1). */
export const inDialog = (page: Page, no: string) =>
  page.getByRole("dialog").locator(`[data-el="${no}"]`);

/** 경고 다이얼로그(UI-6) 안의 요소 — UI-1 3.2 · UI-6 3.2처럼 번호가 겹친다. */
export const inAlert = (page: Page, no: string) =>
  page.getByRole("alertdialog").locator(`[data-el="${no}"]`);

/** 맞는 키를 저장해 둔다 — 화면을 거치지 않고 web의 /api로. */
export async function saveKey(request: APIRequestContext): Promise<void> {
  const res = await request.post("/api/settings/key", { data: { key: GOOD_KEY } });
  if (!res.ok()) throw new Error(`키 저장 실패 ${res.status()}`);
}

export interface FakeState {
  chatDelayMs: number;
  chats: number;
  /** 받아쓰기 요청 수 — 조각 단위(첫 토막만 센다. 앱은 조각을 15초 이하 토막으로 나눠 보낸다) */
  transcriptions: number;
  /** 조각마다 늦추는 시간 · 실패시킬 조각 — 첫 토막에만 걸린다 */
  sttDelayMs: number;
  sttFail: { seq: number; times: number; drop?: boolean } | null;
  chatFail: number;
  models: "drop" | 401 | null;
  /** 받아쓴 조각 번호(첫 토막이 성공한 것), 받은 차례대로 */
  transcribed: number[];
  /** 답한 질문마다 — 앞선 턴 수와 받은 스크립트의 첫 · 끝 시각 */
  asks: { question: string; history: number; first: string | null; last: string | null }[];
  imageDelayMs: number;
  imageFail: "server" | "moderation" | null;
  /** 받은 이미지 요청마다 — 모델 · 크기 · 품질 · 프롬프트 */
  images: { model: string; size: string; quality: string; prompt: string }[];
}

/**
 * 가짜 OpenAI를 조절하거나 지금 값을 읽는다 — 채팅 · 받아쓰기 지연, 조각 하나를 몇 번 실패시킬지
 * (drop이면 500 대신 연결을 끊는다 — 인터넷 끊김), 다음 채팅 몇 번을 실패시킬지, 키 확인(models)을
 * 끊을지(drop) 맞는 키도 거절할지(401), 이미지 지연과 다음 이미지 한 번을 서버 오류 · 안전 정책 거절로 할지.
 * reset이면 부른 수 · 받은 조각 기록 · 남은 실패를 비운다(같은 요청의 설정값은 그 뒤에 들어간다).
 */
export async function fakeOpenAI(
  request: APIRequestContext,
  body: {
    chat_delay_ms?: number;
    stt_delay_ms?: number;
    stt_fail?: { seq: number; times: number; drop?: boolean } | null;
    chat_fail?: number;
    models?: "drop" | 401 | null;
    image_delay_ms?: number;
    image_fail?: "server" | "moderation" | null;
    reset?: boolean;
  } = {},
): Promise<FakeState> {
  const res = await request.post(`${FAKE}/control`, { data: body });
  return (await res.json()) as FakeState;
}

/** 결과 화면을 연다 — 처음이면 사전 안내에서 분석을 시작하고, 이미 분석했으면 바로 결과로 간다. */
export async function openResult(page: Page, url: string): Promise<string> {
  await page.goto("/");
  await el(page, "3.2").locator("input").fill(url);
  await el(page, "3.3").click();
  const start = inDialog(page, "6.3");
  await Promise.race([
    start.waitFor().catch(() => undefined),
    page.waitForURL(/\/videos\/\d+$/).catch(() => undefined),
  ]);
  if (await start.isVisible()) await start.click();
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 30_000 });
  return page.url();
}

/**
 * 장면 단계 전에 분석한 결과처럼 만든다 — 그 영상의 장면 행과 장면 폴더를 지운다.
 * 화면 · API에는 장면을 지우는 길이 없어 백엔드의 파이썬으로 테스트 DB에 직접 한다.
 */
export function forgetFrames(videoId: number): void {
  execFileSync("uv", ["run", "--quiet", "python", "-c", FORGET_FRAMES, TEST_DB, String(videoId)], {
    cwd: BACKEND,
    stdio: "pipe",
  });
  rmSync(path.join(DATA, "frames", String(videoId)), { recursive: true, force: true });
}
