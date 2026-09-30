/**
 * 인포그래픽(VA-UC-001 UC-H9, VA-UI-002 UI-4 15 · UI-8 · UI-9 · UI-5 7, VA-CODE-001 D3) — 카드의 [인포그래픽
 * 만들기]로 확인 창(UI-8)을 열어 값 · 보내는 것을 보고 맡기면 카드가 그리는 중이 되고, 다 되면 그림 · 만든
 * 정보가 보인다. 그림을 누르면 크게 본다(UI-9). 그리는 동안 다른 화면에 갔다 와도 이어진다. 다시 만들기가
 * 실패하면 이전 그림은 그대로이고 실패 한 줄이 붙는다. 키 확인이 실패하면 카드가 키 넣으러 가기를 보인다.
 * 설정에서 품질을 바꾸면 카드 · 확인 창의 한 장 값이 따라 바뀐다. 파일로 저장하면 그림이 노트 곁에 간다.
 * 이미지 모델은 가짜 OpenAI다(e2e/fake-openai.mjs — 작은 PNG).
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { DATA, el, fakeOpenAI, inDialog, openResult, saveKey } from "./helpers";

test.beforeEach(async ({ request }) => {
  await fakeOpenAI(request, { reset: true }); // 키 확인을 막은 앞 테스트가 있어도 키를 넣을 수 있게 먼저
  await saveKey(request);
});

/** 카드의 [인포그래픽 만들기]로 확인 창을 열어 [만들기]를 누른다. */
async function make(page: Page, button = "15.3"): Promise<void> {
  await el(page, button).click();
  await expect(inDialog(page, "4.2")).toBeFocused();
  await inDialog(page, "4.2").click();
  await expect(page.getByRole("dialog")).toHaveCount(0); // 곧바로 닫힌다
}

async function lastPrompt(request: APIRequestContext) {
  return (await fakeOpenAI(request)).images.at(-1);
}

test("인포그래픽을 만든다 — 확인 창 → 그리는 중 → 다 됨 → 크게 보기 → 노트로", async ({
  page,
  request,
}) => {
  await openResult(page, "https://youtu.be/e2eInfogr01");
  // 만들기 전 — 설정 품질(낮음)의 한 장 값
  await expect(el(page, "15.1")).toHaveText("인포그래픽 한 장으로 보기");
  await expect(el(page, "15.2")).toContainText("한 장 약 $0.006 · 누를 때만 만들어요");

  // UI-8 — 값 · 품질 · 보내는 것
  await fakeOpenAI(request, { image_delay_ms: 1500 });
  await el(page, "15.3").click();
  await expect(inDialog(page, "1.1")).toHaveText("인포그래픽 만들기");
  await expect(inDialog(page, "2.1")).toHaveText("약 $0.006");
  await expect(inDialog(page, "2.2")).toHaveText("낮음 · gpt-image-2");
  await expect(inDialog(page, "3.1")).toHaveText("한 줄 요약 1문장 · 인사이트 6개 · 챕터 제목 5개");
  await expect(inDialog(page, "3.3")).toHaveCount(0); // 처음 — 바꿀 그림이 없다
  await expect(inDialog(page, "4.2")).toBeFocused();
  await expect(inDialog(page, "4.2")).toHaveText("만들기 · 약 $0.006");
  await inDialog(page, "4.2").click();
  await expect(page.getByRole("dialog")).toHaveCount(0);

  // 그리는 중 — 결과를 계속 읽는다. 다 되면 그림과 만든 정보
  await expect(el(page, "15.4")).toHaveAttribute("aria-disabled", "true");
  await expect(el(page, "15.4")).toHaveText("그리는 중…");
  await expect(el(page, "15.5")).toBeVisible({ timeout: 10_000 });
  await expect(el(page, "15.6")).toHaveText(/^gpt-image-2 · 낮은 품질 · 오늘 \d\d:\d\d 만듦$/);
  await expect(el(page, "15.7")).toContainText("AI가 그린 그림이에요");
  await expect(el(page, "15.8")).toHaveText("파일로 내보내면 노트에 함께 들어가요.");
  // 보낸 것은 한 줄 요약 · 인사이트 · 챕터 제목뿐 — 스크립트 줄은 없다
  const sent = await lastPrompt(request);
  expect([sent?.model, sent?.size, sent?.quality]).toEqual(["gpt-image-2", "1024x1536", "low"]);
  expect(sent?.prompt).toContain("RAG 서비스를 1년 운영하며");
  expect(sent?.prompt).toContain("pgvector 선택");
  expect(sent?.prompt).not.toContain("번째 문장");

  // UI-9 — 크게 보기. 닫으면 초점이 그림으로 돌아온다
  await el(page, "15.5").click();
  await expect(inDialog(page, "1.1")).toHaveText("인포그래픽");
  await expect(inDialog(page, "1.3")).toBeFocused();
  await expect(inDialog(page, "1.2")).toHaveText(/^gpt-image-2 · 낮은 품질 · 오늘 \d\d:\d\d 만듦$/);
  await expect(inDialog(page, "2")).toHaveAttribute(
    "aria-label",
    "인포그래픽 — 인포그래픽을 만드는 발표",
  );
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "15.5")).toBeFocused();

  // 파일로 저장 — 그림이 노트 곁에, 노트의 한눈에 보기 첫 줄이 그 그림을 가리킨다
  await el(page, "1.2").click();
  await expect(inDialog(page, "2.3").locator(".export-file")).toContainText(["인포그래픽 1장.png"]);
  await inDialog(page, "5.3").click();
  await expect(el(page, "11")).toHaveText(/· 그림 6장$/); // 장면 다섯 + 인포그래픽
  const name = "인포그래픽을 만드는 발표";
  const note = readFileSync(path.join(DATA, "export", `${name}.md`), "utf-8");
  expect(note).toContain(`## 한눈에 보기\n![[${name} 인포그래픽.png]]\n`);
  const png = readFileSync(path.join(DATA, "export", `${name} 인포그래픽.png`));
  expect(png.subarray(1, 4).toString()).toBe("PNG");
});

