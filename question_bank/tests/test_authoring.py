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
    assert {batch.manifest.expected_question_count for batch in report.batch_reports} == {
        21,
        22,
        26,
    }
    assert sum(batch.manifest.expected_question_count for batch in report.batch_reports) == 1_936
    assert report.question_count >= 66
    authored_question_paths = (
        repository_root / "backend_resources/question_bank/g3_math"
    ).glob("**/questions/*.json")
    assert report.question_count == sum(1 for _ in authored_question_paths)
    assert not report.duplicate_matches

    n2_first_batch = next(
        batch for batch in report.batch_reports if batch.manifest.batch_id == "g3-sec1-n2-b001"
    )
    assert n2_first_batch.valid
    assert n2_first_batch.manifest.status == "ready_for_review"
    assert len(n2_first_batch.questions) == 26


def test_authoring_schemas_are_valid_json_schema(repository_root):
    schema_root = repository_root / "backend_resources/question_bank/schema"
    for filename in (
        "question-v1.schema.json",
        "question-batch-manifest-v1.schema.json",
        "question-batch-claims-v1.schema.json",
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
    allocation = Counter((question.primary_outcome, question.difficulty) for question in questions)
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


def test_batch_claims_are_exclusive_idempotent_and_releasable(repository_root, tmp_path):
    from question_bank.collaboration import (
        BatchClaimRegistry,
        claim_batch,
        load_claim_registry,
        release_batch_claim,
    )

    registry_path = tmp_path / "claims.json"
    registry_path.write_text('{"schema_version":"1.0.0","claims":[]}\n')
    banks = repository_root / "backend_resources/question_bank/g3_math"
    claimed_at = datetime(2026, 10, 1, tzinfo=UTC)

    result = claim_batch(
        registry_path,
        banks,
        batch_id="g3-sec1-n2-b002",
        owner="william",
        branch="questions/g3-sec1-n2-b002-william",
        now=claimed_at,
    )
    assert result["changed"] is True
    assert (
        claim_batch(
            registry_path,
            banks,
            batch_id="g3-sec1-n2-b002",
            owner="william",
            branch="questions/g3-sec1-n2-b002-william",
            now=claimed_at,
        )["changed"]
        is False
    )

    with pytest.raises(ValueError, match="already claimed"):
        claim_batch(
            registry_path,
            banks,
            batch_id="g3-sec1-n2-b002",
            owner="friend",
            branch="questions/g3-sec1-n2-b002-friend",
            now=claimed_at,
        )
    with pytest.raises(ValueError, match="already has an active batch claim"):
        claim_batch(
            registry_path,
            banks,
            batch_id="g3-sec1-n2-b003",
            owner="william",
            branch="questions/g3-sec1-n2-b002-william",
            now=claimed_at,
        )

    release_batch_claim(
        registry_path,
        batch_id="g3-sec1-n2-b002",
        owner="william",
        now=datetime(2026, 10, 2, tzinfo=UTC),
    )
    registry = load_claim_registry(registry_path)
    assert isinstance(registry, BatchClaimRegistry)
    assert registry.active_claim("g3-sec1-n2-b002") is None
    assert registry.claims[0].released_at == datetime(2026, 10, 2, tzinfo=UTC)

    ready_claim = claim_batch(
        registry_path,
        banks,
        batch_id="g3-sec1-n2-b001",
        owner="math-reviewer",
        branch="questions/g3-sec1-n2-b001-review",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )
    assert ready_claim["changed"] is True


def test_pull_request_check_exports_claimed_ready_batch(repository_root, tmp_path):
    from question_bank.collaboration import check_pull_request

    branch = "questions/g3-sec1-n2-b001-william"
    registry_path = tmp_path / "claims.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "claims": [
                    {
                        "batch_id": "g3-sec1-n2-b001",
                        "owner": "william",
                        "branch": branch,
                        "claimed_at": "2026-10-01T00:00:00Z",
                        "released_at": None,
                    }
                ],
            }
        )
    )

    report = check_pull_request(
        changed_files=[
            "backend_resources/question_bank/g3_math/secondary_1/n2/v1/questions/n2-l1-001.json"
        ],
        head_branch=branch,
        repository_root=repository_root,
        bank_root=repository_root / "backend_resources/question_bank/g3_math",
        syllabus_path=repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        registry_path=registry_path,
        output=tmp_path / "evidence",
    )

    assert report.valid
    assert report.changed_batches == ["g3-sec1-n2-b001"]
    assert report.exported_batches == ["g3-sec1-n2-b001"]
    assert (tmp_path / "evidence/batches/g3-sec1-n2-b001/index.html").is_file()
    assert "Difficulty L1–L5" in (tmp_path / "evidence/summary.md").read_text()
    assert json.loads((tmp_path / "evidence/report.json").read_text())["valid"] is True


def test_pull_request_check_rejects_wrong_branch_and_planned_question(repository_root, tmp_path):
    from question_bank.collaboration import check_pull_request

    manifest_paths = sorted(
        (repository_root / "backend_resources/question_bank/g3_math").glob(
            "**/batches/*.json"
        )
    )
    manifest_path = next(
        path
        for path in manifest_paths
        if json.loads(path.read_text())["status"] == "planned"
    )
    manifest = json.loads(manifest_path.read_text())
    batch_id = manifest["batch_id"]
    claimed_branch = f"questions/{batch_id}-william"
    question_path = manifest_path.parent.parent / "questions" / (
        f"{manifest['question_keys'][0]}.json"
    )

    registry_path = tmp_path / "claims.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "claims": [
                    {
                        "batch_id": batch_id,
                        "owner": "william",
                        "branch": claimed_branch,
                        "claimed_at": "2026-10-01T00:00:00Z",
                        "released_at": None,
                    }
                ],
            }
        )
    )

    report = check_pull_request(
        changed_files=[question_path.relative_to(repository_root).as_posix()],
        head_branch="questions/wrong-branch",
        repository_root=repository_root,
        bank_root=repository_root / "backend_resources/question_bank/g3_math",
        syllabus_path=repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        registry_path=registry_path,
        output=tmp_path / "evidence",
    )

    assert not report.valid
    assert {issue.code for issue in report.errors} >= {
        "claim_branch_mismatch",
        "planned_batch_has_changed_questions",
    }
    assert not (tmp_path / "evidence/batches").exists()
