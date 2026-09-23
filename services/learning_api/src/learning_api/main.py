"""FastAPI application factory for the core learning API."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .config import Settings
from .contracts import ErrorDetail, ErrorEnvelope, HealthResponse
from .conventions import REQUEST_ID_HEADER, current_request_id, request_id_from
from .course_catalogue import CourseCatalogue
from .routers.courses import router as courses_router

LOGGER = logging.getLogger("learning_api")


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=current_request_id(request),
            details=details,
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def create_app(settings: Settings | None = None) -> FastAPI:
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
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request.state.request_id
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
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception(request: Request, exc: RequestValidationError):
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="validation_error",
            message="The request did not match the API contract.",
            details={"fields": exc.errors(include_url=False, include_context=False)},
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

    @application.get("/api/v1/_error-contract", include_in_schema=False)
    async def error_contract() -> None:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail={"code": "contract_test", "message": "Error contract test."},
        )

    @application.get("/api/v1/_unexpected-error-contract", include_in_schema=False)
    async def unexpected_error_contract() -> None:
        raise RuntimeError("private failure detail")

    application.include_router(courses_router)

    return application


app = create_app()
