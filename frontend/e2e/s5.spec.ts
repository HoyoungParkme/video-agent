/**
 * S5 — 며칠 뒤 다시 열어 질문하고 노트로 옮기고 지운다(VA-SCN-001 S5, VA-CODE-001 B4 · D1 · D2).
 * 브라우저 시각을 7일 뒤로 두고 목록에서 연다 — 다시 분석하지 않는다(OpenAI 호출 없음). 내보낸 파일은
 * api의 데이터 폴더(e2e/.tmp/data/export)에서 읽어 GET 본문과 대 본다. 노트는 한눈에 보기 절(Mermaid 둘)을
 * 갖고, 파일 노트에만 스크립트 절과 장면 그림 줄이 있다 — 장면 그림은 노트 곁에 함께 쓴다.
 * 대기열에서 지우는 두 경우와 저장 실패 · 지우기 취소도 본다.
 */
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { DATA, el, fakeOpenAI, inAlert, inDialog, openResult, saveKey } from "./helpers";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
});

interface Preview {
  filename: string;
  path: string;
  markdown: string;
  files: { kind: string; name: string }[];
}

/** 장면 그림 파일 이름 — `{노트 이름} {MM-SS}.jpg`(1시간 이하 영상, 쌍점은 하이픈). */
function frameName(filename: string, sec: number): string {
  const two = (n: number) => String(Math.floor(n)).padStart(2, "0");
  return `${filename} ${two(sec / 60)}-${two(sec % 60)}.jpg`;
}

/** 고른 방법의 노트 — 파일이면 스크립트 절과 함께 쓸 파일 목록, 클립보드면 둘 다 없다. */
async function exported(
  request: APIRequestContext,
  id: number,
  withChat = false,
  method: "file" | "clipboard" = "file",
) {
  const res = await request.get(`/api/videos/${id}/export?with_chat=${withChat}&method=${method}`);
  return (await res.json()) as Preview;
}

/** 등록하고 분석을 시작한다 — 화면을 거치지 않는다. 영상 id */
async function startVideo(request: APIRequestContext, youtubeId: string): Promise<number> {
  const res = await request.post("/api/videos", {
    data: { source: "youtube", url: `https://youtu.be/${youtubeId}` },
  });
  const id = ((await res.json()) as { video: { id: number } }).video.id;
  expect((await request.post(`/api/videos/${id}/job`)).status()).toBe(201);
  return id;
}

const row = (page: Page, id: number) => page.locator(`[data-video="${id}"]`);
const idOf = (url: string) => Number(url.split("/").pop());

