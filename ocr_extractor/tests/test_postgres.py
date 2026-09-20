"""Opt-in real database regression; TEST_DATABASE_URL must be a disposable test DB."""

import os

import pytest

from ocr_extractor.repository import Repository
from ocr_extractor.review import ReviewInput, ReviewStore, fingerprint


@pytest.mark.postgres
def test_postgres_transaction_and_idempotency(service, normal_pdf):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database")
    result = service.extract_file(normal_pdf)
    with Repository.connect_postgres(url) as repository:
        repository.initialize()
        try:
            repository.save(result)
            repository.save(result)
            with repository.connection.transaction():
                count = repository.connection.execute(
                    "SELECT count(*) FROM ocr_extractor.questions WHERE document_id = %s",
                    (str(result.document.id),),
                ).fetchone()[0]
                assert count == 2
                status = repository.connection.execute(
                    "SELECT status FROM ocr_extractor.questions WHERE document_id = %s",
                    (str(result.document.id),),
                ).fetchall()
                assert all(row[0] == "needs_review" for row in status)
                blocks = repository.connection.execute(
                    "SELECT count(*) FROM ocr_extractor.question_blocks WHERE question_id = %s",
                    (str(result.questions[0].id),),
                ).fetchone()[0]
                assert blocks == len(result.questions[0].content)
                display = repository.connection.execute(
                    "SELECT question_latex FROM ocr_extractor.question_display WHERE id = %s",
                    (str(result.questions[0].id),),
                ).fetchone()
                assert display == (None,)
            question = result.questions[0]
            request = ReviewInput(
                document_id=result.document.id,
                question_id=question.id,
                run_key=result.run_key,
                source_fingerprint=fingerprint(question),
                reviewer="Integration test",
                decision="draft",
                content=question.content,
            )
            review = ReviewStore(service.output_dir, repository).save(request)
            repository.save(result)
            with repository.connection.transaction():
                saved = repository.connection.execute(
                    "SELECT payload FROM ocr_extractor.question_reviews WHERE id = %s",
                    (str(review.id),),
                ).fetchone()[0]
                assert saved["reviewer"] == "Integration test"
                assert saved["content"][0]["source_path"] == question.content[0].source_path
        finally:
            with repository.connection.transaction():
                repository.connection.execute(
                    "DELETE FROM ocr_extractor.question_reviews WHERE document_id = %s",
                    (str(result.document.id),),
                )
                repository.connection.execute(
                    "DELETE FROM ocr_extractor.source_documents WHERE id = %s",
                    (str(result.document.id),),
                )
