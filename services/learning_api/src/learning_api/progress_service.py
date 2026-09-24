"""Application service for local learner progress and next-action decisions."""

from __future__ import annotations

from .course_catalogue import CourseCatalogue
from .course_contracts import CourseMapResponse
from .progress_repository import ProgressRepository


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

    def start_lesson(self, lesson_key: str) -> dict:
        lesson = self.catalogue.lesson(lesson_key)
        record = self.repository.start_lesson(
            self.learner_id,
            lesson.stable_key,
            lesson.revision,
        )
        return self._lesson_response(lesson, record)

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

    def active_session(self, lesson_key: str | None = None):
        return self.repository.active_session(self.learner_id, lesson_key)

    def sync_session(self, summary: dict) -> dict:
        return self.repository.sync_session(
            self.learner_id,
            summary,
            minimum_percentage=self.policy.minimum_eventual_correct_percentage,
        )

    def _lesson_response(self, lesson, record=None) -> dict:
        return {
            "lesson_key": lesson.stable_key,
            "lesson_title": lesson.title,
            "position": lesson.position,
            "state": record.state if record else "not_started",
            "question_count": record.question_count if record else 0,
            "resolved_count": record.resolved_count if record else 0,
            "correct_count": record.correct_count if record else 0,
            "gave_up_count": record.gave_up_count if record else 0,
            "eventual_correct_percentage": (
                record.eventual_correct_percentage if record else 0
            ),
            "checkpoint_passed": record.checkpoint_passed if record else False,
            "last_session_id": record.last_session_id if record else None,
            "updated_at": record.updated_at if record else None,
        }

    def progress(self) -> dict:
        report = self.catalogue.report
        records = {
            record.lesson_key: record
            for record in self.repository.lesson_progress(self.learner_id)
        }
        lessons = sorted(report.lessons, key=lambda lesson: lesson.position)
        return {
            "learner_id": self.learner_id,
            "course_key": report.course.stable_key,
            "proficiency_threshold": self.policy.minimum_eventual_correct_percentage,
            "checkpoint_required_for_mastery": self.policy.mastery_requires_checkpoint,
            "lessons": [
                self._lesson_response(lesson, records.get(lesson.stable_key))
                for lesson in lessons
            ],
        }

    def learning_home(self) -> dict:
        progress = self.progress()
        lesson_by_key = {
            lesson.stable_key: lesson for lesson in self.catalogue.report.lessons
        }
        active = self.active_session()
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
                "session_id": active.session_id,
            }
        else:
            retry = next(
                (
                    lesson
                    for lesson in progress["lessons"]
                    if lesson["state"] == "practice_completed"
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
            if retry is not None:
                action = {
                    "type": "retry_practice",
                    "title": f"Retry {retry['lesson_title']}",
                    "description": (
                        "Retry the lesson practice to resolve questions that "
                        "still need work."
                    ),
                    "href": f"/lessons/{retry['lesson_key']}",
                    "lesson_key": retry["lesson_key"],
                    "session_id": None,
                }
            elif in_progress is not None:
                action = {
                    "type": "continue_lesson",
                    "title": f"Continue {in_progress['lesson_title']}",
                    "description": "Return to the lesson and continue its practice.",
                    "href": f"/lessons/{in_progress['lesson_key']}",
                    "lesson_key": in_progress["lesson_key"],
                    "session_id": None,
                }
            else:
                first_incomplete = next(
                    (
                        lesson
                        for lesson in progress["lessons"]
                        if lesson["state"] not in {"proficient", "mastered"}
                    ),
                    None,
                )
                if first_incomplete is None:
                    action = {
                        "type": "checkpoint_pending",
                        "title": "Unit checkpoint is being prepared",
                        "description": (
                            "Every lesson is proficient. Mastery still requires "
                            "the reviewed unit checkpoint."
                        ),
                        "href": "/progress",
                        "lesson_key": None,
                        "session_id": None,
                    }
                elif first_incomplete["position"] == 1:
                    action = {
                        "type": "start_lesson",
                        "title": f"Start {first_incomplete['lesson_title']}",
                        "description": "Begin the first N1 lesson and its guided practice.",
                        "href": f"/lessons/{first_incomplete['lesson_key']}",
                        "lesson_key": first_incomplete["lesson_key"],
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
                        "session_id": None,
                    }
        return {
            "learner_id": self.learner_id,
            "course_key": progress["course_key"],
            "next_action": action,
            "unresolved_retry_count": sum(
                lesson["gave_up_count"] for lesson in progress["lessons"]
            ),
            "lessons": progress["lessons"],
        }

    def apply_to_course_map(self, course_map: CourseMapResponse) -> CourseMapResponse:
        states = {
            item["lesson_key"]: item["state"]
            for item in self.progress()["lessons"]
        }
        for unit in course_map.units:
            for lesson in unit.lessons:
                lesson.progress_state = states.get(lesson.stable_key, "not_started")
        return course_map
