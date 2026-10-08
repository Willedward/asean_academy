begin;

create table tutor_route_decisions (
    id uuid primary key default gen_random_uuid(),
    reservation_id uuid not null unique
        references tutor_usage_reservations(id) on delete cascade,
    tutor_session_id uuid not null references tutor_sessions(id) on delete cascade,
    student_id uuid not null references auth.users(id) on delete cascade,
    request_id text not null unique,
    policy_version text not null,
    tutor_mode tutor_mode not null,
    question_difficulty smallint not null check (question_difficulty between 1 and 5),
    route_score smallint not null check (route_score >= 0),
    selected_tier text not null check (selected_tier in ('economy', 'premium')),
    provider_name text not null,
    model_name text not null,
    reason_codes text[] not null,
    estimated_input_tokens integer not null check (estimated_input_tokens > 0),
    max_output_tokens integer not null check (max_output_tokens > 0),
    reserved_cost_micros_sgd bigint not null check (reserved_cost_micros_sgd > 0),
    created_at timestamptz not null default now(),
    check (length(btrim(request_id)) between 1 and 200),
    check (length(btrim(policy_version)) between 1 and 100),
    check (length(btrim(provider_name)) between 1 and 100),
    check (length(btrim(model_name)) between 1 and 100),
    check (cardinality(reason_codes) between 1 and 20)
);

create index tutor_route_decisions_student_created_idx
    on tutor_route_decisions(student_id, created_at desc);
create index tutor_route_decisions_tier_created_idx
    on tutor_route_decisions(selected_tier, created_at desc);

alter table tutor_messages
    add column provider_name text,
    add column model_tier text check (model_tier is null or model_tier in ('economy', 'premium')),
    add column route_decision_id uuid references tutor_route_decisions(id) on delete cascade,
    add check (
        role = 'assistant'
        or (provider_name is null and model_tier is null and route_decision_id is null)
    );

create unique index tutor_messages_route_decision_idx
    on tutor_messages(route_decision_id) where route_decision_id is not null;

create trigger tutor_route_decisions_no_update_or_delete
before update or delete on tutor_route_decisions
for each row execute function reject_tutor_usage_event_mutation();

alter table tutor_route_decisions enable row level security;

create policy tutor_route_decisions_owner_read on tutor_route_decisions for select
using (student_id = auth.uid());

revoke all on tutor_route_decisions from anon, authenticated;
grant select on tutor_route_decisions to authenticated;
grant all on tutor_route_decisions to service_role;

comment on table tutor_route_decisions is
    'Append-only deterministic model selection evidence without prompt or answer content.';
comment on column tutor_route_decisions.reason_codes is
    'Bounded machine-readable reasons produced by the versioned server routing policy.';

commit;
