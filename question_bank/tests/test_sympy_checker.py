import json
import time

import pytest

from question_bank.checking import check_answer
from question_bank.course_models import ActiveRecallSection, Lesson
from question_bank.models import AlgebraicResponse, Question
from question_bank.sympy_checker import (
    MAX_INPUT_LENGTH,
    AnswerFormatError,
    check_symbolic_equivalence,
    run_with_timeout,
)

SEC2_N5 = "backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions"
SEC2_N5_LESSONS = "backend_resources/courses/g3_math/secondary_2/g2/v1/lessons"


def n5_spec(repository_root, key: str, part: int = 1):
    path = repository_root / SEC2_N5 / f"{key}.json"
    question = Question.model_validate_json(path.read_text())
    return question.parts[part - 1].response


def recall_spec(repository_root, lesson_number: int):
    path = repository_root / SEC2_N5_LESSONS / f"n5-lesson-{lesson_number:02d}.json"
    lesson = Lesson.model_validate_json(path.read_text())
    return next(s for s in lesson.sections if isinstance(s, ActiveRecallSection)).response


def symbolic(canonical, variables, *, constraints=(), config=None, accepted=()):
    return AlgebraicResponse(
        type="algebraic_expression",
        comparison_mode="symbolic_equivalence",
        canonical_expression=canonical,
        canonical_latex=canonical,
        variables=list(variables),
        domain_constraints=list(constraints),
        accepted_equivalents=list(accepted),
        checker_config=config or {},
    )


def accepted(spec, answer) -> bool:
    result = check_answer(spec, answer)
    return result["correct"]


# --- Reproduced audit failures (PRE_REVIEW_AUDIT_secondary_2_n5, C-1) -----------------------


def test_n5_l1_505_accepts_implicit_multiplication(repository_root):
    spec = n5_spec(repository_root, "n5-l1-505")
    assert spec.canonical_expression == "3*x+6"
    for answer in ["3x+6", "3x + 6", "6+3x", "3(x+2)", "3*x+6"]:
        assert accepted(spec, answer), answer
    assert not accepted(spec, "3x+7")


def test_n5_l1_509_accepts_factors_in_either_order(repository_root):
    spec = n5_spec(repository_root, "n5-l1-509")
    for answer in ["(x+6)(x+4)", "(x+4)(x+6)", "(x+6)*(x+4)", "(x + 4)·(x + 6)"]:
        assert accepted(spec, answer), answer
    assert not accepted(spec, "(x+6)(x-4)")


def test_n5_l2_506_accepts_plain_quotient(repository_root):
    spec = n5_spec(repository_root, "n5-l2-506")
    assert spec.canonical_expression == "(y)/(x)"
    for answer in ["y/x", "y÷x", "(y)/(x)"]:
        assert accepted(spec, answer), answer
    assert not accepted(spec, "x/y")


def test_n5_lesson_12_active_recall_accepts_displayed_factorisation(repository_root):
    spec = recall_spec(repository_root, 12)
    for answer in ["(x-8)(x+8)", "(x+8)(x−8)"]:
        assert accepted(spec, answer), answer
    assert not accepted(spec, "(x-8)(x-8)")


def test_other_audit_examples_are_accepted(repository_root):
    assert accepted(n5_spec(repository_root, "n5-l1-502"), "x²+6x+9")
    assert accepted(n5_spec(repository_root, "n5-l1-502"), "x^2 + 6x + 9")
    assert accepted(n5_spec(repository_root, "n5-l4-504"), "6x^2+9xy-15y^2")
    assert accepted(n5_spec(repository_root, "n5-l1-506"), "x=(y-2)/6")
    assert accepted(n5_spec(repository_root, "n5-l3-512"), "4(x+1)(x+4)")
    assert accepted(recall_spec(repository_root, 13), "(p+q)(x+2y)")
    assert accepted(recall_spec(repository_root, 14), "(x-2)(x-3)")
    assert accepted(recall_spec(repository_root, 15), "3/(2a)")


