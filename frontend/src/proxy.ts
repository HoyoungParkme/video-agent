/**
 * 요청이 라우트에 닿기 전 — `/api/*`의 Host를 localhost · 127.0.0.1로 제한한다(VA-INFRA-001 5절, host.ts).
 * rewrites는 이 뒤에 돈다. api가 보는 Host는 넘긴 곳(api · 127.0.0.1)이라 브라우저의 Host는 여기서 본다.
 */
import { NextResponse, type NextRequest } from "next/server";

import { allowedHost } from "@/host";

export function proxy(request: NextRequest) {
  if (!allowedHost(request.headers.get("host"))) {
    return new NextResponse("허용하지 않는 Host입니다", { status: 400 });
  }
  return NextResponse.next();
}

export const config = { matcher: "/api/:path*" };
