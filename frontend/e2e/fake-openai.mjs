// 가짜 OpenAI — E2E의 api가 여기로 보낸다(VA-MS-007 openai.client의 base_url).
// 키 확인(GET /v1/models): 맞는 키는 하나뿐이고 나머지는 인증 실패(401).
// 채팅(POST /v1/chat/completions): system 문구로 요약 · 챕터 · 추천 질문을 가려 정해 둔 JSON을 준다.
// 시각은 가짜 yt-dlp 자막(100초마다 한 줄) 안에 든다. 받아쓰기는 부르면 안 된다 — 부른 수를 센다.
// 테스트는 /control로 채팅 지연을 바꾸고 부른 수를 읽는다.
import { createServer } from "node:http";

const port = Number(process.argv[2] ?? 8190);
const GOOD_KEY = "sk-e2e-good-000000000000000000"; // e2e/*.spec.ts와 같은 값

const state = { chatDelayMs: 0, chats: 0, transcriptions: 0 };

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

function send(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

function readJson(req) {
  return new Promise((resolve) => {
    let raw = "";
    req.on("data", (chunk) => (raw += chunk));
    req.on("end", () => {
      try {
        resolve(JSON.parse(raw || "{}"));
      } catch {
        resolve({});
      }
    });
  });
}

function reply(system) {
  if (system.includes("챕터를 나누는")) return CHAPTERS;
  if (system.includes("질문을 고르는")) return QUESTIONS;
  return SUMMARY;
}

createServer(async (req, res) => {
  if (req.url === "/health") return send(res, 200, { ok: true });
  if (req.url === "/control") {
    if (req.method === "POST") {
      const body = await readJson(req);
      if (typeof body.chat_delay_ms === "number") state.chatDelayMs = body.chat_delay_ms;
      if (body.reset) Object.assign(state, { chats: 0, transcriptions: 0 });
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
  if (req.url?.startsWith("/v1/audio/transcriptions")) {
    state.transcriptions += 1;
    return send(res, 500, { error: { message: "B1 E2E에서 받아쓰기를 부르면 안 된다" } });
  }
  return send(res, 404, {
    error: { message: "가짜 서버에 없는 경로", type: "invalid_request_error" },
  });
}).listen(port, "127.0.0.1");
