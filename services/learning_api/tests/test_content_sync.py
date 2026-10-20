from pathlib import Path

import pytest
from question_bank.course_repository import course_content_hash, lesson_content_hash
from question_bank.english_repository import english_question_content_hash
from question_bank.repository import content_hash

from learning_api.content_sync import ContentSyncError, check_content
from learning_api.course_catalogue import CourseCatalogue

ROOT = Path(__file__).resolve().parents[3]


class Rows:
    def __init__(self, rows, english_questions, english_passages):
        self.rows = rows
        self.english_questions = english_questions
        self.english_passages = english_passages
        self.current = rows

    def execute(self, query):
        if "english_objective_question_versions" in query:
            self.current = self.english_questions
        elif "english_passage_versions" in query:
            self.current = self.english_passages
        else:
            self.current = self.rows
        return self

    def fetchall(self):
        return self.current


def imported(catalogue):
    report = catalogue.report
    return [
        (
            "course",
            report.course.stable_key,
            report.course.revision,
            course_content_hash(report.course, report.lessons, report.pools),
            report.course.status,
        ),
        *[
            (
                "lesson",
                lesson.stable_key,
                lesson.revision,
                lesson_content_hash(lesson),
                lesson.status,
            )
            for lesson in report.lessons
        ],
        *[
            ("question", q.stable_key, q.revision, content_hash(q), q.status)
            for q in catalogue.questions
        ],
    ]


def database(catalogue, rows=None):
    english = catalogue.english_learner_report
    return Rows(
        rows if rows is not None else imported(catalogue),
        [
            (
                question.stable_key,
                question.revision,
                english_question_content_hash(question),
                question.status,
            )
            for question in english.questions
        ],
        [
            (passage.stable_key, passage.revision, passage.content_sha256, passage.status)
            for passage in english.passages
        ],
    )


def test_exact_content_revisions_are_required_even_when_database_exists():
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    rows = imported(catalogue)
    assert check_content(database(catalogue, rows), catalogue)["questions"] == 1040
    # A healthy database with an older lesson must not report ready.
    missing_lesson = [row for row in rows if row[1] != "n1-lesson-01"]
    with pytest.raises(ContentSyncError, match="lesson:n1-lesson-01:r2"):
        check_content(database(catalogue, missing_lesson), catalogue)


def test_same_revision_with_changed_hash_or_publication_status_is_rejected():
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    rows = imported(catalogue)
    rows[0] = (*rows[0][:3], "0" * 64, rows[0][4])
    with pytest.raises(ContentSyncError):
        check_content(database(catalogue, rows), catalogue)
    rows = imported(catalogue)
    rows[0] = (*rows[0][:4], "published")
    with pytest.raises(ContentSyncError):
        check_content(database(catalogue, rows), catalogue)


def test_missing_english_revision_blocks_readiness():
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    stored = database(catalogue)
    stored.english_questions = [row for row in stored.english_questions if row[0] != "ev-l1-001"]

    with pytest.raises(ContentSyncError, match="english_question:ev-l1-001:r1"):
        check_content(stored, catalogue)
