CREATE TABLE IF NOT EXISTS syllabus_versions (
    id TEXT PRIMARY KEY,
    version_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'active')),
    source_reference TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS syllabus_topics (
    id TEXT PRIMARY KEY,
    syllabus_version_id TEXT NOT NULL REFERENCES syllabus_versions(id),
    code TEXT NOT NULL,
    strand TEXT NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    UNIQUE (syllabus_version_id, code)
);
CREATE TABLE IF NOT EXISTS syllabus_outcomes (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES syllabus_topics(id),
    level TEXT NOT NULL CHECK (level IN ('secondary_1', 'secondary_2')),
    outcome_code TEXT NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    UNIQUE (topic_id, level, outcome_code)
);
CREATE TABLE IF NOT EXISTS categorization_runs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    extraction_run_key TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    classifier_version TEXT NOT NULL,
    input_path TEXT NOT NULL,
    input_sha256 TEXT NOT NULL,
    source_level TEXT,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload))
);
CREATE TABLE IF NOT EXISTS question_categorizations (
    run_id TEXT NOT NULL REFERENCES categorization_runs(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    question_number TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('classified', 'unclassified', 'rejected')),
    primary_topic_code TEXT,
    review_reasons TEXT NOT NULL CHECK (json_valid(review_reasons)),
    payload TEXT NOT NULL CHECK (json_valid(payload)),
    PRIMARY KEY (run_id, question_id)
);
CREATE TABLE IF NOT EXISTS question_parts (
    run_id TEXT NOT NULL REFERENCES categorization_runs(id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    part_label TEXT,
    part_order INTEGER NOT NULL,
    checked_text TEXT NOT NULL,
    checked_latex TEXT NOT NULL,
    source_fingerprint TEXT NOT NULL,
    input_status TEXT NOT NULL CHECK (input_status IN ('checked', 'machine_unchecked')),
    classification_status TEXT NOT NULL CHECK (classification_status IN ('classified', 'unclassified')),
    review_reasons TEXT NOT NULL CHECK (json_valid(review_reasons)),
    PRIMARY KEY (run_id, id),
    UNIQUE (run_id, question_id, part_order)
);
CREATE TABLE IF NOT EXISTS question_topics (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_part_id TEXT NOT NULL,
    topic_id TEXT NOT NULL REFERENCES syllabus_topics(id),
    outcome_id TEXT REFERENCES syllabus_outcomes(id),
    role TEXT NOT NULL CHECK (role IN ('primary', 'secondary')),
    status TEXT NOT NULL CHECK (status IN ('suggested', 'confirmed', 'rejected')),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source TEXT NOT NULL CHECK (source IN ('rules', 'local_model', 'api_model', 'human')),
    classifier_version TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    evidence TEXT NOT NULL CHECK (json_valid(evidence)),
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id, question_part_id) REFERENCES question_parts(run_id, id)
);
CREATE INDEX IF NOT EXISTS question_topics_question_idx
    ON question_topics(question_id, taxonomy_version, status);
CREATE INDEX IF NOT EXISTS question_topics_topic_idx
    ON question_topics(topic_id, outcome_id, status);
