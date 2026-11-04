"""Publish the approved cross-year Mathematics diagnostic forms into PostgreSQL."""

from __future__ import annotations

import hashlib
import json

from .diagnostic_plan import DiagnosticFormPlan, DiagnosticPlan

# The forms cover Secondary 1 and 2, but the schema attaches each form to one course revision.
DIAGNOSTIC_ANCHOR_COURSE_KEY = "g3-sec1-math"
FORM_INSTRUCTIONS = (
    "Answer every question on your own. Your answers save automatically, and your results "
    "appear after you submit."
)


def _form_hash(
    plan: DiagnosticPlan, form: DiagnosticFormPlan, questions: dict, outcomes: dict
) -> str:
    payload = {
        "plan_key": plan.plan_key,
        "stable_key": form.stable_key,
        "revision": form.revision,
        "purpose": form.purpose,
        "title": form.title,
        "instructions": FORM_INSTRUCTIONS,
        "estimated_minutes": form.estimated_minutes,
        "band_policy_version": form.band_policy_version,
        "items": [
            {
                "position": item.position,
                "stable_key": item.stable_key,
                "revision": questions[item.stable_key]["revision"],
                "content_sha256": questions[item.stable_key]["content_sha256"],
                "outcome_id": str(outcomes[item.stable_key]),
            }
            for item in form.items
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class DiagnosticFormImporter:
    """Publish forms only when the plan and every question revision are approved."""

    def __init__(self, connection):
        self.connection = connection

    def _questions(self, plan: DiagnosticPlan) -> dict:
        items = [item for form in plan.forms for item in form.items]
        rows = self.connection.execute(
            """
            select questions.stable_key, banks.bank_key, questions.status::text as status,
                   versions.id as version_id, versions.revision, versions.content_sha256,
                   versions.reviewed_at
            from math_questions questions
            join math_question_banks banks on banks.id = questions.bank_id
            join math_question_versions versions
              on versions.question_id = questions.id and versions.is_current
            where questions.stable_key = any(%s)
            """,
            ([item.stable_key for item in items],),
        ).fetchall()
        banks = {item.stable_key: item.bank_key for item in items}
        return {
            row[0]: {
                "status": row[2],
                "version_id": row[3],
                "revision": row[4],
                "content_sha256": row[5],
                "reviewed_at": row[6],
            }
            for row in rows
            if banks[row[0]] == row[1]
        }

    def _outcomes(self, plan: DiagnosticPlan) -> dict:
        outcomes = {}
        for form in plan.forms:
            for item in form.items:
                row = self.connection.execute(
                    """
                    select outcomes.id
                    from syllabus_outcomes outcomes
                    join syllabus_topics topics on topics.id = outcomes.topic_id
                    join curriculum_versions curricula on curricula.id = topics.curriculum_version_id
                    where curricula.version_key = %s
                      and topics.code = %s
                      and outcomes.school_level = %s
                      and outcomes.code = %s
                    """,
                    (
                        plan.curriculum_version,
                        item.topic_code,
                        item.school_level,
                        item.outcome_code,
                    ),
                ).fetchone()
                if row is None:
                    raise ValueError(f"Diagnostic outcome is not imported for {item.stable_key}")
                outcomes[item.stable_key] = row[0]
        return outcomes

    def _import_form(self, plan, form, course_version_id, questions, outcomes) -> str:
        digest = _form_hash(plan, form, questions, outcomes)
        existing = self.connection.execute(
            "select id, content_sha256, is_current from diagnostic_forms "
            "where stable_key = %s and revision = %s",
            (form.stable_key, form.revision),
        ).fetchone()
        if existing is not None and existing[1] != digest:
            raise ValueError(
                f"Diagnostic form {form.stable_key} revision {form.revision} changed; "
                "increment its revision"
            )
        self.connection.execute(
            """
            update diagnostic_forms forms
            set is_current = false
            from course_versions versions
            join courses on courses.id = versions.course_id
            where versions.id = forms.course_version_id
              and courses.course_key = %s
              and forms.purpose = %s
              and forms.is_current
              and not (forms.stable_key = %s and forms.revision = %s)
            """,
            (DIAGNOSTIC_ANCHOR_COURSE_KEY, form.purpose, form.stable_key, form.revision),
        )
        if existing is not None:
            if existing[2]:
                return "unchanged"
            self.connection.execute(
                "update diagnostic_forms set is_current = true where id = %s", (existing[0],)
            )
            return "restored"
        form_id = self.connection.execute(
            """
            insert into diagnostic_forms (
                stable_key, revision, course_version_id, purpose, status, title, instructions,
                estimated_minutes, content_sha256, band_policy_version, is_current,
                reviewed_at, published_at
            ) values (%s, %s, %s, %s, 'published', %s, %s, %s, %s, %s, true, now(), now())
            returning id
            """,
            (
                form.stable_key,
                form.revision,
                course_version_id,
                form.purpose,
                form.title,
                FORM_INSTRUCTIONS,
                form.estimated_minutes,
                digest,
                form.band_policy_version,
            ),
        ).fetchone()[0]
        for item in form.items:
            self.connection.execute(
                """
                insert into diagnostic_form_items (
                    form_id, question_version_id, outcome_id, position, weight
                ) values (%s, %s, %s, %s, 1)
                """,
                (
                    form_id,
                    questions[item.stable_key]["version_id"],
                    outcomes[item.stable_key],
                    item.position,
                ),
            )
        return "published"

    def import_plan(self, plan: DiagnosticPlan) -> dict:
        keys = [item.stable_key for form in plan.forms for item in form.items]
        with self.connection.transaction():
            questions = self._questions(plan)
            missing = sorted(set(keys) - set(questions))
            unapproved = sorted(
                key
                for key, question in questions.items()
                if question["status"] != "published" or question["reviewed_at"] is None
            )
            if plan.status != "published" or missing or unapproved:
                return {
                    "status": "waiting_for_approval",
                    "plan_status": plan.status,
                    "question_count": len(keys),
                    "missing_questions": len(missing),
                    "unapproved_questions": len(unapproved),
                }
            course = self.connection.execute(
                """
                select versions.id
                from course_versions versions
                join courses on courses.id = versions.course_id
                where courses.course_key = %s and versions.is_current
                """,
                (DIAGNOSTIC_ANCHOR_COURSE_KEY,),
            ).fetchone()
            if course is None:
                raise ValueError(f"Import {DIAGNOSTIC_ANCHOR_COURSE_KEY} before its diagnostics")
            outcomes = self._outcomes(plan)
            forms = {
                form.stable_key: self._import_form(plan, form, course[0], questions, outcomes)
                for form in plan.forms
            }
        return {"status": "published", "question_count": len(keys), "forms": forms}
