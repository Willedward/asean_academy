"""Authenticated request-scoped service composition shared across API routers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from typing import Annotated

import psycopg
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .abuse import (
    POLICIES,
    InMemoryRateLimiter,
    PostgresRateLimiter,
    RateLimiter,
    client_ip,
    decision_headers,
    opaque_subject,
)
from .admin_analytics_repository import PostgresAdminAnalyticsRepository
from .admin_repository import PostgresBetaOperationsRepository
from .conventions import current_request_id
from .identity import AuthenticatedLearner, AuthenticationError
from .identity_repository import IdentityError, PostgresIdentityRepository
from .practice_service import PracticeService
from .progress_repository import PostgresProgressRepository, SQLiteProgressRepository
from .progress_service import ProgressService

bearer = HTTPBearer(auto_error=False)
LOGGER = logging.getLogger("learning_api.abuse")


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


def beta_operations_repository(request: Request) -> PostgresBetaOperationsRepository:
    settings = request.app.state.settings
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "beta_operations_not_configured",
                "message": "Beta operations require the PostgreSQL database.",
            },
        )
    repository = getattr(request.app.state, "beta_operations_repository", None)
    if repository is None:
        repository = PostgresBetaOperationsRepository(settings.database_url)
        request.app.state.beta_operations_repository = repository
    return repository


BetaOperationsRepositoryDependency = Annotated[
    PostgresBetaOperationsRepository, Depends(beta_operations_repository)
]


def admin_analytics_repository(request: Request) -> PostgresAdminAnalyticsRepository:
    settings = request.app.state.settings
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "admin_analytics_not_configured",
                "message": "Administrator analytics require the PostgreSQL database.",
            },
        )
    repository = getattr(request.app.state, "admin_analytics_repository", None)
    if repository is None:
        repository = PostgresAdminAnalyticsRepository(settings.database_url)
        request.app.state.admin_analytics_repository = repository
    return repository


AdminAnalyticsRepositoryDependency = Annotated[
    PostgresAdminAnalyticsRepository, Depends(admin_analytics_repository)
]


def admin_learner(
    learner: LearnerDependency,
    repository: BetaOperationsRepositoryDependency,
) -> AuthenticatedLearner:
    role = repository.role_for(learner.learner_id)
    if role not in {"content_admin", "academic_admin"}:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "administrator_required",
                "message": "An authorized academy administrator is required.",
            },
        )
    return replace(learner, role=role)


AdminLearnerDependency = Annotated[AuthenticatedLearner, Depends(admin_learner)]


def academic_admin_learner(
    administrator: AdminLearnerDependency,
) -> AuthenticatedLearner:
    if administrator.role != "academic_admin":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "academic_administrator_required",
                "message": "An academic administrator is required.",
            },
        )
    return administrator


AcademicAdminLearnerDependency = Annotated[
    AuthenticatedLearner, Depends(academic_admin_learner)
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


def rate_limiter(request: Request) -> RateLimiter:
    limiter = getattr(request.app.state, "rate_limiter", None)
    if limiter is None:
        settings = request.app.state.settings
        limiter = (
            PostgresRateLimiter(settings.database_url)
            if settings.database_url
            else InMemoryRateLimiter()
        )
        request.app.state.rate_limiter = limiter
    return limiter


def _rate_limit_dependency(*policy_keys: str) -> Callable:
    def enforce(
        request: Request,
        response: Response,
        learner: LearnerDependency,
    ) -> None:
        settings = request.app.state.settings
        if not settings.rate_limits_enabled:
            return
        limiter = rate_limiter(request)
        visible_headers: dict[str, str] | None = None
        for policy_key in policy_keys:
            policy = POLICIES[policy_key]
            raw_subject = (
                client_ip(request, trust_proxy_headers=settings.trust_proxy_headers)
                if policy.subject_kind == "ip"
                else learner.learner_id
            )
            digest = opaque_subject(
                settings.abuse_hash_secret,
                policy.subject_kind,
                raw_subject,
            )
            try:
                decision = limiter.consume(
                    policy,
                    digest,
                    request_id=current_request_id(request),
                    path=request.url.path,
                )
            except psycopg.Error as exc:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "abuse_protection_unavailable",
                        "message": "Request protection is temporarily unavailable.",
                    },
                ) from exc
            headers = decision_headers(decision)
            if policy.subject_kind == "learner":
                visible_headers = headers
            if not decision.allowed:
                headers["Retry-After"] = str(decision.retry_after_seconds)
                LOGGER.warning(
                    "rate_limit_exceeded",
                    extra={
                        "request_id": current_request_id(request),
                        "http_method": request.method,
                        "http_path": request.url.path,
                        "rate_limit_policy": policy.key,
                        "rate_limit_subject": policy.subject_kind,
                    },
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "rate_limit_exceeded",
                        "message": "Too many requests. Wait before trying again.",
                        "details": {
                            "limit": decision.limit,
                            "window_seconds": policy.window_seconds,
                            "retry_after_seconds": decision.retry_after_seconds,
                        },
                    },
                    headers=headers,
                )
        if visible_headers:
            response.headers.update(visible_headers)

    return enforce


OnboardingRateLimitDependency = Annotated[
    None,
    Depends(_rate_limit_dependency("onboarding_learner", "onboarding_ip")),
]
PracticeSessionRateLimitDependency = Annotated[
    None,
    Depends(_rate_limit_dependency("practice_session_write")),
]
PracticeAttemptRateLimitDependency = Annotated[
    None,
    Depends(_rate_limit_dependency("practice_attempt")),
]
PracticeSupportRateLimitDependency = Annotated[
    None,
    Depends(_rate_limit_dependency("practice_support")),
]
LearnerProgressWriteRateLimitDependency = Annotated[
    None,
    Depends(_rate_limit_dependency("learner_progress_write")),
]
AdminWriteRateLimitDependency = Annotated[
    None,
    Depends(_rate_limit_dependency("admin_write")),
]
