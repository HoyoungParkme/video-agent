/**
 * 로컬 파일 끌어 놓기 · 고르기(VA-UC-001 UC-H2, VA-UI-002 UI-1 4.7 ~ 4.19 · 8 · UI-2 6.4 · UI-6, VA-CODE-001
 * D4) — [파일 고르기] · 끌어 놓기로 올리면 진행 → 파일 확인 → UI-2 올린 파일 판이 열리고, 분석이 끝나면
 * 사본을 지운다. 올린 파일 판에서 취소해도 지운다. 여러 파일 · 받지 않는 형식은 보내지 않고, 멈추면 받던
 * 것을 지운다. 올리는 동안 떠나려 하면 먼저 묻는다(새로 고침 · 앱 안 링크, CODE-001 E2). 키 확인이
 * 실패하면 본문 전에 거절한다. 실패한 올린 영상은 사본이 남아 다시 시도가 읽는다.
 * 파일은 가짜 ffprobe가 읽는 길이 · 음성 JSON이다(e2e/fake-ffmpeg.mjs) — pad로 크기를 키운다.
 * 서버 재시작의 청소는 pytest(tests/test_main.py)가 본다.
 */
import { readdirSync } from "node:fs";
import http from "node:http";
import path from "node:path";

import { expect, test, type JSHandle, type Page } from "@playwright/test";

import { DATA, el, fakeOpenAI, inAlert, inDialog, saveKey } from "./helpers";

const UPLOADS = path.join(DATA, "uploads");

test.beforeEach(async ({ request }) => {
  await fakeOpenAI(request, { reset: true }); // 키 확인을 막은 앞 테스트가 있어도 키를 넣을 수 있게 먼저
  await saveKey(request);
});

/** 올린 사본 폴더의 파일 — 사본({해시}.mp4) · 받던 것(.part-*) */
function uploads(): string[] {
  try {
    return readdirSync(UPLOADS).sort();
  } catch {
    return []; // 아직 한 번도 올리지 않았다
  }
}

/** 가짜 미디어 — 길이 · 음성을 담은 JSON. 이름을 넣어 내용(해시)을 서로 다르게, pad로 크기를 키운다 */
function content(name: string, duration = 1500, pad = 0): string {
  return JSON.stringify({ name, duration, audio: true, pad: "x".repeat(pad) });
}

function media(name: string, duration = 1500, pad = 0) {
  return { name, mimeType: "video/mp4", buffer: Buffer.from(content(name, duration, pad)) };
}

/** [파일 고르기](4.10)로 브라우저의 파일 고르기 창을 열어 고른다 */
async function pick(page: Page, file: ReturnType<typeof media>): Promise<void> {
  const chooser = page.waitForEvent("filechooser");
  await el(page, "4.10").click();
  await (await chooser).setFiles(file);
}

/** 파일 탐색기에서 끌고 온 것 — 페이지 안의 DataTransfer */
function dragged(page: Page, files: { name: string; content: string }[]): Promise<JSHandle> {
  return page.evaluateHandle((list) => {
    const dt = new DataTransfer();
    for (const f of list) dt.items.add(new File([f.content], f.name, { type: "video/mp4" }));
    return dt;
  }, files);
}

/** /api/uploads로 나간 요청 수를 센다 */
function countUploads(page: Page): { n: number } {
  const count = { n: 0 };
  page.on("request", (r) => {
    if (r.url().endsWith("/api/uploads")) count.n += 1;
  });
  return count;
}

