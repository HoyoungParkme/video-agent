---
doc_id: VA-MS-005
type: MS
title: MINISPEC — SettingsService
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-UC-001, VA-INFRA-001]
---

# MINISPEC — SettingsService

## 0. 이 문서가 다루는 것

`core/settings.py`의 함수 6개. 클래스 명세 [[VA-DOM-002#SettingsService]]의 시그니처를 함수 내부까지 내린 것. `infra/openai.verify_key`는 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10. 내부 타입(`KeyCheck`)은 [[VA-DOM-002]] 2.6, 응답 형태(`Settings` `KeyStatus` `Models` `ModelOption`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `FS:` 파일 접근, `ENV:` 환경 변수.

**이 서비스가 아는 것** — DB가 없다. 키와 모델 선택은 파일에, 마지막 키 확인 결과는 프로세스 메모리(`last_check`)에 산다. 어느 묶음이든 부를 수 있고 이 서비스는 아무 묶음도 부르지 않는다([[VA-DOM-002]] 3.2).

**저장 위치 — 첫 버전 결정.** 웹에서 받은 키와 모델 선택은 `config.DATA_DIR / "settings.json"`에 둔다(`{"openai_api_key": …, "stt_model": …, "text_model": …}`, 파일 권한 600). 이유: `.env`는 컨테이너 안에서 읽기 전용이고 호스트 파일을 컨테이너가 고치려면 쓰기 마운트가 하나 더 필요하다. DB에 두면 설정이 묶음이 되어 도메인 모델부터 고쳐야 한다([[VA-DOM-002]] 5장 1). `data/`는 이미 쓰기 볼륨이다. **키의 우선순위는 파일 → 환경 변수**다 — 사용자가 화면에서 넣은 것이 가장 최근의 명시적 결정이다. 이 결정은 [[VA-INFRA-001#C6]] · [[VA-UI-001]] 8장 · [[VA-API-001]] 6장의 같은 미결을 닫는 제안이고, 사용자 확인이 남아 있다(3장).

**설정값**

| 이름 | 값 | 이유 |
|---|---|---|
| `config.SETTINGS_PATH` | `data/settings.json` | 위 결정 |
| `config.MODEL_OPTIONS` | 받아쓰기 `whisper-1`(분당 $0.006) · 텍스트 `gpt-5-mini`(입력 $0.25 · 출력 $2.00 / 100만 토큰), `gpt-5.4-mini`, `gpt-5.4` — 단가는 초기화 때 당시 값으로 채운다 | [[VA-INFRA-001]] 3절, [[VA-UI-002#UI-5]] 3.1 · 3.3. 받아쓰기 목록은 구간 시각을 주는 모델만([[VA-INFRA-001#C3]]) |
| `config.DEFAULT_MODELS` | `whisper-1` · `gpt-5-mini` | 파일에 선택이 없을 때 |
| `config.KEY_CHECK_TIMEOUT_SEC` | 10 | 키 확인 요청 시간 제한 |

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#SettingsService.get]] | 설정 전부 — 재확인 없음 |
| [[#SettingsService.set_key]] | 새 키 확인 → 저장 |
| [[#SettingsService.set_models]] | 모델 선택 저장 |
| [[#SettingsService.check_stored_key]] | 저장된 키 확인 (시작 · 분석 버튼) |
| [[#SettingsService.require_key]] | 마지막 결과로 막기 |
| [[#SettingsService.current_models]] | 지금 모델과 단가 |

---

## 2. 함수

#### SettingsService.get 설정 전부

**시그니처** `def get() -> Settings`

근거: [[VA-SEQ-001#SEQ-C1]] · [[VA-API-001#GET/api/settings]] · [[VA-UC-001#UC-H8]] 1번 · [[VA-UI-002#UI-5]] 규칙(이 화면을 여는 것만으로는 다시 확인하지 않는다)

**처리**
1. `key = 저장된 키 읽기` — `FS: settings.json`의 `openai_api_key` · 없으면 `ENV: OPENAI_API_KEY` · 둘 다 없으면 `None`. `stored_in` = 파일이면 `'data/settings.json에 저장됨'`, 환경 변수면 `'.env에 저장됨'`, 없으면 `None`
2. `masked` = if `key` → 앞 3자 + `…` + 끝 4자 · else → `None`
3. `status = KeyStatus(state=last_check.state, masked, stored_in, checked_at=last_check.checked_at, reason_kind=last_check.reason_kind, reason=last_check.reason)` — **OpenAI에 아무것도 보내지 않는다**
4. `→ Settings(key=status, models=current_models(), model_options=config.MODEL_OPTIONS, inbox_path=config.INBOX_DISPLAY_PATH)`

**출력** `Settings`. 페이지 넷이 배너를 그리려고 부른다 — 값싸야 한다

**호출하는 것** [[#SettingsService.current_models]]

**테스트 관점** 가짜 OpenAI 클라이언트의 호출 수가 0 · 키 `sk-abcdefghijklmnop1234` → `masked='sk-…1234'` · 파일과 환경 변수 둘 다 있으면 파일 것 · 키 없음 → `masked=None`, `state=missing` · `last_check`가 `invalid`면 `reason`이 그대로 나온다

---

#### SettingsService.set_key 새 키 확인 → 저장

**시그니처** `async def set_key(key: str) -> Settings`

근거: [[VA-SEQ-001#SEQ-12]] · [[VA-API-001#POST/api/settings/key]] · [[VA-UC-001#UC-H8]] 2~4번, 3a · [[VA-UI-002#UI-5]] 2.4 규칙 · [[VA-INFRA-001#C6]]

**입력** `key` — 붙여 넣은 키

**처리**
1. `k = key.strip()` · if 비어 있음 → `! validation {errors: [{field: key, message: 비어 있음}]}`
2. `check = openai.verify_key(k)` — 모델 목록 조회 한 번, `config.KEY_CHECK_TIMEOUT_SEC` 안에
3. if `check.state == invalid and check.reason_kind == network` → `! llm-unavailable {reason: check.reason}` — 저장 안 함, `last_check` 그대로
   elif `check.state == invalid` → `! key-rejected {reason_kind, reason}` (`format` · `auth` · `quota`) — 저장 안 함, `last_check` 그대로(전 키의 결과가 배너 · 버튼을 정한다)
4. `FS: settings.json`에 `openai_api_key = k` 쓰기(임시 파일 → rename, 권한 600) · if `OSError` → `! internal`
5. `last_check = check`(`ok`, `checked_at = now`)
6. `→ get()`

**출력** `Settings`(200). `key.state = ok`, `stored_in = 'data/settings.json에 저장됨'`

**예외**

| 조건 | 에러 |
|---|---|
| 빈 값 | `validation` |
| 형식 오류 · 인증 실패 · 잔액 없음 | `key-rejected` |
| OpenAI에 닿지 못함 | `llm-unavailable` |
| 파일 쓰기 실패 | `internal` |

**호출하는 것** `openai.verify_key` · [[#SettingsService.get]]

**테스트 관점** 가짜 확인이 `auth` 실패 → `key-rejected`, 파일 안 바뀜, `get().key.state`가 전 값 · `network` → `llm-unavailable`, 파일 안 바뀜 · 통과 → 파일에 새 키, `state=ok`, `checked_at` 갱신, `masked`가 새 키 · 파일 권한 600 · 환경 변수 키가 있어도 파일 키가 우선

---

#### SettingsService.set_models 모델 선택 저장

**시그니처** `def set_models(stt_model: str, text_model: str) -> Settings`

근거: [[VA-SEQ-001#SEQ-C1]] · [[VA-API-001#PUT/api/settings/models]] · [[VA-UI-002#UI-5]] 3.1 · 3.3 · 6.2 규칙

**처리**
1. if `stt_model ∉ {o.id for o in MODEL_OPTIONS.stt}` 또는 `text_model ∉ {… .text}` → `! validation {errors: [{field, message: 목록에 없음}]}`
2. `FS: settings.json`에 `stt_model` · `text_model` 쓰기(키는 그대로) · if `OSError` → `! internal`
3. `→ get()`

**출력** `Settings`. 돌고 있는 작업은 시작할 때 복사한 모델을 끝까지 쓴다([[VA-DOM-002#AnalysisJob]]) — 여기서 바꾼 값은 다음 작업 · 질문부터

**호출하는 것** [[#SettingsService.get]]

**테스트 관점** 모르는 id → `validation`, 파일 안 바뀜 · 저장 뒤 `current_models()`가 새 값 · 키가 파일에 그대로 남아 있다

---

#### SettingsService.check_stored_key 저장된 키 확인

**시그니처** `async def check_stored_key() -> KeyStatus`

근거: [[VA-SEQ-001#SEQ-13]] 2~7번 · [[VA-SEQ-001#SEQ-1]] 5~8번 · [[VA-UC-001#UC-H8]] 1a · [[VA-UI-002#UI-5]] 규칙(확인 시점 셋)

**처리**
1. `key = 저장된 키 읽기`(`get` 1번과 같은 순서) · if 없음 → `last_check = KeyCheck(missing, None, None, now)` · `→ get().key`
2. `check = openai.verify_key(key)` — 예외 · 시간 초과도 `KeyCheck(invalid, network, reason, now)`로 접는다(던지지 않는다 — 서버 시작이 멈추면 안 된다)
3. `last_check = check`
4. `→ get().key`

**출력** `KeyStatus`. 서버 시작(`main.py`)과 분석 버튼(`VideoService.register`)만 부른다. 화면 열기 · 폴링은 부르지 않는다

**호출하는 것** `openai.verify_key` · [[#SettingsService.get]]

**테스트 관점** 키 없음 → `missing`, OpenAI 호출 0회 · 가짜 확인 통과 → `ok` · 연결 실패 → `invalid`/`network`, 예외가 밖으로 안 나간다 · 부를 때마다 `checked_at`이 바뀐다

---

#### SettingsService.require_key 마지막 결과로 막기

**시그니처** `def require_key() -> None`

근거: [[VA-API-001]] 1장(키 없이도 읽기는 전부 된다 — 막히는 것은 분석 시작 · 다시 시도 · 질문) · [[VA-UC-001#UC-H0]] 사전조건 · [[VA-UI-002]] 1.4 키 없음 배너

**처리** if `last_check.state == missing` → `! key-missing` · elif `invalid` → `! key-invalid {reason_kind, reason, checked_at}` · else → `→ None`. **OpenAI에 보내지 않는다** — 마지막 결과만 본다. 부르는 곳은 넷: `VideoService.register` · `JobService.start` · `JobService.retry` · `ChatService.ask`

**테스트 관점** `missing` → `key-missing` · `invalid`(`quota`) → `key-invalid`에 `reason_kind=quota` · `ok` → 통과 · 호출 수 0

---

#### SettingsService.current_models 지금 모델과 단가

**시그니처** `def current_models() -> Models`

근거: [[VA-API-001]] 4장 `Models` · [[VA-DOM-002]] 4.2 `estimate` 규칙(단가는 `current_models`의 값)

**처리** `FS: settings.json`의 `stt_model` · `text_model` · 없으면 `config.DEFAULT_MODELS` · `MODEL_OPTIONS`에서 그 id의 `ModelOption`을 찾아 `→ Models(stt=…, text=…)` — 이름과 단가를 같이 돌려준다. 파일의 값이 목록에 없으면(옵션이 바뀐 뒤) 기본값으로

**출력** `Models`. `JobService.estimate` · `start`, `AnalysisService.generate_*`, `ChatService.ask`가 이름과 단가를 여기서 받는다

**테스트 관점** 파일 없음 → 기본값 · 파일에 없는 id → 기본값 · 단가가 `MODEL_OPTIONS`의 값

---

## 3. 미결사항

- [ ] **키 저장 위치를 `data/settings.json`으로, 우선순위를 파일 → 환경 변수로** — 사용자 확인. 확인되면 [[VA-INFRA-001#C6]](「.env 파일 하나」를 「.env 또는 data/settings.json」으로) · [[VA-INFRA-001]] 6절 · [[VA-UI-002#UI-5]] 2.2 캡션 문구 · [[VA-DOM-002]] 7장 · [[VA-API-001]] 6장의 같은 미결을 닫는다
- [ ] 텍스트 모델 `gpt-5.4-mini` · `gpt-5.4`의 단가 — 초기화 때 당시 값을 `config.MODEL_OPTIONS`에 채운다([[VA-INFRA-001]] 9절 버전 고정과 같은 때)
- [ ] 키 확인이 네트워크로 실패했을 때의 배너 문구 — 지금은 `invalid`/`network`라 '키를 확인하지 못했어요 — 연결 실패'가 뜬다. '연결을 확인하지 못했어요'로 가를지 사용자 확인([[VA-SEQ-001]] 3장, [[VA-MS-004]] 3장과 같은 항목)
- [ ] 화면에서 모델을 바꾸는 유스케이스가 없다 — [[VA-UI-001]] 8장의 [[VA-UC-001#UC-H8]] 갱신 요청이 그대로 남아 있다
