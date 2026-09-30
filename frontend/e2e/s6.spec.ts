/**
 * S6 — 잘 안 되는 경우들(VA-SCN-001 S6, VA-CODE-001 B5). 등록 실패가 가는 곳 셋 — 입력 오류(3.4) · 배너 ·
 * 시작 불가 판(UI-2 7) — 을 진짜 api로 본다. 누를 때마다 키를 다시 확인하므로 가짜 OpenAI가 키 확인
 * 요청만 끊거나(인터넷 끊김) 거절한다(401). 주소로 바로 들어오기와 다른 창에서 먼저 시작하기도 본다.
 * 키 없이 시작은 first-run.spec, 분석 도중 실패 · 다시 시도는 retry.spec에 있다(B2).
 */
import { rmSync, utimesSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { el, fakeOpenAI, INBOX, inDialog, saveKey } from "./helpers";

const URL_HINT = "YouTube 주소를 넣어 주세요 — watch · youtu.be · shorts 주소를 받아요";
const OFFLINE = "연결을 확인하지 못했어요 — 인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다";

test.beforeEach(async ({ request }) => {
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 }); // 키 확인을 되돌린 뒤에 저장한다
  await saveKey(request);
});

const fileRow = (page: Page, name: string) => page.locator(".file-row", { hasText: name });

async function analyze(page: Page, url: string) {
  await el(page, "3.2").locator("input").fill(url);
  await el(page, "3.3").click();
}

/** 다른 창처럼 — 화면을 거치지 않고 등록한다. 같은 영상이면 기존 영상. 영상 id */
async function register(request: APIRequestContext, url: string): Promise<number> {
  const res = await request.post("/api/videos", { data: { source: "youtube", url } });
  return ((await res.json()) as { video: { id: number } }).video.id;
}

test("시작할 수 없는 영상 — 비공개 · 4시간은 판에 이유와 길이, 닫으면 넣은 것이 그대로", async ({
  page,
}) => {
  await page.goto("/");
  await analyze(page, "https://youtu.be/e2ePrivate1");
  const reason = "영상 정보를 가져오지 못했어요 — 비공개 영상";
  await expect(inDialog(page, "7.1")).toHaveText(reason);
  await expect(page.getByRole("dialog")).toHaveAccessibleName(reason); // 7.1이 판의 이름
  await expect(inDialog(page, "7.2")).toHaveCount(0); // 길이를 모른다
  await expect(inDialog(page, "6.3")).toHaveCount(0); // 분석 시작이 없다
  await expect(inDialog(page, "7.3")).toBeFocused();
  await inDialog(page, "7.3").click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "3.2").locator("input")).toHaveValue("https://youtu.be/e2ePrivate1");
  await expect(el(page, "3.3")).toBeFocused();
  await expect(el(page, "3.4")).toHaveCount(0); // 3.4는 형식 전용

  // 4시간 YouTube — 제목 · 길이를 가져온 뒤 시작 전에 멈춘다
  await analyze(page, "https://www.youtube.com/watch?v=e2eLong4h01");
  await expect(inDialog(page, "7.1")).toHaveText("3시간이 넘는 영상은 분석할 수 없어요");
  await expect(inDialog(page, "7.2")).toHaveText("길이 4:12:30");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);

  // 4시간 로컬 파일 — 같은 판
  await fileRow(page, "marathon_0901.mp4").click();
  await el(page, "4.6").click();
  await expect(inDialog(page, "7.1")).toHaveText("3시간이 넘는 영상은 분석할 수 없어요");
  await expect(inDialog(page, "7.2")).toHaveText("길이 4:12:30");
  await inDialog(page, "7.3").click();
  await expect(el(page, "4.6")).toBeFocused();
  await expect(fileRow(page, "marathon_0901.mp4")).toHaveAttribute("aria-pressed", "true");
});

