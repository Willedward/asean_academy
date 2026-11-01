begin;

create table english_essay_provider_feedback_attempts (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    submission_id uuid not null references english_essay_submissions(id) on delete restrict,
    rubric_version_id uuid not null references english_essay_rubric_versions(id) on delete restrict,
    reservation_id uuid not null unique references english_essay_feedback_reservations(id) on delete restrict,
    provider_name text not null check (length(btrim(provider_name)) between 1 and 100),
    model_name text not null check (length(btrim(model_name)) between 1 and 200),
    policy_version text not null check (length(btrim(policy_version)) between 1 and 100),
    schema_version text not null check (schema_version = 'english-essay-provider-feedback-v1'),
    status text not null default 'queued' check (
        status in ('queued', 'processing', 'succeeded', 'permanent_failed')
    ),
    lease_token uuid,
    worker_id text,
    last_error_code text,
    last_error_message text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz,
    check ((status = 'processing') = (lease_token is not null)),
    check ((status in ('succeeded', 'permanent_failed')) = (completed_at is not null))
);

create table english_essay_provider_feedback (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    attempt_id uuid not null unique references english_essay_provider_feedback_attempts(id) on delete restrict,
    submission_id uuid not null unique references english_essay_submissions(id) on delete restrict,
    rubric_version_id uuid not null references english_essay_rubric_versions(id) on delete restrict,
    reservation_id uuid not null unique references english_essay_feedback_reservations(id) on delete restrict,
    schema_version text not null check (schema_version = 'english-essay-provider-feedback-v1'),
    validation_version text not null check (validation_version = 'english-essay-evidence-validation-v1'),
    preparation_estimate text not null check (
        preparation_estimate in ('limited', 'emerging', 'developing', 'secure', 'strong')
    ),
    criterion_feedback jsonb not null check (
        jsonb_typeof(criterion_feedback) = 'array'
        and jsonb_array_length(criterion_feedback) between 3 and 6
    ),
    overall_summary text not null check (length(btrim(overall_summary)) > 0),
    strengths jsonb not null check (
        jsonb_typeof(strengths) = 'array' and jsonb_array_length(strengths) between 1 and 4
    ),
    priorities jsonb not null check (
        jsonb_typeof(priorities) = 'array' and jsonb_array_length(priorities) = 2
    ),
    revision_task text not null check (length(btrim(revision_task)) > 0),
    transfer_goal text not null check (length(btrim(transfer_goal)) > 0),
    learner_disclaimer text not null check (
        learner_disclaimer = 'This is a NextScholar AI preparation estimate based on an instructional rubric. It is not an official ASEAN Scholarship score, result or admission prediction.'
    ),
    created_at timestamptz not null default now()
);

create index english_essay_provider_feedback_attempts_student_created_idx
    on english_essay_provider_feedback_attempts(student_id, created_at desc);
create unique index english_essay_provider_feedback_one_active_submission_idx
    on english_essay_provider_feedback_attempts(submission_id)
    where status in ('queued', 'processing', 'succeeded');

create or replace function validate_english_essay_provider_feedback_attempt()
returns trigger
language plpgsql
as $$
declare
    source_submission english_essay_submissions%rowtype;
    source_reservation english_essay_feedback_reservations%rowtype;
begin
    if tg_op = 'INSERT' then
        select * into source_submission from english_essay_submissions where id = new.submission_id;
        select * into source_reservation from english_essay_feedback_reservations where id = new.reservation_id for update;
        if source_submission.id is null or source_reservation.id is null
           or source_reservation.status <> 'reserved' then
            raise exception 'Essay provider feedback requires an active reservation';
        end if;
        if row(new.student_id, new.submission_id)
           is distinct from row(source_reservation.student_id, source_reservation.submission_id) then
            raise exception 'Essay provider feedback attempt must match its reservation';
        end if;
        if row(new.student_id, new.rubric_version_id)
           is distinct from row(source_submission.student_id, source_submission.rubric_version_id) then
            raise exception 'Essay provider feedback attempt must use the immutable owned submission';
        end if;
        if row(new.provider_name, new.model_name, new.policy_version)
           is distinct from row(source_reservation.provider_name,
                                source_reservation.model_name,
                                source_reservation.policy_version) then
            raise exception 'Essay provider feedback attempt must match reserved provider policy';
        end if;
    elsif row(old.student_id, old.submission_id, old.rubric_version_id,
              old.reservation_id, old.provider_name, old.model_name,
              old.policy_version, old.schema_version, old.created_at)
          is distinct from
          row(new.student_id, new.submission_id, new.rubric_version_id,
              new.reservation_id, new.provider_name, new.model_name,
              new.policy_version, new.schema_version, new.created_at) then
        raise exception 'Essay provider feedback attempt identity is immutable';
    elsif old.status <> new.status and not (
        (old.status = 'queued' and new.status = 'processing')
        or (old.status = 'processing' and new.status in ('succeeded', 'permanent_failed'))
    ) then
        raise exception 'Essay provider feedback attempt has an invalid state transition';
    end if;
    return new;
end;
$$;

