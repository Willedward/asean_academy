#!/usr/bin/env python3
"""Run the fixed AI tutor evaluation suite without exposing provider credentials."""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path

from learning_api.tutor_evaluation import (
    load_evaluation_suite,
    run_evaluation,
    write_evaluation_report,
)
from learning_api.tutor_provider import (
    GeminiTutorProvider,
    OpenAITutorProvider,
    SyntheticTutorProvider,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SUITE = (
    REPOSITORY_ROOT
    / "backend_resources"
    / "tutor_evaluations"
    / "g3_math"
    / "v1"
    / "synthetic_foundation.json"
)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic checks and export a human-reviewable tutor report."
    )
    parser.add_argument(
        "--provider",
        choices=("synthetic", "gemini", "openai"),
        default="synthetic",
    )
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Required with a live provider because the run may use paid API tokens.",
    )
    return parser.parse_args()


def integer_environment(name: str, default: int, *, allow_zero: bool = False) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc
    if value < 0 or (value == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise SystemExit(f"{name} must be a {qualifier} integer")
    return value


def selected_provider(name: str, *, live: bool):
    if name == "synthetic":
        return SyntheticTutorProvider(), "synthetic-tutor-v1"
    if not live:
        raise SystemExit("Pass --live to confirm a provider evaluation may consume API quota.")
    if name == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise SystemExit("Set OPENAI_API_KEY in the local environment before a live run.")
        model = os.getenv(
            "ASEAN_ACADEMY_TUTOR_OPENAI_MODEL", "gpt-4o-2024-11-20"
        ).strip()
        return (
            OpenAITutorProvider(
                api_key=api_key,
                model=model,
                timeout_seconds=integer_environment(
                    "ASEAN_ACADEMY_TUTOR_PROVIDER_TIMEOUT_SECONDS", 20
                ),
                max_attempts=integer_environment(
                    "ASEAN_ACADEMY_TUTOR_PROVIDER_MAX_ATTEMPTS", 2
                ),
                input_cost_per_million_micros_sgd=integer_environment(
                    "ASEAN_ACADEMY_TUTOR_OPENAI_INPUT_COST_PER_MILLION_MICROS_SGD",
                    0,
                    allow_zero=True,
                ),
                output_cost_per_million_micros_sgd=integer_environment(
                    "ASEAN_ACADEMY_TUTOR_OPENAI_OUTPUT_COST_PER_MILLION_MICROS_SGD",
                    0,
                    allow_zero=True,
                ),
            ),
            model,
        )
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY in the local environment before a live run.")
    model = os.getenv("ASEAN_ACADEMY_TUTOR_GEMINI_MODEL", "gemini-3.8-flash").strip()
    return (
        GeminiTutorProvider(
            api_key=api_key,
            model=model,
            timeout_seconds=integer_environment(
                "ASEAN_ACADEMY_TUTOR_PROVIDER_TIMEOUT_SECONDS", 20
            ),
            max_attempts=integer_environment("ASEAN_ACADEMY_TUTOR_PROVIDER_MAX_ATTEMPTS", 2),
            input_cost_per_million_micros_sgd=integer_environment(
                "ASEAN_ACADEMY_TUTOR_GEMINI_INPUT_COST_PER_MILLION_MICROS_SGD",
                0,
                allow_zero=True,
            ),
            output_cost_per_million_micros_sgd=integer_environment(
                "ASEAN_ACADEMY_TUTOR_GEMINI_OUTPUT_COST_PER_MILLION_MICROS_SGD",
                0,
                allow_zero=True,
            ),
        ),
        model,
    )


async def main() -> int:
    args = arguments()
    provider, provider_name = selected_provider(args.provider, live=args.live)
    suite = load_evaluation_suite(args.suite.expanduser().resolve())
    output_directory = args.output_dir or (
        REPOSITORY_ROOT
        / "build"
        / "tutor-evaluation"
        / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    )
    report = await run_evaluation(
        provider,
        suite,
        provider_name=provider_name,
        prompt_version=os.getenv(
            "ASEAN_ACADEMY_TUTOR_PROMPT_VERSION", "math-tutor-prompt-v3"
        ),
        max_output_tokens=integer_environment(
            (
                "ASEAN_ACADEMY_TUTOR_PREMIUM_MAX_OUTPUT_TOKENS"
                if args.provider == "openai"
                else "ASEAN_ACADEMY_TUTOR_MAX_OUTPUT_TOKENS"
            ),
            700 if args.provider == "openai" else 1000,
        ),
    )
    json_path, markdown_path = write_evaluation_report(report, output_directory)
    print(f"Automated checks: {report.passed_cases}/{report.total_cases} passed")
    print(f"JSON report: {json_path}")
    print(f"Review report: {markdown_path}")
    print("Human mathematics and editorial review is still required before production approval.")
    return 0 if report.automated_pass else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
