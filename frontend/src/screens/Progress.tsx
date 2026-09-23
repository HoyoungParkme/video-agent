/**
 * VA-UI-002#UI-3 분석 진행 — 1 뒤로 링크 · 2 영상 머리(2.1 ~ 2.3) · 3 진행 카드(3.1 헤드라인 · 3.2 부제 ·
 * 3.3 퍼센트 · 3.4 막대) · 4 단계 목록(4.1 행 · 4.2 표시 · 4.3 이름 · 4.4 메모 · 4.5 연결선) ·
 * 6 카드 아래 줄(6.1 전송 표시 · 6.2 떠나기 안내).
 * 1초마다 진행을 새로 받는다. 끝나면 UI-4로(방문 기록을 바꿔치기), 작업 · 영상이 없으면 UI-1로.
 * 서버에 잠깐 닿지 못하면 영상 정보도 진행도 1초 뒤 다시 받는다 — 빈 화면으로 멈추지 않게.
 * 대기 상태도 같은 화면이다. 화면은 계산하지 않는다 — 서버 값을 그대로 쓴다.
 * B1이 채우지 않은 것: 조각 격자와 범례(4.6 ~ 4.8, B2) · 실패 알림 상자와 다시 시도(5, B2).
 * 실패하면 폴링을 멈추고 헤드라인 · 부제 · 단계 표시만 실패 모양으로 바꾼다.
 */
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ApiError, type Job, type JobStage, type Video } from "@/api/client";
import { durationLabel } from "@/components/TimeChip";
import { stageName } from "@/labels";

const POLL_MS = 1000;
// 스크립트를 보내는 단계 — 결과 화면이 곧 열린다(6.2)
const TEXT_STAGES: JobStage[] = ["summarize", "chapter", "suggest"];

/** 지금 하는 일(3.1). 보드에 없는 단계도 같은 말투로(UI-3 규칙). */
function doing(stage: JobStage, hasCaptions: boolean): string {
  switch (stage) {
    case "download":
      return hasCaptions ? "자막을 가져오는 중" : "음성을 내려받는 중";
    case "extract":
      return "음성을 추출하는 중";
    case "transcribe":
      return "받아쓰기 중";
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

export default function Progress({ id }: { id: number }) {
  const router = useRouter();
  const [video, setVideo] = useState<Video | null>(null);
  const [job, setJob] = useState<Job | null>(null);

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
        if (gone(e))
          router.replace("/"); // 영상이 없으면 UI-1로
        else videoTimer = setTimeout(loadVideo, POLL_MS); // 잠깐 닿지 못하면 다시
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
  }, [id, router]);

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

  let headline: string;
  let sub: string;
  if (queued) {
    headline = "차례를 기다리는 중";
    sub = `앞 영상 ${job.queue_position}개가 끝나면 시작해요`;
  } else if (failed) {
    headline = `${name} 단계가 멈췄어요`;
    sub = `${job.stages.length}단계 중 ${job.stage_index}단계에서 실패`;
    if (TEXT_STAGES.includes(current)) sub += " · 스크립트는 저장됨";
  } else {
    headline = doing(current, video.has_captions);
    const left = remaining(job.remaining_sec);
    sub =
      `${job.stages.length}단계 중 ${job.stage_index}단계` + (left ? ` · 남은 시간 ${left}` : "");
  }

  let transfer = "아직 OpenAI로 보내는 것이 없어요";
  if (!queued && current === "transcribe") {
    transfer =
      `음성 조각 → OpenAI ${job.models.stt}` + (failed ? "" : ` · 동시 ${job.concurrency}개`);
  } else if (!queued && TEXT_STAGES.includes(current)) {
    transfer = `스크립트 텍스트 → OpenAI ${job.models.text}`;
  }
  let leave = "이 화면을 닫아도 분석은 계속돼요.";
  if (queued) leave = "이 화면을 닫아도 차례가 되면 시작돼요.";
  else if (TEXT_STAGES.includes(current))
    leave = "끝나면 결과 화면이 바로 열려요. 닫아도 분석은 계속됩니다.";

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
            const memo =
              state === "done"
                ? took(job.stage_durations_sec[stage] ?? 0)
                : state === "active"
                  ? "진행 중"
                  : state === "failed"
                    ? "멈춤"
                    : "—";
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
                  <span className="step-name" data-el={first ? "4.3" : undefined}>
                    {stageName(stage, video.has_captions)}
                  </span>
                  <span className="step-memo mono" data-el={first ? "4.4" : undefined}>
                    {memo}
                  </span>
                </span>
              </li>
            );
          })}
        </ol>
      </section>

      <div className="progress-foot" data-el="6">
        <span className="progress-transfer" data-el="6.1">
          <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 7h10v10" />
            <path d="M7 17 17 7" />
          </svg>
          {transfer}
        </span>
        {!failed && <span data-el="6.2">{leave}</span>}
      </div>
    </main>
  );
}
