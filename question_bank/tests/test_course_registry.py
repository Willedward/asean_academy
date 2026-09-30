import json

from question_bank.course_registry import validate_course_registry


def registry_paths(repository_root):
    return (
        repository_root / "backend_resources/courses/g3_math/v1/registry.json",
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
    )


def test_full_secondary_one_two_registry_matches_syllabus(repository_root):
    report = validate_course_registry(*registry_paths(repository_root))

    assert report.valid
    assert report.as_dict() == {
        "valid": True,
        "registry_version": "g3_math_courses_v1",
        "course_count": 2,
        "topic_group_count": 19,
        "lesson_count": 87,
        "outcome_count": 87,
        "error_count": 0,
        "issues": [],
    }
    registry = report.registry
    secondary_one, secondary_two = registry.courses
    assert [unit.topic_code for unit in secondary_one.units] == [
        "N1", "N2", "N3", "N4", "N5", "N6", "N7", "G1", "G5", "S1",
    ]
    assert [unit.topic_code for unit in secondary_two.units] == [
        "N2", "N5", "N6", "N7", "G2", "G4", "G5", "S1", "S2",
    ]
    lesson_keys = {
        lesson.stable_key
        for course in registry.courses
        for unit in course.units
        for lesson in unit.lessons
    }
    assert len(lesson_keys) == 87
    assert secondary_one.units[0].content_status == "draft"
    assert all(unit.content_status == "planned" for unit in secondary_two.units)


def test_registry_validation_detects_outcome_drift(repository_root, tmp_path):
    registry_path, syllabus_path = registry_paths(repository_root)
    payload = json.loads(registry_path.read_text())
    payload["courses"][1]["units"][0]["lessons"][0]["outcomes"] = ["2.5"]
    broken = tmp_path / "registry.json"
    broken.write_text(json.dumps(payload))

    report = validate_course_registry(broken, syllabus_path)

    assert not report.valid
    assert "unit_outcome_inventory" in {issue.code for issue in report.issues}
