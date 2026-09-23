/**
 * 공통 1.7 빈 상태 상자 — 목록이 비었을 때 그 자리에 두는 점선 상자. 누를 것이 없다(VA-UI-002 1.7).
 * 요소 번호는 부르는 화면이 준다(UI-1은 7 · 7.1 · 7.2).
 */
interface Props {
  title: string;
  body: string;
  el?: string;
  elTitle?: string;
  elBody?: string;
}

export default function EmptyBox({ title, body, el, elTitle, elBody }: Props) {
  return (
    <div className="empty-box" data-el={el}>
      <span className="empty-box-title" data-el={elTitle}>
        {title}
      </span>
      <span className="empty-box-body" data-el={elBody}>
        {body}
      </span>
    </div>
  );
}
