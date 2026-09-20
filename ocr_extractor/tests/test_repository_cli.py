import json
import sqlite3

import pytest

from ocr_extractor.cli import main
from ocr_extractor.repository import Repository


def test_repository_persists_all_evidence_and_is_idempotent(service, normal_pdf, tmp_path):
    result = service.extract_file(normal_pdf)
    with Repository.sqlite(tmp_path / "questions.sqlite3") as repository:
        repository.save(result)
        repository.save(result)
        connection = repository.connection
        for table, count in [
            ("source_documents", 1),
            ("source_pages", 2),
            ("questions", 2),
            ("question_assets", 4),
            ("answer_keys", 2),
        ]:
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == count
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        record = connection.execute("SELECT payload FROM source_documents").fetchone()[0]
        assert json.loads(record) == result.model_dump(mode="json")


def test_failed_save_rolls_back_previous_rows(service, normal_pdf, monkeypatch):
    result = service.extract_file(normal_pdf)
    with Repository.sqlite(":memory:") as repository:
        repository.save(result)
        before = repository.connection.execute("SELECT * FROM questions").fetchall()
        insert = repository._insert

        def fail_on_question(table, *args, **kwargs):
            if table == "questions":
                raise sqlite3.IntegrityError("Simulated write failure")
            return insert(table, *args, **kwargs)

        monkeypatch.setattr(repository, "_insert", fail_on_question)
        with pytest.raises(sqlite3.IntegrityError):
            repository.save(result)
        assert repository.connection.execute("SELECT * FROM questions").fetchall() == before
        assert repository.connection.execute("SELECT count(*) FROM answer_keys").fetchone()[0] == 2


def test_cli_directory_continues_after_invalid_pdf(normal_pdf, tmp_path, capsys):
    (tmp_path / "broken.PDF").write_bytes(b"bad")
    output = tmp_path / "output"
    args = ["extract", str(tmp_path), "--output", str(output), "--ocr", "off", "--dpi", "100"]
    assert main(args) == 1
    report = json.loads((output / "batch-report.json").read_text())
    assert len(report["files"]) == 2
    assert {row["status"] for row in report["files"]} == {"complete", "failed"}
    assert main(args) == 1  # exclude generated original.pdf when output is inside the input tree
    assert len(json.loads((output / "batch-report.json").read_text())["files"]) == 2
    with sqlite3.connect(output / "questions.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM questions").fetchone()[0] == 2
    capsys.readouterr()


def test_empty_folder_and_missing_api_configuration(tmp_path, monkeypatch, capsys):
    assert main(["extract", str(tmp_path)]) == 2
    assert "No PDFs found" in capsys.readouterr().err
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert main(["init-db", "--postgres"]) == 2
    assert "DATABASE_URL" in capsys.readouterr().err


def test_json_only_does_not_create_database(normal_pdf, tmp_path, capsys):
    output = tmp_path / "out"
    assert (
        main(
            [
                "extract",
                str(normal_pdf),
                "--json-only",
                "--output",
                str(output),
                "--ocr",
                "off",
                "--dpi",
                "100",
            ]
        )
        == 0
    )
    assert list(output.rglob("questions.json"))
    assert not list(output.rglob("*.sqlite3"))
    assert "questions" in capsys.readouterr().out
