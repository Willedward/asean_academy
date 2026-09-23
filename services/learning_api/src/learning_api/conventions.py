"""Request identity, authentication and idempotency conventions."""

from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Header, HTTPException, Request, status

REQUEST_ID_HEADER = "X-Request-ID"
IDEMPOTENCY_HEADER = "Idempotency-Key"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def request_id_from(value: str | None) -> str:
    if value and _SAFE_REQUEST_ID.fullmatch(value):
        return value
    return str(uuid4())


def current_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


async def require_idempotency_key(
    value: Annotated[str | None, Header(alias=IDEMPOTENCY_HEADER)] = None,
) -> UUID:
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "idempotency_key_required",
                "message": f"{IDEMPOTENCY_HEADER} must be supplied for this request.",
            },
        )
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_idempotency_key",
                "message": f"{IDEMPOTENCY_HEADER} must be a UUID.",
            },
        ) from exc


async def require_verified_user() -> None:
    """Fail closed until Stage 4 installs the Supabase JWT verifier."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "authentication_not_configured",
            "message": "Authenticated learning endpoints are not enabled yet.",
        },
    )
