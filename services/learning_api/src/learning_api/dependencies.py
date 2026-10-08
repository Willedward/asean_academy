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
from .account_deletion_repository import PostgresAccountDeletionRepository
from .admin_analytics_repository import PostgresAdminAnalyticsRepository
from .admin_repository import PostgresBetaOperationsRepository
from .conventions import current_request_id
from .diagnostic_repository import PostgresDiagnosticRepository
from .identity import AuthenticatedLearner, AuthenticationError
from .identity_repository import IdentityError, PostgresIdentityRepository
from .practice_service import PracticeService
from .progress_repository import PostgresProgressRepository, SQLiteProgressRepository
from .progress_service import ProgressService
from .question_report_repository import PostgresQuestionReportRepository
from .tutor_provider import provider_for
from .tutor_repository import PostgresTutorRepository, TutorLimits, TutorRepository
from .tutor_routing import (
    TutorModelRouter,
    TutorModelTarget,
    TutorRoutingPolicy,
)
from .tutor_service import TutorService

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


def account_deletion_repository(request: Request) -> PostgresAccountDeletionRepository:
    settings = request.app.state.settings
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "account_deletion_not_configured",
                "message": "Account deletion requires the PostgreSQL database.",
            },
        )
    repository = getattr(request.app.state, "account_deletion_repository", None)
    if repository is None:
        repository = PostgresAccountDeletionRepository(
            settings.database_url,
            settings.abuse_hash_secret,
        )
        request.app.state.account_deletion_repository = repository
    return repository


AccountDeletionRepositoryDependency = Annotated[
    PostgresAccountDeletionRepository, Depends(account_deletion_repository)
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


def diagnostic_repository(request: Request) -> PostgresDiagnosticRepository:
    settings = request.app.state.settings
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "diagnostics_not_configured",
                "message": "Diagnostics require the PostgreSQL database.",
            },
        )
    repository = getattr(request.app.state, "diagnostic_repository", None)
    if repository is None:
        repository = PostgresDiagnosticRepository(settings.database_url)
        request.app.state.diagnostic_repository = repository
    return repository


DiagnosticRepositoryDependency = Annotated[
    PostgresDiagnosticRepository, Depends(diagnostic_repository)
]


def question_report_repository(request: Request) -> PostgresQuestionReportRepository:
    settings = request.app.state.settings
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "question_reports_not_configured",
                "message": "Question reports require the PostgreSQL database.",
            },
        )
    repository = getattr(request.app.state, "question_report_repository", None)
    if repository is None:
        repository = PostgresQuestionReportRepository(settings.database_url)
        request.app.state.question_report_repository = repository
    return repository


QuestionReportRepositoryDependency = Annotated[
    PostgresQuestionReportRepository, Depends(question_report_repository)
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


def tutor_repository(request: Request):
    settings = request.app.state.settings
    repository = getattr(request.app.state, "tutor_repository", None)
    if repository is None:
        if not settings.database_url:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "tutor_not_configured",
                    "message": "Tutor persistence requires the PostgreSQL database.",
                },
            )
        repository = PostgresTutorRepository(settings.database_url)
        request.app.state.tutor_repository = repository
    return repository


TutorRepositoryDependency = Annotated[TutorRepository, Depends(tutor_repository)]


