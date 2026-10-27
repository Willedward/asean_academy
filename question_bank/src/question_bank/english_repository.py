"""Transactional PostgreSQL import for validated objective English sources."""

from __future__ import annotations

import hashlib
import json

from .english_models import EnglishObjectiveQuestion, EnglishPassage


def _digest(payload) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def english_question_content_hash(question: EnglishObjectiveQuestion) -> str:
    payload = question.model_dump(
        mode="json", exclude={"status", "provenance", "parallel_form_of"}
    )
    if question.parallel_form_of is not None:
        payload["parallel_form_of"] = question.parallel_form_of
    return _digest(payload)


def english_passage_revision_hash(passage: EnglishPassage) -> str:
    return _digest(passage.model_dump(mode="json", exclude={"status", "provenance"}))


class EnglishObjectiveImporter:
    """Import one validation-clean English objective snapshot atomically."""

    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def _curriculum(cursor, catalogue):
        curriculum_status = {
            "draft": "draft",
            "reviewed": "active",
            "published": "active",
            "retired": "retired",
        }[catalogue.status]
        cursor.execute(
            """
            insert into curriculum_versions (
                version_key, title, jurisdiction, subject, status, source_reference
            ) values (%s, %s, %s, 'English', %s, %s)
            on conflict (version_key) do update set
                title = excluded.title,
                jurisdiction = excluded.jurisdiction,
                subject = excluded.subject,
                status = excluded.status,
                source_reference = excluded.source_reference
            returning id
            """,
            (
                catalogue.version_key,
                catalogue.title,
                "ASEAN Scholarship preparation for Southeast Asia",
                curriculum_status,
                "backend_resources/english/v1/sources.json",
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _modules_and_outcomes(cursor, curriculum_id, catalogue):
        outcome_ids = {}
        for module in catalogue.modules:
            cursor.execute(
                """
                insert into english_curriculum_modules (
                    curriculum_version_id, module_code, stage, title, purpose, position
                ) values (%s, %s, %s, %s, %s, %s)
                on conflict (curriculum_version_id, module_code) do update set
                    stage = excluded.stage,
                    title = excluded.title,
                    purpose = excluded.purpose,
                    position = excluded.position
                returning id
                """,
                (
                    curriculum_id,
                    module.module_code,
                    module.stage,
                    module.title,
                    module.purpose,
                    module.position,
                ),
            )
            module_id = cursor.fetchone()[0]
            for lesson in module.lessons:
                cursor.execute(
                    """
                    insert into english_curriculum_outcomes (
                        module_id, lesson_code, lesson_key, outcome_code,
                        title, description, position
                    ) values (%s, %s, %s, %s, %s, %s, %s)
                    on conflict (outcome_code) do update set
                        module_id = excluded.module_id,
                        lesson_code = excluded.lesson_code,
                        lesson_key = excluded.lesson_key,
                        title = excluded.title,
                        description = excluded.description,
                        position = excluded.position
                    returning id
                    """,
                    (
                        module_id,
                        lesson.lesson_code,
                        lesson.stable_key,
                        lesson.outcome_code,
                        lesson.title,
                        lesson.outcome,
                        lesson.position,
                    ),
                )
                outcome_ids[lesson.outcome_code] = cursor.fetchone()[0]
        return outcome_ids

    @staticmethod
    def _passage(cursor, passage):
        cursor.execute(
            """
            insert into english_passages (stable_key)
            values (%s)
            on conflict (stable_key) do update set stable_key = excluded.stable_key
            returning id
            """,
            (passage.stable_key,),
        )
        passage_id = cursor.fetchone()[0]
        digest = passage.content_sha256
        cursor.execute(
            """
            select id, content_sha256 from english_passage_versions
            where passage_id = %s and revision = %s
            """,
            (passage_id, passage.revision),
        )
        existing = cursor.fetchone()
        if existing and existing[1] != digest:
            raise ValueError(
                f"Passage {passage.stable_key} revision {passage.revision} changed; increment its revision"
            )
        cursor.execute(
            "update english_passage_versions set is_current = false where passage_id = %s",
            (passage_id,),
        )
        if existing:
            cursor.execute(
                """
                update english_passage_versions set status=%s, provenance=%s::jsonb,
                    reviewed_at=%s, review_notes=%s, is_current=true
                where id=%s
                """,
                (
                    passage.status,
                    json.dumps(passage.provenance.model_dump(mode="json")),
                    passage.provenance.reviewed_at,
                    passage.provenance.review_notes,
                    existing[0],
                ),
            )
            return existing[0]
        cursor.execute(
            """
            insert into english_passage_versions (
                passage_id, revision, schema_version, title, text_type, paragraphs,
                attribution, status, content_sha256, provenance, is_current,
                authored_at, reviewed_at, review_notes
            ) values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb,
                      true, %s, %s, %s)
            returning id
            """,
            (
                passage_id,
                passage.revision,
                passage.schema_version,
                passage.title,
                passage.text_type,
                json.dumps(passage.paragraphs),
                passage.attribution,
                passage.status,
                digest,
                json.dumps(passage.provenance.model_dump(mode="json")),
                passage.provenance.created_at,
                passage.provenance.reviewed_at,
                passage.provenance.review_notes,
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _bank(cursor, curriculum_id, manifest):
        cursor.execute(
            """
            insert into english_objective_question_banks (
                curriculum_version_id, bank_key, revision, schema_version, title,
                status, expected_question_count, outcome_codes, pool_distribution,
                source_refs
            ) values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
            on conflict (bank_key) do update set
                curriculum_version_id = excluded.curriculum_version_id,
                revision = excluded.revision,
                schema_version = excluded.schema_version,
                title = excluded.title,
                status = excluded.status,
                expected_question_count = excluded.expected_question_count,
                outcome_codes = excluded.outcome_codes,
                pool_distribution = excluded.pool_distribution,
                source_refs = excluded.source_refs
            returning id
            """,
            (
                curriculum_id,
                manifest.bank_key,
                manifest.revision,
                manifest.schema_version,
                manifest.title,
                manifest.status,
                manifest.expected_question_count,
                json.dumps(manifest.outcome_codes),
                json.dumps(manifest.pool_distribution),
                json.dumps(manifest.source_refs),
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _question(cursor, question, bank_id, outcome_id, passage_version_id):
        cursor.execute(
            """
            insert into english_objective_questions (
                bank_id, outcome_id, stable_key, difficulty, question_type,
                exposure_pool, status
            ) values (%s, %s, %s, %s, %s, %s, %s)
            on conflict (stable_key) do update set
                bank_id = excluded.bank_id,
                outcome_id = excluded.outcome_id,
                difficulty = excluded.difficulty,
                question_type = excluded.question_type,
                exposure_pool = excluded.exposure_pool,
                status = excluded.status
            returning id
            """,
            (
                bank_id,
                outcome_id,
                question.stable_key,
                question.difficulty,
                question.question_type,
                question.exposure_pool,
                question.status,
            ),
        )
        question_id = cursor.fetchone()[0]
        digest = english_question_content_hash(question)
        cursor.execute(
            """
            select id, content_sha256 from english_objective_question_versions
            where question_id=%s and revision=%s
            """,
            (question_id, question.revision),
        )
        existing = cursor.fetchone()
        if existing and existing[1] != digest:
            raise ValueError(
                f"Question {question.stable_key} revision {question.revision} changed; increment its revision"
            )
        cursor.execute(
            "update english_objective_question_versions set is_current=false where question_id=%s",
            (question_id,),
        )
        provenance = json.dumps(question.provenance.model_dump(mode="json"))
        parts = json.dumps([part.model_dump(mode="json") for part in question.parts])
        if existing:
            cursor.execute(
                """
                update english_objective_question_versions set
                    passage_version_id=%s, provenance=%s::jsonb, reviewed_at=%s,
                    review_notes=%s, is_current=true
                where id=%s
                """,
                (
                    passage_version_id,
                    provenance,
                    question.provenance.reviewed_at,
                    question.provenance.review_notes,
                    existing[0],
                ),
            )
            return existing[0]
        cursor.execute(
            """
            insert into english_objective_question_versions (
                question_id, passage_version_id, revision, schema_version, title,
                instructions, feedback_timing, parts, content_sha256, provenance,
                is_current, authored_at, reviewed_at, review_notes
            ) values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb,
                      true, %s, %s, %s)
            returning id
            """,
            (
                question_id,
                passage_version_id,
                question.revision,
                question.schema_version,
                question.title,
                question.instructions,
                question.feedback_timing,
                parts,
                digest,
                provenance,
                question.provenance.created_at,
                question.provenance.reviewed_at,
                question.provenance.review_notes,
            ),
        )
        return cursor.fetchone()[0]

    def import_all(self, report):
        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                curriculum_id = self._curriculum(cursor, report.catalogue)
                outcome_ids = self._modules_and_outcomes(cursor, curriculum_id, report.catalogue)
                passage_ids = {
                    (passage.stable_key, passage.revision): self._passage(cursor, passage)
                    for passage in report.passages
                }
                bank_ids = {
                    manifest.bank_key: self._bank(cursor, curriculum_id, manifest)
                    for manifest in report.manifests
                }
                version_ids = []
                for question in report.questions:
                    passage_version_id = None
                    if question.passage_ref is not None:
                        passage_version_id = passage_ids[
                            (question.passage_ref.stable_key, question.passage_ref.revision)
                        ]
                    version_ids.append(
                        self._question(
                            cursor,
                            question,
                            bank_ids[question.bank_key],
                            outcome_ids[question.outcome_code],
                            passage_version_id,
                        )
                    )
        return {
            "curriculum_version": report.catalogue.version_key,
            "module_count": len(report.catalogue.modules),
            "outcome_count": len(outcome_ids),
            "passage_count": len(passage_ids),
            "bank_count": len(bank_ids),
            "question_count": len(version_ids),
        }
