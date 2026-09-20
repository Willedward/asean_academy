CREATE TABLE IF NOT EXISTS question_blocks (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    block_order INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('text', 'math', 'table', 'image')),
    text TEXT NOT NULL,
    latex TEXT,
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    status TEXT NOT NULL CHECK (status = 'needs_review'),
    source_path TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload)),
    UNIQUE (question_id, block_order)
);
CREATE TABLE IF NOT EXISTS question_reviews (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    run_key TEXT NOT NULL,
    source_fingerprint TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('draft', 'checked', 'rejected')),
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload))
);
CREATE INDEX IF NOT EXISTS reviews_question_idx ON question_reviews(question_id, run_key);
CREATE VIEW IF NOT EXISTS question_display AS
SELECT q.*, json_extract(q.payload, '$.question_latex') AS question_latex,
       json_extract(q.payload, '$.review_reasons') AS review_reasons
FROM questions q;