test("형식 오류와 빈 칸 — 3.4에 받는 형태, 빈 칸은 서버에 묻지 않는다", async ({ page }) => {
  const posts: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST" && r.url().endsWith("/api/videos")) posts.push(r.url());
  });
  await page.goto("/");
  await el(page, "3.2").locator("input").fill("   ");
  await el(page, "3.3").click();
  await expect(el(page, "3.4")).toHaveText(URL_HINT);
  await expect(el(page, "3.2").locator("input")).toHaveAttribute("aria-invalid", "true");
  expect(posts).toHaveLength(0); // 누를 때의 키 확인도 가지 않는다

  // 형식이 틀린 주소 — 서버가 url-invalid로 돌려보낸다. 판은 열리지 않는다
  await el(page, "3.2").locator("input").fill("https://vimeo.com/76979871");
  await expect(el(page, "3.4")).toHaveCount(0); // 고치면 지운다
  const answered = page.waitForResponse(
    (r) => r.url().endsWith("/api/videos") && r.request().method() === "POST",
  );
  await el(page, "3.3").click();
  expect((await answered).status()).toBe(422);
  await expect(el(page, "3.4")).toHaveText(URL_HINT);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eOffline1");
  await expect(el(page, "3.4")).toHaveCount(0);
});

test("인터넷 끊김 — 누를 때 키 확인이 닿지 못하면 연결 문구 배너, 돌아온 뒤 누르면 UI-2", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await fakeOpenAI(request, { models: "drop" }); // 키 확인 요청만 끊는다
  await analyze(page, "https://youtu.be/e2eOffline1");
  await expect(el(page, "1.1")).toHaveText(OFFLINE);
  await expect(el(page, "1.2")).toHaveCount(0); // [키 넣으러 가기]가 없다
  await expect(el(page, "3.3")).not.toHaveAttribute("aria-disabled", "true"); // 막지 않는다
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "3.4")).toHaveCount(0);

  await fakeOpenAI(request, { models: null }); // 인터넷이 돌아왔다
  await el(page, "3.3").click(); // 서버가 다시 확인해 통과한다
  await expect(inDialog(page, "6.3")).toBeFocused();
  await expect(page.locator(".va-banner")).toHaveCount(0); // 배너가 사라진다
  await inDialog(page, "6.2").click();
});

test("누를 때 키 확인 실패 — 배너와 막힌 버튼, 다시 누르면 설정으로", async ({ page, request }) => {
  await page.goto("/");
  await fakeOpenAI(request, { models: 401 }); // 저장한 뒤 키가 폐기됐다
  await analyze(page, "https://youtu.be/e2eOffline1");
  await expect(el(page, "1.1")).toHaveText("키를 확인하지 못했어요 — 인증에 실패했습니다");
  await expect(el(page, "1.2")).toBeVisible();
  await expect(el(page, "3.3")).toHaveAttribute("aria-disabled", "true");
  await expect(el(page, "4.6")).toHaveAttribute("aria-disabled", "true");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "3.4")).toHaveCount(0);
  // 막힌 버튼 — 형식 검사 · 확인 없이 설정으로(aria-disabled라 키보드로 누른다)
  await el(page, "3.3").focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/settings$/);
});

