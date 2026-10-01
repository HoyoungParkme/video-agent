---
doc_id: VA-MS-003
type: MS
title: MINISPEC — AnalysisService · export
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-DOM-003, VA-UC-001, VA-PRD-001]
---

# MINISPEC — AnalysisService · export

## 0. 이 문서가 다루는 것

`domains/analysis/service.py`의 함수 23개와 `domains/analysis/export.py`의 순수 함수 8개. 클래스 명세 [[VA-DOM-002#AnalysisService]]의 시그니처를 함수 내부까지 내린 것. 4.3 절이 두 파일이라 이 문서도 두 모듈이다. 포트 · 어댑터(`summarizer_openai` · `frames_storyboard` · `frames_local` · `image_openai`)와 원본 경로(`sources.local_path`)는 4.6 · 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10. 내부 타입(`CaptionLine` `SummaryDraft` `ChapterDraft` `FrameShot` `InfographicBrief` `ImageShot` `ChosenModels`)은 [[VA-DOM-002]] 2.6, 응답 형태(`Result` `Transcript` `Segment` `Summary` `Insight` `Part` `Chapter` `SuggestedQuestion` `Frame` `FrameSet` `FrameProgress` `FrameProgressItem` `Infographic` `InfographicImage` `ExportPreview` `ExportResult` `ExportFile` `ChatTurn`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `DB:` 테이블 접근(`crud`를 거친다), `FS:` 파일 접근.

**이 묶음이 아는 것** — `transcripts` · `segments` · `summaries` · `insights` · `parts` · `chapters` · `suggested_questions` · `chapter_frames` · `infographics` 아홉 테이블, `data/export/` · `data/frames/` · `data/infographics/`. 영상은 `Video` DTO로, 대화 턴은 `list[ChatTurn]`으로 인자로 받는다. 작업 묶음을 모른다 — 파이프라인이 부르는 순서는 파이프라인의 것이다([[VA-DOM-002]] 3.2). 세션은 호출자(라우터 또는 파이프라인의 짧은 세션)의 것.

**설정값(첫 값)**

| 이름 | 첫 값 | 이유 |
|---|---|---|
| `config.TEXT_WINDOW_SEC` | 1800 | 스크립트가 길 때 30분 구간으로 나눈다. 3시간이면 6구간 |
| `config.TEXT_TOKEN_LIMIT` | 100000 | 한 번에 보내는 스크립트 토큰 상한. 토큰 수는 [[VA-MS-006#tokens.estimate]]로 어림한다. 3시간 상한 안의 영상은 대부분 한 번에 간다 — 말이 아주 빠르거나 글자가 많은 스크립트만 구간 처리로 간다. 실측(카드 C): 받아쓰기 스크립트는 영상 1분당 약 500토큰이라 3시간이면 9만 안팎이다. 처음 값 4만은 분당 200토큰을 가정한 것이라 올렸다 — 그대로 두면 1시간 반 넘는 영상부터 구간 처리로 가 파트 제목도 모델이 짓지 않는다(사용자 결정 2026-09-29) |
| `config.CHAPTER_MINUTES` | 6 | 챕터 하나가 맡는 분. 목표 챕터 수 = 길이(분) ÷ 6 |
| `config.PART_THRESHOLD_SEC` | 3600 | 이보다 길면 파트를 만든다([[VA-PRD-001#R5]]) |
| `config.FRAMES_DIR` | `{DATA_DIR}/frames` | 대표 장면. 영상마다 폴더 하나, 파일은 `{chapter_seq}.jpg`([[VA-INFRA-001]] 6절) |
| `config.INFOGRAPHICS_DIR` | `{DATA_DIR}/infographics` | 인포그래픽. 영상마다 `{video_id}.png` 한 장 |
| `config.EXPORT_DIR` | `{DATA_DIR}/export` | 파일로 저장하는 곳([[VA-UI-001]] 7장 14). 컨테이너 안에서는 `/app/data/export`다 — 화면에는 이 경로가 아니라 보일 경로 `data/export/{파일 이름}.md`를 준다(저장소 폴더 기준, compose가 `./data`를 붙인다. inbox의 `INBOX_DISPLAY_PATH`와 같은 이유) |

**요약 · 챕터 · 추천 질문의 실행 순서는 파이프라인이 정한다** — 핵심 요약 → 챕터 → 추천 질문([[VA-DOM-002]] 5장 10). 세 함수는 서로를 부르지 않고 각자 `segments`를 읽는다.

**뒤 일 태스크** — 장면 채우기 · 인포그래픽 그리기는 대기열을 거치지 않고 이 서비스가 띄운다([[VA-DOM-002]] 5장 13). 클래스 속성 셋 — `_making: set[int]`(장면을 만드는 중인 영상, 파이프라인의 장면 단계도 넣는다), `_frame_tasks` · `_image_tasks: dict[int, Task]`(영상 id → 태스크). 프로세스 하나 전제다. 태스크는 요청이 끝난 뒤에도 돌므로 요청 세션을 쓰지 않고 `SessionLocal`로 자기 세션을 열어, 같은 포트로 만든 서비스를 쓴다.

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
| [[#AnalysisService.make_frames]] | 챕터마다 장면 한 장 — 파이프라인 장면 단계 · 채우기 태스크 |
| [[#AnalysisService.frames_state]] | 결과의 장면 상태 (absent · making · done · unavailable) |
| [[#AnalysisService.fill_frames]] | 옛 결과에 장면 채우기를 맡긴다 (202) |
| [[#AnalysisService.frames_of]] | 장면 상태와 목록 (3초 폴링) |
| [[#AnalysisService.frame_progress]] | 진행 화면의 장면 칸 |
| [[#AnalysisService.frame_file]] | 장면 그림 파일 경로 |
| [[#AnalysisService.infographic_of]] | 인포그래픽 상태 |
| [[#AnalysisService.start_infographic]] | 인포그래픽 그리기를 맡긴다 (202) |
| [[#AnalysisService.draw_infographic]] | 뒤에서 그린다 (태스크) |
| [[#AnalysisService.infographic_file]] | 인포그래픽 그림 파일 경로 |
| [[#AnalysisService.cancel_tasks]] | 삭제 전에 뒤 일 멈추기 |
| [[#AnalysisService.fail_orphans]] | 시작 때 그리던 인포그래픽을 failed로 |
| [[#AnalysisService.export_markdown]] | 고른 방법의 노트 본문(스크립트 줄 없음) + 파일 이름 + 함께 쓸 파일 |
| [[#AnalysisService.export_to_file]] | `data/export/`에 노트 · 스크립트 · 장면 · 인포그래픽 쓰기 |
| [[#AnalysisService.clamp_secs]] | 시각을 스크립트 범위로 보정 |
| [[#AnalysisService.filename_for]] | 제목 → 파일 이름 |
| [[#export.build]] | 결과 → 노트 마크다운 |
| [[#export.build_script]] | 결과 → 스크립트 마크다운(따로 쓰는 파일) |
| [[#export.gantt]] | 한눈에 보기 — Mermaid `gantt` 블록 |
| [[#export.mindmap]] | 한눈에 보기 — Mermaid `mindmap` 블록 |
| [[#export.frame_name]] | 장면 그림 파일 이름 |
| [[#export.infographic_name]] | 인포그래픽 그림 파일 이름 |
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
3. `chapters = draft.chapters`를 `start_sec` 오름차순 · `start_sec = clamp_secs([start_sec], duration, segments)[0]` · 같은 초(소수를 버린 초 — 시각 표기가 같다)가 둘이면 뒤 것을 뺀다 — 화면 · 노트에 같은 시각의 챕터 둘이 서지 않고, 장면 그림 이름([[#export.frame_name]])이 겹치지 않는다(이슈 #16) · 첫 챕터의 `start_sec`가 0이 아니면 0으로 당긴다(스크립트 처음이 어느 챕터에도 안 들어가는 것을 막는다)
4. `bullets`는 2~3줄로 자른다(4개 이상이면 앞 3개)
5. if `video.duration_sec > config.PART_THRESHOLD_SEC` → 파트 — if `draft.parts`가 있고 `len ≥ 2` → 그대로 · else → 챕터를 60분 단위로 묶어 파트를 만들고 제목은 `SummarizerPort.summary`가 아니라 첫 챕터 제목을 쓴다(미결 3) · 파트 시작 시각도 `clamp_secs`로 보정해 오름차순, 같은 시각은 하나로, **첫 파트는 0초로 당긴다**(첫 챕터가 0초라 어느 파트에도 안 드는 것을 막는다) · 챕터마다 `part_seq` = 시작 시각이 속한 파트(모델이 준 번호가 아니라 시각으로 정한다) · 챕터가 하나도 없는 파트는 빼고 번호를 다시 매긴다 · **파트 시작 시각을 그 파트 첫 챕터의 시작으로 맞춘다** — 모델이 준 파트 시작은 챕터 경계와 다를 수 있어, 한눈에 보기의 파트 띠를 누르면 앞 파트의 챕터가 강조되고 띠와 막대의 경계가 어긋났다(이슈 #14, 카드 D1 코드 리뷰). 챕터가 드는 파트는 그대로다 — 파트의 첫 챕터 시작 ≤ 그 파트 챕터 < 다음 파트의 첫 챕터 시작
   else → 파트 없음, `part_seq=None`
6. **트랜잭션**: `DB: delete parts where video_id` · `DB: delete chapters where video_id` · `DB: parts insert ×M (video_id, seq, title, start_sec)` · `DB: chapters insert ×N (video_id, part_id, seq=1부터 영상 전체 순번, start_sec, title, bullets)`
7. `→ None`

**출력** 없음

**호출하는 것** [[#AnalysisService.segments_of]] · [[#AnalysisService.clamp_secs]] · `SettingsService.current_models` · `SummarizerPort.chapters`

**테스트 관점** 50분 → 파트 0, 챕터 8 안팎, 첫 챕터 0초 · 150분 → 파트 ≥ 2, 챕터마다 `part_id`, 파트 시작 시각이 오름차순 · 모델이 첫 파트를 5분에 두어도 0초로 당겨 첫 챕터가 첫 파트에 든다 · 챕터 없는 파트는 빠진다 · 모델이 둘째 파트를 1:15:00에 두고 챕터가 1:14:30 · 1:16:30이면 둘째 파트는 1:16:30에서 시작하고 1:14:30 챕터는 첫 파트에 남는다 · 모델 파트가 하나뿐이면 60분 묶음 · 같은 시각 챕터 둘 → 하나 · 65.2초 · 65.9초로 보정된 챕터 둘(같은 초) → 앞의 것 하나 · `bullets` 4개 → 3개 · 두 번 돌리면 행이 한 벌

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
4. `parts = DB: parts where video_id order by seq` · `chs = DB: chapters where video_id order by seq` · `qs = DB: suggested_questions where video_id order by seq` · `frs = DB: chapter_frames where chapter_id in chs` · `ig = DB: infographics where video_id`
5. 파트마다 `end_sec` = 다음 파트의 `start_sec`, 마지막은 `video.duration_sec` · `chapter_count` = 그 파트의 챕터 수. 챕터의 `part_seq` = `part_id`로 찾은 파트의 `seq`(없으면 `None`) · 챕터의 `frame` = 그 챕터의 행에 그림이 있고 파일도 있으면 `Frame(chapter_seq, sec, source, width, height, url=f"/api/videos/{id}/frames/{seq}")`, 아니면 `None`
6. `→ Result(video, transcript=Transcript(t.source, t.language, t.model, segments=[Segment(seq, start_sec, end_sec, text) …]), summary=Summary(s.one_liner, s.model, insights=[Insight(seq, text, source_secs) …]), parts, chapters, suggested_questions=[SuggestedQuestion(seq, text) …], models=Models(stt=t.model, text=s.model), analyzed_at=video.analyzed_at, frames_state=frames_state(video, chs, frs), infographic=ig로 만든 Infographic([[#AnalysisService.infographic_of]]와 같은 모양))` — 읽기만 한다. 장면 채우기를 시작하지 않는다([[VA-API-001]] 5장 14)

**출력** `Result`. 구간 수천 개를 한 번에([[VA-API-001]] 5장 3)

**예외** `result-not-ready`

**호출하는 것** 없음

**테스트 관점** 상태 `in_progress` → `result-not-ready`에 `video_status=in_progress` · 파트 둘이면 첫 파트 `end_sec`가 둘째 `start_sec` · 마지막 파트 `end_sec`가 영상 길이 · `chapter_count` 합이 챕터 수 · 자막 결과는 `models.stt=None` · 장면이 있는 챕터만 `frame`이 있고 그림 컬럼이 null인 행 · 파일이 지워진 행은 `frame=None` · 장면 단계 전 결과는 `frames_state=absent` · 인포그래픽이 없으면 `infographic.state=none` · 쿼리 수가 8을 넘지 않는다

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

#### AnalysisService.make_frames 챕터마다 장면 한 장

**시그니처** `async def make_frames(video: Video) -> None`

근거: [[VA-SEQ-001#SEQ-16]] 3~17번 · [[VA-SEQ-001#SEQ-17]] 14번 · [[VA-UC-001#UC-S7]] · [[VA-INFRA-001#C12]] · [[VA-DOM-003#chapter_frames]]

**입력** `video` — `id` · `source_kind` · `source_id` · `origin` · `uploaded`를 쓴다

**처리**
1. `_making.add(video.id)` — 어떻게 끝나든 뺀다(`finally`)
2. `chs = DB: chapters where video_id order by seq` · `todo = 장면 행이 없는 챕터` · if `todo`가 비면 → 끝(다시 시도 · 이어 채우기는 해 본 챕터를 건너뛴다)
3. if `youtube` → `port = storyboard`, `source = video.source_id` · else → `port = local_frames`, `source = sources.local_path(video.origin, video.source_id, video.uploaded)`(MINISPEC 어댑터)
4. `dest = config.FRAMES_DIR / str(video.id)` · `FS: mkdir(dest)`
5. `async for` 로 `port.frames(source, [c.start_sec for c in todo], str(dest))`를 받는다 — 시각 순서대로 하나씩 온다. `c` = 그 차례의 챕터 · if `shot` → `FS: os.replace(shot.path, dest / f"{c.seq}.jpg")` · `DB: chapter_frames insert(chapter_id=c.id, sec, source, width, height, path)` · else → `DB: chapter_frames insert(chapter_id=c.id)`(그림 컬럼 null) · **행마다 커밋** — 진행 폴링이 한 장씩 본다
6. if 포트가 예외를 던지면(취소 빼고 — 스토리보드 없음 · 원본 없음 · yt-dlp · ffmpeg 실패) → 아직 행이 없는 챕터에 null 행을 쓰고 로그 한 줄 · 예외는 올리지 않는다 — 「해 봤다」를 남겨 옛 결과를 다시 채우지 않는다([[VA-DOM-002]] 5장 11, [[VA-UC-001#UC-S7]] 2a · 3a)
7. `→ None`

**출력** 없음

**예외** 포트 실패는 삼킨다(6번). DB 오류 · 취소는 올린다 — 파이프라인은 삼키고(장면은 작업을 실패로 만들지 않는다, [[VA-UC-001#UC-S6]] 1b) 뒤 일 태스크는 로그만 남긴다

**호출하는 것** `FrameSourcePort.frames`(`frames_storyboard` · `frames_local`) · `sources.local_path`

**테스트 관점** 가짜 포트로: 챕터 셋을 다 얻음 → 행 셋, 파일 `data/frames/{id}/1.jpg` ~ `3.jpg` · 둘째가 None → 둘째 행은 그림 컬럼이 null · 첫 시각 뒤 포트가 예외 → 나머지 둘이 null 행이고 예외가 밖으로 나오지 않는다 · 이미 행이 있는 챕터는 시각 목록에 없다 · 로컬 영상은 `local_frames`에 원본 경로, YouTube는 `storyboard`에 영상 ID · 도는 동안 `frames_state`가 `making`, 끝나면(예외여도) 빠진다 · 취소하면 `CancelledError`가 나오고 도는 중에서 빠진다

---

#### AnalysisService.frames_state 결과의 장면 상태

**시그니처** `def frames_state(video: Video, chapters: list[ChapterRow], frames: list[ChapterFrameRow]) -> FramesState`

근거: [[VA-API-001#GET/api/videos/{id}/frames]] `state` · [[VA-DOM-002]] 5장 11 · 13 · [[VA-UC-001#UC-S7]] 1a · 2a

**처리** 위에서부터 — if `video.id in _making` → `making` · if 챕터마다 행이 있다(null 행 포함, 챕터가 없어도) → `done` · if `local`이고 (확장자가 `config.AUDIO_EXTS`이거나 `sources.local_path`의 파일이 없다) → `unavailable` · else → `absent`

**테스트 관점** 도는 중 → `making`(행이 일부여도) · 행이 챕터 수만큼(null 행 포함) → `done` · 음성 파일 → `unavailable` · inbox 원본을 옮긴 로컬 영상 → `unavailable` · 올린 영상은 사본을 지웠어도 행이 다 있으면 `done` · 장면 행이 없는 YouTube → `absent` · 행이 일부만 있는 YouTube(채우다 죽음) → `absent`

---

#### AnalysisService.fill_frames 옛 결과에 장면 채우기를 맡긴다

**시그니처** `async def fill_frames(video: Video) -> FrameSet`

근거: [[VA-SEQ-001#SEQ-17]] 3~16번 · [[VA-API-001#POST/api/videos/{id}/frames]] · [[VA-UC-001#UC-H3]] 1a · 1b · [[VA-API-001]] 5장 14

**처리**
1. if `video.status != analyzed` → `! result-not-ready {video_status}`
2. `chs` · `frs` 읽기 · `st = frames_state(video, chs, frs)`
3. if `unavailable` → `! frames-unavailable {reason}` — 음성 파일이면 '음성 파일이라 장면이 없어요', 원본이 없으면 '원본 파일을 찾을 수 없어요'
4. if `absent` → `_making.add(video.id)` · `_frame_tasks[video.id] = create_task(_fill(video))` · `st = making` — `_fill`은 자기 세션으로 같은 포트의 서비스를 만들어 [[#AnalysisService.make_frames]]를 부르고, 예외는 로그 한 줄로 삼키고, 끝나면 핸들을 뺀다
5. `→ FrameSet(state=st, frames=[Frame …] — 그림이 있고 파일이 있는 행만, 챕터 순서)` — `making` · `done`이면 아무것도 하지 않고 지금 상태를 준다

**출력** `FrameSet`(202)

**예외** `result-not-ready` · `frames-unavailable`

**호출하는 것** [[#AnalysisService.frames_state]] · [[#AnalysisService.make_frames]](태스크 안)

**테스트 관점** `absent` → 202 `making`, 태스크가 끝나면 `frames_of`가 `done` · 곧바로 다시 부르면 태스크가 하나뿐 · `done`이면 태스크를 띄우지 않는다 · 음성 파일 → `frames-unavailable` · 분석 중인 영상 → `result-not-ready` · 키가 없어도 된다(키를 보지 않는다)

---

#### AnalysisService.frames_of 장면 상태와 목록

**시그니처** `async def frames_of(video: Video) -> FrameSet`

근거: [[VA-SEQ-001#SEQ-17]] 17~22번 · [[VA-API-001#GET/api/videos/{id}/frames]]

**처리** if `video.status != analyzed` → `! result-not-ready` · `chs` · `frs` 읽기 · `→ FrameSet(state=frames_state(video, chs, frs), frames=[Frame(chapter_seq, sec, source, width, height, url=f"/api/videos/{id}/frames/{seq}") — 그림이 있고 파일이 있는 행만, 챕터 순서])`

**테스트 관점** 그림 컬럼이 null인 행은 목록에 없다 · 파일이 지워진 행도 없다 · 챕터 순서 · 3초 폴링이라 쿼리 둘(챕터 · 장면)

---

#### AnalysisService.frame_progress 진행 화면의 장면 칸

**시그니처** `async def frame_progress(video_id: int) -> FrameProgress`

근거: [[VA-SEQ-001#SEQ-5]] 3~5번 · [[VA-API-001#GET/api/videos/{id}/job]] `frames` · [[VA-UI-002#UI-3]] 4.9 ~ 4.11 · [[VA-DOM-002]] 5장 14

**처리** `chs` · `frs` 읽기 · 챕터마다 — if 그림이 있는 행 → `done`(`url`) · if null 행 → `missing` · if 행이 없음 → 도는 중이고 행 없는 첫 챕터면 `in_flight`, 아니면 `waiting` · `→ FrameProgress(done=그림이 있는 행 수, total=챕터 수, items)`. 챕터가 아직 없으면(받아쓰기 중) `FrameProgress(0, 0, [])` — 싣는지는 `JobService.progress`가 단계 목록을 보고 정한다

**테스트 관점** 챕터 넷 · 행 둘(그림 하나 · null 하나) · 도는 중 → `[done, missing, in_flight, waiting]`, `done=1` · 안 돌면 셋째도 `waiting` · 챕터 없음 → `0 / 0` · 1초 폴링이라 쿼리 둘

---

#### AnalysisService.frame_file 장면 그림 파일

**시그니처** `async def frame_file(video_id: int, seq: int) -> str`

근거: [[VA-SEQ-001#SEQ-C1]] · [[VA-API-001#GET/api/videos/{id}/frames/{seq}]]

**처리** `DB: chapter_frames join chapters where video_id and chapters.seq = seq` · if 행이 없거나 `path`가 null이거나 파일이 없다 → `! not-found {resource: frame, id: seq}` · `→ path` — 라우터가 `image/jpeg` · `Cache-Control: no-cache`로 준다

**테스트 관점** 있는 장면 → 경로 · null 행 → `not-found(frame)` · 다른 영상의 seq → `not-found` · 영상이 없어도 `not-found(frame)`

---

#### AnalysisService.infographic_of 인포그래픽 상태

**시그니처** `async def infographic_of(video: Video) -> Infographic`

근거: [[VA-SEQ-001#SEQ-18]] 34~39번 · [[VA-API-001#GET/api/videos/{id}/infographic]] · [[VA-UC-001#UC-H9]] 5번

**처리** if `video.status != analyzed` → `! result-not-ready` · `row = DB: infographics where video_id` · if 없음 → `Infographic(state=none, image=None, error_reason=None)` · else → `Infographic(state=row.state, image=그림, error_reason=row.error_reason)` — 그림은 그림 컬럼이 있고 파일이 있으면 `InfographicImage(url=f"/api/videos/{id}/infographic/image?v={int(created_at.timestamp())}", model, quality, width, height, created_at, cost_usd)`, 아니면 `None`

**테스트 관점** 행 없음 → `none` · `making`인데 이전 그림이 있음 → `image`가 있다 · `failed` + 이전 그림 → 둘 다 · 다시 그리면 `?v=`가 바뀐다 · 파일이 없으면 `image=None`

---

#### AnalysisService.start_infographic 인포그래픽 그리기를 맡긴다

**시그니처** `async def start_infographic(video: Video) -> Infographic`

근거: [[VA-SEQ-001#SEQ-18]] 8~24번 · [[VA-API-001#POST/api/videos/{id}/infographic]] 1~4번 · [[VA-UC-001#UC-H9]] 1~4번, 2a · [[VA-API-001]] 5장 13

**처리**
1. if `video.status != analyzed` → `! result-not-ready`
2. `row = DB: infographics where video_id` · if `row.state == making` → `! infographic-busy`
3. `SettingsService.check_stored_key()` · `SettingsService.require_key()` — 분석 버튼 · 올리기와 같다([[VA-API-001]] 1장 키를 확인하는 때)
4. **한 문장**: `DB: insert infographics(video_id, state=making) on conflict (video_id) do update set state=making, error_reason=null where infographics.state <> 'making' returning id` · if 0행(겹친 요청이 먼저 바꿨다) → `! infographic-busy` · 그림 컬럼은 건드리지 않는다 — 이전 그림이 그대로 보인다([[VA-SEQ-001]] 되먹일 것 #11)
5. `choice = SettingsService.current_models()` · `_image_tasks[video.id] = create_task(draw_infographic(video.id, choice))` — 기다리지 않는다
6. `→ infographic_of(video)` — `state=making`, 이전 그림이 있으면 `image`

**출력** `Infographic`(202)

**예외** `result-not-ready` · `infographic-busy` · `key-missing` · `key-invalid`

**호출하는 것** `SettingsService.check_stored_key` · `require_key` · `current_models` · [[#AnalysisService.draw_infographic]](태스크) · [[#AnalysisService.infographic_of]]

**테스트 관점** 처음 → 행이 생기고 202 `making` · 그리는 중에 또 → `infographic-busy` · 두 요청이 동시에 → 하나만 202, 다른 하나는 `infographic-busy` · 키 없음 → `key-missing`, 행이 생기지 않는다 · 이전 그림이 있을 때 다시 → `making`인데 `image`는 이전 것 · 가짜 포트가 오래 걸려도 응답은 바로

---

#### AnalysisService.draw_infographic 뒤에서 그린다

**시그니처** `async def draw_infographic(video_id: int, choice: ChosenModels) -> None`

근거: [[VA-SEQ-001#SEQ-18]] 25~33번 · [[VA-UC-001#UC-H9]] 4 · 5번, 4a · 5a · [[VA-INFRA-001#C11]] · [[VA-DOM-003#infographics]]

**처리** — 태스크 안. `SessionLocal`로 자기 세션을 연다
1. `DB: videos.title · summaries · insights · chapters where video_id` → `brief = InfographicBrief(title, one_liner, insights=[text …], chapter_titles=[title …])` — 스크립트는 넣지 않는다([[VA-UC-001#UC-H9]] 4번)
2. `tmp = config.INFOGRAPHICS_DIR / f"{video_id}.png.part"` · `FS: mkdir`
3. `shot = ImageMakerPort.infographic(brief, choice.image_model, choice.image_quality.id, str(tmp))`
4. `FS: os.replace(tmp, config.INFOGRAPHICS_DIR / f"{video_id}.png")` — 다 그린 뒤 한 번에 바꾼다
5. `DB: update infographics set state=done, model, quality, width, height, cost_usd=choice.image_quality.price_usd, path, created_at=지금, error_reason=null`
6. 1 ~ 5번 어디서든 실패하면 — `llm-unavailable`(어댑터가 OpenAI 실패를 바꾼 것, [[VA-MS-006#answerer_openai.answer]]와 같은 방식) → `reason = e.reason` · `key-missing`(그리는 사이 `.env`에서 키가 빠져 어댑터가 클라이언트를 만들지 못했다) → 'OpenAI API 키 없음' · `OSError` → '그림 파일을 저장하지 못함' · 그 밖(DB 오류 포함) → '알 수 없는 오류'(원인은 로그) · 세션을 되돌린 뒤(1 · 5번의 DB 오류로 트랜잭션이 깨졌을 수 있다) `DB: update set state=failed, error_reason=reason` · 그림 컬럼은 그대로 · `tmp`를 지운다. 4번 뒤에 5번이 실패했다면 파일은 새 그림이고 행의 그림 값은 이전 것이다 — 다음 그리기가 맞춘다. 실패마저 적지 못하면(DB가 없다) 로그만 남긴다 — 행은 `making`으로 남고 다음 시작의 [[#AnalysisService.fail_orphans]]가 되돌린다(카드 D3 코드 리뷰 — 5번이 실패 처리 밖이면 행이 영영 `making`이라 [만들기]가 모두 `infographic-busy`였다)
7. 취소(`CancelledError`) → `tmp`를 지우고 올린다 — 행은 둔다(영상 삭제면 cascade가, 서버 종료면 다음 시작의 [[#AnalysisService.fail_orphans]]가 정리한다)
8. 어떻게 끝나든 `_image_tasks`에서 뺀다

**출력** 없음

**예외** 취소만 올린다

**호출하는 것** `ImageMakerPort.infographic`

**테스트 관점** 가짜 포트로: 성공 → `done`, 그림 컬럼, `cost_usd`가 그 품질의 한 장 값, 파일 `data/infographics/{id}.png` · `llm-unavailable('OpenAI 연결 시간 초과')` → `failed`, `error_reason` 그 문장, 이전 그림 파일과 컬럼 그대로 · 이전 그림이 있을 때 성공 → 새 그림으로 바뀌고 `created_at`이 바뀐다 · `brief`에 스크립트 줄이 없다 · 임시 파일이 남지 않는다 · 5번 DB 쓰기가 실패 → `failed`('알 수 없는 오류') · 1번에서 DB 오류가 나 트랜잭션이 깨져도 `failed`로 적힌다 · 그리는 사이 키가 빠짐 → `failed`('OpenAI API 키 없음')

---

#### AnalysisService.infographic_file 인포그래픽 그림 파일

**시그니처** `async def infographic_file(video_id: int) -> str`

근거: [[VA-SEQ-001#SEQ-C1]] · [[VA-API-001#GET/api/videos/{id}/infographic/image]]

**처리** `row = DB: infographics where video_id` · if 없거나 `path`가 null이거나 파일이 없다 → `! not-found {resource: infographic, id: video_id}` · `→ path` — 라우터가 `image/png`로 준다

**테스트 관점** 그린 뒤 → 경로 · 처음 그리는 중 → `not-found` · 다시 그리는 중 → 이전 그림 경로

---

#### AnalysisService.cancel_tasks 뒤 일 멈추기

**시그니처** `async def cancel_tasks(video_id: int) -> None`

근거: [[VA-SEQ-001#SEQ-11]] 10~12번 · [[VA-API-001#DELETE/api/videos/{id}]]

**처리** `_frame_tasks` · `_image_tasks`에서 그 영상의 핸들을 꺼내 `cancel()`하고 끝나기를 기다린다(`CancelledError`는 삼킨다) · `_making.discard(video_id)` · 없으면 아무것도 안 한다. 파이프라인의 장면 단계는 작업 태스크의 일부라 `JobService.cancel`이 멈춘다

**테스트 관점** 그리는 중 → 태스크가 취소되고 임시 파일이 없다 · 태스크 없는 영상 → 조용히 끝 · 다른 영상의 태스크는 그대로

---

#### AnalysisService.fail_orphans 그리던 인포그래픽 되돌리기

**시그니처** `async def fail_orphans() -> int`

근거: [[VA-SEQ-001#SEQ-13]] 12~14번 · [[VA-DOM-002]] 5장 13

**처리** `DB: update infographics set state=failed, error_reason='서버가 다시 시작됨' where state=making` · `→ 바뀐 행 수`. 장면은 되돌릴 것이 없다 — 「도는 중」이 메모리에만 있다

**테스트 관점** `making` 둘 · `done` 하나 → 2, `done`은 그대로 · 이전 그림 컬럼은 그대로

---

#### AnalysisService.export_markdown 마크다운 본문

**시그니처** `async def export_markdown(video: Video, with_chat: bool, turns: list[ChatTurn], method: ExportMethod) -> ExportPreview`

근거: [[VA-SEQ-001#SEQ-10]] 2~12번 · [[VA-API-001#GET/api/videos/{id}/export]] · [[VA-UC-001#UC-H7]] 1~2번, 2a · 2b · 2c · 2d · [[VA-PRD-001#R10]] · [[VA-UI-002#UI-7]] 규칙(4.1은 고른 방법의 노트)

**처리**
1. `result = result_of(video)` — `result-not-ready`는 여기서 난다
2. `name = filename_for(video)` · `past = turns if with_chat else None`
3. if `method == file` → `md = export.build(result, past, name)` — 저장할 노트와 같다. 그림 줄과 `## 스크립트` 절이 있다 · `files = _files(result, name)` · else(`clipboard`) → `md = export.build(result, past, None)` — 그림 줄도 스크립트 절도 없다(복사한 노트에는 가리킬 파일이 없다) · `files = []`
4. `→ ExportPreview(filename=name, path=f"data/export/{name}.md", markdown=md, files=files)` — `path`는 보일 경로다(UI-7 2.1 · 짧은 알림). 쓰는 곳은 `export_to_file`이 `config.EXPORT_DIR`로 정한다
- `_files(result, name)` = `[ExportFile(note, f"{name}.md"), ExportFile(script, f"{name} 스크립트.md")]` + 장면이 있는 챕터마다 `ExportFile(frame, export.frame_name(name, start_sec, duration_sec))`(챕터 순서) + 인포그래픽 그림이 있으면 `ExportFile(infographic, export.infographic_name(name))` — UI-7 2.3 칩이 이것을 센다. [[#AnalysisService.export_to_file]]이 쓰는 목록과 같다

**출력** `ExportPreview`. `markdown`은 노트 전체 — 화면이 앞부분만 보이고 클립보드는 `clipboard`의 전체를 쓴다

**예외** `result-not-ready`

**호출하는 것** [[#AnalysisService.result_of]] · [[#export.build]] · [[#AnalysisService.filename_for]]

**테스트 관점** `with_chat=false`면 `## 질문 기록` 절이 없다 · `true`이고 턴 0개면 절 제목만 있고 「질문 기록이 없습니다」 한 줄 · `path`가 `data/export/…md` · 스크립트 줄은 어느 방법에도 없다 · `clipboard` → 그림 줄 · `## 스크립트` 절이 없고 `files=[]` · `file` → `## 스크립트` 절, 장면이 있는 챕터에만 장면 줄, 인포그래픽 줄, `files`가 노트 · 스크립트 · 장면 n · 인포그래픽 순서 · 장면 · 인포그래픽이 없으면 `files`는 둘

---

#### AnalysisService.export_to_file 파일로 저장

**시그니처** `async def export_to_file(video: Video, with_chat: bool, turns: list[ChatTurn]) -> ExportResult`

근거: [[VA-SEQ-001#SEQ-10]] 13~24번 · [[VA-API-001#POST/api/videos/{id}/export]] · [[VA-UC-001#UC-H7]] 3번 · [[VA-UI-001]] 7장 14

**처리**
1. `result = result_of(video)` · `name = filename_for(video)` · `script = f"{name} 스크립트"` — 노트와 스크립트를 다시 만든다. 화면이 보낸 본문을 쓰지 않는다
2. `note = export.build(result, turns if with_chat else None, name)` — [[#AnalysisService.export_markdown]]의 `file`과 같다(그림 줄 · `## 스크립트` 절) · `text = `[[#export.build_script]]`(result)`
3. `FS: mkdir(config.EXPORT_DIR)` · 스크립트 `{script}.md` → 노트 `{name}.md` 순서로 UTF-8로 쓰기(덮어쓰기, 파일마다 같은 폴더의 임시 파일에 쓴 뒤 rename) → 장면이 있는 챕터마다 [[#AnalysisService.frame_file]]의 그림을 `export.frame_name(…)`으로, 인포그래픽 그림이 있으면 [[#AnalysisService.infographic_file]]의 그림을 `export.infographic_name(name)`으로 복사(같은 임시 파일 · rename) · if `OSError` → `! export-failed {path: 쓰지 못한 파일의 보일 경로, reason}` · 복사할 그림이 없으면(결과를 읽은 뒤 다시 채우기 · 지우기로 없어졌다 — `frame_file`의 `not-found`, 읽기의 `OSError`) → `! export-failed {path: 그 그림의 보일 경로, reason: '그림 파일을 찾을 수 없음'}`(카드 D2 코드 리뷰 — 없음 404가 아니라 저장 실패로 알린다) — `path`는 보일 경로(`data/export/…`), `reason`은 errno로 고른 한 줄이다(화면이 '파일을 저장하지 못했어요 — {이유}'로 보인다, [[VA-UI-002#UI-7]] 5.1)
   - 노트를 쓰다 실패하면 먼저 쓴 스크립트 파일만 새것으로 남는다 — 화면이 실패를 알리고(5.1) 다시 저장하면 둘이 맞춰진다. 결과는 DB에 있어 파일은 언제든 다시 만든다(카드 C 코드 리뷰)
   - 같은 이름은 덮어쓴다(사용자 결정 2026-09-28). 제목이 `{다른 영상 제목} 스크립트`인 영상의 노트도 그 다른 영상의 스크립트 파일과 이름이 같아, 나중에 저장한 쪽이 덮어쓴다 — 제목이 ' 스크립트'로 끝나야 생기는 드문 경우라 같은 규칙으로 둔다(사용자 결정 2026-09-29, 카드 C 코드 리뷰)

| errno | reason |
|---|---|
| `EACCES` · `EPERM` | 쓰기 권한이 없음 |
| `ENOSPC` | 디스크 공간이 부족함 |
| `EROFS` | 읽기 전용 폴더 |
| `EEXIST` · `ENOTDIR` | 저장 폴더를 만들 수 없음(그 자리에 파일이 있다) |
| 그 밖 | 파일을 쓸 수 없음 |

4. `→ ExportResult(filename=name, path=f"data/export/{name}.md", bytes=쓴 파일 전부의 바이트 합, images=쓴 그림 수, files=쓴 파일 — export_markdown의 _files와 같은 목록)` — `path`는 노트다(화면의 짧은 알림 '{path}에 저장했어요 · 스크립트는 따로 · 그림 {n}장')

**출력** `ExportResult`(201)

**예외** `result-not-ready` · `export-failed`

**호출하는 것** [[#AnalysisService.result_of]] · [[#AnalysisService.filename_for]] · [[#export.build]] · [[#export.build_script]]

**테스트 관점** 응답의 `files`가 `config.EXPORT_DIR`에 실제로 쓴 파일과 같다(이름으로) · 두 파일이 `config.EXPORT_DIR`에 생긴다(0644) · 노트는 `export_markdown(method=file)`의 본문과 같다 · 스크립트 파일은 `# {제목} — 스크립트`로 시작 · 장면 둘 · 인포그래픽이 있으면 파일 다섯, `images=3`, 이름이 `{이름} 09-51.jpg` · `{이름} 인포그래픽.png`이고 노트의 그림 줄이 그 이름을 가리킨다 · 그림 복사가 실패하면 `export-failed`(그 그림의 보일 경로) · 그림 파일이 그 사이 없어지면 `export-failed`('그림 파일을 찾을 수 없음', 그 그림의 보일 경로) · `bytes`는 쓴 파일 전부의 합 · 두 번 저장하면 둘 다 덮어쓴다 · 폴더가 없으면 만든다 · 폴더 자리에 파일이 있으면 `export-failed`(`path`는 보일 경로, `reason` '저장 폴더를 만들 수 없음(그 자리에 파일이 있다)') · 임시 파일이 남지 않는다

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

**처리** `name = video.title` · 로컬 파일이면 확장자를 뗀다 · 유니코드 NFC 정규화 · `\ / : * ? " < > |`와 제어 문자, 위키링크에서 뜻이 있는 `[ ] # ^`를 `_`로 — 노트가 `[[{이름} 스크립트]]`로 스크립트 파일을 가리키는데 Obsidian은 링크 안의 `#`를 제목, `^`를 블록, `]]`를 링크 끝으로 읽는다(`[EP.1] …` · `… #shorts` 같은 YouTube 제목, 카드 C 코드 리뷰) · 연속 공백 · 밑줄을 하나로 · 앞뒤 공백 · 점 제거 · 80자로 자른다(문자 단위) · UTF-8로 235바이트를 넘으면 더 자른다 — 파일 이름 한도가 255바이트이고, 이름 뒤에 붙는 꼬리 가운데 가장 긴 것이 인포그래픽의 ` 인포그래픽.png`(20바이트)다(스크립트 ` 스크립트.md` 16바이트 · 장면 ` 1-05-26.jpg` 12바이트, 카드 C · D3). 한글은 한 글자 3바이트라 80자(240바이트)가 78자(234바이트)가 되고, 이모지처럼 4바이트 글자가 많은 제목은 더 짧아진다 · 자른 끝의 공백 · 점도 뗀다 · 비면 `video-{id}` · `→ name`. 확장자 `.md`는 부르는 쪽이 붙인다

**테스트 관점** `RAG 서비스 1년 운영기` → 그대로 · `a/b:c?` → `a_b_c_` · `[EP.1] RAG #shorts ^v2` → `_EP.1_ RAG _shorts _v2` · 200자 제목 → 80자 · 한글 80자 제목 → 78자(79자는 237바이트라 235를 넘는다 — 카드 D3에서 238 → 235로 줄이며 고침) · 이모지 80자 제목 → 235바이트 이하(`{이름} 인포그래픽.png`까지 255바이트 안) · `workshop_0912.mp4` → `workshop_0912` · 빈 제목 → `video-12`

---

#### export.build 결과 → 마크다운

**시그니처** `def build(result: Result, turns: list[ChatTurn] | None, file_name: str | None = None) -> str`

근거: [[VA-API-001#GET/api/videos/{id}/export]] 내용 순서 · [[VA-UC-001#UC-H7]] 2번, 2a · 2b · 2c · 2d · [[VA-PRD-001#R10]] · [[VA-PRD-001#R11]] · [[VA-UI-002#UI-7]] 규칙(로컬 파일 원본 줄 · 그림 줄)

**입력** `turns`가 `None`이면 질문 기록 절을 붙이지 않는다. `[]`이면 절 제목과 「질문 기록이 없습니다」. `file_name`이 오면(파일로 저장 · 그 미리 보기) 그림 줄과 스크립트 파일을 가리키는 절을 둔다 — `None`이면(복사) 두지 않는다

**처리** — 순수 함수. 순서대로 문자열을 잇는다. `T = timecode(sec, result.video.duration_sec)`, `L = link(sec, result.video)`
1. `# {video.title}`
2. 원본 줄 — if `youtube` → `원본: [{video.origin}]({video.origin}) · {T(duration_sec)}` · else → `원본: {video.origin} · {T(duration_sec)}` (링크 없음)
3. 빈 줄 · `> {summary.one_liner}`
4. `## 한눈에 보기` · if `file_name`이고 `result.infographic.image`가 있다 → `![[{export.infographic_name(file_name)}]]` · [[#export.gantt]] 블록 · 빈 줄 · [[#export.mindmap]] 블록([[VA-PRD-001#R11]])
5. `## 핵심 인사이트` · 인사이트마다 `{seq}. {text} {L(source_secs[0])} {L(…)}` — 시각은 문장 끝에 전부
6. `## 챕터` · if 파트 있음 → 파트마다 `### {part.title} ({T(start)} – {T(end)})` 아래에 챕터 · 챕터는 `#### {L(start_sec)} {title}`와 `- {bullet}` ×N · 파트 없으면 챕터를 `### {L(start_sec)} {title}`로 · if `file_name`이고 그 챕터에 `frame`이 있다 → 챕터 제목 줄 바로 다음에 `![[{export.frame_name(file_name, start_sec, duration_sec)}]]`(요점 앞)
7. if `file_name` → `## 스크립트` · `[[{file_name} 스크립트]]` 한 줄(옵시디언 위키링크 — 같은 폴더의 스크립트 파일). 스크립트 줄은 노트에 없다 — [[#export.build_script]]가 따로 만든다([[VA-PRD-001#R10]], 사용자 결정 2026-09-29 — 한 파일이면 2시간 30분 영상의 노트가 5천 줄이 넘었다)
8. if `turns is not None` → `## 질문 기록` · 턴마다 `**Q.** {question}` · `**A.** {answer}` · 근거가 있으면 `근거: {L(sec)} …` · 빈 줄 · 턴이 없으면 `질문 기록이 없습니다`
9. `→ 문자열` (줄바꿈 `\n`, 끝에 빈 줄 하나)

**출력** 노트 마크다운 문자열. 옵시디언 · 노션에 그대로 붙는다

**호출하는 것** [[#export.timecode]] · [[#export.link]] · [[#export.gantt]] · [[#export.mindmap]] · [[#export.frame_name]] · [[#export.infographic_name]]

**테스트 관점** 스냅샷 테스트: 자막 있는 50분 YouTube 결과 → 예상 문자열과 일치 · 로컬 150분 결과(파트 있음) → 원본 줄에 링크 없음, 파트 제목 줄 있음, 시각이 `h:mm:ss` · `turns=None`과 `[]`의 차이 · 인사이트의 시각 두 개가 모두 나온다 · 스크립트 줄이 없다 · `file_name`이 오면 `## 스크립트`와 `[[{이름} 스크립트]]` 한 줄이 챕터 다음, 질문 기록 앞 · `None`이면 그 절이 없다 · `## 한눈에 보기`가 한 줄 요약 다음, 핵심 인사이트 앞에 있고 gantt · mindmap 블록이 둘 다 있다(어느 방법이든) · 그림 줄은 `file_name`이 있을 때만 — 인포그래픽 줄은 한눈에 보기 첫 줄, 장면 줄은 장면이 있는 챕터의 제목 줄 바로 다음

---

#### export.build_script 결과 → 스크립트 마크다운

**시그니처** `def build_script(result: Result) -> str`

근거: [[VA-PRD-001#R10]] · [[VA-API-001#POST/api/videos/{id}/export]] · [[VA-UC-001#UC-H7]] 2번

**처리** — 순수 함수. `T` · `L`은 [[#export.build]]와 같다
1. `# {video.title} — 스크립트`
2. 원본 줄 — [[#export.build]] 2번과 같다
3. 빈 줄 · 출처 한 줄 · 빈 줄. 출처 줄은 화면 8.1과 같은 문구다 — `자막(수동) · {언어}` · `자막(자동) · {언어}` · `받아쓰기 {transcript.model} · {언어}`. {언어}는 언어 코드의 이름(ko 한국어 · en 영어 · ja 일본어 · zh 중국어 · es 스페인어 · fr 프랑스어 · de 독일어 · pt 포르투갈어 · ru 러시아어 · vi 베트남어, 표에 없으면 코드 그대로)이고 표는 화면(`frontend/src/labels.ts`)과 같은 사본이다 — 서버와 화면이 따로 그려 한 벌로 둘 수 없다
4. 구간마다 `{L(start_sec)} {text}` 한 줄 — 줄바꿈 하나로 잇는다(옵시디언 기본 설정 · 노션에서 줄마다 나뉜다. 사용자가 실제 노트를 보고 그대로 두기로 했다, 2026-09-29)
5. `→ 문자열` (줄바꿈 `\n`, 끝에 줄바꿈 하나)

**출력** 마크다운 문자열. 노트 곁에 `{파일 이름} 스크립트.md`로 쓰인다([[#AnalysisService.export_to_file]])

**호출하는 것** [[#export.timecode]] · [[#export.link]]

**테스트 관점** 스냅샷 테스트: 자막 있는 50분 YouTube 결과 · 로컬 150분 결과 → 예상 문자열과 일치 · 로컬은 원본 줄에 링크 없음, 시각이 `h:mm:ss` · 출처 줄이 화면 8.1과 같다(`자막(수동) · 한국어` · `받아쓰기 whisper-1 · 한국어`)

---

#### export.gantt 한눈에 보기 — 타임라인

**시그니처** `def gantt(result: Result) -> str`

근거: [[VA-PRD-001#R11]] · [[VA-UI-002#UI-7]] 규칙(4.1 미리 보기의 블록) · [[VA-UI-001#UI-7]] 내용 순서(챕터 구간 · 파트 구역 · 인사이트 이정표) · [[VA-INFRA-001]] 3절(`timeline`이 아니라 `gantt`) · [[VA-UI-001]] 8장 미결(Mermaid 글자 규칙과 눈금 — 여기서 정한다)

**처리** — 순수 함수. `H(sec)` = `int(sec)`를 `HH:MM:SS`(두 자리씩)로
1. ```` ```mermaid ```` · `gantt` · `  dateFormat HH:mm:ss` · `  axisFormat %M:%S` — 1시간 이상 영상은 `%-H:%M:%S`(앱의 `h:mm:ss`와 같은 모양) · `  todayMarker off` — 시각에 날짜가 없어 막대가 모두 오늘에 놓이고 Mermaid는 지금 시각에 오늘 선을 긋는다. 자정 무렵에 열면 선이 막대를 가로지른다(코드 리뷰 카드 D1, Mermaid 11.17.2 실측)
2. 챕터 — if 파트 있음 → 파트마다 `  section {part.seq} {이름(part.title)}` 아래에 그 파트의 챕터 · else → `  section 챕터` 아래에 전부. 챕터마다 `  {seq 두 자리} {이름(title)} : {H(start)}, {H(end)}` — `end`는 다음 챕터의 시작, 마지막은 영상 길이. 길이가 0이면 `end = start + 1초`
   - 번호를 앞에 붙인다 — gantt는 줄 머리에서 키워드(`click` · `call` · `title` · `section` · `excludes` …) · 주석(`%%`) · 날짜를 이름보다 먼저 읽는다. 제목이 그것으로 시작하면 블록이 깨지거나 그 막대가 사라진다. 구역도 번호를 붙인다 — Mermaid가 구역을 이름으로 묶어 같은 제목의 파트 둘이나 '인사이트'라는 파트가 한 구역으로 섞인다(코드 리뷰 카드 D1, Mermaid 11.17.2 실측). 화면의 막대 칸 · 파트 띠 '{번호} {제목}'과 같은 모양이다
3. 인사이트 — `  section 인사이트` · 인사이트마다 `  {seq 두 자리} : milestone, {H(source_secs[0])}, 0s`
4. ```` ``` ````로 닫는다 · `→ 문자열`
- `이름(s)` — gantt가 구분자 · 주석으로 읽는 글자를 바꾼다: `:` → `∶`(U+2236) · `;` → `；` · `#` → `＃` · `%` → `％` · `` ` `` → `'` · 줄바꿈 · 캐리지 리턴 → 공백 · 앞뒤 공백을 뗀다 · 비면 챕터는 `챕터`, 파트는 `파트`

**테스트 관점** 42분 결과 → 와이어프레임 UI-7 4.1의 블록과 같다(스냅샷) · 제목의 `:`가 `∶`로 · 150분 결과 → 파트마다 번호 붙은 section, `axisFormat %-H:%M:%S`, 시각이 `01:05:26` 모양 · 마지막 챕터 끝이 영상 길이 · 인사이트 번호가 두 자리 · 이정표가 인사이트의 첫 출처 시각 · `todayMarker off`가 있다 · 제목이 `Click` · `Title` · `Section` · 날짜 · `5%`로 시작해도 줄이 번호로 시작한다 · 같은 제목의 파트 둘이 다른 구역 · 캐리지 리턴이 공백으로

---

#### export.mindmap 한눈에 보기 — 마인드맵

**시그니처** `def mindmap(result: Result) -> str`

근거: [[VA-PRD-001#R11]] · [[VA-UI-001#UI-7]] 내용 순서(한 줄 요약 → (파트 →) 챕터 → 요점) · [[VA-UI-001]] 7장 20(파트가 있으면 요점을 뺀다 — 화면과 노트가 같다) · [[VA-UI-002#UI-7]] 4.1

**처리** — 순수 함수. 들여쓰기 두 칸이 한 단계. `T` = [[#export.timecode]]
1. ```` ```mermaid ```` · `mindmap` · `  root({글(summary.one_liner)})`
2. if 파트 있음 → 파트마다 `    {T(part.start_sec)} {글(part.title)}`, 그 아래 챕터 `      {T(start_sec)} {글(title)}` — 요점은 넣지 않는다 · else → 챕터가 root 바로 아래(`    `), 요점이 그 아래(`      · {글(bullet)}`) — 요점 앞의 가운뎃점은 화면 마인드맵과 같고, 요점이 `mindmap` · `::icon` · `:::`로 시작해도 문법으로 읽히지 않는다
3. ```` ``` ````로 닫는다 · `→ 문자열`
- `글(s)` — mindmap이 모양 기호로 읽는 괄호를 전각으로: `(` `)` → `（` `）` · `[` `]` → `［` `］` · `{` `}` → `｛` `｝` · 모양 안에서 따옴표 문자열로 읽는 `"` → `＂`(한 줄 요약이 따옴표로 시작하면 블록이 깨진다) · 노드 글을 Markdown · HTML로 그릴 때 뜻이 생기는 `<` `>` → `＜` `＞` · `*` → `＊` · `_` → `＿` · `%` → `％` · `#` → `＃`(`Optional<User>`의 `<User>`가 지워지고 `__init__`이 굵게 된다) · `` ` `` → `'` · 줄바꿈 · 캐리지 리턴 → 공백(코드 리뷰 카드 D1, Mermaid 11.17.2 실측)

**테스트 관점** 42분 결과 → UI-7 4.1의 블록과 같다(스냅샷, 괄호가 전각, 요점 줄은 `· `로 시작) · 150분 결과 → root 아래 파트, 그 아래 챕터, 요점 줄이 없다, 시각이 `0:06:20` 모양 · 한 줄 요약에 `)`가 있어도 root가 닫히지 않는다 · 따옴표로 시작하는 한 줄 요약 · `<` `>` `*` `_` `%` `#`이 든 요점이 전각으로 · 캐리지 리턴이 공백으로

---

#### export.frame_name 장면 그림 파일 이름

**시그니처** `def frame_name(file_name: str, sec: float, duration_sec: int) -> str`

근거: [[VA-UI-002#UI-7]] 규칙(`{파일 이름} {시각}.jpg`, 쌍점은 하이픈) · [[VA-API-001#POST/api/videos/{id}/export]]

**처리** `→ f"{file_name} {timecode(sec, duration_sec).replace(':', '-')}.jpg"` — 쌍점을 파일 이름에 쓸 수 없는 곳이 있다. 챕터 시작 시각이라 한 노트 안에서 겹치지 않는다(같은 초의 챕터는 [[#AnalysisService.generate_chapters]]가 하나로 줄인다 — 이슈 #16). 노트의 그림 줄과 복사할 파일이 이 함수 하나를 쓴다

**테스트 관점** 50분 영상 591초 → `{이름} 09-51.jpg` · 150분 영상 3926초 → `{이름} 1-05-26.jpg`

---

#### export.infographic_name 인포그래픽 그림 파일 이름

**시그니처** `def infographic_name(file_name: str) -> str`

**처리** `→ f"{file_name} 인포그래픽.png"` — 노트의 그림 줄과 복사할 파일이 같은 이름을 쓰게 한곳에 둔다

**테스트 관점** `RAG 운영기` → `RAG 운영기 인포그래픽.png`

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

- [x] 미리 보기 · 파일 저장이 [[#AnalysisService.result_of]]로 구간까지 읽는다 — 노트에는 구간이 없어 3시간 영상(구간 약 5천)이면 부를 때마다 수십 ms가 더 든다. 결정(카드 D1 코드 리뷰): 그대로 둔다. 방법 · 체크박스를 바꿀 때만 부르고, 노트만 읽는 함수를 따로 두면 결과를 모으는 길이 둘이 된다

- [x] (반영: 클래스 명세 v10) **되먹임** — `clamp_secs`가 가장 가까운 구간 시각으로 보정하려면 `segments`를 받아야 한다. 클래스 명세 4.3의 `clamp_secs(secs, duration_sec)`에 인자 하나를 더한다([[VA-DOM-002#AnalysisService]]). 시그니처만 바뀌고 규칙은 그대로
- [x] 같은 제목의 영상 둘을 내보내면 파일이 서로 덮어쓴다(`filename_for`). 뒤에 `-{id}`를 붙일지 — 결정(사용자 2026-09-28): 붙이지 않는다. 제목만 쓰고 같은 이름이면 덮어쓴다 — 노트 앱에서 보기 좋은 이름을 두고, 저장 경로는 UI-7 2.1이 미리 보인다
- [x] 스크립트 토큰 수 세기 — 결정(카드 C): 어림을 실측으로 고쳐 `shared/tokens.py`에 둔다([[VA-MS-006#tokens.estimate]] — 줄마다 UTF-8 바이트 ÷ 4 + 8). 실측(카드 C, gpt-5-mini): 한국어 스크립트 세 영상에서 글자 ÷ 2는 실제의 절반 이하였다(0.37~0.5배) — 줄 앞에 붙는 시각 표기(`[mm:ss] ` 5토큰 안팎 · `[h:mm:ss] ` 8토큰 안팎)를 세지 않았고, 받아쓰기 스크립트는 줄이 많다(2시간 30분에 4,875줄). `tiktoken`은 쓰지 않는다
- [ ] 파트 제목 — 포트가 파트를 안 주면 첫 챕터 제목을 쓴다(`generate_chapters` 5번). 파트 제목만 따로 모델에 묻는 호출을 더할지
- [ ] 중간 요약을 재료로 한 최종 요약의 품질 — 챕터를 재료로 쓰는 [[VA-UC-001#UC-S4]] 1a2와 결과가 다를 수 있다. 품질을 보고 실행 순서(챕터 먼저)로 되돌릴지([[VA-DOM-002]] 5장 10)
- [x] 스크립트 · 질문 기록의 줄은 줄바꿈 하나로 잇는다 — 결정(사용자 2026-09-29, 카드 C 실제 노트): 그대로 둔다. 옵시디언(기본 설정) · 노션에서 줄마다 나뉜다. 엄격한 CommonMark(GitHub 미리 보기)에서만 한 문단으로 합쳐진다
- [x] 내보내기 스크립트 절의 크기 — 결정(사용자 2026-09-29, 카드 C 실측 — 2시간 30분 받아쓰기 영상의 노트가 5,022줄 · 206 KB): 스크립트는 별도 파일 `{파일 이름} 스크립트.md`로 쓰고, 노트는 `[[{파일 이름} 스크립트]]`로 가리킨다. 복사는 노트만([[VA-PRD-001#R10]] v6 · [[#export.build_script]])
- [x] 노트의 Mermaid 글자 규칙과 눈금([[VA-UI-001]] 8장 미결) — 결정: gantt는 `:` `;` `#`와 백틱을 바꾸고 1시간 이상이면 눈금 `%-H:%M:%S`, mindmap은 괄호 셋을 전각으로([[#export.gantt]] · [[#export.mindmap]]). 화면 설계 미결은 다음 UI-001 수정 때 닫는다
- [x] 긴 영상의 gantt 눈금(`%-H:%M:%S`)과 챕터 수십 개의 mindmap을 옵시디언이 읽을 만하게 그리는지 — 결정(사용자 2026-09-30, 카드 D1): 실제 노트 둘을 Mermaid 11로 노트 폭 700px에 그려 보았다(사용자 질문 「우리 사이트에서 보면 되는거 아니야?」에 따라 에이전트가 그렸다). gantt는 눈금이 겹치지 않는다 — Mermaid가 42분은 5분, 2시간 30분은 15분 간격을 고른다(눈금 간격 줄은 넣지 않는다). mindmap은 2시간 30분 영상(파트 5 · 챕터 27 · 요점 54)을 Mermaid 11로 노트 폭 700px에 그리면 노드가 겹쳐 읽히지 않았다(카드 D1) → 파트가 있으면 요점을 뺀다([[#export.mindmap]] 2번 — 화면과 같다, 32노드면 읽힌다). 42분(파트 없음, 요점 16)은 그대로 읽힌다
- [x] 인포그래픽 파일 이름 꼬리 때문에 `filename_for`의 바이트 한도를 238 → 235로 줄였다 — 반영: 카드 D3에서 코드와 테스트를 같이 고쳤다(`NAME_BYTES_MAX = 235`, 한글 제목은 78자까지)
