/**
 * VA-UI-002#UI-4 16 플레이어 — 오른쪽 패널 맨 위, 탭 위(영상 같이 보기, VA-PRD-001 R14 · VA-INFRA-001 C13).
 * 처음에는 재생 판(16.1) — 첫 챕터 장면 위의 재생 버튼이고, 누르기 전에는 바깥으로 아무것도 보내지 않는다.
 * 누르면 그 자리에서 재생한다: YouTube는 이때 IFrame Player API를 쿠키 없는 호스트로 처음 불러오고(16.4),
 * 로컬 영상 · 음성 파일은 앱이 내보내는 원본(GET …/media)을 <video> · <audio>가 재생한다.
 * 연 뒤에는 결과 화면이 playAt(초)로 그 시각부터 재생시킨다. 재생 위치를 따라 스크립트가 움직이지는 않는다.
 * 접기(16.7)는 멈추고 막대(16.5)만 남긴다 — 플레이어는 그대로 두어 펼치면 멈춘 자리에서 이어 본다.
 * 올린 파일은 재생하지 않고 16.10 한 줄. 재생할 수 없으면 16.8 — 로컬은 원본이 있는지 HEAD로 물어
 * 원본 없음 · 형식을 가르고, YouTube는 오류 번호(101 · 150 퍼가기 막힘)와 API를 불러오지 못한 것을 가른다.
 */
"use client";

import { useEffect, useImperativeHandle, useRef, useState, type Ref } from "react";

import { api, type Video } from "@/api/client";
import { timeLabel } from "@/components/TimeChip";

/** 결과 화면이 시각 누르기로 부른다 — 열려 재생 중이면 그 시각부터. */
export interface PlayerHandle {
  playAt(sec: number): void;
}

// YouTube IFrame Player API — 쓰는 것만(https://developers.google.com/youtube/iframe_api_reference)
interface YTPlayer {
  seekTo(sec: number, allowSeekAhead: boolean): void;
  playVideo(): void;
  pauseVideo(): void;
  getPlayerState(): number;
  destroy(): void;
}
interface YTNamespace {
  Player: new (
    el: HTMLElement,
    opts: {
      host: string;
      videoId: string;
      width: string;
      height: string;
      playerVars: Record<string, number>;
      events: {
        onReady: (e: { target: YTPlayer }) => void;
        onError: (e: { data: number }) => void;
      };
    },
  ) => YTPlayer;
}
declare global {
  interface Window {
    YT?: YTNamespace;
    onYouTubeIframeAPIReady?: () => void;
  }
}

const YT_PLAYING = 1;
let ytApi: Promise<YTNamespace> | null = null;

/** IFrame Player API를 한 번 불러온다 — 재생 판을 처음 누를 때. 못 불러오면 다음에 다시 시도한다. */
function loadYouTube(): Promise<YTNamespace> {
  if (window.YT?.Player) return Promise.resolve(window.YT);
  ytApi ??= new Promise((resolve, reject) => {
    const before = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      before?.();
      if (window.YT) resolve(window.YT);
    };
    const s = document.createElement("script");
    s.src = "https://www.youtube.com/iframe_api";
    s.async = true;
    s.onerror = () => {
      ytApi = null;
      s.remove();
      reject(new Error("YouTube에 연결하지 못함"));
    };
    document.head.appendChild(s);
  });
  return ytApi;
}

type Kind = "youtube" | "video" | "audio" | "uploaded";
type Phase = "facade" | "loading" | "playing" | "failed";
type Failure = "missing" | "format" | "blocked" | "gone" | "offline";

const FAILURES: Record<Failure, { title: string; body: string }> = {
  missing: {
    title: "원본 파일을 찾지 못했어요",
    body: "inbox에서 옮기거나 지웠어요. 같은 이름으로 다시 두면 재생돼요.",
  },
  format: {
    title: "이 브라우저가 재생하지 못하는 형식이에요",
    body: "원본은 그대로예요. 다른 플레이어로 열어 보세요.",
  },
  blocked: {
    title: "이 영상은 YouTube 밖에서 재생할 수 없어요",
    body: "올린 사람이 다른 사이트에서 재생하지 못하게 했어요.",
  },
  gone: {
    title: "YouTube에서 재생하지 못했어요",
    body: "영상이 지워졌거나 비공개일 수 있어요.",
  },
  offline: {
    title: "YouTube에 연결하지 못했어요",
    body: "인터넷이 되면 다시 눌러 주세요.",
  },
};

function kindOf(video: Video): Kind {
  if (video.source_kind === "youtube") return "youtube";
  if (video.uploaded) return "uploaded";
  return /\.(mp3|m4a|wav)$/i.test(video.origin) ? "audio" : "video";
}

function ext(name: string): string {
  return name.slice(name.lastIndexOf(".") + 1).toLowerCase();
}

function VideoIcon() {
  return (
    <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m10 9 5 3-5 3z" />
    </svg>
  );
}

function PlayGlyph({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className="player-glyph" aria-hidden="true">
      <path d="M8 5.5v13l10.5-6.5z" />
    </svg>
  );
}

