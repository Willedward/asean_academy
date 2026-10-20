"""Persistence adapters for authenticated objective-English learning."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def _now() -> str:
    return datetime.now(UTC).isoformat()


class EnglishLearningError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class EnglishLearningRepository(Protocol):
    def active_session(self, learner_id: str, lesson_key: str, mode: str) -> dict | None: ...
    def create_session(
        self,
        learner_id: str,
        *,
        lesson_key: str,
        lesson_revision: int,
        mode: str,
        questions: list[tuple[str, int, str]],
        idempotency_key: str,
        development_drafts: bool,
    ) -> dict: ...
    def session(self, learner_id: str, session_id: str) -> dict: ...
    def next_assignment(self, learner_id: str, session_id: str) -> dict | None: ...
    def attempt_by_idempotency(self, learner_id: str, idempotency_key: str) -> dict | None: ...
    def record_attempt(
        self,
        learner_id: str,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        attempt_id: str,
        idempotency_key: str,
        answers: dict,
        response: dict,
        correct: bool,
        retry_queued: bool,
    ) -> dict: ...
    def record_classification(
        self, learner_id: str, attempt_id: str, category: str
    ) -> dict: ...
    def retry_keys(self, learner_id: str, lesson_key: str) -> list[str]: ...
    def retry_count(self, learner_id: str, lesson_key: str) -> int: ...
    def progress(self, learner_id: str) -> list[dict]: ...


class InMemoryEnglishLearningRepository:
    """Process-local development adapter; hosted environments use PostgreSQL."""

    def __init__(self):
        self.sessions: dict[str, dict] = {}
        self.assignments: dict[str, list[dict]] = {}
        self.attempts: dict[str, dict] = {}
        self.attempt_keys: dict[tuple[str, str], str] = {}
        self.session_keys: dict[tuple[str, str], str] = {}
        self.classifications: dict[str, str] = {}
        self.retries: dict[tuple[str, str], dict] = {}
        self.lesson_progress: dict[tuple[str, str], dict] = {}

    def _owned(self, learner_id: str, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if session is None or session["learner_id"] != learner_id:
            raise EnglishLearningError(
                "english_session_not_found", "The English practice session was not found.", 404
            )
        return session

    def _summary(self, session: dict) -> dict:
        assignments = self.assignments[session["session_id"]]
        return {
            key: session[key]
            for key in (
                "session_id",
                "status",
                "lesson_key",
                "lesson_revision",
                "mode",
                "question_count",
                "development_drafts",
            )
        } | {
            "assigned_count": len(assignments),
            "resolved_count": sum(item["status"] != "pending" for item in assignments),
            "correct_count": sum(item["status"] == "correct" for item in assignments),
            "incorrect_count": sum(item["status"] == "incorrect" for item in assignments),
        }

    def active_session(self, learner_id: str, lesson_key: str, mode: str) -> dict | None:
        found = next(
            (
                session
                for session in reversed(list(self.sessions.values()))
                if session["learner_id"] == learner_id
                and session["lesson_key"] == lesson_key
                and session["mode"] == mode
                and session["status"] == "active"
            ),
            None,
        )
        return self._summary(found) if found else None

    def create_session(
        self,
        learner_id: str,
        *,
        lesson_key: str,
        lesson_revision: int,
        mode: str,
        questions: list[tuple[str, int, str]],
        idempotency_key: str,
        development_drafts: bool,
    ) -> dict:
        key = (learner_id, idempotency_key)
        existing_id = self.session_keys.get(key)
        if existing_id:
            return self._summary(self.sessions[existing_id])
        active = self.active_session(learner_id, lesson_key, mode)
        if active:
            self.session_keys[key] = active["session_id"]
            return active
        session_id = str(uuid4())
        session = {
            "session_id": session_id,
            "learner_id": learner_id,
            "status": "active",
            "lesson_key": lesson_key,
            "lesson_revision": lesson_revision,
            "mode": mode,
            "question_count": len(questions),
            "development_drafts": development_drafts,
            "created_at": _now(),
        }
        self.sessions[session_id] = session
        self.assignments[session_id] = [
            {
                "position": position,
                "question_key": question_key,
                "question_revision": revision,
                "exposure_pool": exposure_pool,
                "status": "pending",
            }
            for position, (question_key, revision, exposure_pool) in enumerate(questions, 1)
        ]
        self.session_keys[key] = session_id
        progress_key = (learner_id, lesson_key)
        current = self.lesson_progress.get(progress_key)
        if current is None:
            self.lesson_progress[progress_key] = {
                "lesson_key": lesson_key,
                "lesson_revision": lesson_revision,
                "state": "in_progress",
                "question_count": len(questions),
                "resolved_count": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "retry_question_count": self.retry_count(learner_id, lesson_key),
                "last_session_id": session_id,
                "updated_at": _now(),
            }
        return self._summary(session)

    def session(self, learner_id: str, session_id: str) -> dict:
        return self._summary(self._owned(learner_id, session_id))

    def next_assignment(self, learner_id: str, session_id: str) -> dict | None:
        session = self._owned(learner_id, session_id)
        pending = next(
            (item for item in self.assignments[session_id] if item["status"] == "pending"),
            None,
        )
        if pending is None and session["status"] == "active":
            session["status"] = "completed"
        return dict(pending) if pending else None

    def attempt_by_idempotency(self, learner_id: str, idempotency_key: str) -> dict | None:
        attempt_id = self.attempt_keys.get((learner_id, idempotency_key))
        return dict(self.attempts[attempt_id]["response"]) if attempt_id else None

    def _sync_progress(self, learner_id: str, session: dict) -> str:
        assignments = self.assignments[session["session_id"]]
        resolved = sum(item["status"] != "pending" for item in assignments)
        correct = sum(item["status"] == "correct" for item in assignments)
        incorrect = sum(item["status"] == "incorrect" for item in assignments)
        exit_correct = any(
            item["exposure_pool"] == "exit_ticket" and item["status"] == "correct"
            for item in assignments
        )
        if session["mode"] == "retry_review" and correct:
            state = "proficient"
        elif resolved < len(assignments):
            state = "in_progress"
        elif exit_correct:
            state = "proficient"
        else:
            state = "practice_completed"
        progress_key = (learner_id, session["lesson_key"])
        previous = self.lesson_progress.get(progress_key)
        if previous and previous["state"] == "proficient":
            state = "proficient"
        self.lesson_progress[progress_key] = {
            "lesson_key": session["lesson_key"],
            "lesson_revision": session["lesson_revision"],
            "state": state,
            "question_count": len(assignments),
            "resolved_count": resolved,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "retry_question_count": self.retry_count(learner_id, session["lesson_key"]),
            "last_session_id": session["session_id"],
            "updated_at": _now(),
        }
        return state

    def record_attempt(
        self,
        learner_id: str,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        attempt_id: str,
        idempotency_key: str,
        answers: dict,
        response: dict,
        correct: bool,
        retry_queued: bool,
    ) -> dict:
        replay = self.attempt_by_idempotency(learner_id, idempotency_key)
        if replay is not None:
            return replay
        session = self._owned(learner_id, session_id)
        assignment = next(
            (
                item
                for item in self.assignments[session_id]
                if item["question_key"] == question_key
                and item["question_revision"] == question_revision
            ),
            None,
        )
        if assignment is None or assignment["status"] != "pending":
            raise EnglishLearningError(
                "english_question_not_pending",
                "The English question is not awaiting an answer in this session.",
                409,
            )
        attempt_number = 1 + sum(
            attempt["learner_id"] == learner_id
            and attempt["question_key"] == question_key
            for attempt in self.attempts.values()
        )
        response = dict(response, attempt_number=attempt_number)
        assignment["status"] = "correct" if correct else "incorrect"
        if retry_queued:
            self.retries[(learner_id, question_key)] = {
                "lesson_key": session["lesson_key"],
                "question_key": question_key,
                "question_revision": question_revision,
                "state": "queued",
                "queued_at": _now(),
            }
        if session["mode"] == "retry_review" and correct:
            retry = self.retries.get((learner_id, question_key))
            if retry:
                retry["state"] = "resolved"
        if all(item["status"] != "pending" for item in self.assignments[session_id]):
            session["status"] = "completed"
        state = self._sync_progress(learner_id, session)
        response["lesson_state"] = state
        self.attempts[attempt_id] = {
            "attempt_id": attempt_id,
            "learner_id": learner_id,
            "session_id": session_id,
            "question_key": question_key,
            "question_revision": question_revision,
            "answers": answers,
            "correct": correct,
            "response": response,
        }
        self.attempt_keys[(learner_id, idempotency_key)] = attempt_id
        return dict(response)

    def record_classification(
        self, learner_id: str, attempt_id: str, category: str
    ) -> dict:
        attempt = self.attempts.get(attempt_id)
        if attempt is None or attempt["learner_id"] != learner_id:
            raise EnglishLearningError(
                "english_attempt_not_found", "The English attempt was not found.", 404
            )
        if attempt["correct"]:
            raise EnglishLearningError(
                "english_error_classification_not_required",
                "Correct attempts do not require an error category.",
                409,
            )
        existing = self.classifications.get(attempt_id)
        if existing and existing != category:
            raise EnglishLearningError(
                "english_error_already_classified",
                "This attempt already has an immutable error category.",
                409,
            )
        self.classifications[attempt_id] = category
        return {"attempt_id": attempt_id, "category": category, "recorded": True}

    def retry_keys(self, learner_id: str, lesson_key: str) -> list[str]:
        return [
            item["question_key"]
            for (student, _), item in self.retries.items()
            if student == learner_id
            and item["lesson_key"] == lesson_key
            and item["state"] == "queued"
        ]

    def retry_count(self, learner_id: str, lesson_key: str) -> int:
        return len(self.retry_keys(learner_id, lesson_key))

    def progress(self, learner_id: str) -> list[dict]:
        return [
            dict(value)
            for (student, _), value in self.lesson_progress.items()
            if student == learner_id
        ]


class PostgresEnglishLearningRepository:
    """Transactional hosted adapter for English sessions, attempts and retries."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def _set_identity(connection, learner_id: str) -> None:
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)", (learner_id,)
        )

    @staticmethod
    def _summary(connection, session: dict) -> dict:
        counts = connection.execute(
            """
            select count(*)::integer as assigned_count,
                   count(*) filter (where status <> 'pending')::integer as resolved_count,
                   count(*) filter (where status = 'correct')::integer as correct_count,
                   count(*) filter (where status = 'incorrect')::integer as incorrect_count
            from english_session_questions where practice_session_id = %s
            """,
            (session["id"],),
        ).fetchone()
        return {
            "session_id": str(session["id"]),
            "status": session["status"],
            "lesson_key": session["lesson_key"],
            "lesson_revision": session["lesson_revision"],
            "mode": session["mode"],
            "question_count": session["requested_question_count"],
            "assigned_count": counts["assigned_count"],
            "resolved_count": counts["resolved_count"],
            "correct_count": counts["correct_count"],
            "incorrect_count": counts["incorrect_count"],
            "development_drafts": session["development_drafts"],
        }

    @staticmethod
    def _owned(connection, learner_id: str, session_id: str, *, lock: bool = False):
        suffix = " for update" if lock else ""
        session = connection.execute(
            "select * from english_practice_sessions where id=%s and student_id=%s" + suffix,
            (session_id, learner_id),
        ).fetchone()
        if session is None:
            raise EnglishLearningError(
                "english_session_not_found", "The English practice session was not found.", 404
            )
        return session

    def active_session(self, learner_id: str, lesson_key: str, mode: str) -> dict | None:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            session = connection.execute(
                """
                select * from english_practice_sessions
                where student_id=%s and lesson_key=%s and mode=%s and status='active'
                order by created_at desc limit 1
                """,
                (learner_id, lesson_key, mode),
            ).fetchone()
            return self._summary(connection, session) if session else None

    def create_session(
        self,
        learner_id: str,
        *,
        lesson_key: str,
        lesson_revision: int,
        mode: str,
        questions: list[tuple[str, int, str]],
        idempotency_key: str,
        development_drafts: bool,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            self._set_identity(connection, learner_id)
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english:{learner_id}:{lesson_key}:{mode}",),
            )
            existing = connection.execute(
                """
                select sessions.* from english_practice_session_idempotency_keys keys
                join english_practice_sessions sessions on sessions.id=keys.practice_session_id
                where keys.student_id=%s and keys.idempotency_key=%s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if existing:
                return self._summary(connection, existing)
            active = connection.execute(
                """
                select * from english_practice_sessions
                where student_id=%s and lesson_key=%s and mode=%s and status='active'
                order by created_at desc limit 1
                """,
                (learner_id, lesson_key, mode),
            ).fetchone()
            if active:
                connection.execute(
                    """
                    insert into english_practice_session_idempotency_keys
                        (student_id, idempotency_key, practice_session_id)
                    values (%s, %s, %s)
                    """,
                    (learner_id, idempotency_key, active["id"]),
                )
                return self._summary(connection, active)
            session = connection.execute(
                """
                insert into english_practice_sessions (
                    student_id, lesson_key, lesson_revision, mode,
                    requested_question_count, development_drafts
                ) values (%s, %s, %s, %s, %s, %s) returning *
                """,
                (
                    learner_id,
                    lesson_key,
                    lesson_revision,
                    mode,
                    len(questions),
                    development_drafts,
                ),
            ).fetchone()
            for position, (question_key, revision, _exposure) in enumerate(questions, 1):
                question = connection.execute(
                    """
                    select versions.id from english_objective_questions questions
                    join english_objective_question_versions versions
                      on versions.question_id=questions.id
                    where questions.stable_key=%s and versions.revision=%s
                    """,
                    (question_key, revision),
                ).fetchone()
                if question is None:
                    raise EnglishLearningError(
                        "english_question_revision_not_imported",
                        "The assigned English question revision has not been imported.",
                        503,
                    )
                connection.execute(
                    """
                    insert into english_session_questions (
                        practice_session_id, question_version_id, position
                    ) values (%s, %s, %s)
                    """,
                    (session["id"], question["id"], position),
                )
            connection.execute(
                """
                insert into english_practice_session_idempotency_keys
                    (student_id, idempotency_key, practice_session_id)
                values (%s, %s, %s)
                """,
                (learner_id, idempotency_key, session["id"]),
            )
            connection.execute(
                """
                insert into english_lesson_progress (
                    student_id, lesson_key, lesson_revision, state,
                    question_count, last_practice_session_id
                ) values (%s, %s, %s, 'in_progress', %s, %s)
                on conflict (student_id, lesson_key) do update set
                    lesson_revision=excluded.lesson_revision,
                    state=case when english_lesson_progress.state='proficient'
                               then 'proficient'::english_lesson_progress_state
                               else 'in_progress'::english_lesson_progress_state end,
                    question_count=excluded.question_count,
                    last_practice_session_id=excluded.last_practice_session_id,
                    updated_at=now()
                """,
                (learner_id, lesson_key, lesson_revision, len(questions), session["id"]),
            )
            return self._summary(connection, session)

    def session(self, learner_id: str, session_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            return self._summary(connection, self._owned(connection, learner_id, session_id))

    def next_assignment(self, learner_id: str, session_id: str) -> dict | None:
        with self._connect() as connection, connection.transaction():
            self._set_identity(connection, learner_id)
            session = self._owned(connection, learner_id, session_id, lock=True)
            row = connection.execute(
                """
                select assigned.position, questions.stable_key as question_key,
                       versions.revision as question_revision,
                       questions.exposure_pool::text as exposure_pool
                from english_session_questions assigned
                join english_objective_question_versions versions
                  on versions.id=assigned.question_version_id
                join english_objective_questions questions on questions.id=versions.question_id
                where assigned.practice_session_id=%s and assigned.status='pending'
                order by assigned.position limit 1
                """,
                (session["id"],),
            ).fetchone()
            if row is None and session["status"] == "active":
                connection.execute(
                    """
                    update english_practice_sessions set status='completed', completed_at=now()
                    where id=%s
                    """,
                    (session["id"],),
                )
            return dict(row) if row else None

    def attempt_by_idempotency(self, learner_id: str, idempotency_key: str) -> dict | None:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            row = connection.execute(
                """
                select result from english_objective_attempts
                where student_id=%s and idempotency_key=%s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            return row["result"] if row else None

    def _sync_progress(self, connection, learner_id: str, session: dict) -> str:
        counts = connection.execute(
            """
            select count(*)::integer as question_count,
                   count(*) filter (where assigned.status <> 'pending')::integer as resolved_count,
                   count(*) filter (where assigned.status = 'correct')::integer as correct_count,
                   count(*) filter (where assigned.status = 'incorrect')::integer as incorrect_count,
                   bool_or(questions.exposure_pool='exit_ticket' and assigned.status='correct')
                       as exit_correct
            from english_session_questions assigned
            join english_objective_question_versions versions
              on versions.id=assigned.question_version_id
            join english_objective_questions questions on questions.id=versions.question_id
            where assigned.practice_session_id=%s
            """,
            (session["id"],),
        ).fetchone()
        if session["mode"] == "retry_review" and counts["correct_count"]:
            state = "proficient"
        elif counts["resolved_count"] < counts["question_count"]:
            state = "in_progress"
        elif counts["exit_correct"]:
            state = "proficient"
        else:
            state = "practice_completed"
        current = connection.execute(
            """
            select state::text from english_lesson_progress
            where student_id=%s and lesson_key=%s
            """,
            (learner_id, session["lesson_key"]),
        ).fetchone()
        if current and current["state"] == "proficient":
            state = "proficient"
        connection.execute(
            """
            insert into english_lesson_progress (
                student_id, lesson_key, lesson_revision, state, question_count,
                resolved_count, correct_count, incorrect_count, last_practice_session_id
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (student_id, lesson_key) do update set
                lesson_revision=excluded.lesson_revision,
                state=excluded.state,
                question_count=excluded.question_count,
                resolved_count=excluded.resolved_count,
                correct_count=excluded.correct_count,
                incorrect_count=excluded.incorrect_count,
                last_practice_session_id=excluded.last_practice_session_id,
                updated_at=now(),
                completed_at=case when excluded.state in ('practice_completed','proficient')
                                  then coalesce(english_lesson_progress.completed_at, now())
                                  else null end
            """,
            (
                learner_id,
                session["lesson_key"],
                session["lesson_revision"],
                state,
                counts["question_count"],
                counts["resolved_count"],
                counts["correct_count"],
                counts["incorrect_count"],
                session["id"],
            ),
        )
        return state

    def record_attempt(
        self,
        learner_id: str,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        attempt_id: str,
        idempotency_key: str,
        answers: dict,
        response: dict,
        correct: bool,
        retry_queued: bool,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            self._set_identity(connection, learner_id)
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-attempt:{learner_id}:{idempotency_key}",),
            )
            replay = connection.execute(
                """
                select result from english_objective_attempts
                where student_id=%s and idempotency_key=%s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if replay:
                return replay["result"]
            session = self._owned(connection, learner_id, session_id, lock=True)
            assigned = connection.execute(
                """
                select assigned.id, assigned.status, questions.exposure_pool::text,
                       questions.id as question_id
                from english_session_questions assigned
                join english_objective_question_versions versions
                  on versions.id=assigned.question_version_id
                join english_objective_questions questions on questions.id=versions.question_id
                where assigned.practice_session_id=%s and questions.stable_key=%s
                  and versions.revision=%s
                for update of assigned
                """,
                (session["id"], question_key, question_revision),
            ).fetchone()
            if assigned is None or assigned["status"] != "pending":
                raise EnglishLearningError(
                    "english_question_not_pending",
                    "The English question is not awaiting an answer in this session.",
                    409,
                )
            attempt_number = connection.execute(
                """
                select count(*)::integer + 1 as number
                from english_objective_attempts attempts
                join english_session_questions sq on sq.id=attempts.session_question_id
                join english_objective_question_versions versions
                  on versions.id=sq.question_version_id
                join english_objective_questions questions on questions.id=versions.question_id
                where attempts.student_id=%s and questions.stable_key=%s
                """,
                (learner_id, question_key),
            ).fetchone()["number"]
            response = dict(response, attempt_number=attempt_number)
            connection.execute(
                """
                update english_session_questions
                set status=%s, resolved_at=now() where id=%s
                """,
                ("correct" if correct else "incorrect", assigned["id"]),
            )
            pending = connection.execute(
                """
                select count(*)::integer as count from english_session_questions
                where practice_session_id=%s and status='pending'
                """,
                (session["id"],),
            ).fetchone()["count"]
            if pending == 0:
                connection.execute(
                    """
                    update english_practice_sessions set status='completed', completed_at=now()
                    where id=%s
                    """,
                    (session["id"],),
                )
                session["status"] = "completed"
            state = self._sync_progress(connection, learner_id, session)
            response["lesson_state"] = state
            connection.execute(
                """
                insert into english_objective_attempts (
                    id, student_id, session_question_id, attempt_number,
                    idempotency_key, answers, result, is_correct
                ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    attempt_id,
                    learner_id,
                    assigned["id"],
                    attempt_number,
                    idempotency_key,
                    Jsonb(answers),
                    Jsonb(response),
                    correct,
                ),
            )
            if retry_queued:
                connection.execute(
                    """
                    insert into english_retry_queue (
                        student_id, question_id, lesson_key, source_attempt_id,
                        due_at, state
                    ) values (%s, %s, %s, %s, now(), 'queued')
                    on conflict (student_id, question_id) do update set
                        lesson_key=excluded.lesson_key,
                        source_attempt_id=excluded.source_attempt_id,
                        due_at=excluded.due_at,
                        state='queued', resolved_at=null
                    """,
                    (
                        learner_id,
                        assigned["question_id"],
                        session["lesson_key"],
                        attempt_id,
                    ),
                )
            if session["mode"] == "retry_review" and correct:
                connection.execute(
                    """
                    update english_retry_queue set state='resolved', resolved_at=now()
                    where student_id=%s and question_id=%s
                    """,
                    (learner_id, assigned["question_id"]),
                )
            return response

    def record_classification(
        self, learner_id: str, attempt_id: str, category: str
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            self._set_identity(connection, learner_id)
            attempt = connection.execute(
                """
                select id, is_correct from english_objective_attempts
                where id=%s and student_id=%s
                """,
                (attempt_id, learner_id),
            ).fetchone()
            if attempt is None:
                raise EnglishLearningError(
                    "english_attempt_not_found", "The English attempt was not found.", 404
                )
            if attempt["is_correct"]:
                raise EnglishLearningError(
                    "english_error_classification_not_required",
                    "Correct attempts do not require an error category.",
                    409,
                )
            existing = connection.execute(
                "select category::text from english_error_classifications where attempt_id=%s",
                (attempt_id,),
            ).fetchone()
            if existing and existing["category"] != category:
                raise EnglishLearningError(
                    "english_error_already_classified",
                    "This attempt already has an immutable error category.",
                    409,
                )
            if existing is None:
                connection.execute(
                    """
                    insert into english_error_classifications (attempt_id, student_id, category)
                    values (%s, %s, %s)
                    """,
                    (attempt_id, learner_id, category),
                )
            return {"attempt_id": attempt_id, "category": category, "recorded": True}

    def retry_keys(self, learner_id: str, lesson_key: str) -> list[str]:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            rows = connection.execute(
                """
                select questions.stable_key from english_retry_queue retry
                join english_objective_questions questions on questions.id=retry.question_id
                where retry.student_id=%s and retry.lesson_key=%s
                  and retry.state='queued' and retry.due_at <= now()
                order by retry.due_at, questions.stable_key
                """,
                (learner_id, lesson_key),
            ).fetchall()
            return [row["stable_key"] for row in rows]

    def retry_count(self, learner_id: str, lesson_key: str) -> int:
        return len(self.retry_keys(learner_id, lesson_key))

    def progress(self, learner_id: str) -> list[dict]:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            rows = connection.execute(
                """
                select progress.lesson_key, progress.lesson_revision,
                       progress.state::text as state, progress.question_count,
                       progress.resolved_count, progress.correct_count,
                       progress.incorrect_count,
                       progress.last_practice_session_id::text as last_session_id,
                       progress.updated_at::text,
                       count(retry.question_id) filter (where retry.state='queued')::integer
                           as retry_question_count
                from english_lesson_progress progress
                left join english_retry_queue retry
                  on retry.student_id=progress.student_id
                 and retry.lesson_key=progress.lesson_key
                where progress.student_id=%s
                group by progress.student_id, progress.lesson_key
                order by progress.updated_at desc
                """,
                (learner_id,),
            ).fetchall()
            return [dict(row) for row in rows]