test("S5 — 며칠 뒤 목록에서 열어 묻고, 파일로 저장 · 복사하고, 지우면 처음부터", async ({
  page,
  request,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 });
  const id = idOf(await openResult(page, "https://youtu.be/e2eNoteVid1"));

  // 일주일 뒤 — 분석한 날이 '오늘'이 아니다. 다시 여는 데 OpenAI를 부르지 않는다
  await page.clock.setFixedTime(new Date(Date.now() + 7 * 86_400_000));
  const calls = (await fakeOpenAI(request)).chats;
  await page.goto("/");
  await expect(row(page, id).locator(".video-row-status")).toHaveText(/^\d+월 \d+일 분석$/);
  await row(page, id).locator(".video-row-link").click();
  await expect(page).toHaveURL(new RegExp(`/videos/${id}$`));
  await expect(el(page, "2.2")).toHaveText("벡터 DB 운영 노트");
  expect((await fakeOpenAI(request)).chats).toBe(calls); // 다시 분석하지 않는다

  // 새 질문
  await el(page, "7.2").click();
  await el(page, "10.3").locator("textarea").fill("청킹은 어떻게 바꿨어?");
  await el(page, "10.3").locator("textarea").press("Enter");
  await expect(page.locator(".turn")).toHaveCount(1);

  // 파일로 저장 — 서버가 data/export/에 쓰고, 짧은 알림 뒤 초점은 [내보내기]로
  const plain = await exported(request, id);
  await el(page, "1.2").click();
  await expect(inDialog(page, "2.1")).toHaveAttribute("aria-pressed", "true");
  await expect(inDialog(page, "2.1")).toBeFocused();
  await expect(inDialog(page, "2.1")).toContainText(plain.path);
  await expect(inDialog(page, "4.1")).toContainText("# 벡터 DB 운영 노트\n원본: [https://");
  // 한 줄 요약 다음에 한눈에 보기 — Mermaid 블록 둘(gantt · mindmap). 파일 노트는 끝에 스크립트 절
  await expect(inDialog(page, "4.1")).toContainText("## 한눈에 보기\n```mermaid\ngantt\n");
  await expect(inDialog(page, "4.1")).toContainText("```mermaid\nmindmap\n  root(");
  await expect(inDialog(page, "4.1")).toContainText(`## 스크립트\n[[${plain.filename} 스크립트]]`);
  // 함께 저장되는 파일(2.3) — 노트 · 스크립트 · 장면 칩과 그림 안내. 복사 안내(2.4)는 없다
  await expect(inDialog(page, "2.3").locator(".export-file")).toHaveText([
    "노트.md",
    "스크립트.md",
    "장면 5장.jpg",
  ]);
  await expect(inDialog(page, "2.3")).toContainText("그림은 노트 곁에 저장되고 노트가 가리켜요");
  await expect(inDialog(page, "2.4")).toHaveCount(0);
  const result = await (await request.get(`/api/videos/${id}/result`)).json();
  const frames = (result.chapters as { start_sec: number }[]).map((c) =>
    frameName(plain.filename, c.start_sec),
  );
  expect(frames).toHaveLength(5);
  expect(plain.files).toEqual([
    { kind: "note", name: `${plain.filename}.md` },
    { kind: "script", name: `${plain.filename} 스크립트.md` },
    ...frames.map((name) => ({ kind: "frame", name })),
  ]);
  // 챕터 제목 줄 바로 다음에 장면 그림 줄
  expect(plain.markdown).toContain(`![[${frames[0]}]]`);
  await expect(inDialog(page, "3")).toHaveText("질문 기록 1개도 넣기");
  await inDialog(page, "5.3").click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "11")).toHaveText(
    `${plain.path}에 저장했어요 · 스크립트는 따로 · 그림 5장`,
  );
  await expect(el(page, "1.2")).toBeFocused();
  // 노트는 파일 미리 보기 그대로다 — 스크립트는 따로(UI-7 규칙)
  const file = path.join(DATA, "export", `${plain.filename}.md`);
  expect(readFileSync(file, "utf-8")).toBe(plain.markdown);
  const script = path.join(DATA, "export", `${plain.filename} 스크립트.md`);
  expect(readFileSync(script, "utf-8")).toMatch(/^# 벡터 DB 운영 노트 — 스크립트\n원본: \[https:/);
  for (const name of frames) {
    expect(readFileSync(path.join(DATA, "export", name)).subarray(0, 2)).toEqual(
      Buffer.from([0xff, 0xd8]), // JPEG
    );
  }

  // 클립보드에 복사 — 질문 기록을 넣으면 맨 끝에 붙은 마크다운 전체
  await el(page, "1.2").click();
  await expect(inDialog(page, "2.1")).toHaveAttribute("aria-pressed", "true"); // 열 때마다 파일부터
  await inDialog(page, "2.2").click();
  await expect(inDialog(page, "2.2")).toHaveAttribute("aria-pressed", "true");
  await expect(inDialog(page, "5.3")).toHaveText("복사하기");
  // 2.3 자리에 복사 안내(2.4). 미리 보기가 클립보드 노트로 바뀐다 — 한눈에 보기는 있고 스크립트 절은 없다
  await expect(inDialog(page, "2.4")).toHaveAttribute("role", "note");
  await expect(inDialog(page, "2.3")).toHaveCount(0);
  await expect(inDialog(page, "4.1")).toContainText("```mermaid\ngantt\n"); // 새 노트가 온 뒤에
  await expect(inDialog(page, "4.1")).not.toContainText("## 스크립트");
  await expect(inDialog(page, "4.1")).toHaveAttribute("tabindex", "0"); // 키보드로도 스크롤
  await expect(inDialog(page, "4.1")).toHaveAccessibleName("미리 보기");
  await inDialog(page, "3").click();
  const chat = await exported(request, id, true, "clipboard");
  expect(chat.markdown).toContain("## 질문 기록\n**Q.** 청킹은 어떻게 바꿨어?\n**A.** ");
  expect(chat.markdown).not.toContain("## 스크립트");
  expect(chat.markdown).not.toContain("![["); // 복사에는 그림 줄이 없다
  expect(chat.files).toEqual([]);
  await expect(inDialog(page, "5.3")).not.toHaveAttribute("aria-disabled", "true"); // 받은 뒤
  await inDialog(page, "5.3").click();
  await expect(el(page, "11")).toHaveText("클립보드에 복사했어요");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(chat.markdown);

  // 지운다 — UI-4 휴지통 → UI-1, 그 행이 없고 초점은 「분석한 영상」 제목
  await el(page, "1.3").click();
  await expect(inAlert(page, "1.3")).toHaveText("벡터 DB 운영 노트");
  await expect(inAlert(page, "2.1")).toContainText("질문 기록 1개");
  // 장면이 있다 — 열 때 받아 챕터 뒤에(인포그래픽은 만들지 않았다, 이슈 #18)
  await expect(inAlert(page, "2.1")).toContainText("챕터, 대표 장면, 추천 질문");
  await expect(inAlert(page, "2.1")).not.toContainText("임시 음성 파일"); // 끝난 영상
  await expect(inAlert(page, "2.2")).toContainText(
    "YouTube 원본 영상. 다시 넣으면 처음부터 분석합니다.",
  );
  await expect(inAlert(page, "3.2")).toBeFocused();
  await inAlert(page, "3.3").click();
  await expect(page).toHaveURL(/\/$/);
  await expect(el(page, "5.1")).toBeFocused();
  await expect(row(page, id)).toHaveCount(0);
  await page.goBack(); // 방문 기록을 바꿔치기했다 — 지운 영상으로 돌아가지 않는다
  await expect(page).not.toHaveURL(new RegExp(`/videos/${id}$`));

  // 같은 주소를 다시 넣으면 처음부터 — 사전 안내가 뜬다
  await page.goto("/");
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eNoteVid1");
  await el(page, "3.3").click();
  await expect(inDialog(page, "6.3")).toHaveText("분석 시작");
});

