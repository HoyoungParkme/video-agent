---
doc_id: VA-MS-005
type: MS
title: MINISPEC — SettingsService
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-UC-001, VA-INFRA-001]
---

# MINISPEC — SettingsService

## 0. 이 문서가 다루는 것

`core/settings.py`의 함수 9개. 클래스 명세 [[VA-DOM-002#SettingsService]]의 시그니처를 함수 내부까지 내린 것. `infra/openai.verify_key`는 4.7의 MS 문서에서.

형식은 명세 작성 규약 2.10. 내부 타입(`KeyCheck`)은 [[VA-DOM-002]] 2.6, 응답 형태(`Settings` `KeyStatus` `Models` `ModelOption`)는 [[VA-API-001]] 4장.

**표기** — `→` 반환 · 결과, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분), `FS:` 파일 접근.

**이 서비스가 아는 것** — DB가 없다. 키와 모델 선택은 `.env` 파일에, 마지막 키 확인 결과는 프로세스 메모리(`last_check`)에 산다. 어느 묶음이든 부를 수 있고 이 서비스는 아무 묶음도 부르지 않는다([[VA-DOM-002]] 3.2).

**저장 위치 — `.env` 파일 하나**(사용자 결정 2026-09-21, [[VA-INFRA-001#C6]]). 처음 설치 때 사용자가 직접 적은 키도, 화면에서 넣은 키도 같은 파일의 같은 줄이다. 그래서 「어느 쪽이 우선인가」가 없다. compose가 호스트의 `.env`를 api 컨테이너에 읽기·쓰기로 마운트하고, 이 서비스가 그 파일에서 세 줄만 읽고 쓴다 — `OPENAI_API_KEY` · `STT_MODEL` · `TEXT_MODEL`. 앞 판의 `data/settings.json`은 쓰지 않는다.

**환경 변수를 읽지 않는다.** 같은 이름의 환경 변수(`os.environ`)는 컨테이너가 뜰 때의 값이라, 화면에서 키를 바꾼 뒤에는 옛 값이다. 이 세 값은 **늘 파일에서** 읽는다 — 서버를 다시 띄우지 않아도 다음 요청부터 새 값을 쓴다. `core/config.py`가 이 세 값을 갖지 않는 이유다([[VA-DOM-002]] 1장).

**파일을 제자리에서 고친다.** 클래스 명세는 「임시 파일 → rename」이라고 썼는데, 파일 하나를 바인드 마운트하면 그 파일 자체가 마운트 지점이라 rename으로 바꿔치기할 수 없다(`EBUSY`). 그래서 새 내용을 메모리에서 다 만든 뒤 같은 파일을 열어 한 번에 쓰고(`write` 한 번 · `truncate` · `fsync`) 닫는다. 파일이 수백 바이트라 반쯤 쓰인 채 남을 틈이 사실상 없고, 쓰기는 프로세스 안 잠금 하나로 줄 세운다. 클래스 명세 · 시퀀스의 문장은 되먹임으로 고친다(3장).

**설정값**

| 이름 | 값 | 이유 |
|---|---|---|
| `config.ENV_PATH` | `/app/.env` | compose가 호스트 `.env`를 마운트하는 컨테이너 안 경로. 환경 변수 `ENV_PATH`로 바꿀 수 있다(테스트) |
| `config.MODEL_OPTIONS` | 받아쓰기 `whisper-1`(분당 $0.006) · 텍스트 `gpt-5-mini`(입력 $0.25 · 출력 $2.00 / 100만 토큰), `gpt-5.4-mini`, `gpt-5.4` — 단가는 카드 A를 시작할 때 당시 값으로 채운다 | [[VA-INFRA-001]] 3절, [[VA-UI-002#UI-5]] 3.1 · 3.3. 받아쓰기 목록은 구간 시각을 주는 모델만([[VA-INFRA-001#C3]]) |
| `config.DEFAULT_MODELS` | `whisper-1` · `gpt-5-mini` | 파일에 선택이 없을 때 |
| `config.KEY_CHECK_TIMEOUT_SEC` | 10 | 키 확인 요청 시간 제한 |

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#SettingsService.get]] | 설정 전부 — 재확인 없음 |
| [[#SettingsService.set_key]] | 새 키 확인 → `.env`에 저장 |
| [[#SettingsService.set_models]] | 모델 선택을 `.env`에 저장 |
| [[#SettingsService.check_stored_key]] | 저장된 키 확인 (시작 · 분석 버튼 · 연결 실패 뒤) |
| [[#SettingsService.require_key]] | 마지막 결과로 막기 — 연결 실패였으면 한 번 다시 확인 |
| [[#SettingsService.current_models]] | 지금 모델과 단가 |
| [[#SettingsService.api_key]] | 지금 키 — 어댑터의 클라이언트를 만들 때만 |
| [[#SettingsService.read_env]] | `.env`에서 세 값을 읽는다 |
| [[#SettingsService.write_env]] | `.env`의 그 줄만 고친다 |

---

## 2. 함수

#### SettingsService.get 설정 전부

**시그니처** `def get() -> Settings`

근거: [[VA-SEQ-001#SEQ-C1]] · [[VA-API-001#GET/api/settings]] · [[VA-UC-001#UC-H8]] 1번 · [[VA-UI-002#UI-5]] 규칙(이 화면을 여는 것만으로는 다시 확인하지 않는다)

**처리**
1. `key = read_env().get("OPENAI_API_KEY")` · 빈 문자열은 없는 것으로 본다(`.env.example`을 복사한 직후)
2. `masked` = if `key` → 앞 3자 + `…` + 끝 4자 · else → `None` · `stored_in` = if `key` → `'.env에 저장됨'` · else → `None`
3. `status = KeyStatus(state=last_check.state, masked, stored_in, checked_at=last_check.checked_at, reason_kind=last_check.reason_kind, reason=last_check.reason)` — **OpenAI에 아무것도 보내지 않는다**
4. `→ Settings(key=status, models=current_models(), model_options=config.MODEL_OPTIONS, inbox_path=config.INBOX_DISPLAY_PATH)`

**출력** `Settings`. 페이지 넷이 배너를 그리려고 부른다 — 값싸야 한다(작은 파일 읽기 한 번)

**호출하는 것** [[#SettingsService.read_env]] · [[#SettingsService.current_models]]

**테스트 관점** 가짜 OpenAI 클라이언트의 호출 수가 0 · 키 `sk-abcdefghijklmnop1234` → `masked='sk-…1234'`, `stored_in='.env에 저장됨'` · `OPENAI_API_KEY=`(빈 값) → `masked=None`, `stored_in=None`, `state=missing` · `last_check`가 `invalid`면 `reason`이 그대로 나온다 · 환경 변수에 다른 키가 있어도 파일 것

---

#### SettingsService.set_key 새 키 확인 → 저장

**시그니처** `async def set_key(key: str) -> Settings`

근거: [[VA-SEQ-001#SEQ-12]] · [[VA-API-001#POST/api/settings/key]] · [[VA-UC-001#UC-H8]] 2~4번, 3a · 3b · [[VA-UI-002#UI-5]] 2.4 규칙 · [[VA-INFRA-001#C6]]

**입력** `key` — 붙여 넣은 키

**처리**
1. `k = key.strip()` · if 비어 있음 또는 줄바꿈이 들어 있음 → `! validation {errors: [{field: key, message}]}` — 줄바꿈은 `.env`의 다른 줄을 만든다
2. `check = openai.verify_key(k)` — 모델 목록 조회 한 번, `config.KEY_CHECK_TIMEOUT_SEC` 안에
3. if `check.state == invalid and check.reason_kind == network` → `! llm-unavailable {reason: check.reason}` — 저장 안 함, `last_check` 그대로
   elif `check.state == invalid` → `! key-rejected {reason_kind, reason}` (`format` · `auth` · `quota`) — 저장 안 함, `last_check` 그대로(전 키의 결과가 배너 · 버튼을 정한다)
4. `write_env({"OPENAI_API_KEY": k})` · if `OSError` → `! internal`
5. `last_check = check`(`ok`, `checked_at = now`)
6. `→ get()`

**출력** `Settings`(200). `key.state = ok`, `stored_in = '.env에 저장됨'`

**예외**

| 조건 | 에러 |
|---|---|
| 빈 값 · 줄바꿈 | `validation` |
| 형식 오류 · 인증 실패 · 잔액 없음 | `key-rejected` |
| OpenAI에 닿지 못함 | `llm-unavailable` |
| 파일 쓰기 실패(읽기 전용 마운트 등) | `internal` |

**호출하는 것** `openai.verify_key` · [[#SettingsService.write_env]] · [[#SettingsService.get]]

**테스트 관점** 가짜 확인이 `auth` 실패 → `key-rejected`, 파일 안 바뀜, `get().key.state`가 전 값 · `network` → `llm-unavailable`, 파일 안 바뀜 · 통과 → `.env`의 `OPENAI_API_KEY` 줄이 새 키, `state=ok`, `checked_at` 갱신, `masked`가 새 키 · 서버를 다시 띄우지 않고 다음 `get()`이 새 키 · 키에 줄바꿈 → `validation`

---

#### SettingsService.set_models 모델 선택 저장

**시그니처** `def set_models(stt_model: str, text_model: str) -> Settings`

근거: [[VA-SEQ-001#SEQ-C1]] · [[VA-API-001#PUT/api/settings/models]] · [[VA-UC-001#UC-H8]] 5번 · [[VA-UI-002#UI-5]] 3.1 · 3.3 · 6.2 규칙

**처리**
1. if `stt_model ∉ {o.id for o in MODEL_OPTIONS.stt}` 또는 `text_model ∉ {… .text}` → `! validation {errors: [{field, message: 목록에 없음}]}`
2. `write_env({"STT_MODEL": stt_model, "TEXT_MODEL": text_model})`(키 줄은 그대로) · if `OSError` → `! internal`
3. `→ get()`

**출력** `Settings`. 돌고 있는 작업은 시작할 때 복사한 모델을 끝까지 쓴다([[VA-DOM-002#AnalysisJob]]) — 여기서 바꾼 값은 다음 작업 · 질문부터. 대기 중인 작업도 [분석 시작] 때의 모델이다

**호출하는 것** [[#SettingsService.write_env]] · [[#SettingsService.get]]

**테스트 관점** 모르는 id → `validation`, 파일 안 바뀜 · 저장 뒤 `current_models()`가 새 값 · `OPENAI_API_KEY` 줄이 그대로 남아 있다

---

#### SettingsService.check_stored_key 저장된 키 확인

**시그니처** `async def check_stored_key() -> KeyStatus`

근거: [[VA-SEQ-001#SEQ-13]] 2~7번 · [[VA-SEQ-001#SEQ-1]] 5~8번 · [[VA-UC-001#UC-H8]] 1a · 3b · [[VA-UI-002#UI-5]] 규칙(확인 시점) · [[VA-API-001]] 5장 11

**처리**
1. `key = read_env().get("OPENAI_API_KEY")` · if 없음 · 빈 값 → `last_check = KeyCheck(missing, None, None, now)` · `→ get().key`
2. `check = openai.verify_key(key)` — 예외 · 시간 초과도 `KeyCheck(invalid, network, reason, now)`로 접는다(던지지 않는다 — 서버 시작이 멈추면 안 된다)
3. `last_check = check`
4. `→ get().key`

**출력** `KeyStatus`. 부르는 곳은 셋 — 서버 시작(`main.py`), 분석 버튼(`VideoService.register`), 그리고 마지막 결과가 연결 실패일 때의 [[#SettingsService.require_key]]. 화면 열기 · 폴링은 부르지 않는다

**호출하는 것** [[#SettingsService.read_env]] · `openai.verify_key` · [[#SettingsService.get]]

**테스트 관점** 키 없음 → `missing`, OpenAI 호출 0회 · 가짜 확인 통과 → `ok` · 연결 실패 → `invalid`/`network`, 예외가 밖으로 안 나간다 · 부를 때마다 `checked_at`이 바뀐다 · 사용자가 `.env`를 손으로 고친 뒤 부르면 새 키로 확인한다

---

#### SettingsService.require_key 마지막 결과로 막기

**시그니처** `async def require_key() -> None`

근거: [[VA-API-001]] 1장(키 없이도 읽기는 전부 된다 — 막히는 것은 분석 시작 · 다시 시도 · 질문. 마지막이 연결 실패였으면 그때 한 번 다시 확인) · 5장 11 · [[VA-UC-001#UC-H0]] 사전조건 · [[VA-UC-001#UC-H8]] 3b · [[VA-UI-002]] 1.4 키 없음 배너

**처리**
1. if `last_check.state == invalid and last_check.reason_kind == network` → `check_stored_key()` — **한 번만** 다시 확인한다. 키가 틀린 것이 아니라 인터넷이 없었던 것이라 화면이 버튼을 막지 않았고, 이 요청이 「누를 때 다시 확인」이다
2. if `last_check.state == missing` → `! key-missing` · elif `invalid` → `! key-invalid {reason_kind, reason, checked_at}` · else → `→ None`

**출력** 없음. 다른 실패(`format` · `auth` · `quota`)는 다시 확인해도 같으므로 **OpenAI에 보내지 않는다** — 마지막 결과만 본다. 부르는 곳은 넷: `VideoService.register` · `JobService.start` · `JobService.retry` · `ChatService.ask`

**호출하는 것** [[#SettingsService.check_stored_key]]

**테스트 관점** `missing` → `key-missing`, 호출 수 0 · `invalid`(`quota`) → `key-invalid`에 `reason_kind=quota`, 호출 수 0 · `ok` → 통과, 호출 수 0 · `invalid`(`network`)이고 가짜 확인이 통과 → 통과하고 `last_check`가 `ok`, 호출 수 1 · `invalid`(`network`)이고 또 연결 실패 → `key-invalid`에 `reason_kind=network`, 호출 수 1(되풀이하지 않는다)

---

#### SettingsService.current_models 지금 모델과 단가

**시그니처** `def current_models() -> Models`

근거: [[VA-API-001]] 4장 `Models` · [[VA-DOM-002]] 4.2 `estimate` 규칙(단가는 `current_models`의 값)

**처리** `env = read_env()` · `stt = env.get("STT_MODEL")` · `text = env.get("TEXT_MODEL")` · 없거나 빈 값이면 `config.DEFAULT_MODELS` · `MODEL_OPTIONS`에서 그 id의 `ModelOption`을 찾아 `→ Models(stt=…, text=…)` — 이름과 단가를 같이 돌려준다. 파일의 값이 목록에 없으면(옵션이 바뀐 뒤 · 손으로 잘못 적음) 기본값으로

**출력** `Models`. `JobService.estimate` · `start`, `AnalysisService.generate_*`, `ChatService.ask`가 이름과 단가를 여기서 받는다

**호출하는 것** [[#SettingsService.read_env]]

**테스트 관점** 줄 없음 → 기본값 · 목록에 없는 id → 기본값 · 단가가 `MODEL_OPTIONS`의 값

---

#### SettingsService.api_key 지금 키

**시그니처** `def api_key() -> str | None`

근거: [[VA-DOM-002#SettingsService]] 규칙(`api_key` — 어댑터에 넘길 `client_for`가 부른다) · [[VA-MS-006]] 0장(키는 부를 때마다 받는다)

**처리** `k = read_env().get("OPENAI_API_KEY")` · `→ k if k else None`. 부를 때마다 파일에서 읽는다 — 화면이나 `.env`에서 키를 바꾸면 다음 호출부터 새 키다. 부르는 곳은 `main.py`가 조립해 어댑터에 넘기는 `client_for` 하나다(`lambda: openai.client(settings.api_key())`, 키가 없으면 어댑터가 부르기 전에 `require_key`가 막는다). 키 전체가 밖으로 나가는 유일한 길이라 응답 · 로그에 쓰지 않는다

**호출하는 것** [[#SettingsService.read_env]]

**테스트 관점** 키 있음 → 그 문자열 · `OPENAI_API_KEY=`(빈 값) → None · 파일에서 키를 바꾸면 다음 호출이 새 키 · 로그에 키가 찍히지 않는다

---

#### SettingsService.read_env .env에서 세 값을 읽는다

**시그니처** `def read_env() -> dict[str, str]`

근거: [[VA-INFRA-001#C6]] · [[VA-DOM-002#SettingsService]] 규칙(읽을 때마다 파일에서)

**처리**
1. `FS: config.ENV_PATH` 읽기(UTF-8) · if 파일 없음 → `→ {}`
2. 줄마다 — 빈 줄 · `#`으로 시작하는 줄은 건너뛴다 · 앞의 `export `는 뗀다 · 첫 `=`에서 나눠 이름과 값 · 값 양끝의 공백과 한 쌍의 따옴표(`"…"` 또는 `'…'`)를 뗀다
3. 이름이 `OPENAI_API_KEY` · `STT_MODEL` · `TEXT_MODEL`인 것만 담는다. 같은 이름이 두 번이면 **뒤의 것** — 셸과 compose가 그렇게 읽는다
4. `→ dict`

**출력** 있는 것만 담긴 dict. 다른 줄(DB 비밀번호 등)은 읽지 않는다

**테스트 관점** 파일 없음 → `{}` · `OPENAI_API_KEY="sk-abc"` → `sk-abc` · `export STT_MODEL=whisper-1` · 주석 줄 속의 `OPENAI_API_KEY`는 무시 · 같은 이름 두 줄이면 뒤의 값 · `POSTGRES_PASSWORD`가 결과에 없다

---

#### SettingsService.write_env .env의 그 줄만 고친다

**시그니처** `def write_env(values: dict[str, str]) -> None`

근거: [[VA-INFRA-001#C6]](앱이 같은 파일에 쓴다) · [[VA-DOM-002#SettingsService]] 규칙(세 줄만, 다른 줄 · 주석 · 순서는 그대로) · 0장 「파일을 제자리에서 고친다」

**입력** `values` — 이름은 `OPENAI_API_KEY` · `STT_MODEL` · `TEXT_MODEL` 중에서만. 다른 이름이면 `ValueError`(코드 실수)

**처리** — 프로세스 안 잠금(`threading.Lock`) 안에서
1. `lines = FS: config.ENV_PATH`의 줄 목록 · 파일이 없으면 빈 목록
2. 이름마다 — 그 이름의 줄(주석이 아닌 것, `export ` 허용) 중 **마지막** 줄을 `이름=값`으로 바꾼다(`read_env`가 읽는 바로 그 줄). 없으면 끝에 `이름=값` 줄을 더한다. 값은 따옴표 없이 쓴다 — 키와 모델 id에는 공백 · `#` · 따옴표가 없다(`set_key` 1번 · `set_models` 1번이 거른다)
3. `text = "\n".join(lines) + "\n"` · `FS: open(config.ENV_PATH, "r+" 또는 없으면 "w")` · `write(text)` · `truncate()` · `flush` · `fsync` — **제자리 쓰기.** rename으로 바꿔치기하지 않는다(바인드 마운트한 파일은 `EBUSY`)
4. `OSError`는 그대로 올린다(부르는 쪽이 `internal`로 접는다)

**출력** 없음

**테스트 관점** 주석 · 빈 줄 · 다른 변수 · 줄 순서가 그대로다(바이트 비교로 그 줄만 다르다) · 줄이 없으면 끝에 더해진다 · 새 값이 옛 값보다 짧아도 찌꺼기가 없다(`truncate`) · 끝에 줄바꿈 하나 · 허용하지 않는 이름 → `ValueError` · 읽기 전용 파일 → `OSError` · 쓴 뒤 `read_env()`가 새 값

---

## 3. 미결사항

- [x] 키 저장 위치 — 결정: `.env` 파일 하나, 앱이 그 줄을 고친다. `data/settings.json`과 「파일 → 환경 변수」 우선순위는 없앴다(사용자 결정 2026-09-21)
- [x] 키 확인이 네트워크로 실패했을 때의 배너 문구 — 결정: 문구를 가르고 버튼을 막지 않는다. 그래서 `require_key`가 마지막 결과가 `network`면 한 번 다시 확인한다([[VA-API-001]] 5장 11 · [[VA-UI-002]] 2장 되먹임 반영)
- [x] 화면에서 모델을 바꾸는 유스케이스 — 반영: [[VA-UC-001#UC-H8]] 5번
- [ ] 텍스트 모델 `gpt-5.4-mini` · `gpt-5.4`의 단가 — 카드 A를 시작할 때 당시 값을 `config.MODEL_OPTIONS`에 채운다([[VA-INFRA-001]] 9절 버전 고정과 같은 때, 사용자 결정 2026-09-21)
- [x] (반영: 클래스 명세 v12 · 시퀀스 v3 SEQ-12) **되먹임** — `.env`를 rename으로 바꿔치기할 수 없다(0장). [[VA-DOM-002#SettingsService]] 규칙과 [[VA-SEQ-001#SEQ-12]]의 「임시 파일 → rename」을 「제자리 쓰기」로 고친다. 폴더를 마운트하면 rename이 되지만 저장소 뿌리 전체를 api 컨테이너에 쓰기로 여는 것이라 택하지 않았다
- [x] (반영: 클래스 명세 v12) **되먹임** — `require_key`가 `async`가 됐다(OpenAI를 부를 수 있다). 부르는 네 곳(`VideoService.register` · `JobService.start` · `retry` · `ChatService.ask`)은 이미 `async`라 `await`만 붙는다. `read_env` · `write_env` 둘을 [[VA-DOM-002#SettingsService]]에 private 메서드로 더한다
- [ ] compose의 `env_file: .env` — api 서비스에 걸면 같은 이름의 환경 변수가 컨테이너에 옛 값으로 남는다. 이 서비스는 읽지 않으므로 해는 없지만, OpenAI SDK가 `OPENAI_API_KEY` 환경 변수를 스스로 읽지 않게 `infra/openai`가 키를 늘 인자로 넘긴다 — 카드 A에서 확인
- [x] 어댑터에 줄 키 — 결정: 공개 함수 [[#SettingsService.api_key]]. 어댑터 MINISPEC의 되먹임(「키를 돌려주는 공개 함수가 없다」)을 여기서 닫는다