test("파일을 골라 올린다 — 올린 파일 판 → 분석 → 끝나면 사본을 지운다, 목록 부제 '올린 파일'", async ({
  page,
}) => {
  await page.goto("/");
  await expect(el(page, "4.8")).toHaveText("파일을 여기로 끌어 놓으세요");
  await expect(el(page, "4.9")).toHaveText(
    "영상 mp4 · mkv · mov · webm, 음성 mp3 · m4a · wav · 한 번에 한 파일 · 3시간까지",
  );
  await expect(el(page, "4.19")).toContainText("또는 inbox 폴더에서 고르기");
  await expect(el(page, "4.19")).toContainText("~/video-agent/inbox");
  await pick(page, media("meetup_upload.mp4"));

  // UI-2 올린 파일 판 — 출처 줄과 사본 안내. 사본은 해시 이름으로 하나
  await expect(inDialog(page, "2.3")).toHaveText("로컬 파일 · 올린 사본");
  await expect(inDialog(page, "2.2")).toHaveText("meetup_upload.mp4");
  await expect(inDialog(page, "6.4")).toHaveText(
    "취소하면 올린 사본을 지워요. 원본 파일은 그대로예요.",
  );
  expect(uploads()).toEqual([expect.stringMatching(/^[0-9a-f]{64}\.mp4$/)]);
  await expect(el(page, "4.7")).toBeVisible(); // 4.11은 4.7로 돌아왔다

  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 30_000 }); // 끝나면 결과로
  await expect.poll(uploads).toEqual([]); // done 뒤 사본을 지운다
  // 올린 파일은 재생하지 않는다 — 플레이어 자리에 까닭 한 줄(UI-4 16.10, 카드 E7)
  await expect(el(page, "16.10")).toHaveText(
    "올린 파일은 분석이 끝나면 지워서 여기서 재생할 수 없어요",
  );
  await expect(el(page, "16.1")).toHaveCount(0);

  await page.goto("/");
  const row = page.locator(".video-row", { hasText: "meetup_upload.mp4" });
  await expect(row.locator(".video-row-sub")).toHaveText("올린 파일");
});

test("끌어 놓아 올린다 — 덮개 → 놓으면 올리고, 올린 파일 판에서 취소하면 사본을 지웠다는 알림", async ({
  page,
}) => {
  await page.goto("/");
  // 10MB를 넘는다 — proxy가 도는 경로라면 Next가 본문을 10MB에서 잘라 올리지 못한다(INFRA C4)
  const dt = await dragged(page, [
    { name: "drop_12mb.mp4", content: content("drop_12mb.mp4", 1500, 12 << 20) },
  ]);
  await page.dispatchEvent("main", "dragenter", { dataTransfer: dt });
  await expect(el(page, "8")).toBeVisible();
  await expect(el(page, "8.2")).toHaveText("놓으면 이 파일을 올려 분석해요");
  await expect(el(page, "8.3")).toHaveText(
    "한 번에 한 파일 · 영상 mp4 · mkv · mov · webm, 음성 mp3 · m4a · wav",
  );
  await expect(el(page, "8.4")).toHaveText(
    "파일은 이 PC 안의 앱 폴더로 복사될 뿐 밖으로 나가지 않아요",
  );
  await expect(el(page, "4.7")).toHaveClass(/is-over/);
  await page.dispatchEvent("main", "drop", { dataTransfer: dt });
  await expect(el(page, "8")).toHaveCount(0);

  await expect(inDialog(page, "2.3")).toHaveText("로컬 파일 · 올린 사본");
  expect(uploads()).toHaveLength(1);
  await inDialog(page, "6.2").click(); // 취소 — 서버가 사본을 지운다
  await expect(el(page, "4.17")).toHaveText("분석을 취소했어요 — 올린 사본을 지웠어요");
  await expect(el(page, "4.17")).toHaveAttribute("role", "status");
  expect(uploads()).toEqual([]);
  // 다음에 파일을 놓거나 고르면 한 줄은 사라진다
  const two = await dragged(page, [
    { name: "a.mp4", content: "{}" },
    { name: "b.mp4", content: "{}" },
  ]);
  await page.dispatchEvent("main", "drop", { dataTransfer: two });
  await expect(el(page, "4.17")).toHaveText("한 번에 한 파일씩 올려 주세요 — 파일 2개를 놓았어요");
});

