"""Authoring rules that catch answer cues the structural validators cannot see.

Existing findings are recorded in authoring/quality_baseline.json. A finding outside the
baseline is an error, so new content cannot repeat them, and fixing an item must also remove
its baseline entry, so the list only shrinks.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .english_models import EnglishObjectiveQuestion

BASELINE_PATH = "authoring/quality_baseline.json"
LONGEST_KEY_RATIO = 1.3
MAX_KEY_POSITION_SHARE = 0.6
MIN_FORM_PARTS_FOR_POSITION_CHECK = 5
MIN_PARTS_FOR_ORDER_CHECK = 4
MIN_PARTS_FOR_SEQUENCE_CHECK = 5
MAX_DIAGNOSTIC_LONGEST_KEY_SHARE = 0.5
DIAGNOSTIC_POOLS = {"baseline_diagnostic", "endline_diagnostic", "protected_reserve"}
DIAGNOSTIC_FORM_TYPES = {"baseline", "endline", "endline_reserve"}
LESSON_COPY_WORDS = 8
# Level review rule 5: diagnostic passages per task type, in words (whitespace-separated).
DIAGNOSTIC_PASSAGE_WORDS = {
    "reading_comprehension": (300, 450),
    "banked_cloze": (150, 250),
    "open_cloze": (150, 250),
}
PROTECTED_POOLS = {
    "baseline_diagnostic",
    "endline_diagnostic",
    "protected_reserve",
    "module_checkpoint",
}
OPEN_CLOZE_PROMPT = re.compile(
    r"^Gap \d+(?: \([A-Z]+\))?: write (?:one word|the correct form of the word)\.$"
)
TARGET_WORD = re.compile(r"What does [“\"]([^”\"]+)[”\"]")
# Older items ask "What does tentative mean?" without quotation marks.
UNQUOTED_TARGET_WORD = re.compile(r"What does ([A-Za-z’'-]+) mean")
# The reported paper has no editing section and no "answer in your own words" questions
# (exam profile excluded_task_types), so practice must not train either format.
EXCLUDED_QUESTION_TYPES = {"editing"}
CORRECTION_TASK = re.compile(
    r"\bOriginal:|\bWhich revision\b(?! set)|['’]s draft:|\bcorrect the (?:error|mistake)s?\b",
    re.IGNORECASE,
)
OWN_WORDS = re.compile(r"\bin (?:your|their|his|her) own words\b", re.IGNORECASE)
BANNED_TERMS = (
    "blueprint",
    "confound",
    "process compression",
    "fade support",
    "given-to-new",
    "synonym drift",
    "reverse outline",
    "reflective hinge",
    "conceptual closure",
    "structural abstraction",
    "dominant function",
    "operationalise",
)


@dataclass(frozen=True)
class QualityFinding:
    code: str
    location: str
    message: str

    @property
    def key(self) -> str:
        return f"{self.code}|{self.location}"


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9’'-]+", text.casefold())


def _contains_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word.casefold())}\b", text.casefold()) is not None


def _key_texts(question: EnglishObjectiveQuestion) -> list[str]:
    texts = []
    for part in question.parts:
        response = part.response
        if response.type == "single_choice":
            texts.extend(
                option.text for option in response.options if option.key == response.correct_key
            )
        elif response.type == "short_text":
            texts.append(response.canonical_answer)
    return texts


def _title_findings(question: EnglishObjectiveQuestion) -> list[QualityFinding]:
    # Short keys such as "a" and "the" appear in ordinary titles.
    answers = {text for text in _key_texts(question) if len(text) >= 4 and " " not in text}
    answers |= {
        match.group(1)
        for part in question.parts
        for match in [TARGET_WORD.search(part.prompt)]
        if match
    }
    named = sorted(answer for answer in answers if _contains_word(question.title, answer))
    if not named:
        return []
    return [
        QualityFinding(
            "title_names_answer",
            question.stable_key,
            f"The learner-visible title names {named}.",
        )
    ]


def _part_findings(question: EnglishObjectiveQuestion) -> list[QualityFinding]:
    findings = []
    for part in question.parts:
        location = f"{question.stable_key}#{part.position}"
        if question.question_type == "open_cloze" and not OPEN_CLOZE_PROMPT.match(part.prompt):
            findings.append(
                QualityFinding(
                    "open_cloze_prompt_not_neutral",
                    location,
                    "Use 'Gap n: write one word.' Move clue guidance to the hint.",
                )
            )
        response = part.response
        if response.type != "single_choice" or question.question_type == "banked_cloze":
            continue
        lengths = {option.key: len(option.text) for option in response.options}
        key_length = lengths[response.correct_key]
        others = [length for key, length in lengths.items() if key != response.correct_key]
        if key_length > LONGEST_KEY_RATIO * max(others):
            findings.append(
                QualityFinding(
                    "key_uniquely_longest",
                    location,
                    f"The key has {key_length} characters; the longest other option has {max(others)}.",
                )
            )
    return findings


def _banked_cloze_order_findings(question: EnglishObjectiveQuestion) -> list[QualityFinding]:
    """Flag keys that a learner could collect by working through the bank in order."""

    if question.question_type != "banked_cloze" or len(question.parts) < 3:
        return []
    bank = [option.key for option in question.parts[0].response.options]
    positions = [bank.index(part.response.correct_key) for part in question.parts]
    steps = list(zip(positions, positions[1:], strict=False))
    ascending = all(later > earlier for earlier, later in steps)
    in_place = sum(1 for gap, position in enumerate(positions) if gap == position)
    next_word = sum(1 for earlier, later in steps if later == earlier + 1)
    if not (ascending or 2 * in_place > len(positions) or 2 * next_word > len(steps)):
        return []
    keys = "".join(part.response.correct_key for part in question.parts)
    return [
        QualityFinding(
            "banked_cloze_keys_follow_bank_order",
            question.stable_key,
            f"The gap keys {keys} follow the word-bank order. Reorder the bank.",
        )
    ]


def _passage_text(question: EnglishObjectiveQuestion, passages) -> str | None:
    if question.passage_ref is None:
        return ""
    if passages is None:
        return None
    ref = question.passage_ref
    for passage in passages:
        if (passage.stable_key, passage.revision) == (ref.stable_key, ref.revision):
            return " ".join(passage.paragraphs)
    return None


def _appears(text: str, target: str) -> bool:
    text = text.casefold()
    target = target.casefold()
    if target.startswith("-") or target.endswith("-"):
        # Affix items such as “un-” ask about part of a word.
        return target.strip("-") in text
    return re.search(rf"(?<![\w-]){re.escape(target)}(?![\w-])", text) is not None


def _target_word_findings(question: EnglishObjectiveQuestion, passages) -> list[QualityFinding]:
    """Flag “What does X mean?” parts whose sentence or passage never uses X."""

    passage_text = _passage_text(question, passages)
    if passage_text is None:
        return []
    findings = []
    for part in question.parts:
        match = TARGET_WORD.search(part.prompt) or UNQUOTED_TARGET_WORD.search(part.prompt)
        if not match:
            continue
        context = f"{part.prompt[: match.start()]} {passage_text}"
        if not _appears(context, match.group(1)):
            findings.append(
                QualityFinding(
                    "target_word_missing_from_context",
                    f"{question.stable_key}#{part.position}",
                    f"“{match.group(1)}” does not appear in the sentence or passage it asks about.",
                )
            )
    return findings


def _choice_parts(question: EnglishObjectiveQuestion):
    if question.question_type == "banked_cloze":
        return []
    parts = [part for part in question.parts if part.response.type == "single_choice"]
    return parts if len(parts) == len(question.parts) else []


def _option_order_findings(question: EnglishObjectiveQuestion) -> list[QualityFinding]:
    """Flag grouped parts whose keys mostly step to the next option letter (A, B, C, D, A...)."""

    parts = _choice_parts(question)
    if len(parts) < MIN_PARTS_FOR_ORDER_CHECK:
        return []
    steps = 0
    for earlier, later in zip(parts, parts[1:], strict=False):
        letters = [option.key for option in earlier.response.options]
        following = letters[(letters.index(earlier.response.correct_key) + 1) % len(letters)]
        if later.response.correct_key == following:
            steps += 1
    if 2 * steps <= len(parts) - 1:
        return []
    keys = "".join(part.response.correct_key for part in parts)
    return [
        QualityFinding(
            "single_choice_keys_follow_option_order",
            question.stable_key,
            f"The part keys {keys} mostly move to the next option letter. Reorder options.",
        )
    ]


def _repeated_sequence_findings(questions) -> list[QualityFinding]:
    """Flag diagnostic questions that share a key sequence, so one form's answers fit another."""

    seen: dict[str, str] = {}
    findings = []
    for question in sorted(questions, key=lambda item: item.stable_key):
        if question.exposure_pool not in DIAGNOSTIC_POOLS:
            continue
        parts = _choice_parts(question)
        if len(parts) < MIN_PARTS_FOR_SEQUENCE_CHECK:
            continue
        keys = "".join(part.response.correct_key for part in parts)
        if keys in seen:
            findings.append(
                QualityFinding(
                    "diagnostic_key_sequence_repeated",
                    question.stable_key,
                    f"The keys {keys} repeat those of {seen[keys]}.",
                )
            )
        else:
            seen[keys] = question.stable_key
    return findings


