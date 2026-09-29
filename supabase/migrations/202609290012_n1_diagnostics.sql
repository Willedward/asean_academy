begin;

create type diagnostic_purpose as enum ('baseline', 'endline');
create type diagnostic_form_status as enum ('draft', 'published', 'retired');
create type diagnostic_session_state as enum ('in_progress', 'submitted', 'reset');

create table diagnostic_forms (
    id uuid primary key default gen_random_uuid(),
    stable_key text not null,
    revision integer not null check (revision > 0),
    course_version_id uuid not null references course_versions(id) on delete restrict,
    purpose diagnostic_purpose not null,
    status diagnostic_form_status not null default 'draft',
    title text not null,
    instructions text not null,
    estimated_minutes smallint not null check (estimated_minutes between 1 and 120),
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    band_policy_version text not null,
    is_current boolean not null default false,
    authored_at timestamptz not null default now(),
    reviewed_at timestamptz,
    published_at timestamptz,
    unique (stable_key, revision),
    unique (id, course_version_id, purpose),
    check (length(btrim(stable_key)) > 0),
    check (length(btrim(title)) > 0),
    check ((status = 'published' and reviewed_at is not null and published_at is not null)
        or status <> 'published')
);

create unique index diagnostic_forms_one_current_purpose_idx
    on diagnostic_forms(course_version_id, purpose)
    where is_current and status = 'published';

create table diagnostic_form_items (
    id uuid primary key default gen_random_uuid(),
    form_id uuid not null references diagnostic_forms(id) on delete cascade,
    question_version_id uuid not null references math_question_versions(id) on delete restrict,
    outcome_id uuid not null references syllabus_outcomes(id) on delete restrict,
    position smallint not null check (position > 0),
    weight numeric(8,3) not null default 1 check (weight > 0 and weight <= 100),
    unique (form_id, position),
    unique (form_id, question_version_id)
);

create table diagnostic_sessions (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    form_id uuid not null,
    course_version_id uuid not null,
    purpose diagnostic_purpose not null,
    state diagnostic_session_state not null default 'in_progress',
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    request_fingerprint text not null check (request_fingerprint ~ '^[0-9a-f]{64}$'),
    started_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    submitted_at timestamptz,
    reset_at timestamptz,
    foreign key (form_id, course_version_id, purpose)
        references diagnostic_forms(id, course_version_id, purpose) on delete restrict,
    unique (student_id, idempotency_key),
    check (
        (state = 'in_progress' and submitted_at is null and reset_at is null)
        or (state = 'submitted' and submitted_at is not null and reset_at is null)
        or (state = 'reset' and reset_at is not null)
    )
);

create unique index diagnostic_sessions_one_effective_purpose_idx
    on diagnostic_sessions(student_id, course_version_id, purpose)
    where state <> 'reset';
create index diagnostic_sessions_student_started_idx
    on diagnostic_sessions(student_id, started_at desc);

create table diagnostic_responses (
    session_id uuid not null references diagnostic_sessions(id) on delete cascade,
    form_item_id uuid not null references diagnostic_form_items(id) on delete restrict,
    position smallint not null check (position > 0),
    answer_payload jsonb not null,
    answer_sha256 text not null check (answer_sha256 ~ '^[0-9a-f]{64}$'),
    score numeric(10,3) not null check (score >= 0),
    max_score numeric(10,3) not null check (max_score > 0 and score <= max_score),
    answered_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (session_id, form_item_id),
    unique (session_id, position),
    check (jsonb_typeof(answer_payload) = 'object')
);

