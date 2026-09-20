begin;

create type course_content_status as enum ('draft', 'reviewed', 'published', 'retired');
create type lesson_section_type as enum ('explanation', 'worked_example', 'active_recall', 'summary');
create type question_pool_type as enum ('lesson_practice', 'unit_checkpoint', 'adaptive_reserve');
create type question_pool_stage as enum ('guided', 'independent', 'challenge', 'checkpoint', 'adaptive');

create table programmes (
    id uuid primary key default gen_random_uuid(),
    programme_key text not null unique,
    title text not null,
    description text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (length(btrim(programme_key)) > 0),
    check (length(btrim(title)) > 0)
);

create table courses (
    id uuid primary key default gen_random_uuid(),
    programme_id uuid not null references programmes(id) on delete restrict,
    curriculum_version_id uuid not null references curriculum_versions(id) on delete restrict,
    course_key text not null unique,
    school_level math_school_level not null,
    subject text not null,
    created_at timestamptz not null default now(),
    check (length(btrim(course_key)) > 0),
    check (length(btrim(subject)) > 0)
);

create table course_versions (
    id uuid primary key default gen_random_uuid(),
    course_id uuid not null references courses(id) on delete restrict,
    revision integer not null check (revision > 0),
    schema_version text not null,
    title text not null,
    description text not null,
    status course_content_status not null default 'draft',
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    provenance jsonb not null,
    is_current boolean not null default false,
    authored_at timestamptz not null,
    reviewed_at timestamptz,
    review_notes text,
    created_at timestamptz not null default now(),
    unique (course_id, revision),
    check (jsonb_typeof(provenance) = 'object')
);

create unique index course_versions_one_current_idx
    on course_versions(course_id) where is_current;

create table mastery_policies (
    id uuid primary key default gen_random_uuid(),
    course_version_id uuid not null references course_versions(id) on delete cascade,
    policy_key text not null,
    minimum_eventual_correct_percentage smallint not null check (
        minimum_eventual_correct_percentage between 0 and 100
    ),
    mastery_requires_checkpoint boolean not null,
    checkpoint_passing_percentage smallint not null check (
        checkpoint_passing_percentage between 0 and 100
    ),
    give_up_after_incorrect_attempts smallint not null check (
        give_up_after_incorrect_attempts between 1 and 10
    ),
    hints_penalize_marks boolean not null,
    unique (course_version_id, policy_key)
);

create table course_units (
    id uuid primary key default gen_random_uuid(),
    course_id uuid not null references courses(id) on delete restrict,
    unit_key text not null,
    topic_id uuid not null references syllabus_topics(id) on delete restrict,
    created_at timestamptz not null default now(),
    unique (course_id, unit_key)
);

create table unit_versions (
    id uuid primary key default gen_random_uuid(),
    unit_id uuid not null references course_units(id) on delete restrict,
    course_version_id uuid not null references course_versions(id) on delete cascade,
    position smallint not null check (position > 0),
    title text not null,
    checkpoint_question_count smallint not null check (checkpoint_question_count > 0),
    unique (course_version_id, position),
    unique (course_version_id, unit_id)
);

create table course_lessons (
    id uuid primary key default gen_random_uuid(),
    unit_id uuid not null references course_units(id) on delete restrict,
    lesson_key text not null unique,
    created_at timestamptz not null default now(),
    unique (unit_id, lesson_key)
);

create table lesson_versions (
    id uuid primary key default gen_random_uuid(),
    lesson_id uuid not null references course_lessons(id) on delete restrict,
    revision integer not null check (revision > 0),
    schema_version text not null,
    title text not null,
    summary text not null,
    status course_content_status not null default 'draft',
    estimated_minutes smallint not null check (estimated_minutes between 1 and 180),
    objectives jsonb not null,
    mastery_policy_key text not null,
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    provenance jsonb not null,
    is_current boolean not null default false,
    authored_at timestamptz not null,
    reviewed_at timestamptz,
    review_notes text,
    created_at timestamptz not null default now(),
    unique (lesson_id, revision),
    check (jsonb_typeof(objectives) = 'array'),
    check (jsonb_array_length(objectives) > 0),
    check (jsonb_typeof(provenance) = 'object')
);

create unique index lesson_versions_one_current_idx
    on lesson_versions(lesson_id) where is_current;

create table unit_version_lessons (
    unit_version_id uuid not null references unit_versions(id) on delete cascade,
    lesson_version_id uuid not null references lesson_versions(id) on delete restrict,
    position smallint not null check (position > 0),
    required_practice_count smallint not null check (required_practice_count > 0),
    primary key (unit_version_id, lesson_version_id),
    unique (unit_version_id, position)
);

create table lesson_prerequisites (
    lesson_version_id uuid not null references lesson_versions(id) on delete cascade,
    prerequisite_lesson_id uuid not null references course_lessons(id) on delete restrict,
    primary key (lesson_version_id, prerequisite_lesson_id)
);

