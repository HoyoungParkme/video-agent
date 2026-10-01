/**
 * VA-UI-002#UI-1 홈 — 2 제목 영역 · 3 YouTube 링크 카드(3.1 · 3.2 · 3.3 분석 · 3.4 · 3.5) · 4 내 파일 카드
 * (4.1 · 4.7 끌어 놓기 칸 · 4.10 파일 고르기 · 4.11 올리는 중 · 4.17 한 줄 · 4.19 구분선 · 4.2 inbox 목록 ·
 * 4.3 파일 행 · 4.4 빈 안내 · 4.5 · 4.6 선택한 파일 분석) · 5 목록 머리(5.1 · 5.2 · 5.3) · 6 분석한 영상 목록
 * (6.1 ~ 6.8) · 7 빈 상태 상자 · 8 끌어 오는 중 덮개. 키 없음 배너(1)는 layout의 공통 1.4다.
 * 로컬 파일은 둘로 넣는다 — 끌어 놓기(창 어디에 놓아도) · 파일 고르기로 올리기, inbox에서 고르기. 여러 파일 ·
 * 받지 않는 형식은 보내기 전에 거른다. 올리는 동안은 진행과 멈추기, 다 보내면 파일 확인 중이고, 응답은
 * 등록 응답과 같이 다룬다. 올리다 끊기면 한 줄과 다시 올리기. 올리는 동안 떠나려 하면 먼저 묻는다 —
 * 새로 고침 · 창 닫기는 브라우저 창(beforeunload), 앱 안 링크는 확인 창(leave.ts). 떠나면 멈춘다.
 * 분석(3.3) · 선택한 파일 분석(4.6)은 등록 응답의 status로 갈 곳을 정한다 — registered면 UI-2, analyzed면
 * UI-4와 짧은 알림, 그 밖은 UI-3. 대기 표시는 누른 버튼에, 그동안은 어느 쪽도 새 요청을 보내지 않는다.
 * 행 휴지통(6.8)은 모든 상태의 행에 있고 UI-6을 연다. 지우면 목록을 다시 받고, 초점은 바로 아래 행 →
 * 바로 위 행 → 「분석한 영상」 제목(5.1) 순으로 간다. UI-4에서 지우고 왔으면 5.1에 둔다.
 * 등록 실패는 셋으로 가른다 — 3.4는 형식 오류 · 빈 칸만(빈 칸은 서버에 묻지 않는다), 키 오류는 배너만,
 * 그 밖은 UI-2 시작 불가 판(7, 문구는 blockedOf). 고른 파일이 inbox에서 사라졌으면 목록을 다시 받는다.
 */
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useEffectEvent, useRef, useState } from "react";

import {
  api,
  ApiError,
  keyBlocks,
  loadSettings,
  useSettings,
  UploadAborted,
  type Estimate as EstimateData,
  type InboxListing,
  type RegisterResponse,
  type Video,
  type VideoSummary,
} from "@/api/client";
import { Button } from "@/components/buttons";
import EmptyBox from "@/components/EmptyBox";
import { durationLabel } from "@/components/TimeChip";
import { flash } from "@/components/Toast";
import { ACCEPTED, analyzedLabel, KINDS, sizeLabel, stageName } from "@/labels";
import { guardLeave, leaveTo } from "@/leave";
import Delete, { takeListFocus, TrashIcon } from "@/screens/Delete";
import Estimate, { Blocked, blockedOf, type BlockedInfo } from "@/screens/Estimate";

/** 입력 오류(3.4) — 받는 주소 형태를 알린다. 형식이 틀렸거나 비었을 때만(UI-1 규칙) */
const URL_HINT = "YouTube 주소를 넣어 주세요 — watch · youtu.be · shorts 주소를 받아요";
const EMPTY_TITLE = "아직 분석한 영상이 없어요";
const EMPTY_BODY = "위에 링크를 붙여 넣거나 파일을 끌어 놓아 보세요.";
const EMPTY_BODY_NO_KEY = `설정에서 OpenAI API 키를 넣은 뒤, ${EMPTY_BODY}`;
// 진행 중 · 대기 중 행이 있는 동안만 목록을 다시 받는다(UI-1 규칙)
const REFRESH_MS = 3000;
// 서버가 올린 뒤에야 아는 것 — UI-2 시작 불가 판으로 알린다(UI-1 규칙)
const CANNOT = ["unsupported-file", "no-audio-track", "video-too-long"];

