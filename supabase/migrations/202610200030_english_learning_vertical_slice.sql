begin;

create type english_practice_mode as enum ('guided_practice', 'retry_review');
create type english_practice_session_status as enum ('active', 'completed');
create type english_session_question_status as enum ('pending', 'correct', 'incorrect');
create type english_lesson_progress_state as enum (
    'in_progress', 'practice_completed', 'proficient'
);
create type english_error_category as enum (
    'unknown_meaning', 'missed_clue', 'option_trap', 'tone_mismatch'
);
create type english_retry_state as enum ('queued', 'resolved');

create table english_practice_sessions (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    lesson_key text not null,
    lesson_revision integer not null check (lesson_revision > 0),
    mode english_practice_mode not null,
    requested_question_count smallint not null check (
        requested_question_count between 1 and 40
    ),
    status english_practice_session_status not null default 'active',
    development_drafts boolean not null default false,
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    check (lesson_key ~ '^e[0-9]+-lesson-[0-9]{2}$'),
    check ((status = 'completed') = (completed_at is not null))
);

create table english_session_questions (
    id uuid primary key default gen_random_uuid(),
    practice_session_id uuid not null references english_practice_sessions(id) on delete cascade,
    question_version_id uuid not null references english_objective_question_versions(id) on delete restrict,
    position smallint not null check (position > 0),
    status english_session_question_status not null default 'pending',
    assigned_at timestamptz not null default now(),
    resolved_at timestamptz,
    unique (practice_session_id, position),
    unique (practice_session_id, question_version_id),
    check ((status = 'pending') = (resolved_at is null))
);

create table english_practice_session_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    practice_session_id uuid not null references english_practice_sessions(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

create table english_objective_attempts (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    session_question_id uuid not null references english_session_questions(id) on delete restrict,
    attempt_number smallint not null check (attempt_number > 0),
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    answers jsonb not null,
    result jsonb not null,
    is_correct boolean not null,
    submitted_at timestamptz not null default now(),
    unique (student_id, idempotency_key),
    unique (session_question_id),
    check (jsonb_typeof(answers) = 'object'),
    check (jsonb_typeof(result) = 'object')
);

create table english_error_classifications (
    attempt_id uuid primary key references english_objective_attempts(id) on delete restrict,
    student_id uuid not null references auth.users(id) on delete cascade,
    category english_error_category not null,
    recorded_at timestamptz not null default now()
);

create table english_retry_queue (
    student_id uuid not null references auth.users(id) on delete cascade,
    question_id uuid not null references english_objective_questions(id) on delete restrict,
    lesson_key text not null,
    source_attempt_id uuid not null references english_objective_attempts(id) on delete restrict,
    due_at timestamptz not null,
    state english_retry_state not null default 'queued',
    queued_at timestamptz not null default now(),
    resolved_at timestamptz,
    primary key (student_id, question_id),
    check (lesson_key ~ '^e[0-9]+-lesson-[0-9]{2}$'),
    check ((state = 'resolved') = (resolved_at is not null))
);

create table english_lesson_progress (
    student_id uuid not null references auth.users(id) on delete cascade,
    lesson_key text not null,
    lesson_revision integer not null check (lesson_revision > 0),
    state english_lesson_progress_state not null default 'in_progress',
    question_count smallint not null default 0 check (question_count >= 0),
    resolved_count smallint not null default 0 check (resolved_count >= 0),
    correct_count smallint not null default 0 check (correct_count >= 0),
    incorrect_count smallint not null default 0 check (incorrect_count >= 0),
    last_practice_session_id uuid references english_practice_sessions(id) on delete set null,
    started_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz,
    primary key (student_id, lesson_key),
    check (lesson_key ~ '^e[0-9]+-lesson-[0-9]{2}$'),
    check (resolved_count <= question_count),
    check (correct_count + incorrect_count <= resolved_count)
);

create unique index english_practice_one_active_lesson_mode_idx
    on english_practice_sessions(student_id, lesson_key, mode)
    where status = 'active';
create index english_practice_sessions_student_idx
    on english_practice_sessions(student_id, created_at desc);
create index english_session_questions_pending_idx
    on english_session_questions(practice_session_id, status, position);
create index english_attempts_student_idx
    on english_objective_attempts(student_id, submitted_at desc);
create index english_retry_due_idx
    on english_retry_queue(student_id, state, due_at);
create index english_lesson_progress_student_idx
    on english_lesson_progress(student_id, updated_at desc);

create or replace function reject_english_learning_evidence_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'English learning evidence is immutable';
end;
$$;

create trigger english_objective_attempts_are_immutable
before update or delete on english_objective_attempts
for each row execute function reject_english_learning_evidence_mutation();

create trigger english_error_classifications_are_immutable
before update or delete on english_error_classifications
for each row execute function reject_english_learning_evidence_mutation();

alter table english_practice_sessions enable row level security;
alter table english_session_questions enable row level security;
alter table english_practice_session_idempotency_keys enable row level security;
alter table english_objective_attempts enable row level security;
alter table english_error_classifications enable row level security;
alter table english_retry_queue enable row level security;
alter table english_lesson_progress enable row level security;

create policy english_practice_sessions_owner_read
on english_practice_sessions for select using (student_id = auth.uid());

create policy english_session_questions_owner_read
on english_session_questions for select using (
    exists (
        select 1 from english_practice_sessions sessions
        where sessions.id = english_session_questions.practice_session_id
          and sessions.student_id = auth.uid()
    )
);

create policy english_practice_idempotency_owner_read
on english_practice_session_idempotency_keys for select
using (student_id = auth.uid());

create policy english_attempts_owner_read
on english_objective_attempts for select using (student_id = auth.uid());

create policy english_error_classifications_owner_read
on english_error_classifications for select using (student_id = auth.uid());

create policy english_retry_queue_owner_read
on english_retry_queue for select using (student_id = auth.uid());

create policy english_lesson_progress_owner_read
on english_lesson_progress for select using (student_id = auth.uid());

grant select on english_practice_sessions to authenticated;
grant select on english_session_questions to authenticated;
grant select on english_practice_session_idempotency_keys to authenticated;
grant select on english_objective_attempts to authenticated;
grant select on english_error_classifications to authenticated;
grant select on english_retry_queue to authenticated;
grant select on english_lesson_progress to authenticated;

comment on table english_objective_attempts is
    'Immutable deterministic English responses. Results exclude private answer keys.';
comment on table english_retry_queue is
    'Failed English exit tickets queued for an owned retry session.';
comment on table english_error_classifications is
    'One immutable learner reflection category for an incorrect English attempt.';

commit;
