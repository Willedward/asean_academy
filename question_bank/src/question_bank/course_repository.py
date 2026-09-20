"""Transactional PostgreSQL import for validated course authoring sources."""

from __future__ import annotations

import hashlib
import json

from .course_models import Course, Lesson, QuestionPools


def _digest(payload) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def lesson_content_hash(lesson: Lesson) -> str:
    """Hash learner-visible lesson content while excluding review workflow fields."""
    payload = lesson.model_dump(mode="json", exclude={"status", "provenance"})
    return _digest(payload)


def course_content_hash(
    course: Course,
    lessons: list[Lesson],
    pools: QuestionPools,
) -> str:
    """Hash the complete course snapshot pinned by one course revision."""
    course_payload = course.model_dump(mode="json", exclude={"status", "provenance"})
    lesson_payloads = [
        lesson.model_dump(mode="json", exclude={"status", "provenance"})
        for lesson in sorted(lessons, key=lambda item: item.position)
    ]
    return _digest(
        {
            "course": course_payload,
            "lessons": lesson_payloads,
            "question_pools": pools.model_dump(mode="json"),
        }
    )


class CourseImporter:
    """Import one validated course snapshot without mutating authored revisions."""

    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def _id(cursor, query, params, missing):
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not row:
            raise ValueError(missing)
        return row[0]

    def _curriculum_id(self, cursor, version_key):
        return self._id(
            cursor,
            "select id from curriculum_versions where version_key = %s",
            (version_key,),
            f"Curriculum version is not seeded: {version_key}",
        )

    def _topic_id(self, cursor, curriculum_id, topic_code):
        return self._id(
            cursor,
            """
            select id from syllabus_topics
            where curriculum_version_id = %s and code = %s
            """,
            (curriculum_id, topic_code),
            f"Syllabus topic is not seeded: {topic_code}",
        )

    def _outcome_id(self, cursor, topic_id, school_level, code):
        return self._id(
            cursor,
            """
            select id from syllabus_outcomes
            where topic_id = %s and school_level = %s and code = %s
            """,
            (topic_id, school_level, code),
            f"Syllabus outcome is not seeded: {code}",
        )

    def _question_id(self, cursor, bank_key, question_key):
        return self._id(
            cursor,
            """
            select math_questions.id
            from math_questions
            join math_question_banks on math_question_banks.id = math_questions.bank_id
            where math_question_banks.bank_key = %s and math_questions.stable_key = %s
            """,
            (bank_key, question_key),
            f"Question must be imported before course mapping: {question_key}",
        )

    @staticmethod
    def _insert_programme(cursor, course):
        cursor.execute(
            """
            insert into programmes (programme_key, title, description)
            values (%s, %s, %s)
            on conflict (programme_key) do update set
                title = excluded.title,
                description = excluded.description,
                updated_at = now()
            returning id
            """,
            (
                course.programme_key,
                "ASEAN Scholarship preparation",
                "Structured preparation courses for ASEAN scholarship applicants.",
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _insert_course(cursor, course, programme_id, curriculum_id):
        cursor.execute(
            """
            insert into courses (
                programme_id, curriculum_version_id, course_key, school_level, subject
            ) values (%s, %s, %s, %s, %s)
            on conflict (course_key) do update set
                programme_id = excluded.programme_id,
                curriculum_version_id = excluded.curriculum_version_id,
                school_level = excluded.school_level,
                subject = excluded.subject
            returning id
            """,
            (
                programme_id,
                curriculum_id,
                course.stable_key,
                course.school_level,
                course.subject,
            ),
        )
        return cursor.fetchone()[0]

    def _insert_course_version(self, cursor, course, course_id, digest):
        cursor.execute(
            """
            select id, content_sha256
            from course_versions
            where course_id = %s and revision = %s
            """,
            (course_id, course.revision),
        )
        existing = cursor.fetchone()
        provenance = course.provenance.model_dump(mode="json")
        if existing:
            if existing[1] != digest:
                raise ValueError(
                    f"{course.stable_key} revision {course.revision} already has different "
                    "content; increment revision instead of overwriting it"
                )
            cursor.execute(
                "update course_versions set is_current = false where course_id = %s",
                (course_id,),
            )
            cursor.execute(
                """
                update course_versions set
                    status = %s,
                    provenance = %s::jsonb,
                    reviewed_at = %s,
                    review_notes = %s,
                    is_current = true
                where id = %s
                """,
                (
                    course.status,
                    json.dumps(provenance),
                    course.provenance.reviewed_at,
                    course.provenance.review_notes,
                    existing[0],
                ),
            )
            return existing[0], False

        cursor.execute(
            "update course_versions set is_current = false where course_id = %s",
            (course_id,),
        )
        cursor.execute(
            """
            insert into course_versions (
                course_id, revision, schema_version, title, description, status,
                content_sha256, provenance, is_current, authored_at, reviewed_at,
                review_notes
            ) values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, true, %s, %s, %s)
            returning id
            """,
            (
                course_id,
                course.revision,
                course.schema_version,
                course.title,
                course.description,
                course.status,
                digest,
                json.dumps(provenance),
                course.provenance.created_at,
                course.provenance.reviewed_at,
                course.provenance.review_notes,
            ),
        )
        return cursor.fetchone()[0], True

    @staticmethod
    def _insert_lesson_identity(cursor, lesson, unit_id):
        cursor.execute(
            """
            insert into course_lessons (unit_id, lesson_key)
            values (%s, %s)
            on conflict (lesson_key) do update set unit_id = excluded.unit_id
            returning id
            """,
            (unit_id, lesson.stable_key),
        )
        return cursor.fetchone()[0]

    def _insert_lesson_version(self, cursor, lesson, lesson_id):
        digest = lesson_content_hash(lesson)
        cursor.execute(
            """
            select id, content_sha256
            from lesson_versions
            where lesson_id = %s and revision = %s
            """,
            (lesson_id, lesson.revision),
        )
        existing = cursor.fetchone()
        provenance = lesson.provenance.model_dump(mode="json")
        if existing:
            if existing[1] != digest:
                raise ValueError(
                    f"{lesson.stable_key} revision {lesson.revision} already has different "
                    "content; increment revision instead of overwriting it"
                )
            cursor.execute(
                "update lesson_versions set is_current = false where lesson_id = %s",
                (lesson_id,),
            )
            cursor.execute(
                """
                update lesson_versions set
                    status = %s,
                    provenance = %s::jsonb,
                    reviewed_at = %s,
                    review_notes = %s,
                    is_current = true
                where id = %s
                """,
                (
                    lesson.status,
                    json.dumps(provenance),
                    lesson.provenance.reviewed_at,
                    lesson.provenance.review_notes,
                    existing[0],
                ),
            )
            return existing[0], False

        cursor.execute(
            "update lesson_versions set is_current = false where lesson_id = %s",
            (lesson_id,),
        )
        cursor.execute(
            """
            insert into lesson_versions (
                lesson_id, revision, schema_version, title, summary, status,
                estimated_minutes, objectives, mastery_policy_key, content_sha256,
                provenance, is_current, authored_at, reviewed_at, review_notes
            ) values (
                %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s,
                %s::jsonb, true, %s, %s, %s
            )
            returning id
            """,
            (
                lesson_id,
                lesson.revision,
                lesson.schema_version,
                lesson.title,
                lesson.summary,
                lesson.status,
                lesson.estimated_minutes,
                json.dumps(lesson.objectives),
                lesson.mastery_policy_key,
                digest,
                json.dumps(provenance),
                lesson.provenance.created_at,
                lesson.provenance.reviewed_at,
                lesson.provenance.review_notes,
            ),
        )
        return cursor.fetchone()[0], True

    def import_all(self, course: Course, lessons: list[Lesson], pools: QuestionPools):
        """Import a fully validated snapshot as one database transaction."""
        digest = course_content_hash(course, lessons, pools)
        lesson_by_key = {lesson.stable_key: lesson for lesson in lessons}
        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                curriculum_id = self._curriculum_id(cursor, course.curriculum_version)
                programme_id = self._insert_programme(cursor, course)
                course_id = self._insert_course(
                    cursor, course, programme_id, curriculum_id
                )
                course_version_id, created = self._insert_course_version(
                    cursor, course, course_id, digest
                )
                if not created:
                    self._sync_existing_lessons(cursor, course_id, lessons)
                    return {
                        "stable_key": course.stable_key,
                        "revision": course.revision,
                        "status": "unchanged",
                    }

                for policy in course.mastery_policies:
                    cursor.execute(
                        """
                        insert into mastery_policies (
                            course_version_id, policy_key,
                            minimum_eventual_correct_percentage,
                            mastery_requires_checkpoint, checkpoint_passing_percentage,
                            give_up_after_incorrect_attempts, hints_penalize_marks
                        ) values (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            course_version_id,
                            policy.key,
                            policy.minimum_eventual_correct_percentage,
                            policy.mastery_requires_checkpoint,
                            policy.checkpoint_passing_percentage,
                            policy.give_up_after_incorrect_attempts,
                            policy.hints_penalize_marks,
                        ),
                    )

                lesson_ids = {}
                lesson_version_ids = {}
                unit_version_ids = {}
                for unit in course.units:
                    topic_id = self._topic_id(cursor, curriculum_id, unit.topic_code)
                    cursor.execute(
                        """
                        insert into course_units (course_id, unit_key, topic_id)
                        values (%s, %s, %s)
                        on conflict (course_id, unit_key) do update set
                            topic_id = excluded.topic_id
                        returning id
                        """,
                        (course_id, unit.stable_key, topic_id),
                    )
                    unit_id = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        insert into unit_versions (
                            unit_id, course_version_id, position, title,
                            checkpoint_question_count
                        ) values (%s, %s, %s, %s, %s)
                        returning id
                        """,
                        (
                            unit_id,
                            course_version_id,
                            unit.position,
                            unit.title,
                            unit.checkpoint_question_count,
                        ),
                    )
                    unit_version_id = cursor.fetchone()[0]
                    unit_version_ids[unit.stable_key] = unit_version_id

                    for reference in unit.lessons:
                        lesson = lesson_by_key[reference.stable_key]
                        lesson_id = self._insert_lesson_identity(cursor, lesson, unit_id)
                        lesson_version_id, is_new = self._insert_lesson_version(
                            cursor, lesson, lesson_id
                        )
                        lesson_ids[lesson.stable_key] = lesson_id
                        lesson_version_ids[lesson.stable_key] = lesson_version_id
                        cursor.execute(
                            """
                            insert into unit_version_lessons (
                                unit_version_id, lesson_version_id, position,
                                required_practice_count
                            ) values (%s, %s, %s, %s)
                            """,
                            (
                                unit_version_id,
                                lesson_version_id,
                                reference.position,
                                reference.required_practice_count,
                            ),
                        )
                        if is_new:
                            self._insert_lesson_content(
                                cursor,
                                course,
                                lesson,
                                lesson_version_id,
                                topic_id,
                            )

                for lesson in lessons:
                    lesson_version_id = lesson_version_ids[lesson.stable_key]
                    for prerequisite in lesson.prerequisite_lessons:
                        cursor.execute(
                            """
                            insert into lesson_prerequisites (
                                lesson_version_id, prerequisite_lesson_id
                            ) values (%s, %s)
                            on conflict do nothing
                            """,
                            (lesson_version_id, lesson_ids[prerequisite]),
                        )

                self._insert_pools(
                    cursor,
                    pools,
                    unit_version_ids[pools.unit_key],
                    lesson_version_ids,
                )
        return {
            "stable_key": course.stable_key,
            "revision": course.revision,
            "status": "imported",
            "lessons": len(lessons),
            "pools": len(pools.pools),
        }

    def _sync_existing_lessons(self, cursor, course_id, lessons):
        """Promote review state while preserving immutable lesson content."""
        for lesson in lessons:
            cursor.execute(
                """
                select lesson_versions.id, lesson_versions.lesson_id,
                       lesson_versions.content_sha256
                from lesson_versions
                join course_lessons on course_lessons.id = lesson_versions.lesson_id
                join course_units on course_units.id = course_lessons.unit_id
                where course_units.course_id = %s
                  and course_lessons.lesson_key = %s
                  and lesson_versions.revision = %s
                """,
                (course_id, lesson.stable_key, lesson.revision),
            )
            existing = cursor.fetchone()
            if not existing:
                raise ValueError(
                    f"Course revision exists without lesson revision: {lesson.stable_key}"
                )
            if existing[2] != lesson_content_hash(lesson):
                raise ValueError(
                    f"{lesson.stable_key} revision {lesson.revision} already has different "
                    "content; increment revision instead of overwriting it"
                )
            provenance = lesson.provenance.model_dump(mode="json")
            cursor.execute(
                "update lesson_versions set is_current = false where lesson_id = %s",
                (existing[1],),
            )
            cursor.execute(
                """
                update lesson_versions set
                    status = %s,
                    provenance = %s::jsonb,
                    reviewed_at = %s,
                    review_notes = %s,
                    is_current = true
                where id = %s
                """,
                (
                    lesson.status,
                    json.dumps(provenance),
                    lesson.provenance.reviewed_at,
                    lesson.provenance.review_notes,
                    existing[0],
                ),
            )

    def _insert_lesson_content(
        self, cursor, course, lesson, lesson_version_id, topic_id
    ):
        for position, code in enumerate(lesson.outcomes, start=1):
            cursor.execute(
                """
                insert into lesson_outcomes (lesson_version_id, outcome_id, position)
                values (%s, %s, %s)
                """,
                (
                    lesson_version_id,
                    self._outcome_id(
                        cursor, topic_id, course.school_level, code
                    ),
                    position,
                ),
            )
        for section in lesson.sections:
            content = section.model_dump(mode="json")
            cursor.execute(
                """
                insert into lesson_sections (
                    lesson_version_id, section_key, position, section_type,
                    title, content
                ) values (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    lesson_version_id,
                    section.stable_key,
                    section.position,
                    section.type,
                    section.title,
                    json.dumps(content),
                ),
            )
        for asset in lesson.assets:
            cursor.execute(
                """
                insert into lesson_assets (
                    lesson_version_id, asset_key, kind, format, storage_path,
                    alt_text, generation_spec, content_sha256, width, height
                ) values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                """,
                (
                    lesson_version_id,
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

    def _insert_pools(
        self, cursor, pools, unit_version_id, lesson_version_ids
    ):
        for pool in pools.pools:
            if pool.type == "lesson_practice":
                cursor.execute(
                    """
                    insert into lesson_question_pools (
                        unit_version_id, lesson_version_id, pool_key,
                        expected_question_count
                    ) values (%s, %s, %s, %s)
                    returning id
                    """,
                    (
                        unit_version_id,
                        lesson_version_ids[pool.lesson_key],
                        pool.stable_key,
                        pool.expected_question_count,
                    ),
                )
                pool_id = cursor.fetchone()[0]
                table = "lesson_question_pool_items"
            else:
                cursor.execute(
                    """
                    insert into unit_checkpoint_pools (
                        unit_version_id, pool_key, pool_type,
                        expected_question_count
                    ) values (%s, %s, %s, %s)
                    returning id
                    """,
                    (
                        unit_version_id,
                        pool.stable_key,
                        pool.type,
                        pool.expected_question_count,
                    ),
                )
                pool_id = cursor.fetchone()[0]
                table = "unit_checkpoint_pool_items"

            for item in pool.items:
                question_id = self._question_id(
                    cursor, pools.bank_key, item.question_key
                )
                cursor.execute(
                    f"""
                    insert into {table} (
                        pool_id, question_id, position, stage, weight
                    ) values (%s, %s, %s, %s, %s)
                    """,
                    (
                        pool_id,
                        question_id,
                        item.position,
                        item.stage,
                        item.weight,
                    ),
                )
