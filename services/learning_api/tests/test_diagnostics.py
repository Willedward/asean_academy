"""Deterministic diagnostic policy tests without PostgreSQL."""

import pytest

from learning_api.diagnostic_recommendations import build_topic_results
from learning_api.diagnostic_repository import band_for


@pytest.mark.parametrize(
    ("percentage", "band"),
    [
        (0, "getting_started"),
        (49.99, "getting_started"),
        (50, "on_track"),
        (79.99, "on_track"),
        (80, "ahead"),
        (100, "ahead"),
    ],
)
def test_n1_readiness_band_boundaries(percentage, band):
    assert band_for(percentage) == band


def _score_row(
    *,
    school_level: str,
    topic_code: str,
    topic_title: str,
    outcome_code: str,
    score: float,
    lesson_key: str,
    lesson_title: str,
    unit_key: str,
    unit_position: int,
    outcome_position: int = 1,
) -> dict:
    return {
        "school_level": school_level,
        "topic_code": topic_code,
        "topic_title": topic_title,
        "outcome_code": outcome_code,
        "outcome_position": outcome_position,
        "score": score,
        "max_score": 1,
        "course_key": "g3-sec1-math" if school_level == "secondary_1" else "g3-sec2-math",
        "unit_key": unit_key,
        "unit_position": unit_position,
        "lesson_key": lesson_key,
        "lesson_title": lesson_title,
        "lesson_position": outcome_position,
    }


def test_topic_results_keep_repeated_outcome_codes_separate():
    topics, recommendations = build_topic_results(
        [
            _score_row(
                school_level="secondary_1",
                topic_code="N1",
                topic_title="Numbers and their operations",
                outcome_code="1.1",
                score=1,
                lesson_key="n1-lesson-01",
                lesson_title="Primes and prime factorisation",
                unit_key="g3-sec1-n1",
                unit_position=1,
            ),
            _score_row(
                school_level="secondary_1",
                topic_code="G1",
                topic_title="Angles, triangles and polygons",
                outcome_code="1.1",
                score=0,
                lesson_key="g1-lesson-01",
                lesson_title="Right, acute, obtuse and reflex angles",
                unit_key="g3-sec1-g1",
                unit_position=8,
            ),
        ]
    )

    assert [topic["topic_group_key"] for topic in topics] == ["g3-sec1-n1", "g3-sec1-g1"]
    assert recommendations[0]["topic_group_key"] == "g3-sec1-g1"
    assert recommendations[0]["lesson_key"] == "g1-lesson-01"


def test_recommendations_rank_topics_then_choose_weakest_tested_lesson():
    topics, recommendations = build_topic_results(
        [
            _score_row(
                school_level="secondary_1",
                topic_code="N2",
                topic_title="Ratio and proportion",
                outcome_code="2.1",
                score=1,
                lesson_key="n2-lesson-01",
                lesson_title="Ratios involving rational numbers",
                unit_key="g3-sec1-n2",
                unit_position=2,
            ),
            _score_row(
                school_level="secondary_1",
                topic_code="N2",
                topic_title="Ratio and proportion",
                outcome_code="2.2",
                outcome_position=2,
                score=0,
                lesson_key="n2-lesson-02",
                lesson_title="Writing a ratio in its simplest form",
                unit_key="g3-sec1-n2",
                unit_position=2,
            ),
            _score_row(
                school_level="secondary_2",
                topic_code="G2",
                topic_title="Congruence and similarity",
                outcome_code="2.1",
                score=0,
                lesson_key="g2-lesson-01",
                lesson_title="Congruent figures",
                unit_key="g3-sec2-g2",
                unit_position=1,
            ),
        ]
    )

    assert topics[0]["percentage"] == 50
    assert recommendations[0]["lesson_key"] == "g2-lesson-01"
    assert recommendations[1]["lesson_key"] == "n2-lesson-02"
    assert [item["rank"] for item in recommendations] == [1, 2]


def test_high_scoring_diagnostic_still_has_one_clear_starting_lesson():
    _, recommendations = build_topic_results(
        [
            _score_row(
                school_level="secondary_1",
                topic_code="N1",
                topic_title="Numbers and their operations",
                outcome_code="1.1",
                score=1,
                lesson_key="n1-lesson-01",
                lesson_title="Primes and prime factorisation",
                unit_key="g3-sec1-n1",
                unit_position=1,
            )
        ]
    )

    assert len(recommendations) == 1
    assert recommendations[0]["percentage"] == 100
    assert "stretch review" in recommendations[0]["reason"]


def test_recommendations_are_capped_and_ties_follow_course_order():
    rows = [
        _score_row(
            school_level="secondary_1",
            topic_code=f"N{position}",
            topic_title=f"Topic {position}",
            outcome_code=f"{position}.1",
            score=0,
            lesson_key=f"n{position}-lesson-01",
            lesson_title=f"Lesson {position}",
            unit_key=f"g3-sec1-n{position}",
            unit_position=position,
        )
        for position in range(1, 5)
    ]

    _, recommendations = build_topic_results(reversed(rows))

    assert [item["unit_key"] for item in recommendations] == [
        "g3-sec1-n1",
        "g3-sec1-n2",
        "g3-sec1-n3",
    ]
