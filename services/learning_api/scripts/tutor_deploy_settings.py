"""Resolve and validate the tutor settings a deployment will apply.

The deploy workflows read a few plain variables and this script turns them into the
API's environment, so that switching provider or model is a variable change rather
than a workflow edit. The result is checked through the real API settings, so a
combination the API would refuse fails the deployment before anything is changed.

Variables, all optional for today's Gemini-only pilot:

    TUTOR_PROVIDER      gemini (default) or openai
    TUTOR_MODEL         model name; required for openai or any non-default model
    TUTOR_INPUT_COST_PER_MILLION_MICROS_SGD
    TUTOR_OUTPUT_COST_PER_MILLION_MICROS_SGD
                        required whenever the model is not the pilot default

Secrets: <ENVIRONMENT>_GEMINI_API_KEY or <ENVIRONMENT>_OPENAI_API_KEY, matching the
provider, for example STAGING_GEMINI_API_KEY or PRODUCTION_OPENAI_API_KEY.

Hybrid and shadow routing are always written as off; turning them on is a separate
release decision (see docs/plan/CURRENT_PROJECT_HANDOFF.md).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROVIDER = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_GEMINI_INPUT_COST = "384000"
DEFAULT_GEMINI_OUTPUT_COST = "3200000"

_PROVIDERS = {
    "gemini": ("ASEAN_ACADEMY_TUTOR_GEMINI_MODEL", "GEMINI"),
    "openai": ("ASEAN_ACADEMY_TUTOR_OPENAI_MODEL", "OPENAI"),
}


class TutorDeployError(RuntimeError):
    """A deployment variable combination that must not be applied."""


@dataclass(frozen=True, slots=True)
class TutorDeploySettings:
    settings: dict[str, str]
    key_name: str
    key_source: str


def _value(env: Mapping[str, str], name: str) -> str:
    return env.get(name, "").strip()


def resolve(env: Mapping[str, str], environment: str) -> TutorDeploySettings:
    provider = _value(env, "TUTOR_PROVIDER").lower() or DEFAULT_PROVIDER
    if provider not in _PROVIDERS:
        raise TutorDeployError(
            f"TUTOR_PROVIDER must be gemini or openai, not {provider!r}."
        )
    model = _value(env, "TUTOR_MODEL")
    input_cost = _value(env, "TUTOR_INPUT_COST_PER_MILLION_MICROS_SGD")
    output_cost = _value(env, "TUTOR_OUTPUT_COST_PER_MILLION_MICROS_SGD")
    if provider == "gemini" and (not model or model == DEFAULT_GEMINI_MODEL):
        model = DEFAULT_GEMINI_MODEL
        input_cost = input_cost or DEFAULT_GEMINI_INPUT_COST
        output_cost = output_cost or DEFAULT_GEMINI_OUTPUT_COST
    if not model:
        raise TutorDeployError(f"Set TUTOR_MODEL to the {provider} model to deploy.")
    if not input_cost or not output_cost:
        raise TutorDeployError(
            f"Set TUTOR_INPUT_COST_PER_MILLION_MICROS_SGD and "
            f"TUTOR_OUTPUT_COST_PER_MILLION_MICROS_SGD for {model}, because cost limits "
            "depend on them. They default only for the pilot Gemini model."
        )
    for name, cost in (("input", input_cost), ("output", output_cost)):
        if not cost.isdigit() or int(cost) <= 0:
            raise TutorDeployError(f"The tutor {name} cost must be a positive whole number.")

    model_variable, key_prefix = _PROVIDERS[provider]
    key_name = f"{key_prefix}_API_KEY"
    key_source = f"{environment.upper()}_{key_name}"
    key = _value(env, key_source)
    if not key:
        raise TutorDeployError(
            f"Configure the {key_source} secret; the {provider} tutor cannot start without it."
        )
    prefix = f"ASEAN_ACADEMY_TUTOR_{key_prefix}"
    settings = {
        "ASEAN_ACADEMY_TUTOR_ENABLED": "true",
        "ASEAN_ACADEMY_TUTOR_PROVIDER": provider,
        model_variable: model,
        f"{prefix}_INPUT_COST_PER_MILLION_MICROS_SGD": input_cost,
        f"{prefix}_OUTPUT_COST_PER_MILLION_MICROS_SGD": output_cost,
        "ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_ENABLED": "false",
        "ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_SHADOW_ENABLED": "false",
    }
    _check_against_api_settings(settings, key_name, key)
    return TutorDeploySettings(settings=settings, key_name=key_name, key_source=key_source)


def _check_against_api_settings(settings: dict[str, str], key_name: str, key: str) -> None:
    """Runs the API's own start-up validation over the settings to be applied."""
    from learning_api.config import Settings  # noqa: PLC0415

    # Only what the API requires to start in a hosted environment; nothing is contacted.
    candidate = {
        "ASEAN_ACADEMY_ENV": "preview",
        "ASEAN_ACADEMY_DATABASE_URL": "postgresql://validation-only.invalid/db",
        "SUPABASE_URL": "https://validation-only.invalid",
        "ASEAN_ACADEMY_ABUSE_HASH_SECRET": "validation-only-abuse-hash-secret-0123456789",
        **settings,
        key_name: key,
    }
    previous = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update(candidate)
        Settings.from_environment()
    except RuntimeError as exc:
        raise TutorDeployError(str(exc)) from exc
    finally:
        os.environ.clear()
        os.environ.update(previous)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=["staging", "production"], required=True)
    parser.add_argument(
        "--output", type=Path, help="File for KEY=VALUE settings, one per line; holds no secret."
    )
    args = parser.parse_args()
    try:
        resolved = resolve(os.environ, args.environment)
    except TutorDeployError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    lines = [f"{name}={value}" for name, value in resolved.settings.items()]
    if args.output:
        args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as handle:
            handle.write(f"TUTOR_KEY_NAME={resolved.key_name}\n")
            handle.write(f"TUTOR_KEY_SOURCE={resolved.key_source}\n")
    print("Tutor deployment settings are valid:")
    for line in lines:
        print(f"  {line}")
    print(f"  {resolved.key_name} from the {resolved.key_source} secret")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
