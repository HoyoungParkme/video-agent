---
doc_id: VA-DOM-003
type: DOM
title: ERD·DD — 영상 분석 에이전트
status: draft
upstream: [VA-DOM-002, VA-INFRA-001]
---

# ERD·DD

## 0. 이 문서가 다루는 것

[[VA-DOM-002]]의 엔티티 클래스를 **테이블**로 옮긴다. ERD는 그림, DD는 컬럼마다 의미·타입·제약을 적은 설명서다. ORM 모델 = 도메인 객체이므로 테이블은 클래스와 1:1이다. 클래스가 바뀌면 이 문서에 `확인 필요`가 붙어야 한다.

**전제**
- PostgreSQL 16 ([[VA-INFRA-001]] 3장). 기본키는 `bigint` 자동 증가 대리키. 사람이 부르는 식별자(출처 식별자)는 unique
- 열거형은 DB enum이 아니라 `varchar` + 앱 검증
- 시각은 `timestamptz`, 영상 안의 위치(초)는 `double precision`
- **목록형 속성은 JSONB** — 출처 시각·글머리·근거 시각. 단독으로 조회·조인하는 쿼리가 없고 항상 부모와 함께 읽는다. 자식 테이블로 빼면 조인 셋이 늘고 얻는 게 없다([[VA-DOM-002]] 5장 미결 → 여기서 결정)
- **삭제는 하드 삭제 + FK `on delete cascade`.** 영상을 지우면 딸린 전부가 지워진다([[VA-UC-001#UC-H6]]). 복구·감사 요구가 없다(개인용)
- 사용자 테이블 없음 ([[VA-INFRA-001#C5]])

---

## 1. ERD

```mermaid
erDiagram
    videos ||--o{ analysis_jobs : "분석 시도"
    analysis_jobs ||--o{ audio_chunks : "조각"
    videos ||--o| transcripts : "스크립트"
    transcripts ||--|{ segments : "구간"
    videos ||--o| summaries : "요약"
    summaries ||--|{ insights : "인사이트"
    videos ||--o{ parts : "파트"
    videos ||--o{ chapters : "챕터"
    parts ||--o{ chapters : "묶음"
    videos ||--o{ suggested_questions : "추천 질문"
    videos ||--o{ chat_turns : "대화"

    videos {
        bigint id PK
        varchar source_kind
        varchar source_id UK
        varchar title
        varchar channel
        int duration_sec
        varchar origin
        boolean has_captions
        timestamptz analyzed_at
        timestamptz created_at
    }
    analysis_jobs {
        bigint id PK
        bigint video_id FK
        varchar stage
        smallint progress_pct
        int est_seconds
        numeric est_cost_usd
        text error
        timestamptz started_at
        timestamptz finished_at
    }
    audio_chunks {
        bigint id PK
        bigint job_id FK
        int seq
        double offset_sec
        double duration_sec
        varchar path
        boolean done
    }
    transcripts {
        bigint id PK
        bigint video_id FK_UK
        varchar source
        varchar language
        varchar model
        timestamptz created_at
    }
    segments {
        bigint id PK
        bigint transcript_id FK
        int seq
        double start_sec
        double end_sec
        text text
    }
    summaries {
        bigint id PK
        bigint video_id FK_UK
        text one_liner
        varchar model
        timestamptz created_at
    }
    insights {
        bigint id PK
        bigint summary_id FK
        int seq
        text text
        jsonb source_secs
    }
    parts {
        bigint id PK
        bigint video_id FK
        int seq
        varchar title
        double start_sec
    }
    chapters {
        bigint id PK
        bigint video_id FK
        bigint part_id FK
        int seq
        double start_sec
        varchar title
        jsonb bullets
    }
    suggested_questions {
        bigint id PK
        bigint video_id FK
        int seq
        text question
    }
    chat_turns {
        bigint id PK
        bigint video_id FK
        text question
        text answer
        jsonb cited_secs
        varchar model
        timestamptz asked_at
    }
```

---

## 2. DD (데이터 사전)

주요 컬럼만. 이름으로 뜻이 드러나는 것(`id`, `created_at`, `*_id` FK)은 뺐다. FK는 전부 `on delete cascade`.

### videos

클래스: [[VA-DOM-002#Video]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| source_kind | varchar(10) | not null, `youtube`·`local` | 출처 종류 | `youtube` |
| source_id | varchar(64) | UK not null | YouTube 영상 ID(11자) 또는 파일 SHA-256(64자). 중복 판정 키 | `dQw4w9WgXcQ` |
| title | varchar(300) | not null | 제목. 로컬이면 파일명 | `RAG 운영기` |
| channel | varchar(200) | null 허용 | 채널명. 로컬이면 null | |
| duration_sec | int | not null, `> 0`, `≤ 10800` | 길이(초). 3시간 상한은 앱에서도 검사 | `3012` |
| origin | varchar(1000) | not null | 원본 URL 또는 inbox 상대 경로 | `https://youtu.be/…` / `workshop_0912.mp4` |
| has_captions | boolean | not null default false | YouTube 자막 유무. 사전 안내·비용 계산 | |
| analyzed_at | timestamptz | null 허용 | 분석 완료 시각. null이면 미완료 | |

### analysis_jobs

클래스: [[VA-DOM-002#AnalysisJob]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| stage | varchar(12) | not null, JobStage | 현재 단계. `done`·`failed`가 종료 | `transcribe` |
| progress_pct | smallint | not null default 0, `0~100` | 전체 진행률. 단계 가중치로 계산 | `45` |
| est_seconds | int | null 허용 | 시작 전 예상 소요 시간 | `480` |
| est_cost_usd | numeric(8,4) | null 허용 | 시작 전 예상 API 비용. 자막이면 0 | `0.9000` |
| error | text | null 허용 | 실패 시 "단계: 이유". 재시도 성공하면 비운다 | `transcribe 20/30: rate limit` |
| started_at | timestamptz | not null | | |
| finished_at | timestamptz | null 허용 | `done`·`failed` 시각 | |

### audio_chunks

클래스: [[VA-DOM-002#AudioChunk]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| seq | int | (job_id, seq) UK | 순번 0부터 | `12` |
| offset_sec | double | not null | 전체 음성에서 이 조각의 시작 | `7200.0` |
| duration_sec | double | not null | 조각 길이 | `600.0` |
| path | varchar(500) | null 허용 | 임시 파일 경로. 받아쓰기 성공 후 파일 삭제 시 null | `data/tmp/42/12.mp3` |
| done | boolean | not null default false | 받아쓰기 완료. 재개 기준 | |

### transcripts

클래스: [[VA-DOM-002#Transcript]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| video_id | bigint | FK, **UK** | 영상과 1:1 | |
| source | varchar(10) | not null, `caption`·`stt` | 자막인지 받아쓰기인지 | `stt` |
| language | varchar(10) | null 허용 | 감지된 언어 (ISO 639-1) | `ko` |
| model | varchar(50) | null 허용 | 받아쓰기 모델. 자막이면 null | `whisper-1` |

### segments

클래스: [[VA-DOM-002#Segment]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| seq | int | (transcript_id, seq) UK | 순번 | |
| start_sec / end_sec | double | not null, `start ≤ end` | 구간 시각 | `1395.2` / `1398.7` |
| text | text | not null | 구간 텍스트 | |

3시간 영상 기준 3,000~6,000행. 영상당 한 번에 읽으므로 페이지네이션 없음.

### summaries

클래스: [[VA-DOM-002#Summary]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| video_id | bigint | FK, **UK** | 영상과 1:1 | |
| one_liner | text | not null | 한 줄 요약 | |
| model | varchar(50) | not null | 만든 모델 | `gpt-5-mini` |

### insights

클래스: [[VA-DOM-002#Insight]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| seq | int | (summary_id, seq) UK | 순번 | |
| text | text | not null | 인사이트 문장 | |
| source_secs | jsonb | not null, 숫자 배열 | 출처 시각(초) 목록. 비어 있지 않아야 함 — 앱 검증 | `[1395.2, 1442.0]` |

### parts

클래스: [[VA-DOM-002#Part]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| seq | int | (video_id, seq) UK | 순번 | |
| title | varchar(200) | not null | 파트 제목 | `오후 세션 1` |
| start_sec | double | not null | 시작 시각 | |

### chapters

클래스: [[VA-DOM-002#Chapter]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| part_id | bigint | FK null 허용 | 1시간 이하 영상은 null | |
| seq | int | (video_id, seq) UK | 순번. 파트를 넘어 전체 순서 | |
| start_sec | double | not null | 시작 시각. 끝은 다음 챕터의 시작 | `760.0` |
| title | varchar(200) | not null | 챕터 제목 | `아키텍처 개요` |
| bullets | jsonb | not null, 문자열 배열 2~3개 | 글머리 요약 | `["…", "…"]` |

`video_id`와 `part_id`를 둘 다 두는 이유: 파트 없는 영상이 있고, 있어도 "영상의 챕터 전부"를 한 번에 읽는 쿼리가 주다.

### suggested_questions

클래스: [[VA-DOM-002#SuggestedQuestion]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| seq | int | (video_id, seq) UK, `1~3` | 순번 | |
| question | text | not null | 질문 문장 | `청킹 전략을 바꾼 근거는?` |

### chat_turns

클래스: [[VA-DOM-002#ChatTurn]]

| 컬럼 | 타입 | 제약 | 의미 | 예시 |
|---|---|---|---|---|
| question | text | not null | 사용자 질문 | |
| answer | text | not null | 답변 | |
| cited_secs | jsonb | not null default `[]` | 근거 시각 목록. 빈 배열 = 영상에 없는 내용 | `[1395.2, 1442.0]` |
| model | varchar(50) | not null | 답변 모델 | `gpt-5-mini` |
| asked_at | timestamptz | not null | 질문 시각. 맥락 순서 기준 | |

---

## 3. 인덱스와 정규화

FK와 unique는 전부 인덱스(생략). 아래는 조회 패턴에서 온 추가 인덱스만.

| 테이블 | 인덱스 | 이유 (어느 쿼리) |
|---|---|---|
| videos | `(analyzed_at desc nulls first)` | 목록 — 진행 중 먼저, 최근 분석순 · `VideoService.list` |
| analysis_jobs | `(video_id, started_at desc)` | 영상의 최근 작업 · `progress`, `retry` |
| analysis_jobs | `(stage) where stage not in ('done','failed')` 부분 | 서버 시작 시 중단된 작업 찾기 ([[VA-DOM-002]] 5장 미결) |
| audio_chunks | `(job_id, done)` | 재개 시 미완료 조각 · `pipeline` |
| segments | `(transcript_id, start_sec)` | 시각 → 구간 찾기 (화면 이동, 근거 시각 매핑) |
| chapters | `(video_id, start_sec)` | 질문 관련 챕터 고르기 · `ChatService.ask` 3b |
| chat_turns | `(video_id, asked_at)` | 기록 시간순 · `history`, 최근 10턴 |

**정규화** — 전 테이블 3NF. JSONB 셋(`insights.source_secs`, `chapters.bullets`, `chat_turns.cited_secs`)은 1NF 관점에서 배열이지만, 의도적이다: 원자 단위로 조회·조인·갱신하는 쿼리가 하나도 없고 항상 부모 행과 함께 읽고 함께 쓴다. 자식 테이블로 빼면 테이블 셋·조인 셋이 늘고 얻는 것이 없다. 조회 요구가 생기면(예: "이 시각을 근거로 쓴 답변 전부") 그때 뺀다.

`chapters.video_id`는 `part_id → parts.video_id`로 유도 가능하므로 엄밀히는 이행 종속이다. 두는 이유는 위 DD에 적었다 — 파트가 없는 영상이 있고 주 쿼리가 영상 단위다. 정합성은 앱이 같은 트랜잭션에서 쓰므로 어긋날 경로가 없다.

**크기 추정** — 영상 100개 분석 시: segments 약 30만 행(3시간 기준 상한), 나머지 합쳐 수천 행. PostgreSQL에 부담 없다.

---

## 4. 판단이 필요한 지점

**1. 재분석 시 결과 교체** — `transcripts`·`summaries`가 영상과 1:1(UK)이므로 다시 만들면 **기존 행을 지우고 새로 넣는다**. 히스토리는 남지 않는다. [[VA-DOM-001]] 6장 미결과 같은 결정.

**2. `audio_chunks` 행 보존** — 파일은 지우고 행은 남긴다([[VA-DOM-001]] 5장 2번). 영상 삭제 시 cascade로 함께.

**3. 소프트 삭제 없음** — 개인용이고 원본(영상·URL)은 밖에 있어 재분석하면 복구된다. `deleted_at`을 두면 모든 쿼리에 조건이 붙는데 얻는 게 없다.

---

## 5. 미결사항

- [ ] `segments.text`에 전문 검색 인덱스(GIN, `to_tsvector`)를 둘지 — 첫 버전은 안 둔다. 대화 맥락 선별이 챕터 필터로 부족하면 그때 ([[VA-INFRA-001]] 9장 미결과 연결)
- [ ] `est_cost_usd` 단가를 테이블로 뺄지 설정값으로 둘지 — 설정값(`core/config.py`). 모델·단가가 바뀌면 새 작업부터 반영되고 지난 작업의 값은 그대로 남는다
