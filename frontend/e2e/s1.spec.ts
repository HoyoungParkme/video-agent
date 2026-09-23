/**
 * S1 — 자막 있는 YouTube 하나를 주소 → 사전 안내 → 4단계 → 결과까지(VA-SCN-001 S1 · S3, VA-CODE-001 B1).
 * 결과에서는 인사이트 칩 · 챕터 카드 · 구간 줄 어디를 눌러도 같은 이동이다(공통 1.3).
 * 같은 주소를 다른 꼴로 다시 넣으면 UI-2 없이 결과와 '이미 분석한 영상입니다'.
 * 자막 없는 영상은 B1에서 시작 불가 판 '아직 지원하지 않음'(사용자 결정 2026-09-23).
 */
import { expect, test } from "@playwright/test";

import { el, fakeOpenAI, inDialog, saveKey } from "./helpers";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
});

test("자막 있는 YouTube — 사전 안내부터 결과와 시각 이동까지", async ({ page, request }) => {
  // 단계가 보일 만큼 채팅을 늦춘다
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 700 });

  await page.goto("/");
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eCaption1");
  await el(page, "3.3").click();

  // UI-2 자막 있음 판 — 숫자는 서버 값 그대로
  await expect(inDialog(page, "1.1")).toHaveText("분석을 시작할까요?");
  await expect(inDialog(page, "2.2")).toHaveText("RAG 서비스 1년 운영기");
  await expect(inDialog(page, "2.3")).toHaveText("YouTube · E2E 채널");
  await expect(inDialog(page, "2.4")).toHaveText("길이 50:12");
  await expect(inDialog(page, "2.5")).toHaveText("자막 있음 · 한국어");
  await expect(inDialog(page, "3.1")).toHaveText("약 1분");
  await expect(inDialog(page, "4.2")).toContainText("받아쓰기 (자막 사용)$0.00");
  await expect(inDialog(page, "4.1")).toHaveText(/^약 \$\d+\.\d\d$/);
  await expect(inDialog(page, "5")).toContainText("OpenAI(gpt-5-mini)");
  await expect(inDialog(page, "6.1")).toHaveCount(0); // 다른 영상이 돌지 않는다
  await expect(inDialog(page, "6.3")).toBeFocused(); // 처음 초점

  await inDialog(page, "6.3").click();

  // UI-3 — 단계 넷(자막 가져오기 → 핵심 요약 → 챕터 → 추천 질문)
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  await expect(el(page, "2.3")).toHaveText("YouTube · 50:12 · 자막 있음");
  await expect(page.locator(".step-name")).toHaveText([
    "자막 가져오기",
    "핵심 요약",
    "챕터",
    "추천 질문",
  ]);
  await expect(el(page, "3.1")).toHaveText(
    /핵심 요약을 만드는 중|챕터를 만드는 중|추천 질문을 만드는 중/,
  );
  await expect(el(page, "6.1")).toContainText("스크립트 텍스트 → OpenAI gpt-5-mini");

  // 끝나면 UI-4가 저절로 — 뒤로 가기가 UI-3으로 오지 않게 바꿔치기
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 20_000 });
  await expect(el(page, "2.2")).toHaveText("RAG 서비스 1년 운영기");
  await expect(el(page, "2.1")).toHaveText("YouTube50:12자막 · 한국어");
  await expect(el(page, "2.3")).toHaveText(/^E2E 채널 · 오늘 \d\d:\d\d 분석 · 요약 gpt-5-mini$/);
  await expect(el(page, "2.4")).toHaveAttribute(
    "href",
    "https://www.youtube.com/watch?v=e2eCaption1",
  );
  await expect(el(page, "3")).toContainText("검색 품질 문제를 찾고 고친 과정");
  await expect(el(page, "4.1")).toHaveText("6개");
  await expect(el(page, "5.1")).toHaveText("청킹 전략을 바꾼 근거는?");
  await expect(el(page, "6.1")).toHaveText("5개");
  await expect(el(page, "7.1")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "8.1")).toHaveText("자막(수동) · 한국어");
  await expect(el(page, "8.2")).toHaveText(""); // 처음에는 선택한 시각이 없다

  // 인사이트 칩 → 그 시각이 든 구간 강조 · 8.2
  await el(page, "4.3").click();
  await expect(el(page, "8.2")).toHaveText("01:40");
  const selected = page.locator('.segment[aria-pressed="true"]');
  await expect(selected).toHaveCount(1);
  await expect(selected).toContainText("2번째 문장");

  // 챕터 카드 → 같은 동작 + 시작 시각이 같은 챕터가 선택 모양
  await page.locator(".chapter", { hasText: "청킹 다시 보기" }).click();
  await expect(el(page, "8.2")).toHaveText("10:00");
  await expect(selected).toContainText("7번째 문장");
  await expect(page.locator('.chapter[aria-pressed="true"]')).toHaveText(/청킹 다시 보기/);

  // 스크립트 구간 줄 → 같은 동작. 시작 시각이 같은 챕터가 없으면 선택된 카드도 없다
  await page
    .locator(".segment", { has: page.locator(".segment-time", { hasText: /^05:00$/ }) })
    .click();
  await expect(el(page, "8.2")).toHaveText("05:00");
  await expect(page.locator('.chapter[aria-pressed="true"]')).toHaveCount(0);

  // 목록 — 완료 행
  await el(page, "1.1").click();
  await expect(page).toHaveURL(/\/$/);
  await expect(el(page, "6.3")).toHaveText("RAG 서비스 1년 운영기");
  await expect(el(page, "6.4")).toHaveText("YouTube · E2E 채널");
  await expect(el(page, "6.5")).toHaveText("50:12");
  await expect(el(page, "6.6")).toHaveText(/^오늘 \d\d:\d\d 분석$/);

  // 같은 영상을 watch 주소로 다시 — UI-2 없이 결과와 짧은 알림
  await el(page, "3.2").locator("input").fill("https://www.youtube.com/watch?v=e2eCaption1");
  await el(page, "3.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+$/);
  await expect(el(page, "11")).toHaveText("이미 분석한 영상입니다");
  await expect(el(page, "1.1")).toBeVisible();

  const fake = await fakeOpenAI(request, { chat_delay_ms: 0 });
  expect(fake.transcriptions).toBe(0); // 받아쓰기 호출 0회
  expect(fake.chats).toBe(3); // 요약 · 챕터 · 추천 질문
});

test("자막 없는 영상 — 시작 불가 판에 '아직 지원하지 않음'", async ({ page }) => {
  await page.goto("/");
  const input = el(page, "3.2").locator("input");
  await input.fill("https://youtu.be/e2eNoCapt01");
  await el(page, "3.3").click();
  await expect(inDialog(page, "7.1")).toHaveText("자막 없는 영상은 아직 지원하지 않아요");
  await expect(inDialog(page, "7.2")).toHaveText("길이 30:00");
  await expect(inDialog(page, "6.3")).toHaveCount(0); // 분석 시작 버튼이 없다
  await expect(inDialog(page, "7.3")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(input).toHaveValue("https://youtu.be/e2eNoCapt01"); // 넣은 주소가 그대로
  await expect(el(page, "3.3")).toBeFocused(); // 초점은 연 버튼으로

  // 입력칸에서 Enter로 열어도 닫으면 초점은 [분석](3.3)으로
  await input.press("Enter");
  await expect(inDialog(page, "7.3")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(el(page, "3.3")).toBeFocused();
});
