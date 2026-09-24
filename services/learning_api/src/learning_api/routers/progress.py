"""Authenticated learner progress and learning-home endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from ..course_catalogue import CatalogueError
from ..dependencies import ProgressServiceDependency
from ..progress_contracts import (
    LearningHomeResponse,
    LessonProgressResponse,
    ProgressResponse,
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
) -> LessonProgressResponse:
    return _safe(lambda: service.start_lesson(lesson_key))


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
