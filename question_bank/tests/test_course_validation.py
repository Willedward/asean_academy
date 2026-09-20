import json
import shutil

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from question_bank.course_models import Course, Lesson, QuestionPools
from question_bank.course_validation import schema_documents, validate_course


def test_n1_course_source_is_valid_draft(repository_root, bank_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    report = validate_course(course_root, bank_root)

    assert report.valid
    assert report.course.stable_key == "g3-sec1-math"
    assert len(report.lessons) == 7
    assert len(report.pools.pools) == 9
    assert report.as_dict()["allocated_question_count"] == 40
    assert {issue.code for issue in report.warnings} == {"lesson_content_required"}


def test_n1_course_cannot_publish_while_content_and_questions_are_drafts(
    repository_root, bank_root
):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    report = validate_course(course_root, bank_root, publish=True)

    assert not report.valid
    codes = {issue.code for issue in report.errors}
    assert "course_review_required" in codes
    assert "lesson_review_required" in codes
    assert "question_bank_review_required" in codes


def test_generated_course_schemas_match_models(repository_root):
    schemas = schema_documents()

    assert schemas["course-v1.schema.json"] == Course.model_json_schema()
    assert schemas["lesson-v1.schema.json"] == Lesson.model_json_schema()
    assert schemas["question-pools-v1.schema.json"] == QuestionPools.model_json_schema()
    schema_root = repository_root / "backend_resources/courses/schema"
    for filename, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        assert json.loads((schema_root / filename).read_text()) == schema


def test_worked_example_steps_are_explicit_and_ordered(repository_root):
    lesson_path = (
        repository_root
        / "backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n1-lesson-01.json"
    )
    payload = json.loads(lesson_path.read_text())
    payload["sections"] = [
        {
            "stable_key": "prime-example",
            "position": 1,
            "type": "worked_example",
            "title": "Factorise 12",
            "prompt": [
                {"type": "text", "text": "Write 12 as a product of prime factors."}
            ],
            "steps": [
                {
                    "position": 1,
                    "content": [{"type": "display_math", "latex": "12=2\\times6"}],
                },
                {
                    "position": 2,
                    "content": [{"type": "display_math", "latex": "12=2^2\\times3"}],
                },
            ],
            "verification_note": "Both bases are prime and their product is 12.",
        }
    ]

    lesson = Lesson.model_validate(payload)
    assert lesson.sections[0].steps[1].position == 2

    payload["sections"][0]["steps"][1]["position"] = 3
    with pytest.raises(ValidationError, match="consecutive from 1"):
        Lesson.model_validate(payload)


def test_all_questions_are_allocated_once(repository_root, bank_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    report = validate_course(course_root, bank_root)
    allocated = [
        item.question_key for pool in report.pools.pools for item in pool.items
    ]

    assert len(allocated) == 40
    assert len(set(allocated)) == 40


def test_lesson_required_practice_must_match_its_pool(
    repository_root, bank_root, tmp_path
):
    source = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    course_root = tmp_path / "course"
    shutil.copytree(source, course_root)
    course_path = course_root / "course.json"
    payload = json.loads(course_path.read_text())
    payload["units"][0]["lessons"][0]["required_practice_count"] = 4
    course_path.write_text(json.dumps(payload))

    report = validate_course(course_root, bank_root)

    assert not report.valid
    assert "required_practice_count" in {issue.code for issue in report.errors}
