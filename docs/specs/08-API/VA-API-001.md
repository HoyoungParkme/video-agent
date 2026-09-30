---
doc_id: VA-API-001
type: API
title: API 명세 REST — 영상 분석 에이전트
status: draft
upstream: [VA-UI-002, VA-UI-001, VA-UC-001, VA-DOM-001, VA-INFRA-001]
---

# API 명세 — 웹 REST: 영상 분석 에이전트

---

## 0. 이 문서가 다루는 것

브라우저(Next.js)가 부르는 REST API다. 와이어프레임의 화면 9개([[VA-UI-002]])가 서버에서 받아야 하는 값과 서버에 시켜야 하는 일을 엔드포인트로 옮겼다. 입구는 웹 하나뿐이라 MCP 문서는 없다([[VA-INFRA-001#C10]]).

엔드포인트는 23개, 묶음은 여섯이다 — 설정과 키 · inbox · 영상 · 작업 · 결과와 내보내기 · 대화. 결과를 그림으로 보이는 요구와 로컬 파일 끌어 놓기(2026-09-29, [[VA-PRD-001#R1]] · [[VA-PRD-001#R11]] ~ [[VA-PRD-001#R13]])로 일곱을 더했다 — 파일 올리기 하나(영상 묶음), 장면 셋 · 인포그래픽 셋(결과 묶음). 한눈에 보기는 이미 있는 결과로 화면이 그려 입구가 없다. 뒤 넷은 [[VA-DOM-001]] 4장의 묶음(video · job · analysis · chat)과 같고, 설정과 inbox는 도메인이 아니라 인프라 값을 읽고 쓰는 곳이다([[VA-INFRA-001#C4]], [[VA-INFRA-001#C6]]).

이 문서가 정하는 것: 경로·메서드·요청과 응답의 모양·에러·호출 순서. 정하지 않는 것: 서비스 메서드의 안(MINISPEC), 테이블(ERD), 화면 문구(와이어프레임).

---

## 1. 규칙

- 인증이 없다. 서버는 `127.0.0.1`에만 묶이고 사용자는 한 명이다([[VA-INFRA-001#C5]]). 모든 경로는 `/api/` 아래이고 요청·응답은 JSON이다([[VA-INFRA-001#C10]]). 예외는 셋 — [[#POST/api/uploads]]의 요청 본문은 파일 그대로(`application/octet-stream`)이고, 장면 · 인포그래픽 그림(`…/frames/{seq}` · `…/infographic/image`)은 `image/jpeg` · `image/png`로 준다.
- 에러는 RFC 9457 `application/problem+json`이다. `type`은 `urn:va:{종류}`이고 종류별 확장 필드는 2장에 있다.
- 때를 나타내는 값(`*_at`)은 ISO 8601 UTC다. **영상 속 시각(`*_sec`)은 초 단위 숫자**이고 소수를 허용한다. `mm:ss`·`h:mm:ss` 표기는 화면이 한다([[VA-UI-001#UI-4]] 시각 표기).
- 식별자는 정수 `id`다. 화면 주소 `/videos/{id}`의 id와 같은 값이다([[VA-UI-001#UI-3]], [[VA-UI-001#UI-4]]).
- 목록에 페이지가 없다. 사용자 한 명이 분석한 영상은 수십 개다.
- **화면은 계산하지 않는다.** 예상 시간·비용·조각 수·동시 수·남은 시간·진행률은 서버가 준 숫자를 그대로 보인다([[VA-UI-002#UI-2]]·[[VA-UI-002#UI-3]] 규칙). 문장을 조립하는 것은 화면이고, 서버는 코드값과 숫자, 그리고 실패 이유 한 줄(`reason`, 한국어)을 준다.
- **키 없이도 읽기는 전부 된다.** OpenAI API 키가 없거나 확인에 실패해도 GET은 모두 동작한다. 막히는 것은 분석 시작·다시 시도·질문·파일 올리기·인포그래픽 만들기 다섯뿐이고, 그때 `key-missing` 또는 `key-invalid`(503)가 난다([[VA-UI-002]] 1.4 키 없음 배너, [[VA-PRD-001#N3]]).
- 키를 확인하는 때는 다섯이다 — 서버가 시작할 때, [[#POST/api/videos]](분석 버튼)와 [[#POST/api/uploads]](파일 올리기, 본문을 읽기 전)를 받을 때, [[#POST/api/settings/key]]를 받을 때, [[#POST/api/videos/{id}/infographic]]을 받을 때. [[#GET/api/settings]]는 마지막 확인 결과를 돌려줄 뿐 다시 확인하지 않는다([[VA-UI-002#UI-5]] 규칙).
- **마지막 확인이 연결 실패(`reason_kind = network`)였으면 막지 않고 그때 한 번 다시 확인한다.** 분석 시작·다시 시도·질문이 그렇다. 키가 틀린 것이 아니라 인터넷이 없었거나 OpenAI가 잠시 답하지 못한 것(5xx · 요청 한도)이라, 화면은 버튼을 막지 않고 배너 문구만 가른다([[VA-UI-002]] 1.4). 다시 확인해 통과하면 요청이 그대로 이어지고, 또 닿지 못하면 503 `key-invalid`(`reason_kind = network`)다.
- **동시에 도는 분석은 하나이고 나머지는 대기열에서 차례를 기다린다**([[VA-PRD-001#R8]], [[VA-INFRA-001]] 3절). 시작 요청은 거절되지 않는다 — 도는 작업이 있으면 `status = queued`로 들어가고, 앞 작업이 끝나면(완료든 실패든) 서버가 가장 오래 기다린 것을 저절로 시작한다.
- 진행 상태는 폴링이다. 화면이 1초마다 [[#GET/api/videos/{id}/job]]을 부른다([[VA-INFRA-001]] 3절). SSE·WebSocket은 없다. 결과 화면의 뒤 일(장면 채우기 · 인포그래픽 그리기)도 폴링이다 — 그동안 화면이 3초마다 [[#GET/api/videos/{id}/frames]] · [[#GET/api/videos/{id}/infographic]]을 부른다([[VA-UI-002]] 2장 미결의 간격).
- 밖으로 나가는 것은 YouTube에 영상 ID(정보 · 자막 · 음성 · 미리 보기 썸네일), OpenAI에 음성 조각·스크립트 텍스트·질문과 앞선 대화·인포그래픽 재료(한 줄 요약 · 인사이트 · 챕터 제목, 누를 때만)·키 확인 요청뿐이다. 영상 파일·결과·키는 나가지 않는다 — 끌어 놓은 파일도 web에서 api로, 같은 PC 안에서만 간다([[VA-INFRA-001#C9]], [[VA-INFRA-001#C4]]).
- **`/api/uploads`만 web의 라우트 핸들러가 받는다.** 다른 `/api/*`는 web의 넘기기(rewrites)가 api로 보내는데, 그 앞의 Host 확인이 본문을 메모리에 쌓고 10MB에서 자른다. 올리기는 라우트 핸들러가 같은 Host 확인을 한 뒤 본문을 스트림 그대로 api의 같은 경로로 넘기고 응답도 그대로 돌려준다([[VA-INFRA-001#C4]]). 브라우저가 보기에는 같은 `/api/uploads`다.
- 서버가 하지 않는 것 — 브라우저 다운로드(내보내기는 서버가 `data/export/`에 쓰거나 마크다운 텍스트를 돌려주고, 클립보드 복사는 브라우저가 한다), 원본 영상 스트리밍, 모델 목록의 동적 조회(설정값이다).

**화면이 응답으로 갈 곳을 정하는 규칙.** 서버는 상태값만 주고 어느 화면을 열지는 화면이 정한다.

| 값 | 화면이 가는 곳 |
|---|---|
| `Video.status = registered` | UI-2 사전 안내 (작업이 아직 없다) |
| `Video.status = in_progress` 또는 `failed` | UI-3 분석 진행 (`in_progress`는 대기 중과 진행 중을 함께 말한다) |
| `Job.status = queued` | UI-3 대기 상태 · UI-1 '대기 중 · {`queue_position`}번째' |
| `Video.status = analyzed` | UI-4 결과 (다시 넣은 경우 '이미 분석한 영상입니다' 짧은 알림) |
| `Job.status = done` (폴링 중) | UI-4 결과로 넘김 |
| `Job.status = failed` | UI-3 실패 상태 |
| 404 `not-found` (resource `job` 또는 `video`) | UI-1 홈 |
| 409 `result-not-ready` | `video_status`에 따라 UI-3 또는 UI-1 |
| [[#POST/api/uploads]] 200 | [[#POST/api/videos]]와 같다 — `Video.status`로 UI-2 올린 파일 판 · UI-4 · UI-3 |

---

## 2. 에러

`application/problem+json`. 공통 필드 `type`, `title`, `status`, `detail`. 종류별 확장 필드:

| type | status | 언제 | 확장 필드 | 근거 |
|---|---|---|---|---|
| `urn:va:not-found` | 404 | 영상·작업·inbox 파일·장면·인포그래픽 그림 없음 | `resource`(`video` · `job` · `inbox_file` · `frame` · `infographic`) · `id` | [[VA-UI-002#UI-3]] 규칙(영상이 없으면 UI-1로) |
| `urn:va:validation` | 422 | 요청 본문 형식 오류(빈 질문, 모르는 모델 값, 필수 필드 없음) | `errors: [{field, message}]` | — |
| `urn:va:key-missing` | 503 | 저장된 키가 없다 | — | [[VA-UC-001#UC-H8]], [[VA-PRD-001#N3]] |
| `urn:va:key-invalid` | 503 | 저장된 키가 마지막 확인에 실패했다(분석 시작·다시 시도·질문에서). 마지막 실패가 `network`였으면 그 자리에서 다시 확인한 결과다 | `reason_kind`(`format` · `auth` · `quota` · `network`) · `reason` · `checked_at` | [[VA-UC-001#UC-H8]] 3a |
| `urn:va:key-rejected` | 422 | 새로 넣은 키가 확인에 실패했다. 저장하지 않는다 | `reason_kind` · `reason` | [[VA-UC-001#UC-H8]] 3a |
| `urn:va:url-invalid` | 422 | YouTube 주소 형식이 아니다(watch · youtu.be · shorts 아님) | `accepted: ["watch", "youtu.be", "shorts"]` | [[VA-UC-001#UC-H1]] 1a |
| `urn:va:source-unavailable` | 502 | YouTube 정보를 못 가져옴(비공개 · 삭제 · 지역 제한 · 네트워크 · yt-dlp 깨짐) | `reason` · `hint`(예: yt-dlp 업데이트) | [[VA-UC-001#UC-H1]] 2a, [[VA-INFRA-001#C7]] |
| `urn:va:video-too-long` | 422 | 3시간 초과 | `duration_sec` · `max_sec`(10800) | [[VA-PRD-001#N2]], [[VA-UC-001#UC-S1]] 2a |
| `urn:va:no-audio-track` | 422 | 로컬 영상에 음성 트랙이 없다 | `duration_sec` | [[VA-UC-001#UC-H2]] 2a |
| `urn:va:unsupported-file` | 422 | 영상·음성 파일이 아니거나 열 수 없다 | `reason` · `accepted: [mp4, mkv, mov, webm, mp3, m4a, wav]` | [[VA-UC-001#UC-H2]] 1a |
| `urn:va:path-outside-inbox` | 422 | inbox 폴더 밖을 가리키는 경로(`..`, 절대 경로, 하위 폴더) | — | [[VA-INFRA-001#C4]] |
| `urn:va:job-exists` | 409 | 이 영상에 이미 작업이 있는데 새로 시작하려 함 | `job_id` · `job_status` | [[VA-UC-001#UC-S5]], [[VA-UI-002#UI-1]] |
| `urn:va:job-not-failed` | 409 | 실패 상태가 아닌 작업을 다시 시도 | `job_status` | [[VA-UC-001#UC-S3]] 3a3 |
| `urn:va:result-not-ready` | 409 | 결과가 아직 없다(작업 없음 · 진행 중 · 실패) | `video_status` | [[VA-UI-002#UI-4]] 규칙(UI-3으로 넘김) |
| `urn:va:llm-unavailable` | 502 | OpenAI 호출 실패(질문 답변, 키 확인 중 네트워크 · OpenAI 일시 오류). 사용량 초과도 여기 | `reason` | [[VA-UC-001#UC-H4]] 2a |
| `urn:va:export-failed` | 500 | `data/export/`에 파일을 쓰지 못함 | `path` · `reason` | [[VA-UC-001#UC-H7]], [[VA-UI-002#UI-7]] |
| `urn:va:no-space` | 507 | 올린 파일을 둘 디스크 여유가 모자라다. 본문을 받기 전에 판정한다 | `needed_bytes` · `free_bytes` | [[VA-UC-001#UC-H2]] 1d |
| `urn:va:upload-incomplete` | 400 | 받은 본문이 `Content-Length`보다 짧다(올리다 끊김). 받은 부분은 지웠다 | `received_bytes` · `expected_bytes` | [[VA-UC-001#UC-H2]] 1c |
| `urn:va:frames-unavailable` | 409 | 장면을 만들 수 없는 영상에 장면 채우기를 시킴(음성 파일 · 원본을 찾을 수 없는 로컬 파일) | `reason` | [[VA-UC-001#UC-S7]] 1a · 2a |
| `urn:va:infographic-busy` | 409 | 이 영상의 인포그래픽을 이미 그리는 중인데 또 시킴 | — | [[VA-UC-001#UC-H9]] |
| `urn:va:internal` | 500 | 예상 못 한 오류. `detail`은 고정 문구, 원인은 로그만 | — | — |

**표에 없는 예외도 problem+json으로 나간다.** 서버는 포괄 핸들러로 `urn:va:internal`(500)을 만든다. 클라이언트가 problem+json을 전제로 파싱하는데 평문 500이 나가면 오류를 읽지도 못한다.

**problem+json이 아닌 오류 응답은 web 프록시가 대신 답한 것이다.** api는 늘 problem+json으로 답한다. 평문 오류(500 'Internal Server Error')는 web 프록시가 api 대신 답한 것이다 — api가 꺼졌거나, 프록시 시간 제한(60초, [[VA-DOM-002]] 6장)을 넘었다. 프록시는 둘을 같은 500으로 답해 가를 수 없다. 화면은 fetch 자체가 실패한 것과 같이 '서버에 연결할 수 없음'으로 다룬다([[VA-UI-002#UI-1]] 규칙, 카드 B5). 60초를 넘는 요청이 없게 하는 것이 먼저다 — 남은 하나는 큰 로컬 파일 등록의 해시다(VA-MS-001 미결, 카드 C).

**에러 21종마다 라우터 테스트가 있다.** HTTP 응답으로 `type` · `status` · `content-type: application/problem+json` · 확장 필드를 본다. 화면이 `type`으로 입력 오류 · 배너 · 시작 불가 판을 고르기 때문이다(카드 B5).

**삭제 실패에는 종류가 없다.** [[VA-UI-002#UI-6]]의 실패 한 줄('분석 결과를 지우지 못했어요 — {이유}')은 `internal`의 `detail`을 쓴다. 지우기가 실패하는 경우는 디스크·DB 오류뿐이라 따로 가를 것이 없다.

**인포그래픽 그리기의 실패도 HTTP 에러가 아니다.** 그리기는 뒤에서 돈다([[#POST/api/videos/{id}/infographic]]가 맡기고 바로 돌려준다). 실패는 [[#GET/api/videos/{id}/infographic]]의 `state = failed`와 `error_reason`으로 전한다. 장면 채우기도 같다 — 실패한 챕터는 장면이 없을 뿐이다.

**파이프라인 안의 단계 실패는 HTTP 에러가 아니다.** 작업은 백그라운드에서 돌고 그 순간 요청이 없다. 실패는 [[#GET/api/videos/{id}/job]] 응답의 `error` 필드로 전한다(`kind` · `reason` · `chunk_seq` · `attempts`). 화면은 그것으로 실패 알림을 조립한다([[VA-UI-002]] 1.6 실패 알림).

---
## 3. 엔드포인트

항목 = `{METHOD}/{path}`. 엔드포인트마다 헤딩 + 한 줄 요약 + 화면·유스케이스·서비스 + 그 오퍼레이션의 yaml 조각. 공통 스키마·파라미터·응답은 4장에 있고, 뷰가 조각을 합쳐 OpenAPI 전체를 만든다. 에러 응답은 상태 코드마다 `Problem` 참조 하나이고, 어떤 `type`이 나는지는 본문 목록에 적는다.

### 3.1 설정과 키

#### GET/api/settings 설정과 키 상태

키 상태(마지막 확인 결과), 고른 모델, 고를 수 있는 모델과 단가, inbox 경로를 한 번에 준다. UI-5가 열릴 때와, 페이지 넷이 키 없음 배너를 그릴지 정할 때 부른다.

- 다시 확인하지 않는다. `key.state`와 `key.checked_at`은 서버 시작·분석 버튼·키 저장 때 한 마지막 결과다([[VA-UI-002#UI-5]] 규칙). 이 요청으로 OpenAI에 아무것도 나가지 않는다.
- `key.masked`는 앞 3자와 끝 4자만 남긴 값이다. 전체 키는 어떤 응답에도 없다([[VA-UC-001#UC-H8]]).
- 키가 사는 곳은 `.env` 파일 하나다. 처음 설치 때 사용자가 직접 적은 키도, 화면에서 넣은 키도 같은 줄이다([[VA-INFRA-001#C6]], [[VA-UC-001#UC-H8]] 1a). `key.stored_in`은 키가 있으면 늘 '.env에 저장됨'이고 없으면 null이다.
- `key.reason_kind = network`면 화면은 배너 문구를 '연결을 확인하지 못했어요 — …'로 가르고 [키 넣으러 가기]를 빼며 버튼을 막지 않는다([[VA-UI-002]] 1.4).
- `model_options`의 단가는 UI-5 도움말과 UI-2 예상 비용이 같이 쓴다. 받아쓰기 목록에는 구간 시각을 주는 모델만 있다([[VA-INFRA-001#C3]]).
- `image`는 인포그래픽 설정이다 — 고른 이미지 모델 · 품질과, 고를 수 있는 모델 · 품질마다 한 장 값(`price_usd`). UI-5 인포그래픽 카드, UI-4 인포그래픽 카드의 '한 장 약 ${값}', UI-8 예상 비용이 이 값을 쓴다([[VA-PRD-001#R13]]).

화면 [[VA-UI-002#UI-5]] · [[VA-UI-002#UI-1]] · [[VA-UI-002#UI-3]] · [[VA-UI-002#UI-4]](키 없음 배너) · 유스케이스 [[VA-UC-001#UC-H8]] 1번 · 서비스 `SettingsService.get`

```yaml
/api/settings:
  get:
    summary: 설정과 키 상태
    responses:
      '200':
        description: 설정 전부
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Settings'
```

#### POST/api/settings/key 새 키를 확인하고 저장

새 키로 가벼운 요청(모델 목록 조회)을 보내 확인하고, 통과하면 저장한다. UI-5 [확인하고 저장]이 부른다.

- 통과 → `.env` 파일의 `OPENAI_API_KEY` 줄에 쓰고(다른 줄은 그대로) `key.state = ok`, `checked_at`은 지금. 200에 갱신된 `Settings`. 서버를 다시 띄우지 않아도 다음 요청부터 새 키를 쓴다.
- 형식 오류 · 인증 실패 · 잔액 없음 → 422 `urn:va:key-rejected`(`reason_kind` · `reason`). **저장하지 않는다.** 전에 쓰던 키와 그 확인 결과는 그대로다([[VA-UI-002#UI-5]] 규칙, [[VA-UC-001#UC-H8]] 3a).
- OpenAI에 닿지 못함 → 502 `urn:va:llm-unavailable`. 역시 저장하지 않는다.
- 빈 문자열 → 422 `urn:va:validation`.
- 키는 저장소에 커밋되지 않는다([[VA-INFRA-001#C6]]).

화면 [[VA-UI-002#UI-5]] · 유스케이스 [[VA-UC-001#UC-H8]] 2~4번, 확장 3a · 서비스 `SettingsService.set_key`

```yaml
/api/settings/key:
  post:
    summary: 새 키를 확인하고 저장
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/KeyRequest'
    responses:
      '200':
        description: 확인 통과, 저장됨
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Settings'
      '422':
        $ref: '#/components/responses/Problem'
      '502':
        $ref: '#/components/responses/Problem'
```

#### PUT/api/settings/models 모델 선택 저장

받아쓰기 모델과 요약·챕터·질문 모델, 인포그래픽 이미지 모델 · 품질을 저장한다. UI-5 페이지 아래 [저장]이 부른다. 키는 건드리지 않는다.

- 값은 `Settings.model_options` · `Settings.image`에 있는 id만 받는다. 아니면 422 `urn:va:validation`. `image_model` · `image_quality`는 없으면 그대로 둔다(첫 화면이 보내지 않던 요청과 맞게).
- 저장한 모델은 다음 작업과 질문부터 쓴다. 돌고 있는 작업은 시작할 때의 모델을 끝까지 쓴다.
- 저장하는 곳은 키와 같은 `.env` 파일이다(`STT_MODEL` · `TEXT_MODEL` · `IMAGE_MODEL` · `IMAGE_QUALITY` 줄, [[VA-INFRA-001#C6]]). 바꾼 품질은 다음 인포그래픽부터 쓴다.

화면 [[VA-UI-002#UI-5]] · 유스케이스 [[VA-UC-001#UC-H8]] 5번 · 서비스 `SettingsService.set_models`

```yaml
/api/settings/models:
  put:
    summary: 모델 선택 저장
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ModelsRequest'
    responses:
      '200':
        description: 저장됨
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Settings'
      '422':
        $ref: '#/components/responses/Problem'
```

### 3.2 inbox

#### GET/api/inbox inbox 폴더의 파일 목록

읽기 전용으로 마운트된 inbox 폴더의 파일을 길이와 크기까지 준다. UI-1 「내 파일」 카드가 부른다.

- 받는 확장자(mp4 · mkv · mov · webm · mp3 · m4a · wav)만 보인다. 하위 폴더는 보지 않는다.
- 파일마다 `duration_sec`를 준다([[VA-UI-002#UI-1]] 규칙 — 목록을 주는 서버가 길이도 알려 준다). 재지 못하면 null이고, 그 파일을 고르면 [[#POST/api/videos]]가 `unsupported-file`을 낸다.
- 순서는 수정 시각 최근 순이다. 화면은 맨 위 파일을 기본으로 고른다.
- `path`는 사용자에게 보일 호스트 쪽 경로다(설정값). 컨테이너 안 마운트 경로가 아니다([[VA-INFRA-001#C4]]).
- 폴더가 비어 있으면 `files`가 빈 배열이다. 에러가 아니다.

화면 [[VA-UI-002#UI-1]] · [[VA-UI-002#UI-5]](폴더 경로) · 유스케이스 [[VA-UC-001#UC-H2]] 1번 · 서비스 `VideoService.list_inbox`

```yaml
/api/inbox:
  get:
    summary: inbox 폴더의 파일 목록
    responses:
      '200':
        description: 폴더 경로와 파일들
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InboxListing'
```

### 3.3 영상

#### GET/api/videos 분석한 영상 목록

작업이 있는 영상 전부를 최근 순으로 준다. UI-1 「분석한 영상」 목록이 부르고, 열어 둔 동안 진행 중 행을 새로 받는 데도 쓴다.

- **작업이 없는 영상은 빠진다.** 사전 안내에서 취소한 영상은 등록만 된 채 남는데 목록에 보이지 않는다([[VA-UI-002#UI-1]] 규칙, 5장 1).
- 순서는 작업을 시작한 때(`job.started_at`)의 내림차순이다. 완료 행의 시각은 `video.analyzed_at`이다.
- 대기 중 행은 `job.status = queued`이고 `job.queue_position`으로 '대기 중 · {n}번째'를 그린다. 작은 막대는 없다.
- 행마다 `job`이 붙는다. 화면은 `job.status`와 `job.stage`, `chunks_done` · `chunks_total` · `failed_chunk_seq`로 상태 글자를, `progress_pct`로 작은 막대를 그린다([[VA-UC-001#UC-S6]]). 받아쓰기가 아닌 단계는 `stage` 이름을 쓴다.
- `video.chat_turn_count`는 UI-6 「지워지는 것」의 질문 기록 수다.

화면 [[VA-UI-002#UI-1]] · 유스케이스 [[VA-UC-001#UC-H5]] 1번, 확장 1b · [[VA-UC-001#UC-S6]] · [[VA-UC-001#UC-S5]] 3번 · 서비스 `VideoService.list`

```yaml
/api/videos:
  get:
    summary: 분석한 영상 목록
    responses:
      '200':
        description: 작업이 있는 영상, 최근 순
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/VideoSummary'
```

#### POST/api/videos 영상을 등록하고 사전 안내를 만든다

YouTube 주소 또는 inbox 파일을 받아 정보를 확인하고, 같은 영상이 있는지 보고, 없으면 영상을 만들고 예상치를 계산한다. UI-1 [분석]·[선택한 파일 분석]이 부르고 응답으로 UI-2가 열린다.

순서대로 판정하고 걸리는 곳에서 멈춘다.

1. 저장된 키 확인 — 없으면 503 `urn:va:key-missing`, 확인 실패면 503 `urn:va:key-invalid`. 화면은 이동 없이 키 없음 배너를 띄운다([[VA-UI-002#UI-1]] 규칙).
2. 형식 검사 — YouTube 주소가 watch · youtu.be · shorts가 아니면 422 `urn:va:url-invalid`. inbox 밖 경로면 422 `urn:va:path-outside-inbox`, 받지 않는 확장자거나 열 수 없으면 422 `urn:va:unsupported-file`([[VA-PRD-001#R1]], [[VA-PRD-001#R2]]).
3. 정보 조회 — YouTube는 yt-dlp로 제목 · 채널 · 길이 · 자막 유무 · 자막 언어 · 수동/자동을 가져온다. 못 가져오면 502 `urn:va:source-unavailable`. 로컬은 ffprobe로 길이 · 음성 트랙을 확인하고 내용 SHA-256을 만든다. 음성이 없으면 422 `urn:va:no-audio-track`([[VA-UC-001#UC-S1]] 1번, 1a).
4. 길이 상한 — 3시간을 넘으면 422 `urn:va:video-too-long`(`duration_sec` 포함. 화면은 시작 불가 판에 길이를 보인다)([[VA-UC-001#UC-S1]] 2a).
5. 중복 판정 — 출처 식별자(YouTube 영상 ID 또는 내용 해시)로 찾는다. 있으면 그 영상을 돌려준다([[VA-UC-001#UC-S5]] 1번, 1a, 1b). 작업이 있는 영상이면 `estimate`는 null이다.
6. 없으면 Video를 만든다. `status = registered`. 이미 등록만 되고 작업이 없는 영상을 다시 넣으면 3번에서 가져온 정보로 덮어쓰고 `registered`로 돌려준다 — 처음 넣은 것과 같은 경험이다([[VA-UI-002#UI-1]] 규칙).
7. 예상치 계산 — `registered`일 때만. 자막 있음: `needs_stt = false`, `seconds`는 약 60, 받아쓰기 비용 0, 요약 비용 추정값. 받아쓰기 필요: 조각 수 `chunks`, 동시 수 `concurrency`, `stt_minutes × stt_price_per_min`, 요약 비용 추정값, 합계([[VA-UC-001#UC-S1]] 5번). 단가는 지금 설정된 모델의 값이다.

응답은 항상 200이다. 중복이면 기존 것을 돌려주므로 201을 쓰지 않는다. 화면은 `video.status`로 갈 곳을 정한다(1장 표): `registered` → UI-2, `analyzed` → UI-4와 짧은 알림, `in_progress` · `failed` → UI-3. 이 요청까지는 OpenAI로 음성이나 텍스트가 나가지 않는다. 나가는 것은 키 확인 요청과 YouTube에 보내는 영상 ID뿐이다([[VA-UC-001#UC-H0]] 3a).

화면 [[VA-UI-002#UI-1]] · [[VA-UI-002#UI-2]] · 유스케이스 [[VA-UC-001#UC-H1]] 1~2번, 확장 1a·2a·2b · [[VA-UC-001#UC-H2]] 1~2번, 확장 1a·2a · [[VA-UC-001#UC-S1]] · [[VA-UC-001#UC-S5]] 1번 · 서비스 `VideoService.register`

```yaml
/api/videos:
  post:
    summary: 영상을 등록하고 사전 안내를 만든다
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/RegisterRequest'
    responses:
      '200':
        description: 영상(새로 만들었거나 기존 것)과 예상치
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterResponse'
      '422':
        $ref: '#/components/responses/Problem'
      '502':
        $ref: '#/components/responses/Problem'
      '503':
        $ref: '#/components/responses/Problem'
```

#### POST/api/uploads 파일을 올려 등록하고 사전 안내를 만든다

브라우저가 고른(끌어 놓은) 로컬 파일 하나를 본문 그대로 받아 `data/uploads/`에 사본으로 두고, [[#POST/api/videos]]의 로컬 파일과 같은 판정으로 등록한다. UI-1 끌어 놓기 칸 · [파일 고르기]가 부르고 응답으로 UI-2 올린 파일 판이 열린다([[VA-PRD-001#R1]], [[VA-UC-001#UC-H2]], 사용자 요청 2026-09-29).

- 요청 본문은 파일 바이트 그대로다(`Content-Type: application/octet-stream`). 헤더 `X-File-Name`에 원래 파일 이름(UTF-8을 퍼센트 인코딩), `Content-Length`에 크기가 있어야 한다. 화면은 XHR 한 요청으로 보내고 `upload.onprogress`로 진행을 그린다([[VA-UI-002#UI-1]] 4.11). 여러 파일 · 받지 않는 확장자는 화면이 보내기 전에 거른다.
- 이 경로만 web의 라우트 핸들러를 지난다(1장). 라우트 핸들러가 Host를 확인하고(다르면 400 평문), 본문을 버퍼에 담지 않고 스트림으로 api에 넘긴다.

순서대로 판정하고 걸리는 곳에서 멈춘다. 1~3은 본문을 읽기 전이다. 어디서 거절하든 남은 본문은 끝까지 읽어 버린 뒤 답한다 — 브라우저는 본문을 다 보내야 답을 읽는다(카드 D4 실측, 시퀀스 3장 미결을 닫았다). 파일을 남기지는 않는다.

1. 저장된 키 확인 — 503 `urn:va:key-missing` · `urn:va:key-invalid`. 큰 파일을 다 받은 뒤 키 때문에 멈추지 않게 먼저 본다([[VA-UI-001]] 7장 24).
2. 이름 · 크기 — `X-File-Name`이 없거나 비었거나 `Content-Length`가 없으면 422 `urn:va:validation`. 받지 않는 확장자면 422 `urn:va:unsupported-file`(`accepted`).
3. 디스크 여유 — `data/uploads`가 있는 디스크의 여유가 `Content-Length`에 여유분을 더한 것보다 작으면 507 `urn:va:no-space`(`needed_bytes` · `free_bytes`)([[VA-UC-001#UC-H2]] 1d).
4. 본문을 `data/uploads/.part-{무작위}`에 1MB씩 쓰며 SHA-256을 잰다. 받은 크기가 `Content-Length`와 다르거나 연결이 끊기면 `.part`를 지운다 — 응답이 닿으면 400 `urn:va:upload-incomplete`([[VA-UC-001#UC-H2]] 1c).
5. 정보 조회와 길이 상한 — ffprobe로 길이 · 음성 트랙을 본다. 열 수 없으면 422 `urn:va:unsupported-file`, 음성이 없으면 422 `urn:va:no-audio-track`, 3시간을 넘으면 422 `urn:va:video-too-long`. 셋 다 사본을 지운다([[VA-UC-001#UC-H2]] 2a · 2c).
6. 중복 판정 — 내용 해시로 찾는다. inbox에서 고른 영상과 내용이 같아도 같은 영상이다([[VA-UC-001#UC-S5]] 1b). 있고 작업도 있으면 사본을 지우고 그 영상을 [[#POST/api/videos]] 5번과 똑같이 돌려준다 — 그 영상의 원본(inbox 파일 · 남아 있는 사본)은 그대로다. 있는데 작업이 없으면(사전 안내에서 취소했던 영상) 6번과 같이 올린 정보로 덮어쓰고 **사본을 남긴다** — 그 영상의 원본 자리가 이 사본이 된다. 지우면 [분석 시작]이 읽을 원본이 없다(클래스 명세 4.1, 시퀀스 되먹일 것 #9).
7. 없으면 사본을 `data/uploads/{SHA-256}.{확장자}`로 옮기고 Video를 만든다 — `source_kind = local`, `uploaded = true`, `title` · `origin`은 원래 파일 이름, `status = registered`. 예상치는 [[#POST/api/videos]] 7번과 같다.

응답은 [[#POST/api/videos]]와 같은 `RegisterResponse` 200이다. 화면도 같은 규칙으로 갈 곳을 정한다(1장 표). 이 요청까지 OpenAI로 음성 · 텍스트가 나가지 않는다 — 나가는 것은 키 확인 요청뿐이다.

사본의 수명은 [[#POST/api/videos/{id}/job]] · [[#DELETE/api/videos/{id}]]에 있다 — 작업이 끝나면(`done`) 지우고, 실패하면 남기고, 영상을 지우면(사전 안내 취소 포함) 지운다. 서버가 시작할 때 `.part`와 주인 없는 사본, 작업이 끝났거나 없는 영상의 사본을 지운다([[VA-INFRA-001#C4]], 사용자 결정 2026-09-29).

화면 [[VA-UI-002#UI-1]] · [[VA-UI-002#UI-2]] · 유스케이스 [[VA-UC-001#UC-H2]] 1~2번, 확장 1a~1d · 2a · 2c · [[VA-UC-001#UC-S1]] · [[VA-UC-001#UC-S5]] 1b · 서비스 `VideoService.upload`

```yaml
/api/uploads:
  post:
    summary: 파일을 올려 등록하고 사전 안내를 만든다
    parameters:
    - in: header
      name: X-File-Name
      required: true
      schema:
        type: string
      description: 원래 파일 이름. UTF-8을 퍼센트 인코딩
    - in: header
      name: Content-Length
      required: true
      schema:
        type: integer
    requestBody:
      required: true
      content:
        application/octet-stream:
          schema:
            type: string
            format: binary
    responses:
      '200':
        description: 영상(새로 만들었거나 기존 것)과 예상치. POST /api/videos와 같다
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterResponse'
      '400':
        $ref: '#/components/responses/Problem'
      '422':
        $ref: '#/components/responses/Problem'
      '503':
        $ref: '#/components/responses/Problem'
      '507':
        $ref: '#/components/responses/Problem'
```

#### GET/api/videos/{id} 영상 하나와 지금 상태

영상 정보와 작업 요약을 준다. 결과 본문은 없다. UI-3 영상 머리, UI-4 주소로 바로 들어왔을 때의 판정, UI-6 다이얼로그(질문 기록 수 · 진행 중 여부)가 부른다.

- `job`은 가장 최근 작업의 요약이고 작업이 없으면 null이다.
- UI-6은 `video.chat_turn_count`로 '질문 기록 {n}개'를, `video.status`가 `in_progress` · `failed`이면 '임시 음성 파일'을, `video.upload_bytes`가 있으면 '올린 사본({크기})'을 더하고, `video.uploaded`로 「남는 것」 문구를 고른다([[VA-UI-002#UI-6]] 규칙).
- 없으면 404 `urn:va:not-found`(`resource: video`).

화면 [[VA-UI-002#UI-3]] · [[VA-UI-002#UI-4]] · [[VA-UI-002#UI-6]] · 유스케이스 [[VA-UC-001#UC-H5]] 2~3번 · [[VA-UC-001#UC-H6]] 2번 · 서비스 `VideoService.get`

```yaml
/api/videos/{id}:
  get:
    summary: 영상 하나와 지금 상태
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: 영상과 작업 요약
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VideoDetail'
      '404':
        $ref: '#/components/responses/Problem'
```

#### DELETE/api/videos/{id} 영상과 딸린 것 전부 삭제

영상과 스크립트 · 요약 · 챕터 · 추천 질문 · 대화 · 조각 행 · 장면 행 · 인포그래픽 행과 파일(`data/tmp/{id}` · `data/frames/{id}` · `data/infographics/{id}.png` · 남아 있던 올린 사본)을 지운다. UI-6 [삭제]가 부른다. UI-2 올린 파일 판의 취소도 이것을 부른다 — 작업이 없는 올린 영상과 그 사본을 지운다([[VA-UC-001#UC-H2]] 3a).

- 진행 중이면 백그라운드 작업을 먼저 멈추고 지운다. 대기 중이면 대기열에서 빠진다 — 뒤에 기다리던 작업의 `queue_position`이 하나씩 당겨진다. 도는 작업을 지우면 다음 대기 작업이 시작된다([[VA-UC-001#UC-H6]] 4a). 실패한 영상은 보존된 조각 파일까지 지운다([[VA-UI-002#UI-6]] 규칙, [[VA-UI-001]] 7장 13).
- inbox의 원본 파일과 올린 파일의 원래 파일은 건드리지 않는다. 지우는 것은 앱 폴더의 사본뿐이다([[VA-INFRA-001#C4]], [[VA-UC-001#UC-H6]] 성공 보장). 내보낸 노트 · 그림 파일도 남는다.
- 그리는 중인 인포그래픽 · 채우는 중인 장면이 있으면 먼저 멈추고 지운다.
- 다른 영상은 영향받지 않는다([[VA-UC-001#UC-H6]] 최소 보장). 204.
- 없으면 404 `urn:va:not-found`. 디스크·DB 오류면 500 `urn:va:internal`이고 화면은 `detail`을 실패 한 줄에 보인다.
- 키 없음 배너가 떠 있어도 막지 않는다. OpenAI로 나가는 것이 없다.

화면 [[VA-UI-002#UI-6]] · 유스케이스 [[VA-UC-001#UC-H6]] 4번 · 서비스 `VideoService.delete`

```yaml
/api/videos/{id}:
  delete:
    summary: 영상과 딸린 것 전부 삭제
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '204':
        description: 지워짐
      '404':
        $ref: '#/components/responses/Problem'
      '500':
        $ref: '#/components/responses/Problem'
```

### 3.4 작업

#### POST/api/videos/{id}/job 분석을 시작한다

이 영상에 작업 하나를 만든다. 도는 작업이 없으면 바로 시작되고, 있으면 대기열에 들어간다. UI-2 [분석 시작]이 부른다. 본문은 없다.

1. 저장된 키 확인 — 503 `urn:va:key-missing` 또는 `urn:va:key-invalid`.
2. 이 영상에 이미 작업이 있으면 409 `urn:va:job-exists`(`job_id` · `job_status`). 실패한 작업은 새로 만들지 않고 [[#POST/api/videos/{id}/job/retry]]로 잇는다.
3. AnalysisJob을 만든다. 다른 영상의 작업이 `running`이거나 `queued`면 `status = queued`(`stage = pending`, `queue_position` = 대기열에서의 차례)이고, 없으면 `status = running`(`stage = pending`)으로 곧바로 돈다. 어느 쪽이든 `Video.status`는 `in_progress`가 된다. 201에 `Job`([[VA-UC-001#UC-H0]] 3b).
4. 대기 중인 작업은 서버의 워커가 시작한다 — 도는 작업이 끝나면(완료 · 실패 · 삭제) 가장 오래 기다린 작업을 `running`으로 바꿔 돌린다. 화면은 폴링으로 `status`가 바뀐 것을 안다.
- 파이프라인은 `stages` 순서대로 돈다 — 자막 있는 YouTube: download(자막) → summarize → chapter → suggest → frames · 자막 없는 YouTube: download(음성) → transcribe → summarize → chapter → suggest → frames · 로컬 영상(inbox · 올린 사본): extract → transcribe → summarize → chapter → suggest → frames · 로컬 음성: transcribe → summarize → chapter → suggest. `frames`(장면)는 실패해도 작업을 실패로 만들지 않고 `done`으로 끝낸다 — 장면을 얻지 못한 챕터는 장면이 없다([[VA-UC-001#UC-S6]] 1b, [[VA-UC-001#UC-S7]]).
- 올린 사본은 작업이 `done`이 되면 지운다. 실패로 멈추면 다시 시도를 위해 남긴다([[VA-UC-001#UC-H2]] 4번 · 4a, 사용자 결정 2026-09-29)([[VA-UC-001#UC-S2]], [[VA-UC-001#UC-H2]] 2b, [[VA-UI-002#UI-3]] 규칙).
- 음성 조각과 스크립트 텍스트는 작업이 `running`이 된 때부터 OpenAI로 간다([[VA-UC-001#UC-H0]] 3번, 3a). 대기 중에는 아무것도 나가지 않는다.
- 화면은 응답을 기다리는 동안 [분석 시작]을 잠그고, 201이 오면 UI-3으로 간다(`queued`면 대기 상태로 열린다). 에러면 다이얼로그를 그대로 두고 잠금을 푼다([[VA-UI-002#UI-2]] 규칙).

화면 [[VA-UI-002#UI-2]] · 유스케이스 [[VA-UC-001#UC-H0]] 3번 · [[VA-UC-001#UC-S2]] · [[VA-UC-001#UC-S3]] · [[VA-UC-001#UC-S4]](백그라운드) · 서비스 `JobService.start`

```yaml
/api/videos/{id}/job:
  post:
    summary: 분석을 시작한다
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '201':
        description: 만들어진 작업. status는 running 또는 queued
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Job'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
      '503':
        $ref: '#/components/responses/Problem'
```

#### GET/api/videos/{id}/job 진행 상태

가장 최근 작업의 단계 · 진행률 · 조각 · 남은 시간 · 실패 내용을 준다. UI-3이 1초마다 부르고([[VA-INFRA-001]] 3절), UI-1도 진행 중 행을 갱신할 때 같은 값을 쓴다.

- 작업이 없으면 404 `urn:va:not-found`(`resource: job`). 화면은 UI-1로 간다([[VA-UI-002#UI-3]] 규칙). 영상이 없어도 404(`resource: video`).
- `status = done`이면 화면은 UI-4로 넘긴다. `failed`면 실패 상태를, `queued`면 대기 상태를 그린다 — 헤드라인 '차례를 기다리는 중', 부제 '앞 영상 {`queue_position`}개가 끝나면 시작해요'([[VA-UI-002#UI-3]] 규칙). 이때 `progress_pct = 0`, `remaining_sec`와 `chunks`는 null, `stages`는 돌 단계 전부다.
- 화면은 계산하지 않는다. 아래 표의 값을 그대로 쓴다.

| UI-3 요소 | `Job` 필드 |
|---|---|
| 헤드라인(3.1) | `status` · `stage` (실패면 '{단계} … 멈췄어요', 대기면 '차례를 기다리는 중') |
| 부제(3.2) | `stages.length` · `stage_index` · `remaining_sec` · `chunks.done` · `chunks.total` · `error.chunk_seq`(k) · 대기면 `queue_position` |
| 퍼센트 · 막대(3.3 · 3.4) | `progress_pct`. 실패하면 멈춘 값 그대로 |
| 단계 목록(4) | `stages`(이 출처에 필요한 단계만, 순서대로) + `stage` + `status` |
| 단계 메모(4.4) | 완료 단계는 `stage_durations_sec`, 받아쓰기는 `chunks.done` / `chunks.total`, 장면은 `frames.done` / `frames.total` |
| 장면 칸 줄 · 캡션(4.9 ~ 4.11) | `frames.items[].state` · `frames.items[].url` · `video.source_kind` |
| 조각 격자 · 범례(4.6 ~ 4.8) | `chunks.items[].state` · `chunks.done` · `in_flight` · `failed` · `waiting` |
| 실패 알림(5) | `error.kind`(제목) · `error.reason`(왜) · `error.chunk_seq` · `error.attempts` · `chunks.done`(보존된 것) · `chunks.next_seq`(r) |
| 전송 표시(6.1) | `stage` · `models.stt` · `models.text` · `concurrency` · (장면 단계) `video.source_kind` |
| 떠나기 안내(6.2) | `stage` · `chunks.next_seq` |

- `remaining_sec`는 작업 전체가 끝날 때까지의 남은 예상 시간이다. 받아쓰기 단계는 미완료 조각 수 × 지금까지 조각당 평균([[VA-UC-001#UC-S6]] 2번)에 요약 세 단계(핵심 요약 · 챕터 · 추천 질문)의 예상 몫을 더한다. 요약 세 단계는 그 몫에서 세 단계에 쓴 시간을 뺀다. 장면 단계는 남은 챕터 수 × 지금까지 칸당 평균이다(받아쓰기 조각과 같은 방식). 그 앞 단계(자막 가져오기 · 음성 내려받기 · 음성 추출 · 음성을 나누는 중)는 예상 전체 시간에서 지난 시간을 뺀다. 끝난 단계가 예상보다 빨랐거나 늦었던 차이는 뒤 단계로 넘기지 않고, 0보다 작아지지 않는다(MINISPEC 작업 서비스 `JobService.remaining_sec`). **0이면 화면은 남은 시간을 비운다** — '약 0초'를 보이지 않는다. 돌고 있지 않으면(`queued` · `failed` · `done`) null이다.
- `chunks`는 받아쓰기가 있는 작업에만 있고, 받아쓰기가 끝난 뒤에도 남는다(모두 `done`). `next_seq`는 완료하지 않은 첫 조각 번호이고 모두 끝나면 null이다.
- `frames`는 장면 단계가 있는 작업에만 있다. 장면 단계에 들어가기 전에는 `total`만 챕터 수이고 모두 `waiting`이다. 받은 칸은 `done`과 그림 주소 `url`, 얻지 못한 칸은 `missing`이다.
- `error`는 `status = failed`일 때만 있다. `attempts`는 자동 재시도를 포함해 그 조각(또는 단계)을 보낸 횟수다.

화면 [[VA-UI-002#UI-3]] · [[VA-UI-002#UI-1]](진행 중 행) · 유스케이스 [[VA-UC-001#UC-S6]] · [[VA-UC-001#UC-S3]] 3번 · 서비스 `JobService.progress`

```yaml
/api/videos/{id}/job:
  get:
    summary: 진행 상태
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: 가장 최근 작업
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Job'
      '404':
        $ref: '#/components/responses/Problem'
```

#### POST/api/videos/{id}/job/retry 실패한 단계부터 이어서 다시 시도

실패한 작업을 같은 작업인 채로 이어간다. UI-3 실패 알림의 다시 시도가 부른다. 본문은 없다.

1. 저장된 키 확인 — 503 `urn:va:key-missing` 또는 `urn:va:key-invalid`. 키가 없는 동안 화면의 다시 시도는 막힌 버튼이다([[VA-UI-002]] 1.8). 마지막 확인이 연결 실패였으면 막지 않고 여기서 다시 확인한다(1장).
2. 작업이 `failed`가 아니면 409 `urn:va:job-not-failed`(`job_status`). 작업이 없으면 404.
3. `error`를 비우고 실패한 단계부터 다시 돈다. 도는 작업이 없으면 `status = running`으로 곧바로, 있으면 `status = queued`로 대기열 끝에 들어가 차례가 오면 멈춘 곳부터 잇는다([[VA-UI-002#UI-3]] 규칙). `stage`는 실패한 단계 그대로다. 받아쓰기면 `done`이 아닌 조각만 보낸다 — 완료한 조각은 다시 보내지 않는다([[VA-UC-001#UC-S3]] 3a3). 핵심 요약 · 챕터 · 추천 질문 단계면 스크립트는 그대로 두고 그 단계부터([[VA-UC-001#UC-S4]] 1b).
- 새 작업을 만들지 않는다. `id`와 `started_at`이 같다. 200에 `Job`.
- 화면은 응답이 올 때까지 다시 시도를 잠그고, 오면 실패 알림을 지우고 폴링을 계속한다([[VA-UI-002#UI-3]] 규칙).

화면 [[VA-UI-002#UI-3]] · 유스케이스 [[VA-UC-001#UC-S3]] 확장 3a · [[VA-UC-001#UC-S6]] 확장 1a · [[VA-UC-001#UC-H0]] 확장 4a~6a · 서비스 `JobService.retry`

```yaml
/api/videos/{id}/job/retry:
  post:
    summary: 실패한 단계부터 이어서 다시 시도
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: 다시 도는 작업. status는 running 또는 queued
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Job'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
      '503':
        $ref: '#/components/responses/Problem'
```

### 3.5 결과와 내보내기

#### GET/api/videos/{id}/result 분석 결과 전부

스크립트(구간 전부) · 한 줄 요약과 인사이트 · 파트와 챕터 · 추천 질문을 한 번에 준다. UI-4가 열릴 때 부른다.

- 결과가 없으면(작업 없음 · 진행 중 · 실패) 409 `urn:va:result-not-ready`(`video_status`). 화면은 `in_progress` · `failed`면 UI-3, `registered`면 UI-1로 넘긴다([[VA-UI-002#UI-4]] 규칙). 영상이 없으면 404.
- 구간은 나누지 않는다. 3시간 영상도 구간 수천 개를 한 응답에 준다(5장 3). 긴 목록을 그리는 방법은 화면 쪽 미결이다([[VA-UI-001]] 8장).
- 대화 기록은 여기 없다. `video.chat_turn_count`로 질문 수 배지를 그리고, [[#GET/api/videos/{id}/chat]]으로 따로 받는다.
- 결과는 읽기만 한다. 이 요청으로 저장된 것이 바뀌지 않는다([[VA-UC-001#UC-H3]] 최소 보장). 장면 단계 전에 분석한 결과(`frames_state = absent`)의 장면 채우기도 여기서 시작하지 않는다 — 화면이 [[#POST/api/videos/{id}/frames]]로 시킨다(5장 14).

| UI-4 요소 | `Result` 필드 |
|---|---|
| 칩 셋(2.1) | `video.source_kind` · `video.duration_sec` · `transcript.source` · `transcript.language` |
| 영상 제목(2.2) · 메타 줄(2.3) · 원본 영상 열기(2.4) | `video.title` · `video.channel` · `analyzed_at` · `models` · `video.origin`(YouTube만) |
| 한 줄 요약(3) · 핵심 인사이트(4) | `summary.one_liner` · `summary.insights[].text` · `source_secs` |
| 이런 걸 물어볼 수 있어요(5) · 추천 칩(10.1) | `suggested_questions` |
| 챕터(6) · 파트(6.4 ~ 6.6) | `chapters` · `parts`(60분 이하면 빈 배열) · `parts[].start_sec` · `end_sec` · `chapter_count` |
| 대표 장면(6.7) · 가져오는 중(6.8) | `chapters[].frame`(없으면 null) · `frames_state`(`making`이면 6.8) |
| 한눈에 보기(12 ~ 14) | `summary` · `parts` · `chapters` · `video.duration_sec` — 따로 받는 것이 없다 |
| 인포그래픽 카드(15) | `infographic`(처음 모습). 그리는 중이면 [[#GET/api/videos/{id}/infographic]]로 다시 받는다 |
| 질문 수 배지(7.3) | `video.chat_turn_count` |
| 스크립트 머리줄(8.1) · 구간(8.3) | `transcript.source`(수동 · 자동 · 받아쓰기) · `transcript.model` · `transcript.segments` |

화면 [[VA-UI-002#UI-4]] · 유스케이스 [[VA-UC-001#UC-H3]] · [[VA-UC-001#UC-H5]] 3번 · [[VA-UC-001#UC-S4]](결과) · 서비스 `AnalysisService.result_of`

```yaml
/api/videos/{id}/result:
  get:
    summary: 분석 결과 전부
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: 결과
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Result'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
```

#### GET/api/videos/{id}/frames 대표 장면 상태

챕터 대표 장면의 상태와 장면 목록을 준다. UI-4가 장면을 채우는 동안(`state = making`) 3초마다 부른다 — 결과 전부를 다시 받지 않게 가볍게 둔다.

- `state` — `absent`(장면 단계 전에 분석한 결과, 채울 수 있다) · `making`(채우는 중) · `done`(끝남, 장면이 없는 챕터가 있을 수 있다) · `unavailable`(음성 파일 · 원본을 찾을 수 없는 로컬 파일 — 채울 수 없다).
- `frames`는 장면이 있는 챕터만, 챕터 순서대로다. 화면은 `state = making`이면 아직 없는 챕터에 6.8을, `done`이 되면 없는 챕터의 6.8을 거둔다([[VA-UI-002#UI-4]] 규칙).
- 결과가 없으면 409 `urn:va:result-not-ready`. 영상이 없으면 404.

화면 [[VA-UI-002#UI-4]] · 유스케이스 [[VA-UC-001#UC-H3]] 확장 1a · 1b · [[VA-UC-001#UC-S7]] · 서비스 `AnalysisService.frames_of`

```yaml
/api/videos/{id}/frames:
  get:
    summary: 대표 장면 상태
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: 장면 상태와 장면들
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FrameSet'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
```

#### POST/api/videos/{id}/frames 장면을 뒤에서 채운다

장면 단계 전에 분석한 결과에 대표 장면을 채우기 시작한다. UI-4가 결과를 열었는데 `frames_state = absent`이면 한 번 부른다([[VA-UC-001#UC-H3]] 1a). 본문은 없다.

- 채우기는 뒤에서 돈다 — 202에 `FrameSet`(`state = making`)을 바로 돌려준다. 방법은 파이프라인의 장면 단계와 같다: YouTube는 미리 보기 썸네일(스토리보드) 칸을 잘라내고, 로컬 영상은 원본에서 프레임을 뽑는다([[VA-INFRA-001#C12]]). OpenAI 비용이 없고 키도 보지 않는다.
- 이미 `making`이거나 `done`이면 아무것도 하지 않고 202에 지금 상태를 준다 — 두 번 불러도 같다.
- `unavailable`이면 409 `urn:va:frames-unavailable`(`reason`). 결과가 없으면 409 `urn:va:result-not-ready`. 영상이 없으면 404.
- 채우기는 한 번에 한 영상이다. 분석 작업과 겹쳐도 된다 — 잠깐의 ffmpeg · YouTube 요청이다.
- 채우기가 끝나면 `done`이다. 얻지 못한 챕터는 장면이 없고, 다시 채우지 않는다(다시 분석하지 않는 한).

화면 [[VA-UI-002#UI-4]] · 유스케이스 [[VA-UC-001#UC-H3]] 확장 1a · [[VA-UC-001#UC-S7]] · 서비스 `AnalysisService.fill_frames`

```yaml
/api/videos/{id}/frames:
  post:
    summary: 장면을 뒤에서 채운다
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '202':
        description: 채우기를 맡음(또는 이미 채우는 중 · 끝남). 지금 상태
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FrameSet'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
```

#### GET/api/videos/{id}/frames/{seq} 대표 장면 그림

챕터 `seq`의 대표 장면 JPEG을 준다. UI-4 챕터 카드(6.7)와 UI-3 장면 칸(4.10)의 `<img>`가 부른다. 주소는 `Frame.url` 그대로다.

- `image/jpeg`. 크기는 얻은 그대로다(스토리보드 320×180 · 160×90 · 120×90, 로컬 폭 640) — 화면이 칸에 맞춰 줄인다.
- 장면이 없으면 404 `urn:va:not-found`(`resource: frame`).
- 다시 분석하거나 채우면 바뀔 수 있다. 캐시는 짧게 한다(`Cache-Control: no-cache`).

화면 [[VA-UI-002#UI-4]] · [[VA-UI-002#UI-3]] · 유스케이스 [[VA-UC-001#UC-H3]] 3번 · 서비스 `AnalysisService.frame_file`

```yaml
/api/videos/{id}/frames/{seq}:
  get:
    summary: 대표 장면 그림
    parameters:
    - $ref: '#/components/parameters/id'
    - in: path
      name: seq
      required: true
      schema:
        type: integer
      description: 챕터 순번
    responses:
      '200':
        description: JPEG
        content:
          image/jpeg:
            schema:
              type: string
              format: binary
      '404':
        $ref: '#/components/responses/Problem'
```

#### GET/api/videos/{id}/infographic 인포그래픽 상태

이 영상의 인포그래픽 상태와 그림 정보를 준다. UI-4가 그리는 동안(`state = making`) 3초마다 부른다.

- `state` — `none`(만든 적 없음) · `making`(그리는 중) · `done`(그림 있음) · `failed`(마지막 그리기 실패). `image`는 지금 쓰는 그림이고, 다시 만들기가 실패해도 이전 그림이 그대로 있다(`state = failed`인데 `image`가 있음, [[VA-UC-001#UC-H9]] 4a).
- `error_reason`은 `failed`일 때 한 줄(예: 'OpenAI 연결 시간 초과'). 화면이 '인포그래픽을 만들지 못했어요 — {이유}'로 보인다.
- 영상이 없으면 404. 결과가 없으면 409 `urn:va:result-not-ready`.

화면 [[VA-UI-002#UI-4]] · [[VA-UI-002#UI-9]] · 유스케이스 [[VA-UC-001#UC-H9]] 5번 · 서비스 `AnalysisService.infographic_of`

```yaml
/api/videos/{id}/infographic:
  get:
    summary: 인포그래픽 상태
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: 상태와 그림 정보
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Infographic'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
```

#### POST/api/videos/{id}/infographic 인포그래픽 그리기를 맡긴다

설정한 이미지 모델 · 품질로 인포그래픽 한 장 그리기를 맡긴다. UI-8 [만들기]가 부른다. 본문은 없다.

1. 결과가 없으면 409 `urn:va:result-not-ready`. 영상이 없으면 404.
2. 이미 그리는 중이면 409 `urn:va:infographic-busy`.
3. 저장된 키 확인 — 503 `urn:va:key-missing` · `urn:va:key-invalid`(1장 규칙대로 `network`면 다시 확인).
4. 뒤에서 그리기를 시작하고 202에 `Infographic`(`state = making`)을 바로 돌려준다 — 다 그릴 때까지 기다리지 않는다. 그리는 동안 화면을 떠나도 계속된다([[VA-UI-001]] UI-4 규칙). web 넘기기의 시간 제한(60초)에도 걸리지 않는다.
- 재료는 한 줄 요약 · 인사이트 · 챕터 제목뿐이다. 스크립트 전체는 보내지 않는다([[VA-UC-001#UC-H9]] 4번, [[VA-PRD-001#N3]]). 세로 한 장, 설정한 품질이다([[VA-INFRA-001#C11]]).
- 다 그리면 `data/infographics/{id}.png`에 쓰고 `state = done`. 이전 그림이 있으면 바꾼다([[VA-UC-001#UC-H9]] 5a). 실패하면 `state = failed` · `error_reason`이고 이전 그림은 그대로다(4a).
- 비용은 이 요청을 받아 그리기를 맡긴 때 든다. 값은 `Settings.image`의 한 장 값이다.

화면 [[VA-UI-002#UI-8]] · [[VA-UI-002#UI-4]] · 유스케이스 [[VA-UC-001#UC-H9]] 1~5번, 확장 2a · 4a · 5a · 서비스 `AnalysisService.start_infographic`

```yaml
/api/videos/{id}/infographic:
  post:
    summary: 인포그래픽 그리기를 맡긴다
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '202':
        description: 맡음. state는 making
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Infographic'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
      '503':
        $ref: '#/components/responses/Problem'
```

#### GET/api/videos/{id}/infographic/image 인포그래픽 그림

지금 쓰는 인포그래픽 PNG를 준다. UI-4 카드(15.5)와 UI-9 그림(2)의 `<img>`가 부른다. 주소는 `InfographicImage.url` 그대로다 — 그림이 바뀌면 주소 끝의 `?v={만든 시각}`이 바뀌어 새로 받는다.

- `image/png`. 없으면 404 `urn:va:not-found`(`resource: infographic`).

화면 [[VA-UI-002#UI-4]] · [[VA-UI-002#UI-9]] · 유스케이스 [[VA-UC-001#UC-H9]] 5번 · 서비스 `AnalysisService.infographic_file`

```yaml
/api/videos/{id}/infographic/image:
  get:
    summary: 인포그래픽 그림
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: PNG
        content:
          image/png:
            schema:
              type: string
              format: binary
      '404':
        $ref: '#/components/responses/Problem'
```

#### GET/api/videos/{id}/export 마크다운 본문

내보낼 노트(마크다운 전체)와 파일 이름, 파일로 저장할 때 함께 쓸 파일 목록을 준다. 스크립트는 노트에 없다 — 파일로 저장할 때 따로 쓴다([[#POST/api/videos/{id}/export]], [[VA-PRD-001#R10]]). UI-7이 열릴 때와 질문 기록 체크박스를 바꿀 때 부른다. [복사하기]는 받아 둔 `markdown` 전체를 쓰고 다시 부르지 않는다 — 누른 뒤 요청을 기다리는 사이 사용자 동작이 끝나면 브라우저가 클립보드 쓰기를 막을 수 있다.

- 쿼리 `with_chat`(기본 false)이 true면 맨 아래 질문 기록이 붙는다([[VA-UC-001#UC-H7]] 2b). 체크박스를 바꾸면 화면이 다시 부른다.
- 쿼리 `method`(`file` 기본 · `clipboard`)가 노트를 가른다. `file`이면 그림 줄(한눈에 보기의 인포그래픽 `![[{filename} 인포그래픽.png]]`, 챕터마다 장면 `![[{filename} {시각}.jpg]]`)과 `## 스크립트` 절이 들어가고 `files`에 함께 쓸 파일(노트 · 스크립트 · 장면 · 인포그래픽 — 있는 것만)이 온다. `clipboard`면 그림 줄과 `## 스크립트` 절이 없고 `files`는 빈 배열이다 — 복사한 노트에는 가리킬 파일이 없다([[VA-UI-002#UI-7]] 규칙). 방법을 바꾸면 화면이 다시 부른다.
- 내용 순서([[VA-UC-001#UC-H7]] 2번, [[VA-PRD-001#R10]]): `# {제목}` → `원본: {링크} · {길이}`(로컬 파일은 `원본: {파일 이름} · {길이}`, 링크 없음) → `> {한 줄 요약}` → `## 한눈에 보기`(`file`이고 인포그래픽이 있으면 그림 줄, Mermaid `gantt` · `mindmap` 코드 블록 — [[VA-PRD-001#R11]], [[VA-INFRA-001]] 3절) → `## 핵심 인사이트` 번호 목록(문장 끝에 시각) → `## 챕터`(챕터마다 `### [{시각}]({링크}) {제목}`, `file`이고 장면이 있으면 장면 줄, `- {요점}`) → (`file`) `## 스크립트` → (`with_chat`) `## 질문 기록`. Mermaid로 그리는 법(글자 바꾸기 · 눈금)은 MINISPEC 결과 서비스에서 정한다.
- 시각은 `[mm:ss]`(1시간 이상 영상은 `[h:mm:ss]`) 텍스트다. YouTube면 `https://youtu.be/{영상ID}?t={초}` 링크가 걸리고 로컬 파일이면 시각만 남는다([[VA-UI-002#UI-7]] 규칙).
- 미리 보기는 화면이 앞부분만 잘라 보인다. 클립보드 복사는 브라우저가 `markdown` 전체로 한다 — 서버는 클립보드에 닿을 수 없다(5장 5).
- 결과가 없으면 409 `urn:va:result-not-ready`. 파일 이름은 영상 제목에서 만들고(쓸 수 없는 글자는 `_`, 80자까지, 로컬 파일은 확장자를 뗀다), 같은 이름이 있으면 덮어쓴다(6장, 사용자 결정 2026-09-28). `path`는 사용자에게 보일 경로 `data/export/{filename}.md`다 — 컨테이너 안 경로가 아니다.

화면 [[VA-UI-002#UI-7]] · 유스케이스 [[VA-UC-001#UC-H7]] 1~2번, 확장 2a·2b · 서비스 `AnalysisService.export_markdown`

```yaml
/api/videos/{id}/export:
  get:
    summary: 마크다운 본문
    parameters:
    - $ref: '#/components/parameters/id'
    - in: query
      name: with_chat
      required: false
      schema:
        type: boolean
        default: false
      description: 질문 기록을 맨 아래에 붙인다
    - in: query
      name: method
      required: false
      schema:
        type: string
        enum: [file, clipboard]
        default: file
      description: file이면 그림 줄 · 스크립트 절과 함께 쓸 파일 목록, clipboard면 빼고
    responses:
      '200':
        description: 파일 이름과 마크다운 전체
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ExportPreview'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
```

#### POST/api/videos/{id}/export 마크다운을 파일로 저장

서버가 노트 `data/export/{filename}.md`와 스크립트 `data/export/{filename} 스크립트.md`를 쓰고, 장면이 있으면 `{filename} {시각}.jpg`(쌍점은 하이픈)를, 인포그래픽이 있으면 `{filename} 인포그래픽.png`를 같은 폴더에 복사한다([[VA-UC-001#UC-H7]] 2c · 2d). 노트는 GET `method=file`의 `markdown`과 같다. 스크립트 파일은 `# {제목} — 스크립트` → 원본 줄 → 출처 줄 → 구간 줄이다([[VA-PRD-001#R10]]). UI-7 [파일로 저장]이 부른다.

- 본문 `with_chat`은 GET의 쿼리와 같은 뜻이다.
- 같은 이름의 파일이 있으면 둘 다 덮어쓴다. 브라우저 다운로드는 없다([[VA-UI-001]] 7장 14).
- 201에 `ExportResult`(`path`는 노트 경로 — 화면의 짧은 알림 '{path}에 저장했어요 · 스크립트는 따로'에 들어간다. `images`는 쓴 그림 수 — 있으면 알림에 '· 그림 {n}장'. `bytes`는 쓴 파일 전부의 합, `files`는 쓴 파일).
- 쓰지 못하면 500 `urn:va:export-failed`(`path` · `reason`). 화면은 다이얼로그를 닫지 않고 실패 한 줄을 보인다([[VA-UI-002#UI-7]] 규칙).
- 결과가 없으면 409 `urn:va:result-not-ready`.

화면 [[VA-UI-002#UI-7]] · 유스케이스 [[VA-UC-001#UC-H7]] 3번 · 서비스 `AnalysisService.export_to_file`

```yaml
/api/videos/{id}/export:
  post:
    summary: 마크다운을 파일로 저장
    parameters:
    - $ref: '#/components/parameters/id'
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ExportRequest'
    responses:
      '201':
        description: 쓴 파일
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ExportResult'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
      '500':
        $ref: '#/components/responses/Problem'
```

### 3.6 대화

#### GET/api/videos/{id}/chat 질문·답변 기록

이 영상에 저장된 대화 턴을 시간순으로 준다. UI-4 [질문하기] 탭이 부른다.

- 결과가 없는 영상은 빈 배열이다. 에러가 아니다. 영상이 없으면 404.
- 실패한 질문은 저장되지 않으므로 여기 없다([[VA-UI-002#UI-4]] 규칙).
- `cited_secs`가 빈 배열이면 근거 없는 답이다. 화면은 흐린 글자와 '영상에 없는 내용' 배지를 붙인다([[VA-PRD-001#R6]]).

화면 [[VA-UI-002#UI-4]] · 유스케이스 [[VA-UC-001#UC-H5]] 3번 · [[VA-UC-001#UC-H4]] 4번 · 서비스 `ChatService.history`

```yaml
/api/videos/{id}/chat:
  get:
    summary: 질문·답변 기록
    parameters:
    - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: 대화 턴, 시간순
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/ChatTurn'
      '404':
        $ref: '#/components/responses/Problem'
```

#### POST/api/videos/{id}/chat 질문하고 답을 받는다

질문을 받아 스크립트와 앞선 대화를 맥락으로 OpenAI에 보내고, 답과 근거 시각을 저장해 돌려준다. UI-4 [보내기]와 추천 질문이 부른다.

1. 결과가 없으면 409 `urn:va:result-not-ready`. 영상이 없으면 404.
2. 저장된 키 확인 — 503 `urn:va:key-missing` 또는 `urn:va:key-invalid`. 키가 없는 동안 화면은 입력칸을 막고 있다([[VA-UI-002#UI-4]] 규칙).
3. `question`이 비어 있으면(공백뿐이어도) 422 `urn:va:validation`. 스키마는 글자 수를 막지 않는다 — 빈 문자열도 1 · 2번 뒤에 본다 — 순서가 규칙이다(서비스 `ChatService.ask`).
4. 맥락은 구간 전부와 최근 턴 10개다. 스크립트가 설정된 토큰 상한을 넘으면 챕터 제목으로 관련 챕터를 고르고 그 구간만 넣는다([[VA-UC-001#UC-H4]] 3b). 사용자에게는 같은 흐름이다.
5. 답을 받으면 ChatTurn을 저장하고 201로 돌려준다. `Video.chat_turn_count`가 1 는다. 영상에 없는 내용이면 답은 '이 영상에서는 다루지 않습니다' 계열이고 `cited_secs`는 빈 배열이다([[VA-UC-001#UC-H4]] 3a).
- OpenAI 호출이 실패하면 502 `urn:va:llm-unavailable`(`reason`). **저장하지 않는다.** 화면은 답 자리에 이유와 [다시 시도]를 두고 같은 질문을 다시 보낸다([[VA-UC-001#UC-H4]] 2a).
- 응답 시간 목표는 10초 안이다([[VA-PRD-001#N1]]). 화면은 기다리는 동안 입력칸과 [보내기]를 잠근다.
- 추천 질문을 누른 것도 같은 요청이다. `question`에 그 문장이 들어간다([[VA-UC-001#UC-H4]] 1a, [[VA-PRD-001#R9]]).

화면 [[VA-UI-002#UI-4]] · 유스케이스 [[VA-UC-001#UC-H4]] 1~4번, 확장 1a·1b·2a·3a·3b · 서비스 `ChatService.ask`

```yaml
/api/videos/{id}/chat:
  post:
    summary: 질문하고 답을 받는다
    parameters:
    - $ref: '#/components/parameters/id'
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/AskRequest'
    responses:
      '201':
        description: 저장된 대화 턴
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatTurn'
      '404':
        $ref: '#/components/responses/Problem'
      '409':
        $ref: '#/components/responses/Problem'
      '422':
        $ref: '#/components/responses/Problem'
      '502':
        $ref: '#/components/responses/Problem'
      '503':
        $ref: '#/components/responses/Problem'
```

---
## 4. 스키마

엔드포인트 조각이 참조하는 `components`. 항목이 아니다.

```yaml
openapi: 3.1.0
info:
  title: Video Agent API
  version: '1.0'
servers:
- url: /
components:
  parameters:
    id:
      in: path
      name: id
      required: true
      schema:
        type: integer
      description: 영상 id. 화면 주소 /videos/{id}와 같다
  responses:
    Problem:
      description: RFC 9457
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Problem'
  schemas:
    Problem:
      type: object
      required: [type, title, status]
      properties:
        type:
          type: string
          format: uri
          description: urn:va:{종류}. 2장
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
      additionalProperties: true
    SourceKind:
      type: string
      enum: [youtube, local]
    VideoStatus:
      type: string
      enum: [registered, in_progress, failed, analyzed]
      description: registered = 작업 없음(사전 안내 전·취소). 나머지는 최근 작업의 상태를 따른다 — queued · running = in_progress, failed = failed, done = analyzed
    JobStatus:
      type: string
      enum: [queued, running, failed, done]
      description: queued = 다른 작업이 끝나기를 기다린다. 동시에 running인 작업은 하나다
    JobStage:
      type: string
      enum: [pending, download, extract, transcribe, summarize, chapter, suggest, frames]
      description: 파이프라인 단계. 화면 이름 대응은 VA-UI-002 UI-3 규칙 — download는 자막이 있으면 '자막 가져오기', 없으면 '음성 내려받기', frames는 '장면'(실패해도 작업을 실패로 만들지 않는다)
    TranscriptSource:
      type: string
      enum: [caption_manual, caption_auto, stt]
    CaptionKind:
      type: string
      enum: [manual, auto]
    ChunkState:
      type: string
      enum: [waiting, in_flight, done, failed]
    KeyState:
      type: string
      enum: [ok, missing, invalid]
    ReasonKind:
      type: string
      enum: [format, auth, quota, network]
      description: 키 확인 실패 이유. network는 키가 틀린 것이 아니라 OpenAI에 닿지 못했거나 OpenAI가 잠시 답하지 못한 것(시간 초과 · 5xx · 요청 한도) — 다시 확인하면 풀릴 수 있어 화면이 배너 문구를 가르고 버튼을 막지 않는다(VA-UI-002 1.4)
    ErrorKind:
      type: string
      enum: [network, openai, youtube, ffmpeg, disk, unknown]
      description: 파이프라인 실패 종류. 화면이 실패 알림 제목(UI-3 5.1)을 고른다
    Video:
      type: object
      required: [id, source_kind, source_id, title, channel, duration_sec, origin, uploaded, upload_bytes, has_captions, caption_language, caption_kind, status, analyzed_at, created_at, chat_turn_count]
      properties:
        id:
          type: integer
        source_kind:
          $ref: '#/components/schemas/SourceKind'
        source_id:
          type: string
          description: YouTube 영상 ID(11자) 또는 파일 내용 SHA-256. 중복 판정 기준
        title:
          type: string
          description: YouTube 제목 또는 파일 이름
        channel:
          type: [string, 'null']
          description: YouTube 채널. 로컬이면 null
        duration_sec:
          type: integer
        origin:
          type: string
          description: YouTube URL, inbox 파일 이름 또는 올린 파일의 원래 이름. UI-4 '원본 영상 열기'(YouTube만)
        uploaded:
          type: boolean
          description: 끌어 놓아 올린 파일이면 true(원본 자리 = 올린 사본, VA-DOM-001 Video). UI-1 부제 '올린 파일', UI-6 「남는 것」
        upload_bytes:
          type: [integer, 'null']
          description: 올린 사본이 아직 남아 있으면 그 크기. 지웠거나 올린 파일이 아니면 null. UI-6 '올린 사본({크기})'
        has_captions:
          type: boolean
        caption_language:
          type: [string, 'null']
          description: UI-2 '자막 있음 · {언어}'
        caption_kind:
          oneOf:
          - $ref: '#/components/schemas/CaptionKind'
          - type: 'null'
        status:
          $ref: '#/components/schemas/VideoStatus'
        analyzed_at:
          type: [string, 'null']
          format: date-time
          description: 결과가 저장된 때. UI-1 완료 행 '{시각} 분석'
        created_at:
          type: string
          format: date-time
        chat_turn_count:
          type: integer
          description: 저장된 대화 턴 수. UI-4 질문 수 배지, UI-6 '질문 기록 {n}개'
    JobSummary:
      type: object
      required: [id, status, stage, queue_position, progress_pct, chunks_done, chunks_total, failed_chunk_seq, started_at, finished_at]
      properties:
        id:
          type: integer
        status:
          $ref: '#/components/schemas/JobStatus'
        stage:
          $ref: '#/components/schemas/JobStage'
          description: 지금 도는 단계, 실패했으면 실패한 단계
        queue_position:
          type: [integer, 'null']
          minimum: 1
          description: 대기열에서의 차례. 1이 바로 다음. queued가 아니면 null. UI-1 '대기 중 · {n}번째'
        progress_pct:
          type: integer
          minimum: 0
          maximum: 100
          description: UI-1 작은 막대. UI-3 큰 막대와 같은 값
        chunks_done:
          type: [integer, 'null']
          description: 완료한 조각 수(n). 받아쓰기가 없는 작업은 null
        chunks_total:
          type: [integer, 'null']
          description: 조각 수(m)
        failed_chunk_seq:
          type: [integer, 'null']
          description: 실패한 조각 번호(k). 실패 상태가 아니면 null
        started_at:
          type: string
          format: date-time
        finished_at:
          type: [string, 'null']
          format: date-time
    VideoSummary:
      description: 목록 행. 영상 + 최근 작업 요약
      allOf:
      - $ref: '#/components/schemas/Video'
      - type: object
        required: [job]
        properties:
          job:
            $ref: '#/components/schemas/JobSummary'
    VideoDetail:
      type: object
      required: [video, job]
      properties:
        video:
          $ref: '#/components/schemas/Video'
        job:
          oneOf:
          - $ref: '#/components/schemas/JobSummary'
          - type: 'null'
    YouTubeSource:
      type: object
      required: [source, url]
      properties:
        source:
          type: string
          const: youtube
        url:
          type: string
          description: watch · youtu.be · shorts 주소
    LocalSource:
      type: object
      required: [source, path]
      properties:
        source:
          type: string
          const: local
        path:
          type: string
          description: inbox 안 파일 이름. 하위 폴더·절대 경로·.. 금지
    RegisterRequest:
      oneOf:
      - $ref: '#/components/schemas/YouTubeSource'
      - $ref: '#/components/schemas/LocalSource'
      discriminator:
        propertyName: source
        mapping:
          youtube: '#/components/schemas/YouTubeSource'
          local: '#/components/schemas/LocalSource'
    Estimate:
      type: object
      required: [needs_stt, seconds, chunks, concurrency, stt_minutes, stt_price_per_min, stt_cost_usd, text_cost_usd, total_cost_usd, stt_model, text_model]
      properties:
        needs_stt:
          type: boolean
          description: false면 자막 있음 판, true면 받아쓰기 필요 판
        seconds:
          type: integer
          description: 예상 소요. 화면이 '약 {n}분'으로
        chunks:
          type: [integer, 'null']
          description: 조각 수 k. 자막 있음이면 null
        concurrency:
          type: [integer, 'null']
          description: 동시 수 c
        stt_minutes:
          type: [number, 'null']
          description: 받아쓰기 분
        stt_price_per_min:
          type: [number, 'null']
          description: 받아쓰기 모델 단가(USD/분). UI-5 단가와 같다
        stt_cost_usd:
          type: number
          description: 받아쓰기 줄. 자막 사용이면 0
        text_cost_usd:
          type: number
          description: 요약 · 챕터 · 추천 질문 줄(추정)
        total_cost_usd:
          type: number
          description: 합계. 화면은 '약 $'를 붙인다
        stt_model:
          type: string
          description: 전송 안내 상자의 받아쓰기 모델 이름
        text_model:
          type: string
          description: 전송 안내 상자의 요약 모델 이름
    RegisterResponse:
      type: object
      required: [video, estimate]
      properties:
        video:
          $ref: '#/components/schemas/Video'
        estimate:
          oneOf:
          - $ref: '#/components/schemas/Estimate'
          - type: 'null'
          description: video.status가 registered일 때만. 아니면 null
    InboxFile:
      type: object
      required: [name, size_bytes, duration_sec, kind, modified_at]
      properties:
        name:
          type: string
        size_bytes:
          type: integer
        duration_sec:
          type: [integer, 'null']
          description: 재지 못하면 null
        kind:
          type: string
          enum: [video, audio]
        modified_at:
          type: string
          format: date-time
    InboxListing:
      type: object
      required: [path, files]
      properties:
        path:
          type: string
          description: 사용자에게 보일 호스트 쪽 inbox 경로(설정값). UI-1 카드 부제, UI-5 폴더 경로
        files:
          type: array
          items:
            $ref: '#/components/schemas/InboxFile'
    Chunk:
      type: object
      required: [seq, state]
      properties:
        seq:
          type: integer
          description: 1부터
        state:
          $ref: '#/components/schemas/ChunkState'
    Chunks:
      type: object
      required: [total, done, in_flight, failed, waiting, next_seq, items]
      properties:
        total:
          type: integer
        done:
          type: integer
        in_flight:
          type: integer
        failed:
          type: integer
        waiting:
          type: integer
        next_seq:
          type: [integer, 'null']
          description: 완료하지 않은 첫 조각 번호(r). 모두 끝나면 null
        items:
          type: array
          items:
            $ref: '#/components/schemas/Chunk'
    JobError:
      type: object
      required: [kind, reason, chunk_seq, attempts]
      properties:
        kind:
          $ref: '#/components/schemas/ErrorKind'
        reason:
          type: string
          description: 왜 실패했는지 한 줄(한국어)
        chunk_seq:
          type: [integer, 'null']
          description: 실패한 조각 번호(k). 받아쓰기 밖 단계면 null
        attempts:
          type: integer
          description: 자동 재시도를 포함해 보낸 횟수
    Models:
      type: object
      required: [stt, text]
      properties:
        stt:
          type: [string, 'null']
          description: 받아쓰기 모델. 자막으로 만든 결과면 null
        text:
          type: string
          description: 요약 · 챕터 · 질문 모델
    Job:
      type: object
      required: [id, video_id, status, stage, queue_position, stages, stage_index, progress_pct, remaining_sec, chunks, frames, concurrency, models, error, est_seconds, est_cost_usd, stage_durations_sec, started_at, finished_at]
      properties:
        id:
          type: integer
        video_id:
          type: integer
        status:
          $ref: '#/components/schemas/JobStatus'
        stage:
          $ref: '#/components/schemas/JobStage'
          description: 지금 도는 단계, 실패했으면 실패한 단계
        queue_position:
          type: [integer, 'null']
          minimum: 1
          description: 대기열에서의 차례. 1이 바로 다음. queued가 아니면 null. UI-3 '앞 영상 {n}개가 끝나면 시작해요'
        stages:
          type: array
          items:
            $ref: '#/components/schemas/JobStage'
          description: 이 출처에 필요한 단계만, 순서대로. UI-3 단계 목록
        stage_index:
          type: integer
          description: stages 안 위치, 1부터. UI-3 '{단계 수}단계 중 {i}단계'
        progress_pct:
          type: integer
          minimum: 0
          maximum: 100
        remaining_sec:
          type: [integer, 'null']
          description: 남은 예상 시간. 0이면 화면은 비운다. 돌고 있지 않으면(queued · failed · done) null
        chunks:
          oneOf:
          - $ref: '#/components/schemas/Chunks'
          - type: 'null'
          description: 받아쓰기가 있는 작업만. 끝난 뒤에도 남는다
        frames:
          oneOf:
          - $ref: '#/components/schemas/FrameProgress'
          - type: 'null'
          description: 장면 단계가 있는 작업만. UI-3 장면 칸 줄
        concurrency:
          type: [integer, 'null']
          description: 동시에 보내는 조각 수 c
        models:
          $ref: '#/components/schemas/Models'
        error:
          oneOf:
          - $ref: '#/components/schemas/JobError'
          - type: 'null'
          description: status가 failed일 때만
        est_seconds:
          type: integer
          description: 시작 전 예상 소요
        est_cost_usd:
          type: number
          description: 시작 전 예상 비용
        stage_durations_sec:
          type: object
          additionalProperties:
            type: integer
          description: 완료한 단계마다 걸린 시간. 키는 JobStage. UI-3 단계 메모
        started_at:
          type: string
          format: date-time
        finished_at:
          type: [string, 'null']
          format: date-time
    Segment:
      type: object
      required: [seq, start_sec, end_sec, text]
      properties:
        seq:
          type: integer
        start_sec:
          type: number
        end_sec:
          type: number
        text:
          type: string
    Transcript:
      type: object
      required: [source, language, model, segments]
      properties:
        source:
          $ref: '#/components/schemas/TranscriptSource'
        language:
          type: string
        model:
          type: [string, 'null']
          description: stt일 때 받아쓰기 모델
        segments:
          type: array
          items:
            $ref: '#/components/schemas/Segment'
    Insight:
      type: object
      required: [seq, text, source_secs]
      properties:
        seq:
          type: integer
        text:
          type: string
        source_secs:
          type: array
          minItems: 1
          items:
            type: number
          description: 출처 시각들. 화면이 그 시각을 포함하는 구간을 찾는다
    Summary:
      type: object
      required: [one_liner, model, insights]
      properties:
        one_liner:
          type: string
        model:
          type: string
        insights:
          type: array
          items:
            $ref: '#/components/schemas/Insight'
    Part:
      type: object
      required: [seq, title, start_sec, end_sec, chapter_count]
      properties:
        seq:
          type: integer
        title:
          type: string
        start_sec:
          type: number
        end_sec:
          type: number
          description: 다음 파트 시작 또는 영상 길이. UI-4 '{시작} – {끝}'
        chapter_count:
          type: integer
    FrameProgressItem:
      type: object
      required: [chapter_seq, state, url]
      properties:
        chapter_seq:
          type: integer
        state:
          type: string
          enum: [waiting, in_flight, done, missing]
          description: missing = 얻지 못함(장면 없이 넘어감)
        url:
          type: [string, 'null']
          description: done이면 /api/videos/{id}/frames/{seq}
    FrameProgress:
      type: object
      required: [done, total, items]
      properties:
        done:
          type: integer
          description: 받은(뽑은) 장면 수 n. UI-3 '{n} / {m}'
        total:
          type: integer
          description: 챕터 수 m
        items:
          type: array
          items:
            $ref: '#/components/schemas/FrameProgressItem'
    FrameSource:
      type: string
      enum: [storyboard, local_frame]
      description: storyboard = YouTube 미리 보기 썸네일 칸, local_frame = 로컬 원본에서 뽑은 프레임
    Frame:
      type: object
      required: [chapter_seq, sec, source, width, height, url]
      properties:
        chapter_seq:
          type: integer
        sec:
          type: number
          description: 실제로 잘라 온 장면의 시각. 스토리보드는 챕터 시작과 몇 초 다를 수 있다
        source:
          $ref: '#/components/schemas/FrameSource'
        width:
          type: integer
        height:
          type: integer
        url:
          type: string
          description: /api/videos/{id}/frames/{seq}
    FramesState:
      type: string
      enum: [absent, making, done, unavailable]
      description: absent = 장면 단계 전 결과(채울 수 있다) · making = 채우는 중 · done = 끝남 · unavailable = 음성 파일 · 원본 없음
    FrameSet:
      type: object
      required: [state, frames]
      properties:
        state:
          $ref: '#/components/schemas/FramesState'
        frames:
          type: array
          items:
            $ref: '#/components/schemas/Frame'
          description: 장면이 있는 챕터만, 챕터 순서대로
    ImageQuality:
      type: string
      enum: [low, medium]
      description: 인포그래픽 품질. 첫 값 low(VA-PRD-001 R13)
    InfographicState:
      type: string
      enum: [none, making, done, failed]
    InfographicImage:
      type: object
      required: [url, model, quality, width, height, created_at, cost_usd]
      properties:
        url:
          type: string
          description: /api/videos/{id}/infographic/image?v={만든 시각}
        model:
          type: string
        quality:
          $ref: '#/components/schemas/ImageQuality'
        width:
          type: integer
        height:
          type: integer
        created_at:
          type: string
          format: date-time
          description: UI-4 '{만든 시각} 만듦'
        cost_usd:
          type: number
          description: 이 그림에 든 값(한 장 값)
    Infographic:
      type: object
      required: [state, image, error_reason]
      properties:
        state:
          $ref: '#/components/schemas/InfographicState'
        image:
          oneOf:
          - $ref: '#/components/schemas/InfographicImage'
          - type: 'null'
          description: 지금 쓰는 그림. 다시 만들기가 실패해도 이전 그림이 남는다
        error_reason:
          type: [string, 'null']
          description: failed일 때 한 줄
    Chapter:
      type: object
      required: [seq, part_seq, start_sec, title, bullets, frame]
      properties:
        seq:
          type: integer
        part_seq:
          type: [integer, 'null']
          description: 파트가 없으면 null
        start_sec:
          type: number
        title:
          type: string
        bullets:
          type: array
          items:
            type: string
          description: 요점 2~3줄
        frame:
          oneOf:
          - $ref: '#/components/schemas/Frame'
          - type: 'null'
          description: 대표 장면. 없으면 null(UI-4 6.7이 없다)
    SuggestedQuestion:
      type: object
      required: [seq, text]
      properties:
        seq:
          type: integer
        text:
          type: string
    Result:
      type: object
      required: [video, transcript, summary, parts, chapters, suggested_questions, models, analyzed_at, frames_state, infographic]
      properties:
        video:
          $ref: '#/components/schemas/Video'
        transcript:
          $ref: '#/components/schemas/Transcript'
        summary:
          $ref: '#/components/schemas/Summary'
        parts:
          type: array
          items:
            $ref: '#/components/schemas/Part'
          description: 60분 이하면 빈 배열
        chapters:
          type: array
          items:
            $ref: '#/components/schemas/Chapter'
        suggested_questions:
          type: array
          maxItems: 3
          items:
            $ref: '#/components/schemas/SuggestedQuestion'
        models:
          $ref: '#/components/schemas/Models'
        analyzed_at:
          type: string
          format: date-time
        frames_state:
          $ref: '#/components/schemas/FramesState'
        infographic:
          $ref: '#/components/schemas/Infographic'
    ChatTurn:
      type: object
      required: [id, question, answer, cited_secs, asked_at]
      properties:
        id:
          type: integer
        question:
          type: string
        answer:
          type: string
        cited_secs:
          type: array
          items:
            type: number
          description: 근거 시각들. 빈 배열이면 '영상에 없는 내용'
        asked_at:
          type: string
          format: date-time
    AskRequest:
      type: object
      required: [question]
      properties:
        question:
          type: string
    ExportRequest:
      type: object
      properties:
        with_chat:
          type: boolean
          default: false
    ExportFile:
      type: object
      required: [kind, name]
      properties:
        kind:
          type: string
          enum: [note, script, frame, infographic]
        name:
          type: string
          description: data/export/ 안의 파일 이름
    ExportPreview:
      type: object
      required: [filename, path, markdown, files]
      properties:
        filename:
          type: string
        path:
          type: string
          description: data/export/{filename}.md
        markdown:
          type: string
          description: 노트 전체(스크립트 줄 없음). method에 따라 그림 줄 · 스크립트 절이 있고 없다. 미리 보기는 화면이 앞부분만 보인다. 클립보드 복사가 method=clipboard의 이것을 쓴다
        files:
          type: array
          items:
            $ref: '#/components/schemas/ExportFile'
          description: method=file이면 함께 쓸 파일(UI-7 2.3 칩), clipboard면 빈 배열
    ExportResult:
      type: object
      required: [filename, path, bytes, images, files]
      properties:
        filename:
          type: string
        path:
          type: string
          description: 노트 경로 data/export/{filename}.md. 스크립트는 같은 폴더의 {filename} 스크립트.md
        bytes:
          type: integer
          description: 쓴 파일 전부의 바이트 합
        images:
          type: integer
          description: 쓴 그림 수(장면 + 인포그래픽). 짧은 알림 '· 그림 {n}장'
        files:
          type: array
          items:
            $ref: '#/components/schemas/ExportFile'
    KeyStatus:
      type: object
      required: [state, masked, stored_in, checked_at, reason_kind, reason]
      properties:
        state:
          $ref: '#/components/schemas/KeyState'
        masked:
          type: [string, 'null']
          description: 앞 3자 · 끝 4자만. 없으면 null
        stored_in:
          type: [string, 'null']
          description: 저장된 곳 표시 문구. 키가 있으면 늘 '.env에 저장됨', 없으면 null
        checked_at:
          type: [string, 'null']
          format: date-time
        reason_kind:
          oneOf:
          - $ref: '#/components/schemas/ReasonKind'
          - type: 'null'
        reason:
          type: [string, 'null']
          description: 확인 실패 이유 한 줄. UI-1 배너 · UI-5 2.5
    ModelPrice:
      type: object
      properties:
        per_min_usd:
          type: number
          description: 받아쓰기 모델
        input_per_mtok_usd:
          type: number
          description: 텍스트 모델 입력
        output_per_mtok_usd:
          type: number
          description: 텍스트 모델 출력
    ModelOption:
      type: object
      required: [id, label, price]
      properties:
        id:
          type: string
        label:
          type: string
        price:
          $ref: '#/components/schemas/ModelPrice'
    ModelOptions:
      type: object
      required: [stt, text]
      properties:
        stt:
          type: array
          items:
            $ref: '#/components/schemas/ModelOption'
          description: 구간 시각을 주는 모델만
        text:
          type: array
          items:
            $ref: '#/components/schemas/ModelOption'
    ImageQualityOption:
      type: object
      required: [id, label, price_usd]
      properties:
        id:
          $ref: '#/components/schemas/ImageQuality'
        label:
          type: string
          description: '낮음' · '중간'
        price_usd:
          type: number
          description: 한 장 값. UI-4 · UI-5 · UI-8이 같이 쓴다
    ImageSettings:
      type: object
      required: [model, quality, models, qualities]
      properties:
        model:
          type: string
          description: 고른 이미지 모델. 첫 값 gpt-image-2
        quality:
          $ref: '#/components/schemas/ImageQuality'
        models:
          type: array
          items:
            type: string
        qualities:
          type: array
          items:
            $ref: '#/components/schemas/ImageQualityOption'
    Settings:
      type: object
      required: [key, models, model_options, image, inbox_path]
      properties:
        key:
          $ref: '#/components/schemas/KeyStatus'
        models:
          $ref: '#/components/schemas/Models'
        model_options:
          $ref: '#/components/schemas/ModelOptions'
        image:
          $ref: '#/components/schemas/ImageSettings'
        inbox_path:
          type: string
          description: 사용자에게 보일 호스트 쪽 경로
    KeyRequest:
      type: object
      required: [key]
      properties:
        key:
          type: string
          minLength: 1
    ModelsRequest:
      type: object
      required: [stt_model, text_model]
      properties:
        stt_model:
          type: string
        text_model:
          type: string
        image_model:
          type: string
          description: 없으면 그대로 둔다
        image_quality:
          $ref: '#/components/schemas/ImageQuality'
```

시각 필드는 두 종류다. `*_sec`는 영상 속 시각·길이로 초 단위 숫자, `*_at`은 때로 ISO 8601 UTC. 화면이 `mm:ss`·`h:mm:ss`와 '오늘 14:08'을 만든다.

스키마 이름은 [[VA-DOM-001]] 3장의 개념명과 같다 — Video · Transcript · Segment · Summary · Insight · Part · Chapter · SuggestedQuestion · ChatTurn · Infographic. 대표 장면(ChapterFrame)의 응답형은 `Frame`이다. `Job`은 AnalysisJob의 응답형, `Chunk`는 AudioChunk의 응답형이다. 클래스 명세를 다시 쓸 때 이 이름을 그대로 쓴다.

---

## 5. 판단이 필요한 지점

**1. 영상은 사전 안내 전에 만들고, 작업은 [분석 시작] 때 만든다 — 결정: [[#POST/api/videos]]가 Video(`registered`)를 만들어 id를 주고, 목록은 작업 있는 영상만 보인다.**
이유: UI-2가 열리기 전에 정보 조회와 중복 판정이 끝나야 하고, [분석 시작]이 같은 정보를 두 번 조회하지 않아야 한다. 취소해도 행은 남지만 보이지 않고, 다시 넣으면 정보를 다시 조회해 덮어쓴다. [[VA-DOM-001#Video]]는 '분석완료시각이 비어 있으면 결과가 없는 영상'이라고만 하고 작업 없는 영상을 말하지 않는다 — 6장 갱신 요청.

**2. 작업의 `status`와 `stage`를 나눈다 — 결정: `status`(queued · running · failed · done)와 `stage`(파이프라인 단계)를 따로 둔다.**
이유: 실패한 단계를 알려면 상태와 단계가 같이 있어야 한다. UI-3의 '{단계} 단계가 멈췄어요'와 '{단계}부터 다시 시도'가 그것이다. [[VA-DOM-001#AnalysisJob]]의 '단계'는 둘을 합쳐 말한다 — 클래스 명세를 다시 쓸 때 반영.

**3. 결과는 한 번에 준다 — 결정: [[#GET/api/videos/{id}/result]]가 구간 수천 개까지 한 응답.**
이유: UI-4가 한 화면이고 시각 이동이 구간 전체를 필요로 한다. 3시간 영상이 3,000구간 안팎, 수백 KB이고 localhost라 문제가 없다([[VA-INFRA-001#C5]]). 대화 기록만 따로 둔다 — 묶음이 다르고([[VA-DOM-001]] 4장) 질문마다 늘어난다.

**4. 파이프라인 실패는 HTTP 에러가 아니다 — 결정: `Job.error`로 전한다.**
이유: 백그라운드라 그 순간 요청이 없다. 화면은 `kind`로 제목을, `reason`으로 이유를, `chunk_seq` · `attempts` · `chunks.done` · `chunks.next_seq`로 나머지 문장을 만든다([[VA-UI-002]] 1.6).

**5. 클립보드 복사는 브라우저가 한다 — 결정: 서버는 마크다운 텍스트를 주고 파일 쓰기만 직접 한다.**
이유: 서버 프로세스는 사용자 클립보드에 닿을 수 없다. 같은 마크다운을 두 엔드포인트가 만드므로 내용이 갈리지 않는다.

**6. 429를 만들지 않는다 — 결정: OpenAI 사용량 초과는 `llm-unavailable`(502)의 `reason`으로 접는다.**
이유: 우리가 한도를 세지 않는다. 사용자 한 명이고 비용은 사전 안내에서 보고 결정한다([[VA-PRD-001#R8]]).

**7. 키 상태 조회는 재확인하지 않는다 — 결정: [[#GET/api/settings]]는 마지막 결과만 준다.**
이유: 페이지마다 배너를 그리려고 부르는데 그때마다 OpenAI로 요청이 나가면 안 된다. 확인은 시작 · 분석 버튼 · 키 저장 때만 한다([[VA-UI-002#UI-5]] 규칙).

**8. 동시 분석은 하나 — 결정: 두 번째 시작은 거절하지 않고 대기열에 넣는다(`status = queued`).**
이유: 사용자 결정(2026-09-21, [[VA-UI-001]] 7장 16). 긴 받아쓰기가 도는 동안 다음 영상을 걸어 두고 자리를 뜰 수 있다. 함께 돌리지 않는 것은 [[VA-INFRA-001]] 3절(프로세스 안 asyncio 태스크, 워커 하나)과 OpenAI 요청 한도 · 비용 예측 때문이다. 그래서 409 `another-job-running`은 없앴고 에러는 17종이다. 차례는 `queue_position` 하나로 주고, UI-1의 '{n}번째'와 UI-3의 '앞 영상 {n}개'가 같은 값을 쓴다 — 도는 작업 하나 + 앞에서 기다리는 작업 수가 곧 대기열에서의 차례다.

**11. 연결 실패는 막지 않고 다시 확인한다 — 결정: 마지막 확인이 `network`면 분석 시작 · 다시 시도 · 질문이 그 자리에서 한 번 다시 확인한다.**
이유: 배너 문구가 '인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다'다([[VA-UI-002]] 1.4). 마지막 결과만 보고 막으면 인터넷이 돌아와도 분석 버튼을 누르기 전에는 다시 시도와 질문이 풀리지 않는다. 다른 실패(형식 · 인증 · 잔액)는 다시 확인해도 같으므로 마지막 결과로 막는다.

**9. 단계 목록을 서버가 준다 — 결정: `Job.stages`.**
이유: 출처마다 필요한 단계만 보이는 규칙([[VA-UI-002#UI-3]])을 화면이 조합하면 서버의 파이프라인과 두 벌이 된다. 서버가 실제로 돌릴 순서를 그대로 준다.

**12. 파일 올리기는 원문 본문 한 요청 — 결정: [[#POST/api/uploads]]가 `application/octet-stream` 본문을 스트림으로 받는다.**
이유: 화면이 XHR 한 요청으로 보내면 `upload.onprogress`로 진행이 그대로 나온다. 같은 PC라 끊겨도 처음부터 다시 올리면 된다 — 조각으로 나눠 이어 올리기(tus 등)는 서버에 이어 붙이기 · 상태가 늘어 두지 않았다([[VA-INFRA-001]] 3절). multipart가 아니라 원문인 것은 파일 하나뿐이고 이름은 헤더로 충분해서다. 키 · 형식 · 디스크 판정을 본문 전에 해, 수 GB를 받은 뒤에 거절하지 않는다.

**13. 인포그래픽은 맡기고 바로 돌려준다 — 결정: [[#POST/api/videos/{id}/infographic]]은 202이고 결과는 폴링.**
이유: 그림 한 장에 수십 초가 걸릴 수 있어 web 넘기기의 시간 제한(60초)에 걸린다. 사용자가 그리는 동안 결과를 읽거나 다른 화면으로 가도 그림이 이어져야 한다([[VA-UI-001]] UI-4 규칙).

**14. 장면 채우기는 화면이 시킨다 — 결정: 옛 결과는 UI-4가 `frames_state = absent`를 보고 [[#POST/api/videos/{id}/frames]]를 부른다.**
이유: [[#GET/api/videos/{id}/result]]가 부를 때마다 일을 벌이면 GET이 저장된 것을 바꾼다. 화면이 한 번 시키고 가벼운 [[#GET/api/videos/{id}/frames]]로 지켜본다. 두 번 시켜도 같다.

**15. 그림은 api가 파일로 준다 — 결정: 장면 · 인포그래픽은 `…/frames/{seq}` · `…/infographic/image`의 JPEG · PNG.**
이유: 브라우저는 web만 보고 web이 `/api/*`를 넘기므로(1장) 그림도 같은 길로 받는다. base64로 JSON에 넣으면 결과 응답이 수백 KB씩 커진다. 그림 주소는 응답의 `url` 그대로 쓴다.

**10. `Video.status`를 응답에 둔다 — 결정: 최근 작업에서 계산한 값.**
이유: 화면이 갈 곳을 정하는 분기가 다섯 곳(UI-1 분석 버튼, 목록 행, UI-3 · UI-4 주소 진입, UI-6)이고 모두 같은 판정이다. 작업 유무와 상태를 화면마다 조합하지 않게 한 값으로 준다.

---

## 6. 미결사항

- [x] 분석이 도는 동안 새 분석 — 결정: 대기열(`status = queued`, `queue_position`). 409 `another-job-running`은 없앴다(5장 8, 사용자 결정 2026-09-21)
- [x] 웹에서 받은 키의 저장 위치 — 결정: `.env` 파일 하나, 앱이 그 줄을 고친다. `KeyStatus.stored_in`은 '.env에 저장됨' 고정([[VA-INFRA-001#C6]], 사용자 결정 2026-09-21)
- [ ] 예상 비용의 텍스트 모델 몫(`Estimate.text_cost_usd`) 추정식 — MINISPEC
- [x] 인포그래픽 `low` 한 장 값(`ImageQualityOption.price_usd`) — 결정: $0.01. 카드 D3에서 실제 한 장이 $0.0096이었다([[VA-INFRA-001]] 9장)
- [ ] 인포그래픽 `medium` 한 장 값 — 재지 않아 첫 값 $0.05(외부 가격 정리) 그대로다. 처음 만들 때 사용량으로 고친다([[VA-INFRA-001]] 9장)
- [ ] 올리기 요청의 시간 제한 — web 라우트 핸들러가 api로 넘기는 요청은 넘기기의 60초 제한을 받지 않지만, 넘기는 쪽(Node `fetch`)의 기본 대기가 300초다. 같은 PC라 수 GB도 그 안이지만 카드 D4에서 588MB 파일로 잰다(MINISPEC 영상 서비스 3장과 같은 항목)
- [x] 디스크 판정의 여유분 — 결정: 고정 1 GiB. 파일 크기의 몇 %로 두면 작은 파일에 여유가 모자란다. 분석이 그 뒤에 쓰는 임시 음성 · 조각 · 장면을 넉넉히 덮는다(MINISPEC 영상 서비스 0장 `UPLOAD_SPARE_BYTES`)
- [x] 조각이 없는 단계의 `Job.remaining_sec` 계산 — 결정: 예상 전체 시간 − 지난 시간, 0이면 화면이 비운다(MINISPEC 작업 서비스 `JobService.remaining_sec`). 바꿈(사용자 결정, 2026-09-23): 작업 전체가 끝날 때까지, 끝난 단계의 오차는 넘기지 않는다 — 받아쓰기에 요약 세 단계 몫을 더하고 요약 세 단계는 그 몫에서 뺀다([[VA-UI-001]] 8장)
- [ ] inbox 파일 길이 재기 비용 — 파일마다 ffprobe. 수십 개면 첫 응답이 느릴 수 있어 수정 시각 기준 캐시를 둘지 MINISPEC
- [x] 내보내기 파일 이름 규칙(제목 → 파일 이름, 금지 문자, 같은 이름) — 반영: MINISPEC 결과 서비스 `AnalysisService.filename_for`. 같은 이름은 덮어쓴다 — `-{id}`를 붙이지 않는다(사용자 결정 2026-09-28)
- [ ] 서버 재시작으로 죽은 작업 — 시작 때 `running`인 작업을 `failed`(kind `unknown`)로 돌려 다시 시도할 수 있게. 클래스 명세 · MINISPEC
- [x] 작업 없는 영상(`registered`)과 `status` · `stage` 분리를 [[VA-DOM-001#Video]] · [[VA-DOM-001#AnalysisJob]]과 다시 쓸 클래스 명세에 반영(5장 1 · 2) — 반영: 도메인 모델 v3 · 클래스 명세 v10
- [x] `Video.status`가 `failed`인 영상을 목록에서 구분하는 것 — 반영: 도메인 모델 v3 Video(완료 · 진행 중 · 대기 중 · 실패)
- [ ] 설정 서비스가 사는 곳 — 키 · 모델은 도메인이 아니다([[VA-DOM-001]] 1장). `SettingsService`를 `core/`에 둘지 클래스 명세에서
- [x] (반영: ERD v4 `queued_at` · 작업 서비스 MINISPEC v2) **되먹임** 대기열의 순서 기준 — 다시 시도한 작업은 대기열 끝으로 간다(3.4 다시 시도 3번). `started_at`은 다시 시도해도 그대로라 순서 기준으로 쓸 수 없다. `analysis_jobs`에 대기열에 들어간 때(`queued_at`)가 필요하다 — ERD · MINISPEC(작업 서비스)
- [x] (반영: 설정 서비스 MINISPEC v2 `require_key` · 화면 설계 v6 UI-1 규칙 · 클래스 명세 v12) **되먹임** 연결 실패 뒤 다시 확인(5장 11) — MINISPEC(설정 서비스)의 「마지막 결과로 막기」가 마지막 결과가 `network`면 한 번 다시 확인하게 고친다. [[VA-UI-001#UI-1]] 규칙에도 「연결 실패는 막지 않는다」 한 문장([[VA-UI-002]] 2장의 같은 되먹임)
