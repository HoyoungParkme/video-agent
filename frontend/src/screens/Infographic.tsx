/**
 * VA-UI-002#UI-8 인포그래픽 만들기 — UI-4 인포그래픽 카드의 [인포그래픽 만들기](15.3) · [다시 만들기](15.10)가 연다.
 * 1 다이얼로그(1.1 제목 · 1.2 부제 · 1.3 닫기) · 2 비용과 품질(2.1 예상 비용 · 2.2 품질 · 2.3 설정에서 바꾸기) ·
 * 3 보내는 것(3.1 · 3.2 · 다시 만들기면 3.3) · 4 버튼 줄(4.1 취소 · 4.2 만들기).
 * 값과 품질은 설정에서 고른 품질의 서버 값 그대로다. [만들기]는 서버에 그리기를 맡기고 곧바로 닫힌다 — 다 그릴
 * 때까지 기다리지 않는다. 키 확인이 실패하면 닫고 카드가 이유를 보인다. 서버에 닿지 못하면 닫지 않고 버튼 줄
 * 왼쪽에 한 줄을 보인다. 닫는 길은 모두 취소이고 아무것도 보내지 않는다.
 */
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  api,
  ApiError,
  loadSettings,
  type ImageSettings,
  type Infographic as InfographicData,
} from "@/api/client";
import { Button } from "@/components/buttons";
import Dialog from "@/components/Dialog";
import { usd } from "@/labels";

interface Props {
  videoId: number;
  insightCount: number;
  chapterCount: number;
  /** 이미 그림이 있다 — 다시 만들기(3.3) */
  hasImage: boolean;
  image: ImageSettings;
  onClose: () => void;
  /** 맡겼다 — 카드가 그리는 중이 된다 */
  onStarted: (infographic: InfographicData) => void;
  /** 서버가 받지 않았다(키 확인 실패 등) — 닫힌 뒤 카드가 이 이유를 보인다 */
  onRejected: (reason: string) => void;
}

export default function Infographic({
  videoId,
  insightCount,
  chapterCount,
  hasImage,
  image,
  onClose,
  onStarted,
  onRejected,
}: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const quality = image.qualities.find((q) => q.id === image.quality) ?? image.qualities[0];
  const price = usd(quality?.price_usd);

  function close() {
    if (!busy) onClose(); // 맡기는 동안은 닫지 않는다
  }

  async function make() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      onStarted(await api.makeInfographic(videoId));
    } catch (e) {
      const ours = e instanceof ApiError && e.kind !== "unknown";
      if (!ours) {
        // 서버에 닿지 못했다 — 닫지 않고 한 줄(UI-8 규칙)
        setError("인포그래픽을 맡기지 못했어요 — 서버에 연결할 수 없음");
        setBusy(false);
        return;
      }
      if (e.kind === "infographic-busy") {
        // 다른 창에서 먼저 맡겼다 — 지금 상태를 받아 카드가 그리는 중을 보인다
        const now = await api.infographic(videoId).catch(() => null);
        if (now) onStarted(now);
        else onClose();
        return;
      }
      if (e.kind === "key-missing" || e.kind === "key-invalid") void loadSettings(); // 배너가 따라온다
      onRejected(e.reason.replace(/[.。]\s*$/, ""));
    }
  }

  return (
    <Dialog
      el="1"
      labelledBy="ig-title"
      width={580}
      top={120}
      onClose={close}
      initialFocus='[data-el="4.2"]'
    >
      <div className="ig">
        <div className="dialog-head">
          <div className="dialog-head-text">
            <h2 id="ig-title" className="dialog-title" data-el="1.1">
              인포그래픽 만들기
            </h2>
            <span className="dialog-sub" data-el="1.2">
              이 영상의 내용을 그림 한 장으로 그려요.
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
        <div className="ig-cost" data-el="2">
          <div className="ig-cost-box">
            <span className="ig-cost-label">예상 비용</span>
            <span className="ig-cost-value mono" data-el="2.1">
              약 {price}
            </span>
          </div>
          <div className="ig-cost-box">
            <span className="ig-cost-label">품질</span>
            <span className="ig-quality" data-el="2.2">
              {quality?.label} · {image.model}
            </span>
            <a
              href="/settings"
              className="ig-settings-link"
              data-el="2.3"
              onClick={(e) => {
                e.preventDefault();
                if (busy) return;
                onClose(); // 아무것도 보내지 않고 닫힌다
                router.push("/settings");
              }}
            >
              설정에서 바꾸기
            </a>
          </div>
        </div>
        <div className="ig-send" data-el="3">
          <span className="ig-send-title">
            <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M7 7h10v10" />
              <path d="M7 17 17 7" />
            </svg>
            OpenAI로 보내는 것
          </span>
          <span className="ig-send-what" data-el="3.1">
            한 줄 요약 1문장 · 인사이트 {insightCount}개 · 챕터 제목 {chapterCount}개
          </span>
          <span className="ig-send-note" data-el="3.2">
            스크립트 전체는 보내지 않아요. 그림 속 글자 · 숫자는 틀릴 수 있어요.
          </span>
          {hasImage && (
            <span className="ig-send-replace" data-el="3.3">
              새 그림이 지금 그림을 바꿔요.
            </span>
          )}
        </div>
        <div className="dialog-actions" data-el="4">
          {error && (
            <span className="dialog-error" role="alert">
              {error}
            </span>
          )}
          <Button
            kind="secondary"
            el="4.1"
            aria-disabled={busy ? "true" : undefined}
            onClick={close}
          >
            취소
          </Button>
          <Button kind="primary" el="4.2" busy={busy} onClick={() => void make()}>
            만들기 · 약 {price}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
