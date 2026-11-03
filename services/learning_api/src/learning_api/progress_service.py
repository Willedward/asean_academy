"""Application service for learner progress, checkpoints and next actions."""

from __future__ import annotations

from question_bank.checking import check_answer
from question_bank.course_models import ActiveRecallSection

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

    @staticmethod
    def _policy(report):
        return report.course.mastery_policies[0]

    def _active_reports(self) -> list:
        """Return the learner's active courses in catalogue order.

        A learner with no enrolment in the catalogue is the local development learner.
        Production routes reach this service only through the enrolled-learner check.
        """
        active = set(self.repository.active_course_keys(self.learner_id))
        reports = self.catalogue.reports
        return [report for key, report in reports.items() if key in active] or list(
            reports.values()
        )

    def _owned_unit(self, unit_key: str):
        report = self.catalogue.report_for_unit(unit_key)
        if report is None:
            raise ProgressError("unit_not_found", "The requested unit was not found.", 404)
        unit = next(
            candidate for candidate in report.course.units if candidate.stable_key == unit_key
        )
        return report, unit

    def _authored_lesson_model(self, lesson_key: str):
        report = self.catalogue.report_for_lesson(lesson_key)
        if report is None:
            return None
        return next(
            candidate for candidate in report.lessons if candidate.stable_key == lesson_key
        )

    def _retry_counts(self) -> dict[str, int]:
        unresolved = set(
            self.repository.unresolved_question_keys(self.learner_id)
        )
        counts = {
            lesson.stable_key: 0
            for report in self.catalogue.reports.values()
            for lesson in report.lessons
        }
        for report in self.catalogue.reports.values():
            for question in report.questions:
                if question.stable_key not in unresolved:
                    continue
                manifest = next(
                    (
                        candidate
                        for candidate in report.pools.manifests
                        if candidate.bank_key == question.bank_key
                    ),
                    None,
                )
                unit = (
                    next(
                        (
                            candidate
                            for candidate in report.course.units
                            if candidate.stable_key == manifest.unit_key
                        ),
                        None,
                    )
                    if manifest is not None
                    else None
                )
                lesson_keys = {
                    candidate.stable_key for candidate in unit.lessons
                } if unit is not None else set()
                lesson = next(
                    (
                        candidate
                        for candidate in report.lessons
                        if candidate.stable_key in lesson_keys
                        and question.primary_outcome in candidate.outcomes
                    ),
                    None,
                )
                if lesson is not None:
                    counts[lesson.stable_key] += 1
        return counts

    def assert_lesson_unlocked(self, lesson_key: str) -> None:
        lesson = self._authored_lesson_model(lesson_key)
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

    def _authored_lesson(self, lesson_key: str):
        self.catalogue.lesson(lesson_key)
        lesson = self._authored_lesson_model(lesson_key)
        if lesson is None:
            raise ProgressError("lesson_not_found", "The requested lesson was not found.", 404)
        self.assert_lesson_unlocked(lesson_key)
        return lesson

    @staticmethod
    def _section(lesson, section_key: str):
        section = next(
            (item for item in lesson.sections if item.stable_key == section_key),
            None,
        )
        if section is None:
            raise ProgressError(
                "lesson_section_not_found",
                "The requested lesson section was not found.",
                404,
            )
        return section

    def _section_progress_response(self, lesson) -> dict:
        valid_keys = {section.stable_key for section in lesson.sections}
        completed = [
            key
            for key in self.repository.completed_section_keys(
                self.learner_id,
                lesson.stable_key,
                lesson.revision,
            )
            if key in valid_keys
        ]
        return {
            "lesson_key": lesson.stable_key,
            "lesson_revision": lesson.revision,
            "total_sections": len(lesson.sections),
            "completed_count": len(completed),
            "completed_section_keys": completed,
        }

    def section_progress(self, lesson_key: str) -> dict:
        lesson = self._authored_lesson(lesson_key)
        return self._section_progress_response(lesson)

    def set_section_completion(
        self,
        lesson_key: str,
        section_key: str,
        *,
        completed: bool,
    ) -> dict:
        lesson = self._authored_lesson(lesson_key)
        section = self._section(lesson, section_key)
        if completed and isinstance(section, ActiveRecallSection):
            raise ProgressError(
                "active_recall_answer_required",
                "Answer this recall check correctly to complete the section.",
                409,
            )
        self.repository.start_lesson(
            self.learner_id,
            lesson.stable_key,
            lesson.revision,
        )
        self.repository.set_section_completion(
            self.learner_id,
            lesson.stable_key,
            lesson.revision,
            section.stable_key,
            completed,
        )
        return self._section_progress_response(lesson)

    def check_active_recall(
        self,
        lesson_key: str,
        section_key: str,
        *,
        answer: str,
    ) -> dict:
        lesson = self._authored_lesson(lesson_key)
        section = self._section(lesson, section_key)
        if not isinstance(section, ActiveRecallSection):
            raise ProgressError(
                "active_recall_required",
                "The requested section is not an active-recall check.",
                409,
            )
        checked = check_answer(section.response, answer)
        if checked["correct"]:
            self.repository.start_lesson(
                self.learner_id,
                lesson.stable_key,
                lesson.revision,
            )
            self.repository.set_section_completion(
                self.learner_id,
                lesson.stable_key,
                lesson.revision,
                section.stable_key,
                True,
            )
        return {
            "correct": checked["correct"],
            "error": checked["error"],
            "feedback": (
                [block.model_dump(mode="json") for block in section.feedback]
                if checked["correct"]
                else []
            ),
            "progress": self._section_progress_response(lesson),
        }

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
            report, unit = self._owned_unit(summary["unit_key"])
            policy = self._policy(report)
            return self.repository.sync_checkpoint(
                self.learner_id,
                summary,
                lesson_keys=[lesson.stable_key for lesson in unit.lessons],
                passing_percentage=policy.checkpoint_passing_percentage,
                policy_key=policy.key,
            )
        # A session without a known lesson changes no lesson record, so the first
        # course's policy is only a placeholder for it.
        report = self.catalogue.report_for_lesson(summary.get("lesson_key") or "")
        policy = self._policy(report or next(iter(self.catalogue.reports.values())))
        return self.repository.sync_session(
            self.learner_id,
            summary,
            minimum_percentage=policy.minimum_eventual_correct_percentage,
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
            "course_key": lesson.course_key,
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
        report, unit = self._owned_unit(unit_key)
        policy = self._policy(report)
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
            "course_key": report.course.stable_key,
            "unit_key": unit_key,
            "state": state,
            "available": available and state != "passed",
            "question_count": unit.checkpoint_question_count,
            "passing_percentage": policy.checkpoint_passing_percentage,
            "last_session_id": latest.session_id if latest else None,
            "last_percentage": latest.percentage if latest else None,
        }

    def _lesson_responses(self, reports: list) -> list[dict]:
        records = {
            record.lesson_key: record
            for record in self.repository.lesson_progress(self.learner_id)
        }
        retry_counts = self._retry_counts()
        responses = []
        for report in reports:
            unit_positions = {
                unit.stable_key: unit.position for unit in report.course.units
            }
            lessons = sorted(
                report.lessons,
                key=lambda lesson: (unit_positions[lesson.unit_key], lesson.position),
            )
            for lesson in lessons:
                unlocked = all(
                    records.get(key) is not None
                    and records[key].state in {"proficient", "mastered"}
                    for key in lesson.prerequisite_lessons
                )
                responses.append(
                    self._lesson_response(
                        lesson,
                        records.get(lesson.stable_key),
                        unlocked=unlocked,
                        retry_question_count=retry_counts[lesson.stable_key],
                    )
                )
        return responses

    def _checkpoint_responses(self, reports: list) -> list[dict]:
        return [
            self.checkpoint_status(unit.stable_key)
            for report in reports
            for unit in report.course.units
        ]

    def _course_summaries(self, reports: list) -> list[dict]:
        return [
            {
                "course_key": report.course.stable_key,
                "course_revision": report.course.revision,
                "title": report.course.title,
                "school_level": report.course.school_level,
                "proficiency_threshold": (
                    self._policy(report).minimum_eventual_correct_percentage
                ),
            }
            for report in reports
        ]

    def progress(self) -> dict:
        reports = self._active_reports()
        first_policy = self._policy(reports[0])
        scheduled_retry_count, next_retry_due_at = self.repository.retry_schedule(
            self.learner_id
        )
        return {
            "learner_id": self.learner_id,
            "course_key": reports[0].course.stable_key,
            "courses": self._course_summaries(reports),
            "proficiency_threshold": first_policy.minimum_eventual_correct_percentage,
            "checkpoint_required_for_mastery": first_policy.mastery_requires_checkpoint,
            "scheduled_retry_count": scheduled_retry_count,
            "next_retry_due_at": next_retry_due_at,
            "lessons": self._lesson_responses(reports),
            "checkpoints": self._checkpoint_responses(reports),
        }

    def learning_home(self) -> dict:
        progress = self.progress()
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
            lesson = self._authored_lesson_model(active.lesson_key)
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
            _, unit = self._owned_unit(active_checkpoint["unit_key"])
            action = {
                "type": "resume_checkpoint",
                "title": f"Resume the {unit.topic_code} checkpoint",
                "description": "Continue the unit checkpoint from your last question.",
                "href": f"/checkpoints/{active_checkpoint['last_session_id']}",
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
                _, unit = self._owned_unit(checkpoint["unit_key"])
                action = {
                    "type": "start_checkpoint",
                    "title": f"Start the {unit.topic_code} checkpoint",
                    "description": "Complete the checkpoint to turn proficiency into mastery.",
                    "href": "/progress#checkpoint-title",
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
                        "title": "Course mastery complete",
                        "description": "You passed every checkpoint and mastered this course.",
                        "href": "/progress",
                        "lesson_key": None,
                        "unit_key": None,
                        "session_id": None,
                    }
                elif first_incomplete["position"] == 1:
                    action = {
                        "type": "start_lesson",
                        "title": f"Start {first_incomplete['lesson_title']}",
                        "description": "Begin this lesson and its guided practice.",
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
            "courses": progress["courses"],
            "next_action": action,
            "unresolved_retry_count": sum(
                lesson["retry_question_count"] for lesson in progress["lessons"]
            ),
            "scheduled_retry_count": progress["scheduled_retry_count"],
            "next_retry_due_at": progress["next_retry_due_at"],
            "lessons": progress["lessons"],
            "checkpoints": progress["checkpoints"],
        }

    def apply_to_course_map(self, course_map: CourseMapResponse) -> CourseMapResponse:
        report = next(
            (
                candidate
                for candidate in self._active_reports()
                if candidate.course.stable_key == course_map.stable_key
            ),
            None,
        )
        if report is None:
            return course_map
        lesson_progress = {
            item["lesson_key"]: item for item in self._lesson_responses([report])
        }
        checkpoint_progress = {
            item["unit_key"]: item for item in self._checkpoint_responses([report])
        }
        for unit in course_map.units:
            unit.checkpoint_available = checkpoint_progress[unit.stable_key]["available"]
            for lesson in unit.lessons:
                state = lesson_progress[lesson.stable_key]
                lesson.progress_state = state["state"]
                lesson.unlocked = state["unlocked"]
                lesson.unlock_reason = state["unlock_reason"]
        return course_map
