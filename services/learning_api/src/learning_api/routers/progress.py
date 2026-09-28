"""Authenticated learner progress and learning-home endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from ..course_catalogue import CatalogueError
from ..dependencies import (
    LearnerProgressWriteRateLimitDependency,
    ProgressServiceDependency,
)
from ..progress_contracts import (
    ActiveRecallAttemptRequest,
    ActiveRecallAttemptResponse,
    LearningHomeResponse,
    LessonProgressResponse,
    LessonSectionProgressResponse,
    ProgressResponse,
    SetLessonSectionCompletionRequest,
)
from ..progress_repository import ProgressError

router = APIRouter(prefix="/api/v1", tags=["progress"])


def _safe(call):
    try:
        return call()
    except (ProgressError, CatalogueError) as exc:
        status_code = getattr(exc, "status", getattr(exc, "status_code", 400))
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.post(
    "/lessons/{lesson_key}/start",
    operation_id="startLesson",
    response_model=LessonProgressResponse,
    summary="Idempotently start a lesson for the authenticated learner",
)
async def start_lesson(
    lesson_key: Annotated[str, Path(pattern=r"^n1-lesson-[0-9]{2}$")],
    service: ProgressServiceDependency,
    _rate_limit: LearnerProgressWriteRateLimitDependency,
) -> LessonProgressResponse:
    return _safe(lambda: service.start_lesson(lesson_key))


@router.get(
    "/lessons/{lesson_key}/section-progress",
    operation_id="getLessonSectionProgress",
    response_model=LessonSectionProgressResponse,
    summary="Get explicit section completion for the current lesson revision",
)
async def lesson_section_progress(
    lesson_key: Annotated[str, Path(pattern=r"^n1-lesson-[0-9]{2}$")],
    service: ProgressServiceDependency,
) -> LessonSectionProgressResponse:
    return _safe(lambda: service.section_progress(lesson_key))


@router.put(
    "/lessons/{lesson_key}/sections/{section_key}/completion",
    operation_id="setLessonSectionCompletion",
    response_model=LessonSectionProgressResponse,
    summary="Explicitly mark a lesson note section complete or incomplete",
)
async def set_lesson_section_completion(
    body: SetLessonSectionCompletionRequest,
    lesson_key: Annotated[str, Path(pattern=r"^n1-lesson-[0-9]{2}$")],
    section_key: Annotated[str, Path(pattern=r"^[a-z0-9-]+$")],
    service: ProgressServiceDependency,
    _rate_limit: LearnerProgressWriteRateLimitDependency,
) -> LessonSectionProgressResponse:
    return _safe(
        lambda: service.set_section_completion(
            lesson_key,
            section_key,
            completed=body.completed,
        )
    )


@router.post(
    "/lessons/{lesson_key}/sections/{section_key}/active-recall",
    operation_id="checkLessonActiveRecall",
    response_model=ActiveRecallAttemptResponse,
    summary="Check an authored lesson recall answer without exposing its answer key",
)
async def check_lesson_active_recall(
    body: ActiveRecallAttemptRequest,
    lesson_key: Annotated[str, Path(pattern=r"^n1-lesson-[0-9]{2}$")],
    section_key: Annotated[str, Path(pattern=r"^[a-z0-9-]+$")],
    service: ProgressServiceDependency,
    _rate_limit: LearnerProgressWriteRateLimitDependency,
) -> ActiveRecallAttemptResponse:
    return _safe(
        lambda: service.check_active_recall(
            lesson_key,
            section_key,
            answer=body.answer,
        )
    )


@router.get(
    "/progress",
    operation_id="getProgress",
    response_model=ProgressResponse,
    summary="Get authenticated learner progress across the N1 course",
)
async def progress(service: ProgressServiceDependency) -> ProgressResponse:
    return _safe(service.progress)


@router.get(
    "/learning-home",
    operation_id="getLearningHome",
    response_model=LearningHomeResponse,
    summary="Get authenticated learner progress and the recommended next action",
)
async def learning_home(service: ProgressServiceDependency) -> LearningHomeResponse:
    return _safe(service.learning_home)