test("그리는 동안 다른 화면에 갔다 와도 이어진다", async ({ page, request }) => {
  const url = await openResult(page, "https://youtu.be/e2eInfogr02");
  await fakeOpenAI(request, { image_delay_ms: 3000 });
  await make(page);
  await expect(el(page, "15.4")).toBeVisible();
  await page.goto("/"); // 떠난다 — 서버는 계속 그린다
  await page.goto(url);
  await expect(el(page, "15.4")).toBeVisible(); // 돌아오면 그리는 중이거나
  await expect(el(page, "15.5")).toBeVisible({ timeout: 10_000 }); // 다 된 모습
});

test("그리기가 실패하면 이유 한 줄 — 다시 만들기가 실패해도 이전 그림은 그대로", async ({
  page,
  request,
}) => {
  await openResult(page, "https://youtu.be/e2eInfogr03");
  // 처음 그리기가 안전 정책에 걸렸다 — 실패 카드와 다시 만들기
  await fakeOpenAI(request, { image_fail: "moderation" });
  await make(page);
  await expect(el(page, "15.11")).toHaveText(
    "인포그래픽을 만들지 못했어요 — 안전 정책에 걸려 그리지 않음",
    { timeout: 10_000 },
  );
  await expect(el(page, "15.5")).toHaveCount(0);
  // 다시 만들기 — 이번에는 된다
  await make(page, "15.10");
  await expect(el(page, "15.5")).toBeVisible({ timeout: 10_000 });
  await expect(el(page, "15.11")).toHaveCount(0);
  // 한 번 더 — 서버 오류. 확인 창은 바꾼다는 안내를 보이고, 실패해도 이전 그림이 남는다
  await fakeOpenAI(request, { image_fail: "server" });
  await el(page, "15.10").click();
  await expect(inDialog(page, "3.3")).toHaveText("새 그림이 지금 그림을 바꿔요.");
  await inDialog(page, "4.2").click();
  await expect(el(page, "15.11")).toHaveText("인포그래픽을 만들지 못했어요 — OpenAI 서버 오류", {
    timeout: 10_000,
  });
  await expect(el(page, "15.5")).toBeVisible(); // 다 됨 카드 위에 실패 한 줄
});

test("키 확인이 실패하면 — 확인 창이 닫히고 카드가 키 넣으러 가기", async ({ page, request }) => {
  await openResult(page, "https://youtu.be/e2eInfogr04");
  await fakeOpenAI(request, { models: 401 }); // 맡길 때 다시 확인하면 거절된다
  try {
    await make(page);
    await expect(el(page, "15.12")).toHaveText("키 넣으러 가기");
    await expect(el(page, "15")).toContainText("OpenAI API 키가 없어서 지금은 만들 수 없어요.");
    expect((await fakeOpenAI(request)).images).toEqual([]); // 그리지 않았다
    await el(page, "15.12").click();
    await expect(page).toHaveURL(/\/settings$/);
  } finally {
    await fakeOpenAI(request, { models: null });
    await saveKey(request); // 뒤 테스트가 맞는 키로 시작하게
  }
});

test("설정에서 품질을 바꾸면 카드 · 확인 창의 한 장 값이 바뀐다", async ({ page }) => {
  const url = await openResult(page, "https://youtu.be/e2eInfogr05");
  await expect(el(page, "15.2")).toContainText("한 장 약 $0.006");
  await page.goto("/settings");
  await expect(el(page, "7.5")).toHaveText("값이 가장 싸요. 그림 속 작은 글자는 흐릴 수 있어요.");
  await expect(el(page, "7.3").getByRole("radio", { name: /낮음 \(기본\)/ })).toBeChecked();
  await el(page, "7.3").getByRole("radio", { name: /중간/ }).check();
  await expect(el(page, "7.5")).toHaveText("글자가 더 또렷해요. 값은 낮음의 약 8배예요.");
  await el(page, "6.2").click();
  await expect(page).toHaveURL(/\/$/);
  try {
    await page.goto(url);
    await expect(el(page, "15.2")).toContainText("한 장 약 $0.05 · 누를 때만 만들어요");
    await el(page, "15.3").click();
    await expect(inDialog(page, "2.1")).toHaveText("약 $0.05");
    await expect(inDialog(page, "2.2")).toHaveText("중간 · gpt-image-2");
    await page.keyboard.press("Escape"); // 그만둔다 — 아무것도 보내지 않는다
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(el(page, "15.3")).toBeFocused();
  } finally {
    // 뒤 테스트가 낮음으로 시작하게 되돌린다
    await page.goto("/settings");
    await el(page, "7.3").getByRole("radio", { name: /낮음/ }).check();
    await el(page, "6.2").click();
    await expect(page).toHaveURL(/\/$/);
  }
});
