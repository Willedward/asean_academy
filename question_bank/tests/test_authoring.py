import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from question_bank.authoring import (
    BatchAllocation,
    GeneratorMetadata,
    QuestionBatchManifest,
    SourceReference,
    detect_prompt_duplicates,
    export_reviewer_batch,
    validate_authoring_pipeline,
)
from question_bank.models import Question


def test_repository_authoring_plan_covers_all_topic_groups(repository_root):
    report = validate_authoring_pipeline(
        repository_root / "backend_resources/question_bank/g3_math",
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        repository_root=repository_root,
    )

    assert report.valid
    assert report.blueprint_count == 19
    assert len(report.batch_reports) == 75
    assert {batch.manifest.expected_question_count for batch in report.batch_reports} == {21, 22, 26}
    assert sum(batch.manifest.expected_question_count for batch in report.batch_reports) == 1_936
    assert report.question_count == 66
    assert not report.duplicate_matches

    n2_first_batch = next(
        batch
        for batch in report.batch_reports
        if batch.manifest.batch_id == "g3-sec1-n2-b001"
    )
    assert n2_first_batch.valid
    assert n2_first_batch.manifest.status == "ready_for_review"
    assert len(n2_first_batch.questions) == 26


def test_authoring_schemas_are_valid_json_schema(repository_root):
    schema_root = repository_root / "backend_resources/question_bank/schema"
    for filename in (
        "question-v1.schema.json",
        "question-batch-manifest-v1.schema.json",
        "question-house-rules-v1.schema.json",
    ):
        Draft202012Validator.check_schema(json.loads((schema_root / filename).read_text()))


def test_manifest_rejects_batches_outside_reviewable_size():
    payload = {
        "batch_id": "g3-sec1-n2-b001",
        "bank_key": "g3-sec1-n2-v1",
        "curriculum_version": "g3_math_v1_draft",
        "school_level": "secondary_1",
        "topic_code": "N2",
        "status": "planned",
        "created_at": "2026-09-30T00:00:00Z",
        "generator": {
            "provider": "unassigned",
            "model": "unassigned",
            "generator_version": "unassigned",
            "prompt_version": "math-question-authoring-v1",
        },
        "source_references": [
            {
                "path": "syllabus.json",
                "sha256": "0" * 64,
                "role": "syllabus",
            }
        ],
        "allocation": [{"outcome_code": "2.1", "difficulty": 1, "count": 19}],
        "expected_question_count": 19,
    }

    with pytest.raises(ValidationError):
        QuestionBatchManifest.model_validate(payload)


def test_number_variants_are_reported_as_near_duplicate_templates(bank_root):
    payload = json.loads((bank_root / "questions/n1-l1-01.json").read_text())
    first = Question.model_validate(payload)
    variant = json.loads(json.dumps(payload).replace("360", "420"))
    variant["stable_key"] = "n1-l1-999"
    second = Question.model_validate(variant)

    matches = detect_prompt_duplicates([first, second])

    assert len(matches) == 1
    assert matches[0].kind == "exact_prompt"
    assert matches[0].similarity == 1


def test_authored_batch_executes_answers_and_exports_reviewer_packet(
    repository_root, bank_root, tmp_path
):
    target = tmp_path / "bank"
    shutil.copytree(bank_root, target)
    questions = [
        Question.model_validate_json(path.read_text())
        for path in sorted((target / "questions").glob("*.json"))[:20]
    ]
    allocation = Counter(
        (question.primary_outcome, question.difficulty) for question in questions
    )
    syllabus = repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json"
    manifest = QuestionBatchManifest(
        batch_id="g3-sec1-n1-b001",
        bank_key="g3-sec1-n1-v1",
        curriculum_version="g3_math_v1_draft",
        school_level="secondary_1",
        topic_code="N1",
        status="draft",
        created_at=datetime.now(UTC),
        generator=GeneratorMetadata(
            provider="codex",
            model="repository-test",
            generator_version="test-v1",
            prompt_version="math-question-authoring-v1",
        ),
        source_references=[
            SourceReference(
                path=str(syllabus.relative_to(repository_root)),
                sha256=hashlib.sha256(syllabus.read_bytes()).hexdigest(),
                role="syllabus",
            )
        ],
        allocation=[
            BatchAllocation(outcome_code=outcome, difficulty=difficulty, count=count)
            for (outcome, difficulty), count in sorted(allocation.items())
        ],
        expected_question_count=20,
        question_keys=[question.stable_key for question in questions],
    )
    manifest_path = target / "batches/g3-sec1-n1-b001.json"
    manifest_path.parent.mkdir(exist_ok=True)
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2))

    result = export_reviewer_batch(
        manifest_path,
        tmp_path / "review",
        repository_root=repository_root,
        syllabus_path=syllabus,
    )

    assert result["question_count"] == 20
    assert set(result["files"]) == {
        "index.html",
        "manifest.json",
        "questions.json",
        "review.csv",
        "review.md",
        "validation.json",
    }
    assert "g3-sec1-n1-b001" in (tmp_path / "review/index.html").read_text()
    review_markdown = (tmp_path / "review/review.md").read_text()
    assert "Mathematics decision: `pending`" in review_markdown
    assert "Editorial decision: `pending`" in review_markdown
    assert questions[0].stable_key in review_markdown
