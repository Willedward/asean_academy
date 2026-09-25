"""PostgreSQL practice adapter matching the local deterministic PracticeEngine contract."""

from __future__ import annotations

import hashlib
import json
import random
import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from question_bank.checking import check_answer
from question_bank.models import NumericResponse, Question
from question_bank.practice import PracticeError, public_question, solution_for


def _fingerprint(value: dict) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _canonical_submission(response) -> str:
    if isinstance(response, NumericResponse):
        return response.canonical_answer
    if response.comparison_mode == "prime_factorisation":
        return response.canonical_latex
    return response.canonical_expression


class PostgresPracticeEngine:
    """Persist learner-owned practice atomically in the production PostgreSQL schema."""

    def __init__(
        self,
        database_url: str,
        questions: list[Question],
        learner_id: str,
        *,
        allow_drafts: bool = False,
        rng: random.Random | random.SystemRandom | None = None,
    ):
        self.database_url = database_url
        self.learner_id = str(uuid.UUID(learner_id))
        allowed = questions if allow_drafts else [q for q in questions if q.status == "published"]
        self.questions = {question.stable_key: question for question in allowed}
        self.bank_key = questions[0].bank_key if questions else "g3-sec1-n1-v1"
        self.development_drafts = any(q.status != "published" for q in allowed)
        self.rng = rng or random.SystemRandom()

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            connect_timeout=10,
            row_factory=dict_row,
        )

    def _set_identity(self, connection) -> None:
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)",
            (self.learner_id,),
        )

    def _question(self, key: str, revision: int | None = None) -> Question:
        question = self.questions.get(key)
        if question is None or (revision is not None and question.revision != revision):
            raise PracticeError(
                "question_revision_unavailable",
                "The assigned question revision is unavailable.",
                409,
            )
        return question

    def _bank_id(self, connection):
        row = connection.execute(
            "select id from math_question_banks where bank_key = %s",
            (self.bank_key,),
        ).fetchone()
        if row is None:
            raise PracticeError(
                "question_bank_not_imported",
                "The question bank has not been imported into PostgreSQL.",
                503,
            )
        return row["id"]

    def _question_ids(self, connection, key: str, revision: int):
        row = connection.execute(
            """
            select questions.id as question_id, versions.id as question_version_id
            from math_questions questions
            join math_question_banks banks on banks.id = questions.bank_id
            join math_question_versions versions on versions.question_id = questions.id
            where banks.bank_key = %s
              and questions.stable_key = %s
              and versions.revision = %s
            """,
            (self.bank_key, key, revision),
        ).fetchone()
        if row is None:
            raise PracticeError(
                "question_revision_not_imported",
                "The selected question revision has not been imported into PostgreSQL.",
                503,
            )
        return row

    def _session(self, connection, session_id: str, *, lock: bool = False):
        query = """
            select * from practice_sessions
            where id = %s and student_id = %s
        """
        if lock:
            query += " for update"
        row = connection.execute(query, (session_id, self.learner_id)).fetchone()
        if row is None:
            raise PracticeError("session_not_found", "Practice session was not found.", 404)
        return row

    def _creation_response(self, session) -> dict:
        scope = session["scope"]
        return {
            "session_id": str(session["id"]),
            "status": session["status"],
            "question_count": session["requested_question_count"],
            "lesson_key": scope.get("lesson_key"),
            "unit_key": scope.get("unit_key"),
            "mode": scope.get("mode"),
            "development_drafts": self.development_drafts,
        }

    def _summary(self, connection, session) -> dict:
        counts = connection.execute(
            """
            select
                count(*)::integer as assigned_count,
                count(*) filter (where status <> 'pending')::integer as resolved_count,
                count(*) filter (where status = 'correct')::integer as correct_count,
                count(*) filter (where status = 'incorrect')::integer as incorrect_count,
                count(*) filter (where status = 'gave_up')::integer as gave_up_count
            from session_questions where practice_session_id = %s
            """,
            (session["id"],),
        ).fetchone()
        scope = session["scope"]
        return {
            "session_id": str(session["id"]),
            "status": session["status"],
            "question_count": session["requested_question_count"],
            "assigned_count": counts["assigned_count"],
            "resolved_count": counts["resolved_count"],
            "correct_count": counts["correct_count"],
            "incorrect_count": counts["incorrect_count"],
            "gave_up_count": counts["gave_up_count"],
            "lesson_key": scope.get("lesson_key"),
            "unit_key": scope.get("unit_key"),
            "mode": scope.get("mode"),
            "development_drafts": self.development_drafts,
        }

    def create_session(
        self,
        *,
        question_count: int = 5,
        difficulties: list[int] | None = None,
        outcomes: list[str] | None = None,
        ordered_question_keys: list[str] | None = None,
        context: dict[str, str | dict[str, str]] | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        if not self.questions:
            raise PracticeError(
                "no_published_questions", "No published questions are available.", 409
            )
        if idempotency_key is not None and not 1 <= len(idempotency_key) <= 200:
            raise PracticeError("invalid_idempotency_key", "Supply a non-empty idempotency key.")
        difficulties = sorted(set(difficulties or [1, 2, 3]))
        outcomes = sorted(set(outcomes or []))
        if not difficulties or any(level not in {1, 2, 3} for level in difficulties):
            raise PracticeError("invalid_difficulties", "difficulties must contain levels 1, 2, or 3.")
        ordered_question_keys = list(ordered_question_keys or [])
        if len(ordered_question_keys) != len(set(ordered_question_keys)):
            raise PracticeError("invalid_question_pool", "Question-pool keys must be unique.")
        pool_keys = set(ordered_question_keys)
        eligible = [
            question
            for question in self.questions.values()
            if question.difficulty in difficulties
            and (not outcomes or question.primary_outcome in outcomes)
            and (not pool_keys or question.stable_key in pool_keys)
        ]
        if pool_keys - set(self.questions):
            raise PracticeError(
                "question_pool_unavailable",
                "One or more configured question revisions are unavailable.",
                409,
            )
        maximum = min(40, len(eligible))
        if not 1 <= question_count <= maximum:
            raise PracticeError(
                "invalid_question_count", f"question_count must be between 1 and {maximum}."
            )
        scope = {
            "difficulties": difficulties,
            "outcomes": outcomes,
            "question_keys": ordered_question_keys,
            **(context or {}),
        }
        fingerprint = _fingerprint({"question_count": question_count, "scope": scope})
        with self._connect() as connection:
            self._set_identity(connection)
            if idempotency_key is not None:
                connection.execute(
                    "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (f"{self.learner_id}:{idempotency_key}",),
                )
                existing = connection.execute(
                    """
                    select keys.request_fingerprint, sessions.*
                    from practice_session_idempotency_keys keys
                    join practice_sessions sessions on sessions.id = keys.practice_session_id
                    where keys.student_id = %s and keys.idempotency_key = %s
                    """,
                    (self.learner_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    if existing["request_fingerprint"] != fingerprint:
                        raise PracticeError(
                            "idempotency_key_reused",
                            "This idempotency key was already used for different session data.",
                            409,
                        )
                    return self._creation_response(existing)
            context_name = "lesson_key" if scope.get("lesson_key") else "unit_key"
            context_key = scope.get(context_name)
            if context_key:
                connection.execute(
                    "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (f"{self.learner_id}:{context_name}:{context_key}",),
                )
                active = connection.execute(
                    """
                    select * from practice_sessions
                    where student_id = %s
                      and status = 'active'
                      and scope->>%s = %s
                    order by created_at desc
                    limit 1
                    """,
                    (self.learner_id, context_name, context_key),
                ).fetchone()
                if active is not None:
                    if idempotency_key is not None:
                        connection.execute(
                            """
                            insert into practice_session_idempotency_keys (
                                student_id, idempotency_key, practice_session_id,
                                request_fingerprint
                            ) values (%s, %s, %s, %s)
                            """,
                            (
                                self.learner_id,
                                idempotency_key,
                                active["id"],
                                fingerprint,
                            ),
                        )
                    return self._creation_response(active)
            session = connection.execute(
                """
                insert into practice_sessions (
                    student_id, bank_id, requested_question_count, scope
                ) values (%s, %s, %s, %s)
                returning *
                """,
                (self.learner_id, self._bank_id(connection), question_count, Jsonb(scope)),
            ).fetchone()
            if idempotency_key is not None:
                connection.execute(
                    """
                    insert into practice_session_idempotency_keys (
                        student_id, idempotency_key, practice_session_id, request_fingerprint
                    ) values (%s, %s, %s, %s)
                    """,
                    (self.learner_id, idempotency_key, session["id"], fingerprint),
                )
            return self._creation_response(session)

    def session_summary(self, session_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection)
            return self._summary(connection, self._session(connection, session_id))

    def _select(self, connection, session):
        assigned_rows = connection.execute(
            """
            select questions.stable_key, questions.difficulty
            from session_questions assigned
            join math_question_versions versions on versions.id = assigned.question_version_id
            join math_questions questions on questions.id = versions.question_id
            where assigned.practice_session_id = %s
            """,
            (session["id"],),
        ).fetchall()
        assigned = {row["stable_key"] for row in assigned_rows}
        difficulty_counts = {1: 0, 2: 0, 3: 0}
        for row in assigned_rows:
            difficulty_counts[row["difficulty"]] += 1
        progress_rows = connection.execute(
            """
            select questions.stable_key, progress.state::text as state,
                   progress.last_attempted_at
            from question_progress progress
            join math_questions questions on questions.id = progress.question_id
            where progress.student_id = %s
            """,
            (self.learner_id,),
        ).fetchall()
        progress = {row["stable_key"]: row for row in progress_rows}
        scope = session["scope"]
        candidates = [
            question
            for question in self.questions.values()
            if question.stable_key not in assigned
            and question.difficulty in scope["difficulties"]
            and (not scope["outcomes"] or question.primary_outcome in scope["outcomes"])
            and (not scope.get("question_keys") or question.stable_key in scope["question_keys"])
        ]
        if not candidates:
            return None
        if scope.get("question_keys"):
            by_key = {question.stable_key: question for question in candidates}
            selected = next(by_key[key] for key in scope["question_keys"] if key in by_key)
            return selected, scope.get("selection_reason", "configured_lesson_pool")
        ranked = []
        for question in candidates:
            state = progress.get(question.stable_key)
            if state is not None and state["state"] in {"queued_for_retry", "gave_up"}:
                priority, reason = 0, "required_retry"
            elif state is None:
                priority, reason = 1, "unseen"
            else:
                priority, reason = 2, "least_recently_attempted"
            last_attempt = state["last_attempted_at"] if state is not None else None
            ranked.append(
                (
                    priority,
                    difficulty_counts[question.difficulty],
                    last_attempt.isoformat() if last_attempt else "",
                    self.rng.random(),
                    question,
                    reason,
                )
            )
        _, _, _, _, question, reason = min(ranked, key=lambda item: item[:4])
        return question, reason

    def retry_question_keys(self, eligible_keys: list[str]) -> list[str]:
        if not eligible_keys:
            return []
        with self._connect() as connection:
            self._set_identity(connection)
            rows = connection.execute(
                """
                select questions.stable_key
                from question_progress progress
                join math_questions questions on questions.id = progress.question_id
                where progress.student_id = %s
                  and progress.state in ('queued_for_retry', 'gave_up')
                  and questions.stable_key = any(%s)
                order by progress.last_attempted_at nulls first, questions.stable_key
                """,
                (self.learner_id, eligible_keys),
            ).fetchall()
        return [row["stable_key"] for row in rows]

    def next_question(self, session_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection)
            session = self._session(connection, session_id, lock=True)
            pending = connection.execute(
                """
                select assigned.*, questions.stable_key, versions.revision
                from session_questions assigned
                join math_question_versions versions on versions.id = assigned.question_version_id
                join math_questions questions on questions.id = versions.question_id
                where assigned.practice_session_id = %s and assigned.status = 'pending'
                order by assigned.position limit 1
                """,
                (session["id"],),
            ).fetchone()
            if pending is None and session["status"] == "active":
                assigned_count = connection.execute(
                    "select count(*) from session_questions where practice_session_id = %s",
                    (session["id"],),
                ).fetchone()["count"]
                if assigned_count >= session["requested_question_count"]:
                    connection.execute(
                        """
                        update practice_sessions set status = 'completed', completed_at = now()
                        where id = %s
                        """,
                        (session["id"],),
                    )
                else:
                    candidate = self._select(connection, session)
                    if candidate is None:
                        connection.execute(
                            """
                            update practice_sessions set status = 'completed', completed_at = now()
                            where id = %s
                            """,
                            (session["id"],),
                        )
                    else:
                        question, reason = candidate
                        ids = self._question_ids(connection, question.stable_key, question.revision)
                        pending = connection.execute(
                            """
                            insert into session_questions (
                                practice_session_id, question_version_id, position,
                                status, selection_reason
                            ) values (%s, %s, %s, 'pending', %s)
                            returning *, %s::text as stable_key, %s::integer as revision
                            """,
                            (
                                session["id"],
                                ids["question_version_id"],
                                assigned_count + 1,
                                reason,
                                question.stable_key,
                                question.revision,
                            ),
                        ).fetchone()
            session = self._session(connection, session_id)
            summary = self._summary(connection, session)
            if pending is None:
                return {"status": "completed", "session": summary, "question": None}
            question = self._question(pending["stable_key"], pending["revision"])
            attempt_count = connection.execute(
                "select count(*) from attempts where session_question_id = %s",
                (pending["id"],),
            ).fetchone()["count"]
            return {
                "status": "active",
                "session": summary,
                "position": pending["position"],
                "selection_reason": pending["selection_reason"],
                "stage": session["scope"].get("stages", {}).get(question.stable_key),
                "attempt_count": attempt_count,
                "highest_hint_stage": pending["highest_hint_stage"],
                "solution_available": pending["incorrect_attempts"] >= 2,
                "question": public_question(question),
            }

    def submit_attempt(
        self,
        *,
        session_id: str,
        stable_key: str,
        revision: int,
        answers: dict,
        idempotency_key: str,
    ) -> dict:
        if not isinstance(answers, dict):
            raise PracticeError("invalid_answers", "answers must be an object keyed by part position.")
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 200:
            raise PracticeError("invalid_idempotency_key", "Supply a non-empty idempotency key.")
        with self._connect() as connection:
            self._set_identity(connection)
            session = self._session(connection, session_id, lock=True)
            checkpoint = session["scope"].get("mode") == "checkpoint"
            existing = connection.execute(
                """
                select attempts.answers, attempts.result, assigned.practice_session_id,
                       questions.stable_key, versions.revision
                from attempts
                join session_questions assigned on assigned.id = attempts.session_question_id
                join math_question_versions versions on versions.id = attempts.question_version_id
                join math_questions questions on questions.id = versions.question_id
                where attempts.student_id = %s and attempts.idempotency_key = %s
                """,
                (self.learner_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["practice_session_id"]) != session_id
                    or existing["stable_key"] != stable_key
                    or existing["revision"] != revision
                    or existing["answers"] != answers
                ):
                    raise PracticeError(
                        "idempotency_key_reused",
                        "This idempotency key was already used for different attempt data.",
                        409,
                    )
                return existing["result"]
            assignment = connection.execute(
                """
                select assigned.*, versions.revision, versions.id as question_version_id,
                       questions.id as question_id, questions.stable_key
                from session_questions assigned
                join math_question_versions versions on versions.id = assigned.question_version_id
                join math_questions questions on questions.id = versions.question_id
                where assigned.practice_session_id = %s
                  and questions.stable_key = %s
                  and assigned.status = 'pending'
                for update of assigned
                """,
                (session_id, stable_key),
            ).fetchone()
            if assignment is None or assignment["revision"] != revision:
                raise PracticeError(
                    "question_not_current",
                    "This question is not the current unresolved assignment.",
                    409,
                )
            question = self._question(stable_key, revision)
            attempt_number = connection.execute(
                "select count(*) from attempts where session_question_id = %s",
                (assignment["id"],),
            ).fetchone()["count"] + 1
            part_results = []
            marks_awarded = 0
            for part in question.parts:
                answer = str(answers.get(str(part.position), answers.get(part.position, "")))
                checked = check_answer(part.response, answer)
                if checked["correct"]:
                    marks_awarded += part.marks
                part_results.append(
                    {
                        "position": part.position,
                        "correct": checked["correct"],
                        "error": checked["error"],
                        "marks_awarded": part.marks if checked["correct"] else 0,
                        "marks_available": part.marks,
                    }
                )
            correct = all(result["correct"] for result in part_results)
            incorrect_attempts = assignment["incorrect_attempts"] + (0 if correct else 1)
            result = {
                "attempt_number": attempt_number,
                "correct": correct,
                "parts": part_results,
                "marks_awarded": marks_awarded,
                "marks_available": question.total_marks,
                "question_finished": correct or checkpoint,
                "solution_available": (
                    False if checkpoint else not correct and incorrect_attempts >= 2
                ),
            }
            connection.execute(
                """
                insert into attempts (
                    student_id, session_question_id, question_version_id, attempt_number,
                    idempotency_key, answers, result, is_correct, marks_awarded
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    self.learner_id,
                    assignment["id"],
                    assignment["question_version_id"],
                    attempt_number,
                    idempotency_key,
                    Jsonb(answers),
                    Jsonb(result),
                    correct,
                    marks_awarded,
                ),
            )
            connection.execute(
                """
                update session_questions
                set status = %s, incorrect_attempts = %s,
                    resolved_at = case when %s then now() else null end
                where id = %s
                """,
                (
                    "correct" if correct else ("incorrect" if checkpoint else "pending"),
                    incorrect_attempts,
                    correct or checkpoint,
                    assignment["id"],
                ),
            )
            state = "correct" if correct else "queued_for_retry"
            connection.execute(
                """
                insert into question_progress (
                    student_id, question_id, latest_question_version_id, state,
                    attempts_total, incorrect_total, correct_total, last_attempted_at
                ) values (%s, %s, %s, %s, 1, %s, %s, now())
                on conflict (student_id, question_id) do update set
                    latest_question_version_id = excluded.latest_question_version_id,
                    state = excluded.state,
                    attempts_total = question_progress.attempts_total + 1,
                    incorrect_total = question_progress.incorrect_total + excluded.incorrect_total,
                    correct_total = question_progress.correct_total + excluded.correct_total,
                    last_attempted_at = excluded.last_attempted_at,
                    updated_at = now()
                """,
                (
                    self.learner_id,
                    assignment["question_id"],
                    assignment["question_version_id"],
                    state,
                    0 if correct else 1,
                    1 if correct else 0,
                ),
            )
            return result

    def reveal_hint(self, session_id: str, stable_key: str, stage: int) -> dict:
        if stage not in {1, 2}:
            raise PracticeError("invalid_hint_stage", "Hint stage must be 1 or 2.")
        with self._connect() as connection:
            self._set_identity(connection)
            session = self._session(connection, session_id)
            if session["scope"].get("mode") == "checkpoint":
                raise PracticeError(
                    "checkpoint_support_locked",
                    "Hints are unavailable during a checkpoint.",
                    403,
                )
            assignment = connection.execute(
                """
                select assigned.*, versions.revision
                from session_questions assigned
                join math_question_versions versions on versions.id = assigned.question_version_id
                join math_questions questions on questions.id = versions.question_id
                where assigned.practice_session_id = %s
                  and questions.stable_key = %s
                  and assigned.status = 'pending'
                for update of assigned
                """,
                (session_id, stable_key),
            ).fetchone()
            if assignment is None:
                raise PracticeError("question_not_current", "This question is not current.", 409)
            if stage == 2 and assignment["highest_hint_stage"] < 1:
                raise PracticeError("hint_order", "Open hint 1 before hint 2.", 409)
            question = self._question(stable_key, assignment["revision"])
            connection.execute(
                """
                update session_questions
                set highest_hint_stage = greatest(highest_hint_stage, %s)
                where id = %s
                """,
                (stage, assignment["id"]),
            )
            return {
                "stage": stage,
                "parts": [
                    {
                        "position": part.position,
                        "content": [
                            block.model_dump(mode="json")
                            for block in next(h for h in part.hints if h.stage == stage).content
                        ],
                    }
                    for part in question.parts
                ],
            }

    def give_up(self, session_id: str, stable_key: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection)
            session = self._session(connection, session_id, lock=True)
            if session["scope"].get("mode") == "checkpoint":
                raise PracticeError(
                    "checkpoint_support_locked",
                    "Give up and solutions are unavailable during a checkpoint.",
                    403,
                )
            assignment = connection.execute(
                """
                select assigned.*, versions.revision,
                       versions.id as question_version_id, questions.id as question_id
                from session_questions assigned
                join math_question_versions versions on versions.id = assigned.question_version_id
                join math_questions questions on questions.id = versions.question_id
                where assigned.practice_session_id = %s
                  and questions.stable_key = %s
                  and assigned.status = 'pending'
                for update of assigned
                """,
                (session_id, stable_key),
            ).fetchone()
            if assignment is None:
                raise PracticeError("question_not_current", "This question is not current.", 409)
            if assignment["incorrect_attempts"] < 2:
                raise PracticeError(
                    "solution_locked", "The solution unlocks after two incorrect attempts.", 403
                )
            question = self._question(stable_key, assignment["revision"])
            connection.execute(
                """
                update session_questions set status = 'gave_up', resolved_at = now()
                where id = %s
                """,
                (assignment["id"],),
            )
            connection.execute(
                """
                insert into question_progress (
                    student_id, question_id, latest_question_version_id, state
                ) values (%s, %s, %s, 'gave_up')
                on conflict (student_id, question_id) do update set
                    latest_question_version_id = excluded.latest_question_version_id,
                    state = excluded.state,
                    updated_at = now()
                """,
                (
                    self.learner_id,
                    assignment["question_id"],
                    assignment["question_version_id"],
                ),
            )
            return {"status": "gave_up", "solution": solution_for(question)}
