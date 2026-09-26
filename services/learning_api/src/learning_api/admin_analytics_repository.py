"""PostgreSQL administrator analytics and role-management queries."""

from __future__ import annotations

from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .admin_analytics_contracts import AdminUserRole
from .admin_repository import BetaOperationsError
from .identity import AuthenticatedLearner


class PostgresAdminAnalyticsRepository:
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
    def _student_summary_sql() -> str:
        return """
            select
                profiles.id as learner_id,
                profiles.email,
                profiles.display_name,
                profiles.target_track,
                case
                    when coalesce(enrolments.has_active, false) then 'active'
                    when coalesce(enrolments.has_completed, false) then 'completed'
                    when coalesce(enrolments.enrolment_count, 0) > 0 then 'withdrawn'
                    else 'not_enrolled'
                end as enrolment_status,
                coalesce(enrolments.course_keys, array[]::text[]) as course_keys,
                enrolments.enrolled_at,
                greatest(
                    enrolments.last_enrolment_at,
                    lessons.last_lesson_at,
                    sessions.last_session_at,
                    attempt_totals.last_attempt_at
                ) as last_activity_at,
                coalesce(lessons.lessons_started, 0)::integer as lessons_started,
                coalesce(lessons.lessons_proficient, 0)::integer as lessons_proficient,
                coalesce(lessons.lessons_mastered, 0)::integer as lessons_mastered,
                coalesce(sessions.practice_sessions, 0)::integer as practice_sessions,
                coalesce(attempt_totals.attempts, 0)::integer as attempts,
                coalesce(attempt_totals.correct_attempts, 0)::integer as correct_attempts,
                case
                    when coalesce(attempt_totals.attempts, 0) = 0 then 0
                    else round(
                        100.0 * attempt_totals.correct_attempts / attempt_totals.attempts,
                        2
                    )
                end::float as accuracy_percentage,
                coalesce(retries.retry_question_count, 0)::integer as retry_question_count
            from profiles
            left join lateral (
                select
                    count(*) as enrolment_count,
                    bool_or(course_enrolments.status = 'active') as has_active,
                    bool_or(course_enrolments.status = 'completed') as has_completed,
                    array_agg(courses.course_key order by courses.course_key) as course_keys,
                    min(course_enrolments.enrolled_at) as enrolled_at,
                    max(coalesce(course_enrolments.completed_at, course_enrolments.enrolled_at))
                        as last_enrolment_at
                from course_enrolments
                join courses on courses.id = course_enrolments.course_id
                where course_enrolments.student_id = profiles.id
            ) enrolments on true
            left join lateral (
                select
                    count(*) as lessons_started,
                    count(*) filter (
                        where learner_lesson_progress.state in ('proficient', 'mastered')
                    ) as lessons_proficient,
                    count(*) filter (
                        where learner_lesson_progress.state = 'mastered'
                    ) as lessons_mastered,
                    max(learner_lesson_progress.updated_at) as last_lesson_at
                from learner_lesson_progress
                where learner_lesson_progress.student_id = profiles.id
            ) lessons on true
            left join lateral (
                select
                    count(*) as practice_sessions,
                    max(coalesce(
                        practice_sessions.completed_at,
                        practice_sessions.abandoned_at,
                        practice_sessions.created_at
                    )) as last_session_at
                from practice_sessions
                where practice_sessions.student_id = profiles.id
            ) sessions on true
            left join lateral (
                select
                    count(*) as attempts,
                    count(*) filter (where attempts.is_correct) as correct_attempts,
                    max(attempts.submitted_at) as last_attempt_at
                from attempts
                where attempts.student_id = profiles.id
            ) attempt_totals on true
            left join lateral (
                select count(*) as retry_question_count
                from question_progress
                where question_progress.student_id = profiles.id
                  and question_progress.state in ('queued_for_retry', 'gave_up')
            ) retries on true
        """

    @staticmethod
    def _serialize_student(row: dict) -> dict:
        return {
            "learner_id": row["learner_id"],
            "email": row["email"],
            "display_name": row["display_name"],
            "target_track": row["target_track"],
            "enrolment_status": row["enrolment_status"],
            "course_keys": list(row["course_keys"]),
            "enrolled_at": row["enrolled_at"],
            "last_activity_at": row["last_activity_at"],
            "lessons_started": row["lessons_started"],
            "lessons_proficient": row["lessons_proficient"],
            "lessons_mastered": row["lessons_mastered"],
            "practice_sessions": row["practice_sessions"],
            "attempts": row["attempts"],
            "correct_attempts": row["correct_attempts"],
            "accuracy_percentage": row["accuracy_percentage"],
            "retry_question_count": row["retry_question_count"],
        }

    def list_students(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        conditions = ["profiles.role = 'student'"]
        parameters: list[object] = []
        if search:
            conditions.append(
                "(profiles.email ilike %s or coalesce(profiles.display_name, '') ilike %s)"
            )
            pattern = f"%{search.strip()}%"
            parameters.extend([pattern, pattern])
        where = " and ".join(conditions)
        with self._connect() as connection:
            rows = connection.execute(
                self._student_summary_sql()
                + f"""
                    where {where}
                    order by last_activity_at desc nulls last, profiles.created_at desc
                    limit %s offset %s
                """,
                (*parameters, limit, offset),
            ).fetchall()
            total = connection.execute(
                f"select count(*) as total from profiles where {where}",
                parameters,
            ).fetchone()["total"]
        return {
            "students": [self._serialize_student(dict(row)) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def student_detail(self, learner_id: UUID) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                self._student_summary_sql()
                + " where profiles.role = 'student' and profiles.id = %s",
                (learner_id,),
            ).fetchone()
            if row is None:
                raise BetaOperationsError(
                    "student_not_found", "The requested student was not found.", 404
                )
            lessons = connection.execute(
                """
                select lessons.lesson_key, versions.title as lesson_title,
                       progress.state::text as state, progress.question_count,
                       progress.resolved_count, progress.correct_count,
                       progress.gave_up_count,
                       progress.eventual_correct_percentage::float,
                       progress.checkpoint_passed, progress.started_at,
                       progress.updated_at, progress.completed_at
                from learner_lesson_progress progress
                join course_lessons lessons on lessons.id = progress.lesson_id
                join lesson_versions versions on versions.id = progress.lesson_version_id
                where progress.student_id = %s
                order by progress.started_at, lessons.lesson_key
                """,
                (learner_id,),
            ).fetchall()
            difficulty = connection.execute(
                """
                select questions.difficulty,
                       count(*)::integer as attempts,
                       count(*) filter (where attempts.is_correct)::integer
                           as correct_attempts,
                       case when count(*) = 0 then 0 else
                           round(100.0 * count(*) filter (where attempts.is_correct)
                                 / count(*), 2)
                       end::float as accuracy_percentage
                from attempts
                join math_question_versions versions
                  on versions.id = attempts.question_version_id
                join math_questions questions on questions.id = versions.question_id
                where attempts.student_id = %s
                group by questions.difficulty
                order by questions.difficulty
                """,
                (learner_id,),
            ).fetchall()
        return {
            "student": self._serialize_student(dict(row)),
            "lessons": [dict(item) for item in lessons],
            "difficulty_performance": [dict(item) for item in difficulty],
        }

    def overview(self) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                """
                with student_activity as (
                    select profiles.id,
                           greatest(
                               (select max(coalesce(completed_at, enrolled_at))
                                from course_enrolments where student_id = profiles.id),
                               (select max(updated_at) from learner_lesson_progress
                                where student_id = profiles.id),
                               (select max(coalesce(completed_at, abandoned_at, created_at))
                                from practice_sessions where student_id = profiles.id),
                               (select max(submitted_at) from attempts
                                where student_id = profiles.id)
                           ) as last_activity_at
                    from profiles where profiles.role = 'student'
                )
                select
                    (select count(*) from profiles where role = 'student')::integer
                        as total_students,
                    (select count(distinct student_id) from course_enrolments
                     where status = 'active')::integer as active_enrolments,
                    (select count(*) from student_activity
                     where last_activity_at >= now() - interval '7 days')::integer
                        as active_students_last_7_days,
                    (select count(*) from student_activity
                     where last_activity_at >= now() - interval '30 days')::integer
                        as active_students_last_30_days,
                    (select count(*) from learner_lesson_progress progress join profiles on profiles.id = progress.student_id where profiles.role = 'student')::integer
                        as lessons_started,
                    (select count(*) from learner_lesson_progress progress join profiles on profiles.id = progress.student_id where profiles.role = 'student' and progress.state = 'mastered')::integer as lessons_mastered,
                    (select count(*) from practice_sessions sessions join profiles on profiles.id = sessions.student_id where profiles.role = 'student')::integer as practice_sessions,
                    (select count(*) from practice_sessions sessions join profiles on profiles.id = sessions.student_id where profiles.role = 'student' and sessions.status = 'completed')::integer as completed_practice_sessions,
                    (select count(*) from attempts join profiles on profiles.id = attempts.student_id where profiles.role = 'student')::integer as attempts,
                    (select count(*) from attempts join profiles on profiles.id = attempts.student_id where profiles.role = 'student' and attempts.is_correct)::integer
                        as correct_attempts,
                    case when (select count(*) from attempts join profiles on profiles.id = attempts.student_id where profiles.role = 'student') = 0 then 0 else
                        round(100.0 * (select count(*) from attempts join profiles on profiles.id = attempts.student_id where profiles.role = 'student' and attempts.is_correct)
                              / (select count(*) from attempts join profiles on profiles.id = attempts.student_id where profiles.role = 'student'), 2)
                    end::float as overall_accuracy_percentage,
                    coalesce((select sum(assigned.highest_hint_stage) from session_questions assigned join practice_sessions sessions on sessions.id = assigned.practice_session_id join profiles on profiles.id = sessions.student_id where profiles.role = 'student'), 0)::integer
                        as hint_reveals,
                    (select count(*) from session_questions assigned join practice_sessions sessions on sessions.id = assigned.practice_session_id join profiles on profiles.id = sessions.student_id where profiles.role = 'student' and assigned.status = 'gave_up')::integer as give_ups,
                    (select count(distinct progress.student_id) from question_progress progress join profiles on profiles.id = progress.student_id where profiles.role = 'student' and progress.state in ('queued_for_retry', 'gave_up'))::integer
                        as students_with_retries,
                    (select count(*) from practice_sessions sessions join profiles on profiles.id = sessions.student_id where profiles.role = 'student' and sessions.scope->>'mode' = 'checkpoint')::integer as checkpoint_attempts,
                    (select count(*) from mastery_events events join profiles on profiles.id = events.student_id where profiles.role = 'student' and events.event_type = 'checkpoint_passed')::integer as checkpoint_passes
                """
            ).fetchone()
        assert row is not None
        return dict(row)

    def question_analytics(
        self,
        *,
        difficulty: int | None,
        outcome: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        conditions = ["versions.is_current"]
        parameters: list[object] = []
        if difficulty is not None:
            conditions.append("questions.difficulty = %s")
            parameters.append(difficulty)
        if outcome:
            conditions.append("outcomes.code = %s")
            parameters.append(outcome.strip())
        where = " and ".join(conditions)
        query = f"""
            with attempt_totals as (
                select versions.question_id,
                       count(*)::integer as attempt_count,
                       count(distinct attempts.student_id)::integer as unique_students,
                       count(*) filter (where attempts.is_correct)::integer
                           as correct_attempts
                from attempts
                join math_question_versions versions
                  on versions.id = attempts.question_version_id
                join profiles on profiles.id = attempts.student_id
                where profiles.role = 'student'
                group by versions.question_id
            ), assignment_totals as (
                select versions.question_id,
                       coalesce(sum(assigned.highest_hint_stage), 0)::integer as hint_reveals,
                       count(*) filter (where assigned.status = 'gave_up')::integer
                           as give_up_count
                from session_questions assigned
                join math_question_versions versions
                  on versions.id = assigned.question_version_id
                join practice_sessions sessions on sessions.id = assigned.practice_session_id
                join profiles on profiles.id = sessions.student_id
                where profiles.role = 'student'
                group by versions.question_id
            ), retry_totals as (
                select question_id,
                       count(*) filter (
                           where state in ('queued_for_retry', 'gave_up')
                       )::integer as queued_for_retry_students
                from question_progress
                join profiles on profiles.id = question_progress.student_id
                where profiles.role = 'student'
                group by question_id
            )
            select questions.stable_key as question_key, versions.title,
                   questions.difficulty, outcomes.code as outcome_code,
                   coalesce(attempt_totals.attempt_count, 0)::integer as attempt_count,
                   coalesce(attempt_totals.unique_students, 0)::integer as unique_students,
                   coalesce(attempt_totals.correct_attempts, 0)::integer
                       as correct_attempts,
                   case when coalesce(attempt_totals.attempt_count, 0) = 0 then 0 else
                       round(100.0 * attempt_totals.correct_attempts
                             / attempt_totals.attempt_count, 2)
                   end::float as accuracy_percentage,
                   coalesce(assignment_totals.hint_reveals, 0)::integer as hint_reveals,
                   coalesce(assignment_totals.give_up_count, 0)::integer as give_up_count,
                   coalesce(retry_totals.queued_for_retry_students, 0)::integer
                       as queued_for_retry_students
            from math_questions questions
            join math_question_versions versions on versions.question_id = questions.id
            join syllabus_outcomes outcomes on outcomes.id = questions.primary_outcome_id
            left join attempt_totals on attempt_totals.question_id = questions.id
            left join assignment_totals on assignment_totals.question_id = questions.id
            left join retry_totals on retry_totals.question_id = questions.id
            where {where}
        """
        with self._connect() as connection:
            rows = connection.execute(
                query
                + """
                    order by accuracy_percentage asc, attempt_count desc,
                             questions.difficulty, questions.stable_key
                    limit %s offset %s
                """,
                (*parameters, limit, offset),
            ).fetchall()
            total = connection.execute(
                f"""
                select count(*) as total
                from math_questions questions
                join math_question_versions versions on versions.question_id = questions.id
                join syllabus_outcomes outcomes on outcomes.id = questions.primary_outcome_id
                where {where}
                """,
                parameters,
            ).fetchone()["total"]
        return {
            "questions": [dict(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def change_role(
        self,
        administrator: AuthenticatedLearner,
        learner_id: UUID,
        role: AdminUserRole,
        request_id: str,
    ) -> dict:
        if str(learner_id) == administrator.learner_id:
            raise BetaOperationsError(
                "self_role_change_forbidden",
                "Administrators cannot change their own role.",
                409,
            )
        with self._connect() as connection:
            target = connection.execute(
                """
                select id, email, display_name, role::text as role, updated_at
                from profiles where id = %s for update
                """,
                (learner_id,),
            ).fetchone()
            if target is None:
                raise BetaOperationsError(
                    "user_not_found", "The requested user was not found.", 404
                )
            previous_role = target["role"]
            if previous_role == role:
                return {
                    "learner_id": target["id"],
                    "email": target["email"],
                    "display_name": target["display_name"],
                    "role": previous_role,
                    "updated_at": target["updated_at"],
                }
            if previous_role == "academic_admin" and role != "academic_admin":
                academic_admins = connection.execute(
                    "select count(*) as total from profiles where role = 'academic_admin'"
                ).fetchone()["total"]
                if academic_admins <= 1:
                    raise BetaOperationsError(
                        "last_academic_admin",
                        "The last academic administrator cannot be demoted.",
                        409,
                    )
            updated = connection.execute(
                """
                update profiles set role = %s, updated_at = now()
                where id = %s
                returning id as learner_id, email, display_name,
                          role::text as role, updated_at
                """,
                (role, learner_id),
            ).fetchone()
            connection.execute(
                """
                insert into beta_audit_events (
                    event_type, actor_user_id, target_user_id, request_id, metadata
                ) values ('role_changed', %s, %s, %s, %s::jsonb)
                """,
                (
                    administrator.learner_id,
                    learner_id,
                    request_id,
                    Jsonb({"previous_role": previous_role, "new_role": role}),
                ),
            )
        assert updated is not None
        return dict(updated)
