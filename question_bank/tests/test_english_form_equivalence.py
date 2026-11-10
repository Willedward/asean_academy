import json
from pathlib import Path

import pytest

from question_bank.cli import main
from question_bank.english_form_equivalence import (
    estimate_syllables,
    form_equivalence_report,
    render_markdown,
)

ENGLISH_ROOT = Path(__file__).resolve().parents[2] / "backend_resources/english/v1"


@pytest.fixture(scope="module")
def report():
    return form_equivalence_report(ENGLISH_ROOT)


def test_report_covers_the_three_diagnostic_forms_in_order(report):
    assert [form["form_type"] for form in report["forms"]] == [
        "baseline",
        "endline",
        "endline_reserve",
    ]
    for form in report["forms"]:
        assert form["structure"]["parts"] == 43
        assert form["structure"]["matches_declared_distribution"]
        assert form["vocabulary"]["targets"] == 15
        assert form["cloze_answers"]["targets"] == 16
        reading = [p["words"] for p in form["passages"]["items"] if p["task"] == "reading_comprehension"]
        assert len(reading) == 2 and all(300 <= words <= 450 for words in reading)
        assert sum(form["keys"]["single_choice"].values()) == form["options"]["single_choice_parts"]
    assert report["corpus_documents"] > 1000


def test_report_excludes_the_forms_own_files_from_the_frequency_corpus(report):
    # "noncommittal" is tested in the baseline and used nowhere else, so if the form's own
    # files were counted it would show at least one document.
    rarest = {row["target"]: row["documents"] for row in report["forms"][0]["vocabulary"]["rarest"]}
    assert rarest.get("noncommittal") == 0


def test_flags_name_differences_without_failing(report):
    assert isinstance(report["flags"], list)
    assert not any("different part counts" in flag for flag in report["flags"])


def test_markdown_and_cli_render_every_section(report, tmp_path, capsys):
    markdown = render_markdown(report)
    for heading in ("## Structure", "## Passages", "## Options", "## Key positions",
                    "## Vocabulary proxy", "## Flags"):
        assert heading in markdown

    assert main(["english-form-equivalence", str(ENGLISH_ROOT)]) == 0
    assert "# English diagnostic form equivalence" in capsys.readouterr().out
    output = tmp_path / "equivalence.json"
    assert main(["english-form-equivalence", str(ENGLISH_ROOT), "--format", "json",
                 "--output", str(output)]) == 0
    assert len(json.loads(output.read_text())["forms"]) == 3


@pytest.mark.parametrize(
    ("word", "syllables"),
    [("cat", 1), ("orderly", 3), ("make", 1), ("judicious", 3), ("adapted", 3), ("table", 2)],
)
def test_syllable_estimate_is_close_enough_for_a_proxy(word, syllables):
    assert estimate_syllables(word) == syllables
