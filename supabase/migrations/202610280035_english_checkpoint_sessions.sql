begin;

create table english_checkpoint_sessions (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    exam_profile_key text not null check (
        exam_profile_key ~ '^asean-english-[a-z0-9-]+-v[0-9]+$'
    ),
    form_key text not null check (
        form_key ~ '^english-checkpoint-[a-z0-9-]+-v[0-9]+$'
    ),
    form_revision integer not null check (form_revision > 0),
    module_code text not null check (module_code ~ '^E(0|[1-9][0-9]*)$'),
    mastery_lesson_keys text[] not null check (cardinality(mastery_lesson_keys) > 0),
    requested_question_count smallint not null check (
        requested_question_count between 1 and 40
    ),
    status english_practice_session_status not null default 'active',
    score numeric(6,5) check (score between 0 and 1),
    passed boolean,
    development_drafts boolean not null default false,
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    check (
        (status = 'active' and completed_at is null and score is null and passed is null)
        or
        (status = 'completed' and completed_at is not null and score is not null and passed is not null)
    )
);

create table english_checkpoint_session_questions (
    id uuid primary key default gen_random_uuid(),
    checkpoint_session_id uuid not null
        references english_checkpoint_sessions(id) on delete cascade,
    question_version_id uuid not null
        references english_objective_question_versions(id) on delete restrict,
    position smallint not null check (position > 0),
    status english_session_question_status not null default 'pending',
    correct_parts smallint not null default 0 check (correct_parts >= 0),
    total_parts smallint not null default 0 check (total_parts >= 0),
    assigned_at timestamptz not null default now(),
    resolved_at timestamptz,
    unique (checkpoint_session_id, position),
    unique (checkpoint_session_id, question_version_id),
    check (correct_parts <= total_parts),
    check ((status = 'pending') = (resolved_at is null))
);

create table english_checkpoint_session_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    checkpoint_session_id uuid not null
        references english_checkpoint_sessions(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

create table english_checkpoint_attempts (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    checkpoint_session_question_id uuid not null
        references english_checkpoint_session_questions(id) on delete restrict,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    answers jsonb not null,
    correct_parts smallint not null check (correct_parts >= 0),
    total_parts smallint not null check (total_parts > 0),
    submitted_at timestamptz not null default now(),
    unique (student_id, idempotency_key),
    unique (checkpoint_session_question_id),
    check (jsonb_typeof(answers) = 'object'),
    check (correct_parts <= total_parts)
);

create unique index english_checkpoint_one_active_module_idx
    on english_checkpoint_sessions(student_id, module_code)
    where status = 'active';
create index english_checkpoint_sessions_student_idx
    on english_checkpoint_sessions(student_id, created_at desc);
create index english_checkpoint_questions_pending_idx
    on english_checkpoint_session_questions(checkpoint_session_id, status, position);

create trigger english_checkpoint_attempts_are_immutable
before update or delete on english_checkpoint_attempts
for each row execute function reject_english_learning_evidence_mutation();

alter table english_checkpoint_sessions enable row level security;
alter table english_checkpoint_session_questions enable row level security;
alter table english_checkpoint_session_idempotency_keys enable row level security;
alter table english_checkpoint_attempts enable row level security;

create policy english_checkpoint_sessions_owner_read
on english_checkpoint_sessions for select using (student_id = auth.uid());

create policy english_checkpoint_questions_owner_read
on english_checkpoint_session_questions for select using (
    exists (
        select 1 from english_checkpoint_sessions sessions
        where sessions.id = english_checkpoint_session_questions.checkpoint_session_id
          and sessions.student_id = auth.uid()
    )
);

create policy english_checkpoint_idempotency_owner_read
on english_checkpoint_session_idempotency_keys for select
using (student_id = auth.uid());

create policy english_checkpoint_attempts_owner_read
on english_checkpoint_attempts for select using (student_id = auth.uid());

grant select on english_checkpoint_sessions to authenticated;
grant select on english_checkpoint_session_questions to authenticated;
grant select on english_checkpoint_session_idempotency_keys to authenticated;
grant select on english_checkpoint_attempts to authenticated;

comment on table english_checkpoint_sessions is
    'Protected module-checkpoint sessions pinning form revision and mastery scope.';
comment on table english_checkpoint_attempts is
    'Immutable deterministic checkpoint evidence; learner feedback remains withheld until form completion.';

commit;
