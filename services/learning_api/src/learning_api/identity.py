"""Authenticated learner identity and Supabase access-token verification."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from uuid import UUID

import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    InvalidTokenError,
    PyJWKClientConnectionError,
    PyJWKClientError,
)


class AuthenticationError(ValueError):
    """A safe authentication failure suitable for the public API."""

    def __init__(self, code: str, message: str, status: int = 401):
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True, slots=True)
class AuthenticatedLearner:
    learner_id: str
    role: str
    email: str | None = None
    source: str = "supabase"


class TokenVerifier(Protocol):
    def verify(self, token: str) -> AuthenticatedLearner: ...


def _learner(payload: dict, *, source: str) -> AuthenticatedLearner:
    subject = str(payload.get("sub") or payload.get("id") or "")
    try:
        learner_id = str(UUID(subject))
    except (ValueError, TypeError) as exc:
        raise AuthenticationError(
            "invalid_access_token",
            "The access token does not identify a valid learner.",
        ) from exc
    role = str(payload.get("role") or "authenticated")
    if role not in {"authenticated", "student", "content_admin", "academic_admin"}:
        raise AuthenticationError(
            "invalid_access_token",
            "The access token has an unsupported role.",
        )
    email = payload.get("email")
    return AuthenticatedLearner(
        learner_id=learner_id,
        role=role,
        email=str(email) if email else None,
        source=source,
    )


class SupabaseTokenVerifier:
    """Verify asymmetric Supabase JWTs locally and legacy HS256 tokens via Auth."""

    def __init__(
        self,
        supabase_url: str,
        *,
        audience: str = "authenticated",
        anon_key: str | None = None,
        timeout_seconds: float = 5,
    ):
        self.supabase_url = supabase_url.rstrip("/")
        self.issuer = f"{self.supabase_url}/auth/v1"
        self.audience = audience
        self.anon_key = anon_key
        self.timeout_seconds = timeout_seconds
        self.jwks = PyJWKClient(f"{self.issuer}/.well-known/jwks.json", cache_keys=True)

    def verify(self, token: str) -> AuthenticatedLearner:
        try:
            algorithm = str(jwt.get_unverified_header(token).get("alg", ""))
        except InvalidTokenError as exc:
            raise AuthenticationError(
                "invalid_access_token", "The access token is invalid."
            ) from exc
        if algorithm in {"RS256", "ES256"}:
            return self._verify_asymmetric(token, algorithm)
        if algorithm == "HS256":
            return self._verify_with_auth_server(token)
        raise AuthenticationError(
            "invalid_access_token",
            "The access token uses an unsupported signing algorithm.",
        )

    def _verify_asymmetric(self, token: str, algorithm: str) -> AuthenticatedLearner:
        try:
            signing_key = self.jwks.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub", "role"]},
            )
        except PyJWKClientConnectionError as exc:
            raise AuthenticationError(
                "identity_provider_unavailable",
                "The identity provider could not be reached.",
                503,
            ) from exc
        except (InvalidTokenError, PyJWKClientError) as exc:
            raise AuthenticationError(
                "invalid_access_token",
                "The access token is expired or invalid.",
            ) from exc
        return _learner(payload, source="supabase_jwks")

    def _verify_with_auth_server(self, token: str) -> AuthenticatedLearner:
        if not self.anon_key:
            raise AuthenticationError(
                "legacy_token_verification_unavailable",
                "Legacy Supabase tokens require SUPABASE_ANON_KEY on the API server.",
                503,
            )
        request = UrlRequest(
            f"{self.issuer}/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": self.anon_key,
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except HTTPError as exc:
            status = 401 if exc.code in {400, 401, 403} else 503
            code = "invalid_access_token" if status == 401 else "identity_provider_unavailable"
            message = (
                "The access token is expired or invalid."
                if status == 401
                else "The identity provider could not be reached."
            )
            raise AuthenticationError(code, message, status) from exc
        except (URLError, TimeoutError, ValueError) as exc:
            raise AuthenticationError(
                "identity_provider_unavailable",
                "The identity provider could not be reached.",
                503,
            ) from exc
        return _learner(payload, source="supabase_auth")


class StaticTokenVerifier:
    """Deterministic verifier used by contract tests and local preview harnesses."""

    def __init__(self, identities: dict[str, AuthenticatedLearner]):
        self.identities = identities

    def verify(self, token: str) -> AuthenticatedLearner:
        identity = self.identities.get(token)
        if identity is None:
            raise AuthenticationError(
                "invalid_access_token", "The access token is expired or invalid."
            )
        return identity
