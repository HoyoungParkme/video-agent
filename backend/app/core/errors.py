"""problem+json 에러 17종 — 종류마다 예외 클래스 하나(VA-API-001 2장, DEV-5).

서비스는 이 예외를 던지기만 하고 라우터는 잡지 않는다. main.py가 건 핸들러가 응답으로 바꾸고,
표에 없는 예외는 포괄 핸들러가 `internal`로 만든다. 카드 스텁의 `not-implemented`(501)는
표에 없는 임시 종류다 — 스텁이 모두 풀리는 B4에서 지운다(VA-CODE-001 0장).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

MEDIA_TYPE = "application/problem+json"


class Problem(Exception):
    """problem+json 하나. 하위 클래스가 종류 · 상태 · 제목을 정하고, 확장 필드는 키워드로 받는다."""

    kind = "internal"
    status = 500
    title = "예상하지 못한 오류가 났어요"

    def __init__(self, detail: str | None = None, **extra: Any) -> None:
        super().__init__(detail or self.title)
        self.detail = detail or self.title
        self.extra = extra

    def body(self) -> dict[str, Any]:
        """응답 본문 — 공통 넷 + 확장 필드."""
        return {
            "type": f"urn:va:{self.kind}",
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            **self.extra,
        }


class NotFound(Problem):
    """영상 · 작업 · inbox 파일 없음. resource · id"""

    kind, status, title = "not-found", 404, "찾을 수 없어요"


class Validation(Problem):
    """요청 본문 형식 오류. errors: [{field, message}]"""

    kind, status, title = "validation", 422, "요청 형식이 맞지 않아요"


class KeyMissing(Problem):
    """저장된 키가 없다."""

    kind, status, title = "key-missing", 503, "OpenAI API 키가 없어요"


class KeyInvalid(Problem):
    """저장된 키가 마지막 확인에 실패했다. reason_kind · reason · checked_at"""

    kind, status, title = "key-invalid", 503, "OpenAI API 키를 확인하지 못했어요"


class KeyRejected(Problem):
    """새로 넣은 키가 확인에 실패했다 — 저장하지 않는다. reason_kind · reason"""

    kind, status, title = "key-rejected", 422, "키를 확인하지 못했어요"


class UrlInvalid(Problem):
    """YouTube 주소 형식이 아니다. accepted"""

    kind, status, title = "url-invalid", 422, "YouTube 주소가 아니에요"


class SourceUnavailable(Problem):
    """YouTube 정보를 못 가져왔다. reason · hint"""

    kind, status, title = "source-unavailable", 502, "영상 정보를 가져오지 못했어요"


class VideoTooLong(Problem):
    """3시간 초과. duration_sec · max_sec"""

    kind, status, title = "video-too-long", 422, "3시간보다 긴 영상이에요"


class NoAudioTrack(Problem):
    """로컬 영상에 음성 트랙이 없다. duration_sec"""

    kind, status, title = "no-audio-track", 422, "음성이 없는 파일이에요"


class UnsupportedFile(Problem):
    """영상 · 음성 파일이 아니거나 열 수 없다. reason · accepted"""

    kind, status, title = "unsupported-file", 422, "열 수 없는 파일이에요"


class PathOutsideInbox(Problem):
    """inbox 폴더 밖을 가리키는 경로."""

    kind, status, title = "path-outside-inbox", 422, "inbox 폴더 밖의 경로예요"


class JobExists(Problem):
    """이 영상에 이미 작업이 있다. job_id · job_status"""

    kind, status, title = "job-exists", 409, "이미 분석한 영상이에요"


class JobNotFailed(Problem):
    """실패 상태가 아닌 작업을 다시 시도. job_status"""

    kind, status, title = "job-not-failed", 409, "실패한 작업이 아니에요"


class ResultNotReady(Problem):
    """결과가 아직 없다. video_status"""

    kind, status, title = "result-not-ready", 409, "결과가 아직 없어요"


class LlmUnavailable(Problem):
    """OpenAI 호출 실패 · 사용량 초과. reason"""

    kind, status, title = "llm-unavailable", 502, "OpenAI API에 연결하지 못했어요"


class ExportFailed(Problem):
    """data/export/에 파일을 쓰지 못했다. path · reason"""

    kind, status, title = "export-failed", 500, "파일을 저장하지 못했어요"


class Internal(Problem):
    """예상 못 한 오류. detail은 고정 문구, 원인은 로그만."""


class NotImplementedYet(Problem):
    """아직 만들지 않은 기능 — 카드의 스텁(VA-CODE-001 0장). API 에러 표에 없는 임시 종류."""

    kind, status, title = "not-implemented", 501, "아직 지원하지 않는 기능이에요"


def _response(problem: Problem) -> JSONResponse:
    return JSONResponse(problem.body(), status_code=problem.status, media_type=MEDIA_TYPE)


async def _on_problem(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, Problem)
    if exc.status >= 500:  # 원인(from e)은 로그로만 — 응답에는 고정 문구뿐
        log.error("%s: %s", exc.kind, exc.detail, exc_info=exc)
    return _response(exc)


async def _on_validation(_: Request, exc: Exception) -> JSONResponse:
    # 입력값은 돌려주지 않는다 — 키가 들어 있을 수 있다(DEV-6)
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
        for e in exc.errors()
    ]
    return _response(Validation(errors=errors))


async def _on_unexpected(_: Request, exc: Exception) -> JSONResponse:
    # 원인은 로그로만 — Starlette가 응답을 보낸 뒤 예외를 다시 올려 서버가 기록한다
    return _response(Internal())


def install(app: FastAPI) -> None:
    """앱에 핸들러 셋을 건다 — 17종 · 요청 형식 오류 · 포괄."""
    app.add_exception_handler(Problem, _on_problem)
    app.add_exception_handler(RequestValidationError, _on_validation)
    app.add_exception_handler(Exception, _on_unexpected)
