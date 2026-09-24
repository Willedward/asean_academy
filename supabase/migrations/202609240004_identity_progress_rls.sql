begin;

create type academy_user_role as enum ('student', 'content_admin', 'academic_admin');
create type course_enrolment_status as enum ('active', 'completed', 'withdrawn');
create type lesson_progress_state as enum (
    'in_progress', 'practice_completed', 'proficient', 'mastered'
);
create type mastery_event_type as enum (
    'lesson_proficient', 'checkpoint_passed', 'lesson_mastered'
);

create table profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    role academy_user_role not null default 'student',
    display_name text,
    target_track text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (display_name is null or length(btrim(display_name)) between 1 and 80),
    check (target_track is null or length(btrim(target_track)) between 1 and 80)
);

create table beta_invitations (
    id uuid primary key default gen_random_uuid(),
    token_sha256 text not null unique check (token_sha256 ~ '^[0-9a-f]{64}$'),
    email text not null,
    course_version_id uuid not null references course_versions(id) on delete restrict,
    max_uses smallint not null default 1 check (max_uses between 1 and 100),
    use_count smallint not null default 0 check (use_count between 0 and max_uses),
    expires_at timestamptz not null,
    revoked_at timestamptz,
    created_by uuid references auth.users(id) on delete set null,
    created_at timestamptz not null default now(),
    check (length(btrim(email)) > 3)
);

create table course_enrolments (
    student_id uuid not null references auth.users(id) on delete cascade,
    course_id uuid not null references courses(id) on delete restrict,
    course_version_id uuid not null references course_versions(id) on delete restrict,
    accepted_invitation_id uuid references beta_invitations(id) on delete set null,
    status course_enrolment_status not null default 'active',
    enrolled_at timestamptz not null default now(),
    completed_at timestamptz,
    primary key (student_id, course_id),
    check ((status = 'completed') = (completed_at is not null))
);

create table learner_lesson_progress (
    student_id uuid not null references auth.users(id) on delete cascade,
    lesson_id uuid not null references course_lessons(id) on delete restrict,
    lesson_version_id uuid not null references lesson_versions(id) on delete restrict,
    state lesson_progress_state not null default 'in_progress',
    question_count smallint not null default 0 check (question_count >= 0),
    resolved_count smallint not null default 0 check (resolved_count >= 0),
    correct_count smallint not null default 0 check (correct_count >= 0),
    gave_up_count smallint not null default 0 check (gave_up_count >= 0),
    eventual_correct_percentage numeric(5,2) not null default 0 check (
        eventual_correct_percentage between 0 and 100
    ),
    checkpoint_passed boolean not null default false,
    last_practice_session_id uuid references practice_sessions(id) on delete set null,
    started_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz,
    primary key (student_id, lesson_id),
    check (resolved_count <= question_count),
    check (correct_count + gave_up_count <= resolved_count)
);

create table mastery_events (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    lesson_id uuid references course_lessons(id) on delete restrict,
    event_type mastery_event_type not null,
    source_practice_session_id uuid references practice_sessions(id) on delete restrict,
    evidence jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    check (jsonb_typeof(evidence) = 'object'),
    unique (student_id, event_type, source_practice_session_id)
);

create table practice_session_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    practice_session_id uuid not null references practice_sessions(id) on delete cascade,
    request_fingerprint text not null check (request_fingerprint ~ '^[0-9a-f]{64}$'),
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

alter table attempts
    alter column idempotency_key type text using idempotency_key::text;
alter table attempts
    add constraint attempts_idempotency_key_length
    check (length(idempotency_key) between 1 and 200);

alter table session_questions
    drop constraint session_questions_selection_reason_check;
alter table session_questions
    add constraint session_questions_selection_reason_check check (
        selection_reason in (
            'required_retry', 'unseen', 'least_recently_attempted',
            'configured_lesson_pool'
        )
    );

create index course_enrolments_student_status_idx
    on course_enrolments(student_id, status, enrolled_at desc);
create index learner_lesson_progress_student_state_idx
    on learner_lesson_progress(student_id, state, updated_at desc);
create unique index practice_sessions_one_active_lesson_idx
    on practice_sessions(student_id, (scope->>'lesson_key'))
    where status = 'active' and scope ? 'lesson_key';
create index mastery_events_student_created_idx
    on mastery_events(student_id, created_at desc);

create or replace function reject_mastery_event_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'mastery events are immutable';
end;
$$;

create trigger mastery_events_are_immutable
before update or delete on mastery_events
for each row execute function reject_mastery_event_mutation();

alter table profiles enable row level security;
alter table beta_invitations enable row level security;
alter table course_enrolments enable row level security;
alter table learner_lesson_progress enable row level security;
alter table mastery_events enable row level security;
alter table practice_session_idempotency_keys enable row level security;

create policy profiles_owner_read
on profiles for select
using (id = auth.uid());

create policy course_enrolments_owner_read
on course_enrolments for select
using (student_id = auth.uid());

create policy learner_lesson_progress_owner_read
on learner_lesson_progress for select
using (student_id = auth.uid());

create policy mastery_events_owner_read
on mastery_events for select
using (student_id = auth.uid());

create policy practice_session_idempotency_owner_read
on practice_session_idempotency_keys for select
using (student_id = auth.uid());

grant select on profiles to authenticated;
grant select on course_enrolments to authenticated;
grant select on learner_lesson_progress to authenticated;
grant select on mastery_events to authenticated;
grant select on practice_sessions to authenticated;
grant select on session_questions to authenticated;
grant select on attempts to authenticated;
grant select on question_progress to authenticated;
grant select on practice_session_idempotency_keys to authenticated;

comment on table beta_invitations is
    'Server-managed invitation tokens stored only as SHA-256 digests; raw codes are never persisted.';
comment on table course_enrolments is
    'Pins each student to the exact course revision accepted during onboarding.';
comment on table learner_lesson_progress is
    'Derived lesson progress. Mastered requires separate checkpoint evidence.';
comment on table mastery_events is
    'Immutable evidence events supporting proficiency and later checkpoint mastery.';

commit;
