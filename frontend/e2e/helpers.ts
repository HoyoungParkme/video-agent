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
  sttDelayMs: number;
  sttFail: { seq: number; times: number; drop?: boolean } | null;
  chatFail: number;
  /** 받아쓴 조각 번호(성공한 것), 받은 차례대로 */
  transcribed: number[];
}

/**
 * 가짜 OpenAI를 조절하거나 지금 값을 읽는다 — 채팅 · 받아쓰기 지연, 조각 하나를 몇 번 실패시킬지
 * (drop이면 500 대신 연결을 끊는다 — 인터넷 끊김), 다음 채팅 몇 번을 실패시킬지.
 * reset이면 부른 수 · 받은 조각 기록 · 남은 실패를 비운다(같은 요청의 설정값은 그 뒤에 들어간다).
 */
export async function fakeOpenAI(
  request: APIRequestContext,
  body: {
    chat_delay_ms?: number;
    stt_delay_ms?: number;
    stt_fail?: { seq: number; times: number; drop?: boolean } | null;
    chat_fail?: number;
    reset?: boolean;
  } = {},
): Promise<FakeState> {
  const res = await request.post(`${FAKE}/control`, { data: body });
  return (await res.json()) as FakeState;
}
