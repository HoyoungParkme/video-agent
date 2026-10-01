// 가짜 OpenAI — E2E의 api가 여기로 보낸다(VA-MS-007 openai.client의 base_url).
// 키 확인(GET /v1/models): 맞는 키는 하나뿐이고 나머지는 인증 실패(401). /control의 models로 키 확인만
// 끊거나(drop — 인터넷 끊김) 맞는 키도 거절한다(401 — 저장한 뒤 키가 폐기됨).
// 채팅(POST /v1/chat/completions): system 문구로 요약 · 챕터 · 추천 질문 · 질문 답변을 가려 JSON을 준다.
// 답변은 받은 스크립트의 첫 · 끝 시각과 앞선 턴으로 흉내 내고, 받은 것을 기록(asks)에 남긴다.
// 1시간 넘는 영상(챕터 지시에 '파트 2~5개')이면 파트로 묶은 챕터를 준다. 시각은 스크립트(100초마다 한 줄) 안에 든다.
// 받아쓰기(POST /v1/audio/transcriptions): 올라온 조각(가짜 ffmpeg가 쓴 길이 JSON)으로 100초마다 구간을 준다.
// 이미지(POST /v1/images/generations): 작은 PNG(64×96) 한 장을 b64로 준다. 받은 프롬프트를 남긴다.
// 테스트는 /control로 채팅 · 받아쓰기 · 이미지 지연, 조각 하나를 몇 번 실패시킬지(500 또는 연결 끊기), 다음 채팅
// 몇 번을 실패시킬지, 다음 이미지를 서버 오류(500) · 안전 정책 거절(400 moderation_blocked)로 할지를 정하고 부른
// 수 · 받은 조각을 읽는다.
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
  models: null, // 키 확인 — null이면 보통, "drop"이면 연결을 끊고, 401이면 맞는 키도 거절한다
  transcribed: [], // 받아쓴 조각 번호(성공한 것), 받은 차례대로
  asks: [], // 답한 질문마다 { question, history(앞선 턴 수), first, last(받은 스크립트의 첫 · 끝 시각) }
  imageDelayMs: 0,
  imageFail: null, // 다음 이미지 한 번 — "server"(500) · "moderation"(400 moderation_blocked)
  images: [], // 받은 이미지 요청마다 { model, size, quality, prompt }
};

