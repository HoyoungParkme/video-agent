/**
 * VA-UI-002#UI-3 분석 진행 — 1 뒤로 링크 · 2 영상 머리(2.1 ~ 2.3) · 3 진행 카드(3.1 헤드라인 · 3.2 부제 ·
 * 3.3 퍼센트 · 3.4 막대) · 4 단계 목록(4.1 행 · 4.2 표시 · 4.3 이름 · 4.4 메모 · 4.5 연결선 ·
 * 받아쓰기 행 아래 4.6 조각 격자 · 4.7 조각 칸 · 4.8 범례) · 5 실패 알림(5.1 제목 · 5.2 본문 ·
 * 5.3 목록으로 · 5.4 다시 시도) · 6 카드 아래 줄(6.1 전송 표시 · 6.2 떠나기 안내).
 * 1초마다 진행을 새로 받는다. 끝나면 UI-4로(방문 기록을 바꿔치기), 작업 · 영상이 없으면 UI-1로.
 * 서버에 잠깐 닿지 못하면 영상 정보도 진행도 1초 뒤 다시 받는다 — 빈 화면으로 멈추지 않게.
 * 대기 상태도 같은 화면이다. 화면은 계산하지 않는다 — 서버 값을 그대로 쓴다. 실패하면 폴링을 멈추고,
 * 다시 시도(5.4)가 받아 주면 실패 알림을 지우고 다시 폴링한다.
 */
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  api,
  ApiError,
  keyBlocks,
  loadSettings,
  useSettings,
  type Chunks,
  type ErrorKind,
  type Job,
  type JobStage,
  type Video,
} from "@/api/client";
import { Button } from "@/components/buttons";
import { durationLabel } from "@/components/TimeChip";
import { stageName } from "@/labels";

const POLL_MS = 1000;
// 스크립트를 보내는 단계 — 결과 화면이 곧 열린다(6.2)
const TEXT_STAGES: JobStage[] = ["summarize", "chapter", "suggest"];
// 실패 알림 제목(5.1) — 실패 종류로(UI-3 규칙)
const FAILURE_TITLES: Record<ErrorKind, string> = {
  network: "OpenAI API에 연결하지 못했어요",
  openai: "OpenAI가 요청을 처리하지 못했어요",
  youtube: "YouTube에서 받아 오지 못했어요",
  ffmpeg: "음성을 처리하지 못했어요",
  disk: "저장 공간이 부족해요",
  unknown: "예상하지 못한 문제로 멈췄어요",
};

/** 지금 하는 일(3.1). 보드에 없는 단계도 같은 말투로(UI-3 규칙). */
function doing(stage: JobStage, hasCaptions: boolean, splitting: boolean): string {
  switch (stage) {
    case "download":
      return hasCaptions ? "자막을 가져오는 중" : "음성을 내려받는 중";
    case "extract":
      return "음성을 추출하는 중";
    case "transcribe":
      return splitting ? "음성을 조각으로 나누는 중" : "받아쓰기 중";
    case "summarize":
      return "핵심 요약을 만드는 중";
    case "chapter":
      return "챕터를 만드는 중";
    default:
      return "추천 질문을 만드는 중";
  }
}

/** 남은 시간 — 1분 미만은 '약 {s}초', 이상은 '약 {t}분'. 0이나 없으면 비운다. */
function remaining(sec: number | null): string | null {
  if (!sec) return null;
  return sec < 60 ? `약 ${sec}초` : `약 ${Math.ceil(sec / 60)}분`;
}

/** 걸린 시간 메모(4.4) — '18초' · '1분 5초'. */
function took(sec: number): string {
  if (sec < 60) return `${sec}초`;
  const rest = sec % 60;
  return rest ? `${Math.floor(sec / 60)}분 ${rest}초` : `${Math.floor(sec / 60)}분`;
}

/** 서버가 준 이유 한 줄 — 끝의 마침표는 틀이 붙이므로 뗀다. */
function reasonOf(job: Job): string {
  return (job.error?.reason ?? "").replace(/[.。]\s*$/, "");
}

type StepState = "done" | "active" | "failed" | "waiting";

