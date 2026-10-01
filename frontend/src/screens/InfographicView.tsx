/**
 * VA-UI-002#UI-9 인포그래픽 크게 보기 — UI-4 인포그래픽 그림(15.5)이나 [크게 보기](15.9)가 연다.
 * 1 다이얼로그(1.1 제목 · 1.2 만든 정보 · 1.3 닫기) · 2 그림 · 3 틀릴 수 있다는 안내. 덮개는 다른 다이얼로그보다
 * 짙다. 그림은 폭 432px로 줄여 가운데에 두고, 창이 낮으면 창 높이에 맞춰 더 줄인다. 불러오는 동안은 그림 자리
 * 색이다. 닫는 길은 닫기 · Esc · 덮개 누름이고 초점은 연 것으로 돌아간다. 내려받기는 없다.
 */
"use client";

import type { InfographicImage } from "@/api/client";
import Dialog from "@/components/Dialog";
import { madeLabel } from "@/labels";

interface Props {
  image: InfographicImage;
  /** 영상 제목 — 그림의 대체 글 */
  title: string;
  onClose: () => void;
}

export default function InfographicView({ image, title, onClose }: Props) {
  return (
    <Dialog
      labelledBy="iv-title"
      width={640}
      top={48}
      padding="var(--space-24)"
      dark
      initialFocus='[data-el="1.3"]'
      el="1"
      onClose={onClose}
    >
      <div className="iv">
        <div className="iv-head">
          <div className="iv-head-text">
            <h2 id="iv-title" className="iv-title" data-el="1.1">
              인포그래픽
            </h2>
            <span className="iv-made" data-el="1.2">
              {madeLabel(image)}
            </span>
          </div>
          <button
            type="button"
            className="icon-btn"
            aria-label="닫기"
            data-el="1.3"
            onClick={onClose}
          >
            <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>
        <span
          role="img"
          aria-label={`인포그래픽 — ${title}`}
          className="iv-picture"
          style={{
            aspectRatio: `${image.width} / ${image.height}`,
            backgroundImage: `url("${image.url}")`,
          }}
          data-el="2"
        />
        <span className="iv-note" data-el="3">
          AI가 그린 그림이에요 — 그림 속 글자 · 숫자가 틀릴 수 있어요.
        </span>
      </div>
    </Dialog>
  );
}
