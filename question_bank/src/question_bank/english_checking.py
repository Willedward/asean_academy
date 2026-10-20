"""Deterministic marking for objective English responses."""

from __future__ import annotations

import re
import unicodedata

from .english_models import (
    EnglishResponse,
    MultipleResponse,
    ShortTextResponse,
    SingleChoiceResponse,
    TextNormalisation,
)


def normalise_text(value: str, rules: TextNormalisation) -> str:
    """Apply only reviewable, non-semantic transformations to an answer."""
    normalised = unicodedata.normalize(rules.unicode_form, value).strip()
    if rules.collapse_whitespace:
        normalised = re.sub(r"\s+", " ", normalised)
    if rules.strip_terminal_punctuation:
        normalised = normalised.rstrip(".!?").rstrip()
    if not rules.case_sensitive:
        normalised = normalised.casefold()
    return normalised


def check_english_answer(
    spec: EnglishResponse, submission: str | list[str]
) -> dict[str, object]:
    """Mark an English response without fuzzy matching or an external model call."""
    if isinstance(spec, SingleChoiceResponse):
        if not isinstance(submission, str) or not submission.strip():
            return {"correct": False, "error": "Select one answer."}
        submitted = submission.strip().upper()
        option_keys = {option.key for option in spec.options}
        if submitted not in option_keys:
            return {"correct": False, "error": "Select one of the available options."}
        return {"correct": submitted == spec.correct_key, "error": None}

    if isinstance(spec, MultipleResponse):
        if not isinstance(submission, list) or not submission:
            return {"correct": False, "error": "Select at least one answer."}
        submitted = [value.strip().upper() for value in submission if value.strip()]
        option_keys = {option.key for option in spec.options}
        if len(submitted) != len(set(submitted)):
            return {"correct": False, "error": "Each option can be selected once."}
        if not set(submitted) <= option_keys:
            return {"correct": False, "error": "Select only available options."}
        return {"correct": set(submitted) == set(spec.correct_keys), "error": None}

    if not isinstance(spec, ShortTextResponse):
        raise TypeError(f"Unsupported English response: {type(spec).__name__}")
    if not isinstance(submission, str) or not submission.strip():
        return {"correct": False, "error": "Enter an answer before checking."}
    submitted = normalise_text(submission, spec.normalisation)
    accepted = {
        normalise_text(value, spec.normalisation)
        for value in [spec.canonical_answer, *spec.accepted_alternatives]
    }
    return {"correct": submitted in accepted, "error": None}
