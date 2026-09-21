---
doc_id: VA-MS-001
type: MS
title: MINISPEC — VideoService
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-DOM-003, VA-UC-001]
---

# MINISPEC — VideoService

## 0. 이 문서가 다루는 것

`domains/video/service.py`의 함수 7개. 클래스 명세 [[VA-DOM-002#VideoService]]의 시그니처를 함수 내부까지 내린 것. **MS 문서 하나 = 클래스 명세 4장 절 하나 = 코드 파일 하나** — 이 파일을 짤 때 이 문서를 본다. 포트 · 어댑터(`youtube_info` · `media_probe`)는 4.6 · 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10 — 시그니처 · 근거 · 입력 · 처리 · 출력 · 예외 · 호출하는 것 · 테스트 관점, 분기는 `if 조건 → 결과`, 간략형 허용. 내부 타입(`SourceInfo` 등)은 [[VA-DOM-002]] 2.6, 응답 형태(`Video` `VideoSummary` `VideoDetail` `InboxListing`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `DB:` 테이블 접근(`crud`를 거친다), `FS:` 파일 접근, `·` 같은 단계 안 구분.

**이 서비스가 아는 것** — `videos` 테이블, inbox 폴더, `data/tmp/`. 작업 요약과 대화 수는 `JobService` · `ChatService`에 ID로 묻는다([[VA-DOM-002]] 3.2). 세션은 라우터가 열고, 함수는 그 안에서 돈다. `register` · `delete`만 트랜잭션 범위를 말한다.

**설정값** — `config.INBOX_DIR`(컨테이너 안 마운트 경로) · `config.INBOX_DISPLAY_PATH`(사용자에게 보일 호스트 경로) · `config.DATA_DIR` · `config.MAX_DURATION_SEC = 10800` · `ACCEPTED = {mp4, mkv, mov, webm} ∪ {mp3, m4a, wav}` · `config.PROBE_CONCURRENCY = 4`.

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#VideoService.list_inbox]] | inbox 파일 목록 — 길이 · 크기까지 |
| [[#VideoService.register]] | 등록 — 키 확인 → 형식 → 정보 → 상한 → 중복 → 생성 |
| [[#VideoService.list]] | 작업이 있는 영상 목록, 최근 순 |
| [[#VideoService.get]] | 영상 하나 + 작업 요약 |
| [[#VideoService.delete]] | 영상과 딸린 것 전부 삭제 |
| [[#VideoService.info_of]] | 출처별 정보 조회 (YouTube · 로컬) |
| [[#VideoService.to_dto]] | 행 + 작업 요약 + 대화 수 → `Video` (상태 계산) |

---

## 2. 함수

#### VideoService.list_inbox inbox 파일 목록

**시그니처** `async def list_inbox() -> InboxListing`

근거: [[VA-SEQ-001#SEQ-C1]] · [[VA-API-001#GET/api/inbox]] · [[VA-UC-001#UC-H2]] 1번 · [[VA-UI-002#UI-1]] 「내 파일」

**처리**
1. `dir = config.INBOX_DIR` · if 없거나 읽을 수 없음 → `! internal` (마운트가 안 된 것은 설치 오류다. 빈 폴더와 다르다)
2. `FS: dir 바로 아래 항목` 중 파일이고 · 이름이 `.`으로 시작하지 않고 · 확장자(소문자로 비교) ∈ `ACCEPTED`인 것만. 하위 폴더는 들어가지 않는다
3. 파일마다 `name` · `size_bytes = stat.st_size` · `modified_at = stat.st_mtime`(UTC) · `kind = video if 확장자 ∈ {mp4, mkv, mov, webm} else audio` · `duration_sec = MediaProbePort.probe(path)[0]` — `config.PROBE_CONCURRENCY`개씩 동시에 · if probe가 예외 → `duration_sec = None` (그 파일을 고르면 `register`가 `unsupported-file`을 낸다)
4. `modified_at` 내림차순 정렬 → `→ InboxListing(path=config.INBOX_DISPLAY_PATH, files=[InboxFile ×N])`

**출력** `InboxListing`. 폴더가 비어 있으면 `files = []`

**예외** `internal`(마운트 없음)뿐

**호출하는 것** `MediaProbePort.probe`

**테스트 관점** 하위 폴더 안 파일은 안 보인다 · `.DS_Store` 같은 숨김 파일은 안 보인다 · `MP4` 대문자 확장자도 받는다 · txt 파일은 안 보인다 · 깨진 파일은 `duration_sec=None`으로 목록에 있다 · 수정 시각 최근 것이 맨 위 · 빈 폴더 → `files=[]`, 200 · `path`는 마운트 경로가 아니라 표시 경로

---

#### VideoService.register 등록 — 사전 안내 전까지

**시그니처** `async def register(req: RegisterRequest) -> Video`

근거: [[VA-SEQ-001#SEQ-1]] · [[VA-API-001#POST/api/videos]] 1~7번 · [[VA-UC-001#UC-H1]] 1~2번 · [[VA-UC-001#UC-H2]] 1~2번 · [[VA-UC-001#UC-S1]] · [[VA-UC-001#UC-S5]] 1번

**입력** `req` — `{source: youtube, url}` 또는 `{source: local, path}`. `path`는 inbox 안 파일 이름

**처리** — 걸리는 곳에서 멈춘다. 순서가 규칙이다
1. `SettingsService.check_stored_key()` — 저장된 키로 OpenAI에 가벼운 요청 한 번(분석 버튼을 누를 때 확인, [[VA-UI-002#UI-5]] 규칙) · `SettingsService.require_key()` · if 키 없음 → `! key-missing` · if 확인 실패 → `! key-invalid {reason_kind, reason, checked_at}`
2. 형식 —
   - if `req.source == youtube` → `vid = 영상 ID 추출(req.url)`. 받는 형태는 셋: `youtube.com/watch?v={id}` · `youtu.be/{id}` · `youtube.com/shorts/{id}` (`www.` · `m.` 허용, `id`는 `[A-Za-z0-9_-]{11}`) · if 못 뽑음 → `! url-invalid {accepted: [watch, youtu.be, shorts]}`
   - else → `name = req.path` · if `/`·`\`가 들어 있거나 `.`으로 시작하거나 `..`이 들어 있음 → `! path-outside-inbox` · if 확장자 ∉ `ACCEPTED` → `! unsupported-file {reason: 받지 않는 형식, accepted}` · `path = config.INBOX_DIR / name` · if 파일 없음 → `! not-found {resource: inbox_file, id: name}`
3. `info = info_of(req)` — 정보 조회. `source-unavailable` · `unsupported-file` · `no-audio-track`은 거기서 난다
4. if `info.duration_sec > config.MAX_DURATION_SEC` → `! video-too-long {duration_sec, max_sec}` (길이는 알려야 화면이 시작 불가 판에 보인다)
5. **트랜잭션**: `row = DB: videos where source_id = info.source_id` (중복 판정 — YouTube는 영상 ID, 로컬은 내용 해시라 주소 형태 · 파일 이름이 달라도 같다)
   - if `row` 있음 → `job = JobService.latest(row.id)` · if `job is None`(사전 안내에서 취소했던 영상) → `DB: videos update row ← info` (title · channel · duration_sec · origin · has_captions · caption_language · caption_kind. `id` · `created_at`은 그대로) · else → 그대로 둔다
   - else → `row = DB: videos insert(info)` · `job = None`
   - if insert가 unique 위반(같은 영상을 동시에 두 번 넣음) → 다시 읽어 `row`로 (한 번만)
6. `count = ChatService.count_by_videos([row.id]).get(row.id, 0)`
7. `→ to_dto(row, job, count)` — `status`가 계산돼 나간다. 예상치는 라우터가 `JobService.estimate(video)`로 붙인다([[VA-DOM-002]] 3.1)

**출력** `Video`. `status`는 `registered`(방금 만들었거나 작업 없음) · `in_progress` · `failed` · `analyzed` 중 하나

**예외**

| 조건 | 에러 |
|---|---|
| 저장된 키 없음 · 확인 실패 | `key-missing` · `key-invalid` |
| YouTube 주소 형태 아님 | `url-invalid` |
| inbox 밖 경로 · 받지 않는 확장자 · 파일 없음 | `path-outside-inbox` · `unsupported-file` · `not-found` |
| YouTube 정보 조회 실패 | `source-unavailable` (info_of) |
| 파일을 못 열음 · 음성 트랙 없음 | `unsupported-file` · `no-audio-track` (info_of) |
| 3시간 초과 | `video-too-long` |

**호출하는 것** `SettingsService.check_stored_key` · `SettingsService.require_key` · [[#VideoService.info_of]] · `JobService.latest` · `ChatService.count_by_videos` · [[#VideoService.to_dto]]

**테스트 관점** 키 없음 → `key-missing`이고 YouTube · ffprobe에 닿지 않는다 · `https://youtu.be/dQw4w9WgXcQ`와 `https://www.youtube.com/watch?v=dQw4w9WgXcQ`는 같은 `source_id` · `shorts/` 주소도 받는다 · `https://vimeo.com/…` → `url-invalid` · `../etc/passwd` · `sub/a.mp4` → `path-outside-inbox` · `notes.txt` → `unsupported-file` · 같은 파일을 이름만 바꿔 넣으면 같은 영상 · 취소했던 영상을 다시 넣으면 제목이 새 정보로 바뀌고 `status=registered` · 작업이 있는 영상을 다시 넣으면 행이 안 바뀌고 `status`가 작업을 따른다 · 3시간 1초 → `video-too-long`, 행이 안 생긴다 · 동시에 두 번 넣어도 행은 하나

---

#### VideoService.list 작업이 있는 영상 목록

**시그니처** `async def list() -> list[VideoSummary]`

근거: [[VA-SEQ-001#SEQ-7]] · [[VA-API-001#GET/api/videos]] · [[VA-UC-001#UC-H5]] 1번 · [[VA-UC-001#UC-S5]] 3번

**처리**
1. `rows = DB: videos where id in (select video_id from analysis_jobs)` — 작업이 없는 영상(사전 안내에서 취소)은 빠진다
2. `jobs = JobService.latest_by_videos([row.id …])` · `counts = ChatService.count_by_videos([row.id …])` — 각각 쿼리 하나(N+1 금지)
3. `→ [VideoSummary(**to_dto(row, jobs[row.id], counts.get(row.id, 0)), job=jobs[row.id]) …]`를 `jobs[row.id].started_at` 내림차순으로

**출력** `list[VideoSummary]`. 비어 있으면 `[]`(화면이 빈 상태 상자)

**호출하는 것** `JobService.latest_by_videos` · `ChatService.count_by_videos` · [[#VideoService.to_dto]]

**테스트 관점** 작업 없는 영상은 목록에 없다 · 영상 3개면 쿼리는 셋(videos · jobs · counts)이지 3×N이 아니다 · 순서는 작업 시작 최근 순이지 영상 생성 순이 아니다 · 실패한 영상도 목록에 있고 `status=failed`

---

#### VideoService.get 영상 하나 + 작업 요약

**시그니처** `async def get(video_id: int) -> VideoDetail`

근거: [[VA-SEQ-001#SEQ-7]] · [[VA-API-001#GET/api/videos/{id}]] · [[VA-UC-001#UC-H5]] 2~3번 · [[VA-UC-001#UC-H6]] 2번

**처리**
1. `row = DB: videos where id` · if 없음 → `! not-found {resource: video, id}`
2. `job = JobService.latest(video_id)` · `count = ChatService.count_by_videos([video_id]).get(video_id, 0)`
3. `→ VideoDetail(video=to_dto(row, job, count), job=job)`

**출력** `VideoDetail`. job · analysis · chat 라우터가 인자용으로도 부른다([[VA-DOM-002]] 3.1 표)

**예외** `not-found`

**호출하는 것** `JobService.latest` · `ChatService.count_by_videos` · [[#VideoService.to_dto]]

**테스트 관점** 없는 id → `not-found` · 작업 없는 영상 → `job=None`, `status=registered` · `chat_turn_count`가 UI-6 '질문 기록 {n}개'와 같다

---

#### VideoService.delete 영상과 딸린 것 전부 삭제

**시그니처** `async def delete(video_id: int) -> None`

근거: [[VA-SEQ-001#SEQ-11]] · [[VA-API-001#DELETE/api/videos/{id}]] · [[VA-UC-001#UC-H6]] 4번 · [[VA-DOM-003]] 4장 5

**처리** — 진행 중 작업을 멈추는 것은 라우터가 먼저 `JobService.cancel(video_id)`로 한다. 이 함수는 멈춰 있다고 본다
1. `row = DB: videos where id` · if 없음 → `! not-found {resource: video, id}`
2. **트랜잭션**: `DB: delete videos where id` — `analysis_jobs` · `audio_chunks` · `transcripts` · `segments` · `summaries` · `insights` · `parts` · `chapters` · `suggested_questions` · `chat_turns`는 FK cascade가 지운다. 앱이 자식을 순서대로 지우지 않는다
3. 커밋 뒤 `FS: shutil.rmtree(config.DATA_DIR / "tmp" / str(video_id), ignore_errors=True)` — 임시 음성 · 조각 파일. inbox 원본은 건드리지 않는다([[VA-INFRA-001#C4]])
4. `→ None`

**출력** 없음(204)

**예외** `not-found` · DB · 디스크 오류는 `internal`로 새어 나간다 — 화면이 `detail`을 실패 한 줄에 보인다

**호출하는 것** 없음 (cascade와 파일 삭제뿐)

**테스트 관점** 지운 뒤 `get` → `not-found` · 딸린 열 종류의 행이 전부 사라진다 · `data/tmp/{id}`가 사라진다 · inbox 파일은 그대로 · 다른 영상의 행은 그대로 · 같은 영상을 다시 넣으면 `registered`로 처음부터 · 임시 폴더가 없어도 실패하지 않는다

---

#### VideoService.info_of 출처별 정보 조회

**시그니처** `async def info_of(req: RegisterRequest) -> SourceInfo`

근거: [[VA-SEQ-001#SEQ-1]] · [[VA-UC-001#UC-S1]] 1번, 1a · [[VA-UC-001#UC-H1]] 2번, 2a · [[VA-UC-001#UC-H2]] 2번, 1a · 2a

**처리**
- if `req.source == youtube` → `info = YouTubeInfoPort.info(req.url)` · if 실패 → `! source-unavailable {reason, hint}` (`hint`는 yt-dlp 추출기 오류일 때 'yt-dlp 업데이트', 아니면 null. [[VA-INFRA-001#C7]]) · `→ SourceInfo(youtube, source_id=영상 ID, title, channel, duration_sec, origin=정규화한 주소 https://www.youtube.com/watch?v={id}, has_captions, caption_language, caption_kind)` — 수동 자막이 있으면 `manual`, 자동뿐이면 `auto`, 없으면 `has_captions=false`
- else → `(duration_sec, has_audio) = MediaProbePort.probe(path)` · if 못 열음 → `! unsupported-file {reason, accepted}` · if `not has_audio` → `! no-audio-track {duration_sec}` · `sha = FS: 파일을 1MB씩 읽어 SHA-256` (수 GB면 몇 초 걸린다 — 화면은 버튼 대기 표시) · `→ SourceInfo(local, source_id=sha, title=파일 이름, channel=None, duration_sec, origin=파일 이름, has_captions=False, None, None)`

**출력** `SourceInfo`

**예외** `source-unavailable` · `unsupported-file` · `no-audio-track`

**호출하는 것** `YouTubeInfoPort.info` · `MediaProbePort.probe`

**테스트 관점** 가짜 포트로: 비공개 영상 → `source-unavailable`에 `reason` 있음 · 수동 자막 + 자동 자막 → `manual` · 자동만 → `auto` · 자막 없음 → `has_captions=false`, 언어 null · 음성 없는 mp4 → `no-audio-track`에 길이 있음 · 같은 내용의 파일 둘 → 같은 `source_id` · mp3 → `has_audio=true`로 통과

---

#### VideoService.to_dto 행 → Video (상태 계산)

**시그니처** `def to_dto(row: VideoRow, job: JobSummary | None, chat_count: int) -> Video`

근거: [[VA-DOM-002#Video]] (status · analyzed_at은 컬럼이 아니다) · [[VA-API-001]] 1장 갈 곳 표 · [[VA-DOM-002]] 5장 4

**처리**
1. `status` = if `job is None` → `registered` · elif `job.status == running` → `in_progress` · elif `failed` → `failed` · else → `analyzed`
2. `analyzed_at` = if `status == analyzed` → `job.finished_at` · else → `None`
3. `→ Video(row의 컬럼 전부, status, analyzed_at, chat_turn_count=chat_count)`

**출력** `Video`

**테스트 관점** 작업 없음 → `registered` · `running` → `in_progress` · `done` → `analyzed`이고 `analyzed_at == job.finished_at` · `failed` → `analyzed_at=None` · **이 함수 말고 `status`를 만드는 곳이 없다**(grep으로 확인)

---

## 3. 미결사항

- [ ] `list_inbox`의 길이 재기 캐시 — 파일 수십 개면 ffprobe 수십 번. 수정 시각 + 크기를 키로 메모리에 둘지. 첫 버전은 캐시 없음, 동시 4개([[VA-DOM-002]] 7장과 같은 항목)
- [ ] `info_of`의 SHA-256이 수 GB 파일에서 몇 초 걸린다 — 화면 대기 표시로 충분한지, 앞 64MB만 해시할지. 앞부분만 하면 같은 앞부분을 가진 다른 파일이 같은 영상으로 판정될 수 있어 첫 버전은 전체
- [ ] UI-1이 열려 있는 동안 `list`를 다시 부르는 주기 — [[VA-SEQ-001]] 3장과 같은 항목. 진행 중 행이 있을 때만 3초로 시작
