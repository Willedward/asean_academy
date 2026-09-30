from pathlib import Path
from types import SimpleNamespace

from learning_api.beta_release import (
    REQUIRED_CONFIRMATIONS,
    BetaReleaseRequirements,
    build_evidence,
    evaluate_diagnostics,
    release_metadata_checks,
    source_checks,
)
from learning_api.course_catalogue import CourseCatalogue

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_current_n1_catalogue_is_reported_as_blocked_without_mutating_it():
    catalogue = CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)
    checks, snapshot = source_checks(catalogue, BetaReleaseRequirements())
    by_id = {check.check_id: check for check in checks}

    assert snapshot["topics"] == 1
    assert snapshot["questions"] == 40
    assert len(snapshot["course_content_sha256"]) == 64
    assert not by_id["source.full_syllabus"].passed
    assert not by_id["source.question_volume"].passed
    assert not by_id["source.publication_status"].passed
    assert not by_id["source.lesson_materials"].passed
    assert by_id["source.pool_inventory"].passed
    assert by_id["source.checkpoint_reserve_capacity"].passed


def test_diagnostics_require_disjoint_38_item_forms_and_learning_isolation():
    rows = []
    for purpose, prefix in (("baseline", "b"), ("endline", "e")):
        rows.extend(
            {
                "purpose": purpose,
                "stable_key": f"sec-math-{purpose}",
                "revision": 1,
                "question_id": f"{prefix}-{position}",
            }
            for position in range(38)
        )

    passed = evaluate_diagnostics(rows, set(), BetaReleaseRequirements())
    assert passed.passed
    assert passed.details["distinct_total"] == 76

    rows[-1]["question_id"] = "b-0"
    blocked = evaluate_diagnostics(rows, {"e-1"}, BetaReleaseRequirements())
    assert not blocked.passed
    assert blocked.details["cross_form_overlap_count"] == 1
    assert blocked.details["learning_pool_overlap_count"] == 1


def test_release_metadata_is_exact_phase_bound_and_fail_closed():
    sha = "a" * 40
    checks = release_metadata_checks(
        release_sha=sha,
        current_sha=sha,
        repository_clean=True,
        phase="friendly_users",
        cohort_label="friendly-01",
        cohort_size=5,
        confirmations=set(REQUIRED_CONFIRMATIONS),
    )
    assert all(check.passed for check in checks)

    blocked = release_metadata_checks(
        release_sha="a" * 12,
        current_sha=sha,
        repository_clean=False,
        phase="friendly_users",
        cohort_label="",
        cohort_size=10,
        confirmations={"hosted_google_oauth"},
    )
    assert not any(check.passed for check in blocked)


def test_evidence_lists_every_failed_check():
    checks = [
        SimpleNamespace(
            check_id="one",
            passed=True,
            as_dict=lambda: {"check_id": "one", "passed": True, "summary": "ok", "details": {}},
        ),
        SimpleNamespace(
            check_id="two",
            passed=False,
            as_dict=lambda: {"check_id": "two", "passed": False, "summary": "blocked", "details": {}},
        ),
    ]
    evidence = build_evidence(
        release_sha="a" * 40,
        phase="founder_alpha",
        cohort_label="alpha",
        cohort_size=1,
        attested_by="operator",
        source_snapshot={},
        checks=checks,
        requirements=BetaReleaseRequirements(),
    )

    assert evidence["status"] == "blocked"
    assert evidence["blockers"] == ["two"]


def test_draft_only_review_result_does_not_count_as_complete_approval(monkeypatch):
    import learning_api.beta_release as release

    class Result:
        def fetchall(self):
            return []

    class Connection:
        def execute(self, _query, _parameters):
            return Result()

    catalogue = CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)
    monkeypatch.setattr(release, "check_content", lambda *_args: {"status": "current"})
    monkeypatch.setattr(
        release,
        "verify_release_workflow",
        lambda *_args: {"status": "approved", "checked_items": 0},
    )

    checks = release.database_checks(Connection(), catalogue, BetaReleaseRequirements())
    by_id = {check.check_id: check for check in checks}

    assert not by_id["database.human_approvals"].passed
    assert by_id["database.human_approvals"].details["expected_items"] == 48
