CREATE TABLE IF NOT EXISTS ocr_extractor.question_blocks (
    id UUID PRIMARY KEY,
    question_id UUID NOT NULL REFERENCES ocr_extractor.questions(id) ON DELETE CASCADE,
    block_order INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('text', 'math', 'table', 'image')),
    text TEXT NOT NULL,
    latex TEXT,
    confidence DOUBLE PRECISION CHECK (confidence BETWEEN 0 AND 1),
    status TEXT NOT NULL CHECK (status = 'needs_review'),
    source_path TEXT NOT NULL,
    payload JSONB NOT NULL,
    UNIQUE (question_id, block_order)
);
-- Review history deliberately survives replacement of staging question rows.
CREATE TABLE IF NOT EXISTS ocr_extractor.question_reviews (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    question_id UUID NOT NULL,
    run_key TEXT NOT NULL,
    source_fingerprint TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('draft', 'checked', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS reviews_question_idx
    ON ocr_extractor.question_reviews(question_id, run_key);
CREATE OR REPLACE VIEW ocr_extractor.question_display WITH (security_invoker = true) AS
SELECT q.*, q.payload->>'question_latex' AS question_latex,
       q.payload->'review_reasons' AS review_reasons
FROM ocr_extractor.questions q;
ALTER TABLE ocr_extractor.question_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_extractor.question_reviews ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ocr_extractor.question_blocks, ocr_extractor.question_reviews,
    ocr_extractor.question_display FROM PUBLIC;
