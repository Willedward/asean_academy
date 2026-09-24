"""Authenticated course map and lesson read endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Request

from ..course_catalogue import CatalogueError, CourseCatalogue
from ..course_contracts import CourseMapResponse, LessonResponse
from ..dependencies import EnrolledLearnerDependency, ProgressServiceDependency

router = APIRouter(prefix="/api/v1", tags=["courses"])


def _catalogue(request: Request) -> CourseCatalogue:
    return request.app.state.course_catalogue


def _safe(call):
    try:
        return call()
    except CatalogueError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.get(
    "/courses/{course_key}/map",
    operation_id="getCourseMap",
    response_model=CourseMapResponse,
    summary="Get the authenticated learner's safe course map",
)
async def course_map(
    request: Request,
    course_key: Annotated[str, Path(pattern=r"^[a-z0-9-]+$")],
    progress: ProgressServiceDependency,
) -> CourseMapResponse:
    course = _safe(lambda: _catalogue(request).course_map(course_key))
    return progress.apply_to_course_map(course)


@router.get(
    "/lessons/{lesson_key}",
    operation_id="getLesson",
    response_model=LessonResponse,
    summary="Get an authenticated learner-safe lesson revision",
)
async def lesson(
    request: Request,
    lesson_key: Annotated[str, Path(pattern=r"^[a-z0-9-]+$")],
    _learner: EnrolledLearnerDependency,
) -> LessonResponse:
    return _safe(lambda: _catalogue(request).lesson(lesson_key))
