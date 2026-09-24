begin;

create type beta_audit_event_type as enum (
    'invitation_created',
    'invitation_revoked',
    'invitation_accepted'
);

create table beta_audit_events (
    id uuid primary key default gen_random_uuid(),
    event_type beta_audit_event_type not null,
    actor_user_id uuid references auth.users(id) on delete set null,
    invitation_id uuid references beta_invitations(id) on delete restrict,
    target_user_id uuid references auth.users(id) on delete set null,
    request_id text not null check (length(btrim(request_id)) between 1 and 200),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    check (jsonb_typeof(metadata) = 'object')
);

create index beta_invitations_created_at_idx
    on beta_invitations(created_at desc);
create index beta_invitations_email_idx
    on beta_invitations(lower(email), created_at desc);
create index beta_audit_events_created_at_idx
    on beta_audit_events(created_at desc);
create index beta_audit_events_invitation_idx
    on beta_audit_events(invitation_id, created_at desc);

create or replace function reject_beta_audit_event_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'beta audit events are immutable';
end;
$$;

create trigger beta_audit_events_are_immutable
before update or delete on beta_audit_events
for each row execute function reject_beta_audit_event_mutation();

alter table beta_audit_events enable row level security;

comment on table beta_audit_events is
    'Append-only server-managed audit events for beta invitations and onboarding. Raw invitation codes are never stored.';
comment on column beta_audit_events.metadata is
    'Operational metadata only. Do not store raw invitation codes, access tokens or student answers.';

commit;
