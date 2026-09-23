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
  models: Models;
  model_options: { stt: ModelOption[]; text: ModelOption[] };
  inbox_path: string;
}

export type SourceKind = "youtube" | "local";
export type CaptionKind = "manual" | "auto";
export type VideoStatus = "registered" | "in_progress" | "failed" | "analyzed";
export type JobStatus = "queued" | "running" | "failed" | "done";
export type JobStage =
  "pending" | "download" | "extract" | "transcribe" | "summarize" | "chapter" | "suggest";
export type ChunkState = "waiting" | "in_flight" | "done" | "failed";
export type ErrorKind = "network" | "openai" | "youtube" | "ffmpeg" | "disk" | "unknown";
export type TranscriptSource = "caption_manual" | "caption_auto" | "stt";

export interface Models {
  stt: string | null;
  text: string;
}

export interface Video {
  id: number;
  source_kind: SourceKind;
  source_id: string;
  title: string;
  channel: string | null;
  duration_sec: number;
  origin: string;
  has_captions: boolean;
  caption_language: string | null;
  caption_kind: CaptionKind | null;
  status: VideoStatus;
  analyzed_at: string | null;
  created_at: string;
  chat_turn_count: number;
}

export interface JobSummary {
  id: number;
  status: JobStatus;
  stage: JobStage;
  queue_position: number | null;
  progress_pct: number;
  chunks_done: number | null;
  chunks_total: number | null;
  failed_chunk_seq: number | null;
  started_at: string;
  finished_at: string | null;
}

export interface VideoSummary extends Video {
  job: JobSummary;
}

export interface VideoDetail {
  video: Video;
  job: JobSummary | null;
}

export interface Estimate {
  needs_stt: boolean;
  seconds: number;
  chunks: number | null;
  concurrency: number | null;
  stt_minutes: number | null;
  stt_price_per_min: number | null;
  stt_cost_usd: number;
  text_cost_usd: number;
  total_cost_usd: number;
  stt_model: string;
  text_model: string;
}

export interface RegisterResponse {
  video: Video;
  estimate: Estimate | null;
}

export interface Chunks {
  total: number;
  done: number;
  in_flight: number;
  failed: number;
  waiting: number;
  next_seq: number | null;
  items: { seq: number; state: ChunkState }[];
}

export interface JobError {
  kind: ErrorKind;
  reason: string;
  chunk_seq: number | null;
  attempts: number;
}

export interface Job {
  id: number;
  video_id: number;
  status: JobStatus;
  stage: JobStage;
  queue_position: number | null;
  stages: JobStage[];
  stage_index: number;
  progress_pct: number;
  remaining_sec: number | null;
  chunks: Chunks | null;
  concurrency: number | null;
  models: Models;
  error: JobError | null;
  est_seconds: number;
  est_cost_usd: number;
  stage_durations_sec: Partial<Record<JobStage, number>>;
  started_at: string;
  finished_at: string | null;
}

export interface Segment {
  seq: number;
  start_sec: number;
  end_sec: number;
  text: string;
}

export interface Chapter {
  seq: number;
  part_seq: number | null;
  start_sec: number;
  title: string;
  bullets: string[];
}

export interface Result {
  video: Video;
  transcript: {
    source: TranscriptSource;
    language: string;
    model: string | null;
    segments: Segment[];
  };
  summary: {
    one_liner: string;
    model: string;
    insights: { seq: number; text: string; source_secs: number[] }[];
  };
  parts: {
    seq: number;
    title: string;
    start_sec: number;
    end_sec: number;
    chapter_count: number;
  }[];
  chapters: Chapter[];
  suggested_questions: { seq: number; text: string }[];
  models: Models;
  analyzed_at: string;
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
  /** POST /api/videos — YouTube 주소를 등록하고 사전 안내 예상치를 받는다. 중복이면 기존 영상 */
  register: (url: string) =>
    call<RegisterResponse>("POST", "/api/videos", { source: "youtube", url }),
  /** GET /api/videos — 작업이 있는 영상, 작업 시작 최근 순 */
  videos: () => call<VideoSummary[]>("GET", "/api/videos"),
  /** GET /api/videos/{id} — 영상과 최근 작업 요약 */
  video: (id: number) => call<VideoDetail>("GET", `/api/videos/${id}`),
  /** POST /api/videos/{id}/job — 분석 시작. running 또는 queued */
  startJob: (id: number) => call<Job>("POST", `/api/videos/${id}/job`),
  /** GET /api/videos/{id}/job — 진행 상태(UI-3이 1초마다) */
  job: (id: number) => call<Job>("GET", `/api/videos/${id}/job`),
  /** GET /api/videos/{id}/result — 결과 전부 */
  result: (id: number) => call<Result>("GET", `/api/videos/${id}/result`),
};

// 설정 한 벌을 화면들이 같이 본다 — layout의 배너와 화면이 같은 값을 쓰고, 키를 저장하면 배너가 바로 바뀐다
let current: Settings | null = null;
let version = 0; // 알릴 때마다 는다 — 늦게 온 옛 응답이 새 값을 덮지 않게
let inflight: Promise<Settings> | null = null;
const listeners = new Set<() => void>();
const RETRY_MS = 2000;

/** 새 설정을 알린다 — 저장 응답을 받은 화면이 부른다. */
export function publishSettings(next: Settings): void {
  version += 1;
  current = next;
  listeners.forEach((listener) => listener());
}

/** 설정을 다시 받는다. 동시에 여러 번 불러도 요청은 하나. */
export function loadSettings(): Promise<Settings> {
  inflight ??= (async () => {
    const started = version;
    const fetched = await api.settings();
    if (version === started) publishSettings(fetched);
    return current ?? fetched;
  })().finally(() => {
    inflight = null;
  });
  return inflight;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/**
 * 지금 설정. 부르는 컴포넌트가 붙을 때 새로 받는다 — 받기 전에는 null.
 * 서버가 아직 뜨는 중이면(compose를 막 올렸을 때) 받을 때까지 2초마다 다시 부른다.
 */
export function useSettings(): Settings | null {
  const settings = useSyncExternalStore(
    subscribe,
    () => current,
    () => null,
  );
  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const attempt = () => {
      loadSettings().catch(() => {
        if (alive) timer = setTimeout(attempt, RETRY_MS);
      });
    };
    attempt();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, []);
  return settings;
}

/** 키 상태로 분석 버튼을 막는가 — 연결 실패는 막지 않는다(VA-UI-002 1.4). */
export function keyBlocks(key: KeyStatus): boolean {
  return key.state === "missing" || (key.state === "invalid" && key.reason_kind !== "network");
}
