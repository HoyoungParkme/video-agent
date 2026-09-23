/**
 * VA-UI-002#UI-2 사전 안내 — UI-1 위의 다이얼로그. 1 머리(1.1 · 1.2 · 1.3 닫기) · 2 영상 카드(2.1 ~ 2.5) ·
 * 3 예상 시간(3.1 · 3.2) · 4 예상 비용(4.1 ~ 4.3) · 5 전송 안내 · 6 버튼 줄(6.1 대기 안내 · 6.2 취소 ·
 * 6.3 분석 시작) · 7 시작 불가 판(7.1 · 7.2 · 7.3).
 * 숫자는 서버가 준 값을 그대로 보인다. B1은 자막 있음 판 — 자막 없는 영상은 시작 불가 판에
 * '아직 지원하지 않음'(사용자 결정 2026-09-23, VA-CODE-001 B1). 받아쓰기 필요 판은 B2, 시작 불가 이유 넷은 B5.
 */
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  api,
  ApiError,
  loadSettings,
  type Estimate as EstimateData,
  type Video,
} from "@/api/client";
import { Button } from "@/components/buttons";
import Dialog from "@/components/Dialog";
import { durationLabel } from "@/components/TimeChip";
import { languageName } from "@/labels";

interface Props {
  video: Video;
  estimate: EstimateData | null;
  /** 열 때 목록에 진행 중 · 대기 중 영상이 있었는가 — 대기 안내(6.1) */
  othersRunning: boolean;
  onClose: () => void;
}

const usd = (n: number) => `$${n.toFixed(2)}`;

function PlayIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M8 5.5v13l10.5-6.5z" />
    </svg>
  );
}

/** 시작할 수 없는 영상 — 이유 · 길이 · [닫기]만(7). B1은 자막 없는 영상 하나. */
function Blocked({ video, onClose }: { video: Video; onClose: () => void }) {
  return (
    <Dialog
      labelledBy="blk-title"
      width={540}
      top={104}
      onClose={onClose}
      initialFocus='[data-el="7.3"]'
    >
      <div className="estimate" data-el="7">
        <div className="estimate-blocked">
          <h2 id="blk-title" className="dialog-title" data-el="7.1">
            자막 없는 영상은 아직 지원하지 않아요
          </h2>
          <div className="chips">
            <span className="chip" data-el="7.2">
              길이 {durationLabel(video.duration_sec)}
            </span>
          </div>
        </div>
        <div className="dialog-actions">
          <Button kind="secondary" el="7.3" onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

export default function Estimate({ video, estimate, othersRunning, onClose }: Props) {
  const router = useRouter();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!estimate || estimate.needs_stt) return <Blocked video={video} onClose={onClose} />;

  // [분석 시작]을 누른 뒤에는 어느 길로도 닫히지 않는다(UI-2 규칙)
  const close = () => {
    if (!starting) onClose();
  };

  async function start() {
    if (starting) return;
    setStarting(true);
    setError(null);
    try {
      await api.startJob(video.id);
      router.replace(`/videos/${video.id}/progress`);
    } catch (e) {
      if (e instanceof ApiError && (e.kind === "key-missing" || e.kind === "key-invalid")) {
        void loadSettings();
      }
      setError(e instanceof ApiError ? e.reason : "서버에 닿지 못했어요");
      setStarting(false); // 실패하면 잠금을 풀고 다이얼로그를 그대로 둔다
    }
  }

  return (
    <Dialog
      labelledBy="est-title"
      width={620}
      top={104}
      onClose={close}
      initialFocus='[data-el="6.3"]'
    >
      <div className="estimate">
        <div className="dialog-head" data-el="1">
          <div className="dialog-head-text">
            <h2 id="est-title" className="dialog-title" data-el="1.1">
              분석을 시작할까요?
            </h2>
            <span className="dialog-sub" data-el="1.2">
              걸릴 시간과 비용을 먼저 확인하세요.
            </span>
          </div>
          <button
            type="button"
            className="icon-btn"
            aria-label="닫기"
            data-el="1.3"
            onClick={close}
          >
            <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>

        <div className="estimate-video" data-el="2">
          <span className="estimate-thumb" data-el="2.1">
            <PlayIcon />
          </span>
          <div className="estimate-video-text">
            <span className="estimate-video-title" data-el="2.2">
              {video.title}
            </span>
            <span className="estimate-video-sub" data-el="2.3">
              YouTube · {video.channel ?? ""}
            </span>
            <div className="chips">
              <span className="chip" data-el="2.4">
                길이 {durationLabel(video.duration_sec)}
              </span>
              <span className="chip chip-teal" data-el="2.5">
                자막 있음 · {languageName(video.caption_language)}
              </span>
            </div>
          </div>
        </div>

        <div className="estimate-stats">
          <div className="stat" data-el="3">
            <span className="stat-label">예상 시간</span>
            <span className="stat-value" data-el="3.1">
              약 {Math.max(1, Math.ceil(estimate.seconds / 60))}분
            </span>
            <span className="stat-note" data-el="3.2">
              받아쓰기 없이 자막을 가져와 바로 요약합니다.
            </span>
          </div>
          <div className="stat" data-el="4">
            <span className="stat-label">예상 비용</span>
            <span className="stat-value" data-el="4.1">
              약 {usd(estimate.total_cost_usd)}
            </span>
            <div className="stat-lines">
              <span className="stat-line" data-el="4.2">
                <span>받아쓰기 (자막 사용)</span>
                <span className="mono">{usd(estimate.stt_cost_usd)}</span>
              </span>
              <span className="stat-line" data-el="4.3">
                <span>요약 · 챕터 · 추천 질문</span>
                <span className="mono">{usd(estimate.text_cost_usd)}</span>
              </span>
            </div>
          </div>
        </div>

        <div className="info-box" data-el="5">
          <svg
            className="icon info-box-icon"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
          <span>
            요약을 만들려고 스크립트 텍스트가 OpenAI({estimate.text_model})로 전송됩니다. 영상은
            전송되지 않아요.
          </span>
        </div>

        {error && <p className="field-error">{error}</p>}
        <div className="dialog-actions" data-el="6">
          {othersRunning && (
            <span className="dialog-note" data-el="6.1">
              지금 다른 영상을 분석 중이에요. 시작하면 차례를 기다렸다가 저절로 시작돼요.
            </span>
          )}
          <Button
            kind="secondary"
            el="6.2"
            onClick={close}
            aria-disabled={starting ? "true" : undefined}
          >
            취소
          </Button>
          <Button kind="primary" el="6.3" busy={starting} onClick={() => void start()}>
            분석 시작
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
