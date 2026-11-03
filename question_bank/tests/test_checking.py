import ast
import json
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from question_bank import checking
from question_bank.checking import MAX_ANSWER_LENGTH, check_answer
from question_bank.course_models import ActiveRecallSection, Lesson
from question_bank.models import (
    SYMBOLIC_FORMS,
    AlgebraicResponse,
    NumericResponse,
    Question,
    UnitSpec,
)
from question_bank.validation import validate_bank


def questions_by_key(bank_root):
    report = validate_bank(bank_root)
    return {question.stable_key: question for question in report.questions}


def test_exact_numeric_checker(bank_root):
    question = questions_by_key(bank_root)["n1-l1-02"]
    spec = question.parts[0].response

    assert check_answer(spec, "-14")["correct"]
    assert not check_answer(spec, "14")["correct"]


def test_prime_factorisation_requires_prime_bases(bank_root):
    question = questions_by_key(bank_root)["n1-l1-01"]
    spec = question.parts[0].response

    assert check_answer(spec, "5 * 3^2 * 2^3")["correct"]
    result = check_answer(spec, "360")
    assert not result["correct"]
    assert "prime" in result["error"].lower()


def test_significant_figures_checker_preserves_requested_precision(bank_root):
    question = questions_by_key(bank_root)["n1-l2-02"]
    spec = question.parts[0].response

    assert check_answer(spec, "0.00786")["correct"]
    assert not check_answer(spec, "0.007860")["correct"]


def test_significant_figures_treats_integer_placeholders_as_non_significant():
    from question_bank.models import NumericResponse

    spec = NumericResponse(
        type="numeric",
        comparison_mode="rounded_sf",
        canonical_answer="48400",
        canonical_latex="48400",
        accepted_answers=[],
        rounding_precision=3,
    )

    assert check_answer(spec, "48400")["correct"]
    assert check_answer(spec, "4.84e4")["correct"]


def test_ordered_list_accepts_equivalent_fractions(bank_root):
    question = questions_by_key(bank_root)["n1-l3-01"]
    spec = question.parts[0].response

    assert check_answer(spec, "-5/2, -1/2, 1, 5/2")["correct"]
    assert not check_answer(spec, "2.5, 1, -0.5, -2.5")["correct"]


def test_relation_accepts_reversed_equivalent(bank_root):
    question = questions_by_key(bank_root)["n1-l3-01"]
    spec = question.parts[1].response

    assert check_answer(spec, "-0.5 < 2.5")["correct"]
    assert check_answer(spec, "2.5 > -0.5")["correct"]
    assert not check_answer(spec, "-0.5 > 2.5")["correct"]


def test_every_canonical_answer_is_accepted(bank_root):
    for question in questions_by_key(bank_root).values():
        for part in question.parts:
            spec = part.response
            if isinstance(spec, AlgebraicResponse) and spec.comparison_mode == "prime_factorisation":
                answer = spec.canonical_latex.replace("\\times", "*")
            elif isinstance(spec, AlgebraicResponse):
                answer = spec.canonical_expression
            else:
                answer = spec.canonical_answer
            result = check_answer(spec, answer)
            assert result["correct"], (question.stable_key, part.position, answer, result)


def test_exact_ratio_accepts_colons_and_to_notation():
    spec = AlgebraicResponse(
        type="algebraic_expression",
        comparison_mode="exact_ratio",
        canonical_expression="3:5",
        canonical_latex="3:5",
        variables=[],
        domain_constraints=[],
        accepted_equivalents=[],
        checker_config={"terms": 2, "require_simplest_integer_terms": False},
    )

    assert check_answer(spec, "6:10")["correct"]
    assert check_answer(spec, "3 to 5")["correct"]
    assert not check_answer(spec, "5:3")["correct"]


