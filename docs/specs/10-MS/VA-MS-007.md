---
doc_id: VA-MS-007
type: MS
title: MINISPEC — infra (ytdlp · ffmpeg · openai)
status: draft
upstream: [VA-DOM-002, VA-INFRA-001, VA-SEQ-001]
---

# MINISPEC — infra (ytdlp · ffmpeg · openai)

## 0. 이 문서가 다루는 것

`infra/ytdlp.py` · `infra/ffmpeg.py` · `infra/openai.py`의 함수 11개. 클래스 명세 [[VA-DOM-002]] 4.7의 시그니처를 함수 내부까지 내린 것. 외부 프로그램 · API를 감싸는 얇은 층이고 **도메인 타입을 모른다** — 돌려주는 것은 dict · 문자열 · 경로다. 어댑터([[VA-MS-006]])만 부른다. 밖으로 나가는 것은 이 파일 셋을 지나는 것뿐이다([[VA-INFRA-001#C9]]).

형식은 명세 작성 규약 2.10. 간략형이 많다 — 대부분 명령 한 줄이다.

**표기** — `→` 반환, `!` 예외, `EXT:` 외부에 닿는 호출, `PROC:` 자식 프로세스 실행.

**예외 클래스** — `infra/errors.py`에 둘: `YtdlpError(reason, kind)`(`kind` ∈ `private` · `unavailable` · `geo` · `network` · `extractor` · `other`), `FfmpegError(reason, returncode)`. OpenAI는 SDK 예외를 그대로 낸다(`APIConnectionError` · `APIStatusError` · `APITimeoutError`). 어댑터 · 파이프라인이 이것으로 `ErrorKind`를 정한다([[VA-MS-002#pipeline.error_kind]]).

**자식 프로세스** — yt-dlp · ffmpeg는 `asyncio.create_subprocess_exec`로 띄운다(셸 없이, 인자 목록으로 — 경로에 공백 · 특수 문자가 있어도 안전). 표준 오류는 모아서 예외 `reason`에 마지막 3줄을 넣는다. 시간 제한은 `config.PROC_TIMEOUT_SEC`(첫 값 1800 — 3시간 영상 추출도 30분이면 끝난다).

**설정값(첫 값)**

| 이름 | 첫 값 | 이유 |
|---|---|---|
| `config.PROC_TIMEOUT_SEC` | 1800 | 자식 프로세스 상한 |
| `config.YTDLP_BIN` · `config.FFMPEG_BIN` · `config.FFPROBE_BIN` | `yt-dlp` · `ffmpeg` · `ffprobe` | 이미지에 든 실행 파일([[VA-INFRA-001#C8]]) |
| `config.OPENAI_TIMEOUT_SEC` | 120 | 조각 하나 받아쓰기 · 긴 요약 호출의 상한 |
| `config.OPENAI_BASE_URL` | None | OpenAI 주소. 비우면 공식 주소. E2E가 가짜 OpenAI 서버를 가리킬 때만 채운다 — 사용자가 채울 값이 아니다 |
| `config.OPENAI_MAX_RETRIES` | 0 | SDK 자체 재시도를 끈다 — 재시도는 파이프라인이 세면서 한다([[VA-MS-002#pipeline.transcribe_stage]]) |

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#ytdlp.info]] | 영상 정보 JSON (내려받기 없음) |
| [[#ytdlp.captions]] | 자막 원문(VTT) |
| [[#ytdlp.download_audio]] | 가장 좋은 음성 스트림 내려받기 |
| [[#ffmpeg.probe]] | 길이 · 스트림 정보 |
| [[#ffmpeg.extract_audio]] | 음성 추출 · 변환 |
| [[#ffmpeg.silences]] | 무음 구간 가운데 시각 |
| [[#ffmpeg.cut]] | 구간 잘라 새 파일 |
| [[#openai.client]] | 키로 클라이언트 |
| [[#openai.verify_key]] | 모델 목록 조회로 키 확인 |
| [[#openai.transcribe]] | 음성 → verbose_json |
| [[#openai.chat]] | 채팅 완성 (JSON 모드) |

---

## 2. 함수

#### ytdlp.info 영상 정보

**시그니처** `async def info(url: str) -> dict`

근거: [[VA-INFRA-001#C7]] · [[VA-MS-006#youtube_info.info]] · [[VA-MS-006#audio_source.captions]]

**처리**
1. `PROC: yt-dlp --dump-single-json --skip-download --no-playlist --no-warnings {url}` — 정보만. 재생 목록 주소면 그 영상 하나만
2. if 종료 코드 ≠ 0 → 표준 오류에서 종류를 가른다: `Private video` → `private` · `Video unavailable` · `removed` → `unavailable` · `not available in your country` → `geo` · `Unable to download webpage` · `getaddrinfo` · `timed out` → `network` · `Unsupported URL` · `Unable to extract` → `extractor` · 그 밖 → `other` · `! YtdlpError(reason=마지막 줄, kind)`
3. `→ json.loads(표준 출력)` — `id` · `title` · `channel` · `uploader` · `duration` · `subtitles` · `automatic_captions` · `is_live`를 쓴다

**출력** yt-dlp의 JSON 그대로(dict)

**예외** `YtdlpError`

**테스트 관점** 고정 JSON을 내는 가짜 실행 파일로: 필드가 그대로 · 종료 코드 1 + 'Private video' → `kind=private` · 'Unable to extract' → `extractor` · 시간 제한 초과 → `YtdlpError(kind=network)` · 셸을 거치지 않는다(인자에 `;`가 있어도 명령이 안 된다)

---

#### ytdlp.captions 자막 원문

**시그니처** `async def captions(video_id: str, lang: str, kind: str) -> str`

근거: [[VA-MS-006#audio_source.captions]] · [[VA-UC-001#UC-S2]] 1번

**처리** `PROC: yt-dlp --skip-download --no-playlist --sub-format vtt --sub-langs {lang} {--write-subs | --write-auto-subs} -o {tmp}/%(id)s https://www.youtube.com/watch?v={video_id}` (`kind`가 `manual`이면 `--write-subs`, `auto`면 `--write-auto-subs`) · 실패 → `! YtdlpError` · `→ FS: {tmp}/{video_id}.{lang}.vtt 읽은 문자열` · 파일은 읽은 뒤 지운다

**테스트 관점** 가짜 실행 파일이 만든 vtt를 읽어 돌려준다 · `manual`과 `auto`가 다른 플래그 · 파일이 안 생기면 `YtdlpError`

---

#### ytdlp.download_audio 음성 내려받기

**시그니처** `async def download_audio(video_id: str, dest: str) -> str`

근거: [[VA-UC-001#UC-S2]] 1a · [[VA-MS-006#audio_source.download_audio]]

**처리** `PROC: yt-dlp --no-playlist -f bestaudio -o {dest}/source.%(ext)s https://www.youtube.com/watch?v={video_id}` · 실패 → `! YtdlpError` · `→ {dest}/source.{ext}` (m4a 또는 webm/opus. 변환은 어댑터가 `ffmpeg.extract_audio`로)

**테스트 관점** 반환 경로에 파일이 있다 · 영상 스트림을 받지 않는다(`-f bestaudio`) · 네트워크 끊김 → `kind=network`

---

#### ffmpeg.probe 길이 · 스트림

**시그니처** `async def probe(path: str) -> dict`

근거: [[VA-MS-006#media_probe.probe]] · [[VA-MS-006#audio_split.split]]

**처리** `PROC: ffprobe -v error -print_format json -show_format -show_streams {path}` · if 종료 코드 ≠ 0 → `! FfmpegError(reason, returncode)` · `→ json.loads(표준 출력)` — `format.duration`(문자열 초) · `streams[].codec_type`을 쓴다

**테스트 관점** mp4 → `format.duration` 있음, 스트림에 `video` · `audio` · 손상 파일 → `FfmpegError` · 없는 경로 → `FfmpegError`

---

#### ffmpeg.extract_audio 음성 추출 · 변환

**시그니처** `async def extract_audio(src: str, dest: str) -> str`

근거: [[VA-MS-006#audio_source.extract_audio]] · [[VA-MS-006#audio_source.download_audio]] · [[VA-INFRA-001#C2]]

**처리** `out = {dest}/audio.mp3` · `PROC: ffmpeg -y -v error -i {src} -vn -ac 1 -ar 16000 -b:a 64k -codec:a libmp3lame {out}` (`config.AUDIO_FORMAT`) · 실패 → `! FfmpegError` · `src`는 읽기만 · `→ out`

**테스트 관점** 결과 스트림이 mp3 · 모노 · 16kHz(ffprobe로) · 영상 스트림 없음 · `src`는 그대로 · `-y`라 있던 파일을 덮어쓴다

---

#### ffmpeg.silences 무음 시각

**시그니처** `async def silences(path: str) -> list[float]`

근거: [[VA-UC-001#UC-S3]] 1번(조각 경계는 무음 근처) · [[VA-MS-006#audio_split.split]] 2번

**처리**
1. `PROC: ffmpeg -v info -i {path} -af silencedetect=noise={config.SILENCE_DB}dB:d={config.SILENCE_MIN_SEC} -f null -` — 표준 오류에 `silence_start: t` · `silence_end: t` 줄이 나온다
2. 줄을 짝지어 `(start + end) / 2`를 모은다 · 끝이 없는 마지막 `silence_start`는 버린다
3. `→ 오름차순 float 목록`. 무음이 없으면 `[]`

**테스트 관점** 고정 표준 오류 텍스트를 파싱 → 가운데 시각 목록 · 짝 없는 마지막 start 무시 · 무음 없음 → `[]`

---

#### ffmpeg.cut 구간 잘라 새 파일

**시그니처** `async def cut(path: str, start: float, end: float, dest: str) -> str`

근거: [[VA-MS-006#audio_split.split]] 4~5번 · [[VA-INFRA-001#C2]]

**처리** `PROC: ffmpeg -y -v error -ss {start} -to {end} -i {path} -c copy {dest}` — 다시 인코딩하지 않는다(빠르고 음질 그대로. mp3는 프레임 경계라 수십 ms 오차가 있고 오프셋 계산에는 `start`를 쓴다) · 실패 → `! FfmpegError` · `→ dest`

**테스트 관점** 잘린 파일 길이 ≈ `end − start`(±0.1초) · `-c copy`라 빠르다(150분 파일 15조각이 수 초) · `end > 길이`면 끝까지

---

#### openai.client 키로 클라이언트

**시그니처** `def client(key: str) -> AsyncOpenAI`

근거: [[VA-DOM-002]] 4.7 규칙(키는 SettingsService가 준다 · 키마다 클라이언트 하나) · [[VA-MS-005#SettingsService.api_key]] · [[VA-MS-006]] 0장(어댑터는 부를 때마다 `client_for`를 부른다)

**처리** 마지막으로 만든 `(키, 클라이언트)` 한 쌍을 모듈에 둔다 · if `key`가 그 키와 같다 → `→ 그 클라이언트` · else → `c = AsyncOpenAI(api_key=key, base_url=config.OPENAI_BASE_URL, timeout=config.OPENAI_TIMEOUT_SEC, max_retries=config.OPENAI_MAX_RETRIES)` · 쌍을 `(key, c)`로 바꾼다 · `→ c`. 옛 클라이언트는 닫지 않고 버린다 — 옛 키로 보낸 요청이 아직 돌 수 있다. 부르는 곳은 `main.py`가 어댑터에 넘기는 `client_for` 하나이고, 어댑터가 모델을 부를 때마다 불린다. 그래서 화면이나 `.env`에서 키를 바꾸면 다음 호출부터 새 클라이언트다

**테스트 관점** `max_retries=0` · 시간 제한이 설정값 · 같은 키로 두 번 → 같은 객체 · 키가 바뀌면 새 객체, 다시 옛 키면 또 새 객체(한 쌍만 둔다) · 키 문자열이 로그에 안 찍힌다

---

#### openai.verify_key 키 확인

**시그니처** `async def verify_key(key: str) -> KeyCheck`

근거: [[VA-SEQ-001#SEQ-12]] 5~11번 · [[VA-SEQ-001#SEQ-13]] 4~6번 · [[VA-UC-001#UC-H8]] 3번, 3a · [[VA-MS-005#SettingsService.set_key]] · [[VA-MS-005#SettingsService.check_stored_key]]

**처리**
1. if `not key.startswith("sk-") or len(key) < 20` → `→ KeyCheck(invalid, format, '키 형식이 아닙니다', now)` — 요청 없이
2. `c = client(key)` · `EXT: c.models.list()` — 가장 가벼운 인증 요청. `config.KEY_CHECK_TIMEOUT_SEC` 안에
3. if `AuthenticationError`(401) → `KeyCheck(invalid, auth, '인증에 실패했습니다', now)` · `RateLimitError`이고 본문에 `insufficient_quota` → `KeyCheck(invalid, quota, '잔액이 없습니다', now)` · `APIConnectionError` · `APITimeoutError` → `KeyCheck(invalid, network, '연결하지 못했습니다', now)` · 그 밖 `APIStatusError` → `KeyCheck(invalid, auth, 상태 코드와 한 줄, now)`
4. `→ KeyCheck(ok, None, None, now)`

**출력** `KeyCheck`. 던지지 않는다 — 호출자가 상태로 판단한다. `KeyCheck`는 [[VA-DOM-002]] 2.6의 DTO를 `infra`가 만드는 유일한 예외이고 도메인 개념이 아니라 허용한다

**테스트 관점** `abc` → `format`, 요청 0회 · 가짜 401 → `auth` · 429 + `insufficient_quota` → `quota` · 연결 예외 → `network` · 200 → `ok`, `checked_at` 있음

---

#### openai.transcribe 음성 → verbose_json

**시그니처** `async def transcribe(client: AsyncOpenAI, path: str, model: str) -> dict`

근거: [[VA-INFRA-001#C3]] · [[VA-UC-001#UC-S3]] 3번 · [[VA-MS-006#stt_openai.transcribe]]

**처리** `FS: open(path, "rb")` · `EXT: client.audio.transcriptions.create(model=model, file=f, response_format="verbose_json", timestamp_granularities=["segment"])` · `→ 응답을 dict로(language, duration, segments[{start, end, text}])`. SDK 예외는 그대로 올린다. 언어 인자는 주지 않는다(자동 감지)

**테스트 관점** 가짜 SDK가 받은 인자에 `verbose_json` · `["segment"]` · 파일 핸들이 닫힌다 · 25MB 넘는 파일은 SDK가 413을 낸다 — 어댑터 · 파이프라인이 `openai`로 접는지는 그쪽 테스트

---

#### openai.chat 채팅 완성 (JSON 모드)

**시그니처** `async def chat(client: AsyncOpenAI, model: str, messages: list[dict], json_mode: bool = True) -> str`

근거: [[VA-MS-006#summarizer_openai.summary]] · [[VA-MS-006#answerer_openai.answer]] · [[VA-INFRA-001]] 3절(단순 API 호출)

**처리** `EXT: client.chat.completions.create(model=model, messages=messages, response_format={"type": "json_object"} if json_mode else None)` · `→ choices[0].message.content` (문자열. 파싱은 어댑터가) · 빈 응답이면 `""`. SDK 예외는 그대로. 토큰 사용량(`usage`)은 로그에 한 줄 — 비용 확인용([[VA-PRD-001#R8]])

**테스트 관점** `json_mode=True`면 `response_format`이 들어간다 · 응답 문자열이 그대로 · 예외가 그대로 나간다 · 메시지 본문(스크립트)은 로그에 안 찍힌다 — 사용량만

---

## 3. 미결사항

- [ ] yt-dlp 버전 고정과 업데이트 주기 — 이미지 빌드 때 최신을 넣고, 깨지면 이미지를 다시 빌드한다([[VA-INFRA-001#C7]] · 7절). 자동 업데이트(`yt-dlp -U`)를 컨테이너 시작 때 돌릴지 사용자 확인
- [ ] `ffmpeg.cut`의 `-c copy` 오차 — mp3 프레임 경계라 수십 ms. 받아쓰기 시각에는 무시할 수준이지만, 재인코딩(`-c:a libmp3lame`)으로 바꾸면 정확해지는 대신 15조각에 수십 초가 든다. 첫 버전은 `-c copy`
- [ ] OpenAI 사용량 로그를 작업 행에 모아 실제 비용을 보여 줄지 — 사전 안내 예상치와 비교하는 화면이 요구에 없어 첫 버전은 로그만
- [ ] `verify_key`의 `format` 검사(`sk-` 접두)가 앞으로의 키 형식과 맞는지 — 형식이 바뀌면 이 검사만 풀고 요청으로 판정
