"""Application service joining course pools, practice and learner progress."""

from __future__ import annotations

import hashlib
from pathlib import Path

from question_bank.practice import PracticeEngine, PracticeError
from question_bank.validation import validate_bank

from .course_catalogue import BANK_ROOT, CourseCatalogue
from .postgres_practice import PostgresPracticeEngine
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
        database_url: str | None = None,
    ):
        report = validate_bank(repository_root / BANK_ROOT)
        if not report.valid:
            raise PracticeError(
                "question_bank_invalid",
                "The question bank failed validation and is temporarily unavailable.",
                503,
            )
        self.questions = report.questions
        self.catalogue = catalogue
        self.progress = progress
        self.postgres = database_url is not None
        if database_url is not None:
            self.engine = PostgresPracticeEngine(
                database_url,
                report.questions,
                progress.learner_id,
                allow_drafts=allow_drafts,
            )
        else:
            self.engine = PracticeEngine(
                database,
                report.questions,
                allow_drafts=allow_drafts,
            )

    def _owned_session(self, session_id: str) -> None:
        if (
            self.progress.session(session_id) is None
            and self.progress.checkpoint_session(session_id) is None
        ):
            raise PracticeError(
                "session_not_found", "Practice session was not found.", 404
            )

    def _session_idempotency_key(self, key: str) -> str:
        if self.postgres:
            return key
        return hashlib.sha256(
            f"{self.progress.learner_id}:{key}".encode()
        ).hexdigest()

    def _sync(self, summary: dict) -> None:
        self.progress.sync_session(summary)

    @staticmethod
    def _creation_response(summary: dict) -> dict:
        return {
            "session_id": summary["session_id"],
            "status": summary["status"],
            "question_count": summary["question_count"],
            "lesson_key": summary.get("lesson_key"),
            "unit_key": summary.get("unit_key"),
            "mode": summary["mode"],
            "development_drafts": summary["development_drafts"],
        }

    def _lesson_pool(self, lesson_key: str):
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
        return pool

    def _unit(self, unit_key: str):
        course = self.catalogue.report.course
        self.catalogue.course_map(course.stable_key)
        unit = next(
            (candidate for candidate in course.units if candidate.stable_key == unit_key),
            None,
        )
        if unit is None:
            raise PracticeError("unit_not_found", "The requested unit was not found.", 404)
        return unit

    def create_session(
        self,
        *,
        lesson_key: str | None,
        unit_key: str | None,
        mode: str,
        question_count: int | None,
        idempotency_key: str,
    ) -> dict:
        if mode == "checkpoint":
            assert unit_key is not None
            return self.create_checkpoint_session(
                unit_key=unit_key,
                question_count=question_count,
                idempotency_key=idempotency_key,
            )
        assert lesson_key is not None
        return self.create_lesson_session(
            lesson_key=lesson_key,
            mode=mode,
            question_count=question_count,
            idempotency_key=idempotency_key,
        )

    def create_lesson_session(
        self,
        *,
        lesson_key: str,
        mode: str,
        question_count: int | None,
        idempotency_key: str,
    ) -> dict:
        if mode not in {"guided_practice", "retry_review"}:
            raise PracticeError("invalid_practice_mode", "Unsupported lesson practice mode.")
        lesson = self.catalogue.lesson(lesson_key)
        self.progress.assert_lesson_unlocked(lesson_key)
        active = self.progress.active_session(lesson_key)
        if active is not None:
            self.progress.attach_session(
                lesson.stable_key,
                lesson.revision,
                active.session_id,
                active.question_count,
            )
            summary = self.engine.session_summary(active.session_id)
            self._sync(summary)
            if summary["status"] == "active":
                return self._creation_response(summary)

        pool = self._lesson_pool(lesson_key)
        pool_keys = [item.question_key for item in pool.items]
        if mode == "retry_review":
            lesson_keys = [
                question.stable_key
                for question in self.questions
                if question.primary_outcome in lesson.outcomes
            ]
            ordered_keys = self.engine.retry_question_keys(lesson_keys)
            if not ordered_keys:
                raise PracticeError(
                    "retry_queue_empty",
                    "This lesson has no unresolved questions to retry.",
                    409,
                )
            selected_count = question_count or len(ordered_keys)
            stages = {key: "adaptive" for key in ordered_keys}
            selection_reason = "required_retry"
        else:
            ordered_keys = pool_keys
            selected_count = question_count or pool.expected_question_count
            stages = {item.question_key: item.stage for item in pool.items}
            selection_reason = "configured_lesson_pool"
        if selected_count > len(ordered_keys):
            raise PracticeError(
                "invalid_question_count",
                f"This session has {len(ordered_keys)} available questions.",
            )
        created = self.engine.create_session(
            question_count=selected_count,
            ordered_question_keys=ordered_keys,
            context={
                "lesson_key": lesson.stable_key,
                "mode": mode,
                "stages": stages,
                "selection_reason": selection_reason,
            },
            idempotency_key=self._session_idempotency_key(idempotency_key),
        )
        self.progress.attach_session(
            lesson.stable_key,
            lesson.revision,
            created["session_id"],
            created["question_count"],
        )
        return created

    def create_checkpoint_session(
        self,
        *,
        unit_key: str,
        question_count: int | None,
        idempotency_key: str,
    ) -> dict:
        unit = self._unit(unit_key)
        status = self.progress.checkpoint_status(unit_key)
        latest = self.progress.latest_checkpoint_session(unit_key)
        if latest is not None and latest.status == "active":
            summary = self.engine.session_summary(latest.session_id)
            self._sync(summary)
            return self._creation_response(summary)
        if status["state"] == "passed":
            raise PracticeError(
                "checkpoint_already_passed",
                "This unit checkpoint has already been passed.",
                409,
            )
        if not status["available"]:
            raise PracticeError(
                "checkpoint_locked",
                "Every lesson in this unit must be proficient before the checkpoint.",
                409,
            )
        pool = next(
            (
                candidate
                for candidate in self.catalogue.report.pools.pools
                if candidate.type == "unit_checkpoint"
            ),
            None,
        )
        if pool is None:
            raise PracticeError(
                "checkpoint_pool_missing",
                "The checkpoint question pool has not been configured.",
                503,
            )
        selected_count = question_count or unit.checkpoint_question_count
        if selected_count != unit.checkpoint_question_count:
            raise PracticeError(
                "invalid_checkpoint_question_count",
                f"This checkpoint requires exactly {unit.checkpoint_question_count} questions.",
            )
        if selected_count > pool.expected_question_count:
            raise PracticeError(
                "checkpoint_pool_incomplete",
                "The checkpoint pool does not contain enough questions.",
                503,
            )
        created = self.engine.create_session(
            question_count=selected_count,
            ordered_question_keys=[item.question_key for item in pool.items],
            context={
                "unit_key": unit.stable_key,
                "mode": "checkpoint",
                "stages": {item.question_key: item.stage for item in pool.items},
                "selection_reason": "configured_checkpoint_pool",
            },
            idempotency_key=self._session_idempotency_key(idempotency_key),
        )
        self.progress.attach_checkpoint_session(
            unit.stable_key,
            created["session_id"],
            created["question_count"],
        )
        return created

    def session(self, session_id: str) -> dict:
        self._owned_session(session_id)
        summary = self.engine.session_summary(session_id)
        self._sync(summary)
        return summary

    def next_question(self, session_id: str) -> dict:
        self._owned_session(session_id)
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
        self._owned_session(session_id)
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
        self._owned_session(session_id)
        return self.engine.reveal_hint(session_id, question_key, stage)

    def give_up(self, *, session_id: str, question_key: str) -> dict:
        self._owned_session(session_id)
        response = self.engine.give_up(session_id, question_key)
        self._sync(self.engine.session_summary(session_id))
        return response
