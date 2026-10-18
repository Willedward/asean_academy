"""Deterministic topic scoring and lesson recommendations for diagnostics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

RECOMMENDATION_POLICY_VERSION = "topic-readiness-v1"
MAX_RECOMMENDATIONS = 3


def _number(value: Decimal | float | int) -> float:
    return round(float(value), 3)


def _percentage(score: float, maximum: float) -> float:
    return round(score * 100 / maximum, 2)


def _topic_group_key(row: dict[str, Any]) -> str:
    if row.get("unit_key"):
        return str(row["unit_key"])
    level = "sec1" if row["school_level"] == "secondary_1" else "sec2"
    return f"g3-{level}-{str(row['topic_code']).lower()}"


def _reason(percentage: float) -> str:
    if percentage < 50:
        return "Start here to rebuild the foundation shown by this readiness check."
    if percentage < 80:
        return "Practise this next to turn partial understanding into reliable marks."
    return "This was your lowest topic score, so use this lesson as a stretch review."


def build_topic_results(rows: Iterable[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    """Aggregate scored form items and rank up to three actionable lessons.

    Topic identity includes school level and syllabus topic. This avoids collisions
    between repeated outcome codes such as N1 1.1, G1 1.1 and S1 1.1.
    """

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "score": 0.0,
            "max_score": 0.0,
            "outcome_codes": set(),
            "candidates": [],
        }
    )
    for row in rows:
        key = _topic_group_key(row)
        bucket = grouped[key]
        bucket.update(
            {
                "topic_group_key": key,
                "school_level": row["school_level"],
                "topic_code": row["topic_code"],
                "title": row["topic_title"],
                "unit_position": row.get("unit_position") or 10_000,
            }
        )
        score = _number(row["score"])
        maximum = _number(row["max_score"])
        bucket["score"] += score
        bucket["max_score"] += maximum
        bucket["outcome_codes"].add(row["outcome_code"])
        if row.get("lesson_key"):
            bucket["candidates"].append(
                {
                    "outcome_percentage": _percentage(score, maximum),
                    "outcome_position": row.get("outcome_position") or 10_000,
                    "lesson_position": row.get("lesson_position") or 10_000,
                    "course_key": row["course_key"],
                    "unit_key": row["unit_key"],
                    "lesson_key": row["lesson_key"],
                    "lesson_title": row["lesson_title"],
                }
            )

    topic_scores: list[dict] = []
    recommendation_candidates: list[dict] = []
    for bucket in grouped.values():
        score = round(bucket["score"], 3)
        maximum = round(bucket["max_score"], 3)
        topic = {
            "topic_group_key": bucket["topic_group_key"],
            "school_level": bucket["school_level"],
            "topic_code": bucket["topic_code"],
            "title": bucket["title"],
            "score": score,
            "max_score": maximum,
            "percentage": _percentage(score, maximum),
            "outcome_codes": sorted(bucket["outcome_codes"]),
        }
        topic_scores.append(topic)
        candidates = sorted(
            bucket["candidates"],
            key=lambda item: (
                item["outcome_percentage"],
                item["outcome_position"],
                item["lesson_position"],
                item["lesson_key"],
            ),
        )
        if candidates:
            recommendation_candidates.append(
                {
                    **topic,
                    "course_key": candidates[0]["course_key"],
                    "unit_key": candidates[0]["unit_key"],
                    "lesson_key": candidates[0]["lesson_key"],
                    "lesson_title": candidates[0]["lesson_title"],
                    "unit_position": bucket["unit_position"],
                }
            )

    topic_scores.sort(
        key=lambda item: (
            0 if item["school_level"] == "secondary_1" else 1,
            grouped[item["topic_group_key"]]["unit_position"],
            item["topic_code"],
        )
    )
    recommendation_candidates.sort(
        key=lambda item: (
            item["percentage"],
            0 if item["school_level"] == "secondary_1" else 1,
            item["unit_position"],
            item["topic_code"],
        )
    )
    below_mastery = [item for item in recommendation_candidates if item["percentage"] < 80]
    selected = (below_mastery or recommendation_candidates)[:MAX_RECOMMENDATIONS]
    recommendations = [
        {
            "rank": rank,
            "topic_group_key": item["topic_group_key"],
            "school_level": item["school_level"],
            "topic_code": item["topic_code"],
            "topic_title": item["title"],
            "score": item["score"],
            "max_score": item["max_score"],
            "percentage": item["percentage"],
            "course_key": item["course_key"],
            "unit_key": item["unit_key"],
            "lesson_key": item["lesson_key"],
            "lesson_title": item["lesson_title"],
            "reason": _reason(item["percentage"]),
        }
        for rank, item in enumerate(selected, 1)
    ]
    return topic_scores, recommendations
