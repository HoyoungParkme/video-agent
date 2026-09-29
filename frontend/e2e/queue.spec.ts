/**
 * 대기열 — 첫 영상이 도는 동안 둘째를 시작하면 차례를 기다렸다가 저절로 돈다
 * (VA-UC-001 UC-H0 3b, VA-CODE-001 B1). 서버 재시작 갈래는 pytest(tests/test_main.py)가 본다.
 */
import { expect, test } from "@playwright/test";

import { el, fakeOpenAI, inDialog, saveKey } from "./helpers";

test("둘째 영상은 대기 중 · 1번째로 기다렸다가 첫 영상이 끝나면 돈다", async ({
  page,
  request,
}) => {
  await saveKey(request);
  // 첫 영상이 한동안 돌게 — 채팅 셋이 각각 2.5초
  await fakeOpenAI(request, { reset: true, chat_delay_ms: 2500 });

  // 첫 영상 시작
  await page.goto("/");
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eCaption2");
  await el(page, "3.3").click();
  await inDialog(page, "6.3").click();
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  await expect(el(page, "3.1")).not.toHaveText("차례를 기다리는 중");

  // 둘째 — 사전 안내에 대기 안내(6.1)
  await el(page, "1").click();
  await expect(page).toHaveURL(/\/$/);
  await expect(el(page, "6.6")).toHaveText(/ 중$/); // 목록의 첫 영상은 진행 중
  await el(page, "3.2").locator("input").fill("https://youtu.be/e2eCaption3");
  await el(page, "3.3").click();
  await expect(inDialog(page, "6.1")).toHaveText(
    "지금 다른 영상을 분석 중이에요. 시작하면 차례를 기다렸다가 저절로 시작돼요.",
  );
  await expect(inDialog(page, "6.3")).toHaveText("분석 시작"); // 켜져 있고 문구도 그대로
  await inDialog(page, "6.3").click();

  // UI-3 대기 상태
  await expect(page).toHaveURL(/\/videos\/\d+\/progress$/);
  const second = page.url();
  await expect(el(page, "3.1")).toHaveText("차례를 기다리는 중");
  await expect(el(page, "3.2")).toHaveText("앞 영상 1개가 끝나면 시작해요");
  await expect(el(page, "3.3")).toHaveText("0%");
  await expect(page.locator(".step-memo")).toHaveText(["—", "—", "—", "—"]);
  await expect(el(page, "6.1")).toHaveText("아직 OpenAI로 보내는 것이 없어요");
  await expect(el(page, "6.2")).toHaveText("이 화면을 닫아도 차례가 되면 시작돼요.");

  // UI-1 — 대기 중 행(가장 늦게 시작해 맨 위)
  await el(page, "1").click();
  await expect(el(page, "6.3")).toHaveText("LLM 에이전트 설계 패턴");
  await expect(el(page, "6.6")).toHaveText("대기 중 · 1번째");
  await expect(el(page, "6.7")).toHaveCount(0); // 대기 중 행에는 막대가 없다
  await expect(el(page, "5.2")).toHaveText(/개$/);

  // 행을 누르면 대기 상태 UI-3 — 첫 영상이 끝나면 같은 화면이 저절로 진행되고 결과로 간다
  await el(page, "6.1").click();
  await expect(page).toHaveURL(second);
  await expect(el(page, "3.1")).not.toHaveText("차례를 기다리는 중", { timeout: 30_000 });
  await fakeOpenAI(request, { chat_delay_ms: 0 });
  await expect(page).toHaveURL(/\/videos\/\d+$/, { timeout: 30_000 });
  await expect(el(page, "2.2")).toHaveText("LLM 에이전트 설계 패턴");
});
