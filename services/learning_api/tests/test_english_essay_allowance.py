from datetime import UTC, datetime

import pytest

from learning_api.english_essay_allowance import (
    EssayFeedbackActual,
    EssayFeedbackLimits,
    EssayFeedbackQuote,
    InMemoryEssayFeedbackAllowanceRepository,
)
from learning_api.english_essay_repository import EnglishEssayError

LEARNER = "learner-one"
SUBMISSION_ONE = "submission-one"
SUBMISSION_TWO = "submission-two"
NOVEMBER = datetime(2026, 11, 1, tzinfo=UTC)


class EligibleEssays:
    def get_submission(self, learner_id: str, submission_id: str):
        if learner_id != LEARNER or submission_id not in {
            SUBMISSION_ONE,
            SUBMISSION_TWO,
        }:
            raise EnglishEssayError("essay_submission_not_found", "Not found", 404)
        return {"submission_id": submission_id, "learner_id": learner_id}

    def get_self_review(self, learner_id: str, submission_id: str):
        self.get_submission(learner_id, submission_id)
        return {"submission_id": submission_id}


def limits(*, enabled: bool = True, monthly_feedback: int = 2):
    return EssayFeedbackLimits(
        enabled=enabled,
        monthly_feedback=monthly_feedback,
        monthly_cost_micros_sgd=2_000,
        academy_monthly_cost_micros_sgd=4_000,
        max_feedback_cost_micros_sgd=1_000,
    )


def reserve(repository, submission_id: str, key: str):
    return repository.reserve(
        LEARNER,
        submission_id,
        quote=EssayFeedbackQuote(max_cost_micros_sgd=1_000),
        limits=limits(),
        idempotency_key=key,
        request_id=f"request-{key}",
        provider_name="future-provider",
        model_name="future-model",
        policy_version="english-essay-feedback-v1",
        at=NOVEMBER,
    )


def test_disabled_allowance_fails_closed_without_exposing_costs():
    repository = InMemoryEssayFeedbackAllowanceRepository(EligibleEssays())
    snapshot = repository.allowance(LEARNER, limits(enabled=False), at=NOVEMBER)
    assert snapshot.enabled is False
    assert snapshot.monthly_feedback_remaining == 0
    assert snapshot.availability == "provider_not_released"

    with pytest.raises(EnglishEssayError, match="has not been released") as error:
        repository.reserve(
            LEARNER,
            SUBMISSION_ONE,
            quote=EssayFeedbackQuote(max_cost_micros_sgd=1_000),
            limits=limits(enabled=False),
            idempotency_key="disabled",
            request_id="request-disabled",
            provider_name="future-provider",
            model_name="future-model",
            policy_version="english-essay-feedback-v1",
            at=NOVEMBER,
        )
    assert error.value.status == 503


def test_reserve_commit_and_release_are_idempotent_and_auditable():
    repository = InMemoryEssayFeedbackAllowanceRepository(EligibleEssays())
    first = reserve(repository, SUBMISSION_ONE, "first")
    repeated = reserve(repository, SUBMISSION_ONE, "first")
    assert repeated.reservation_id == first.reservation_id
    assert repository.allowance(LEARNER, limits(), at=NOVEMBER).monthly_feedback_remaining == 1

    committed = repository.commit(
        first,
        EssayFeedbackActual(cost_micros_sgd=700),
        limits(),
        request_id="request-commit",
    )
    assert committed.monthly_feedback_remaining == 1

    second = reserve(repository, SUBMISSION_TWO, "second")
    exhausted = repository.allowance(LEARNER, limits(), at=NOVEMBER)
    assert exhausted.monthly_feedback_remaining == 0
    assert exhausted.availability == "allowance_exhausted"

    released = repository.release(
        second,
        limits(),
        request_id="request-release",
        reason="provider_unavailable",
    )
    assert released.monthly_feedback_remaining == 1
    assert [event["event_type"] for event in repository.events] == [
        "reserved",
        "committed",
        "reserved",
        "released",
    ]


def test_reservation_rejects_zero_cost_and_provider_overage():
    repository = InMemoryEssayFeedbackAllowanceRepository(EligibleEssays())
    with pytest.raises(EnglishEssayError, match="configured boundary"):
        repository.reserve(
            LEARNER,
            SUBMISSION_ONE,
            quote=EssayFeedbackQuote(max_cost_micros_sgd=0),
            limits=limits(),
            idempotency_key="zero",
            request_id="request-zero",
            provider_name="fixture",
            model_name="fixture",
            policy_version="fixture",
            at=NOVEMBER,
        )

    reservation = reserve(repository, SUBMISSION_ONE, "overage")
    with pytest.raises(EnglishEssayError, match="outside the reserved boundary"):
        repository.commit(
            reservation,
            EssayFeedbackActual(cost_micros_sgd=1_001),
            limits(),
            request_id="request-overage",
        )
    assert repository.reservations[reservation.reservation_id]["status"] == "reserved"
