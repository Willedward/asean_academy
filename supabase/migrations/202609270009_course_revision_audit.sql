begin;

alter type beta_audit_event_type add value if not exists 'course_revision_changed';

-- All enrolment changes and new practice sessions take this same learner lock.
-- No student data or existing content revision is rewritten by this migration.
comment on column course_enrolments.course_version_id is
    'Explicit curriculum pin. Administrator migrations compare the expected source revision, reject active sessions and incompatible progress, and append an audit event.';

commit;
