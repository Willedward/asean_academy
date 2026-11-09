import json
from datetime import UTC, datetime

from question_bank.review_readiness import (
    BatchReadiness,
    ReadinessFinding,
    ReviewReadinessReport,
    _open_content_findings,
    audit_review_readiness,
    readiness_markdown,
    write_readiness_report,
)


def test_repository_readiness_audit_is_report_only_and_evidence_backed(
    repository_root, tmp_path
):
    report = audit_review_readiness(
        repository_root / "backend_resources/question_bank/g3_math",
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        repository_root / "backend_resources/question_bank/authoring/batch-claims-v1.json",
        repository_root=repository_root,
        worklist_path=repository_root / "docs/plan/CONTENT_FIX_LEDGER.json",
        now=datetime(2026, 11, 6, tzinfo=UTC),
    )

    assert report.valid
    assert len(report.batches) == 75
    assert all("diagnostic" not in batch.batch_id for batch in report.batches)

    by_id = {batch.batch_id: batch for batch in report.batches}
    assert all(batch.packet_status == "current" for batch in report.batches)
    completed_chart_batch = by_id["g3-sec2-n6-b001"]
    assert completed_chart_batch.packet_status == "current"
    assert completed_chart_batch.state == "ready"
    assert completed_chart_batch.active_claim is None

    unresolved_s2_batch = by_id["g3-sec2-s2-b003"]
    assert unresolved_s2_batch.packet_status == "current"
    assert unresolved_s2_batch.state == "blocked"
    assert unresolved_s2_batch.active_claim is None
    assert "open_content_finding" in {
        finding.code for finding in unresolved_s2_batch.blockers
    }

    unfinished_chart_batch = by_id["g3-sec1-g1-b003"]
    assert unfinished_chart_batch.packet_status == "current"
    assert unfinished_chart_batch.state == "blocked"
    assert unfinished_chart_batch.active_claim is None
    assert unfinished_chart_batch.pending_asset_keys == ["g1-l4-011"]
    assert "planned_assets_missing" in {
        finding.code for finding in unfinished_chart_batch.blockers
    }

    unresolved_checker_batch = by_id["g3-sec1-n1-b001"]
    open_messages = [
        finding.message
        for finding in unresolved_checker_batch.blockers
        if finding.code == "open_content_finding"
    ]
    assert any(message.startswith("CFL-177 (category 3, open)") for message in open_messages)
    assert any(
        message.startswith("CFL-181 (category 3, open)") for message in open_messages
    )

    codename_batch = by_id["g3-sec2-n7-b004"]
    codename_blocker = next(
        finding
        for finding in codename_batch.blockers
        if finding.code == "learner_visible_codename"
    )
    assert "n7-l1-517" in codename_blocker.message

    write_readiness_report(report, tmp_path)
    payload = json.loads((tmp_path / "report.json").read_text())
    assert payload["ready_count"] == len(report.ready_batches)
    assert payload["pending_asset_count"] == sum(
        len(batch.pending_asset_keys) for batch in report.batches
    )
    assert "records no Mathematics or editorial approval" in (
        tmp_path / "summary.md"
    ).read_text()


def test_readiness_markdown_separates_ready_and_blocked_batches():
    report = ReviewReadinessReport(
        generated_at="2026-11-06T00:00:00+00:00",
        batches=[
            BatchReadiness(
                batch_id="g3-sec1-n1-b001",
                bank_key="g3-sec1-n1-v1",
                school_level="secondary_1",
                topic_code="N1",
                manifest_status="ready_for_review",
                question_count=21,
                packet_status="current",
                state="ready",
            ),
            BatchReadiness(
                batch_id="g3-sec2-n6-b001",
                bank_key="g3-sec2-n6-v1",
                school_level="secondary_2",
                topic_code="N6",
                manifest_status="ready_for_review",
                question_count=26,
                packet_status="stale",
                state="blocked",
                blockers=[
                    ReadinessFinding(
                        "stale_packet_questions",
                        "questions.json",
                        "Packet questions no longer match source.",
                    )
                ],
            ),
        ],
    )

    page = readiness_markdown(report)

    assert "Ready for assignment: 1" in page
    assert "`g3-sec1-n1-b001`" in page
    assert "`g3-sec2-n6-b001` | blocked | stale" in page
    assert "approval" in page


def test_open_content_findings_use_explicit_unresolved_statuses(tmp_path):
    worklist = tmp_path / "worklist.json"
    worklist.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "id": "CFL-001",
                        "category_rank": 1,
                        "status": "confirmed",
                        "batches": ["g3-sec1-n1-b001"],
                    },
                    {
                        "id": "CFL-002",
                        "category_rank": 2,
                        "status": "open",
                        "batches": ["g3-sec1-n1-b001"],
                    },
                    {
                        "id": "CFL-003",
                        "category_rank": 3,
                        "status": "needs_checker_config",
                        "batches": ["g3-sec1-n1-b002"],
                    },
                    {
                        "id": "CFL-004",
                        "category_rank": 4,
                        "status": "open",
                        "batches": ["g3-sec1-n1-b003"],
                    },
                ]
            }
        )
    )

    findings = _open_content_findings(worklist)

    assert [item["id"] for item in findings["g3-sec1-n1-b001"]] == ["CFL-002"]
    assert [item["id"] for item in findings["g3-sec1-n1-b002"]] == ["CFL-003"]
    assert "g3-sec1-n1-b003" not in findings
