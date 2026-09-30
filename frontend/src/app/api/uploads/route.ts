/**
 * POST /api/uploads — 화면이 아니다(VA-DOM-002 1장, VA-INFRA-001 C4). 다른 `/api/*`는 넘기기(rewrites)가
 * api로 보내지만, 그 앞의 Host 확인(proxy)이 도는 요청은 Next가 본문을 메모리에 복제하고 10MB에서
 * 자른다. 그래서 이 경로만 proxy에서 빠졌고, 여기서 같은 Host 판정(host.ts)을 한 뒤 본문을 버퍼에
 * 담지 않고 스트림 그대로 api에 넘기고 응답을 그대로 돌려준다. 판단은 없다.
 */
import { allowedHost } from "@/host";

// next.config.ts의 env가 빌드 때 굳힌다 — rewrites와 같은 곳(이미지는 http://api:8000)
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8001";
// api에 넘기는 요청 머리 — 본문 형식 · 크기 · 원래 파일 이름(VA-API-001 POST /api/uploads)
const PASSED = ["content-type", "content-length", "x-file-name"];

export async function POST(request: Request): Promise<Response> {
  if (!allowedHost(request.headers.get("host"))) {
    return new Response("허용하지 않는 Host입니다", { status: 400 });
  }
  const headers = new Headers();
  for (const name of PASSED) {
    const value = request.headers.get(name);
    if (value !== null) headers.set(name, value);
  }
  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/api/uploads`, {
      method: "POST",
      headers,
      body: request.body,
      signal: request.signal, // 화면이 멈추면(abort) api도 끊긴 것을 안다 — 받던 .part를 지운다
      // 본문을 스트림으로 보낼 때 Node의 fetch가 요구한다(요청을 다 보내기 전에 응답을 받을 수 있다)
      duplex: "half",
    } as RequestInit & { duplex: "half" });
  } catch {
    // api에 닿지 못했다 — 화면은 problem+json이 아닌 응답을 '서버에 연결할 수 없음'으로 본다
    return new Response("api에 연결할 수 없어요", { status: 502 });
  }
  const type = upstream.headers.get("content-type") ?? "application/json";
  return new Response(upstream.body, {
    status: upstream.status,
    headers: { "content-type": type },
  });
}