def test_every_authored_symbolic_canonical_checks_against_itself(repository_root):
    roots = [
        repository_root / "backend_resources/question_bank",
        repository_root / "backend_resources/courses",
    ]
    checked = 0

    def visit(node, path):
        nonlocal checked
        if isinstance(node, dict):
            if (
                node.get("type") == "algebraic_expression"
                and node.get("comparison_mode") == "symbolic_equivalence"
            ):
                spec = AlgebraicResponse.model_validate(node)
                result = check_answer(spec, spec.canonical_expression)
                assert result["correct"], (str(path), spec.canonical_expression, result)
                checked += 1
            for value in node.values():
                visit(value, path)
        elif isinstance(node, list):
            for value in node:
                visit(value, path)

    for root in roots:
        for path in root.rglob("*.json"):
            visit(json.loads(path.read_text()), path)
    assert checked > 200


# --- Parser -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "answer",
    [
        "a^2b",
        "a²b",
        "a**2*b",
        "b·a^2",
        "(a)(a)(b)",
        "[a^2][b]",
    ],
)
def test_implicit_multiplication_and_powers(answer):
    assert accepted(symbolic("a^2*b", "ab"), answer)


def test_unicode_minus_and_operators():
    spec = symbolic("(4*P+5)/(3-P)", ["P", "q"], constraints=["P != 3"])
    assert accepted(spec, "(4P+5)/(3−P)")
    assert accepted(spec, "−(4P+5)/(P−3)")
    assert accepted(spec, "(4P + 5) ÷ (3 – P)")
    assert accepted(symbolic("6*x", "x"), "2×3x")


def test_decimals_and_negative_powers():
    assert accepted(symbolic("0.05*m-7", "m"), "m/20 - 7")
    assert accepted(symbolic("y/x", "xy"), "yx^-1")
    assert accepted(symbolic("y/x", "xy"), "yx⁻¹")


def test_letters_that_are_sympy_names_stay_plain_variables():
    spec = symbolic("E+I+S+N+Q", ["E", "I", "S", "N", "Q"])
    assert accepted(spec, "Q+N+S+I+E")
    assert not accepted(spec, "Q+N+S+I")


def test_multi_letter_variables_are_matched_before_single_letters():
    spec = symbolic("2*ab+c", ["ab", "c"])
    assert accepted(spec, "c+2ab")


@pytest.mark.parametrize(
    "answer, message",
    [
        ("3y+6", "Use only x"),
        ("__import__('os').system('true')", "cannot be used"),
        ("x.real", "cannot be used"),
        ("lambda: 1", "Use only x"),
        ("sqrt(x)", "Use only x"),
        ("3x+6=0", "not an equation"),
        ("(3x+6", "not closed"),
        ("3x+6)", "closing bracket"),
        ("3x+", "ends unexpectedly"),
        ("x3", "multiplication sign"),
        ("x^x", "whole numbers"),
        ("x^0.5", "whole numbers"),
        ("()", "empty pair of brackets"),
    ],
)
def test_unsafe_or_malformed_input_is_rejected_with_a_message(answer, message):
    result = check_answer(symbolic("3*x+6", "x"), answer)
    assert result["correct"] is False
    assert message in result["error"]


def test_input_length_limit():
    spec = symbolic("x", "x")
    result = check_answer(spec, "x" + "+0" * MAX_INPUT_LENGTH)
    assert result["correct"] is False
    assert "too long" in result["error"]


def test_power_and_size_limits():
    spec = symbolic("x", "x")
    assert "Powers larger than" in check_answer(spec, "(x+1)^99")["error"]
    assert "too complicated" in check_answer(spec, "x^12^12")["error"]
    assert "too many digits" in check_answer(spec, "x+10000000000000")["error"]


def test_timeout_is_enforced():
    with pytest.raises(AnswerFormatError, match="too long to check"):
        run_with_timeout(time.sleep, 0.5, timeout=0.05)


def test_subject_prefix_only_for_variable_absent_from_answer():
    spec = symbolic("(y-2)/6", "xy")
    assert accepted(spec, "x = (y-2)/6")
    result = check_answer(spec, "y = (y-2)/6")
    assert "not an equation" in result["error"]


def test_accepted_equivalents_still_bypass_the_parser():
    spec = symbolic("3*x+6", "x", accepted=["3 lots of (x+2)"])
    assert accepted(spec, "3 lots of (x+2)")


# --- Domain constraints ---------------------------------------------------------------------


def test_domain_constraints_are_respected():
    spec = symbolic("(1-3*y)/(2*y-4)", "xy", constraints=["2*y-4 != 0"])
    assert accepted(spec, "(3y-1)/(4-2y)")
    assert not accepted(spec, "(3y-1)/(2y-4)")


