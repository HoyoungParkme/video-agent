---
doc_id: VA-MS-004
type: MS
title: MINISPEC — ChatService
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-DOM-003, VA-UC-001, VA-PRD-001]
---

# MINISPEC — ChatService

## 0. 이 문서가 다루는 것

`domains/chat/service.py`의 함수 4개. 클래스 명세 [[VA-DOM-002#ChatService]]의 시그니처를 함수 내부까지 내린 것. 포트 · 어댑터(`answerer_openai`)는 4.6 · 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10. 내부 타입(`AnswerDraft`)은 [[VA-DOM-002]] 2.6, 응답 형태(`ChatTurn` `Segment` `Chapter`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `DB:` 테이블 접근(`crud`를 거친다).

**이 묶음이 아는 것** — `chat_turns` 테이블 하나. 구간 · 챕터는 `AnalysisService`에 `video_id`로 묻고 DTO 목록을 받는다([[VA-DOM-002]] 3.2). 결과를 바꾸지 않는다([[VA-DOM-001]] 4장). 세션은 라우터의 것.

**만들기** — `ChatService(session, answerer)`. 포트는 `ask`만 쓴다 — 영상 목록의 대화 수는 `ChatService(session)`, 구간 · 챕터는 `AnalysisService(session)`로 포트 없이 읽는다([[VA-DOM-002]] 6장).

**설정값(첫 값)**

| 이름 | 첫 값 | 이유 |
|---|---|---|
| `config.CHAT_HISTORY_TURNS` | 10 | 맥락에 넣는 앞선 턴 수([[VA-DOM-002]] 4.4 규칙) |
| `config.CHAT_TOKEN_LIMIT` | 30000 | 맥락 구간의 토큰 상한. 넘으면 챕터로 고른다. 답 10초 목표([[VA-PRD-001#N1]])에 맞춘 값. 실측(카드 C): 스크립트 7만 5천 토큰(2시간 30분)을 통째로 보내면 답이 8.6~12초였다 |
| `config.CHAT_CHAPTERS` | 3 | 관련 챕터로 고르는 수(점수로). 직전 턴의 근거 챕터는 이것과 따로 더한다 |
| `config.CHAT_SUMMARY_WEIGHT` | 3 | 챕터 글에서 제목 · 요점의 조각을 세는 배수 — 짧지만 그 챕터를 가장 잘 말한다. 실측(2026-10-01, 상위 3챕터에 정답이 든 수): 스크립트만 — 2:30:30 강의 29문항 27, 영상 1 · 4(상한을 낮춤) 16문항 14 · 제목 · 요점 × 3 + 스크립트 — 27, 15 |
| `config.CHAT_BM25_K1` · `config.CHAT_BM25_B` | 1.2 · 0.75 | BM25의 흔한 값 — 같은 조각이 거듭 나올 때 점수가 느는 정도 · 긴 챕터를 깎는 정도 |
| `config.CHAT_TIMEOUT_SEC` | 20 | 모델 호출 시간 제한. 넘으면 `llm-unavailable` |

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#ChatService.history]] | 영상의 대화 턴, 시간순 |
| [[#ChatService.ask]] | 질문 → 맥락 → 모델 → 저장 |
| [[#ChatService.count_by_videos]] | 영상별 턴 수, 쿼리 하나 |
| [[#ChatService.context_for]] | 맥락 구간 고르기 (전부 또는 관련 챕터) |

---

## 2. 함수

#### ChatService.history 대화 턴 목록

**시그니처** `async def history(video_id: int) -> list[ChatTurn]`

근거: [[VA-SEQ-001#SEQ-8]] 17~22번 · [[VA-SEQ-001#SEQ-10]] 4~6번 · [[VA-API-001#GET/api/videos/{id}/chat]] · [[VA-UC-001#UC-H5]] 3번 · [[VA-UC-001#UC-H7]] 2b

**처리** `DB: chat_turns where video_id order by asked_at, id` · `→ [ChatTurn(id, question, answer, cited_secs, asked_at) …]`. 없으면 `[]`. 영상이 없는지는 라우터가 `VideoService.get`으로 먼저 본다([[VA-DOM-002]] 3.1 표)

**테스트 관점** 시간순 · 같은 초에 둘이면 `id`순 · 결과 없는 영상 → `[]`(예외 아님)

---

#### ChatService.ask 질문 → 답 저장

**시그니처** `async def ask(video: Video, question: str) -> ChatTurn`

근거: [[VA-SEQ-001#SEQ-9]] · [[VA-API-001#POST/api/videos/{id}/chat]] 1~5번 · [[VA-UC-001#UC-H4]] 1~4번, 확장 1a · 1b · 2a · 3a · 3b · [[VA-PRD-001#R6]] · [[VA-DOM-003#chat_turns]]

**입력** `video` — 라우터가 `VideoService.get`으로 받아 넘긴 DTO. `question` — 사용자가 친 문장 또는 추천 질문 문장(같은 요청)

**처리** — 순서가 규칙이다
1. if `video.status != analyzed` → `! result-not-ready {video_status: video.status}`
2. `await SettingsService.require_key()` · `! key-missing` · `! key-invalid` — 마지막 키 확인이 연결 실패(`network`)였으면 여기서 한 번 다시 확인한다([[VA-MS-005#SettingsService.require_key]]). 또 닿지 못하면 `key-invalid`(`reason_kind = network`)이고, 화면은 그 질문 자리에 답변 실패로 '연결을 확인하지 못했어요'를 보인다([[VA-UI-002#UI-4]] 10.2 규칙). 질문은 저장하지 않는다
3. `q = question.strip()` · if 비어 있음 → `! validation {errors: [{field: question, message: 비어 있음}]}` · 2,000자를 넘으면 자른다
4. `context = context_for(video, q)` — 구간 목록
5. `history = DB: chat_turns where video_id order by asked_at desc limit config.CHAT_HISTORY_TURNS`를 시간순으로 뒤집는다([[VA-UC-001#UC-H4]] 1b — 대명사가 풀린다)
6. `model = SettingsService.current_models().text.id`
7. `draft = AnswererPort.answer(q, context, history, model)` — `config.CHAT_TIMEOUT_SEC` 안에 · 포트가 올린 `llm-unavailable`(OpenAI 호출 · 출력 형식 실패, 이유는 [[VA-MS-007#openai.reason_of]])은 그대로 · 시간 초과면 `! llm-unavailable {reason: '응답 시간 초과'}`([[VA-UI-002#UI-4]] 9.8 보드 예) — 어느 쪽이든 **저장하지 않는다**([[VA-UI-002#UI-4]] 규칙: 실패한 질문은 기록에 남지 않는다). 그 밖의 예외는 코드 실수라 `internal`
8. `cited = [s for s in draft.cited_secs if 0 ≤ s ≤ video.duration_sec]` 오름차순 · 중복 제거 — 범위 밖 시각은 버린다(인사이트와 달리 보정하지 않는다. 답의 근거는 모델이 실제로 본 구간에서만 나와야 한다)
9. **트랜잭션**: `row = DB: chat_turns insert(video_id, question=q, answer=draft.answer, cited_secs=cited, model, asked_at=now)`
10. `→ ChatTurn(row)`

**출력** `ChatTurn`(201). `cited_secs`가 `[]`이면 화면이 '영상에 없는 내용'을 붙인다

**예외**

| 조건 | 에러 |
|---|---|
| 결과 없음(작업 없음 · 진행 중 · 실패) | `result-not-ready` |
| 키 없음 · 확인 실패(연결 실패였으면 다시 확인한 뒤에도 실패) | `key-missing` · `key-invalid` |
| 빈 질문 | `validation` |
| 모델 호출 실패 · 시간 초과 | `llm-unavailable` |

**호출하는 것** `SettingsService.require_key` · `SettingsService.current_models` · [[#ChatService.context_for]] · `AnswererPort.answer`

**테스트 관점** 가짜 포트로: 답 성공 → 행 하나, `count_by_videos` +1 · 포트가 `llm-unavailable`을 올리면 그대로이고 행이 없다 · 포트가 시간 제한을 넘으면 `llm-unavailable`('응답 시간 초과')이고 행이 없다 · 빈 질문 · 공백만 → `validation` · `in_progress` 영상 → `result-not-ready`, 포트 호출 없음 · 12턴 있을 때 포트가 받는 `history`는 최근 10개 시간순 · `cited_secs`에 길이 밖 값이 오면 버려진다 · 근거 없음 → `cited_secs=[]` 저장 · 키 없음 → 포트 호출 없음 · 마지막 키 확인이 `network`이고 다시 확인도 실패 → `key-invalid`(`network`), 포트 호출 없음, 행 없음 · 다시 확인이 통과 → 답을 받아 저장한다 · 저장된 행의 `model`이 모델 id다

---

#### ChatService.count_by_videos 영상별 턴 수

**시그니처** `async def count_by_videos(video_ids: list[int]) -> dict[int, int]`

근거: [[VA-SEQ-001#SEQ-7]] · [[VA-API-001]] 4장 `Video.chat_turn_count` · [[VA-UC-001#UC-H5]] 1번

**처리** `DB: chat_turns where video_id in … group by video_id → count` 한 쿼리 · `→ {video_id: n}`. 턴이 없는 영상은 키가 없다(부르는 쪽이 `.get(id, 0)`)

**테스트 관점** 영상 50개에 쿼리 하나 · 빈 목록 → `{}` · 턴 0개 영상은 키 없음

---

#### ChatService.context_for 맥락 구간 고르기

**시그니처** `async def context_for(video: Video, question: str) -> list[Segment]`

근거: [[VA-SEQ-001#SEQ-9]] 15~21번 · [[VA-UC-001#UC-H4]] 1b, 2번, 3b · [[VA-DOM-002]] 4.4 규칙 · [[VA-INFRA-001]] 3절 AI 전략(벡터 DB 없음 — 두 글자 조각 BM25, 사용자 결정 2026-10-01)

**처리**
1. `segments = AnalysisService.segments_of(video.id)` · `tokens = `[[VA-MS-006#tokens.estimate]]`(줄 텍스트)` — 줄 앞 시각 표기까지 어림한다(카드 C)
2. if `tokens ≤ config.CHAT_TOKEN_LIMIT` → `→ segments` (전부)
3. `chapters = AnalysisService.chapters_of(video.id)`(시각순) · 챕터가 없으면 `→ segments`
4. **두 글자 조각** — 글을 낱말로 나눈다(2자 이상 · 한글 어절 · 영문 · 숫자 모두, 영문은 소문자로. 한 글자 낱말은 버린다 — 영문 'a' · 숫자 '2'는 거의 모든 글에 있다) · 낱말마다 이웃한 두 글자를 모두 뽑는다('비용은' → '비용' · '용은'). 조사 · 어미가 붙어도 앞 조각이 같아 맞는다 — 형태소 분석기 없이
5. 챕터마다 글 = 제목 · 요점의 조각 × `config.CHAT_SUMMARY_WEIGHT` + 그 챕터 범위(6번) 구간들의 조각. 질문의 조각으로 BM25 점수를 낸다(`k1 = config.CHAT_BM25_K1`, `b = config.CHAT_BM25_B`): 조각 t마다 `idf = ln(1 + (N − df + 0.5) / (df + 0.5))`(N 챕터 수, df t가 든 챕터 수) × `tf · (k1 + 1) / (tf + k1 · (1 − b + b · 글 길이 / 평균 글 길이))`를 질문에 있는 조각(겹치면 한 번)마다 더한다. 모든 챕터에 흔한 조각(예: 자석 강의의 '자석')은 idf가 작아 점수를 거의 올리지 않는다
6. 챕터 범위 = `[chapter.start_sec, 다음 챕터.start_sec)`(마지막은 영상 끝). 첫 챕터는 0초에서 시작하므로([[VA-MS-003#AnalysisService.generate_chapters]] 3번) 스크립트 처음도 어느 챕터 범위에 든다
7. 고르는 순서 — 점수 > 0인 챕터를 점수 내림차순(같으면 시각순)으로 앞 `config.CHAT_CHAPTERS`개를 고르되, **직전 턴의 근거 챕터**(DB: 가장 최근 턴 하나의 `cited_secs`마다 그 시각이 든 챕터, 이미 고른 것은 빼고)를 점수 1위 바로 뒤에 넣는다 — 이어지는 질문('그 실험은 누가 했어요?', [[VA-UC-001#UC-H4]] 1b)은 낱말로는 못 찾는다. 앞 질문의 글을 질문에 붙이는 방법은 화제가 바뀐 질문을 해쳐 쓰지 않는다(실측, 3장) · 점수 > 0인 챕터도 직전 턴도 없으면 앞 `config.CHAT_CHAPTERS`개 챕터
8. 고른 챕터 범위의 구간을 시각순으로 모은다 · 합이 `config.CHAT_TOKEN_LIMIT`를 넘으면 고른 순서의 **뒤에서부터** 뺀다(점수 3위 → 2위 → 근거 챕터 — 1위는 남는다). 챕터 하나만 남으면 상한을 넘어도 그대로 보낸다 — 챕터 안을 자르면 질문과 맞는 구간을 잃을 수 있고, 상한은 비용 · 속도를 위한 값이지 모델이 받을 수 있는 양의 한계가 아니다
9. `→ 구간 목록` (시각순. 챕터 사이가 비어 있어도 그대로 — 모델에게는 `[시각] 문장` 줄이라 빈틈이 보인다)

**출력** `list[Segment]`

**호출하는 것** `AnalysisService.segments_of` · `AnalysisService.chapters_of` · DB: `chat_turns`(가장 최근 하나)

**테스트 관점** 50분 영상 → 구간 전부 · 3시간 영상 + 질문 'RAG 비용' → 비용을 다룬 챕터가 고른 것에 들고 구간은 고른 챕터 범위만, 토큰 상한 이하 · 조사가 붙은 질문('비용은')도 그 챕터와 맞는다(두 글자 조각) · 제목 · 요점에 없고 그 챕터의 스크립트에만 있는 낱말('하이퍼루프')로 물어도 그 챕터를 고른다 · 모든 챕터에 든 조각만으로 된 질문은 그 조각 때문에 순서가 바뀌지 않는다(idf) · 이어지는 질문('그 실험은 누가 했어요?')은 직전 턴 근거 시각이 든 챕터가 들어간다 · 아무 조각도 안 맞고 앞 턴도 없으면 앞 3챕터 · 상한을 넘으면 점수 3위 → 2위 → 근거 챕터 순으로 빠지고 1위는 남는다 · 챕터 하나만 남으면 상한을 넘어도 그 챕터의 구간 전부 · 고른 구간이 시각순 · 한 글자 낱말('A/B 테스트'의 'a' · 'b')은 조각을 만들지 않는다

---

## 3. 미결사항

- [x] 관련 챕터 고르기를 낱말 일치로 시작한다. 품질이 모자라면 간단 임베딩(`pgvector`, [[VA-DOM-003]] 5장)으로 — 사용자가 결과를 보고 결정([[VA-INFRA-001]] 9절) — 결정: 두 글자 조각 BM25(2장 `context_for`, 사용자 결정 2026-10-01). 실측(2:30:30 강의에 정답 챕터를 붙인 29문항 — 상위 3챕터에 정답이 든 수): 처음 방식(낱말 부분 일치, 제목 · 요점만) 13 · 임베딩(text-embedding-3-small, 챕터 스크립트를 2,500자 창으로) 22 · 섞기 24 · 두 글자 조각 BM25(제목 · 요점 × 3 + 챕터 스크립트) 27. 이어 묻기 셋은 직전 턴 근거 챕터로 3/3, 앞 질문 글을 붙이는 방법은 새 화제 26문항이 24 → 21로 나빠졌다. 질문 묶음은 스크립트를 보고 만들어 낱말 방식에 유리할 수 있다 — 카드 뒤 진짜 스택에서 바꿔 말한 질문으로 다시 본다
- [x] 한글 낱말 나누기 — 조사 · 어미를 떼지 않으면 '비용은'과 '비용'이 안 맞는다. 부분 일치로 넘기지만 형태소 분석기를 붙일지 — 결정: 붙이지 않는다. 두 글자 조각이 조사 · 어미를 흡수한다(2장 4번)
- [ ] 답 시간 제한 20초 — 목표 10초([[VA-PRD-001#N1]])보다 길게 잡았다. 긴 맥락에서 실제 시간을 재고 조정
- [x] 키 확인이 네트워크로 실패했을 때 질문 입력의 안내 문구 — 결정: 입력 영역의 안내(10.2)를 '연결을 확인하지 못했어요 — …'로 가르고 링크는 없다. 입력칸 · 보내기 · 추천 질문은 막지 않고, 보내면 `ask` 2번에서 키를 다시 확인한다(사용자 결정 2026-09-21, [[VA-UI-002#UI-4]] · [[VA-MS-005#SettingsService.require_key]])
