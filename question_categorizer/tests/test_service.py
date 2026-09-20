import json
from uuid import uuid4

from conftest import question

from question_categorizer.service import CategorizationService


def test_service_splits_parts_and_classifies_each(export_factory):
    multipart = question(
        7,
        "",
        content=[
            {
                "type": "text",
                "text": (
                    "(i) A developer needs 96 men to build a house in 14 days. "
                    "How many men are needed in 12 days? "
                    "(ii) If y is inversely proportional to x, find the percentage decrease."
                ),
                "latex": None,
                "rows": [],
            }
        ],
    )
    circle = question(5, "O is the centre of a circle. Use a circle theorem to find angle ABC.")
    path, _, _ = export_factory([multipart, circle], source_level="Secondary Two")
    result = CategorizationService().categorize_file(path)

    assert result.source_level == "secondary_2"
    first = result.questions[0]
    assert [part.label for part in first.parts] == ["i", "ii"]
    assert first.parts[0].assignments[0].topic_code == "N2"
    assert [a.topic_code for a in first.parts[1].assignments[:2]] == ["N2", "N3"]
    assert first.primary_topic_code == "N2"
    assert result.questions[1].status == "unclassified"
    assert all(part.input_status == "machine_unchecked" for part in first.parts)
    assert "machine_unchecked_questions:2" in result.warnings


def test_checked_review_is_used_and_rejected_review_is_skipped(export_factory):
    raw = question(1, "Calculate the probability of the event.")
    rejected = question(2, "Find the HCF.")
    path, document_id, run_key = export_factory([raw, rejected])
    root = path.parents[2]
    for item, decision, text in [
        (raw, "checked", "Find the HCF and LCM of 24 and 36."),
        (rejected, "rejected", "Find the HCF."),
    ]:
        directory = root / "reviews" / str(document_id) / run_key / item["id"]
        directory.mkdir(parents=True)
        record = {
            "id": str(uuid4()),
            "document_id": str(document_id),
            "question_id": item["id"],
            "run_key": run_key,
            "source_fingerprint": "b" * 64,
            "reviewer": "founder",
            "decision": decision,
            "notes": "",
            "content": [{"type": "text", "text": text, "latex": None, "rows": []}],
            "created_at": "2026-09-16T00:00:00+00:00",
        }
        (directory / f"{record['id']}.json").write_text(json.dumps(record))

    result = CategorizationService().categorize_file(path)
    assert result.questions[0].parts[0].input_status == "checked"
    assert result.questions[0].parts[0].assignments[0].topic_code == "N1"
    assert result.questions[1].status == "rejected"
    assert not result.questions[1].parts


def test_run_id_and_part_ids_are_deterministic(export_factory):
    path, _, _ = export_factory([question(1, "Find the probability of a single event.")])
    service = CategorizationService()
    first = service.categorize_file(path)
    second = service.categorize_file(path)
    assert first.run_id == second.run_id
    assert first.questions[0].parts[0].id == second.questions[0].parts[0].id
