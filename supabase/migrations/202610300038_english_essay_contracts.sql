begin;

create table english_essay_rubrics (
    id uuid primary key default gen_random_uuid(),
    stable_key text not null unique check (
        stable_key ~ '^english-essay-rubric-[a-z0-9-]+$'
    ),
    created_at timestamptz not null default now()
);

create table english_essay_rubric_versions (
    id uuid primary key default gen_random_uuid(),
    rubric_id uuid not null references english_essay_rubrics(id) on delete restrict,
    revision integer not null check (revision > 0),
    schema_version text not null,
    exam_profile_key text not null check (
        exam_profile_key ~ '^asean-english-[a-z0-9-]+-v[0-9]+$'
    ),
    title text not null check (length(title) > 0),
    purpose text not null check (length(purpose) > 0),
    status english_question_status not null default 'draft',
    official_score_claim boolean not null default false check (not official_score_claim),
    scale_min smallint not null default 1 check (scale_min = 1),
    scale_max smallint not null default 5 check (scale_max = 5),
    criteria jsonb not null check (
        jsonb_typeof(criteria) = 'array' and jsonb_array_length(criteria) between 3 and 6
    ),
    learner_disclaimer text not null check (length(learner_disclaimer) > 0),
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    provenance jsonb not null check (jsonb_typeof(provenance) = 'object'),
    is_current boolean not null default false,
    authored_at timestamptz not null,
    reviewed_at timestamptz,
    review_notes text,
    created_at timestamptz not null default now(),
    unique (rubric_id, revision),
    check (
        (status in ('reviewed', 'published') and reviewed_at is not null)
        or status in ('draft', 'retired')
    )
);

create unique index english_essay_rubric_versions_one_current_idx
    on english_essay_rubric_versions(rubric_id) where is_current;

create table english_essay_prompts (
    id uuid primary key default gen_random_uuid(),
    stable_key text not null unique check (
        stable_key ~ '^english-essay-prompt-[a-z0-9-]+$'
    ),
    created_at timestamptz not null default now()
);

create table english_essay_prompt_versions (
    id uuid primary key default gen_random_uuid(),
    prompt_id uuid not null references english_essay_prompts(id) on delete restrict,
    rubric_version_id uuid not null
        references english_essay_rubric_versions(id) on delete restrict,
    revision integer not null check (revision > 0),
    schema_version text not null,
    exam_profile_key text not null check (
        exam_profile_key ~ '^asean-english-[a-z0-9-]+-v[0-9]+$'
    ),
    title text not null check (length(title) > 0),
    prompt_family text not null check (
        prompt_family in (
            'reflective_personal_expository',
            'narrative',
            'opinion_discursive',
            'general_expository'
        )
    ),
    prompt_text text not null check (length(prompt_text) > 0),
    instructions jsonb not null check (
        jsonb_typeof(instructions) = 'array' and jsonb_array_length(instructions) > 0
    ),
    time_limit_minutes smallint not null check (time_limit_minutes between 10 and 120),
    time_limit_evidence text not null check (
        time_limit_evidence in ('official', 'candidate_reported', 'inferred')
    ),
    word_count_guidance smallint check (word_count_guidance between 50 and 2000),
    word_count_status text not null check (
        word_count_status in ('not_stated', 'guidance', 'strict')
    ),
    status english_question_status not null default 'draft',
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    provenance jsonb not null check (jsonb_typeof(provenance) = 'object'),
    is_current boolean not null default false,
    authored_at timestamptz not null,
    reviewed_at timestamptz,
    review_notes text,
    created_at timestamptz not null default now(),
    unique (prompt_id, revision),
    check (
        (word_count_guidance is null) = (word_count_status = 'not_stated')
    ),
    check (
        (status in ('reviewed', 'published') and reviewed_at is not null)
        or status in ('draft', 'retired')
    )
);

create unique index english_essay_prompt_versions_one_current_idx
    on english_essay_prompt_versions(prompt_id) where is_current;
create index english_essay_prompt_versions_rubric_idx
    on english_essay_prompt_versions(rubric_version_id);

create or replace function protect_english_essay_rubric_revision()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE' then
        raise exception 'English essay rubric revisions cannot be deleted';
    end if;
    if row(
        old.rubric_id, old.revision, old.schema_version, old.exam_profile_key,
        old.title, old.purpose, old.official_score_claim, old.scale_min,
        old.scale_max, old.criteria, old.learner_disclaimer, old.content_sha256,
        old.authored_at
    ) is distinct from row(
        new.rubric_id, new.revision, new.schema_version, new.exam_profile_key,
        new.title, new.purpose, new.official_score_claim, new.scale_min,
        new.scale_max, new.criteria, new.learner_disclaimer, new.content_sha256,
        new.authored_at
    ) then
        raise exception 'English essay rubric revision content is immutable; create a new revision';
    end if;
    return new;
end;
$$;

create or replace function protect_english_essay_prompt_revision()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE' then
        raise exception 'English essay prompt revisions cannot be deleted';
    end if;
    if row(
        old.prompt_id, old.rubric_version_id, old.revision, old.schema_version,
        old.exam_profile_key, old.title, old.prompt_family, old.prompt_text,
        old.instructions, old.time_limit_minutes, old.time_limit_evidence,
        old.word_count_guidance, old.word_count_status, old.content_sha256,
        old.authored_at
    ) is distinct from row(
        new.prompt_id, new.rubric_version_id, new.revision, new.schema_version,
        new.exam_profile_key, new.title, new.prompt_family, new.prompt_text,
        new.instructions, new.time_limit_minutes, new.time_limit_evidence,
        new.word_count_guidance, new.word_count_status, new.content_sha256,
        new.authored_at
    ) then
        raise exception 'English essay prompt revision content is immutable; create a new revision';
    end if;
    return new;
end;
$$;

create trigger english_essay_rubric_revision_content_is_immutable
before update or delete on english_essay_rubric_versions
for each row execute function protect_english_essay_rubric_revision();

create trigger english_essay_prompt_revision_content_is_immutable
before update or delete on english_essay_prompt_versions
for each row execute function protect_english_essay_prompt_revision();

alter table english_essay_rubrics enable row level security;
alter table english_essay_rubric_versions enable row level security;
alter table english_essay_prompts enable row level security;
alter table english_essay_prompt_versions enable row level security;

comment on table english_essay_rubric_versions is
    'Immutable instructional rubric revisions. These are not official scholarship scoring schemes.';
comment on table english_essay_prompt_versions is
    'Immutable original-authored essay prompt revisions pinned to an exact instructional rubric revision.';
comment on column english_essay_rubric_versions.official_score_claim is
    'Fail-closed invariant: NextScholar rubric revisions cannot claim to be an official scholarship score.';

commit;
