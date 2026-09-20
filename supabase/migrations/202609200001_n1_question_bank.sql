begin;

create extension if not exists pgcrypto;

create type curriculum_status as enum ('draft', 'active', 'retired');
create type math_bank_status as enum ('draft', 'reviewed', 'published', 'retired');
create type math_question_status as enum ('draft', 'reviewed', 'published', 'retired');
create type math_school_level as enum ('secondary_1', 'secondary_2');
create type math_response_type as enum ('numeric', 'algebraic_expression');
create type math_comparison_mode as enum (
    'exact_numeric',
    'absolute_tolerance',
    'rounded_dp',
    'rounded_sf',
    'symbolic_equivalence',
    'prime_factorisation',
    'ordered_numeric_list',
    'exact_relation'
);
create type math_mark_type as enum ('B', 'M', 'A');
create type math_asset_kind as enum ('number_line', 'geometry', 'chart', 'table', 'image');
create type math_asset_format as enum ('svg', 'png', 'webp');

create table curriculum_versions (
    id uuid primary key default gen_random_uuid(),
    version_key text not null unique,
    title text not null,
    jurisdiction text not null,
    subject text not null,
    status curriculum_status not null default 'draft',
    source_reference text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (length(btrim(version_key)) > 0),
    check (length(btrim(title)) > 0)
);

create table syllabus_topics (
    id uuid primary key default gen_random_uuid(),
    curriculum_version_id uuid not null references curriculum_versions(id) on delete restrict,
    code text not null,
    title text not null,
    strand text not null,
    position integer not null check (position > 0),
    unique (curriculum_version_id, code)
);

create table syllabus_outcomes (
    id uuid primary key default gen_random_uuid(),
    topic_id uuid not null references syllabus_topics(id) on delete cascade,
    school_level math_school_level not null,
    code text not null,
    description text not null,
    position integer not null check (position > 0),
    unique (topic_id, school_level, code)
);

create table math_question_banks (
    id uuid primary key default gen_random_uuid(),
    bank_key text not null unique,
    curriculum_version_id uuid not null references curriculum_versions(id) on delete restrict,
    topic_id uuid not null references syllabus_topics(id) on delete restrict,
    school_level math_school_level not null,
    revision integer not null default 1 check (revision > 0),
    schema_version text not null default '1.0.0',
    title text not null,
    description text,
    status math_bank_status not null default 'draft',
    expected_question_count integer not null check (expected_question_count > 0),
    difficulty_counts jsonb not null,
    source_style_references jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    published_at timestamptz,
    check (jsonb_typeof(difficulty_counts) = 'object'),
    check (difficulty_counts ?& array['1', '2', '3']),
    check (jsonb_typeof(source_style_references) = 'array'),
    check ((status = 'published' and published_at is not null) or status <> 'published')
);

create table math_questions (
    id uuid primary key default gen_random_uuid(),
    bank_id uuid not null references math_question_banks(id) on delete restrict,
    primary_outcome_id uuid not null references syllabus_outcomes(id) on delete restrict,
    stable_key text not null,
    difficulty smallint not null check (difficulty between 1 and 3),
    status math_question_status not null default 'draft',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (bank_id, stable_key)
);

create table math_question_versions (
    id uuid primary key default gen_random_uuid(),
    question_id uuid not null references math_questions(id) on delete restrict,
    revision integer not null check (revision > 0),
    schema_version text not null default '1.0.0',
    title text not null,
    calculator_allowed boolean not null,
    question_type text not null check (question_type = 'structured'),
    stem_blocks jsonb not null default '[]'::jsonb,
    total_marks smallint not null check (total_marks > 0),
    content_sha256 text not null,
    provenance jsonb not null,
    is_current boolean not null default false,
    authored_at timestamptz not null default now(),
    authored_by uuid,
    reviewed_at timestamptz,
    reviewed_by uuid,
    review_notes text,
    unique (question_id, revision),
    check (jsonb_typeof(stem_blocks) = 'array'),
    check (jsonb_typeof(provenance) = 'object'),
    check (content_sha256 ~ '^[0-9a-f]{64}$'),
    check ((reviewed_at is null and reviewed_by is null) or reviewed_at is not null)
);

create unique index math_question_versions_one_current_idx
    on math_question_versions(question_id)
    where is_current;

create table math_question_parts (
    id uuid primary key default gen_random_uuid(),
    question_version_id uuid not null references math_question_versions(id) on delete cascade,
    label text,
    position smallint not null check (position > 0),
    prompt_blocks jsonb not null,
    marks smallint not null check (marks > 0),
    response_type math_response_type not null,
    unique (id, response_type),
    unique (question_version_id, position),
    check (label is null or length(btrim(label)) > 0),
    check (jsonb_typeof(prompt_blocks) = 'array'),
    check (jsonb_array_length(prompt_blocks) > 0)
);

