/**
 * POST /api/uploads — 화면이 아니다(VA-DOM-002 1장, VA-INFRA-001 C4). 다른 `/api/*`는 넘기기(rewrites)가
 * api로 보내지만, 그 앞의 Host 확인(proxy)이 도는 요청은 Next가 본문을 메모리에 복제하고 10MB에서
 * 자른다. 그래서 이 경로만 proxy에서 빠졌고, 여기서 같은 Host 판정(host.ts)을 한 뒤 Node 요청을 그대로
 * api 요청에 흘려보내고(pipe — 받는 쪽이 느리면 보내는 쪽을 멈춘다) 응답을 그대로 돌려준다. 판단은 없다.
 * App Router 라우트 핸들러가 아니라 Pages Router API 라우트인 것은 라우트 핸들러가 본문을 받는 쪽
 * 속도와 상관없이 읽어 들여 web 메모리에 쌓기 때문이다(카드 D4 실측 — 300MB에 +344MB, 이 라우트는
 * 1GB에 +70MB 안). `src/pages/`에는 이것 하나뿐이다 — 화면은 App Router다.
 */
import http from "node:http";

import type { NextApiRequest, NextApiResponse } from "next";

import { allowedHost } from "@/host";

// next.config.ts의 env가 빌드 때 굳힌다 — rewrites와 같은 곳(이미지는 http://api:8000)
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8001";
// api에 넘기는 요청 머리 — 본문 형식 · 크기 · 원래 파일 이름(VA-API-001 POST /api/uploads)
const PASSED = ["content-type", "content-length", "x-file-name"];

// 본문을 Next가 읽지 않게(그대로 흘려보낸다), 응답 크기 경고 없이
export const config = { api: { bodyParser: false, responseLimit: false } };

export default function handler(req: NextApiRequest, res: NextApiResponse): Promise<void> {
  return new Promise((resolve) => {
    if (!allowedHost(req.headers.host ?? null)) {
      res.status(400).send("허용하지 않는 Host입니다");
      return resolve();
    }
    const headers: Record<string, string> = {};
    for (const name of PASSED) {
      const value = req.headers[name];
      if (typeof value === "string") headers[name] = value;
    }
    const upstream = http.request(`${API_URL}/api/uploads`, { method: "POST", headers }, (up) => {
      const type = up.headers["content-type"] ?? "application/json";
      res.writeHead(up.statusCode ?? 502, { "content-type": type });
      up.pipe(res);
      up.on("end", resolve);
      up.on("error", () => resolve());
    });
    upstream.on("error", () => {
      // api에 닿지 못했다 — 화면은 problem+json이 아닌 응답을 '서버에 연결할 수 없음'으로 본다
      if (!res.headersSent) res.status(502).send("api에 연결할 수 없어요");
      else res.destroy();
      resolve();
    });
    // 화면이 멈추면(abort) 다 받기 전에 끊긴다 — api 요청도 끊어 받던 .part를 지우게 한다
    req.on("close", () => {
      if (!req.complete) upstream.destroy();
    });
    req.pipe(upstream);
  });
}
