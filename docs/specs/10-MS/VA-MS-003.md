---
doc_id: VA-MS-003
type: MS
title: MINISPEC — AnalysisService · export
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-DOM-003, VA-UC-001, VA-PRD-001]
---

# MINISPEC — AnalysisService · export

## 0. 이 문서가 다루는 것

`domains/analysis/service.py`의 함수 11개와 `domains/analysis/export.py`의 순수 함수 3개. 클래스 명세 [[VA-DOM-002#AnalysisService]]의 시그니처를 함수 내부까지 내린 것. 4.3 절이 두 파일이라 이 문서도 두 모듈이다. 포트 · 어댑터(`summarizer_openai`)는 4.6 · 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10. 내부 타입(`CaptionLine` `SummaryDraft` `ChapterDraft`)은 [[VA-DOM-002]] 2.6, 응답 형태(`Result` `Transcript` `Segment` `Summary` `Insight` `Part` `Chapter` `SuggestedQuestion` `ExportPreview` `ExportResult` `ChatTurn`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `DB:` 테이블 접근(`crud`를 거친다), `FS:` 파일 접근.

**이 묶음이 아는 것** — `transcripts` · `segments` · `summaries` · `insights` · `parts` · `chapters` · `suggested_questions` 일곱 테이블, `data/export/`. 영상은 `Video` DTO로, 대화 턴은 `list[ChatTurn]`으로 인자로 받는다. 작업 묶음을 모른다 — 파이프라인이 부르는 순서는 파이프라인의 것이다([[VA-DOM-002]] 3.2). 세션은 호출자(라우터 또는 파이프라인의 짧은 세션)의 것.

**설정값(첫 값)**

| 이름 | 첫 값 | 이유 |
|---|---|---|
| `config.TEXT_WINDOW_SEC` | 1800 | 스크립트가 길 때 30분 구간으로 나눈다. 3시간이면 6구간 |
| `config.TEXT_TOKEN_LIMIT` | 40000 | 한 번에 보내는 스크립트 토큰 상한. 분당 200토큰이면 200분이라 3시간 상한 안의 영상은 대부분 한 번에 간다 — 말이 아주 빠르거나 글자가 많은 스크립트만 구간 처리로 간다 |
| `config.CHAPTER_MINUTES` | 6 | 챕터 하나가 맡는 분. 목표 챕터 수 = 길이(분) ÷ 6 |
| `config.PART_THRESHOLD_SEC` | 3600 | 이보다 길면 파트를 만든다([[VA-PRD-001#R5]]) |
| `config.EXPORT_DIR` | `data/export` | 파일로 저장 위치([[VA-UI-001]] 7장 14) |

**요약 · 챕터 · 추천 질문의 실행 순서는 파이프라인이 정한다** — 핵심 요약 → 챕터 → 추천 질문([[VA-DOM-002]] 5장 10). 세 함수는 서로를 부르지 않고 각자 `segments`를 읽는다.

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#AnalysisService.save_transcript]] | 스크립트 + 구간 교체 저장 |
| [[#AnalysisService.generate_summary]] | 한 줄 요약 + 인사이트 (긴 스크립트는 중간 요약) |
| [[#AnalysisService.generate_chapters]] | 챕터 (60분 넘으면 파트) |
| [[#AnalysisService.generate_questions]] | 추천 질문 3개 |
| [[#AnalysisService.result_of]] | 결과 화면 응답 전부 |
| [[#AnalysisService.segments_of]] | 구간 목록 (대화용) |
| [[#AnalysisService.chapters_of]] | 챕터 목록 (대화용) |
| [[#AnalysisService.export_markdown]] | 마크다운 본문 + 파일 이름 |
| [[#AnalysisService.export_to_file]] | `data/export/`에 쓰기 |
| [[#AnalysisService.clamp_secs]] | 시각을 스크립트 범위로 보정 |
| [[#AnalysisService.filename_for]] | 제목 → 파일 이름 |
| [[#export.build]] | 결과 → 마크다운 문자열 |
| [[#export.timecode]] | 초 → `mm:ss` 또는 `h:mm:ss` |
| [[#export.link]] | 시각 → YouTube 링크 또는 텍스트 |

---

## 2. 함수

#### AnalysisService.save_transcript 스크립트 + 구간 교체 저장

**시그니처** `async def save_transcript(video_id: int, source: TranscriptSource, language: str, model: str | None, lines: list[CaptionLine]) -> None`

근거: [[VA-SEQ-001#SEQ-3]] 5~7번 · [[VA-SEQ-001#SEQ-4]] 32~35번 · [[VA-UC-001#UC-S2]] 2번 · [[VA-UC-001#UC-S3]] 4~5번 · [[VA-DOM-003#transcripts]] · [[VA-DOM-003#segments]]

**입력** `lines` — 시각순이 아닐 수 있다(조각 병렬). `model`은 `stt`일 때만

**처리** — **트랜잭션**
1. `lines`를 `start_sec` 오름차순 정렬 · 빈 `text`는 뺀다 · `end_sec < start_sec`이면 `end_sec = start_sec`
2. `DB: delete transcripts where video_id` (cascade로 `segments`도) — 교체. 재시도가 같은 단계를 다시 돌려도 중복이 없다
3. `DB: transcripts insert(video_id, source, language, model)` · `DB: segments insert ×N (transcript_id, seq=1부터, start_sec, end_sec, text)` — 한 번에(bulk)
4. `→ None`

**출력** 없음

**예외** 던지지 않는다. `lines`가 비어 있으면 `ValueError` — 파이프라인이 `unknown`으로 접는다(자막이 있다고 했는데 줄이 없는 경우)

**호출하는 것** 없음

**테스트 관점** 두 번 저장하면 행이 한 벌 · `seq`가 시각순 1~N · 3,000줄이 쿼리 하나로 들어간다 · 자막 저장은 `model=None` · 빈 목록 → `ValueError`

---

#### AnalysisService.generate_summary 한 줄 요약 + 인사이트

**시그니처** `async def generate_summary(video: Video) -> None`

근거: [[VA-SEQ-001#SEQ-3]] 9~18번 · [[VA-UC-001#UC-S4]] 3번, 1a · 5a · [[VA-PRD-001#R4]] · [[VA-DOM-003#summaries]] · [[VA-DOM-003#insights]]

**입력** `video` — `duration_sec`와 `id`를 쓴다

**처리**
1. `segments = segments_of(video.id)` · `model = SettingsService.current_models().text.id`
2. `n_max = 10 if video.duration_sec > config.PART_THRESHOLD_SEC else 8` · `n_min = 5`
3. if `토큰 수(segments) ≤ config.TEXT_TOKEN_LIMIT` → `draft = SummarizerPort.summary(segments, video.duration_sec, model)`
   else → 구간마다 `SummarizerPort.summary(구간의 segments, 구간 길이, model)`로 중간 요약을 얻고, 그 한 줄 요약(구간 시작 시각의 줄) · 인사이트(첫 출처 시각의 줄)를 `[시각] 문장` 줄들의 가짜 구간 목록으로 시각순으로 만들어 `SummarizerPort.summary(그 목록, video.duration_sec, model)` — 최종 요약. 구간은 `config.TEXT_WINDOW_SEC`씩([[VA-UC-001#UC-S4]] 1a2를 챕터 대신 중간 요약으로)
4. `insights = draft.insights[:n_max]` · if `len < n_min` → 그대로 둔다(프롬프트가 5~8을 요구하고 모자라면 있는 만큼)
5. 인사이트마다 `source_secs = clamp_secs(source_secs, video.duration_sec, segments)` · 빈 목록이 되면 그 인사이트를 뺀다(출처 없는 인사이트는 화면에 시각 칩이 없어 규칙 위반)
6. **트랜잭션**: `DB: delete summaries where video_id`(cascade로 insights) · `DB: summaries insert(video_id, one_liner, model)` · `DB: insights insert ×N (summary_id, seq=1부터, text, source_secs)`
7. `→ None`

**출력** 없음

**예외** 포트 예외는 그대로 올린다 — 파이프라인이 `fail`로 접는다

**호출하는 것** [[#AnalysisService.segments_of]] · [[#AnalysisService.clamp_secs]] · `SettingsService.current_models` · `SummarizerPort.summary`

**테스트 관점** 가짜 포트로: 50분 → 포트 호출 1회, 인사이트 ≤ 8 · 150분이고 토큰이 상한을 넘는 스크립트 → 구간 5 + 최종 1 = 6회, 인사이트 ≤ 10 · 150분이라도 상한 안이면 1회 · 출처 시각이 길이를 넘는 인사이트 → 가장 가까운 구간 시각으로 · 출처가 전부 밖이라 비면 그 인사이트가 빠진다 · 두 번 돌리면 행이 한 벌 · 언어는 프롬프트가 한국어로(어댑터 테스트)

---

#### AnalysisService.generate_chapters 챕터 (60분 넘으면 파트)

**시그니처** `async def generate_chapters(video: Video) -> None`

근거: [[VA-SEQ-001#SEQ-3]] 19~26번 · [[VA-UC-001#UC-S4]] 2번, 1a · 2a · 5a · [[VA-PRD-001#R5]] · [[VA-DOM-003#parts]] · [[VA-DOM-003#chapters]]

**처리**
1. `segments = segments_of(video.id)` · `model = …text` · `target = max(3, round(video.duration_sec / 60 / config.CHAPTER_MINUTES))` — 목표 챕터 수
2. if `토큰 수 ≤ config.TEXT_TOKEN_LIMIT` → `draft = SummarizerPort.chapters(segments, video.duration_sec, model)`
   else → 구간(`config.TEXT_WINDOW_SEC`)마다 `SummarizerPort.chapters(구간 segments, 구간 길이, model)` · 챕터 목록을 이어 붙인다(시각은 절대 시각으로 이미 온다) · 파트는 만들지 않는다 — 5번에서 만든다
3. `chapters = draft.chapters`를 `start_sec` 오름차순 · `start_sec = clamp_secs([start_sec], duration, segments)[0]` · 같은 시각이 둘이면 뒤 것을 뺀다 · 첫 챕터의 `start_sec`가 0이 아니면 0으로 당긴다(스크립트 처음이 어느 챕터에도 안 들어가는 것을 막는다)
4. `bullets`는 2~3줄로 자른다(4개 이상이면 앞 3개)
5. if `video.duration_sec > config.PART_THRESHOLD_SEC` → 파트 — if `draft.parts`가 있고 `len ≥ 2` → 그대로 · else → 챕터를 60분 단위로 묶어 파트를 만들고 제목은 `SummarizerPort.summary`가 아니라 첫 챕터 제목을 쓴다(미결 3) · 파트 시작 시각도 `clamp_secs`로 보정해 오름차순, 같은 시각은 하나로, **첫 파트는 0초로 당긴다**(첫 챕터가 0초라 어느 파트에도 안 드는 것을 막는다) · 챕터마다 `part_seq` = 시작 시각이 속한 파트(모델이 준 번호가 아니라 시각으로 정한다) · 챕터가 하나도 없는 파트는 빼고 번호를 다시 매긴다
   else → 파트 없음, `part_seq=None`
6. **트랜잭션**: `DB: delete parts where video_id` · `DB: delete chapters where video_id` · `DB: parts insert ×M (video_id, seq, title, start_sec)` · `DB: chapters insert ×N (video_id, part_id, seq=1부터 영상 전체 순번, start_sec, title, bullets)`
7. `→ None`

**출력** 없음

**호출하는 것** [[#AnalysisService.segments_of]] · [[#AnalysisService.clamp_secs]] · `SettingsService.current_models` · `SummarizerPort.chapters`

**테스트 관점** 50분 → 파트 0, 챕터 8 안팎, 첫 챕터 0초 · 150분 → 파트 ≥ 2, 챕터마다 `part_id`, 파트 시작 시각이 오름차순 · 모델이 첫 파트를 5분에 두어도 0초로 당겨 첫 챕터가 첫 파트에 든다 · 챕터 없는 파트는 빠진다 · 모델 파트가 하나뿐이면 60분 묶음 · 같은 시각 챕터 둘 → 하나 · `bullets` 4개 → 3개 · 두 번 돌리면 행이 한 벌

---

#### AnalysisService.generate_questions 추천 질문 3개

**시그니처** `async def generate_questions(video: Video) -> None`

근거: [[VA-SEQ-001#SEQ-3]] 27~32번 · [[VA-UC-001#UC-S4]] 4번 · [[VA-PRD-001#R9]] · [[VA-DOM-003#suggested_questions]]

**처리**
1. `segments = segments_of(video.id)` · if 토큰 수가 상한을 넘으면 앞 · 중간 · 끝에서 `config.TEXT_TOKEN_LIMIT / 3`씩 뽑아 보낸다(질문은 전체를 다 볼 필요가 없다)
2. `qs = SummarizerPort.questions(segments, model)` · 앞 3개 · 빈 문장 · 중복 제거 · 3개보다 적으면 있는 만큼
3. **트랜잭션**: `DB: delete suggested_questions where video_id` · `DB: insert ×3 (video_id, seq, text)`
4. `→ None`

**호출하는 것** [[#AnalysisService.segments_of]] · `SummarizerPort.questions`

**테스트 관점** 정확히 3행 · 포트가 5개 주면 3개만 · 두 번 돌리면 3행 그대로

---

#### AnalysisService.result_of 결과 화면 응답

**시그니처** `async def result_of(video: Video) -> Result`

근거: [[VA-SEQ-001#SEQ-8]] · [[VA-API-001#GET/api/videos/{id}/result]]와 그 요소 ↔ 필드 표 · [[VA-UC-001#UC-H3]] · [[VA-UC-001#UC-H5]] 3번

**입력** `video` — 라우터가 `VideoService.get`으로 받아 넘긴 DTO(`status` · `chat_turn_count` 포함)

**처리**
1. if `video.status != analyzed` → `! result-not-ready {video_status: video.status}`
2. `t = DB: transcripts where video_id` · if 없음 → `! result-not-ready`(상태는 `analyzed`인데 스크립트가 없는 것은 있을 수 없지만 방어) · `segs = DB: segments where transcript_id order by seq`
3. `s = DB: summaries where video_id` · `ins = DB: insights where summary_id order by seq`
4. `parts = DB: parts where video_id order by seq` · `chs = DB: chapters where video_id order by seq` · `qs = DB: suggested_questions where video_id order by seq`
5. 파트마다 `end_sec` = 다음 파트의 `start_sec`, 마지막은 `video.duration_sec` · `chapter_count` = 그 파트의 챕터 수. 챕터의 `part_seq` = `part_id`로 찾은 파트의 `seq`(없으면 `None`)
6. `→ Result(video, transcript=Transcript(t.source, t.language, t.model, segments=[Segment(seq, start_sec, end_sec, text) …]), summary=Summary(s.one_liner, s.model, insights=[Insight(seq, text, source_secs) …]), parts, chapters, suggested_questions=[SuggestedQuestion(seq, text) …], models=Models(stt=t.model, text=s.model), analyzed_at=video.analyzed_at)`

**출력** `Result`. 구간 수천 개를 한 번에([[VA-API-001]] 5장 3)

**예외** `result-not-ready`

**호출하는 것** 없음

**테스트 관점** 상태 `in_progress` → `result-not-ready`에 `video_status=in_progress` · 파트 둘이면 첫 파트 `end_sec`가 둘째 `start_sec` · 마지막 파트 `end_sec`가 영상 길이 · `chapter_count` 합이 챕터 수 · 자막 결과는 `models.stt=None` · 쿼리 수가 6을 넘지 않는다

---

#### AnalysisService.segments_of 구간 목록

**시그니처** `async def segments_of(video_id: int) -> list[Segment]`

**처리** `DB: segments join transcripts where video_id order by seq` · `→ [Segment(seq, start_sec, end_sec, text) …]`. 스크립트가 없으면 `[]`

**테스트 관점** 시각순 · 없으면 빈 목록(예외 아님)

---

#### AnalysisService.chapters_of 챕터 목록

**시그니처** `async def chapters_of(video_id: int) -> list[Chapter]`

**처리** `DB: chapters where video_id order by seq` · `→ [Chapter(seq, part_seq, start_sec, title, bullets) …]`. `part_seq`는 `parts`를 같이 읽어 채운다

**테스트 관점** 파트 없는 영상 → `part_seq=None` 전부

---

#### AnalysisService.export_markdown 마크다운 본문

**시그니처** `async def export_markdown(video: Video, with_chat: bool, turns: list[ChatTurn]) -> ExportPreview`

근거: [[VA-SEQ-001#SEQ-10]] 2~12번 · [[VA-API-001#GET/api/videos/{id}/export]] · [[VA-UC-001#UC-H7]] 1~2번, 2a · 2b · [[VA-PRD-001#R10]]

**처리**
1. `result = result_of(video)` — `result-not-ready`는 여기서 난다
2. `md = export.build(result, turns if with_chat else None)`
3. `name = filename_for(video)` · `→ ExportPreview(filename=name, path=f"{config.EXPORT_DIR}/{name}.md", markdown=md)`

**출력** `ExportPreview`. `markdown`은 전체 — 화면이 앞부분만 보이고 클립보드는 전체를 쓴다

**예외** `result-not-ready`

**호출하는 것** [[#AnalysisService.result_of]] · [[#export.build]] · [[#AnalysisService.filename_for]]

**테스트 관점** `with_chat=false`면 `## 질문 기록` 절이 없다 · `true`이고 턴 0개면 절 제목만 있고 「질문 기록이 없습니다」 한 줄 · `path`가 `data/export/…md`

---

#### AnalysisService.export_to_file 파일로 저장

**시그니처** `async def export_to_file(video: Video, with_chat: bool, turns: list[ChatTurn]) -> ExportResult`

근거: [[VA-SEQ-001#SEQ-10]] 13~24번 · [[VA-API-001#POST/api/videos/{id}/export]] · [[VA-UC-001#UC-H7]] 3번 · [[VA-UI-001]] 7장 14

**처리**
1. `pre = export_markdown(video, with_chat, turns)` — 같은 마크다운을 다시 만든다. 화면이 보낸 본문을 쓰지 않는다
2. `FS: mkdir(config.EXPORT_DIR)` · `FS: pre.path에 UTF-8로 쓰기(덮어쓰기, 임시 파일에 쓴 뒤 rename)` · if `OSError` → `! export-failed {path, reason: 오류 문구 한 줄}`
3. `→ ExportResult(filename=pre.filename, path=pre.path, bytes=쓴 바이트 수)`

**출력** `ExportResult`(201)

**예외** `result-not-ready` · `export-failed`

**호출하는 것** [[#AnalysisService.export_markdown]]

**테스트 관점** 파일이 생기고 내용이 `export_markdown`과 같다 · 두 번 저장하면 덮어쓴다 · 폴더가 없으면 만든다 · 쓸 수 없는 폴더 → `export-failed`에 `path`

---

#### AnalysisService.clamp_secs 시각 보정

**시그니처** `def clamp_secs(secs: list[float], duration_sec: int, segments: list[Segment]) -> list[float]`

근거: [[VA-UC-001#UC-S4]] 5a · [[VA-DOM-001]] 5장 1(출처 시각은 초 단위 값)

**처리** 시각마다 — if `0 ≤ sec ≤ duration_sec` → 그대로 · else → `segments` 중 `start_sec`가 `sec`에 가장 가까운 것의 `start_sec`(길이를 넘으면 마지막 구간의 시작) · 결과에서 중복을 없애고 오름차순 · `→ list`. `segments`가 비어 있으면 범위 밖 시각을 뺀다

**테스트 관점** `-3` → 첫 구간 시작 · `duration+10` → 마지막 구간 시작 · 범위 안은 안 바뀐다 · 같은 값 둘 → 하나

---

#### AnalysisService.filename_for 제목 → 파일 이름

**시그니처** `def filename_for(video: Video) -> str`

근거: [[VA-UI-002#UI-7]] 2.1(저장 경로 표시) · [[VA-API-001]] 6장 미결(파일 이름 규칙 — 여기서 정한다)

**처리** `name = video.title` · 로컬 파일이면 확장자를 뗀다 · 유니코드 NFC 정규화 · `\ / : * ? " < > |`와 제어 문자를 `_`로 · 연속 공백 · 밑줄을 하나로 · 앞뒤 공백 · 점 제거 · 80자로 자른다(문자 단위) · 비면 `video-{id}` · `→ name`. 확장자 `.md`는 부르는 쪽이 붙인다

**테스트 관점** `RAG 서비스 1년 운영기` → 그대로 · `a/b:c?` → `a_b_c_` · 200자 제목 → 80자 · `workshop_0912.mp4` → `workshop_0912` · 빈 제목 → `video-12`

---

#### export.build 결과 → 마크다운

**시그니처** `def build(result: Result, turns: list[ChatTurn] | None) -> str`

근거: [[VA-API-001#GET/api/videos/{id}/export]] 내용 순서 · [[VA-UC-001#UC-H7]] 2번, 2a · 2b · [[VA-PRD-001#R10]] · [[VA-UI-002#UI-7]] 규칙(로컬 파일 원본 줄)

**입력** `turns`가 `None`이면 질문 기록 절을 붙이지 않는다. `[]`이면 절 제목과 「질문 기록이 없습니다」

**처리** — 순수 함수. 순서대로 문자열을 잇는다. `T = timecode(sec, result.video.duration_sec)`, `L = link(sec, result.video)`
1. `# {video.title}`
2. 원본 줄 — if `youtube` → `원본: [{video.origin}]({video.origin}) · {T(duration_sec)}` · else → `원본: {video.origin} · {T(duration_sec)}` (링크 없음)
3. 빈 줄 · `> {summary.one_liner}`
4. `## 핵심 인사이트` · 인사이트마다 `{seq}. {text} {L(source_secs[0])} {L(…)}` — 시각은 문장 끝에 전부
5. `## 챕터` · if 파트 있음 → 파트마다 `### {part.title} ({T(start)} – {T(end)})` 아래에 챕터 · 챕터는 `#### {L(start_sec)} {title}`와 `- {bullet}` ×N · 파트 없으면 챕터를 `### {L(start_sec)} {title}`로
6. `## 스크립트` · 구간마다 `{L(start_sec)} {text}` 한 줄 · 출처 한 줄을 절 제목 아래에: `자막(수동) · ko` 꼴(화면 8.1과 같은 문구)
7. if `turns is not None` → `## 질문 기록` · 턴마다 `**Q.** {question}` · `**A.** {answer}` · 근거가 있으면 `근거: {L(sec)} …` · 빈 줄 · 턴이 없으면 `질문 기록이 없습니다`
8. `→ 문자열` (줄바꿈 `\n`, 끝에 빈 줄 하나)

**출력** 마크다운 문자열. 옵시디언 · 노션에 그대로 붙는다

**호출하는 것** [[#export.timecode]] · [[#export.link]]

**테스트 관점** 스냅샷 테스트: 자막 있는 50분 YouTube 결과 → 예상 문자열과 일치 · 로컬 150분 결과(파트 있음) → 원본 줄에 링크 없음, 파트 제목 줄 있음, 시각이 `h:mm:ss` · `turns=None`과 `[]`의 차이 · 인사이트의 시각 두 개가 모두 나온다

---

#### export.timecode 초 → 표기

**시그니처** `def timecode(sec: float, duration_sec: int) -> str`

근거: [[VA-UI-001#UI-4]] 시각 표기(형식은 영상 길이로 정한다)

**처리** `→ timecode.label(sec, long=duration_sec ≥ 3600)` — 표기 규칙은 공용 [[VA-MS-006#timecode.label]] 하나에만 둔다. 어댑터와 내보내기가 같은 함수를 쓰므로 두 벌이 되지 않는다. 한 영상 안에서 표기가 섞이지 않는다(영상 길이로 정한다)

**호출하는 것** [[VA-MS-006#timecode.label]]

**테스트 관점** 50분 영상의 760.12 → `12:40` · 150분 영상의 380 → `0:06:20` · 150분 영상의 3600 → `1:00:00`

---

#### export.link 시각 → 링크 또는 텍스트

**시그니처** `def link(sec: float, video: Video) -> str`

근거: [[VA-PRD-001#R10]] · [[VA-UC-001#UC-H7]] 2a · [[VA-UI-002#UI-7]] 규칙

**처리** `t = timecode(sec, video.duration_sec)` · if `video.source_kind == youtube` → `f"[{t}](https://youtu.be/{video.source_id}?t={int(sec)})"` · else → `f"[{t}]"`

**테스트 관점** YouTube → `[12:40](https://youtu.be/dQw4w9WgXcQ?t=760)` · 로컬 → `[12:40]`

---

## 3. 미결사항

- [x] (반영: 클래스 명세 v10) **되먹임** — `clamp_secs`가 가장 가까운 구간 시각으로 보정하려면 `segments`를 받아야 한다. 클래스 명세 4.3의 `clamp_secs(secs, duration_sec)`에 인자 하나를 더한다([[VA-DOM-002#AnalysisService]]). 시그니처만 바뀌고 규칙은 그대로
- [ ] 같은 제목의 영상 둘을 내보내면 파일이 서로 덮어쓴다(`filename_for`). 뒤에 `-{id}`를 붙일지 사용자 확인 — 붙이면 화면의 경로 표시도 바뀐다
- [ ] 스크립트 토큰 수 세기 — `tiktoken`으로 정확히 셀지, 글자 수 ÷ 2로 어림할지. 첫 버전은 어림(의존성 없음). `config.TEXT_TOKEN_LIMIT`가 여유 있으니 오차가 문제되지 않는다
- [ ] 파트 제목 — 포트가 파트를 안 주면 첫 챕터 제목을 쓴다(`generate_chapters` 5번). 파트 제목만 따로 모델에 묻는 호출을 더할지
- [ ] 중간 요약을 재료로 한 최종 요약의 품질 — 챕터를 재료로 쓰는 [[VA-UC-001#UC-S4]] 1a2와 결과가 다를 수 있다. 품질을 보고 실행 순서(챕터 먼저)로 되돌릴지([[VA-DOM-002]] 5장 10)
- [ ] 내보내기 스크립트 절의 크기 — 3시간이면 3,000줄이다. 스크립트를 별도 파일로 뺄지 사용자 확인. 첫 버전은 한 파일([[VA-PRD-001#R10]] 「하나의 마크다운 파일」)