function StepMark({ state }: { state: StepState }) {
  if (state === "done" || state === "failed") {
    return (
      <span className={`step-mark is-${state}`} data-state={state}>
        <svg
          className="icon icon-bold"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          {state === "done" ? (
            <path d="M20 6 9 17l-5-5" />
          ) : (
            <>
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </>
          )}
        </svg>
      </span>
    );
  }
  return (
    <span
      className={`step-mark is-${state}${state === "active" ? " va-pulse" : ""}`}
      data-state={state}
    >
      {state === "active" && <span className="step-dot" />}
    </span>
  );
}

const CELL_NAMES = { done: "완료", in_flight: "받아쓰는 중", failed: "실패", waiting: "대기" };

/** 조각 격자(4.6) · 칸(4.7) · 범례(4.8) — 받아쓰기 행 아래. 범례는 칸이 있는 상태만. */
function ChunkGrid({ chunks }: { chunks: Chunks }) {
  const counts = {
    done: chunks.done,
    in_flight: chunks.in_flight,
    failed: chunks.failed,
    waiting: chunks.waiting,
  };
  let label = `조각 ${chunks.total}개 중 ${chunks.done}개 완료`;
  if (chunks.in_flight) label += `, ${chunks.in_flight}개 받아쓰는 중`;
  if (chunks.failed) label += `, ${chunks.failed}개 실패`;
  return (
    <span className="chunk-box">
      <span role="img" aria-label={label} className="chunk-grid" data-el="4.6">
        {chunks.items.map((c, i) => (
          <span
            key={c.seq}
            className={`chunk-cell is-${c.state}${c.state === "in_flight" ? " va-pulse" : ""}`}
            data-el={i === 0 ? "4.7" : undefined}
          />
        ))}
      </span>
      <span className="chunk-legend" data-el="4.8">
        {(Object.keys(counts) as (keyof typeof counts)[])
          .filter((k) => counts[k] > 0)
          .map((k) => (
            <span key={k} className="chunk-legend-item">
              <span className={`chunk-swatch is-${k}`} />
              {CELL_NAMES[k]} {counts[k]}
            </span>
          ))}
      </span>
    </span>
  );
}

