from question_bank.course_repository import course_content_hash, lesson_content_hash
from question_bank.course_validation import validate_course


def test_course_and_lesson_hashes_are_stable(repository_root, bank_root):
    report = validate_course(
        repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1",
        bank_root,
    )

    first_course = course_content_hash(report.course, report.lessons, report.pools)
    same_course = course_content_hash(
        report.course.model_copy(deep=True),
        [lesson.model_copy(deep=True) for lesson in report.lessons],
        report.pools.model_copy(deep=True),
    )
    assert first_course == same_course

    first_lesson = lesson_content_hash(report.lessons[0])
    changed_lesson = report.lessons[0].model_copy(deep=True)
    changed_lesson.objectives.append("Explain why 1 is not a prime number.")
    assert first_lesson != lesson_content_hash(changed_lesson)


def test_review_workflow_does_not_change_lesson_content_hash(
    repository_root, bank_root
):
    report = validate_course(
        repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1",
        bank_root,
    )
    lesson = report.lessons[0]
    promoted = lesson.model_copy(update={"status": "reviewed"})

    assert lesson_content_hash(lesson) == lesson_content_hash(promoted)
