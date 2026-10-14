import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

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
from question_bank.authoring_executor import (
    AuthoringExecutionError,
    execute_authoring_work_order,
    response_schema,
)
from question_bank.authoring_runner import (
    create_authoring_work_order,
    next_authoring_batch,
)
from question_bank.models import Question


def _generated_response_for(work_order):
    distinct_words = (
        "amber birch cedar dahlia elm fern granite hazel iris juniper kelp linen "
        "maple nectar orchid pebble quartz reed saffron tulip umber velvet willow "
        "xylem yarrow zircon"
    ).split()
    questions = []
    for index, slot in enumerate(work_order["slots"], start=1):
        key = slot["stable_key"]
        outcome = slot["primary_outcome"]
        distinct = distinct_words[index - 1]
        questions.append(
            {
                "schema_version": "1.0.0",
                "revision": 1,
                "stable_key": key,
                "bank_key": work_order["bank_key"],
                "curriculum_version": work_order["curriculum_version"],
                "school_level": work_order["school_level"],
                "topic_code": work_order["topic"]["code"],
                "primary_outcome": outcome,
                "title": f"Executor contract example {distinct}",
                "difficulty": slot["difficulty"],
                "calculator_allowed": False,
                "question_type": "structured",
                "status": "draft",
                "stem": [],
                "parts": [
                    {
                        "position": 1,
                        "label": None,
                        "prompt": [
                            {
                                "type": "text",
                                "text": (
                                    f"For the {distinct} contract, write the value of one."
                                ),
                            }
                        ],
                        "marks": 1,
                        "primary_outcome": outcome,
                        "secondary_outcomes": [],
                        "response": {
                            "type": "numeric",
                            "comparison_mode": "exact_numeric",
                            "canonical_answer": "1",
                            "canonical_latex": "1",
                            "accepted_answers": [],
                            "absolute_tolerance": None,
                            "rounding_precision": None,
                            "unit": None,
                        },
                        "hints": [
                            {
                                "stage": 1,
                                "content": [{"type": "text", "text": "Read the value."}],
                            },
                            {
                                "stage": 2,
                                "content": [{"type": "text", "text": "Enter one."}],
                            },
                        ],
                        "solution": [
                            {
                                "position": 1,
                                "content": [{"type": "display_math", "latex": "1"}],
                                "mark_type": "B",
                                "mark_value": 1,
                            }
                        ],
                    }
                ],
                "total_marks": 1,
                "assets": [],
                "provenance": {
                    "authoring_method": "original_generated",
                    "style_references": ["replaced-by-executor"],
                    "created_at": "2026-10-12T00:00:00Z",
                    "authored_by": "replaced-by-executor",
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "review_notes": None,
                },
            }
        )
    return {"questions": questions}


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
    assert n2_first_batch.manifest.status == "approved"
    assert n2_first_batch.manifest.review.mathematics == "approved"
    assert n2_first_batch.manifest.review.editorial == "approved"
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


def test_runner_selects_next_unclaimed_batch_and_builds_exact_work_order(
    repository_root, tmp_path
):
    banks = repository_root / "backend_resources/question_bank/g3_math"
    claims = tmp_path / "batch-claims-v1.json"
    claims.write_text('{"schema_version":"1.0.0","claims":[]}\n')
    next_batch = next_authoring_batch(
        banks,
        claims,
        owner="Willedward",
        syllabus_path=repository_root
        / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        school_level="secondary_2",
        topic_code="N6",
    )

    assert next_batch["status"] == "ready"
    assert next_batch["batch_id"] == "g3-sec2-n6-b001"
    assert next_batch["branch"] == "questions/g3-sec2-n6-b001-willedward"
    assert "authoring-claim g3-sec2-n6-b001" in next_batch["claim_command"]

    result = create_authoring_work_order(
        Path(next_batch["manifest"]),
        tmp_path,
        repository_root=repository_root,
        syllabus_path=repository_root
        / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        house_rules_path=repository_root
        / "backend_resources/question_bank/authoring/house-rules-v1.json",
    )
    work_order = json.loads((tmp_path / "work-order.json").read_text())

    assert result["question_count"] == 26
    assert len(work_order["slots"]) == 26
    assert all(slot["stable_key"].startswith("n6-l") for slot in work_order["slots"])
    manifest_payload = json.loads(Path(next_batch["manifest"]).read_text())
    assert {slot["primary_outcome"] for slot in work_order["slots"]} == {
        allocation["outcome_code"] for allocation in manifest_payload["allocation"]
    }
    assert work_order["generation_contract"]["human_review_required"] == [
        "mathematics",
        "editorial",
    ]
    manifest_keys = manifest_payload["question_keys"]
    assert {slot["stable_key"] for slot in work_order["slots"]} == set(manifest_keys)
    assert "Generation never grants approval" in (tmp_path / "prompt.md").read_text()


