/**
 * VA-UI-002#UI-4 15 인포그래픽 카드 — 한눈에 보기 맨 아래. 상태 다섯마다 모양이 다르다:
 * 만들기 전(15.1 제목 · 15.2 설명 · 15.3 만들기) · 그리는 중(15.4) · 다 됨(15.5 그림 · 15.6 만든 정보 · 15.7
 * 틀릴 수 있다는 안내 · 15.8 내보내기 안내 · 15.9 크게 보기 · 15.10 다시 만들기) · 실패(15.11 · 15.10) · 키
 * 없음(15.1 · 키 없음 설명 · 15.12 키 넣으러 가기). 상태는 서버의 인포그래픽 상태를 그대로 따르고, 다시
 * 만들기가 실패해도 이전 그림이 그대로면 다 됨 카드 위에 실패 한 줄을 붙인다(UC-H9 4a). 맡기기가 서버에서
 * 거절된 이유(키 확인 실패 등)는 행이 없어 이 화면이 들고 있다가 실패 모양으로 보인다(UI-8 규칙).
 * 폴링 · 다이얼로그는 Result.tsx가 한다 — 여기는 그리기만 한다.
 */
"use client";

import Link from "next/link";

import { keyBlocks, type Infographic, type Settings } from "@/api/client";
import { Button } from "@/components/buttons";
import { madeLabel, usd } from "@/labels";

interface Props {
  infographic: Infographic;
  settings: Settings | null;
  /** 맡기기가 서버에서 거절된 이유 — 서버에 행이 없어 카드가 들고 있다 */
  rejected: string | null;
  /** 15.3 · 15.10 — UI-8을 연다(키가 막혔으면 부른 쪽이 설정으로) */
  onMake: () => void;
  /** 15.5 · 15.9 — UI-9를 연다 */
  onView: () => void;
}

function PictureIcon() {
  return (
    <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="m21 15-3.09-3.09a2 2 0 0 0-2.82 0L6 21" />
    </svg>
  );
}

export default function InfographicCard({
  infographic,
  settings,
  rejected,
  onMake,
  onView,
}: Props) {
  const { state, image } = infographic;
  const failure = state === "failed" ? infographic.error_reason : rejected;
  const blocked = settings ? keyBlocks(settings.key) : false;
  const quality = settings?.image.qualities.find((q) => q.id === settings.image.quality);
  const failLine = failure && (
    <span role="alert" className="ig-card-fail" data-el="15.11">
      인포그래픽을 만들지 못했어요 — {failure}
    </span>
  );

  if (state === "making") {
    return (
      <div role="status" className="ig-card is-drawing" data-el="15">
        <span className="ig-tile is-drawing va-pulse">
          <PictureIcon />
        </span>
        <span className="ig-card-text">
          <span className="ig-card-title">인포그래픽을 그리는 중이에요</span>
          <span className="ig-card-desc">
            다 되면 여기에 보여요. 그동안 결과를 계속 읽어도 돼요.
          </span>
        </span>
        <Button kind="secondary" className="ig-drawing-btn" aria-disabled="true" el="15.4">
          그리는 중…
        </Button>
      </div>
    );
  }

  if (image) {
    return (
      <div className="ig-card is-done" data-el="15">
        <button
          type="button"
          className="ig-thumb"
          aria-label="인포그래픽 크게 보기"
          style={{ backgroundImage: `url("${image.url}")` }}
          data-el="15.5"
          onClick={onView}
        />
        <div className="ig-done-body">
          {failLine}
          <div className="ig-card-text">
            <span className="ig-card-title">인포그래픽</span>
            <span className="ig-made" data-el="15.6">
              {madeLabel(image)}
            </span>
          </div>
          <div className="ig-warn" data-el="15.7">
            <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
            <span>
              AI가 그린 그림이에요 — 그림 속 글자 · 숫자가 틀릴 수 있어요. 근거 시각은 인사이트와
              챕터에서 확인하세요.
            </span>
          </div>
          <span className="ig-card-desc" data-el="15.8">
            파일로 내보내면 노트에 함께 들어가요.
          </span>
          <div className="ig-actions">
            <Button kind="secondary" el="15.9" onClick={onView}>
              크게 보기
            </Button>
            <Button kind="secondary" el="15.10" onClick={onMake}>
              다시 만들기
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (blocked) {
    return (
      <div className="ig-card is-dashed" data-el="15">
        <span className="ig-tile is-muted">
          <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="7.5" cy="15.5" r="5.5" />
            <path d="m21 2-9.6 9.6" />
            <path d="m15.5 7.5 3 3L22 7l-3-3" />
          </svg>
        </span>
        <span className="ig-card-text">
          <span className="ig-card-title is-muted" data-el="15.1">
            인포그래픽 한 장으로 보기
          </span>
          <span className="ig-card-desc">OpenAI API 키가 없어서 지금은 만들 수 없어요.</span>
        </span>
        <Link href="/settings" className="btn btn-primary" data-el="15.12">
          키 넣으러 가기
        </Link>
      </div>
    );
  }

  if (failLine) {
    return (
      <div className="ig-card is-failed" data-el="15">
        <span className="ig-tile is-failed">
          <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4" />
            <path d="M12 16h.01" />
          </svg>
        </span>
        {failLine}
        <Button kind="secondary" el="15.10" onClick={onMake}>
          다시 만들기
        </Button>
      </div>
    );
  }

  return (
    <div className="ig-card is-dashed" data-el="15">
      <span className="ig-tile">
        <PictureIcon />
      </span>
      <span className="ig-card-text">
        <span className="ig-card-title" data-el="15.1">
          인포그래픽 한 장으로 보기
        </span>
        <span className="ig-card-desc" data-el="15.2">
          한 줄 요약 · 인사이트 · 챕터 제목으로 그림을 그려요. 한 장 약 {usd(quality?.price_usd)} ·
          누를 때만 만들어요
        </span>
      </span>
      <Button kind="secondary" el="15.3" onClick={onMake}>
        인포그래픽 만들기
      </Button>
    </div>
  );
}
