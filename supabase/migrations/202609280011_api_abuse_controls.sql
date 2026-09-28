begin;

create table api_rate_limit_counters (
    policy_key text not null check (length(policy_key) between 1 and 80),
    subject_hash text not null check (subject_hash ~ '^[0-9a-f]{64}$'),
    window_started_at timestamptz not null,
    request_count integer not null check (request_count > 0),
    updated_at timestamptz not null default now(),
    primary key (policy_key, subject_hash)
);

create table api_security_events (
    id uuid primary key default gen_random_uuid(),
    event_type text not null check (event_type = 'rate_limit_exceeded'),
    policy_key text not null check (length(policy_key) between 1 and 80),
    subject_hash text not null check (subject_hash ~ '^[0-9a-f]{64}$'),
    request_id text not null check (length(request_id) between 1 and 128),
    request_path text not null check (length(request_path) between 1 and 500),
    occurred_at timestamptz not null default now()
);

create index api_security_events_occurred_idx
    on api_security_events(occurred_at desc);
create index api_security_events_policy_occurred_idx
    on api_security_events(policy_key, occurred_at desc);

create or replace function reject_api_security_event_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'API security events are immutable';
end;
$$;

create trigger api_security_events_are_immutable
before update or delete on api_security_events
for each row execute function reject_api_security_event_mutation();

alter table api_rate_limit_counters enable row level security;
alter table api_security_events enable row level security;

comment on table api_rate_limit_counters is
    'Bounded shared counters for sensitive API mutations. Subjects are stored only as HMAC-SHA256 values.';
comment on table api_security_events is
    'Append-only rate-limit rejection evidence. Raw learner IDs, IP addresses, tokens, answers and invitation codes are prohibited.';

commit;
