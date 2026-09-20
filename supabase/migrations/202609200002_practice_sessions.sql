begin;

create type practice_session_status as enum ('active', 'completed', 'abandoned');
create type session_question_status as enum ('pending', 'correct', 'gave_up');
create type question_progress_state as enum (
    'unseen', 'attempting', 'correct', 'gave_up', 'queued_for_retry'
);

create table practice_sessions (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    bank_id uuid not null references math_question_banks(id) on delete restrict,
    requested_question_count smallint not null check (requested_question_count between 1 and 40),
    scope jsonb not null default '{}'::jsonb,
    status practice_session_status not null default 'active',
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    abandoned_at timestamptz,
    check (jsonb_typeof(scope) = 'object'),
    check ((status = 'completed') = (completed_at is not null)),
    check ((status = 'abandoned') = (abandoned_at is not null))
);

create table session_questions (
    id uuid primary key default gen_random_uuid(),
    practice_session_id uuid not null references practice_sessions(id) on delete cascade,
    question_version_id uuid not null references math_question_versions(id) on delete restrict,
    position smallint not null check (position > 0),
    status session_question_status not null default 'pending',
    selection_reason text not null check (
        selection_reason in ('required_retry', 'unseen', 'least_recently_attempted')
    ),
    incorrect_attempts smallint not null default 0 check (incorrect_attempts >= 0),
    highest_hint_stage smallint not null default 0 check (highest_hint_stage between 0 and 2),
    assigned_at timestamptz not null default now(),
    resolved_at timestamptz,
    unique (practice_session_id, position),
    unique (practice_session_id, question_version_id),
    check ((status = 'pending') = (resolved_at is null))
);

create table attempts (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    session_question_id uuid not null references session_questions(id) on delete restrict,
    question_version_id uuid not null references math_question_versions(id) on delete restrict,
    attempt_number smallint not null check (attempt_number > 0),
    idempotency_key uuid not null,
    answers jsonb not null,
    result jsonb not null,
    is_correct boolean not null,
    marks_awarded smallint not null check (marks_awarded >= 0),
    submitted_at timestamptz not null default now(),
    unique (session_question_id, attempt_number),
    unique (student_id, idempotency_key),
    check (jsonb_typeof(answers) = 'object'),
    check (jsonb_typeof(result) = 'object')
);

create table question_progress (
    student_id uuid not null references auth.users(id) on delete cascade,
    question_id uuid not null references math_questions(id) on delete cascade,
    latest_question_version_id uuid not null references math_question_versions(id) on delete restrict,
    state question_progress_state not null default 'unseen',
    attempts_total integer not null default 0 check (attempts_total >= 0),
    incorrect_total integer not null default 0 check (incorrect_total >= 0),
    correct_total integer not null default 0 check (correct_total >= 0),
    last_attempted_at timestamptz,
    updated_at timestamptz not null default now(),
    primary key (student_id, question_id)
);

create index practice_sessions_student_status_idx
    on practice_sessions(student_id, status, created_at desc);
create index session_questions_session_status_idx
    on session_questions(practice_session_id, status, position);
create index attempts_student_submitted_idx
    on attempts(student_id, submitted_at desc);
create index question_progress_selection_idx
    on question_progress(student_id, state, last_attempted_at);

create or replace function reject_attempt_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'attempts are immutable';
end;
$$;

create trigger attempts_are_immutable
before update or delete on attempts
for each row execute function reject_attempt_mutation();

alter table practice_sessions enable row level security;
alter table session_questions enable row level security;
alter table attempts enable row level security;
alter table question_progress enable row level security;

create policy practice_sessions_owner_read
on practice_sessions for select
using (student_id = auth.uid());

create policy session_questions_owner_read
on session_questions for select
using (
    exists (
        select 1 from practice_sessions
        where practice_sessions.id = session_questions.practice_session_id
          and practice_sessions.student_id = auth.uid()
    )
);

create policy attempts_owner_read
on attempts for select
using (student_id = auth.uid());

create policy question_progress_owner_read
on question_progress for select
using (student_id = auth.uid());

comment on table practice_sessions is
    'One authenticated student practice visit and its immutable bank/scope target.';
comment on table session_questions is
    'Persisted question order. question_version_id pins the exact assessed revision.';
comment on table attempts is
    'Immutable answer submissions. result must never contain private canonical answer data.';
comment on table question_progress is
    'Derived selection state used to prioritize retries, unseen work and recency.';

commit;