interface Props {
  video: Video;
  /** 첫 챕터의 대표 장면 — 없으면 잉크 바탕 */
  frame: string | null;
  /** 재생 판의 시작 시각 — 고른 시각, 없으면 0 */
  start: number;
  long: boolean;
  ref?: Ref<PlayerHandle>;
}

export default function Player({ video, frame, start, long, ref }: Props) {
  const kind = kindOf(video);
  const [phase, setPhase] = useState<Phase>("facade");
  const [open, setOpen] = useState(true);
  // 마지막으로 재생을 시작한 시각 — 막대 글(16.6)이 보인다. 재생하며 바뀌지 않는다
  const [at, setAt] = useState(start);
  const [failure, setFailure] = useState<Failure | null>(null);
  const yt = useRef<YTPlayer | null>(null);
  const ytHost = useRef<HTMLDivElement>(null);
  const media = useRef<HTMLVideoElement & HTMLAudioElement>(null);
  // 접을 때 재생 중이었는가 — 펼치면 이어 본다
  const resume = useRef(false);
  // 접혀 있는가 — YouTube가 준비됐을 때(onReady) 읽는다. 상태는 그 함수가 만들어질 때의 값이라 따로 둔다
  const folded = useRef(false);

  // 화면을 떠나면 YouTube 플레이어를 치운다
  useEffect(() => () => yt.current?.destroy(), []);

  function fail(why: Failure) {
    setFailure(why);
    setPhase("failed");
  }

  async function startYouTube(sec: number) {
    setPhase("loading");
    try {
      const YT = await loadYouTube();
      const host = ytHost.current;
      if (!host) return;
      host.replaceChildren(); // 다시 시도면 앞의 것을 치운다
      const el = document.createElement("div");
      host.appendChild(el); // API가 이 자리를 iframe으로 바꾼다 — React가 그린 것이 아니다
      yt.current = new YT.Player(el, {
        host: "https://www.youtube-nocookie.com",
        videoId: video.source_id,
        width: "100%",
        height: "100%",
        // 저절로 재생(autoplay)은 두지 않는다 — 불러오는 사이에 접었으면 재생하지 않아야 한다
        playerVars: { start: Math.floor(sec), playsinline: 1, rel: 0 },
        events: {
          onReady: (e) => {
            if (folded.current) resume.current = true;
            else e.target.playVideo();
            setPhase("playing");
          },
          // 101 · 150 — 올린 사람이 다른 사이트의 재생을 막았다. 그 밖(지워짐 · 비공개 · 재생 오류)
          onError: (e) => fail(e.data === 101 || e.data === 150 ? "blocked" : "gone"),
        },
      });
    } catch {
      fail("offline");
    }
  }

  /** 재생 판(16.1) · 다시 시도(16.9) — 고른 시각부터 그 자리에서 */
  function play() {
    setAt(start);
    setFailure(null);
    if (kind === "youtube") void startYouTube(start);
    else setPhase("playing");
  }

  /** 로컬 원본을 재생하지 못했다 — 원본이 있는지 물어 까닭을 가른다 */
  async function mediaFailed() {
    const exists = await api.mediaExists(video.id).catch(() => true);
    fail(exists ? "format" : "missing");
  }

  useImperativeHandle(
    ref,
    () => ({
      playAt(sec: number) {
        // 열기 전 · 접힘 · 실패면 스크립트만 옮긴다(재생 판의 시각은 start로 따라온다)
        if (!open || phase !== "playing") return;
        setAt(sec);
        if (kind === "youtube") {
          yt.current?.seekTo(sec, true);
          yt.current?.playVideo();
        } else if (media.current) {
          media.current.currentTime = sec;
          void media.current.play();
        }
      },
    }),
    [open, phase, kind],
  );

  function toggle() {
    if (open) {
      if (kind === "youtube") {
        // 준비되기 전(불러오는 중)에는 재생 함수가 아직 없다 — 준비되면 onReady가 재생하지 않고 남긴다
        const ready = phase === "playing";
        resume.current = !ready || yt.current?.getPlayerState() === YT_PLAYING;
        if (ready) yt.current?.pauseVideo();
      } else {
        resume.current = media.current ? !media.current.paused : false;
        media.current?.pause();
      }
    } else if (resume.current && phase === "playing") {
      if (kind === "youtube") yt.current?.playVideo();
      else void media.current?.play();
    }
    folded.current = open;
    setOpen(!open);
  }

  if (kind === "uploaded") {
    return (
      <div className="player" data-el="16">
        <div className="player-note-line" role="note" data-el="16.10">
          <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
          <span>올린 파일은 분석이 끝나면 지워서 여기서 재생할 수 없어요</span>
        </div>
      </div>
    );
  }

  const source = kind === "youtube" ? "YouTube" : "원본 파일";
  const t = timeLabel(at, long);
  const barText = !open
    ? "영상 — 펼치면 이 자리에서 재생해요"
    : phase === "playing"
      ? `${source} · ${t}부터 재생 중`
      : phase === "loading"
        ? "YouTube · 불러오는 중"
        : phase === "failed"
          ? kind === "youtube"
            ? "YouTube"
            : `원본 파일 · ${failure === "missing" ? `inbox/${video.origin}` : ext(video.origin)}`
          : kind === "youtube"
            ? "YouTube · 누르면 불러와요"
            : `원본 파일 · ${ext(video.origin)} · 누르면 재생해요`;
  const fold = (
    <button
      type="button"
      className="icon-btn player-fold"
      data-el="16.7"
      aria-label={open ? "영상 접기" : "영상 펼치기"}
      onClick={toggle}
    >
      <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
        <path d={open ? "m18 15-6-6-6 6" : "m6 9 6 6 6-6"} />
      </svg>
    </button>
  );
  const why = failure && FAILURES[failure];

  // 음성 파일 — 그림이 없어 재생 판 대신 한 줄(16.11). 누르면 <audio>와 막대
  if (kind === "audio" && phase === "facade") {
    return (
      <div className="player" data-el="16">
        <div className="player-audio" data-el="16.11" hidden={!open}>
          <button
            type="button"
            className="player-audio-play"
            aria-label={`음성 재생 — ${timeLabel(start, long)}부터`}
            onClick={play}
          >
            <PlayGlyph size={18} />
          </button>
          <span className="player-audio-text">
            <span className="player-audio-title">
              음성 파일 · {timeLabel(start, long)}부터 재생
            </span>
            <span>누르면 이 줄이 브라우저 재생 막대로 바뀌어요</span>
          </span>
          {fold}
        </div>
        {!open && (
          <div className="player-bar" data-el="16.5">
            <VideoIcon />
            <span className="player-bar-text" data-el="16.6">
              {barText}
            </span>
            {fold}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="player" data-el="16">
      <div
        className={`player-area${kind === "audio" ? " is-audio" : ""}${phase === "failed" ? " is-failed" : ""}`}
        hidden={!open}
      >
        {kind === "youtube" && (
          <div
            ref={ytHost}
            className="player-screen"
            data-el={phase === "playing" ? "16.4" : undefined}
          />
        )}
        {kind === "video" && phase === "playing" && (
          <video
            ref={media}
            className="player-screen"
            data-el="16.4"
            src={api.mediaUrl(video.id)}
            controls
            autoPlay
            playsInline
            preload="auto"
            onLoadedMetadata={(e) => {
              e.currentTarget.currentTime = at;
            }}
            onError={() => void mediaFailed()}
          />
        )}
        {kind === "audio" && phase === "playing" && (
          <audio
            ref={media}
            className="player-audio-el"
            data-el="16.4"
            src={api.mediaUrl(video.id)}
            controls
            autoPlay
            preload="auto"
            onLoadedMetadata={(e) => {
              e.currentTarget.currentTime = at;
            }}
            onError={() => void mediaFailed()}
          />
        )}
        {(phase === "facade" || phase === "loading") && kind !== "audio" && (
          <button
            type="button"
            className="player-facade"
            data-el="16.1"
            aria-label={`영상 재생 — ${timeLabel(start, long)}부터`}
            aria-disabled={phase === "loading" ? "true" : undefined}
            onClick={phase === "facade" ? play : undefined}
          >
            {frame && (
              <span className="player-facade-img" style={{ backgroundImage: `url("${frame}")` }} />
            )}
            <span className="player-facade-dim" />
            <span className="player-facade-center">
              {phase === "loading" ? (
                <span className="player-loading va-pulse" role="status">
                  불러오는 중
                </span>
              ) : (
                <>
                  <span className="player-play">
                    <PlayGlyph size={26} />
                  </span>
                  <span className="player-start" data-el="16.2">
                    {timeLabel(start, long)}부터 재생
                  </span>
                  <span className="player-hint" data-el="16.3">
                    {kind === "youtube"
                      ? "누르면 YouTube 플레이어를 불러와요"
                      : "누르면 원본 파일을 재생해요"}
                  </span>
                </>
              )}
            </span>
          </button>
        )}
        {phase === "failed" && why && (
          <div className="player-failed" role="alert" data-el="16.8">
            <span className="player-failed-icon">
              <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4" />
                <path d="M12 16h.01" />
              </svg>
            </span>
            <span className="player-failed-title">{why.title}</span>
            <span className="player-failed-body">{why.body}</span>
            {(failure === "blocked" || failure === "gone") && (
              <a
                className="btn btn-secondary"
                data-el="16.9"
                href={video.origin}
                target="_blank"
                rel="noopener noreferrer"
              >
                원본 영상 열기
                <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M15 3h6v6" />
                  <path d="M10 14 21 3" />
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                </svg>
              </a>
            )}
            {failure === "offline" && (
              <button type="button" className="btn btn-secondary" data-el="16.9" onClick={play}>
                <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
                  <path d="M21 3v5h-5" />
                </svg>
                다시 시도
              </button>
            )}
          </div>
        )}
      </div>
      <div className="player-bar" data-el="16.5">
        <VideoIcon />
        <span className="player-bar-text" data-el="16.6">
          {barText}
        </span>
        {fold}
      </div>
    </div>
  );
}
