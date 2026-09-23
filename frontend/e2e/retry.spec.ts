/**
 * S6 4번 — 받아쓰기 조각 하나가 세 번 실패하면 실패 알림, 다시 시도하면 그 조각부터 이어서 받아쓴다
 * (VA-SCN-001 S6, VA-CODE-001 B2). 완료한 조각을 다시 보내지 않는 것은 가짜 OpenAI가 받은 조각 기록으로 본다.
 * 요약 단계에서 멈추면 그 단계부터 다시 한다. 인터넷 끊김 변형은 가짜가 연결을 끊어 본다 — 대기열에서
 * 다시 시도하는 테스트와 함께(앞 영상은 자막 없는 YouTube를 내려받아 받아쓴다).
 * 서버 재시작 갈래(받아쓰기 도중 → 실패 → 다시 시도)는 pytest(tests/test_main.py)가 본다.
 */
import { expect, test } from "@playwright/test";

import { el, fakeOpenAI, inDialog, saveKey } from "./helpers";

test.beforeEach(async ({ request }) => {
  await saveKey(request);
});

test("8번 조각이 세 번 실패 → 실패 알림 → 다시 시도하면 8번 조각만 다시 보낸다", async ({
  page,
  request,
}) => {
  // 받아쓰기를 조금 늦춘다 — 8번이 세 번 실패하는 동안 같이 시작한 7 · 9번이 돈다. 실패 뒤에는
  // 새 조각을 시작하지 않고 돌던 조각만 끝까지 가므로(UC-S3 3a2) 완료가 늘 8개다
  await fakeOpenAI(request, {
    reset: true,
    chat_delay_ms: 0,
    stt_delay_ms: 300,
    stt_fail: { seq: 8, times: 3 },
  });

  await page.goto("/");
  await page.locator(".file-row", { hasText: "lecture_0920.mp4" }).click();
  await el(page, "4.6").click();
  await expect(inDialog(page, "3.2")).toHaveText(
    "음성을 뽑아 9개 조각으로 나누고, 3개씩 동시에 받아씁니다.",
  );
  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);

  // 실패 상태 — 8번 조각을 세 번 보냈고 나머지 여덟은 끝났다
  await expect(el(page, "5")).toBeVisible({ timeout: 20_000 });
  await expect(el(page, "3.1")).toHaveText("받아쓰기가 멈췄어요");
  await expect(el(page, "3.2")).toHaveText("조각 8 / 9에서 실패 · 완료한 8개는 저장됨");
  await expect(page.locator(".step-memo")).toHaveText([/초$/, "8 / 9에서 멈춤", "—", "—", "—"]);
  await expect(page.locator(".step-mark").nth(1)).toHaveAttribute("data-state", "failed");
  await expect(el(page, "4.6")).toHaveAttribute("aria-label", "조각 9개 중 8개 완료, 1개 실패");
  await expect(el(page, "4.8")).toHaveText("완료 8실패 1");
  await expect(el(page, "5.1")).toHaveText("OpenAI가 요청을 처리하지 못했어요");
  await expect(el(page, "5.2")).toHaveText(
    "8번째 조각을 3번 보냈지만 실패했어요 — OpenAI 서버 오류. 완료한 8개 조각은 저장돼 있어 처음부터 다시 받아쓰지 않아요.",
  );
  await expect(el(page, "5.4")).toHaveText("8번째 조각부터 다시 시도");
  await expect(el(page, "6.1")).toHaveText("음성 조각 → OpenAI whisper-1");
  await expect(el(page, "6.2")).toHaveText("다시 시도하면 8번째 조각부터 이어서 받아씁니다.");

  // UI-1 실패 행 — 행을 누르면 이 화면으로 돌아온다
  const failedUrl = page.url();
  await el(page, "5.3").click();
  await expect(page).toHaveURL(/\/$/);
  const row = page.locator(".video-row", { hasText: "lecture_0920.mp4" });
  await expect(row.locator(".video-row-status")).toHaveText("받아쓰기 8 / 9에서 멈춤");
  await row.locator(".video-row-link").click();
  await expect(page).toHaveURL(failedUrl);

  const before = await fakeOpenAI(request);
  expect([...before.transcribed].sort((a, b) => a - b)).toEqual([1, 2, 3, 4, 5, 6, 7, 9]);

  // 다시 시도 — 실패 알림이 사라지고 8번 조각부터 끝까지 간다
  await el(page, "5.4").click();
  await expect(el(page, "5")).toHaveCount(0);
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 20_000 });
  await expect(el(page, "2.2")).toHaveText("lecture_0920.mp4");
  await expect(el(page, "6.1")).toHaveText(/^\d+개 · 파트 2개$/); // 1시간 넘는 영상

  const after = await fakeOpenAI(request);
  expect(after.transcriptions - before.transcriptions).toBe(1); // 8번 조각 하나만 더 보냈다
  expect(after.transcribed.slice(before.transcribed.length)).toEqual([8]);
});

