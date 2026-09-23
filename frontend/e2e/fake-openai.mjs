// 가짜 OpenAI — E2E의 api가 키 확인(GET /v1/models)을 여기로 보낸다(VA-MS-007 openai.client의 base_url).
// 맞는 키는 하나뿐이고, 나머지는 인증 실패(401)다.
import { createServer } from "node:http";

const port = Number(process.argv[2] ?? 8190);
const GOOD_KEY = "sk-e2e-good-000000000000000000"; // e2e/first-run.spec.ts와 같은 값

function send(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

createServer((req, res) => {
  if (req.url === "/health") return send(res, 200, { ok: true });
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
  return send(res, 404, {
    error: { message: "가짜 서버에 없는 경로", type: "invalid_request_error" },
  });
}).listen(port, "127.0.0.1");
