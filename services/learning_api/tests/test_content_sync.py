from pathlib import Path

import pytest
from question_bank.course_repository import course_content_hash, lesson_content_hash
from question_bank.repository import content_hash

from learning_api.content_sync import ContentSyncError, check_content
from learning_api.course_catalogue import CourseCatalogue

ROOT = Path(__file__).resolve().parents[3]


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, _query):
        return self

    def fetchall(self):
        return self.rows


def imported(catalogue):
    report = catalogue.report
    return [
        ("course", report.course.stable_key, report.course.revision,
         course_content_hash(report.course, report.lessons, report.pools), report.course.status),
        *[("lesson", lesson.stable_key, lesson.revision, lesson_content_hash(lesson), lesson.status)
          for lesson in report.lessons],
        *[("question", q.stable_key, q.revision, content_hash(q), q.status)
          for q in catalogue.questions],
    ]


def test_exact_content_revisions_are_required_even_when_database_exists():
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    rows = imported(catalogue)
    assert check_content(Rows(rows), catalogue)["questions"] == 144
    # A healthy database with an older lesson must not report ready.
    missing_lesson = [row for row in rows if row[1] != "n1-lesson-01"]
    with pytest.raises(ContentSyncError, match="lesson:n1-lesson-01:r2"):
        check_content(Rows(missing_lesson), catalogue)


def test_same_revision_with_changed_hash_or_publication_status_is_rejected():
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    rows = imported(catalogue)
    rows[0] = (*rows[0][:3], "0" * 64, rows[0][4])
    with pytest.raises(ContentSyncError):
        check_content(Rows(rows), catalogue)
    rows = imported(catalogue)
    rows[0] = (*rows[0][:4], "published")
    with pytest.raises(ContentSyncError):
        check_content(Rows(rows), catalogue)
