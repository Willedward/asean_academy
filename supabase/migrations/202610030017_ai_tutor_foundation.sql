begin;

create type tutor_session_status as enum ('active', 'closed');
create type tutor_message_role as enum ('student', 'assistant');
create type tutor_mode as enum (
    'clarify_question',
    'diagnose_misconception',
    'socratic_prompt',
    'alternative_explanation',
    'analogous_example',
    'solution_explanation',
    'lesson_recommendation'
);
create type tutor_reservation_status as enum ('reserved', 'reconciled', 'released');
create type tutor_usage_event_type as enum ('reserved', 'reconciled', 'released');

create table tutor_sessions (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    lesson_version_id uuid not null references lesson_versions(id) on delete restrict,
    session_question_id uuid not null references session_questions(id) on delete restrict,
    status tutor_session_status not null default 'active',
    answer_lock_state jsonb not null,
    model_policy_version text not null,
    created_at timestamptz not null default now(),
    closed_at timestamptz,
    check (jsonb_typeof(answer_lock_state) = 'object'),
    check (answer_lock_state ?& array['answer_locked', 'solution_locked']),
    check (jsonb_typeof(answer_lock_state->'answer_locked') = 'boolean'),
    check (jsonb_typeof(answer_lock_state->'solution_locked') = 'boolean'),
    check (length(btrim(model_policy_version)) between 1 and 100),
    check ((status = 'closed') = (closed_at is not null))
);

create unique index tutor_sessions_one_active_question_idx
    on tutor_sessions(student_id, session_question_id) where status = 'active';
create index tutor_sessions_student_created_idx
    on tutor_sessions(student_id, created_at desc);

create table tutor_messages (
    id uuid primary key default gen_random_uuid(),
    tutor_session_id uuid not null references tutor_sessions(id) on delete cascade,
    student_id uuid not null references auth.users(id) on delete cascade,
    role tutor_message_role not null,
    mode tutor_mode,
    content jsonb not null,
    grounding_revision_ids uuid[] not null default '{}',
    model_name text,
    prompt_version text,
    safety_outcome text not null check (
        safety_outcome in ('accepted', 'answer_leakage_blocked', 'provider_fallback')
    ),
    latency_ms integer check (latency_ms is null or latency_ms >= 0),
    token_usage jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    check (jsonb_typeof(content) = 'object'),
    check (content ? 'blocks'),
    check (jsonb_typeof(content->'blocks') = 'array'),
    check (jsonb_typeof(token_usage) = 'object'),
    check (
        (role = 'student' and mode is null and model_name is null and prompt_version is null)
        or
        (role = 'assistant' and mode is not null and model_name is not null and prompt_version is not null)
    )
);

create index tutor_messages_session_created_idx
    on tutor_messages(tutor_session_id, created_at, id);

create table tutor_usage_daily (
    student_id uuid not null references auth.users(id) on delete cascade,
    usage_date date not null,
    reserved_requests integer not null default 0 check (reserved_requests >= 0),
    actual_requests integer not null default 0 check (actual_requests >= 0),
    failed_requests integer not null default 0 check (failed_requests >= 0),
    reserved_tokens bigint not null default 0 check (reserved_tokens >= 0),
    actual_input_tokens bigint not null default 0 check (actual_input_tokens >= 0),
    actual_output_tokens bigint not null default 0 check (actual_output_tokens >= 0),
    actual_tokens bigint not null default 0 check (actual_tokens >= 0),
    updated_at timestamptz not null default now(),
    primary key (student_id, usage_date),
    check (actual_tokens = actual_input_tokens + actual_output_tokens)
);

create table tutor_usage_monthly (
    student_id uuid not null references auth.users(id) on delete cascade,
    usage_month date not null check (extract(day from usage_month) = 1),
    reserved_cost_micros_sgd bigint not null default 0 check (reserved_cost_micros_sgd >= 0),
    actual_cost_micros_sgd bigint not null default 0 check (actual_cost_micros_sgd >= 0),
    updated_at timestamptz not null default now(),
    primary key (student_id, usage_month)
);

create index tutor_usage_monthly_academy_idx
    on tutor_usage_monthly(usage_month);