test("다른 창에서 분석을 시작한 올린 영상 — 이 창에서 취소해도 지우지 않는다", async ({
  page,
  context,
}) => {
  const file = media("two_tabs.mp4");
  await page.goto("/");
  await pick(page, file);
  await expect(inDialog(page, "2.3")).toHaveText("로컬 파일 · 올린 사본");
  // 다른 창에서 같은 파일을 올려(같은 영상) 분석을 시작한다
  const other = await context.newPage();
  await other.goto("/");
  await pick(other, file);
  await inDialog(other, "6.3").click();
  await expect(other).toHaveURL(/\/videos\/\d+\/progress$/);
  // 이 창의 올린 파일 판을 닫는다 — 그 사이 작업이 생겨 지우지 않고 알림 없이 닫힌다
  await inDialog(page, "6.2").click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "4.17")).toHaveCount(0);
  await expect(other).toHaveURL(/\/videos\/\d+$/, { timeout: 30_000 }); // 분석은 끝까지 간다
});

test("여러 파일 · 받지 않는 형식은 보내지 않고 한 줄", async ({ page }) => {
  const sent = countUploads(page);
  await page.goto("/");
  const three = await dragged(page, [
    { name: "a.mp4", content: "{}" },
    { name: "b.mp4", content: "{}" },
    { name: "c.mp4", content: "{}" },
  ]);
  await page.dispatchEvent("main", "drop", { dataTransfer: three });
  await expect(el(page, "4.17")).toHaveText("한 번에 한 파일씩 올려 주세요 — 파일 3개를 놓았어요");
  await expect(el(page, "4.17")).toHaveAttribute("role", "alert");
  await pick(page, {
    name: "발표자료.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF"),
  });
  await expect(el(page, "4.17")).toHaveText(
    "mp4 · mkv · mov · webm · mp3 · m4a · wav 파일만 받아요 — 발표자료.pdf는 올리지 않았어요",
  );
  expect(sent.n).toBe(0); // 아무것도 보내지 않았다
});

test("올리다 끊기면 — 한 줄과 다시 올리기, 다시 올리면 같은 파일을 처음부터", async ({ page }) => {
  await page.goto("/");
  await page.route("**/api/uploads", (route) => route.abort(), { times: 1 });
  await pick(page, media("cut_upload.mp4"));
  await expect(el(page, "4.17").locator(".upload-line-text")).toHaveText(
    "올리지 못했어요 — 서버에 연결할 수 없음. 올라간 부분은 지웠어요",
  );
  await expect(el(page, "4.18")).toHaveText("다시 올리기");
  await el(page, "4.18").click();
  await expect(inDialog(page, "2.2")).toHaveText("cut_upload.mp4");
  await inDialog(page, "6.2").click();
  await expect(el(page, "4.17")).toHaveText("분석을 취소했어요 — 올린 사본을 지웠어요");
});

test("올리는 동안 진행과 멈추기 — 멈추면 알림, 받던 것은 지웠다", async ({ page }) => {
  await page.goto("/");
  // 올리기를 느리게 — 1초에 2MB. 진행을 보고 멈출 틈을 둔다
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 0,
    downloadThroughput: -1,
    uploadThroughput: 2 << 20,
  });
  await pick(page, media("stop_upload.mp4", 1500, 20 << 20));
  await expect(el(page, "4.11")).toBeVisible();
  await expect(el(page, "4.12")).toHaveText("stop_upload.mp4");
  await expect(el(page, "4.13")).toHaveText(/^올리는 중 · \d+ MB \/ 21 MB$/);
  await expect(el(page, "4.14")).toHaveText(/^\d+%$/);
  await expect(el(page, "4.16")).toHaveText("멈추기");
  await expect.poll(uploads).toEqual([expect.stringMatching(/^\.part-/)]); // 서버가 받기 시작했다
  await el(page, "4.16").click();
  await expect(el(page, "4.17")).toHaveText("올리기를 멈췄어요 — 올라간 부분은 지웠어요");
  await expect(el(page, "4.7")).toBeVisible();
  await expect.poll(uploads).toEqual([]); // api도 끊긴 것을 알고 받던 것을 지웠다
});

