begin;

create table english_essay_submissions (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references auth.users(id) on delete cascade,
    draft_id uuid not null references english_essay_drafts(id) on delete restrict,
    prompt_version_id uuid not null
        references english_essay_prompt_versions(id) on delete restrict,
    rubric_version_id uuid not null
        references english_essay_rubric_versions(id) on delete restrict,
    draft_edit_revision integer not null check (draft_edit_revision > 0),
    submission_revision integer not null check (submission_revision > 0),
    body text not null check (length(body) between 1 and 20000),
    body_sha256 text not null check (body_sha256 ~ '^[0-9a-f]{64}$'),
    word_count integer not null check (word_count > 0),
    paragraph_count integer not null check (paragraph_count > 0),
    deterministic_checks jsonb not null check (
        jsonb_typeof(deterministic_checks) = 'array'
        and jsonb_array_length(deterministic_checks) > 0
    ),
    draft_created_at timestamptz not null,
    draft_updated_at timestamptz not null,
    draft_age_seconds integer not null check (draft_age_seconds >= 0),
    submitted_at timestamptz not null default now(),
    unique (draft_id, submission_revision),
    unique (draft_id, draft_edit_revision)
);

create table english_essay_submission_idempotency_keys (
    student_id uuid not null references auth.users(id) on delete cascade,
    idempotency_key text not null check (length(idempotency_key) between 1 and 200),
    submission_id uuid not null references english_essay_submissions(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (student_id, idempotency_key)
);

create index english_essay_submissions_student_submitted_idx
    on english_essay_submissions(student_id, submitted_at desc);

create or replace function validate_english_essay_submission_snapshot()
returns trigger
language plpgsql
as $$
declare
    source_draft english_essay_drafts%rowtype;
    source_rubric_version_id uuid;
    expected_revision integer;
begin
    select * into source_draft
      from english_essay_drafts
     where id = new.draft_id
     for update;
    if not found then
        raise exception 'English essay submission draft does not exist';
    end if;

    select rubric_version_id into source_rubric_version_id
      from english_essay_prompt_versions
     where id = source_draft.prompt_version_id;

    select coalesce(max(submission_revision), 0) + 1 into expected_revision
      from english_essay_submissions
     where draft_id = new.draft_id;

    if row(
        new.student_id, new.prompt_version_id, new.rubric_version_id,
        new.draft_edit_revision, new.body, new.word_count,
        new.draft_created_at, new.draft_updated_at
    ) is distinct from row(
        source_draft.student_id, source_draft.prompt_version_id,
        source_rubric_version_id, source_draft.edit_revision,
        source_draft.body, source_draft.word_count,
        source_draft.created_at, source_draft.updated_at
    ) then
        raise exception 'English essay submission must exactly snapshot its owned draft and pinned revisions';
    end if;
    if new.submission_revision <> expected_revision then
        raise exception 'English essay submission revision must be the next revision';
    end if;
    return new;
end;
$$;

create or replace function protect_english_essay_submission()
returns trigger
language plpgsql
as $$
begin
    raise exception 'English essay submissions are immutable';
end;
$$;

create trigger english_essay_submission_snapshot_is_exact
before insert on english_essay_submissions
for each row execute function validate_english_essay_submission_snapshot();

create trigger english_essay_submission_is_immutable
before update or delete on english_essay_submissions
for each row execute function protect_english_essay_submission();

alter table english_essay_submissions enable row level security;
alter table english_essay_submission_idempotency_keys enable row level security;

create policy english_essay_submissions_owner_read
on english_essay_submissions for select using (student_id = auth.uid());

create policy english_essay_submission_idempotency_owner_read
on english_essay_submission_idempotency_keys for select using (student_id = auth.uid());

grant select on english_essay_submissions to authenticated;
grant select on english_essay_submission_idempotency_keys to authenticated;

comment on table english_essay_submissions is
    'Immutable learner-owned essay snapshots pinned to exact draft, prompt and instructional-rubric revisions. No score or AI feedback is stored here.';
comment on column english_essay_submissions.draft_age_seconds is
    'Wall-clock age from draft creation to submission; not a claim of continuous timed writing.';
comment on column english_essay_submissions.deterministic_checks is
    'Server-generated structural checks only. This field contains no quality grade or official-score claim.';

commit;
