from question_bank.course_preview import render_course_preview
from question_bank.course_validation import validate_course


def test_course_preview_renders_course_map_without_answers(repository_root, bank_root):
    report = validate_course(
        repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1",
        bank_root,
    )

    page = render_course_preview(report)

    assert "Singapore Secondary 1 G3 Mathematics" in page
    assert "Primes and prime factorisation" in page
    assert "40" in page
    assert "n1-unit-checkpoint" in page
    assert "canonical_answer" not in page
