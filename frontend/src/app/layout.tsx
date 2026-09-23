/**
 * 뿌리 레이아웃 — 공통 1.4 키 없음 배너 · 1.1 헤더 · 페이지(VA-DOM-002 1장). 글꼴 파일은 앱 안에서 제공한다
 * — 앱을 쓰는 동안 글꼴 요청이 밖으로 나가지 않는다(VA-UI-001 3.2).
 */
import type { Metadata } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";

import Header from "@/components/Header";
import KeyBanner from "@/components/KeyBanner";
import "@/styles.css";

const serif = localFont({
  src: "../assets/Hahmlet-VF.woff2",
  weight: "500 600",
  variable: "--font-hahmlet",
  display: "swap",
});
const sans = localFont({
  src: [
    { path: "../assets/IBMPlexSansKR-Regular.woff2", weight: "400" },
    { path: "../assets/IBMPlexSansKR-Medium.woff2", weight: "500" },
    { path: "../assets/IBMPlexSansKR-SemiBold.woff2", weight: "600" },
  ],
  variable: "--font-plex-sans",
  display: "swap",
});
const mono = localFont({
  src: [
    { path: "../assets/IBMPlexMono-Medium.woff2", weight: "500" },
    { path: "../assets/IBMPlexMono-SemiBold.woff2", weight: "600" },
  ],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Video Agent",
  description: "영상을 넣으면 스크립트 · 핵심 요약 · 챕터를 만들고 질문에 답한다",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko" className={`${serif.variable} ${sans.variable} ${mono.variable}`}>
      <body>
        <KeyBanner />
        <Header />
        {children}
      </body>
    </html>
  );
}
