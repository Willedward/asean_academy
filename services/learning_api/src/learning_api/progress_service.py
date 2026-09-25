"""Application service for learner progress, checkpoints and next actions."""

from __future__ import annotations

from .course_catalogue import CourseCatalogue
from .course_contracts import CourseMapResponse
from .progress_repository import ProgressError, ProgressRepository


class ProgressService:
    def __init__(
        self,
        catalogue: CourseCatalogue,
        repository: ProgressRepository,
        learner_id: str,
    ):
        self.catalogue = catalogue
        self.repository = repository
        self.learner_id = learner_id

    @property
    def policy(self):
        course = self.catalogue.report.course
        return course.mastery_policies[0]

    def _unit(self, unit_key: str):
        unit = next(
            (
                candidate
                for candidate in self.catalogue.report.course.units
                if candidate.stable_key == unit_key
            ),
            None,
        )
        if unit is None:
            raise ProgressError("unit_not_found", "The requested unit was not found.", 404)
        return unit

    def _retry_counts(self) -> dict[str, int]:
        unresolved = set(
            self.repository.unresolved_question_keys(self.learner_id)
        )
        counts = {lesson.stable_key: 0 for lesson in self.catalogue.report.lessons}
        for question in self.catalogue.questions:
            if question.stable_key not in unresolved:
                continue
            lesson = next(
                (
                    candidate
                    for candidate in self.catalogue.report.lessons
                    if question.primary_outcome in candidate.outcomes
                ),
                None,
            )
            if lesson is not None:
                counts[lesson.stable_key] += 1
        return counts

    def assert_lesson_unlocked(self, lesson_key: str) -> None:
        lesson = next(
            (
                candidate
                for candidate in self.catalogue.report.lessons
                if candidate.stable_key == lesson_key
            ),
            None,
        )
        if lesson is None:
            raise ProgressError("lesson_not_found", "The requested lesson was not found.", 404)
        records = {
            record.lesson_key: record
            for record in self.repository.lesson_progress(self.learner_id)
        }
        if any(
            records.get(key) is None
            or records[key].state not in {"proficient", "mastered"}
            for key in lesson.prerequisite_lessons
        ):
            raise ProgressError(
                "lesson_locked",
                "Complete the prerequisite lesson practice before starting this lesson.",
                409,
            )

    def start_lesson(self, lesson_key: str) -> dict:
        lesson = self.catalogue.lesson(lesson_key)
        self.assert_lesson_unlocked(lesson_key)
        record = self.repository.start_lesson(
            self.learner_id,
            lesson.stable_key,
            lesson.revision,
        )
        return self._lesson_response(
            lesson,
            record,
            unlocked=True,
            retry_question_count=self._retry_counts()[lesson.stable_key],
        )

    def attach_session(
        self,
        lesson_key: str,
        lesson_revision: int,
        session_id: str,
        question_count: int,
    ) -> None:
        self.repository.attach_session(
            self.learner_id,
            lesson_key,
            lesson_revision,
            session_id,
            question_count,
        )

    def attach_checkpoint_session(
        self,
        unit_key: str,
        session_id: str,
        question_count: int,
    ) -> None:
        self.repository.attach_checkpoint_session(
            self.learner_id,
            unit_key,
            session_id,
            question_count,
        )

    def session(self, session_id: str):
        return self.repository.session(self.learner_id, session_id)

    def checkpoint_session(self, session_id: str):
        return self.repository.checkpoint_session(self.learner_id, session_id)

    def active_session(self, lesson_key: str | None = None):
        return self.repository.active_session(self.learner_id, lesson_key)

    def latest_checkpoint_session(self, unit_key: str):
        return self.repository.latest_checkpoint_session(self.learner_id, unit_key)

    def sync_session(self, summary: dict):
        if summary.get("mode") == "checkpoint":
            unit = self._unit(summary["unit_key"])
            return self.repository.sync_checkpoint(
                self.learner_id,
                summary,
                lesson_keys=[lesson.stable_key for lesson in unit.lessons],
                passing_percentage=self.policy.checkpoint_passing_percentage,
                policy_key=self.policy.key,
            )
        return self.repository.sync_session(
            self.learner_id,
            summary,
            minimum_percentage=self.policy.minimum_eventual_correct_percentage,
        )

    def _lesson_response(
        self,
        lesson,
        record=None,
        *,
        unlocked: bool,
        retry_question_count: int = 0,
    ) -> dict:
        return {
            "lesson_key": lesson.stable_key,
            "lesson_title": lesson.title,
            "position": lesson.position,
            "state": record.state if record else "not_started",
            "unlocked": unlocked,
            "unlock_reason": None if unlocked else "prerequisite_not_proficient",
            "question_count": record.question_count if record else 0,
            "resolved_count": record.resolved_count if record else 0,
            "correct_count": record.correct_count if record else 0,
            "gave_up_count": record.gave_up_count if record else 0,
            "retry_question_count": retry_question_count,
            "eventual_correct_percentage": (
                record.eventual_correct_percentage if record else 0
            ),
            "checkpoint_passed": record.checkpoint_passed if record else False,
            "last_session_id": record.last_session_id if record else None,
            "updated_at": record.updated_at if record else None,
        }

    def checkpoint_status(self, unit_key: str) -> dict:
        unit = self._unit(unit_key)
        records = {
            record.lesson_key: record
            for record in self.repository.lesson_progress(self.learner_id)
        }
        lesson_keys = [lesson.stable_key for lesson in unit.lessons]
        passed = bool(lesson_keys) and all(
            records.get(key) is not None and records[key].checkpoint_passed
            for key in lesson_keys
        )
        available = bool(lesson_keys) and all(
            records.get(key) is not None
            and records[key].state in {"proficient", "mastered"}
            for key in lesson_keys
        )
        latest = self.latest_checkpoint_session(unit_key)
        if passed:
            state = "passed"
        elif latest is not None and latest.status == "active":
            state = "in_progress"
        elif available:
            state = "available"
        else:
            state = "locked"
        return {
            "unit_key": unit_key,
            "state": state,
            "available": available and state != "passed",
            "question_count": unit.checkpoint_question_count,
            "passing_percentage": self.policy.checkpoint_passing_percentage,
            "last_session_id": latest.session_id if latest else None,
            "last_percentage": latest.percentage if latest else None,
        }

    def progress(self) -> dict:
        report = self.catalogue.report
        records = {
            record.lesson_key: record
            for record in self.repository.lesson_progress(self.learner_id)
        }
        lessons = sorted(report.lessons, key=lambda lesson: lesson.position)
        retry_counts = self._retry_counts()
        lesson_responses = []
        for lesson in lessons:
            unlocked = all(
                records.get(key) is not None
                and records[key].state in {"proficient", "mastered"}
                for key in lesson.prerequisite_lessons
            )
            lesson_responses.append(
                self._lesson_response(
                    lesson,
                    records.get(lesson.stable_key),
                    unlocked=unlocked,
                    retry_question_count=retry_counts[lesson.stable_key],
                )
            )
        return {
            "learner_id": self.learner_id,
            "course_key": report.course.stable_key,
            "proficiency_threshold": self.policy.minimum_eventual_correct_percentage,
            "checkpoint_required_for_mastery": self.policy.mastery_requires_checkpoint,
            "lessons": lesson_responses,
            "checkpoints": [
                self.checkpoint_status(unit.stable_key)
                for unit in report.course.units
            ],
        }

    def learning_home(self) -> dict:
        progress = self.progress()
        lesson_by_key = {
            lesson.stable_key: lesson for lesson in self.catalogue.report.lessons
        }
        active = self.active_session()
        active_checkpoint = next(
            (
                checkpoint
                for checkpoint in progress["checkpoints"]
                if checkpoint["state"] == "in_progress"
            ),
            None,
        )
        if active is not None:
            lesson = lesson_by_key[active.lesson_key]
            action = {
                "type": "resume_practice",
                "title": f"Resume {lesson.title}",
                "description": (
                    f"Continue question {active.resolved_count + 1} "
                    f"of {active.question_count}."
                ),
                "href": f"/practice/{active.session_id}",
                "lesson_key": lesson.stable_key,
                "unit_key": None,
                "session_id": active.session_id,
            }
        elif active_checkpoint is not None:
            action = {
                "type": "resume_checkpoint",
                "title": "Resume the N1 checkpoint",
                "description": "Continue the unit checkpoint from your last question.",
                "href": f"/practice/{active_checkpoint['last_session_id']}",
                "lesson_key": None,
                "unit_key": active_checkpoint["unit_key"],
                "session_id": active_checkpoint["last_session_id"],
            }
        else:
            retry = next(
                (
                    lesson
                    for lesson in progress["lessons"]
                    if lesson["retry_question_count"] > 0
                    and lesson["state"] != "mastered"
                ),
                None,
            )
            in_progress = next(
                (
                    lesson
                    for lesson in progress["lessons"]
                    if lesson["state"] == "in_progress"
                ),
                None,
            )
            checkpoint = next(
                (
                    item
                    for item in progress["checkpoints"]
                    if item["state"] == "available"
                ),
                None,
            )
            if retry is not None:
                action = {
                    "type": "retry_practice",
                    "title": f"Retry {retry['lesson_title']}",
                    "description": "Review the questions that still need work.",
                    "href": f"/lessons/{retry['lesson_key']}",
                    "lesson_key": retry["lesson_key"],
                    "unit_key": None,
                    "session_id": None,
                }
            elif in_progress is not None:
                action = {
                    "type": "continue_lesson",
                    "title": f"Continue {in_progress['lesson_title']}",
                    "description": "Return to the lesson and continue its practice.",
                    "href": f"/lessons/{in_progress['lesson_key']}",
                    "lesson_key": in_progress["lesson_key"],
                    "unit_key": None,
                    "session_id": None,
                }
            elif checkpoint is not None:
                action = {
                    "type": "start_checkpoint",
                    "title": "Start the N1 checkpoint",
                    "description": "Complete the checkpoint to turn proficiency into mastery.",
                    "href": "/progress",
                    "lesson_key": None,
                    "unit_key": checkpoint["unit_key"],
                    "session_id": None,
                }
            else:
                first_incomplete = next(
                    (
                        lesson
                        for lesson in progress["lessons"]
                        if lesson["state"] not in {"proficient", "mastered"}
                        and lesson["unlocked"]
                    ),
                    None,
                )
                if first_incomplete is None:
                    action = {
                        "type": "course_complete",
                        "title": "N1 mastery complete",
                        "description": "You passed the checkpoint and mastered this unit.",
                        "href": "/progress",
                        "lesson_key": None,
                        "unit_key": None,
                        "session_id": None,
                    }
                elif first_incomplete["position"] == 1:
                    action = {
                        "type": "start_lesson",
                        "title": f"Start {first_incomplete['lesson_title']}",
                        "description": "Begin the first N1 lesson and its guided practice.",
                        "href": f"/lessons/{first_incomplete['lesson_key']}",
                        "lesson_key": first_incomplete["lesson_key"],
                        "unit_key": None,
                        "session_id": None,
                    }
                else:
                    action = {
                        "type": "content_pending",
                        "title": f"Next: {first_incomplete['lesson_title']}",
                        "description": (
                            "The next lesson shell exists, but its reviewed learning "
                            "material is still being prepared."
                        ),
                        "href": f"/lessons/{first_incomplete['lesson_key']}",
                        "lesson_key": first_incomplete["lesson_key"],
                        "unit_key": None,
                        "session_id": None,
                    }
        return {
            "learner_id": self.learner_id,
            "course_key": progress["course_key"],
            "next_action": action,
            "unresolved_retry_count": sum(
                lesson["retry_question_count"] for lesson in progress["lessons"]
            ),
            "lessons": progress["lessons"],
            "checkpoints": progress["checkpoints"],
        }

    def apply_to_course_map(self, course_map: CourseMapResponse) -> CourseMapResponse:
        progress = self.progress()
        lesson_progress = {item["lesson_key"]: item for item in progress["lessons"]}
        checkpoint_progress = {
            item["unit_key"]: item for item in progress["checkpoints"]
        }
        for unit in course_map.units:
            unit.checkpoint_available = checkpoint_progress[unit.stable_key]["available"]
            for lesson in unit.lessons:
                state = lesson_progress[lesson.stable_key]
                lesson.progress_state = state["state"]
                lesson.unlocked = state["unlocked"]
                lesson.unlock_reason = state["unlock_reason"]
        return course_map
