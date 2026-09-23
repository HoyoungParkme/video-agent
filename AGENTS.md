# AGENTS.md — 이 저장소에서 에이전트가 일하는 법

이 저장소는 **명세 우선**이다. 코드는 명세를 옮긴 것이고, 명세에 없는 코드는 만들지 않는다.

## 처음 열었을 때

1. `docs/specs/11-CODE/VA-CODE-001.md` — 구현 계획. **여기서 카드 하나를 받는다.** 순서는 A → B1 → B2 → B3 → B4 → B5 → C
2. 개발 규약 SYNC-STD-004(DEV-1~19)와 명세 작성 규약 SYNC-STD-001 — 싱크독 저장소의 `docs/specs/STD/`에 있다
3. 폴더 구조의 확정본은 `docs/specs/06-DOM/VA-DOM-002.md` 1장

## 작업 순서 (DEV-13)

```
1. CODE-001에서 완료가 "—"이고 선행이 끝난 첫 카드를 받는다
2. 카드의 참조를 전부 연다 — 시나리오 · 유스케이스(왜) → MINISPEC(어떻게) → API · 화면(입구)
   [[VA-MS-007#ytdlp.info]] → docs/specs/10-MS/VA-MS-007.md 의 #### ytdlp.info 블록
3. MINISPEC 순서대로 구현. 함수 하나 = 커밋 하나. docstring 첫 줄 = 항목 ID("VA-MS-007#ytdlp.info")
4. MINISPEC "테스트 관점"을 테스트로. 통과할 때까지
5. 카드의 E2E (시나리오 흐름 그대로)
6. 완료 조건(DEV-14) 확인 → PR → CODE-001 카드 완료란에 기록 → 다음 카드
   화면이 있는 카드는 사람이 브라우저에서 data-el 대로 눌러 본다(일곱째)
```

**막히면 명세가 틀렸거나 모자란 것이다. 코드로 우회하지 않는다.** 명세는 싱크독(MCP `update_document`)으로 고친다 — `docs/specs/`를 손으로 고치지 않는다. 싱크독이 `main`에 커밋하므로 작업 브랜치에는 `git fetch origin main` 뒤 `git merge origin/main`으로 가져온다.

## 브랜치 · 커밋 (사용자 결정 2026-09-23)

- `main`(명세 · 배포) · `dev`(통합) · 작업 브랜치 `feat/card-a`처럼 카드 하나에 하나. 작업 브랜치는 `dev`에서 만든다
- 카드가 끝나면 GitHub PR로 `dev`에 **squash 머지**. PR = 카드 하나, 설명 = 카드 내용 + 완료 조건 체크
- `dev` → `main`은 카드 C(첫 배포) 때 PR. force push는 하지 않는다
- 커밋 `code(카드): 함수명 — 요약`, 둘째 줄부터 이유. 끝난 카드의 버그는 `fix(#이슈번호): 요약`(DEV-15)
- **커밋 메시지와 PR 본문에 에이전트 표시를 넣지 않는다** — `Co-Authored-By` · 세션 링크 · 「Generated with」 없이 제목과 본문만(STD-001 1.10)
- `.env`는 커밋하지 않는다. 키 원문은 로그 · 응답 · 커밋 어디에도 남기지 않는다(DEV-6)

## 개발

호스트에서 돌리고 DB만 compose로 띄운다(INFRA 8절). 호스트 포트는 5433 · 8001 — 5432 · 8000은 다른 앱이 흔히 쓴다.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db   # db → 127.0.0.1:5433
cd backend
export ENV_PATH=../.env INBOX_DIR=../inbox DATA_DIR=../data
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8001
# 다른 터미널에서 저장소 뿌리부터
cd frontend && npm run dev          # http://localhost:3000, /api/* → 127.0.0.1:8001
```

진짜 영상을 호스트에서 돌리려면 ffmpeg와 deno도 필요하다(yt-dlp는 파이썬 의존성이라 함께 깔린다).

## 검사

- `cd backend && uv run pytest` — **전용 DB에서만.** 이름에 `test`가 없는 DB면 시작하지 않는다. 기본은 `va_test`(5433), 바꾸려면 `VA_TEST_DATABASE_URL`. 한 DB에 pytest를 둘 이상 동시에 돌리지 않는다
- `uv run ruff check .` · `uv run ruff format --check .`
- `cd frontend && npx tsc --noEmit` · `npx eslint` · `npm run format` · `npm run build`
- `cd frontend && npm run e2e` — Playwright. 가짜 OpenAI(8190) · api(8100, 빈 .env · 테스트 DB) · web(3100, E2E 전용 빌드)을 스스로 띄운다
- 에이전트가 `next dev`를 돌리면 Next가 `frontend/AGENTS.md` · `CLAUDE.md`를 만든다(무시 목록에 있다). 확인은 `next build` 뒤 standalone 서버로 한다
- 싱크독 검사 도구는 싱크독 저장소 것을 경로로 부른다(사본을 두지 않는다). `S=~/dev/personal/syncdoc/tools`, `D=docs/specs`
  - `python3 $S/check_code.py --specs $D` — MINISPEC ↔ 코드 시그니처(DEV-14 첫째 · 둘째)
  - `python3 $S/check_ui.py --specs $D --screens UI-5` — 와이어프레임 요소 번호 ↔ `data-el`(DEV-17)
  - `python3 $S/check_tokens.py --specs $D` — 디자인 토큰이 UI-001 3장과 같은 값인지. 지금은 싱크독 형식의 3.3만 읽어 VA 문서에서는 간격 줄에서 멈춘다(카드 A 보고)
