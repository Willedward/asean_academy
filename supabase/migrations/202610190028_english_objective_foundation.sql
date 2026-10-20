begin;

create type english_question_status as enum ('draft', 'reviewed', 'published', 'retired');
create type english_passage_status as enum ('draft', 'reviewed', 'published', 'retired');
create type english_question_type as enum (
    'vocabulary_in_context',
    'grammar_usage',
    'banked_cloze',
    'open_cloze',
    'reading_comprehension',
    'editing'
);
create type english_exposure_pool as enum (
    'lesson_example',
    'guided_practice',
    'independent_practice',
    'exit_ticket',
    'retry_review',
    'module_checkpoint',
    'baseline_diagnostic',
    'endline_diagnostic',
    'full_mock',
    'protected_reserve'
);
create type english_feedback_timing as enum ('after_item', 'after_group');

create table english_curriculum_modules (
    id uuid primary key default gen_random_uuid(),
    curriculum_version_id uuid not null references curriculum_versions(id) on delete restrict,
    module_code text not null,
    stage text not null check (stage in ('orientation', 'toolkit', 'paper_application', 'composition')),
    title text not null,
    purpose text not null,
    position smallint not null check (position between 0 and 9),
    unique (curriculum_version_id, module_code),
    unique (curriculum_version_id, position),
    check (module_code ~ '^E[0-9]+$')
);

create table english_curriculum_outcomes (
    id uuid primary key default gen_random_uuid(),
    module_id uuid not null references english_curriculum_modules(id) on delete cascade,
    lesson_code text not null,
    lesson_key text not null,
    outcome_code text not null,
    title text not null,
    description text not null,
    position smallint not null check (position > 0),
    unique (module_id, lesson_code),
    unique (lesson_key),
    unique (outcome_code),
    unique (module_id, position),
    check (lesson_code ~ '^E[0-9]+\.[0-9]+$'),
    check (lesson_key ~ '^e[0-9]+-lesson-[0-9]{2}$'),
    check (outcome_code ~ '^(EX|EV|EG|EB|EO|ER|EW)[0-9]+\.[0-9]+$')
);

create table english_passages (
    id uuid primary key default gen_random_uuid(),
    stable_key text not null unique,
    created_at timestamptz not null default now(),
    check (stable_key ~ '^english-passage-[a-z0-9-]+$')
);

create table english_passage_versions (
    id uuid primary key default gen_random_uuid(),
    passage_id uuid not null references english_passages(id) on delete restrict,
    revision integer not null check (revision > 0),
    schema_version text not null,
    title text not null,
    text_type text not null check (text_type in ('narrative', 'informational', 'argumentative', 'reflective')),
    paragraphs jsonb not null,
    attribution text not null,
    status english_passage_status not null default 'draft',
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    provenance jsonb not null,
    is_current boolean not null default false,
    authored_at timestamptz not null,
    reviewed_at timestamptz,
    review_notes text,
    created_at timestamptz not null default now(),
    unique (passage_id, revision),
    check (jsonb_typeof(paragraphs) = 'array'),
    check (jsonb_array_length(paragraphs) > 0),
    check (jsonb_typeof(provenance) = 'object'),
    check ((status in ('reviewed', 'published') and reviewed_at is not null) or status in ('draft', 'retired'))
);

create unique index english_passage_versions_one_current_idx
    on english_passage_versions(passage_id) where is_current;

create table english_objective_question_banks (
    id uuid primary key default gen_random_uuid(),
    curriculum_version_id uuid not null references curriculum_versions(id) on delete restrict,
    bank_key text not null unique,
    revision integer not null check (revision > 0),
    schema_version text not null,
    title text not null,
    status english_question_status not null default 'draft',
    expected_question_count integer not null check (expected_question_count > 0),
    outcome_codes jsonb not null,
    pool_distribution jsonb not null,
    source_refs jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (bank_key ~ '^english-(ev|eg|eb|eo|er|ex)-v[0-9]+$'),
    check (jsonb_typeof(outcome_codes) = 'array'),
    check (jsonb_typeof(pool_distribution) = 'object'),
    check (jsonb_typeof(source_refs) = 'array')
);

create table english_objective_questions (
    id uuid primary key default gen_random_uuid(),
    bank_id uuid not null references english_objective_question_banks(id) on delete restrict,
    outcome_id uuid not null references english_curriculum_outcomes(id) on delete restrict,
    stable_key text not null unique,
    difficulty smallint not null check (difficulty between 1 and 5),
    question_type english_question_type not null,
    exposure_pool english_exposure_pool not null,
    status english_question_status not null default 'draft',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (stable_key ~ '^(ev|eg|eb|eo|er|ex)-l[1-5]-[0-9]{3,4}$')
);

create table english_objective_question_versions (
    id uuid primary key default gen_random_uuid(),
    question_id uuid not null references english_objective_questions(id) on delete restrict,
    passage_version_id uuid references english_passage_versions(id) on delete restrict,
    revision integer not null check (revision > 0),
    schema_version text not null,
    title text not null,
    instructions text not null,
    feedback_timing english_feedback_timing not null,
    parts jsonb not null,
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    provenance jsonb not null,
    is_current boolean not null default false,
    authored_at timestamptz not null,
    reviewed_at timestamptz,
    review_notes text,
    created_at timestamptz not null default now(),
    unique (question_id, revision),
    check (jsonb_typeof(parts) = 'array'),
    check (jsonb_array_length(parts) > 0),
    check (jsonb_typeof(provenance) = 'object')
);

create unique index english_objective_question_versions_one_current_idx
    on english_objective_question_versions(question_id) where is_current;
create index english_objective_questions_bank_status_idx
    on english_objective_questions(bank_id, status);
create index english_objective_questions_pool_idx
    on english_objective_questions(exposure_pool, status);

create trigger english_objective_question_banks_set_updated_at
before update on english_objective_question_banks
for each row execute function set_question_bank_updated_at();

create trigger english_objective_questions_set_updated_at
before update on english_objective_questions
for each row execute function set_question_bank_updated_at();

alter table english_curriculum_modules enable row level security;
alter table english_curriculum_outcomes enable row level security;
alter table english_passages enable row level security;
alter table english_passage_versions enable row level security;
alter table english_objective_question_banks enable row level security;
alter table english_objective_questions enable row level security;
alter table english_objective_question_versions enable row level security;

comment on table english_passage_versions is
    'Immutable English passage revisions. Questions pin an exact revision and checksum before publication.';
comment on table english_objective_question_versions is
    'Versioned deterministic objective-English content. Response specifications are validated against the generated source contract before import.';
comment on column english_objective_questions.exposure_pool is
    'Separates lesson, retry, checkpoint, diagnostic, mock and reserve exposure so live assessment items are not leaked through practice.';

commit;