def _uniquely_longest(response) -> bool:
    lengths = {option.key: len(option.text) for option in response.options}
    key_length = lengths[response.correct_key]
    return all(length < key_length for key, length in lengths.items() if key != response.correct_key)


def _diagnostic_longest_findings(forms, by_key) -> list[QualityFinding]:
    """Flag diagnostic forms where choosing the longest option scores most parts."""

    findings = []
    for form in forms:
        if form.form_type not in DIAGNOSTIC_FORM_TYPES:
            continue
        responses = [
            part.response
            for key in form.question_keys
            if key in by_key
            for part in _choice_parts(by_key[key])
        ]
        if not responses:
            continue
        longest = sum(1 for response in responses if _uniquely_longest(response))
        if longest > MAX_DIAGNOSTIC_LONGEST_KEY_SHARE * len(responses):
            findings.append(
                QualityFinding(
                    "diagnostic_key_often_longest",
                    form.form_key,
                    f"The key is the longest option in {longest} of {len(responses)} parts.",
                )
            )
    return findings


def passage_word_count(passage) -> int:
    return sum(len(paragraph.split()) for paragraph in passage.paragraphs)


def _diagnostic_passage_length_findings(forms, by_key, passages) -> list[QualityFinding]:
    """Flag baseline, endline and reserve passages outside the level-review length range."""

    if passages is None:
        return []
    by_revision = {(passage.stable_key, passage.revision): passage for passage in passages}
    findings = []
    seen = set()
    for form in forms:
        if form.form_type not in DIAGNOSTIC_FORM_TYPES:
            continue
        for key in form.question_keys:
            question = by_key.get(key)
            if question is None or question.passage_ref is None:
                continue
            limits = DIAGNOSTIC_PASSAGE_WORDS.get(question.question_type)
            ref = question.passage_ref
            passage = by_revision.get((ref.stable_key, ref.revision))
            if limits is None or passage is None or ref.stable_key in seen:
                continue
            seen.add(ref.stable_key)
            words = passage_word_count(passage)
            low, high = limits
            if not low <= words <= high:
                findings.append(
                    QualityFinding(
                        "diagnostic_passage_length",
                        ref.stable_key,
                        f"{words} words; {question.question_type} passages need {low}-{high}.",
                    )
                )
    return findings