// 64×96 PNG(세로 2:3) — 진짜 ffmpeg로 만든 것
const PNG_B64 =
  "iVBORw0KGgoAAAANSUhEUgAAAEAAAABgCAIAAAAip+O/AAAACXBIWXMAAAABAAAAAQBPJcTWAAAE8klEQVR4nM2WeVfaQBRH8w3KEkIIrVVw33Hrpq2CKK5VW61awX3p+v3/7JvJJJlJgDwqCe+cfIB757z8ztVe/H2K7/vz+OLXfeLnXeLHbeLpJvFwnbi/TNw1krf15PVF8uo8eXmWrJ+mLr6lvp+kzr+mTr+kvh2lTg7TxwfpL/vpo7304W76YEff39b3avrupr6zocVL/6DSX0n03xl9w6U/Tp1J9F8/u/Tpz0C/ZdPr29W4BID+N9DfC/pHm/6S0d/Y9OdAn6y79PD8Ej08v0u/D/Q1m17fWo9FgNOz4/lxJ+gfJPprm/6M0V+49PD8Ej08fzP6zGYlegGXHo7n6VbQ3wN9Q9Bf2fSnKv2RSr8r6OH0dzZter1WyWyUoxdoSV9X6eF4PHp2PC79oUQPp7+9Ieg3y5nqWsQCv6XZebyx6dmPe9Pp7Gy5s6NvVQX9xlpmfTVKgZDRbD87++rs1NzZ0WvrLn2m8ikyATE7d+rsNLCz02I0OX2F0VcZfab8MRoBb3Zum8zOlTQ7HY4mpy8z+nVGn1lbiUCg5Wg21NE8RY1mYHbgx2X0FUZvrC53W6DdaNb9o6nMzgFydvjpC3rj04duC7j04bNzrM6OTL+j0lf99GVBb3x831WBCFqN0yuzA/SZNUFvrLzrnkA0rebRO7PD6FcFvbH8tksCkbWaN5rO7Mj0xoc33RCIstV8o8lP36M33i89WyDiVvONJj99jz77bvHZAhG3WnB2jBWPPvt2/nkC0bdacHaMZZd+Ibs09wyBWFpNzE5T+jfz2cXS/wrE1WqB2ZHol+ayC7P/JRBjqzF6ZXYk+sVSdn6mc4F4W43RK7Mj08+ac9MdCsTear7R9OgXgH7GLE11KBB7q6mjueDSw/GYpWlzdrITgV60WnB2BP0c0E+ZMxNogR61WnB2ZHpzehwn0LtWU+lLgr4E9JNAb06NIQR62mq+0RT0s0A/AfTm5GiYQK9bTZ0dhx6OZ2oc6HMTI2ECvW41dXYcejieyTGgz40PtxUg0Gq+0ZToR4E+NzbUWoBGqwVnB06f048AfW50sIUAmVYLzg47fUY/DPS5kWIzAUqtFpwddvoOfW6oEBAg1moS/bhEP8TohwvW4IDWnJ5Mq0mjKWaH0w8CfW5owCr2qwL0Ws03muzHZfRFRj/YbxVea+jZ6U2rSbMzbM8Opy/Y9NZAnybRU2w132g69HA8jN7qf6URbzXfaDr08PyM3nr9UiPeasHZ4fTw/Ize6strxFstODv26Vv9jD7/ytKIt5pDX2xKn3+Z04i3mkPvzQ4/fUGfz5sa8Vbz6IsuPTy/oM9bWY14q3mjWXDp4fkFPReg3Wq+0RSn79BzAdqt5htNcfoOPReg3WrB2ZGfnwvQbrXg7Mj0TIB4q9mn34qeC9BuNXH6Lei5AO1WC85OQIB2q/HjaUnPBWi3mm80mwnQbrU2xyMEiLdae3ouQLvVEAK0Ww0hQLvVEAK0Ww0hQLvVEAK0Wy1cgHirIQRotxpCgHarIQRotxpCgHarIQRot1q4APFWQwjQbjWEAO1WQwjQbjWEAO1WQwjQbjWEAO1WCxcg3moIAdqthhCg3WoIAdqthhCg3WoIAdqthhCg3WrhAsRbDSFAu9UQArRbDSFAu9UQArRbDSFAu9XCBYi3GkKAdqshBGi3GkKAdqshBGi3Wuj3D2iVyfYz+WogAAAAAElFTkSuQmCC";

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
  // `8_012.mp3` → 조각 8 · 토막 12. 토막 번호가 없으면 0(첫 토막)
  const piece = Number(name.match(/_(\d+)\./)?.[1] ?? 0);
  return { seq: Number.parseInt(name, 10), piece, duration };
}

/**
 * 질문 답변 — 마지막 user 메시지의 `<transcript>` 줄에서 첫 · 끝 시각을, 앞선 턴에서 직전 질문을 읽는다.
 * '매출'을 물으면 영상에 없는 답(시각을 하나 붙여 어댑터가 비우는지 본다), 아니면 첫 · 둘째 시각이 근거다.
 */
function answer(messages) {
  const last = messages.at(-1)?.content ?? "";
  const m = last.match(/<transcript>\n([\s\S]*?)\n<\/transcript>\n\n([\s\S]*)$/);
  const script = m?.[1] ?? "";
  const question = m?.[2] ?? "";
  const times = [...script.matchAll(/^\[([\d:]+)\]/gm)].map((t) => t[1]);
  const history = Math.max(0, (messages.length - 2) / 2); // system + (user, assistant) × n + 마지막 user
  const previous = history > 0 ? messages.at(-3)?.content : null;
  state.asks.push({ question, history, first: times[0] ?? null, last: times.at(-1) ?? null });
  if (question.includes("매출")) {
    return {
      answer: "이 영상에서는 다루지 않습니다. 발표자 회사의 매출 이야기는 나오지 않아요.",
      times: times.slice(0, 1),
    };
  }
  const lead = previous ? `앞선 질문('${previous}')에 이어 답합니다. ` : "";
  return {
    answer: `${lead}'${question}'에 대한 답입니다 — 스크립트 ${times[0]}부터 ${times.at(-1)}까지를 봤어요.`,
    times: times.slice(0, 2),
  };
}

