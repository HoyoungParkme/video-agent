/**
 * 공통 1.5 짧은 알림 — 끝난 일을 잠깐 알리고 저절로 사라진다. 누를 것이 없고 초점을 옮기지 않는다.
 * 보이는 시간과 겹침은 아직 미결이다(VA-UI-002 2장) — 첫 값 4초, 새 알림이 앞의 것을 바꾼다.
 * 쓰는 화면은 UI-4(B1 · B4)부터.
 */
"use client";

import { useEffect, useRef } from "react";

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
    <div role="status" className="toast">
      {message}
    </div>
  );
}