def tutor_service(
    request: Request,
    learner: EnrolledLearnerDependency,
) -> TutorService:
    settings = request.app.state.settings
    if not settings.tutor_enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "tutor_disabled",
                "message": "The AI tutor is not enabled. Authored hints and solutions remain available.",
            },
        )
    repository = tutor_repository(request)
    provider = getattr(request.app.state, "tutor_provider", None)
    if provider is None:
        economy_input_price, economy_output_price = _tutor_prices(
            settings, settings.tutor_provider
        )
        provider = provider_for(
            settings.tutor_provider,
            environment=settings.environment,
            gemini_api_key=settings.tutor_gemini_api_key,
            gemini_model=settings.tutor_gemini_model,
            openai_api_key=settings.tutor_openai_api_key,
            openai_model=settings.tutor_openai_model,
            timeout_seconds=settings.tutor_provider_timeout_seconds,
            max_attempts=settings.tutor_provider_max_attempts,
            input_cost_per_million_micros_sgd=economy_input_price,
            output_cost_per_million_micros_sgd=economy_output_price,
        )
        request.app.state.tutor_provider = provider
    economy_input_price, economy_output_price = _tutor_prices(
        settings, settings.tutor_provider
    )
    economy_target = TutorModelTarget(
        tier="economy",
        provider_name=settings.tutor_provider,
        model_name=_tutor_model_name(settings, settings.tutor_provider),
        max_output_tokens=settings.tutor_economy_max_output_tokens,
        input_cost_per_million_micros_sgd=economy_input_price,
        output_cost_per_million_micros_sgd=economy_output_price,
    )
    premium_provider = None
    premium_target = None
    if settings.tutor_hybrid_routing_enabled:
        premium_provider = getattr(request.app.state, "tutor_premium_provider", None)
        premium_input_price, premium_output_price = _tutor_prices(
            settings, settings.tutor_premium_provider
        )
        if premium_provider is None:
            premium_provider = provider_for(
                settings.tutor_premium_provider,
                environment=settings.environment,
                gemini_api_key=settings.tutor_gemini_api_key,
                gemini_model=settings.tutor_gemini_model,
                openai_api_key=settings.tutor_openai_api_key,
                openai_model=settings.tutor_openai_model,
                timeout_seconds=settings.tutor_provider_timeout_seconds,
                max_attempts=settings.tutor_provider_max_attempts,
                input_cost_per_million_micros_sgd=premium_input_price,
                output_cost_per_million_micros_sgd=premium_output_price,
            )
            request.app.state.tutor_premium_provider = premium_provider
        premium_target = TutorModelTarget(
            tier="premium",
            provider_name=settings.tutor_premium_provider,
            model_name=_tutor_model_name(settings, settings.tutor_premium_provider),
            max_output_tokens=settings.tutor_premium_max_output_tokens,
            input_cost_per_million_micros_sgd=premium_input_price,
            output_cost_per_million_micros_sgd=premium_output_price,
        )
    router = TutorModelRouter(
        TutorRoutingPolicy(
            version=settings.tutor_routing_policy_version,
            economy=economy_target,
            premium=premium_target,
            premium_threshold=settings.tutor_premium_threshold,
            max_premium_turns_per_session=(
                settings.tutor_max_premium_turns_per_session
            ),
        )
    )
    return TutorService(
        repository,
        provider,
        router,
        learner.learner_id,
        premium_provider=premium_provider,
        limits=TutorLimits(
            daily_messages=settings.tutor_daily_message_limit,
            daily_tokens=settings.tutor_daily_token_limit,
            monthly_cost_micros_sgd=settings.tutor_monthly_cost_limit_micros_sgd,
            academy_monthly_cost_micros_sgd=(
                settings.tutor_academy_monthly_cost_limit_micros_sgd
            ),
            max_input_tokens=settings.tutor_max_input_tokens,
            max_output_tokens=settings.tutor_max_output_tokens,
            max_turn_cost_micros_sgd=settings.tutor_max_turn_cost_micros_sgd,
        ),
        model_policy_version=settings.tutor_model_policy_version,
        prompt_version=settings.tutor_prompt_version,
    )


def _tutor_model_name(settings, provider_name: str) -> str:
    if provider_name == "gemini":
        return settings.tutor_gemini_model
    if provider_name == "openai":
        return settings.tutor_openai_model
    if provider_name == "synthetic":
        return "synthetic-tutor-v1"
    raise RuntimeError(f"Unsupported tutor provider: {provider_name}")


def _tutor_prices(settings, provider_name: str) -> tuple[int, int]:
    if provider_name == "gemini":
        return (
            settings.tutor_gemini_input_cost_per_million_micros_sgd,
            settings.tutor_gemini_output_cost_per_million_micros_sgd,
        )
    if provider_name == "openai":
        return (
            settings.tutor_openai_input_cost_per_million_micros_sgd,
            settings.tutor_openai_output_cost_per_million_micros_sgd,
        )
    if provider_name == "synthetic":
        return (0, 0)
    raise RuntimeError(f"Unsupported tutor provider: {provider_name}")


TutorServiceDependency = Annotated[TutorService, Depends(tutor_service)]


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
TutorMessageRateLimitDependency = Annotated[
    None,
    Depends(_rate_limit_dependency("tutor_message")),
]
