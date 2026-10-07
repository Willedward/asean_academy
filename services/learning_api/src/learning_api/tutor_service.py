"""Grounded tutor orchestration with server-owned locks and cost boundaries."""

from __future__ import annotations

import re
from time import perf_counter

from .tutor_contracts import TutorBlock, TutorMode
from .tutor_provider import TutorProvider, TutorProviderError, TutorProviderRequest
from .tutor_repository import (
    QuotaSnapshot,
    TutorError,
    TutorLimits,
    TutorRepository,
    UsageActual,
)


class TutorService:
    def __init__(
        self,
        repository: TutorRepository,
        provider: TutorProvider,
        learner_id: str,
        *,
        limits: TutorLimits,
        model_policy_version: str,
        prompt_version: str,
    ):
        self.repository = repository
        self.provider = provider
        self.learner_id = learner_id
        self.limits = limits
        self.model_policy_version = model_policy_version
        self.prompt_version = prompt_version

    def create_session(
        self,
        *,
        practice_session_id: str,
        question_key: str,
        question_revision: int,
    ) -> dict:
        return self.repository.create_session(
            self.learner_id,
            practice_session_id=practice_session_id,
            question_key=question_key,
            question_revision=question_revision,
            model_policy_version=self.model_policy_version,
        )

    def session(self, session_id: str) -> dict:
        return self.repository.get_session(self.learner_id, session_id)

    def close(self, session_id: str) -> dict:
        return self.repository.close_session(self.learner_id, session_id)

    async def send_message(self, session_id: str, message: str, *, request_id: str) -> dict:
        grounding = self.repository.grounding(self.learner_id, session_id)
        mode = self._select_mode(message, grounding.answer_lock_state.solution_locked,
                                 grounding.incorrect_attempts)
        reservation = self.repository.reserve(
            self.learner_id,
            session_id,
            self.limits,
            request_id=request_id,
        )
        self.repository.append_message(
            session_id,
            role="student",
            mode=None,
            content={"blocks": [{"type": "text", "content": message}]},
        )
        request = TutorProviderRequest(
            mode=mode,
            learner_message=message,
            question_title=grounding.question_title,
            question_blocks=grounding.question_blocks,
            unlocked_hint_blocks=grounding.unlocked_hint_blocks,
            lesson_sections=grounding.lesson_sections,
            unlocked_solution_blocks=grounding.unlocked_solution_blocks,
            latest_attempt=grounding.latest_attempt,
            recent_messages=grounding.recent_messages,
            answer_locked=grounding.answer_lock_state.answer_locked,
            solution_locked=grounding.answer_lock_state.solution_locked,
            prompt_version=self.prompt_version,
            max_output_tokens=self.limits.max_output_tokens,
        )
        started = perf_counter()
        try:
            generated = await self.provider.generate(request)
        except TutorProviderError as exc:
            self.repository.release(
                reservation,
                request_id=request_id,
                reason="provider_unavailable",
            )
            raise TutorError(
                "tutor_provider_unavailable",
                "The AI tutor is temporarily unavailable. Authored hints and worked solutions still work.",
                503,
            ) from exc
        latency_ms = round((perf_counter() - started) * 1000)
        actual = UsageActual(
            input_tokens=generated.usage.input_tokens,
            output_tokens=generated.usage.output_tokens,
            cost_micros_sgd=generated.usage.cost_micros_sgd,
        )
        quota = self.repository.reconcile(
            reservation,
            actual,
            self.limits,
            request_id=request_id,
        )
        blocks = generated.blocks
        safety_outcome = "accepted"
        suggested_replies = list(generated.suggested_replies[:4])
        next_action = generated.recommended_next_action
        if grounding.answer_lock_state.answer_locked and self._likely_leakage(
            blocks, grounding.leakage_answers
        ):
            blocks = (
                TutorBlock(
                    type="text",
                    content=(
                        "I cannot reveal the final answer yet. Tell me which step you have tried, "
                        "and I will help you choose the next one."
                    ),
                ),
            )
            safety_outcome = "answer_leakage_blocked"
            suggested_replies = ["Give me a smaller hint.", "Explain the key idea again."]
            next_action = "Try the next step without revealing the final answer."
        content = {
            "blocks": [block.model_dump(mode="json") for block in blocks],
            "suggested_replies": suggested_replies,
            "recommended_next_action": next_action,
        }
        stored = self.repository.append_message(
            session_id,
            role="assistant",
            mode=mode,
            content=content,
            grounding_revision_ids=grounding.grounding_revision_ids,
            model_name=generated.model_name,
            prompt_version=self.prompt_version,
            safety_outcome=safety_outcome,
            latency_ms=latency_ms,
            token_usage={
                "input_tokens": actual.input_tokens,
                "output_tokens": actual.output_tokens,
                "total_tokens": actual.total_tokens,
                "cost_micros_sgd": actual.cost_micros_sgd,
            },
        )
        return {
            "session_id": session_id,
            "message": stored,
            "suggested_replies": suggested_replies,
            "recommended_next_action": next_action,
            "answer_lock_state": grounding.answer_lock_state.model_dump(),
            "quota": self._quota_dict(quota),
        }

    @staticmethod
    def _quota_dict(quota: QuotaSnapshot) -> dict:
        return {
            "daily_messages_remaining": quota.daily_messages_remaining,
            "daily_tokens_remaining": quota.daily_tokens_remaining,
            "monthly_cost_remaining_micros_sgd": quota.monthly_cost_remaining_micros_sgd,
            "resets_at": quota.resets_at,
        }

    @staticmethod
    def _select_mode(message: str, solution_locked: bool, incorrect_attempts: int) -> TutorMode:
        normalized = message.casefold()
        if not solution_locked and any(word in normalized for word in ("solution", "answer", "working")):
            return "solution_explanation"
        if any(phrase in normalized for phrase in ("don't understand", "dont understand", "still confused", "another way")):
            return "alternative_explanation"
        if "example" in normalized:
            return "analogous_example"
        if any(phrase in normalized for phrase in ("what does", "what is the question", "rephrase", "meaning")):
            return "clarify_question"
        if any(phrase in normalized for phrase in ("lesson", "revise", "review")):
            return "lesson_recommendation"
        if incorrect_attempts:
            return "diagnose_misconception"
        return "socratic_prompt"

    @staticmethod
    def _likely_leakage(blocks: tuple[TutorBlock, ...], answers: tuple[str, ...]) -> bool:
        for block in blocks:
            rendered = " ".join(block.content.casefold().split())
            compact = re.sub(r"\s+", "", rendered)
            for raw_answer in answers:
                answer = " ".join(str(raw_answer).casefold().split())
                answer_compact = re.sub(r"\s+", "", answer)
                if not answer_compact:
                    continue
                if block.type == "display_math" and compact.strip("$ ") == answer_compact.strip("$ "):
                    return True
                escaped = re.escape(answer)
                if re.search(rf"(?:final answer|answer is|answer:)\s*\$?{escaped}(?:\b|\$|$)", rendered):
                    return True
        return False
