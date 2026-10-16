"""Deterministic work orders for provider-independent question generation."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .authoring import HouseRules, load_manifest, validate_batch
from .catalogue import load_catalogue
from .collaboration import load_claim_registry
from .diagnostic_plan import DiagnosticPlan
from .difficulty import DIFFICULTY_DEFINITIONS
from .models import Question

WORK_ORDER_SCHEMA_VERSION = "1.0.0"


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _diagnostic_usage(manifest, repository_root: Path) -> dict[str, dict]:
    if manifest.bank_role != "diagnostic":
        return {}
    references = [
        reference
        for reference in manifest.source_references
        if reference.role == "diagnostic_plan"
    ]
    if len(references) != 1:
        raise ValueError("A diagnostic work order requires one diagnostic_plan reference")
    plan = DiagnosticPlan.model_validate_json(
        (repository_root / references[0].path).read_text()
    )
    return {
        slot.stable_key: {
            "purpose": form.purpose,
            "form_key": form.stable_key,
            "form_position": slot.position,
            "primary_outcome": slot.outcome_code,
            "difficulty": slot.difficulty,
        }
        for form in plan.forms
        for slot in form.items
        if slot.bank_key == manifest.bank_key
    }


def _question_slots(
    manifest, outcomes_by_code: dict[str, str], diagnostic_usage: dict[str, dict]
) -> list[dict]:
    if diagnostic_usage:
        return [
            {
                "stable_key": key,
                "primary_outcome": diagnostic_usage[key]["primary_outcome"],
                "outcome_description": outcomes_by_code[
                    diagnostic_usage[key]["primary_outcome"]
                ],
                "difficulty": diagnostic_usage[key]["difficulty"],
                "difficulty_definition": DIFFICULTY_DEFINITIONS[
                    str(diagnostic_usage[key]["difficulty"])
                ],
                "diagnostic_usage": {
                    field: value
                    for field, value in diagnostic_usage[key].items()
                    if field not in {"primary_outcome", "difficulty"}
                },
            }
            for key in manifest.question_keys
        ]

    keys_by_difficulty: dict[int, list[str]] = defaultdict(list)
    for key in manifest.question_keys:
        keys_by_difficulty[int(key.split("-l", 1)[1].split("-", 1)[0])].append(key)

    slots = []
    for difficulty in sorted(keys_by_difficulty):
        outcomes = []
        for allocation in manifest.allocation:
            if allocation.difficulty == difficulty:
                outcomes.extend([allocation.outcome_code] * allocation.count)
        keys = keys_by_difficulty[difficulty]
        if len(keys) != len(outcomes):
            raise ValueError(
                f"Difficulty {difficulty} reserves {len(keys)} keys but allocates "
                f"{len(outcomes)} questions"
            )
        for key, outcome in zip(keys, outcomes, strict=True):
            slot = {
                "stable_key": key,
                "primary_outcome": outcome,
                "outcome_description": outcomes_by_code[outcome],
                "difficulty": difficulty,
                "difficulty_definition": DIFFICULTY_DEFINITIONS[str(difficulty)],
            }
            slots.append(slot)
    return slots


def create_authoring_work_order(
    manifest_path: Path,
    output: Path,
    *,
    repository_root: Path,
    syllabus_path: Path,
    house_rules_path: Path | None = None,
) -> dict:
    """Package one planned batch into exact model input and a human-readable prompt."""

    report = validate_batch(
        manifest_path,
        repository_root=repository_root,
        syllabus_path=syllabus_path,
    )
    if not report.valid or report.manifest is None:
        raise ValueError(json.dumps(report.as_dict(), indent=2))
    manifest = report.manifest
    if manifest.status != "planned":
        raise ValueError("Work orders can only be created for planned batches")

    catalogue = load_catalogue(syllabus_path)
    topic = catalogue.topic(manifest.topic_code)
    if topic is None:
        raise ValueError(f"Unknown topic {manifest.topic_code}")
    outcomes_by_code = {
        outcome.code: outcome.description
        for outcome in topic.outcomes
        if outcome.school_level == manifest.school_level
    }
    house_rules_reference = next(
        (
            reference
            for reference in manifest.source_references
            if reference.role == "house_rules"
        ),
        None,
    )
    if house_rules_reference is None:
        raise ValueError("Manifest has no checksum-tracked house-rules reference")
    referenced_house_rules = repository_root / house_rules_reference.path
    if house_rules_path is not None and (
        house_rules_path.resolve() != referenced_house_rules.resolve()
    ):
        raise ValueError(
            f"Manifest references {house_rules_reference.path}, not {house_rules_path}"
        )
    house_rules_path = referenced_house_rules
    actual_checksum = hashlib.sha256(house_rules_path.read_bytes()).hexdigest()
    if actual_checksum != house_rules_reference.sha256:
        raise ValueError("House-rules checksum no longer matches the batch manifest")
    house_rules = HouseRules.model_validate_json(house_rules_path.read_text())
    diagnostic_usage = _diagnostic_usage(manifest, repository_root)
    slots = _question_slots(manifest, outcomes_by_code, diagnostic_usage)

    output.mkdir(parents=True, exist_ok=True)
    work_order = {
        "schema_version": WORK_ORDER_SCHEMA_VERSION,
        "batch_id": manifest.batch_id,
        "manifest_path": str(manifest_path.resolve().relative_to(repository_root.resolve())),
        "bank_key": manifest.bank_key,
        "bank_role": manifest.bank_role,
        "curriculum_version": manifest.curriculum_version,
        "school_level": manifest.school_level,
        "topic": {"code": topic.code, "title": topic.title},
        "expected_question_count": manifest.expected_question_count,
        "prompt_version": manifest.generator.prompt_version,
        "house_rules": house_rules.model_dump(mode="json"),
        "source_references": [
            reference.model_dump(mode="json") for reference in manifest.source_references
        ],
        "slots": slots,
        "generation_contract": {
            "response_file": "questions.json",
            "response_shape": (
                "A JSON object with a questions array containing one complete Question "
                "object per slot."
            ),
            "stable_keys_must_match": True,
            "slot_outcome_and_difficulty_must_match": True,
            "original_wording_required": True,
            "hints_per_part": 2,
            "answers_must_pass_deterministic_checker": True,
            "human_review_required": ["mathematics", "editorial"],
            "learning_question_reuse_allowed": manifest.bank_role != "diagnostic",
        },
        "question_json_schema": Question.model_json_schema(),
    }
    _write_json(output / "work-order.json", work_order)
    _write_json(output / "response-template.json", {"questions": slots})

    allocation_lines = "\n".join(
        f"- `{slot['stable_key']}`: outcome {slot['primary_outcome']}, "
        f"difficulty {slot['difficulty']} — {slot['difficulty_definition']}"
        for slot in slots
    )
    content_kind = "diagnostic" if manifest.bank_role == "diagnostic" else "learning"
    diagnostic_instruction = (
        "Baseline and endline items must assess the assigned skill at comparable difficulty "
        "while using distinct wording, values and solution paths. Do not reuse any learning "
        "question. Author both hints and the complete worked solution even though diagnostic "
        "learners will not see help during the assessment."
        if manifest.bank_role == "diagnostic"
        else ""
    )
    prompt = f"""# Question authoring work order: {manifest.batch_id}

