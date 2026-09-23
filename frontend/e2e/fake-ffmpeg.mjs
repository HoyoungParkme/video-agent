#!/usr/bin/env node
// 가짜 ffmpeg · ffprobe — E2E의 api가 FFMPEG_BIN · FFPROBE_BIN으로 부른다(VA-MS-007 ffmpeg.*).
// 한 파일이 인자 모양으로 역할을 가른다: -show_format 재기 · -af 무음 · -c copy 자르기 · -vn 추출.
// 미디어 파일은 길이 · 음성 유무를 담은 JSON 한 줄이다 — inbox의 가짜 파일도, 추출 · 자르기가 쓰는 파일도.
// JSON이 아니면 진짜 ffprobe처럼 "Invalid data"로 실패한다. 무음은 600초마다 5초 뒤에 둔다.
// `--make-inbox <폴더>`는 E2E inbox를 만든다(파일 이름은 e2e/*.spec.ts와 같은 값).
import { mkdirSync, readFileSync, utimesSync, writeFileSync } from "node:fs";
import path from "node:path";

// 이름 · 내용(길이 · 음성). 위에 있을수록 최근에 고친 파일 — 화면은 맨 위를 기본으로 고른다
const INBOX = [
  ["workshop_0912.mp4", { duration: 9000, audio: true }], // S2 — 2:30:00, 15조각
  ["lecture_0920.mp4", { duration: 5400, audio: true }], // S6 4번 — 1:30:00, 9조각
  ["call_0915.m4a", { duration: 1500, audio: true }], // 로컬 음성 — 대기열에서 다시 시도, 3조각
  ["memo_0917.wav", { duration: 1500, audio: true }], // 로컬 음성 — 받아쓰기 필요 판만(시작하지 않는다)
  ["silent_demo.mp4", { duration: 600, audio: false }], // 음성 트랙이 없다
  ["notes.mp4", null], // 영상 · 음성이 아니다(열 수 없다)
];

const args = process.argv.slice(2);

function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exit(1);
}

function media(file) {
  try {
    return JSON.parse(readFileSync(file, "utf8"));
  } catch {
    return fail(`${file}: Invalid data found when processing input`);
  }
}

function write(file, duration) {
  writeFileSync(file, JSON.stringify({ duration, audio: true }));
}

const after = (flag) => args[args.indexOf(flag) + 1];

if (args[0] === "--make-inbox") {
  const dir = args[1];
  mkdirSync(dir, { recursive: true });
  const now = Date.now() / 1000;
  INBOX.forEach(([name, info], i) => {
    const file = path.join(dir, name);
    // 이름을 넣어 내용을 서로 다르게 — 내용 해시가 출처 식별자다
    writeFileSync(file, info ? JSON.stringify({ name, ...info }) : "이건 영상이 아니다");
    utimesSync(file, now - i * 60, now - i * 60);
  });
  process.exit(0);
}

if (args.includes("-show_format")) {
  const info = media(args[args.length - 1]);
  const streams = [];
  if (!/\.(mp3|m4a|wav)$/.test(args[args.length - 1])) streams.push({ codec_type: "video" });
  if (info.audio) streams.push({ codec_type: "audio" });
  process.stdout.write(JSON.stringify({ format: { duration: String(info.duration) }, streams }));
  process.exit(0);
}

if (args.includes("-af")) {
  const { duration } = media(after("-i"));
  const lines = [];
  for (let t = 600; t < duration; t += 600) {
    lines.push(`[silencedetect @ 0x0] silence_start: ${t + 4}`);
    lines.push(`[silencedetect @ 0x0] silence_end: ${t + 6} | silence_duration: 2`);
  }
  process.stderr.write(`${lines.join("\n")}\n`);
  process.exit(0);
}

if (args.includes("-c") && after("-c") === "copy") {
  const { duration } = media(after("-i"));
  const start = Number(after("-ss"));
  const end = Math.min(Number(after("-to")), duration);
  write(args[args.length - 1], end - start);
  process.exit(0);
}

if (args.includes("-vn")) {
  const { duration } = media(after("-i"));
  write(args[args.length - 1], duration);
  process.exit(0);
}

fail("가짜 ffmpeg가 모르는 호출");
