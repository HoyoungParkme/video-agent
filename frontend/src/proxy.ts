/**
 * 요청이 라우트에 닿기 전 — `/api/*`의 Host를 localhost · 127.0.0.1로 제한한다(VA-INFRA-001 5절, host.ts).
 * rewrites는 이 뒤에 돈다. api가 보는 Host는 넘긴 곳(api · 127.0.0.1)이라 브라우저의 Host는 여기서 본다.
 * `/api/uploads`만 뺀다 — proxy가 도는 요청은 Next가 본문을 메모리에 복제하고 10MB에서 자른다. 그 경로는
 * API 라우트(pages/api/uploads.ts)가 같은 판정을 하고 본문을 스트림으로 넘긴다(VA-INFRA-001 C4).
 */
import { NextResponse, type NextRequest } from "next/server";

import { allowedHost } from "@/host";

export function proxy(request: NextRequest) {
  if (!allowedHost(request.headers.get("host"))) {
    return new NextResponse("허용하지 않는 Host입니다", { status: 400 });
  }
  return NextResponse.next();
}

// 정확히 /api/uploads만 뺀다 — 그 아래 경로는 API 라우트가 받지 않아 넘기기로 가므로 Host를 여기서 본다
export const config = { matcher: "/api/((?!uploads$).*)" };
