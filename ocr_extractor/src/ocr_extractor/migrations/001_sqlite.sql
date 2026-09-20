CREATE TABLE IF NOT EXISTS source_documents (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    page_count INTEGER NOT NULL CHECK (page_count > 0),
    status TEXT NOT NULL CHECK (status = 'needs_review'),
    run_key TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload)),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_pages (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    page_type TEXT NOT NULL,
    image_path TEXT NOT NULL,
    ocr_text TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload)),
    UNIQUE (document_id, page_number)
);
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
    question_number TEXT NOT NULL,
    paper TEXT,
    section TEXT,
    question_text TEXT NOT NULL,
    marks REAL CHECK (marks >= 0),
    answer_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status = 'needs_review'),
    payload TEXT NOT NULL CHECK (json_valid(payload))
);
CREATE INDEX IF NOT EXISTS questions_document_idx ON questions(document_id);
CREATE TABLE IF NOT EXISTS question_assets (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
    question_id TEXT REFERENCES questions(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('question', 'solution')),
    asset_order INTEGER NOT NULL,
    path TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload)),
    FOREIGN KEY (document_id, page_number) REFERENCES source_pages(document_id, page_number)
);
CREATE INDEX IF NOT EXISTS assets_question_idx ON question_assets(question_id);
CREATE TABLE IF NOT EXISTS answer_keys (
    question_id TEXT PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    raw_text TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload))
);
