#!/usr/bin/env python3
"""Run a small bounded concurrency smoke against a deployed ASEAN Academy API."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Sample:
    status: int | None
    duration_ms: float
    error: str | None


def _origin(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("API URL must be an absolute HTTP(S) origin.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise argparse.ArgumentTypeError(
            "API URL cannot contain credentials, a query string, or a fragment."
        )
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "")
    )


def _path(value: str) -> str:
    if not value.startswith("/") or "?" in value or "#" in value:
        raise argparse.ArgumentTypeError(
            "Path must begin with / and cannot contain a query or fragment."
        )
    return value


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _request(url: str, token: str | None, timeout_seconds: float) -> Sample:
    headers = {"Accept": "application/json", "User-Agent": "asean-academy-load-smoke/1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response.read(1024)
            status = response.status
    except urllib.error.HTTPError as exc:
        exc.read(1024)
        status = exc.code
        error = f"http_{exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        status = None
        error = type(exc).__name__
    else:
        error = None
    return Sample(
        status=status,
        duration_ms=round((time.perf_counter() - started) * 1000, 2),
        error=error,
    )


def run(
    *,
    api_url: str,
    path: str,
    requests: int,
    concurrency: int,
    timeout_seconds: float,
    max_p95_ms: float,
    minimum_success_ratio: float,
    expected_status: int,
    token: str | None,
) -> tuple[dict, bool]:
    target = f"{api_url}{path}"
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        samples = list(
            executor.map(
                lambda _: _request(target, token, timeout_seconds),
                range(requests),
            )
        )
    elapsed_seconds = time.perf_counter() - started
    successful = [sample for sample in samples if sample.status == expected_status]
    durations = [sample.duration_ms for sample in samples]
    status_counts: dict[str, int] = {}
    for sample in samples:
        key = (
            str(sample.status)
            if sample.status is not None
            else sample.error or "unknown"
        )
        status_counts[key] = status_counts.get(key, 0) + 1
    success_ratio = len(successful) / requests
    p95_ms = _percentile(durations, 0.95)
    passed = success_ratio >= minimum_success_ratio and p95_ms <= max_p95_ms
    result = {
        "status": "passed" if passed else "failed",
        "target": target,
        "requests": requests,
        "concurrency": concurrency,
        "expected_status": expected_status,
        "status_counts": status_counts,
        "success_ratio": round(success_ratio, 4),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "requests_per_second": round(requests / elapsed_seconds, 2),
        "latency_ms": {
            "min": min(durations),
            "mean": round(statistics.fmean(durations), 2),
            "p50": _percentile(durations, 0.50),
            "p95": p95_ms,
            "max": max(durations),
        },
        "thresholds": {
            "minimum_success_ratio": minimum_success_ratio,
            "max_p95_ms": max_p95_ms,
        },
    }
    if not passed:
        result["failed_samples"] = [
            asdict(sample) for sample in samples if sample.status != expected_status
        ][:10]
    return result, passed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bounded staging load smoke; does not create learner data."
    )
    parser.add_argument("--api-url", required=True, type=_origin)
    parser.add_argument("--path", default="/api/v1/health", type=_path)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--max-p95-ms", type=float, default=1500.0)
    parser.add_argument("--minimum-success-ratio", type=float, default=0.99)
    parser.add_argument("--expected-status", type=int, default=200)
    args = parser.parse_args()
    if not 1 <= args.requests <= 1_000:
        parser.error("--requests must be between 1 and 1000")
    if not 1 <= args.concurrency <= min(args.requests, 50):
        parser.error("--concurrency must be between 1 and min(requests, 50)")
    if not 0 < args.timeout_seconds <= 60:
        parser.error("--timeout-seconds must be greater than 0 and at most 60")
    if not 0 < args.minimum_success_ratio <= 1:
        parser.error("--minimum-success-ratio must be greater than 0 and at most 1")
    if args.max_p95_ms <= 0:
        parser.error("--max-p95-ms must be greater than 0")

    result, passed = run(
        api_url=args.api_url,
        path=args.path,
        requests=args.requests,
        concurrency=args.concurrency,
        timeout_seconds=args.timeout_seconds,
        max_p95_ms=args.max_p95_ms,
        minimum_success_ratio=args.minimum_success_ratio,
        expected_status=args.expected_status,
        token=os.getenv("LOAD_TEST_ACCESS_TOKEN"),
    )
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
