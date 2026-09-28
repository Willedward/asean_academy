#!/usr/bin/env python3
"""Retrying, secrets-free smoke checks for a deployed ASEAN Academy release."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


class SmokeCheckError(RuntimeError):
    pass


@dataclass(frozen=True)
class CheckResult:
    name: str
    url: str
    status: int
    release_sha: str | None = None


def normalize_base_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Deployment URLs must use http or https and include a host.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Deployment URLs must not contain credentials, queries, or fragments.")
    netloc = parsed.hostname
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    path = parsed.path.rstrip("/") + "/"
    return urlunsplit((parsed.scheme, netloc, path, "", ""))


def request(
    url: str,
    *,
    timeout: float,
    require_json: bool,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any, dict[str, str]]:
    request_headers = {"User-Agent": "asean-academy-release-smoke/1.0"}
    request_headers.update(headers or {})
    req = Request(url, headers=request_headers)
    try:
        with urlopen(req, timeout=timeout) as response:
            status = response.status
            body = response.read()
            response_headers = {
                key.lower(): value for key, value in response.headers.items()
            }
    except HTTPError as exc:
        raise SmokeCheckError(f"{url} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise SmokeCheckError(f"{url} could not be reached: {exc.reason}") from exc
    if not 200 <= status < 400:
        raise SmokeCheckError(f"{url} returned HTTP {status}")
    if not require_json:
        return status, body.decode("utf-8", errors="replace"), response_headers
    try:
        return status, json.loads(body), response_headers
    except json.JSONDecodeError as exc:
        raise SmokeCheckError(f"{url} did not return valid JSON") from exc


def check_api(
    api_url: str,
    *,
    expected_release: str | None,
    expected_environment: str | None,
    timeout: float,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    health_url = urljoin(api_url, "api/v1/health")
    status, health, headers = request(health_url, timeout=timeout, require_json=True)
    if health.get("status") != "ok":
        raise SmokeCheckError("The API health contract did not report status=ok.")
    if expected_environment and health.get("environment") != expected_environment:
        raise SmokeCheckError(
            f"The API environment is {health.get('environment')!r}, not "
            f"{expected_environment!r}."
        )
    release_sha = health.get("release", {}).get("sha")
    header_release = headers.get("x-release-sha")
    if not release_sha or header_release != release_sha:
        raise SmokeCheckError("The API release identity body and header did not match.")
    if expected_release and not release_sha.startswith(expected_release):
        raise SmokeCheckError(
            f"The active API release {release_sha[:12]} does not match "
            f"{expected_release[:12]}."
        )
    results.append(CheckResult("api_health", health_url, status, release_sha))

    ready_url = urljoin(api_url, "api/v1/ready")
    status, ready, _ = request(ready_url, timeout=timeout, require_json=True)
    if ready.get("status") != "ready":
        raise SmokeCheckError("The API readiness contract did not report status=ready.")
    if ready.get("release", {}).get("sha") != release_sha:
        raise SmokeCheckError("Health and readiness reported different releases.")
    if expected_environment and ready.get("environment") != expected_environment:
        raise SmokeCheckError("Health and readiness reported different environments.")
    results.append(CheckResult("api_readiness", ready_url, status, release_sha))
    return results


def check_web(web_url: str, *, timeout: float) -> CheckResult:
    status, _, _ = request(web_url, timeout=timeout, require_json=False)
    return CheckResult("web_root", web_url, status)


def check_web_auth_gate(web_url: str, *, timeout: float) -> CheckResult:
    protected_url = urljoin(web_url, "learn")
    req = Request(
        protected_url,
        headers={"User-Agent": "asean-academy-release-smoke/1.0"},
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
            final_url = response.geturl()
    except HTTPError as exc:
        raise SmokeCheckError(f"{protected_url} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise SmokeCheckError(
            f"{protected_url} could not be reached: {exc.reason}"
        ) from exc
    final = urlsplit(final_url)
    query = parse_qs(final.query)
    if final.path.rstrip("/") != "/login" or query.get("next") != ["/learn"]:
        raise SmokeCheckError(
            "The protected learner page did not redirect to /login?next=/learn."
        )
    if "Continue with Google" not in body:
        raise SmokeCheckError("The hosted login page did not expose Google sign-in.")
    return CheckResult("web_auth_gate", protected_url, status)


def check_supabase_auth(
    supabase_url: str,
    *,
    publishable_key: str,
    timeout: float,
) -> list[CheckResult]:
    headers = {"apikey": publishable_key}
    health_url = urljoin(supabase_url, "auth/v1/health")
    status, health, _ = request(
        health_url,
        timeout=timeout,
        require_json=True,
        headers=headers,
    )
    if health.get("name") != "GoTrue":
        raise SmokeCheckError("Supabase Auth health did not identify GoTrue.")
    settings_url = urljoin(supabase_url, "auth/v1/settings")
    settings_status, settings, _ = request(
        settings_url,
        timeout=timeout,
        require_json=True,
        headers=headers,
    )
    if settings.get("external", {}).get("google") is not True:
        raise SmokeCheckError("Google is not enabled in Supabase Auth settings.")
    return [
        CheckResult("supabase_auth_health", health_url, status),
        CheckResult("supabase_google_provider", settings_url, settings_status),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--web-url")
    parser.add_argument("--expected-release")
    parser.add_argument("--expected-environment")
    parser.add_argument("--require-auth-gate", action="store_true")
    parser.add_argument("--supabase-url")
    parser.add_argument("--supabase-publishable-key")
    parser.add_argument("--attempts", type=int, default=24)
    parser.add_argument("--interval-seconds", type=float, default=5)
    parser.add_argument("--timeout-seconds", type=float, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.attempts < 1 or args.interval_seconds < 0 or args.timeout_seconds <= 0:
        raise SystemExit("Attempts and timeout must be positive; interval cannot be negative.")
    if args.require_auth_gate and not args.web_url:
        raise SystemExit("--require-auth-gate also requires --web-url.")
    if bool(args.supabase_url) != bool(args.supabase_publishable_key):
        raise SystemExit(
            "--supabase-url and --supabase-publishable-key must be supplied together."
        )
    api_url = normalize_base_url(args.api_url)
    web_url = normalize_base_url(args.web_url) if args.web_url else None
    supabase_url = (
        normalize_base_url(args.supabase_url) if args.supabase_url else None
    )

    last_error: SmokeCheckError | None = None
    for attempt in range(1, args.attempts + 1):
        try:
            results = check_api(
                api_url,
                expected_release=args.expected_release,
                expected_environment=args.expected_environment,
                timeout=args.timeout_seconds,
            )
            if web_url:
                results.append(check_web(web_url, timeout=args.timeout_seconds))
            if web_url and args.require_auth_gate:
                results.append(
                    check_web_auth_gate(web_url, timeout=args.timeout_seconds)
                )
            if supabase_url and args.supabase_publishable_key:
                results.extend(
                    check_supabase_auth(
                        supabase_url,
                        publishable_key=args.supabase_publishable_key,
                        timeout=args.timeout_seconds,
                    )
                )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "attempt": attempt,
                        "checks": [asdict(item) for item in results],
                    },
                    separators=(",", ":"),
                )
            )
            return 0
        except SmokeCheckError as exc:
            last_error = exc
            if attempt < args.attempts:
                print(
                    f"Smoke attempt {attempt}/{args.attempts} pending: {exc}",
                    file=sys.stderr,
                )
                time.sleep(args.interval_seconds)

    print(
        json.dumps(
            {
                "status": "failed",
                "attempts": args.attempts,
                "error": str(last_error),
            },
            separators=(",", ":"),
        ),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