Create exactly {manifest.expected_question_count} original Singapore Secondary Mathematics
{content_kind} questions for **{topic.code} · {topic.title}**. Read `work-order.json` as the authoritative
contract and return only one JSON object with a `questions` array of complete Question
objects that validate against `question_json_schema`.

{diagnostic_instruction}

Every question must use its reserved key, outcome and difficulty below. Include complete
stems, parts, deterministic response contracts, two staged hints per part, fully marked
solutions, calculator permission, provenance and any referenced asset metadata. Use
Singapore/British English, metric units and SGD where money is needed. Do not copy wording
from source papers. Do not mark content reviewed or published. Set `assets` to an empty
array unless matching checksum-tracked asset files have already been prepared in the bank.

## Reserved slots

{allocation_lines}

## Completion gate

The batch is complete only after schema validation, executable answer checks, allocation
checks, source and asset checks, the cross-bank duplicate scan, reviewer-packet export,
and separate Mathematics and editorial review. Generation never grants approval.
"""
    (output / "prompt.md").write_text(prompt)
    return {
        "batch_id": manifest.batch_id,
        "question_count": len(slots),
        "output": str(output),
        "files": ["prompt.md", "response-template.json", "work-order.json"],
    }


def next_authoring_batch(
    bank_root: Path,
    claims_path: Path,
    *,
    owner: str,
    syllabus_path: Path,
    school_level: str | None = None,
    topic_code: str | None = None,
    bank_role: str | None = None,
) -> dict:
    """Return the next unclaimed planned batch and exact claim/branch instructions."""

    registry = load_claim_registry(claims_path)
    active = {claim.batch_id for claim in registry.claims if claim.released_at is None}
    catalogue = load_catalogue(syllabus_path)
    topic_position = {topic.code: topic.position for topic in catalogue.topics}
    planned = []
    for path in sorted(bank_root.glob("**/batches/*.json")):
        manifest = load_manifest(path)
        if school_level is not None and manifest.school_level != school_level:
            continue
        if topic_code is not None and manifest.topic_code != topic_code.upper():
            continue
        if bank_role is not None and manifest.bank_role != bank_role:
            continue
        if manifest.status == "planned" and manifest.batch_id not in active:
            planned.append((path, manifest))
    planned.sort(
        key=lambda item: (
            int(item[1].school_level.rsplit("_", 1)[1]),
            topic_position[item[1].topic_code],
            item[1].batch_id,
        )
    )
    if not planned:
        return {"status": "complete", "remaining_unclaimed_planned_batches": 0}

    path, manifest = planned[0]
    safe_owner = owner.strip().lower().replace(" ", "-")
    if not safe_owner:
        raise ValueError("owner must not be empty")
    branch = f"questions/{manifest.batch_id}-{safe_owner}"
    return {
        "status": "ready",
        "remaining_unclaimed_planned_batches": len(planned),
        "batch_id": manifest.batch_id,
        "bank_role": manifest.bank_role,
        "manifest": str(path),
        "branch": branch,
        "claim_command": (
            "uv run --project question_bank question-bank authoring-claim "
            f"{manifest.batch_id} --owner {owner} --branch {branch}"
        ),
        "work_order_command": (
            "uv run --project question_bank question-bank authoring-work-order "
            f"{path} build/authoring-work-orders/{manifest.batch_id}"
        ),
    }
