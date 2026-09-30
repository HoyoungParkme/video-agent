/**
 * VA-UI-002#UI-7 내보내기 — UI-4 머리 [내보내기](1.2)가 연다. 1 다이얼로그(1.1 제목 · 1.2 부제 · 1.3 닫기) ·
 * 2 내보내는 방법(2.1 파일로 저장 · 2.2 클립보드에 복사, 그 아래 2.3 함께 저장되는 파일 또는 2.4 복사 안내) ·
 * 3 질문 기록 넣기 · 4 미리 보기(4.1) · 5 버튼 줄(5.1 실패 한 줄 · 5.2 취소 · 5.3 주 버튼).
 * 미리 보기는 고른 방법의 노트다 — 열 때와 방법이나 3을 바꿀 때 받는다. 파일 노트에만 그림 줄과
 * `## 스크립트` 절(`[[{이름} 스크립트]]`)이 있다. 복사는 받아 둔 클립보드 노트 전체로 한다 — 누른 뒤 다시
 * 받으면 사용자 동작이 끝나 브라우저가 클립보드 쓰기를 막을 수 있다. 받지 못하면 영상이 없을 때 UI-1로,
 * 그 밖은 2초 뒤 다시 받고, 그동안 [복사하기]는 막혀 있다. 파일은 서버가 노트 · 스크립트(그림이 있으면
 * 그림도)를 다시 만들어 쓰고, 2.3의 칩은 파일 미리 보기가 준 목록이다(UI-7 규칙).
 */
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  api,
  ApiError,
  type ExportFile,
  type ExportMethod,
  type ExportPreview,
  type Video,
} from "@/api/client";
import { Button } from "@/components/buttons";
import Dialog from "@/components/Dialog";

// 미리 보기를 받지 못했을 때 다시 받는 간격(UI-7 규칙 — UI-4 결과 받기와 같다)
const RETRY_MS = 2000;
// 4.1에 넣는 앞부분 — 미리 보기는 노트의 앞부분이다(UI-7 4.1). 상자 안에서 스크롤한다
const PREVIEW_CHARS = 4000;
// 2.3 칩 — 종류마다 하나, 장면은 몇 장인지 센다. 그림 칩은 연한 청록이다(VA-UI-001 UI-7)
const CHIPS: Record<
  ExportFile["kind"],
  { label: (n: number) => string; ext: string; image: boolean }
> = {
  note: { label: () => "노트", ext: ".md", image: false },
  script: { label: () => "스크립트", ext: ".md", image: false },
  frame: { label: (n) => `장면 ${n}장`, ext: ".jpg", image: true },
  infographic: { label: (n) => `인포그래픽 ${n}장`, ext: ".png", image: true },
};

interface Props {
  video: Video;
  /** 질문 기록 수 — UI-4 [질문하기] 배지와 같은 값. 0이면 체크박스(3)를 그리지 않는다 */
  turns: number;
  onClose: () => void;
  /** 내보냈다 — 짧은 알림(UI-4 11) 문구를 준다 */
  onDone: (message: string) => void;
}

/** 5.1의 {이유} — 파일은 서버가 준 이유, 클립보드는 브라우저가 막았는지로(UI-7 규칙). */
function failureText(method: ExportMethod, e: unknown): string {
  if (method === "file") {
    const why = e instanceof ApiError ? e.reason : "서버에 연결할 수 없음";
    return `파일을 저장하지 못했어요 — ${why}`;
  }
  const blocked = e instanceof DOMException && e.name === "NotAllowedError";
  return `클립보드에 복사하지 못했어요 — ${blocked ? "브라우저가 클립보드 쓰기를 막음" : "클립보드를 쓸 수 없음"}`;
}

export function DownloadIcon() {
  return (
    <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="m7 10 5 5 5-5" />
      <path d="M12 15V3" />
    </svg>
  );
}

/** 함께 쓸 파일 → 2.3 칩. 서버가 준 순서(노트 · 스크립트 · 장면 · 인포그래픽)대로 종류마다 하나. */
function chips(files: ExportFile[]) {
  const kinds = [...new Set(files.map((f) => f.kind))];
  return kinds.map((kind) => {
    const chip = CHIPS[kind];
    return { kind, ...chip, label: chip.label(files.filter((f) => f.kind === kind).length) };
  });
}

function CopyIcon() {
  return (
    <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="8" y="8" width="14" height="14" rx="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
  );
}

