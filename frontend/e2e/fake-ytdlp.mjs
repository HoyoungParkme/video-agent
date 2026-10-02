#!/usr/bin/env node
// 가짜 yt-dlp — E2E의 api가 YTDLP_BIN으로 부른다(VA-MS-007 ytdlp.*). 영상 정보(JSON)와 자막(VTT)을
// 정해 둔 대로 준다. 음성 내려받기는 가짜 ffmpeg가 읽는 모양의 파일을 쓴다. 네트워크에 닿지 않는다.
// 영상 정보에는 스토리보드 형식(sb0 — 320×180 칸, 장마다 3 × 3, 10분에 한 장)이 있다. storyboard: false면
// 없고, frameDelayMs를 주면 장 주소에 붙여 가짜 ffmpeg가 칸마다 그만큼 늦게 자른다.
// 영상 ID는 e2e/*.spec.ts와 같은 값.
import { writeFileSync } from "node:fs";

const VIDEOS = {
  // 자막(수동 · 한국어) 있는 50분 발표 — S1
  e2eCaption1: { title: "RAG 서비스 1년 운영기", duration: 3012, subtitles: { ko: [] } },
  // 대기열 — 두 영상을 차례로
  e2eCaption2: { title: "벡터 검색 튜닝 실전", duration: 2285, subtitles: { ko: [] } },
  e2eCaption3: { title: "LLM 에이전트 설계 패턴", duration: 2400, subtitles: { ko: [] } },
  // 서버에 잠깐 닿지 못해도 화면이 다시 받는다 — UI-3 · UI-4
  e2eCaption4: { title: "임베딩 모델 고르기", duration: 1500, subtitles: { ko: [] } },
  // 요약 단계에서 실패 → 그 단계부터 다시 시도 — S6 4번
  e2eCaption5: { title: "평가 세트 만드는 법", duration: 1200, subtitles: { ko: [] } },
  // 영상에 질문하기 — S4
  e2eAskVid01: { title: "RAG 검색 품질 회고", duration: 3000, subtitles: { ko: [] } },
  // 탭을 오가도 읽던 대화 위치(카드 E6)
  e2eChatPos1: { title: "읽던 자리를 지키는 대화", duration: 1800, subtitles: { ko: [] } },
  // 3시간 — 10초마다 70자 줄이라 대화 토큰 상한(3만)을 넘는다. 질문과 맞는 챕터만 보낸다
  e2eLong3h01: {
    title: "데이터 카탈로그 워크숍 종일",
    duration: 10800,
    subtitles: { ko: [] },
    step: 10,
    width: 70,
  },
  // 키보드로 보는 3시간 워크숍 — 한눈에 보기 세 줄(파트 · 점 · 막대)과 탭(a11y)
  e2eA11yLng1: { title: "키보드로 보는 워크숍", duration: 10800, subtitles: { ko: [] } },
  // 시각을 고른 뒤의 자리 · 주소 ?t= — 37.5초마다라 구간 시각 절반이 소수다(카드 E6)
  e2eScroll01: { title: "주소에 남는 시각", duration: 3000, subtitles: { ko: [] }, step: 37.5 },
  // 영상 같이 보기 — 재생 판 · 그 시각부터 · 접기 · 재생할 수 없음(카드 E7)
  e2ePlayer01: { title: "같이 보는 발표", duration: 3000, subtitles: { ko: [] } },
  // 며칠 뒤 다시 열어 묻고 내보내고 지운다 — S5
  e2eNoteVid1: { title: "벡터 DB 운영 노트", duration: 1800, subtitles: { ko: [] } },
  // 대기열에서 지운다 — 도는 영상 · 기다리는 영상 둘(s5)
  e2eDelRun01: { title: "지울 영상 — 도는 중", duration: 1200, subtitles: { ko: [] } },
  e2eDelWait1: { title: "지울 영상 — 기다리는 중", duration: 1200, subtitles: { ko: [] } },
  e2eDelWait2: { title: "뒤에 기다리는 영상", duration: 1200, subtitles: { ko: [] } },
  // 자막 없는 영상 — 받아쓰기 필요 판(s1)
  e2eNoCapt01: { title: "자막 없는 강연", duration: 1800, subtitles: {} },
  // 자막 없는 영상을 끝까지 — 음성 내려받기 · 추출 · 받아쓰기(대기열에서 다시 시도의 앞 영상)
  e2eNoCapt02: { title: "자막 없는 좌담", duration: 1200, subtitles: {} },
  // 잘 안 되는 경우들 — S6. 비공개 영상은 yt-dlp가 표준 오류로 알린다
  e2ePrivate1: { error: "Private video. Sign in if you've been granted access to this video" },
  e2eLong4h01: { title: "하루 종일 컨퍼런스 녹화", duration: 15150, subtitles: { ko: [] } }, // 4:12:30
  e2eOffline1: { title: "연결이 돌아온 뒤의 발표", duration: 1500, subtitles: { ko: [] } },
  e2eJobExst1: { title: "다른 창에서 시작한 발표", duration: 1500, subtitles: { ko: [] } },
  e2eDirect01: { title: "주소로 바로 여는 발표", duration: 1500, subtitles: { ko: [] } },
  // 챕터 대표 장면 — 칸을 천천히 잘라 진행 화면에서 장면 칸이 차는 것을 본다(frames)
  e2eFrames01: {
    title: "장면이 있는 발표",
    duration: 3012,
    subtitles: { ko: [] },
    frameDelayMs: 500,
  },
  // 스토리보드가 없다 — 장면 없이 끝난다(frames)
  e2eNoBoard1: {
    title: "스토리보드 없는 발표",
    duration: 3012,
    subtitles: { ko: [] },
    storyboard: false,
  },
  // 장면 단계 전에 분석한 결과처럼 — 장면을 지운 뒤 열어 채운다(frames)
  e2eOldRes01: { title: "장면을 나중에 채우는 발표", duration: 3012, subtitles: { ko: [] } },
  e2eOldRes02: {
    title: "채우다 지우는 발표",
    duration: 3012,
    subtitles: { ko: [] },
    frameDelayMs: 800,
  },
  e2eOldRes03: { title: "채우기가 장면 없이 끝나는 발표", duration: 3012, subtitles: { ko: [] } },
  // 인포그래픽(infographic) — 만들고 크게 보고 노트로 · 떠났다 돌아오기 · 실패 · 키 없음 · 품질 바꾸기
  e2eInfogr01: { title: "인포그래픽을 만드는 발표", duration: 3012, subtitles: { ko: [] } },
  e2eInfogr02: { title: "그리는 동안 떠나는 발표", duration: 3012, subtitles: { ko: [] } },
  e2eInfogr03: { title: "그리기가 실패하는 발표", duration: 3012, subtitles: { ko: [] } },
  e2eInfogr04: { title: "키 없이 그리려는 발표", duration: 3012, subtitles: { ko: [] } },
  e2eInfogr05: { title: "품질을 바꾸는 발표", duration: 3012, subtitles: { ko: [] } },
  e2eInfogr06: { title: "실패 뒤에 거절되는 발표", duration: 3012, subtitles: { ko: [] } },
  e2eInfogr07: { title: "두 창에서 그리는 발표", duration: 3012, subtitles: { ko: [] } },
};

