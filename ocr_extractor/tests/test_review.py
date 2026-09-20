import json
from uuid import uuid4

import pytest

from ocr_extractor.pdf import ExtractionError
from ocr_extractor.repository import Repository
from ocr_extractor.review import ReviewInput, ReviewStore, fingerprint


def review_request(result):
    question = result.questions[0]
    content = [b.model_copy(deep=True) for b in question.content]
    content[0].type = "math"
    content[0].latex = "\\frac{12+8}{2}"
    return ReviewInput(
        document_id=result.document.id,
        question_id=question.id,
        run_key=result.run_key,
        source_fingerprint=fingerprint(question),
        reviewer="Test reviewer",
        decision="checked",
        content=content,
    )


def test_reviews_persist_separately_survive_reingestion_and_detect_conflicts(service, normal_pdf):
    result = service.extract_file(normal_pdf)
    raw_manifest = service.result_path(result).read_bytes()
    with Repository.sqlite(service.output_dir / "questions.sqlite3") as repo:
        repo.save(result)
        store = ReviewStore(service.output_dir, repo)
        request = review_request(result)
        record = store.save(request)
        assert service.result_path(result).read_bytes() == raw_manifest
        assert store.latest_review(result, result.questions[0]) == record
        with pytest.raises(ExtractionError, match="Another review"):
            store.save(request)
        # Updating one review creates a new immutable revision.
        request.previous_review_id = record.id
        request.notes = "Checked the fraction against the source"
        second = store.save(request)
        assert second.id != record.id
        assert len(list((service.output_dir / "reviews").rglob("*.json"))) == 2
        repo.save(result)
        assert repo.connection.execute("SELECT count(*) FROM question_reviews").fetchone()[0] == 2
        block = repo.connection.execute("SELECT payload FROM question_blocks LIMIT 1").fetchone()[0]
        assert json.loads(block)["type"] == "text"  # Raw extraction is preserved.
        assert (
            repo.connection.execute(
                "SELECT question_latex FROM question_display LIMIT 1"
            ).fetchone()[0]
            is None
        )


def test_review_rejects_forged_evidence_and_stale_extractions(service, normal_pdf):
    result = service.extract_file(normal_pdf)
    store = ReviewStore(service.output_dir)
    request = review_request(result)
    request.content[0].source_path = "../../.env"
    with pytest.raises(ValueError, match="original source"):
        store.save(request)
    request = review_request(result)
    request.source_fingerprint = "0" * 64
    with pytest.raises(ExtractionError, match="Extraction changed"):
        store.save(request)


def test_review_validation_and_split_blocks(service, normal_pdf):
    result = service.extract_file(normal_pdf)
    request = review_request(result)
    split = request.content[0].model_copy(deep=True)
    split.id = uuid4()
    split.type, split.text = "text", "Calculate this value."
    request.content.append(split)
    assert len(ReviewStore(service.output_dir).save(request).content) == 2
    payload = request.model_dump()
    payload["content"][0]["latex"] = "\\frac{a}{b"
    with pytest.raises(ValueError, match="balanced LaTeX"):
        ReviewInput.model_validate(payload)
    payload["decision"] = "draft"
    assert ReviewInput.model_validate(payload).decision == "draft"


def test_migrations_upgrade_existing_staging_database(tmp_path):
    import sqlite3
    from importlib.resources import files

    path = tmp_path / "v1.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.executescript(files("ocr_extractor").joinpath("migrations/001_sqlite.sql").read_text())
    with Repository.sqlite(path) as repo:
        repo.initialize()
        assert repo.connection.execute("SELECT count(*) FROM question_blocks").fetchone()[0] == 0
        assert repo.connection.execute("SELECT count(*) FROM question_reviews").fetchone()[0] == 0