def test_exact_ratio_can_require_simplest_three_term_form():
    spec = AlgebraicResponse(
        type="algebraic_expression",
        comparison_mode="exact_ratio",
        canonical_expression="2:3:1",
        canonical_latex="2:3:1",
        variables=[],
        domain_constraints=[],
        accepted_equivalents=[],
        checker_config={"terms": 3, "require_simplest_integer_terms": True},
    )

    assert check_answer(spec, "2:3:1")["correct"]
    assert not check_answer(spec, "4:6:2")["correct"]
    assert not check_answer(spec, "2/3:1:1/3")["correct"]


# ---------------------------------------------------------------------------
# Shared helpers for the learner-answer checker regression suite
# ---------------------------------------------------------------------------

def symbolic(canonical, variables, *, form=None, accepted=()):
    return AlgebraicResponse(
        type="algebraic_expression",
        comparison_mode="symbolic_equivalence",
        canonical_expression=canonical,
        canonical_latex=canonical,
        variables=variables,
        domain_constraints=[],
        accepted_equivalents=list(accepted),
        checker_config={} if form is None else {"form": form},
    )


def numeric(canonical, latex=None, *, mode="exact_numeric", accepted=(), **extra):
    return NumericResponse(
        type="numeric",
        comparison_mode=mode,
        canonical_answer=canonical,
        canonical_latex=latex or canonical,
        accepted_answers=list(accepted),
        **extra,
    )


def passes(spec, answer):
    result = check_answer(spec, answer)
    assert result["error"] is None, (answer, result)
    return result["correct"]


@pytest.fixture(scope="session")
def authored_responses(repository_root):
    """Every response spec in every question bank and lesson, keyed by (stable_key, part)."""

    found = {}
    resources = repository_root / "backend_resources"
    for path in sorted((resources / "question_bank").glob("**/questions/*.json")):
        question = Question.model_validate(json.loads(path.read_text()))
        for part in question.parts:
            found[(question.stable_key, part.position)] = part.response
    for path in sorted((resources / "courses").glob("**/lessons/*.json")):
        lesson = Lesson.model_validate(json.loads(path.read_text()))
        for section in lesson.sections:
            if isinstance(section, ActiveRecallSection):
                found[(lesson.stable_key, section.stable_key)] = section.response
    return found


# ---------------------------------------------------------------------------
# Defect 1: symbolic_equivalence compared exact text only
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "answer",
    ["3*x+6", "3x+6", "3x + 6", " 3 x+6 ", "6+3x", "3(x+2)", "3×x+6", "3·x + 6", "3x\u2212(\u22126)", "x+x+x+6"],
)
def test_symbolic_equivalence_accepts_equivalent_answers(authored_responses, answer):
    spec = authored_responses[("n5-l1-505", 1)]
    assert spec.canonical_expression == "3*x+6"
    assert passes(spec, answer)


@pytest.mark.parametrize("answer", ["3x+5", "3x-6", "x+6", "3(x+6)", "6x+3", "3x"])
def test_symbolic_equivalence_still_rejects_wrong_answers(authored_responses, answer):
    assert not passes(authored_responses[("n5-l1-505", 1)], answer)


def test_symbolic_equivalence_accepts_products_powers_and_unicode(authored_responses):
    product = authored_responses[("n5-l1-509", 1)]
    for answer in ["(x+4)(x+6)", "(x + 6)(x + 4)", "x^2+10x+24", "x²+10x+24", "x**2 + 10*x + 24"]:
        assert passes(product, answer), answer
    for answer in ["(x+6)(x-4)", "(x+6)(x+4)+1", "x^2+10x+25"]:
        assert not passes(product, answer), answer

    square = authored_responses[("n5-l1-502", 1)]
    for answer in ["x²+6x+9", "x^2 + 6x + 9", "(x+3)^2", "(x+3)²", "9+6x+x^2"]:
        assert passes(square, answer), answer
    for answer in ["x^2+6x+6", "x^3+6x+9", "(x+3)^3"]:
        assert not passes(square, answer), answer

    linear = authored_responses[("n6-l3-019", 1)]
    for answer in ["84\u22126x", "84 \u2013 6x", "-6x+84", "84-6×x", "84 - 6 * x"]:
        assert passes(linear, answer), answer
    for answer in ["84+6x", "6x-84", "84-6"]:
        assert not passes(linear, answer), answer

    recall = authored_responses[("n5-lesson-12", "n5-12-recall")]
    assert passes(recall, "(x-8)(x+8)")
    assert passes(recall, "(x+8)(x-8)")
    assert not passes(recall, "(x-8)^2")