test("인터넷 끊김 · 다른 영상이 도는 동안 다시 시도 — 대기 상태로 기다렸다가 이어서 받아쓴다", async ({
  page,
  request,
}) => {
  await fakeOpenAI(request, {
    reset: true,
    chat_delay_ms: 0,
    stt_delay_ms: 0,
    stt_fail: { seq: 2, times: 3, drop: true },
  });

  // 로컬 음성 — 단계에 추출이 없다. 2번 조각을 보낼 때마다 연결이 끊긴다(인터넷 끊김)
  await page.goto("/");
  await page.locator(".file-row", { hasText: "call_0915.m4a" }).click();
  await el(page, "4.6").click();
  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  await expect(el(page, "5")).toBeVisible({ timeout: 20_000 });
  await expect(page.locator(".step-name")).toHaveText([
    "받아쓰기",
    "핵심 요약",
    "챕터",
    "추천 질문",
  ]);
  await expect(el(page, "5.1")).toHaveText("OpenAI API에 연결하지 못했어요");
  await expect(el(page, "5.2")).toHaveText(
    "2번째 조각을 3번 보냈지만 실패했어요 — 네트워크에 연결할 수 없음. 완료한 2개 조각은 저장돼 있어 처음부터 다시 받아쓰지 않아요.",
  );
  await expect(el(page, "5.4")).toHaveText("2번째 조각부터 다시 시도");
  const failedUrl = page.url();

  // 자막 없는 YouTube를 끝까지 — 채팅을 늦춰 한동안 돌게 한다
  await fakeOpenAI(request, { chat_delay_ms: 2500 });
  await el(page, "1").click();
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eNoCapt02");
  await el(page, "3.3").click();
  await expect(inDialog(page, "2.5")).toHaveText("자막 없음 · 받아쓰기 필요");
  await expect(inDialog(page, "6.1")).toHaveCount(0); // 실패한 영상은 도는 영상이 아니다
  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  // 내려받기가 mp3까지 만든다 — 추출 단계가 없다(DOM-002 stages_for)
  await expect(page.locator(".step-name")).toHaveText([
    "음성 내려받기",
    "받아쓰기",
    "핵심 요약",
    "챕터",
    "추천 질문",
  ]);
  await expect(el(page, "3.1")).toHaveText(/만드는 중$/, { timeout: 20_000 });

  // 실패한 영상으로 돌아가 다시 시도 — 앞 영상이 끝날 때까지 대기 상태
  await page.goto(failedUrl);
  const before = await fakeOpenAI(request);
  await el(page, "5.4").click();
  await expect(el(page, "5")).toHaveCount(0);
  await expect(el(page, "3.1")).toHaveText("차례를 기다리는 중");
  await expect(el(page, "3.2")).toHaveText("앞 영상 1개가 끝나면 시작해요");
  await expect(el(page, "6.2")).toHaveText("이 화면을 닫아도 차례가 되면 시작돼요.");

  // 앞 영상이 끝나면 이어서 — 2번 조각만 다시 보내고 결과까지
  await fakeOpenAI(request, { chat_delay_ms: 0 });
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 30_000 });
  await expect(el(page, "2.2")).toHaveText("call_0915.m4a");
  await expect(el(page, "6.1")).toHaveText(/^\d+개$/); // 1시간 안이라 파트 없이
  const after = await fakeOpenAI(request);
  expect(after.transcriptions - before.transcriptions).toBe(1);
  expect(after.transcribed.at(-1)).toBe(2);
});

test("핵심 요약 단계에서 실패 → 그 단계부터 다시 시도한다", async ({ page, request }) => {
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 0, chat_fail: 1 });

  await page.goto("/");
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eCaption5");
  await el(page, "3.3").click();
  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);

  // 받아쓰기 아닌 단계의 실패 — 격자 없이 단계 X, 스크립트는 저장돼 있다
  await expect(el(page, "5")).toBeVisible({ timeout: 20_000 });
  await expect(el(page, "3.1")).toHaveText("핵심 요약 단계가 멈췄어요");
  await expect(el(page, "3.2")).toHaveText("4단계 중 2단계에서 실패 · 스크립트는 저장됨");
  await expect(page.locator(".step-memo")).toHaveText([/초$/, "멈춤", "—", "—"]);
  await expect(page.locator(".step-mark").nth(1)).toHaveAttribute("data-state", "failed");
  await expect(el(page, "4.6")).toHaveCount(0);
  await expect(el(page, "5.1")).toHaveText("OpenAI가 요청을 처리하지 못했어요");
  await expect(el(page, "5.2")).toHaveText(
    "핵심 요약 단계에서 멈췄어요 — OpenAI 서버 오류. 스크립트는 저장돼 있어 처음부터 다시 하지 않아요.",
  );
  await expect(el(page, "5.4")).toHaveText("핵심 요약부터 다시 시도");
  await expect(el(page, "6.2")).toHaveText("다시 시도하면 핵심 요약부터 이어서 합니다.");

  await el(page, "5.4").click();
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 20_000 });
  await expect(el(page, "2.2")).toHaveText("평가 세트 만드는 법");
  const fake = await fakeOpenAI(request);
  expect(fake.chats).toBe(4); // 실패한 요약 한 번 + 다시 시도의 요약 · 챕터 · 추천 질문
  expect(fake.transcriptions).toBe(0);
});
