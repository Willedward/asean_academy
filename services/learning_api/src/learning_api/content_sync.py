"""Compare the serving catalogue with imported immutable PostgreSQL revisions."""
from __future__ import annotations

import psycopg
from question_bank.course_repository import course_content_hash, lesson_content_hash
from question_bank.english_repository import english_question_content_hash
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
    english = catalogue.english_learner_report
    expected_english_questions = {
        (item.stable_key, item.revision): (english_question_content_hash(item), item.status)
        for item in english.questions
    }
    english_question_rows = connection.execute("""
        select questions.stable_key, versions.revision, versions.content_sha256,
               questions.status::text
        from english_objective_question_versions versions
        join english_objective_questions questions on questions.id=versions.question_id
    """).fetchall()
    actual_english_questions = {
        (key, revision): (digest, status)
        for key, revision, digest, status in english_question_rows
    }
    english_question_mismatches = [
        f"english_question:{key}:r{revision}"
        for (key, revision), value in expected_english_questions.items()
        if actual_english_questions.get((key, revision)) != value
    ]
    expected_passages = {
        (item.stable_key, item.revision): (item.content_sha256, item.status)
        for item in english.passages
    }
    passage_rows = connection.execute("""
        select passages.stable_key, versions.revision, versions.content_sha256,
               versions.status::text
        from english_passage_versions versions
        join english_passages passages on passages.id=versions.passage_id
    """).fetchall()
    actual_passages = {
        (key, revision): (digest, status)
        for key, revision, digest, status in passage_rows
    }
    passage_mismatches = [
        f"english_passage:{key}:r{revision}"
        for (key, revision), value in expected_passages.items()
        if actual_passages.get((key, revision)) != value
    ]
    english_mismatches = english_question_mismatches + passage_mismatches
    if english_mismatches:
        raise ContentSyncError(
            "Imported English content is out of sync: "
            + ", ".join(english_mismatches[:8])
            + ". Run corepack pnpm bootstrap:api --apply."
        )
    return {
        "status": "current",
        "course_key": report.course.stable_key,
        "course_revision": report.course.revision,
        "lessons": len(report.lessons),
        "questions": len(catalogue.questions),
        "english_passages": len(english.passages),
        "english_questions": len(english.questions),
    }


def verify_database_content(database_url: str, catalogue: CourseCatalogue) -> dict:
    with psycopg.connect(database_url, connect_timeout=5, prepare_threshold=None) as connection:
        return check_content(connection, catalogue)