export default function Export({ video, turns, onClose, onDone }: Props) {
  const router = useRouter();
  // 열 때마다 파일로 저장으로 시작한다 — 지난번 방법을 기억하지 않는다(UI-7 규칙)
  const [method, setMethod] = useState<ExportMethod>("file");
  const [withChat, setWithChat] = useState(false);
  // 받은 미리 보기와 그때의 방법 · 체크박스 값. 4.1은 새로 받는 동안 앞의 것을 그대로 보이고,
  // 복사는 지금 값과 맞는 것(preview)으로만 한다
  const [loaded, setLoaded] = useState<{
    method: ExportMethod;
    withChat: boolean;
    data: ExportPreview;
  } | null>(null);
  const preview = loaded?.method === method && loaded.withChat === withChat ? loaded.data : null;
  // 2.3 칩 — 파일 미리 보기가 준 목록. 체크박스와 상관없어 방법을 오가도 그대로 둔다
  const [files, setFiles] = useState<ExportFile[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const got = await api.exportPreview(video.id, withChat, method);
        if (!alive) return;
        setLoaded({ method, withChat, data: got });
        if (method === "file") setFiles(got.files);
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 404) {
          router.replace("/"); // 그 사이 영상이 지워졌다
          return;
        }
        timer = setTimeout(load, RETRY_MS);
      }
    };
    void load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [video.id, withChat, method, router]);

  // 내보내는 중에는 어느 길로도 닫히지 않는다(UI-7 규칙)
  const close = () => {
    if (!busy) onClose();
  };
  const pick = (next: ExportMethod) => {
    if (busy) return;
    setMethod(next);
    setError(null); // 방법을 바꾸면 실패 한 줄이 사라진다
  };
  // 받아 둔 전체로 복사하므로 받기 전에는 [복사하기]가 막힌다
  const copyBlocked = method === "clipboard" && preview === null;

  async function send() {
    if (busy || copyBlocked) return;
    setBusy(true);
    setError(null);
    try {
      if (method === "file") {
        const done = await api.exportFile(video.id, withChat);
        const images = done.images > 0 ? ` · 그림 ${done.images}장` : "";
        onDone(`${done.path}에 저장했어요 · 스크립트는 따로${images}`);
      } else {
        await navigator.clipboard.writeText(preview?.markdown ?? ""); // 클립보드 노트 — 그림 줄 · 스크립트 절 없음
        onDone("클립보드에 복사했어요");
      }
    } catch (e) {
      setError(failureText(method, e));
      setBusy(false); // 실패하면 열린 채 잠금을 푼다
    }
  }

  return (
    <Dialog
      el="1"
      labelledBy="exp-title"
      width={660}
      top={48}
      padding="var(--space-28) var(--space-32)"
      onClose={close}
      initialFocus='[data-el="2.1"]'
    >
      <div className="export">
        <div className="dialog-head">
          <div className="dialog-head-text">
            <h2 id="exp-title" className="dialog-title" data-el="1.1">
              마크다운으로 내보내기
            </h2>
            <span className="dialog-sub" data-el="1.2">
              시각은 [12:40] 형태로 남고, YouTube 영상이면 그 시점 링크가 걸려요.
            </span>
          </div>
          <button
            type="button"
            className="icon-btn"
            aria-label="닫기"
            aria-disabled={busy ? "true" : undefined}
            data-el="1.3"
            onClick={close}
          >
            <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>
        <div className="export-methods" role="group" aria-label="내보내는 방법" data-el="2">
          <button
            type="button"
            className={`export-method${method === "file" ? " is-on" : ""}`}
            aria-pressed={method === "file"}
            aria-disabled={busy ? "true" : undefined}
            data-el="2.1"
            onClick={() => pick("file")}
          >
            <span className="export-method-name">
              <DownloadIcon />
              파일로 저장
            </span>
            <span className="export-method-path">{loaded?.data.path ?? ""}</span>
          </button>
          <button
            type="button"
            className={`export-method${method === "clipboard" ? " is-on" : ""}`}
            aria-pressed={method === "clipboard"}
            aria-disabled={busy ? "true" : undefined}
            data-el="2.2"
            onClick={() => pick("clipboard")}
          >
            <span className="export-method-name">
              <CopyIcon />
              클립보드에 복사
            </span>
            <span className="export-method-note">노트 앱에 바로 붙여 넣기</span>
          </button>
        </div>
        {method === "file" ? (
          <div className="export-files" data-el="2.3">
            <span className="export-files-label">함께 저장되는 파일</span>
            <div className="export-files-chips">
              {chips(files ?? []).map((c) => (
                <span key={c.kind} className={`export-file${c.image ? " is-image" : ""}`}>
                  {c.label}
                  <span className="export-file-ext">{c.ext}</span>
                </span>
              ))}
            </div>
            {files?.some((f) => CHIPS[f.kind].image) && (
              <span className="export-files-note">
                그림은 노트 곁에 저장되고 노트가 가리켜요 — 옵시디언에서 열면 바로 보여요.
              </span>
            )}
          </div>
        ) : (
          <div className="export-copy-note" role="note" data-el="2.4">
            <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
            <span>
              복사에는 그림 파일이 빠져요 — 장면 · 인포그래픽 줄도 넣지 않아요. 한눈에 보기는
              Mermaid 코드라 노트 앱이 그대로 그려요.
            </span>
          </div>
        )}
        {turns > 0 && (
          <label className="export-chat" data-el="3">
            <input
              type="checkbox"
              checked={withChat}
              disabled={busy}
              onChange={(e) => setWithChat(e.target.checked)}
            />
            <span>질문 기록 {turns}개도 넣기</span>
          </label>
        )}
        <div className="export-preview" data-el="4">
          <span className="export-preview-label">미리 보기</span>
          <pre className="export-preview-box" data-el="4.1">
            {loaded?.data.markdown.slice(0, PREVIEW_CHARS) ?? ""}
          </pre>
        </div>
        <div className="dialog-actions" data-el="5">
          {error && (
            <span className="dialog-error" role="alert" data-el="5.1">
              {error}
            </span>
          )}
          <Button
            kind="secondary"
            el="5.2"
            aria-disabled={busy ? "true" : undefined}
            onClick={close}
          >
            취소
          </Button>
          <Button kind="primary" el="5.3" busy={busy} blocked={copyBlocked} onClick={send}>
            {method === "file" ? "파일로 저장" : "복사하기"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