def test_symbolic_equivalence_compares_algebraic_fractions_exactly():
    spec = symbolic("(2*b)/(3*a)", ["a", "b"])
    for answer in ["2b/(3a)", "(2b)/(3a)", "(2/3)*b/a", "b/a*2/3", "4b/(6a)"]:
        assert passes(spec, answer), answer
    for answer in ["3a/(2b)", "2b/(3a)+1", "(2/3)*a/b"]:
        assert not passes(spec, answer), answer
    rational = symbolic("(8*x-41)/((x-4)*(x-7))", ["x"])
    assert passes(rational, "3/(x-4)+5/(x-7)")
    assert passes(rational, "(8x-41)/(x^2-11x+28)")
    assert not passes(rational, "(8x-41)/(x^2-11x-28)")


@pytest.mark.parametrize(
    ("answer", "message"),
    [
        ("3x+", "expression"),
        ("3x+6)", "bracket"),
        ("(3x+6", "bracket"),
        ("y=3x+6", "equals"),
        ("3y+6", "letter x"),
        ("x3+6", "number before a letter"),
        ("3,5x", "decimal point"),
        ("sqrt(x)", "letter x"),
        ("3/2x", "brackets to show what is divided"),
        ("x^-1", "whole numbers"),
        ("x^2^3", "power of a power"),
        ("1/(x-x)", "divides by zero"),
    ],
)
def test_malformed_symbolic_answers_return_format_errors(answer, message):
    result = check_answer(symbolic("3*x+6", ["x"]), answer)
    assert result["correct"] is False
    assert message in result["error"].lower() or message in result["error"], result


# ---------------------------------------------------------------------------
# Defect 2: mixed numbers lost their space and became a different number
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "mixed", "concatenated"),
    [("n1-l2-022", "1 3/4", "13/4"), ("n1-l2-028", "1 1/4", "11/4"), ("n1-l4-002", "2 5/24", "25/24")],
)
def test_mixed_numbers_are_read_as_mixed_numbers(authored_responses, key, mixed, concatenated):
    spec = authored_responses[(key, 1)]
    assert passes(spec, mixed)
    assert not passes(spec, concatenated)


def test_mixed_number_parsing_handles_signs_and_rejects_improper_parts(authored_responses):
    assert passes(authored_responses[("n2-l2-508", 1)], "10 2/3")
    assert not passes(authored_responses[("n2-l2-508", 1)], "102/3")
    negative = numeric("-7/4")
    assert passes(negative, "-1 3/4")
    assert passes(negative, "\u22121 3/4")
    assert not passes(negative, "1 3/4")
    for answer in ["1 7/4", "1 0/4", "2 1/0", "1 3 /4 5"]:
        result = check_answer(negative, answer)
        assert result["correct"] is False and result["error"], (answer, result)


# ---------------------------------------------------------------------------
# Defect 3: a percentage answer typed with % was divided by 100
# ---------------------------------------------------------------------------


def test_percentage_questions_accept_the_percent_sign(authored_responses):
    spec = authored_responses[("n3-l1-001", 1)]
    for answer in ["30", "30%", "30 %", "30.0%"]:
        assert passes(spec, answer), answer
    for answer in ["0.3", "0.3%", "3/10", "300%"]:
        assert not passes(spec, answer), answer


def test_explicit_percentage_unit_is_the_preferred_signal():
    spec = numeric(
        "30", "30", unit=UnitSpec(canonical="%", accepted=["%", "percent"], required=False)
    )
    for answer in ["30", "30%", "30 percent", "30 Percent"]:
        assert passes(spec, answer), answer
    for answer in ["0.3", "3/10"]:
        assert not passes(spec, answer), answer
    assert check_answer(spec, "30%%")["error"]


