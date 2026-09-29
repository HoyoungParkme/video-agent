/**
 * 화면 설정 — standalone 출력(web 컨테이너) · `/api/*`를 api로 넘긴다(VA-DOM-002 1장).
 * 브라우저는 web 하나만 본다. 넘길 곳은 빌드 때 굳는다 — 이미지는 http://api:8000, 호스트 개발은 8001.
 */
import type { NextConfig } from "next";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8001";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // E2E는 따로 빌드한다 — 넘길 주소가 달라서(playwright.config.ts)
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  // 넘길 때 시간 제한 60초(기본 30초) — 가장 긴 요청인 질문이 키 다시 확인(10초)과 답(20초)을
  // 이어 기본값에 닿는다. 넘기면 화면은 실패인데 서버는 답을 저장한다(VA-DOM-002 6장)
  experimental: { proxyTimeout: 60_000 },
};

export default nextConfig;
