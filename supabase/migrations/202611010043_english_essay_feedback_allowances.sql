begin;

create table english_essay_feedback_monthly_usage (
    student_id uuid not null references auth.users(id) on delete cascade,
    usage_month date not null check (extract(day from usage_month) = 1),
    reserved_feedback integer not null default 0 check (reserved_feedback >= 0),
    committed_feedback integer not null default 0 check (committed_feedback >= 0),
    released_feedback integer not null default 0 check (released_feedback >= 0),
    reserved_cost_micros_sgd bigint not null default 0 check (reserved_cost_micros_sgd >= 0),
    actual_cost_micros_sgd bigint not null default 0 check (actual_cost_micros_sgd >= 0),
    updated_at timestamptz not null default now(),
    primary key (student_id, usage_month)
);

create table english_essay_feedback_academy_monthly_usage (
    usage_month date primary key check (extract(day from usage_month) = 1),
    reserved_cost_micros_sgd bigint not null default 0 check (reserved_cost_micros_sgd >= 0),
    actual_cost_micros_sgd bigint not null default 0 check (actual_cost_micros_sgd >= 0),
    updated_at timestamptz not null default now()
);

create table english_essay_feedback_reservations (
    id uuid primary key,
    student_id uuid not null references auth.users(id) on delete cascade,
    submission_id uuid not null references english_essay_submissions(id) on delete restrict,
    usage_month date not null check (extract(day from usage_month) = 1),
    status text not null default 'reserved' check (
        status in ('reserved', 'committed', 'released')
    ),
    policy_version text not null check (length(btrim(policy_version)) between 1 and 100),
    provider_name text not null check (length(btrim(provider_name)) between 1 and 100),
    model_name text not null check (length(btrim(model_name)) between 1 and 200),
    reserved_cost_micros_sgd bigint not null check (reserved_cost_micros_sgd > 0),
    actual_cost_micros_sgd bigint check (
        actual_cost_micros_sgd is null or actual_cost_micros_sgd >= 0
    ),
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    check ((status = 'reserved') = (completed_at is null)),
    check (
        (status = 'committed' and actual_cost_micros_sgd is not null)
        or (status <> 'committed' and actual_cost_micros_sgd is null)
    )
);

create unique index english_essay_feedback_one_active_student_idx
    on english_essay_feedback_reservations(student_id) where status = 'reserved';
create unique index english_essay_feedback_one_active_submission_idx
    on english_essay_feedback_reservations(submission_id) where status = 'reserved';
create index english_essay_feedback_reservations_student_created_idx
    on english_essay_feedback_reservations(student_id, created_at desc);

create table english_essay_feedback_reservation_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    reservation_id uuid not null
        references english_essay_feedback_reservations(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

create table english_essay_feedback_usage_events (
    id uuid primary key default gen_random_uuid(),
    reservation_id uuid not null
        references english_essay_feedback_reservations(id) on delete restrict,
    student_id uuid not null references auth.users(id) on delete cascade,
    submission_id uuid not null references english_essay_submissions(id) on delete restrict,
    event_type text not null check (event_type in ('reserved', 'committed', 'released')),
    request_id text not null check (length(btrim(request_id)) between 1 and 200),
    usage jsonb not null check (jsonb_typeof(usage) = 'object'),
    created_at timestamptz not null default now()
);

create index english_essay_feedback_usage_events_student_created_idx
    on english_essay_feedback_usage_events(student_id, created_at desc);

create or replace function validate_english_essay_feedback_reservation()
returns trigger
language plpgsql
as $$
declare
    source_submission english_essay_submissions%rowtype;
begin
    if tg_op = 'INSERT' then
        select * into source_submission
          from english_essay_submissions
         where id = new.submission_id;
        if not found or source_submission.student_id <> new.student_id then
            raise exception 'Essay feedback reservation must use an owned submission';
        end if;
        if not exists (
            select 1 from english_essay_self_reviews reviews
             where reviews.student_id = new.student_id
               and reviews.submission_id = new.submission_id
        ) then
            raise exception 'Essay feedback reservation requires a completed learner self-review';
        end if;
    elsif row(old.student_id, old.submission_id, old.usage_month,
              old.policy_version, old.provider_name, old.model_name,
              old.reserved_cost_micros_sgd, old.created_at)
          is distinct from
          row(new.student_id, new.submission_id, new.usage_month,
              new.policy_version, new.provider_name, new.model_name,
              new.reserved_cost_micros_sgd, new.created_at) then
        raise exception 'Essay feedback reservation identity is immutable';
    elsif old.status <> new.status and not (
        old.status = 'reserved' and new.status in ('committed', 'released')
    ) then
        raise exception 'Essay feedback reservation has an invalid state transition';
    end if;
    return new;
end;
$$;

create or replace function protect_english_essay_feedback_usage_event()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE'
       and current_setting('app.account_deletion_target', true) = old.student_id::text then
        return old;
    end if;
    raise exception 'Essay feedback usage events are append-only';
end;
$$;

create trigger english_essay_feedback_reservation_is_valid
before insert or update on english_essay_feedback_reservations
for each row execute function validate_english_essay_feedback_reservation();

create trigger english_essay_feedback_usage_event_is_immutable
before update or delete on english_essay_feedback_usage_events
for each row execute function protect_english_essay_feedback_usage_event();

alter table english_essay_feedback_monthly_usage enable row level security;
alter table english_essay_feedback_academy_monthly_usage enable row level security;
alter table english_essay_feedback_reservations enable row level security;
alter table english_essay_feedback_reservation_idempotency_keys enable row level security;
alter table english_essay_feedback_usage_events enable row level security;

create policy english_essay_feedback_monthly_usage_owner_read
on english_essay_feedback_monthly_usage for select using (student_id = auth.uid());
create policy english_essay_feedback_reservations_owner_read
on english_essay_feedback_reservations for select using (student_id = auth.uid());
create policy english_essay_feedback_reservation_keys_owner_read
on english_essay_feedback_reservation_idempotency_keys for select
using (student_id = auth.uid());
create policy english_essay_feedback_usage_events_owner_read
on english_essay_feedback_usage_events for select using (student_id = auth.uid());

revoke all on english_essay_feedback_monthly_usage,
    english_essay_feedback_academy_monthly_usage,
    english_essay_feedback_reservations,
    english_essay_feedback_reservation_idempotency_keys,
    english_essay_feedback_usage_events from anon, authenticated;
grant select on english_essay_feedback_monthly_usage,
    english_essay_feedback_reservations,
    english_essay_feedback_reservation_idempotency_keys,
    english_essay_feedback_usage_events to authenticated;
grant all on english_essay_feedback_monthly_usage,
    english_essay_feedback_academy_monthly_usage,
    english_essay_feedback_reservations,
    english_essay_feedback_reservation_idempotency_keys,
    english_essay_feedback_usage_events to service_role;

comment on table english_essay_feedback_reservations is
    'Atomic pre-provider reservations enforcing finite learner feedback and academy cost ceilings.';
comment on table english_essay_feedback_usage_events is
    'Append-only reservation, commit and release audit evidence without essay or provider content.';
comment on table english_essay_feedback_academy_monthly_usage is
    'Server-only aggregate cost circuit breaker; learner APIs never expose provider cost or token data.';

commit;
