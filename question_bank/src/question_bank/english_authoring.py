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

from .english_models import EnglishModel, EnglishObjectiveQuestion
from .english_validation import EnglishIssue, validate_english_foundation

ENGLISH_BATCH_PATTERN = r"^english-(ev|eg|eb|eo|er|ex)-b[0-9]{3}$"


class EnglishBatchReviewState(EnglishModel):
    english: Literal["pending", "approved", "changes_requested"] = "pending"
    editorial: Literal["pending", "approved", "changes_requested"] = "pending"


class EnglishBatchManifest(EnglishModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    batch_id: str = Field(pattern=ENGLISH_BATCH_PATTERN)
    bank_key: str = Field(pattern=r"^english-(ev|eg|eb|eo|er|ex)-v[0-9]+$")
    module_code: str = Field(pattern=r"^E[0-9]+$")
    status: Literal[
        "planned", "draft", "ready_for_review", "changes_requested", "approved"
    ]
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
                    EnglishDuplicateMatch(
                        "exact_prompt", first.stable_key, second.stable_key, 1.0
                    )
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
    return response.canonical_answer


def export_english_reviewer_batch(
    root: Path, batch_path: Path, output: Path
) -> dict[str, object]:
    foundation = validate_english_foundation(root)
    if not foundation.valid:
        raise ValueError("English foundation must validate before reviewer export")
    batch = load_english_batch(batch_path)
    questions = {question.stable_key: question for question in foundation.questions}
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
        markdown.extend(
            [
                "",
                f"## {question.stable_key} · {question.title}",
                "",
                f"Outcome {question.outcome_code} · Difficulty {question.difficulty} · {question.exposure_pool}",
                "",
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
            options = response.get("options", [])
            option_html = "".join(
                f"<li><strong>{html.escape(option['key'])}.</strong> {html.escape(option['text'])}</li>"
                for option in options
            )
            part_html.append(
                f"<section><p>{html.escape(part.prompt)}</p><ol>{option_html}</ol>"
                f"<p class='answer'><strong>Answer:</strong> {html.escape(_part_answer(part))}</p>"
                f"<p><strong>Explanation:</strong> {html.escape(part.correct_explanation)}</p></section>"
            )
        cards.append(
            f"<article><p class='meta'>{html.escape(question.stable_key)} · Outcome "
            f"{html.escape(question.outcome_code)} · Difficulty {question.difficulty} · "
            f"{html.escape(question.exposure_pool)}</p><h2>{html.escape(question.title)}</h2>"
            f"{''.join(part_html)}</article>"
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
</head><body><h1>{html.escape(batch.batch_id)}</h1><p>Protected English and editorial reviewer packet.</p>{''.join(cards)}</body></html>"""
    (output / "index.html").write_text(page)
    digest = hashlib.sha256((output / "index.html").read_bytes()).hexdigest()
    return {
        "batch_id": batch.batch_id,
        "question_count": len(selected),
        "output": str(output),
        "preview_sha256": digest,
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
        (claim for claim in reversed(registry.claims) if claim.batch_id == batch_id and claim.active),
        None,
    )
    if claim is None:
        raise ValueError(f"English batch {batch_id} has no active claim")
    if claim.owner != owner:
        raise ValueError(f"English batch {batch_id} is claimed by {claim.owner}")
    claim.released_at = now or datetime.now(UTC)
    registry_path.write_text(json.dumps(registry.model_dump(mode="json"), indent=2) + "\n")
    return {"batch_id": batch_id, "status": "released", "owner": owner}
