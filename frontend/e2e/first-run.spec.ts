/**
 * 첫 실행 — 빈 앱을 열면 배너 → 설정에서 키 저장 → 배너 사라짐(VA-SCN-001 S6 1번, VA-UI-002 UI-1 S-8 · UI-5 S-1 · S-2).
 * 요소는 와이어프레임 번호(data-el)로 찾는다.
 */
import http from "node:http";

import { expect, test, type Page } from "@playwright/test";

const GOOD_KEY = "sk-e2e-good-000000000000000000"; // e2e/fake-openai.mjs와 같은 값
const el = (page: Page, no: string) => page.locator(`[data-el="${no}"]`);

test("키 없이 열고, 설정에서 키를 넣으면 배너가 사라진다", async ({ page }) => {
  await page.goto("/");
  await expect(el(page, "1")).toBeVisible();
  await expect(el(page, "1.1")).toHaveText(/^OpenAI API 키가 없어서 아직 분석할 수 없어요/);
  await expect(el(page, "3.3")).toHaveAttribute("aria-disabled", "true");
  await expect(el(page, "4.6")).toHaveAttribute("aria-disabled", "true");
  await expect(el(page, "5.2")).toHaveText("0개");
  await expect(el(page, "7.1")).toHaveText("아직 분석한 영상이 없어요");
  await expect(el(page, "7.2")).toContainText("설정에서 OpenAI API 키를 넣은 뒤");

  // 막힌 분석 버튼은 초점을 받고, 누르면 설정으로 간다(aria-disabled라 키보드로 누른다)
  await el(page, "4.6").focus();
  await expect(el(page, "4.6")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page.getByRole("status")).toHaveCount(0); // UI-5에는 배너가 없다(여기의 1은 제목 영역)
  await expect(el(page, "2.1")).toHaveText("키 없음");
  await expect(el(page, "2.2")).toHaveCount(0);
  await expect(page.getByLabel("키 넣기")).toBeVisible();

  // 틀린 키 — 저장하지 않고 이유를 보인다
  await page.getByLabel("키 넣기").fill("sk-e2e-wrong-00000000000000000");
  await el(page, "2.4").click();
  await expect(el(page, "2.5")).toHaveText(/^키를 확인하지 못했어요 — /);
  await expect(el(page, "2.1")).toHaveText("확인 실패");
  await expect(el(page, "2.2")).toHaveCount(0);

  // 맞는 키 — 저장되고 가린 키가 보인다. 전체 키는 화면에 없다
  await page.getByLabel("키 넣기").fill(GOOD_KEY);
  await el(page, "2.4").click();
  await expect(el(page, "2.1")).toContainText("확인됨 · 오늘");
  await expect(el(page, "2.2")).toContainText("sk-…0000");
  await expect(el(page, "2.2")).toContainText(".env에 저장됨");
  await expect(el(page, "2.5")).toHaveCount(0);
  await expect(page.getByLabel("새 키로 바꾸기")).toHaveValue("");
  await expect(page.locator("body")).not.toContainText(GOOD_KEY);

  // 저장하고 홈으로 — 배너가 사라지고 버튼이 켜진다
  await el(page, "6.2").click();
  await expect(page).toHaveURL(/\/$/);
  await expect(el(page, "1")).toHaveCount(0);
  await expect(el(page, "3.3")).not.toHaveAttribute("aria-disabled", "true");
  await expect(el(page, "7.2")).not.toContainText("설정에서");
});

test("모델을 바꾸면 단가 도움말이 따라 바뀐다", async ({ page }) => {
  await page.goto("/settings");
  await expect(el(page, "3.4")).toHaveText("100만 토큰당 입력 $0.25 · 출력 $2.00");
  await expect(el(page, "3.2")).toContainText("분당 $0.006");
  await page.locator("#llm-model").selectOption("gpt-5.4");
  await expect(el(page, "3.4")).toHaveText("100만 토큰당 입력 $2.50 · 출력 $15.00");
  await el(page, "6.1").click(); // 취소 — 저장하지 않는다
  await page.goto("/settings");
  await expect(page.locator("#llm-model")).toHaveValue("gpt-5-mini");
});

