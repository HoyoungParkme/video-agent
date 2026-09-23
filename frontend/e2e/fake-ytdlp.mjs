#!/usr/bin/env node
// 가짜 yt-dlp — E2E의 api가 YTDLP_BIN으로 부른다(VA-MS-007 ytdlp.*). 영상 정보(JSON)와 자막(VTT)을
// 정해 둔 대로 준다. 네트워크에 닿지 않는다. 영상 ID는 e2e/*.spec.ts와 같은 값.
import { writeFileSync } from "node:fs";

const VIDEOS = {
  // 자막(수동 · 한국어) 있는 50분 발표 — S1
  e2eCaption1: { title: "RAG 서비스 1년 운영기", duration: 3012, subtitles: { ko: [] } },
  // 대기열 — 두 영상을 차례로
  e2eCaption2: { title: "벡터 검색 튜닝 실전", duration: 2285, subtitles: { ko: [] } },
  e2eCaption3: { title: "LLM 에이전트 설계 패턴", duration: 2400, subtitles: { ko: [] } },
  // 자막 없는 영상 — B1은 시작 불가 판 '아직 지원하지 않음'
  e2eNoCapt01: { title: "자막 없는 강연", duration: 1800, subtitles: {} },
};

const args = process.argv.slice(2);
const url = args[args.length - 1] ?? "";
const id = (url.match(/(?:v=|youtu\.be\/|shorts\/)([A-Za-z0-9_-]{11})/) ?? [])[1];
const video = id ? VIDEOS[id] : undefined;

if (!video) {
  process.stderr.write(`ERROR: [youtube] ${id}: Video unavailable\n`);
  process.exit(1);
}

/** 100초마다 한 줄 — 가짜 OpenAI의 시각(01:40 · 10:00 …)이 이 안에 든다. */
function vtt(duration) {
  const ts = (s) => {
    const two = (n) => String(n).padStart(2, "0");
    return `${two(Math.floor(s / 3600))}:${two(Math.floor((s % 3600) / 60))}:${two(s % 60)}.000`;
  };
  const cues = [];
  for (let s = 0, n = 1; s < duration; s += 100, n += 1) {
    cues.push(
      `${ts(s)} --> ${ts(Math.min(s + 90, duration))}\n${n}번째 문장 — 검색 품질 이야기를 이어 갑니다.`,
    );
  }
  return `WEBVTT\nKind: captions\nLanguage: ko\n\n${cues.join("\n\n")}\n`;
}

if (args.includes("--dump-single-json")) {
  process.stdout.write(
    JSON.stringify({
      id,
      title: video.title,
      channel: "E2E 채널",
      uploader: "E2E 채널",
      duration: video.duration,
      subtitles: video.subtitles,
      automatic_captions: {},
      language: "ko",
    }),
  );
  process.exit(0);
}

if (args.includes("--write-subs") || args.includes("--write-auto-subs")) {
  const out = args[args.indexOf("-o") + 1].replace("%(id)s", id);
  const lang = args[args.indexOf("--sub-langs") + 1];
  writeFileSync(`${out}.${lang}.vtt`, vtt(video.duration));
  process.exit(0);
}

process.stderr.write("ERROR: 가짜 yt-dlp가 모르는 호출\n");
process.exit(2);
