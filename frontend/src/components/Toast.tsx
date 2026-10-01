/**
 * 공통 1.5 짧은 알림 — 끝난 일을 잠깐 알리고 저절로 사라진다. 누를 것이 없고 초점을 옮기지 않는다.
 * 4초 보인다. 마우스를 올린 동안은 멈추고, 내리면 4초를 처음부터 센다. 새 알림은 앞의 것을 바꾸고 처음부터
 * 센다 — 같은 글이어도 쓰는 화면이 알림마다 key를 바꿔 새로 그린다(VA-UI-002 1.5).
 * 화면이 바뀌면서 알리는 경우(UI-1 → UI-4 '이미 분석한 영상입니다')는 새 화면에서 보인다 —
 * 연 쪽이 flash로 맡기고 새 화면이 takeFlash로 꺼낸다(주소를 바꾸지 않는다).
 * 와이어프레임 요소 번호는 화면마다 달라 쓰는 화면이 el로 준다(UI-4는 11).
 */
"use client";

import { useEffect, useRef, useState } from "react";

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
  el?: string;
}

export default function Toast({ message, onDone, ms = 4000, el }: Props) {
  // onDone이 그릴 때마다 새 함수여도 시계를 다시 맞추지 않는다
  const done = useRef(onDone);
  useEffect(() => {
    done.current = onDone;
  });
  // 마우스를 올린 동안은 세지 않는다 — 내리면 처음부터
  const [held, setHeld] = useState(false);
  useEffect(() => {
    if (held) return;
    const timer = setTimeout(() => done.current(), ms);
    return () => clearTimeout(timer);
  }, [message, ms, held]);
  return (
    <div
      role="status"
      className="toast"
      data-el={el}
      onMouseEnter={() => setHeld(true)}
      onMouseLeave={() => setHeld(false)}
    >
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
