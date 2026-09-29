begin;

alter type beta_audit_event_type add value if not exists 'question_report_created';
alter type beta_audit_event_type add value if not exists 'question_report_status_changed';

create type retry_resolution as enum (
    'clean_correct', 'assisted_correct', 'incorrect', 'gave_up', 'checkpoint_incorrect'
);
create type question_report_category as enum (
    'possible_error', 'unclear_wording', 'display_problem', 'other'
);
create type question_report_status as enum ('open', 'in_review', 'resolved', 'dismissed');

alter table question_progress
    add column due_at timestamptz,
    add column interval_days smallint check (interval_days in (2, 4, 7, 14)),
    add column review_stage smallint not null default 0 check (review_stage between 0 and 3),
    add column review_streak smallint not null default 0 check (review_streak between 0 and 100),
    add column last_resolution retry_resolution;

alter table session_questions
    add column retry_origin_question_id uuid references math_questions(id) on delete restrict;

update question_progress
set due_at = coalesce(last_attempted_at, updated_at),
    interval_days = 2,
    last_resolution = case when state = 'gave_up' then 'gave_up'::retry_resolution
                           else 'incorrect'::retry_resolution end
where state in ('queued_for_retry', 'gave_up');

create index question_progress_due_selection_idx
    on question_progress(student_id, due_at, updated_at)
    where state in ('queued_for_retry', 'gave_up');

create table question_reports (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    question_version_id uuid not null references math_question_versions(id) on delete restrict,
    practice_session_id uuid references practice_sessions(id) on delete set null,
    category question_report_category not null,
    comment text not null check (length(btrim(comment)) between 1 and 1000),
    status question_report_status not null default 'open',
    resolution text check (resolution is null or length(btrim(resolution)) between 1 and 2000),
    resolved_by uuid references auth.users(id) on delete restrict,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    resolved_at timestamptz,
    check (
        (status in ('resolved', 'dismissed') and resolution is not null and resolved_by is not null and resolved_at is not null)
        or (status in ('open', 'in_review') and resolution is null and resolved_by is null and resolved_at is null)
    )
);

create index question_reports_student_created_idx
    on question_reports(student_id, created_at desc);
create index question_reports_admin_queue_idx
    on question_reports(status, created_at);

alter table question_reports enable row level security;
create policy question_reports_owner_read on question_reports for select
    to authenticated using (student_id = auth.uid());
grant select on question_reports to authenticated;

comment on column question_progress.due_at is
    'Server-owned next eligible review time under the 2/4/7/14-day policy.';
comment on column session_questions.retry_origin_question_id is
    'Original learning record advanced when an adaptive reserve variant is served.';
comment on table question_reports is
    'Learner reports pinned to the exact rendered question revision; submitted answers are excluded.';

commit;
