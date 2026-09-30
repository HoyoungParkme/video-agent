/**
 * Host 판정 한곳(VA-DOM-002 1장) — localhost · 127.0.0.1 · [::1]만 받는다(VA-INFRA-001 5절).
 * 인증이 없어, 악성 페이지가 자기 도메인을 127.0.0.1로 돌리는 DNS 리바인딩은 바인딩만으로 못 막는다.
 * proxy.ts(`/api/*`)와 app/api/uploads/route.ts(올리기 — proxy에서 빠졌다)가 같이 쓴다.
 */
const ALLOWED = new Set(["localhost", "127.0.0.1", "[::1]"]);

/** 'localhost:3000' · '[::1]:3000' → 포트를 뗀 이름 */
function hostname(host: string | null): string {
  if (!host) return "";
  const name = host.startsWith("[") ? host.slice(0, host.indexOf("]") + 1) : host.split(":")[0];
  return name.toLowerCase();
}

/** 이 Host 헤더로 온 요청을 받는가 */
export function allowedHost(host: string | null): boolean {
  return ALLOWED.has(hostname(host));
}