export default function Progress({ id }: { id: number }) {
  const router = useRouter();
  const settings = useSettings();
  const [video, setVideo] = useState<Video | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [retrying, setRetrying] = useState(false);
  // 다시 시도가 받아 주면 늘린다 — 멈췄던 폴링을 다시 돌린다
  const [round, setRound] = useState(0);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let videoTimer: ReturnType<typeof setTimeout> | undefined;
    const gone = (e: unknown) => e instanceof ApiError && (e.status === 404 || e.status === 422);
    const loadVideo = async () => {
      try {
        const detail = await api.video(id);
        if (alive) setVideo(detail.video);
      } catch (e) {
        if (!alive) return;
        if (gone(e)) {
          router.replace("/"); // 영상이 없으면 UI-1로
        } else {
          videoTimer = setTimeout(loadVideo, POLL_MS); // 잠깐 닿지 못하면 다시
        }
      }
    };
    void loadVideo();
    const poll = async () => {
      try {
        const next = await api.job(id);
        if (!alive) return;
        if (next.status === "done") {
          router.replace(`/videos/${id}`); // 끝나면 결과로 — 뒤로 가기가 이 화면으로 오지 않게
          return;
        }
        setJob(next);
        if (next.status === "queued" || next.status === "running")
          timer = setTimeout(poll, POLL_MS);
      } catch (e) {
        if (!alive) return;
        if (gone(e)) {
          router.replace("/"); // 작업이 없는 영상
          return;
        }
        timer = setTimeout(poll, POLL_MS); // 잠깐 닿지 못하면 다시
      }
    };
    void poll();
    return () => {
      alive = false;
      clearTimeout(timer);
      clearTimeout(videoTimer);
    };
  }, [id, router, round]);

  if (!video || !job) return <main className="progress" aria-busy="true" />;

  const queued = job.status === "queued";
  const failed = job.status === "failed";
  // pending은 첫 단계가 진행 중인 모습 — 대기면 대기 상태
  const current: JobStage = job.stage === "pending" ? job.stages[0] : job.stage;
  const at = queued ? -1 : job.stages.indexOf(current);
  const stepState = (i: number): StepState => {
    if (queued || i > at) return "waiting";
    if (i < at) return "done";
    return failed ? "failed" : "active";
  };
  const name = stageName(current, video.has_captions);
  const chunks = job.chunks;
  const transcribing = !queued && current === "transcribe";
  const splitting = transcribing && !chunks; // 받아쓰기에 들어갔지만 조각이 아직 없다
  const k = job.error?.chunk_seq ?? null;
  const saved = chunks?.done ? ` · 완료한 ${chunks.done}개는 저장됨` : "";

  let headline: string;
  let sub: string;
  if (queued) {
    headline = "차례를 기다리는 중";
    sub = `앞 영상 ${job.queue_position}개가 끝나면 시작해요`;
  } else if (failed) {
    headline = transcribing ? "받아쓰기가 멈췄어요" : `${name} 단계가 멈췄어요`;
    if (transcribing && chunks && k !== null) {
      sub = `조각 ${k} / ${chunks.total}에서 실패${saved}`;
    } else {
      sub = `${job.stages.length}단계 중 ${job.stage_index}단계에서 실패`;
      if (transcribing) sub += saved;
      if (TEXT_STAGES.includes(current)) sub += " · 스크립트는 저장됨";
    }
  } else {
    headline = doing(current, video.has_captions, splitting);
    const left = remaining(job.remaining_sec);
    const tail = left ? ` · 남은 시간 ${left}` : "";
    sub =
      transcribing && chunks
        ? `조각 ${chunks.done} / ${chunks.total}${tail}`
        : `${job.stages.length}단계 중 ${job.stage_index}단계${tail}`;
  }

  let transfer = "아직 OpenAI로 보내는 것이 없어요";
  if (transcribing && chunks) {
    transfer =
      `음성 조각 → OpenAI ${job.models.stt}` + (failed ? "" : ` · 동시 ${job.concurrency}개`);
  } else if (!queued && TEXT_STAGES.includes(current)) {
    transfer = `스크립트 텍스트 → OpenAI ${job.models.text}`;
  }

  // 다시 시도가 시작할 곳 — 받아쓰기는 완료하지 않은 첫 조각(r), 그 밖은 멈춘 단계
  const r = transcribing && chunks ? chunks.next_seq : null;
  const from = r !== null ? `${r}번째 조각` : name;
  let leave = "이 화면을 닫아도 분석은 계속돼요.";
  if (queued) leave = "이 화면을 닫아도 차례가 되면 시작돼요.";
  else if (failed)
    leave =
      r !== null
        ? `다시 시도하면 ${r}번째 조각부터 이어서 받아씁니다.`
        : `다시 시도하면 ${name}부터 이어서 합니다.`;
  else if (TEXT_STAGES.includes(current))
    leave = "끝나면 결과 화면이 바로 열려요. 닫아도 분석은 계속됩니다.";

  let body = "";
  if (failed && job.error) {
    const why = reasonOf(job);
    const kept = chunks?.done
      ? ` 완료한 ${chunks.done}개 조각은 저장돼 있어 처음부터 다시 받아쓰지 않아요.`
      : "";
    if (transcribing && k !== null) {
      body = `${k}번째 조각을 ${job.error.attempts}번 보냈지만 실패했어요 — ${why}.${kept}`;
    } else if (transcribing) {
      body = `받아쓰기 중에 멈췄어요 — ${why}.${kept}`;
    } else if (TEXT_STAGES.includes(current)) {
      body = `${name} 단계에서 멈췄어요 — ${why}. 스크립트는 저장돼 있어 처음부터 다시 하지 않아요.`;
    } else {
      body = `${name} 단계에서 멈췄어요 — ${why}.`;
    }
  }

  const blocked = settings ? keyBlocks(settings.key) : false;
  async function retry() {
    if (blocked) {
      router.push("/settings"); // 키가 없으면 UI-5(공통 1.8)
      return;
    }
    if (retrying) return;
    setRetrying(true);
    try {
      setJob(await api.retry(id)); // 실패 알림이 사라지고 진행 · 대기 상태로
      setRound((n) => n + 1);
    } catch (e) {
      if (e instanceof ApiError && (e.kind === "key-missing" || e.kind === "key-invalid")) {
        void loadSettings(); // 누를 때 확인에 실패했으면 배너가 뜬다
      }
    } finally {
      setRetrying(false);
    }
  }

  return (
    <main className="progress">
      <Link href="/" className="back-link" data-el="1">
        <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
          <path d="m12 19-7-7 7-7" />
          <path d="M19 12H5" />
        </svg>
        분석한 영상
      </Link>

      <div className="progress-video" data-el="2">
        <span className="icon-tile icon-tile-lg" data-el="2.1">
          {video.source_kind === "youtube" ? (
            <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
            </svg>
          ) : (
            <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M7 3v18" />
              <path d="M17 3v18" />
              <path d="M3 12h18" />
            </svg>
          )}
        </span>
        <div className="progress-video-text">
          <span className="progress-video-title" data-el="2.2">
            {video.title}
          </span>
          <span className="progress-video-sub" data-el="2.3">
            {video.source_kind === "youtube" ? "YouTube" : "로컬 파일"} ·{" "}
            {durationLabel(video.duration_sec)} · {video.has_captions ? "자막 있음" : "자막 없음"}
          </span>
        </div>
      </div>

      <section
        className={`card progress-card${failed ? " is-failed" : ""}`}
        aria-live="polite"
        data-el="3"
      >
        <div className="progress-top">
          <div className="progress-heading">
            <h1 className="progress-headline" data-el="3.1">
              {headline}
            </h1>
            <span className="progress-sub" data-el="3.2">
              {sub}
            </span>
          </div>
          <span className="progress-pct mono" data-el="3.3">
            {job.progress_pct}%
          </span>
        </div>
        <div className="progress-bar" data-el="3.4">
          <div className="progress-bar-fill" style={{ width: `${job.progress_pct}%` }} />
        </div>
        <ol className="steps" data-el="4">
          {job.stages.map((stage, i) => {
            const state = stepState(i);
            const counted = stage === "transcribe" && chunks;
            let memo = "—";
            if (state === "done") memo = took(job.stage_durations_sec[stage] ?? 0);
            else if (state === "active")
              memo = counted ? `${chunks.done} / ${chunks.total}` : "진행 중";
            else if (state === "failed")
              memo = counted && k !== null ? `${k} / ${chunks.total}에서 멈춤` : "멈춤";
            const first = i === 0;
            const last = i === job.stages.length - 1;
            return (
              <li key={stage} className={`step is-${state}`} data-el={first ? "4.1" : undefined}>
                <span className="step-rail">
                  <span data-el={first ? "4.2" : undefined}>
                    <StepMark state={state} />
                  </span>
                  {!last && (
                    <span
                      className={`step-line${state === "done" ? " is-done" : ""}`}
                      data-el={first ? "4.5" : undefined}
                    />
                  )}
                </span>
                <span className="step-body">
                  <span className="step-top">
                    <span className="step-name" data-el={first ? "4.3" : undefined}>
                      {stageName(stage, video.has_captions)}
                    </span>
                    <span className="step-memo mono" data-el={first ? "4.4" : undefined}>
                      {memo}
                    </span>
                  </span>
                  {counted && state !== "waiting" && <ChunkGrid chunks={chunks} />}
                </span>
              </li>
            );
          })}
        </ol>
        {failed && job.error && (
          <div role="alert" className="failure" data-el="5">
            <div className="failure-text">
              <svg
                className="icon failure-icon"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4" />
                <path d="M12 16h.01" />
              </svg>
              <span className="failure-words">
                <span className="failure-title" data-el="5.1">
                  {FAILURE_TITLES[job.error.kind]}
                </span>
                <span className="failure-body" data-el="5.2">
                  {body}
                </span>
              </span>
            </div>
            <div className="failure-actions">
              <Button kind="secondary" el="5.3" onClick={() => router.push("/")}>
                목록으로
              </Button>
              <Button
                kind="primary"
                el="5.4"
                blocked={blocked}
                busy={retrying}
                onClick={() => void retry()}
              >
                <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
                  <path d="M21 3v5h-5" />
                </svg>
                {from}부터 다시 시도
              </Button>
            </div>
          </div>
        )}
      </section>

      <div className="progress-foot" data-el="6">
        <span className="progress-transfer" data-el="6.1">
          <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 7h10v10" />
            <path d="M7 17 17 7" />
          </svg>
          {transfer}
        </span>
        <span data-el="6.2">{leave}</span>
      </div>
    </main>
  );
}
