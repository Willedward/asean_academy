begin;

create table english_essay_marking_jobs (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    submission_id uuid not null unique
        references english_essay_submissions(id) on delete restrict,
    rubric_version_id uuid not null
        references english_essay_rubric_versions(id) on delete restrict,
    mode text not null default 'deterministic_fixture' check (
        mode = 'deterministic_fixture'
    ),
    status text not null default 'queued' check (
        status in (
            'queued', 'processing', 'retryable_failed',
            'succeeded', 'permanent_failed'
        )
    ),
    attempt_count smallint not null default 0 check (attempt_count >= 0),
    max_attempts smallint not null default 3 check (max_attempts between 1 and 5),
    run_after timestamptz not null default now(),
    lease_token uuid,
    leased_at timestamptz,
    worker_id text,
    last_error_code text,
    last_error_message text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz,
    check (
        (status = 'processing' and lease_token is not null and leased_at is not null)
        or (status <> 'processing' and lease_token is null and leased_at is null)
    ),
    check (
        (status = 'succeeded' and completed_at is not null)
        or (status <> 'succeeded' and completed_at is null)
    )
);

create table english_essay_marking_feedback (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    job_id uuid not null unique
        references english_essay_marking_jobs(id) on delete restrict,
    submission_id uuid not null unique
        references english_essay_submissions(id) on delete restrict,
    rubric_version_id uuid not null
        references english_essay_rubric_versions(id) on delete restrict,
    fixture_version text not null check (
        fixture_version ~ '^english-essay-fixture-v[0-9]+$'
    ),
    criterion_feedback jsonb not null check (
        jsonb_typeof(criterion_feedback) = 'array'
        and jsonb_array_length(criterion_feedback) between 3 and 6
    ),
    overall_summary text not null check (length(btrim(overall_summary)) > 0),
    strengths jsonb not null check (
        jsonb_typeof(strengths) = 'array' and jsonb_array_length(strengths) > 0
    ),
    priorities jsonb not null check (
        jsonb_typeof(priorities) = 'array' and jsonb_array_length(priorities) > 0
    ),
    learner_disclaimer text not null check (length(btrim(learner_disclaimer)) > 0),
    created_at timestamptz not null default now()
);

create table english_essay_marking_job_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    job_id uuid not null references english_essay_marking_jobs(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

create index english_essay_marking_jobs_due_idx
    on english_essay_marking_jobs(run_after, created_at)
    where status in ('queued', 'retryable_failed', 'processing');
create index english_essay_marking_jobs_student_created_idx
    on english_essay_marking_jobs(student_id, created_at desc);

create or replace function validate_english_essay_marking_job()
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
        if not found then
            raise exception 'English essay marking submission does not exist';
        end if;
        if row(new.student_id, new.rubric_version_id)
           is distinct from row(source_submission.student_id, source_submission.rubric_version_id) then
            raise exception 'English essay marking job must use the owned submission and pinned rubric revision';
        end if;
        if not exists (
            select 1 from english_essay_self_reviews reviews
             where reviews.submission_id = new.submission_id
               and reviews.student_id = new.student_id
        ) then
            raise exception 'English essay marking requires a completed learner self-review';
        end if;
    elsif row(old.student_id, old.submission_id, old.rubric_version_id, old.mode,
              old.max_attempts, old.created_at)
          is distinct from
          row(new.student_id, new.submission_id, new.rubric_version_id, new.mode,
              new.max_attempts, new.created_at) then
        raise exception 'English essay marking job identity is immutable';
    end if;
    return new;
end;
$$;

create or replace function validate_english_essay_marking_feedback()
returns trigger
language plpgsql
as $$
declare
    source_job english_essay_marking_jobs%rowtype;
    submitted_keys text[];
    rubric_keys text[];
begin
    select * into source_job
      from english_essay_marking_jobs
     where id = new.job_id
     for update;
    if not found then
        raise exception 'English essay marking job does not exist';
    end if;
    if row(new.student_id, new.submission_id, new.rubric_version_id)
       is distinct from row(source_job.student_id, source_job.submission_id,
                            source_job.rubric_version_id) then
        raise exception 'English essay marking feedback must match its job snapshot';
    end if;
    if exists (
        select 1 from jsonb_array_elements(new.criterion_feedback) feedback
         where jsonb_typeof(feedback) <> 'object'
            or coalesce(feedback->>'criterion_key', '') = ''
            or length(btrim(coalesce(feedback->>'observed_evidence', ''))) = 0
            or length(btrim(coalesce(feedback->>'what_works', ''))) = 0
            or length(btrim(coalesce(feedback->>'next_step', ''))) = 0
    ) then
        raise exception 'English essay marking criterion feedback is invalid';
    end if;
    select array_agg(feedback->>'criterion_key' order by feedback->>'criterion_key')
      into submitted_keys
      from jsonb_array_elements(new.criterion_feedback) feedback;
    select array_agg(criterion->>'criterion_key' order by criterion->>'criterion_key')
      into rubric_keys
      from english_essay_rubric_versions versions,
           jsonb_array_elements(versions.criteria) criterion
     where versions.id = new.rubric_version_id;
    if submitted_keys is distinct from rubric_keys then
        raise exception 'English essay marking feedback must cover every pinned rubric criterion exactly once';
    end if;
    return new;
end;
$$;

create or replace function protect_english_essay_marking_feedback()
returns trigger
language plpgsql
as $$
begin
    raise exception 'English essay marking feedback is immutable';
end;
$$;

create trigger english_essay_marking_job_is_valid
before insert or update on english_essay_marking_jobs
for each row execute function validate_english_essay_marking_job();

create trigger english_essay_marking_feedback_is_valid
before insert on english_essay_marking_feedback
for each row execute function validate_english_essay_marking_feedback();

create trigger english_essay_marking_feedback_is_immutable
before update or delete on english_essay_marking_feedback
for each row execute function protect_english_essay_marking_feedback();

alter table english_essay_marking_jobs enable row level security;
alter table english_essay_marking_feedback enable row level security;
alter table english_essay_marking_job_idempotency_keys enable row level security;

create policy english_essay_marking_jobs_owner_read
on english_essay_marking_jobs for select using (student_id = auth.uid());
create policy english_essay_marking_feedback_owner_read
on english_essay_marking_feedback for select using (student_id = auth.uid());
create policy english_essay_marking_job_idempotency_owner_read
on english_essay_marking_job_idempotency_keys for select using (student_id = auth.uid());

grant select on english_essay_marking_jobs to authenticated;
grant select on english_essay_marking_feedback to authenticated;
grant select on english_essay_marking_job_idempotency_keys to authenticated;

comment on table english_essay_marking_jobs is
    'Durable, retryable jobs for deterministic local fixture feedback. This queue makes no external provider calls.';
comment on table english_essay_marking_feedback is
    'Immutable structured development-fixture feedback. It is neither AI feedback nor an official scholarship score or prediction.';

commit;
