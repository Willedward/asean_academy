"""PostgreSQL question-report inbox with learner ownership and audit evidence."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class QuestionReportError(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class PostgresQuestionReportRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            connect_timeout=10,
            prepare_threshold=None,
            row_factory=dict_row,
        )

    @staticmethod
    def _payload(row: dict, *, admin: bool = False) -> dict:
        payload = {
            "report_id": row["report_id"],
            "question_key": row["question_key"],
            "question_revision": row["question_revision"],
            "question_title": row["question_title"],
            "category": row["category"],
            "comment": row["comment"],
            "status": row["status"],
            "resolution": row["resolution"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "resolved_at": row["resolved_at"],
        }
        if admin:
            payload.update(
                learner_id=row["learner_id"],
                learner_email=row["learner_email"],
                session_id=row["session_id"],
            )
        return payload

    @staticmethod
    def _query() -> str:
        return """
            select reports.id as report_id, reports.student_id as learner_id,
                   profiles.email as learner_email,
                   reports.practice_session_id as session_id,
                   questions.stable_key as question_key,
                   versions.revision as question_revision,
                   versions.title as question_title,
                   reports.category::text as category,
                   reports.comment, reports.status::text as status,
                   reports.resolution, reports.created_at, reports.updated_at,
                   reports.resolved_at
            from question_reports reports
            join math_question_versions versions on versions.id = reports.question_version_id
            join math_questions questions on questions.id = versions.question_id
            join profiles on profiles.id = reports.student_id
        """

    def create(
        self,
        learner_id: str,
        *,
        session_id: str,
        question_key: str,
        question_revision: int,
        category: str,
        comment: str,
        request_id: str,
    ) -> dict:
        with self._connect() as connection:
            assignment = connection.execute(
                """
                select versions.id as question_version_id
                from practice_sessions sessions
                join session_questions assigned on assigned.practice_session_id = sessions.id
                join math_question_versions versions on versions.id = assigned.question_version_id
                join math_questions questions on questions.id = versions.question_id
                where sessions.id = %s and sessions.student_id = %s
                  and questions.stable_key = %s and versions.revision = %s
                """,
                (session_id, learner_id, question_key, question_revision),
            ).fetchone()
            if assignment is None:
                raise QuestionReportError(
                    "question_report_context_not_found",
                    "That question was not assigned in this learner session.",
                    404,
                )
            report = connection.execute(
                """
                insert into question_reports (
                    student_id, question_version_id, practice_session_id, category, comment
                ) values (%s, %s, %s, %s, %s)
                returning id
                """,
                (learner_id, assignment["question_version_id"], session_id, category, comment.strip()),
            ).fetchone()
            connection.execute(
                """
                insert into beta_audit_events (
                    event_type, actor_user_id, target_user_id, request_id, metadata
                ) values ('question_report_created', %s, %s, %s, %s)
                """,
                (
                    learner_id,
                    learner_id,
                    request_id,
                    Jsonb({"report_id": str(report["id"]), "question_key": question_key}),
                ),
            )
            row = connection.execute(
                self._query() + " where reports.id = %s",
                (report["id"],),
            ).fetchone()
        return self._payload(row)

    def learner_list(self, learner_id: str) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                self._query()
                + " where reports.student_id = %s order by reports.created_at desc",
                (learner_id,),
            ).fetchall()
        return {"reports": [self._payload(row) for row in rows], "total": len(rows)}

    def learner_get(self, learner_id: str, report_id: str) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                self._query()
                + " where reports.id = %s and reports.student_id = %s",
                (report_id, learner_id),
            ).fetchone()
        if row is None:
            raise QuestionReportError(
                "question_report_not_found", "Report not found.", 404
            )
        return self._payload(row)

    def admin_get(self, report_id: str) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                self._query() + " where reports.id = %s",
                (report_id,),
            ).fetchone()
        if row is None:
            raise QuestionReportError(
                "question_report_not_found", "Report not found.", 404
            )
        return self._payload(row, admin=True)

    def admin_list(self, *, status: str | None, limit: int, offset: int) -> dict:
        parameters: list[object] = []
        condition = ""
        if status:
            condition = " where reports.status = %s"
            parameters.append(status)
        with self._connect() as connection:
            total = connection.execute(
                "select count(*) as total from question_reports reports" + condition,
                parameters,
            ).fetchone()["total"]
            rows = connection.execute(
                self._query()
                + condition
                + " order by reports.created_at asc limit %s offset %s",
                [*parameters, limit, offset],
            ).fetchall()
        return {
            "reports": [self._payload(row, admin=True) for row in rows],
            "total": total,
        }

    def resolve(
        self,
        report_id: str,
        *,
        status: str,
        resolution: str | None,
        administrator_id: str,
        request_id: str,
    ) -> dict:
        if status in {"resolved", "dismissed"} and not (resolution or "").strip():
            raise QuestionReportError(
                "report_resolution_required",
                "Resolved and dismissed reports require a response.",
                422,
            )
        with self._connect() as connection:
            row = connection.execute(
                "select status::text as status from question_reports where id = %s for update",
                (report_id,),
            ).fetchone()
            if row is None:
                raise QuestionReportError("question_report_not_found", "Report not found.", 404)
            terminal = status in {"resolved", "dismissed"}
            connection.execute(
                """
                update question_reports
                set status = %s, resolution = %s,
                    resolved_by = case when %s then %s::uuid else null end,
                    resolved_at = case when %s then now() else null end,
                    updated_at = now()
                where id = %s
                """,
                (status, resolution.strip() if resolution else None, terminal,
                 administrator_id, terminal, report_id),
            )
            connection.execute(
                """
                insert into beta_audit_events (
                    event_type, actor_user_id, request_id, metadata
                ) values ('question_report_status_changed', %s, %s, %s)
                """,
                (
                    administrator_id,
                    request_id,
                    Jsonb({"report_id": report_id, "from": row["status"], "to": status}),
                ),
            )
            updated = connection.execute(
                self._query() + " where reports.id = %s",
                (report_id,),
            ).fetchone()
        return self._payload(updated, admin=True)
