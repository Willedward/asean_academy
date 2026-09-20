"""Relational persistence for taxonomy and versioned categorization runs."""

import json
import sqlite3
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .models import CategorizationResult, Taxonomy


class Repository:
    def __init__(self, connection, *, postgres: bool = False):
        self.connection = connection
        self.postgres = postgres
        self.prefix = "question_categorizer." if postgres else ""
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
            raise RuntimeError("Install PostgreSQL support with --extra postgres") from exc
        try:
            repository = cls(psycopg.connect(url, connect_timeout=10), postgres=True)
            repository.initialize()
            return repository
        except psycopg.Error as exc:
            raise RuntimeError("Cannot connect to PostgreSQL; check DATABASE_URL") from exc

    def initialize(self):
        dialect = "postgres" if self.postgres else "sqlite"
        migrations = files("question_categorizer").joinpath("migrations")
        sql = "\n".join(
            path.read_text()
            for path in sorted(migrations.iterdir(), key=lambda path: path.name)
            if path.name.endswith(f"_{dialect}.sql")
        )
        if self.postgres:
            with self.connection.transaction():
                self.connection.execute(sql)
        else:
            self.connection.executescript(sql)

    def _insert(self, table: str, values: dict, *, conflict: tuple[str, ...] | None = None):
        columns = ", ".join(values)
        placeholders = ", ".join(self.placeholder for _ in values)
        sql = f"INSERT INTO {self.prefix}{table} ({columns}) VALUES ({placeholders})"
        if conflict:
            keys = ", ".join(conflict)
            updates = ", ".join(
                f"{column} = excluded.{column}" for column in values if column not in conflict
            )
            sql += f" ON CONFLICT ({keys}) DO UPDATE SET {updates}"
        self.connection.execute(sql, tuple(values.values()))

    def seed_taxonomy(self, taxonomy: Taxonomy):
        version_id = uuid5(NAMESPACE_URL, f"asean-academy:syllabus:{taxonomy.version}")
        transaction = self.connection.transaction() if self.postgres else self.connection
        with transaction:
            self._insert(
                "syllabus_versions",
                {
                    "id": str(version_id),
                    "version_key": taxonomy.version,
                    "title": taxonomy.title,
                    "status": taxonomy.status,
                    "source_reference": taxonomy.source_reference,
                    "created_at": datetime.now(UTC).isoformat(),
                },
                conflict=("id",),
            )
            for topic in taxonomy.topics:
                self._insert(
                    "syllabus_topics",
                    {
                        "id": str(topic.id),
                        "syllabus_version_id": str(version_id),
                        "code": topic.code,
                        "strand": topic.strand,
                        "name": topic.name,
                        "sort_order": topic.order,
                    },
                    conflict=("id",),
                )
            for outcome in taxonomy.outcomes:
                self._insert(
                    "syllabus_outcomes",
                    {
                        "id": str(outcome.id),
                        "topic_id": str(outcome.topic_id),
                        "level": outcome.level,
                        "outcome_code": outcome.code,
                        "description": outcome.description,
                        "sort_order": outcome.order,
                    },
                    conflict=("id",),
                )

    def save(self, result: CategorizationResult, taxonomy: Taxonomy):
        self.seed_taxonomy(taxonomy)
        result = CategorizationResult.model_validate(result.model_dump())
        now = datetime.now(UTC).isoformat()
        transaction = self.connection.transaction() if self.postgres else self.connection
        with transaction:
            self._insert(
                "categorization_runs",
                {
                    "id": str(result.run_id),
                    "document_id": str(result.document_id),
                    "extraction_run_key": result.extraction_run_key,
                    "taxonomy_version": result.taxonomy_version,
                    "classifier_version": result.classifier_version,
                    "input_path": result.input_path,
                    "input_sha256": result.input_sha256,
                    "source_level": result.source_level,
                    "created_at": result.created_at,
                    "payload": result.model_dump_json(),
                },
                conflict=("id",),
            )
            self.connection.execute(
                f"DELETE FROM {self.prefix}question_topics "
                f"WHERE run_id = {self.placeholder} AND status = 'suggested'",
                (str(result.run_id),),
            )
            for question in result.questions:
                self._insert(
                    "question_categorizations",
                    {
                        "run_id": str(result.run_id),
                        "question_id": str(question.question_id),
                        "question_number": question.question_number,
                        "status": question.status,
                        "primary_topic_code": question.primary_topic_code,
                        "review_reasons": json.dumps(question.review_reasons),
                        "payload": question.model_dump_json(),
                    },
                    conflict=("run_id", "question_id"),
                )
                for part in question.parts:
                    self._insert(
                        "question_parts",
                        {
                            "run_id": str(result.run_id),
                            "id": str(part.id),
                            "question_id": str(question.question_id),
                            "part_label": part.label,
                            "part_order": part.order,
                            "checked_text": part.content,
                            "checked_latex": part.latex,
                            "source_fingerprint": part.source_fingerprint,
                            "input_status": part.input_status,
                            "classification_status": part.classification_status,
                            "review_reasons": json.dumps(part.review_reasons),
                        },
                        conflict=("run_id", "id"),
                    )
                    for assignment in part.assignments:
                        existing = self.connection.execute(
                            f"SELECT status FROM {self.prefix}question_topics "
                            f"WHERE id = {self.placeholder}",
                            (str(assignment.id),),
                        ).fetchone()
                        if existing and existing[0] in {"confirmed", "rejected"}:
                            continue
                        self._insert(
                            "question_topics",
                            {
                                "id": str(assignment.id),
                                "run_id": str(result.run_id),
                                "question_id": str(question.question_id),
                                "question_part_id": str(part.id),
                                "topic_id": str(assignment.topic_id),
                                "outcome_id": str(assignment.outcome_id)
                                if assignment.outcome_id
                                else None,
                                "role": assignment.role,
                                "status": assignment.status,
                                "confidence": assignment.confidence,
                                "source": assignment.source,
                                "classifier_version": result.classifier_version,
                                "taxonomy_version": result.taxonomy_version,
                                "evidence": json.dumps(
                                    [entry.model_dump(mode="json") for entry in assignment.evidence]
                                ),
                                "reviewed_by": None,
                                "reviewed_at": None,
                                "created_at": now,
                            },
                        )

    def review_assignment(self, assignment_id: str, reviewer: str, decision: str):
        if not reviewer.strip():
            raise ValueError("Reviewer is required")
        if decision not in {"confirmed", "rejected"}:
            raise ValueError("Decision must be confirmed or rejected")
        cursor = self.connection.execute(
            f"UPDATE {self.prefix}question_topics "
            f"SET status = {self.placeholder}, source = 'human', "
            f"reviewed_by = {self.placeholder}, "
            f"reviewed_at = {self.placeholder} WHERE id = {self.placeholder}",
            (decision, reviewer.strip(), datetime.now(UTC).isoformat(), assignment_id),
        )
        self.connection.commit()
        if cursor.rowcount != 1:
            raise ValueError("Assignment not found")

    def confirm(self, assignment_id: str, reviewer: str):
        self.review_assignment(assignment_id, reviewer, "confirmed")

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
