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

export type ImageQuality = "low" | "medium";

export interface ImageQualityOption {
  id: ImageQuality;
  /** '낮음' · '중간' */
  label: string;
  /** 한 장 값 — UI-4 카드 · UI-5 · UI-8이 같이 쓴다 */
  price_usd: number;
}

export interface ImageSettings {
  model: string;
  quality: ImageQuality;
  models: string[];
  qualities: ImageQualityOption[];
}

export interface Settings {
  key: KeyStatus;
  models: Models;
  model_options: { stt: ModelOption[]; text: ModelOption[] };
  /** 인포그래픽 이미지 모델 · 품질과 품질마다 한 장 값 */
  image: ImageSettings;
  inbox_path: string;
}

export type SourceKind = "youtube" | "local";
export type CaptionKind = "manual" | "auto";
export type VideoStatus = "registered" | "in_progress" | "failed" | "analyzed";
export type JobStatus = "queued" | "running" | "failed" | "done";
export type JobStage =
  | "pending"
  | "download"
  | "extract"
  | "transcribe"
  | "summarize"
  | "chapter"
  | "suggest"
  | "frames";
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
  /** 끌어 놓아 올린 파일인가(원본 자리 = 올린 사본) — UI-1 부제 '올린 파일', UI-6 「남는 것」 */
  uploaded: boolean;
  /** 올린 사본이 아직 남아 있으면 그 크기 — UI-6 '올린 사본({크기})' */
  upload_bytes: number | null;
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

export interface InboxFile {
  name: string;
  size_bytes: number;
  duration_sec: number | null;
  kind: "video" | "audio";
  modified_at: string;
}