def test_lesson_percentage_recall_uses_its_declared_unit(authored_responses):
    spec = authored_responses[("n3-lesson-01", "percentage-reference-recall")]
    for answer in ["30", "30%", "30 percent"]:
        assert passes(spec, answer), answer
    assert not passes(spec, "0.3")


def test_percent_sign_still_means_hundredths_where_no_percentage_is_asked():
    decimal = numeric("0.75")
    assert passes(decimal, "75%")
    assert not passes(decimal, "75")
    percentage_points = numeric("6")
    assert not passes(percentage_points, "6%")


def test_rounded_percentage_counts_decimal_places_without_the_sign():
    spec = numeric("12.5", r"12.5\%", mode="rounded_dp", rounding_precision=1)
    assert passes(spec, "12.5%")
    assert passes(spec, "12.50 %")
    assert not passes(spec, "12%")
    assert not passes(spec, "0.125")


# ---------------------------------------------------------------------------
# Defect 4: learner-visible digit separators caused false failures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "answer", ["48400", "48 400", "48,400", "48\u2009400", "48\u00a0400", "48\u202f400"]
)
def test_digit_separators_do_not_change_significant_figures(authored_responses, answer):
    assert passes(authored_responses[("n1-l1-14", 1)], answer)


def test_digit_separators_must_group_in_threes():
    spec = numeric("1250000")
    for answer in ["1,250,000", "1 250 000", "1250000"]:
        assert passes(spec, answer), answer
    for answer in ["12,50,000", "1,250 000", "1.250.000", "1,2500,00"]:
        result = check_answer(spec, answer)
        assert result["correct"] is False and result["error"], (answer, result)
    assert not passes(spec, "125,000")
    rounded = numeric("4188.8", mode="rounded_dp", rounding_precision=1)
    assert passes(rounded, "4,188.8")
    decimal_comma = check_answer(numeric("1.2"), "1,2")
    assert decimal_comma["correct"] is False and decimal_comma["error"]


def test_lesson_feedback_number_format_is_accepted(authored_responses):
    spec = authored_responses[("n1-lesson-07", "approximation-recall")]
    assert passes(spec, "78,600")
    assert passes(spec, "78 600")
    assert not passes(spec, "78,500")


def test_declared_units_may_follow_the_number(authored_responses):
    spec = authored_responses[("n4-lesson-01", "average-speed-recall")]
    for answer in ["60", "60 km/h", "60km/h", "60 kilometres per hour"]:
        assert passes(spec, answer), answer
    assert not passes(spec, "6 km/h")
    assert check_answer(spec, "60 m/s")["error"]


def test_prime_factorisation_accepts_superscripts_and_latex(bank_root):
    spec = questions_by_key(bank_root)["n1-l1-01"].parts[0].response
    for answer in ["2³ × 3² × 5", "2^3 x 3^2 x 5", r"2^{3}\times 3^{2}\times 5", "2**3*3**2*5"]:
        assert passes(spec, answer), answer
    assert not passes(spec, "2^3 × 3^2 × 7")


# ---------------------------------------------------------------------------
# Written form for factorise, expand and simplify tasks
# ---------------------------------------------------------------------------


