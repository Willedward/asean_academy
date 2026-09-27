"""Conservative, audited course enrolment transitions; never erase learner evidence."""
from __future__ import annotations

from uuid import UUID

from psycopg.types.json import Jsonb

from .admin_repository import BetaOperationsError
from .content_sync import verify_database_content


def learner_lock(connection, learner_id):
    connection.execute("select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                       (f"curriculum:{learner_id}",))


def preview_transition(connection, learner_id, course_key, target_revision):
    enrolment = connection.execute("""
        select e.course_id, e.course_version_id, e.status::text, v.revision
        from course_enrolments e join courses c on c.id=e.course_id
        join course_versions v on v.id=e.course_version_id
        where e.student_id=%s and c.course_key=%s for update of e
    """, (learner_id, course_key)).fetchone()
    if not enrolment:
        raise BetaOperationsError("enrolment_not_found", "Course enrolment was not found.", 404)
    target = connection.execute("""
        select id, content_sha256 from course_versions where course_id=%s and revision=%s
    """, (enrolment["course_id"], target_revision)).fetchone()
    if not target:
        raise BetaOperationsError("target_not_imported", "Import the target course first.", 409)
    active = connection.execute(
        "select count(*) as total from practice_sessions where student_id=%s and status='active'",
        (learner_id,),
    ).fetchone()["total"]
    incompatible = connection.execute("""
        select distinct l.lesson_key
        from learner_lesson_progress p join course_lessons l on l.id=p.lesson_id
        where p.student_id=%s and not exists (
            select 1 from unit_version_lessons mapping
            join unit_versions unit on unit.id=mapping.unit_version_id
            where unit.course_version_id=%s and mapping.lesson_version_id=p.lesson_version_id
        )
        union
        select distinct l.lesson_key
        from learner_lesson_section_progress p
        join lesson_sections s on s.id=p.lesson_section_id
        join lesson_versions v on v.id=s.lesson_version_id
        join course_lessons l on l.id=v.lesson_id
        where p.student_id=%s and not exists (
            select 1 from unit_version_lessons mapping
            join unit_versions unit on unit.id=mapping.unit_version_id
            where unit.course_version_id=%s and mapping.lesson_version_id=v.id
        )
    """, (learner_id, target["id"], learner_id, target["id"])).fetchall()
    blockers = []
    if enrolment["status"] != "active":
        blockers.append("Only an active enrolment can move.")
    if target_revision <= enrolment["revision"]:
        blockers.append("Choose a newer revision than the current enrolment.")
    if active:
        blockers.append("Finish active practice/checkpoint sessions before moving.")
    if incompatible:
        blockers.append("Progress belongs to changed or removed lessons; evidence migration requires review.")
    return {
        "learner_id": learner_id, "course_key": course_key,
        "from_revision": enrolment["revision"], "target_revision": target_revision,
        "target_hash": target["content_sha256"], "active_sessions": active,
        "incompatible_lessons": sorted(row["lesson_key"] for row in incompatible),
        "blockers": blockers, "allowed": not blockers,
    }, target["id"]


def migrate(repository, administrator, learner_id: UUID, body, request_id, catalogue):
    if body.target_revision != catalogue.report.course.revision or body.course_key != catalogue.report.course.stable_key:
        raise BetaOperationsError("unsupported_target", "Choose the course revision served by this release.", 409)
    verify_database_content(repository.database_url, catalogue)
    with repository._connect() as connection:
        learner_lock(connection, learner_id)
        preview, version_id = preview_transition(connection, learner_id, body.course_key, body.target_revision)
        if body.from_revision != preview["from_revision"] or body.target_hash != preview["target_hash"]:
            raise BetaOperationsError("migration_preview_stale", "Enrolment or target changed. Preview again.", 409)
        if not preview["allowed"]:
            raise BetaOperationsError("curriculum_migration_blocked", " ".join(preview["blockers"]), 409)
        connection.execute("""
            update course_enrolments set course_version_id=%s
            where student_id=%s and course_id=(select course_id from course_versions where id=%s)
        """, (version_id, learner_id, version_id))
        connection.execute("""
            insert into beta_audit_events(event_type, actor_user_id, target_user_id, request_id, metadata)
            values ('course_revision_changed', %s, %s, %s, %s)
        """, (administrator.learner_id, learner_id, request_id, Jsonb({
            "course_key": body.course_key, "from_revision": body.from_revision,
            "target_revision": body.target_revision, "reason": body.reason,
            "target_hash": body.target_hash,
        })))
    return {"migrated": True, "learner_id": learner_id, "course_revision": body.target_revision}