/** 4.17 한 줄 — 오류(빨강 · alert) 또는 알림(status). retry가 있으면 4.18 */
interface Line {
  text: string;
  alert: boolean;
  retry?: File;
}

/** 올리는 중(4.11) — 보낸 바이트가 크기에 닿으면 파일 확인 중 */
interface Sending {
  file: File;
  sent: number;
  abort: () => void;
}

function inProgress(v: VideoSummary): boolean {
  return v.job.status === "queued" || v.job.status === "running";
}

/**
 * 분석한 영상 목록. 진행 중 · 대기 중 행이 있으면 3초마다 다시 받는다. 받기 전에는 null.
 * drop은 지운 행을 곧바로 빼고 다시 받는다 — 기다리던 영상이 돌기 시작했을 수 있다.
 */
function useVideos(): [VideoSummary[] | null, (id: number) => void] {
  const [rows, setRows] = useState<VideoSummary[] | null>(null);
  const [round, setRound] = useState(0);
  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const got = await api.videos();
        if (!alive) return;
        setRows(got);
        if (got.some(inProgress)) timer = setTimeout(load, REFRESH_MS);
      } catch {
        if (alive) timer = setTimeout(load, REFRESH_MS); // 서버가 아직 뜨는 중이면 다시
      }
    };
    void load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [round]);
  const drop = useCallback((id: number) => {
    setRows((prev) => prev && prev.filter((r) => r.id !== id));
    setRound((n) => n + 1);
  }, []);
  return [rows, drop];
}

/**
 * inbox 파일 목록 — 처음 한 번, 그리고 reload를 부를 때. 서버가 아직 뜨는 중이면 3초마다 다시.
 * 받기 전에는 null.
 */
function useInbox(): [InboxListing | null, () => void] {
  const [listing, setListing] = useState<InboxListing | null>(null);
  const [round, setRound] = useState(0);
  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const got = await api.inbox();
        if (alive) setListing(got);
      } catch {
        if (alive) timer = setTimeout(load, REFRESH_MS);
      }
    };
    void load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [round]);
  const reload = useCallback(() => setRound((n) => n + 1), []);
  return [listing, reload];
}

/** 서버가 준 한 줄 — 닿지 못했으면 '서버에 연결할 수 없음'(UI-1 규칙) */
function reasonOf(e: unknown): string {
  if (e instanceof ApiError && e.kind !== "unknown") return e.reason.replace(/[.。]\s*$/, "");
  return "서버에 연결할 수 없음";
}

function UploadIcon({ size = 20 }: { size?: number }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="m17 8-5-5-5 5" />
      <path d="M12 3v12" />
    </svg>
  );
}

function LineIcon({ alert }: { alert: boolean }) {
  return (
    <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      {alert ? <path d="M12 8v4" /> : <path d="M12 16v-4" />}
      {alert ? <path d="M12 16h.01" /> : <path d="M12 8h.01" />}
    </svg>
  );
}

