from question_bank.checking import check_answer
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
