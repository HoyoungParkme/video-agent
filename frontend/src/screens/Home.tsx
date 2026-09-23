/**
 * VA-UI-002#UI-1 홈 — 2 제목 영역 · 3 YouTube 링크 카드(3.1 · 3.2 · 3.3 분석 · 3.4 · 3.5) · 4 내 파일 카드
 * (4.1 · 4.2 · 4.5 · 4.6) · 5 목록 머리(5.1 · 5.2 · 5.3) · 6 분석한 영상 목록(6.1 ~ 6.7) · 7 빈 상태 상자.
 * 키 없음 배너(1)는 layout의 공통 1.4다. 분석(3.3)은 등록 응답의 status로 갈 곳을 정한다 —
 * registered면 UI-2, analyzed면 UI-4와 짧은 알림, 그 밖은 UI-3.
 * B1이 채우지 않은 것: 3.4는 서버 문구 한 줄뿐(종류별 판 가르기는 B5) · inbox 파일 행(4.3 · 4.4)과 4.6의 동작은 B2 ·
 * 실패 행의 모양은 B2 · 행 휴지통(6.8)은 B4.
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
  type RegisterResponse,
  type VideoSummary,
} from "@/api/client";
import { Button } from "@/components/buttons";
import EmptyBox from "@/components/EmptyBox";
import { durationLabel } from "@/components/TimeChip";
import { flash } from "@/components/Toast";
import { analyzedLabel, stageName } from "@/labels";
import Estimate from "@/screens/Estimate";

const EMPTY_TITLE = "아직 분석한 영상이 없어요";
const EMPTY_BODY = "위에 링크를 붙여 넣거나 inbox 폴더에 파일을 넣어 보세요.";
const EMPTY_BODY_NO_KEY = `설정에서 OpenAI API 키를 넣은 뒤, ${EMPTY_BODY}`;
// 진행 중 · 대기 중 행이 있는 동안만 목록을 다시 받는다(UI-1 규칙)
const REFRESH_MS = 3000;

function inProgress(v: VideoSummary): boolean {
  return v.job.status === "queued" || v.job.status === "running";
}

/** 분석한 영상 목록. 진행 중 · 대기 중 행이 있으면 3초마다 다시 받는다. 받기 전에는 null. */
function useVideos(): VideoSummary[] | null {
  const [rows, setRows] = useState<VideoSummary[] | null>(null);
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
  }, []);
  return rows;
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

function VideoRow({ v, first }: { v: VideoSummary; first: boolean }) {
  const status = rowStatus(v);
  const href = v.status === "analyzed" ? `/videos/${v.id}` : `/videos/${v.id}/progress`;
  // 요소 번호는 첫 행에만 — 와이어프레임이 한 행에 번호를 매겼다
  const el = (no: string) => (first ? no : undefined);
  return (
    <div className="video-row">
      <Link href={href} className="video-row-link" data-el={el("6.1")}>
        <span className="icon-tile" data-el={el("6.2")}>
          <SourceIcon local={v.source_kind === "local"} />
        </span>
        <span className="video-row-text">
          <span className="video-row-title" data-el={el("6.3")}>
            {v.title}
          </span>
          <span className="video-row-sub" data-el={el("6.4")}>
            {v.source_kind === "youtube" ? `YouTube · ${v.channel ?? ""}` : "로컬 파일"}
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
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const settings = useSettings();
  const videos = useVideos();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [opened, setOpened] = useState<(RegisterResponse & { othersRunning: boolean }) | null>(
    null,
  );
  // 키를 받기 전에는 막지 않는다 — 받은 뒤 막힘이 정해진다
  const blocked = settings ? keyBlocks(settings.key) : false;
  const noKey = settings?.key.state === "missing";

  // 막힌 분석 버튼은 형식 검사 · 정보 확인 없이 설정으로 간다(공통 1.8)
  function toSettingsIfBlocked() {
    if (blocked) router.push("/settings");
  }

  async function analyze() {
    if (blocked) return toSettingsIfBlocked();
    if (busy) return; // 대기 표시 중에는 새 요청을 보내지 않는다
    setBusy(true);
    setUrlError(null);
    try {
      const res = await api.register(url);
      const v = res.video;
      if (v.status === "registered") {
        // 대기 안내(6.1)는 열 때의 목록으로 정한다(UI-2 규칙)
        setOpened({ ...res, othersRunning: (videos ?? []).some(inProgress) });
      } else if (v.status === "analyzed") {
        flash("이미 분석한 영상입니다");
        router.push(`/videos/${v.id}`);
      } else {
        router.push(`/videos/${v.id}/progress`);
      }
    } catch (e) {
      if (e instanceof ApiError && (e.kind === "key-missing" || e.kind === "key-invalid")) {
        void loadSettings(); // 누를 때 확인에 실패했으면 배너가 뜬다
      }
      setUrlError(e instanceof ApiError ? e.reason : "서버에 닿지 못했어요");
    } finally {
      setBusy(false);
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
            YouTube 링크를 붙여 넣거나 inbox 폴더의 파일을 고르세요. 분석 결과는 이 PC에만
            저장됩니다.
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
                  kind="primary"
                  tall
                  blocked={blocked}
                  busy={busy}
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
                <span className="card-head-path">{settings?.inbox_path}</span>
              </div>
            </div>
            {/* inbox 파일 행(4.3)과 빈 안내(4.4)는 B2의 GET /api/inbox로 채운다 */}
            <div role="group" aria-label="inbox 파일" className="home-files" data-el="4.2" />
            <div className="home-files-foot">
              <span className="caption" data-el="4.5">
                mp4 · mkv · mov · webm · mp3 · m4a · wav
              </span>
              <Button
                kind="primary"
                className="btn-wide"
                blocked={blocked}
                el="4.6"
                onClick={toSettingsIfBlocked}
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
            <h2 id="list-title" tabIndex={-1} className="section-title" data-el="5.1">
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
              <VideoRow key={v.id} v={v} first={i === 0} />
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
          onClose={() => setOpened(null)}
        />
      )}
    </main>
  );
}