create or replace function validate_english_essay_provider_feedback()
returns trigger
language plpgsql
as $$
declare
    source_attempt english_essay_provider_feedback_attempts%rowtype;
    source_submission english_essay_submissions%rowtype;
    source_reservation english_essay_feedback_reservations%rowtype;
    submitted_keys text[];
    rubric_keys text[];
    criterion jsonb;
    span jsonb;
    span_start integer;
    span_end integer;
begin
    select * into source_attempt from english_essay_provider_feedback_attempts
     where id = new.attempt_id for update;
    select * into source_submission from english_essay_submissions
     where id = new.submission_id;
    select * into source_reservation from english_essay_feedback_reservations
     where id = new.reservation_id for update;
    if source_attempt.status <> 'processing' or source_reservation.status <> 'reserved' then
        raise exception 'Essay provider feedback must finalise an active attempt and reservation';
    end if;
    if row(new.student_id, new.submission_id, new.rubric_version_id, new.reservation_id)
       is distinct from row(source_attempt.student_id, source_attempt.submission_id,
                            source_attempt.rubric_version_id, source_attempt.reservation_id) then
        raise exception 'Essay provider feedback must match its attempt snapshot';
    end if;

    select array_agg(value->>'criterion_key' order by value->>'criterion_key')
      into submitted_keys from jsonb_array_elements(new.criterion_feedback);
    select array_agg(value->>'criterion_key' order by value->>'criterion_key')
      into rubric_keys
      from english_essay_rubric_versions versions,
           jsonb_array_elements(versions.criteria) value
     where versions.id = new.rubric_version_id;
    if submitted_keys is distinct from rubric_keys then
        raise exception 'Essay provider feedback must cover every rubric criterion exactly once';
    end if;

    for criterion in select value from jsonb_array_elements(new.criterion_feedback) loop
        if jsonb_typeof(criterion) <> 'object'
           or coalesce(criterion->>'criterion_title', '') = ''
           or coalesce((criterion->>'preparation_level')::integer, 0) not between 1 and 5
           or coalesce(criterion->>'what_works', '') = ''
           or coalesce(criterion->>'next_step', '') = ''
           or jsonb_typeof(criterion->'evidence_spans') <> 'array'
           or jsonb_array_length(criterion->'evidence_spans') = 0 then
            raise exception 'Essay provider criterion feedback is incomplete';
        end if;
        if criterion->>'criterion_title' is distinct from (
            select rubric_criterion->>'title'
              from english_essay_rubric_versions versions,
                   jsonb_array_elements(versions.criteria) rubric_criterion
             where versions.id = new.rubric_version_id
               and rubric_criterion->>'criterion_key' = criterion->>'criterion_key'
        ) then
            raise exception 'Essay provider criterion title must match the pinned rubric';
        end if;
        for span in select value from jsonb_array_elements(criterion->'evidence_spans') loop
            if jsonb_typeof(span) <> 'object'
               or jsonb_typeof(span->'start') <> 'number'
               or jsonb_typeof(span->'end') <> 'number'
               or coalesce(span->>'quote', '') = '' then
                raise exception 'Essay provider evidence span is invalid';
            end if;
            span_start := (span->>'start')::integer;
            span_end := (span->>'end')::integer;
            if span_start < 0 or span_end <= span_start
               or span_end > length(source_submission.body)
               or substring(source_submission.body from span_start + 1 for span_end - span_start)
                  is distinct from span->>'quote' then
                raise exception 'Essay provider evidence does not match immutable submission';
            end if;
        end loop;
    end loop;
    return new;
end;
$$;

create or replace function protect_english_essay_provider_feedback()
returns trigger
language plpgsql
as $$
begin
    raise exception 'Essay provider feedback is immutable';
end;
$$;

create trigger english_essay_provider_feedback_attempt_is_valid
before insert or update on english_essay_provider_feedback_attempts
for each row execute function validate_english_essay_provider_feedback_attempt();

create trigger english_essay_provider_feedback_is_valid
before insert on english_essay_provider_feedback
for each row execute function validate_english_essay_provider_feedback();

create trigger english_essay_provider_feedback_is_immutable
before update or delete on english_essay_provider_feedback
for each row execute function protect_english_essay_provider_feedback();

alter table english_essay_provider_feedback_attempts enable row level security;
alter table english_essay_provider_feedback enable row level security;

create policy english_essay_provider_feedback_attempts_owner_read
on english_essay_provider_feedback_attempts for select using (student_id = auth.uid());
create policy english_essay_provider_feedback_owner_read
on english_essay_provider_feedback for select using (student_id = auth.uid());

revoke all on english_essay_provider_feedback_attempts,
    english_essay_provider_feedback from anon, authenticated;
grant select on english_essay_provider_feedback_attempts,
    english_essay_provider_feedback to authenticated;
grant all on english_essay_provider_feedback_attempts,
    english_essay_provider_feedback to service_role;

comment on table english_essay_provider_feedback_attempts is
    'Disabled-by-default provider-candidate lifecycle. No provider adapter is released before calibration.';
comment on table english_essay_provider_feedback is
    'Immutable schema-validated formative feedback whose quoted spans exactly match the essay submission.';

commit;