def test_domain_constraints_select_sample_points():
    # Every sample point must satisfy the constraint; the checker should still decide.
    spec = symbolic("x", "x", constraints=["x > 0", "x < 1"])
    assert accepted(spec, "x^2/x")
    assert not accepted(spec, "x^2")


def test_answer_undefined_inside_the_domain_is_rejected():
    assert not check_symbolic_equivalence("x/0", canonical="x", variables=["x"])
    assert not accepted(symbolic("x", "x"), "x+1/0")


def test_invalid_constraints_and_canonicals_fail_validation():
    with pytest.raises(ValueError, match="Use only x"):
        symbolic("3*x+6", "x", constraints=["y != 0"])
    with pytest.raises(ValueError, match="Use only x"):
        symbolic("3*x+6*y", "x")
    with pytest.raises(ValueError, match="must have the form"):
        symbolic("x", "x", constraints=["x"])


# --- Form rules -----------------------------------------------------------------------------


def test_factorised_form_rejects_unfactorised_input():
    spec = symbolic("(x+6)*(x+4)", "x", config={"form": "factorised"})
    assert accepted(spec, "(x+4)(x+6)")
    assert accepted(spec, "-(-x-6)(x+4)")
    for answer in ["x^2+10x+24", "x²+10x+24", "(x^2+10x+24)", "(x+4)(x+6)+0"]:
        result = check_answer(spec, answer)
        assert result["correct"] is False, answer
        assert "not factorised" in result["error"], answer


def test_factorised_form_requires_coprime_integer_bracket_coefficients():
    spec = symbolic("4*(x+1)*(x+4)", "x", config={"form": "factorised"})
    assert accepted(spec, "4(x+1)(x+4)")
    assert accepted(spec, "(x+4)·4·(x+1)")
    for answer in ["(2x+2)(2x+8)", "(4x+4)(x+4)", "2(x+1)(2x+8)"]:
        result = check_answer(spec, answer)
        assert result["correct"] is False, answer
        assert "common factor" in result["error"], answer
    result = check_answer(spec, "4(x^2+5x+4)")
    assert "can still be factorised" in result["error"]
    result = check_answer(spec, "8(x/2+1/2)(x+4)")
    assert "whole-number coefficients" in result["error"]


def test_factorised_form_with_several_variables_and_powers():
    spec = symbolic("(p-q)*(4+7*x)", "pqx", config={"form": "factorised"})
    assert accepted(spec, "(4+7x)(p-q)")
    assert not accepted(spec, "4p-4q+7px-7qx")
    square = symbolic("45*(x+1)^2", "x", config={"form": "factorised"})
    assert accepted(square, "45(x+1)²")
    assert accepted(square, "45(x+1)(x+1)")
    assert not accepted(square, "5(3x+3)(3x+3)")
    difference = symbolic("(x-8)*(x+8)", "x", config={"form": "factorised"})
    assert not accepted(difference, "x^2-64")
    assert accepted(difference, "(8+x)(x-8)")


def test_factorised_canonical_that_is_not_complete_fails_its_own_check():
    # The authoring validators run check_answer on canonicals, so this is caught at import.
    spec = symbolic("(2*x+2)*(2*x+8)", "x", config={"form": "factorised"})
    assert not accepted(spec, spec.canonical_expression)


def test_simplified_form_rejects_the_original_expression():
    spec = symbolic(
        "2*q-2",
        "qx",
        config={"form": "simplified", "original_expression": "(4*q-4)/2"},
    )
    assert accepted(spec, "2q-2")
    assert accepted(spec, "2(q-1)")
    assert accepted(spec, "x = 2q - 2")
    for answer in ["(4q-4)/2", "(-4 + 4q)/2", "((4q)-(4))/(2)"]:
        result = check_answer(spec, answer)
        assert result["correct"] is False, answer
        assert "expression you started with" in result["error"], answer


def test_checker_config_is_validated():
    with pytest.raises(ValueError, match="form must be one of"):
        symbolic("x", "x", config={"form": "expanded"})
    with pytest.raises(ValueError, match="requires checker_config.original_expression"):
        symbolic("x", "x", config={"form": "simplified"})
    with pytest.raises(ValueError, match="Unknown symbolic checker_config keys"):
        symbolic("x", "x", config={"forms": "factorised"})
    with pytest.raises(ValueError, match="Use only x"):
        symbolic("x", "x", config={"form": "simplified", "original_expression": "2y"})
