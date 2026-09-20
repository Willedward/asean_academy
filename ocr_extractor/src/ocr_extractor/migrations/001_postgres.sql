-- Private staging schema. This is not the future student-facing content schema.
CREATE SCHEMA IF NOT EXISTS ocr_extractor;
REVOKE ALL ON SCHEMA ocr_extractor FROM PUBLIC;
CREATE TABLE IF NOT EXISTS ocr_extractor.source_documents (
    id UUID PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    page_count INTEGER NOT NULL CHECK (page_count > 0),
    status TEXT NOT NULL CHECK (status = 'needs_review'),
    run_key TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS ocr_extractor.source_pages (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES ocr_extractor.source_documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    page_type TEXT NOT NULL,
    image_path TEXT NOT NULL,
    ocr_text TEXT NOT NULL,
    payload JSONB NOT NULL,
    UNIQUE (document_id, page_number)
);
CREATE TABLE IF NOT EXISTS ocr_extractor.questions (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES ocr_extractor.source_documents(id) ON DELETE CASCADE,
    question_number TEXT NOT NULL,
    paper TEXT,
    section TEXT,
    question_text TEXT NOT NULL,
    marks DOUBLE PRECISION CHECK (marks >= 0),
    answer_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status = 'needs_review'),
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS questions_document_idx ON ocr_extractor.questions(document_id);
CREATE TABLE IF NOT EXISTS ocr_extractor.question_assets (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES ocr_extractor.source_documents(id) ON DELETE CASCADE,
    question_id UUID REFERENCES ocr_extractor.questions(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('question', 'solution')),
    asset_order INTEGER NOT NULL,
    path TEXT NOT NULL,
    payload JSONB NOT NULL,
    FOREIGN KEY (document_id, page_number)
        REFERENCES ocr_extractor.source_pages(document_id, page_number)
);
CREATE INDEX IF NOT EXISTS assets_question_idx ON ocr_extractor.question_assets(question_id);
CREATE TABLE IF NOT EXISTS ocr_extractor.answer_keys (
    question_id UUID PRIMARY KEY REFERENCES ocr_extractor.questions(id) ON DELETE CASCADE,
    raw_text TEXT NOT NULL,
    payload JSONB NOT NULL
);
ALTER TABLE ocr_extractor.source_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_extractor.source_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_extractor.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_extractor.question_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_extractor.answer_keys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA ocr_extractor FROM PUBLIC;
-- No student policies: connect as the schema owner (trusted worker) for ingestion.
