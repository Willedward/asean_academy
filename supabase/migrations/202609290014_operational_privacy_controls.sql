begin;

alter type beta_audit_event_type add value if not exists 'account_deletion_completed';

create table account_deletion_records (
    id uuid primary key default gen_random_uuid(),
    target_user_id uuid references auth.users(id) on delete set null,
    target_reference text not null check (target_reference ~ '^[0-9a-f]{64}$'),
    email_reference text not null check (email_reference ~ '^[0-9a-f]{64}$'),
    requested_by uuid references auth.users(id) on delete set null,
    reason text not null check (length(btrim(reason)) between 10 and 500),
    preview_counts jsonb not null check (jsonb_typeof(preview_counts) = 'object'),
    request_id text not null check (length(btrim(request_id)) between 1 and 200),
    completed_at timestamptz not null default now()
);

create index account_deletion_records_completed_idx
    on account_deletion_records(completed_at desc);
create index account_deletion_records_target_reference_idx
    on account_deletion_records(target_reference);

alter table account_deletion_records enable row level security;

create or replace function reject_attempt_mutation()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'attempts are immutable';
end;
$$;

create or replace function reject_mastery_event_mutation()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'mastery events are immutable';
end;
$$;

create or replace function reject_diagnostic_result_mutation()
returns trigger language plpgsql as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'diagnostic results are immutable';
end;
$$;

create or replace function reject_diagnostic_reset_mutation()
returns trigger language plpgsql as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'diagnostic reset audit records are immutable';
end;
$$;

create or replace function reject_beta_audit_event_mutation()
returns trigger
language plpgsql
as $$
declare
    target text := current_setting('app.account_deletion_target', true);
begin
    if tg_op = 'UPDATE'
       and target <> ''
       and (
           old.actor_user_id::text = target
           or old.target_user_id::text = target
       )
       and (
           new.actor_user_id is not distinct from old.actor_user_id
           or (old.actor_user_id::text = target and new.actor_user_id is null)
       )
       and (
           new.target_user_id is not distinct from old.target_user_id
           or (old.target_user_id::text = target and new.target_user_id is null)
       )
       and (
           new.actor_user_id is distinct from old.actor_user_id
           or new.target_user_id is distinct from old.target_user_id
       )
       and (to_jsonb(new) - 'actor_user_id' - 'target_user_id')
           = (to_jsonb(old) - 'actor_user_id' - 'target_user_id') then
        return new;
    end if;
    raise exception 'beta audit events are immutable';
end;
$$;

comment on table account_deletion_records is
    'Pseudonymous completion evidence for academic-admin learner deletion. Raw email, answers and profile fields are prohibited.';
comment on column account_deletion_records.preview_counts is
    'Counts confirmed before deletion; values contain no answer payloads or direct identifiers.';

commit;

