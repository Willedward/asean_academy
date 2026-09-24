"""Learner-progress repository boundary and local SQLite implementation."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ProgressError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True, slots=True)
class LessonProgressRecord:
    learner_id: str
    lesson_key: str
    lesson_revision: int
    state: str
    question_count: int
    resolved_count: int
    correct_count: int
    gave_up_count: int
    eventual_correct_percentage: float
    checkpoint_passed: bool
    last_session_id: str | None
    started_at: str
    updated_at: str
    completed_at: str | None


@dataclass(frozen=True, slots=True)
class SessionProgressRecord:
    session_id: str
    learner_id: str
    lesson_key: str
    status: str
    question_count: int
    resolved_count: int
    correct_count: int
    gave_up_count: int
    updated_at: str


class ProgressRepository(Protocol):
    def start_lesson(
        self,
        learner_id: str,
        lesson_key: str,
        lesson_revision: int,
    ) -> LessonProgressRecord: ...

    def attach_session(
        self,
        learner_id: str,
        lesson_key: str,
        lesson_revision: int,
        session_id: str,
        question_count: int,
    ) -> None: ...

    def active_session(
        self,
        learner_id: str,
        lesson_key: str | None = None,
    ) -> SessionProgressRecord | None: ...

    def sync_session(
        self,
        learner_id: str,
        summary: dict,
        *,
        minimum_percentage: int,
    ) -> LessonProgressRecord: ...

    def lesson_progress(self, learner_id: str) -> list[LessonProgressRecord]: ...


class SQLiteProgressRepository:
    """Local adapter; production PostgreSQL must implement the same behaviour."""

    def __init__(self, database: Path):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma foreign_keys = on")
        connection.execute("pragma busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                pragma journal_mode = wal;

                create table if not exists learner_lesson_progress (
                    learner_id text not null,
                    lesson_key text not null,
                    lesson_revision integer not null,
                    state text not null check (
                        state in ('in_progress', 'practice_completed', 'proficient', 'mastered')
                    ),
                    question_count integer not null default 0,
                    resolved_count integer not null default 0,
                    correct_count integer not null default 0,
                    gave_up_count integer not null default 0,
                    eventual_correct_percentage real not null default 0,
                    checkpoint_passed integer not null default 0,
                    last_session_id text,
                    started_at text not null,
                    updated_at text not null,
                    completed_at text,
                    primary key (learner_id, lesson_key)
                );

                create table if not exists learner_practice_sessions (
                    session_id text primary key,
                    learner_id text not null,
                    lesson_key text not null,
                    status text not null check (status in ('active', 'completed')),
                    question_count integer not null,
                    resolved_count integer not null default 0,
                    correct_count integer not null default 0,
                    gave_up_count integer not null default 0,
                    created_at text not null,
                    updated_at text not null
                );

                create index if not exists learner_active_session_idx
                on learner_practice_sessions (learner_id, status, updated_at desc);
                """
            )

    @staticmethod
    def _lesson(row) -> LessonProgressRecord:
        return LessonProgressRecord(
            learner_id=row["learner_id"],
            lesson_key=row["lesson_key"],
            lesson_revision=row["lesson_revision"],
            state=row["state"],
            question_count=row["question_count"],
            resolved_count=row["resolved_count"],
            correct_count=row["correct_count"],
            gave_up_count=row["gave_up_count"],
            eventual_correct_percentage=row["eventual_correct_percentage"],
            checkpoint_passed=bool(row["checkpoint_passed"]),
            last_session_id=row["last_session_id"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )

    @staticmethod
    def _session(row) -> SessionProgressRecord:
        return SessionProgressRecord(
            session_id=row["session_id"],
            learner_id=row["learner_id"],
            lesson_key=row["lesson_key"],
            status=row["status"],
            question_count=row["question_count"],
            resolved_count=row["resolved_count"],
            correct_count=row["correct_count"],
            gave_up_count=row["gave_up_count"],
            updated_at=row["updated_at"],
        )

    def start_lesson(
        self,
        learner_id: str,
        lesson_key: str,
        lesson_revision: int,
    ) -> LessonProgressRecord:
        timestamp = _now()
        with self._connect() as connection:
            connection.execute(
                """
                insert into learner_lesson_progress (
                    learner_id, lesson_key, lesson_revision, state, started_at, updated_at
                ) values (?, ?, ?, 'in_progress', ?, ?)
                on conflict(learner_id, lesson_key) do update set
                    lesson_revision = excluded.lesson_revision,
                    updated_at = excluded.updated_at
                """,
                (learner_id, lesson_key, lesson_revision, timestamp, timestamp),
            )
            row = connection.execute(
                """
                select * from learner_lesson_progress
                where learner_id = ? and lesson_key = ?
                """,
                (learner_id, lesson_key),
            ).fetchone()
            return self._lesson(row)

    def attach_session(
        self,
        learner_id: str,
        lesson_key: str,
        lesson_revision: int,
        session_id: str,
        question_count: int,
    ) -> None:
        self.start_lesson(learner_id, lesson_key, lesson_revision)
        timestamp = _now()
        with self._connect() as connection:
            connection.execute(
                """
                insert into learner_practice_sessions (
                    session_id, learner_id, lesson_key, status, question_count,
                    created_at, updated_at
                ) values (?, ?, ?, 'active', ?, ?, ?)
                on conflict(session_id) do nothing
                """,
                (
                    session_id,
                    learner_id,
                    lesson_key,
                    question_count,
                    timestamp,
                    timestamp,
                ),
            )
            connection.execute(
                """
                update learner_lesson_progress
                set last_session_id = ?, updated_at = ?
                where learner_id = ? and lesson_key = ?
                """,
                (session_id, timestamp, learner_id, lesson_key),
            )

    def active_session(
        self,
        learner_id: str,
        lesson_key: str | None = None,
    ) -> SessionProgressRecord | None:
        query = """
            select * from learner_practice_sessions
            where learner_id = ? and status = 'active'
        """
        parameters: list[str] = [learner_id]
        if lesson_key is not None:
            query += " and lesson_key = ?"
            parameters.append(lesson_key)
        query += " order by updated_at desc limit 1"
        with self._connect() as connection:
            row = connection.execute(query, parameters).fetchone()
            return self._session(row) if row is not None else None

    def sync_session(
        self,
        learner_id: str,
        summary: dict,
        *,
        minimum_percentage: int,
    ) -> LessonProgressRecord:
        session_id = summary["session_id"]
        timestamp = _now()
        with self._connect() as connection:
            owner = connection.execute(
                """
                select * from learner_practice_sessions
                where session_id = ? and learner_id = ?
                """,
                (session_id, learner_id),
            ).fetchone()
            if owner is None:
                raise ProgressError(
                    "practice_session_not_owned",
                    "The practice session is not linked to the local learner.",
                    404,
                )
            lesson_key = owner["lesson_key"]
            question_count = summary["question_count"]
            resolved_count = summary["resolved_count"]
            correct_count = summary["correct_count"]
            gave_up_count = summary["gave_up_count"]
            percentage = round(
                (100 * correct_count / question_count) if question_count else 0,
                2,
            )
            completed = summary["status"] == "completed"
            connection.execute(
                """
                update learner_practice_sessions
                set status = ?, question_count = ?, resolved_count = ?,
                    correct_count = ?, gave_up_count = ?, updated_at = ?
                where session_id = ?
                """,
                (
                    summary["status"],
                    question_count,
                    resolved_count,
                    correct_count,
                    gave_up_count,
                    timestamp,
                    session_id,
                ),
            )
            current = connection.execute(
                """
                select * from learner_lesson_progress
                where learner_id = ? and lesson_key = ?
                """,
                (learner_id, lesson_key),
            ).fetchone()
            if current is None:
                raise ProgressError(
                    "lesson_progress_missing",
                    "Lesson progress was not started for this session.",
                    409,
                )
            passed = (
                completed
                and percentage >= minimum_percentage
                and gave_up_count == 0
            )
            state = current["state"]
            if state != "mastered":
                if passed:
                    state = "proficient"
                elif completed and state != "proficient":
                    state = "practice_completed"
                elif state not in {"practice_completed", "proficient"}:
                    state = "in_progress"
            completed_at = timestamp if completed else current["completed_at"]
            connection.execute(
                """
                update learner_lesson_progress
                set state = ?, question_count = ?, resolved_count = ?,
                    correct_count = ?, gave_up_count = ?,
                    eventual_correct_percentage = ?, last_session_id = ?,
                    updated_at = ?, completed_at = ?
                where learner_id = ? and lesson_key = ?
                """,
                (
                    state,
                    question_count,
                    resolved_count,
                    correct_count,
                    gave_up_count,
                    percentage,
                    session_id,
                    timestamp,
                    completed_at,
                    learner_id,
                    lesson_key,
                ),
            )
            updated = connection.execute(
                """
                select * from learner_lesson_progress
                where learner_id = ? and lesson_key = ?
                """,
                (learner_id, lesson_key),
            ).fetchone()
            return self._lesson(updated)

    def lesson_progress(self, learner_id: str) -> list[LessonProgressRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                select * from learner_lesson_progress
                where learner_id = ?
                order by started_at, lesson_key
                """,
                (learner_id,),
            ).fetchall()
            return [self._lesson(row) for row in rows]
