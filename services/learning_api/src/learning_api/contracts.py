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
    authentication: Literal["planned_stage_4"] = "planned_stage_4"
    tutor: Literal["disabled"] = "disabled"


class HealthResponse(ApiModel):
    status: Literal["ok"] = "ok"
    service: Literal["learning-api"] = "learning-api"
    version: str
    environment: str
    request_id: str
    dependencies: HealthDependencies = Field(default_factory=HealthDependencies)
