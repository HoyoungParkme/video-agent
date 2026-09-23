/**
 * S2 — inbox의 2시간 30분 워크숍 파일을 받아쓰기로 분석한다(VA-SCN-001 S2, VA-CODE-001 B2).
 * 받아쓰기 필요 판(15조각 · 3개씩 동시) → 조각 격자가 차오른다 → 1시간 넘는 영상이라 챕터가 파트로 묶인다.
 * 로컬 음성 판(취소하면 아무것도 보내지 않는다 — S6 변형) · 시작할 수 없는 파일(음성 트랙 없음 · 영상 아님)도 본다.
 * inbox 파일은 길이를 담은 JSON이다 — 가짜 ffmpeg가 만들고 잰다(e2e/fake-ffmpeg.mjs).
 */
import { expect, test } from "@playwright/test";

import { el, fakeOpenAI, inDialog, saveKey } from "./helpers";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
});

const fileRow = (page: import("@playwright/test").Page, name: string) =>
  page.locator(".file-row", { hasText: name });

test("inbox 워크숍 — 받아쓰기 필요 판부터 파트로 묶인 챕터까지", async ({ page, request }) => {
  // 격자가 차오르는 것이 보일 만큼 받아쓰기를 늦춘다
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0, stt_delay_ms: 1000, stt_fail: null });

  await page.goto("/");
  // 「내 파일」 — 최근에 고친 파일이 위, 처음에는 맨 위 파일이 골라져 있다
  await expect(page.locator(".file-name")).toHaveText([
    "workshop_0912.mp4",
    "lecture_0920.mp4",
    "call_0915.m4a",
    "memo_0917.wav",
    "silent_demo.mp4",
    "notes.mp4",
  ]);
  await expect(el(page, "4.3")).toHaveAttribute("aria-pressed", "true");
  await expect(el(page, "4.3").locator(".file-length")).toHaveText("2:30:00");
  await el(page, "4.6").click();

  // UI-2 받아쓰기 필요 판(로컬 영상) — 숫자는 서버 값 그대로
  await expect(inDialog(page, "2.2")).toHaveText("workshop_0912.mp4");
  await expect(inDialog(page, "2.3")).toHaveText("로컬 파일 · inbox");
  await expect(inDialog(page, "2.4")).toHaveText("길이 2:30:00");
  await expect(inDialog(page, "2.5")).toHaveText("자막 없음 · 받아쓰기 필요");
  await expect(inDialog(page, "3.1")).toHaveText("약 8분");
  await expect(inDialog(page, "3.2")).toHaveText(
    "음성을 뽑아 15개 조각으로 나누고, 3개씩 동시에 받아씁니다.",
  );
  await expect(inDialog(page, "4.2")).toHaveText("받아쓰기 150분 × $0.006$0.90");
  await expect(inDialog(page, "5")).toHaveText(
    "받아쓰기에는 음성 조각이, 요약에는 스크립트 텍스트가 OpenAI로 전송됩니다. 영상 파일 자체는 이 PC 밖으로 나가지 않아요.",
  );
  await inDialog(page, "6.3").click();

  // UI-3 — 단계 다섯(음성 추출 → 받아쓰기 → 핵심 요약 → 챕터 → 추천 질문)
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  await expect(el(page, "2.3")).toHaveText("로컬 파일 · 2:30:00 · 자막 없음");
  await expect(page.locator(".step-name")).toHaveText([
    "음성 추출",
    "받아쓰기",
    "핵심 요약",
    "챕터",
    "추천 질문",
  ]);

  // 받아쓰기 — 15칸 격자가 차오르고, 3개씩 동시에 보낸다
  await expect(el(page, "3.1")).toHaveText("받아쓰기 중", { timeout: 15_000 });
  await expect(el(page, "4.6").locator(".chunk-cell")).toHaveCount(15);
  await expect(el(page, "4.6")).toHaveAttribute(
    "aria-label",
    /^조각 15개 중 ([1-9]|1[0-4])개 완료, 3개 받아쓰는 중$/,
  );
  await expect(el(page, "3.2")).toHaveText(/^조각 ([1-9]|1[0-4]) \/ 15/);
  await expect(el(page, "4.8")).toContainText("받아쓰는 중 3");
  await expect(el(page, "6.1")).toHaveText("음성 조각 → OpenAI whisper-1 · 동시 3개");

  // 끝나면 UI-4 — 1시간 넘는 영상이라 챕터가 파트 둘로 묶이고 첫 파트만 펼쳐진다
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 30_000 });
  await expect(el(page, "2.1")).toHaveText("로컬 파일2:30:00받아쓰기 · 한국어");
  await expect(el(page, "2.3")).toHaveText(
    /^로컬 파일 · 오늘 \d\d:\d\d 분석 · 받아쓰기 whisper-1$/,
  );
  await expect(el(page, "2.4")).toHaveCount(0); // 원본 링크는 YouTube만
  await expect(el(page, "8.1")).toHaveText("받아쓰기 whisper-1 · 한국어");
  await expect(el(page, "6.1")).toHaveText("6개 · 파트 2개");
  const parts = page.locator(".part-head");
  await expect(el(page, "6.5")).toHaveAttribute("aria-expanded", "true");
  await expect(el(page, "6.5")).toContainText("오전 세션 — 현황과 문제");
  await expect(el(page, "6.5")).toContainText("챕터 3개");
  await expect(el(page, "6.5")).toContainText("0:00:00 – 1:15:00");
  await expect(parts.nth(1)).toHaveAttribute("aria-expanded", "false");
  await expect(parts.nth(1)).toContainText("1:15:00 – 2:30:00");
  await expect(page.locator(".chapter")).toHaveCount(3); // 접힌 파트의 챕터는 그리지 않는다
  await expect(el(page, "6.6")).toContainText("워크숍 소개");

  // 둘째 파트를 펴고 그 챕터를 누르면 스크립트가 그 시각으로 — 시각은 h:mm:ss
  await parts.nth(1).click();
  await expect(parts.nth(1)).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator(".chapter")).toHaveCount(6);
  await page.locator(".chapter", { hasText: "실습 준비" }).click();
  await expect(el(page, "8.2")).toHaveText("1:15:00");
  await expect(page.locator('.segment[aria-pressed="true"]')).toHaveCount(1);
  // 첫 파트를 접어도 둘째는 그대로 — 파트마다 따로 편다
  await el(page, "6.5").click();
  await expect(el(page, "6.5")).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".chapter")).toHaveCount(3);

  const fake = await fakeOpenAI(request, { stt_delay_ms: 0 });
  expect([...fake.transcribed].sort((a, b) => a - b)).toEqual(
    Array.from({ length: 15 }, (_, i) => i + 1),
  ); // 조각마다 한 번씩
  expect(fake.chats).toBe(3); // 스크립트가 상한 안이라 구간 없이 요약 · 챕터 · 추천 질문
});

