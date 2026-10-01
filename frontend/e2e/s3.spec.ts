/**
 * S3 구간 찾기를 키보드로(VA-SCN-001 S3 · 카드 E5, VA-UI-001 4.6) — 한눈에 보기의 줄마다 Tab 한 번 · ← → · Enter ·
 * 가리킨 칸 이름(UI-4 13.6), 결과 탭 ← →, 키보드 초점 고리와 헤더 밑에 숨지 않게 띄우는 스크롤 여백.
 * 3시간 워크숍이라 파트 띠까지 세 줄이다. 키를 저장하므로 빈 앱을 보는 first-run보다 뒤에 돈다(파일 이름 순).
 */
import { expect, test } from "@playwright/test";

import { fakeOpenAI, saveKey } from "./helpers";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 });
});

test("초점 고리 — 키보드 초점에 청록 2px, 헤더 밑에 숨지 않게 띄운다", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  await expect(focused).toHaveCSS("outline-style", "solid");
  await expect(focused).toHaveCSS("outline-width", "2px");
  await expect(focused).toHaveCSS("outline-color", "rgb(15, 110, 104)");
  await expect(focused).toHaveCSS("outline-offset", "2px");
  // 헤더 64px + 키 없음 배너(없음) + 16px
  expect(
    await page.evaluate(() => getComputedStyle(document.documentElement).scrollPaddingTop),
  ).toBe("80px");
});
