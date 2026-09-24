"""Application service joining course pools, practice and learner progress."""

from __future__ import annotations

from pathlib import Path

from question_bank.practice import PracticeEngine, PracticeError
from question_bank.validation import validate_bank

from .course_catalogue import BANK_ROOT, CourseCatalogue
from .progress_service import ProgressService


class PracticeService:
    def __init__(
        self,
        repository_root: Path,
        database: Path,
        catalogue: CourseCatalogue,
        progress: ProgressService,
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
        self.progress = progress
        self.engine = PracticeEngine(
            database,
            report.questions,
            allow_drafts=allow_drafts,
        )

    def _sync(self, summary: dict) -> None:
        self.progress.sync_session(summary)

    @staticmethod
    def _creation_response(summary: dict) -> dict:
        return {
            "session_id": summary["session_id"],
            "status": summary["status"],
            "question_count": summary["question_count"],
            "lesson_key": summary["lesson_key"],
            "mode": summary["mode"],
            "development_drafts": summary["development_drafts"],
        }

    def create_lesson_session(
        self,
        *,
        lesson_key: str,
        mode: str,
        question_count: int | None,
        idempotency_key: str,
    ) -> dict:
        lesson = self.catalogue.lesson(lesson_key)
        active = self.progress.active_session(lesson_key)
        if active is not None:
            summary = self.engine.session_summary(active.session_id)
            self._sync(summary)
            if summary["status"] == "active":
                return self._creation_response(summary)

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
        created = self.engine.create_session(
            question_count=selected_count,
            ordered_question_keys=[item.question_key for item in pool.items],
            context={
                "lesson_key": lesson.stable_key,
                "mode": mode,
                "stages": {item.question_key: item.stage for item in pool.items},
            },
            idempotency_key=idempotency_key,
        )
        self.progress.attach_session(
            lesson.stable_key,
            lesson.revision,
            created["session_id"],
            created["question_count"],
        )
        return created

    def session(self, session_id: str) -> dict:
        summary = self.engine.session_summary(session_id)
        self._sync(summary)
        return summary

    def next_question(self, session_id: str) -> dict:
        response = self.engine.next_question(session_id)
        self._sync(response["session"])
        return response

    def submit_attempt(
        self,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        answers: dict[str, str],
        idempotency_key: str,
    ) -> dict:
        response = self.engine.submit_attempt(
            session_id=session_id,
            stable_key=question_key,
            revision=question_revision,
            answers=answers,
            idempotency_key=idempotency_key,
        )
        self._sync(self.engine.session_summary(session_id))
        return response

    def reveal_hint(
        self,
        *,
        session_id: str,
        question_key: str,
        stage: int,
    ) -> dict:
        return self.engine.reveal_hint(session_id, question_key, stage)

    def give_up(self, *, session_id: str, question_key: str) -> dict:
        response = self.engine.give_up(session_id, question_key)
        self._sync(self.engine.session_summary(session_id))
        return response
