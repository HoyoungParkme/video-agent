---
doc_id: VA-MS-002
type: MS
title: MINISPEC — JobService · pipeline
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-DOM-003, VA-UC-001, VA-INFRA-001]
---

# MINISPEC — JobService · pipeline

## 0. 이 문서가 다루는 것

`domains/job/service.py`의 함수 20개와 `domains/job/pipeline.py`의 함수 6개. 클래스 명세 [[VA-DOM-002#JobService]]와 그 아래 「파이프라인」의 시그니처를 함수 내부까지 내린 것. **MS 문서 하나 = 클래스 명세 4장 절 하나** — 4.2 절이 두 파일이라 이 문서도 두 모듈이다. 포트 · 어댑터(`audio_source` · `audio_split` · `stt_openai`)는 4.6 · 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10. 내부 타입(`ChunkPlan` `SttSegment` `Progress`)은 [[VA-DOM-002]] 2.6, 응답 형태(`Job` `JobSummary` `Chunks` `Chunk` `JobError` `Estimate` `Models`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `DB:` 테이블 접근(`crud`를 거친다), `FS:` 파일 접근, `now` 현재 시각(UTC).

**이 묶음이 아는 것** — `analysis_jobs` · `audio_chunks` 테이블, `data/tmp/{video_id}/`. 영상은 `Video` DTO로 받고 영상 테이블을 읽지 않는다. 결과 저장은 `AnalysisService`에 넘긴다([[VA-DOM-002]] 3.2).

**세션** — 서비스 함수는 호출자의 세션 안에서 돈다. 라우터는 요청마다 하나. **파이프라인은 서비스를 부를 때마다 짧은 세션을 열고 닫는다**([[VA-DOM-002]] 6장) — 십여 분 도는 태스크가 세션 하나를 잡지 않게. 아래 `DB:`가 붙은 서비스 함수 하나가 트랜잭션 하나다.

**설정값(첫 값)** — 인프라 9절의 미결을 여기서 정한다.

| 이름 | 첫 값 | 이유 |
|---|---|---|
| `config.CHUNK_SEC` | 600 | 64kbps 모노 10분 ≈ 4.8MB. 25MB 상한([[VA-INFRA-001#C2]])의 1/5라 무음 경계로 조금 늘어나도 안전 |
| `config.STT_CONCURRENCY` | 3 | 시간당 3분 목표([[VA-PRD-001#N1]])와 OpenAI 요청 제한 사이. 측정 뒤 조정 |
| `config.CHUNK_MAX_ATTEMPTS` | 3 | 화면 문구 '3번 다시 보냈지만'([[VA-UI-002#UI-3]]) |
| `config.CHUNK_EST_SEC` | 45 | 조각 하나(10분)의 받아쓰기 예상 시간. 예상치 계산용. 측정 뒤 조정 |
| `config.TEXT_EST_SEC` | 60 | 요약 · 챕터 · 추천 질문 세 단계 합. 자막 있음의 '약 1분' |
| `config.TOKENS_PER_MIN` | 200 | 한국어 말하기 분당 토큰 추정. 텍스트 비용 계산용 |
| `config.WORKER_IDLE_SEC` | 5 | 워커가 신호 없이도 대기열을 다시 보는 간격. 깨우는 신호를 놓쳤을 때의 안전망이라 짧을 필요가 없다 |

**진행률 가중치** — `stages`에 `transcribe`가 있으면 받아쓰기 70, 나머지 단계가 30을 똑같이 나눈다. 없으면 단계들이 100을 똑같이 나눈다. 받아쓰기 안에서는 완료 조각 비율로 채운다. 단계가 끝나면 그 가중치만큼 더한다.

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#JobService.estimate]] | 사전 안내 예상치 (작업 있으면 null) |
| [[#JobService.start]] | 작업 행을 `queued`로 넣고 워커를 깨운다 |
| [[#JobService.progress]] | 폴링 응답 `Job` |
| [[#JobService.retry]] | 실패 작업을 같은 행으로 대기열 끝에 |
| [[#JobService.cancel]] | 태스크 취소 (삭제 전) |
| [[#JobService.latest]] | 영상의 최근 작업 요약 |
| [[#JobService.latest_by_videos]] | 여러 영상의 최근 작업 요약, 쿼리 하나 |
| [[#JobService.mark_stage]] | 단계 전환 · 걸린 시간 · 진행률 |
| [[#JobService.plan_chunks]] | 조각 행 생성 |
| [[#JobService.mark_chunk]] | 조각 상태 전이 (attempts · result · 진행률) |
| [[#JobService.finish]] | done |
| [[#JobService.fail]] | failed + error |
| [[#JobService.fail_orphans]] | 시작 때 running 정리 |
| [[#JobService.claim_next]] | 대기열에서 다음 작업을 `running`으로 |
| [[#JobService.wake]] | 워커를 깨운다 |
| [[#JobService.wait_for_work]] | 할 일이 생길 때까지 기다린다 |
| [[#JobService.queue_position]] | 대기열에서의 차례 |
| [[#JobService.stages_for]] | 출처 → 단계 목록 |
| [[#JobService.remaining_sec]] | 남은 시간 계산 |
| [[#JobService.to_job]] | 행 + 조각 → `Job` |
| [[#pipeline.worker]] | 대기열 워커 — 하나씩 차례로 돌린다 |
| [[#pipeline.run]] | 첫 단계부터 |
| [[#pipeline.resume]] | 행의 단계부터 |
| [[#pipeline.transcribe_stage]] | 조각 병렬 받아쓰기 |
| [[#pipeline.error_kind]] | 예외 → `ErrorKind` |
| [[#pipeline.reason_of]] | 예외 → 실패 이유 한 줄(한국어) |

---

## 2. 함수

#### JobService.estimate 사전 안내 예상치

**시그니처** `async def estimate(video: Video) -> Estimate | None`

근거: [[VA-SEQ-001#SEQ-1]] 27~31번 · [[VA-API-001#POST/api/videos]] 7번 · [[VA-UC-001#UC-S1]] 5번 · [[VA-UI-002#UI-2]]

**입력** `video` — `register`가 돌려준 DTO. `status` · `duration_sec` · `has_captions` · `source_kind`를 본다

**처리**
1. if `video.status != registered` → `→ None` (작업이 있다. 라우터는 분기 없이 그대로 응답에 싣는다)
2. `models = SettingsService.current_models()` — 모델 이름과 단가
3. `needs_stt = not video.has_captions`
4. if `not needs_stt` → `chunks = None` · `concurrency = None` · `stt_minutes = None` · `stt_price_per_min = None` · `stt_cost = 0` · `seconds = config.TEXT_EST_SEC`
   else → `chunks = ceil(duration_sec / config.CHUNK_SEC)` · `concurrency = config.STT_CONCURRENCY` · `stt_minutes = duration_sec / 60`(소수 첫째 자리) · `stt_price_per_min = models.stt.price.per_min_usd` · `stt_cost = stt_minutes × stt_price_per_min` · `seconds = ceil(chunks / concurrency) × config.CHUNK_EST_SEC + config.TEXT_EST_SEC` (+ 로컬 영상이면 추출, YouTube면 내려받기, 로컬 음성이면 mp3 변환 몫으로 `duration_sec / 60`초를 더한다 — 로컬 음성도 받아쓰기 단계가 조각을 나누기 전에 바꾼다, [[#pipeline.run]])
5. `in_tokens = duration_sec / 60 × config.TOKENS_PER_MIN` · `text_cost = (in_tokens × 3 × models.text.price.input_per_mtok_usd + 6000 × models.text.price.output_per_mtok_usd) / 1_000_000` — 스크립트를 세 번(요약 · 챕터 · 추천 질문) 보내고 출력은 합쳐 6천 토큰으로 본다
6. `→ Estimate(needs_stt, seconds, chunks, concurrency, stt_minutes, stt_price_per_min, stt_cost_usd=round(stt_cost, 4), text_cost_usd=round(text_cost, 4), total_cost_usd=round(stt_cost + text_cost, 2), stt_model=models.stt.id, text_model=models.text.id)`

**출력** `Estimate` 또는 `None`. 화면은 숫자를 그대로 보이고 합계에 '약'을 붙인다

**호출하는 것** `SettingsService.current_models`

**테스트 관점** 자막 있음 50분 → `chunks=None`, `stt_cost=0`, `seconds=60`, `text_cost>0` · 로컬 150분 → `chunks=15`, `concurrency=3`, `stt_minutes=150`, `stt_cost=0.9`(단가 0.006) · 상태가 `in_progress`면 `None` · 단가를 바꾸면 값이 따라 바뀐다(설정에서 읽는다)

---

#### JobService.start 작업 시작

**시그니처** `async def start(video: Video) -> Job`

근거: [[VA-SEQ-001#SEQ-2]] · [[VA-API-001#POST/api/videos/{id}/job]] · [[VA-UC-001#UC-H0]] 3번 · 3b · [[VA-DOM-003#analysis_jobs]] `queued_at`

**입력** `video` — 라우터가 `VideoService.get`으로 받아 넘긴 DTO

**처리**
1. `SettingsService.require_key()` · if 없음 → `! key-missing` · if 확인 실패 → `! key-invalid`
2. `DB: analysis_jobs where video_id` · if 있음 → `! job-exists {job_id, job_status}` — 실패한 작업은 `retry`로, 끝난 작업은 다시 만들지 않는다
3. `stages = stages_for(video)` · `est = estimate(video)`(여기서는 `status`를 보지 않는다 — 작업이 없다는 것을 2에서 확인했다) · `models = SettingsService.current_models()`
4. **트랜잭션**: `DB: analysis_jobs insert(video_id, status=queued, stage=pending, stages, progress_pct=0, est_seconds=est.seconds, est_cost_usd=est.total_cost_usd, concurrency=config.STT_CONCURRENCY, stt_model=models.stt.id if needs_stt else None, text_model=models.text.id, stage_durations_sec={}, started_at=now, queued_at=now, stage_started_at=now)` — **늘 `queued`다.** 다른 영상이 도는지 보지 않는다. `running`으로 바꾸는 것은 워커 하나라([[#JobService.claim_next]]) 시작하는 길이 하나다 · 커밋이 영상 하나에 작업 하나인 부분 unique([[VA-DOM-003]] 3장)에 걸리면 — 2와 4 사이에 같은 영상의 [분석 시작]이 하나 더 들어왔다(탭 둘) — 롤백하고 먼저 들어간 작업으로 `! job-exists`
5. 커밋 뒤 `wake()` · `await asyncio.sleep(0)` — 워커에게 한 번 양보한다. 도는 작업이 없으면 워커가 이 틈에 꺼내 `running`이 된다(보장은 아니다 — 안 됐으면 `queued`로 나가고 첫 폴링에서 바뀐다)
6. `row = DB: analysis_jobs where id`(다시 읽기) · `→ to_job(row, [], queue_position(row))`

**출력** `Job`(`status=running` 또는 `queued` · `stage=pending` · `chunks=None` · `queued`면 `queue_position`)

**예외** `key-missing` · `key-invalid` · `job-exists`

**호출하는 것** `SettingsService.require_key` · `SettingsService.current_models` · [[#JobService.stages_for]] · [[#JobService.estimate]] · [[#JobService.wake]] · [[#JobService.queue_position]] · [[#JobService.to_job]]

**테스트 관점** 응답이 파이프라인을 기다리지 않는다(깨우기만 한다) · 같은 영상 두 번 → 둘째는 `job-exists` · 2에서 못 본 같은 영상의 작업이 커밋 때 부분 unique에 걸리면 `job-exists`이고 행은 하나 · 다른 영상이 `running`이어도 **거절하지 않고** `queued` · `queue_position=1` · 대기 작업이 하나 더 있으면 2 · 자막 있는 YouTube → `stt_model=None`, `stages` 4개 · 행에 그때의 모델 이름 · 동시 수 · 예상치가 남는다 · 키가 없으면 행이 안 생긴다

---

#### JobService.progress 폴링 응답

**시그니처** `async def progress(video_id: int) -> Job`

근거: [[VA-SEQ-001#SEQ-5]] · [[VA-API-001#GET/api/videos/{id}/job]] · [[VA-UC-001#UC-S6]]

**처리**
1. `row = DB: analysis_jobs where video_id order by started_at desc limit 1` · if 없음 → `! not-found {resource: job, id: video_id}`
2. `chunks = DB: audio_chunks where job_id order by seq` (`result` 컬럼은 읽지 않는다 — 폴링 응답에 안 나간다)
3. `→ to_job(row, chunks, queue_position(row))`

**출력** `Job`. 1초마다 불리므로 쿼리 둘로 끝난다(대기 중일 때만 차례를 세는 쿼리 하나가 더 있다)

**예외** `not-found`(job)

**호출하는 것** [[#JobService.to_job]] · [[#JobService.queue_position]]

**테스트 관점** 작업 없는 영상 → `not-found`에 `resource=job` · 대기 중이면 `status=queued` · `queue_position` · `remaining_sec=None` · `chunks=None` · 조각 30개 중 12 완료 · 3 진행 중이면 `chunks.done=12` `in_flight=3` `waiting=15` `next_seq=13` · `result`를 select하지 않는다(쿼리 로그)

---

#### JobService.retry 실패 작업 재개

**시그니처** `async def retry(video: Video) -> Job`

근거: [[VA-SEQ-001#SEQ-6]] · [[VA-API-001#POST/api/videos/{id}/job/retry]] · [[VA-UC-001#UC-S3]] 3a3 · [[VA-UC-001#UC-S6]] 1a

**처리**
1. `SettingsService.require_key()` · `! key-missing` · `! key-invalid`
2. `row = DB: analysis_jobs where video_id order by started_at desc limit 1` · if 없음 → `! not-found {resource: job}`
3. if `row.status != failed` → `! job-not-failed {job_status}`
4. **트랜잭션**: `DB: analysis_jobs update status=queued · queued_at=now · error_kind=error_reason=error_chunk_seq=error_attempts=null` (같은 행. `stage` · `stages` · `started_at` · 모델은 그대로. `stage`가 `pending`이 아니라서 워커가 `resume`으로 돌린다) · `DB: audio_chunks where job_id and state = failed → state = waiting` (실패 조각도 다시 보낸다. `attempts`는 누적 이력이라 그대로 두고, 상한은 다음 실행에서 새로 센다 — [[#pipeline.transcribe_stage]] 3번)
5. 커밋 뒤 `wake()` · `await asyncio.sleep(0)` — `start` 5번과 같다
6. 행을 다시 읽어 `→ to_job(row, chunks, queue_position(row))`

**출력** `Job`(`status=running` 또는 `queued`, 실패 알림이 사라질 값). 다른 영상이 돌고 있으면 대기열 **끝**에서 기다린다 — `queued_at`을 지금으로 적기 때문이다

**예외** `key-missing` · `key-invalid` · `not-found` · `job-not-failed`

**호출하는 것** `SettingsService.require_key` · [[#JobService.wake]] · [[#JobService.queue_position]] · [[#JobService.to_job]]

**테스트 관점** `running`인 작업에 부르면 `job-not-failed` · 재개 뒤 `id` · `started_at`이 같고 `queued_at`만 바뀐다 · 다른 영상이 돌고 있고 하나가 더 기다리면 `queue_position=2` · `error_*`가 비워진다 · `failed` 조각이 `waiting`으로 돌아가고 `done` 조각은 그대로 · 목록 순서가 바뀌지 않는다

---

#### JobService.cancel 태스크 취소

**시그니처** `async def cancel(video_id: int) -> None`

근거: [[VA-SEQ-001#SEQ-11]] · [[VA-API-001#DELETE/api/videos/{id}]] · [[VA-UI-001]] 7장 13

**처리**
1. `task = self.tasks.get(video_id)` · if 없음 → `→ None` (돌고 있지 않다 — 대기 중 · 실패 · 완료. 대기 중인 작업은 행이 지워지면 대기열에서 빠진 것이다)
2. `task.cancel()` · `await task`를 `CancelledError`를 삼키며 기다린다 — 파이프라인이 열어 둔 세션이 닫힐 때까지
3. `→ None`. 행은 건드리지 않는다 — 라우터가 이어서 부르는 `VideoService.delete`의 cascade가 지운다. **워커를 깨우지 않는다** — 라우터가 삭제 뒤에 [[#JobService.wake]]를 부른다(시퀀스 되먹임 #8)

**출력** 없음

**호출하는 것** 없음

**테스트 관점** 돌고 있는 작업을 취소하면 태스크가 끝나 있다(`task.done()`) · 취소 뒤 DB에 반쯤 쓰인 행이 없다 · 없는 영상에 불러도 예외 없음

---

#### JobService.latest 최근 작업 요약

**시그니처** `async def latest(video_id: int) -> JobSummary | None`

**처리** `DB: analysis_jobs where video_id order by started_at desc limit 1` · `DB: audio_chunks where job_id`의 집계(`done` 수 · 전체 수) · `→ JobSummary(id, status, stage, queue_position=queue_position(row), progress_pct, chunks_done, chunks_total, failed_chunk_seq=error_chunk_seq, started_at, finished_at)` · 없으면 `None`

**테스트 관점** 조각 없는 작업 → `chunks_done=chunks_total=None` · 실패 작업 → `failed_chunk_seq`가 채워진다 · 대기 작업 → `queue_position`

---

#### JobService.latest_by_videos 여러 영상의 최근 작업

**시그니처** `async def latest_by_videos(video_ids: list[int]) -> dict[int, JobSummary]`

근거: [[VA-SEQ-001#SEQ-7]] · [[VA-API-001#GET/api/videos]]

**처리** `DB: analysis_jobs distinct on (video_id) where video_id in … order by video_id, started_at desc` 한 쿼리 · 조각 집계도 `job_id in …`으로 한 쿼리 · 결과에 `queued`가 있으면 `DB: analysis_jobs where status = queued order by queued_at`의 id 목록을 한 번 읽어 순번을 매긴다(행마다 세지 않는다) · `→ {video_id: JobSummary}`. 작업 없는 영상은 키가 없다

**테스트 관점** 영상 50개에 쿼리 둘(대기 작업이 있으면 셋) · 영상마다 최근 것 하나만 · 빈 목록 → `{}`

---

#### JobService.mark_stage 단계 전환

**시그니처** `async def mark_stage(job_id: int, stage: JobStage) -> None`

근거: [[VA-SEQ-001#SEQ-3]] · [[VA-UC-001#UC-S6]] 1 · 3번 · 0장 진행률 가중치

**처리** — **트랜잭션**
1. `row = DB: analysis_jobs where id`
2. if `row.stage != pending` → `row.stage_durations_sec[row.stage] += round(now − row.stage_started_at)` — 끝난 단계의 걸린 시간. 다시 시도로 같은 단계를 여러 번 돌면 더해 간다(없으면 0부터)
3. `row.stage = stage` · `row.stage_started_at = now`
4. `row.progress_pct = 완료한 단계들의 가중치 합`(0장 표. `stages`에서 `stage` 앞에 있는 것들) · if `stage == transcribe`이고 조각 행이 있음(다시 시도) → `+ 70 × (done 수 / 전체 수)` — 진행률이 뒤로 가지 않게([[#JobService.mark_chunk]]와 같은 식)
5. `DB: update`

**출력** 없음

**테스트 관점** 자막 있는 YouTube에서 `summarize`로 바꾸면 `stage_durations_sec[download]`가 생기고 `progress_pct=25` · 받아쓰기 있는 작업에서 `summarize`로 바꾸면 `progress_pct=70+7`(download 7.5 → 반올림 규칙 한 가지로) · `pending`에서 첫 단계로 갈 때는 duration이 안 생긴다 · 30개 중 15 완료에서 받아쓰기로 다시 들어가면 진행률이 받아쓰기 몫의 절반부터 · 같은 단계를 두 번 돌면 걸린 시간이 더해진다

---

#### JobService.plan_chunks 조각 행 생성

**시그니처** `async def plan_chunks(job_id: int, plans: list[ChunkPlan]) -> None`

근거: [[VA-SEQ-001#SEQ-4]] 12~13번 · [[VA-UC-001#UC-S3]] 1~2번

**처리** **트랜잭션**: `DB: audio_chunks where job_id` · if 이미 있음 → `→ None`(재개 때는 만들지 않는다) · else → `DB: insert ×N (job_id, seq, offset_sec, duration_sec, path, state=waiting, attempts=0)` · `→ None`

**테스트 관점** 30개 계획 → 30행, `seq` 1~30, 전부 `waiting` · 두 번 불러도 행이 늘지 않는다

---

#### JobService.mark_chunk 조각 상태 전이

**시그니처** `async def mark_chunk(job_id: int, seq: int, state: ChunkState, result: list[SttSegment] | None = None) -> None`

근거: [[VA-SEQ-001#SEQ-4]] 17~28번 · [[VA-DOM-002#AudioChunk]] · [[VA-DOM-003#audio_chunks]] · 시퀀스 되먹임 #1 · #2

**처리** — **트랜잭션**
1. `chunk = DB: audio_chunks where job_id and seq`
2. if `state == in_flight` → `chunk.attempts += 1`
   elif `state == done` → `chunk.done_at = now` · `chunk.result = result` · `chunk.path`의 파일은 파이프라인이 지운다(여기서는 `path = None`으로) · `row.progress_pct = 완료 단계 가중치 합 + 70 × (done 수 / 전체 수)`
   else (`waiting` · `failed`) → 상태만
3. `chunk.state = state` · `DB: update`

**출력** 없음

**테스트 관점** `in_flight` 두 번 → `attempts=2` · `done`이면 `done_at` · `result` · `path=None`이고 `progress_pct`가 오른다 · `failed`는 `attempts`를 안 올린다 · 30개 중 15 완료 → `progress_pct`가 받아쓰기 몫의 절반

---

#### JobService.finish 완료

**시그니처** `async def finish(job_id: int) -> None`

**처리** **트랜잭션**: `mark_stage`와 같은 방식으로 마지막 단계의 duration 기록 · `status=done` · `progress_pct=100` · `finished_at=now` · `DB: update`. `finished_at`이 곧 영상의 분석 완료 시각([[VA-DOM-002#Video]])

**테스트 관점** `finish` 뒤 `VideoService.get`의 `status=analyzed`, `analyzed_at`이 같다

---

#### JobService.fail 실패

**시그니처** `async def fail(job_id: int, error: JobError) -> None`

근거: [[VA-SEQ-001#SEQ-4]] · [[VA-UC-001#UC-S6]] 1a · [[VA-API-001]] 2장 마지막 문단

**처리** **트랜잭션**: `status=failed` · `error_kind=error.kind` · `error_reason=error.reason` · `error_chunk_seq=error.chunk_seq` · `error_attempts=error.attempts` · `stage`는 실패한 단계 그대로 · `progress_pct` 그대로 · `DB: update`

**테스트 관점** 실패 뒤 `progress`의 `error`가 채워지고 `stage`가 실패 단계 · `progress_pct`가 멈춘 값

---

#### JobService.fail_orphans 시작 때 running 정리

**시그니처** `async def fail_orphans() -> int`

근거: [[VA-SEQ-001#SEQ-13]] · [[VA-DOM-002]] 5장 8 · 시퀀스 되먹임 #3

**처리** **트랜잭션**: `rows = DB: analysis_jobs where status = running` · 행마다 `status=failed` · `error_kind=unknown` · `error_reason='서버가 다시 시작됨'` · `error_chunk_seq=None` · `error_attempts=1`(돌던 단계를 한 번 보낸 것 — 응답의 `JobError.attempts`는 비지 않는 정수다, [[VA-API-001]] 4장) · `DB: audio_chunks where job_id and state = in_flight → waiting` · `→ len(rows)`. `queued`는 건드리지 않는다 — 기다리던 것이라 워커가 뜨면 이어서 돈다. `main.py` lifespan이 **워커를 띄우기 전에** 부른다 — 거꾸로면 죽은 `running` 행 때문에 워커가 아무것도 꺼내지 못한다([[VA-SEQ-001#SEQ-13]])

**테스트 관점** `running` 하나 → `failed`, `error_attempts=1`, 반환 1(둘은 부분 unique 인덱스가 막아 데이터로도 만들 수 없다) · `in_flight` 조각이 `waiting` · `done` 조각은 그대로 · `queued` 작업은 그대로 · 없으면 0

---

#### JobService.claim_next 대기열에서 다음 작업을 꺼낸다

**시그니처** `async def claim_next() -> AnalysisJobRow | None`

근거: [[VA-SEQ-001#SEQ-14]] · [[VA-DOM-002#JobService]] 규칙 · [[VA-DOM-003#analysis_jobs]] 부분 unique · 대기열 인덱스 · [[VA-UC-001#UC-H0]] 3b

**처리** — **트랜잭션**
1. `DB: analysis_jobs where status = running limit 1` · if 있음 → `→ None` (동시에 도는 분석은 하나)
2. `row = DB: analysis_jobs where status = queued order by queued_at limit 1 for update skip locked` · if 없음 → `→ None`
3. `row.status = running` · `row.stage_started_at = now` · `DB: update` · if 부분 unique 위반(`running` 둘 — 서버가 두 번 뜬 경우) → 롤백하고 `→ None`
4. `→ row`

**출력** `running`으로 바뀐 행 또는 `None`. `stage`는 건드리지 않는다 — `pending`이면 처음 도는 작업, 아니면 다시 시도한 작업이다

**호출하는 것** 없음

**테스트 관점** `running`이 있으면 `queued`가 있어도 `None` · `queued` 셋이면 `queued_at`이 가장 이른 것 · 다시 시도한 작업(`queued_at`이 늦다)은 먼저 기다리던 작업 뒤 · 꺼낸 행의 `stage_started_at`이 지금 · 두 번 연달아 부르면 둘째는 `None`

---

#### JobService.wake 워커를 깨운다

**시그니처** `def wake() -> None`

근거: [[VA-SEQ-001#SEQ-2]] · [[VA-SEQ-001#SEQ-6]] · [[VA-SEQ-001#SEQ-11]] · 시퀀스 되먹임 #8

**처리** `self.work_event.set()`. 부르는 곳은 셋 — `start` · `retry`(커밋 **뒤**), 그리고 삭제 라우터가 `VideoService.delete` **뒤**에. `cancel`은 부르지 않는다 — 행이 아직 있을 때 깨우면 워커가 곧 지워질 행을 꺼내거나, 취소된 작업의 `running` 행 때문에 아무것도 못 꺼내고 다시 잠든다

**테스트 관점** 도는 작업을 지운 뒤 `wake` → 다음 대기 작업이 `running`이 된다 · `wake` 없이도 `config.WORKER_IDLE_SEC` 안에 시작된다(아래 `wait_for_work`)

---

#### JobService.wait_for_work 할 일이 생길 때까지 기다린다

**시그니처** `async def wait_for_work() -> None`

근거: [[VA-SEQ-001#SEQ-14]] · [[VA-DOM-002]] 5장 8(메모리에는 깨우는 신호만)

**처리** `await asyncio.wait_for(self.work_event.wait(), timeout=config.WORKER_IDLE_SEC)` · `TimeoutError`는 삼킨다 · `→ None`. 신호를 놓쳐도 `WORKER_IDLE_SEC`마다 한 번은 대기열을 본다. `work_event.clear()`는 워커가 `claim_next`를 부르기 **전에** 한다([[#pipeline.worker]]) — 확인과 잠들기 사이에 온 신호를 잃지 않으려고

**테스트 관점** `wake` 뒤 곧바로 돌아온다 · 신호가 없어도 `WORKER_IDLE_SEC` 뒤 돌아온다 · 예외가 밖으로 나가지 않는다

---

#### JobService.queue_position 대기열에서의 차례

**시그니처** `async def queue_position(row: AnalysisJobRow) -> int | None`

근거: [[VA-API-001]] 4장 `Job.queue_position` · 5장 8 · [[VA-UI-002#UI-1]] 6.6 '대기 중 · {n}번째' · [[VA-UI-002#UI-3]] 3.2 '앞 영상 {n}개가 끝나면 시작해요'

**처리** if `row.status != queued` → `→ None` · else → `→ (DB: count analysis_jobs where status = queued and queued_at < row.queued_at) + 1`. 1이 바로 다음 차례다. 도는 작업이 하나 있고 자기가 맨 앞이면 1이고, 그때 '앞 영상 1개'와 '1번째'가 같은 수다

**테스트 관점** `queued` 셋의 차례가 1 · 2 · 3 · 맨 앞 것이 `running`이 되면 나머지가 1 · 2 · `running` · `failed` · `done`은 `None`

---

#### JobService.stages_for 출처 → 단계 목록

**시그니처** `def stages_for(video: Video) -> list[JobStage]`

근거: [[VA-UC-001#UC-S2]] · [[VA-UC-001#UC-H2]] 2b · [[VA-UI-002#UI-3]] 규칙(출처마다 필요한 단계만)

**처리** if `youtube and has_captions` → `[download, summarize, chapter, suggest]` · elif `youtube` → `[download, transcribe, summarize, chapter, suggest]` · elif `local and 확장자 ∈ {mp3, m4a, wav}` → `[transcribe, summarize, chapter, suggest]` · else → `[extract, transcribe, summarize, chapter, suggest]`

**테스트 관점** 네 출처 각각 · 로컬 음성 판정은 `origin`의 확장자

---

#### JobService.remaining_sec 남은 시간

**시그니처** `def remaining_sec(row: AnalysisJobRow, chunks: list[AudioChunkRow]) -> int | None`

근거: [[VA-UC-001#UC-S6]] 2번 · [[VA-UI-002#UI-3]] 3.2 · [[VA-UI-001]] 8장(조각이 없는 단계)

**처리**
- if `row.status != running` → `→ None`
- elif `row.stage == transcribe`이고 조각 행이 있음 → `left = done이 아닌 조각 수` · `now_done = [c for c in chunks if c.state == done and c.done_at ≥ row.stage_started_at]` — **이번 실행에서 끝난 조각만**(다시 시도 뒤 이전 실행의 조각까지 세면 속도가 부푼다) · if `now_done` 비어 있음 → `→ ceil(left / row.concurrency) × config.CHUNK_EST_SEC` · else → `rate = len(now_done) / (now − row.stage_started_at)`(초당 조각) · `→ ceil(left / rate)`
- elif `row.stage == transcribe`이고 조각 행이 없음(음성을 나누는 중) → 아래 조각 없는 단계와 같다
- else → `→ max(row.est_seconds − Σ row.stage_durations_sec.values() − (now − row.stage_started_at), 0)` — 예상 전체에서 지난 시간을 뺀다. 0이 되면 화면이 '약 0초'가 아니라 값을 비운다([[VA-API-001#GET/api/videos/{id}/job]] — 0이면 화면이 비운다)

**테스트 관점** 30개 중 12 완료가 4분 걸렸으면 남은 18개는 6분 · 첫 조각 완료 전에는 예상치 기반 · 요약 단계에서 예상보다 오래 걸리면 0 · 다시 시도 뒤 이전 실행의 완료 조각은 속도에 안 든다 · 조각 행이 아직 없으면 예상 전체 − 지난 시간

---

#### JobService.to_job 행 → Job

**시그니처** `def to_job(row: AnalysisJobRow, chunks: list[AudioChunkRow], queue_position: int | None = None) -> Job`

근거: [[VA-API-001#GET/api/videos/{id}/job]]의 요소 ↔ 필드 표

**처리**
1. `stage_index = row.stages.index(row.stage) + 1` (`pending`이면 1)
2. `chunks_dto` = if `chunks` 비어 있음 → `None` · else → `Chunks(total, done, in_flight, failed, waiting 수, next_seq=state != done인 첫 seq 또는 None, items=[Chunk(seq, state) …])`
3. `error` = if `row.status == failed` → `JobError(row.error_kind, row.error_reason, row.error_chunk_seq, row.error_attempts)` · else → `None`
4. `→ Job(id, video_id, status, stage, queue_position, stages, stage_index, progress_pct, remaining_sec=remaining_sec(row, chunks), chunks=chunks_dto, concurrency=row.concurrency if transcribe in stages else None, models=Models(stt=row.stt_model, text=row.text_model), error, est_seconds, est_cost_usd, stage_durations_sec, started_at, finished_at)`

**호출하는 것** [[#JobService.remaining_sec]]. `queue_position`은 DB를 읽어야 해서 부르는 쪽이 세어 넘긴다 — 이 함수는 순수 함수로 둔다

**테스트 관점** `stages` 4개 · `stage=chapter`면 `stage_index=3` · 실패 작업의 `error.chunk_seq`가 화면 k · `next_seq`가 r(k와 다를 수 있다 — 16번 실패, 17번 완료면 `next_seq=16`)

---

#### pipeline.worker 대기열 워커

**시그니처** `async def worker(load_video: Callable[[int], Awaitable[Video | None]]) -> None`

근거: [[VA-SEQ-001#SEQ-14]] · [[VA-SEQ-001#SEQ-13]] · [[VA-DOM-002]] 5장 8 · 시퀀스 되먹임 #7

**입력** `load_video` — 영상 id로 `Video` DTO를 주는 함수. `main.py`가 `VideoService.get`을 감싸 넘긴다(없으면 `None`). 작업 묶음은 영상 묶음을 import하지 않는다 — 조립하는 곳(`main.py`)만 둘을 안다. 작업 행에 영상 값을 복사해 두는 안은 같은 값이 두 테이블에 생겨 버렸다(3장)

**처리** — `main.py` lifespan이 태스크 하나로 띄운다. 끝없이 돈다
1. `JobService.work_event.clear()`
2. `row = JobService.claim_next()`(짧은 세션) · if `None` → `JobService.wait_for_work()` · 1로. `claim_next`가 예외면(DB가 잠깐 안 됨 등) 로그를 남기고 `None`과 같게 — 워커는 죽지 않는다
3. `video = load_video(row.video_id)` · if `None`(그 사이 지워짐 — 행도 cascade로 없다) → 1로 · if 예외 → 그 작업을 `fail`(`error_kind(e)`)로 접고 1로 — `running`으로 꺼낸 채 두면 대기열이 막힌다
4. `coro = run(row.id, video) if row.stage == pending else resume(row.id, video)` · `task = asyncio.create_task(coro)` · `JobService.tasks[video.id] = task`
5. `await task`를 `CancelledError`(삭제가 취소한 것) · `Exception`을 삼키며 기다린다 · `JobService.tasks.pop(video.id, None)` · 태스크가 예외로 끝났으면(`run`이 `fail`로 접지 못한 경우) 그 작업을 `fail`(`error_kind(e)`)로 접는다 — `running`으로 남으면 대기열이 막힌다 · 1로
6. **워커 자신이** 취소되면(서버 종료) 돌던 `task`도 취소하고 끝난다. 그 작업은 `running`인 채 남고 다음 시작 때 `fail_orphans`가 되돌린다

**출력** 없음. 끝나지 않는다

**호출하는 것** [[#JobService.claim_next]] · [[#JobService.wait_for_work]] · [[#pipeline.run]] · [[#pipeline.resume]]

**테스트 관점** 가짜 `run`으로: `queued` 둘을 넣으면 차례로 하나씩만 돈다(동시에 `running` 둘이 없다) · 첫 작업이 예외로 끝나도 둘째가 시작된다(첫 작업은 `failed`) · `stage != pending`인 행은 `resume`으로 · `load_video`가 `None`이면 건너뛴다 · 워커를 취소하면 돌던 태스크도 취소된다 · 5에서 구분할 것 — 삼키는 `CancelledError`는 `task`의 것이고, 워커 자신의 취소는 다시 던진다(`task.cancelled()`로 가른다)

---

#### pipeline.run 첫 단계부터

**시그니처** `async def run(job_id: int, video: Video) -> None`

근거: [[VA-SEQ-001#SEQ-3]] · [[VA-SEQ-001#SEQ-4]] · [[VA-UC-001#UC-H0]] 4~7번 · [[VA-UC-001#UC-S2]] · [[VA-UC-001#UC-S4]]

**처리** — 워커([[#pipeline.worker]])가 띄운 백그라운드 태스크 안. 서비스 호출마다 세션 하나
1. `stages = DB: analysis_jobs where id`의 `stages`(짧은 세션) · `tmp = config.DATA_DIR / "tmp" / str(video.id)` · `FS: mkdir`
2. `for stage in stages:` `JobService.mark_stage(job_id, stage)` 뒤 단계 실행 —
   - `download` · if `video.has_captions` → `(lines, lang, kind) = AudioSourcePort.captions(video.source_id)` · if `None`(등록 뒤 자막이 사라짐 — 단계 목록에 받아쓰기가 없다) → `! YtdlpError('자막을 찾지 못했습니다', kind=unavailable)`, `youtube`로 접힌다 · `AnalysisService.save_transcript(video.id, caption_manual if kind == manual else caption_auto, lang, None, lines)` · else → `audio = AudioSourcePort.download_audio(video.source_id, tmp)`
   - `extract` → `audio = AudioSourcePort.extract_audio(config.INBOX_DIR / video.origin, tmp)`
   - `transcribe` → if `audio` 없음(로컬 음성 — 추출 단계가 없다) → `audio = AudioSourcePort.extract_audio(config.INBOX_DIR / video.origin, tmp)` — mp3로 바꾼다. `ffmpeg.cut`은 다시 인코딩하지 않아 wav · m4a를 그대로 자를 수 없고, 조각이 하나면 음성 파일이 곧 조각이라 받아쓰기가 끝나면 지워진다 — inbox 원본은 읽기만 한다 · `transcribe_stage(job_id, video, audio, tmp)`
   - `summarize` → `AnalysisService.generate_summary(video)`
   - `chapter` → `AnalysisService.generate_chapters(video)`
   - `suggest` → `AnalysisService.generate_questions(video)`
3. `JobService.finish(job_id)` · `FS: rmtree(tmp, ignore_errors=True)`
4. 예외 처리 — `except CancelledError → raise`(아무것도 쓰지 않는다. 조각 파일도 둔다) · `except Exception as e → JobService.fail(job_id, JobError(error_kind(e), reason=reason_of(e), chunk_seq=None, attempts=1))` · 내려받기 · 추출 실패면 `FS: rmtree(tmp)`([[VA-UC-001#UC-S2]] 1d). 받아쓰기 실패는 `transcribe_stage`가 `chunk_seq` · `attempts`를 채운 `JobError`로 던진다

**출력** 없음. 결과는 행에

**호출하는 것** [[#JobService.mark_stage]] · [[#JobService.finish]] · [[#JobService.fail]] · [[#pipeline.transcribe_stage]] · [[#pipeline.error_kind]] · [[#pipeline.reason_of]] · `AudioSourcePort.captions` · `download_audio` · `extract_audio` · `AnalysisService.save_transcript` · `generate_summary` · `generate_chapters` · `generate_questions`

**테스트 관점** 가짜 포트로: 자막 있는 YouTube → 단계 4개 지나 `done`, OpenAI 받아쓰기 호출 0회 · 요약 단계에서 예외 → `failed`, `stage=summarize`, 스크립트는 남아 있다 · 취소 → 행 상태가 안 바뀌고 예외가 밖으로 · 끝나면 `data/tmp/{id}`가 없다 · 내려받기 실패 → `tmp` 폴더가 없다 · 자막이 사라져 `captions`가 None → `failed`, `error.kind=youtube` · 로컬 음성(wav) → `extract_audio`로 바꾼 `tmp` 안 mp3를 나누고, inbox 원본은 그대로 남는다

---

#### pipeline.resume 행의 단계부터

**시그니처** `async def resume(job_id: int, video: Video) -> None`

근거: [[VA-SEQ-001#SEQ-6]] 21~26번 · [[VA-UC-001#UC-S3]] 3a3 · [[VA-UC-001#UC-S4]] 1b

**처리**
1. `row = DB: analysis_jobs where id` · `start_at = row.stages.index(row.stage)` — 실패한 단계
2. `run`과 같은 반복을 `stages[start_at:]`부터. 단 —
   - `download` · `extract`에서 실패했으면 처음부터와 같다(임시 파일이 지워졌다)
   - `transcribe`에서 실패했으면 조각 행이 있을 때는 음성 파일이 필요 없다 — `transcribe_stage`는 `done`이 아닌 조각만, 남아 있는 조각 파일로 보낸다. 조각 행이 없으면(나누다 멈춤) `audio = tmp / audio.mp3`(내려받기 · 추출 · 변환이 쓰는 이름) · 없으면 로컬 음성은 받아쓰기 단계가 다시 바꾸고([[#pipeline.run]]), 그 밖은 `stages`에서 앞 단계(`download` · `extract`)를 찾아 그 단계부터
   - `summarize` 이후 실패는 스크립트가 있으므로 그 단계부터
3. 마무리 · 예외 처리는 `run`과 같다

**호출하는 것** [[#pipeline.run]]의 것 전부 · [[#pipeline.transcribe_stage]]

**테스트 관점** 16번 조각 실패 상태에서 재개 → 1~15번은 OpenAI에 안 보낸다(가짜 포트 호출 기록) · 요약 실패에서 재개 → 받아쓰기를 안 한다 · 음성 파일이 지워진 채 받아쓰기 재개 → 추출부터 다시

---

#### pipeline.transcribe_stage 조각 병렬 받아쓰기

**시그니처** `async def transcribe_stage(job_id: int, video: Video, audio: str, tmp: str) -> None`

근거: [[VA-SEQ-001#SEQ-4]] 12~30번 · [[VA-UC-001#UC-S3]] 전부 · [[VA-UI-002#UI-3]] 숫자 규칙 · 시퀀스 되먹임 #1 · #4

**처리**
1. `chunks = DB: audio_chunks where job_id` · if 비어 있음 → `plans = AudioSplitPort.split(audio, tmp)` · `JobService.plan_chunks(job_id, plans)` · 다시 읽는다
2. `todo = [c for c in chunks if c.state != done]` · `sem = Semaphore(row.concurrency)` · `models = row.stt_model` · 조각마다 `base = c.attempts`(이번 실행을 시작할 때의 누적 횟수)
3. 조각마다 태스크 — `async def one(c):` `async with sem:` `loop:` `JobService.mark_chunk(job_id, c.seq, in_flight)` · `try: segs = SttPort.transcribe(c.path, model)` · `JobService.mark_chunk(job_id, c.seq, done, segs)` · `FS: remove(c.path)` · `return` · `except Exception as e:` `sent = attempts(방금 올린 값) − base`(**이번 실행에서 보낸 횟수** — 다시 시도하면 상한을 새로 센다) · if `sent < config.CHUNK_MAX_ATTEMPTS` → `mark_chunk(waiting)` · 계속(같은 조각을 다시) · else → `mark_chunk(failed)` · `raise ChunkFailed(seq=c.seq, sent, cause=e)`
4. `results = gather(one(c) for c in todo, return_exceptions=True)` — **하나가 실패해도 나머지를 끝까지 기다린다.** 그래야 완료 수(j)와 다음 조각(r)이 맞다
5. if `ChunkFailed`가 하나라도 있음 → 가장 작은 `seq`의 것으로 `raise JobFailure(JobError(kind=error_kind(cause), reason=reason_of(cause), chunk_seq=seq, attempts=sent))` — `run`이 받아 그 `JobError` 그대로 `fail`. `attempts`는 이번 실행에서 보낸 횟수라 화면 문구 '{n}번 보냈지만'이 상한과 같다
6. `all = DB: audio_chunks where job_id order by seq`(이번엔 `result` 포함) · `lines = []` · 조각마다 `result`의 `SttSegment`에 `offset_sec`을 더해 `CaptionLine(start_sec, end_sec, text)`으로 · `language`는 첫 조각의 `language`
7. `AnalysisService.save_transcript(video.id, stt, language, row.stt_model, lines)`

**출력** 없음

**예외** `JobFailure`(조각 상한 초과) · 그 밖의 예외는 `run`이 `unknown`으로 접는다

**호출하는 것** [[#JobService.plan_chunks]] · [[#JobService.mark_chunk]] · [[#pipeline.error_kind]] · [[#pipeline.reason_of]] · `AudioSplitPort.split` · `SttPort.transcribe` · `AnalysisService.save_transcript`

**테스트 관점** 가짜 STT가 16번을 세 번 실패시키면 → `failed` 조각 하나, `attempts=3`, 나머지는 끝까지 돌아 `done` · `JobError.chunk_seq=16` · 재개 시 `done` 조각은 호출 안 됨 · 동시에 도는 태스크가 `concurrency`를 넘지 않는다(가짜 STT가 동시 수를 센다) · 이어 붙인 구간의 시각이 오프셋만큼 밀린다(2번째 조각 0초 → 600초) · `done` 조각의 파일은 지워지고 `waiting` 조각의 파일은 남는다 · 다시 시도 뒤 `attempts=3`인 실패 조각도 다시 3번까지 보내고, 또 실패하면 `JobError.attempts=3`(누적 6)

---

#### pipeline.error_kind 예외 → ErrorKind

**시그니처** `def error_kind(e: BaseException) -> ErrorKind`

근거: [[VA-DOM-002]] 4.2 파이프라인 문단 · [[VA-UI-002#UI-3]] 5.1 제목 재료

**처리** if `isinstance(e, (TimeoutError, OSError의 네트워크 계열, openai.APIConnectionError))` → `network`(`APITimeoutError`는 `APIConnectionError`의 하위라 함께 걸린다) · elif OpenAI SDK 예외 또는 `OpenAIOutputError`(모델 출력이 형식에 맞지 않아 어댑터가 던진 것 — [[VA-MS-007]] 0장) → `openai` · elif 어댑터의 `YtdlpError` → `youtube` · elif 어댑터의 `FfmpegError` → `ffmpeg` · elif `OSError(ENOSPC)` → `disk` · else → `unknown`

**테스트 관점** 여섯 종류 각각 · `OpenAIOutputError` → `openai` · OpenAI SDK의 연결 오류는 `openai`가 아니라 `network`(SDK가 `APIConnectionError`로 감싼다 — 먼저 검사)

---

#### pipeline.reason_of 예외 → 실패 이유 한 줄

**시그니처** `def reason_of(e: BaseException) -> str`

근거: [[VA-UI-002#UI-3]] 5.2 '왜' · [[VA-SCN-001#S6]] 4번과 변형(인터넷 끊김) · [[VA-DOM-003#analysis_jobs]] `error_reason`(한 줄, 한국어)

어댑터는 예외를 그대로 올리고(분류 · 재시도가 파이프라인 몫이듯) 이유 한 줄도 여기서 만든다. 어댑터가 SDK 예외를 감싸 바꾸면 [[#pipeline.error_kind]]가 종류를 가를 수 없다.

**처리**
1. `line = str(e)의 첫 줄(앞뒤 공백 없이)` · if `line`에 한글이 있음 → `→ line` — 앱이 만든 문장이다(`NotImplementedYet` · `OpenAIOutputError` · 파이프라인의 `YtdlpError('자막을 찾지 못했습니다')` · infra의 '시간 제한을 넘었습니다' 등)
2. else `error_kind(e)`로 —
   - `network` → 시간 초과(`TimeoutError` · `APITimeoutError`)면 '네트워크 시간 초과', 아니면 '네트워크에 연결할 수 없음'
   - `openai` → 상태 401 'API 키 인증 실패' · 403 'OpenAI 권한 없음' · 429는 `insufficient_quota`면 'OpenAI 잔액 부족', 아니면 'OpenAI 요청 한도 초과' · 5xx 'OpenAI 서버 오류' · 그 밖 상태 'OpenAI가 요청을 거절함({상태})' · 상태 없음 'OpenAI 오류'
   - `youtube` → `YtdlpError.kind`로 private '비공개 영상' · unavailable '삭제되었거나 볼 수 없는 영상' · geo '이 지역에서 볼 수 없는 영상' · network 'YouTube 연결 실패' · extractor 'yt-dlp가 영상을 읽지 못함 — yt-dlp 업데이트' · other 'yt-dlp 오류'
   - `ffmpeg` → 'ffmpeg 처리 실패' · `disk` → '저장 공간 부족'
   - `unknown` → '알 수 없는 오류({예외 클래스 이름})'

**출력** 한 줄(한국어). 화면이 실패 알림 본문의 '왜'로 그대로 쓴다([[VA-UI-002#UI-3]] 5.2)

**호출하는 것** [[#pipeline.error_kind]]

**테스트 관점** `APITimeoutError` → '네트워크 시간 초과' · `APIConnectionError` → '네트워크에 연결할 수 없음' · 401 → 'API 키 인증 실패' · 429 `insufficient_quota` → 'OpenAI 잔액 부족' · 503 → 'OpenAI 서버 오류' · 영어 표준 오류의 `YtdlpError(kind=private)` → '비공개 영상' · `NotImplementedYet` · `OpenAIOutputError`는 그 문장 · 여러 줄 한국어 → 첫 줄 · `KeyError('x')` → '알 수 없는 오류(KeyError)'

---

## 3. 미결사항

- [x] (반영: 클래스 명세 v9 · ERD v3) **되먹임** — `AnalysisJob`에 `stage_started_at` 속성(`analysis_jobs.stage_started_at timestamptz`)이 필요하다. 걸린 시간과 남은 시간 계산의 기준이고, 재시도 뒤에는 `started_at`으로 계산할 수 없다. [[VA-DOM-002#AnalysisJob]] · [[VA-DOM-003#analysis_jobs]]에 더한다
- [x] 조각이 없는 단계의 남은 시간을 0까지 내려 주는 것 — 결정: 0을 주고 화면이 비운다([[VA-API-001]] v2 4장 `remaining_sec`)
- [ ] 진행률 반올림 — 30을 네 단계로 나누면 7.5. 단계마다 내림하고 마지막 단계에서 100을 맞춘다로 갈지
- [ ] 첫 값 여섯(`CHUNK_SEC` · `STT_CONCURRENCY` · `CHUNK_MAX_ATTEMPTS` · `CHUNK_EST_SEC` · `TEXT_EST_SEC` · `TOKENS_PER_MIN`)은 측정 뒤 조정. [[VA-INFRA-001]] 9절의 조각 길이 · 병렬 수 미결을 이 값으로 닫는다
- [x] 동시 분석 대기열 — 결정: 대기열(사용자 결정 2026-09-21). `start` · `retry`는 `queued`로 넣고, `claim_next` · `wake` · `wait_for_work` · `queue_position` · `pipeline.worker`를 더했다. 부분 unique 인덱스는 그대로다
- [x] 워커가 `Video`를 얻는 길(시퀀스 되먹임 #7) — 결정: `main.py`가 `worker(load_video)`로 넘긴다. 작업 행에 영상 값을 복사하는 안은 같은 값이 두 테이블에 생기고, 영상 정보가 덮어써질 때([[VA-API-001#POST/api/videos]] 다시 넣기) 어긋날 수 있어 버렸다. `run(job_id)`로 시그니처를 줄이는 안은 `AnalysisService.generate_*`가 `Video`를 받고 있어 고칠 곳이 더 많다
- [x] (반영: 클래스 명세 v12) **되먹임** — [[VA-DOM-002#JobService]]에 `wake() None`을 더하고, `claim_next` · `wait_for_work`와 함께 「`finish` · `fail` · `cancel`이 깨운다」는 규칙을 「`start` · `retry` · 삭제 라우터(삭제 뒤)가 깨운다」로 고친다. 파이프라인 블록의 `worker()`는 `worker(load_video)`로. 워커가 태스크를 기다리므로 `finish` · `fail`은 깨울 필요가 없다. `queue_position`은 DB를 읽으므로 `async`이고 반환은 `int | None`, `to_job`은 셋째 인자 `queue_position`을 받는다
- [x] (반영: 클래스 명세 v12 3.1 표 · 시퀀스 v3 SEQ-11 · 구현 계획 v2 카드 B4) **되먹임** — 삭제 라우터가 `VideoService.delete` 뒤에 `JobService.wake`를 부른다. 라우터는 MINISPEC 항목이 아니라 영상 서비스 MINISPEC은 고치지 않는다