def _form_findings(forms, by_key) -> list[QualityFinding]:
    findings = []
    for form in forms:
        positions: dict[str, int] = {}
        for key in form.question_keys:
            question = by_key.get(key)
            if question is None or question.question_type == "banked_cloze":
                continue
            for part in question.parts:
                if part.response.type == "single_choice":
                    correct = part.response.correct_key
                    positions[correct] = positions.get(correct, 0) + 1
        total = sum(positions.values())
        if total < MIN_FORM_PARTS_FOR_POSITION_CHECK:
            continue
        share = max(positions.values()) / total
        if share > MAX_KEY_POSITION_SHARE:
            findings.append(
                QualityFinding(
                    "key_position_unbalanced",
                    form.form_key,
                    f"One option position holds {share:.0%} of {total} keys: {positions}.",
                )
            )
    return findings


def _protected_reuse_findings(questions, lessons) -> list[QualityFinding]:
    open_text = [
        (question.stable_key, " ".join(_strings(question.model_dump(mode="json"))))
        for question in questions
        if question.exposure_pool not in PROTECTED_POOLS
    ]
    open_text += [
        (lesson.stable_key, " ".join(_strings(lesson.model_dump(mode="json"))))
        for lesson in lessons
    ]
    findings = []
    for question in questions:
        if question.exposure_pool not in PROTECTED_POOLS:
            continue
        for part in question.parts:
            match = TARGET_WORD.search(part.prompt)
            if not match:
                continue
            seen = [key for key, text in open_text if _contains_word(text, match.group(1))]
            if seen:
                findings.append(
                    QualityFinding(
                        "protected_word_already_taught",
                        f"{question.stable_key}#{part.position}",
                        f"“{match.group(1)}” also appears in {seen[:3]}.",
                    )
                )
    return findings


