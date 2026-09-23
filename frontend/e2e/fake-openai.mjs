// 가짜 OpenAI — E2E의 api가 여기로 보낸다(VA-MS-007 openai.client의 base_url).
// 키 확인(GET /v1/models): 맞는 키는 하나뿐이고 나머지는 인증 실패(401).
// 채팅(POST /v1/chat/completions): system 문구로 요약 · 챕터 · 추천 질문을 가려 정해 둔 JSON을 준다.
// 1시간 넘는 영상(챕터 지시에 '파트 2~5개')이면 파트로 묶은 챕터를 준다. 시각은 스크립트(100초마다 한 줄) 안에 든다.
// 받아쓰기(POST /v1/audio/transcriptions): 올라온 조각(가짜 ffmpeg가 쓴 길이 JSON)으로 100초마다 구간을 준다.
// 테스트는 /control로 채팅 · 받아쓰기 지연, 조각 하나를 몇 번 실패시킬지(500 또는 연결 끊기), 다음 채팅 몇 번을
// 실패시킬지를 정하고 부른 수 · 받은 조각을 읽는다.
import { createServer } from "node:http";

const port = Number(process.argv[2] ?? 8190);
const GOOD_KEY = "sk-e2e-good-000000000000000000"; // e2e/*.spec.ts와 같은 값

const state = {
  chatDelayMs: 0,
  chats: 0,
  transcriptions: 0,
  sttDelayMs: 0,
  sttFail: null, // { seq, times, drop? } — 그 조각을 times번 실패시킨다. drop이면 500 대신 연결을 끊는다
  chatFail: 0, // 다음 채팅 몇 번을 500으로
  transcribed: [], // 받아쓴 조각 번호(성공한 것), 받은 차례대로
};

const SUMMARY = {
  one_liner: "RAG 서비스를 1년 운영하며 검색 품질 문제를 찾고 고친 과정을 공유하는 발표.",
  insights: [
    { text: "틀린 답의 원인은 대부분 검색 단계에 있었다.", times: ["01:40"] },
    { text: "실제 질문 로그로 평가 세트부터 만들었다.", times: ["05:00"] },
    { text: "청킹 크기를 줄이자 재현율이 올랐다.", times: ["10:00", "11:40"] },
    { text: "pgvector로 원본 데이터와 같은 곳에서 관리했다.", times: ["20:00"] },
    { text: "재순위 후보 수를 줄여 지연을 되돌렸다.", times: ["30:00"] },
    { text: "가장 효과가 컸던 것은 사람이 읽는 주간 리뷰였다.", times: ["45:00"] },
  ],
};

const CHAPTERS = {
  parts: [],
  chapters: [
    {
      part: null,
      start: "00:00",
      title: "발표자 소개",
      bullets: ["팀과 서비스 소개", "오늘 주제는 검색 품질"],
    },
    {
      part: null,
      start: "10:00",
      title: "청킹 다시 보기",
      bullets: ["512에서 256 토큰으로", "재현율 12%p 상승"],
    },
    {
      part: null,
      start: "20:00",
      title: "pgvector 선택",
      bullets: ["원본과 같은 DB", "운영이 단순해졌다"],
    },
    {
      part: null,
      start: "30:00",
      title: "재순위와 지연",
      bullets: ["정확도는 올랐지만 느려졌다", "후보 수를 줄였다"],
    },
    {
      part: null,
      start: "40:00",
      title: "운영과 리뷰",
      bullets: ["바뀐 청크만 다시 임베딩", "매주 사람이 읽는다"],
    },
  ],
};

const QUESTIONS = {
  questions: [
    "청킹 전략을 바꾼 근거는?",
    "pgvector 대신 검토한 대안은?",
    "운영 비용은 어떻게 달라졌나?",
  ],
};

// 1시간 넘는 영상 — 파트 둘로 묶은 챕터. 스크립트 끝이 1시간을 넘어 시각이 h:mm:ss다
const CHAPTERS_LONG = {
  parts: [
    { title: "오전 세션 — 현황과 문제", start: "0:00:00" },
    { title: "오후 세션 — 실습과 정리", start: "1:15:00" },
  ],
  chapters: [
    { part: 1, start: "0:00:00", title: "워크숍 소개", bullets: ["오늘 목표", "진행 방식"] },
    {
      part: 1,
      start: "0:20:00",
      title: "데이터를 찾는 시간",
      bullets: ["묻고 기다린다", "같은 질문"],
    },
    { part: 1, start: "0:45:00", title: "카탈로그 후보", bullets: ["세 도구 비교", "기준 셋"] },
    { part: 2, start: "1:15:00", title: "실습 준비", bullets: ["계정 만들기", "샘플 데이터"] },
    {
      part: 2,
      start: "1:50:00",
      title: "메타데이터 채우기",
      bullets: ["설명 쓰기", "소유자 정하기"],
    },
    { part: 2, start: "2:20:00", title: "정리와 다음 단계", bullets: ["운영 방식", "다음 워크숍"] },
  ],
};

