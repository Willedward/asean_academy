begin;

alter type beta_audit_event_type add value if not exists 'role_changed';

alter table profiles add column email text;

update profiles
set email = lower(btrim(users.email))
from auth.users users
where users.id = profiles.id;

alter table profiles
    alter column email set not null,
    add constraint profiles_email_normalized_check check (
        email = lower(btrim(email))
        and length(email) between 5 and 320
        and email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'
    );

create unique index profiles_email_lower_idx on profiles(lower(email));
create index profiles_role_created_idx on profiles(role, created_at desc);
create index attempts_question_correct_submitted_idx
    on attempts(question_version_id, is_correct, submitted_at desc);
create index session_questions_question_status_idx
    on session_questions(question_version_id, status);
create index practice_sessions_created_status_idx
    on practice_sessions(created_at desc, status);
create index learner_lesson_progress_state_updated_idx
    on learner_lesson_progress(state, updated_at desc);

comment on column profiles.email is
    'Normalized verified email copied from the authenticated identity for server-side administration. Never expose this column through public browser database grants.';

commit;