create table lesson_outcomes (
    lesson_version_id uuid not null references lesson_versions(id) on delete cascade,
    outcome_id uuid not null references syllabus_outcomes(id) on delete restrict,
    position smallint not null check (position > 0),
    primary key (lesson_version_id, outcome_id),
    unique (lesson_version_id, position)
);

create table lesson_sections (
    id uuid primary key default gen_random_uuid(),
    lesson_version_id uuid not null references lesson_versions(id) on delete cascade,
    section_key text not null,
    position smallint not null check (position > 0),
    section_type lesson_section_type not null,
    title text not null,
    content jsonb not null,
    unique (lesson_version_id, section_key),
    unique (lesson_version_id, position),
    check (jsonb_typeof(content) = 'object')
);

create table lesson_assets (
    id uuid primary key default gen_random_uuid(),
    lesson_version_id uuid not null references lesson_versions(id) on delete cascade,
    asset_key text not null,
    kind math_asset_kind not null,
    format math_asset_format not null,
    storage_path text not null,
    alt_text text not null,
    generation_spec jsonb not null default '{}'::jsonb,
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    width integer check (width is null or width > 0),
    height integer check (height is null or height > 0),
    unique (lesson_version_id, asset_key),
    check (jsonb_typeof(generation_spec) = 'object')
);

create table lesson_question_pools (
    id uuid primary key default gen_random_uuid(),
    unit_version_id uuid not null references unit_versions(id) on delete cascade,
    lesson_version_id uuid not null references lesson_versions(id) on delete restrict,
    pool_key text not null,
    expected_question_count smallint not null check (expected_question_count > 0),
    unique (unit_version_id, pool_key),
    unique (unit_version_id, lesson_version_id)
);

create table lesson_question_pool_items (
    pool_id uuid not null references lesson_question_pools(id) on delete cascade,
    question_id uuid not null references math_questions(id) on delete restrict,
    question_version_id uuid references math_question_versions(id) on delete restrict,
    position smallint not null check (position > 0),
    stage question_pool_stage not null check (stage in ('guided', 'independent', 'challenge')),
    weight smallint not null default 1 check (weight between 1 and 100),
    active_from timestamptz,
    active_until timestamptz,
    primary key (pool_id, question_id),
    unique (pool_id, position),
    check (active_until is null or active_from is null or active_until > active_from)
);

create table unit_checkpoint_pools (
    id uuid primary key default gen_random_uuid(),
    unit_version_id uuid not null references unit_versions(id) on delete cascade,
    pool_key text not null,
    pool_type question_pool_type not null check (pool_type in ('unit_checkpoint', 'adaptive_reserve')),
    expected_question_count smallint not null check (expected_question_count > 0),
    unique (unit_version_id, pool_key),
    unique (unit_version_id, pool_type)
);

create table unit_checkpoint_pool_items (
    pool_id uuid not null references unit_checkpoint_pools(id) on delete cascade,
    question_id uuid not null references math_questions(id) on delete restrict,
    question_version_id uuid references math_question_versions(id) on delete restrict,
    position smallint not null check (position > 0),
    stage question_pool_stage not null check (stage in ('checkpoint', 'adaptive')),
    weight smallint not null default 1 check (weight between 1 and 100),
    active_from timestamptz,
    active_until timestamptz,
    primary key (pool_id, question_id),
    unique (pool_id, position),
    check (active_until is null or active_from is null or active_until > active_from)
);

alter table programmes enable row level security;
alter table courses enable row level security;
alter table course_versions enable row level security;
alter table mastery_policies enable row level security;
alter table course_units enable row level security;
alter table unit_versions enable row level security;
alter table course_lessons enable row level security;
alter table lesson_versions enable row level security;
alter table unit_version_lessons enable row level security;
alter table lesson_prerequisites enable row level security;
alter table lesson_outcomes enable row level security;
alter table lesson_sections enable row level security;
alter table lesson_assets enable row level security;
alter table lesson_question_pools enable row level security;
alter table lesson_question_pool_items enable row level security;
alter table unit_checkpoint_pools enable row level security;
alter table unit_checkpoint_pool_items enable row level security;

comment on table course_versions is
    'Immutable versioned course metadata. A draft import never makes content learner-visible.';
comment on table lesson_versions is
    'Immutable lesson content; changed content requires an incremented revision.';
comment on table unit_version_lessons is
    'Pins exact lesson revisions and ordering to an exact unit/course revision.';
comment on column lesson_question_pool_items.question_version_id is
    'Optional authoring pin. Session creation must persist the resolved published version.';
comment on table unit_checkpoint_pools is
    'Stores both unseen checkpoint candidates and adaptive reserve pools for a unit version.';

commit;