FORM_CASES = [
    (
        "expanded",
        "3x+12",
        ["x"],
        ["3x+12", "12+3x", "3*x + 12", "(3x+12)"],
        ["3(x+4)", "3(4+x)", "3x+10+2", "x+2x+12"],
    ),
    ("expanded", "a^2b", ["a", "b"], ["a^2b", "ba²", "a^2*b"], ["a*a*b", "aab", "a·a·b"]),
    ("expanded", "4x^2y^2", ["x", "y"], ["4x^2y^2", "4y²x²"], ["(2xy)^2", "2*2x^2y^2", "4(xy)^2"]),
    ("expanded", "32*x", ["x"], ["32x"], ["(x+8)^2-(x-8)^2", "(x+8)²-(x-8)²"]),
    (
        "factorised",
        "(x+6)*(x+4)",
        ["x"],
        ["(x+4)(x+6)", "(x+6)(x+4)"],
        ["x^2+10x+24", "(x^2+10x+24)"],
    ),
    (
        "factorised_completely",
        "6(x+2)",
        ["x"],
        ["6(x+2)", "(x+2)*6", "-6(-x-2)"],
        ["6x+12", "2(3x+6)", "3(2x+4)", "(6x+12)", "1(6x+12)"],
    ),
    (
        "factorised_completely",
        "4*(x+1)*(x+4)",
        ["x"],
        ["4(x+1)(x+4)", "4(x+4)(x+1)"],
        ["(2x+2)(2x+8)", "4(x^2+5x+4)", "(4x+4)(x+4)", "4x^2+20x+16"],
    ),
    (
        "factorised_completely",
        "6*(2*x-1)*(x-1)",
        ["x"],
        ["6(2x-1)(x-1)", "6(1-2x)(1-x)"],
        ["6(2x^2-3x+1)", "(12x-6)(x-1)"],
    ),
    (
        "factorised_completely",
        "(p+q)*(x+2*y)",
        ["p", "q", "x", "y"],
        ["(p+q)(x+2y)", "(x+2y)(q+p)"],
        ["px+qx+2py+2qy", "p(x+2y)+q(x+2y)"],
    ),
    (
        "factorised_completely",
        "2*x*y*(x+2)",
        ["x", "y"],
        ["2xy(x+2)"],
        ["2x(xy+2y)", "2(x^2y+2xy)", "2x^2y+4xy"],
    ),
    (
        "simplified_fraction",
        "6/(x-3)",
        ["x"],
        ["6/(x-3)", "-6/(3-x)"],
        ["2/(x-3)+4/(x-3)", "12/(2x-6)", "(6x)/(x^2-3x)"],
    ),
    (
        "simplified_fraction",
        "(2*b)/(3*a)",
        ["a", "b"],
        ["2b/(3a)", "(2b)/(3a)"],
        ["(5a/(5b))(6b^2/(9a^2))", "30ab^2/(45a^2b)"],
    ),
    (
        "simplified_fraction",
        "5x/4-2",
        ["x"],
        ["5x/4-2", "(5x-8)/4", "1.25x-2", "(5/4)x-2"],
        ["(x/2+3)+(3x/4-5)", "(10x-16)/8"],
    ),
    (
        "simplified_fraction",
        "(3*(x-5))/(5)",
        ["x"],
        ["3(x-5)/5", "(3x-15)/5", "0.6x-3"],
        ["((x^2-25)/(5x))(3x/(x+5))", "(3x^2-15x)/(5x)"],
    ),
]


@pytest.mark.parametrize(("form", "canonical", "variables", "accepted", "rejected"), FORM_CASES)
def test_form_setting_rejects_the_unfinished_expression(form, canonical, variables, accepted, rejected):
    spec = symbolic(canonical, variables, form=form)
    assert passes(spec, canonical)
    for answer in accepted:
        assert passes(spec, answer), (form, answer)
    unconstrained = symbolic(canonical, variables)
    for answer in rejected:
        assert passes(unconstrained, answer), ("must be equivalent", answer)
        assert not passes(spec, answer), (form, answer)


UNREDUCED_COEFFICIENT_CASES = [
    ("x/2", ["x"], ["2x/4", "(2x)/4", "(2/4)x", "2/4*x", "x*2/4"], ["x/2", "(x)/2", "(1/2)x", "0.5x"]),
    ("2a/3", ["a"], ["6a/9", "(6a)/9", "(6/9)a"], ["2a/3", "(2a)/3", "(2/3)a"]),
    ("5x/4-2", ["x"], ["10x/8-2", "(10x)/8-2", "(10/8)x-2"], ["5x/4-2", "(5x)/4-2", "1.25x-2"]),
    ("3x+1", ["x"], ["6x/2+1", "(6x)/2+1", "3x/1+2/2", "1.5x/0.5+1"], ["3x+1", "1+3x"]),
]


