"""Application service for the first authenticated objective-English journey."""

from __future__ import annotations

from uuid import uuid4

from question_bank.english_checking import check_english_answer
from question_bank.english_models import (
    MultipleResponse,
    ShortTextResponse,
    SingleChoiceResponse,
)

from .course_catalogue import CatalogueError, CourseCatalogue
from .english_learning_repository import (
    EnglishLearningError,
    EnglishLearningRepository,
)


class EnglishLearningService:
    def __init__(
        self,
        catalogue: CourseCatalogue,
        repository: EnglishLearningRepository,
        learner_id: str,
        *,
        allow_drafts: bool,
    ):
        self.catalogue = catalogue
        self.repository = repository
        self.learner_id = learner_id
        self.allow_drafts = allow_drafts
        self.report = catalogue.english_learner_report
        self.questions = {question.stable_key: question for question in self.report.questions}
        self.passages = {
            (passage.stable_key, passage.revision): passage for passage in self.report.passages
        }
        self.lessons = {lesson.stable_key: lesson for lesson in self.report.lessons}
        self.forms = {form.form_key: form for form in self.report.forms}

    def _visible(self, status: str) -> bool:
        return status == "published" or (self.allow_drafts and status in {"draft", "reviewed"})

    def _assert_curriculum_visible(self) -> None:
        catalogue = self.report.catalogue
        if catalogue is None or not self._visible(catalogue.status):
            raise CatalogueError(
                "english_course_not_found", "The English course is not available.", 404
            )

    def _lesson(self, lesson_key: str):
        self._assert_curriculum_visible()
        lesson = self.lessons.get(lesson_key)
        if lesson is None or not self._visible(lesson.status):
            raise CatalogueError(
                "english_lesson_not_found", "The English lesson was not found.", 404
            )
        return lesson

    def _question(self, question_key: str, revision: int | None = None):
        question = self.questions.get(question_key)
        if (
            question is None
            or not self._visible(question.status)
            or (revision is not None and question.revision != revision)
        ):
            raise EnglishLearningError(
                "english_question_revision_unavailable",
                "The assigned English question revision is unavailable.",
                409,
            )
        return question

    def course_map(self) -> dict:
        self._assert_curriculum_visible()
        catalogue = self.report.catalogue
        assert catalogue is not None
        exam_profile = self.report.exam_profile
        assert exam_profile is not None
        authored = self.lessons
        progress = {item["lesson_key"]: item for item in self.repository.progress(self.learner_id)}
        modules = []
        for module in catalogue.modules:
            lessons = []
            for lesson_ref in module.lessons:
                lesson = authored.get(lesson_ref.stable_key)
                is_visible = lesson is not None and self._visible(lesson.status)
                item_progress = progress.get(lesson_ref.stable_key)
                lessons.append(
                    {
                        "stable_key": lesson_ref.stable_key,
                        "lesson_code": lesson_ref.lesson_code,
                        "position": lesson_ref.position,
                        "title": lesson_ref.title,
                        "outcome_code": lesson_ref.outcome_code,
                        "outcome": lesson_ref.outcome,
                        "route_tags": lesson_ref.route_tags,
                        "content_status": lesson.status if lesson else "planned",
                        "authored": lesson is not None,
                        "available": is_visible,
                        "href": (
                            f"/english/lessons/{lesson_ref.stable_key}" if is_visible else None
                        ),
                        "progress_state": (
                            item_progress["state"] if item_progress else "not_started"
                        ),
                        "retry_question_count": (
                            item_progress["retry_question_count"] if item_progress else 0
                        ),
                    }
                )
            modules.append(
                {
                    "module_code": module.module_code,
                    "position": module.position,
                    "stage": module.stage,
                    "title": module.title,
                    "purpose": module.purpose,
                    "lessons": lessons,
                }
            )
        return {
            "stable_key": "asean-scholarship-english",
            "revision": 1,
            "title": catalogue.title,
            "description": (
                "Build vocabulary, grammar, cloze, reading and writing skills for "
                "ASEAN Scholarship selection-test preparation."
            ),
            "subject": "English",
            "content_status": catalogue.status,
            "development_preview": catalogue.status != "published",
            "exam_profile": {
                "profile_key": exam_profile.profile_key,
                "status": exam_profile.status,
                "evidence_boundary": exam_profile.evidence_boundary,
                "entry_level": exam_profile.entry_level,
                "effective_from": exam_profile.effective_from.isoformat(),
                "review_due": exam_profile.review_due.isoformat(),
                "sections": [section.model_dump(mode="json") for section in exam_profile.sections],
                "excluded_task_types": exam_profile.excluded_task_types,
            },
            "modules": modules,
        }

    def lesson(self, lesson_key: str) -> dict:
        lesson = self._lesson(lesson_key)
        question_keys = [key for section in lesson.sections for key in section.question_keys]
        visible_questions = [
            key
            for key in question_keys
            if key in self.questions and self._visible(self.questions[key].status)
        ]
        material_ready = lesson.status == "published" and len(visible_questions) == len(
            question_keys
        )
        return {
            "stable_key": lesson.stable_key,
            "revision": lesson.revision,
            "lesson_code": lesson.lesson_code,
            "outcome_code": lesson.outcome_code,
            "title": lesson.title,
            "summary": lesson.summary,
            "estimated_minutes": lesson.estimated_minutes,
            "content_status": lesson.status,
            "development_preview": lesson.status != "published",
            "sections": [
                {
                    "position": section.position,
                    "section_type": section.section_type,
                    "title": section.title,
                    "content": section.content,
                    "question_count": len(section.question_keys),
                }
                for section in lesson.sections
            ],
            "practice": {
                "lesson_key": lesson.stable_key,
                "question_count": len(question_keys),
                "available": material_ready,
                "development_available": self.allow_drafts and not material_ready,
                "retry_question_count": self.repository.retry_count(
                    self.learner_id, lesson.stable_key
                ),
            },
        }

    def create_session(
        self,
        *,
        lesson_key: str,
        mode: str,
        idempotency_key: str,
    ) -> dict:
        if not 1 <= len(idempotency_key) <= 200:
            raise EnglishLearningError(
                "invalid_idempotency_key", "Supply a non-empty idempotency key."
            )
        lesson = self._lesson(lesson_key)
        active = self.repository.active_session(self.learner_id, lesson_key, mode)
        if active:
            return active
        ordered_keys = [key for section in lesson.sections for key in section.question_keys]
        retry_source_by_key: dict[str, str | None] = {key: None for key in ordered_keys}
        if mode == "retry_review":
            due = set(self.repository.retry_keys(self.learner_id, lesson_key))
            if not due:
                raise EnglishLearningError(
                    "english_retry_queue_empty",
                    "This English lesson has no exit-ticket questions to retry.",
                    409,
                )
            parallel = [
                question
                for question in self.report.questions
                if question.parallel_form_of in due
                and question.exposure_pool == "retry_review"
                and self._visible(question.status)
            ]
            covered = {question.parallel_form_of for question in parallel}
            missing = sorted(due - covered)
            if missing:
                raise EnglishLearningError(
                    "english_parallel_retry_unavailable",
                    "A fresh parallel retry is not available for: " + ", ".join(missing),
                    409,
                )
            ordered_keys = [question.stable_key for question in parallel]
            retry_source_by_key = {
                question.stable_key: question.parallel_form_of for question in parallel
            }
        questions = [self._question(key) for key in ordered_keys]
        if not questions:
            raise EnglishLearningError(
                "english_practice_unavailable",
                "This English lesson has no available objective questions.",
                409,
            )
        return self.repository.create_session(
            self.learner_id,
            exam_profile_key=self.report.exam_profile.profile_key,
            lesson_key=lesson.stable_key,
            lesson_revision=lesson.revision,
            mode=mode,
            questions=[
                (
                    question.stable_key,
                    question.revision,
                    question.exposure_pool,
                    retry_source_by_key[question.stable_key],
                )
                for question in questions
            ],
            idempotency_key=idempotency_key,
            development_drafts=any(question.status != "published" for question in questions),
        )

    def session(self, session_id: str) -> dict:
        return self.repository.session(self.learner_id, session_id)

    def create_checkpoint_session(
        self, *, module_code: str, idempotency_key: str
    ) -> dict:
        if not 1 <= len(idempotency_key) <= 200:
            raise EnglishLearningError(
                "invalid_idempotency_key", "Supply a non-empty idempotency key."
            )
        forms = sorted(
            (
                form
                for form in self.report.forms
                if form.form_type == "checkpoint"
                and form.module_code == module_code
                and self._visible(form.status)
            ),
            key=lambda form: form.form_key,
        )
        if not forms:
            raise EnglishLearningError(
                "english_checkpoint_not_found",
                "No English checkpoint is available for this module.",
                404,
            )
        active = self.repository.active_checkpoint_session(self.learner_id, module_code)
        if active:
            return active
        progress = {
            item["lesson_key"]: item for item in self.repository.progress(self.learner_id)
        }
        mastery_keys = forms[0].mastery_lesson_keys
        missing = [
            key
            for key in mastery_keys
            if key not in progress or progress[key]["state"] not in {"proficient", "mastered"}
        ]
        if missing:
            raise EnglishLearningError(
                "english_checkpoint_locked",
                "Every scoped lesson must be proficient before the checkpoint: "
                + ", ".join(missing),
                409,
            )
        if all(progress[key]["state"] == "mastered" for key in mastery_keys):
            raise EnglishLearningError(
                "english_checkpoint_already_passed",
                "This English module checkpoint has already been passed.",
                409,
            )
        latest = self.repository.latest_checkpoint_session(self.learner_id, module_code)
        selected = forms[0]
        if latest is not None and latest["passed"] is False:
            latest_form = self.forms[latest["form_key"]]
            selected = self.forms[latest_form.paired_form_key]
        questions = [self._question(key) for key in selected.question_keys]
        return self.repository.create_checkpoint_session(
            self.learner_id,
            exam_profile_key=self.report.exam_profile.profile_key,
            form_key=selected.form_key,
            form_revision=selected.revision,
            module_code=module_code,
            mastery_lesson_keys=selected.mastery_lesson_keys,
            questions=[(question.stable_key, question.revision) for question in questions],
            idempotency_key=idempotency_key,
            development_drafts=(
                selected.status != "published"
                or any(question.status != "published" for question in questions)
            ),
        )

    def checkpoint_session(self, session_id: str) -> dict:
        return self.repository.checkpoint_session(self.learner_id, session_id)

    def next_checkpoint_question(self, session_id: str) -> dict:
        session = self.repository.checkpoint_session(self.learner_id, session_id)
        assignment = self.repository.next_checkpoint_assignment(self.learner_id, session_id)
        session = self.repository.checkpoint_session(self.learner_id, session_id)
        if assignment is None:
            return {"status": "completed", "session": session}
        question = self._question(assignment["question_key"], assignment["question_revision"])
        return {
            "status": "active",
            "session": session,
            "position": assignment["position"],
            "question": self._public_question(question),
        }

    def submit_checkpoint_attempt(
        self,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        answers: dict[str, str | list[str]],
        idempotency_key: str,
    ) -> dict:
        replay = self.repository.checkpoint_attempt_by_idempotency(
            self.learner_id, idempotency_key
        )
        if replay is not None:
            return replay
        assignment = self.repository.next_checkpoint_assignment(self.learner_id, session_id)
        if assignment is None:
            raise EnglishLearningError(
                "english_checkpoint_completed", "This checkpoint is complete.", 409
            )
        if (
            assignment["question_key"] != question_key
            or assignment["question_revision"] != question_revision
        ):
            raise EnglishLearningError(
                "english_checkpoint_question_not_pending",
                "Answer the currently assigned checkpoint question.",
                409,
            )
        question = self._question(question_key, question_revision)
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
        return self.repository.record_checkpoint_attempt(
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

    @staticmethod
    def _public_part(part) -> dict:
        spec = part.response
        options = (
            [option.model_dump(mode="json") for option in spec.options]
            if isinstance(spec, (SingleChoiceResponse, MultipleResponse))
            else []
        )
        return {
            "position": part.position,
            "prompt": part.prompt,
            "response_type": spec.type,
            "options": options,
        }

    def _public_question(self, question) -> dict:
        passage = None
        if question.passage_ref is not None:
            source = self.passages[(question.passage_ref.stable_key, question.passage_ref.revision)]
            passage = {
                "stable_key": source.stable_key,
                "revision": source.revision,
                "title": source.title,
                "text_type": source.text_type,
                "paragraphs": source.paragraphs,
                "attribution": source.attribution,
            }
        word_bank = None
        if question.question_type == "banked_cloze":
            first = question.parts[0].response
            assert isinstance(first, SingleChoiceResponse)
            word_bank = [option.model_dump(mode="json") for option in first.options]
        parts = [self._public_part(part) for part in question.parts]
        if word_bank is not None:
            for part in parts:
                part["options"] = []
        return {
            "stable_key": question.stable_key,
            "revision": question.revision,
            "title": question.title,
            "difficulty": question.difficulty,
            "outcome_code": question.outcome_code,
            "question_type": question.question_type,
            "exposure_pool": question.exposure_pool,
            "instructions": question.instructions,
            "passage": passage,
            "word_bank": word_bank,
            "parts": parts,
        }

    def next_question(self, session_id: str) -> dict:
        session = self.repository.session(self.learner_id, session_id)
        assignment = self.repository.next_assignment(self.learner_id, session_id)
        session = self.repository.session(self.learner_id, session_id)
        if assignment is None:
            return {"status": "completed", "session": session}
        question = self._question(assignment["question_key"], assignment["question_revision"])
        return {
            "status": "active",
            "session": session,
            "position": assignment["position"],
            "question": self._public_question(question),
        }

    @staticmethod
    def _wrong_feedback(part, submission) -> str:
        spec = part.response
        if isinstance(spec, (SingleChoiceResponse, MultipleResponse)):
            keys = [submission] if isinstance(submission, str) else submission
            rationales = [spec.choice_rationales.get(str(key).upper()) for key in keys]
            useful = [text for text in rationales if text]
            return " ".join(useful) if useful else part.hint
        if isinstance(spec, ShortTextResponse):
            return spec.rationale
        return part.hint

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
            return replay
        assignment = self.repository.next_assignment(self.learner_id, session_id)
        if assignment is None:
            raise EnglishLearningError(
                "english_session_completed", "This English practice session is complete.", 409
            )
        if (
            assignment["question_key"] != question_key
            or assignment["question_revision"] != question_revision
        ):
            raise EnglishLearningError(
                "english_question_not_pending",
                "Answer the currently assigned English question.",
                409,
            )
        question = self._question(question_key, question_revision)
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
        parts = []
        for part in question.parts:
            submission = answers[str(part.position)]
            checked = check_english_answer(part.response, submission)
            correct = bool(checked["correct"])
            parts.append(
                {
                    "position": part.position,
                    "correct": correct,
                    "error": checked["error"],
                    "feedback": (
                        part.correct_explanation
                        if correct
                        else self._wrong_feedback(part, submission)
                    ),
                }
            )
        correct_parts = sum(part["correct"] for part in parts)
        total_parts = len(parts)
        score = correct_parts / total_parts
        hint_used = bool(assignment.get("hint_used", False))
        threshold_met = score >= 0.75 and not hint_used
        correct = correct_parts == total_parts
        retry_queued = not threshold_met and question.exposure_pool == "exit_ticket"
        attempt_id = str(uuid4())
        response = {
            "attempt_id": attempt_id,
            "attempt_number": 1,
            "correct": correct,
            "correct_parts": correct_parts,
            "total_parts": total_parts,
            "score": score,
            "threshold_met": threshold_met,
            "hint_used": hint_used,
            "parts": parts,
            "question_finished": True,
            "retry_queued": retry_queued,
            "needs_error_classification": not correct,
            "lesson_state": "in_progress",
        }
        return self.repository.record_attempt(
            self.learner_id,
            session_id=session_id,
            question_key=question_key,
            question_revision=question_revision,
            attempt_id=attempt_id,
            idempotency_key=idempotency_key,
            answers=answers,
            response=response,
            correct=correct,
            correct_parts=correct_parts,
            total_parts=total_parts,
            threshold_met=threshold_met,
            retry_queued=retry_queued,
        )

    def classify_error(self, attempt_id: str, category: str) -> dict:
        return self.repository.record_classification(self.learner_id, attempt_id, category)

    def hint(self, session_id: str, question_key: str) -> dict:
        assignment = self.repository.next_assignment(self.learner_id, session_id)
        if assignment is None or assignment["question_key"] != question_key:
            raise EnglishLearningError(
                "english_question_not_pending",
                "The English question is not awaiting an answer in this session.",
                409,
            )
        question = self._question(question_key, assignment["question_revision"])
        self.repository.record_hint(self.learner_id, session_id, question_key)
        return {
            "question_key": question_key,
            "parts": [part.hint for part in question.parts],
            "hint_used": True,
        }

    def progress(self) -> dict:
        return {
            "learner_id": self.learner_id,
            "lessons": self.repository.progress(self.learner_id),
        }
