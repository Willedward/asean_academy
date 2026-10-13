"""Authenticated delivery of validated lesson and question diagrams."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Request
from fastapi.responses import FileResponse

from ..course_catalogue import CatalogueError
from ..dependencies import LearnerDependency

router = APIRouter(prefix="/api/v1", tags=["content-assets"])


@router.get(
    "/content-assets/{content_kind}/{stable_key}/{asset_key}",
    operation_id="getContentAsset",
    response_class=FileResponse,
    summary="Return an authenticated validated lesson or question diagram",
)
async def content_asset(
    request: Request,
    content_kind: Literal["lesson", "question"],
    stable_key: Annotated[str, Path(pattern=r"^[a-z0-9-]+$")],
    asset_key: Annotated[str, Path(pattern=r"^[a-z0-9-]+$")],
    _learner: LearnerDependency,
) -> FileResponse:
    try:
        path, asset = request.app.state.course_catalogue.content_asset(
            content_kind, stable_key, asset_key
        )
    except CatalogueError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    media_type = {
        "svg": "image/svg+xml",
        "png": "image/png",
        "webp": "image/webp",
    }[asset.format]
    return FileResponse(
        path,
        media_type=media_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
        },
    )
