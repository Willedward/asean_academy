"""Fixture tests for the content guardrails in ``question_bank.content_lint``.

Each check has at least one failing fixture (the defect the pre-review audits found) and a
passing fixture (the corrected form).  The fixtures live in ``tests/fixtures/content_lint``.
"""

import json
import shutil
from pathlib import Path

import pytest

from question_bank.collaboration import _content_guardrail_summary
from question_bank.content_lint import (
    CHECKS,
    CONTENT_LINT_CODES,
    ContentLintPolicy,
    is_content_lint_code,
    latex_to_plain,
    lesson_math_items,
    lint_lesson,
    lint_question,
    load_policy,
    math_duplicate_findings,
    parse_value,
    question_math_items,
)
from question_bank.course_models import Lesson
from question_bank.models import Question
from question_bank.validation import Issue, validate_bank

FIXTURES = Path(__file__).parent / "fixtures" / "content_lint"


def _question(name: str) -> Question:
    return Question.model_validate_json((FIXTURES / "questions" / f"{name}.json").read_text())


def _lesson(name: str) -> Lesson:
    return Lesson.model_validate_json((FIXTURES / "lessons" / f"{name}.json").read_text())


def _codes(findings) -> list[str]:
    return [finding.code for finding in findings]


def test_every_check_has_a_failing_and_a_passing_fixture():
    names = {path.stem for path in (FIXTURES / "questions").glob("*.json")}
    names |= {f"lesson-{path.stem}" for path in (FIXTURES / "lessons").glob("*.json")}
    expected_prefix = {
        "content_control_character": "control-character",
        "content_float_noise": "float-noise",
        "content_math_duplicate": "math-duplicate",
        "content_plain_text_math": "plain-text-math",
        "content_prompt_without_question": "prompt-without-question",
        "content_hint_reveals_answer": "hint-reveals-answer",
        "content_answer_solution_mismatch": "answer-solution-mismatch",
    }
    assert set(expected_prefix) == set(CHECKS)
    for prefix in expected_prefix.values():
        assert any(name.startswith(prefix) and name.endswith("fail") for name in names), prefix
        assert any(name.startswith(prefix) and name.endswith("pass") for name in names) or (
            "clean" in names
        ), prefix


def test_clean_fixtures_produce_no_findings():
    assert lint_question(_question("clean")) == []
    assert lint_lesson(_lesson("clean")) == []


@pytest.mark.parametrize(
    ("fixture", "code"),
    [
        ("control-character-fail", "content_control_character"),
        ("control-character-double-escape-fail", "content_control_character"),
        ("float-noise-fail", "content_float_noise"),
        ("float-noise-integer-as-float-fail", "content_float_noise"),
        ("plain-text-math-fail", "content_plain_text_math"),
        ("prompt-without-question-fail", "content_prompt_without_question"),
        ("hint-reveals-answer-fail", "content_hint_reveals_answer"),
        ("hint-reveals-answer-fraction-fail", "content_hint_reveals_answer"),
        ("hint-reveals-answer-expression-fail", "content_hint_reveals_answer"),
        ("answer-solution-mismatch-final-fail", "content_answer_solution_mismatch"),
        ("answer-solution-mismatch-substitution-fail", "content_answer_solution_mismatch"),
        ("answer-solution-mismatch-decision-fail", "content_answer_solution_mismatch"),
        ("answer-solution-mismatch-arithmetic-fail", "content_answer_solution_mismatch"),
    ],
)
def test_failing_question_fixture_is_reported(fixture, code):
    assert _codes(lint_question(_question(fixture))) == [code]


@pytest.mark.parametrize(
    "fixture",
    [
        "float-noise-pass",
        "plain-text-math-pass",
        "prompt-without-question-pass",
        "hint-reveals-answer-pass",
        "answer-solution-mismatch-pass",
        "math-duplicate-latex",
        "math-duplicate-plain-fail",
        "math-duplicate-plain-pass",
    ],
)
def test_passing_question_fixture_is_clean(fixture):
    assert lint_question(_question(fixture)) == []


def test_tab_message_names_the_swallowed_command():
    (finding,) = lint_question(_question("control-character-fail"))
    assert "TAB character before 'imes'" in finding.message
    assert "\\times" in finding.message
    assert finding.location.startswith("parts[0].solution[0]")


def test_float_noise_reports_the_canonical_answer():
    (finding,) = lint_question(_question("float-noise-fail"))
    assert "canonical_answer = '3.333333333333332'" in finding.message


