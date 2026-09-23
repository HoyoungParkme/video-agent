---
doc_id: VA-CODE-001
type: CODE
title: 구현 계획 — 슬라이스 카드와 커밋 기록
status: draft
upstream: [VA-SCN-001, VA-UC-001, VA-INFRA-001, VA-DOM-002, VA-DOM-003, VA-API-001, VA-UI-001, VA-UI-002, VA-MS-001, VA-MS-002, VA-MS-003, VA-MS-004, VA-MS-005, VA-MS-006, VA-MS-007]
---

# 구현 계획

## 0. 이 문서가 다루는 것

11단계 CODE. 싱크독 개발 규약 DEV-11~15대로 작업을 슬라이스 카드로 자르고, 카드마다 커밋을 기록한다. **에이전트는 카드 하나를 받아 카드 안 참조만 따라간다.** 카드에 없는 함수를 짜게 되면 카드가 틀린 것이다 — 카드를 고치고, 필요하면 MINISPEC을 고친다.

슬라이스는 시나리오([[VA-SCN-001]]) 순서다 — S1 YouTube 자막 영상이 첫 슬라이스(B1). 기반 A가 끝나야 B가 시작되고, B1이 끝나면 자막 있는 YouTube 하나를 넣어 요약 · 챕터 · 스크립트를 읽을 수 있다. 그 뒤 받아쓰기(B2) → 질문(B3) → 다시 열기 · 내보내기 · 삭제(B4) → 잘 안 되는 경우(B5) → 통합 · 배포(C).

**카드는 호출 그래프로 닫혀 있다.** 카드의 함수가 부르는 함수는 같은 카드에 있거나, 선행 카드에서 끝났거나, 카드의 `스텁` 행에 적혀 있다. 스텁은 둘뿐 — 빈 결과, 또는 `not-implemented`(501). 조용히 다르게 동작하는 스텁은 없다. 스텁을 해제한 카드가 완료란에 그 사실을 적는다. `not-implemented`는 [[VA-API-001]] 2장 에러 표에 없는 임시 종류다 — `core/errors.py`의 `NotImplementedYet`(`urn:va:not-implemented`, 501)이 내고, 파이프라인 안에서 나면 작업이 `unknown`으로 실패한다. 스텁이 모두 풀리는 B4에서 지운다.

**화면이 있는 카드는 사람이 브라우저에서 와이어프레임 요소 번호대로 눌러 본다**(DEV-14 일곱째). 에이전트는 `tsc` · `build` · API 테스트까지다.

**커밋 규격** — `code(슬라이스): 함수명 — 요약`. 함수 하나 = 커밋 하나, docstring 첫 줄 = MINISPEC 항목 ID. PR = 슬라이스 하나. **커밋 메시지와 PR 본문에 에이전트 표시(`Co-Authored-By` · 세션 링크 · 「Generated with」)를 넣지 않는다** — 제목과 본문만 쓴다(싱크독 규약 STD-001 1.10, 사용자 결정 2026-09-22).