function send(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve) => {
    const parts = [];
    req.on("data", (chunk) => parts.push(chunk));
    req.on("end", () => resolve(Buffer.concat(parts)));
  });
}

async function readJson(req) {
  try {
    return JSON.parse((await readBody(req)).toString("utf8") || "{}");
  } catch {
    return {};
  }
}

/** 멀티파트에서 올라온 조각 — 파일 이름의 번호와 내용(가짜 ffmpeg가 쓴 길이 JSON). */
function uploaded(body) {
  const text = body.toString("latin1");
  const m = text.match(/filename="([^"]+)"[\s\S]*?\r\n\r\n([\s\S]*?)\r\n--/);
  const name = (m?.[1] ?? "").split(/[\\/]/).pop();
  let duration = 600;
  try {
    duration = JSON.parse(m?.[2] ?? "{}").duration ?? 600;
  } catch {
    // 모르는 모양이면 10분으로
  }
  return { seq: Number.parseInt(name, 10), duration };
}

function reply(system) {
  if (system.includes("파트 2~5개")) return CHAPTERS_LONG;
  if (system.includes("챕터를 나누는")) return CHAPTERS;
  if (system.includes("질문을 고르는")) return QUESTIONS;
  return SUMMARY;
}

createServer(async (req, res) => {
  if (req.url === "/health") return send(res, 200, { ok: true });
  if (req.url === "/control") {
    if (req.method === "POST") {
      const body = await readJson(req);
      // 비우기가 먼저 — 같은 요청의 설정값을 지우지 않게. 남은 실패도 비운다(앞 테스트가 도중에 끝났을 때)
      if (body.reset) {
        Object.assign(state, { chats: 0, transcriptions: 0, transcribed: [] });
        Object.assign(state, { sttFail: null, chatFail: 0 });
      }
      if (typeof body.chat_delay_ms === "number") state.chatDelayMs = body.chat_delay_ms;
      if (typeof body.stt_delay_ms === "number") state.sttDelayMs = body.stt_delay_ms;
      if (body.stt_fail !== undefined) state.sttFail = body.stt_fail;
      if (typeof body.chat_fail === "number") state.chatFail = body.chat_fail;
    }
    return send(res, 200, state);
  }
  if (req.method === "GET" && req.url?.startsWith("/v1/models")) {
    if (req.headers.authorization === `Bearer ${GOOD_KEY}`) {
      return send(res, 200, {
        object: "list",
        data: [{ id: "gpt-5-mini", object: "model", created: 0, owned_by: "openai" }],
      });
    }
    return send(res, 401, {
      error: {
        message: "Incorrect API key provided",
        type: "invalid_request_error",
        code: "invalid_api_key",
      },
    });
  }
  if (req.method === "POST" && req.url?.startsWith("/v1/chat/completions")) {
    const body = await readJson(req);
    state.chats += 1;
    const system = body.messages?.find((m) => m.role === "system")?.content ?? "";
    if (state.chatDelayMs) await new Promise((r) => setTimeout(r, state.chatDelayMs));
    if (state.chatFail > 0) {
      state.chatFail -= 1;
      return send(res, 500, {
        error: { message: "The server had an error", type: "server_error" },
      });
    }
    return send(res, 200, {
      id: "chatcmpl-e2e",
      object: "chat.completion",
      created: 0,
      model: body.model,
      choices: [
        {
          index: 0,
          message: { role: "assistant", content: JSON.stringify(reply(system)) },
          finish_reason: "stop",
        },
      ],
      usage: { prompt_tokens: 100, completion_tokens: 50, total_tokens: 150 },
    });
  }
  if (req.method === "POST" && req.url?.startsWith("/v1/audio/transcriptions")) {
    state.transcriptions += 1;
    const { seq, duration } = uploaded(await readBody(req));
    if (state.sttDelayMs) await new Promise((r) => setTimeout(r, state.sttDelayMs));
    if (state.sttFail && state.sttFail.seq === seq && state.sttFail.times > 0) {
      state.sttFail.times -= 1;
      if (state.sttFail.drop) return req.socket.destroy(); // 인터넷 끊김 — 응답 없이 연결이 끊긴다
      return send(res, 500, {
        error: { message: "The server had an error", type: "server_error" },
      });
    }
    state.transcribed.push(seq);
    const segments = [];
    for (let t = 0; t < duration; t += 100) {
      segments.push({
        start: t,
        end: Math.min(t + 90, duration),
        text: `${seq}번 조각 ${t}초 — 워크숍 이야기를 이어 갑니다.`,
      });
    }
    return send(res, 200, { task: "transcribe", language: "korean", duration, text: "", segments });
  }
  return send(res, 404, {
    error: { message: "가짜 서버에 없는 경로", type: "invalid_request_error" },
  });
}).listen(port, "127.0.0.1");
