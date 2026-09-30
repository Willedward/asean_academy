"""Transactional PostgreSQL import for syllabus catalogues and their banks."""

from __future__ import annotations

import json
import re

from .catalogue import BankBlueprint, SyllabusCatalogue
from .models import Question
from .repository import QuestionImporter


class CatalogueImporter:
    """Upsert catalogue metadata before importing immutable question revisions."""

    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def _upsert_curriculum(cursor, syllabus: SyllabusCatalogue):
        cursor.execute(
            """
            insert into curriculum_versions (
                version_key, title, jurisdiction, subject, status, source_reference
            ) values (%s, %s, %s, %s, %s, %s)
            on conflict (version_key) do update set
                title = excluded.title,
                jurisdiction = excluded.jurisdiction,
                subject = excluded.subject,
                status = excluded.status,
                source_reference = excluded.source_reference,
                updated_at = now()
            returning id
            """,
            (
                syllabus.version_key,
                syllabus.title,
                syllabus.jurisdiction,
                syllabus.subject,
                syllabus.status,
                syllabus.source_reference,
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _upsert_topic(cursor, curriculum_id, topic):
        cursor.execute(
            """
            insert into syllabus_topics (
                curriculum_version_id, code, title, strand, position
            ) values (%s, %s, %s, %s, %s)
            on conflict (curriculum_version_id, code) do update set
                title = excluded.title,
                strand = excluded.strand,
                position = excluded.position
            returning id
            """,
            (curriculum_id, topic.code, topic.title, topic.strand, topic.position),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _upsert_outcome(cursor, topic_id, outcome):
        cursor.execute(
            """
            insert into syllabus_outcomes (
                topic_id, school_level, code, description, position
            ) values (%s, %s, %s, %s, %s)
            on conflict (topic_id, school_level, code) do update set
                description = excluded.description,
                position = excluded.position
            """,
            (
                topic_id,
                outcome.school_level,
                outcome.code,
                outcome.description,
                outcome.position,
            ),
        )

    @staticmethod
    def _upsert_bank(cursor, curriculum_id, topic_id, blueprint: BankBlueprint):
        revision_match = re.search(r"-v([0-9]+)$", blueprint.bank_key)
        revision = int(revision_match.group(1))
        cursor.execute(
            """
            insert into math_question_banks (
                id, bank_key, curriculum_version_id, topic_id, school_level,
                revision, schema_version, title, description, status,
                expected_question_count, difficulty_counts,
                source_style_references, published_at, bank_role
            ) values (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s::jsonb, %s::jsonb,
                case when %s = 'published' then now() else null end,
                %s
            )
            on conflict (bank_key) do update set
                curriculum_version_id = excluded.curriculum_version_id,
                topic_id = excluded.topic_id,
                school_level = excluded.school_level,
                schema_version = excluded.schema_version,
                title = excluded.title,
                description = excluded.description,
                status = excluded.status,
                expected_question_count = excluded.expected_question_count,
                difficulty_counts = excluded.difficulty_counts,
                source_style_references = excluded.source_style_references,
                published_at = case
                    when excluded.status = 'published'
                    then coalesce(math_question_banks.published_at, now())
                    else null
                end,
                bank_role = excluded.bank_role,
                updated_at = now()
            """,
            (
                blueprint.bank_id,
                blueprint.bank_key,
                curriculum_id,
                topic_id,
                blueprint.school_level,
                revision,
                blueprint.schema_version,
                f"{blueprint.topic.code}: {blueprint.topic.title}",
                f"{blueprint.course} {blueprint.school_level} {blueprint.bank_role} bank",
                blueprint.status,
                blueprint.question_count,
                json.dumps(blueprint.difficulty_distribution),
                json.dumps(blueprint.style_references),
                blueprint.status,
                blueprint.bank_role,
            ),
        )

    def import_all(
        self,
        syllabus: SyllabusCatalogue,
        banks: list[tuple[BankBlueprint, list[Question]]],
    ) -> dict:
        question_importer = QuestionImporter(self.connection)
        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                curriculum_id = self._upsert_curriculum(cursor, syllabus)
                topic_ids = {}
                for topic in syllabus.topics:
                    topic_id = self._upsert_topic(cursor, curriculum_id, topic)
                    topic_ids[topic.code] = topic_id
                    for outcome in topic.outcomes:
                        self._upsert_outcome(cursor, topic_id, outcome)
                question_results = []
                for blueprint, questions in banks:
                    self._upsert_bank(
                        cursor,
                        curriculum_id,
                        topic_ids[blueprint.topic.code],
                        blueprint,
                    )
                    for question in questions:
                        question_results.append(
                            question_importer.import_question(cursor, question)
                        )
        return {
            "catalogue_version": syllabus.version_key,
            "topic_count": len(syllabus.topics),
            "bank_count": len(banks),
            "question_count": len(question_results),
            "question_results": question_results,
        }
