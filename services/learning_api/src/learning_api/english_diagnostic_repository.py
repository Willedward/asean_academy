"""Persistence for protected objective-English baseline and endline diagnostics."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .english_learning_repository import EnglishLearningError


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _band(percentage: float) -> str:
    if percentage < 50:
        return "foundation"
    if percentage < 75:
        return "developing"
    return "secure"


class EnglishDiagnosticRepository(Protocol):
    def latest(self, learner_id: str, purpose: str) -> dict | None: ...
    def create_session(
        self,
        learner_id: str,
        *,
        exam_profile_key: str,
        purpose: str,
        form_key: str,
        form_revision: int,
        title: str,
        questions: list[tuple[str, int, str]],
        expected_part_count: int,
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
        correct_parts: int,
        total_parts: int,
    ) -> dict: ...


class InMemoryEnglishDiagnosticRepository:
    def __init__(self):
        self.sessions: dict[str, dict] = {}
        self.assignments: dict[str, list[dict]] = {}
        self.attempts: dict[str, dict] = {}
        self.attempt_keys: dict[tuple[str, str], str] = {}
        self.session_keys: dict[tuple[str, str], str] = {}

    def _owned(self, learner_id: str, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if session is None or session["learner_id"] != learner_id:
            raise EnglishLearningError(
                "english_diagnostic_session_not_found",
                "The English diagnostic session was not found.",
                404,
            )
        return session

    def _summary(self, session: dict) -> dict:
        assigned = self.assignments[session["session_id"]]
        completed = session["status"] == "completed"
        raw_correct_parts = sum(item["correct_parts"] for item in assigned)
        raw_total_parts = sum(item["total_parts"] for item in assigned)
        correct_parts = raw_correct_parts if completed else 0
        total_parts = raw_total_parts if completed else 0
        score = raw_correct_parts / raw_total_parts if completed else None
        task_scores = []
        if completed:
            for task_type in sorted({item["task_type"] for item in assigned}):
                rows = [item for item in assigned if item["task_type"] == task_type]
                task_correct = sum(item["correct_parts"] for item in rows)
                task_total = sum(item["total_parts"] for item in rows)
                task_scores.append(
                    {
                        "task_type": task_type,
                        "correct_parts": task_correct,
                        "total_parts": task_total,
                        "percentage": round(100 * task_correct / task_total, 2),
                    }
                )
        return {
            "session_id": session["session_id"],
            "status": session["status"],
            "purpose": session["purpose"],
            "exam_profile_key": session["exam_profile_key"],
            "form_key": session["form_key"],
            "form_revision": session["form_revision"],
            "title": session["title"],
            "question_count": len(assigned),
            "expected_part_count": session["expected_part_count"],
            "resolved_count": sum(item["status"] != "pending" for item in assigned),
            "correct_parts": correct_parts,
            "total_parts": total_parts,
            "score": score,
            "percentage": round(score * 100, 2) if score is not None else None,
            "band": _band(score * 100) if score is not None else None,
            "task_scores": task_scores,
            "development_drafts": session["development_drafts"],
            "started_at": session["started_at"],
            "completed_at": session.get("completed_at"),
        }

    def latest(self, learner_id: str, purpose: str) -> dict | None:
        found = next(
            (
                session
                for session in reversed(list(self.sessions.values()))
                if session["learner_id"] == learner_id and session["purpose"] == purpose
            ),
            None,
        )
        return self._summary(found) if found else None

    def create_session(
        self,
        learner_id: str,
        *,
        exam_profile_key: str,
        purpose: str,
        form_key: str,
        form_revision: int,
        title: str,
        questions: list[tuple[str, int, str]],
        expected_part_count: int,
        idempotency_key: str,
        development_drafts: bool,
    ) -> dict:
        key = (learner_id, idempotency_key)
        if existing_id := self.session_keys.get(key):
            return self._summary(self.sessions[existing_id])
        latest = self.latest(learner_id, purpose)
        if latest is not None:
            self.session_keys[key] = latest["session_id"]
            return latest
        session_id = str(uuid4())
        session = {
            "session_id": session_id,
            "learner_id": learner_id,
            "status": "active",
            "purpose": purpose,
            "exam_profile_key": exam_profile_key,
            "form_key": form_key,
            "form_revision": form_revision,
            "title": title,
            "expected_part_count": expected_part_count,
            "development_drafts": development_drafts,
            "started_at": _now(),
        }
        self.sessions[session_id] = session
        self.assignments[session_id] = [
            {
                "position": position,
                "question_key": question_key,
                "question_revision": revision,
                "task_type": task_type,
                "status": "pending",
                "correct_parts": 0,
                "total_parts": 0,
            }
            for position, (question_key, revision, task_type) in enumerate(questions, 1)
        ]
        self.session_keys[key] = session_id
        return self._summary(session)

    def session(self, learner_id: str, session_id: str) -> dict:
        return self._summary(self._owned(learner_id, session_id))

    def next_assignment(self, learner_id: str, session_id: str) -> dict | None:
        self._owned(learner_id, session_id)
        return next(
            (dict(item) for item in self.assignments[session_id] if item["status"] == "pending"),
            None,
        )

    def attempt_by_idempotency(self, learner_id: str, idempotency_key: str) -> dict | None:
        attempt_id = self.attempt_keys.get((learner_id, idempotency_key))
        return dict(self.attempts[attempt_id]) if attempt_id else None

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
        correct_parts: int,
        total_parts: int,
    ) -> dict:
        if replay := self.attempt_by_idempotency(learner_id, idempotency_key):
            return replay
        session = self._owned(learner_id, session_id)
        if session["status"] != "active":
            raise EnglishLearningError(
                "english_diagnostic_completed", "This English diagnostic is complete.", 409
            )
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
                "english_diagnostic_question_not_pending",
                "Answer the currently assigned English diagnostic question.",
                409,
            )
        assignment.update(
            status="correct" if correct_parts == total_parts else "incorrect",
            correct_parts=correct_parts,
            total_parts=total_parts,
        )
        if all(item["status"] != "pending" for item in self.assignments[session_id]):
            session["status"] = "completed"
            session["completed_at"] = _now()
        response = {
            "attempt_id": attempt_id,
            "accepted": True,
            "diagnostic_completed": session["status"] == "completed",
            "session": self._summary(session),
        }
        self.attempts[attempt_id] = response
        self.attempt_keys[(learner_id, idempotency_key)] = attempt_id
        return response


class PostgresEnglishDiagnosticRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def _set_identity(connection, learner_id: str) -> None:
        connection.execute("select set_config('request.jwt.claim.sub', %s, true)", (learner_id,))

    @staticmethod
    def _owned(connection, learner_id: str, session_id: str, *, lock: bool = False):
        suffix = " for update" if lock else ""
        row = connection.execute(
            "select * from english_diagnostic_sessions where id=%s and student_id=%s" + suffix,
            (session_id, learner_id),
        ).fetchone()
        if row is None:
            raise EnglishLearningError(
                "english_diagnostic_session_not_found",
                "The English diagnostic session was not found.",
                404,
            )
        return row

    @staticmethod
    def _summary(connection, session: dict) -> dict:
        totals = connection.execute(
            """
            select count(*)::integer as question_count,
                   count(*) filter (where status <> 'pending')::integer as resolved_count,
                   coalesce(sum(correct_parts), 0)::integer as correct_parts,
                   coalesce(sum(total_parts), 0)::integer as total_parts
            from english_diagnostic_session_questions where diagnostic_session_id=%s
            """,
            (session["id"],),
        ).fetchone()
        task_scores = []
        if session["status"] == "completed":
            rows = connection.execute(
                """
                select task_type, sum(correct_parts)::integer as correct_parts,
                       sum(total_parts)::integer as total_parts
                from english_diagnostic_session_questions
                where diagnostic_session_id=%s group by task_type order by task_type
                """,
                (session["id"],),
            ).fetchall()
            task_scores = [
                {
                    "task_type": row["task_type"],
                    "correct_parts": row["correct_parts"],
                    "total_parts": row["total_parts"],
                    "percentage": round(100 * row["correct_parts"] / row["total_parts"], 2),
                }
                for row in rows
            ]
        completed = session["status"] == "completed"
        score = float(session["score"]) if completed and session["score"] is not None else None
        return {
            "session_id": str(session["id"]),
            "status": session["status"],
            "purpose": session["purpose"],
            "exam_profile_key": session["exam_profile_key"],
            "form_key": session["form_key"],
            "form_revision": session["form_revision"],
            "title": session["title"],
            "question_count": totals["question_count"],
            "expected_part_count": session["expected_part_count"],
            "resolved_count": totals["resolved_count"],
            "correct_parts": totals["correct_parts"] if completed else 0,
            "total_parts": totals["total_parts"] if completed else 0,
            "score": score,
            "percentage": round(score * 100, 2) if score is not None else None,
            "band": _band(score * 100) if score is not None else None,
            "task_scores": task_scores,
            "development_drafts": session["development_drafts"],
            "started_at": session["started_at"],
            "completed_at": session["completed_at"],
        }

    def latest(self, learner_id: str, purpose: str) -> dict | None:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            row = connection.execute(
                """
                select * from english_diagnostic_sessions
                where student_id=%s and purpose=%s order by started_at desc limit 1
                """,
                (learner_id, purpose),
            ).fetchone()
            return self._summary(connection, row) if row else None

    def create_session(
        self,
        learner_id: str,
        *,
        exam_profile_key: str,
        purpose: str,
        form_key: str,
        form_revision: int,
        title: str,
        questions: list[tuple[str, int, str]],
        expected_part_count: int,
        idempotency_key: str,
        development_drafts: bool,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            self._set_identity(connection, learner_id)
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-diagnostic:{learner_id}:{purpose}",),
            )
            existing = connection.execute(
                """
                select sessions.* from english_diagnostic_session_idempotency_keys keys
                join english_diagnostic_sessions sessions on sessions.id=keys.diagnostic_session_id
                where keys.student_id=%s and keys.idempotency_key=%s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if existing:
                return self._summary(connection, existing)
            latest = connection.execute(
                """
                select * from english_diagnostic_sessions
                where student_id=%s and purpose=%s order by started_at desc limit 1
                """,
                (learner_id, purpose),
            ).fetchone()
            if latest:
                connection.execute(
                    """
                    insert into english_diagnostic_session_idempotency_keys
                        (student_id, idempotency_key, diagnostic_session_id)
                    values (%s, %s, %s)
                    """,
                    (learner_id, idempotency_key, latest["id"]),
                )
                return self._summary(connection, latest)
            session = connection.execute(
                """
                insert into english_diagnostic_sessions (
                    student_id, exam_profile_key, purpose, form_key, form_revision,
                    title, expected_part_count, development_drafts
                ) values (%s,%s,%s,%s,%s,%s,%s,%s) returning *
                """,
                (
                    learner_id,
                    exam_profile_key,
                    purpose,
                    form_key,
                    form_revision,
                    title,
                    expected_part_count,
                    development_drafts,
                ),
            ).fetchone()
            for position, (question_key, revision, task_type) in enumerate(questions, 1):
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
                        "The assigned English diagnostic revision has not been imported.",
                        503,
                    )
                connection.execute(
                    """
                    insert into english_diagnostic_session_questions (
                        diagnostic_session_id, question_version_id, position, task_type
                    ) values (%s,%s,%s,%s)
                    """,
                    (session["id"], question["id"], position, task_type),
                )
            connection.execute(
                """
                insert into english_diagnostic_session_idempotency_keys
                    (student_id, idempotency_key, diagnostic_session_id)
                values (%s,%s,%s)
                """,
                (learner_id, idempotency_key, session["id"]),
            )
            return self._summary(connection, session)

    def session(self, learner_id: str, session_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            return self._summary(connection, self._owned(connection, learner_id, session_id))

    def next_assignment(self, learner_id: str, session_id: str) -> dict | None:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            session = self._owned(connection, learner_id, session_id)
            row = connection.execute(
                """
                select assigned.position, questions.stable_key as question_key,
                       versions.revision as question_revision, assigned.task_type
                from english_diagnostic_session_questions assigned
                join english_objective_question_versions versions
                  on versions.id=assigned.question_version_id
                join english_objective_questions questions on questions.id=versions.question_id
                where assigned.diagnostic_session_id=%s and assigned.status='pending'
                order by assigned.position limit 1
                """,
                (session["id"],),
            ).fetchone()
            return dict(row) if row else None

    def attempt_by_idempotency(self, learner_id: str, idempotency_key: str) -> dict | None:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            row = connection.execute(
                """
                select attempts.id as attempt_id, sessions.*
                from english_diagnostic_attempts attempts
                join english_diagnostic_session_questions assigned
                  on assigned.id=attempts.diagnostic_session_question_id
                join english_diagnostic_sessions sessions
                  on sessions.id=assigned.diagnostic_session_id
                where attempts.student_id=%s and attempts.idempotency_key=%s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if row is None:
                return None
            return {
                "attempt_id": str(row["attempt_id"]),
                "accepted": True,
                "diagnostic_completed": row["status"] == "completed",
                "session": self._summary(connection, row),
            }

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
        correct_parts: int,
        total_parts: int,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            self._set_identity(connection, learner_id)
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-diagnostic-attempt:{learner_id}:{idempotency_key}",),
            )
            replay = self.attempt_by_idempotency(learner_id, idempotency_key)
            if replay:
                return replay
            session = self._owned(connection, learner_id, session_id, lock=True)
            if session["status"] != "active":
                raise EnglishLearningError(
                    "english_diagnostic_completed", "This English diagnostic is complete.", 409
                )
            assigned = connection.execute(
                """
                select assigned.id, assigned.status
                from english_diagnostic_session_questions assigned
                join english_objective_question_versions versions
                  on versions.id=assigned.question_version_id
                join english_objective_questions questions on questions.id=versions.question_id
                where assigned.diagnostic_session_id=%s and questions.stable_key=%s
                  and versions.revision=%s for update of assigned
                """,
                (session["id"], question_key, question_revision),
            ).fetchone()
            if assigned is None or assigned["status"] != "pending":
                raise EnglishLearningError(
                    "english_diagnostic_question_not_pending",
                    "Answer the currently assigned English diagnostic question.",
                    409,
                )
            connection.execute(
                """
                update english_diagnostic_session_questions
                set status=%s, correct_parts=%s, total_parts=%s, resolved_at=now()
                where id=%s
                """,
                (
                    "correct" if correct_parts == total_parts else "incorrect",
                    correct_parts,
                    total_parts,
                    assigned["id"],
                ),
            )
            connection.execute(
                """
                insert into english_diagnostic_attempts (
                    id, student_id, diagnostic_session_question_id, idempotency_key,
                    answers, correct_parts, total_parts
                ) values (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    attempt_id,
                    learner_id,
                    assigned["id"],
                    idempotency_key,
                    Jsonb(answers),
                    correct_parts,
                    total_parts,
                ),
            )
            totals = connection.execute(
                """
                select count(*) filter (where status='pending')::integer as pending,
                       coalesce(sum(correct_parts),0)::integer as correct_parts,
                       coalesce(sum(total_parts),0)::integer as total_parts
                from english_diagnostic_session_questions where diagnostic_session_id=%s
                """,
                (session["id"],),
            ).fetchone()
            if totals["pending"] == 0:
                if totals["total_parts"] != session["expected_part_count"]:
                    raise EnglishLearningError(
                        "english_diagnostic_part_count_mismatch",
                        "The completed diagnostic did not match its protected form contract.",
                        409,
                    )
                score = totals["correct_parts"] / totals["total_parts"]
                session = connection.execute(
                    """
                    update english_diagnostic_sessions
                    set status='completed', score=%s, completed_at=now()
                    where id=%s returning *
                    """,
                    (score, session["id"]),
                ).fetchone()
            return {
                "attempt_id": attempt_id,
                "accepted": True,
                "diagnostic_completed": session["status"] == "completed",
                "session": self._summary(connection, session),
            }
