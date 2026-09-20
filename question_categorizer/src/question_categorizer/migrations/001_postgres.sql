CREATE SCHEMA IF NOT EXISTS question_categorizer;
CREATE TABLE IF NOT EXISTS question_categorizer.syllabus_versions (
    id UUID PRIMARY KEY,
    version_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'active')),
    source_reference TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS question_categorizer.syllabus_topics (
    id UUID PRIMARY KEY,
    syllabus_version_id UUID NOT NULL REFERENCES question_categorizer.syllabus_versions(id),
    code TEXT NOT NULL,
    strand TEXT NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    UNIQUE (syllabus_version_id, code)
);
CREATE TABLE IF NOT EXISTS question_categorizer.syllabus_outcomes (
    id UUID PRIMARY KEY,
    topic_id UUID NOT NULL REFERENCES question_categorizer.syllabus_topics(id),
    level TEXT NOT NULL CHECK (level IN ('secondary_1', 'secondary_2')),
    outcome_code TEXT NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    UNIQUE (topic_id, level, outcome_code)
);
CREATE TABLE IF NOT EXISTS question_categorizer.categorization_runs (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    extraction_run_key TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    classifier_version TEXT NOT NULL,
    input_path TEXT NOT NULL,
    input_sha256 TEXT NOT NULL,
    source_level TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS question_categorizer.question_categorizations (
    run_id UUID NOT NULL REFERENCES question_categorizer.categorization_runs(id) ON DELETE CASCADE,
    question_id UUID NOT NULL,
    question_number TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('classified', 'unclassified', 'rejected')),
    primary_topic_code TEXT,
    review_reasons JSONB NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (run_id, question_id)
);
CREATE TABLE IF NOT EXISTS question_categorizer.question_parts (
    run_id UUID NOT NULL REFERENCES question_categorizer.categorization_runs(id) ON DELETE CASCADE,
    id UUID NOT NULL,
    question_id UUID NOT NULL,
    part_label TEXT,
    part_order INTEGER NOT NULL,
    checked_text TEXT NOT NULL,
    checked_latex TEXT NOT NULL,
    source_fingerprint TEXT NOT NULL,
    input_status TEXT NOT NULL CHECK (input_status IN ('checked', 'machine_unchecked')),
    classification_status TEXT NOT NULL CHECK (classification_status IN ('classified', 'unclassified')),
    review_reasons JSONB NOT NULL,
    PRIMARY KEY (run_id, id),
    UNIQUE (run_id, question_id, part_order)
);
CREATE TABLE IF NOT EXISTS question_categorizer.question_topics (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL,
    question_id UUID NOT NULL,
    question_part_id UUID NOT NULL,
    topic_id UUID NOT NULL REFERENCES question_categorizer.syllabus_topics(id),
    outcome_id UUID REFERENCES question_categorizer.syllabus_outcomes(id),
    role TEXT NOT NULL CHECK (role IN ('primary', 'secondary')),
    status TEXT NOT NULL CHECK (status IN ('suggested', 'confirmed', 'rejected')),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source TEXT NOT NULL CHECK (source IN ('rules', 'local_model', 'api_model', 'human')),
    classifier_version TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    evidence JSONB NOT NULL,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (run_id, question_part_id)
        REFERENCES question_categorizer.question_parts(run_id, id)
);
CREATE INDEX IF NOT EXISTS question_topics_question_idx
    ON question_categorizer.question_topics(question_id, taxonomy_version, status);
CREATE INDEX IF NOT EXISTS question_topics_topic_idx
    ON question_categorizer.question_topics(topic_id, outcome_id, status);
