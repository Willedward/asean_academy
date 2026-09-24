"""Authenticated request-scoped service composition shared across API routers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .identity import AuthenticatedLearner, AuthenticationError
from .identity_repository import IdentityError, PostgresIdentityRepository
from .practice_service import PracticeService
from .progress_repository import PostgresProgressRepository, SQLiteProgressRepository
from .progress_service import ProgressService

bearer = HTTPBearer(auto_error=False)


def current_learner(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthenticatedLearner:
    settings = request.app.state.settings
    if credentials is not None:
        verifier = request.app.state.token_verifier
        if verifier is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "authentication_not_configured",
                    "message": "Supabase authentication is not configured on this API.",
                },
            )
        try:
            return verifier.verify(credentials.credentials)
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=exc.status,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc
    if settings.development_learner_id is not None:
        return AuthenticatedLearner(
            learner_id=settings.development_learner_id,
            role="student",
            source="development",
        )
    raise HTTPException(
        status_code=401,
        detail={
            "code": "authentication_required",
            "message": "Supply a valid Supabase access token.",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


LearnerDependency = Annotated[AuthenticatedLearner, Depends(current_learner)]


def identity_repository(request: Request) -> PostgresIdentityRepository:
    settings = request.app.state.settings
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "onboarding_not_configured",
                "message": "Invitation onboarding requires the PostgreSQL database.",
            },
        )
    repository = getattr(request.app.state, "identity_repository", None)
    if repository is None:
        repository = PostgresIdentityRepository(settings.database_url)
        request.app.state.identity_repository = repository
    return repository


IdentityRepositoryDependency = Annotated[
    PostgresIdentityRepository, Depends(identity_repository)
]


def enrolled_learner(
    request: Request,
    learner: LearnerDependency,
) -> AuthenticatedLearner:
    if learner.source == "development" or not request.app.state.settings.database_url:
        return learner
    try:
        current = identity_repository(request).current_learner(learner)
    except IdentityError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    if not any(item["status"] == "active" for item in current["enrolments"]):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "active_enrolment_required",
                "message": "An active course enrolment is required.",
            },
        )
    return learner


EnrolledLearnerDependency = Annotated[AuthenticatedLearner, Depends(enrolled_learner)]


def progress_repository(request: Request):
    repository = getattr(request.app.state, "progress_repository", None)
    if repository is None:
        settings = request.app.state.settings
        if settings.database_url:
            repository = PostgresProgressRepository(settings.database_url)
        else:
            database = settings.practice_database or (
                settings.repository_root / ".local" / "practice.sqlite3"
            )
            repository = SQLiteProgressRepository(database)
        request.app.state.progress_repository = repository
    return repository


def progress_service(
    request: Request,
    learner: EnrolledLearnerDependency,
) -> ProgressService:
    return ProgressService(
        request.app.state.course_catalogue,
        progress_repository(request),
        learner.learner_id,
    )


ProgressServiceDependency = Annotated[ProgressService, Depends(progress_service)]


def practice_service(
    request: Request,
    progress: ProgressServiceDependency,
) -> PracticeService:
    settings = request.app.state.settings
    database = settings.practice_database or (
        settings.repository_root / ".local" / "practice.sqlite3"
    )
    return PracticeService(
        settings.repository_root,
        database,
        request.app.state.course_catalogue,
        progress,
        allow_drafts=settings.allow_draft_content,
        database_url=settings.database_url,
    )


PracticeServiceDependency = Annotated[PracticeService, Depends(practice_service)]
