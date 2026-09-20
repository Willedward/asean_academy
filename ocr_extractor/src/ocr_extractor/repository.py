"""Transactional staging persistence for SQLite or PostgreSQL/Supabase."""

import sqlite3
from importlib.resources import files
from pathlib import Path

from .models import ExtractionResult
from .pdf import ExtractionError


class Repository:
    def __init__(self, connection, *, postgres: bool = False):
        self.connection = connection
        self.postgres = postgres
        self.prefix = "ocr_extractor." if postgres else ""
        self.placeholder = "%s" if postgres else "?"

    @classmethod
    def sqlite(cls, path: Path | str):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(path), timeout=30)
        connection.execute("PRAGMA foreign_keys = ON")
        repository = cls(connection)
        repository.initialize()
        return repository

    @classmethod
    def connect_postgres(cls, url: str):
        try:
            import psycopg
        except ImportError as exc:
            raise ExtractionError(
                "missing_dependency",
                "Install PostgreSQL support: uv sync --extra postgres",
            ) from exc
        try:
            return cls(psycopg.connect(url, connect_timeout=10), postgres=True)
        except psycopg.Error as exc:
            raise ExtractionError(
                "database_connection_failed",
                "Cannot connect to PostgreSQL; check DATABASE_URL.",
            ) from exc

    def initialize(self):
        dialect = "postgres" if self.postgres else "sqlite"
        migrations = files("ocr_extractor").joinpath("migrations")
        sql = "\n".join(
            p.read_text()
            for p in sorted(migrations.iterdir(), key=lambda p: p.name)
            if p.name.endswith(f"_{dialect}.sql")
        )
        if self.postgres:
            with self.connection.transaction():
                self.connection.execute(sql)
        else:
            self.connection.executescript(sql)

    def _insert(self, table: str, values: dict, *, upsert: bool = False):
        columns = ", ".join(values)
        placeholders = ", ".join(self.placeholder for _ in values)
        sql = f"INSERT INTO {self.prefix}{table} ({columns}) VALUES ({placeholders})"
        if upsert:
            updates = ", ".join(f"{name} = excluded.{name}" for name in values if name != "id")
            sql += f" ON CONFLICT (id) DO UPDATE SET {updates}"
        self.connection.execute(sql, tuple(values.values()))

    def save(self, result: ExtractionResult):
        """Replace this document's staging rows atomically; stable IDs survive reruns."""
        result = ExtractionResult.model_validate(result.model_dump())
        transaction = self.connection.transaction() if self.postgres else self.connection
        with transaction:
            doc = result.document
            doc_id = str(doc.id)
            self._insert(
                "source_documents",
                {
                    "id": doc_id,
                    "sha256": doc.sha256,
                    "original_filename": doc.original_filename,
                    "storage_path": doc.storage_path,
                    "page_count": doc.page_count,
                    "status": doc.status,
                    "run_key": result.run_key,
                    "payload": result.model_dump_json(),
                    "created_at": result.created_at,
                },
                upsert=True,
            )
            # Delete assets before pages; answer_keys cascade from questions.
            for table in ["question_assets", "questions", "source_pages"]:
                self.connection.execute(
                    f"DELETE FROM {self.prefix}{table} WHERE document_id = {self.placeholder}",
                    (doc_id,),
                )
            for page in result.pages:
                self._insert(
                    "source_pages",
                    {
                        "id": str(page.id),
                        "document_id": doc_id,
                        "page_number": page.page_number,
                        "page_type": page.page_type,
                        "image_path": page.image_path,
                        "ocr_text": page.text,
                        "payload": page.model_dump_json(),
                    },
                )
            for question in result.questions:
                self._insert(
                    "questions",
                    {
                        "id": str(question.id),
                        "document_id": doc_id,
                        "question_number": question.question_number,
                        "paper": question.paper,
                        "section": question.section,
                        "question_text": question.question_text,
                        "marks": question.marks,
                        "answer_type": question.answer_type,
                        "status": question.status,
                        "payload": question.model_dump_json(),
                    },
                )
                for asset in question.assets:
                    self._save_asset(asset, doc_id, str(question.id))
                for order, block in enumerate(question.content):
                    self._insert(
                        "question_blocks",
                        {
                            "id": str(block.id),
                            "question_id": str(question.id),
                            "block_order": order,
                            "type": block.type,
                            "text": block.text,
                            "latex": block.latex,
                            "confidence": block.confidence,
                            "status": block.status,
                            "source_path": block.source_path,
                            "payload": block.model_dump_json(),
                        },
                    )
                if question.answer_key:
                    self._insert(
                        "answer_keys",
                        {
                            "question_id": str(question.id),
                            "raw_text": question.answer_key.raw_text,
                            "payload": question.answer_key.model_dump_json(),
                        },
                    )
            for asset in result.unpaired_solutions:
                self._save_asset(asset, doc_id, None)

    def _save_asset(self, asset, doc_id, question_id):
        self._insert(
            "question_assets",
            {
                "id": str(asset.id),
                "document_id": doc_id,
                "question_id": question_id,
                "page_number": asset.page_number,
                "kind": asset.kind,
                "asset_order": asset.order,
                "path": asset.path,
                "payload": asset.model_dump_json(),
            },
        )

    def close(self):
        self.connection.close()

    def save_review(self, review):
        transaction = self.connection.transaction() if self.postgres else self.connection
        with transaction:
            self._insert(
                "question_reviews",
                {
                    **{
                        key: str(getattr(review, key))
                        for key in (
                            "id",
                            "document_id",
                            "question_id",
                            "run_key",
                            "source_fingerprint",
                            "reviewer",
                            "decision",
                            "created_at",
                        )
                    },
                    "payload": review.model_dump_json(),
                },
            )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