test("서버에 닿지 못함 — 판에 '…을 확인하지 못했어요 — 서버에 연결할 수 없음'", async ({
  page,
}) => {
  // api가 꺼졌다 — 요청이 끊기거나(fetch 실패), web이 problem+json 아닌 평문 500으로 대신 답한다
  let plain = false;
  await page.route("**/api/videos", (route) => {
    if (route.request().method() !== "POST") return route.continue();
    if (!plain) return route.abort("connectionrefused");
    return route.fulfill({ status: 500, contentType: "text/plain", body: "Internal Server Error" });
  });
  await page.goto("/");
  await analyze(page, "https://youtu.be/e2eOffline1");
  await expect(inDialog(page, "7.1")).toHaveText(
    "영상 정보를 확인하지 못했어요 — 서버에 연결할 수 없음",
  );
  await expect(inDialog(page, "7.2")).toHaveCount(0);
  await inDialog(page, "7.3").click();
  await expect(el(page, "3.4")).toHaveCount(0);

  plain = true;
  // 목록을 받기 전에 누르면 고른 파일이 없어 요청이 나가지 않는다 — 맨 위 파일이 골라진 뒤에 누른다
  await expect(el(page, "4.3")).toHaveAttribute("aria-pressed", "true");
  await el(page, "4.6").click();
  await expect(inDialog(page, "7.1")).toHaveText(
    "파일을 확인하지 못했어요 — 서버에 연결할 수 없음",
  );
});

test("inbox에서 사라진 파일 — 판에 알리고, 목록을 다시 받아 맨 위 파일이 골라진다", async ({
  page,
}) => {
  // 목록 맨 아래(가장 오래된 파일)에 둔다 — 도중에 끝나도 기본으로 골라지는 파일이 바뀌지 않게
  const gone = path.join(INBOX, "gone_0830.mp4");
  writeFileSync(gone, JSON.stringify({ name: "gone_0830.mp4", duration: 1200, audio: true }));
  utimesSync(gone, new Date("2026-08-30T00:00:00Z"), new Date("2026-08-30T00:00:00Z"));
  try {
    await page.goto("/");
    await fileRow(page, "gone_0830.mp4").click();
    rmSync(gone); // 고른 뒤 inbox에서 지웠다
    await el(page, "4.6").click();
    await expect(inDialog(page, "7.1")).toHaveText(
      "파일을 찾지 못했어요 — inbox에서 옮겨졌거나 지워졌어요",
    );
    await expect(inDialog(page, "7.2")).toHaveCount(0);
    await inDialog(page, "7.3").click();
    await expect(fileRow(page, "gone_0830.mp4")).toHaveCount(0); // 다시 받은 목록
    await expect(el(page, "4.3")).toHaveAttribute("aria-pressed", "true"); // 맨 위 파일
  } finally {
    rmSync(gone, { force: true });
  }
});

test("주소로 바로 들어온다 — 도는 영상의 결과는 UI-3, 끝난 영상의 진행은 UI-4, 없는 영상은 UI-1", async ({
  page,
  request,
}) => {
  await fakeOpenAI(request, { chat_delay_ms: 2500 }); // 요약 단계에서 붙잡는다
  const id = await register(request, "https://youtu.be/e2eDirect01");
  expect((await request.post(`/api/videos/${id}/job`)).status()).toBe(201);
  await page.goto(`/videos/${id}`); // 아직 결과가 없다
  await expect(page).toHaveURL(new RegExp(`/videos/${id}/progress$`));
  await fakeOpenAI(request, { chat_delay_ms: 0 });
  await expect(page).toHaveURL(new RegExp(`/videos/${id}$`), { timeout: 30_000 }); // 끝나면 결과로

  await page.goto(`/videos/${id}/progress`); // 끝난 영상의 진행 주소
  await expect(page).toHaveURL(new RegExp(`/videos/${id}$`));
  await page.goto("/videos/999999");
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/videos/999999/progress");
  await expect(page).toHaveURL(/\/$/);
});

test("다른 창에서 먼저 시작했다 — 6.3을 누르면 실패가 아니라 그 작업의 UI-3으로", async ({
  page,
  request,
}) => {
  const url = "https://youtu.be/e2eJobExst1";
  await page.goto("/");
  await analyze(page, url);
  await expect(inDialog(page, "6.3")).toBeFocused();
  const id = await register(request, url); // 다른 창 — 같은 영상을 넣고 먼저 시작한다
  expect((await request.post(`/api/videos/${id}/job`)).status()).toBe(201);
  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(new RegExp(`/videos/${id}/progress$`));
});