create table tutor_usage_reservations (
    id uuid primary key,
    tutor_session_id uuid not null references tutor_sessions(id) on delete cascade,
    student_id uuid not null references auth.users(id) on delete cascade,
    usage_date date not null,
    usage_month date not null check (extract(day from usage_month) = 1),
    status tutor_reservation_status not null default 'reserved',
    reserved_tokens bigint not null check (reserved_tokens > 0),
    reserved_cost_micros_sgd bigint not null check (reserved_cost_micros_sgd > 0),
    actual_input_tokens bigint check (actual_input_tokens is null or actual_input_tokens >= 0),
    actual_output_tokens bigint check (actual_output_tokens is null or actual_output_tokens >= 0),
    actual_cost_micros_sgd bigint check (
        actual_cost_micros_sgd is null or actual_cost_micros_sgd >= 0
    ),
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    check ((status = 'reserved') = (completed_at is null))
);

create unique index tutor_usage_one_generation_per_student_idx
    on tutor_usage_reservations(student_id) where status = 'reserved';
create index tutor_usage_reservations_session_idx
    on tutor_usage_reservations(tutor_session_id, created_at desc);

create table tutor_usage_events (
    id uuid primary key default gen_random_uuid(),
    reservation_id uuid not null references tutor_usage_reservations(id) on delete restrict,
    student_id uuid not null references auth.users(id) on delete cascade,
    tutor_session_id uuid not null references tutor_sessions(id) on delete cascade,
    event_type tutor_usage_event_type not null,
    request_id text not null,
    usage jsonb not null,
    created_at timestamptz not null default now(),
    check (length(btrim(request_id)) between 1 and 200),
    check (jsonb_typeof(usage) = 'object')
);

create index tutor_usage_events_student_created_idx
    on tutor_usage_events(student_id, created_at desc);

create function reject_tutor_message_mutation()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'tutor messages and usage events are append-only';
end;
$$;

create function reject_tutor_usage_event_mutation()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'tutor messages and usage events are append-only';
end;
$$;

create trigger tutor_messages_no_update_or_delete
before update or delete on tutor_messages
for each row execute function reject_tutor_message_mutation();

create trigger tutor_usage_events_no_update_or_delete
before update or delete on tutor_usage_events
for each row execute function reject_tutor_usage_event_mutation();

alter table tutor_sessions enable row level security;
alter table tutor_messages enable row level security;
alter table tutor_usage_daily enable row level security;
alter table tutor_usage_monthly enable row level security;
alter table tutor_usage_reservations enable row level security;
alter table tutor_usage_events enable row level security;

create policy tutor_sessions_owner_read on tutor_sessions for select
using (student_id = auth.uid());
create policy tutor_messages_owner_read on tutor_messages for select
using (student_id = auth.uid());
create policy tutor_usage_daily_owner_read on tutor_usage_daily for select
using (student_id = auth.uid());
create policy tutor_usage_monthly_owner_read on tutor_usage_monthly for select
using (student_id = auth.uid());
create policy tutor_usage_reservations_owner_read on tutor_usage_reservations for select
using (student_id = auth.uid());
create policy tutor_usage_events_owner_read on tutor_usage_events for select
using (student_id = auth.uid());

revoke all on tutor_sessions, tutor_messages, tutor_usage_daily, tutor_usage_monthly,
    tutor_usage_reservations, tutor_usage_events from anon, authenticated;
grant select on tutor_sessions, tutor_messages, tutor_usage_daily, tutor_usage_monthly,
    tutor_usage_reservations, tutor_usage_events to authenticated;
grant all on tutor_sessions, tutor_messages, tutor_usage_daily, tutor_usage_monthly,
    tutor_usage_reservations, tutor_usage_events to service_role;

comment on table tutor_sessions is
    'Learner-owned tutor conversation pinned to exact lesson and assigned-question revisions.';
comment on table tutor_messages is
    'Append-only structured tutor conversation; raw provider payloads and credentials are excluded.';
comment on table tutor_usage_reservations is
    'Atomic pre-provider reservations enforcing one generation per learner and hard cost limits.';
comment on table tutor_usage_events is
    'Append-only reservation and reconciliation audit ledger without prompt or answer content.';

commit;
