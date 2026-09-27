"""Stable response and error envelopes shared by every API module."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorDetail(ApiModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$")
    message: str
    request_id: str
    details: dict[str, Any] | None = None


class ErrorEnvelope(ApiModel):
    error: ErrorDetail


class HealthDependencies(ApiModel):
    course_content: Literal["draft_placeholders"] = "draft_placeholders"
    authentication: Literal["supabase_bearer"] = "supabase_bearer"
    tutor: Literal["disabled"] = "disabled"


class ReleaseMetadata(ApiModel):
    sha: str
    deployment_id: str | None = None
    required_schema_revision: str


class HealthResponse(ApiModel):
    status: Literal["ok"] = "ok"
    service: Literal["learning-api"] = "learning-api"
    version: str
    environment: str
    request_id: str
    release: ReleaseMetadata
    dependencies: HealthDependencies = Field(default_factory=HealthDependencies)


class ReadinessDependencies(ApiModel):
    database: Literal["ready", "local"]
    schema_status: Literal["current", "local"]


class ReadinessResponse(ApiModel):
    status: Literal["ready"] = "ready"
    service: Literal["learning-api"] = "learning-api"
    version: str
    environment: str
    request_id: str
    release: ReleaseMetadata
    dependencies: ReadinessDependencies