def test_executor_repairs_and_validates_complete_planned_work_order(repository_root, tmp_path):
    manifest = (
        repository_root
        / "backend_resources/question_bank/g3_math/secondary_2/n6/v1/batches"
        / "g3-sec2-n6-b001.json"
    )
    create_authoring_work_order(
        manifest,
        tmp_path,
        repository_root=repository_root,
        syllabus_path=repository_root
        / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        house_rules_path=repository_root
        / "backend_resources/question_bank/authoring/house-rules-v1.json",
    )
    work_order = json.loads((tmp_path / "work-order.json").read_text())
    valid_response = _generated_response_for(work_order)
    calls = []

    def provider(prompt, schema):
        calls.append((prompt, schema))
        if len(calls) == 1:
            return {"questions": []}
        return valid_response

    result = execute_authoring_work_order(
        tmp_path / "work-order.json",
        provider,
        repository_root=repository_root,
        provider="test",
        model="deterministic-fixture",
        authored_by="Test pipeline",
        max_repairs=1,
        dry_run=True,
    )

    assert result["status"] == "validated"
    assert result["question_count"] == 26
    assert [attempt["valid"] for attempt in result["attempts"]] == [False, True]
    assert "Correction request" in calls[1][0]
    assert calls[0][1]["required"] == ["questions"]
    assert calls[0][1]["properties"]["questions"]["items"]["additionalProperties"] is False


def test_executor_rejects_wrong_slot_order_without_writing(repository_root, tmp_path):
    manifest = (
        repository_root
        / "backend_resources/question_bank/g3_math/secondary_2/n6/v1/batches"
        / "g3-sec2-n6-b001.json"
    )
    create_authoring_work_order(
        manifest,
        tmp_path,
        repository_root=repository_root,
        syllabus_path=repository_root
        / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        house_rules_path=repository_root
        / "backend_resources/question_bank/authoring/house-rules-v1.json",
    )
    work_order = json.loads((tmp_path / "work-order.json").read_text())
    response = _generated_response_for(work_order)
    response["questions"][0]["stable_key"] = "g2-l1-999"

    with pytest.raises(AuthoringExecutionError, match="exact stable keys"):
        execute_authoring_work_order(
            tmp_path / "work-order.json",
            lambda _prompt, _schema: response,
            repository_root=repository_root,
            provider="test",
            model="deterministic-fixture",
            authored_by="Test pipeline",
            max_repairs=0,
            dry_run=True,
        )


def test_openai_response_schema_requires_every_question_field():
    schema = response_schema(Question.model_json_schema())
    question = schema["properties"]["questions"]["items"]

    assert set(question["required"]) == set(question["properties"])
    assert question["additionalProperties"] is False

    def assert_strict(node):
        if isinstance(node, list):
            for item in node:
                assert_strict(item)
            return
        if not isinstance(node, dict):
            return
        assert "oneOf" not in node
        assert "prefixItems" not in node
        assert "discriminator" not in node
        if node.get("type") == "object" or "properties" in node:
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node.get("properties", {}))
        for value in node.values():
            assert_strict(value)

    assert_strict(schema)


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
    preview_html = (tmp_path / "review/index.html").read_text()
    assert "KaTeX_Main" in preview_html
    assert "document.querySelectorAll('[data-latex]')" in preview_html
    assert 'class="math display-math"' in preview_html
    assert list((tmp_path / "review/assets/katex/fonts").glob("*.woff2"))
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
    claimable_statuses = {"planned", "draft", "ready_for_review", "changes_requested"}
    claimable_batch_ids = [
        manifest["batch_id"]
        for path in sorted(banks.glob("**/batches/*.json"))
        if (manifest := json.loads(path.read_text()))["status"] in claimable_statuses
    ]
    batch_id, other_batch_id = claimable_batch_ids[:2]
    branch = f"questions/{batch_id}-william"

    result = claim_batch(
        registry_path,
        banks,
        batch_id=batch_id,
        owner="william",
        branch=branch,
        now=claimed_at,
    )
    assert result["changed"] is True
    assert (
        claim_batch(
            registry_path,
            banks,
            batch_id=batch_id,
            owner="william",
            branch=branch,
            now=claimed_at,
        )["changed"]
        is False
    )

    with pytest.raises(ValueError, match="already claimed"):
        claim_batch(
            registry_path,
            banks,
            batch_id=batch_id,
            owner="friend",
            branch=f"questions/{batch_id}-friend",
            now=claimed_at,
        )
    with pytest.raises(ValueError, match="already has an active batch claim"):
        claim_batch(
            registry_path,
            banks,
            batch_id=other_batch_id,
            owner="william",
            branch=branch,
            now=claimed_at,
        )

    release_batch_claim(
        registry_path,
        batch_id=batch_id,
        owner="william",
        now=datetime(2026, 10, 2, tzinfo=UTC),
    )
    registry = load_claim_registry(registry_path)
    assert isinstance(registry, BatchClaimRegistry)
    assert registry.active_claim(batch_id) is None
    assert registry.claims[0].released_at == datetime(2026, 10, 2, tzinfo=UTC)

    reclaimed = claim_batch(
        registry_path,
        banks,
        batch_id=batch_id,
        owner="math-reviewer",
        branch=f"questions/{batch_id}-review",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )
    assert reclaimed["changed"] is True


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
