"""Run only against a disposable TEST_DATABASE_URL."""
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row

from learning_api.admin_analytics_contracts import CurriculumMigrationRequest
from learning_api.admin_analytics_repository import PostgresAdminAnalyticsRepository
from learning_api.admin_repository import BetaOperationsError
from learning_api.course_catalogue import CourseCatalogue
from learning_api.curriculum_admin import migrate, preview_transition
from learning_api.identity import AuthenticatedLearner
from learning_api.postgres_practice import PostgresPracticeEngine

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.postgres
def test_curriculum_migration_is_previewed_audited_and_preserves_progress():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires a disposable database")
    learner, administrator = uuid4(), uuid4()
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    repository = PostgresAdminAnalyticsRepository(url)
    with psycopg.connect(url, row_factory=dict_row) as c:
        for user, role in [(learner, "student"), (administrator, "academic_admin")]:
            c.execute("insert into auth.users(id,email) values (%s,%s)", (user, f"{user}@example.test"))
            c.execute("insert into profiles(id,email,role) values (%s,%s,%s)", (user, f"{user}@example.test", role))
        target = c.execute("select id, course_id, revision, content_sha256 from course_versions where is_current").fetchone()
        previous = c.execute("""insert into course_versions(course_id,revision,schema_version,title,description,
            status,content_sha256,provenance,is_current,authored_at)
            values (%s,1,'1.0','Old snapshot','Test','draft',%s,'{}',false,now())
            on conflict (course_id,revision) do update set is_current=false returning id""",
            (target["course_id"], "f"*64)).fetchone()
        c.execute("insert into course_enrolments(student_id,course_id,course_version_id) values(%s,%s,%s)",
                  (learner, target["course_id"], previous["id"]))
    with repository._connect() as c:
        preview, _ = preview_transition(c, learner, "g3-sec1-math", target["revision"])
    assert preview["allowed"]
    body = CurriculumMigrationRequest(course_key="g3-sec1-math", from_revision=1,
        target_revision=target["revision"], target_hash=preview["target_hash"], reason="Beta curriculum update")
    actor = AuthenticatedLearner(str(administrator), "academic_admin")
    result = migrate(repository, actor, learner, body, "migration-test", catalogue)
    assert result["migrated"]
    with psycopg.connect(url) as c:
        assert c.execute("select count(*) from beta_audit_events where target_user_id=%s and event_type='course_revision_changed'", (learner,)).fetchone()[0] == 1
    with pytest.raises(BetaOperationsError, match="Preview again"):
        migrate(repository, actor, learner, body, "stale-test", catalogue)
    engine = PostgresPracticeEngine(url, catalogue.questions, str(learner), allow_drafts=True)
    engine.create_session(question_count=1, idempotency_key=str(uuid4()), context={"lesson_key": "n1-lesson-01", "mode": "guided_practice"})
    with repository._connect() as c:
        # Returning to the old pin here is only a disposable test fixture.
        c.execute("update course_enrolments set course_version_id=%s where student_id=%s", (previous["id"], learner))
    with repository._connect() as c:
        blocked, _ = preview_transition(c, learner, "g3-sec1-math", target["revision"])
    assert not blocked["allowed"]
    assert blocked["active_sessions"] == 1
    with pytest.raises(BetaOperationsError, match="Finish active"):
        migrate(repository, actor, learner, body, "blocked-test", catalogue)
    with psycopg.connect(url, row_factory=dict_row) as c:
        c.execute("update practice_sessions set status='abandoned', abandoned_at=now() where student_id=%s", (learner,))
        lesson = c.execute("select * from lesson_versions where is_current limit 1").fetchone()
        old = c.execute("""insert into lesson_versions(lesson_id,revision,schema_version,title,summary,
            objectives,mastery_policy_key,estimated_minutes,status,content_sha256,provenance,is_current,authored_at)
            values(%s,99,'1.0','Changed lesson','Test','["Test objective"]','n1-default-v1',10,'draft',%s,'{}',false,now())
            on conflict (lesson_id,revision) do update set is_current=false returning id""",
            (lesson["lesson_id"], "a"*64)).fetchone()
        c.execute("insert into learner_lesson_progress(student_id,lesson_id,lesson_version_id) values(%s,%s,%s)",
            (learner, lesson["lesson_id"], old["id"]))
    with repository._connect() as c:
        blocked, _ = preview_transition(c, learner, "g3-sec1-math", target["revision"])
    assert blocked["incompatible_lessons"]
    assert not blocked["allowed"]
