/**
 * 챕터 대표 장면(VA-UC-001 UC-S7 · UC-H3 1a, VA-CODE-001 D2) — 장면 단계에서 진행 화면의 장면 칸이 한 장씩
 * 차고(UI-3 4.9 ~ 4.11) 결과 챕터 카드에 장면이 붙는다(UI-4 6.7). 스토리보드가 없는 영상은 장면 없이 끝난다.
 * 장면 단계 전에 분석한 결과는 열 때 채우기를 맡기고 그동안 6.8이 깜빡인다 — OpenAI는 부르지 않는다.
 * 채우는 동안 지우면 채우기가 멈춰 장면 폴더가 다시 생기지 않는다. 채우기가 장면 없이 끝나면 다시
 * 맡기지 않고 6.8을 거둔다(열 때 한 번).
 * 스토리보드 · 칸 자르기는 가짜다(e2e/fake-ytdlp.mjs · fake-ffmpeg.mjs).
 */
import { existsSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import {
  DATA,
  el,
  fakeOpenAI,
  forgetFrames,
  inAlert,
  inDialog,
  openResult,
  saveKey,
} from "./helpers";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
  await fakeOpenAI(request, { reset: true });
});

const idOf = (url: string) => Number(url.split("/").pop());

test("장면 단계 — 진행 화면의 장면 칸이 차고 결과 챕터 카드에 장면", async ({ page, request }) => {
  await page.goto("/");
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eFrames01");
  await el(page, "3.3").click();
  await inDialog(page, "6.3").click();

  // UI-3 — 자막 있는 YouTube는 다섯 단계, 장면이 마지막
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  await expect(page.locator(".step-name")).toHaveText([
    "자막 가져오기",
    "핵심 요약",
    "챕터",
    "추천 질문",
    "장면",
  ]);
  // 장면 단계 — 가짜 ffmpeg가 칸을 0.5초마다 하나씩 자른다
  await expect(el(page, "3.1")).toHaveText("챕터 장면을 가져오는 중", { timeout: 20_000 });
  await expect(el(page, "3.2")).toHaveText(/^5단계 중 5단계/);
  await expect(el(page, "6.1")).toHaveText(
    "YouTube에서 미리 보기 썸네일 받기 · OpenAI로 보내는 것 없음",
  );
  await expect(el(page, "6.2")).toHaveText(
    "장면을 못 받아도 분석은 끝나요 — 결과가 장면 없이 열려요.",
  );
  await expect(page.locator(".frame-cell")).toHaveCount(5);
  await expect(page.locator(".frame-cell.is-done").first()).toBeVisible();
  await expect(el(page, "4.9")).toHaveAttribute("aria-label", /^챕터 5개 중 \d개 장면을 받음$/);
  await expect(el(page, "4.11")).toHaveText(
    "YouTube 재생 막대의 미리 보기 썸네일에서 챕터 시작에 가장 가까운 칸을 잘라요 — 영상은 내려받지 않아요.",
  );
  await expect(page.locator(".step-memo").last()).toHaveText(/^\d \/ 5$/);

  // 끝나면 결과 — 챕터 카드마다 장면(6.7), 가져오는 중(6.8)은 없다
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 20_000 });
  const id = idOf(page.url());
  await expect(page.locator(".chapter-frame")).toHaveCount(5);
  await expect(page.locator(".chapter-frame-wait")).toHaveCount(0);
  await expect(el(page, "6.7")).toHaveAttribute("role", "img");
  await expect(el(page, "6.7")).toHaveAttribute("aria-label", "00:00 장면");
  const picture = await request.get(`/api/videos/${id}/frames/1`);
  expect(picture.headers()["content-type"]).toBe("image/jpeg");
  // 장면을 누르면 카드를 누른 것과 같다
  await page.locator(".chapter-frame").nth(2).click();
  await expect(el(page, "8.2")).toHaveText("20:00");
  await expect(page.locator('.chapter[aria-pressed="true"]')).toContainText("pgvector 선택");
});

test("스토리보드가 없는 영상 — 장면 없이 결과가 열린다", async ({ page, request }) => {
  const id = idOf(await openResult(page, "https://youtu.be/e2eNoBoard1"));
  await expect(el(page, "6.1")).toHaveText("5개");
  await expect(page.locator(".chapter-frame")).toHaveCount(0);
  await expect(page.locator(".chapter-frame-wait")).toHaveCount(0);
  const set = await (await request.get(`/api/videos/${id}/frames`)).json();
  expect(set).toEqual({ state: "done", frames: [] }); // 해 봤지만 없다 — 다시 채우지 않는다
});

test("장면 단계 전에 분석한 결과 — 가져오는 중이 깜빡이고 장면이 채워진다", async ({
  page,
  request,
}) => {
  const id = idOf(await openResult(page, "https://youtu.be/e2eOldRes01"));
  forgetFrames(id);
  const chats = (await fakeOpenAI(request)).chats;

  await page.reload();
  // 열 때 채우기를 맡기고 3초마다 장면만 다시 받는다 — 그 전까지 챕터마다 6.8
  await expect(page.locator(".chapter-frame-wait")).toHaveCount(5);
  await expect(el(page, "6.8")).toHaveText("장면 가져오는 중");
  await expect(page.locator(".chapter-frame")).toHaveCount(5, { timeout: 10_000 });
  await expect(page.locator(".chapter-frame-wait")).toHaveCount(0);
  expect((await fakeOpenAI(request)).chats).toBe(chats); // OpenAI 비용이 없다
});

test("장면을 채우는 동안 지우면 — 채우기가 멈추고 장면 폴더가 다시 생기지 않는다", async ({
  page,
}) => {
  const id = idOf(await openResult(page, "https://youtu.be/e2eOldRes02"));
  forgetFrames(id);
  await page.reload();
  await expect(page.locator(".chapter-frame-wait").first()).toBeVisible();

  await el(page, "1.3").click();
  await inAlert(page, "3.3").click();
  await expect(page).toHaveURL(/\/$/);
  // 칸 하나를 자르는 데 0.8초 — 멈추지 않았다면 그 사이에 장면 폴더를 다시 쓴다
  await page.waitForTimeout(2000);
  expect(existsSync(path.join(DATA, "frames", String(id)))).toBe(false);
});

test("채우기가 장면 없이 끝나면 — 다시 맡기지 않고 6.8을 거둔다", async ({ page }) => {
  const id = idOf(await openResult(page, "https://youtu.be/e2eOldRes03"));
  forgetFrames(id);
  // 서버가 장면을 쓰지 못하고 끝난 것처럼 — 맡기면 making, 다시 받으면 absent
  let posts = 0;
  await page.route(`**/api/videos/${id}/frames`, (route) => {
    if (route.request().method() === "POST") {
      posts += 1;
      return route.fulfill({ status: 202, json: { state: "making", frames: [] } });
    }
    return route.fulfill({ json: { state: "absent", frames: [] } });
  });
  await page.reload();
  await expect(page.locator(".chapter-frame-wait")).toHaveCount(5);
  // 3초 뒤 다시 받은 상태가 absent — 6.8을 거둔다
  await expect(page.locator(".chapter-frame-wait")).toHaveCount(0, { timeout: 10_000 });
  await page.waitForTimeout(4000); // 폴링 간격이 지나도 다시 맡기지 않는다
  expect(posts).toBe(1);
  await expect(page.locator(".chapter-frame-wait")).toHaveCount(0);
});
