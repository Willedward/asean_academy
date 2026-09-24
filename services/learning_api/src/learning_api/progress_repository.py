"""Learner-progress repository boundary and local SQLite implementation."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import psycopg
from psycopg.rows import dict_row


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

    def session(
        self, learner_id: str, session_id: str
    ) -> SessionProgressRecord | None: ...

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

    def session(
        self, learner_id: str, session_id: str
    ) -> SessionProgressRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                select * from learner_practice_sessions
                where learner_id = ? and session_id = ?
                """,
                (learner_id, session_id),
            ).fetchone()
            return self._session(row) if row is not None else None

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


def _iso(value) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


class PostgresProgressRepository:
    """PostgreSQL progress adapter with explicit learner ownership on every query."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            connect_timeout=10,
            row_factory=dict_row,
        )

    @staticmethod
    def _set_identity(connection, learner_id: str) -> None:
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)",
            (learner_id,),
        )

    @staticmethod
    def _lesson(row) -> LessonProgressRecord:
        return LessonProgressRecord(
            learner_id=str(row["learner_id"]),
            lesson_key=row["lesson_key"],
            lesson_revision=row["lesson_revision"],
            state=row["state"],
            question_count=row["question_count"],
            resolved_count=row["resolved_count"],
            correct_count=row["correct_count"],
            gave_up_count=row["gave_up_count"],
            eventual_correct_percentage=float(row["eventual_correct_percentage"]),
            checkpoint_passed=row["checkpoint_passed"],
            last_session_id=(
                str(row["last_session_id"]) if row["last_session_id"] else None
            ),
            started_at=_iso(row["started_at"]),
            updated_at=_iso(row["updated_at"]),
            completed_at=_iso(row["completed_at"]),
        )

    @staticmethod
    def _session(row) -> SessionProgressRecord:
        return SessionProgressRecord(
            session_id=str(row["session_id"]),
            learner_id=str(row["learner_id"]),
            lesson_key=row["lesson_key"],
            status=row["status"],
            question_count=row["question_count"],
            resolved_count=row["resolved_count"],
            correct_count=row["correct_count"],
            gave_up_count=row["gave_up_count"],
            updated_at=_iso(row["updated_at"]),
        )

    @staticmethod
    def _lesson_identity(connection, lesson_key: str, revision: int):
        row = connection.execute(
            """
            select course_lessons.id as lesson_id, lesson_versions.id as lesson_version_id
            from course_lessons
            join lesson_versions on lesson_versions.lesson_id = course_lessons.id
            where course_lessons.lesson_key = %s and lesson_versions.revision = %s
            """,
            (lesson_key, revision),
        ).fetchone()
        if row is None:
            raise ProgressError(
                "lesson_not_imported",
                "The requested lesson revision has not been imported into PostgreSQL.",
                503,
            )
        return row

    @staticmethod
    def _lesson_query() -> str:
        return """
            select
                progress.student_id as learner_id,
                lessons.lesson_key,
                versions.revision as lesson_revision,
                progress.state::text as state,
                progress.question_count,
                progress.resolved_count,
                progress.correct_count,
                progress.gave_up_count,
                progress.eventual_correct_percentage,
                progress.checkpoint_passed,
                progress.last_practice_session_id as last_session_id,
                progress.started_at,
                progress.updated_at,
                progress.completed_at
            from learner_lesson_progress progress
            join course_lessons lessons on lessons.id = progress.lesson_id
            join lesson_versions versions on versions.id = progress.lesson_version_id
        """

    @staticmethod
    def _session_query() -> str:
        return """
            select
                sessions.id as session_id,
                sessions.student_id as learner_id,
                sessions.scope->>'lesson_key' as lesson_key,
                sessions.status::text as status,
                sessions.requested_question_count as question_count,
                count(questions.id) filter (where questions.status <> 'pending')::integer
                    as resolved_count,
                count(questions.id) filter (where questions.status = 'correct')::integer
                    as correct_count,
                count(questions.id) filter (where questions.status = 'gave_up')::integer
                    as gave_up_count,
                coalesce(sessions.completed_at, sessions.created_at) as updated_at
            from practice_sessions sessions
            left join session_questions questions
                on questions.practice_session_id = sessions.id
        """

    def start_lesson(
        self,
        learner_id: str,
        lesson_key: str,
        lesson_revision: int,
    ) -> LessonProgressRecord:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            identity = self._lesson_identity(connection, lesson_key, lesson_revision)
            connection.execute(
                """
                insert into learner_lesson_progress (
                    student_id, lesson_id, lesson_version_id, state
                ) values (%s, %s, %s, 'in_progress')
                on conflict (student_id, lesson_id) do update set
                    lesson_version_id = excluded.lesson_version_id,
                    updated_at = now()
                """,
                (learner_id, identity["lesson_id"], identity["lesson_version_id"]),
            )
            row = connection.execute(
                self._lesson_query()
                + " where progress.student_id = %s and progress.lesson_id = %s",
                (learner_id, identity["lesson_id"]),
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
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            owned = connection.execute(
                """
                select id from practice_sessions
                where id = %s and student_id = %s and scope->>'lesson_key' = %s
                """,
                (session_id, learner_id, lesson_key),
            ).fetchone()
            if owned is None:
                raise ProgressError(
                    "practice_session_not_owned",
                    "The practice session does not belong to this learner.",
                    404,
                )
            connection.execute(
                """
                update learner_lesson_progress progress
                set last_practice_session_id = %s,
                    question_count = %s,
                    updated_at = now()
                from course_lessons lessons
                where progress.lesson_id = lessons.id
                  and progress.student_id = %s
                  and lessons.lesson_key = %s
                """,
                (session_id, question_count, learner_id, lesson_key),
            )

    def session(
        self, learner_id: str, session_id: str
    ) -> SessionProgressRecord | None:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            row = connection.execute(
                self._session_query()
                + """
                  where sessions.student_id = %s and sessions.id = %s
                  group by sessions.id
                """,
                (learner_id, session_id),
            ).fetchone()
            return self._session(row) if row else None

    def active_session(
        self,
        learner_id: str,
        lesson_key: str | None = None,
    ) -> SessionProgressRecord | None:
        conditions = ["sessions.student_id = %s", "sessions.status = 'active'"]
        parameters: list[str] = [learner_id]
        if lesson_key is not None:
            conditions.append("sessions.scope->>'lesson_key' = %s")
            parameters.append(lesson_key)
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            row = connection.execute(
                self._session_query()
                + " where "
                + " and ".join(conditions)
                + " group by sessions.id order by sessions.created_at desc limit 1",
                parameters,
            ).fetchone()
            return self._session(row) if row else None

    def sync_session(
        self,
        learner_id: str,
        summary: dict,
        *,
        minimum_percentage: int,
    ) -> LessonProgressRecord:
        session_id = summary["session_id"]
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            session = connection.execute(
                """
                select id, scope->>'lesson_key' as lesson_key
                from practice_sessions
                where id = %s and student_id = %s
                for update
                """,
                (session_id, learner_id),
            ).fetchone()
            if session is None:
                raise ProgressError(
                    "practice_session_not_owned",
                    "The practice session does not belong to this learner.",
                    404,
                )
            current = connection.execute(
                self._lesson_query()
                + """
                  where progress.student_id = %s and lessons.lesson_key = %s
                  for update of progress
                """,
                (learner_id, session["lesson_key"]),
            ).fetchone()
            if current is None:
                raise ProgressError(
                    "lesson_progress_missing",
                    "Lesson progress was not started for this session.",
                    409,
                )
            count = summary["question_count"]
            correct = summary["correct_count"]
            gave_up = summary["gave_up_count"]
            percentage = round((100 * correct / count) if count else 0, 2)
            completed = summary["status"] == "completed"
            passed = completed and percentage >= minimum_percentage and gave_up == 0
            state = current["state"]
            if state != "mastered":
                if passed:
                    state = "proficient"
                elif completed and state != "proficient":
                    state = "practice_completed"
                elif state not in {"practice_completed", "proficient"}:
                    state = "in_progress"
            row = connection.execute(
                """
                update learner_lesson_progress progress
                set state = %s,
                    question_count = %s,
                    resolved_count = %s,
                    correct_count = %s,
                    gave_up_count = %s,
                    eventual_correct_percentage = %s,
                    last_practice_session_id = %s,
                    updated_at = now(),
                    completed_at = case when %s then coalesce(completed_at, now()) else completed_at end
                from course_lessons lessons
                where progress.lesson_id = lessons.id
                  and progress.student_id = %s
                  and lessons.lesson_key = %s
                returning progress.*
                """,
                (
                    state,
                    count,
                    summary["resolved_count"],
                    correct,
                    gave_up,
                    percentage,
                    session_id,
                    completed,
                    learner_id,
                    session["lesson_key"],
                ),
            ).fetchone()
            if state == "proficient" and current["state"] != "proficient":
                connection.execute(
                    """
                    insert into mastery_events (
                        student_id, lesson_id, event_type, source_practice_session_id,
                        evidence
                    )
                    values (%s, %s, 'lesson_proficient', %s, %s::jsonb)
                    on conflict (student_id, event_type, source_practice_session_id)
                    do nothing
                    """,
                    (
                        learner_id,
                        row["lesson_id"],
                        session_id,
                        psycopg.types.json.Jsonb(
                            {
                                "eventual_correct_percentage": percentage,
                                "gave_up_count": gave_up,
                                "minimum_percentage": minimum_percentage,
                            }
                        ),
                    ),
                )
            updated = connection.execute(
                self._lesson_query()
                + " where progress.student_id = %s and progress.lesson_id = %s",
                (learner_id, row["lesson_id"]),
            ).fetchone()
            return self._lesson(updated)

    def lesson_progress(self, learner_id: str) -> list[LessonProgressRecord]:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            rows = connection.execute(
                self._lesson_query()
                + " where progress.student_id = %s order by progress.started_at, lessons.lesson_key",
                (learner_id,),
            ).fetchall()
            return [self._lesson(row) for row in rows]
