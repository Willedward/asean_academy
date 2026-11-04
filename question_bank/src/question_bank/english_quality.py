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
LESSON_COPY_WORDS = 8
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


def english_quality_findings(questions, lessons, forms) -> list[QualityFinding]:
    by_key = {question.stable_key: question for question in questions}
    findings = []
    for question in questions:
        findings.extend(_title_findings(question))
        findings.extend(_part_findings(question))
    findings.extend(_form_findings(forms, by_key))
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