def test_answer_solution_messages_explain_the_disagreement():
    (decision,) = lint_question(_question("answer-solution-mismatch-decision-fail"))
    assert "8209 with 7921" in decision.message
    assert "should be 0" in decision.message
    (substitution,) = lint_question(_question("answer-solution-mismatch-substitution-fail"))
    assert "h = 10 does not satisfy" in substitution.message
    (final,) = lint_question(_question("answer-solution-mismatch-final-fail"))
    assert "ends with '60'" in final.message


def test_math_duplicates_match_latex_and_plain_text_behind_different_contexts():
    latex = _question("math-duplicate-latex")
    plain = _question("math-duplicate-plain-fail")
    (finding,) = math_duplicate_findings(question_math_items(latex) + question_math_items(plain))
    assert finding.code == "content_math_duplicate"
    assert finding.subject == plain.stable_key
    assert latex.stable_key in finding.message

    different = _question("math-duplicate-plain-pass")
    assert math_duplicate_findings(question_math_items(latex) + question_math_items(different)) == []


def test_lesson_examples_are_compared_with_bank_questions_of_the_same_topic():
    question = _question("math-duplicate-latex")
    repeated = _lesson("math-duplicate-fail")
    (finding,) = math_duplicate_findings(
        question_math_items(question) + lesson_math_items(repeated)
    )
    assert finding.subject == repeated.stable_key
    assert "fraction-example" in finding.location

    clean = _lesson("clean")
    assert math_duplicate_findings(question_math_items(question) + lesson_math_items(clean)) == []


def test_code_selection_prompts_compare_their_scenario_not_the_code_numbers():
    base = json.loads((FIXTURES / "questions" / "clean.json").read_text())

    def coded(key, scenario):
        payload = json.loads(json.dumps(base))
        payload["stable_key"] = key
        payload["parts"][0]["prompt"] = [
            {
                "type": "text",
                "text": "Use code 1 for a table, 2 for a bar graph and 3 for a line graph. "
                f"{scenario} Enter the most suitable code only.",
            }
        ]
        payload["parts"][0]["response"]["canonical_answer"] = "3"
        payload["parts"][0]["response"]["canonical_latex"] = "3"
        return Question.model_validate(payload)

    first = coded("n1-l2-951", "A sensor reports pressure every minute.")
    same = coded("n1-l2-952", "A sensor reports pressure every minute.")
    other = coded("n1-l2-953", "A scientist tracks temperature through one day.")
    assert len(math_duplicate_findings(question_math_items(first) + question_math_items(same))) == 1
    assert math_duplicate_findings(question_math_items(first) + question_math_items(other)) == []


@pytest.mark.parametrize(
    ("fixture", "codes"),
    [
        ("control-and-plain-text-fail", ["content_control_character", "content_plain_text_math"]),
        ("prompt-without-question-fail", ["content_prompt_without_question"]),
    ],
)
def test_failing_lesson_fixture_is_reported(fixture, codes):
    assert _codes(lint_lesson(_lesson(fixture))) == codes


def test_latex_and_plain_text_normalise_to_the_same_value():
    assert parse_value("\\frac{7}{12}") == parse_value("7/12")
    assert parse_value("48\\,400") == 48400
    assert parse_value("84\\text{ cm}") == 84
    assert parse_value("100\\%") == 100
    assert latex_to_plain("180^\\circ-50^{\\circ}") == "180-50"


def test_policy_defaults_to_warnings_and_promotes_by_scope():
    policy = ContentLintPolicy.model_validate(
        {
            "checks": {
                "content_control_character": {"severity": "error"},
                "content_float_noise": {"error_scopes": ["g3-sec2-s1-v1"]},
                "content_plain_text_math": {"error_scopes": ["g3-sec1-n*"]},
            }
        }
    )
    assert policy.severity("content_control_character", ["anything"]) == "error"
    assert policy.severity("content_float_noise", ["g3-sec2-s1-v1", "s1-l4-507"]) == "error"
    assert policy.severity("content_float_noise", ["g3-sec1-n1-v1"]) == "warning"
    assert policy.severity("content_plain_text_math", ["g3-sec1-n5-v1"]) == "error"
    assert policy.severity("content_plain_text_math", ["g3-sec2-n5-v1"]) == "warning"
    assert policy.severity("content_hint_reveals_answer", ["g3-sec1-g1-v1"]) == "warning"


def test_policy_rejects_unknown_checks(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"checks": {"content_typo": {"severity": "error"}}}))
    with pytest.raises(ValueError, match="Unknown content-lint checks"):
        load_policy(path)


def test_committed_policy_is_valid_and_lists_every_check(monkeypatch):
    monkeypatch.delenv("QUESTION_BANK_CONTENT_LINT_POLICY", raising=False)
    policy = load_policy()
    assert set(policy.checks) == set(CONTENT_LINT_CODES)
    # Promotions are made by editing the policy; CI (authoring-validate and course-validate)
    # then proves that the promoted scope is clean.  See docs/plan/CONTENT_LINT_GUARDRAILS.md.