test("올리는 동안 떠나려 하면 묻는다 — 새로 고침은 브라우저 창, 앱 안 링크는 확인 창(UI-1 규칙)", async ({
  page,
}) => {
  await page.goto("/");
  const dialogs: string[] = [];
  // 올리지 않을 때는 묻지 않는다 — 설정에 갔다 온다
  page.on("dialog", (d) => dialogs.push(`${d.type()}:${d.message()}`));
  await page.getByRole("link", { name: "설정" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  expect(dialogs).toEqual([]);
  page.removeAllListeners("dialog");

  // 올리기를 느리게 — 1초에 2MB. 묻는 동안 끝나지 않게
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 0,
    downloadThroughput: -1,
    uploadThroughput: 2 << 20,
  });
  await pick(page, media("leave_upload.mp4", 1500, 20 << 20));
  await expect(el(page, "4.11")).toBeVisible();
  await expect.poll(uploads).toEqual([expect.stringMatching(/^\.part-/)]);

  // 새로 고침 — 브라우저의 떠나기 확인. 머무르면 그대로 올린다
  page.once("dialog", (d) => {
    dialogs.push(d.type());
    void d.dismiss();
  });
  await page.reload({ timeout: 3000 }).catch(() => undefined);
  expect(dialogs).toEqual(["beforeunload"]);
  await expect(el(page, "4.11")).toBeVisible();

  // 지금 화면과 같은 주소(로고 → '/')는 떠나지 않아 묻지 않는다. 목록 행(6.1)은 묻는다 — 앞 테스트가
  // 남긴 행이 있으면
  const asked: string[] = [];
  page.on("dialog", (d) => {
    asked.push(d.type());
    void d.dismiss();
  });
  await page.getByRole("link", { name: "Video Agent" }).click();
  await expect(el(page, "4.11")).toBeVisible();
  const rows = await el(page, "6.1").count();
  if (rows) {
    await el(page, "6.1").click();
    await expect(el(page, "4.11")).toBeVisible();
    await expect(page).toHaveURL(/\/$/);
  }
  page.removeAllListeners("dialog");
  expect(asked).toEqual(rows ? ["confirm"] : []);

  // 앱 안 링크 — 확인 창. 취소면 이 화면에서 그대로 올린다
  page.once("dialog", (d) => {
    dialogs.push(`${d.type()}:${d.message()}`);
    void d.dismiss();
  });
  await page.getByRole("link", { name: "설정" }).click();
  await expect(el(page, "4.11")).toBeVisible();
  await expect(page).toHaveURL(/\/$/);
  expect(dialogs[1]).toBe("confirm:올리기를 멈추고 이동할까요? 올라간 부분은 지워져요.");

  // 확인하면 멈추고 그 화면으로 간다 — 받던 것은 지웠다
  page.once("dialog", (d) => void d.accept());
  await page.getByRole("link", { name: "설정" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await expect.poll(uploads).toEqual([]);
});

test("키 확인이 실패하면 — 본문 전에 거절, 배너와 막힌 칸. 막힌 칸은 놓아도 올리지 않고 고르기는 설정으로", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await fakeOpenAI(request, { models: 401 }); // 올릴 때 다시 확인하면 거절된다
  try {
    // 30MB — 서버가 본문을 받기 전에 거절한 응답이 브라우저에 닿는가(SEQ-001 3장 미결)
    await pick(page, media("no_key.mp4", 1500, 30 << 20));
    await expect(page.locator(".va-banner")).toBeVisible();
    await expect(el(page, "4.7")).toHaveClass(/is-blocked/);
    await expect(el(page, "4.8")).toHaveText("OpenAI API 키를 넣은 뒤 올릴 수 있어요");
    await expect(el(page, "4.10")).toHaveAttribute("aria-disabled", "true");
    expect(uploads()).toEqual([]); // 본문을 받지 않았다

    const sent = countUploads(page);
    const dt = await dragged(page, [{ name: "later.mp4", content: content("later.mp4") }]);
    await page.dispatchEvent("main", "dragenter", { dataTransfer: dt });
    await expect(el(page, "8")).toHaveCount(0); // 덮개도 띄우지 않는다
    await page.dispatchEvent("main", "drop", { dataTransfer: dt });
    expect(sent.n).toBe(0);
    // 막힌 [파일 고르기]는 초점을 받고, 누르면 설정으로(aria-disabled라 키보드로 누른다)
    await el(page, "4.10").focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/settings$/);
  } finally {
    await fakeOpenAI(request, { models: null });
    await saveKey(request); // 뒤 테스트가 맞는 키로 시작하게
  }
});