export interface InboxListing {
  /** 사용자에게 보일 호스트 쪽 폴더 경로 */
  path: string;
  files: InboxFile[];
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

/** 진행 화면의 장면 칸(UI-3 4.9) — missing은 얻지 못하고 넘어간 칸. url은 done일 때만 */
export interface FrameProgress {
  done: number;
  total: number;
  items: {
    chapter_seq: number;
    state: "waiting" | "in_flight" | "done" | "missing";
    url: string | null;
  }[];
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
  /** 장면 단계가 있는 작업만 */
  frames: FrameProgress | null;
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

export type FrameSource = "storyboard" | "local_frame";
/** absent = 장면 단계 전 결과(채울 수 있다) · making = 채우는 중 · unavailable = 음성 파일 · 원본 없음 */
export type FramesState = "absent" | "making" | "done" | "unavailable";

export interface Frame {
  chapter_seq: number;
  /** 실제로 잘라 온 장면의 시각 — 챕터 시작과 몇 초 다를 수 있다 */
  sec: number;
  source: FrameSource;
  width: number;
  height: number;
  /** /api/videos/{id}/frames/{seq} */
  url: string;
}

export interface FrameSet {
  state: FramesState;
  /** 장면이 있는 챕터만, 챕터 순서대로 */
  frames: Frame[];
}

/** none = 만든 적 없음 · making = 그리는 중 · done = 그림 있음 · failed = 마지막 그리기 실패 */
export type InfographicState = "none" | "making" | "done" | "failed";

export interface InfographicImage {
  /** /api/videos/{id}/infographic/image?v={만든 시각} — 그림이 바뀌면 주소가 바뀐다 */
  url: string;
  model: string;
  quality: ImageQuality;
  width: number;
  height: number;
  created_at: string;
  cost_usd: number;
}

export interface Infographic {
  state: InfographicState;
  /** 지금 쓰는 그림 — 다시 만들기가 실패해도 이전 그림이 남는다 */
  image: InfographicImage | null;
  /** failed일 때 한 줄 */
  error_reason: string | null;
}

export interface Chapter {
  seq: number;
  part_seq: number | null;
  start_sec: number;
  title: string;
  bullets: string[];
  /** 대표 장면. 없으면 null(UI-4 6.7이 없다) */
  frame: Frame | null;
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
  /** 대표 장면 — making이면 UI-4가 3초마다 장면을 다시 받는다, absent면 한 번 채우기를 맡긴다 */
  frames_state: FramesState;
  /** 인포그래픽 — making이면 UI-4가 3초마다 다시 받는다 */
  infographic: Infographic;
}

/** 질문 하나와 답(VA-API-001 4장 ChatTurn). cited_secs가 비면 '영상에 없는 내용'. */
export interface ChatTurn {
  id: number;
  question: string;
  answer: string;
  cited_secs: number[];
  asked_at: string;
}

/**
 * 내보내는 방법 — 파일이면 그림 줄과 `## 스크립트` 절이 든 노트, 클립보드면 둘 다 없는 노트
 * (VA-API-001 GET export).
 */
export type ExportMethod = "file" | "clipboard";

/** 함께 쓸 파일 하나 — UI-7 2.3 칩. name은 data/export/ 안의 파일 이름. */
export interface ExportFile {
  kind: "note" | "script" | "frame" | "infographic";
  name: string;
}

/**
 * 내보낼 노트 전체와 파일 이름. path는 보일 경로 `data/export/{filename}.md`.
 * files는 method=file일 때 함께 쓸 파일, clipboard면 빈 배열.
 */
export interface ExportPreview {
  filename: string;
  path: string;
  markdown: string;
  files: ExportFile[];
}

/** 쓴 파일 — path는 짧은 알림 '{path}에 저장했어요'에, images(쓴 그림 수)는 '· 그림 {n}장'에. */
export interface ExportResult {
  filename: string;
  path: string;
  bytes: number;
  images: number;
  files: ExportFile[];
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

/** 올리는 중인 요청 하나 — 응답(done)과 멈추기(abort) */
export interface Upload {
  done: Promise<RegisterResponse>;
  abort: () => void;
}

/** 멈추기(abort)로 끝난 올리기 — 서버 오류가 아니다 */
export class UploadAborted extends Error {}

/**
 * POST /api/uploads — 파일 하나를 본문 그대로 올려 등록한다(VA-API-001). 이것만 XHR이다 — fetch는
 * 올리는 쪽 진행을 주지 않는다(VA-DOM-002 1장). onProgress는 보낸 바이트를 받는다(다 보내면 파일
 * 크기). 서버가 거절하면 ApiError, 닿지 못하면 TypeError, 멈추면 UploadAborted로 끝난다.
 */
function upload(file: File, onProgress: (sent: number) => void): Upload {
  const xhr = new XMLHttpRequest();
  const done = new Promise<RegisterResponse>((resolve, reject) => {
    xhr.open("POST", "/api/uploads");
    xhr.setRequestHeader("Content-Type", "application/octet-stream");
    xhr.setRequestHeader("X-File-Name", encodeURIComponent(file.name));
    xhr.upload.onprogress = (e) => onProgress(e.loaded);
    xhr.upload.onload = () => onProgress(file.size); // 다 보냈다 — 서버가 파일을 확인하는 중
    xhr.onload = () => {
      let body: Record<string, unknown> = {};
      try {
        body = JSON.parse(xhr.responseText) as Record<string, unknown>;
      } catch {
        // 평문 오류(web이 api에 닿지 못해 대신 답한 경우 등)도 ApiError로
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as unknown as RegisterResponse);
      else reject(new ApiError(xhr.status, body));
    };
    xhr.onerror = () => reject(new TypeError("서버에 연결할 수 없음"));
    xhr.onabort = () => reject(new UploadAborted("올리기를 멈췄다"));
    xhr.send(file);
  });
  return { done, abort: () => xhr.abort() };
}

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  if (res.ok) {
    // 연결 문구 배너가 떠 있는데 요청이 통과했다 — 서버가 키를 다시 확인해 통과시켰을 수 있다.
    // 설정을 다시 받아 배너를 새로 그린다(공통 1.4 — 분석 버튼 · 다시 시도 · 질문 보내기)
    if (
      method !== "GET" &&
      current?.key.state === "invalid" &&
      current.key.reason_kind === "network"
    )
      loadSettings().catch(() => undefined); // 받지 못하면 배너는 그대로
    if (res.status === 204) return undefined as T; // 본문 없음(삭제)
    return (await res.json()) as T;
  }
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
  saveModels: (
    stt_model: string,
    text_model: string,
    image?: { image_model: string; image_quality: ImageQuality },
  ) => call<Settings>("PUT", "/api/settings/models", { stt_model, text_model, ...image }),
  /** POST /api/videos — YouTube 주소를 등록하고 사전 안내 예상치를 받는다. 중복이면 기존 영상 */
  register: (url: string) =>
    call<RegisterResponse>("POST", "/api/videos", { source: "youtube", url }),
  /** POST /api/videos — inbox 파일을 등록한다. 같은 내용이면 기존 영상 */
  registerLocal: (path: string) =>
    call<RegisterResponse>("POST", "/api/videos", { source: "local", path }),
  /** POST /api/uploads — 끌어 놓거나 고른 파일을 올려 등록한다. 같은 내용이면 기존 영상 */
  upload,
  /** GET /api/inbox — inbox 파일 목록(길이까지), 수정 시각 최근 순 */
  inbox: () => call<InboxListing>("GET", "/api/inbox"),
  /** GET /api/videos — 작업이 있는 영상, 작업 시작 최근 순 */
  videos: () => call<VideoSummary[]>("GET", "/api/videos"),
  /** GET /api/videos/{id} — 영상과 최근 작업 요약 */
  video: (id: number) => call<VideoDetail>("GET", `/api/videos/${id}`),
  /** POST /api/videos/{id}/job — 분석 시작. running 또는 queued */
  startJob: (id: number) => call<Job>("POST", `/api/videos/${id}/job`),
  /** GET /api/videos/{id}/job — 진행 상태(UI-3이 1초마다) */
  job: (id: number) => call<Job>("GET", `/api/videos/${id}/job`),
  /** POST /api/videos/{id}/job/retry — 실패한 단계부터 이어서. running 또는 queued */
  retry: (id: number) => call<Job>("POST", `/api/videos/${id}/job/retry`),
  /** GET /api/videos/{id}/result — 결과 전부 */
  result: (id: number) => call<Result>("GET", `/api/videos/${id}/result`),
  /** GET /api/videos/{id}/frames — 장면 상태와 장면들. UI-4가 채우는 동안 3초마다 */
  frames: (id: number) => call<FrameSet>("GET", `/api/videos/${id}/frames`),
  /** POST /api/videos/{id}/frames — 옛 결과에 장면 채우기를 맡긴다(202). 두 번 불러도 같다 */
  fillFrames: (id: number) => call<FrameSet>("POST", `/api/videos/${id}/frames`),
  /** GET /api/videos/{id}/infographic — 상태와 지금 그림. UI-4가 그리는 동안 3초마다 */
  infographic: (id: number) => call<Infographic>("GET", `/api/videos/${id}/infographic`),
  /** POST /api/videos/{id}/infographic — 그리기를 맡긴다(202). 그리는 중이면 409, 키가 없으면 503 */
  makeInfographic: (id: number) => call<Infographic>("POST", `/api/videos/${id}/infographic`),
  /** GET /api/videos/{id}/chat — 질문 · 답변 기록, 시간순 */
  chat: (id: number) => call<ChatTurn[]>("GET", `/api/videos/${id}/chat`),
  /** POST /api/videos/{id}/chat — 질문하고 답을 받는다. 실패하면 저장되지 않는다 */
  ask: (id: number, question: string) =>
    call<ChatTurn>("POST", `/api/videos/${id}/chat`, { question }),
  /** GET /api/videos/{id}/export — 고른 방법의 노트 전체와 파일 이름. UI-7이 열 때 · 방법이나 3을 바꿀 때 */
  exportPreview: (id: number, withChat: boolean, method: ExportMethod) =>
    call<ExportPreview>("GET", `/api/videos/${id}/export?with_chat=${withChat}&method=${method}`),
  /** POST /api/videos/{id}/export — 파일 방법의 노트와 스크립트(그림이 있으면 그림도)를 서버가 data/export/에 쓴다 */
  exportFile: (id: number, withChat: boolean) =>
    call<ExportResult>("POST", `/api/videos/${id}/export`, { with_chat: withChat }),
  /** DELETE /api/videos/{id} — 영상과 딸린 것 전부. 도는 분석은 멈추고 대기 중이면 대기열에서 빠진다 */
  deleteVideo: (id: number) => call<void>("DELETE", `/api/videos/${id}`),
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
