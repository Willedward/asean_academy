"""Server-owned routing and deterministic marking for English diagnostics."""

from __future__ import annotations

from uuid import uuid4

from question_bank.english_checking import check_english_answer

from .english_diagnostic_repository import EnglishDiagnosticRepository
from .english_learning_repository import EnglishLearningError
from .english_learning_service import EnglishLearningService

TASK_RECOMMENDATIONS = {
    "vocabulary_in_context": ("e1-lesson-01", "Vocabulary in context"),
    "banked_cloze": ("e3-lesson-01", "Banked cloze"),
    "open_cloze": ("e4-lesson-01", "Open cloze"),
    "reading_comprehension": ("e5-lesson-01", "Reading comprehension"),
}


class EnglishDiagnosticService:
    def __init__(
        self,
        learning: EnglishLearningService,
        repository: EnglishDiagnosticRepository,
    ):
        self.learning = learning
        self.repository = repository
        self.learner_id = learning.learner_id

    def _form(self, purpose: str):
        form = next(
            (
                form
                for form in self.learning.report.forms
                if form.form_type == purpose and self.learning._visible(form.status)
            ),
            None,
        )
        return form

    def _sprint_mastered(self) -> bool:
        catalogue = self.learning.report.catalogue
        if catalogue is None:
            return False
        sprint_keys = {
            lesson.stable_key
            for module in catalogue.modules
            for lesson in module.lessons
            if "sprint" in lesson.route_tags
        }
        progress = {
            item["lesson_key"]: item["state"]
            for item in self.learning.repository.progress(self.learner_id)
        }
        return bool(sprint_keys) and all(progress.get(key) == "mastered" for key in sprint_keys)

    def next(self) -> dict:
        self.learning._assert_curriculum_visible()
        baseline_form = self._form("baseline")
        if baseline_form is None:
            return {
                "status": "content_pending",
                "title": "English baseline is being prepared",
                "message": "The protected baseline form is not available yet.",
            }
        baseline = self.repository.latest(self.learner_id, "baseline")
        if baseline is None:
            return {
                "status": "start",
                "purpose": "baseline",
                "title": baseline_form.title,
                "message": (
                    "Complete 20 objective parts independently. Feedback remains hidden "
                    "until the full form is complete."
                ),
                "estimated_minutes": 25,
                "question_count": len(baseline_form.question_keys),
            }
        if baseline["status"] == "active":
            return {
                "status": "resume",
                "purpose": "baseline",
                "session_id": baseline["session_id"],
                "title": "Resume your English baseline",
                "message": "Your completed question groups are saved.",
            }

        endline = self.repository.latest(self.learner_id, "endline")
        if endline is not None:
            if endline["status"] == "active":
                return {
                    "status": "resume",
                    "purpose": "endline",
                    "session_id": endline["session_id"],
                    "title": "Resume your English endline",
                    "message": "Your completed question groups are saved.",
                }
            return {
                "status": "completed",
                "purpose": "endline",
                "result_session_id": endline["session_id"],
                "title": "English diagnostic journey complete",
                "message": "Compare your matched baseline and endline skill profiles.",
            }

        if not self._sprint_mastered():
            return {
                "status": "baseline_complete",
                "purpose": "baseline",
                "result_session_id": baseline["session_id"],
                "title": "English baseline complete",
                "message": (
                    "Continue the Sprint learning route. The matched endline unlocks after "
                    "every Sprint lesson checkpoint is mastered."
                ),
            }

        endline_form = self._form("endline")
        if endline_form is None:
            return {
                "status": "content_pending",
                "title": "English endline is being prepared",
                "message": "The matched protected endline form is not available yet.",
            }
        return {
            "status": "start",
            "purpose": "endline",
            "title": endline_form.title,
            "message": (
                "Complete the matched 20-part form independently. Results appear only after "
                "the full form is complete."
            ),
            "estimated_minutes": 25,
            "question_count": len(endline_form.question_keys),
        }

    def create_session(self, *, expected_purpose: str | None, idempotency_key: str) -> dict:
        if not 1 <= len(idempotency_key) <= 200:
            raise EnglishLearningError(
                "invalid_idempotency_key", "Supply a non-empty idempotency key."
            )
        action = self.next()
        if action["status"] == "resume":
            if expected_purpose and expected_purpose != action["purpose"]:
                raise EnglishLearningError(
                    "english_diagnostic_purpose_changed",
                    "The eligible English diagnostic purpose has changed. Refresh and try again.",
                    409,
                )
            return self.repository.session(self.learner_id, action["session_id"])
        if action["status"] != "start":
            raise EnglishLearningError(
                "english_diagnostic_not_available",
                "No English diagnostic can be started at this time.",
                409,
            )
        purpose = action["purpose"]
        if expected_purpose and expected_purpose != purpose:
            raise EnglishLearningError(
                "english_diagnostic_purpose_changed",
                "The eligible English diagnostic purpose has changed. Refresh and try again.",
                409,
            )
        form = self._form(purpose)
        if form is None:
            raise EnglishLearningError(
                "english_diagnostic_form_not_found",
                "The eligible English diagnostic form is unavailable.",
                404,
            )
        questions = [self.learning._question(key) for key in form.question_keys]
        expected_pool = f"{purpose}_diagnostic"
        if any(question.exposure_pool != expected_pool for question in questions):
            raise EnglishLearningError(
                "english_diagnostic_exposure_mismatch",
                "The protected diagnostic form contains a question from another exposure pool.",
                409,
            )
        actual_parts = sum(len(question.parts) for question in questions)
        if actual_parts != form.expected_scored_part_count:
            raise EnglishLearningError(
                "english_diagnostic_part_count_mismatch",
                "The protected diagnostic form does not match its scored-part contract.",
                409,
            )
        return self.repository.create_session(
            self.learner_id,
            exam_profile_key=form.profile_key,
            purpose=purpose,
            form_key=form.form_key,
            form_revision=form.revision,
            title=form.title,
            questions=[
                (question.stable_key, question.revision, question.question_type)
                for question in questions
            ],
            expected_part_count=form.expected_scored_part_count,
            idempotency_key=idempotency_key,
            development_drafts=(
                form.status != "published"
                or any(question.status != "published" for question in questions)
            ),
        )

    def session(self, session_id: str) -> dict:
        return self._enrich(self.repository.session(self.learner_id, session_id))

    def next_question(self, session_id: str) -> dict:
        session = self.repository.session(self.learner_id, session_id)
        assignment = self.repository.next_assignment(self.learner_id, session_id)
        if assignment is None:
            return {"status": "completed", "session": self._enrich(session)}
        question = self.learning._question(
            assignment["question_key"], assignment["question_revision"]
        )
        return {
            "status": "active",
            "session": self._enrich(session),
            "position": assignment["position"],
            "question": self.learning._public_question(question),
        }

    def submit_attempt(
        self,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        answers: dict[str, str | list[str]],
        idempotency_key: str,
    ) -> dict:
        replay = self.repository.attempt_by_idempotency(self.learner_id, idempotency_key)
        if replay is not None:
            replay["session"] = self._enrich(replay["session"])
            return replay
        assignment = self.repository.next_assignment(self.learner_id, session_id)
        if assignment is None:
            raise EnglishLearningError(
                "english_diagnostic_completed", "This English diagnostic is complete.", 409
            )
        if (
            assignment["question_key"] != question_key
            or assignment["question_revision"] != question_revision
        ):
            raise EnglishLearningError(
                "english_diagnostic_question_not_pending",
                "Answer the currently assigned English diagnostic question.",
                409,
            )
        question = self.learning._question(question_key, question_revision)
        expected = {str(part.position) for part in question.parts}
        if set(answers) != expected:
            raise EnglishLearningError(
                "english_answers_incomplete",
                "Supply one answer for every part of the English question.",
            )
        if question.question_type == "banked_cloze":
            selected = [
                value.strip().upper()
                for value in answers.values()
                if isinstance(value, str) and value.strip()
            ]
            if len(selected) != len(question.parts) or len(selected) != len(set(selected)):
                raise EnglishLearningError(
                    "english_banked_cloze_word_reused",
                    "Use each word-bank choice at most once.",
                )
        correct_parts = sum(
            bool(check_english_answer(part.response, answers[str(part.position)])["correct"])
            for part in question.parts
        )
        response = self.repository.record_attempt(
            self.learner_id,
            session_id=session_id,
            question_key=question_key,
            question_revision=question_revision,
            attempt_id=str(uuid4()),
            idempotency_key=idempotency_key,
            answers=answers,
            correct_parts=correct_parts,
            total_parts=len(question.parts),
        )
        response["session"] = self._enrich(response["session"])
        return response

    def result(self, session_id: str) -> dict:
        session = self.repository.session(self.learner_id, session_id)
        if session["status"] != "completed":
            raise EnglishLearningError(
                "english_diagnostic_incomplete",
                "Complete the English diagnostic before viewing results.",
                409,
            )
        return self._enrich(session)

    @staticmethod
    def _enrich(session: dict) -> dict:
        session = dict(session)
        task_scores = []
        for score in session.get("task_scores", []):
            lesson_key, lesson_title = TASK_RECOMMENDATIONS.get(
                score["task_type"], ("e0-lesson-01", "English orientation")
            )
            task_scores.append(
                dict(
                    score, recommended_lesson_key=lesson_key, recommended_lesson_title=lesson_title
                )
            )
        session["task_scores"] = task_scores
        return session
