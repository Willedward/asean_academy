"""Transactional PostgreSQL import for validated authored questions."""

import hashlib
import json

from .models import AlgebraicResponse, NumericResponse, Question


def content_hash(question: Question) -> str:
    content = {
        "schema_version": question.schema_version,
        "revision": question.revision,
        "title": question.title,
        "calculator_allowed": question.calculator_allowed,
        "question_type": question.question_type,
        "stem": question.model_dump(mode="json")["stem"],
        "parts": question.model_dump(mode="json")["parts"],
        "total_marks": question.total_marks,
        "assets": question.model_dump(mode="json")["assets"],
    }
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class QuestionImporter:
    def __init__(self, connection):
        self.connection = connection

    def _bank_id(self, cursor, bank_key):
        cursor.execute("select id from math_question_banks where bank_key = %s", (bank_key,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Question bank is not seeded: {bank_key}")
        return row[0]

    def _outcome_id(self, cursor, question, code):
        cursor.execute(
            """
            select syllabus_outcomes.id
            from syllabus_outcomes
            join syllabus_topics on syllabus_topics.id = syllabus_outcomes.topic_id
            join curriculum_versions on curriculum_versions.id = syllabus_topics.curriculum_version_id
            where curriculum_versions.version_key = %s
              and syllabus_topics.code = %s
              and syllabus_outcomes.school_level = %s
              and syllabus_outcomes.code = %s
            """,
            (
                question.curriculum_version,
                question.topic_code,
                question.school_level,
                code,
            ),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Syllabus outcome is not seeded: {question.topic_code} {code}")
        return row[0]

    def import_question(self, cursor, question: Question):
        bank_id = self._bank_id(cursor, question.bank_key)
        primary_outcome_id = self._outcome_id(cursor, question, question.primary_outcome)
        cursor.execute(
            """
            insert into math_questions (
                bank_id, primary_outcome_id, stable_key, difficulty, status
            ) values (%s, %s, %s, %s, %s)
            on conflict (bank_id, stable_key) do update set
                primary_outcome_id = excluded.primary_outcome_id,
                difficulty = excluded.difficulty,
                status = excluded.status
            returning id
            """,
            (
                bank_id,
                primary_outcome_id,
                question.stable_key,
                question.difficulty,
                question.status,
            ),
        )
        question_id = cursor.fetchone()[0]
        digest = content_hash(question)
        cursor.execute(
            """
            select id, content_sha256
            from math_question_versions
            where question_id = %s and revision = %s
            """,
            (question_id, question.revision),
        )
        existing = cursor.fetchone()
        if existing:
            if existing[1] != digest:
                raise ValueError(
                    f"{question.stable_key} revision {question.revision} already has different content; "
                    "increment revision instead of overwriting it"
                )
            cursor.execute(
                "update math_question_versions set is_current = (id = %s) where question_id = %s",
                (existing[0], question_id),
            )
            return {"stable_key": question.stable_key, "status": "unchanged"}

        cursor.execute(
            "update math_question_versions set is_current = false where question_id = %s",
            (question_id,),
        )
        payload = question.model_dump(mode="json")
        cursor.execute(
            """
            insert into math_question_versions (
                question_id, revision, schema_version, title, calculator_allowed,
                question_type, stem_blocks, total_marks, content_sha256, provenance,
                is_current, authored_at, reviewed_at, review_notes
            ) values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, true, %s, %s, %s)
            returning id
            """,
            (
                question_id,
                question.revision,
                question.schema_version,
                question.title,
                question.calculator_allowed,
                question.question_type,
                json.dumps(payload["stem"]),
                question.total_marks,
                digest,
                json.dumps(payload["provenance"]),
                question.provenance.created_at,
                question.provenance.reviewed_at,
                question.provenance.review_notes,
            ),
        )
        version_id = cursor.fetchone()[0]

        for asset in question.assets:
            cursor.execute(
                """
                insert into math_question_assets (
                    question_version_id, asset_key, kind, format, storage_path,
                    alt_text, generation_spec, content_sha256, width, height
                ) values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                """,
                (
                    version_id,
                    asset.asset_key,
                    asset.kind,
                    asset.format,
                    asset.path,
                    asset.alt_text,
                    json.dumps(asset.generation_spec),
                    asset.sha256,
                    asset.width,
                    asset.height,
                ),
            )

        for part in question.parts:
            cursor.execute(
                """
                insert into math_question_parts (
                    question_version_id, label, position, prompt_blocks, marks, response_type
                ) values (%s, %s, %s, %s::jsonb, %s, %s)
                returning id
                """,
                (
                    version_id,
                    part.label,
                    part.position,
                    json.dumps([block.model_dump(mode="json") for block in part.prompt]),
                    part.marks,
                    part.response.type,
                ),
            )
            part_id = cursor.fetchone()[0]
            for role, code in [
                ("primary", part.primary_outcome),
                *(("secondary", code) for code in part.secondary_outcomes),
            ]:
                cursor.execute(
                    """
                    insert into math_question_outcomes (question_part_id, outcome_id, role)
                    values (%s, %s, %s)
                    """,
                    (part_id, self._outcome_id(cursor, question, code), role),
                )
            for hint in part.hints:
                cursor.execute(
                    """
                    insert into math_question_hints (question_part_id, stage, content_blocks)
                    values (%s, %s, %s::jsonb)
                    """,
                    (
                        part_id,
                        hint.stage,
                        json.dumps([block.model_dump(mode="json") for block in hint.content]),
                    ),
                )
            self._insert_answer(cursor, part_id, part.response)
            for step in part.solution:
                cursor.execute(
                    """
                    insert into math_solution_steps (
                        question_part_id, position, content_blocks, mark_type, mark_value
                    ) values (%s, %s, %s::jsonb, %s, %s)
                    """,
                    (
                        part_id,
                        step.position,
                        json.dumps([block.model_dump(mode="json") for block in step.content]),
                        step.mark_type,
                        step.mark_value,
                    ),
                )
        return {"stable_key": question.stable_key, "status": "imported", "revision": question.revision}

    def _insert_answer(self, cursor, part_id, response):
        if isinstance(response, NumericResponse):
            canonical_answer = response.canonical_answer
            accepted = response.accepted_answers
            variables = []
            constraints = []
            checker_config = {}
            tolerance = response.absolute_tolerance
            precision = response.rounding_precision
            unit = response.unit.model_dump(mode="json") if response.unit else None
        elif isinstance(response, AlgebraicResponse):
            canonical_answer = response.canonical_expression
            accepted = response.accepted_equivalents
            variables = response.variables
            constraints = response.domain_constraints
            checker_config = response.checker_config
            tolerance = None
            precision = None
            unit = None
        else:
            raise TypeError(f"Unsupported response: {type(response)}")
        cursor.execute(
            """
            insert into math_answer_specs (
                question_part_id, response_type, comparison_mode, canonical_answer,
                canonical_latex, absolute_tolerance, rounding_precision, variables,
                domain_constraints, accepted_answers, checker_config, unit_spec
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
            """,
            (
                part_id,
                response.type,
                response.comparison_mode,
                canonical_answer,
                response.canonical_latex,
                tolerance,
                precision,
                variables,
                constraints,
                json.dumps(accepted),
                json.dumps(checker_config),
                json.dumps(unit) if unit is not None else None,
            ),
        )

    def import_all(self, questions):
        results = []
        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                for question in questions:
                    results.append(self.import_question(cursor, question))
        return results
