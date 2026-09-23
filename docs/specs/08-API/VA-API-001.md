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

브라우저(Next.js)가 부르는 REST API다. 와이어프레임의 화면 7개([[VA-UI-002]])가 서버에서 받아야 하는 값과 서버에 시켜야 하는 일을 엔드포인트로 옮겼다. 입구는 웹 하나뿐이라 MCP 문서는 없다([[VA-INFRA-001#C10]]).

엔드포인트는 16개, 묶음은 여섯이다 — 설정과 키 · inbox · 영상 · 작업 · 결과와 내보내기 · 대화. 뒤 넷은 [[VA-DOM-001]] 4장의 묶음(video · job · analysis · chat)과 같고, 설정과 inbox는 도메인이 아니라 인프라 값을 읽고 쓰는 곳이다([[VA-INFRA-001#C4]], [[VA-INFRA-001#C6]]).

이 문서가 정하는 것: 경로·메서드·요청과 응답의 모양·에러·호출 순서. 정하지 않는 것: 서비스 메서드의 안(MINISPEC), 테이블(ERD), 화면 문구(와이어프레임).

---

## 1. 규칙

- 인증이 없다. 서버는 `127.0.0.1`에만 묶이고 사용자는 한 명이다([[VA-INFRA-001#C5]]). 모든 경로는 `/api/` 아래이고 요청·응답은 JSON뿐이다([[VA-INFRA-001#C10]]).
- 에러는 RFC 9457 `application/problem+json`이다. `type`은 `urn:va:{종류}`이고 종류별 확장 필드는 2장에 있다.
- 때를 나타내는 값(`*_at`)은 ISO 8601 UTC다. **영상 속 시각(`*_sec`)은 초 단위 숫자**이고 소수를 허용한다. `mm:ss`·`h:mm:ss` 표기는 화면이 한다([[VA-UI-001#UI-4]] 시각 표기).
- 식별자는 정수 `id`다. 화면 주소 `/videos/{id}`의 id와 같은 값이다([[VA-UI-001#UI-3]], [[VA-UI-001#UI-4]]).
- 목록에 페이지가 없다. 사용자 한 명이 분석한 영상은 수십 개다.
- **화면은 계산하지 않는다.** 예상 시간·비용·조각 수·동시 수·남은 시간·진행률은 서버가 준 숫자를 그대로 보인다([[VA-UI-002#UI-2]]·[[VA-UI-002#UI-3]] 규칙). 문장을 조립하는 것은 화면이고, 서버는 코드값과 숫자, 그리고 실패 이유 한 줄(`reason`, 한국어)을 준다.
- **키 없이도 읽기는 전부 된다.** OpenAI API 키가 없거나 확인에 실패해도 GET은 모두 동작한다. 막히는 것은 분석 시작·다시 시도·질문 셋뿐이고, 그때 `key-missing` 또는 `key-invalid`(503)가 난다([[VA-UI-002]] 1.4 키 없음 배너, [[VA-PRD-001#N3]]).
- 키를 확인하는 때는 셋이다 — 서버가 시작할 때, [[#POST/api/videos]](분석 버튼)를 받을 때, [[#POST/api/settings/key]]를 받을 때. [[#GET/api/settings]]는 마지막 확인 결과를 돌려줄 뿐 다시 확인하지 않는다([[VA-UI-002#UI-5]] 규칙).
- **마지막 확인이 연결 실패(`reason_kind = network`)였으면 막지 않고 그때 한 번 다시 확인한다.** 분석 시작·다시 시도·질문이 그렇다. 키가 틀린 것이 아니라 인터넷이 없었던 것이라, 화면은 버튼을 막지 않고 배너 문구만 가른다([[VA-UI-002]] 1.4). 다시 확인해 통과하면 요청이 그대로 이어지고, 또 닿지 못하면 503 `key-invalid`(`reason_kind = network`)다.
- **동시에 도는 분석은 하나이고 나머지는 대기열에서 차례를 기다린다**([[VA-PRD-001#R8]], [[VA-INFRA-001]] 3절). 시작 요청은 거절되지 않는다 — 도는 작업이 있으면 `status = queued`로 들어가고, 앞 작업이 끝나면(완료든 실패든) 서버가 가장 오래 기다린 것을 저절로 시작한다.
- 진행 상태는 폴링이다. 화면이 1초마다 [[#GET/api/videos/{id}/job]]을 부른다([[VA-INFRA-001]] 3절). SSE·WebSocket은 없다.
- 밖으로 나가는 것은 YouTube에 영상 ID, OpenAI에 음성 조각·스크립트 텍스트·질문과 앞선 대화·키 확인 요청뿐이다. 영상 파일·결과·키는 나가지 않는다([[VA-INFRA-001#C9]]).
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

---

## 2. 에러

`application/problem+json`. 공통 필드 `type`, `title`, `status`, `detail`. 종류별 확장 필드:

| type | status | 언제 | 확장 필드 | 근거 |
|---|---|---|---|---|
| `urn:va:not-found` | 404 | 영상·작업·inbox 파일 없음 | `resource`(`video` · `job` · `inbox_file`) · `id` | [[VA-UI-002#UI-3]] 규칙(영상이 없으면 UI-1로) |
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
| `urn:va:llm-unavailable` | 502 | OpenAI 호출 실패(질문 답변, 키 확인 중 네트워크). 사용량 초과도 여기 | `reason` | [[VA-UC-001#UC-H4]] 2a |
| `urn:va:export-failed` | 500 | `data/export/`에 파일을 쓰지 못함 | `path` · `reason` | [[VA-UC-001#UC-H7]], [[VA-UI-002#UI-7]] |
| `urn:va:internal` | 500 | 예상 못 한 오류. `detail`은 고정 문구, 원인은 로그만 | — | — |

**표에 없는 예외도 problem+json으로 나간다.** 서버는 포괄 핸들러로 `urn:va:internal`(500)을 만든다. 클라이언트가 problem+json을 전제로 파싱하는데 평문 500이 나가면 오류를 읽지도 못한다.

**삭제 실패에는 종류가 없다.** [[VA-UI-002#UI-6]]의 실패 한 줄('분석 결과를 지우지 못했어요 — {이유}')은 `internal`의 `detail`을 쓴다. 지우기가 실패하는 경우는 디스크·DB 오류뿐이라 따로 가를 것이 없다.

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

받아쓰기 모델과 요약·챕터·질문 모델을 저장한다. UI-5 페이지 아래 [저장]이 부른다. 키는 건드리지 않는다.

- 값은 `Settings.model_options`에 있는 id만 받는다. 아니면 422 `urn:va:validation`.
- 저장한 모델은 다음 작업과 질문부터 쓴다. 돌고 있는 작업은 시작할 때의 모델을 끝까지 쓴다.
- 저장하는 곳은 키와 같은 `.env` 파일이다(`STT_MODEL` · `TEXT_MODEL` 줄, [[VA-INFRA-001#C6]]).

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

#### GET/api/videos/{id} 영상 하나와 지금 상태

영상 정보와 작업 요약을 준다. 결과 본문은 없다. UI-3 영상 머리, UI-4 주소로 바로 들어왔을 때의 판정, UI-6 다이얼로그(질문 기록 수 · 진행 중 여부)가 부른다.

- `job`은 가장 최근 작업의 요약이고 작업이 없으면 null이다.
- UI-6은 `video.chat_turn_count`로 '질문 기록 {n}개'를, `video.status`가 `in_progress` · `failed`이면 '임시 음성 파일'을 더한다([[VA-UI-002#UI-6]] 규칙).
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

영상과 스크립트 · 요약 · 챕터 · 추천 질문 · 대화 · 조각 행 · `data/tmp/{id}`를 지운다. UI-6 [삭제]가 부른다.

- 진행 중이면 백그라운드 작업을 먼저 멈추고 지운다. 대기 중이면 대기열에서 빠진다 — 뒤에 기다리던 작업의 `queue_position`이 하나씩 당겨진다. 도는 작업을 지우면 다음 대기 작업이 시작된다([[VA-UC-001#UC-H6]] 4a). 실패한 영상은 보존된 조각 파일까지 지운다([[VA-UI-002#UI-6]] 규칙, [[VA-UI-001]] 7장 13).
- inbox의 원본 파일은 건드리지 않는다([[VA-INFRA-001#C4]], [[VA-UC-001#UC-H6]] 성공 보장).
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
- 파이프라인은 `stages` 순서대로 돈다 — 자막 있는 YouTube: download(자막) → summarize → chapter → suggest · 자막 없는 YouTube: download(음성) → transcribe → summarize → chapter → suggest · 로컬 영상: extract → transcribe → summarize → chapter → suggest · 로컬 음성: transcribe → summarize → chapter → suggest([[VA-UC-001#UC-S2]], [[VA-UC-001#UC-H2]] 2b, [[VA-UI-002#UI-3]] 규칙).
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
| 단계 메모(4.4) | 완료 단계는 `stage_durations_sec`, 받아쓰기는 `chunks.done` / `chunks.total` |
| 조각 격자 · 범례(4.6 ~ 4.8) | `chunks.items[].state` · `chunks.done` · `in_flight` · `failed` · `waiting` |
| 실패 알림(5) | `error.kind`(제목) · `error.reason`(왜) · `error.chunk_seq` · `error.attempts` · `chunks.done`(보존된 것) · `chunks.next_seq`(r) |
| 전송 표시(6.1) | `stage` · `models.stt` · `models.text` · `concurrency` |
| 떠나기 안내(6.2) | `stage` · `chunks.next_seq` |

- `remaining_sec`는 받아쓰기 단계에서 미완료 조각 수 × 지금까지 조각당 평균이다([[VA-UC-001#UC-S6]] 2번). 조각이 없는 단계는 예상 전체 시간에서 지난 시간을 뺀 값이고 0보다 작아지지 않는다(MINISPEC 작업 서비스 `JobService.remaining_sec`). **0이면 화면은 남은 시간을 비운다** — '약 0초'를 보이지 않는다. 돌고 있지 않으면(`queued` · `failed` · `done`) null이다.
- `chunks`는 받아쓰기가 있는 작업에만 있고, 받아쓰기가 끝난 뒤에도 남는다(모두 `done`). `next_seq`는 완료하지 않은 첫 조각 번호이고 모두 끝나면 null이다.
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
- 결과는 읽기만 한다. 이 요청으로 저장된 것이 바뀌지 않는다([[VA-UC-001#UC-H3]] 최소 보장).

| UI-4 요소 | `Result` 필드 |
|---|---|
| 칩 셋(2.1) | `video.source_kind` · `video.duration_sec` · `transcript.source` · `transcript.language` |
| 영상 제목(2.2) · 메타 줄(2.3) · 원본 영상 열기(2.4) | `video.title` · `video.channel` · `analyzed_at` · `models` · `video.origin`(YouTube만) |
| 한 줄 요약(3) · 핵심 인사이트(4) | `summary.one_liner` · `summary.insights[].text` · `source_secs` |
| 이런 걸 물어볼 수 있어요(5) · 추천 칩(10.1) | `suggested_questions` |
| 챕터(6) · 파트(6.4 ~ 6.6) | `chapters` · `parts`(60분 이하면 빈 배열) · `parts[].start_sec` · `end_sec` · `chapter_count` |
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

#### GET/api/videos/{id}/export 마크다운 본문

내보낼 마크다운 전체와 파일 이름을 준다. UI-7이 열릴 때 미리 보기용으로, [복사하기]를 눌렀을 때 클립보드용으로 부른다.

- 쿼리 `with_chat`(기본 false)이 true면 맨 아래 질문 기록이 붙는다([[VA-UC-001#UC-H7]] 2b). 체크박스를 바꾸면 화면이 다시 부른다.
- 내용 순서([[VA-UC-001#UC-H7]] 2번, [[VA-PRD-001#R10]]): `# {제목}` → `원본: {링크} · {길이}`(로컬 파일은 `원본: {파일 이름} · {길이}`, 링크 없음) → `> {한 줄 요약}` → `## 핵심 인사이트` 번호 목록(문장 끝에 시각) → `## 챕터`(챕터마다 `### [{시각}]({링크}) {제목}`과 `- {요점}`) → `## 스크립트` 구간 줄 → (`with_chat`) `## 질문 기록`.
- 시각은 `[mm:ss]`(1시간 이상 영상은 `[h:mm:ss]`) 텍스트다. YouTube면 `https://youtu.be/{영상ID}?t={초}` 링크가 걸리고 로컬 파일이면 시각만 남는다([[VA-UI-002#UI-7]] 규칙).
- 미리 보기는 화면이 앞부분만 잘라 보인다. 클립보드 복사는 브라우저가 `markdown` 전체로 한다 — 서버는 클립보드에 닿을 수 없다(5장 5).
- 결과가 없으면 409 `urn:va:result-not-ready`. 파일 이름 규칙은 6장 미결이다.

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

같은 마크다운을 서버가 `data/export/{filename}.md`에 쓴다. UI-7 [파일로 저장]이 부른다.

- 본문 `with_chat`은 GET의 쿼리와 같은 뜻이다.
- 같은 이름의 파일이 있으면 덮어쓴다. 브라우저 다운로드는 없다([[VA-UI-001]] 7장 14).
- 201에 `ExportResult`(`path`는 화면의 짧은 알림 '{path}에 저장했어요'에 들어간다).
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
3. `question`이 비어 있으면 422 `urn:va:validation`.
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
      enum: [pending, download, extract, transcribe, summarize, chapter, suggest]
      description: 파이프라인 단계. 화면 이름 대응은 VA-UI-002 UI-3 규칙 — download는 자막이 있으면 '자막 가져오기', 없으면 '음성 내려받기'
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
      description: 키 확인 실패 이유. network는 키가 틀린 것이 아니라 OpenAI에 닿지 못한 것 — 화면이 배너 문구를 가르고 버튼을 막지 않는다(VA-UI-002 1.4)
    ErrorKind:
      type: string
      enum: [network, openai, youtube, ffmpeg, disk, unknown]
      description: 파이프라인 실패 종류. 화면이 실패 알림 제목(UI-3 5.1)을 고른다
    Video:
      type: object
      required: [id, source_kind, source_id, title, channel, duration_sec, origin, has_captions, caption_language, caption_kind, status, analyzed_at, created_at, chat_turn_count]
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
          description: YouTube URL 또는 inbox 파일 이름. UI-4 '원본 영상 열기'
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
      required: [id, video_id, status, stage, queue_position, stages, stage_index, progress_pct, remaining_sec, chunks, concurrency, models, error, est_seconds, est_cost_usd, stage_durations_sec, started_at, finished_at]
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
    Chapter:
      type: object
      required: [seq, part_seq, start_sec, title, bullets]
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
      required: [video, transcript, summary, parts, chapters, suggested_questions, models, analyzed_at]
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
          minLength: 1
    ExportRequest:
      type: object
      properties:
        with_chat:
          type: boolean
          default: false
    ExportPreview:
      type: object
      required: [filename, path, markdown]
      properties:
        filename:
          type: string
        path:
          type: string
          description: data/export/{filename}.md
        markdown:
          type: string
          description: 전체. 미리 보기는 화면이 앞부분만 보인다
    ExportResult:
      type: object
      required: [filename, path, bytes]
      properties:
        filename:
          type: string
        path:
          type: string
        bytes:
          type: integer
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
    Settings:
      type: object
      required: [key, models, model_options, inbox_path]
      properties:
        key:
          $ref: '#/components/schemas/KeyStatus'
        models:
          $ref: '#/components/schemas/Models'
        model_options:
          $ref: '#/components/schemas/ModelOptions'
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
```

시각 필드는 두 종류다. `*_sec`는 영상 속 시각·길이로 초 단위 숫자, `*_at`은 때로 ISO 8601 UTC. 화면이 `mm:ss`·`h:mm:ss`와 '오늘 14:08'을 만든다.

스키마 이름은 [[VA-DOM-001]] 3장의 개념명과 같다 — Video · Transcript · Segment · Summary · Insight · Part · Chapter · SuggestedQuestion · ChatTurn. `Job`은 AnalysisJob의 응답형, `Chunk`는 AudioChunk의 응답형이다. 클래스 명세를 다시 쓸 때 이 이름을 그대로 쓴다.

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

**10. `Video.status`를 응답에 둔다 — 결정: 최근 작업에서 계산한 값.**
이유: 화면이 갈 곳을 정하는 분기가 다섯 곳(UI-1 분석 버튼, 목록 행, UI-3 · UI-4 주소 진입, UI-6)이고 모두 같은 판정이다. 작업 유무와 상태를 화면마다 조합하지 않게 한 값으로 준다.

---

## 6. 미결사항

- [x] 분석이 도는 동안 새 분석 — 결정: 대기열(`status = queued`, `queue_position`). 409 `another-job-running`은 없앴다(5장 8, 사용자 결정 2026-09-21)
- [x] 웹에서 받은 키의 저장 위치 — 결정: `.env` 파일 하나, 앱이 그 줄을 고친다. `KeyStatus.stored_in`은 '.env에 저장됨' 고정([[VA-INFRA-001#C6]], 사용자 결정 2026-09-21)
- [ ] 예상 비용의 텍스트 모델 몫(`Estimate.text_cost_usd`) 추정식 — MINISPEC
- [x] 조각이 없는 단계의 `Job.remaining_sec` 계산 — 결정: 예상 전체 시간 − 지난 시간, 0이면 화면이 비운다(MINISPEC 작업 서비스 `JobService.remaining_sec`)
- [ ] inbox 파일 길이 재기 비용 — 파일마다 ffprobe. 수십 개면 첫 응답이 느릴 수 있어 수정 시각 기준 캐시를 둘지 MINISPEC
- [ ] 내보내기 파일 이름 규칙(제목 → 파일 이름, 금지 문자, 같은 이름) — MINISPEC
- [ ] 서버 재시작으로 죽은 작업 — 시작 때 `running`인 작업을 `failed`(kind `unknown`)로 돌려 다시 시도할 수 있게. 클래스 명세 · MINISPEC
- [x] 작업 없는 영상(`registered`)과 `status` · `stage` 분리를 [[VA-DOM-001#Video]] · [[VA-DOM-001#AnalysisJob]]과 다시 쓸 클래스 명세에 반영(5장 1 · 2) — 반영: 도메인 모델 v3 · 클래스 명세 v10
- [x] `Video.status`가 `failed`인 영상을 목록에서 구분하는 것 — 반영: 도메인 모델 v3 Video(완료 · 진행 중 · 대기 중 · 실패)
- [ ] 설정 서비스가 사는 곳 — 키 · 모델은 도메인이 아니다([[VA-DOM-001]] 1장). `SettingsService`를 `core/`에 둘지 클래스 명세에서
- [x] (반영: ERD v4 `queued_at` · 작업 서비스 MINISPEC v2) **되먹임** 대기열의 순서 기준 — 다시 시도한 작업은 대기열 끝으로 간다(3.4 다시 시도 3번). `started_at`은 다시 시도해도 그대로라 순서 기준으로 쓸 수 없다. `analysis_jobs`에 대기열에 들어간 때(`queued_at`)가 필요하다 — ERD · MINISPEC(작업 서비스)
- [x] (반영: 설정 서비스 MINISPEC v2 `require_key` · 화면 설계 v6 UI-1 규칙 · 클래스 명세 v12) **되먹임** 연결 실패 뒤 다시 확인(5장 11) — MINISPEC(설정 서비스)의 「마지막 결과로 막기」가 마지막 결과가 `network`면 한 번 다시 확인하게 고친다. [[VA-UI-001#UI-1]] 규칙에도 「연결 실패는 막지 않는다」 한 문장([[VA-UI-002]] 2장의 같은 되먹임)
