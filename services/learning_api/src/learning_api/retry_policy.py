"""Pure 2/4/7/14-day spaced retry transition policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

Resolution = Literal[
    "clean_correct",
    "assisted_correct",
    "incorrect",
    "gave_up",
    "checkpoint_incorrect",
]


@dataclass(frozen=True, slots=True)
class RetryTransition:
    scheduled: bool
    due_at: datetime | None
    interval_days: int | None
    review_stage: int
    review_streak: int
    state: str
    resolution: Resolution


def transition_retry(
    *,
    mode: str,
    correct: bool,
    gave_up: bool = False,
    incorrect_attempts: int = 0,
    highest_hint_stage: int = 0,
    previous_interval_days: int | None = None,
    previous_review_stage: int = 0,
    previous_review_streak: int = 0,
    now: datetime | None = None,
) -> RetryTransition:
    """Return the next retry state without reading time or persistence implicitly."""

    instant = now or datetime.now(UTC)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)

    if gave_up:
        days, stage, streak, resolution = 2, 0, 0, "gave_up"
    elif mode == "checkpoint" and not correct:
        days, stage, streak, resolution = 2, 0, 0, "checkpoint_incorrect"
    elif not correct:
        return RetryTransition(
            scheduled=False,
            due_at=None,
            interval_days=previous_interval_days,
            review_stage=previous_review_stage,
            review_streak=0,
            state="attempting",
            resolution="incorrect",
        )
    elif mode != "retry_review":
        if incorrect_attempts or highest_hint_stage:
            days, stage, streak, resolution = 4, 0, 0, "assisted_correct"
        else:
            return RetryTransition(
                scheduled=False,
                due_at=None,
                interval_days=None,
                review_stage=0,
                review_streak=0,
                state="correct",
                resolution="clean_correct",
            )
    elif incorrect_attempts or highest_hint_stage:
        days = previous_interval_days or 2
        stage = previous_review_stage
        streak = 0
        resolution = "assisted_correct"
    else:
        next_stage = previous_review_stage + 1
        if next_stage == 1:
            days = 7
        elif next_stage == 2:
            days = 14
        else:
            return RetryTransition(
                scheduled=False,
                due_at=None,
                interval_days=None,
                review_stage=next_stage,
                review_streak=previous_review_streak + 1,
                state="correct",
                resolution="clean_correct",
            )
        stage = next_stage
        streak = previous_review_streak + 1
        resolution = "clean_correct"

    return RetryTransition(
        scheduled=True,
        due_at=instant + timedelta(days=days),
        interval_days=days,
        review_stage=stage,
        review_streak=streak,
        state="queued_for_retry",
        resolution=resolution,
    )
