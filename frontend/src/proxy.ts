/**
 * 요청이 라우트에 닿기 전 — `/api/*`의 Host를 localhost · 127.0.0.1로 제한한다(VA-INFRA-001 5절).
 * 인증이 없어, 악성 페이지가 자기 도메인을 127.0.0.1로 돌리는 DNS 리바인딩은 바인딩만으로 못 막는다.
 * rewrites는 이 뒤에 돈다. api가 보는 Host는 넘긴 곳(api · 127.0.0.1)이라 브라우저의 Host는 여기서 본다.
 */
import { NextResponse, type NextRequest } from "next/server";

const ALLOWED = new Set(["localhost", "127.0.0.1", "[::1]"]);

/** 'localhost:3000' · '[::1]:3000' → 포트를 뗀 이름 */
function hostname(host: string | null): string {
  if (!host) return "";
  const name = host.startsWith("[") ? host.slice(0, host.indexOf("]") + 1) : host.split(":")[0];
  return name.toLowerCase();
}

export function proxy(request: NextRequest) {
  if (!ALLOWED.has(hostname(request.headers.get("host")))) {
    return new NextResponse("허용하지 않는 Host입니다", { status: 400 });
  }
  return NextResponse.next();
}

export const config = { matcher: "/api/:path*" };
