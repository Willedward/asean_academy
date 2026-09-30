"""Fail-closed Beta release evidence for the controlled B5 pilot."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from question_bank.course_repository import course_content_hash

from .content_review import verify_release_workflow
from .content_sync import check_content


@dataclass(frozen=True, slots=True)
class BetaReleaseRequirements:
    minimum_topics: int = 19
    minimum_questions: int = 1_900
    diagnostic_items_per_form: int = 38
    minimum_diagnostic_items: int = 76


@dataclass(frozen=True, slots=True)
class ReleaseCheck:
    check_id: str
    passed: bool
    summary: str
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


PHASE_LIMITS = {
    "founder_alpha": (1, 2),
    "friendly_users": (3, 5),
    "beta_cohort": (10, 30),
}

REQUIRED_CONFIRMATIONS = (
    "deployed_release_smoke",
    "hosted_google_oauth",
    "authenticated_e2e",
    "restore_drill",
    "rate_limit_and_load",
    "accessibility",
    "incident_and_data_owners",
    "schema_content_freeze",
    "founder_release_signoff",
)


def _check(
    check_id: str,
    passed: bool,
    success: str,
    failure: str,
    **details: Any,
) -> ReleaseCheck:
    return ReleaseCheck(check_id, passed, success if passed else failure, details)


def source_checks(catalogue, requirements: BetaReleaseRequirements) -> tuple[list[ReleaseCheck], dict]:
    """Inspect the validated Git catalogue without requiring PostgreSQL."""
    report = catalogue.report
    course = report.course
    questions = catalogue.questions
    units = course.units
    lessons = report.lessons
    pools = report.pools.pools

    topic_codes = sorted({unit.topic_code for unit in units})
    published_questions = sum(question.status == "published" for question in questions)
    published_lessons = sum(lesson.status == "published" for lesson in lessons)
    populated_lessons = sum(bool(lesson.sections) for lesson in lessons)
    section_types = {
        lesson.stable_key: sorted({section.type for section in lesson.sections})
        for lesson in lessons
    }
    pool_keys: dict[str, set[str]] = {
        "lesson_practice": set(),
        "unit_checkpoint": set(),
        "adaptive_reserve": set(),
    }
    duplicate_allocations: set[str] = set()
    allocated: set[str] = set()
    for pool in pools:
        keys = {item.question_key for item in pool.items}
        duplicate_allocations.update(allocated.intersection(keys))
        allocated.update(keys)
        pool_keys[pool.type].update(keys)

    allocation_counts = {kind: len(keys) for kind, keys in pool_keys.items()}
    lesson_material_types_ready = all(
        {"explanation", "worked_example", "active_recall", "summary"}.issubset(types)
        for types in section_types.values()
    )
    all_source_published = (
        course.status == "published"
        and published_lessons == len(lessons)
        and published_questions == len(questions)
    )
    pool_inventory_ok = (
        not duplicate_allocations
        and allocated == {question.stable_key for question in questions}
    )
    capacity_ok = bool(pool_keys["unit_checkpoint"] and pool_keys["adaptive_reserve"])

    checks = [
        _check(
            "source.full_syllabus",
            len(topic_codes) >= requirements.minimum_topics,
            "The authored catalogue covers the required Mathematics topic groups.",
            "The authored catalogue does not yet cover all required Mathematics topic groups.",
            actual=len(topic_codes),
            required=requirements.minimum_topics,
            topic_codes=topic_codes,
        ),
        _check(
            "source.question_volume",
            len(questions) >= requirements.minimum_questions,
            "The reviewed question inventory meets the Beta volume floor.",
            "The question inventory is below the Beta volume floor.",
            actual=len(questions),
            required=requirements.minimum_questions,
        ),
        _check(
            "source.publication_status",
            all_source_published,
            "The course, lessons and questions are published revisions.",
            "One or more course, lesson or question revisions remain unpublished.",
            course_status=course.status,
            published_lessons=published_lessons,
            lesson_count=len(lessons),
            published_questions=published_questions,
            question_count=len(questions),
        ),
        _check(
            "source.lesson_materials",
            populated_lessons == len(lessons) and lesson_material_types_ready,
            "Every lesson has explanation, example, active-recall and summary material.",
            "One or more lessons lack the required reviewed learning-note sections.",
            populated_lessons=populated_lessons,
            lesson_count=len(lessons),
            required_section_types=[
                "explanation",
                "worked_example",
                "active_recall",
                "summary",
            ],
        ),
        _check(
            "source.pool_inventory",
            pool_inventory_ok,
            "Practice, checkpoint and reserve allocations are mutually exclusive and complete.",
            "Question pool allocations overlap or omit authored questions.",
            allocation_counts=allocation_counts,
            duplicate_question_keys=sorted(duplicate_allocations),
            unallocated_question_keys=sorted(
                {question.stable_key for question in questions} - allocated
            ),
        ),
        _check(
            "source.checkpoint_reserve_capacity",
            capacity_ok,
            "Checkpoint and adaptive-reserve capacity is present.",
            "Checkpoint or adaptive-reserve capacity is missing.",
            checkpoint_questions=allocation_counts["unit_checkpoint"],
            adaptive_reserve_questions=allocation_counts["adaptive_reserve"],
        ),
    ]
    snapshot = {
        "course_key": course.stable_key,
        "course_revision": course.revision,
        "course_content_sha256": course_content_hash(course, lessons, report.pools),
        "course_status": course.status,
        "topics": len(topic_codes),
        "lessons": len(lessons),
        "questions": len(questions),
        "allocation_counts": allocation_counts,
    }
    return checks, snapshot


def evaluate_diagnostics(
    rows: Iterable[dict[str, Any]],
    allocated_question_ids: set[str],
    requirements: BetaReleaseRequirements,
) -> ReleaseCheck:
    """Require two current, disjoint, published 38-item diagnostic forms."""
    by_purpose: dict[str, set[str]] = {"baseline": set(), "endline": set()}
    form_keys: dict[str, set[str]] = {"baseline": set(), "endline": set()}
    for row in rows:
        purpose = str(row["purpose"])
        if purpose not in by_purpose:
            continue
        by_purpose[purpose].add(str(row["question_id"]))
        form_keys[purpose].add(f"{row['stable_key']}:r{row['revision']}")

    baseline = by_purpose["baseline"]
    endline = by_purpose["endline"]
    union = baseline | endline
    cross_form_overlap = baseline & endline
    learning_overlap = union & allocated_question_ids
    form_counts = {purpose: len(keys) for purpose, keys in by_purpose.items()}
    passed = (
        all(len(keys) == 1 for keys in form_keys.values())
        and all(
            count == requirements.diagnostic_items_per_form
            for count in form_counts.values()
        )
        and len(union) >= requirements.minimum_diagnostic_items
        and not cross_form_overlap
        and not learning_overlap
    )
    return _check(
        "database.diagnostic_inventory",
        passed,
        "Baseline and endline forms are published, matched and isolated from learning pools.",
        "Published diagnostic forms are missing, undersized, overlapping or reuse learning questions.",
        forms={purpose: sorted(keys) for purpose, keys in form_keys.items()},
        item_counts=form_counts,
        required_per_form=requirements.diagnostic_items_per_form,
        required_total=requirements.minimum_diagnostic_items,
        distinct_total=len(union),
        cross_form_overlap_count=len(cross_form_overlap),
        learning_pool_overlap_count=len(learning_overlap),
    )


def database_checks(connection, catalogue, requirements: BetaReleaseRequirements) -> list[ReleaseCheck]:
    """Verify imported hashes, review decisions and production diagnostic isolation."""
    checks: list[ReleaseCheck] = []
    try:
        sync = check_content(connection, catalogue)
    except Exception as exc:  # converted to evidence; the CLI still fails closed
        checks.append(
            _check(
                "database.content_hashes",
                False,
                "Imported content matches Git-authored revisions.",
                "Imported content does not match the Git-authored release candidate.",
                error=str(exc),
            )
        )
    else:
        checks.append(
            _check(
                "database.content_hashes",
                True,
                "Imported content matches Git-authored revisions.",
                "Imported content does not match the Git-authored release candidate.",
                **sync,
            )
        )

    try:
        approvals = verify_release_workflow(connection, catalogue)
    except Exception as exc:  # content workflow errors are safe release blockers
        checks.append(
            _check(
                "database.human_approvals",
                False,
                "Every student-visible revision has its required human approvals.",
                "The content review and publication workflow is incomplete.",
                error=str(exc),
            )
        )
    else:
        expected_items = 1 + len(catalogue.report.lessons) + len(catalogue.questions)
        approvals_complete = approvals["checked_items"] == expected_items
        checks.append(
            _check(
                "database.human_approvals",
                approvals_complete,
                "Every student-visible revision has its required human approvals.",
                "The content review and publication workflow is incomplete.",
                expected_items=expected_items,
                **approvals,
            )
        )

    report = catalogue.report
    course = report.course
    diagnostic_rows = connection.execute(
        """
        select forms.purpose::text as purpose, forms.stable_key, forms.revision,
               question_versions.question_id
        from diagnostic_forms forms
        join course_versions versions on versions.id = forms.course_version_id
        join courses on courses.id = versions.course_id
        join diagnostic_form_items items on items.form_id = forms.id
        join math_question_versions question_versions
          on question_versions.id = items.question_version_id
        where courses.course_key = %s
          and versions.revision = %s
          and forms.status = 'published'
          and forms.is_current
        order by forms.purpose, items.position
        """,
        (course.stable_key, course.revision),
    ).fetchall()
    allocated_rows = connection.execute(
        """
        select items.question_id
        from lesson_question_pool_items items
        join lesson_question_pools pools on pools.id = items.pool_id
        join unit_versions units on units.id = pools.unit_version_id
        join course_versions versions on versions.id = units.course_version_id
        join courses on courses.id = versions.course_id
        where courses.course_key = %s and versions.revision = %s
        union
        select items.question_id
        from unit_checkpoint_pool_items items
        join unit_checkpoint_pools pools on pools.id = items.pool_id
        join unit_versions units on units.id = pools.unit_version_id
        join course_versions versions on versions.id = units.course_version_id
        join courses on courses.id = versions.course_id
        where courses.course_key = %s and versions.revision = %s
        """,
        (course.stable_key, course.revision, course.stable_key, course.revision),
    ).fetchall()
    allocated_ids = {
        str(row["question_id"])
        for row in allocated_rows
        if row["question_id"] is not None
    }
    checks.append(evaluate_diagnostics(diagnostic_rows, allocated_ids, requirements))
    return checks


def release_metadata_checks(
    *,
    release_sha: str,
    current_sha: str,
    repository_clean: bool,
    phase: str,
    cohort_label: str,
    cohort_size: int,
    confirmations: set[str],
) -> list[ReleaseCheck]:
    minimum, maximum = PHASE_LIMITS[phase]
    exact_sha = len(release_sha) == 40 and release_sha == current_sha
    missing_confirmations = sorted(set(REQUIRED_CONFIRMATIONS) - confirmations)
    return [
        _check(
            "release.exact_sha",
            exact_sha,
            "The candidate is bound to the exact checked-out Git commit.",
            "The release SHA is not the exact checked-out 40-character commit.",
            release_sha=release_sha,
            current_sha=current_sha,
        ),
        _check(
            "release.clean_tree",
            repository_clean,
            "The release candidate has no uncommitted source changes.",
            "The working tree contains changes that are absent from the release SHA.",
        ),
        _check(
            "release.cohort",
            minimum <= cohort_size <= maximum and bool(cohort_label.strip()),
            "The named cohort follows the controlled rollout size for this phase.",
            "The cohort label is empty or its size is outside the controlled rollout range.",
            phase=phase,
            cohort_label=cohort_label.strip(),
            cohort_size=cohort_size,
            allowed_size=[minimum, maximum],
        ),
        _check(
            "release.operator_confirmations",
            not missing_confirmations,
            "All hosted and human release confirmations were recorded.",
            "One or more hosted or human release confirmations are missing.",
            required=list(REQUIRED_CONFIRMATIONS),
            missing=missing_confirmations,
        ),
    ]


def build_evidence(
    *,
    release_sha: str,
    phase: str,
    cohort_label: str,
    cohort_size: int,
    attested_by: str,
    source_snapshot: dict[str, Any],
    checks: list[ReleaseCheck],
    requirements: BetaReleaseRequirements,
) -> dict[str, Any]:
    blockers = [check.check_id for check in checks if not check.passed]
    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "ready" if not blockers else "blocked",
        "release_sha": release_sha,
        "phase": phase,
        "cohort": {"label": cohort_label.strip(), "planned_size": cohort_size},
        "attested_by": attested_by.strip() or None,
        "requirements": asdict(requirements),
        "content_snapshot": source_snapshot,
        "checks": [check.as_dict() for check in checks],
        "blockers": blockers,
    }


def evidence_markdown(evidence: dict[str, Any]) -> str:
    marker = "READY" if evidence["status"] == "ready" else "BLOCKED"
    lines = [
        "# Beta release evidence",
        "",
        f"**Status:** {marker}",
        f"**Release SHA:** `{evidence['release_sha']}`",
        f"**Phase:** `{evidence['phase']}`",
        f"**Cohort:** {evidence['cohort']['label']} ({evidence['cohort']['planned_size']})",
        f"**Generated:** {evidence['generated_at']}",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    for check in evidence["checks"]:
        result = "PASS" if check["passed"] else "BLOCK"
        summary = str(check["summary"]).replace("|", "\\|")
        lines.append(f"| `{check['check_id']}` | {result} | {summary} |")
    if evidence["blockers"]:
        lines.extend(["", "## Blocking checks", ""])
        lines.extend(f"- `{blocker}`" for blocker in evidence["blockers"])
    lines.extend(
        [
            "",
            "This artifact contains no invitation codes, access tokens, student emails or answers.",
            "",
        ]
    )
    return "\n".join(lines)