/** 올리는 중(4.11) — 보낸 만큼 막대와 퍼센트. 다 보내면 파일 확인 중(4.14 · 4.16이 빠지고 깜빡이는 막대) */
function SendingBox({ sending, onStop }: { sending: Sending; onStop: () => void }) {
  const { file, sent } = sending;
  const checking = sent >= file.size;
  const pct = file.size > 0 ? Math.floor((sent / file.size) * 100) : 0;
  return (
    <div className="upload-box" role="status" aria-live="polite" data-el="4.11">
      <div className="upload-head">
        <span className="icon-tile icon-tile-teal">
          {checking ? <SourceIcon local /> : <UploadIcon size={18} />}
        </span>
        <span className="upload-text">
          <span className="upload-name" data-el="4.12">
            {file.name}
          </span>
          <span className="upload-state" data-el="4.13">
            {checking
              ? "다 올렸어요. 길이와 음성 트랙을 확인하는 중이에요"
              : `올리는 중 · ${sizeLabel(sent, file.size)} / ${sizeLabel(file.size)}`}
          </span>
        </span>
        {!checking && (
          <span className="upload-pct mono" data-el="4.14">
            {pct}%
          </span>
        )}
      </div>
      {checking ? (
        <div className="upload-bar is-checking va-pulse" data-el="4.15" />
      ) : (
        <div className="upload-bar" data-el="4.15">
          <div className="upload-bar-fill" style={{ width: `${pct}%` }} />
        </div>
      )}
      {!checking && (
        <div className="upload-foot">
          <span className="caption">이 화면을 떠나면 올리기가 멈춰요</span>
          <Button kind="secondary" className="btn-small" el="4.16" onClick={onStop}>
            멈추기
          </Button>
        </div>
      )}
    </div>
  );
}

/** 상태 글자(6.6)와 그 색 — 숫자는 UI-3 숫자 규칙대로 서버 값을 그대로 쓴다. */
function rowStatus(v: VideoSummary): { text: string; tone: string } {
  const job = v.job;
  switch (job.status) {
    case "done":
      return { text: `${analyzedLabel(v.analyzed_at ?? job.started_at)} 분석`, tone: "done" };
    case "queued":
      return { text: `대기 중 · ${job.queue_position}번째`, tone: "queued" };
    case "running":
      if (job.stage === "transcribe") {
        return {
          text: `받아쓰기 중 · ${job.chunks_done ?? 0} / ${job.chunks_total ?? 0}`,
          tone: "active",
        };
      }
      if (job.stage === "pending") return { text: "시작하는 중", tone: "active" };
      return { text: `${stageName(job.stage, v.has_captions)} 중`, tone: "active" };
    default:
      if (job.stage === "transcribe" && job.failed_chunk_seq !== null) {
        return {
          text: `받아쓰기 ${job.failed_chunk_seq} / ${job.chunks_total ?? 0}에서 멈춤`,
          tone: "failed",
        };
      }
      // 첫 단계에 들어가기 전 — 워커가 꺼낸 직후 서버가 죽었거나 임시 폴더를 만들지 못했다
      if (job.stage === "pending") return { text: "시작하기 전에 멈춤", tone: "failed" };
      return { text: `${stageName(job.stage, v.has_captions)}에서 멈춤`, tone: "failed" };
  }
}

