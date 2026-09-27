/**
 * S4 — 영상에 질문하기(VA-SCN-001 S4, VA-CODE-001 B3). 추천 질문으로 시작해 근거 칩을 따라가고, 이어 묻고,
 * 영상에 없는 것을 묻는다. 다시 열어도 기록이 남는다. 답변 실패는 다시 시도로, 3시간 스크립트는 질문과 맞는
 * 챕터만 보낸다. 가짜 OpenAI가 받은 스크립트 범위 · 앞선 턴 수를 기록한다(e2e/fake-openai.mjs).
 */
import { expect, test, type Page } from "@playwright/test";

import { el, fakeOpenAI, inDialog, saveKey } from "./helpers";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
});

/** 결과 화면을 연다 — 처음이면 사전 안내에서 분석을 시작하고, 이미 분석했으면 바로 결과로 간다. */
async function openResult(page: Page, url: string): Promise<string> {
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

const box = (page: Page) => el(page, "10.3").locator("textarea");

test("S4 — 추천 질문 · 근거 칩 · 이어지는 질문 · 영상에 없는 내용 · 다시 열기", async ({
  page,
  request,
}) => {
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 });
  const url = await openResult(page, "https://youtu.be/e2eAskVid01");

  // 처음에는 스크립트 탭이고 질문 수 배지는 0
  await expect(el(page, "7.1")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "7.3")).toHaveText("0");

  // 추천 질문 알약 → 질문하기 탭으로 바뀌고 바로 보낸다. 답을 기다리는 동안 잠긴다
  await fakeOpenAI(request, { chat_delay_ms: 800 });
  await el(page, "5.1").click();
  await expect(el(page, "7.2")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "9.3")).toHaveText("청킹 전략을 바꾼 근거는?");
  await expect(el(page, "9.7")).toHaveText("답을 만드는 중이에요");
  await expect(el(page, "10.4")).toHaveAttribute("aria-disabled", "true");
  await expect(el(page, "9.4")).toContainText("'청킹 전략을 바꾼 근거는?'에 대한 답입니다");
  await expect(el(page, "9.7")).toHaveCount(0);
  await expect(el(page, "10.4")).not.toHaveAttribute("aria-disabled", "true");
  await expect(el(page, "9.5")).toHaveText("00:00");
  await expect(el(page, "7.3")).toHaveText("1");

  // 근거 칩 → 스크립트 탭 · 그 시각(공통 1.3)
  await el(page, "9.5").click();
  await expect(el(page, "7.1")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "8.2")).toHaveText("00:00");

  // 이어지는 질문 — 앞선 대화가 맥락으로 간다. Enter로 보내고 입력칸이 비워진다
  await fakeOpenAI(request, { chat_delay_ms: 0 });
  await el(page, "7.2").click();
  await box(page).fill("그거 성능은?");
  await box(page).press("Enter");
  const turns = page.locator(".turn");
  await expect(turns).toHaveCount(2);
  await expect(turns.nth(1).locator(".turn-answer")).toContainText(
    "앞선 질문('청킹 전략을 바꾼 근거는?')에 이어",
  );
  await expect(box(page)).toHaveValue("");
  await expect(el(page, "7.3")).toHaveText("2");

  // 영상에 없는 질문 — 흐린 답과 '영상에 없는 내용', 근거 칩 없음(모델이 시각을 붙여도)
  await box(page).fill("발표자 회사 매출은?");
  await el(page, "10.4").click();
  await expect(turns).toHaveCount(3);
  await expect(turns.nth(2).locator(".turn-answer")).toHaveClass(/is-dim/);
  await expect(turns.nth(2).locator(".turn-none")).toHaveText("영상에 없는 내용");
  await expect(turns.nth(2).locator(".time-chip")).toHaveCount(0);
  await expect(el(page, "7.3")).toHaveText("3");

  const fake = await fakeOpenAI(request);
  expect(fake.asks.map((a) => a.history)).toEqual([0, 1, 2]); // 앞선 턴이 쌓여 간다

  // 다시 열면 기본은 스크립트 탭 — 배지가 기록을 알리고, 질문하기 탭에 세 턴이 그대로 있다
  await page.goto(url);
  await expect(el(page, "7.1")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "7.3")).toHaveText("3");
  await el(page, "7.2").click();
  await expect(page.locator(".turn")).toHaveCount(3);
});