@pytest.mark.parametrize("form", ["expanded", "simplified_fraction"])
@pytest.mark.parametrize(("canonical", "variables", "unreduced", "reduced"), UNREDUCED_COEFFICIENT_CASES)
def test_simplified_forms_reject_coefficients_not_in_lowest_terms(
    form, canonical, variables, unreduced, reduced
):
    spec = symbolic(canonical, variables, form=form)
    unconstrained = symbolic(canonical, variables)
    for answer in unreduced:
        assert passes(unconstrained, answer), ("must be equivalent", answer)
        assert not passes(spec, answer), (form, answer)
    for answer in reduced:
        assert passes(spec, answer), (form, answer)


@pytest.mark.parametrize("form", SYMBOLIC_FORMS)
@pytest.mark.parametrize(
    ("bracketed", "plain"),
    [("(2x)/4", "2x/4"), ("(5x)/4-2", "5x/4-2"), ("(6a)/9", "6a/9"), ("(x)/2", "x/2")],
)
def test_bracketed_and_plain_numerators_are_checked_the_same(form, bracketed, plain):
    for canonical, variables in (("x/2", ["x"]), ("5x/4-2", ["x"]), ("2a/3", ["a"])):
        if set(variables) != {character for character in plain if character.isalpha()}:
            continue
        spec = symbolic(canonical, variables, form=form)
        assert check_answer(spec, bracketed) == check_answer(spec, plain), (form, canonical)


def test_form_defaults_to_any_for_backward_compatibility():
    default = symbolic("3x+12", ["x"])
    explicit = symbolic("3x+12", ["x"], form="any")
    assert default.checker_config == {}
    for spec in (default, explicit):
        assert passes(spec, "3(x+4)")


@pytest.mark.parametrize("form", SYMBOLIC_FORMS)
def test_every_documented_form_is_valid(form):
    assert symbolic("6(x+2)", ["x"], form=form).checker_config == {"form": form}


@pytest.mark.parametrize(
    ("mode", "config"),
    [
        ("symbolic_equivalence", {"form": "factorized"}),
        ("symbolic_equivalence", {"form": None}),
        ("symbolic_equivalence", {"fom": "expanded"}),
        ("exact_ratio", {"terms": 2, "require_simplest_integer_terms": True, "form": "expanded"}),
    ],
)
def test_response_model_rejects_invalid_form_configuration(mode, config):
    with pytest.raises(ValidationError):
        AlgebraicResponse(
            type="algebraic_expression",
            comparison_mode=mode,
            canonical_expression="2:3" if mode == "exact_ratio" else "x",
            canonical_latex="x",
            variables=["x"],
            domain_constraints=[],
            accepted_equivalents=[],
            checker_config=config,
        )


# ---------------------------------------------------------------------------
# Authored content: nothing that was correct may become incorrect
# ---------------------------------------------------------------------------


def test_every_authored_canonical_and_accepted_answer_passes(authored_responses):
    assert len(authored_responses) > 2000
    failures = []
    for key, spec in authored_responses.items():
        if isinstance(spec, NumericResponse):
            candidates = [spec.canonical_answer, *spec.accepted_answers]
        elif spec.comparison_mode == "prime_factorisation":
            candidates = [spec.canonical_latex, *spec.accepted_equivalents]
        else:
            candidates = [spec.canonical_expression, *spec.accepted_equivalents]
        for answer in candidates:
            result = check_answer(spec, answer)
            if not result["correct"]:
                failures.append((key, answer, result))
    assert failures == []


# ---------------------------------------------------------------------------
# Untrusted input: hostile, malformed and oversized answers
# ---------------------------------------------------------------------------


