/**
 * 올리는 중 떠나기 확인 한곳(VA-DOM-002 1장 leave.ts, VA-UI-002 UI-1 규칙 「올리는 동안」).
 * Home이 올리는 동안 멈추기를 맡기고(`guardLeave`), 앱 안 링크(Header · KeyBanner · 목록 행)는
 * `onNavigate`에서 `leaveTo(href)`로 묻는다. 새로 고침 · 창 닫기는 Home이 `beforeunload`로 브라우저
 * 확인 창을 띄운다. 앱 안에서 브라우저 뒤로 가기는 묻지 못한다 — Home이 사라지며 멈춘다.
 */

// 올리는 동안 맡겨 둔 멈추기 — 없으면 묻지 않는다
let stop: (() => void) | null = null;

export const LEAVE_TEXT = "올리기를 멈추고 이동할까요? 올라간 부분은 지워져요.";

/** 올리는 동안 켠다 — 떠나기를 고르면 부를 멈추기를 맡긴다. null이면 끈다. */
export function guardLeave(abort: (() => void) | null): void {
  stop = abort;
}

/** 지금 올리는 중인가 — Home의 beforeunload가 본다 */
export function uploading(): boolean {
  return stop !== null;
}

/**
 * 앱 안 링크의 onNavigate — 올리는 중이면 묻고, 머무르면 이동을 막는다. 떠나기를 고르면 올리기를
 * 멈추고 간다. 지금 화면과 같은 주소면 묻지 않는다 — 떠나지 않아 올리기가 이어진다.
 */
export function leaveTo(href: string) {
  return (e: { preventDefault: () => void }) => {
    if (!stop || href === window.location.pathname) return;
    if (!window.confirm(LEAVE_TEXT)) {
      e.preventDefault();
      return;
    }
    const abort = stop;
    stop = null;
    abort();
  };
}
