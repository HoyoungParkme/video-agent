/**
 * 공통 1.1 헤더 — 로고(→ UI-1)와 주 메뉴('분석한 영상' → UI-1 · 설정 → UI-5).
 * 헤더에는 요소 번호가 없다(VA-UI-002 1.1). 현재 위치는 UI-1 · UI-5에만 표시한다.
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const path = usePathname();
  return (
    <header className="va-header">
      <Link href="/" className="va-logo">
        <span className="va-logo-tile">
          <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8 5.5v13l10.5-6.5z" />
          </svg>
        </span>
        <span className="va-logo-text">Video Agent</span>
      </Link>
      <nav aria-label="주 메뉴" className="va-nav">
        <Link href="/" className="va-nav-text" aria-current={path === "/" ? "page" : undefined}>
          분석한 영상
        </Link>
        <Link
          href="/settings"
          className="va-nav-icon"
          aria-label="설정"
          aria-current={path === "/settings" ? "page" : undefined}
        >
          <svg
            className="icon icon-thin"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M20 7h-9" />
            <path d="M14 17H5" />
            <circle cx="17" cy="17" r="3" />
            <circle cx="7" cy="7" r="3" />
          </svg>
        </Link>
      </nav>
    </header>
  );
}