function reply(system, messages) {
  if (system.includes("근거로 질문에 답하는")) return answer(messages);
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
        Object.assign(state, {
          chats: 0,
          transcriptions: 0,
          transcribed: [],
          asks: [],
          images: [],
        });
        Object.assign(state, { sttFail: null, chatFail: 0, models: null, imageFail: null });
        state.imageDelayMs = 0;
      }
      if (typeof body.chat_delay_ms === "number") state.chatDelayMs = body.chat_delay_ms;
      if (typeof body.stt_delay_ms === "number") state.sttDelayMs = body.stt_delay_ms;
      if (body.stt_fail !== undefined) state.sttFail = body.stt_fail;
      if (typeof body.chat_fail === "number") state.chatFail = body.chat_fail;
      if (body.models !== undefined) state.models = body.models;
      if (typeof body.image_delay_ms === "number") state.imageDelayMs = body.image_delay_ms;
      if (body.image_fail !== undefined) state.imageFail = body.image_fail;
    }
    return send(res, 200, state);
  }
  if (req.method === "GET" && req.url?.startsWith("/v1/models")) {
    if (state.models === "drop") return req.socket.destroy(); // 인터넷 끊김
    if (state.models === null && req.headers.authorization === `Bearer ${GOOD_KEY}`) {
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
          message: {
            role: "assistant",
            content: JSON.stringify(reply(system, body.messages ?? [])),
          },
          finish_reason: "stop",
        },
      ],
      usage: { prompt_tokens: 100, completion_tokens: 50, total_tokens: 150 },
    });
  }
  if (req.method === "POST" && req.url?.startsWith("/v1/images/generations")) {
    const body = await readJson(req);
    state.images.push({
      model: body.model,
      size: body.size,
      quality: body.quality,
      prompt: body.prompt,
    });
    if (state.imageDelayMs) await new Promise((r) => setTimeout(r, state.imageDelayMs));
    const fail = state.imageFail;
    state.imageFail = null; // 다음 한 번만
    if (fail === "server") {
      return send(res, 500, {
        error: { message: "The server had an error", type: "server_error" },
      });
    }
    if (fail === "moderation") {
      return send(res, 400, {
        error: {
          message: "Your request was rejected by the safety system.",
          type: "image_generation_user_error",
          code: "moderation_blocked",
        },
      });
    }
    return send(res, 200, {
      created: 0,
      data: [{ b64_json: PNG_B64 }],
      usage: { input_tokens: 320, output_tokens: 272, total_tokens: 592 },
    });
  }
  if (req.method === "POST" && req.url?.startsWith("/v1/audio/transcriptions")) {
    // 앱은 10분 조각을 15초 이하 토막으로 나눠 보낸다(VA-MS-006 stt_openai) — 파일 이름 `{조각}_{토막}.mp3`.
    // 조각 단위로 세고 늦추고 실패시킨다: 첫 토막(_000)만. 첫 토막이 실패하면 그 조각이 실패한다
    const { seq, piece, duration } = uploaded(await readBody(req));
    const first = piece === 0;
    if (first) {
      state.transcriptions += 1;
      if (state.sttDelayMs) await new Promise((r) => setTimeout(r, state.sttDelayMs));
      if (state.sttFail && state.sttFail.seq === seq && state.sttFail.times > 0) {
        state.sttFail.times -= 1;
        if (state.sttFail.drop) return req.socket.destroy(); // 인터넷 끊김 — 응답 없이 연결이 끊긴다
        return send(res, 500, {
          error: { message: "The server had an error", type: "server_error" },
        });
      }
      state.transcribed.push(seq);
    }
    // gpt-transcribe는 json만 준다 — 글 · 감지한 언어 · 쓴 초(시각은 앱이 토막 경계로)
    return send(res, 200, {
      text: `${seq}번 조각 ${piece}번 토막 — 워크숍 이야기를 이어 갑니다.`,
      languages: [{ code: "ko" }],
      usage: { type: "duration", seconds: Math.ceil(duration) },
    });
  }
  return send(res, 404, {
    error: { message: "가짜 서버에 없는 경로", type: "invalid_request_error" },
  });
}).listen(port, "127.0.0.1");
