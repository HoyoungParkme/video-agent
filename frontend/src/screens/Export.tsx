/**
 * VA-UI-002#UI-7 내보내기 — UI-4 머리 [내보내기](1.2)가 연다. 1 다이얼로그(1.1 제목 · 1.2 부제 · 1.3 닫기) ·
 * 2 내보내는 방법(2.1 파일로 저장 · 2.2 클립보드에 복사) · 3 질문 기록 넣기 · 4 미리 보기(4.1) ·
 * 5 버튼 줄(5.1 실패 한 줄 · 5.2 취소 · 5.3 주 버튼).
 * 미리 보기는 열 때와 3을 바꿀 때 받는다. 복사는 받아 둔 전체로 한다 — 누른 뒤 다시 받으면 사용자
 * 동작이 끝나 브라우저가 클립보드 쓰기를 막을 수 있다. 받지 못하면 영상이 없을 때 UI-1로, 그 밖은
 * 2초 뒤 다시 받고, 그동안 [복사하기]는 막혀 있다. 미리 보기 · 복사는 노트만이다. 파일은 서버가 노트와
 * 스크립트 파일 둘을 다시 만들어 쓴다 — 노트가 `[[{이름} 스크립트]]`로 가리킨다(UI-7 규칙).
 */
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ApiError, type ExportPreview, type Video } from "@/api/client";
import { Button } from "@/components/buttons";
import Dialog from "@/components/Dialog";

// 미리 보기를 받지 못했을 때 다시 받는 간격(UI-7 규칙 — UI-4 결과 받기와 같다)
const RETRY_MS = 2000;
// 4.1에 넣는 앞부분 — 최대 높이에서 잘리므로 스크립트 전부를 그릴 필요가 없다
const PREVIEW_CHARS = 4000;

type Method = "file" | "clipboard";

interface Props {
  video: Video;
  /** 질문 기록 수 — UI-4 [질문하기] 배지와 같은 값. 0이면 체크박스(3)를 그리지 않는다 */
  turns: number;
  onClose: () => void;
  /** 내보냈다 — 짧은 알림(UI-4 11) 문구를 준다 */
  onDone: (message: string) => void;
}

/** 5.1의 {이유} — 파일은 서버가 준 이유, 클립보드는 브라우저가 막았는지로(UI-7 규칙). */
function failureText(method: Method, e: unknown): string {
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
  const [method, setMethod] = useState<Method>("file");
  const [withChat, setWithChat] = useState(false);
  // 받은 미리 보기와 그때의 체크박스 값. 4.1은 새로 받는 동안 앞의 것을 그대로 보이고,
  // 복사는 지금 값과 맞는 것(preview)으로만 한다
  const [loaded, setLoaded] = useState<{ withChat: boolean; data: ExportPreview } | null>(null);
  const preview = loaded?.withChat === withChat ? loaded.data : null;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const got = await api.exportPreview(video.id, withChat);
        if (alive) setLoaded({ withChat, data: got });
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
  }, [video.id, withChat, router]);

  // 내보내는 중에는 어느 길로도 닫히지 않는다(UI-7 규칙)
  const close = () => {
    if (!busy) onClose();
  };
  const pick = (next: Method) => {
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
        onDone(`${done.path}에 저장했어요 · 스크립트는 따로`);
      } else {
        await navigator.clipboard.writeText(preview?.markdown ?? "");
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
      top={80}
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