def test_is_content_lint_code_accepts_prefixed_course_codes():
    assert is_content_lint_code("content_float_noise")
    assert is_content_lint_code("question_bank_content_float_noise")
    assert not is_content_lint_code("asset_checksum")


def _bank_with_tab(repository_root: Path, tmp_path: Path) -> Path:
    source = repository_root / "backend_resources/question_bank/g3_math/secondary_1/n1/v1"
    bank = tmp_path / "question_bank/g3_math/secondary_1/n1/v1"
    shutil.copytree(source, bank, ignore=shutil.ignore_patterns("review_packets", "batches"))
    shutil.copytree(
        repository_root / "backend_resources/question_bank/schema",
        tmp_path / "question_bank/schema",
    )
    syllabus = tmp_path / "syllabi/g3_math/v1"
    syllabus.mkdir(parents=True)
    shutil.copy(
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json", syllabus
    )
    path = bank / "questions/n1-l1-016.json"
    payload = json.loads(path.read_text())
    payload["parts"][0]["hints"][0]["content"].append(
        # An unescaped "\t" in "\times" leaves a TAB followed by "imes".
        {"type": "inline_math", "latex": "2" + "\t" + "imes3"}
    )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return bank


def test_bank_validation_reports_content_findings_as_warnings(
    repository_root, tmp_path, monkeypatch
):
    monkeypatch.delenv("QUESTION_BANK_CONTENT_LINT_POLICY", raising=False)
    report = validate_bank(_bank_with_tab(repository_root, tmp_path))

    assert report.valid
    tabs = [issue for issue in report.warnings if issue.code == "content_control_character"]
    assert [Path(issue.path).stem for issue in tabs] == ["n1-l1-016"]
    assert report.as_dict()["content_lint_counts"]["content_control_character"] == 1


def test_policy_promotion_turns_a_bank_warning_into_an_error(
    repository_root, tmp_path, monkeypatch
):
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "checks": {"content_control_character": {"error_scopes": ["g3-sec1-n1-v1"]}},
            }
        )
    )
    monkeypatch.setenv("QUESTION_BANK_CONTENT_LINT_POLICY", str(policy))
    report = validate_bank(_bank_with_tab(repository_root, tmp_path))

    assert not report.valid
    assert [issue.code for issue in report.errors] == ["content_control_character"]


def test_invalid_policy_is_an_error_not_a_silent_downgrade(
    repository_root, tmp_path, monkeypatch
):
    monkeypatch.setenv("QUESTION_BANK_CONTENT_LINT_POLICY", str(tmp_path / "missing.json"))
    report = validate_bank(_bank_with_tab(repository_root, tmp_path))

    assert "content_lint_policy_invalid" in {issue.code for issue in report.errors}


def test_pull_request_summary_aggregates_catalogue_warnings():
    warnings = [
        Issue("warning", "content_float_noise", "bank/questions/s1-l4-507.json", "noise"),
        Issue("warning", "content_float_noise", "bank/questions/s1-l4-510.json", "noise"),
        Issue("warning", "content_plain_text_math", "bank/questions/n1-l1-016.json", "caret"),
    ]
    lines = _content_guardrail_summary(warnings, {"s1-l4-507"})

    assert "| `content_float_noise` (Floating-point noise in answers) | 1 | 2 |" in lines
    assert any(line.startswith("| `content_plain_text_math`") and "| 0 | 1 |" in line for line in lines)


def test_cross_topic_matches_with_two_numbers_need_a_shared_concept():
    from question_bank.content_lint import MathItem, math_signature
    from question_bank.models import TextBlock

    def item(key, topic, text, answer):
        response = _question("clean").parts[0].response.model_copy(
            update={"canonical_answer": answer, "canonical_latex": answer}
        )
        signature = math_signature([TextBlock(type="text", text=text)], response)
        return MathItem(key, "parts[0]", f"bank-{topic}", topic, signature, "question")

    rate = item("n4-l1-901", "n4", "Water flows at 12 litres per minute for 9 minutes. Find the volume.", "108")
    area = item("g5-l1-901", "g5", "A flag is 12 cm by 9 cm. Find its area.", "108")
    discount = item("n3-l1-901", "n3", "After a 20% discount a bag costs S$64. Find the original price.", "80")
    repeat = item("n7-l2-901", "n7", "A jacket costs S$64 after a 20% discount. Find the original price x.", "80")

    assert math_duplicate_findings([rate, area]) == []
    (finding,) = math_duplicate_findings([discount, repeat])
    assert finding.subject == "n7-l2-901"
