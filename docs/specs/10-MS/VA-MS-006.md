---
doc_id: VA-MS-006
type: MS
title: MINISPEC — 어댑터 (포트 구현)
status: draft
upstream: [VA-DOM-002, VA-SEQ-001, VA-API-001, VA-UC-001, VA-INFRA-001, VA-PRD-001]
---

# MINISPEC — 어댑터 (포트 구현)

## 0. 이 문서가 다루는 것

클래스 명세 4.6의 포트 7개를 구현하는 어댑터 파일 7개, 함수 11개. 어댑터는 `infra/` 클라이언트([[VA-MS-007]])를 부르고 결과를 그 묶음의 DTO로 바꾼다. 도메인 판단은 하지 않는다 — 서비스가 한다. 프롬프트는 어댑터 안에 산다([[VA-DOM-002]] 1장).

| 파일 | 포트 | 항목 |
|---|---|---|
| `domains/video/adapters/youtube_info.py` | `YouTubeInfoPort` | [[#youtube_info.info]] |
| `domains/video/adapters/media_probe.py` | `MediaProbePort` | [[#media_probe.probe]] |
| `domains/job/adapters/audio_source.py` | `AudioSourcePort` | [[#audio_source.captions]] · [[#audio_source.download_audio]] · [[#audio_source.extract_audio]] |
| `domains/job/adapters/audio_split.py` | `AudioSplitPort` | [[#audio_split.split]] |
| `domains/job/adapters/stt_openai.py` | `SttPort` | [[#stt_openai.transcribe]] |
| `domains/analysis/adapters/summarizer_openai.py` | `SummarizerPort` | [[#summarizer_openai.summary]] · [[#summarizer_openai.chapters]] · [[#summarizer_openai.questions]] |
| `domains/chat/adapters/answerer_openai.py` | `AnswererPort` | [[#answerer_openai.answer]] |

항목 ID는 `파일.함수`다. 코드에서는 파일마다 Protocol을 구현하는 클래스 하나이고(`YouTubeInfoAdapter` 등) 메서드 docstring이 이 항목 ID를 가리킨다. 테스트는 가짜 어댑터로 바꿔 끼우고, 어댑터 자체 테스트는 `infra/`를 가짜로 둔다.

**표기** — `→` 반환, `!` 예외(이름은 [[VA-API-001]] 2장의 `urn:va:` 뒤 부분 또는 `infra/`의 예외 클래스), `FS:` 파일 접근, `EXT:` 외부(YouTube · OpenAI · ffmpeg)에 닿는 호출.

**OpenAI 어댑터 셋의 공통 규칙** — 키는 인자로 받지 않는다. `SettingsService`가 준 키로 `openai.client(key)`를 만든 것을 생성자에서 받는다([[VA-DOM-002]] 4.7 규칙). 모델에 보내는 스크립트는 **`[mm:ss] 문장`** 줄(60분 이상 영상은 `[h:mm:ss]`)이고, 모델이 돌려주는 시각은 같은 표기를 초로 되돌린다. 구조화 출력은 JSON 모드로 받고, JSON이 아니거나 필드가 빠지면 한 번 다시 부른 뒤 그래도 실패하면 `OpenAIOutputError`(→ `ErrorKind.openai`)를 던진다. 언어는 한국어로 지시한다([[VA-UC-001#UC-S4]] 6번).

**설정값(첫 값)**

| 이름 | 첫 값 | 이유 |
|---|---|---|
| `config.CAPTION_LANGS` | `["ko", "en"]` | 자막 언어 우선순위. 없으면 첫 번째 |
| `config.AUDIO_FORMAT` | mp3 · 64kbps · 모노 · 16kHz | 크기와 whisper-1 정확도 사이([[VA-INFRA-001]] 9절 미결을 이 값으로) |
| `config.SPLIT_WINDOW_SEC` | 30 | 조각 경계를 찾을 때 목표 시각 앞뒤로 무음을 찾는 폭 |
| `config.SILENCE_DB` · `config.SILENCE_MIN_SEC` | -35dB · 0.5 | 무음 판정 |
| `config.CHUNK_MAX_BYTES` | 24MB | 25MB 상한([[VA-INFRA-001#C2]])의 안전선 |
| `config.LLM_RETRY` | 1 | 출력 형식 실패 때 다시 부르는 횟수 |

---

## 1. 함수 목록

| 함수 | 한 줄 |
|---|---|
| [[#youtube_info.info]] | 주소 → SourceInfo (제목 · 채널 · 길이 · 자막) |
| [[#media_probe.probe]] | 파일 → (길이, 음성 유무) |
| [[#audio_source.captions]] | 자막 내려받아 줄 목록으로 (수동 → 자동) |
| [[#audio_source.download_audio]] | YouTube 음성 내려받기 |
| [[#audio_source.extract_audio]] | 영상 파일 → mp3 |
| [[#audio_split.split]] | 무음 근처에서 조각 자르기 |
| [[#stt_openai.transcribe]] | 조각 → 시각 붙은 구간 |
| [[#summarizer_openai.summary]] | 한 줄 요약 + 인사이트 |
| [[#summarizer_openai.chapters]] | 챕터 (+ 파트) |
| [[#summarizer_openai.questions]] | 추천 질문 |
| [[#answerer_openai.answer]] | 근거 있는 답 |

---

## 2. 함수

#### youtube_info.info 주소 → SourceInfo

**시그니처** `async def info(url: str) -> SourceInfo`

근거: [[VA-SEQ-001#SEQ-1]] 13~15번 · [[VA-UC-001#UC-H1]] 2번, 2a · [[VA-UC-001#UC-S1]] 1번 · [[VA-INFRA-001#C7]] · [[VA-MS-001#VideoService.info_of]]

**처리**
1. `raw = EXT: ytdlp.info(url)` — 정보만, 내려받기 없음. if `YtdlpError` → `! source-unavailable {reason: 원인 한 줄(비공개 · 삭제 · 지역 제한 · 네트워크를 가려 한국어로), hint: 추출기 오류면 'yt-dlp 업데이트' else None}`
2. `vid = raw.id` · `subs = raw.subtitles`(수동) · `auto = raw.automatic_captions`
3. 자막 — `config.CAPTION_LANGS` 순서로 `subs`에서 찾고, 없으면 `auto`에서 찾는다 · 그래도 없으면 `subs` · `auto`의 첫 언어 · 둘 다 비어 있으면 없음 → `(has_captions, caption_language, caption_kind)` = `(True, lang, manual)` · `(True, lang, auto)` · `(False, None, None)`
4. `→ SourceInfo(source_kind=youtube, source_id=vid, title=raw.title, channel=raw.channel 또는 uploader, duration_sec=int(raw.duration), origin=f"https://www.youtube.com/watch?v={vid}", has_captions, caption_language, caption_kind)` · if `duration`이 없음(라이브 · 예정) → `! source-unavailable {reason: 길이를 알 수 없는 영상}`

**출력** `SourceInfo`

**예외** `source-unavailable`

**호출하는 것** `ytdlp.info` ([[VA-MS-007#ytdlp.info]])

**테스트 관점** 가짜 `ytdlp.info`로: 수동 ko + 자동 en → `manual` · `ko` · 자동만 → `auto` · 자막 없음 → `has_captions=False` · 비공개 오류 → `source-unavailable`에 한국어 `reason` · 추출기 오류 → `hint` 있음 · `channel`이 없으면 `uploader`

---

#### media_probe.probe 파일 → (길이, 음성 유무)

**시그니처** `async def probe(path: str) -> tuple[int, bool]`

근거: [[VA-SEQ-001#SEQ-1]] 17~23번 · [[VA-UC-001#UC-H2]] 2번, 1a · 2a · [[VA-MS-001#VideoService.list_inbox]] · [[VA-MS-001#VideoService.info_of]]

**처리**
1. `raw = EXT: ffmpeg.probe(path)` · if `FfmpegError`(못 열음 · 형식 아님) → `! unsupported-file {reason, accepted}`
2. `duration = int(round(raw.format.duration))` · `has_audio = any(s.codec_type == audio for s in raw.streams)`
3. `→ (duration, has_audio)`

**테스트 관점** 음성 없는 mp4 → `(길이, False)` · mp3 → `(길이, True)` · 손상 파일 → `unsupported-file` · 길이 반올림(3011.6 → 3012)

---

#### audio_source.captions 자막 → 줄 목록

**시그니처** `async def captions(video_id: str) -> tuple[list[CaptionLine], str, CaptionKind] | None`

근거: [[VA-SEQ-001#SEQ-3]] 3~4번 · [[VA-UC-001#UC-S2]] 1~2번 · [[VA-PRD-001#R3]]

**처리**
1. `raw = EXT: ytdlp.info(f"https://www.youtube.com/watch?v={video_id}")` · 언어 · 종류 고르기는 [[#youtube_info.info]] 3번과 같은 규칙 · if 없음 → `→ None`
2. `vtt = EXT: ytdlp.captions(video_id, lang, kind)` — VTT 원문
3. VTT 파싱 → `CaptionLine(start_sec, end_sec, text)` — 큐마다 시각 두 개와 텍스트. 태그(`<c>` · `<00:00:01.000>`) 제거 · 빈 줄 제외
4. 자동 자막의 **굴러가는 중복**을 없앤다 — 앞 큐의 텍스트가 뒤 큐의 앞부분과 같으면 뒤 큐에서 겹친 부분을 뗀다 · 텍스트가 비면 큐를 뺀다 · 같은 텍스트가 잇달아 오면 하나로(끝 시각은 뒤 것)
5. `→ (lines, lang, kind)`

**출력** 줄 목록과 언어 · 종류. `None`이면 파이프라인이 받아쓰기로 간다

**예외** `YtdlpError` → 파이프라인이 `youtube`로 접는다

**호출하는 것** `ytdlp.info` · `ytdlp.captions` ([[VA-MS-007#ytdlp.captions]])

**테스트 관점** VTT 고정 파일로: 수동 자막 30줄 → 30 `CaptionLine`, 시각이 초 · 자동 자막의 굴러가는 큐 → 중복 없이, 문장이 한 번씩 · 태그 제거 · 자막 없음 → `None`

---

#### audio_source.download_audio YouTube 음성 내려받기

**시그니처** `async def download_audio(video_id: str, dest: str) -> str`

근거: [[VA-SEQ-001#SEQ-4]] 2~4번 · [[VA-UC-001#UC-S2]] 1a · [[VA-INFRA-001]] 6절

**처리** `path = EXT: ytdlp.download_audio(video_id, dest)` — 가장 좋은 음성만(m4a · opus), 영상 스트림 없음 · `→ EXT: ffmpeg.extract_audio(path, dest)` — `config.AUDIO_FORMAT`으로 변환한 mp3 경로 · 원본 m4a는 지운다. `YtdlpError` · `FfmpegError`는 그대로 올린다(파이프라인이 접고 `tmp`를 지운다)

**테스트 관점** 가짜 클라이언트로: 반환 경로가 `dest` 안 mp3 · 중간 파일이 남지 않는다 · 내려받기 실패 → `YtdlpError`

---

#### audio_source.extract_audio 영상 → mp3

**시그니처** `async def extract_audio(src: str, dest: str) -> str`

근거: [[VA-SEQ-001#SEQ-4]] 6~8번 · [[VA-UC-001#UC-S2]] 1b · 1c · [[VA-INFRA-001#C4]] · [[VA-INFRA-001]] 9절(음성 파일 형식)

**처리** `→ EXT: ffmpeg.extract_audio(src, dest)` — `config.AUDIO_FORMAT`(mp3 64kbps 모노 16kHz). `src`는 읽기만 한다. 로컬 음성 파일(mp3 · m4a · wav)도 같은 변환을 거친다 — 크기와 형식을 맞추기 위해. `FfmpegError`는 그대로

**테스트 관점** 결과가 모노 · 16kHz · 64kbps(ffprobe로 확인) · `src`의 mtime · 크기가 그대로 · 150분 영상 → 약 72MB

---

#### audio_split.split 무음 근처에서 조각 자르기

**시그니처** `async def split(path: str, dest_dir: str) -> list[ChunkPlan]`

근거: [[VA-SEQ-001#SEQ-4]] 12~14번 · [[VA-UC-001#UC-S3]] 1~2번 · [[VA-INFRA-001#C2]] · [[VA-MS-002#pipeline.transcribe_stage]] 1번

**처리**
1. `total = ffmpeg.probe(path).format.duration` · if `total ≤ config.CHUNK_SEC + config.SPLIT_WINDOW_SEC` → 조각 하나: `→ [ChunkPlan(seq=1, offset_sec=0, duration_sec=total, path=path)]` (자르지 않는다)
2. `silences = EXT: ffmpeg.silences(path)` — 무음 구간의 가운데 시각 목록(`config.SILENCE_DB` · `SILENCE_MIN_SEC`)
3. 경계 = `k × config.CHUNK_SEC`(k = 1, 2, …)마다 `[목표 − SPLIT_WINDOW_SEC, 목표 + SPLIT_WINDOW_SEC]` 안에서 목표에 가장 가까운 무음 시각 · 없으면 목표 시각 그대로(문장이 잘릴 수 있다 — 어쩔 수 없다)
4. 경계마다 `EXT: ffmpeg.cut(path, start, end, f"{dest_dir}/{seq}.mp3")` · `ChunkPlan(seq, offset_sec=start, duration_sec=end − start, path)`
5. if 어느 조각의 파일 크기 > `config.CHUNK_MAX_BYTES` → 그 조각을 반으로 다시 자른다(무음 없이) — 64kbps라 10분이면 4.8MB여서 사실상 안 일어난다
6. `→ 계획 목록 (seq 순)`

**출력** `list[ChunkPlan]`. 조각 수가 화면의 `{k}개 조각`

**예외** `FfmpegError`

**호출하는 것** `ffmpeg.probe` · `ffmpeg.silences` · `ffmpeg.cut` ([[VA-MS-007#ffmpeg.silences]] · [[VA-MS-007#ffmpeg.cut]])

**테스트 관점** 150분 파일 → 15 조각, 경계가 각 600초 ±30초 안의 무음 · 무음 없는 파일 → 정확히 600초마다 · 8분 파일 → 조각 하나, 자르기 호출 없음 · 조각 길이 합 = 전체 · 모든 조각 < 24MB

---

#### stt_openai.transcribe 조각 → 구간

**시그니처** `async def transcribe(path: str, model: str) -> list[SttSegment]`

근거: [[VA-SEQ-001#SEQ-4]] 18~19번 · [[VA-UC-001#UC-S3]] 3번 · [[VA-INFRA-001#C3]] · [[VA-PRD-001#R3]]

**처리**
1. `raw = EXT: openai.transcribe(client, path, model)` — `response_format=verbose_json` · `timestamp_granularities=[segment]` · 언어는 지정하지 않는다(자동 감지, [[VA-UC-001#UC-S3]] 3번)
2. `lang = raw.language`(ISO 639-1로 정규화 — whisper-1은 `korean` 같은 이름을 준다. 표에 없으면 그대로)
3. `→ [SttSegment(start_sec=s.start, end_sec=s.end, text=s.text.strip(), language=lang) for s in raw.segments if s.text.strip()]` — 시각은 조각 안 상대 시각. 오프셋은 파이프라인이 더한다
4. 예외(`APIConnectionError` · `APIStatusError` · 시간 초과)는 그대로 올린다 — 재시도 · 분류는 파이프라인의 몫([[VA-MS-002#pipeline.transcribe_stage]] · [[VA-MS-002#pipeline.error_kind]])

**출력** `list[SttSegment]`

**호출하는 것** `openai.transcribe` ([[VA-MS-007#openai.transcribe]])

**테스트 관점** 가짜 응답으로: `segments` 20개 → 20 `SttSegment`, 빈 텍스트 제외 · `language='korean'` → `ko` · 요청 인자에 `verbose_json`과 `segment`가 들어간다 · 429 → 예외가 그대로 나간다(어댑터가 재시도하지 않는다)

---

#### summarizer_openai.summary 한 줄 요약 + 인사이트

**시그니처** `async def summary(segments: list[Segment], duration_sec: int, model: str) -> SummaryDraft`

근거: [[VA-SEQ-001#SEQ-3]] 11~14번 · [[VA-UC-001#UC-S4]] 3번 · [[VA-PRD-001#R4]] · [[VA-MS-003#AnalysisService.generate_summary]]

**처리**
1. `n = 10 if duration_sec > 3600 else 8` · 본문 = 구간을 `[mm:ss] 문장` 줄로(표기는 길이 기준)
2. 프롬프트(system) — 역할: 영상 스크립트를 읽고 요약하는 편집자 · 규칙: **스크립트에 없는 말을 지어내지 않는다** · 한국어 · 한 줄 요약은 한 문장 · 인사이트는 5~`n`개, 각각 한 문장 + 그 내용이 나오는 시각 1~3개(스크립트의 `[시각]` 표기 그대로) · 출력은 JSON `{"one_liner": str, "insights": [{"text": str, "times": ["12:40", …]}]}`
3. `raw = EXT: openai.chat(client, model, [system, user=본문])` — JSON 모드 · 파싱 · `times`를 초로 · if 형식 오류 → `config.LLM_RETRY`만큼 다시, 그래도 실패 → `! OpenAIOutputError`
4. `→ SummaryDraft(one_liner, insights=[(text, [secs …]) …])` — 시각 범위 보정은 서비스가 한다

**출력** `SummaryDraft`

**호출하는 것** `openai.chat` ([[VA-MS-007#openai.chat]])

**테스트 관점** 가짜 응답으로: JSON 파싱 · `12:40` → 760 · `1:02:03` → 3723 · 깨진 JSON 한 번 → 다시 부르고 성공 · 두 번 깨짐 → `OpenAIOutputError` · 프롬프트에 「지어내지 않는다」와 「한국어」가 들어 있다(스냅샷)

---

#### summarizer_openai.chapters 챕터 (+ 파트)

**시그니처** `async def chapters(segments: list[Segment], duration_sec: int, model: str) -> ChapterDraft`

근거: [[VA-SEQ-001#SEQ-3]] 21~23번 · [[VA-UC-001#UC-S4]] 2번, 2a · [[VA-PRD-001#R5]] · [[VA-MS-003#AnalysisService.generate_chapters]]

**처리**
1. `target = max(3, round(duration_sec / 60 / 6))` · 본문은 `summary`와 같은 형식
2. 프롬프트 — 역할: 주제가 바뀌는 지점을 찾는 편집자 · 규칙: 챕터 `target`개 안팎, 첫 챕터는 스크립트 처음부터, 각 챕터는 시작 시각 · 제목(15자 안팎) · 요점 2~3줄 · 시각은 스크립트의 표기 그대로 · `duration_sec > 3600`이면 챕터를 2~5개 파트로 묶고 파트 제목을 붙인다 · JSON `{"parts": [{"title", "start"}], "chapters": [{"part": int|null, "start", "title", "bullets": [str]}]}`
3. `raw = EXT: openai.chat(…)` · 파싱 · 시각 → 초 · 형식 실패는 `summary`와 같다
4. `→ ChapterDraft(parts=[(title, start_sec) …], chapters=[(part_seq, start_sec, title, bullets) …])` — 60분 이하면 `parts=[]`, `part_seq=None`

**호출하는 것** `openai.chat`

**테스트 관점** 50분 → `parts=[]` · 150분 → 파트 2~5, 챕터마다 `part_seq` · 시각 변환 · 프롬프트에 `target`이 들어간다

---

#### summarizer_openai.questions 추천 질문

**시그니처** `async def questions(segments: list[Segment], model: str) -> list[str]`

근거: [[VA-SEQ-001#SEQ-3]] 29~30번 · [[VA-UC-001#UC-S4]] 4번 · [[VA-PRD-001#R9]] · [[VA-MS-003#AnalysisService.generate_questions]]

**처리** 프롬프트 — 규칙: 이 스크립트만으로 답할 수 있는 질문 3개, 각각 한 문장, 서로 다른 주제, 한국어, 물음표로 끝 · JSON `{"questions": [str, str, str]}` · `raw = EXT: openai.chat(…)` · `→ 문자열 3개` (형식 실패 처리는 같다)

**테스트 관점** 3개 · 물음표로 끝 · 4개 오면 3개로

---

#### answerer_openai.answer 근거 있는 답

**시그니처** `async def answer(question: str, context: list[Segment], history: list[ChatTurn], model: str) -> AnswerDraft`

근거: [[VA-SEQ-001#SEQ-9]] 25~30번 · [[VA-UC-001#UC-H4]] 2~3번, 1b · 3a · [[VA-PRD-001#R6]] · [[VA-MS-004#ChatService.ask]]

**처리**
1. 본문 = `context`를 `[mm:ss] 문장` 줄로(표기는 마지막 구간의 끝 시각이 3600 이상이면 `h:mm:ss`) · 메시지 = `[system, (user, assistant) × history 순서대로, user=question]` — 앞선 턴은 질문 · 답을 그대로, 근거 시각은 답 뒤에 `(근거: 12:40)`로 붙여 대명사가 풀리게
2. 프롬프트(system) — 역할: 이 스크립트에 대해서만 답하는 조수 · 규칙: **스크립트에 있는 내용으로만** 답한다 · 답에 쓴 근거 구간의 시각 1~3개를 스크립트 표기 그대로 · 스크립트에 없는 내용이면 답을 「이 영상에서는 다루지 않습니다.」로 시작하고 시각을 비운다 · 한국어 · 3~5문장 · JSON `{"answer": str, "times": [str]}`
3. `raw = EXT: openai.chat(client, model, messages)` — JSON 모드 · `config.CHAT_TIMEOUT_SEC`는 서비스가 건다 · 형식 실패 처리는 `summary`와 같다
4. `→ AnswerDraft(answer, cited_secs=[초 …])` — 「다루지 않습니다」로 시작하면 `cited_secs=[]`로 강제(모델이 시각을 붙여도)

**출력** `AnswerDraft`

**호출하는 것** `openai.chat`

**테스트 관점** 가짜 응답으로: 근거 둘 → `cited_secs` 두 개 초 단위 · 「다루지 않습니다」 + 시각 → `cited_secs=[]` · `history` 3턴 → 메시지 8개(system + 6 + question) · 프롬프트에 「스크립트에 있는 내용으로만」이 들어 있다

---

## 3. 미결사항

- [ ] 프롬프트 원문은 코드(`adapters/*.py`)에 산다. 스냅샷 테스트로 규칙 문구가 빠지지 않게 지키되, 문장 자체를 명세에 두지 않는다 — 품질을 보며 자주 바뀌기 때문. 이 결정이 맞는지 사용자 확인
- [ ] 자동 자막의 굴러가는 중복 제거 규칙(`captions` 4번)이 YouTube 형식 변화에 약하다. 실제 영상 셋으로 검증 뒤 조정
- [ ] 로컬 음성 파일(mp3 · m4a · wav)도 mp3 64kbps로 다시 변환한다(`extract_audio`). 이미 작은 mp3면 건너뛸지 — 첫 버전은 항상 변환(형식을 하나로)
- [ ] whisper-1 언어 이름 → ISO 코드 표 — 자주 나오는 20개만 두고 나머지는 그대로. [[VA-INFRA-001]] 9절 음성 형식 미결은 `config.AUDIO_FORMAT`으로 닫는다
- [ ] JSON 모드가 시각 표기를 가끔 `12:40:00`처럼 바꾼다 — 파서가 `h:mm:ss`로 읽어 버리면 시각이 밀린다. 길이가 60분 미만인데 세 자리 표기가 오면 `mm:ss:00`으로 해석할지 테스트로 확인