create unique index math_question_parts_label_idx
    on math_question_parts(question_version_id, label)
    where label is not null;

create table math_question_outcomes (
    question_part_id uuid not null references math_question_parts(id) on delete cascade,
    outcome_id uuid not null references syllabus_outcomes(id) on delete restrict,
    role text not null default 'primary' check (role in ('primary', 'secondary')),
    primary key (question_part_id, outcome_id)
);

create unique index math_question_outcomes_one_primary_idx
    on math_question_outcomes(question_part_id)
    where role = 'primary';

create table math_question_hints (
    id uuid primary key default gen_random_uuid(),
    question_part_id uuid not null references math_question_parts(id) on delete cascade,
    stage smallint not null check (stage in (1, 2)),
    content_blocks jsonb not null,
    unique (question_part_id, stage),
    check (jsonb_typeof(content_blocks) = 'array'),
    check (jsonb_array_length(content_blocks) > 0)
);

create table math_answer_specs (
    id uuid primary key default gen_random_uuid(),
    question_part_id uuid not null unique,
    response_type math_response_type not null,
    comparison_mode math_comparison_mode not null,
    canonical_answer text not null,
    canonical_latex text,
    absolute_tolerance numeric,
    rounding_precision smallint,
    variables text[] not null default '{}',
    domain_constraints text[] not null default '{}',
    accepted_answers jsonb not null default '[]'::jsonb,
    checker_config jsonb not null default '{}'::jsonb,
    unit_spec jsonb,
    foreign key (question_part_id, response_type)
        references math_question_parts(id, response_type) on delete cascade,
    check (length(btrim(canonical_answer)) > 0),
    check (absolute_tolerance is null or absolute_tolerance >= 0),
    check (rounding_precision is null or rounding_precision >= 0),
    check (jsonb_typeof(accepted_answers) = 'array'),
    check (jsonb_typeof(checker_config) = 'object'),
    check (unit_spec is null or jsonb_typeof(unit_spec) = 'object'),
    check (
        (response_type = 'numeric' and comparison_mode in (
            'exact_numeric', 'absolute_tolerance', 'rounded_dp', 'rounded_sf'
        ))
        or
        (response_type = 'algebraic_expression' and comparison_mode in (
            'symbolic_equivalence', 'prime_factorisation',
            'ordered_numeric_list', 'exact_relation'
        ))
    ),
    check (
        (comparison_mode = 'absolute_tolerance' and absolute_tolerance is not null)
        or comparison_mode <> 'absolute_tolerance'
    ),
    check (
        (comparison_mode in ('rounded_dp', 'rounded_sf') and rounding_precision is not null)
        or comparison_mode not in ('rounded_dp', 'rounded_sf')
    )
);

create table math_solution_steps (
    id uuid primary key default gen_random_uuid(),
    question_part_id uuid not null references math_question_parts(id) on delete cascade,
    position smallint not null check (position > 0),
    content_blocks jsonb not null,
    mark_type math_mark_type,
    mark_value smallint not null default 0 check (mark_value >= 0),
    unique (question_part_id, position),
    check (jsonb_typeof(content_blocks) = 'array'),
    check (jsonb_array_length(content_blocks) > 0),
    check ((mark_type is null and mark_value = 0) or (mark_type is not null and mark_value > 0))
);

create table math_question_assets (
    id uuid primary key default gen_random_uuid(),
    question_version_id uuid not null references math_question_versions(id) on delete cascade,
    asset_key text not null,
    kind math_asset_kind not null,
    format math_asset_format not null,
    storage_path text not null,
    alt_text text not null,
    generation_spec jsonb not null default '{}'::jsonb,
    content_sha256 text not null,
    width integer check (width is null or width > 0),
    height integer check (height is null or height > 0),
    unique (question_version_id, asset_key),
    unique (storage_path),
    check (length(btrim(asset_key)) > 0),
    check (length(btrim(storage_path)) > 0),
    check (length(btrim(alt_text)) > 0),
    check (jsonb_typeof(generation_spec) = 'object'),
    check (content_sha256 ~ '^[0-9a-f]{64}$')
);

create index math_questions_bank_status_idx on math_questions(bank_id, status);
create index math_questions_difficulty_idx on math_questions(bank_id, difficulty);
create index math_question_parts_version_idx on math_question_parts(question_version_id, position);
create index math_question_outcomes_outcome_idx on math_question_outcomes(outcome_id);

create or replace function set_question_bank_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger curriculum_versions_set_updated_at
before update on curriculum_versions
for each row execute function set_question_bank_updated_at();

create trigger math_question_banks_set_updated_at
before update on math_question_banks
for each row execute function set_question_bank_updated_at();

create trigger math_questions_set_updated_at
before update on math_questions
for each row execute function set_question_bank_updated_at();

