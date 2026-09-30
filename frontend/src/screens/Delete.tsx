/**
 * VA-UI-002#UI-6 삭제 확인 — UI-1 행 휴지통(6.8)이나 UI-4 머리 휴지통(1.3)이 연다. 1 경고 다이얼로그
 * (1.1 아이콘 타일 · 1.2 제목 · 1.3 대상 제목) · 2 지울 것과 남는 것(2.1 · 2.2) · 3 버튼 줄(3.1 실패 한 줄 ·
 * 3.2 취소 · 3.3 삭제). 올린 사본이 남아 있으면 2.1 끝에 '올린 사본({크기})', 올린 파일이면 2.2가 'PC에
 * 있는 원본 파일'이다 — 원본은 지우지 않는다.
 * 덮개를 눌러도 닫히지 않고 Esc는 취소와 같다. 지우는 동안은 두 버튼과 Esc가 잠긴다. 이미 지워졌으면(404)
 * 지운 것과 같다. 지운 뒤 갈 곳과 초점은 연 화면이 정한다 — UI-4에서 지웠으면 UI-1의 「분석한 영상」
 * 제목(5.1)으로 간다(markListFocus · takeListFocus, 사용자 결정 2026-09-28).
 */
"use client";

import { useState } from "react";

import { api, ApiError, type Video } from "@/api/client";
import { Button } from "@/components/buttons";
import Dialog from "@/components/Dialog";
import { sizeLabel } from "@/labels";

// UI-4에서 지운 뒤 열리는 UI-1이 5.1에 초점을 둔다 — 연 쪽이 맡기고 UI-1이 한 번만 꺼낸다
let listFocus = false;

/** 다음에 열리는 UI-1이 「분석한 영상」 제목에 초점을 두게 맡긴다. */
export function markListFocus(): void {
  listFocus = true;
}

/** 맡긴 초점을 꺼낸다 — 한 번만. */
export function takeListFocus(): boolean {
  const take = listFocus;
  listFocus = false;
  return take;
}

interface Props {
  video: Video;
  /** 질문 기록 수 — UI-4는 이 화면에서 늘어난 것까지(배지와 같은 값) */
  turns: number;
  onClose: () => void;
  onDeleted: () => void;
}

export function TrashIcon({ size = 18 }: { size?: number }) {
  return (
    <svg
      className="icon icon-thin"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    </svg>
  );
}

export default function Delete({ video, turns, onClose, onDeleted }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 분석이 끝나지 않은 영상(진행 중 · 대기 중 · 실패)은 임시 음성 파일도 지운다
  const unfinished = video.status === "in_progress" || video.status === "failed";
  // 올린 사본이 아직 남아 있으면(진행 중 · 대기 중 · 실패한 올린 파일) 맨 끝에 크기와 함께
  const copy = video.upload_bytes === null ? "" : `, 올린 사본(${sizeLabel(video.upload_bytes)})`;
  const gone = `스크립트, 핵심 요약, 챕터, 추천 질문, 질문 기록 ${turns}개${unfinished ? ", 임시 음성 파일" : ""}${copy}`;
  // 남는 것 — 원본은 지우지 않는다. 올린 파일은 앱 폴더의 사본만 지운다(INFRA C4)
  const origin =
    video.source_kind === "youtube"
      ? "YouTube 원본 영상"
      : video.uploaded
        ? "PC에 있는 원본 파일"
        : "inbox 원본 파일";

  // 지우는 동안은 취소도 Esc도 받지 않는다(UI-6 규칙)
  const close = () => {
    if (!busy) onClose();
  };

  async function remove() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await api.deleteVideo(video.id);
      onDeleted();
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        onDeleted(); // 다른 창에서 이미 지웠다 — 지운 것과 같다
        return;
      }
      const why = e instanceof ApiError ? e.reason : "서버에 연결할 수 없음";
      setError(`분석 결과를 지우지 못했어요 — ${why}`);
      setBusy(false); // 실패하면 열린 채 두 버튼을 다시 푼다
    }
  }

  return (
    <Dialog
      role="alertdialog"
      el="1"
      labelledBy="del-title"
      describedBy="del-desc"
      width={540}
      top={180}
      onClose={close}
      closeOnOverlay={false}
      initialFocus='[data-el="3.2"]'
    >
      <div className="delete">
        <span className="delete-tile" data-el="1.1">
          <TrashIcon size={22} />
        </span>
        <div className="delete-head">
          <h2 id="del-title" className="delete-title" data-el="1.2">
            분석 결과를 지울까요?
          </h2>
          <p id="del-desc" className="delete-target" data-el="1.3">
            {video.title}
          </p>
        </div>
        <div className="delete-boxes" data-el="2">
          <div className="delete-box is-gone" data-el="2.1">
            <span className="delete-box-label">지워지는 것</span>
            <span className="delete-box-text">{gone}</span>
          </div>
          <div className="delete-box" data-el="2.2">
            <span className="delete-box-label">남는 것</span>
            <span className="delete-box-text">{origin}. 다시 넣으면 처음부터 분석합니다.</span>
          </div>
        </div>
        <div className="dialog-actions" data-el="3">
          {error && (
            <span className="dialog-error" role="alert" data-el="3.1">
              {error}
            </span>
          )}
          <Button
            kind="secondary"
            el="3.2"
            aria-disabled={busy ? "true" : undefined}
            onClick={close}
          >
            취소
          </Button>
          <Button kind="danger" el="3.3" busy={busy} onClick={remove}>
            삭제
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
