from question_bank.course_preview import render_course_preview
from question_bank.course_validation import validate_course


def test_course_preview_renders_course_map_without_answers(repository_root, course_bank_root):
    report = validate_course(
        repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1",
        course_bank_root,
    )

    page = render_course_preview(report)

    assert "Singapore Secondary 1 G3 Mathematics" in page
    assert "Primes and prime factorisation" in page
    assert "976" in page
    assert "Ratios involving rational numbers" in page
    assert "Expressing one quantity as a percentage of another" in page
    assert "Concepts of average rate, speed, constant speed and average speed" in page
    assert "Using letters to represent numbers" in page
    assert "Concept of equation" in page
    assert "Right, acute, obtuse and reflex angles" in page
    assert "Area of a parallelogram and trapezium" in page
    assert "Collecting, classifying and tabulating data" in page
    assert "n1-unit-checkpoint" in page
    assert "n3-unit-checkpoint" in page
    assert "n4-unit-checkpoint" in page
    assert "n5-unit-checkpoint" in page
    assert "n7-unit-checkpoint" in page
    assert "g1-unit-checkpoint" in page
    assert "g5-unit-checkpoint" in page
    assert "s1-unit-checkpoint" in page
    assert "canonical_answer" not in page
