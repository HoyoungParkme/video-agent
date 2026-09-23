/**
 * 공통 1.2 다이얼로그 틀 — 덮개 위 흰 카드, 가로 가운데 · 세로 위(VA-UI-002 1.2, 모양은 VA-UI-001 4.3).
 * 열리면 초점이 안으로 들어가 밖으로 나가지 않고, 닫히면 연 버튼으로 돌아간다.
 * Esc는 늘 닫기다. 덮개 누름은 closeOnOverlay일 때만(UI-6은 닫히지 않는다). 쓰는 화면은 B1 · B4부터.
 */
"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface Props {
  /** UI-6만 alertdialog */
  role?: "dialog" | "alertdialog";
  labelledBy: string;
  describedBy?: string;
  /** 폭(px) — UI-2 620 · UI-6 540 · UI-7 660 */
  width: number;
  /** 위 여백(px) — UI-2 104 · UI-6 180 · UI-7 80 */
  top: number;
  onClose: () => void;
  closeOnOverlay?: boolean;
  /** 처음 초점을 받을 요소의 CSS 선택자. 없으면 첫 초점 가능한 요소 */
  initialFocus?: string;
  children: ReactNode;
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

export default function Dialog({
  role = "dialog",
  labelledBy,
  describedBy,
  width,
  top,
  onClose,
  closeOnOverlay = true,
  initialFocus,
  children,
}: Props) {
  const box = useRef<HTMLDivElement>(null);
  const close = useRef(onClose);
  useEffect(() => {
    close.current = onClose;
  });

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    const target = initialFocus ? box.current?.querySelector<HTMLElement>(initialFocus) : null;
    (target ?? box.current?.querySelector<HTMLElement>(FOCUSABLE))?.focus();
    return () => opener?.focus();
  }, [initialFocus]);

  // 문서 전체에서 듣는다 — 덮개를 눌러 초점이 body로 빠져도 Esc와 초점 가두기가 산다
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        close.current();
        return;
      }
      if (e.key !== "Tab" || !box.current) return;
      const items = Array.from(box.current.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      const inside = box.current.contains(document.activeElement);
      if (!inside || (e.shiftKey && document.activeElement === first)) {
        e.preventDefault();
        (e.shiftKey && inside ? last : first).focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  return createPortal(
    <div
      className="dialog-overlay"
      style={{ paddingTop: top }}
      onMouseDown={(e) => {
        if (closeOnOverlay && e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={box}
        className="dialog"
        style={{ maxWidth: width }}
        role={role}
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
