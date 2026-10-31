"""Learner-safe projection of the server-owned essay feedback allowance."""

from __future__ import annotations

from .english_contracts import EnglishEssayFeedbackAllowanceResponse
from .english_essay_allowance import EssayFeedbackLimits


class EnglishEssayFeedbackAllowanceService:
    def __init__(self, repository, learner_id: str, limits: EssayFeedbackLimits):
        self.repository = repository
        self.learner_id = learner_id
        self.limits = limits

    def current(self) -> EnglishEssayFeedbackAllowanceResponse:
        snapshot = self.repository.allowance(self.learner_id, self.limits)
        return EnglishEssayFeedbackAllowanceResponse(
            live_feedback_available=(
                snapshot.enabled and snapshot.availability == "available"
            ),
            availability=snapshot.availability,
            monthly_feedback_limit=snapshot.monthly_feedback_limit,
            monthly_feedback_remaining=snapshot.monthly_feedback_remaining,
            resets_at=snapshot.resets_at,
        )
