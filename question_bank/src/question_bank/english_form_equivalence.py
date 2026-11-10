"""Per-form equivalence report for the English baseline, endline and reserve diagnostics.

The three forms are meant to be interchangeable, so a learner's change between baseline and
endline reflects learning rather than an easier form. This report compares what can be
measured from the source files: structure, passage length, option lengths, key positions and a
word-frequency proxy for vocabulary difficulty.

The proxy is not a difficulty rating. It counts how many other source documents in the
repository use each tested word (document frequency) and adds word length and an estimated
syllable count, which tend to rise as words get rarer. The English educator's rating of each
target word replaces it; this report only shows where to look first.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean

from .english_models import EnglishObjectiveQuestion
from .english_quality import DIAGNOSTIC_FORM_TYPES, TARGET_WORD, passage_word_count
from .english_validation import validate_english_foundation

FORM_ORDER = {"baseline": 0, "endline": 1, "endline_reserve": 2}
WORD = re.compile(r"[a-z]+(?:['’-][a-z]+)*")
SENTENCE_END = re.compile(r"[.!?]+(?:[’”\"'])?(?=\s|$)")
VOWEL_GROUPS = re.compile(r"[aeiouy]+")
# Tolerances for flagging a form that differs from the others. They are prompts to look,
# not pass marks.
PASSAGE_WORD_TOLERANCE = 0.15
OPTION_RATIO_TOLERANCE = 0.15
SYLLABLE_TOLERANCE = 0.3
DOCUMENT_SHARE_TOLERANCE = 0.5
MIN_COMPARABLE_SHARE = 0.01
MAX_KEY_SHARE = 0.4


def estimate_syllables(word: str) -> int:
    word = word.casefold().replace("’", "'")
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    if len(word) > 3 and word.endswith("e") and not word.endswith(("le", "ee", "ye")):
        word = word[:-1]
    if word.endswith("ed") and len(word) > 4 and word[-3] not in "td":
        word = word[:-2]
    return max(1, len(VOWEL_GROUPS.findall(word)))


def _words(text: str) -> list[str]:
    return WORD.findall(text.casefold())


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def document_frequencies(corpus_root: Path, excluded: set[Path]) -> tuple[Counter, int]:
    """Count, for each word, the number of source JSON documents that use it."""

    counts: Counter = Counter()
    documents = 0
    for path in sorted(corpus_root.rglob("*.json")):
        if path.resolve() in excluded:
            continue
        try:
            payload = json.loads(path.read_text())
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        words = {word for text in _strings(payload) for word in _words(text)}
        if words:
            documents += 1
            counts.update(words)
    return counts, documents


def _targets(question: EnglishObjectiveQuestion) -> list[str]:
    """Tested words: vocabulary targets, or banked-cloze keys and open-cloze answers."""

    targets = []
    for part in question.parts:
        response = part.response
        if question.question_type == "vocabulary_in_context":
            match = TARGET_WORD.search(part.prompt)
            if match:
                targets.append(match.group(1))
            elif response.type == "single_choice":
                targets.append(
                    next(o.text for o in response.options if o.key == response.correct_key)
                )
        elif question.question_type == "banked_cloze":
            targets.append(next(o.text for o in response.options if o.key == response.correct_key))
        elif question.question_type == "open_cloze":
            targets.append(response.canonical_answer)
    return targets


def _option_profile(questions: list[EnglishObjectiveQuestion]) -> dict:
    key_lengths, distractor_lengths = [], []
    longest = shortest = parts = 0
    for question in questions:
        if question.question_type == "banked_cloze":
            continue
        for part in question.parts:
            response = part.response
            if response.type != "single_choice":
                continue
            lengths = {option.key: len(option.text) for option in response.options}
            key = lengths[response.correct_key]
            others = [length for k, length in lengths.items() if k != response.correct_key]
            parts += 1
            key_lengths.append(key)
            distractor_lengths.extend(others)
            longest += key > max(others)
            shortest += key < min(others)
    key_mean = mean(key_lengths) if key_lengths else 0.0
    distractor_mean = mean(distractor_lengths) if distractor_lengths else 0.0
    return {
        "single_choice_parts": parts,
        "mean_key_characters": round(key_mean, 1),
        "mean_distractor_characters": round(distractor_mean, 1),
        "key_to_distractor_ratio": round(key_mean / distractor_mean, 2) if distractor_mean else 0.0,
        "key_uniquely_longest": longest,
        "key_uniquely_shortest": shortest,
    }


def _key_distribution(questions: list[EnglishObjectiveQuestion]) -> dict:
    letters: Counter = Counter()
    banked: Counter = Counter()
    for question in questions:
        for part in question.parts:
            if part.response.type != "single_choice":
                continue
            target = banked if question.question_type == "banked_cloze" else letters
            target[part.response.correct_key] += 1
    total = sum(letters.values())
    return {
        "single_choice": dict(sorted(letters.items())),
        "largest_share": round(max(letters.values()) / total, 2) if total else 0.0,
        "banked_cloze": dict(sorted(banked.items())),
    }


def _passage_profile(passage) -> dict:
    text = " ".join(passage.paragraphs)
    words = _words(text)
    sentences = max(1, len(SENTENCE_END.findall(text)))
    return {
        "words": passage_word_count(passage),
        "paragraphs": len(passage.paragraphs),
        "mean_sentence_words": round(len(words) / sentences, 1),
        "three_plus_syllable_share": round(
            sum(estimate_syllables(word) >= 3 for word in words) / len(words), 3
        )
        if words
        else 0.0,
    }


def _vocabulary_profile(targets: list[str], frequencies: Counter, documents: int) -> dict:
    rows = []
    for target in targets:
        words = _words(target)
        if not words:
            continue
        # Multi-word answers are rated by their rarest word.
        word = min(words, key=lambda candidate: frequencies.get(candidate, 0))
        rows.append(
            {
                "target": target,
                "documents": frequencies.get(word, 0),
                "letters": len(word),
                "syllables": estimate_syllables(word),
            }
        )
    rows.sort(key=lambda row: (row["documents"], -row["letters"], row["target"]))
    if not rows:
        return {"targets": 0}
    shares = [row["documents"] / documents for row in rows] if documents else [0.0]
    return {
        "targets": len(rows),
        "mean_document_share": round(mean(shares), 4),
        "median_documents": sorted(row["documents"] for row in rows)[len(rows) // 2],
        "in_fewer_than_5_documents": sum(row["documents"] < 5 for row in rows),
        "mean_letters": round(mean(row["letters"] for row in rows), 2),
        "mean_syllables": round(mean(row["syllables"] for row in rows), 2),
        "rarest": rows[:8],
    }


def _relative_gap(values: list[float]) -> float:
    low, high = min(values), max(values)
    return (high - low) / high if high else 0.0


def _flags(forms: list[dict]) -> list[str]:
    flags = []
    structures = {json.dumps(form["structure"]["parts_by_task"], sort_keys=True) for form in forms}
    if len(structures) > 1:
        flags.append("Forms have different part counts by task type.")
    for task in ("reading_comprehension", "banked_cloze", "open_cloze"):
        totals = [form["passages"]["total_words"].get(task, 0) for form in forms]
        if all(totals) and _relative_gap(totals) > PASSAGE_WORD_TOLERANCE:
            flags.append(f"{task} passage words differ by more than 15%: {totals}.")
    ratios = [form["options"]["key_to_distractor_ratio"] for form in forms]
    if max(ratios) - min(ratios) > OPTION_RATIO_TOLERANCE:
        flags.append(f"Key-to-distractor length ratios differ: {ratios}.")
    for form in forms:
        if form["keys"]["largest_share"] > MAX_KEY_SHARE:
            flags.append(
                f"{form['form_key']}: one letter holds {form['keys']['largest_share']:.0%} of keys."
            )
    for section, label in (("vocabulary", "vocabulary target"), ("cloze_answers", "cloze answer")):
        syllables = [form[section].get("mean_syllables", 0) for form in forms]
        if max(syllables) - min(syllables) > SYLLABLE_TOLERANCE:
            flags.append(f"Mean {label} syllables differ: {syllables}.")
        shares = [form[section].get("mean_document_share", 0) for form in forms]
        # Shares near zero (most targets in no other document) are too coarse to compare.
        if max(shares) >= MIN_COMPARABLE_SHARE and _relative_gap(shares) > DOCUMENT_SHARE_TOLERANCE:
            flags.append(f"Mean {label} document share differs by more than half: {shares}.")
    return flags


def form_equivalence_report(root: Path, corpus_root: Path | None = None) -> dict:
    root = root.resolve()
    corpus_root = (corpus_root or root.parents[1]).resolve()
    foundation = validate_english_foundation(root)
    by_key = {question.stable_key: question for question in foundation.questions}
    passages = {(p.stable_key, p.revision): p for p in foundation.passages}
    forms = sorted(
        (form for form in foundation.forms if form.form_type in DIAGNOSTIC_FORM_TYPES),
        key=lambda form: FORM_ORDER[form.form_type],
    )

    excluded = set()
    for form in forms:
        for key in form.question_keys:
            excluded.add((root / "questions" / f"{key}.json").resolve())
            ref = by_key[key].passage_ref
            if ref is not None:
                excluded.add((root / "passages" / f"{ref.stable_key}.json").resolve())
    frequencies, documents = document_frequencies(corpus_root, excluded)

    reports = []
    for form in forms:
        questions = [by_key[key] for key in form.question_keys]
        parts_by_task: Counter = Counter()
        passage_rows = []
        total_words: Counter = Counter()
        vocabulary, cloze = [], []
        for question in questions:
            parts_by_task[question.question_type] += len(question.parts)
            if question.question_type == "vocabulary_in_context":
                vocabulary.extend(_targets(question))
            else:
                cloze.extend(_targets(question))
            ref = question.passage_ref
            if ref is not None:
                profile = _passage_profile(passages[(ref.stable_key, ref.revision)])
                passage_rows.append(
                    {"question": question.stable_key, "task": question.question_type,
                     "passage": ref.stable_key, **profile}
                )
                total_words[question.question_type] += profile["words"]
        reports.append(
            {
                "form_key": form.form_key,
                "form_type": form.form_type,
                "structure": {
                    "questions": len(questions),
                    "parts": sum(parts_by_task.values()),
                    "parts_by_task": dict(sorted(parts_by_task.items())),
                    "matches_declared_distribution": dict(parts_by_task)
                    == form.task_part_distribution,
                },
                "passages": {"items": passage_rows, "total_words": dict(sorted(total_words.items()))},
                "options": _option_profile(questions),
                "keys": _key_distribution(questions),
                "vocabulary": _vocabulary_profile(vocabulary, frequencies, documents),
                "cloze_answers": _vocabulary_profile(cloze, frequencies, documents),
            }
        )
    return {
        "corpus_documents": documents,
        "proxy_note": (
            "Vocabulary figures are a proxy: the number of other repository documents that use "
            "each tested word, plus its length and estimated syllables. Most target words appear "
            "in no other document, so length and syllables carry most of the signal. The "
            "educator's rating of each word replaces these figures."
        ),
        "forms": reports,
        "flags": _flags(reports),
    }


def render_markdown(report: dict) -> str:
    forms = report["forms"]
    names = [form["form_type"] for form in forms]
    lines = ["# English diagnostic form equivalence", ""]

    def row(label, values):
        lines.append(f"| {label} | " + " | ".join(str(value) for value in values) + " |")

    lines += ["## Structure", "", "| Measure | " + " | ".join(names) + " |",
              "| --- |" + " --- |" * len(forms)]
    row("Questions", [f["structure"]["questions"] for f in forms])
    row("Scored parts", [f["structure"]["parts"] for f in forms])
    tasks = sorted({task for f in forms for task in f["structure"]["parts_by_task"]})
    for task in tasks:
        row(f"{task} parts", [f["structure"]["parts_by_task"].get(task, 0) for f in forms])
    row("Matches declared distribution", [f["structure"]["matches_declared_distribution"] for f in forms])

    lines += ["", "## Passages (words)", "", "| Task | " + " | ".join(names) + " |",
              "| --- |" + " --- |" * len(forms)]
    for task in ("reading_comprehension", "banked_cloze", "open_cloze"):
        cells = []
        for form in forms:
            items = [p for p in form["passages"]["items"] if p["task"] == task]
            cells.append(", ".join(str(p["words"]) for p in items) or "-")
        row(task, cells)
    row("Mean sentence words (reading)", [
        round(mean(p["mean_sentence_words"] for p in f["passages"]["items"]
                   if p["task"] == "reading_comprehension"), 1) for f in forms
    ])
    row("3+ syllable word share (reading)", [
        round(mean(p["three_plus_syllable_share"] for p in f["passages"]["items"]
                   if p["task"] == "reading_comprehension"), 3) for f in forms
    ])

    lines += ["", "## Options (single choice, excluding banked cloze)", "",
              "| Measure | " + " | ".join(names) + " |", "| --- |" + " --- |" * len(forms)]
    for label, field in (
        ("Parts", "single_choice_parts"),
        ("Mean key characters", "mean_key_characters"),
        ("Mean distractor characters", "mean_distractor_characters"),
        ("Key / distractor ratio", "key_to_distractor_ratio"),
        ("Key uniquely longest", "key_uniquely_longest"),
        ("Key uniquely shortest", "key_uniquely_shortest"),
    ):
        row(label, [f["options"][field] for f in forms])

    lines += ["", "## Key positions", "", "| Measure | " + " | ".join(names) + " |",
              "| --- |" + " --- |" * len(forms)]
    row("Single choice A/B/C/D", [
        " ".join(f"{k}{v}" for k, v in f["keys"]["single_choice"].items()) for f in forms
    ])
    row("Largest share", [f["keys"]["largest_share"] for f in forms])
    row("Banked cloze bank letters", [
        " ".join(f"{k}{v}" for k, v in f["keys"]["banked_cloze"].items()) for f in forms
    ])

    lines += ["", "## Vocabulary proxy", "", report["proxy_note"],
              f"Corpus: {report['corpus_documents']} documents."]
    for title, section in (
        ("Vocabulary-in-context targets", "vocabulary"),
        ("Cloze answers (banked and open)", "cloze_answers"),
    ):
        lines += ["", f"### {title}", "", "| Measure | " + " | ".join(names) + " |",
                  "| --- |" + " --- |" * len(forms)]
        for label, field in (
            ("Tested words", "targets"),
            ("Mean document share", "mean_document_share"),
            ("Median documents", "median_documents"),
            ("In fewer than 5 documents", "in_fewer_than_5_documents"),
            ("Mean letters", "mean_letters"),
            ("Mean syllables", "mean_syllables"),
        ):
            row(label, [f[section].get(field, "-") for f in forms])
        row("Rarest (documents)", [
            ", ".join(f"{r['target']} ({r['documents']})" for r in f[section].get("rarest", []))
            for f in forms
        ])

    lines += ["", "## Flags", ""]
    lines += [f"- {flag}" for flag in report["flags"]] or ["- None."]
    return "\n".join(lines) + "\n"
