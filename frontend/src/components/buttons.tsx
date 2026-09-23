/**
 * 공통 1.8 버튼 — 주 · 보조 · 위험(VA-UI-002 1.8, 모양은 VA-UI-001 4.2).
 * 막힌 주 버튼은 disabled가 아니라 aria-disabled다 — 초점을 받고, 누르면 부른 쪽이 설정으로 보낸다.
 * 기다리는 동안(busy)은 잠그고 글자를 깜빡인다(VA-UI-001 3.4 「지금 하는 중」).
 */
import type { ComponentPropsWithRef } from "react";

type Kind = "primary" | "secondary" | "danger";

// ref도 받는다 — 연 버튼으로 초점을 돌려줄 때(공통 1.2)
interface Props extends ComponentPropsWithRef<"button"> {
  kind: Kind;
  /** 막힌 주 버튼 — 키가 없거나 확인에 실패했을 때 */
  blocked?: boolean;
  /** 서버를 기다리는 중 */
  busy?: boolean;
  /** 입력칸과 높이를 맞춘다(48px) */
  tall?: boolean;
  /** 요소 번호(data-el) */
  el?: string;
}

export function Button({
  kind,
  blocked,
  busy,
  tall,
  el,
  className,
  onClick,
  children,
  ...rest
}: Props) {
  const classes = ["btn", `btn-${kind}`, tall && "btn-tall", blocked && "is-blocked", className]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      type="button"
      className={classes}
      // 막힘 · 기다림 모두 aria-disabled — disabled면 초점이 body로 빠져 돌아갈 곳을 잃는다
      aria-disabled={blocked || busy ? "true" : undefined}
      aria-busy={busy ? "true" : undefined}
      data-el={el}
      onClick={busy ? undefined : onClick}
      {...rest}
    >
      <span className={busy ? "va-pulse" : undefined}>{children}</span>
    </button>
  );
}
