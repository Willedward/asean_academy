import json

from conftest import question

from question_categorizer.cli import main
from question_categorizer.repository import Repository
from question_categorizer.service import CategorizationService


def test_repository_persists_taxonomy_parts_and_preserves_confirmation(tmp_path, export_factory):
    path, _, _ = export_factory([question(1, "Express as a single algebraic fraction.")])
    service = CategorizationService()
    result = service.categorize_file(path, source_level="secondary_2")
    database = tmp_path / "categorization.sqlite3"
    assignment_id = str(result.questions[0].parts[0].assignments[0].id)

    with Repository.sqlite(database) as repository:
        repository.save(result, service.taxonomy)
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM syllabus_topics").fetchone()[0]
            == 13
        )
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM syllabus_outcomes").fetchone()[0]
            == 87
        )
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM question_parts").fetchone()[0] == 1
        )
        repository.confirm(assignment_id, "founder")
        repository.save(result, service.taxonomy)
        row = repository.connection.execute(
            "SELECT status, source, reviewed_by FROM question_topics WHERE id = ?",
            (assignment_id,),
        ).fetchone()
        assert row == ("confirmed", "human", "founder")


def test_assignment_can_be_rejected(tmp_path, export_factory):
    path, _, _ = export_factory([question(1, "Find the probability of one event.")])
    service = CategorizationService()
    result = service.categorize_file(path)
    assignment_id = str(result.questions[0].parts[0].assignments[0].id)
    with Repository.sqlite(tmp_path / "review.sqlite3") as repository:
        repository.save(result, service.taxonomy)
        repository.review_assignment(assignment_id, "founder", "rejected")
        assert (
            repository.connection.execute(
                "SELECT status FROM question_topics WHERE id = ?", (assignment_id,)
            ).fetchone()[0]
            == "rejected"
        )


def test_cli_writes_json_without_database(tmp_path, export_factory, capsys):
    path, _, _ = export_factory([question(1, "Find the probability of a single event.")])
    output = tmp_path / "result.json"
    assert main(["categorize", str(path), "--output", str(output), "--json-only"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "complete"
    assert report["classified"] == 1
    assert json.loads(output.read_text())["taxonomy_version"] == "g3_math_v1_draft"
