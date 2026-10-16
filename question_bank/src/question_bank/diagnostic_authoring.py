"""Create isolated four-question authoring banks from the diagnostic source plan."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .authoring import (
    DEFAULT_STYLE_REFERENCES,
    BatchAllocation,
    GeneratorMetadata,
    QuestionBatchManifest,
    SourceReference,
    build_blueprint,
    load_manifest,
)
from .catalogue import (
    BankBlueprint,
    BankTopic,
    OutcomeDistribution,
    load_blueprint,
    load_catalogue,
)
from .diagnostic_plan import DiagnosticPlan
from .difficulty import DIFFICULTY_KEYS

DIAGNOSTIC_AUTHORING_CREATED_AT = datetime(2026, 10, 16, tzinfo=UTC)


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reference(repository_root: Path, path: Path, role: str) -> SourceReference:
    relative = path.resolve().relative_to(repository_root.resolve()).as_posix()
    return SourceReference(path=relative, sha256=_checksum(path), role=role)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _slots_by_bank(plan: DiagnosticPlan):
    grouped = defaultdict(list)
    for form in plan.forms:
        for slot in form.items:
            grouped[slot.bank_key].append(slot)
    return dict(grouped)


def _diagnostic_blueprint(catalogue, bank_key: str, slots) -> BankBlueprint:
    first = slots[0]
    topic = catalogue.topic(first.topic_code)
    if topic is None:
        raise ValueError(f"Unknown diagnostic topic {first.topic_code}")
    base = build_blueprint(catalogue, first.school_level, first.topic_code)
    cell_counts = Counter((slot.outcome_code, slot.difficulty) for slot in slots)
    difficulty = Counter(slot.difficulty for slot in slots)
    outcome_by_code = {
        outcome.code: outcome
        for outcome in topic.outcomes
        if outcome.school_level == first.school_level
    }
    used_outcomes = sorted(
        {slot.outcome_code for slot in slots},
        key=lambda code: outcome_by_code[code].position,
    )
    return BankBlueprint(
        bank_id=uuid5(NAMESPACE_URL, f"https://nextscholar.sg/question-banks/{bank_key}"),
        bank_key=bank_key,
        bank_role="diagnostic",
        curriculum_version=catalogue.version_key,
        school_level=first.school_level,
        course="ASEAN Scholarship Mathematics readiness diagnostics",
        topic=BankTopic(code=topic.code, title=topic.title),
        status="draft",
        question_count=4,
        difficulty_distribution={
            level: difficulty[int(level)] for level in DIFFICULTY_KEYS
        },
        outcome_distribution=[
            OutcomeDistribution(
                code=code,
                title=outcome_by_code[code].description,
                difficulty_counts={
                    level: cell_counts[(code, int(level))]
                    for level in DIFFICULTY_KEYS
                },
                total=sum(
                    cell_counts[(code, int(level))] for level in DIFFICULTY_KEYS
                ),
            )
            for code in used_outcomes
        ],
        defaults=base.defaults,
        difficulty_definitions=base.difficulty_definitions,
        style_references=DEFAULT_STYLE_REFERENCES,
        publication_checks=[
            "exactly_4_diagnostic_questions",
            "diagnostic_plan_slots_match",
            "baseline_and_endline_items_are_disjoint",
            "learning_question_reuse_is_forbidden",
            "part_marks_sum_to_question_total",
            "exactly_two_ordered_hints_per_part",
            "canonical_and_accepted_answers_pass_checker",
            "asset_references_exist_and_checksums_match",
            "cross_bank_exact_and_near_duplicate_scan_passes",
            "mathematics_review_complete",
            "editorial_review_complete",
        ],
    )


def _diagnostic_manifest(
    blueprint: BankBlueprint,
    slots,
    references: list[SourceReference],
) -> QuestionBatchManifest:
    counts = Counter((slot.outcome_code, slot.difficulty) for slot in slots)
    prefix = f"g3-sec{blueprint.school_level[-1]}-{blueprint.topic.code.lower()}"
    return QuestionBatchManifest(
        batch_id=f"{prefix}-diagnostic-b001",
        bank_key=blueprint.bank_key,
        bank_role="diagnostic",
        curriculum_version=blueprint.curriculum_version,
        school_level=blueprint.school_level,
        topic_code=blueprint.topic.code,
        status="planned",
        created_at=DIAGNOSTIC_AUTHORING_CREATED_AT,
        generator=GeneratorMetadata(
            provider="unassigned",
            model="unassigned",
            generator_version="unassigned",
            prompt_version="math-diagnostic-question-authoring-v1",
        ),
        source_references=references,
        allocation=[
            BatchAllocation(outcome_code=outcome, difficulty=difficulty, count=count)
            for (outcome, difficulty), count in sorted(counts.items())
        ],
        expected_question_count=4,
        question_keys=[slot.stable_key for slot in slots],
    )


def _blueprint_matches(current: BankBlueprint, expected: BankBlueprint) -> bool:
    ignored = {"status"}
    return current.model_dump(exclude=ignored) == expected.model_dump(exclude=ignored)


def _manifest_matches(current: QuestionBatchManifest, expected: QuestionBatchManifest) -> bool:
    immutable = {
        "schema_version",
        "batch_id",
        "bank_key",
        "bank_role",
        "curriculum_version",
        "school_level",
        "topic_code",
        "source_references",
        "allocation",
        "expected_question_count",
        "question_keys",
    }
    current_payload = current.model_dump(include=immutable, mode="json")
    expected_payload = expected.model_dump(include=immutable, mode="json")
    return current_payload == expected_payload


def plan_diagnostic_authoring_banks(
    plan_path: Path,
    bank_catalogue_root: Path,
    repository_root: Path,
    syllabus_path: Path,
    house_rules_path: Path,
) -> dict:
    """Materialise one four-question v2 bank and manifest per diagnostic topic group."""

    plan = DiagnosticPlan.model_validate_json(plan_path.read_text())
    catalogue = load_catalogue(syllabus_path)
    if plan.curriculum_version != catalogue.version_key:
        raise ValueError(
            f"Diagnostic plan uses {plan.curriculum_version}, not {catalogue.version_key}"
        )
    grouped = _slots_by_bank(plan)
    if len(grouped) != 19 or any(len(slots) != 4 for slots in grouped.values()):
        raise ValueError("The diagnostic plan must allocate four questions to all 19 banks")

    common_references = [
        _reference(repository_root, syllabus_path, "syllabus"),
        _reference(repository_root, house_rules_path, "house_rules"),
        _reference(repository_root, plan_path, "diagnostic_plan"),
    ]
    common_references.extend(
        _reference(repository_root, repository_root / relative, "style")
        for relative in DEFAULT_STYLE_REFERENCES
    )

    created_blueprints: list[str] = []
    preserved_blueprints: list[str] = []
    created_manifests: list[str] = []
    preserved_manifests: list[str] = []
    for bank_key, slots in sorted(grouped.items()):
        expected_blueprint = _diagnostic_blueprint(catalogue, bank_key, slots)
        bank_root = (
            bank_catalogue_root
            / expected_blueprint.school_level
            / expected_blueprint.topic.code.lower()
            / "v2"
        )
        blueprint_path = bank_root / "blueprint.json"
        if blueprint_path.exists():
            current_blueprint = load_blueprint(blueprint_path)
            if not _blueprint_matches(current_blueprint, expected_blueprint):
                raise ValueError(f"Existing diagnostic blueprint drifted: {blueprint_path}")
            preserved_blueprints.append(str(blueprint_path))
        else:
            _write_json(blueprint_path, expected_blueprint.model_dump(mode="json"))
            (bank_root / "questions").mkdir(parents=True, exist_ok=True)
            (bank_root / "questions/.gitkeep").touch()
            created_blueprints.append(str(blueprint_path))

        expected_manifest = _diagnostic_manifest(
            expected_blueprint, slots, common_references
        )
        manifest_path = bank_root / "batches" / f"{expected_manifest.batch_id}.json"
        if manifest_path.exists():
            current_manifest = load_manifest(manifest_path)
            if not _manifest_matches(current_manifest, expected_manifest):
                raise ValueError(f"Existing diagnostic manifest drifted: {manifest_path}")
            preserved_manifests.append(str(manifest_path))
        else:
            _write_json(manifest_path, expected_manifest.model_dump(mode="json"))
            created_manifests.append(str(manifest_path))

    return {
        "plan_key": plan.plan_key,
        "bank_count": len(grouped),
        "question_slots": sum(len(slots) for slots in grouped.values()),
        "created_blueprints": created_blueprints,
        "preserved_blueprints": preserved_blueprints,
        "created_manifests": created_manifests,
        "preserved_manifests": preserved_manifests,
    }
