---
doc_id: VA-MS-001
type: MS
title: MINISPEC — VideoService
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-DOM-003, VA-UC-001]
---

# MINISPEC — VideoService

## 0. 이 문서가 다루는 것

`domains/video/service.py`의 함수 10개. 클래스 명세 [[VA-DOM-002#VideoService]]의 시그니처를 함수 내부까지 내린 것. **MS 문서 하나 = 클래스 명세 4장 절 하나 = 코드 파일 하나** — 이 파일을 짤 때 이 문서를 본다. 포트 · 어댑터(`youtube_info` · `media_probe`)는 4.6 · 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10 — 시그니처 · 근거 · 입력 · 처리 · 출력 · 예외 · 호출하는 것 · 테스트 관점, 분기는 `if 조건 → 결과`, 간략형 허용. 내부 타입(`SourceInfo` 등)은 [[VA-DOM-002]] 2.6, 응답 형태(`Video` `VideoSummary` `VideoDetail` `InboxListing`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `DB:` 테이블 접근(`crud`를 거친다), `FS:` 파일 접근, `·` 같은 단계 안 구분.

**이 서비스가 아는 것** — `videos` 테이블, inbox 폴더, `data/uploads/`(올린 사본 — 수명을 이 서비스가 쥔다, [[VA-DOM-001]] 4장), 지울 때만 `data/tmp/` · `data/frames/` · `data/infographics/`. 작업 요약과 대화 수는 `JobService` · `ChatService`에 ID로 묻는다([[VA-DOM-002]] 3.2). 로컬 원본의 경로는 `sources.local_path`(shared) 하나가 푼다 — inbox 파일이면 `INBOX_DIR / origin`, 올린 사본이면 `UPLOAD_DIR / {source_id}{origin의 확장자}`([[VA-DOM-002]] 5장 12). 세션은 라우터가 열고, 함수는 그 안에서 돈다. `register` · `upload` · `delete`만 트랜잭션 범위를 말한다.

**설정값** — `config.INBOX_DIR`(컨테이너 안 마운트 경로) · `config.INBOX_DISPLAY_PATH`(사용자에게 보일 호스트 경로) · `config.DATA_DIR` · `config.MAX_DURATION_SEC = 10800` · `ACCEPTED = {mp4, mkv, mov, webm} ∪ {mp3, m4a, wav}` · `config.PROBE_CONCURRENCY = 4` · `config.UPLOAD_DIR = {DATA_DIR}/uploads` · `config.UPLOAD_SPARE_BYTES = 1 GiB` — 올릴 때 파일 크기에 더해 남아 있어야 할 여유. 분석이 그 뒤에 쓰는 것(3시간 mp3 약 86 MB와 조각 · 장면)을 넉넉히 덮는 고정값이다([[VA-API-001]] 6장 미결을 여기서 정한다) · `config.UPLOAD_WRITE_BYTES = 1 MiB` — 받은 조각을 이만큼 모아 스레드에서 쓴다(이벤트 루프를 막지 않게).

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#VideoService.list_inbox]] | inbox 파일 목록 — 길이 · 크기까지 |
| [[#VideoService.register]] | 등록 — 키 확인 → 형식 → 정보 → 상한 → 중복 → 생성 |
| [[#VideoService.upload]] | 올린 파일 등록 — 키 → 이름 → 디스크 → 쓰며 해시 → 정보 → 중복 → 사본 |
| [[#VideoService.list]] | 작업이 있는 영상 목록, 최근 순 |
| [[#VideoService.get]] | 영상 하나 + 작업 요약 |
| [[#VideoService.delete]] | 영상과 딸린 것 전부 삭제 — 행 · 임시 음성 · 장면 · 인포그래픽 · 올린 사본 |
| [[#VideoService.release_upload]] | 올린 사본 놓기 (작업이 done이 된 뒤 · 지울 때) |
| [[#VideoService.sweep_uploads]] | 시작 때 올리다 만 것 · 주인 없는 사본 · 끝난 작업의 사본 청소 |
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
3. 파일마다 `name` · `size_bytes = stat.st_size` · `modified_at = stat.st_mtime`(UTC) · `kind = video if 확장자 ∈ {mp4, mkv, mov, webm} else audio` · `duration_sec = MediaProbePort.probe(path)[0]` — `config.PROBE_CONCURRENCY`개씩 동시에 · if probe가 예외 → `duration_sec = None` (그 파일을 고르면 `register`가 `unsupported-file`을 낸다) · 목록을 읽은 뒤 재기 전에 파일이 사라졌으면(옮기는 중) 그 파일만 뺀다 — 목록 전체가 실패하지 않게
4. `modified_at` 내림차순 정렬 → `→ InboxListing(path=config.INBOX_DISPLAY_PATH, files=[InboxFile ×N])`

**출력** `InboxListing`. 폴더가 비어 있으면 `files = []`

**예외** `internal`(마운트 없음)뿐

**호출하는 것** `MediaProbePort.probe`

**테스트 관점** 하위 폴더 안 파일은 안 보인다 · `.DS_Store` 같은 숨김 파일은 안 보인다 · `MP4` 대문자 확장자도 받는다 · txt 파일은 안 보인다 · 깨진 파일은 `duration_sec=None`으로 목록에 있다 · 읽는 사이 사라진 파일은 빠지고 나머지는 200 · 수정 시각 최근 것이 맨 위 · 빈 폴더 → `files=[]`, 200 · `path`는 마운트 경로가 아니라 표시 경로

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
3. `info = info_of(req)` — 정보 조회와 길이 상한. `source-unavailable` · `unsupported-file` · `no-audio-track` · `video-too-long`(길이를 알려야 화면이 시작 불가 판에 보인다)은 거기서 난다
4. **트랜잭션**: `row = DB: videos where source_id = info.source_id` (중복 판정 — YouTube는 영상 ID, 로컬은 내용 해시라 주소 형태 · 파일 이름이 달라도 같다)
   - if `row` 있음 → `job = JobService.latest(row.id)` · if `job is None`(사전 안내에서 취소했던 영상) → `DB: videos update row ← info` (title · channel · duration_sec · origin · has_captions · caption_language · caption_kind. `id` · `created_at`은 그대로) · else → 그대로 둔다. 단 inbox 영상(`uploaded=false`)이고 `origin`이 다르면(이름을 바꿨다) `origin`만 지금 이름으로 고친다 — 다시 시도하는 파이프라인이 `sources.local_path`로 `INBOX_DIR / origin`을 읽는다([[VA-MS-002#pipeline.resume]]). 제목은 그대로. 올린 영상은 고치지 않는다 — 사본 이름이 원래 이름의 확장자를 따르고 다시 시도는 사본을 읽는다. 작업이 없는 올린 영상(사본은 취소 때 지웠다)을 inbox에서 고르면 `info`로 덮어써 inbox 영상이 된다(`uploaded=false`)
   - else → `row = DB: videos insert(info)` · `job = None`
   - if insert가 unique 위반(같은 영상을 동시에 두 번 넣음) → 다시 읽어 `row`로 (한 번만)
5. `count = ChatService.count_by_videos([row.id]).get(row.id, 0)`
6. `→ to_dto(row, job, count)` — `status`가 계산돼 나간다. 예상치는 라우터가 `JobService.estimate(video)`로 붙인다([[VA-DOM-002]] 3.1)

**출력** `Video`. `status`는 `registered`(방금 만들었거나 작업 없음) · `in_progress` · `failed` · `analyzed` 중 하나

**예외**

| 조건 | 에러 |
|---|---|
| 저장된 키 없음 · 확인 실패 | `key-missing` · `key-invalid` |
| YouTube 주소 형태 아님 | `url-invalid` |
| inbox 밖 경로 · 받지 않는 확장자 · 파일 없음 | `path-outside-inbox` · `unsupported-file` · `not-found` |
| YouTube 정보 조회 실패 | `source-unavailable` (info_of) |
| 파일을 못 열음 · 음성 트랙 없음 | `unsupported-file` · `no-audio-track` (info_of) |
| 3시간 초과 | `video-too-long` (info_of) |

**호출하는 것** `SettingsService.check_stored_key` · `SettingsService.require_key` · [[#VideoService.info_of]] · `JobService.latest` · `ChatService.count_by_videos` · [[#VideoService.to_dto]]

**테스트 관점** 키 없음 → `key-missing`이고 YouTube · ffprobe에 닿지 않는다 · `https://youtu.be/dQw4w9WgXcQ`와 `https://www.youtube.com/watch?v=dQw4w9WgXcQ`는 같은 `source_id` · `shorts/` 주소도 받는다 · `https://vimeo.com/…` → `url-invalid` · `../etc/passwd` · `sub/a.mp4` → `path-outside-inbox` · `notes.txt` → `unsupported-file` · 같은 파일을 이름만 바꿔 넣으면 같은 영상 · 취소했던 영상을 다시 넣으면 제목이 새 정보로 바뀌고 `status=registered` · 작업이 있는 영상을 다시 넣으면 행이 안 바뀌고 `status`가 작업을 따른다 · 작업이 실패한 로컬 파일을 이름만 바꿔 넣으면 `origin`만 새 이름이고 제목 · 작업은 그대로 · 작업이 있는 올린 영상과 같은 내용을 inbox에서 고르면 행이 안 바뀐다(`origin`도) · 작업이 없는 올린 영상과 같은 내용을 inbox에서 고르면 `uploaded=false`로 덮어쓴다 · 3시간 1초 → `video-too-long`, 행이 안 생긴다 · 동시에 두 번 넣어도 행은 하나

---

#### VideoService.upload 올린 파일 등록 — 사전 안내 전까지

**시그니처** `async def upload(name: str, size: int, body: AsyncIterator[bytes]) -> Video`

근거: [[VA-SEQ-001#SEQ-15]] · [[VA-API-001#POST/api/uploads]] 1~7번 · [[VA-UC-001#UC-H2]] 1~2번, 1a · 1c · 1d · 2a · 2c · [[VA-UC-001#UC-S5]] 1b · [[VA-INFRA-001#C4]] · [[VA-DOM-002]] 5장 15

**입력** `name` — 라우터가 `X-File-Name`의 퍼센트 인코딩을 푼 원래 파일 이름(헤더가 없으면 라우터가 `validation`). `size` — `Content-Length`(없으면 라우터가 `validation`). `body` — `request.stream()`, 본문 조각의 비동기 반복자. 라우터는 헤더를 읽어 넘길 뿐이다 · 이 함수가 예외로 끝나면(어느 판정이든) 라우터가 남은 본문을 끝까지 읽어 버린 뒤 오류를 돌려준다 — 브라우저는 본문을 다 보내야 답을 읽는다. 읽지 않으면 올리기가 멈춘 채 끝나지 않는다([[VA-SEQ-001]] 3장, 카드 D4 실측). 끊겼으면(`ClientDisconnect`) 그만 읽는다

**처리** — 걸리는 곳에서 멈춘다. 1~3은 본문을 읽기 전이다
1. `SettingsService.check_stored_key()` · `SettingsService.require_key()` — [[#VideoService.register]] 1번과 같다. 큰 파일을 다 받은 뒤 키 때문에 멈추지 않게 먼저 본다
2. 이름 · 크기 — `name = NFC 정규화(name).strip()` · if 비었거나 · 제어 문자가 있거나 · 300자를 넘음 → `! validation {errors: [{field: X-File-Name, message}]}` · if `size ≤ 0` → `! validation {field: Content-Length}` · if 확장자(소문자) ∉ `ACCEPTED` → `! unsupported-file {reason: 받지 않는 형식, accepted}`. 원래 이름은 제목과 `origin`에만 쓴다 — 사본 파일 이름은 해시다
3. 디스크 — `free = shutil.disk_usage(config.UPLOAD_DIR).free` · if `free < size + config.UPLOAD_SPARE_BYTES` → `! no-space {needed_bytes: size + UPLOAD_SPARE_BYTES, free_bytes: free}`([[VA-UC-001#UC-H2]] 1d)
4. 받기 — `FS: mkdir(config.UPLOAD_DIR)` · `part = UPLOAD_DIR / f".part-{uuid4().hex}{확장자}"`(확장자를 붙여 두면 ffprobe가 형식을 덜 헤맨다) · `body`의 조각마다 `sha.update(조각)` · `got += len(조각)` · `UPLOAD_WRITE_BYTES`만큼 모이면 스레드에서 쓴다 · if `got > size` → 멈춘다 · 끝나면 if `got != size` → `! upload-incomplete {received_bytes: got, expected_bytes: size}` · 연결이 끊기면(`ClientDisconnect`) → `! upload-incomplete`(응답은 닿지 않는다) · `OSError(ENOSPC)` → `! no-space` — **옮기지 못한 채 끝나는 모든 길에서 `part`를 지운다**(`finally`, [[VA-UC-001#UC-H2]] 최소 보장)
5. 정보 — `(duration_sec, has_audio) = MediaProbePort.probe(part)` · 판정은 [[#VideoService.info_of]] 로컬 갈래와 같은 함수를 지난다(두 벌이 되지 않게): 못 열음 → `! unsupported-file {reason, accepted}` · 음성 없음 → `! no-audio-track {duration_sec}` · 3시간 초과 → `! video-too-long {duration_sec, max_sec}` · `info = SourceInfo(local, source_id=sha.hexdigest(), title=name, channel=None, duration_sec, origin=name, uploaded=True, has_captions=False, None, None)`
6. 중복 — **트랜잭션**: `row = DB: videos where source_id = info.source_id` · `copy = sources.local_path(name, sha, True)` = `UPLOAD_DIR / f"{sha}{확장자}"`
   - if `row` 있음이고 `job = JobService.latest(row.id)`가 있다 → `part`를 지우고 그 영상 그대로(행 · 그 영상의 원본은 건드리지 않는다, [[VA-UC-001#UC-H2]] 2c)
   - elif `row` 있음(작업 없음 — 사전 안내에서 취소했던 영상) → `FS: os.replace(part, copy)` · `DB: videos update row ← info`(`uploaded=true`, `origin`은 지금 이름) — 사본을 지우면 그 영상의 원본이 없어진다([[VA-SEQ-001]] 되먹일 것 #9)
   - else → `FS: os.replace(part, copy)` · `row = DB: videos insert(info)` · `job = None` · unique 위반(같은 파일을 동시에 둘) → 다시 읽어 그 행으로 — 사본은 같은 이름이라 덮어써도 같은 내용이다
7. `count = ChatService.count_by_videos([row.id]).get(row.id, 0)` · `→ to_dto(row, job, count)` — 예상치는 라우터가 `JobService.estimate(video)`로 붙인다([[#VideoService.register]]와 같다)

**출력** `Video`. `status`는 `registered`(새로 · 덮어쓰기) · 작업이 있는 영상이면 그 작업을 따른다

**예외**

| 조건 | 에러 |
|---|---|
| 저장된 키 없음 · 확인 실패 | `key-missing` · `key-invalid` |
| 이름 없음 · 이상함 · 크기 없음 | `validation` |
| 받지 않는 확장자 · 열 수 없음 | `unsupported-file` |
| 디스크 여유 부족 | `no-space` |
| 받은 크기가 다름 · 끊김 | `upload-incomplete` |
| 음성 트랙 없음 · 3시간 초과 | `no-audio-track` · `video-too-long` |

**호출하는 것** `SettingsService.check_stored_key` · `SettingsService.require_key` · `MediaProbePort.probe` · `sources.local_path` · `JobService.latest` · `ChatService.count_by_videos` · [[#VideoService.to_dto]]

**테스트 관점** 가짜 본문 조각으로: 조각 셋 → 사본 `data/uploads/{sha}.mp4`, `source_id`가 같은 파일을 inbox로 등록한 것과 같다, `uploaded=true`, `title=origin=원래 이름` · 키 없음 → `key-missing`이고 본문을 한 조각도 읽지 않는다 · `notes.txt` → `unsupported-file`, 읽지 않는다 · 여유가 모자라면 `no-space`, `needed_bytes = size + 1 GiB` · 본문이 `Content-Length`보다 짧다 · 길다 · 중간에 예외 → `upload-incomplete`이고 `.part`가 없다 · 음성 없는 mp4 → `no-audio-track`, `.part`가 없다 · 4시간 → `video-too-long`, 행 · 사본이 없다 · 작업이 있는 영상과 같은 내용 → 그 영상, 새 사본도 `.part`도 없다 · 사전 안내에서 취소한 올린 영상을 다시 올림 → 같은 행, 사본이 다시 생긴다 · 작업 없는 inbox 영상과 같은 내용 → 같은 행이 `uploaded=true`로 · 동시에 같은 파일 둘 → 행 하나 · (라우터) 키 없음으로 본문 전에 거절해도 본문을 끝까지 읽은 뒤 `key-missing`

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

**테스트 관점** 작업 없는 영상은 목록에 없다 · 영상 3개든 6개든 쿼리 수가 같다 — 넷(영상 · 작업 · 조각 집계 · 대화 수. 작업 쪽 둘은 [[VA-MS-002#JobService.latest_by_videos]])이지 3×N이 아니다 · 순서는 작업 시작 최근 순이지 영상 생성 순이 아니다 · 실패한 영상도 목록에 있고 `status=failed`

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

**처리** — 진행 중 작업을 멈추는 것은 라우터가 먼저 `JobService.cancel(video_id)`로, 뒤 일(장면 채우기 · 인포그래픽)은 `AnalysisService.cancel_tasks(video_id)`로 한다. 이 함수는 멈춰 있다고 본다. 사전 안내에서 취소한 올린 영상도 이 길이다([[VA-UC-001#UC-H2]] 3a)
1. `row = DB: videos where id` · if 없음 → `! not-found {resource: video, id}`
2. **트랜잭션**: `DB: delete videos where id` — `analysis_jobs` · `audio_chunks` · `transcripts` · `segments` · `summaries` · `insights` · `parts` · `chapters` · `suggested_questions` · `chat_turns` · `chapter_frames` · `infographics`는 FK cascade가 지운다. 앱이 자식을 순서대로 지우지 않는다
3. 커밋 뒤 — 수백 MB일 수 있어 스레드에서, 없으면 넘어간다: `FS: rmtree(config.DATA_DIR / "tmp" / str(video_id))`(임시 음성 · 조각) · `FS: rmtree(config.FRAMES_DIR / str(video_id))`(장면) · `FS: remove(config.INFOGRAPHICS_DIR / f"{video_id}.png")`(인포그래픽) · if `row.uploaded` → `FS: remove(sources.local_path(row.origin, row.source_id, True))`(올린 사본 — [[#VideoService.release_upload]]와 같은 규칙). inbox 원본과 올린 파일의 원래 파일(PC에 있는 것), 내보낸 노트 · 그림은 건드리지 않는다([[VA-INFRA-001#C4]])
4. `→ None`

**출력** 없음(204)

**예외** `not-found` · DB · 디스크 오류는 `internal`로 새어 나간다 — 화면이 `detail`을 실패 한 줄에 보인다

**호출하는 것** 없음 (cascade와 파일 삭제뿐)

**테스트 관점** 지운 뒤 `get` → `not-found` · 딸린 열두 종류의 행이 전부 사라진다 · `data/tmp/{id}` · `data/frames/{id}` · `data/infographics/{id}.png` · 올린 사본이 사라진다 · inbox 파일은 그대로 · 다른 영상의 행은 그대로 · 같은 영상을 다시 넣으면 `registered`로 처음부터 · 임시 폴더가 없어도 실패하지 않는다

---

#### VideoService.release_upload 올린 사본 놓기

**시그니처** `async def release_upload(video: Video) -> None`

근거: [[VA-SEQ-001#SEQ-16]] 20~21번 · [[VA-UC-001#UC-H2]] 4번 · [[VA-DOM-002]] 5장 12 · [[VA-DOM-001]] 5장 6

**처리** if `not video.uploaded` → 끝 · `FS: remove(sources.local_path(video.origin, video.source_id, True))` — 없으면(이미 지웠다) 조용히 끝 · 행은 건드리지 않는다 — `uploaded`는 그대로다(다시 시도할 때 어디서 읽을지 정하는 값). 세션이 필요 없다 — `main.py`가 감싸 워커에게 넘기고, 파이프라인이 작업을 `done`으로 적은 뒤 부른다([[VA-MS-002#pipeline.run]])

**테스트 관점** 올린 영상 → 사본이 없어진다 · 두 번 불러도 예외가 없다 · inbox 영상 → 아무것도 하지 않는다(inbox 파일 그대로) · 행의 `uploaded`가 그대로

---

#### VideoService.sweep_uploads 시작 때 올린 사본 청소

**시그니처** `async def sweep_uploads() -> int`

근거: [[VA-SEQ-001#SEQ-13]] 15~21번 · [[VA-API-001#POST/api/uploads]] 마지막 문단 · [[VA-INFRA-001#C4]] · [[VA-UC-001#UC-H2]] 최소 보장

**처리** — `main.py` lifespan이 `JobService.fail_orphans` **뒤**에 부른다(죽은 `running`이 `failed`가 된 뒤라야 그 사본이 남는다)
1. `FS: config.UPLOAD_DIR 바로 아래 파일` · 폴더가 없으면 `→ 0`
2. `.part-`로 시작하는 것 → 지운다(서버가 올리는 도중에 죽었다)
3. 나머지는 확장자 앞을 `sha`로 · `rows = DB: videos where source_id in (sha …)` · `jobs = JobService.latest_by_videos([row.id …])`
4. 파일마다 — if 그 `sha`의 행이 없다(주인 없음 — 이름 모양이 다른 파일도) · 행이 `uploaded=false` · 작업이 없다(사전 안내에서 멈췄다) · 작업이 `done` → 지운다 · else(`failed` · `queued` · `running`) → 남긴다 — 다시 시도 · 대기열이 읽는다
5. `→ 지운 파일 수` — `main.py`가 로그 한 줄로 남긴다

**테스트 관점** `.part-x` → 지워진다 · 행 없는 사본 → 지워진다 · 작업이 `done`인 사본 → 지워진다 · `failed` · `queued`인 사본 → 남는다 · 작업이 없는 올린 영상의 사본 → 지워진다 · 폴더가 없으면 0 · 쿼리는 영상 하나 · 작업 요약 하나(파일 수와 무관)

---

#### VideoService.info_of 출처별 정보 조회

**시그니처** `async def info_of(req: RegisterRequest) -> SourceInfo`

근거: [[VA-SEQ-001#SEQ-1]] · [[VA-UC-001#UC-S1]] 1번, 1a · [[VA-UC-001#UC-H1]] 2번, 2a · [[VA-UC-001#UC-H2]] 2번, 1a · 2a

**처리**
- if `req.source == youtube` → `info = YouTubeInfoPort.info(req.url)` · if 실패 → `! source-unavailable {reason, hint}` (`hint`는 yt-dlp 추출기 오류일 때 'yt-dlp 업데이트', 아니면 null. [[VA-INFRA-001#C7]]) · `→ SourceInfo(youtube, source_id=영상 ID, title, channel, duration_sec, origin=정규화한 주소 https://www.youtube.com/watch?v={id}, uploaded=False, has_captions, caption_language, caption_kind)` — 수동 자막이 있으면 `manual`, 자동뿐이면 `auto`, 없으면 `has_captions=false` · if `duration_sec > config.MAX_DURATION_SEC` → `! video-too-long {duration_sec, max_sec}`
- else → `(duration_sec, has_audio) = MediaProbePort.probe(path)` · if 못 열음 → `! unsupported-file {reason, accepted}` · if `not has_audio` → `! no-audio-track {duration_sec}` · if `duration_sec > config.MAX_DURATION_SEC` → `! video-too-long {duration_sec, max_sec}` — 해시보다 먼저 본다(4시간짜리 큰 파일을 다 읽고 나서 거절하지 않게, 카드 B5) · `sha = FS: 파일을 1MB씩 읽어 SHA-256` (수 GB면 몇 초 걸린다 — 화면은 버튼 대기 표시) · `→ SourceInfo(local, source_id=sha, title=파일 이름, channel=None, duration_sec, origin=파일 이름, uploaded=False, has_captions=False, None, None)` — 열기 · 음성 · 길이 판정은 [[#VideoService.upload]] 5번과 같은 함수다

**출력** `SourceInfo`

**예외** `source-unavailable` · `unsupported-file` · `no-audio-track` · `video-too-long`

길이 상한(3시간, [[VA-PRD-001#N2]])은 이 함수 한곳에서 본다 — YouTube는 정보를 받은 뒤, 로컬은 해시 전에. 두 출처 모두 같은 줄(`duration_sec > MAX_DURATION_SEC`)을 지나고, [[#VideoService.register]]는 다시 보지 않는다(코드 리뷰, 카드 B5 — 두 곳이면 한쪽만 바뀔 수 있다)

**호출하는 것** `YouTubeInfoPort.info` · `MediaProbePort.probe`

**테스트 관점** 가짜 포트로: 비공개 영상 → `source-unavailable`에 `reason` 있음 · 수동 자막 + 자동 자막 → `manual` · 자동만 → `auto` · 자막 없음 → `has_captions=false`, 언어 null · 음성 없는 mp4 → `no-audio-track`에 길이 있음 · 4시간 YouTube → `video-too-long`에 길이 · 4시간 로컬 파일 → 해시를 읽지 않고 `video-too-long` · 같은 내용의 파일 둘 → 같은 `source_id` · mp3 → `has_audio=true`로 통과

---

#### VideoService.to_dto 행 → Video (상태 계산)

**시그니처** `def to_dto(row: VideoRow, job: JobSummary | None, chat_count: int) -> Video`

근거: [[VA-DOM-002#Video]] (status · analyzed_at은 컬럼이 아니다) · [[VA-API-001]] 1장 갈 곳 표 · [[VA-DOM-002]] 5장 4

**처리**
1. `status` = if `job is None` → `registered` · elif `job.status ∈ {queued, running}` → `in_progress`(대기 중도 진행 중이다 — [[VA-API-001]] 4장 `VideoStatus`) · elif `failed` → `failed` · else(`done`) → `analyzed`
2. `analyzed_at` = if `status == analyzed` → `job.finished_at` · else → `None`
3. `upload_bytes` = if `row.uploaded`이고 사본 파일(`sources.local_path(row.origin, row.source_id, True)`)이 있다 → `stat().st_size` · else → `None`
4. `→ Video(row의 컬럼 전부(uploaded 포함), status, analyzed_at, upload_bytes, chat_turn_count=chat_count)` — UI-6이 '올린 사본({크기})'과 「남는 것」 문구를 이것으로 고른다([[VA-API-001#GET/api/videos/{id}]])

**출력** `Video`

**테스트 관점** 작업 없음 → `registered` · `running` → `in_progress` · `queued` → `in_progress` · `done` → `analyzed`이고 `analyzed_at == job.finished_at` · `failed` → `analyzed_at=None` · **이 함수 말고 `status`를 만드는 곳이 없다**(grep으로 확인) · 올린 영상에 사본이 있으면 `upload_bytes`가 크기, 지운 뒤에는 `None` · inbox 영상은 `None`

---

## 3. 미결사항

- [ ] `list_inbox`의 길이 재기 캐시 — 파일 수십 개면 ffprobe 수십 번. 수정 시각 + 크기를 키로 메모리에 둘지. 첫 버전은 캐시 없음, 동시 4개([[VA-DOM-002]] 7장과 같은 항목)
- [x] `info_of`의 SHA-256이 수 GB 파일에서 몇 초 걸린다 — 화면 대기 표시로 충분한지, 앞 64MB만 해시할지. 앞부분만 하면 같은 앞부분을 가진 다른 파일이 같은 영상으로 판정될 수 있어 첫 버전은 전체 · 느린 디스크(WSL의 Windows 드라이브 등)에서는 수십 초라 web 프록시 60초([[VA-DOM-002]] 6장)에 닿을 수 있다 — 넘기면 화면은 연결 오류인데 서버는 등록을 마친다(다시 누르면 같은 영상으로 열린다). 결정(카드 C 실측, 사용자 2026-09-29): **전체 해시 그대로** — WSL2 PC의 리눅스 쪽 폴더(ext4 바인드 마운트)에서 4 GiB 파일이 4.6~6.5초(초당 630~900 MiB), 실제 561 MiB 영상 등록이 2.5초라 3시간 녹화본도 60초에 멀다. Windows 드라이브(`/mnt/c`)는 재지 않았다 — README가 WSL이면 inbox를 리눅스 쪽 폴더에 두라고 알린다
- [x] 올릴 때 디스크 여유분([[VA-API-001]] 6장 미결) — 결정: 고정 1 GiB(`UPLOAD_SPARE_BYTES`). 파일 크기의 몇 %로 두면 작은 파일에 여유가 모자란다. API 미결은 다음 API 수정 때 닫는다
- [ ] 올리기 시간 제한 — web 라우트 핸들러의 `fetch`(undici)는 헤더 · 본문 대기가 기본 300초다. 같은 PC라 수 GB도 그 안이지만 카드 D4에서 588MB 파일로 잰다([[VA-API-001]] 6장 미결과 같은 항목)
- [ ] 사전 안내가 열린 채 서버가 다시 뜨면 시작 청소가 그 영상의 사본을 지운다(작업이 없다) — [분석 시작]이 추출 단계에서 실패하고, 다시 올려야 한다. 드물어 그대로 둔다. 겪으면 청소 조건을 「작업이 없고 하루 지난 사본」으로 좁힌다
- [x] UI-1이 열려 있는 동안 `list`를 다시 부르는 주기 — [[VA-SEQ-001]] 3장과 같은 항목. 결정(카드 B1): 진행 중 · 대기 중 행이 있는 동안 3초, 없으면 부르지 않는다([[VA-UI-002#UI-1]] 규칙)
