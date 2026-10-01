/**
 * S3 구간 찾기를 키보드로(VA-SCN-001 S3 · 카드 E5, VA-UI-001 4.6) — 한눈에 보기의 줄마다 Tab 한 번 · ← → · Enter ·
 * 가리킨 칸 이름(UI-4 13.6), 결과 탭 ← →, 키보드 초점 고리와 헤더 밑에 숨지 않게 띄우는 스크롤 여백.
 * 3시간 워크숍이라 파트 띠까지 세 줄이다. 키를 저장하므로 빈 앱을 보는 first-run보다 뒤에 돈다(파일 이름 순).
 * 시각을 고른 뒤의 자리(카드 E6, 공통 1.3) — 이미 보이는 구간은 움직이지 않고, 안 보이면 가운데, 같은 시각을
 * 다시 눌러도 같다. 고른 시각은 주소 `?t={초}`에 남아 새로 고치거나 다녀와도 그 자리다. 37.5초마다 줄이 있는
 * 50분 발표라 구간 시각 절반이 소수다.
 */
import { expect, test, type Page } from "@playwright/test";

import { el, fakeOpenAI, openResult, saveKey } from "./helpers";

const VIDEO = "https://youtu.be/e2eA11yLng1";
const SCROLL = "https://youtu.be/e2eScroll01";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 });
});

test("한눈에 보기 — 줄마다 Tab 한 번, 화살표로 옮기고 Enter로 고른다", async ({ page }) => {
  await openResult(page, VIDEO);
  const focused = page.locator(":focus");

  // 줄마다 칸 하나만 Tab이 멈춘다 — 고른 시각이 없으면 첫 칸
  for (const row of ["파트 띠", "인사이트 점", "챕터 막대"]) {
    await expect(
      page.getByRole("toolbar", { name: row }).locator('button[tabindex="0"]'),
    ).toHaveCount(1);
  }
  await el(page, "13.1").focus();
  await expect(focused).toHaveAttribute("aria-label", "파트 1 · 0:00:00 오전 세션 — 현황과 문제");
  await page.keyboard.press("Tab");
  await expect(focused).toHaveAttribute("aria-label", /^인사이트 01 · /);
  await page.keyboard.press("Tab");
  await expect(focused).toHaveAttribute("aria-label", "챕터 1 · 0:00:00 워크숍 소개");

  // ← → · Home · End는 초점만 옮긴다 — 범례 자리에 가리킨 칸 이름, 고른 시각은 그대로
  await page.keyboard.press("ArrowRight");
  await expect(focused).toHaveAttribute("aria-label", "챕터 2 · 0:20:00 데이터를 찾는 시간");
  await expect(focused).toHaveCSS("outline-style", "solid");
  await expect(focused).toHaveCSS("outline-color", "rgb(15, 110, 104)");
  await expect(el(page, "13.6")).toContainText("챕터 2");
  await expect(el(page, "13.6")).toContainText("0:20:00");
  await expect(el(page, "13.6")).toContainText("데이터를 찾는 시간");
  await expect(el(page, "13.6")).toContainText("← → 옮기기 · Enter 이동");
  await expect(el(page, "13.5")).toHaveCount(0);
  await expect(el(page, "8.2")).toHaveText("");
  await page.keyboard.press("End");
  await expect(focused).toHaveAttribute("aria-label", /^챕터 6 · /);
  await page.keyboard.press("ArrowRight"); // 끝에서 멈춘다
  await expect(focused).toHaveAttribute("aria-label", /^챕터 6 · /);
  await page.keyboard.press("Home");
  await expect(focused).toHaveAttribute("aria-label", /^챕터 1 · /);

  // Enter가 누르기 — 그 시각으로 간다
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("Enter");
  await expect(el(page, "8.2")).toHaveText("0:20:00");
  await expect(focused).toHaveAttribute("aria-pressed", "true");

  // Esc로 이름 줄을 닫으면 범례가 돌아온다
  await page.keyboard.press("Escape");
  await expect(el(page, "13.6")).toHaveCount(0);
  await expect(el(page, "13.5")).toBeVisible();

  // 막대 다음은 마인드맵 — 줄로 돌아오면 고른 칸에서 시작한다
  await page.keyboard.press("Tab");
  await expect(focused).toHaveAttribute("data-el", "14.4");
  await page.keyboard.press("Shift+Tab");
  await expect(focused).toHaveAttribute("aria-label", "챕터 2 · 0:20:00 데이터를 찾는 시간");
  await expect(el(page, "13.6")).toContainText("데이터를 찾는 시간");

  // 키보드와 마우스가 겹치면 마지막으로 가리킨 쪽 — 마우스로 가리키면 그 칸, 다시 → 하면 초점 칸
  const bars = page.getByRole("toolbar", { name: "챕터 막대" });
  await bars.getByRole("button", { name: /^챕터 4 · / }).hover();
  await expect(el(page, "13.6")).toContainText("실습 준비");
  await expect(el(page, "13.6")).not.toContainText("옮기기");
  await page.keyboard.press("ArrowRight");
  await expect(focused).toHaveAttribute("aria-label", /^챕터 3 · /);
  await expect(el(page, "13.6")).toContainText("카탈로그 후보");
  await expect(el(page, "13.6")).toContainText("← → 옮기기 · Enter 이동");
  // 마우스로 가리켰다가 카드를 나가면 남은 쪽 — 초점이 아직 줄에 있어 초점 칸 이름이 돌아온다
  await bars.getByRole("button", { name: /^챕터 5 · / }).hover();
  await expect(el(page, "13.6")).toContainText("메타데이터 채우기");
  await el(page, "3").hover();
  await expect(el(page, "13.6")).toContainText("카탈로그 후보");
  await expect(el(page, "13.6")).toContainText("← → 옮기기 · Enter 이동");
});

