"""Validation of symbolic_equivalence parts that ask for a form but do not set one."""

import json
import shutil

import pytest

from question_bank.authoring import validate_batch
from question_bank.course_validation import validate_course
from question_bank.models import AlgebraicResponse, InlineMathBlock, NumericResponse, TextBlock
from question_bank.validation import SYMBOLIC_FORM_MISSING, missing_symbolic_form, validate_bank

N5_BANK = "backend_resources/question_bank/g3_math/secondary_1/n5/v1"
SYLLABUS = "backend_resources/syllabi/g3_math/v1/catalogue.json"
SECONDARY_1_COURSE = "backend_resources/courses/g3_math/secondary_1/n1/v1"


def symbolic(config=None, mode="symbolic_equivalence"):
    return AlgebraicResponse(
        type="algebraic_expression",
        comparison_mode=mode,
        canonical_expression="2:3" if mode == "exact_ratio" else "3x+12",
        canonical_latex="3x+12",
        variables=["x"],
        domain_constraints=[],
        accepted_equivalents=[],
        checker_config={} if config is None else config,
    )


def text(value):
    return [TextBlock(type="text", text=value)]


def flagged(report, severity):
    issues = report.errors if severity == "error" else report.warnings
    return {issue.path for issue in issues if issue.code == SYMBOLIC_FORM_MISSING}


@pytest.mark.parametrize(
    ("prompt", "verb"),
    [
        ("Simplify 3x + 5x.", "simplify"),
        ("Amber warm-up: Expand and simplify 3(x+2).", "expand"),
        ("Factorise 6x + 12 completely.", "factorise"),
        ("Factorize x^2 - 64.", "factorise"),
        ("Write the square of 2xy in index notation and simplify the numerical factor.", "simplify"),
        ("Simplify 5x + 10y - 2x - 4y, then factorise completely.", "simplify"),
    ],
)
def test_form_tasks_without_a_form_are_detected(prompt, verb):
    assert missing_symbolic_form(text(prompt), symbolic()) == verb


@pytest.mark.parametrize(
    ("prompt", "response"),
    [
        ("Simplify 3(x + 4).", symbolic({"form": "expanded"})),
        ("Simplify 3(x + 4).", symbolic({"form": "any"})),
        ("Given y = 6x + 2, make x the subject.", symbolic()),
        ("Write the cost of 6 exercise books.", symbolic()),
        (
            "Simplify 6:9.",
            symbolic({"terms": 2, "require_simplest_integer_terms": True}, "exact_ratio"),
        ),
        (
            "Simplify 3/4 + 1/4.",
            NumericResponse(
                type="numeric",
                comparison_mode="exact_numeric",
                canonical_answer="1",
                canonical_latex="1",
            ),
        ),
    ],
)
def test_set_forms_other_modes_and_other_tasks_are_not_flagged(prompt, response):
    assert missing_symbolic_form(text(prompt), response) is None


def test_only_prompt_text_is_read_for_the_task():
    prompt = [InlineMathBlock(type="inline_math", latex=r"\text{simplify}")]
    assert missing_symbolic_form(prompt, symbolic()) is None


def bank_without_forms(repository_root, root, *question_keys):
    """Copy the N5 bank and clear the form on these items, so each test sets its own state."""

    bank_root = root / "question_bank/g3_math/secondary_1/n5/v1"
    shutil.copytree(repository_root / N5_BANK, bank_root)
    shutil.copytree(
        repository_root / "backend_resources/question_bank/schema",
        root / "question_bank/schema",
    )
    for question_key in question_keys:
        question_path = bank_root / f"questions/{question_key}.json"
        question = json.loads(question_path.read_text())
        question["parts"][0]["response"]["checker_config"] = {}
        question_path.write_text(json.dumps(question))
    return bank_root


def test_bank_warns_for_drafts_and_blocks_publication(repository_root, tmp_path):
    bank_root = bank_without_forms(repository_root, tmp_path, "n5-l1-016")
    catalogue = repository_root / SYLLABUS
    draft = validate_bank(bank_root, catalogue_path=catalogue)
    assert draft.valid
    warned = flagged(draft, "warning")
    assert any(path.endswith("n5-l1-016.json") for path in warned)
    assert not any(path.endswith("n5-l1-001.json") for path in warned)

    publish = validate_bank(bank_root, catalogue_path=catalogue, publish=True)
    assert flagged(publish, "error") == warned
    assert not flagged(publish, "warning")


def test_setting_a_form_clears_the_issue(repository_root, tmp_path):
    bank_root = bank_without_forms(repository_root, tmp_path, "n5-l1-015", "n5-l1-016")
    question_path = bank_root / "questions/n5-l1-016.json"
    question = json.loads(question_path.read_text())
    question["parts"][0]["response"]["checker_config"] = {"form": "expanded"}
    question_path.write_text(json.dumps(question))

    report = validate_bank(bank_root, catalogue_path=repository_root / SYLLABUS)

    assert report.valid
    assert not any(path.endswith("n5-l1-016.json") for path in flagged(report, "warning"))
    assert any(path.endswith("n5-l1-015.json") for path in flagged(report, "warning"))


def test_lesson_recall_warns_for_drafts_and_blocks_publication(
    repository_root, course_bank_root, tmp_path
):
    course_root = tmp_path / "course"
    shutil.copytree(repository_root / SECONDARY_1_COURSE, course_root)
    # The committed recalls set their forms; strip them to check that a missing form is caught.
    for key in ("n5-lesson-06", "n5-lesson-07", "n5-lesson-08"):
        lesson_path = course_root / "lessons" / f"{key}.json"
        lesson = json.loads(lesson_path.read_text())
        for section in lesson["sections"]:
            if section["type"] == "active_recall":
                section["response"]["checker_config"] = {}
        lesson_path.write_text(json.dumps(lesson))
    draft = validate_course(course_root, course_bank_root)
    assert draft.valid
    warned = flagged(draft, "warning")
    assert {path.rsplit("/", 1)[-1] for path in warned} == {
        "n5-lesson-06.json",
        "n5-lesson-07.json",
        "n5-lesson-08.json",
    }

    publish = validate_course(course_root, course_bank_root, publish=True)
    assert warned <= flagged(publish, "error")


@pytest.mark.parametrize(("status", "severity"), [("ready_for_review", "warning"), ("approved", "error")])
def test_batch_validation_blocks_only_approved_batches(repository_root, tmp_path, status, severity):
    isolated_root = tmp_path / "repository"
    bank_root = isolated_root / N5_BANK
    shutil.copytree(repository_root / N5_BANK, bank_root)
    question_path = bank_root / "questions/n5-l1-016.json"
    question = json.loads(question_path.read_text())
    question["parts"][0]["response"]["checker_config"] = {}
    question_path.write_text(json.dumps(question))
    manifest_path = next(
        path
        for path in sorted((bank_root / "batches").glob("*.json"))
        if "n5-l1-016" in json.loads(path.read_text())["question_keys"]
    )
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = status
    if status == "approved":
        manifest["review"].update({"mathematics": "approved", "editorial": "approved"})
    manifest_path.write_text(json.dumps(manifest))
    for reference in manifest["source_references"]:
        target = isolated_root / reference["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.symlink_to(repository_root / reference["path"])

    report = validate_batch(
        manifest_path, repository_root=isolated_root, syllabus_path=repository_root / SYLLABUS
    )

    assert report.valid is (severity == "warning")
    assert any(path.endswith("n5-l1-016.json") for path in flagged(report, severity))