test("받아쓰기가 실패한 올린 영상 — 사본이 남아 삭제 창이 크기를 보이고, 다시 시도가 읽고 끝나면 지운다", async ({
  page,
  request,
}) => {
  await fakeOpenAI(request, { stt_fail: { seq: 2, times: 9 } }); // 토막 세 번 × 조각 세 번
  await page.goto("/");
  await pick(page, media("fail_upload.mp4")); // 25분 — 조각 셋
  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  await expect(el(page, "5")).toBeVisible({ timeout: 20_000 }); // 실패 알림
  expect(uploads()).toHaveLength(1); // 실패 — 사본이 남는다(다시 시도가 읽는다)
  const failedUrl = page.url();

  // UI-6 — 남아 있는 사본의 크기와 PC에 있는 원본
  await page.goto("/");
  const row = page.locator(".video-row", { hasText: "fail_upload.mp4" });
  await row.locator(".video-row-trash").click();
  await expect(inAlert(page, "2.1")).toContainText(/올린 사본\(\d+ KB\)$/);
  await expect(inAlert(page, "2.2")).toContainText(
    "PC에 있는 원본 파일. 다시 넣으면 처음부터 분석합니다.",
  );
  await inAlert(page, "3.2").click(); // 지우지 않는다

  await page.goto(failedUrl);
  await el(page, "5.4").click(); // 다시 시도 — 사본에서 이어 간다
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 30_000 });
  await expect.poll(uploads).toEqual([]);
});

/** Host 헤더를 마음대로 정해 올리기 — 브라우저는 Host를 바꿀 수 없어 Node로 보낸다 */
function uploadWithHost(url: string, host: string): Promise<number> {
  return new Promise((resolve, reject) => {
    const body = content("host.mp4");
    const req = http.request(
      url,
      {
        method: "POST",
        headers: {
          Host: host,
          "Content-Type": "application/octet-stream",
          "Content-Length": Buffer.byteLength(body),
          "X-File-Name": "host.mp4",
        },
      },
      (res) => {
        res.resume();
        resolve(res.statusCode ?? 0);
      },
    );
    req.on("error", reject);
    req.end(body);
  });
}

test("다른 Host로 온 올리기는 막는다 — proxy에서 빠진 경로도 같은 판정(INFRA 5절)", async ({
  baseURL,
}) => {
  const url = `${baseURL}/api/uploads`;
  const port = new URL(url).port;
  const before = uploads();
  expect(await uploadWithHost(url, `evil.example:${port}`)).toBe(400);
  expect(uploads()).toEqual(before); // api에 닿지 않았다
  // 그 아래 경로는 proxy가 본다 — API 라우트가 받지 않는 경로가 Host 확인 없이 api로 가지 않게
  expect(await uploadWithHost(`${url}/x`, `evil.example:${port}`)).toBe(400);
});