insert into curriculum_versions (
    id, version_key, title, jurisdiction, subject, status, source_reference
) values (
    'b0caa9ce-7063-5131-89a5-816a7372bf19',
    'g3_math_v1_draft',
    'Singapore G3 Mathematics, Secondary 1 and 2',
    'Singapore',
    'Mathematics',
    'draft',
    'User-provided G3 Mathematics syllabus extracts'
)
on conflict (id) do nothing;

insert into syllabus_topics (
    id, curriculum_version_id, code, title, strand, position
) values (
    '0b7db168-df83-5a0a-8f17-1f037be69e3e',
    'b0caa9ce-7063-5131-89a5-816a7372bf19',
    'N1',
    'Numbers and their operations',
    'Number and Algebra',
    1
)
on conflict (id) do nothing;

insert into syllabus_outcomes (id, topic_id, school_level, code, description, position) values
    ('03f96e88-f92c-562b-b541-568d2ed42980', '0b7db168-df83-5a0a-8f17-1f037be69e3e', 'secondary_1', '1.1', 'Primes and prime factorisation', 1),
    ('2bb38012-cd58-567d-bfb6-7908d960fb28', '0b7db168-df83-5a0a-8f17-1f037be69e3e', 'secondary_1', '1.2', 'Finding HCF and LCM, squares, cubes, square roots and cube roots by prime factorisation', 2),
    ('b0744940-1e9c-51c8-a205-9f787959ebf6', '0b7db168-df83-5a0a-8f17-1f037be69e3e', 'secondary_1', '1.3', 'Negative numbers, integers, rational numbers, real numbers and their four operations', 3),
    ('dc7cbdbe-e222-5759-815b-021708bfb5ae', '0b7db168-df83-5a0a-8f17-1f037be69e3e', 'secondary_1', '1.4', 'Calculations with a calculator', 4),
    ('77cfdaea-b22c-521d-9833-0a11efc88b50', '0b7db168-df83-5a0a-8f17-1f037be69e3e', 'secondary_1', '1.5', 'Representation and ordering of numbers on the number line', 5),
    ('354db7cc-bb54-5870-94dd-b229b907258f', '0b7db168-df83-5a0a-8f17-1f037be69e3e', 'secondary_1', '1.6', 'Use of less than, greater than, less than or equal to, and greater than or equal to', 6),
    ('2d6de75c-4ef3-5d91-a1a9-ba11c0444b02', '0b7db168-df83-5a0a-8f17-1f037be69e3e', 'secondary_1', '1.7', 'Approximation and estimation, including rounding to decimal places or significant figures and estimating results', 7)
on conflict (id) do nothing;

insert into math_question_banks (
    id, bank_key, curriculum_version_id, topic_id, school_level, revision,
    schema_version, title, description, status, expected_question_count,
    difficulty_counts, source_style_references
) values (
    '252de3fb-79c0-5293-b8e3-13ec383a2c28',
    'g3-sec1-n1-v1',
    'b0caa9ce-7063-5131-89a5-816a7372bf19',
    '0b7db168-df83-5a0a-8f17-1f037be69e3e',
    'secondary_1',
    1,
    '1.0.0',
    'Secondary 1 G3 Mathematics: N1 Numbers and their operations',
    'Forty fixed structured questions with two hints and a worked solution for every part.',
    'draft',
    40,
    '{"1": 15, "2": 15, "3": 10}'::jsonb,
    '["TMS 2023 1E Math P2 (QP).pdf", "TMS 2023 1E Math P2 (ANS).pdf", "2022 Sec 2 Express Math EOY Anglo Chinese School with Answers.pdf", "2022 Sec 2 Express Math EOY Canberra Secondary with Answers.pdf", "Math - Sec2 - SA2 - 2023 - Zhonghua Sec.pdf"]'::jsonb
)
on conflict (id) do nothing;

alter table curriculum_versions enable row level security;
alter table syllabus_topics enable row level security;
alter table syllabus_outcomes enable row level security;
alter table math_question_banks enable row level security;
alter table math_questions enable row level security;
alter table math_question_versions enable row level security;
alter table math_question_parts enable row level security;
alter table math_question_outcomes enable row level security;
alter table math_question_hints enable row level security;
alter table math_answer_specs enable row level security;
alter table math_solution_steps enable row level security;
alter table math_question_assets enable row level security;

comment on table math_question_versions is
    'Versioned assessed content. Attempts must reference this row rather than only math_questions.';
comment on column math_question_versions.stem_blocks is
    'Ordered text, inline_math, display_math, and asset_ref blocks rendered safely by the client.';
comment on table math_answer_specs is
    'Private deterministic checking configuration; exclude from unanswered-question API payloads.';
comment on table math_solution_steps is
    'Private worked solution and optional B/M/A marking annotations.';

commit;