test("인사이트 점은 시각 차례로 옮긴다 — 번호가 시각 차례가 아니어도", async ({ page }) => {
  // 인사이트 번호는 모델이 정한 차례라 시각과 다를 수 있다 — 01의 근거를 0:25:00으로 옮겨 본다
  await page.route("**/api/videos/*/result", async (route) => {
    const res = await route.fetch();
    const body = await res.json();
    body.summary.insights[0].source_secs = [1500];
    await route.fulfill({ response: res, json: body });
  });
  await openResult(page, VIDEO);
  const focused = page.locator(":focus");
  const dots = page.getByRole("toolbar", { name: "인사이트 점" });

  // 들어오면 시각 차례의 첫 점 — 02(0:05:00)
  const first = dots.locator('button[tabindex="0"]');
  await expect(first).toHaveAttribute("aria-label", /^인사이트 02 · /);
  await first.focus();
  await page.keyboard.press("ArrowRight");
  await expect(focused).toHaveAttribute("aria-label", /^인사이트 03 · /);
  await page.keyboard.press("ArrowRight");
  await expect(focused).toHaveAttribute("aria-label", /^인사이트 04 · /);
  await page.keyboard.press("ArrowRight");
  await expect(focused).toHaveAttribute("aria-label", "인사이트 01 · 0:25:00");
  await page.keyboard.press("End");
  await expect(focused).toHaveAttribute("aria-label", /^인사이트 06 · /);
  await page.keyboard.press("Home");
  await expect(focused).toHaveAttribute("aria-label", /^인사이트 02 · /);
});

test("마우스로 가리킨 칸 — 범례 자리에 이름, 카드를 나가면 범례", async ({ page }) => {
  await openResult(page, VIDEO);
  const bars = page.getByRole("toolbar", { name: "챕터 막대" });
  const third = bars.getByRole("button", { name: "챕터 3 · 0:45:00 카탈로그 후보" });

  await third.hover();
  await expect(third).toHaveCSS("background-color", "rgb(207, 230, 225)");
  await expect(el(page, "13.6")).toContainText("카탈로그 후보");
  await expect(el(page, "13.6")).not.toContainText("옮기기");
  // 카드 안에서는 이름 줄 쪽으로 옮겨도 남는다(WCAG 1.4.13)
  await el(page, "13.4").hover();
  await expect(el(page, "13.6")).toContainText("카탈로그 후보");
  // Esc로 닫는다
  await page.keyboard.press("Escape");
  await expect(el(page, "13.5")).toBeVisible();

  // 다시 가리키면 뜨고, 카드를 나가면 범례로 돌아간다
  await bars.getByRole("button", { name: /^챕터 4 · / }).hover();
  await expect(el(page, "13.6")).toContainText("실습 준비");
  await el(page, "3").hover();
  await expect(el(page, "13.5")).toBeVisible();
  await expect(el(page, "13.6")).toHaveCount(0);
});

