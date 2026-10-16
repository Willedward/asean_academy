"""Deterministic source contract for full-syllabus Mathematics diagnostics."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .catalogue import SchoolLevel, SyllabusCatalogue, load_catalogue
from .models import BANK_KEY_PATTERN, OUTCOME_PATTERN, QUESTION_KEY_PATTERN, TOPIC_PATTERN, Model
from .validation import Issue

DiagnosticPurpose = Literal["baseline", "endline"]


class DiagnosticSlot(Model):
    position: int = Field(ge=1)
    purpose: DiagnosticPurpose
    stable_key: str = Field(pattern=QUESTION_KEY_PATTERN)
    bank_key: str = Field(pattern=BANK_KEY_PATTERN)
    school_level: SchoolLevel
    topic_code: str = Field(pattern=TOPIC_PATTERN)
    topic_group_key: str = Field(pattern=r"^g3-sec[12]-[ngs][0-9]+$")
    outcome_code: str = Field(pattern=OUTCOME_PATTERN)
    difficulty: int = Field(ge=2, le=4)

    @model_validator(mode="after")
    def identifiers_match(self):
        prefix = f"g3-sec{self.school_level[-1]}-{self.topic_code.lower()}"
        if self.topic_group_key != prefix:
            raise ValueError("topic_group_key must match school_level and topic_code")
        if self.bank_key != f"{prefix}-v2":
            raise ValueError("diagnostic slots must use the reserved v2 bank")
        if not self.stable_key.startswith(f"{self.topic_code.lower()}-l{self.difficulty}-"):
            raise ValueError("stable_key must match topic_code and difficulty")
        return self


class DiagnosticFormPlan(Model):
    stable_key: str = Field(pattern=r"^g3-sec1-2-math-(baseline|endline)-v[0-9]+$")
    revision: int = Field(ge=1)
    purpose: DiagnosticPurpose
    title: str = Field(min_length=1)
    estimated_minutes: int = Field(ge=1, le=180)
    band_policy_version: str = Field(pattern=r"^[a-z0-9-]+$")
    items: list[DiagnosticSlot] = Field(min_length=38, max_length=38)

    @model_validator(mode="after")
    def positions_and_purpose_match(self):
        if [item.position for item in self.items] != list(range(1, 39)):
            raise ValueError("diagnostic item positions must be consecutive from 1 to 38")
        if any(item.purpose != self.purpose for item in self.items):
            raise ValueError("every diagnostic slot must match the form purpose")
        return self


class DiagnosticPlan(Model):
    schema_version: Literal["1.0.0"] = "1.0.0"
    plan_key: Literal["g3-sec1-2-math-readiness-v1"]
    curriculum_version: str = Field(pattern=r"^[a-z0-9_]+$")
    status: Literal["draft", "reviewed", "published"] = "draft"
    dedicated_questions_required: Literal[76] = 76
    learning_question_reuse_allowed: Literal[False] = False
    forms: list[DiagnosticFormPlan] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def forms_are_matched_and_disjoint(self):
        by_purpose = {form.purpose: form for form in self.forms}
        if set(by_purpose) != {"baseline", "endline"}:
            raise ValueError("the plan requires one baseline and one endline form")
        baseline = by_purpose["baseline"]
        endline = by_purpose["endline"]
        baseline_keys = {item.stable_key for item in baseline.items}
        endline_keys = {item.stable_key for item in endline.items}
        if len(baseline_keys) != 38 or len(endline_keys) != 38:
            raise ValueError("question keys must be unique within each diagnostic form")
        if baseline_keys & endline_keys:
            raise ValueError("baseline and endline question keys must be disjoint")
        for form in self.forms:
            groups = Counter(item.topic_group_key for item in form.items)
            if len(groups) != 19 or set(groups.values()) != {2}:
                raise ValueError("each form requires exactly two items for all 19 topic groups")
        baseline_difficulty = {
            item.topic_group_key: sorted(
                slot.difficulty
                for slot in baseline.items
                if slot.topic_group_key == item.topic_group_key
            )
            for item in baseline.items
        }
        endline_difficulty = {
            item.topic_group_key: sorted(
                slot.difficulty
                for slot in endline.items
                if slot.topic_group_key == item.topic_group_key
            )
            for item in endline.items
        }
        if baseline_difficulty != endline_difficulty:
            raise ValueError("baseline and endline difficulty must match by topic group")
        return self


def _topic_groups(catalogue: SyllabusCatalogue):
    groups = []
    for topic in catalogue.topics:
        for school_level in ("secondary_1", "secondary_2"):
            outcomes = sorted(
                (item for item in topic.outcomes if item.school_level == school_level),
                key=lambda item: item.position,
            )
            if outcomes:
                groups.append((school_level, topic.code, outcomes))
    return groups


def build_diagnostic_plan(catalogue: SyllabusCatalogue) -> DiagnosticPlan:
    groups = _topic_groups(catalogue)
    if len(groups) != 19:
        raise ValueError(f"Expected 19 level-specific topic groups, found {len(groups)}")
    forms = []
    for purpose, offset in (("baseline", 901), ("endline", 903)):
        slots = []
        position = 1
        for index, (school_level, topic_code, outcomes) in enumerate(groups):
            difficulties = (2 if index % 2 == 0 else 3, 4 if index % 3 == 0 else 3)
            outcome_offset = 0 if purpose == "baseline" else 2
            for local_index, difficulty in enumerate(difficulties):
                outcome = outcomes[(outcome_offset + local_index) % len(outcomes)]
                prefix = f"g3-sec{school_level[-1]}-{topic_code.lower()}"
                key_number = offset + local_index + (50 if school_level == "secondary_2" else 0)
                slots.append(
                    DiagnosticSlot(
                        position=position,
                        purpose=purpose,
                        stable_key=f"{topic_code.lower()}-l{difficulty}-{key_number}",
                        bank_key=f"{prefix}-v2",
                        school_level=school_level,
                        topic_code=topic_code,
                        topic_group_key=prefix,
                        outcome_code=outcome.code,
                        difficulty=difficulty,
                    )
                )
                position += 1
        forms.append(
            DiagnosticFormPlan(
                stable_key=f"g3-sec1-2-math-{purpose}-v1",
                revision=1,
                purpose=purpose,
                title=(
                    "ASEAN Scholarship Mathematics starting readiness check"
                    if purpose == "baseline"
                    else "ASEAN Scholarship Mathematics progress readiness check"
                ),
                estimated_minutes=60,
                band_policy_version="asean-scholarship-math-readiness-v1",
                items=slots,
            )
        )
    return DiagnosticPlan(
        plan_key="g3-sec1-2-math-readiness-v1",
        curriculum_version=catalogue.version_key,
        forms=forms,
    )


def validate_diagnostic_plan(
    plan_path: Path, syllabus_path: Path
) -> tuple[DiagnosticPlan | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        plan = DiagnosticPlan.model_validate_json(plan_path.read_text())
        catalogue = load_catalogue(syllabus_path)
    except (OSError, ValueError) as exc:
        return None, [Issue("error", "invalid_diagnostic_plan", str(plan_path), str(exc))]
    valid_groups = {
        (school_level, topic_code): {outcome.code for outcome in outcomes}
        for school_level, topic_code, outcomes in _topic_groups(catalogue)
    }
    for form in plan.forms:
        for item in form.items:
            outcomes = valid_groups.get((item.school_level, item.topic_code))
            if outcomes is None:
                issues.append(
                    Issue("error", "unknown_diagnostic_topic_group", item.stable_key, item.topic_group_key)
                )
            elif item.outcome_code not in outcomes:
                issues.append(
                    Issue("error", "unknown_diagnostic_outcome", item.stable_key, item.outcome_code)
                )
    return plan, issues


def write_diagnostic_plan(syllabus_path: Path, output: Path) -> DiagnosticPlan:
    plan = build_diagnostic_plan(load_catalogue(syllabus_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan.model_dump(mode="json"), indent=2) + "\n")
    return plan