HOSTILE_ANSWERS = [
    "__import__('os').system('id')",
    "eval('1+1')",
    "exec('x=1')",
    "lambda: 0",
    "x.__class__",
    "open('/etc/passwd')",
    "\x00x",
    "x\u202e+1",
    "1e999999999",
    "9" * 199,
    "0." + "0" * 190 + "1",
    "x^999999999999",
    "((x^20)^20)^20",
    "(a+b+x+y)^8(a+b+x+y)^8",
    "(a+b+x+y)^6*(a+x+b+y)^6",
    "(" * 9 + "x" + ")" * 9,
    "(" * 99 + "x" + ")" * 99,
    "[" * 99 + "]" * 99,
    "-" * 150 + "1",
    "x" * MAX_ANSWER_LENGTH,
    "x" * (MAX_ANSWER_LENGTH + 1),
    "1" * 10_000,
    "618970019642690137449562111",
    "2^99999999999",
    "1/0",
    "0^0",
    "%%%",
    "",
    "   ",
]

HOSTILE_SPECS = [
    symbolic("(a+b)*(x+2*y)", ["a", "b", "x", "y"]),
    symbolic("6(x+2)", ["x"], form="factorised_completely"),
    numeric("30", r"30\%"),
    numeric("48400", mode="rounded_sf", rounding_precision=3),
    AlgebraicResponse(
        type="algebraic_expression",
        comparison_mode="prime_factorisation",
        canonical_expression="360",
        canonical_latex="2^3",
        variables=[],
        domain_constraints=[],
        accepted_equivalents=[],
        checker_config={"require_prime_bases": True},
    ),
    AlgebraicResponse(
        type="algebraic_expression",
        comparison_mode="ordered_numeric_list",
        canonical_expression="[1,2]",
        canonical_latex="1,2",
        variables=[],
        domain_constraints=[],
        accepted_equivalents=[],
        checker_config={"order": "ascending"},
    ),
]


@pytest.mark.parametrize("answer", HOSTILE_ANSWERS)
@pytest.mark.parametrize("spec", HOSTILE_SPECS, ids=lambda spec: spec.comparison_mode)
def test_hostile_input_is_rejected_quickly_without_raising(spec, answer):
    started = time.perf_counter()
    result = check_answer(spec, answer)
    elapsed = time.perf_counter() - started
    assert result["correct"] is False
    assert result["error"] is None or isinstance(result["error"], str)
    assert elapsed < 0.5, (answer[:40], elapsed)


def test_oversized_and_non_text_answers_return_format_errors():
    spec = symbolic("x", ["x"])
    assert check_answer(spec, "x" * (MAX_ANSWER_LENGTH + 1))["error"] == checking.TOO_LONG_MESSAGE
    assert check_answer(spec, None)["error"] == checking.EMPTY_MESSAGE
    assert check_answer(spec, "(" * 9 + "x" + ")" * 9)["error"] == checking.NESTING_MESSAGE
    assert check_answer(spec, "x^21")["error"] == checking.POWER_MESSAGE
    assert check_answer(spec, "(x+1)^20(x-1)^20(x+2)")["error"] == checking.TOO_LARGE_MESSAGE


def test_invalid_authored_answer_is_reported_as_configuration_error():
    assert check_answer(symbolic("3x+", ["x"]), "3x")["error"] == checking.CONFIGURATION_MESSAGE
    assert check_answer(numeric("thirty"), "30")["error"] == checking.CONFIGURATION_MESSAGE


def test_checker_never_evaluates_learner_text():
    source = Path(checking.__file__).read_text()
    tree = ast.parse(source)
    forbidden_builtins = {"eval", "exec", "compile", "__import__"}
    forbidden_functions = {"sympify", "parse_expr", "literal_eval"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_builtins | forbidden_functions, node.func.id
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_functions, node.func.attr
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [alias.name for alias in node.names] + [getattr(node, "module", "") or ""]
            assert not {"ast", "sympy"} & {module.split(".")[0] for module in modules}, modules
