/**
 * 서버 호출 한곳 — 화면은 fetch하지 않고 여기 함수를 부른다(VA-DOM-002 1장).
 * 형태는 VA-API-001 4장 스키마 그대로다. 실패는 problem+json을 ApiError로 바꿔 던진다.
 */
import { useEffect, useSyncExternalStore } from "react";

export type KeyState = "ok" | "missing" | "invalid";
export type ReasonKind = "format" | "auth" | "quota" | "network";

export interface KeyStatus {
  state: KeyState;
  masked: string | null;
  stored_in: string | null;
  checked_at: string | null;
  reason_kind: ReasonKind | null;
  reason: string | null;
}

export interface ModelPrice {
  per_min_usd?: number;
  input_per_mtok_usd?: number;
  output_per_mtok_usd?: number;
}

export interface ModelOption {
  id: string;
  label: string;
  price: ModelPrice;
}

export interface Settings {
  key: KeyStatus;
  models: { stt: string | null; text: string };
  model_options: { stt: ModelOption[]; text: ModelOption[] };
  inbox_path: string;
}

/** problem+json 하나. kind는 `urn:va:` 뒤 — key-rejected · validation 등(VA-API-001 2장). */
export class ApiError extends Error {
  readonly status: number;
  readonly kind: string;
  readonly body: Record<string, unknown>;

  constructor(status: number, body: Record<string, unknown>) {
    const detail = typeof body.detail === "string" ? body.detail : `HTTP ${status}`;
    super(detail);
    this.status = status;
    this.body = body;
    this.kind = typeof body.type === "string" ? body.type.replace("urn:va:", "") : "unknown";
  }

  /** 확장 필드 reason(한 줄, 한국어). 없으면 detail. */
  get reason(): string {
    return typeof this.body.reason === "string" ? this.body.reason : this.message;
  }
}

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  if (res.ok) return (await res.json()) as T;
  let problem: Record<string, unknown> = {};
  try {
    problem = (await res.json()) as Record<string, unknown>;
  } catch {
    // 평문 오류(서버가 꺼져 web이 대신 답한 경우 등)도 ApiError로
  }
  throw new ApiError(res.status, problem);
}

export const api = {
  /** GET /api/settings — 다시 확인하지 않는다. */
  settings: () => call<Settings>("GET", "/api/settings"),
  /** POST /api/settings/key — 확인이 통과해야 저장된다. */
  saveKey: (key: string) => call<Settings>("POST", "/api/settings/key", { key }),
  /** PUT /api/settings/models */
  saveModels: (stt_model: string, text_model: string) =>
    call<Settings>("PUT", "/api/settings/models", { stt_model, text_model }),
};

// 설정 한 벌을 화면들이 같이 본다 — layout의 배너와 화면이 같은 값을 쓰고, 키를 저장하면 배너가 바로 바뀐다
let current: Settings | null = null;
let inflight: Promise<Settings> | null = null;
const listeners = new Set<() => void>();

/** 새 설정을 알린다 — 저장 응답을 받은 화면이 부른다. */
export function publishSettings(next: Settings): void {
  current = next;
  listeners.forEach((listener) => listener());
}

/** 설정을 다시 받는다. 동시에 여러 번 불러도 요청은 하나. */
export function loadSettings(): Promise<Settings> {
  inflight ??= api
    .settings()
    .then((s) => {
      publishSettings(s);
      return s;
    })
    .finally(() => {
      inflight = null;
    });
  return inflight;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** 지금 설정. 부르는 컴포넌트가 붙을 때 한 번 새로 받는다 — 받기 전에는 null. */
export function useSettings(): Settings | null {
  const settings = useSyncExternalStore(
    subscribe,
    () => current,
    () => null,
  );
  useEffect(() => {
    loadSettings().catch(() => {
      // 서버가 꺼져 있으면 배너 · 막힘을 판단하지 못한다 — 그대로 둔다
    });
  }, []);
  return settings;
}

/** 키 상태로 분석 버튼을 막는가 — 연결 실패는 막지 않는다(VA-UI-002 1.4). */
export function keyBlocks(key: KeyStatus): boolean {
  return key.state === "missing" || (key.state === "invalid" && key.reason_kind !== "network");
}
