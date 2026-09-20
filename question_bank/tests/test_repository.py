from question_bank.repository import content_hash
from question_bank.validation import validate_bank


def test_content_hash_is_stable_and_changes_with_assessed_content(bank_root):
    question = validate_bank(bank_root).questions[0]
    first = content_hash(question)
    same = content_hash(question.model_copy(deep=True))
    changed = question.model_copy(deep=True)
    changed.parts[0].marks += 1

    assert first == same
    assert first != content_hash(changed)
