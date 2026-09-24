"""Lazy local service composition shared across API routers."""

from __future__ import annotations

from fastapi import HTTPException, Request

from .practice_service import PracticeService
from .progress_repository import SQLiteProgressRepository
from .progress_service import ProgressService


def local_progress_service(request: Request) -> ProgressService:
    settings = request.app.state.settings
    if settings.development_learner_id is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "authentication_required",
                "message": "Learner progress requires authenticated identity.",
            },
        )
    service = getattr(request.app.state, "progress_service", None)
    if service is None:
        database = settings.practice_database or (
            settings.repository_root / ".local" / "practice.sqlite3"
        )
        service = ProgressService(
            request.app.state.course_catalogue,
            SQLiteProgressRepository(database),
            settings.development_learner_id,
        )
        request.app.state.progress_service = service
    return service


def local_practice_service(request: Request) -> PracticeService:
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
            local_progress_service(request),
            allow_drafts=settings.allow_draft_content,
        )
        request.app.state.practice_service = service
    return service
