"""Batch planning, claims, duplicate checks and reviewer exports for English."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from .english_models import (
    EnglishAssessmentForm,
    EnglishLesson,
    EnglishModel,
    EnglishObjectiveQuestion,
    EnglishPassage,
)
from .english_validation import (
    EnglishFoundationReport,
    EnglishIssue,
    validate_english_foundation,
)

ENGLISH_BATCH_PATTERN = r"^english-(ev|eg|eb|eo|er|ex)-b[0-9]{3}$"


class EnglishBatchReviewState(EnglishModel):
    english: Literal["pending", "approved", "changes_requested"] = "pending"
    editorial: Literal["pending", "approved", "changes_requested"] = "pending"


class EnglishBatchManifest(EnglishModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    batch_id: str = Field(pattern=ENGLISH_BATCH_PATTERN)
    bank_key: str = Field(pattern=r"^english-(ev|eg|eb|eo|er|ex)-v[0-9]+$")
    module_code: str = Field(pattern=r"^E[0-9]+$")
    status: Literal["planned", "draft", "ready_for_review", "changes_requested", "approved"]
    expected_question_count: int = Field(ge=1, le=30)
    question_keys: list[str] = Field(min_length=1, max_length=30)
    review: EnglishBatchReviewState = Field(default_factory=EnglishBatchReviewState)

    @model_validator(mode="after")
    def batch_is_consistent(self):
        if len(self.question_keys) != len(set(self.question_keys)):
            raise ValueError("Batch question keys must be unique")
        if len(self.question_keys) != self.expected_question_count:
            raise ValueError("Batch question count must match expected_question_count")
        if self.status == "approved" and (
            self.review.english != "approved" or self.review.editorial != "approved"
        ):
            raise ValueError("An approved English batch needs English and editorial approval")
        batch_subject = self.batch_id.split("-")[1]
        bank_subject = self.bank_key.split("-")[1]
        if batch_subject != bank_subject:
            raise ValueError("Batch and bank skill prefixes must match")
        return self


class EnglishBatchClaim(EnglishModel):
    batch_id: str = Field(pattern=ENGLISH_BATCH_PATTERN)
    owner: str = Field(min_length=2, max_length=100)
    branch: str = Field(min_length=3, max_length=240, pattern=r"^[A-Za-z0-9._/-]+$")
    claimed_at: datetime
    released_at: datetime | None = None

    @model_validator(mode="after")
    def release_follows_claim(self):
        if self.released_at is not None and self.released_at < self.claimed_at:
            raise ValueError("released_at cannot precede claimed_at")
        return self

    @property
    def active(self):
        return self.released_at is None


class EnglishBatchClaimRegistry(EnglishModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    claims: list[EnglishBatchClaim]

    @model_validator(mode="after")
    def active_claims_are_exclusive(self):
        active = [claim for claim in self.claims if claim.active]
        batch_ids = [claim.batch_id for claim in active]
        branches = [claim.branch for claim in active]
        if len(batch_ids) != len(set(batch_ids)):
            raise ValueError("Each English batch can have only one active claim")
        if len(branches) != len(set(branches)):
            raise ValueError("Each branch can claim only one active English batch")
        return self


@dataclass(frozen=True)
class EnglishDuplicateMatch:
    kind: Literal["exact_prompt", "near_prompt"]
    first_key: str
    second_key: str
    similarity: float


@dataclass(frozen=True)
class EnglishRouteReviewSelection:
    """Exact authored records referenced by one protected English route packet."""

    lessons: tuple[EnglishLesson, ...]
    forms: tuple[EnglishAssessmentForm, ...]
    questions: tuple[EnglishObjectiveQuestion, ...]
    passages: tuple[EnglishPassage, ...]
    parallel_retry_keys: frozenset[str]


@dataclass
class EnglishAuthoringReport:
    batches: list[EnglishBatchManifest] = field(default_factory=list)
    questions: list[EnglishObjectiveQuestion] = field(default_factory=list)
    duplicates: list[EnglishDuplicateMatch] = field(default_factory=list)
    issues: list[EnglishIssue] = field(default_factory=list)

    @property
    def errors(self):
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self):
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def valid(self):
        return not self.errors

    def as_dict(self):
        return {
            "valid": self.valid,
            "batch_count": len(self.batches),
            "question_count": len(self.questions),
            "duplicate_count": len(self.duplicates),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
            "duplicates": [asdict(match) for match in self.duplicates],
        }


def _issue(report, severity, code, path, message):
    report.issues.append(EnglishIssue(severity, code, str(path), message))


def _question_prompt(question: EnglishObjectiveQuestion) -> str:
    return " ".join([question.instructions, *(part.prompt for part in question.parts)])


def _normalise_prompt(value: str, *, template: bool = False) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    if template:
        value = re.sub(r"\b\d+(?:\.\d+)?\b", "#", value)
        value = re.sub(r"[“”\"'‘’][^“”\"'‘’]{2,40}[“”\"'‘’]", "<target>", value)
    return " ".join(re.findall(r"[a-z]+|#|<target>", value))


def detect_english_duplicates(
    questions: list[EnglishObjectiveQuestion], *, near_threshold: float = 0.9
) -> list[EnglishDuplicateMatch]:
    matches = []
    for index, first in enumerate(questions):
        first_exact = _normalise_prompt(_question_prompt(first))
        first_template = _normalise_prompt(_question_prompt(first), template=True)
        for second in questions[index + 1 :]:
            second_exact = _normalise_prompt(_question_prompt(second))
            if first_exact == second_exact:
                matches.append(
                    EnglishDuplicateMatch("exact_prompt", first.stable_key, second.stable_key, 1.0)
                )
                continue
            second_template = _normalise_prompt(_question_prompt(second), template=True)
            similarity = SequenceMatcher(None, first_template, second_template).ratio()
            if similarity >= near_threshold:
                matches.append(
                    EnglishDuplicateMatch(
                        "near_prompt",
                        first.stable_key,
                        second.stable_key,
                        round(similarity, 4),
                    )
                )
    return matches


def load_english_batch(path: Path) -> EnglishBatchManifest:
    return EnglishBatchManifest.model_validate_json(path.read_text())


def load_english_claims(path: Path) -> EnglishBatchClaimRegistry:
    return EnglishBatchClaimRegistry.model_validate_json(path.read_text())


def validate_english_authoring(
    root: Path, *, near_duplicate_threshold: float = 0.9
) -> EnglishAuthoringReport:
    root = root.resolve()
    foundation = validate_english_foundation(root)
    report = EnglishAuthoringReport(
        questions=foundation.questions,
        issues=list(foundation.issues),
    )
    question_by_key = {question.stable_key: question for question in report.questions}
    assignments: dict[str, str] = {}
    batch_root = root / "authoring/batches"
    for path in sorted(batch_root.glob("*.json")):
        try:
            batch = load_english_batch(path)
        except (OSError, ValueError, ValidationError) as exc:
            _issue(report, "error", "invalid_english_batch", path, str(exc))
            continue
        if path.stem != batch.batch_id:
            _issue(report, "error", "english_batch_filename", path, batch.batch_id)
        for key in batch.question_keys:
            question = question_by_key.get(key)
            if question is None:
                _issue(report, "error", "missing_batch_question", path, key)
                continue
            if question.bank_key != batch.bank_key:
                _issue(report, "error", "wrong_batch_bank", path, key)
            if key in assignments:
                _issue(
                    report,
                    "error",
                    "question_assigned_twice",
                    path,
                    f"{key} is already in {assignments[key]}",
                )
            assignments[key] = batch.batch_id
        report.batches.append(batch)
    unassigned = sorted(set(question_by_key) - set(assignments))
    if unassigned:
        _issue(
            report,
            "error",
            "unassigned_english_questions",
            batch_root,
            f"Questions without a batch: {unassigned}",
        )
    report.duplicates = detect_english_duplicates(
        report.questions, near_threshold=near_duplicate_threshold
    )
    for duplicate in report.duplicates:
        _issue(
            report,
            "error",
            duplicate.kind,
            root / "questions",
            f"{duplicate.first_key} and {duplicate.second_key}: {duplicate.similarity:.4f}",
        )
    return report


def question_batch_map(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted((root / "authoring/batches").glob("*.json")):
        batch = load_english_batch(path)
        for key in batch.question_keys:
            result[key] = batch.batch_id
    return result


def _answer_summary(question: EnglishObjectiveQuestion) -> str:
    values = []
    for part in question.parts:
        values.append(f"{part.position}. {_part_answer(part)}")
    return " | ".join(values)


def _part_answer(part) -> str:
    response = part.response
    if response.type == "single_choice":
        return response.correct_key
    if response.type == "multiple_response":
        return ", ".join(response.correct_keys)
    if response.accepted_alternatives:
        alternatives = ", ".join(response.accepted_alternatives)
        return f"{response.canonical_answer} (also accepted: {alternatives})"
    return response.canonical_answer


def export_english_reviewer_batch(root: Path, batch_path: Path, output: Path) -> dict[str, object]:
    foundation = validate_english_foundation(root)
    if not foundation.valid:
        raise ValueError("English foundation must validate before reviewer export")
    batch = load_english_batch(batch_path)
    questions = {question.stable_key: question for question in foundation.questions}
    passages = {(passage.stable_key, passage.revision): passage for passage in foundation.passages}
    selected = [questions[key] for key in batch.question_keys]
    output.mkdir(parents=True, exist_ok=True)

    markdown = [
        f"# {batch.batch_id}",
        "",
        f"English decision: `{batch.review.english}`",
        f"Editorial decision: `{batch.review.editorial}`",
        "",
        "Record corrections against the exact stable key and revision.",
    ]
    rows = []
    cards = []
    for question in selected:
        passage = (
            passages[(question.passage_ref.stable_key, question.passage_ref.revision)]
            if question.passage_ref is not None
            else None
        )
        bank = (
            question.parts[0].response.options if question.question_type == "banked_cloze" else []
        )
        markdown.extend(
            [
                "",
                f"## {question.stable_key} · {question.title}",
                "",
                f"Outcome {question.outcome_code} · Difficulty {question.difficulty} · {question.exposure_pool}",
                "",
                f"**Instructions:** {question.instructions}",
                "",
                *(
                    [f"**Passage: {passage.title}**", "", *passage.paragraphs, ""]
                    if passage is not None
                    else []
                ),
                *(
                    ["**Shared word bank:** " + ", ".join(option.text for option in bank), ""]
                    if bank
                    else []
                ),
                *[part.prompt for part in question.parts],
                "",
                f"**Answer:** {_answer_summary(question)}",
            ]
        )
        rows.append(
            {
                "stable_key": question.stable_key,
                "revision": question.revision,
                "outcome_code": question.outcome_code,
                "difficulty": question.difficulty,
                "exposure_pool": question.exposure_pool,
                "english_decision": "pending",
                "editorial_decision": "pending",
                "notes": "",
            }
        )
        part_html = []
        for part in question.parts:
            response = part.response.model_dump(mode="json")
            options = [] if bank else response.get("options", [])
            option_html = "".join(
                f"<li><strong>{html.escape(option['key'])}.</strong> {html.escape(option['text'])}</li>"
                for option in options
            )
            part_html.append(
                f"<section><p>{html.escape(part.prompt)}</p><ol>{option_html}</ol>"
                f"<p class='answer'><strong>Answer:</strong> {html.escape(_part_answer(part))}</p>"
                f"<p><strong>Explanation:</strong> {html.escape(part.correct_explanation)}</p></section>"
            )
        passage_html = ""
        if passage is not None:
            paragraphs = "".join(
                f"<p>{html.escape(paragraph)}</p>" for paragraph in passage.paragraphs
            )
            passage_html = (
                f"<section class='passage'><h3>{html.escape(passage.title)}</h3>"
                f"{paragraphs}</section>"
            )
        bank_html = ""
        if bank:
            choices = "".join(
                f"<li><strong>{html.escape(option.key)}.</strong> {html.escape(option.text)}</li>"
                for option in bank
            )
            bank_html = f"<section><h3>Shared word bank</h3><ol>{choices}</ol></section>"
        cards.append(
            f"<article><p class='meta'>{html.escape(question.stable_key)} · Outcome "
            f"{html.escape(question.outcome_code)} · Difficulty {question.difficulty} · "
            f"{html.escape(question.exposure_pool)}</p><h2>{html.escape(question.title)}</h2>"
            f"<p><strong>Instructions:</strong> {html.escape(question.instructions)}</p>"
            f"{passage_html}{bank_html}{''.join(part_html)}</article>"
        )

    (output / "review.md").write_text("\n".join(markdown) + "\n")
    with (output / "review.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{html.escape(batch.batch_id)} English reviewer packet</title>
<style>body{{font:16px/1.55 system-ui;max-width:960px;margin:auto;padding:32px;background:#f7faf9;color:#123f40}}article{{background:white;border:1px solid #cbdedb;border-radius:18px;padding:24px;margin:24px 0}}.meta{{color:#087f75;font-weight:700}}.answer{{background:#fef3c7;padding:12px;border-radius:10px}}li{{margin:.5rem 0}}</style>
</head><body><h1>{html.escape(batch.batch_id)}</h1><p>Protected English and editorial reviewer packet.</p>{"".join(cards)}</body></html>"""
    (output / "index.html").write_text(page)
    digest = hashlib.sha256((output / "index.html").read_bytes()).hexdigest()
    return {
        "batch_id": batch.batch_id,
        "question_count": len(selected),
        "output": str(output),
        "preview_sha256": digest,
    }


