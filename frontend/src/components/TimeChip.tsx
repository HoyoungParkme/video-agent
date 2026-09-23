/**
 * 공통 1.3 시각 칩 — 영상 속 한 시각. 누르면 오른쪽 스크립트가 그 시각으로 간다(VA-UI-002 1.3).
 * 시각 표기도 여기 산다(VA-DOM-002 7장) — 1시간 미만 영상은 mm:ss, 이상은 h:mm:ss이고
 * 한 영상 안의 시각은 모두 같은 형식이다(VA-UI-001 4.4).
 */
"use client";

/** 초 → 시각 표기. long이면 h:mm:ss, 아니면 mm:ss(분이 60을 넘어도 그대로). 소수는 버린다. */
export function timeLabel(sec: number, long: boolean): string {
  const s = Math.max(0, Math.floor(sec));
  const two = (n: number) => String(n).padStart(2, "0");
  if (long) return `${Math.floor(s / 3600)}:${two(Math.floor((s % 3600) / 60))}:${two(s % 60)}`;
  return `${two(Math.floor(s / 60))}:${two(s % 60)}`;
}

/** 영상 길이로 형식을 정한다 — 이 영상의 시각은 모두 이 형식이다. */
export function isLong(durationSec: number): boolean {
  return durationSec >= 3600;
}

/** 영상 길이 표기 — 길이 자신도 같은 규칙. */
export function durationLabel(durationSec: number): string {
  return timeLabel(durationSec, isLong(durationSec));
}

interface Props {
  sec: number;
  long: boolean;
  onSelect: (sec: number) => void;
  el?: string;
}

export default function TimeChip({ sec, long, onSelect, el }: Props) {
  const label = timeLabel(sec, long);
  return (
    <button
      type="button"
      className="time-chip"
      aria-label={`${label} 위치의 스크립트로 이동`}
      data-el={el}
      onClick={() => onSelect(sec)}
    >
      {label}
    </button>
  );
}
