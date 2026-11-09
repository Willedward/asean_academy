"""The deploy variables for the tutor resolve to settings the API accepts, or fail clearly."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tutor_deploy_settings.py"
spec = importlib.util.spec_from_file_location("tutor_deploy_settings", SCRIPT)
assert spec is not None and spec.loader is not None
script = importlib.util.module_from_spec(spec)
sys.modules["tutor_deploy_settings"] = script
spec.loader.exec_module(script)

GEMINI_KEY = {"STAGING_GEMINI_API_KEY": "private-gemini-key"}
OPENAI_KEY = {"PRODUCTION_OPENAI_API_KEY": "private-openai-key"}
OPENAI_VARS = {
    "TUTOR_PROVIDER": "openai",
    "TUTOR_MODEL": "gpt-4o-2024-11-20",
    "TUTOR_INPUT_COST_PER_MILLION_MICROS_SGD": "3200000",
    "TUTOR_OUTPUT_COST_PER_MILLION_MICROS_SGD": "12800000",
}


def test_defaults_match_the_gemini_only_pilot():
    resolved = script.resolve(GEMINI_KEY, "staging")

    assert resolved.settings == {
        "ASEAN_ACADEMY_TUTOR_ENABLED": "true",
        "ASEAN_ACADEMY_TUTOR_PROVIDER": "gemini",
        "ASEAN_ACADEMY_TUTOR_GEMINI_MODEL": "gemini-3.5-flash-lite",
        "ASEAN_ACADEMY_TUTOR_GEMINI_INPUT_COST_PER_MILLION_MICROS_SGD": "384000",
        "ASEAN_ACADEMY_TUTOR_GEMINI_OUTPUT_COST_PER_MILLION_MICROS_SGD": "3200000",
        "ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_ENABLED": "false",
        "ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_SHADOW_ENABLED": "false",
    }
    assert resolved.key_name == "GEMINI_API_KEY"
    assert resolved.key_source == "STAGING_GEMINI_API_KEY"


def test_openai_switch_uses_its_own_model_prices_and_key():
    resolved = script.resolve({**OPENAI_VARS, **OPENAI_KEY}, "production")

    assert resolved.settings["ASEAN_ACADEMY_TUTOR_PROVIDER"] == "openai"
    assert resolved.settings["ASEAN_ACADEMY_TUTOR_OPENAI_MODEL"] == "gpt-4o-2024-11-20"
    assert (
        resolved.settings["ASEAN_ACADEMY_TUTOR_OPENAI_INPUT_COST_PER_MILLION_MICROS_SGD"]
        == "3200000"
    )
    assert resolved.settings["ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_ENABLED"] == "false"
    assert resolved.key_name == "OPENAI_API_KEY"
    assert resolved.key_source == "PRODUCTION_OPENAI_API_KEY"


def test_key_value_is_never_in_the_written_settings():
    resolved = script.resolve({**OPENAI_VARS, **OPENAI_KEY}, "production")

    assert "private-openai-key" not in "".join(resolved.settings.values())


def test_another_gemini_model_needs_its_prices():
    with pytest.raises(script.TutorDeployError, match="COST_PER_MILLION"):
        script.resolve({**GEMINI_KEY, "TUTOR_MODEL": "gemini-3.8-flash"}, "staging")


@pytest.mark.parametrize(
    ("variables", "message"),
    [
        ({"TUTOR_PROVIDER": "claude"}, "must be gemini or openai"),
        ({"TUTOR_PROVIDER": "openai"}, "Set TUTOR_MODEL"),
        ({**OPENAI_VARS, "PRODUCTION_OPENAI_API_KEY": ""}, "PRODUCTION_OPENAI_API_KEY secret"),
        (
            {**OPENAI_KEY, **OPENAI_VARS, "TUTOR_MODEL": "gemini-3.5-flash-lite"},
            "must name an OpenAI model",
        ),
        (
            {**OPENAI_KEY, **OPENAI_VARS, "TUTOR_INPUT_COST_PER_MILLION_MICROS_SGD": ""},
            "COST_PER_MILLION",
        ),
        (
            {**OPENAI_KEY, **OPENAI_VARS, "TUTOR_OUTPUT_COST_PER_MILLION_MICROS_SGD": "free"},
            "positive whole number",
        ),
    ],
)
def test_wrong_combinations_fail_clearly(variables, message):
    with pytest.raises(script.TutorDeployError, match=message):
        script.resolve(variables, "production")


def test_gemini_with_an_openai_model_fails_clearly():
    variables = {
        **GEMINI_KEY,
        "TUTOR_MODEL": "gpt-4o-2024-11-20",
        "TUTOR_INPUT_COST_PER_MILLION_MICROS_SGD": "1",
        "TUTOR_OUTPUT_COST_PER_MILLION_MICROS_SGD": "1",
    }
    with pytest.raises(script.TutorDeployError, match="must name a Gemini model"):
        script.resolve(variables, "staging")


def test_resolving_restores_the_process_environment(monkeypatch):
    monkeypatch.setenv("UNRELATED_VARIABLE", "kept")

    script.resolve(GEMINI_KEY, "staging")

    assert "ASEAN_ACADEMY_TUTOR_PROVIDER" not in __import__("os").environ
    assert __import__("os").environ["UNRELATED_VARIABLE"] == "kept"