def _lesson_copy_findings(questions, lessons) -> list[QualityFinding]:
    assessed: dict[tuple[str, ...], str] = {}
    for question in questions:
        if question.exposure_pool not in PROTECTED_POOLS | {"exit_ticket"}:
            continue
        for part in question.parts:
            words = _words(part.prompt) + [
                word for text in _key_texts(question) for word in _words(text)
            ]
            for index in range(len(words) - LESSON_COPY_WORDS + 1):
                assessed.setdefault(
                    tuple(words[index : index + LESSON_COPY_WORDS]), question.stable_key
                )
    findings = []
    for lesson in lessons:
        copied = set()
        for section in lesson.sections:
            words = _words(" ".join(_strings(section.model_dump(mode="json"))))
            for index in range(len(words) - LESSON_COPY_WORDS + 1):
                source = assessed.get(tuple(words[index : index + LESSON_COPY_WORDS]))
                if source:
                    copied.add(source)
        for source in sorted(copied):
            findings.append(
                QualityFinding(
                    "lesson_copies_assessment",
                    f"{lesson.stable_key}>{source}",
                    f"The lesson repeats at least {LESSON_COPY_WORDS} consecutive words from {source}.",
                )
            )
    return findings


def _excluded_task_findings(question: EnglishObjectiveQuestion) -> list[QualityFinding]:
    findings = []
    if question.question_type in EXCLUDED_QUESTION_TYPES:
        findings.append(
            QualityFinding(
                "excluded_task_type",
                question.stable_key,
                f"The paper has no {question.question_type} questions; use a task type it reports.",
            )
        )
    texts = [question.instructions, *(part.prompt for part in question.parts)]
    if any(CORRECTION_TASK.search(text) for text in texts):
        findings.append(
            QualityFinding(
                "correction_task",
                question.stable_key,
                "The paper has no editing questions; ask what to write, not how to fix a given text.",
            )
        )
    if any(OWN_WORDS.search(text) for text in texts):
        findings.append(
            QualityFinding(
                "own_words_question",
                question.stable_key,
                "The paper has no answer-in-your-own-words questions.",
            )
        )
    return findings


def _banned_term_findings(questions, lessons) -> list[QualityFinding]:
    findings = []
    for item in [*questions, *lessons]:
        payload = item.model_dump(mode="json", exclude={"provenance"})
        text = " ".join(_strings(payload)).casefold()
        for term in BANNED_TERMS:
            if term in text:
                findings.append(
                    QualityFinding(
                        "banned_learner_term",
                        f"{item.stable_key}:{term}",
                        f"Replace “{term}” with plain wording.",
                    )
                )
    return findings


def english_quality_findings(questions, lessons, forms, passages=None) -> list[QualityFinding]:
    """Return rule findings. Without passages, passage-based items skip the target-word rule."""

    by_key = {question.stable_key: question for question in questions}
    findings = []
    for question in questions:
        findings.extend(_title_findings(question))
        findings.extend(_part_findings(question))
        findings.extend(_banked_cloze_order_findings(question))
        findings.extend(_target_word_findings(question, passages))
        findings.extend(_option_order_findings(question))
        findings.extend(_excluded_task_findings(question))
    findings.extend(_repeated_sequence_findings(questions))
    findings.extend(_form_findings(forms, by_key))
    findings.extend(_diagnostic_longest_findings(forms, by_key))
    findings.extend(_diagnostic_passage_length_findings(forms, by_key, passages))
    findings.extend(_protected_reuse_findings(questions, lessons))
    findings.extend(_lesson_copy_findings(questions, lessons))
    findings.extend(_banned_term_findings(questions, lessons))
    return findings


def load_quality_baseline(root: Path) -> set[str]:
    path = root / BASELINE_PATH
    if not path.exists():
        return set()
    return set(json.loads(path.read_text())["accepted_findings"])


def write_quality_baseline(root: Path, findings: list[QualityFinding]) -> int:
    keys = sorted({finding.key for finding in findings})
    payload = {
        "note": "Known findings to fix. Do not add to this list; new content must pass the rules.",
        "accepted_findings": keys,
    }
    (root / BASELINE_PATH).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return len(keys)
