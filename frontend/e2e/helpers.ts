/** E2E 공용 — 요소 번호로 찾기 · 키 저장 · 가짜 OpenAI 조절. */
import type { APIRequestContext, Page } from "@playwright/test";

export const GOOD_KEY = "sk-e2e-good-000000000000000000"; // e2e/fake-openai.mjs와 같은 값
const FAKE = "http://127.0.0.1:8190";

export const el = (page: Page, no: string) => page.locator(`[data-el="${no}"]`);

/** 다이얼로그 안의 요소 — UI-2는 UI-1 위에 떠서 요소 번호가 겹친다(UI-1 6.1 · UI-2 6.1). */
export const inDialog = (page: Page, no: string) =>
  page.getByRole("dialog").locator(`[data-el="${no}"]`);

/** 맞는 키를 저장해 둔다 — 화면을 거치지 않고 web의 /api로. */
export async function saveKey(request: APIRequestContext): Promise<void> {
  const res = await request.post("/api/settings/key", { data: { key: GOOD_KEY } });
  if (!res.ok()) throw new Error(`키 저장 실패 ${res.status()}`);
}

export interface FakeState {
  chatDelayMs: number;
  chats: number;
  transcriptions: number;
}

/** 가짜 OpenAI의 채팅 지연을 바꾸거나(reset이면 부른 수도 0으로) 지금 값을 읽는다. */
export async function fakeOpenAI(
  request: APIRequestContext,
  body: { chat_delay_ms?: number; reset?: boolean } = {},
): Promise<FakeState> {
  const res = await request.post(`${FAKE}/control`, { data: body });
  return (await res.json()) as FakeState;
}
