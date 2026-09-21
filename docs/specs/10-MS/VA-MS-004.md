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

**설정값(첫 값)**

| 이름 | 첫 값 | 이유 |
|---|---|---|
| `config.CHAT_HISTORY_TURNS` | 10 | 맥락에 넣는 앞선 턴 수([[VA-DOM-002]] 4.4 규칙) |
| `config.CHAT_TOKEN_LIMIT` | 30000 | 맥락 구간의 토큰 상한. 넘으면 챕터로 고른다. 답 10초 목표([[VA-PRD-001#N1]])에 맞춘 값 |
| `config.CHAT_CHAPTERS` | 3 | 관련 챕터로 고르는 수 |
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
2. `SettingsService.require_key()` · `! key-missing` · `! key-invalid`
3. `q = question.strip()` · if 비어 있음 → `! validation {errors: [{field: question, message: 비어 있음}]}` · 2,000자를 넘으면 자른다
4. `context = context_for(video, q)` — 구간 목록
5. `history = DB: chat_turns where video_id order by asked_at desc limit config.CHAT_HISTORY_TURNS`를 시간순으로 뒤집는다([[VA-UC-001#UC-H4]] 1b — 대명사가 풀린다)
6. `model = SettingsService.current_models().text`
7. `draft = AnswererPort.answer(q, context, history, model)` — `config.CHAT_TIMEOUT_SEC` 안에 · if 예외 · 시간 초과 → `! llm-unavailable {reason}` — **저장하지 않는다**([[VA-UI-002#UI-4]] 규칙: 실패한 질문은 기록에 남지 않는다)
8. `cited = [s for s in draft.cited_secs if 0 ≤ s ≤ video.duration_sec]` 오름차순 · 중복 제거 — 범위 밖 시각은 버린다(인사이트와 달리 보정하지 않는다. 답의 근거는 모델이 실제로 본 구간에서만 나와야 한다)
9. **트랜잭션**: `row = DB: chat_turns insert(video_id, question=q, answer=draft.answer, cited_secs=cited, model, asked_at=now)`
10. `→ ChatTurn(row)`

**출력** `ChatTurn`(201). `cited_secs`가 `[]`이면 화면이 '영상에 없는 내용'을 붙인다

**예외**

| 조건 | 에러 |
|---|---|
| 결과 없음(작업 없음 · 진행 중 · 실패) | `result-not-ready` |
| 키 없음 · 확인 실패 | `key-missing` · `key-invalid` |
| 빈 질문 | `validation` |
| 모델 호출 실패 · 시간 초과 | `llm-unavailable` |

**호출하는 것** `SettingsService.require_key` · `SettingsService.current_models` · [[#ChatService.context_for]] · `AnswererPort.answer`

**테스트 관점** 가짜 포트로: 답 성공 → 행 하나, `count_by_videos` +1 · 포트 예외 → `llm-unavailable`이고 행이 없다 · 빈 질문 · 공백만 → `validation` · `in_progress` 영상 → `result-not-ready`, 포트 호출 없음 · 12턴 있을 때 포트가 받는 `history`는 최근 10개 시간순 · `cited_secs`에 길이 밖 값이 오면 버려진다 · 근거 없음 → `cited_secs=[]` 저장 · 키 없음 → 포트 호출 없음

---

#### ChatService.count_by_videos 영상별 턴 수

**시그니처** `async def count_by_videos(video_ids: list[int]) -> dict[int, int]`

근거: [[VA-SEQ-001#SEQ-7]] · [[VA-API-001]] 4장 `Video.chat_turn_count` · [[VA-UC-001#UC-H5]] 1번

**처리** `DB: chat_turns where video_id in … group by video_id → count` 한 쿼리 · `→ {video_id: n}`. 턴이 없는 영상은 키가 없다(부르는 쪽이 `.get(id, 0)`)

**테스트 관점** 영상 50개에 쿼리 하나 · 빈 목록 → `{}` · 턴 0개 영상은 키 없음

---

#### ChatService.context_for 맥락 구간 고르기

**시그니처** `async def context_for(video: Video, question: str) -> list[Segment]`

근거: [[VA-SEQ-001#SEQ-9]] 17~22번 · [[VA-UC-001#UC-H4]] 2번, 3b · [[VA-DOM-002]] 4.4 규칙 · [[VA-INFRA-001]] 3절(벡터 DB 없음 — 챕터 필터)

**처리**
1. `segments = AnalysisService.segments_of(video.id)` · `tokens = 어림(글자 수 ÷ 2)`
2. if `tokens ≤ config.CHAT_TOKEN_LIMIT` → `→ segments` (전부)
3. `chapters = AnalysisService.chapters_of(video.id)` · 질문을 낱말로 나눈다 — 한글은 2자 이상 어절, 영문 · 숫자는 소문자 단어, 조사 어미는 떼지 않는다(첫 버전)
4. 챕터마다 점수 = `title + bullets`에 나오는 질문 낱말 수(부분 일치 포함) · 점수 > 0인 챕터를 점수 내림차순, 같으면 시각순으로 앞 `config.CHAT_CHAPTERS`개
5. if 점수 > 0인 챕터가 없음 → 최근 턴들의 `cited_secs`가 속한 챕터(이어지는 질문, [[VA-UC-001#UC-H4]] 1b) · 그것도 없으면 앞 `config.CHAT_CHAPTERS`개 챕터
6. 고른 챕터마다 범위 = `[chapter.start_sec, 다음 챕터.start_sec)`(마지막은 영상 끝) · 그 범위의 구간을 시각순으로 모은다 · 합이 `config.CHAT_TOKEN_LIMIT`를 넘으면 점수 낮은 챕터부터 뺀다
7. `→ 구간 목록` (시각순. 챕터 사이가 비어 있어도 그대로 — 모델에게는 `[시각] 문장` 줄이라 빈틈이 보인다)

**출력** `list[Segment]`

**호출하는 것** `AnalysisService.segments_of` · `AnalysisService.chapters_of`

**테스트 관점** 50분 영상 → 구간 전부 · 3시간 영상 + 질문 'RAG 비용' → 제목에 '비용'이 든 챕터의 구간만, 토큰 상한 이하 · 아무 낱말도 안 맞으면 앞 3챕터 · 이어지는 질문('그거 성능은?')은 직전 턴의 근거 챕터 · 고른 구간이 시각순

---

## 3. 미결사항

- [ ] 관련 챕터 고르기를 낱말 일치로 시작한다. 품질이 모자라면 간단 임베딩(`pgvector`, [[VA-DOM-003]] 5장)으로 — 사용자가 결과를 보고 결정([[VA-INFRA-001]] 9절)
- [ ] 한글 낱말 나누기 — 조사 · 어미를 떼지 않으면 '비용은'과 '비용'이 안 맞는다. 부분 일치로 넘기지만 형태소 분석기를 붙일지
- [ ] 답 시간 제한 20초 — 목표 10초([[VA-PRD-001#N1]])보다 길게 잡았다. 긴 맥락에서 실제 시간을 재고 조정
- [ ] 키 확인이 네트워크로 실패했을 때 질문 입력의 안내 문구 — [[VA-SEQ-001]] 3장(되먹일 것 #6)과 같은 항목. 사용자 확인
