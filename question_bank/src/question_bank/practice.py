"""Practice-session domain service with a persistent local SQLite adapter."""

from __future__ import annotations

import json
import random
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .checking import check_answer
from .models import NumericResponse, Question


class PracticeError(ValueError):
    """A safe error that can be returned by the practice API."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json(value) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _response_placeholder(response) -> str:
    if isinstance(response, NumericResponse):
        return "Enter a number, decimal, fraction, or percentage"
    modes = {
        "prime_factorisation": "Enter a product of prime factors",
        "ordered_numeric_list": "Enter values in the required order",
        "exact_relation": "Enter the complete inequality or relation",
    }
    return modes.get(response.comparison_mode, "Enter a mathematical expression")


def public_question(question: Question) -> dict:
    """Return student-visible content without answer specifications or solutions."""

    return {
        "stable_key": question.stable_key,
        "revision": question.revision,
        "title": question.title,
        "difficulty": question.difficulty,
        "primary_outcome": question.primary_outcome,
        "calculator_allowed": question.calculator_allowed,
        "total_marks": question.total_marks,
        "source_status": question.status,
        "stem": [block.model_dump(mode="json") for block in question.stem],
        "parts": [
            {
                "position": part.position,
                "label": part.label,
                "prompt": [block.model_dump(mode="json") for block in part.prompt],
                "marks": part.marks,
                "response_type": part.response.type,
                "input_placeholder": _response_placeholder(part.response),
            }
            for part in question.parts
        ],
        "assets": [
            {
                "asset_key": asset.asset_key,
                "kind": asset.kind,
                "format": asset.format,
                "path": asset.path,
                "alt_text": asset.alt_text,
                "width": asset.width,
                "height": asset.height,
            }
            for asset in question.assets
        ],
    }


def _canonical_submission(response) -> str:
    if isinstance(response, NumericResponse):
        return response.canonical_answer
    if response.comparison_mode == "prime_factorisation":
        return response.canonical_latex
    return response.canonical_expression


def solution_for(question: Question) -> dict:
    return {
        "stable_key": question.stable_key,
        "revision": question.revision,
        "parts": [
            {
                "position": part.position,
                "label": part.label,
                "canonical_answer": _canonical_submission(part.response),
                "canonical_latex": part.response.canonical_latex,
                "steps": [step.model_dump(mode="json") for step in part.solution],
            }
            for part in question.parts
        ],
    }


@dataclass(frozen=True)
class Candidate:
    question: Question
    reason: str


class PracticeEngine:
    """Coordinates selection and attempts while pinning question revisions."""

    def __init__(
        self,
        database: Path,
        questions: list[Question],
        *,
        allow_drafts: bool = False,
        rng: random.Random | random.SystemRandom | None = None,
    ):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        allowed = questions if allow_drafts else [q for q in questions if q.status == "published"]
        self.questions = {question.stable_key: question for question in allowed}
        self.bank_key = questions[0].bank_key if questions else "g3-sec1-n1-v1"
        self.development_drafts = any(q.status != "published" for q in allowed)
        self.rng = rng or random.SystemRandom()
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma foreign_keys = on")
        connection.execute("pragma busy_timeout = 10000")
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.executescript(
                """
                pragma journal_mode = wal;

                create table if not exists practice_sessions (
                    id text primary key,
                    bank_key text not null,
                    requested_count integer not null check (requested_count between 1 and 40),
                    scope_json text not null,
                    status text not null check (status in ('active', 'completed')),
                    created_at text not null,
                    completed_at text
                );

                create table if not exists session_idempotency_keys (
                    idempotency_key text primary key,
                    session_id text not null references practice_sessions(id) on delete cascade,
                    created_at text not null
                );

                create table if not exists session_questions (
                    session_id text not null references practice_sessions(id) on delete cascade,
                    question_key text not null,
                    question_revision integer not null,
                    position integer not null,
                    status text not null check (status in ('pending', 'correct', 'gave_up')),
                    selection_reason text not null,
                    incorrect_attempts integer not null default 0,
                    highest_hint_stage integer not null default 0 check (highest_hint_stage between 0 and 2),
                    assigned_at text not null,
                    resolved_at text,
                    primary key (session_id, position),
                    unique (session_id, question_key)
                );

                create table if not exists attempts (
                    id text primary key,
                    session_id text not null,
                    question_key text not null,
                    question_revision integer not null,
                    attempt_number integer not null,
                    idempotency_key text not null,
                    answers_json text not null,
                    result_json text not null,
                    is_correct integer not null,
                    marks_awarded integer not null,
                    created_at text not null,
                    unique (session_id, idempotency_key),
                    unique (session_id, question_key, attempt_number)
                );

                create table if not exists question_progress (
                    question_key text primary key,
                    question_revision integer not null,
                    state text not null check (
                        state in ('attempting', 'correct', 'gave_up', 'queued_for_retry')
                    ),
                    attempts_total integer not null default 0,
                    incorrect_total integer not null default 0,
                    correct_total integer not null default 0,
                    last_attempted_at text,
                    updated_at text not null
                );
                """
            )

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
                "no_published_questions",
                "No published questions are available. Use the local development-drafts flag only for review.",
                409,
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
                "invalid_question_count",
                f"question_count must be between 1 and {maximum}.",
            )
        session_id = str(uuid.uuid4())
        scope = {
            "difficulties": difficulties,
            "outcomes": outcomes,
            "question_keys": ordered_question_keys,
            **(context or {}),
        }
        with self._connect() as connection:
            if idempotency_key is not None:
                existing = connection.execute(
                    "select session_id from session_idempotency_keys where idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing is not None:
                    return self._creation_response(
                        self._session(connection, existing["session_id"])
                    )
            connection.execute(
                """
                insert into practice_sessions (
                    id, bank_key, requested_count, scope_json, status, created_at
                ) values (?, ?, ?, ?, 'active', ?)
                """,
                (session_id, self.bank_key, question_count, _json(scope), _now()),
            )
            if idempotency_key is not None:
                connection.execute(
                    "insert into session_idempotency_keys values (?, ?, ?)",
                    (idempotency_key, session_id, _now()),
                )
            return self._creation_response(self._session(connection, session_id))

    def _creation_response(self, session) -> dict:
        scope = json.loads(session["scope_json"])
        return {
            "session_id": session["id"],
            "status": session["status"],
            "question_count": session["requested_count"],
            "lesson_key": scope.get("lesson_key"),
            "mode": scope.get("mode"),
            "development_drafts": self.development_drafts,
        }

    def _session(self, connection, session_id: str):
        row = connection.execute(
            "select * from practice_sessions where id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise PracticeError("session_not_found", "Practice session was not found.", 404)
        return row

    def _question(self, key: str, revision: int | None = None) -> Question:
        question = self.questions.get(key)
        if question is None or (revision is not None and question.revision != revision):
            raise PracticeError(
                "question_revision_unavailable",
                "The assigned question revision is no longer available locally.",
                409,
            )
        return question

    def _select(self, connection, session) -> Candidate | None:
        scope = json.loads(session["scope_json"])
        assigned = {
            row["question_key"]
            for row in connection.execute(
                "select question_key from session_questions where session_id = ?",
                (session["id"],),
            )
        }
        difficulty_counts = {1: 0, 2: 0, 3: 0}
        for row in connection.execute(
            """
            select question_key from session_questions where session_id = ?
            """,
            (session["id"],),
        ):
            question = self.questions.get(row["question_key"])
            if question:
                difficulty_counts[question.difficulty] += 1

        progress = {
            row["question_key"]: row
            for row in connection.execute("select * from question_progress")
        }
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
            question = next(by_key[key] for key in scope["question_keys"] if key in by_key)
            return Candidate(question, "configured_lesson_pool")

        ranked = []
        for question in candidates:
            state = progress.get(question.stable_key)
            if state is not None and state["state"] in {"queued_for_retry", "gave_up"}:
                priority, reason = 0, "required_retry"
            elif state is None:
                priority, reason = 1, "unseen"
            else:
                priority, reason = 2, "least_recently_attempted"
            last_attempt = state["last_attempted_at"] if state is not None else ""
            ranked.append(
                (
                    priority,
                    difficulty_counts[question.difficulty],
                    last_attempt or "",
                    self.rng.random(),
                    question,
                    reason,
                )
            )
        _, _, _, _, question, reason = min(ranked, key=lambda item: item[:4])
        return Candidate(question, reason)

    def _summary(self, connection, session) -> dict:
        scope = json.loads(session["scope_json"])
        rows = connection.execute(
            "select status from session_questions where session_id = ?", (session["id"],)
        ).fetchall()
        resolved = sum(row["status"] != "pending" for row in rows)
        correct = sum(row["status"] == "correct" for row in rows)
        gave_up = sum(row["status"] == "gave_up" for row in rows)
        return {
            "session_id": session["id"],
            "status": session["status"],
            "question_count": session["requested_count"],
            "assigned_count": len(rows),
            "resolved_count": resolved,
            "correct_count": correct,
            "gave_up_count": gave_up,
            "lesson_key": scope.get("lesson_key"),
            "mode": scope.get("mode"),
            "development_drafts": self.development_drafts,
        }

    def session_summary(self, session_id: str) -> dict:
        with self._connect() as connection:
            return self._summary(connection, self._session(connection, session_id))

    def next_question(self, session_id: str) -> dict:
        with self._connect() as connection:
            session = self._session(connection, session_id)
            pending = connection.execute(
                """
                select * from session_questions
                where session_id = ? and status = 'pending'
                order by position limit 1
                """,
                (session_id,),
            ).fetchone()
            if pending is None and session["status"] == "active":
                assigned_count = connection.execute(
                    "select count(*) from session_questions where session_id = ?",
                    (session_id,),
                ).fetchone()[0]
                if assigned_count >= session["requested_count"]:
                    connection.execute(
                        """
                        update practice_sessions
                        set status = 'completed', completed_at = ? where id = ?
                        """,
                        (_now(), session_id),
                    )
                else:
                    candidate = self._select(connection, session)
                    if candidate is None:
                        connection.execute(
                            """
                            update practice_sessions
                            set status = 'completed', completed_at = ? where id = ?
                            """,
                            (_now(), session_id),
                        )
                    else:
                        position = assigned_count + 1
                        connection.execute(
                            """
                            insert into session_questions (
                                session_id, question_key, question_revision, position,
                                status, selection_reason, assigned_at
                            ) values (?, ?, ?, ?, 'pending', ?, ?)
                            """,
                            (
                                session_id,
                                candidate.question.stable_key,
                                candidate.question.revision,
                                position,
                                candidate.reason,
                                _now(),
                            ),
                        )
                        pending = connection.execute(
                            """
                            select * from session_questions
                            where session_id = ? and position = ?
                            """,
                            (session_id, position),
                        ).fetchone()
            session = self._session(connection, session_id)
            summary = self._summary(connection, session)
            if pending is None:
                return {"status": "completed", "session": summary, "question": None}
            question = self._question(pending["question_key"], pending["question_revision"])
            scope = json.loads(session["scope_json"])
            attempt_count = connection.execute(
                """
                select count(*) from attempts
                where session_id = ? and question_key = ?
                """,
                (session_id, question.stable_key),
            ).fetchone()[0]
            return {
                "status": "active",
                "session": summary,
                "position": pending["position"],
                "selection_reason": pending["selection_reason"],
                "stage": scope.get("stages", {}).get(question.stable_key),
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
            self._session(connection, session_id)
            existing = connection.execute(
                """
                select result_json from attempts
                where session_id = ? and idempotency_key = ?
                """,
                (session_id, idempotency_key),
            ).fetchone()
            if existing:
                return json.loads(existing["result_json"])
            assignment = connection.execute(
                """
                select * from session_questions
                where session_id = ? and question_key = ? and status = 'pending'
                """,
                (session_id, stable_key),
            ).fetchone()
            if assignment is None or assignment["question_revision"] != revision:
                raise PracticeError(
                    "question_not_current",
                    "This question is not the current unresolved assignment.",
                    409,
                )
            question = self._question(stable_key, revision)
            attempt_number = connection.execute(
                """
                select count(*) from attempts where session_id = ? and question_key = ?
                """,
                (session_id, stable_key),
            ).fetchone()[0] + 1
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
                "question_finished": correct,
                "solution_available": not correct and incorrect_attempts >= 2,
            }
            timestamp = _now()
            connection.execute(
                """
                insert into attempts (
                    id, session_id, question_key, question_revision, attempt_number,
                    idempotency_key, answers_json, result_json, is_correct,
                    marks_awarded, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    session_id,
                    stable_key,
                    revision,
                    attempt_number,
                    idempotency_key,
                    _json(answers),
                    _json(result),
                    int(correct),
                    marks_awarded,
                    timestamp,
                ),
            )
            connection.execute(
                """
                update session_questions
                set status = ?, incorrect_attempts = ?, resolved_at = ?
                where session_id = ? and question_key = ?
                """,
                (
                    "correct" if correct else "pending",
                    incorrect_attempts,
                    timestamp if correct else None,
                    session_id,
                    stable_key,
                ),
            )
            state = "correct" if correct else "queued_for_retry"
            connection.execute(
                """
                insert into question_progress (
                    question_key, question_revision, state, attempts_total,
                    incorrect_total, correct_total, last_attempted_at, updated_at
                ) values (?, ?, ?, 1, ?, ?, ?, ?)
                on conflict(question_key) do update set
                    question_revision = excluded.question_revision,
                    state = excluded.state,
                    attempts_total = question_progress.attempts_total + 1,
                    incorrect_total = question_progress.incorrect_total + excluded.incorrect_total,
                    correct_total = question_progress.correct_total + excluded.correct_total,
                    last_attempted_at = excluded.last_attempted_at,
                    updated_at = excluded.updated_at
                """,
                (
                    stable_key,
                    revision,
                    state,
                    0 if correct else 1,
                    1 if correct else 0,
                    timestamp,
                    timestamp,
                ),
            )
            return result

    def reveal_hint(self, session_id: str, stable_key: str, stage: int) -> dict:
        if stage not in {1, 2}:
            raise PracticeError("invalid_hint_stage", "Hint stage must be 1 or 2.")
        with self._connect() as connection:
            self._session(connection, session_id)
            assignment = connection.execute(
                """
                select * from session_questions
                where session_id = ? and question_key = ? and status = 'pending'
                """,
                (session_id, stable_key),
            ).fetchone()
            if assignment is None:
                raise PracticeError("question_not_current", "This question is not current.", 409)
            if stage == 2 and assignment["highest_hint_stage"] < 1:
                raise PracticeError("hint_order", "Open hint 1 before hint 2.", 409)
            question = self._question(stable_key, assignment["question_revision"])
            connection.execute(
                """
                update session_questions
                set highest_hint_stage = max(highest_hint_stage, ?)
                where session_id = ? and question_key = ?
                """,
                (stage, session_id, stable_key),
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
            self._session(connection, session_id)
            assignment = connection.execute(
                """
                select * from session_questions
                where session_id = ? and question_key = ? and status = 'pending'
                """,
                (session_id, stable_key),
            ).fetchone()
            if assignment is None:
                raise PracticeError("question_not_current", "This question is not current.", 409)
            if assignment["incorrect_attempts"] < 2:
                raise PracticeError(
                    "solution_locked",
                    "The solution unlocks after two incorrect attempts.",
                    403,
                )
            timestamp = _now()
            question = self._question(stable_key, assignment["question_revision"])
            connection.execute(
                """
                update session_questions
                set status = 'gave_up', resolved_at = ?
                where session_id = ? and question_key = ?
                """,
                (timestamp, session_id, stable_key),
            )
            connection.execute(
                """
                insert into question_progress (
                    question_key, question_revision, state, updated_at
                ) values (?, ?, 'gave_up', ?)
                on conflict(question_key) do update set
                    question_revision = excluded.question_revision,
                    state = excluded.state,
                    updated_at = excluded.updated_at
                """,
                (stable_key, assignment["question_revision"], timestamp),
            )
            return {"status": "gave_up", "solution": solution_for(question)}
