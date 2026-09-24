"""Answer-only practice endpoints backed by deterministic Mathematics marking."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Path, Request
from question_bank.practice import PracticeError

from ..course_catalogue import CatalogueError
from ..practice_contracts import (
    AttemptResponse,
    CreatePracticeSessionRequest,
    GiveUpResponse,
    HintResponse,
    NextQuestionResponse,
    PracticeSessionResponse,
    PracticeSessionSummary,
    SubmitAttemptRequest,
)
from ..practice_service import PracticeService

router = APIRouter(prefix="/api/v1", tags=["practice"])

IdempotencyHeader = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=1, max_length=200),
]


def _service(request: Request) -> PracticeService:
    service = getattr(request.app.state, "practice_service", None)
    if service is None:
        settings = request.app.state.settings
        database = settings.practice_database or (
            settings.repository_root / ".local" / "practice.sqlite3"
        )
        service = PracticeService(
            settings.repository_root,
            database,
            request.app.state.course_catalogue,
            allow_drafts=settings.allow_draft_content,
        )
        request.app.state.practice_service = service
    return service


def _safe(call):
    try:
        return call()
    except (PracticeError, CatalogueError) as exc:
        status_code = getattr(exc, "status", getattr(exc, "status_code", 400))
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.post(
    "/practice-sessions",
    operation_id="createPracticeSession",
    response_model=PracticeSessionResponse,
    status_code=201,
    summary="Start or replay an idempotent lesson-practice session",
)
async def create_session(
    request: Request,
    body: CreatePracticeSessionRequest,
    idempotency_key: IdempotencyHeader,
) -> PracticeSessionResponse:
    return _safe(
        lambda: _service(request).create_lesson_session(
            lesson_key=body.lesson_key,
            mode=body.mode,
            question_count=body.question_count,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/practice-sessions/{session_id}",
    operation_id="getPracticeSession",
    response_model=PracticeSessionSummary,
    summary="Resume practice-session progress",
)
async def get_session(
    request: Request,
    session_id: UUID,
) -> PracticeSessionSummary:
    return _safe(lambda: _service(request).session(str(session_id)))


@router.get(
    "/practice-sessions/{session_id}/next",
    operation_id="getNextPracticeQuestion",
    response_model=NextQuestionResponse,
    summary="Get the current unresolved question or assign the next one",
)
async def next_question(
    request: Request,
    session_id: UUID,
) -> NextQuestionResponse:
    return _safe(lambda: _service(request).next_question(str(session_id)))


@router.post(
    "/attempts",
    operation_id="submitPracticeAttempt",
    response_model=AttemptResponse,
    summary="Submit typed final answers for deterministic marking",
)
async def submit_attempt(
    request: Request,
    body: SubmitAttemptRequest,
    idempotency_key: IdempotencyHeader,
) -> AttemptResponse:
    return _safe(
        lambda: _service(request).submit_attempt(
            session_id=body.session_id,
            question_key=body.question_key,
            question_revision=body.question_revision,
            answers=body.answers,
            idempotency_key=idempotency_key,
        )
    )


@router.post(
    "/practice-sessions/{session_id}/questions/{question_key}/hints/{stage}",
    operation_id="revealPracticeHint",
    response_model=HintResponse,
    summary="Reveal the next authored hint",
)
async def reveal_hint(
    request: Request,
    session_id: UUID,
    question_key: Annotated[str, Path(pattern=r"^n1-l[1-3]-[0-9]{2}$")],
    stage: Annotated[int, Path(ge=1, le=2)],
) -> HintResponse:
    return _safe(
        lambda: _service(request).reveal_hint(
            session_id=str(session_id),
            question_key=question_key,
            stage=stage,
        )
    )


@router.post(
    "/practice-sessions/{session_id}/questions/{question_key}/give-up",
    operation_id="giveUpPracticeQuestion",
    response_model=GiveUpResponse,
    summary="Unlock the authored solution after two incorrect attempts",
)
async def give_up(
    request: Request,
    session_id: UUID,
    question_key: Annotated[str, Path(pattern=r"^n1-l[1-3]-[0-9]{2}$")],
) -> GiveUpResponse:
    return _safe(
        lambda: _service(request).give_up(
            session_id=str(session_id),
            question_key=question_key,
        )
    )
