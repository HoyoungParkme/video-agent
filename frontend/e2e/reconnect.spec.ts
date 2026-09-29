/**
 * 서버에 잠깐 닿지 못해도 화면이 빈 채로 멈추지 않는다 — UI-3은 영상 정보를 1초 뒤, UI-4는 결과를
 * 2초 뒤 다시 받는다(VA-UI-002 UI-3 · UI-4 규칙, 카드 B1 코드 리뷰). 첫 요청 하나만 끊는다.
 */
import { expect, test, type Page } from "@playwright/test";

import { el, fakeOpenAI, saveKey } from "./helpers";

/** 이 경로의 첫 요청만 끊는다(브라우저에는 연결 실패). 들어온 요청 수를 돌려주는 함수를 준다. */
async function cutFirst(page: Page, path: string): Promise<() => number> {
  let seen = 0;
  await page.route(`**${path}`, (route) => {
    seen += 1;
    return seen === 1 ? route.abort() : route.continue();
  });
  return () => seen;
}

test.afterEach(async ({ request }) => {
  await fakeOpenAI(request, { chat_delay_ms: 0 });
});

test("첫 요청이 끊겨도 UI-3 · UI-4가 다시 받아 그린다", async ({ page, request }) => {
  await saveKey(request);
  await fakeOpenAI(request, { chat_delay_ms: 3000 }); // UI-3을 보는 동안 끝나지 않게
  const res = await request.post("/api/videos", {
    data: { source: "youtube", url: "https://youtu.be/e2eCaption4" },
  });
  const { video } = (await res.json()) as { video: { id: number } };
  expect((await request.post(`/api/videos/${video.id}/job`)).status()).toBe(201);

  // UI-3 — 영상 정보의 첫 요청이 끊긴다
  const videoCalls = await cutFirst(page, `/api/videos/${video.id}`);
  await page.goto(`/videos/${video.id}/progress`);
  await expect(el(page, "2.3")).toHaveText("YouTube · 25:00 · 자막 있음"); // UI-3의 영상 머리
  await expect(page).toHaveURL(new RegExp(`/videos/${video.id}/progress$`)); // 아직 도는 중
  expect(videoCalls()).toBeGreaterThanOrEqual(2);

  // 끝나면 UI-4 — 결과의 첫 요청도 끊긴다
  const resultCalls = await cutFirst(page, `/api/videos/${video.id}/result`);
  await fakeOpenAI(request, { chat_delay_ms: 0 });
  await expect(page).toHaveURL(new RegExp(`/videos/${video.id}$`), { timeout: 30_000 });
  await expect(el(page, "2.2")).toHaveText("임베딩 모델 고르기");
  expect(resultCalls()).toBeGreaterThanOrEqual(2);
});
