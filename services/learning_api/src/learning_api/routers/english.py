"""Authenticated learner routes for deterministic objective-English practice."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Path

from ..course_catalogue import CatalogueError
from ..dependencies import (
    EnglishLearningServiceDependency,
    PracticeAttemptRateLimitDependency,
    PracticeSessionRateLimitDependency,
    PracticeSupportRateLimitDependency,
)
from ..english_contracts import (
    ClassifyEnglishErrorRequest,
    CreateEnglishCheckpointSessionRequest,
    CreateEnglishPracticeSessionRequest,
    EnglishAttemptResponse,
    EnglishCheckpointAttemptResponse,
    EnglishCheckpointNextQuestionResponse,
    EnglishCheckpointSessionResponse,
    EnglishCourseMapResponse,
    EnglishErrorClassificationResponse,
    EnglishHintResponse,
    EnglishLessonResponse,
    EnglishNextQuestionResponse,
    EnglishPracticeSessionResponse,
    EnglishProgressResponse,
    SubmitEnglishAttemptRequest,
    SubmitEnglishCheckpointAttemptRequest,
)
from ..english_learning_repository import EnglishLearningError

router = APIRouter(prefix="/api/v1/english", tags=["english"])

IdempotencyHeader = Annotated[
    str, Header(alias="Idempotency-Key", min_length=1, max_length=200)
]


def _safe(call):
    try:
        return call()
    except (EnglishLearningError, CatalogueError) as exc:
        status_code = getattr(exc, "status", getattr(exc, "status_code", 400))
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.get(
    "/course-map",
    operation_id="getEnglishCourseMap",
    response_model=EnglishCourseMapResponse,
    summary="Get the authenticated learner's English module map",
)
async def course_map(
    service: EnglishLearningServiceDependency,
) -> EnglishCourseMapResponse:
    return _safe(service.course_map)


@router.get(
    "/lessons/{lesson_key}",
    operation_id="getEnglishLesson",
    response_model=EnglishLessonResponse,
    summary="Get one learner-safe English lesson revision",
)
async def lesson(
    lesson_key: Annotated[str, Path(pattern=r"^e[0-9]+-lesson-[0-9]{2}$")],
    service: EnglishLearningServiceDependency,
) -> EnglishLessonResponse:
    return _safe(lambda: service.lesson(lesson_key))


@router.post(
    "/practice-sessions",
    operation_id="createEnglishPracticeSession",
    response_model=EnglishPracticeSessionResponse,
    status_code=201,
    summary="Start or resume an idempotent English objective-practice session",
)
async def create_session(
    body: CreateEnglishPracticeSessionRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSessionRateLimitDependency,
) -> EnglishPracticeSessionResponse:
    return _safe(
        lambda: service.create_session(
            lesson_key=body.lesson_key,
            mode=body.mode,
            idempotency_key=idempotency_key,
        )
    )


@router.post(
    "/checkpoint-sessions",
    operation_id="createEnglishCheckpointSession",
    response_model=EnglishCheckpointSessionResponse,
    status_code=201,
    summary="Start or resume an idempotent protected English module checkpoint",
)
async def create_checkpoint_session(
    body: CreateEnglishCheckpointSessionRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSessionRateLimitDependency,
) -> EnglishCheckpointSessionResponse:
    return _safe(
        lambda: service.create_checkpoint_session(
            module_code=body.module_code,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/checkpoint-sessions/{session_id}",
    operation_id="getEnglishCheckpointSession",
    response_model=EnglishCheckpointSessionResponse,
    summary="Resume an owned English module checkpoint",
)
async def checkpoint_session(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishCheckpointSessionResponse:
    return _safe(lambda: service.checkpoint_session(str(session_id)))


@router.get(
    "/checkpoint-sessions/{session_id}/next",
    operation_id="getNextEnglishCheckpointQuestion",
    response_model=EnglishCheckpointNextQuestionResponse,
    summary="Get the next learner-safe protected checkpoint question",
)
async def next_checkpoint_question(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishCheckpointNextQuestionResponse:
    return _safe(lambda: service.next_checkpoint_question(str(session_id)))


@router.post(
    "/checkpoint-attempts",
    operation_id="submitEnglishCheckpointAttempt",
    response_model=EnglishCheckpointAttemptResponse,
    summary="Submit a protected English checkpoint response without early feedback",
)
async def submit_checkpoint_attempt(
    body: SubmitEnglishCheckpointAttemptRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishCheckpointAttemptResponse:
    return _safe(
        lambda: service.submit_checkpoint_attempt(
            session_id=body.session_id,
            question_key=body.question_key,
            question_revision=body.question_revision,
            answers=body.answers,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/practice-sessions/{session_id}",
    operation_id="getEnglishPracticeSession",
    response_model=EnglishPracticeSessionResponse,
    summary="Resume an owned English objective-practice session",
)
async def session(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishPracticeSessionResponse:
    return _safe(lambda: service.session(str(session_id)))


@router.get(
    "/practice-sessions/{session_id}/next",
    operation_id="getNextEnglishQuestion",
    response_model=EnglishNextQuestionResponse,
    summary="Get the next learner-safe English question",
)
async def next_question(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishNextQuestionResponse:
    return _safe(lambda: service.next_question(str(session_id)))


@router.post(
    "/practice-sessions/{session_id}/questions/{question_key}/hint",
    operation_id="revealEnglishHint",
    response_model=EnglishHintResponse,
    summary="Reveal the authored hint for the current English question",
)
async def hint(
    session_id: UUID,
    question_key: Annotated[
        str, Path(pattern=r"^(ev|eg|eb|eo|er|ex)-l[1-5]-[0-9]{3,4}$")
    ],
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSupportRateLimitDependency,
) -> EnglishHintResponse:
    return _safe(lambda: service.hint(str(session_id), question_key))


@router.post(
    "/attempts",
    operation_id="submitEnglishAttempt",
    response_model=EnglishAttemptResponse,
    summary="Submit an English response for deterministic marking",
)
async def submit_attempt(
    body: SubmitEnglishAttemptRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishAttemptResponse:
    return _safe(
        lambda: service.submit_attempt(
            session_id=body.session_id,
            question_key=body.question_key,
            question_revision=body.question_revision,
            answers=body.answers,
            idempotency_key=idempotency_key,
        )
    )


@router.post(
    "/attempts/{attempt_id}/error-classification",
    operation_id="classifyEnglishAttemptError",
    response_model=EnglishErrorClassificationResponse,
    summary="Record one immutable learner error category for an incorrect attempt",
)
async def classify_error(
    body: ClassifyEnglishErrorRequest,
    attempt_id: UUID,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSupportRateLimitDependency,
) -> EnglishErrorClassificationResponse:
    return _safe(lambda: service.classify_error(str(attempt_id), body.category))


@router.get(
    "/progress",
    operation_id="getEnglishProgress",
    response_model=EnglishProgressResponse,
    summary="Get authenticated objective-English lesson progress and retry counts",
)
async def progress(
    service: EnglishLearningServiceDependency,
) -> EnglishProgressResponse:
    return _safe(service.progress)
