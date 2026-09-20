from question_bank.checking import check_answer
from question_bank.models import AlgebraicResponse
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