test("대기열에서 지운다 — 기다리던 영상은 차례가 당겨지고, 도는 영상은 멈춘다", async ({
  page,
  request,
}) => {
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 2500 }); // 요약 단계에서 붙잡는다
  const running = await startVideo(request, "e2eDelRun01");
  const waiting = await startVideo(request, "e2eDelWait1");
  const last = await startVideo(request, "e2eDelWait2");
  const tmp = path.join(DATA, "tmp", String(running));
  await expect.poll(() => existsSync(tmp)).toBe(true); // 도는 영상의 임시 폴더

  await page.goto("/");
  await expect(row(page, last).locator(".video-row-status")).toHaveText("대기 중 · 2번째");

  // 기다리던 영상 — 대기열에서 빠지고 뒤 영상의 차례가 당겨진다. 목록은 작업 시작 최근 순이라
  // [last, waiting, running] — 초점은 바로 아래 행(running)으로
  await row(page, waiting).getByRole("button").click();
  await expect(inAlert(page, "2.1")).toContainText("임시 음성 파일"); // 끝나지 않은 영상
  await inAlert(page, "3.3").click();
  await expect(row(page, waiting)).toHaveCount(0);
  await expect(row(page, running).locator(".video-row-link")).toBeFocused();
  await expect(row(page, last).locator(".video-row-status")).toHaveText("대기 중 · 1번째");

  // 도는 영상 — 작업을 멈추고 지운다. 임시 폴더가 없고, 기다리던 영상이 돌기 시작한다
  await row(page, running).getByRole("button").click();
  await inAlert(page, "3.3").click();
  await expect(row(page, running)).toHaveCount(0);
  expect(existsSync(tmp)).toBe(false);
  await expect(row(page, last).locator(".video-row-status")).toHaveText(/ 중$/, {
    timeout: 10_000,
  });
  await fakeOpenAI(request, { chat_delay_ms: 0 }); // 남은 영상이 곧 끝나게
});

test("저장 실패 — 실패 한 줄을 보이고 열린 채, 치우고 다시 누르면 저장된다", async ({
  page,
  request,
}) => {
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 });
  const id = idOf(await openResult(page, "https://youtu.be/e2eNoteVid1"));
  const folder = path.join(DATA, "export");
  rmSync(folder, { recursive: true, force: true });
  mkdirSync(DATA, { recursive: true });
  writeFileSync(folder, ""); // 저장 폴더 자리에 파일
  try {
    await el(page, "1.2").click();
    await inDialog(page, "5.3").click();
    await expect(inDialog(page, "5.1")).toHaveText(
      "파일을 저장하지 못했어요 — 저장 폴더를 만들 수 없음(그 자리에 파일이 있다)",
    );
    await expect(page.getByRole("dialog")).toHaveCount(1); // 닫히지 않는다
  } finally {
    rmSync(folder, { force: true });
  }
  await inDialog(page, "5.3").click(); // 다시 누르면 다시 시도 — 5.1이 사라진다
  const plain = await exported(request, id);
  await expect(el(page, "11")).toHaveText(
    `${plain.path}에 저장했어요 · 스크립트는 따로 · 그림 5장`,
  );
  expect(readFileSync(path.join(folder, `${plain.filename}.md`), "utf-8")).toBe(plain.markdown);
  expect(existsSync(path.join(folder, `${plain.filename} 스크립트.md`))).toBe(true);
});

test("지우지 않고 닫는다 — 덮개는 닫지 않고, Esc · 취소는 아무것도 지우지 않는다", async ({
  page,
  request,
}) => {
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0 });
  const id = idOf(await openResult(page, "https://youtu.be/e2eNoteVid1"));
  await page.goto("/");
  const trash = row(page, id).getByRole("button");
  await expect(trash).toHaveAttribute("aria-label", "벡터 DB 운영 노트 분석 결과 삭제");
  await trash.click();
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await page.mouse.click(8, 8); // 덮개
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("alertdialog")).toHaveCount(0);
  await expect(trash).toBeFocused(); // 연 휴지통으로
  await trash.click();
  await inAlert(page, "3.2").click();
  await expect(page.getByRole("alertdialog")).toHaveCount(0);
  await expect(row(page, id)).toHaveCount(1); // 그대로
});