create table diagnostic_response_idempotency_keys (
    session_id uuid not null references diagnostic_sessions(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    position smallint not null check (position > 0),
    request_fingerprint text not null check (request_fingerprint ~ '^[0-9a-f]{64}$'),
    created_at timestamptz not null default now(),
    primary key (session_id, idempotency_key)
);

create table diagnostic_results (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null unique references diagnostic_sessions(id) on delete restrict,
    student_id uuid not null references auth.users(id) on delete cascade,
    form_id uuid not null references diagnostic_forms(id) on delete restrict,
    purpose diagnostic_purpose not null,
    score numeric(10,3) not null check (score >= 0),
    max_score numeric(10,3) not null check (max_score > 0 and score <= max_score),
    percentage numeric(5,2) not null check (percentage between 0 and 100),
    band text not null check (band in ('getting_started', 'on_track', 'ahead')),
    outcome_scores jsonb not null,
    band_policy_version text not null,
    created_at timestamptz not null default now(),
    check (jsonb_typeof(outcome_scores) = 'object')
);

create table diagnostic_resets (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references diagnostic_sessions(id) on delete restrict,
    student_id uuid not null references auth.users(id) on delete cascade,
    purpose diagnostic_purpose not null,
    reset_by uuid not null references auth.users(id) on delete restrict,
    reason text not null check (length(btrim(reason)) between 10 and 500),
    request_id text not null,
    created_at timestamptz not null default now(),
    unique (session_id)
);

create or replace function reject_diagnostic_result_mutation()
returns trigger language plpgsql as $$
begin
    raise exception 'diagnostic results are immutable';
end;
$$;

create trigger diagnostic_results_are_immutable
before update or delete on diagnostic_results
for each row execute function reject_diagnostic_result_mutation();

create or replace function reject_diagnostic_reset_mutation()
returns trigger language plpgsql as $$
begin
    raise exception 'diagnostic reset audit records are immutable';
end;
$$;

create trigger diagnostic_resets_are_immutable
before update or delete on diagnostic_resets
for each row execute function reject_diagnostic_reset_mutation();

create or replace function enforce_diagnostic_question_isolation()
returns trigger language plpgsql as $$
begin
    if not exists (
        select 1
        from math_question_versions versions
        join math_questions questions on questions.id = versions.question_id
        where versions.id = new.question_version_id
          and versions.reviewed_at is not null
          and questions.status = 'published'
    ) then
        raise exception 'diagnostic forms require reviewed, published question revisions';
    end if;
    if exists (
        select 1
        from math_question_versions versions
        where versions.id = new.question_version_id
          and (
            exists (
                select 1 from lesson_question_pool_items items
                where items.question_id = versions.question_id
                   or items.question_version_id = versions.id
            )
            or exists (
                select 1 from unit_checkpoint_pool_items items
                where items.question_id = versions.question_id
                   or items.question_version_id = versions.id
            )
          )
    ) then
        raise exception 'diagnostic questions cannot belong to practice, checkpoint, or reserve pools';
    end if;
    return new;
end;
$$;

create trigger diagnostic_items_require_isolated_questions
before insert or update on diagnostic_form_items
for each row execute function enforce_diagnostic_question_isolation();

create or replace function enforce_learning_pool_question_isolation()
returns trigger language plpgsql as $$
begin
    if exists (
        select 1
        from diagnostic_form_items diagnostic
        join math_question_versions versions on versions.id = diagnostic.question_version_id
        where versions.question_id = new.question_id
           or (new.question_version_id is not null and diagnostic.question_version_id = new.question_version_id)
    ) then
        raise exception 'diagnostic questions cannot belong to practice, checkpoint, or reserve pools';
    end if;
    return new;
end;
$$;

create trigger lesson_pool_items_reject_diagnostic_questions
before insert or update on lesson_question_pool_items
for each row execute function enforce_learning_pool_question_isolation();
create trigger checkpoint_pool_items_reject_diagnostic_questions
before insert or update on unit_checkpoint_pool_items
for each row execute function enforce_learning_pool_question_isolation();

alter table diagnostic_forms enable row level security;
alter table diagnostic_form_items enable row level security;
alter table diagnostic_sessions enable row level security;
alter table diagnostic_responses enable row level security;
alter table diagnostic_response_idempotency_keys enable row level security;
alter table diagnostic_results enable row level security;
alter table diagnostic_resets enable row level security;

create policy diagnostic_forms_authenticated_read on diagnostic_forms for select
to authenticated using (status = 'published');
create policy diagnostic_form_items_authenticated_read on diagnostic_form_items for select
to authenticated using (exists (
    select 1 from diagnostic_forms forms where forms.id = form_id and forms.status = 'published'
));
create policy diagnostic_sessions_owner_read on diagnostic_sessions for select
to authenticated using (student_id = auth.uid());
create policy diagnostic_responses_owner_read on diagnostic_responses for select
to authenticated using (exists (
    select 1 from diagnostic_sessions sessions
    where sessions.id = session_id and sessions.student_id = auth.uid()
));
create policy diagnostic_results_owner_read on diagnostic_results for select
to authenticated using (student_id = auth.uid());

revoke all on diagnostic_response_idempotency_keys from authenticated;
revoke all on diagnostic_resets from authenticated;
grant select on diagnostic_forms, diagnostic_form_items, diagnostic_sessions,
    diagnostic_responses, diagnostic_results to authenticated;

comment on table diagnostic_forms is 'Immutable, course-revision-pinned baseline and endline assessment forms.';
comment on table diagnostic_form_items is 'Exact isolated question revisions assigned to one diagnostic form.';
comment on table diagnostic_responses is 'Autosaved answers with server-only deterministic scores; correctness is withheld until submission.';
comment on table diagnostic_results is 'Immutable submitted score evidence using a versioned band policy.';
comment on table diagnostic_resets is 'Append-only academic-administrator audit trail allowing an exceptional retake.';

commit;