test("답변 실패 — 이유 한 줄과 다시 시도, 실패한 질문은 세지 않는다", async ({ page, request }) => {
  await openResult(page, "https://youtu.be/e2eAskVid01");
  await el(page, "7.2").click();
  const before = Number(await el(page, "7.3").textContent());
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0, chat_fail: 1 });
  await box(page).fill("RAG를 고른 이유는?");
  await el(page, "10.4").click();
  await expect(el(page, "9.8")).toHaveText("OpenAI API에 연결하지 못했어요 — OpenAI 서버 오류");
  await expect(el(page, "7.3")).toHaveText(String(before)); // 실패한 질문은 세지 않는다
  await el(page, "9.9").click();
  await expect(el(page, "9.8")).toHaveCount(0);
  await expect(page.locator(".turn").last().locator(".turn-answer")).toContainText(
    "'RAG를 고른 이유는?'에 대한 답입니다",
  );
  await expect(el(page, "7.3")).toHaveText(String(before + 1));
});

test("3시간 스크립트 — 질문과 맞는 챕터만 보낸다", async ({ page, request }) => {
  await openResult(page, "https://youtu.be/e2eLong3h01");
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 });
  await el(page, "7.2").click();
  await expect(el(page, "9.1")).toContainText("아직 질문이 없어요");
  await box(page).fill("소유자는 누가 정했어?");
  await box(page).press("Enter");
  await expect(el(page, "9.1")).toHaveCount(0);
  await expect(el(page, "9.4")).toContainText("스크립트 1:50:00부터 2:19:50까지를 봤어요");
  await expect(el(page, "9.5")).toHaveText("1:50:00"); // 1시간 넘는 영상은 h:mm:ss
  const fake = await fakeOpenAI(request);
  // 스크립트 전부가 아니라 '메타데이터 채우기' 챕터(1:50:00 ~ 2:20:00)만 받았다
  expect(fake.asks).toEqual([
    { question: "소유자는 누가 정했어?", history: 0, first: "1:50:00", last: "2:19:50" },
  ]);
});

test("키가 없으면 — 기록은 보이고 질문은 막힌다(10.2)", async ({ page, request }) => {
  const url = await openResult(page, "https://youtu.be/e2eAskVid01");
  await page.route("**/api/settings", async (route) => {
    const res = await route.fetch();
    const body = await res.json();
    body.key = { ...body.key, state: "missing", reason_kind: null, reason: null };
    await route.fulfill({ response: res, json: body });
  });
  await page.goto(url);
  const sent = (await fakeOpenAI(request, { reset: true })).asks.length;
  await el(page, "7.2").click();
  await expect(page.locator(".turn").first()).toBeVisible(); // 이전 기록은 그대로
  await expect(el(page, "10.2")).toHaveText("API 키가 없어 질문할 수 없어요. 키 넣으러 가기");
  await expect(el(page, "10.2").getByRole("link")).toHaveAttribute("href", "/settings");
  await expect(box(page)).toBeDisabled();
  await expect(el(page, "10.4")).toHaveAttribute("aria-disabled", "true");
  await el(page, "10.1").click(); // 추천 칩도 보내지 않는다
  await el(page, "7.1").click();
  await el(page, "5.1").click(); // 알약은 탭만 바꾼다
  await expect(el(page, "7.2")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "9.7")).toHaveCount(0);
  expect((await fakeOpenAI(request)).asks.length).toBe(sent);
});
