"""Compare the serving catalogue with imported immutable PostgreSQL revisions."""
from __future__ import annotations

import psycopg
from question_bank.course_repository import course_content_hash, lesson_content_hash
from question_bank.repository import content_hash

from .course_catalogue import CourseCatalogue


class ContentSyncError(RuntimeError):
    pass


def check_content(connection, catalogue: CourseCatalogue) -> dict:
    report = catalogue.report
    expected = {
        ("course", report.course.stable_key, report.course.revision):
            (course_content_hash(report.course, report.lessons, report.pools), report.course.status),
        **{("lesson", item.stable_key, item.revision): (lesson_content_hash(item), item.status)
           for item in report.lessons},
        **{("question", item.stable_key, item.revision): (content_hash(item), item.status)
           for item in catalogue.questions},
    }
    # Do not compare is_current: old and new releases can overlap during a rolling deploy.
    rows = connection.execute("""
        select 'course', c.course_key, v.revision, v.content_sha256, v.status::text
        from course_versions v join courses c on c.id = v.course_id
        union all
        select 'lesson', l.lesson_key, v.revision, v.content_sha256, v.status::text
        from lesson_versions v join course_lessons l on l.id = v.lesson_id
        union all
        select 'question', q.stable_key, v.revision, v.content_sha256, q.status::text
        from math_question_versions v join math_questions q on q.id = v.question_id
    """).fetchall()
    actual = {(kind, key, revision): (digest, status)
              for kind, key, revision, digest, status in rows}
    mismatches = [f"{kind}:{key}:r{revision}"
                  for (kind, key, revision), value in expected.items()
                  if actual.get((kind, key, revision)) != value]
    if mismatches:
        raise ContentSyncError(
            "Imported content is out of sync: " + ", ".join(mismatches[:8])
            + ". Run corepack pnpm bootstrap:api --apply."
        )
    return {"status": "current", "course_key": report.course.stable_key,
            "course_revision": report.course.revision, "lessons": len(report.lessons),
            "questions": len(catalogue.questions)}


def verify_database_content(database_url: str, catalogue: CourseCatalogue) -> dict:
    with psycopg.connect(database_url, connect_timeout=5, prepare_threshold=None) as connection:
        return check_content(connection, catalogue)