// 스토리보드 — 칸 320×180, 장마다 3 × 3칸, 칸 하나가 600 / 9초(장 하나가 10분)
const SB_FPS = 9 / 600;

function storyboard(id, video) {
  if (video.storyboard === false) return [];
  const sheets = Math.ceil(Math.ceil(video.duration * SB_FPS) / 9);
  const delay = video.frameDelayMs ? `?delay=${video.frameDelayMs}` : "";
  return [
    {
      format_id: "sb0",
      format_note: "storyboard",
      width: 320,
      height: 180,
      rows: 3,
      columns: 3,
      fps: SB_FPS,
      fragments: Array.from({ length: sheets }, (_, i) => ({
        url: `https://e2e.invalid/sb/${id}/M${i}.jpg${delay}`,
      })),
    },
  ];
}

const args = process.argv.slice(2);
const url = args[args.length - 1] ?? "";
const id = (url.match(/(?:v=|youtu\.be\/|shorts\/)([A-Za-z0-9_-]{11})/) ?? [])[1];
const video = id ? VIDEOS[id] : undefined;

if (!video) {
  process.stderr.write(`ERROR: [youtube] ${id}: Video unavailable\n`);
  process.exit(1);
}

if (video.error) {
  process.stderr.write(`ERROR: [youtube] ${id}: ${video.error}\n`);
  process.exit(1);
}

/**
 * step초마다 한 줄(기본 100초 — 가짜 OpenAI의 시각 01:40 · 10:00 …이 이 안에 든다). step이 소수면
 * 줄 시각도 소수다. width를 주면 줄을 그 글자 수로 채운다 — 긴 스크립트를 만든다.
 */
function vtt({ duration, step = 100, width }) {
  const ts = (s) => {
    const two = (n) => String(n).padStart(2, "0");
    const total = Math.round(s * 1000); // 밀리초로 먼저 반올림 — .9995가 1000ms로 넘치지 않게
    const whole = Math.floor(total / 1000);
    const ms = String(total % 1000).padStart(3, "0");
    return `${two(Math.floor(whole / 3600))}:${two(Math.floor((whole % 3600) / 60))}:${two(whole % 60)}.${ms}`;
  };
  const cues = [];
  for (let s = 0, n = 1; s < duration; s += step, n += 1) {
    const text = `${n}번째 문장 — 검색 품질 이야기를 이어 갑니다.`;
    const line = width ? text.padEnd(width, " 이어서") : text;
    cues.push(`${ts(s)} --> ${ts(Math.min(s + Math.round(step * 0.9), duration))}\n${line}`);
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
      formats: storyboard(id, video),
    }),
  );
  process.exit(0);
}

if (args.includes("--write-subs") || args.includes("--write-auto-subs")) {
  const out = args[args.indexOf("-o") + 1].replace("%(id)s", id);
  const lang = args[args.indexOf("--sub-langs") + 1];
  writeFileSync(`${out}.${lang}.vtt`, vtt(video));
  process.exit(0);
}

if (args.includes("-f") && args[args.indexOf("-f") + 1] === "bestaudio") {
  // 음성 내려받기 — 가짜 ffmpeg가 읽는 모양(길이를 담은 JSON)으로 source.m4a를 쓴다
  const out = args[args.indexOf("-o") + 1].replace("%(ext)s", "m4a");
  writeFileSync(out, JSON.stringify({ duration: video.duration, audio: true }));
  process.exit(0);
}

process.stderr.write("ERROR: 가짜 yt-dlp가 모르는 호출\n");
process.exit(2);