def _without_review_workflow_metadata(value):
    if isinstance(value, list):
        return [_without_review_workflow_metadata(item) for item in value]
    if not isinstance(value, dict):
        return value
    ignored = {
        "revision",
        "status",
        "review",
        "reviewed_at",
        "reviewed_by",
        "review_notes",
    }
    return {
        key: _without_review_workflow_metadata(item)
        for key, item in value.items()
        if key not in ignored
    }


def english_review_fingerprint(value) -> str:
    """Hash learner-visible English semantics while excluding workflow metadata."""

    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    payload = _without_review_workflow_metadata(payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _route_question_html(question, passages) -> str:
    passage = (
        passages[(question.passage_ref.stable_key, question.passage_ref.revision)]
        if question.passage_ref is not None
        else None
    )
    shared_bank = (
        question.parts[0].response.options
        if question.question_type == "banked_cloze"
        else []
    )
    passage_html = ""
    if passage is not None:
        paragraphs = "".join(
            f"<p>{html.escape(paragraph)}</p>" for paragraph in passage.paragraphs
        )
        passage_html = (
            f"<section class='passage'><h4>{html.escape(passage.title)}</h4>"
            f"{paragraphs}<p class='small'>{html.escape(passage.attribution)}</p></section>"
        )
    bank_html = ""
    if shared_bank:
        choices = "".join(
            f"<li><strong>{html.escape(option.key)}.</strong> "
            f"{html.escape(option.text)}</li>"
            for option in shared_bank
        )
        bank_html = f"<section><h4>Shared word bank</h4><ol>{choices}</ol></section>"
    part_html = []
    for part in question.parts:
        response = part.response.model_dump(mode="json")
        options = [] if shared_bank else response.get("options", [])
        option_html = "".join(
            f"<li><strong>{html.escape(option['key'])}.</strong> "
            f"{html.escape(option['text'])}</li>"
            for option in options
        )
        rationales = response.get("choice_rationales", {})
        rationale_html = "".join(
            f"<li><strong>{html.escape(key)}:</strong> {html.escape(value)}</li>"
            for key, value in sorted(rationales.items())
        )
        part_html.append(
            f"<section class='part'><p><strong>Part {part.position}.</strong> "
            f"{html.escape(part.prompt)}</p><ol>{option_html}</ol>"
            f"<p class='answer'><strong>Answer:</strong> "
            f"{html.escape(_part_answer(part))}</p>"
            f"<p><strong>Explanation:</strong> "
            f"{html.escape(part.correct_explanation)}</p>"
            f"{f'<details><summary>Option rationales</summary><ul>{rationale_html}</ul></details>' if rationale_html else ''}"
            "</section>"
        )
    return (
        f"<article class='question' id='question-{html.escape(question.stable_key)}'>"
        f"<p class='meta'>{html.escape(question.stable_key)} · revision {question.revision} · "
        f"Outcome {html.escape(question.outcome_code)} · Difficulty {question.difficulty} · "
        f"{html.escape(question.exposure_pool)}</p>"
        f"<h3>{html.escape(question.title)}</h3>"
        f"<p><strong>Instructions:</strong> {html.escape(question.instructions)}</p>"
        f"{passage_html}{bank_html}{''.join(part_html)}</article>"
    )


def english_route_review_selection(
    foundation: EnglishFoundationReport,
    *,
    route: Literal["full", "core", "sprint"] = "sprint",
) -> EnglishRouteReviewSelection:
    """Resolve and validate the exact records included in one route review session."""

    if not foundation.valid or foundation.catalogue is None:
        raise ValueError("English foundation must validate before route reviewer export")

    catalogue = foundation.catalogue
    route_keys = catalogue.route_lesson_keys(route)
    lessons_by_key = {lesson.stable_key: lesson for lesson in foundation.lessons}
    missing_lessons = sorted(set(route_keys) - set(lessons_by_key))
    if missing_lessons:
        raise ValueError(f"The {route} route has unauthored lessons: {missing_lessons}")
    lessons = tuple(lessons_by_key[key] for key in route_keys)
    route_key_set = set(route_keys)
    forms = tuple(
        sorted(
            (
                form
                for form in foundation.forms
                if form.form_type == "checkpoint"
                and set(form.mastery_lesson_keys) <= route_key_set
            ),
            key=lambda form: (int(form.module_code[1:]), form.form_key),
        )
    )
    form_modules = [form.module_code for form in forms]
    if len(forms) != 20 or any(form_modules.count(f"E{index}") != 2 for index in range(10)):
        raise ValueError("The route reviewer packet requires two checkpoints for every E0–E9 module")

    lesson_question_keys = {
        key for lesson in lessons for section in lesson.sections for key in section.question_keys
    }
    parallel_retry_keys = frozenset(
        question.stable_key
        for question in foundation.questions
        if question.exposure_pool == "retry_review"
        and question.parallel_form_of in lesson_question_keys
    )
    if len(parallel_retry_keys) != len(route_keys):
        raise ValueError(
            f"The {route} route requires one parallel retry for every lesson; "
            f"found {len(parallel_retry_keys)} for {len(route_keys)} lessons"
        )
    form_question_keys = {key for form in forms for key in form.question_keys}
    selected_question_keys = sorted(
        lesson_question_keys | parallel_retry_keys | form_question_keys
    )
    questions_by_key = {
        question.stable_key: question for question in foundation.questions
    }
    missing_questions = sorted(set(selected_question_keys) - set(questions_by_key))
    if missing_questions:
        raise ValueError(f"The route reviewer packet has missing questions: {missing_questions}")
    questions = tuple(questions_by_key[key] for key in selected_question_keys)
    passages_by_key = {
        (passage.stable_key, passage.revision): passage
        for passage in foundation.passages
    }
    passage_keys = sorted(
        {
            (question.passage_ref.stable_key, question.passage_ref.revision)
            for question in questions
            if question.passage_ref is not None
        }
    )
    passages = tuple(passages_by_key[key] for key in passage_keys)
    return EnglishRouteReviewSelection(
        lessons=lessons,
        forms=forms,
        questions=questions,
        passages=passages,
        parallel_retry_keys=parallel_retry_keys,
    )


def export_english_route_reviewer_packet(
    root: Path,
    output: Path,
    *,
    route: Literal["full", "core", "sprint"] = "sprint",
) -> dict[str, object]:
    """Export one deterministic route packet without changing review or publication state."""

    foundation = validate_english_foundation(root)
    selection = english_route_review_selection(foundation, route=route)
    catalogue = foundation.catalogue
    lessons = selection.lessons
    forms = selection.forms
    questions = selection.questions
    passages = selection.passages
    parallel_retry_keys = selection.parallel_retry_keys
    passages_by_key = {
        (passage.stable_key, passage.revision): passage
        for passage in foundation.passages
    }

    output.mkdir(parents=True, exist_ok=True)
    lesson_manifest = [
        {
            "stable_key": lesson.stable_key,
            "lesson_code": lesson.lesson_code,
            "revision": lesson.revision,
            "status": lesson.status,
            "fingerprint": english_review_fingerprint(lesson),
        }
        for lesson in lessons
    ]
    form_manifest = [
        {
            "form_key": form.form_key,
            "revision": form.revision,
            "module_code": form.module_code,
            "status": form.status,
            "paired_form_key": form.paired_form_key,
            "fingerprint": english_review_fingerprint(form),
        }
        for form in forms
    ]
    question_manifest = [
        {
            "stable_key": question.stable_key,
            "revision": question.revision,
            "status": question.status,
            "exposure_pool": question.exposure_pool,
            "fingerprint": english_review_fingerprint(question),
        }
        for question in questions
    ]
    passage_manifest = [
        {
            "stable_key": passage.stable_key,
            "revision": passage.revision,
            "status": passage.status,
            "content_sha256": passage.content_sha256,
            "fingerprint": english_review_fingerprint(passage),
        }
        for passage in passages
    ]
    manifest = {
        "schema_version": "1.0.0",
        "packet_key": f"english-{route}-route-v3b-review",
        "curriculum_version": catalogue.version_key,
        "route": route,
        "lesson_count": len(lessons),
        "checkpoint_form_count": len(forms),
        "parallel_retry_count": len(parallel_retry_keys),
        "question_count": len(questions),
        "passage_count": len(passages),
        "lessons": lesson_manifest,
        "checkpoint_forms": form_manifest,
        "questions": question_manifest,
        "passages": passage_manifest,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )

    rows = []
    for item_type, items, key_field in (
        ("lesson", lesson_manifest, "stable_key"),
        ("checkpoint_form", form_manifest, "form_key"),
        ("question", question_manifest, "stable_key"),
        ("passage", passage_manifest, "stable_key"),
    ):
        for item in items:
            rows.append(
                {
                    "item_type": item_type,
                    "stable_key": item[key_field],
                    "revision": item["revision"],
                    "status": item["status"],
                    "fingerprint": item["fingerprint"],
                    "english_decision": "pending",
                    "editorial_decision": "pending",
                    "notes": "",
                }
            )
    with (output / "review.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    markdown = [
        f"# English {route.title()} route consolidated reviewer packet",
        "",
        "This packet is protected reviewer evidence. It does not publish content.",
        "",
        f"- Lessons: {len(lessons)}",
        f"- Reciprocal checkpoint forms: {len(forms)}",
        f"- Parallel lesson retries: {len(parallel_retry_keys)}",
        f"- Unique referenced question groups: {len(questions)}",
        f"- Referenced passages: {len(passages)}",
        "- English decision: `pending`",
        "- Editorial decision: `pending`",
        "",
        "## Review order",
        "",
        "1. Review the 16 lesson explanations and examples.",
        "2. Review the A/B checkpoint pairing, mastery scope and scored-part counts.",
        "3. Review every protected answer, explanation and option rationale.",
        "4. Record exclusions or corrections in `review.csv` against the pinned fingerprint.",
        "",
        "## Lessons",
        "",
        *[
            f"- {lesson.lesson_code} · {lesson.title} · `{lesson.stable_key}` revision {lesson.revision}"
            for lesson in lessons
        ],
        "",
        "## Checkpoint forms",
        "",
        *[
            f"- {form.module_code} · `{form.form_key}` · {form.expected_scored_part_count} scored parts · pair `{form.paired_form_key}`"
            for form in forms
        ],
    ]
    (output / "review.md").write_text("\n".join(markdown) + "\n")

    lesson_cards = []
    for lesson in lessons:
        sections = []
        for section in lesson.sections:
            content = "".join(f"<p>{html.escape(item)}</p>" for item in section.content)
            refs = "".join(
                f"<li><a href='#question-{html.escape(key)}'>{html.escape(key)}</a></li>"
                for key in section.question_keys
            )
            sections.append(
                f"<section><h4>{section.position}. {html.escape(section.title)}</h4>"
                f"{content}{f'<p><strong>Question references</strong></p><ul>{refs}</ul>' if refs else ''}</section>"
            )
        lesson_cards.append(
            f"<article class='lesson' id='lesson-{html.escape(lesson.stable_key)}'>"
            f"<p class='meta'>{html.escape(lesson.lesson_code)} · Outcome "
            f"{html.escape(lesson.outcome_code)} · revision {lesson.revision} · "
            f"{html.escape(lesson.status)}</p><h3>{html.escape(lesson.title)}</h3>"
            f"<p>{html.escape(lesson.summary)}</p>{''.join(sections)}</article>"
        )
    form_cards = []
    for form in forms:
        question_links = "".join(
            f"<li><a href='#question-{html.escape(key)}'>{html.escape(key)}</a></li>"
            for key in form.question_keys
        )
        mastery = ", ".join(form.mastery_lesson_keys)
        distribution = ", ".join(
            f"{key.replace('_', ' ')}: {value}"
            for key, value in form.task_part_distribution.items()
        )
        form_cards.append(
            f"<article class='form' id='form-{html.escape(form.form_key)}'>"
            f"<p class='meta'>{html.escape(form.module_code)} · revision {form.revision} · "
            f"{html.escape(form.status)}</p><h3>{html.escape(form.title)}</h3>"
            f"<p><strong>Pair:</strong> {html.escape(form.paired_form_key or 'none')}</p>"
            f"<p><strong>Mastery scope:</strong> {html.escape(mastery)}</p>"
        f"<p><strong>Scored parts:</strong> {form.expected_scored_part_count} "
            f"({html.escape(distribution)})</p><ul>{question_links}</ul></article>"
        )
    question_cards = [
        _route_question_html(question, passages_by_key) for question in questions
    ]
    lesson_nav = "".join(
        f"<li><a href='#lesson-{html.escape(lesson.stable_key)}'>"
        f"{html.escape(lesson.lesson_code)} · {html.escape(lesson.title)}</a></li>"
        for lesson in lessons
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>English {html.escape(route.title())} route reviewer packet</title>
<style>body{{font:16px/1.55 system-ui;max-width:1120px;margin:auto;padding:32px;background:#f7faf9;color:#123f40}}article{{background:white;border:1px solid #cbdedb;border-radius:18px;padding:24px;margin:24px 0}}h1,h2,h3,h4{{line-height:1.2}}.summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.summary div{{background:#e8f3f1;border-radius:12px;padding:16px}}.meta{{color:#087f75;font-weight:700}}.answer{{background:#fef3c7;padding:12px;border-radius:10px}}.passage{{border-left:4px solid #087f75;padding-left:16px}}.part{{border-top:1px solid #dbe8e6;padding-top:12px}}.small{{font-size:.875rem;color:#526d6d}}li{{margin:.4rem 0}}a{{color:#066a63}}@media(max-width:700px){{body{{padding:16px}}.summary{{grid-template-columns:1fr 1fr}}}}</style>
</head><body><p class="meta">PROTECTED REVIEWER EVIDENCE · DRAFT ONLY</p><h1>English {html.escape(route.title())} route</h1><p>Review the exact pinned lesson, form, question and passage revisions below. Recording a decision does not publish the content.</p><div class="summary"><div><strong>{len(lessons)}</strong><br>lessons</div><div><strong>{len(forms)}</strong><br>checkpoint forms</div><div><strong>{len(parallel_retry_keys)}</strong><br>parallel retries</div><div><strong>{len(questions)}</strong><br>question groups</div></div><p class="small">Referenced passages: {len(passages)}</p><h2>Contents</h2><ol>{lesson_nav}</ol><h2>1. {html.escape(route.title())} lessons</h2>{''.join(lesson_cards)}<h2>2. Protected checkpoint forms</h2>{''.join(form_cards)}<h2>3. Referenced questions and answers</h2>{''.join(question_cards)}</body></html>"""
    (output / "index.html").write_text(page)
    preview_sha256 = hashlib.sha256((output / "index.html").read_bytes()).hexdigest()
    return {
        "packet_key": manifest["packet_key"],
        "route": route,
        "lesson_count": len(lessons),
        "checkpoint_form_count": len(forms),
        "parallel_retry_count": len(parallel_retry_keys),
        "question_count": len(questions),
        "passage_count": len(passages),
        "review_item_count": len(rows),
        "output": str(output),
        "preview_sha256": preview_sha256,
    }


def claim_english_batch(
    registry_path: Path,
    root: Path,
    *,
    batch_id: str,
    owner: str,
    branch: str,
    now: datetime | None = None,
) -> dict:
    registry = load_english_claims(registry_path)
    report = validate_english_authoring(root)
    if not report.valid:
        raise ValueError("English authoring sources must validate before claiming a batch")
    available = {batch.batch_id for batch in report.batches}
    if batch_id not in available:
        raise ValueError(f"Unknown English batch {batch_id}")
    for claim in registry.claims:
        if claim.active and claim.batch_id == batch_id:
            if claim.owner == owner and claim.branch == branch:
                return {"batch_id": batch_id, "status": "already_claimed"}
            raise ValueError(f"English batch {batch_id} is already claimed")
        if claim.active and claim.branch == branch:
            raise ValueError(f"Branch {branch} already has an active English batch")
    registry.claims.append(
        EnglishBatchClaim(
            batch_id=batch_id,
            owner=owner,
            branch=branch,
            claimed_at=now or datetime.now(UTC),
        )
    )
    registry_path.write_text(json.dumps(registry.model_dump(mode="json"), indent=2) + "\n")
    return {"batch_id": batch_id, "status": "claimed", "owner": owner, "branch": branch}


def release_english_batch(
    registry_path: Path,
    *,
    batch_id: str,
    owner: str,
    now: datetime | None = None,
) -> dict:
    registry = load_english_claims(registry_path)
    claim = next(
        (
            claim
            for claim in reversed(registry.claims)
            if claim.batch_id == batch_id and claim.active
        ),
        None,
    )
    if claim is None:
        raise ValueError(f"English batch {batch_id} has no active claim")
    if claim.owner != owner:
        raise ValueError(f"English batch {batch_id} is claimed by {claim.owner}")
    claim.released_at = now or datetime.now(UTC)
    registry_path.write_text(json.dumps(registry.model_dump(mode="json"), indent=2) + "\n")
    return {"batch_id": batch_id, "status": "released", "owner": owner}
