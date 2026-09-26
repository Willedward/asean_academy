"""FastAPI application factory for the core learning API."""

from __future__ import annotations

import logging
from time import perf_counter

import psycopg
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

from . import __version__
from .config import Settings
from .contracts import (
    ErrorDetail,
    ErrorEnvelope,
    HealthResponse,
    ReadinessDependencies,
    ReadinessResponse,
)
from .conventions import REQUEST_ID_HEADER, current_request_id, request_id_from
from .course_catalogue import CourseCatalogue
from .identity import SupabaseTokenVerifier, TokenVerifier
from .routers.admin import router as admin_router
from .routers.admin_analytics import router as admin_analytics_router
from .routers.courses import router as courses_router
from .routers.identity import router as identity_router
from .routers.practice import router as practice_router
from .routers.progress import router as progress_router

LOGGER = logging.getLogger("learning_api")


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=current_request_id(request),
            details=details,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
        headers=headers,
    )


def create_app(
    settings: Settings | None = None,
    *,
    token_verifier: TokenVerifier | None = None,
) -> FastAPI:
    settings = settings or Settings.from_environment()
    logging.basicConfig(level=settings.log_level)

    application = FastAPI(
        title="ASEAN Academy Learning API",
        version=__version__,
        description=(
            "Versioned course and practice API. Lesson bodies remain draft placeholders "
            "until reviewed content and video assets are supplied."
        ),
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        responses={
            400: {"model": ErrorEnvelope},
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
            500: {"model": ErrorEnvelope},
        },
    )
    application.state.settings = settings
    application.state.token_verifier = token_verifier or (
        SupabaseTokenVerifier(
            settings.supabase_url,
            audience=settings.supabase_jwt_audience,
            anon_key=settings.supabase_anon_key,
        )
        if settings.supabase_url
        else None
    )
    application.state.course_catalogue = CourseCatalogue(
        settings.repository_root,
        allow_drafts=settings.allow_draft_content,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
        expose_headers=[REQUEST_ID_HEADER],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request_id_from(request.headers.get(REQUEST_ID_HEADER))
        started_at = perf_counter()
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request.state.request_id
        LOGGER.info(
            "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request.state.request_id,
            request.method,
            request.url.path,
            response.status_code,
            (perf_counter() - started_at) * 1000,
        )
        return response

    @application.exception_handler(HTTPException)
    async def http_exception(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            code = str(exc.detail.get("code", "http_error"))
            message = str(exc.detail.get("message", "The request could not be completed."))
            details = exc.detail.get("details")
        else:
            code = "http_error"
            message = str(exc.detail)
            details = None
        return _error_response(
            request,
            status_code=exc.status_code,
            code=code,
            message=message,
            details=details,
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception(request: Request, exc: RequestValidationError):
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="validation_error",
            message="The request did not match the API contract.",
            details={
                "fields": [
                    {key: value for key, value in error.items() if key not in {"ctx", "url"}}
                    for error in exc.errors()
                ]
            },
        )

    @application.exception_handler(Exception)
    async def unexpected_exception(request: Request, exc: Exception):
        LOGGER.exception(
            "unhandled_exception request_id=%s",
            current_request_id(request),
            exc_info=exc,
        )
        return _error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message="The server could not complete the request.",
        )

    @application.get(
        "/api/v1/health",
        operation_id="getHealth",
        tags=["system"],
        response_model=HealthResponse,
        summary="Check learning API availability",
    )
    async def health(request: Request) -> HealthResponse:
        return HealthResponse(
            version=__version__,
            environment=settings.environment,
            request_id=current_request_id(request),
        )

    @application.get(
        "/api/v1/ready",
        operation_id="getReadiness",
        tags=["system"],
        response_model=ReadinessResponse,
        summary="Check database and schema readiness before receiving traffic",
    )
    def readiness(request: Request) -> ReadinessResponse:
        if not settings.database_url:
            dependencies = ReadinessDependencies(database="local", schema_status="local")
        else:
            try:
                with psycopg.connect(
                    settings.database_url,
                    connect_timeout=5,
                    prepare_threshold=None,
                    row_factory=dict_row,
                ) as connection:
                    row = connection.execute(
                        """
                        select exists (
                            select 1 from information_schema.columns
                            where table_schema = 'public'
                              and table_name = 'profiles'
                              and column_name = 'email'
                        ) as schema_ready
                        """
                    ).fetchone()
            except psycopg.Error as exc:
                LOGGER.warning(
                    "readiness_database_failed request_id=%s error_type=%s",
                    current_request_id(request),
                    type(exc).__name__,
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "database_unavailable",
                        "message": "The learning database is unavailable.",
                    },
                ) from exc
            if row is None or not row["schema_ready"]:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "database_schema_outdated",
                        "message": "The learning database schema is not ready.",
                    },
                )
            dependencies = ReadinessDependencies(database="ready", schema_status="current")
        return ReadinessResponse(
            version=__version__,
            environment=settings.environment,
            request_id=current_request_id(request),
            dependencies=dependencies,
        )

    @application.get("/api/v1/_error-contract", include_in_schema=False)
    async def error_contract() -> None:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail={"code": "contract_test", "message": "Error contract test."},
        )

    @application.get("/api/v1/_unexpected-error-contract", include_in_schema=False)
    async def unexpected_error_contract() -> None:
        raise RuntimeError("private failure detail")

    application.include_router(identity_router)
    application.include_router(admin_router)
    application.include_router(admin_analytics_router)
    application.include_router(courses_router)
    application.include_router(practice_router)
    application.include_router(progress_router)

    return application


app = create_app()
