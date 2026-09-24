"""Application service joining course pools to the deterministic practice engine."""

from __future__ import annotations

from pathlib import Path

from question_bank.practice import PracticeEngine, PracticeError
from question_bank.validation import validate_bank

from .course_catalogue import BANK_ROOT, CourseCatalogue


class PracticeService:
    def __init__(
        self,
        repository_root: Path,
        database: Path,
        catalogue: CourseCatalogue,
        *,
        allow_drafts: bool,
    ):
        report = validate_bank(repository_root / BANK_ROOT)
        if not report.valid:
            raise PracticeError(
                "question_bank_invalid",
                "The question bank failed validation and is temporarily unavailable.",
                503,
            )
        self.catalogue = catalogue
        self.engine = PracticeEngine(
            database,
            report.questions,
            allow_drafts=allow_drafts,
        )

    def create_lesson_session(
        self,
        *,
        lesson_key: str,
        mode: str,
        question_count: int | None,
        idempotency_key: str,
    ) -> dict:
        lesson = self.catalogue.lesson(lesson_key)
        pool = next(
            (
                candidate
                for candidate in self.catalogue.report.pools.pools
                if candidate.type == "lesson_practice"
                and candidate.lesson_key == lesson_key
            ),
            None,
        )
        if pool is None:
            raise PracticeError(
                "lesson_pool_missing",
                "Practice has not been configured for this lesson.",
                503,
            )
        selected_count = question_count or pool.expected_question_count
        if selected_count > pool.expected_question_count:
            raise PracticeError(
                "invalid_question_count",
                f"This lesson has {pool.expected_question_count} configured practice questions.",
            )
        return self.engine.create_session(
            question_count=selected_count,
            ordered_question_keys=[item.question_key for item in pool.items],
            context={
                "lesson_key": lesson.stable_key,
                "mode": mode,
                "stages": {item.question_key: item.stage for item in pool.items},
            },
            idempotency_key=idempotency_key,
        )

    def session(self, session_id: str) -> dict:
        return self.engine.session_summary(session_id)

    def next_question(self, session_id: str) -> dict:
        return self.engine.next_question(session_id)

    def submit_attempt(
        self,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        answers: dict[str, str],
        idempotency_key: str,
    ) -> dict:
        return self.engine.submit_attempt(
            session_id=session_id,
            stable_key=question_key,
            revision=question_revision,
            answers=answers,
            idempotency_key=idempotency_key,
        )

    def reveal_hint(
        self,
        *,
        session_id: str,
        question_key: str,
        stage: int,
    ) -> dict:
        return self.engine.reveal_hint(session_id, question_key, stage)

    def give_up(self, *, session_id: str, question_key: str) -> dict:
        return self.engine.give_up(session_id, question_key)