**진행 상황**: 카드 7장 중 **A · B1 완료**(2026-09-23, PR #1 · #2). 다음은 B2 — 시작할 때 `main`을 `dev`에 머지해 명세를 맞추고 `feat/card-b2`를 만든다.

---

## 1. 슬라이스

#### A 기반

| 항목 | 내용 |
|---|---|
| 근거 | [[VA-INFRA-001]] 3 · 5 · 6 · 8절 · [[VA-INFRA-001#C6]] · [[VA-DOM-002]] 1장(폴더 구조) · [[VA-DOM-003]] · [[VA-MS-007]] · [[VA-MS-005]] · [[VA-MS-006]] 0장(프롬프트 파일 · 시각 표기) · [[VA-UI-001]] 3 · 4장(토큰 · 공통 틀) |
| 구현 | **시작할 때 먼저**: 텍스트 모델 단가(`gpt-5.4-mini` · `gpt-5.4`)와 Next.js · FastAPI · PostgreSQL 버전을 그날 값으로 고정한다(3장 5) · 저장소 루트 — `backend/` · `frontend/` · `Dockerfile` · `Dockerfile.web` · `docker-compose.yml`(api · web · db, inbox 읽기 전용 · data 쓰기 · **`.env` 파일 하나를 api에 읽기·쓰기** 마운트, [[VA-INFRA-001#C6]]) · `.env.example` · `.gitignore` · `.dockerignore` · `README.md` · `AGENTS.md`(+ `CLAUDE.md` 한 줄) · **backend**: `pyproject.toml`(FastAPI · SQLAlchemy 2 async · asyncpg · Alembic · openai · httpx · pydantic-settings, `uv`) · `app/main.py`(앱 조립 · lifespan · `/health`) · `core/config.py`(설정값 전부 — MS 문서들의 「설정값(첫 값)」 표. 키와 고른 모델은 두지 않고 `.env` 경로만, [[VA-MS-005]] 0장) · `core/db.py` · `core/errors.py`(problem+json 17종 → 예외 17개 + 핸들러 · 포괄 `internal`) · `domains/*/models.py` 11개 · `infra/errors.py` · `app/prompts/`(`summary.md` · `chapters.md` · `questions.md` · `answer.md` 첫 판 — [[VA-MS-006]] 0장 표의 자리 표시 · 반드시 들어갈 규칙 · 출력 형식을 지킨다 · `__init__.py`) · `shared/timecode.py` · **frontend**: Next.js App Router · `styles.css`([[VA-UI-001]] 3장 전사) · `next/font` 로컬 글꼴 · `components/Header` · `KeyBanner` · `Dialog` · `Toast` · `EmptyBox` · buttons · `api/client.ts`(problem+json → 예외) · `app/layout.tsx` |
| DB | Alembic `0001_initial` — 테이블 11개 + 인덱스 · 제약(부분 unique · 복합 FK · CHECK) 전부([[VA-DOM-003]] 3장). `analysis_jobs`의 `status`에 `queued`, `queued_at` 컬럼, 대기열 부분 인덱스까지 · `downgrade` |
| infra | [[VA-MS-007#ytdlp.info]] · [[VA-MS-007#ytdlp.captions]] · [[VA-MS-007#ytdlp.download_audio]] · [[VA-MS-007#ffmpeg.probe]] · [[VA-MS-007#ffmpeg.extract_audio]] · [[VA-MS-007#ffmpeg.silences]] · [[VA-MS-007#ffmpeg.cut]] · [[VA-MS-007#openai.client]] · [[VA-MS-007#openai.verify_key]] · [[VA-MS-007#openai.transcribe]] · [[VA-MS-007#openai.chat]] — 11개 |
| 설정 | [[VA-MS-005#SettingsService.get]] · [[VA-MS-005#SettingsService.set_key]] · [[VA-MS-005#SettingsService.set_models]] · [[VA-MS-005#SettingsService.check_stored_key]] · [[VA-MS-005#SettingsService.require_key]] · [[VA-MS-005#SettingsService.current_models]] · [[VA-MS-005#SettingsService.read_env]] · [[VA-MS-005#SettingsService.write_env]] · [[VA-MS-005#SettingsService.api_key]] — 9개 · `core/settings_router.py`. `api_key`를 부르는 `client_for`는 어댑터를 조립하는 B1에서 `main.py`가 만든다 |
| 공용 조각 | [[VA-MS-006#prompts.render]] · [[VA-MS-006#timecode.label]] · [[VA-MS-006#timecode.parse]] — 3개. 어댑터가 B1 · B3에서, 내보내기가 B4에서 쓴다 |
| API | [[VA-API-001#GET/api/settings]] · [[VA-API-001#POST/api/settings/key]] · [[VA-API-001#PUT/api/settings/models]] |
| 화면 | [[VA-UI-002#UI-5]] 설정(키 카드 · 모델 카드 · 폴더 · 데이터 표) · 공통 1.1 헤더 · 1.4 키 없음 배너(문구 셋 — 키 없음 · 확인 실패 · 연결을 확인하지 못함. 연결 문구일 때는 [키 넣으러 가기]가 없고 버튼을 막지 않는다) · [[VA-UI-002#UI-1]]의 첫 실행 상태(배너 + 막힌 버튼 + 빈 상태 상자 — 입력 카드 동작은 B1 · B2) |
| 테스트 | 마이그레이션 up/down · `infra`는 가짜 실행 파일 · 가짜 OpenAI 클라이언트로 11개 테스트 관점 · 설정 9개 테스트 관점(`.env` 제자리 쓰기 — 다른 줄 · 주석 보존, 연결 실패 뒤 한 번 다시 확인) · 공용 조각 3개 테스트 관점(프롬프트 파일 넷 검사 포함) · `GET/POST/PUT /api/settings*` · 프런트 `tsc` · `build` · **E2E**: 빈 상태로 앱을 열면 배너 → 설정에서 키 저장(가짜 OpenAI) → 배너 사라짐([[VA-SCN-001#S6]] 1번) |
| 스텁 | `main.py` lifespan은 키 확인만 한다. 죽은 작업 되돌리기(`fail_orphans`)와 대기열 워커는 B1에서 넣는다 · 도메인 라우터 넷은 아직 없다(B1부터) |
| 선행 | 없음 |
| 완료 | 2026-09-23(KST) · 브랜치 `feat/card-a` → `dev` squash `80941d3`(PR #1, 커밋 63개 — 함수 하나 = 커밋 하나, 단계마다 그 함수의 테스트가 통과한 채로) · 테스트: pytest 147(api 이미지 안 148 — 진짜 ffmpeg 포함) · E2E 7 · `check_ui --screens UI-5` 21/21 · `check_code` 카드 A 22/23 — `prompts.render`는 도구가 `**values`를 읽지 않아 난 불일치(싱크독 이슈로 넘김, 도구를 고치면 23/23) · 화면 확인: 사용자 지시로 에이전트가 Playwright MCP로 UI-1 첫 실행 · UI-5와 키 상태 넷(없음 · 확인됨 · 인증 실패 · 연결 실패)을 요소 번호대로(PR #1 댓글) · 스텁 그대로: `fail_orphans` · 대기열 워커 · 도메인 라우터 넷은 B1 · 되먹임(모두 반영): [[VA-INFRA-001]] v5~v7(deno · inbox 위치 한 값 · Host 확인) · [[VA-DOM-002]] v13~v16 · [[VA-API-001]] v4(`network`에 OpenAI 일시 오류) · [[VA-MS-005]] v5 · v6(`ChosenModels` · `.env` 읽기) · [[VA-MS-007]] v4(키 확인 실패 가르기 · 자식 프로세스) · [[VA-UI-002]] v5 · 코드 리뷰(`/code-review`) 반영 — 남긴 것은 [[VA-MS-005]] 3장(손으로 바꾼 키의 지문, B1) · 라우팅 404 · 405의 problem+json · Next 프록시 30초(B3 · B4) |

#### B1 YouTube 링크로 첫 분석 — 자막 있는 영상

| 항목 | 내용 |
|---|---|
| 근거 | [[VA-SCN-001#S1]] · [[VA-SCN-001#S3]] · [[VA-UC-001#UC-H1]] · [[VA-UC-001#UC-H0]] · [[VA-UC-001#UC-H3]] · [[VA-UC-001#UC-S1]] · [[VA-UC-001#UC-S2]] 1~2번 · [[VA-UC-001#UC-S4]] · [[VA-UC-001#UC-S5]] · [[VA-UC-001#UC-S6]] · [[VA-SEQ-001#SEQ-1]] · [[VA-SEQ-001#SEQ-2]] · [[VA-SEQ-001#SEQ-3]] · [[VA-SEQ-001#SEQ-5]] · [[VA-SEQ-001#SEQ-7]] · [[VA-SEQ-001#SEQ-8]] · [[VA-SEQ-001#SEQ-13]] · [[VA-SEQ-001#SEQ-14]] |
| 구현 함수 | **video** [[VA-MS-001#VideoService.register]] · [[VA-MS-001#VideoService.list]] · [[VA-MS-001#VideoService.get]] · [[VA-MS-001#VideoService.info_of]](YouTube 갈래만) · [[VA-MS-001#VideoService.to_dto]] · **job** [[VA-MS-002#JobService.estimate]] · [[VA-MS-002#JobService.start]] · [[VA-MS-002#JobService.progress]] · [[VA-MS-002#JobService.latest]] · [[VA-MS-002#JobService.latest_by_videos]] · [[VA-MS-002#JobService.mark_stage]] · [[VA-MS-002#JobService.finish]] · [[VA-MS-002#JobService.fail]] · [[VA-MS-002#JobService.stages_for]] · [[VA-MS-002#JobService.remaining_sec]](조각 없는 갈래만) · [[VA-MS-002#JobService.to_job]] · [[VA-MS-002#JobService.fail_orphans]] · [[VA-MS-002#JobService.claim_next]] · [[VA-MS-002#JobService.wake]] · [[VA-MS-002#JobService.wait_for_work]] · [[VA-MS-002#JobService.queue_position]] · [[VA-MS-002#pipeline.worker]] · [[VA-MS-002#pipeline.run]](자막 갈래) · [[VA-MS-002#pipeline.error_kind]] · **analysis** [[VA-MS-003#AnalysisService.save_transcript]] · [[VA-MS-003#AnalysisService.generate_summary]] · [[VA-MS-003#AnalysisService.generate_chapters]](파트 없는 갈래) · [[VA-MS-003#AnalysisService.generate_questions]] · [[VA-MS-003#AnalysisService.result_of]] · [[VA-MS-003#AnalysisService.segments_of]] · [[VA-MS-003#AnalysisService.chapters_of]] · [[VA-MS-003#AnalysisService.clamp_secs]] · **chat** [[VA-MS-004#ChatService.count_by_videos]] · **adapters** [[VA-MS-006#youtube_info.info]] · [[VA-MS-006#audio_source.captions]] · [[VA-MS-006#summarizer_openai.summary]] · [[VA-MS-006#summarizer_openai.chapters]] · [[VA-MS-006#summarizer_openai.questions]] · **shared** [[VA-MS-006#captions.pick]](자막 고르기 — 실제 yt-dlp 목록에서 찾은 되먹임, 두 어댑터가 같이 쓴다) — 39개 · `main.py` lifespan이 `fail_orphans`를 부른 **뒤에** 워커를 띄운다([[VA-SEQ-001#SEQ-13]]) |
| API | [[VA-API-001#POST/api/videos]] · [[VA-API-001#GET/api/videos]] · [[VA-API-001#GET/api/videos/{id}]] · [[VA-API-001#POST/api/videos/{id}/job]] · [[VA-API-001#GET/api/videos/{id}/job]] · [[VA-API-001#GET/api/videos/{id}/result]] |
| 화면 | [[VA-UI-002#UI-1]] 「YouTube 링크」 카드 · 「분석한 영상」 목록(완료 · 진행 중 · 대기 중 행) · [[VA-UI-002#UI-2]] 자막 있음 판 · 대기 안내(6.1) · 자막 없는 영상은 시작 불가 판(7)에 '아직 지원하지 않음'(사용자 결정 2026-09-23 — B2가 받아쓰기 필요 판으로 바꾸고, B5가 이유 넷을 더한다) · [[VA-UI-002#UI-3]] 요약 중(단계 4개, 1초 폴링, 끝나면 UI-4로) · 대기 상태 · [[VA-UI-002#UI-4]] 왼쪽 본문 전부 + [스크립트] 탭 + 시각 이동(공통 1.3) · 추천 질문 알약은 보이되 누르면 아무 일도 없다(B3) · 공통 1.5 짧은 알림 '이미 분석한 영상입니다'(B4에서 옮김 — E2E S1의 「같은 주소 다시」가 본다) |
| 테스트 | 구현 함수의 테스트 관점 전부 · 가짜 yt-dlp(고정 JSON · VTT) · 가짜 OpenAI(고정 JSON 응답) · **E2E S1**: 주소 넣기 → 사전 안내(약 1분 · 요약 비용) → 시작 → 폴링이 `done` → 결과(한 줄 요약 · 인사이트 · 챕터 · 스크립트 · 시각 이동) · 같은 주소 다시 → 이미 분석한 영상 · **E2E 대기열**([[VA-UC-001#UC-H0]] 3b): 첫 영상이 도는 동안 둘째를 시작 → 사전 안내에 대기 안내 → UI-3 대기 상태 · 목록 '대기 중 · 1번째' → 첫 영상이 끝나면 둘째가 저절로 진행 · 서버 재시작 → `running`이 `failed`로, `queued`는 이어서 돈다(Playwright가 띄운 api는 죽였다 살리기 어려워 이 갈래는 pytest가 실제 lifespan을 두 번 돌려 본다) |
| 스텁 | [[VA-MS-002#pipeline.transcribe_stage]] · `pipeline.run`의 download(음성) · extract · transcribe 갈래 → `! not-implemented`(자막 없는 YouTube는 화면이 시작 불가 판 '아직 지원하지 않음'으로 막는다. B2 해제) · `JobService.remaining_sec`의 조각 갈래 → `! not-implemented`(받아쓰기 작업이 없어 닿지 않는다. B2) · `AnalysisService.generate_summary`의 구간 갈래 · `generate_chapters`의 파트 갈래 → `! not-implemented`(60분 넘는 자막 영상은 챕터 단계에서 실패로 멈춘다. B2 해제) · `VideoService.info_of`의 로컬 갈래 → `! not-implemented`(B2) · `POST /job/retry` → 501(B2) · `DELETE /videos/{id}` → 501(B4) · `GET /inbox` → `files: []`(B2) · `GET/POST /chat` → `[]` · 501(B3) · `GET/POST /export` → 501(B4) · `JobService.cancel` → 아무것도 안 함(B4) · `JobService.retry` → 501(B2) · [[VA-MS-002#pipeline.resume]] → `! not-implemented`(B2) — 워커가 부르지만, 다시 시도가 501이라 B1에서는 `stage`가 `pending`이 아닌 작업이 대기열에 들어오지 않는다 |
| 선행 | A |
| 완료 | 2026-09-23(KST) · 브랜치 `feat/card-b1` → `dev` squash `1de5520`(PR #2, 커밋 66개 — 함수 하나 = 커밋 하나, 단계마다 그 함수의 테스트가 통과한 채로, 코드 리뷰 반영 9개 포함) · 테스트: pytest 293(api 이미지 안 294 — 진짜 ffmpeg 포함) · E2E 11(카드 A 7 + S1 · 자막 없는 영상의 시작 불가 판 · 대기열 · 첫 요청이 끊겨도 다시 받기) · 서버 재시작은 pytest가 실제 lifespan을 두 번 돌려 본다 · `check_code` B1 39/39 · 스텁 넷(`transcribe_stage` · `resume` · `retry` · `cancel`)도 일치 · `check_ui` UI-2 26/26 · UI-1 22/35 · UI-3 14/27 · UI-4 20/48 — 모자란 것은 뒤 카드 몫과 도구 한계(목록 첫 항목에만 붙인 `data-el={i === 0 ? … : undefined}`를 못 읽음 · 레이아웃이 그리는 배너 번호), 싱크독 이슈로 넘김. 도구를 고친 시제품으로 UI-1 29/35 · UI-3 19/27 · UI-4 25/48 · 화면 확인: 사용자 지시로 에이전트가 docker + Playwright MCP로 S1 · 대기열 · 시작 불가 · 다시 넣기 · 주소로 바로 열기 · 서버 재시작 · 리뷰 뒤 UI-1 실패 행을, 진짜 yt-dlp로 공개 영상 하나를(PR #2 댓글) · 스텁 해제: 카드 A의 `fail_orphans` · 대기열 워커 · 도메인 라우터 넷. 새 스텁은 위 스텁 행 그대로 · 되먹임(모두 반영): [[VA-DOM-002]] v17~v19 · [[VA-DOM-003]] v5(영상 하나에 기다리는 · 도는 작업 하나, 마이그레이션 `0002`) · [[VA-UI-002]] v6~v8 · [[VA-SEQ-001]] v4 · [[VA-MS-001]] v2 · v3 · [[VA-MS-002]] v5~v7 · [[VA-MS-003]] v3 · [[VA-MS-006]] v4~v7 · [[VA-MS-007]] v5 · 이 문서 v5 · v6 · 코드 리뷰(`/code-review`) 10건 — 고친 것 다섯(같은 영상 동시 시작 · 자막 겹침을 글자로 떼던 것 · UI-1 '시작하기 전에 멈춤' · UI-3 · UI-4가 빈 화면으로 멈추던 것 · 짧은 알림의 요소 번호), 남긴 것: 파이프라인 안 yt-dlp 실패의 이유 한 줄([[VA-MS-006]] 3장 미결, B2) · `start`의 양보 뒤 다시 읽기(명세의 「보장은 아니다」) · `GET …/job`이 영상을 먼저 읽는 것(영상 없음과 작업 없음을 가른다) · 상수 두 벌(명세가 두 곳에 정한 규칙) |

#### B2 로컬 파일 — 2시간 30분 워크숍 받아쓰기

| 항목 | 내용 |
|---|---|
| 근거 | [[VA-SCN-001#S2]] · [[VA-SCN-001#S6]] 4번과 변형(인터넷 끊김) · [[VA-UC-001#UC-H2]] · [[VA-UC-001#UC-S2]] 확장 1a · 1b · 1c · [[VA-UC-001#UC-S3]] · [[VA-UC-001#UC-S4]] 1a · 2a · [[VA-UC-001#UC-S6]] 2번, 1a · [[VA-SEQ-001#SEQ-4]] · [[VA-SEQ-001#SEQ-6]] · [[VA-SEQ-001#SEQ-13]] · [[VA-INFRA-001#C2]] · [[VA-INFRA-001#C4]] |
| 구현 함수 | **video** [[VA-MS-001#VideoService.list_inbox]] · `VideoService.info_of` 로컬 갈래(스텁 해제) · **job** [[VA-MS-002#JobService.retry]] · [[VA-MS-002#JobService.plan_chunks]] · [[VA-MS-002#JobService.mark_chunk]] · `JobService.remaining_sec` 조각 갈래 · [[VA-MS-002#pipeline.resume]] · [[VA-MS-002#pipeline.transcribe_stage]] · `pipeline.run`의 download(음성) · extract · transcribe 갈래 · **analysis** `AnalysisService.generate_chapters`의 파트 갈래 · `generate_summary`의 구간 처리 갈래 · **adapters** [[VA-MS-006#media_probe.probe]] · [[VA-MS-006#audio_source.download_audio]] · [[VA-MS-006#audio_source.extract_audio]] · [[VA-MS-006#audio_split.split]] · [[VA-MS-006#stt_openai.transcribe]] — 새 함수 11개 + 갈래 해제 5곳 |
| API | [[VA-API-001#GET/api/inbox]] · [[VA-API-001#POST/api/videos/{id}/job/retry]] · `POST /api/videos`의 `local` 갈래 · `GET …/job`의 `chunks` |
| 화면 | [[VA-UI-002#UI-1]] 「내 파일」 카드(inbox 목록 · 선택 · 빈 안내) · 실패 행 · [[VA-UI-002#UI-2]] 받아쓰기 필요 판(조각 수 · 동시 수 · 줄별 비용, YouTube 자막 없음 · 로컬 음성 변형 — B1의 '아직 지원하지 않음' 판을 바꾼다) · [[VA-UI-002#UI-3]] 받아쓰기 중(조각 격자 · 범례 · 남은 시간) · 실패 상태(실패 알림 · 다시 시도 · 목록으로 — 알림의 이유 한 줄은 어댑터가 만든 한국어여야 한다. [[VA-MS-006]] 3장 미결 「파이프라인 안에서 난 yt-dlp 실패의 이유 한 줄」, B1 코드 리뷰) · 받아쓰기 아닌 단계 실패 · [[VA-UI-002#UI-4]] 파트 카드(펴고 접기) · `h:mm:ss` 표기 · 받아쓰기 메타 |
| 테스트 | 구현 함수의 테스트 관점 전부 · 가짜 ffmpeg(고정 무음 목록 · 잘린 파일) · 가짜 STT(조각 하나를 세 번 실패시키는 갈래) · **E2E S2**: inbox 파일 고르기 → 받아쓰기 필요 판(15조각 · 3동시 · $0.9) → 받아쓰기 격자가 늘어남 → 파트로 묶인 챕터 · **E2E S6 4번**: 16번 조각 실패 → 실패 알림 → 다시 시도 → 1~15번은 다시 보내지 않고 이어감 · 다른 영상이 도는 동안 다시 시도 → 대기열 끝에서 기다렸다 이어감 · 받아쓰기 도중 서버 재시작 → `failed`, 다시 시도로 이어감 |
| 스텁 | B1의 스텁 중 `transcribe_stage` · `run`의 세 갈래 · `remaining_sec` 조각 갈래 · `generate_summary` 구간 갈래 · `generate_chapters` 파트 갈래 · `info_of` 로컬 · `retry` · `resume` · `GET /inbox`를 해제. 나머지(`DELETE` · `chat` · `export` · `cancel`)는 그대로 |
| 선행 | B1 |
| 완료 | — |

#### B3 영상에 질문하기

| 항목 | 내용 |
|---|---|
| 근거 | [[VA-SCN-001#S4]] · [[VA-UC-001#UC-H4]] · [[VA-SEQ-001#SEQ-9]] · [[VA-PRD-001#R6]] · [[VA-PRD-001#R9]] |
| 구현 함수 | [[VA-MS-004#ChatService.history]] · [[VA-MS-004#ChatService.ask]] · [[VA-MS-004#ChatService.context_for]] · [[VA-MS-006#answerer_openai.answer]] — 4개 |
| API | [[VA-API-001#GET/api/videos/{id}/chat]] · [[VA-API-001#POST/api/videos/{id}/chat]] |
| 화면 | [[VA-UI-002#UI-4]] [질문하기] 탭 전부 — 대화 목록 · 빈 상태 상자 · 질문 턴 · 근거 칩(시각 이동) · '영상에 없는 내용' · 답 대기 · 답변 실패 + 다시 시도 · 입력 영역(추천 칩 · 입력칸 · 보내기 · 전송 안내 · 키 없음 안내) · 추천 질문 알약 → 바로 전송 · 질문 수 배지 |
| 테스트 | 구현 함수의 테스트 관점 전부 · 가짜 answerer(근거 있음 · 없음 · 실패 세 갈래) · **E2E S4**: 추천 질문 → 근거 칩 답 → 이어지는 질문('그거 성능은?')이 맥락으로 답함 → 영상에 없는 질문 → 배지 → 다시 열어도 기록이 남음 · 3시간 스크립트(가짜)에서 챕터로 맥락을 고른다 |
| 스텁 | B1의 `chat` 스텁 해제. `DELETE` · `export` · `cancel`은 그대로 |
| 선행 | B2 |
| 완료 | — |

#### B4 며칠 뒤 다시 열어 내보내고 지운다

| 항목 | 내용 |
|---|---|
| 근거 | [[VA-SCN-001#S5]] · [[VA-UC-001#UC-H5]] · [[VA-UC-001#UC-H6]] · [[VA-UC-001#UC-H7]] · [[VA-SEQ-001#SEQ-10]] · [[VA-SEQ-001#SEQ-11]] · [[VA-PRD-001#R7]] · [[VA-PRD-001#R10]] |
| 구현 함수 | [[VA-MS-003#AnalysisService.export_markdown]] · [[VA-MS-003#AnalysisService.export_to_file]] · [[VA-MS-003#AnalysisService.filename_for]] · [[VA-MS-003#export.build]] · [[VA-MS-003#export.timecode]] · [[VA-MS-003#export.link]] · [[VA-MS-001#VideoService.delete]] · [[VA-MS-002#JobService.cancel]] — 8개 · 삭제 라우터는 `VideoService.delete` **뒤에** [[VA-MS-002#JobService.wake]]를 부른다([[VA-SEQ-001#SEQ-11]]) · `export.timecode`는 [[VA-MS-006#timecode.label]]을 부른다([[VA-MS-006]] 3장 되먹임) |
| API | [[VA-API-001#GET/api/videos/{id}/export]] · [[VA-API-001#POST/api/videos/{id}/export]] · [[VA-API-001#DELETE/api/videos/{id}]] |
| 화면 | [[VA-UI-002#UI-7]] 내보내기(방법 둘 · 체크박스 · 미리 보기 · 실패 한 줄) · [[VA-UI-002#UI-6]] 삭제 확인(지워지는 것 · 남는 것 · 진행 중 영상 · 실패 한 줄) · [[VA-UI-002#UI-4]] 머리의 [내보내기] · 휴지통 · 짧은 알림(공통 1.5 — 내보내기 완료. '이미 분석한 영상입니다'는 B1에서 했다) · [[VA-UI-002#UI-1]] 행 휴지통 · 삭제 뒤 초점 |
| 테스트 | 구현 함수의 테스트 관점 전부 · `export.build` 스냅샷 둘(YouTube 자막 50분 · 로컬 파트 150분) · **E2E S5**: 며칠 뒤(시각을 흘려) 목록에서 열기 → 질문 → 파일로 저장(`data/export/…md` 내용 확인) → 복사(markdown 전체) → 삭제 → 목록에서 빠짐 → 같은 주소 다시 넣으면 처음부터 · 진행 중 영상 삭제 → 태스크가 취소되고 임시 폴더가 없고, 기다리던 다음 영상이 시작된다 · 대기 중 영상 삭제 → 대기열에서 빠지고 뒤 영상의 차례가 당겨진다 |
| 스텁 | 남은 스텁 셋(`DELETE` · `export` · `cancel`) 전부 해제. 이 카드 뒤에 스텁이 없다 |
| 선행 | B3 |
| 완료 | — |

#### B5 잘 안 되는 경우들

| 항목 | 내용 |
|---|---|
| 근거 | [[VA-SCN-001#S6]] 전부 · [[VA-UC-001#UC-H1]] 1a · 2a · [[VA-UC-001#UC-H2]] 1a · 2a · [[VA-UC-001#UC-H8]] 3a · [[VA-UC-001#UC-S1]] 1a · 2a · [[VA-UI-001]] 4.5 안내 · 오류 표시 · [[VA-UI-002]] 1.4 · 1.6 · 1.8 |
| 구현 함수 | 새 함수 없음. B1~B4 함수의 **오류 갈래**를 화면까지 잇는다 — `url-invalid` · `source-unavailable` · `video-too-long` · `no-audio-track` · `unsupported-file` · `path-outside-inbox` · `key-missing` · `key-invalid`(분석 버튼에서. 이유가 `network`면 막지 않고 누를 때 다시 확인) · `job-exists` · `result-not-ready`(주소로 바로 들어옴 → UI-3 · UI-1로) · `llm-unavailable`(키 저장 · 질문) |
| API | 새 엔드포인트 없음. [[VA-API-001]] 2장 에러 표 17종이 전부 화면에 닿는지 |
| 화면 | [[VA-UI-002#UI-1]] 입력 오류 한 줄 · 키 확인 실패 배너 문구 · 연결을 확인하지 못함 배너(버튼을 막지 않는다) · 막힌 버튼 → UI-5 · 대기 표시 · [[VA-UI-002#UI-2]] 시작 불가 판 넷(정보 조회 실패 · 3시간 초과 · 음성 없음 · 파일 아님) · [[VA-UI-002#UI-3]] · [[VA-UI-002#UI-4]] 키 없음 배너 · 주소로 바로 들어왔을 때 넘김(UI-3 ↔ UI-4 ↔ UI-1) · [[VA-UI-002#UI-5]] 확인 실패 · 키 없음 상태 |
| 테스트 | 에러 17종마다 API 테스트 하나(problem+json 모양) · **E2E S6**: 키 없이 분석 → 배너 · 비공개 영상 → 시작 불가 판 · 4시간 영상 → 길이와 함께 시작 불가 · 받아쓰기 도중 실패 → 다시 시도(B2와 겹치면 생략) · 인터넷 끊김(가짜 네트워크 예외) → 연결 문구 배너, 분석 버튼은 켜져 있음 → 네트워크가 돌아온 뒤 누르면 다시 확인해 통과 |
| 스텁 | 없음 |
| 선행 | B4 |
| 완료 | — |

#### C 통합·배포

| 항목 | 내용 |
|---|---|
| 근거 | [[VA-INFRA-001#C8]] · [[VA-INFRA-001]] 8절 · [[VA-PRD-001#N4]] · [[VA-PRD-001#N1]] · [[VA-PRD-001#N3]] |
| 구현 | `docker compose up -d`로 web · api · db 셋이 뜬다 · 이미지에 ffmpeg · yt-dlp · `.env.example` → `.env` 복사만으로 시작(키는 비워 두고 화면에서 넣어도 된다 — 앱이 `.env`에 쓴다) · `README.md`(설치 · inbox 넣는 법 · 밖으로 나가는 데이터 표 [[VA-UI-002#UI-5]] 5.1과 같은 내용) · `AGENTS.md`(명세 위치 · 규약 · 카드 순서) · 진짜 키로 **실제 영상** 셋 — 자막 있는 YouTube 50분 · 자막 없는 YouTube · 로컬 mp4 2시간 30분 · 시간당 3분 목표 측정([[VA-PRD-001#N1]]) · 설정 첫 값 여섯([[VA-MS-002]] 0장) 조정 |
| 테스트 | 컨테이너 안에서 pytest 전부 · 세 영상의 실제 결과를 사람이 읽고 품질 판단(인사이트 시각이 맞는지, 챕터 경계, 답의 근거) · `check_code.py`(MINISPEC ↔ 코드) 전 문서 0 불일치 · `check_ui.py`(와이어프레임 ↔ 화면 요소) 화면 7개 |
| 선행 | B5 |
| 완료 | — |

---

## 2. 통합 테스트 시나리오

| 시나리오 | 슬라이스 | 검증하는 것 |
|---|---|---|
| [[VA-SCN-001#S1]] YouTube 링크로 첫 분석 | B1 | 주소 → 사전 안내 → 4단계 → 결과. 1분 안. OpenAI 받아쓰기 호출 0회 |
| [[VA-SCN-001#S2]] 로컬 파일 2시간 30분 | B2 | inbox → 15조각 · 3동시 → 격자 → 파트 묶음. 조각 파일이 지워짐. 다른 영상이 도는 동안 시작하면 차례를 기다리는 변형은 B1 |
| [[VA-SCN-001#S3]] 챕터 · 인사이트로 구간 찾기 | B1 | 시각 칩 · 챕터 카드 · 구간 줄 어디를 눌러도 같은 이동. 파트 안 챕터도(B2) |
| [[VA-SCN-001#S4]] 영상에 질문하기 | B3 | 근거 칩 · 이어지는 질문 · 없는 내용 · 기록 보존 |
| [[VA-SCN-001#S5]] 다시 열기 · 내보내기 · 삭제 | B4 | 목록에서 열기 · 파일 저장 · 복사 · 삭제 · 다시 넣기 |
| [[VA-SCN-001#S6]] 잘 안 되는 경우들 | A · B2 · B5 | 키 없음 · 비공개 · 4시간 · 도중 실패 · 인터넷 끊김(연결 문구, 버튼은 막지 않음). 프로그램이 죽지 않는다 |

E2E는 가짜 yt-dlp · ffmpeg · OpenAI로 돈다(C에서만 진짜). 테스트 DB는 이름에 `test`가 든 것만 — 아니면 시작하지 않는다(DEV-14).

---

## 3. CODE 단계 전 결정

코드를 시작하기 전에 정리할 것. 카드 A를 받는 에이전트가 이것부터 본다. 2~7은 사용자가 2026-09-21에 정했다.

| # | 무엇 | 결정 | 반영한 곳 |
|---|---|---|---|
| 1 | **상위 문서 갱신 요청 정리** — 화면 설계 8장의 「상위 문서 갱신 요청」 16건과 그 뒤 되먹임을 위 문서부터 한 문서씩 반영 | 끝났다(2026-09-23). 열린 되먹임이 없다 | PRD v5 · SCN v3 · UC v2 · INFRA v3 · 도메인 모델 v3 · 클래스 명세 v12 · ERD v4 · 화면 설계 v6 · 와이어프레임 v4 · API v3 · 시퀀스 v3 · [[VA-MS-002]] v3 · [[VA-MS-003]] v2 · [[VA-MS-004]] v2 · [[VA-MS-005]] v3 · [[VA-MS-006]] v3 · [[VA-MS-007]] v2 |
| 2 | **키 저장 위치** | `.env` 파일 하나. 화면에서 넣은 키도 앱이 그 줄을 제자리에서 고친다(바인드 마운트라 rename 불가). `data/settings.json`은 쓰지 않는다 | [[VA-INFRA-001#C6]] · [[VA-MS-005]] 0장 |
| 3 | **동시 분석** | 대기열. 도는 분석은 하나이고 나머지는 `queued`로 차례를 기다린다. 워커 하나가 꺼내 돌린다. `another-job-running`은 없앴다 | [[VA-API-001]] 5장 8 · [[VA-MS-002]] · [[VA-SEQ-001#SEQ-14]] |
| 4 | **결과 화면의 YouTube 시점 링크** | 두지 않는다. 링크는 내보낸 마크다운에만 | [[VA-UC-001#UC-H3]] 6a · [[VA-UI-001]] 8장 |
| 5 | **텍스트 모델 단가와 프레임워크 버전** | 카드 A를 시작할 때 그날 값으로 고정했다(2026-09-23) | [[VA-INFRA-001]] 3절 버전 표 · [[VA-MS-005]] 0장 단가 |
| 6 | **프롬프트 자리** | `backend/app/prompts/*.md` 파일 넷. 명세는 자리 표시 · 반드시 들어갈 규칙 · 출력 형식만 정한다 | [[VA-MS-006]] 0장 · [[VA-DOM-002]] 1장 |
| 7 | **네트워크로 키 확인이 실패했을 때** | 배너 문구를 '연결을 확인하지 못했어요 — …'로 가르고 [키 넣으러 가기]를 뺀다. 버튼은 막지 않고, 누를 때 서버가 한 번 다시 확인한다 | [[VA-UI-002]] 1.4 · [[VA-API-001]] 5장 11 · [[VA-MS-005#SettingsService.require_key]] |

일곱 모두 끝났다. 5번은 카드 A 첫 작업으로 닫았다.

---

## 4. 커밋·PR 목록

슬라이스 카드의 `완료` 행에 기록한다 — 날짜(KST) · 브랜치 · 커밋 범위 · PR · 테스트 수 · `check_code.py` 결과 · 스텁 해제 · 되먹임.

| 카드 | 날짜(KST) | PR | dev squash | 커밋 |
|---|---|---|---|---|
| A | 2026-09-23 | #1 (`feat/card-a` → `dev`) | `80941d3` | 63 |
| B1 | 2026-09-23 | #2 (`feat/card-b1` → `dev`) | `1de5520` | 66 |

---

## 5. 미결사항

- [x] `check_code.py` · `check_ui.py`는 싱크독 저장소의 도구다 — 결정(카드 A): 사본을 두지 않고 싱크독 것을 경로로 부른다(`AGENTS.md` 「검사」). 카드 A에서 찾은 도구 문제 둘(`check_code`가 `**values`를 못 읽음 · `check_tokens`가 VA의 3.3 형식에서 멈춤)과 B1에서 찾은 하나(`check_ui`가 목록 첫 항목에만 붙인 식 `data-el`을 못 읽음 · 레이아웃이 그리는 배너 번호)는 싱크독 이슈로 넘겼다
- [x] 개발 중 프롬프트 고치기 — 결정(카드 A): 개발은 호스트에서 돈다(`uv run uvicorn --reload` · `npm run dev`), DB만 compose(`docker-compose.dev.yml`, 5433). [[VA-MS-006#prompts.render]]가 부를 때마다 파일을 읽으므로 고치면 바로 쓰인다. 이미지에 구운 프롬프트는 다시 빌드한다
- [x] 프런트 E2E 도구 — 결정(카드 A): Playwright(`frontend/e2e/`). 가짜 OpenAI · api · web을 스스로 띄우고 와이어프레임 요소 번호(`data-el`)로 누른다. 화면 확인(DEV-14 일곱째)은 사람 몫이지만 카드 A는 사용자 지시로 에이전트가 Playwright MCP로 했다
- [ ] 진짜 영상으로 하는 C 카드의 품질 판단 기준 — 인사이트 시각 오차 허용(±10초?), 챕터 수 범위. 사용자가 세 영상을 보고 정한다
- [x] B1이 끝난 시점에 자막 없는 YouTube를 넣으면 시작 불가 판에 '아직 지원하지 않음'이 뜬다(스텁). B2 전까지 그대로 둘지, B1에서 받아쓰기 필요 판까지만 열고 시작을 막을지 — 결정(사용자, 2026-09-23): 그대로 둔다. 받아쓰기 필요 판은 B2에서 그린다
