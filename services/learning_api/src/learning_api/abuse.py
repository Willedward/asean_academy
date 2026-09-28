"""Shared, privacy-preserving request rate limits for sensitive API mutations."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import math
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    key: str
    limit: int
    window_seconds: int
    subject_kind: str = "learner"


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime

    @property
    def retry_after_seconds(self) -> int:
        return max(1, math.ceil((self.reset_at - datetime.now(UTC)).total_seconds()))


POLICIES = {
    "onboarding_learner": RateLimitPolicy("onboarding_learner", 5, 15 * 60),
    "onboarding_ip": RateLimitPolicy("onboarding_ip", 20, 15 * 60, "ip"),
    "practice_session_write": RateLimitPolicy("practice_session_write", 30, 10 * 60),
    "practice_attempt": RateLimitPolicy("practice_attempt", 120, 10 * 60),
    "practice_support": RateLimitPolicy("practice_support", 60, 10 * 60),
    "learner_progress_write": RateLimitPolicy("learner_progress_write", 120, 10 * 60),
    "admin_write": RateLimitPolicy("admin_write", 30, 10 * 60),
}


class RateLimiter(Protocol):
    def consume(
        self,
        policy: RateLimitPolicy,
        subject_hash: str,
        *,
        request_id: str,
        path: str,
    ) -> RateLimitDecision: ...


def opaque_subject(secret: str, kind: str, value: str) -> str:
    """Return a stable HMAC without persisting a learner ID, IP address, or token."""

    return hmac.new(
        secret.encode("utf-8"),
        f"{kind}:{value}".encode(),
        hashlib.sha256,
    ).hexdigest()


def client_ip(request, *, trust_proxy_headers: bool) -> str:
    value = request.client.host if request.client else "unknown"
    if trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        if forwarded:
            value = forwarded
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return "unknown"


class InMemoryRateLimiter:
    """Single-process development/test implementation with the production contract."""

    def __init__(self, *, clock=time.time):
        self._clock = clock
        self._buckets: dict[tuple[str, str], tuple[float, int]] = {}
        self._lock = threading.Lock()

    def consume(
        self,
        policy: RateLimitPolicy,
        subject_hash: str,
        *,
        request_id: str,
        path: str,
    ) -> RateLimitDecision:
        del request_id, path
        now = self._clock()
        key = (policy.key, subject_hash)
        with self._lock:
            started_at, count = self._buckets.get(key, (now, 0))
            if now >= started_at + policy.window_seconds:
                started_at, count = now, 0
            count += 1
            self._buckets[key] = (started_at, count)
        return RateLimitDecision(
            allowed=count <= policy.limit,
            limit=policy.limit,
            remaining=max(0, policy.limit - count),
            reset_at=datetime.fromtimestamp(started_at + policy.window_seconds, UTC),
        )


class PostgresRateLimiter:
    """Atomic fixed-window counters shared by every hosted API replica."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def consume(
        self,
        policy: RateLimitPolicy,
        subject_hash: str,
        *,
        request_id: str,
        path: str,
    ) -> RateLimitDecision:
        with psycopg.connect(
            self.database_url,
            connect_timeout=5,
            prepare_threshold=None,
            row_factory=dict_row,
        ) as connection:
            row = connection.execute(
                """
                insert into api_rate_limit_counters as counters (
                    policy_key, subject_hash, window_started_at, request_count, updated_at
                ) values (%s, %s, now(), 1, now())
                on conflict (policy_key, subject_hash) do update set
                    request_count = case
                        when counters.window_started_at + make_interval(secs => %s) <= now()
                            then 1
                        else counters.request_count + 1
                    end,
                    window_started_at = case
                        when counters.window_started_at + make_interval(secs => %s) <= now()
                            then now()
                        else counters.window_started_at
                    end,
                    updated_at = now()
                returning request_count,
                          window_started_at + make_interval(secs => %s) as reset_at
                """,
                (
                    policy.key,
                    subject_hash,
                    policy.window_seconds,
                    policy.window_seconds,
                    policy.window_seconds,
                ),
            ).fetchone()
            if row is None:
                raise RuntimeError("Rate-limit counter did not return a result.")
            allowed = row["request_count"] <= policy.limit
            if not allowed:
                connection.execute(
                    """
                    insert into api_security_events (
                        event_type, policy_key, subject_hash, request_id, request_path
                    ) values ('rate_limit_exceeded', %s, %s, %s, %s)
                    """,
                    (policy.key, subject_hash, request_id, path),
                )
            return RateLimitDecision(
                allowed=allowed,
                limit=policy.limit,
                remaining=max(0, policy.limit - row["request_count"]),
                reset_at=row["reset_at"],
            )


def decision_headers(decision: RateLimitDecision) -> dict[str, str]:
    return {
        "RateLimit-Limit": str(decision.limit),
        "RateLimit-Remaining": str(decision.remaining),
        "RateLimit-Reset": str(max(0, decision.retry_after_seconds)),
    }
