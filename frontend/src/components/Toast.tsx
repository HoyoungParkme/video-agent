/**
 * 공통 1.5 짧은 알림 — 끝난 일을 잠깐 알리고 저절로 사라진다. 누를 것이 없고 초점을 옮기지 않는다.
 * 보이는 시간과 겹침은 아직 미결이다(VA-UI-002 2장) — 첫 값 4초, 새 알림이 앞의 것을 바꾼다.
 * 화면이 바뀌면서 알리는 경우(UI-1 → UI-4 '이미 분석한 영상입니다')는 새 화면에서 보인다 —
 * 연 쪽이 flash로 맡기고 새 화면이 takeFlash로 꺼낸다(주소를 바꾸지 않는다).
 */
"use client";

import { useEffect, useRef } from "react";

let pending: string | null = null;

/** 다음 화면에 보일 알림을 맡긴다. */
export function flash(message: string): void {
  pending = message;
}

/** 맡긴 알림을 꺼낸다 — 한 번만. */
export function takeFlash(): string | null {
  const message = pending;
  pending = null;
  return message;
}

interface Props {
  message: string;
  onDone: () => void;
  ms?: number;
}

export default function Toast({ message, onDone, ms = 4000 }: Props) {
  // onDone이 그릴 때마다 새 함수여도 시계를 다시 맞추지 않는다
  const done = useRef(onDone);
  useEffect(() => {
    done.current = onDone;
  });
  useEffect(() => {
    const timer = setTimeout(() => done.current(), ms);
    return () => clearTimeout(timer);
  }, [message, ms]);
  return (
    <div role="status" className="toast" data-el="11">
      <svg
        className="icon toast-icon"
        width="18"
        height="18"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d="M20 6 9 17l-5-5" />
      </svg>
      {message}
    </div>
  );
}