test.describe("배너 문구 셋", () => {
  const status = (key: Record<string, unknown>) => ({
    key: {
      masked: "sk-…1234",
      stored_in: ".env에 저장됨",
      checked_at: new Date().toISOString(),
      ...key,
    },
    models: { stt: "whisper-1", text: "gpt-5-mini" },
    model_options: { stt: [], text: [] },
    inbox_path: "~/video-agent/inbox",
  });

  test("확인 실패 — 이유를 보이고 버튼을 막는다", async ({ page }) => {
    await page.route("**/api/settings", (route) =>
      route.fulfill({
        json: status({ state: "invalid", reason_kind: "quota", reason: "잔액이 없습니다" }),
      }),
    );
    await page.goto("/");
    await expect(el(page, "1.1")).toHaveText("키를 확인하지 못했어요 — 잔액이 없습니다");
    await expect(el(page, "1.2")).toBeVisible();
    await expect(el(page, "3.3")).toHaveAttribute("aria-disabled", "true");
  });

  test("연결을 확인하지 못함 — [키 넣으러 가기]가 없고 버튼을 막지 않는다", async ({ page }) => {
    await page.route("**/api/settings", (route) =>
      route.fulfill({
        json: status({ state: "invalid", reason_kind: "network", reason: "연결하지 못했습니다" }),
      }),
    );
    await page.goto("/");
    await expect(el(page, "1.1")).toHaveText(/^연결을 확인하지 못했어요 — /);
    await expect(el(page, "1.2")).toHaveCount(0);
    await expect(el(page, "3.3")).not.toHaveAttribute("aria-disabled", "true");
    await expect(el(page, "4.6")).not.toHaveAttribute("aria-disabled", "true");
  });
});

test.describe("저장 실패", () => {
  test("키 확인이 연결 실패면 이유만 보이고 2.1은 그대로다(SEQ-12)", async ({ page }) => {
    await page.route("**/api/settings/key", (route) =>
      route.fulfill({
        status: 502,
        contentType: "application/problem+json",
        json: { type: "urn:va:llm-unavailable", status: 502, reason: "연결하지 못했습니다" },
      }),
    );
    await page.goto("/settings");
    const before = await el(page, "2.1").textContent();
    await page.locator("#new-key").fill(GOOD_KEY);
    await el(page, "2.4").click();
    await expect(el(page, "2.5")).toHaveText("키를 확인하지 못했어요 — 연결하지 못했습니다");
    await expect(el(page, "2.1")).toHaveText(before ?? "");
    await expect(page.locator("#new-key")).not.toHaveAttribute("aria-invalid", "true");
  });

  test("모델 저장이 실패하면 그 자리에 알리고 머문다", async ({ page }) => {
    await page.route("**/api/settings/models", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/problem+json",
        json: { type: "urn:va:internal", status: 500, detail: "모델 선택을 .env에 쓰지 못했어요" },
      }),
    );
    await page.goto("/settings");
    await el(page, "6.2").click();
    await expect(el(page, "6").getByRole("alert")).toHaveText(
      "모델 선택을 저장하지 못했어요 — 모델 선택을 .env에 쓰지 못했어요",
    );
    await expect(page).toHaveURL(/\/settings$/);
  });
});

/** Host 헤더를 마음대로 정해 web에 GET — 브라우저는 Host를 바꿀 수 없어 Node로 보낸다 */
function getWithHost(url: string, host: string): Promise<number> {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { headers: { Host: host } }, (res) => {
      res.resume();
      resolve(res.statusCode ?? 0);
    });
    req.on("error", reject);
  });
}

test("다른 Host로 온 /api 요청은 막는다 — DNS 리바인딩(INFRA 5절)", async ({ baseURL }) => {
  const url = `${baseURL}/api/settings`;
  const port = new URL(url).port;
  expect(await getWithHost(url, `evil.example:${port}`)).toBe(400);
  expect(await getWithHost(url, `127.0.0.1:${port}`)).toBe(200);
  expect(await getWithHost(url, `localhost:${port}`)).toBe(200);
});