function SourceIcon({ local }: { local: boolean }) {
  if (local) {
    return (
      <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M7 3v18" />
        <path d="M17 3v18" />
        <path d="M3 7.5h4" />
        <path d="M3 12h18" />
        <path d="M3 16.5h4" />
        <path d="M17 7.5h4" />
        <path d="M17 16.5h4" />
      </svg>
    );
  }
  return (
    <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

function VideoRow({
  v,
  first,
  onDelete,
}: {
  v: VideoSummary;
  first: boolean;
  onDelete: () => void;
}) {
  const status = rowStatus(v);
  const href = v.status === "analyzed" ? `/videos/${v.id}` : `/videos/${v.id}/progress`;
  // 요소 번호는 첫 행에만 — 와이어프레임이 한 행에 번호를 매겼다
  const el = (no: string) => (first ? no : undefined);
  return (
    <div className="video-row" data-video={v.id}>
      <Link href={href} className="video-row-link" data-el={el("6.1")} onNavigate={leaveTo(href)}>
        <span className="icon-tile" data-el={el("6.2")}>
          <SourceIcon local={v.source_kind === "local"} />
        </span>
        <span className="video-row-text">
          <span className="video-row-title" data-el={el("6.3")}>
            {v.title}
          </span>
          <span className="video-row-sub" data-el={el("6.4")}>
            {v.source_kind === "youtube"
              ? `YouTube · ${v.channel ?? ""}`
              : v.uploaded
                ? "올린 파일"
                : "로컬 파일"}
          </span>
        </span>
        <span className="video-row-length mono" data-el={el("6.5")}>
          {durationLabel(v.duration_sec)}
        </span>
        <span className="video-row-state">
          <span className={`video-row-status is-${status.tone}`} data-el={el("6.6")}>
            {status.text}
          </span>
          {v.job.status === "running" && (
            <span className="mini-bar" data-el={el("6.7")}>
              <span className="mini-bar-fill" style={{ width: `${v.job.progress_pct}%` }} />
            </span>
          )}
        </span>
      </Link>
      <button
        type="button"
        className="icon-btn video-row-trash"
        aria-label={`${v.title} 분석 결과 삭제`}
        data-el={el("6.8")}
        onClick={onDelete}
      >
        <TrashIcon />
      </button>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const settings = useSettings();
  const [videos, dropVideo] = useVideos();
  const [inbox, reloadInbox] = useInbox();
  const analyzeButton = useRef<HTMLButtonElement>(null);
  const listTitle = useRef<HTMLHeadingElement>(null);
  // 휴지통으로 연 영상(UI-6)과, 지운 뒤 초점을 둘 곳(행 id 또는 5.1)
  const [deleting, setDeleting] = useState<VideoSummary | null>(null);
  const focusAfter = useRef<number | "title" | null>(null);
  const fileButton = useRef<HTMLButtonElement>(null);
  const [url, setUrl] = useState("");
  const [picked, setPicked] = useState<string | null>(null);
  // 대기 표시를 단 버튼 — 그동안은 3.3 · 4.6 어느 쪽도 새 요청을 보내지 않는다(UI-1 규칙)
  const [busy, setBusy] = useState<"url" | "file" | null>(null);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [opened, setOpened] = useState<{
    video: Video;
    estimate: EstimateData;
    othersRunning: boolean;
  } | null>(null);
  const [cannot, setCannot] = useState<BlockedInfo | null>(null);
  // 올리기 — 올리는 중(4.11) · 한 줄(4.17) · 창에 파일을 끌고 들어왔다(덮개 8)
  const [sending, setSending] = useState<Sending | null>(null);
  const [line, setLine] = useState<Line | null>(null);
  const [dragging, setDragging] = useState(false);
  const picker = useRef<HTMLInputElement>(null);
  const stopSending = useRef<(() => void) | null>(null);
  // 처음 열면 맨 위 파일이 골라져 있다(UI-1 규칙)
  const chosen = picked ?? inbox?.files[0]?.name ?? null;
  const inboxEmpty = inbox !== null && inbox.files.length === 0;
  // 키를 받기 전에는 막지 않는다 — 받은 뒤 막힘이 정해진다
  const blocked = settings ? keyBlocks(settings.key) : false;
  const noKey = settings?.key.state === "missing";

  // 막힌 분석 버튼은 형식 검사 · 정보 확인 없이 설정으로 간다(공통 1.8)
  function toSettingsIfBlocked() {
    if (blocked) router.push("/settings");
  }

  /** 등록 응답으로 갈 곳 — registered는 UI-2, analyzed는 UI-4와 짧은 알림, 그 밖은 UI-3. */
  function route(res: RegisterResponse) {
    const v = res.video;
    if (v.status === "registered" && res.estimate) {
      // 대기 안내(6.1)는 열 때의 목록으로 정한다(UI-2 규칙)
      setOpened({
        video: v,
        estimate: res.estimate,
        othersRunning: (videos ?? []).some(inProgress),
      });
    } else if (v.status === "analyzed") {
      flash("이미 분석한 영상입니다");
      router.push(`/videos/${v.id}`);
    } else {
      router.push(`/videos/${v.id}/progress`);
    }
  }

  // UI-4에서 지우고 왔으면 「분석한 영상」 제목에 초점(UI-6 규칙, 사용자 결정 2026-09-28)
  useEffect(() => {
    if (takeListFocus()) listTitle.current?.focus();
  }, []);

  // 지운 뒤 — 연 휴지통이 없어졌으므로 바로 아래 행 → 바로 위 행 → 5.1(UI-1 규칙). 행이 빠진 목록이
  // 그려진 뒤에 옮긴다
  useEffect(() => {
    const target = focusAfter.current;
    if (target === null) return;
    focusAfter.current = null;
    const link =
      target === "title"
        ? null
        : document.querySelector<HTMLElement>(`[data-video="${target}"] .video-row-link`);
    (link ?? listTitle.current)?.focus();
  }, [videos]);

  function deleted(id: number) {
    // 이웃은 지금 그려진 목록에서 — 지우는 사이(도는 작업 멈추기) 목록을 다시 받았을 수 있다
    const node = document.querySelector<HTMLElement>(`[data-video="${id}"]`);
    const next = (node?.nextElementSibling ?? node?.previousElementSibling) as HTMLElement | null;
    focusAfter.current = next?.dataset.video ? Number(next.dataset.video) : "title";
    setDeleting(null);
    dropVideo(id);
  }

  function keyFailed(e: unknown): boolean {
    const failed = e instanceof ApiError && (e.kind === "key-missing" || e.kind === "key-invalid");
    if (failed) void loadSettings(); // 누를 때 확인에 실패했으면 배너가 뜬다
    return failed;
  }

  /** 놓거나 고른 파일 — 보내기 전에 거르고, 한 파일이면 올린다(UI-1 규칙). */
  async function send(files: File[]) {
    // 막혔으면 올리지 않는다 · 올리는 동안은 새 요청이 없다 · 다이얼로그가 떠 있으면 뒤 화면은 받지 않는다
    if (blocked || busy || sending || opened || deleting || cannot) return;
    setLine(null);
    if (files.length === 0) return;
    if (files.length > 1) {
      return setLine({
        text: `한 번에 한 파일씩 올려 주세요 — 파일 ${files.length}개를 놓았어요`,
        alert: true,
      });
    }
    const file = files[0];
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!file.name.includes(".") || !ACCEPTED.includes(ext)) {
      return setLine({
        text: `${ACCEPTED.join(" · ")} 파일만 받아요 — ${file.name}는 올리지 않았어요`,
        alert: true,
      });
    }
    const { done, abort } = api.upload(file, (sent) => setSending((s) => s && { ...s, sent }));
    stopSending.current = abort;
    guardLeave(abort); // 떠나기를 고르면 이것으로 멈춘다
    setSending({ file, sent: 0, abort });
    try {
      route(await done);
    } catch (e) {
      if (e instanceof UploadAborted) {
        setLine({ text: "올리기를 멈췄어요 — 올라간 부분은 지웠어요", alert: false });
      } else if (keyFailed(e)) {
        // 배너가 뜨고 4.7이 막힌 모양이 된다
      } else if (e instanceof ApiError && e.kind === "no-space") {
        const needed = Number(e.body.needed_bytes);
        const free = Number(e.body.free_bytes);
        setLine({
          text: `올릴 자리가 모자라요 — ${sizeLabel(needed)}가 필요한데 앱 폴더에 ${sizeLabel(free)} 남았어요`,
          alert: true,
        });
      } else if (e instanceof ApiError && CANNOT.includes(e.kind)) {
        setCannot(blockedOf(e, "file")); // 올린 뒤에야 안 것 — 사본은 서버가 이미 지웠다
      } else {
        setLine({
          text: `올리지 못했어요 — ${reasonOf(e)}. 올라간 부분은 지웠어요`,
          alert: true,
          retry: file,
        });
      }
    } finally {
      stopSending.current = null;
      guardLeave(null);
      setSending(null);
    }
  }

  // 다른 화면으로 가면 올리기를 멈춘다 — 앱 안 링크는 떠나기 전에 묻지만(leave.ts), 브라우저 뒤로
  // 가기는 묻지 못한다(UI-1 규칙)
  useEffect(
    () => () => {
      stopSending.current?.();
      guardLeave(null);
    },
    [],
  );

  // 올리는 동안 새로 고침 · 창 닫기 · 주소 바꾸기는 브라우저가 먼저 묻는다(UI-1 규칙)
  const uploading = sending !== null;
  useEffect(() => {
    if (!uploading) return;
    const ask = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", ask);
    return () => window.removeEventListener("beforeunload", ask);
  }, [uploading]);

  // 끌어 놓기 — 창 어디에 놓아도 같다. 파일을 끌 때만 덮개(8)를 띄우고, 브라우저가 파일을 열어
  // 버리지 않게 페이지 전체에서 놓기를 받는다(UI-1 규칙)
  const dropped = useEffectEvent((files: File[]) => void send(files));
  useEffect(() => {
    let depth = 0; // 창 안 요소를 오갈 때마다 들어옴 · 나감이 온다 — 0이면 창 밖으로 나갔다
    const isFiles = (e: DragEvent) => e.dataTransfer?.types.includes("Files") ?? false;
    const enter = (e: DragEvent) => {
      if (!isFiles(e)) return;
      e.preventDefault();
      depth += 1;
      setDragging(true);
    };
    const over = (e: DragEvent) => {
      if (isFiles(e)) e.preventDefault();
    };
    const leave = (e: DragEvent) => {
      if (!isFiles(e)) return;
      depth = Math.max(0, depth - 1);
      if (depth === 0) setDragging(false);
    };
    const drop = (e: DragEvent) => {
      if (!isFiles(e)) return;
      e.preventDefault();
      depth = 0;
      setDragging(false);
      dropped([...(e.dataTransfer?.files ?? [])]);
    };
    window.addEventListener("dragenter", enter);
    window.addEventListener("dragover", over);
    window.addEventListener("dragleave", leave);
    window.addEventListener("drop", drop);
    return () => {
      window.removeEventListener("dragenter", enter);
      window.removeEventListener("dragover", over);
      window.removeEventListener("dragleave", leave);
      window.removeEventListener("drop", drop);
    };
  }, []);

  /** 4.10 — 막혔으면 설정으로, 아니면 브라우저의 파일 고르기 창(받는 확장자만) */
  function pick() {
    if (blocked) return toSettingsIfBlocked();
    picker.current?.click();
  }

  async function analyze() {
    if (blocked) return toSettingsIfBlocked();
    if (busy || sending) return; // 대기 표시 · 올리는 중에는 새 요청을 보내지 않는다
    setLine(null);
    if (!url.trim()) return setUrlError(URL_HINT); // 빈 칸은 서버에 묻지 않는다 — 키 확인도 없이
    // 입력칸에서 Enter로 눌렀어도 연 버튼은 3.3 — 다이얼로그가 닫히면 초점이 여기로 돌아온다(공통 1.2)
    analyzeButton.current?.focus();
    setBusy("url");
    setUrlError(null);
    try {
      route(await api.register(url));
    } catch (e) {
      // 3.4는 형식 전용 · 키 오류는 배너만 · 그 밖은 시작 불가 판(UI-1 규칙)
      if (e instanceof ApiError && e.kind === "url-invalid") setUrlError(URL_HINT);
      else if (!keyFailed(e)) setCannot(blockedOf(e, "url"));
    } finally {
      setBusy(null);
    }
  }

  async function analyzeFile() {
    if (blocked) return toSettingsIfBlocked();
    if (busy || sending || !chosen) return; // 빈 inbox — 요청을 보내지 않고 화면도 그대로
    setLine(null);
    setBusy("file");
    try {
      route(await api.registerLocal(chosen));
    } catch (e) {
      if (keyFailed(e)) return; // 배너만
      setCannot(blockedOf(e, "file"));
      if (e instanceof ApiError && e.kind === "not-found") {
        // inbox에서 사라진 파일 — 목록을 다시 받고 처음 열 때처럼 맨 위를 고른다. 고른 이름을 남겨
        // 두면 같은 이름의 파일이 돌아왔을 때 누르지 않은 파일로 옮겨 간다(UI-1 규칙)
        setPicked(null);
        reloadInbox();
      }
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="home">
      <section aria-labelledby="home-title" className="home-intro">
        <div className="home-heading" data-el="2">
          <h1 id="home-title" className="page-title" data-el="2.1">
            어떤 영상을 읽어 볼까요?
          </h1>
          <p className="page-lead" data-el="2.2">
            YouTube 링크를 붙여 넣거나, 영상 파일을 끌어 놓거나 inbox 폴더에서 고르세요. 분석 결과는
            이 PC에만 저장됩니다.
          </p>
        </div>
        <div className="home-cards">
          <div className="card home-card home-card-yt" data-el="3">
            <div className="card-head" data-el="3.1">
              <span className="icon-tile icon-tile-teal">
                <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
              </span>
              <div className="card-head-text">
                <span className="card-head-title">YouTube 링크</span>
                <span className="card-head-sub">watch · youtu.be · shorts 주소를 받아요</span>
              </div>
            </div>
            <form
              className="field"
              onSubmit={(e) => {
                e.preventDefault();
                void analyze();
              }}
            >
              <label htmlFor="yt-url" className="field-label">
                영상 주소
              </label>
              <div className="field-row">
                <span className="field-wrap" data-el="3.2">
                  <input
                    id="yt-url"
                    type="url"
                    className="field-input"
                    placeholder="https://www.youtube.com/watch?v=…"
                    value={url}
                    aria-invalid={urlError ? "true" : undefined}
                    aria-describedby={urlError ? "yt-url-error" : undefined}
                    onChange={(e) => {
                      setUrl(e.target.value);
                      setUrlError(null); // 주소를 고치면 오류를 지운다
                    }}
                  />
                </span>
                <Button
                  ref={analyzeButton}
                  kind="primary"
                  tall
                  blocked={blocked}
                  busy={busy === "url"}
                  el="3.3"
                  onClick={() => void analyze()}
                >
                  분석
                </Button>
              </div>
              {urlError && (
                <p id="yt-url-error" className="field-error" data-el="3.4">
                  {urlError}
                </p>
              )}
            </form>
            <p className="field-help" data-el="3.5">
              자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.
            </p>
          </div>

          <div className="card home-card home-card-files" data-el="4">
            <div className="card-head" data-el="4.1">
              <span className="icon-tile">
                <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
                </svg>
              </span>
              <div className="card-head-text">
                <span className="card-head-title">내 파일</span>
                <span className="card-head-sub">끌어 놓거나 inbox 폴더에서 골라요</span>
              </div>
            </div>
            {sending ? (
              <SendingBox sending={sending} onStop={() => sending.abort()} />
            ) : (
              <div
                className={`drop-zone${blocked ? " is-blocked" : dragging ? " is-over" : ""}`}
                data-el="4.7"
              >
                <span className="drop-icon">
                  <UploadIcon />
                </span>
                <span className="drop-text">
                  <span className="drop-title" data-el="4.8">
                    {blocked
                      ? "OpenAI API 키를 넣은 뒤 올릴 수 있어요"
                      : "파일을 여기로 끌어 놓으세요"}
                  </span>
                  <span className="drop-help" data-el="4.9">
                    {KINDS} · 한 번에 한 파일 · 3시간까지
                  </span>
                </span>
                <Button kind="secondary" blocked={blocked} el="4.10" onClick={pick}>
                  <svg
                    className="icon"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <path d="M14 2v6h6" />
                  </svg>
                  파일 고르기
                </Button>
                <input
                  ref={picker}
                  type="file"
                  hidden
                  accept={ACCEPTED.map((x) => `.${x}`).join(",")}
                  onChange={(e) => {
                    const files = [...(e.target.files ?? [])];
                    e.target.value = ""; // 같은 파일을 다시 골라도 알게
                    void send(files);
                  }}
                />
              </div>
            )}
            {line && (
              <div
                className={`upload-line${line.alert ? " is-error" : ""}`}
                role={line.alert ? "alert" : "status"}
                data-el="4.17"
              >
                <LineIcon alert={line.alert} />
                <span className="upload-line-text">{line.text}</span>
                {line.retry && (
                  <Button
                    kind="secondary"
                    className="btn-small"
                    el="4.18"
                    onClick={() => line.retry && void send([line.retry])}
                  >
                    다시 올리기
                  </Button>
                )}
              </div>
            )}
            <div className="inbox-divider" data-el="4.19">
              <span className="inbox-divider-line" />
              <span className="caption">또는 inbox 폴더에서 고르기</span>
              <span className="inbox-divider-path mono">{settings?.inbox_path}</span>
              <span className="inbox-divider-line" />
            </div>
            <div role="group" aria-label="inbox 파일" className="home-files" data-el="4.2">
              {inbox?.files.map((f, i) => {
                const on = f.name === chosen;
                return (
                  <button
                    key={f.name}
                    type="button"
                    className={`file-row${on ? " is-picked" : ""}`}
                    aria-pressed={on}
                    data-el={i === 0 ? "4.3" : undefined}
                    onClick={() => setPicked(f.name)}
                  >
                    <span className="file-radio" aria-hidden="true">
                      <span className="file-radio-dot" />
                    </span>
                    <span className="file-name">{f.name}</span>
                    <span className="file-length mono">
                      {f.duration_sec === null ? "—" : durationLabel(f.duration_sec)}
                    </span>
                    <span className="file-size">{sizeLabel(f.size_bytes)}</span>
                  </button>
                );
              })}
              {inboxEmpty && (
                <p id="inbox-empty" className="file-empty" data-el="4.4">
                  inbox 폴더에 파일이 없어요
                </p>
              )}
            </div>
            <div className="home-files-foot">
              <span className="caption" data-el="4.5">
                inbox 파일은 복사하지 않고 읽기만 해요
              </span>
              <Button
                ref={fileButton}
                kind="primary"
                className="btn-wide"
                blocked={blocked || inboxEmpty}
                busy={busy === "file"}
                aria-describedby={!blocked && inboxEmpty ? "inbox-empty" : undefined}
                el="4.6"
                onClick={() => void analyzeFile()}
              >
                선택한 파일 분석
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section aria-labelledby="list-title" className="home-list">
        <div className="home-list-head" data-el="5">
          <div className="home-list-title">
            <h2
              id="list-title"
              ref={listTitle}
              tabIndex={-1}
              className="section-title"
              data-el="5.1"
            >
              분석한 영상
            </h2>
            <span className="home-list-count" data-el="5.2">
              {videos === null ? "" : `${videos.length}개`}
            </span>
          </div>
          <span className="caption" data-el="5.3">
            최근 순
          </span>
        </div>
        {videos !== null && videos.length > 0 && (
          <div className="video-list" data-el="6">
            {videos.map((v, i) => (
              <VideoRow key={v.id} v={v} first={i === 0} onDelete={() => setDeleting(v)} />
            ))}
          </div>
        )}
        {videos !== null && videos.length === 0 && (
          <EmptyBox
            title={EMPTY_TITLE}
            body={noKey ? EMPTY_BODY_NO_KEY : EMPTY_BODY}
            el="7"
            elTitle="7.1"
            elBody="7.2"
          />
        )}
      </section>

      {opened && (
        <Estimate
          video={opened.video}
          estimate={opened.estimate}
          othersRunning={opened.othersRunning}
          onClose={(discarded) => {
            setOpened(null);
            // 올린 파일 판에서 취소했다 — 서버가 사본을 지웠다(UI-1 4.17 알림)
            if (discarded)
              setLine({ text: "분석을 취소했어요 — 올린 사본을 지웠어요", alert: false });
          }}
        />
      )}
      {deleting && (
        <Delete
          video={deleting}
          turns={deleting.chat_turn_count}
          onClose={() => setDeleting(null)}
          onDeleted={() => deleted(deleting.id)}
        />
      )}
      {cannot && (
        <Blocked
          reason={cannot.reason}
          durationSec={cannot.durationSec}
          onClose={() => setCannot(null)}
        />
      )}
      {dragging && !blocked && !sending && !opened && !deleting && !cannot && (
        <div className="drop-overlay" data-el="8">
          <div className="drop-overlay-box" data-el="8.1">
            <span className="drop-overlay-icon">
              <UploadIcon size={28} />
            </span>
            <span className="drop-overlay-title" data-el="8.2">
              놓으면 이 파일을 올려 분석해요
            </span>
            <span className="drop-overlay-sub" data-el="8.3">
              한 번에 한 파일 · {KINDS}
            </span>
            <span className="drop-overlay-note" data-el="8.4">
              파일은 이 PC 안의 앱 폴더로 복사될 뿐 밖으로 나가지 않아요
            </span>
          </div>
        </div>
      )}
    </main>
  );
}
