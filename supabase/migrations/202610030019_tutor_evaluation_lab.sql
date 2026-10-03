begin;

alter type beta_audit_event_type add value if not exists 'tutor_evaluation_run_created';
alter type beta_audit_event_type add value if not exists 'tutor_evaluation_review_recorded';

create table tutor_evaluation_runs (
    id uuid primary key default gen_random_uuid(),
    suite_id text not null,
    suite_version text not null,
    case_id text not null,
    case_snapshot jsonb not null,
    provider text not null check (provider in ('synthetic', 'gemini')),
    model_name text,
    prompt_version text not null,
    automated_pass boolean not null,
    latency_ms integer not null check (latency_ms >= 0),
    input_tokens integer not null check (input_tokens >= 0),
    output_tokens integer not null check (output_tokens >= 0),
    cost_micros_sgd bigint not null check (cost_micros_sgd >= 0),
    response_blocks jsonb not null,
    suggested_replies jsonb not null,
    recommended_next_action text,
    automated_checks jsonb not null,
    provider_error text,
    created_by uuid not null references profiles(id) on delete restrict,
    request_id text not null,
    created_at timestamptz not null default now()
);

create index tutor_evaluation_runs_case_created_idx
    on tutor_evaluation_runs (case_id, created_at desc);

create table tutor_evaluation_reviews (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references tutor_evaluation_runs(id) on delete restrict,
    dimension text not null check (dimension in ('mathematics', 'editorial')),
    decision text not null check (decision in ('approved', 'changes_requested')),
    mathematics_correctness smallint check (mathematics_correctness between 1 and 5),
    pedagogical_quality smallint check (pedagogical_quality between 1 and 5),
    curriculum_fit smallint check (curriculum_fit between 1 and 5),
    safety_and_leakage smallint check (safety_and_leakage between 1 and 5),
    notes text not null check (length(btrim(notes)) between 10 and 2000),
    reviewer_id uuid not null references profiles(id) on delete restrict,
    request_id text not null,
    created_at timestamptz not null default now()
);

create index tutor_evaluation_reviews_run_dimension_created_idx
    on tutor_evaluation_reviews (run_id, dimension, created_at desc);

create function reject_tutor_evaluation_mutation()
returns trigger language plpgsql as $$
begin
    raise exception 'tutor evaluation runs and reviews are append-only';
end;
$$;

create trigger tutor_evaluation_runs_append_only
before update or delete on tutor_evaluation_runs
for each row execute function reject_tutor_evaluation_mutation();

create trigger tutor_evaluation_reviews_append_only
before update or delete on tutor_evaluation_reviews
for each row execute function reject_tutor_evaluation_mutation();

alter table tutor_evaluation_runs enable row level security;
alter table tutor_evaluation_reviews enable row level security;
revoke all on tutor_evaluation_runs from anon, authenticated;
revoke all on tutor_evaluation_reviews from anon, authenticated;
grant all on tutor_evaluation_runs to service_role;
grant all on tutor_evaluation_reviews to service_role;

commit;
