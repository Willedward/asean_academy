from datetime import UTC, datetime, timedelta

from learning_api.retry_policy import transition_retry

NOW = datetime(2026, 9, 29, 4, 0, tzinfo=UTC)


def test_give_up_and_checkpoint_miss_return_in_two_days():
    gave_up = transition_retry(mode="guided_practice", correct=False, gave_up=True, now=NOW)
    missed = transition_retry(mode="checkpoint", correct=False, now=NOW)
    assert gave_up.due_at == missed.due_at == NOW + timedelta(days=2)
    assert gave_up.state == missed.state == "queued_for_retry"


def test_assisted_initial_success_returns_in_four_days():
    result = transition_retry(
        mode="guided_practice", correct=True, incorrect_attempts=1, now=NOW
    )
    assert result.due_at == NOW + timedelta(days=4)
    assert result.interval_days == 4


def test_clean_reviews_progress_through_seven_and_fourteen_days_then_clear():
    first = transition_retry(mode="retry_review", correct=True, now=NOW)
    second = transition_retry(
        mode="retry_review",
        correct=True,
        previous_interval_days=first.interval_days,
        previous_review_stage=first.review_stage,
        previous_review_streak=first.review_streak,
        now=NOW,
    )
    third = transition_retry(
        mode="retry_review",
        correct=True,
        previous_interval_days=second.interval_days,
        previous_review_stage=second.review_stage,
        previous_review_streak=second.review_streak,
        now=NOW,
    )
    assert first.due_at == NOW + timedelta(days=7)
    assert second.due_at == NOW + timedelta(days=14)
    assert third.scheduled is False
    assert third.state == "correct"


def test_assisted_review_repeats_current_gap_and_resets_streak():
    result = transition_retry(
        mode="retry_review",
        correct=True,
        highest_hint_stage=1,
        previous_interval_days=7,
        previous_review_stage=1,
        previous_review_streak=1,
        now=NOW,
    )
    assert result.due_at == NOW + timedelta(days=7)
    assert result.review_stage == 1
    assert result.review_streak == 0


def test_wrong_review_attempt_preserves_its_gap_for_the_eventual_resolution():
    result = transition_retry(
        mode="retry_review",
        correct=False,
        previous_interval_days=7,
        previous_review_stage=1,
        previous_review_streak=1,
        now=NOW,
    )
    assert result.state == "attempting"
    assert result.interval_days == 7
    assert result.review_stage == 1
