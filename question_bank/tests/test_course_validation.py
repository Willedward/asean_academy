import hashlib
import json
import shutil

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from question_bank.course_models import Course, Lesson, QuestionPools
from question_bank.course_validation import (
    lesson_note_depth_shortfalls,
    schema_documents,
    validate_course,
)


def test_complete_secondary_1_course_source_is_valid(repository_root, course_bank_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    report = validate_course(course_root, course_bank_root)

    assert report.valid
    assert report.course.stable_key == "g3-sec1-math"
    assert len(report.lessons) == 52
    assert len(report.pools.pools) == 72
    assert report.as_dict()["allocated_question_count"] == 976
    assert {issue.code for issue in report.warnings} == {"lesson_notes_thin"}
    assert {issue.path.rsplit("/", 1)[-1] for issue in report.warnings} == {
        *(f"n5-lesson-{number:02}.json" for number in range(1, 9)),
    }


def test_secondary_2_authored_course_source_is_valid(repository_root, course_bank_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_2/g2/v1"
    report = validate_course(course_root, course_bank_root)

    assert report.valid
    assert report.course.stable_key == "g3-sec2-math"
    assert [unit.topic_code for unit in report.course.units] == ["G2", "S2", "N2", "G4"]
    assert len(report.lessons) == 12
    assert len(report.pools.pools) == 20
    assert report.as_dict()["allocated_question_count"] == 416
    assert report.warnings == []


def test_integrated_secondary_2_s2_lessons_meet_the_depth_and_asset_gates(repository_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_2/g2/v1"
    lesson_paths = sorted((course_root / "lessons").glob("s2-*.json"))

    assert [path.stem for path in lesson_paths] == ["s2-lesson-01", "s2-lesson-02"]
    for path in lesson_paths:
        lesson = Lesson.model_validate_json(path.read_text())
        assert lesson.status == "draft"
        assert lesson_note_depth_shortfalls(lesson) == []
        for asset in lesson.assets:
            asset_path = course_root / asset.path
            assert asset_path.is_file()
            assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == asset.sha256


def test_integrated_secondary_2_n2_lessons_meet_the_depth_and_asset_gates(repository_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_2/g2/v1"
    lesson_paths = sorted((course_root / "lessons").glob("n2-*.json"))

    assert [path.stem for path in lesson_paths] == ["n2-lesson-04", "n2-lesson-05"]
    for path in lesson_paths:
        lesson = Lesson.model_validate_json(path.read_text())
        assert lesson.status == "draft"
        assert lesson_note_depth_shortfalls(lesson) == []
        for asset in lesson.assets:
            asset_path = course_root / asset.path
            assert asset_path.is_file()
            assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == asset.sha256


def test_integrated_secondary_2_g4_lessons_meet_the_depth_and_asset_gates(repository_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_2/g2/v1"
    lesson_paths = sorted((course_root / "lessons").glob("g4-*.json"))

    assert [path.stem for path in lesson_paths] == [
        "g4-lesson-01",
        "g4-lesson-02",
        "g4-lesson-03",
    ]
    for path in lesson_paths:
        lesson = Lesson.model_validate_json(path.read_text())
        assert lesson.status == "draft"
        assert lesson_note_depth_shortfalls(lesson) == []
        for asset in lesson.assets:
            asset_path = course_root / asset.path
            assert asset_path.is_file()
            assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == asset.sha256


def test_thin_lesson_notes_block_publication(repository_root, course_bank_root, tmp_path):
    source = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    course_root = tmp_path / "course"
    shutil.copytree(source, course_root)

    draft_report = validate_course(course_root, course_bank_root)
    assert "lesson_notes_thin" in {issue.code for issue in draft_report.warnings}

    publish_report = validate_course(course_root, course_bank_root, publish=True)
    assert "lesson_notes_thin" in {issue.code for issue in publish_report.errors}

    thin_path = course_root / "lessons/n5-lesson-01.json"
    thin_lesson = json.loads(thin_path.read_text())
    thin_lesson["status"] = "reviewed"
    thin_lesson["provenance"].update(
        {
            "reviewed_at": "2026-10-13T12:00:00+08:00",
            "reviewed_by": "Test reviewer",
            "review_notes": "Structural gate test.",
        }
    )
    thin_path.write_text(json.dumps(thin_lesson))
    reviewed_report = validate_course(course_root, course_bank_root)
    assert "lesson_notes_thin" in {issue.code for issue in reviewed_report.errors}


def test_secondary_1_course_cannot_publish_while_course_lessons_and_questions_are_drafts(
    repository_root, course_bank_root
):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    report = validate_course(course_root, course_bank_root, publish=True)

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


def test_all_questions_are_allocated_once(repository_root, course_bank_root):
    course_root = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    report = validate_course(course_root, course_bank_root)
    allocated = [
        item.question_key for pool in report.pools.pools for item in pool.items
    ]

    assert len(allocated) == 976
    assert len(set(allocated)) == 976


def test_lesson_required_practice_must_match_its_pool(
    repository_root, course_bank_root, tmp_path
):
    source = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    course_root = tmp_path / "course"
    shutil.copytree(source, course_root)
    course_path = course_root / "course.json"
    payload = json.loads(course_path.read_text())
    payload["units"][0]["lessons"][0]["required_practice_count"] = 4
    course_path.write_text(json.dumps(payload))

    report = validate_course(course_root, course_bank_root)

    assert not report.valid
    assert "required_practice_count" in {issue.code for issue in report.errors}


def test_angle_type_diagram_rays_must_match_the_declared_classification(
    repository_root, course_bank_root, tmp_path
):
    source = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1"
    course_root = tmp_path / "course"
    shutil.copytree(source, course_root)
    lesson_path = course_root / "lessons/g1-lesson-01.json"
    lesson = json.loads(lesson_path.read_text())
    asset = lesson["assets"][0]
    svg_path = course_root / asset["path"]
    svg = svg_path.read_text()
    svg = svg.replace(
        '<line x1="520" y1="230" x2="628.25" y2="292.5"/>',
        '<line x1="520" y1="230" x2="628.25" y2="167.5"/>',
        1,
    )
    svg_path.write_text(svg)
    asset["sha256"] = hashlib.sha256(svg_path.read_bytes()).hexdigest()
    lesson_path.write_text(json.dumps(lesson))

    report = validate_course(course_root, course_bank_root)

    assert not report.valid
    assert "geometry_angle_measure" in {issue.code for issue in report.errors}
