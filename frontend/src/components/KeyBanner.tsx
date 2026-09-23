/**
 * 공통 1.4 키 없음 배너 — 키가 없거나 확인에 실패했을 때 헤더 위에 뜬다(VA-UI-002 1.4).
 * 문구 셋: 키 없음 · 확인 실패 · 연결을 확인하지 못함(이때는 [키 넣으러 가기]가 없다).
 * UI-5에는 두지 않는다. 요소 번호(1 · 1.1 · 1.2)는 UI-1에서만 붙는다.
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useSettings } from "@/api/client";

const MISSING =
  "OpenAI API 키가 없어서 아직 분석할 수 없어요. 분석해 둔 영상은 키 없이도 읽을 수 있습니다.";
const OFFLINE = "연결을 확인하지 못했어요 — 인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다";

export default function KeyBanner() {
  const path = usePathname();
  const settings = useSettings();
  if (path === "/settings" || !settings || settings.key.state === "ok") return null;
  const { state, reason_kind, reason } = settings.key;
  const offline = state === "invalid" && reason_kind === "network";
  const text =
    state === "missing" ? MISSING : offline ? OFFLINE : `키를 확인하지 못했어요 — ${reason}`;
  const home = path === "/";
  return (
    <div role="status" className="va-banner" data-el={home ? "1" : undefined}>
      <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 8v4" />
        <path d="M12 16h.01" />
      </svg>
      <span className="va-banner-text" data-el={home ? "1.1" : undefined}>
        {text}
      </span>
      {!offline && (
        <Link href="/settings" className="btn-banner" data-el={home ? "1.2" : undefined}>
          키 넣으러 가기
        </Link>
      )}
    </div>
  );
}