test("결과 탭 — Tab 한 번에 묶고 ← →로 옮기면 바로 열린다", async ({ page }) => {
  await openResult(page, VIDEO);
  await expect(el(page, "7.1")).toHaveAttribute("tabindex", "0");
  await expect(el(page, "7.2")).toHaveAttribute("tabindex", "-1");

  await el(page, "7.1").focus();
  await page.keyboard.press("ArrowRight");
  await expect(el(page, "7.2")).toBeFocused();
  await expect(el(page, "7.2")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "9")).toBeVisible();
  await expect(el(page, "7.1")).toHaveAttribute("tabindex", "-1");

  await page.keyboard.press("ArrowLeft");
  await expect(el(page, "7.1")).toBeFocused();
  await expect(el(page, "7.1")).toHaveAttribute("aria-selected", "true");
  await expect(el(page, "8")).toBeVisible();
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

/** 고른 구간(8.3)이 스크립트(8) 가운데 언저리에 있는가 — 한 줄 높이 안. */
const centered = (page: Page) =>
  page.locator(".script-body").evaluate((box) => {
    const row = box.querySelector<HTMLElement>(".segment.is-selected");
    if (!row) return false;
    const mid = row.offsetTop + row.offsetHeight / 2 - box.scrollTop;
    return Math.abs(mid - box.clientHeight / 2) <= row.offsetHeight;
  });

test("시각을 고른 뒤의 자리 — 보이는 구간은 그대로, 안 보이면 가운데, 같은 시각도 다시", async ({
  page,
}) => {
  await openResult(page, SCROLL);
  const body = page.locator(".script-body");
  const top = () => body.evaluate((e) => Math.round(e.scrollTop));

  // 이미 다 보이는 구간을 누르면 강조만 옮겨 가고 움직이지 않는다 — 패널 아래쪽의 줄
  await body.evaluate((e) => {
    e.scrollTop = 600;
  });
  const low = await body.evaluate((box) =>
    [...box.querySelectorAll<HTMLElement>(".segment")].findIndex(
      (r) =>
        r.offsetTop >= box.scrollTop + box.clientHeight - 160 &&
        r.offsetTop + r.offsetHeight <= box.scrollTop + box.clientHeight,
    ),
  );
  expect(low).toBeGreaterThan(0);
  await page.locator(".segment").nth(low).click();
  await expect(page.locator(".segment").nth(low)).toHaveAttribute("aria-pressed", "true");
  expect(await top()).toBe(600);

  // 안 보이는 시각은 가운데로 — 인사이트 20:00
  const chip = page.getByRole("button", { name: "20:00 위치의 스크립트로 이동", exact: true });
  await chip.click();
  await expect.poll(() => centered(page)).toBe(true);

  // 스크롤해 떠난 뒤 같은 시각을 다시 누르면 돌아온다
  await body.evaluate((e) => {
    e.scrollTop = 0;
  });
  await chip.click();
  await expect.poll(() => centered(page)).toBe(true);
});

test("고른 시각은 주소에 — 소수 시각 · 새로 고침 · 설정에 다녀오기 · 잘못된 t", async ({ page }) => {
  const url = await openResult(page, SCROLL);
  const entries = await page.evaluate(() => history.length);

  // 소수 시각의 구간(0:37.5)을 누르면 주소에 그대로 남고, 새로 고쳐도 같은 구간이다
  const row = page.locator(".segment").nth(1);
  await row.click();
  await expect(page).toHaveURL(`${url}?t=37.5`);
  await page.reload();
  await expect(row).toHaveAttribute("aria-pressed", "true");
  await expect(el(page, "8.2")).toHaveText("00:37");

  // 챕터 카드 — 설정에 갔다가 뒤로 가기로 돌아와도 같은 챕터가 선택 모양이다
  const card = page.locator(".chapter", { hasText: "pgvector 선택" });
  await card.click();
  await expect(page).toHaveURL(`${url}?t=1200`);
  expect(await page.evaluate(() => history.length)).toBe(entries); // 바꿔 써서 기록이 늘지 않는다
  await page.getByRole("link", { name: "설정" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await page.goBack();
  await expect(card).toHaveAttribute("aria-pressed", "true");
  await expect(el(page, "8.2")).toHaveText("20:00");
  await expect.poll(() => centered(page)).toBe(true);

  // 뒤로 가기는 시각마다 멈추지 않고 결과 앞 화면으로
  await page.goBack();
  await expect(page).not.toHaveURL(/\/videos\//);

  // 잘못된 t — 음수 · 길이(50:00) 넘음 · 글자 · 소수 넷째 자리는 고르지 않은 채로 연다
  for (const bad of ["-5", "3001", "abc", "12.3456"]) {
    await page.goto(`${url}?t=${bad}`);
    await expect(el(page, "8.3")).toBeVisible();
    await expect(el(page, "8.2")).toHaveText("");
    await expect(page.locator(".segment.is-selected")).toHaveCount(0);
  }
});