test("inbox 음성 파일 — 받아쓰기 필요 판의 음성 문구, 취소하면 아무것도 보내지 않는다", async ({
  page,
  request,
}) => {
  const sent = await fakeOpenAI(request, { reset: true });
  await page.goto("/");
  await fileRow(page, "memo_0917.wav").click();
  await expect(fileRow(page, "memo_0917.wav")).toHaveAttribute("aria-pressed", "true");
  await expect(el(page, "4.3")).toHaveAttribute("aria-pressed", "false"); // 하나만 골라진다
  await el(page, "4.6").click();

  // 음성은 뽑을 것이 없다 — 3.2에 '음성을 뽑아'가 없고, 5는 음성 파일
  await expect(inDialog(page, "2.2")).toHaveText("memo_0917.wav");
  await expect(inDialog(page, "2.3")).toHaveText("로컬 파일 · inbox");
  await expect(inDialog(page, "2.4")).toHaveText("길이 25:00");
  await expect(inDialog(page, "2.5")).toHaveText("자막 없음 · 받아쓰기 필요");
  await expect(inDialog(page, "3.2")).toHaveText("3개 조각으로 나누고, 3개씩 동시에 받아씁니다.");
  await expect(inDialog(page, "4.2")).toHaveText("받아쓰기 25분 × $0.006$0.15");
  await expect(inDialog(page, "5")).toHaveText(
    "받아쓰기에는 음성 조각이, 요약에는 스크립트 텍스트가 OpenAI로 전송됩니다. 음성 파일 자체는 이 PC 밖으로 나가지 않아요.",
  );
  await inDialog(page, "6.2").click(); // 취소 — 작업은 만들지 않는다
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "4.6")).toBeFocused();
  const after = await fakeOpenAI(request);
  expect([after.transcriptions, after.chats]).toEqual([sent.transcriptions, sent.chats]); // S6 변형
});

test("시작할 수 없는 파일 — 음성 트랙 없음 · 영상 아님", async ({ page }) => {
  await page.goto("/");

  // 음성 트랙이 없는 영상 — 서버 이유와 길이
  await fileRow(page, "silent_demo.mp4").click();
  await el(page, "4.6").click();
  await expect(inDialog(page, "7.1")).toHaveText("음성이 없는 파일이에요");
  await expect(inDialog(page, "7.2")).toHaveText("길이 10:00");
  await expect(inDialog(page, "7.3")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(el(page, "4.6")).toBeFocused();

  // 열 수 없는 파일 — 목록의 길이는 '—', 시작 불가 판에는 길이가 없다
  const notes = fileRow(page, "notes.mp4");
  await expect(notes.locator(".file-length")).toHaveText("—");
  await notes.click();
  await el(page, "4.6").click();
  await expect(inDialog(page, "7.1")).toHaveText("영상·음성 파일이 아닙니다");
  await expect(inDialog(page, "7.2")).toHaveCount(0);
  await inDialog(page, "7.3").click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});
