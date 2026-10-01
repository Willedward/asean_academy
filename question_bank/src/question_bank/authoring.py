"""Controlled batch planning, validation, duplicate detection, and review exports."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from pydantic import Field, ValidationError, model_validator

from .catalogue import (
    BankBlueprint,
    BankTopic,
    OutcomeDistribution,
    SyllabusCatalogue,
    load_blueprint,
    load_catalogue,
)
from .checking import check_answer
from .difficulty import DIFFICULTY_DEFINITIONS, DIFFICULTY_KEYS
from .models import AlgebraicResponse, Model, NumericResponse, Question
from .validation import Issue, validate_catalogue

BATCH_SCHEMA_VERSION = "1.0.0"
HOUSE_RULES_SCHEMA_VERSION = "1.0.0"
BATCH_ID_PATTERN = r"^g3-sec[12]-[ngs][0-9]+-b[0-9]{3}$"
DEFAULT_DIFFICULTY_DISTRIBUTION = {"1": 21, "2": 31, "3": 31, "4": 16, "5": 5}
DEFAULT_STYLE_REFERENCES = [
    "backend_resources/sample_papers/TMS 2023 1E Math P2 (QP).pdf",
    "backend_resources/sample_papers/TMS 2023 1E Math P2 (ANS).pdf",
    "backend_resources/sample_papers/2022 Sec 2 Express Math EOY Anglo Chinese School with Answers.pdf",
    "backend_resources/sample_papers/2022 Sec 2 Express Math EOY Canberra Secondary with Answers.pdf",
    "backend_resources/sample_papers/Math - Sec2 - SA2 - 2023 - Zhonghua Sec.pdf",
]


class GeneratorMetadata(Model):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    generator_version: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)


class SourceReference(Model):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: Literal["syllabus", "style", "house_rules", "other"]


class BatchAllocation(Model):
    outcome_code: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    difficulty: int = Field(ge=1, le=5)
    count: int = Field(ge=1, le=30)


class ReviewState(Model):
    mathematics: Literal["pending", "approved", "changes_requested"] = "pending"
    editorial: Literal["pending", "approved", "changes_requested"] = "pending"


class QuestionBatchManifest(Model):
    schema_version: Literal["1.0.0"] = BATCH_SCHEMA_VERSION
    batch_id: str = Field(pattern=BATCH_ID_PATTERN)
    bank_key: str = Field(pattern=r"^g3-sec[12]-[ngs][0-9]+-v[0-9]+$")
    curriculum_version: str = Field(pattern=r"^[a-z0-9_]+$")
    school_level: Literal["secondary_1", "secondary_2"]
    topic_code: str = Field(pattern=r"^[NGS][0-9]+$")
    status: Literal[
        "planned", "draft", "ready_for_review", "changes_requested", "approved"
    ]
    created_at: datetime
    generator: GeneratorMetadata
    source_references: list[SourceReference] = Field(min_length=1)
    allocation: list[BatchAllocation] = Field(min_length=1)
    expected_question_count: int = Field(ge=20, le=30)
    question_keys: list[str] = Field(default_factory=list)
    review: ReviewState = Field(default_factory=ReviewState)

    @model_validator(mode="after")
    def manifest_is_consistent(self):
        expected_prefix = f"g3-sec{self.school_level[-1]}-{self.topic_code.lower()}"
        if not self.bank_key.startswith(f"{expected_prefix}-v"):
            raise ValueError("Batch bank_key must match school_level and topic_code")
        if not self.batch_id.startswith(f"{expected_prefix}-b"):
            raise ValueError("batch_id must match school_level and topic_code")
        cells = [(item.outcome_code, item.difficulty) for item in self.allocation]
        if len(cells) != len(set(cells)):
            raise ValueError("Batch allocation cells must be unique")
        if sum(item.count for item in self.allocation) != self.expected_question_count:
            raise ValueError("Batch allocation must add up to expected_question_count")
        if len(self.question_keys) != len(set(self.question_keys)):
            raise ValueError("Batch question_keys must be unique")
        if len(self.question_keys) != self.expected_question_count:
            raise ValueError("Every batch must reserve all allocated stable question keys")
        if self.status != "planned" and "unassigned" in {
            self.generator.provider,
            self.generator.model,
            self.generator.generator_version,
        }:
            raise ValueError("A started batch requires concrete generator metadata")
        if self.status == "approved" and (
            self.review.mathematics != "approved" or self.review.editorial != "approved"
        ):
            raise ValueError("An approved batch requires both review approvals")
        return self


class HouseRules(Model):
    schema_version: Literal["1.0.0"] = HOUSE_RULES_SCHEMA_VERSION
    version_key: str = Field(pattern=r"^[a-z0-9_]+$")
    locale: str = Field(min_length=1)
    language_variant: str = Field(min_length=1)
    measurement_system: Literal["metric"] = "metric"
    currency: str = Field(min_length=1)
    exact_answers_by_default: bool = True
    rounding_must_be_explicit: bool = True
    calculator_permission_per_question: bool = True
    error_carried_forward: bool = False
    prohibited_contexts: list[str]
    notes: list[str]


@dataclass
class BatchValidationReport:
    manifest: QuestionBatchManifest | None = None
    questions: list[Question] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

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
            "batch_id": self.manifest.batch_id if self.manifest else None,
            "status": self.manifest.status if self.manifest else None,
            "expected_question_count": (
                self.manifest.expected_question_count if self.manifest else None
            ),
            "question_count": len(self.questions),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
        }


@dataclass(frozen=True)
class DuplicateMatch:
    kind: Literal["exact_prompt", "near_prompt"]
    first_key: str
    second_key: str
    first_bank: str
    second_bank: str
    similarity: float


@dataclass
class PipelineValidationReport:
    blueprint_count: int = 0
    batch_reports: list[BatchValidationReport] = field(default_factory=list)
    question_count: int = 0
    duplicate_matches: list[DuplicateMatch] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

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
            "blueprint_count": self.blueprint_count,
            "batch_count": len(self.batch_reports),
            "question_count": self.question_count,
            "duplicate_count": len(self.duplicate_matches),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
            "duplicates": [asdict(match) for match in self.duplicate_matches],
            "batches": [batch.as_dict() for batch in self.batch_reports],
        }


def _issue(report, severity: str, code: str, path: Path | str, message: str) -> None:
    report.issues.append(Issue(severity, code, str(path), message))


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_manifest(path: Path) -> QuestionBatchManifest:
    return QuestionBatchManifest.model_validate_json(path.read_text())


def write_authoring_schemas(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    documents = {
        "question-v1.schema.json": Question.model_json_schema(),
        "question-batch-manifest-v1.schema.json": QuestionBatchManifest.model_json_schema(),
        "question-house-rules-v1.schema.json": HouseRules.model_json_schema(),
    }
    for filename, schema in documents.items():
        _write_json(output / filename, schema)


def _outcome_matrix(outcome_count: int, distribution: dict[str, int]) -> list[dict[str, int]]:
    matrix = [{level: 0 for level in DIFFICULTY_KEYS} for _ in range(outcome_count)]
    cursor = 0
    for level in DIFFICULTY_KEYS:
        for _ in range(distribution[level]):
            matrix[cursor % outcome_count][level] += 1
            cursor += 1
    return matrix


def build_blueprint(
    catalogue: SyllabusCatalogue,
    school_level: Literal["secondary_1", "secondary_2"],
    topic_code: str,
    *,
    question_count: int = 104,
) -> BankBlueprint:
    if question_count != 104:
        raise ValueError("The v1 generator currently supports the approved 104-question target")
    topic = catalogue.topic(topic_code)
    if topic is None:
        raise ValueError(f"Unknown syllabus topic {topic_code}")
    outcomes = [item for item in topic.outcomes if item.school_level == school_level]
    if not outcomes:
        raise ValueError(f"{topic_code} is not taught in {school_level}")
    matrix = _outcome_matrix(len(outcomes), DEFAULT_DIFFICULTY_DISTRIBUTION)
    bank_key = f"g3-sec{school_level[-1]}-{topic_code.lower()}-v1"
    return BankBlueprint(
        bank_id=uuid5(NAMESPACE_URL, f"https://nextscholar.sg/question-banks/{bank_key}"),
        bank_key=bank_key,
        bank_role="learning",
        curriculum_version=catalogue.version_key,
        school_level=school_level,
        course="Singapore G3 Mathematics",
        topic=BankTopic(code=topic.code, title=topic.title),
        status="draft",
        question_count=question_count,
        difficulty_distribution=DEFAULT_DIFFICULTY_DISTRIBUTION,
        outcome_distribution=[
            OutcomeDistribution(
                code=outcome.code,
                title=outcome.description,
                difficulty_counts=counts,
                total=sum(counts.values()),
            )
            for outcome, counts in zip(outcomes, matrix, strict=True)
        ],
        defaults={
            "calculator_allowed": True,
            "question_type": "structured",
            "hints_per_part": 2,
            "hint_policy": {
                "stage_1": "Point to the relevant concept or first decision without giving the answer.",
                "stage_2": "Give an explicit next method or intermediate setup without giving the final answer.",
                "automatic_mark_penalty": False,
            },
            "marking_policy": {
                "mark_types": ["B", "M", "A"],
                "score_each_part_independently": True,
                "error_carried_forward": False,
                "record_hint_usage_separately": True,
            },
            "response_types": ["numeric", "algebraic_expression"],
            "comparison_modes": [
                "exact_numeric",
                "absolute_tolerance",
                "rounded_dp",
                "rounded_sf",
                "symbolic_equivalence",
                "prime_factorisation",
                "ordered_numeric_list",
                "exact_relation",
                "exact_ratio",
            ],
            "diagram_formats": ["svg"],
            "math_rendering": ["KaTeX", "MathJax"],
        },
        difficulty_definitions=DIFFICULTY_DEFINITIONS,
        style_references=DEFAULT_STYLE_REFERENCES,
        publication_checks=[
            "exactly_104_questions",
            "difficulty_distribution_matches_blueprint",
            "outcome_distribution_matches_blueprint",
            "batch_manifests_cover_blueprint",
            "part_marks_sum_to_question_total",
            "exactly_two_ordered_hints_per_part",
            "canonical_and_accepted_answers_pass_checker",
            "solution_marks_do_not_exceed_part_marks",
            "asset_references_exist_and_checksums_match",
            "latex_fragments_render",
            "cross_bank_exact_and_near_duplicate_scan_passes",
            "mathematics_review_complete",
            "editorial_review_complete",
        ],
    )


def write_missing_blueprints(
    catalogue_path: Path,
    bank_catalogue_root: Path,
    *,
    question_count: int = 104,
) -> dict:
    catalogue = load_catalogue(catalogue_path)
    created: list[str] = []
    upgraded: list[str] = []
    preserved: list[str] = []
    for school_level in ("secondary_1", "secondary_2"):
        for topic in catalogue.topics:
            if not topic.outcome_codes(school_level):
                continue
            bank_root = bank_catalogue_root / school_level / topic.code.lower() / "v1"
            path = bank_root / "blueprint.json"
            if path.exists():
                current = load_blueprint(path)
                if current.question_count >= question_count:
                    preserved.append(str(path))
                    continue
                blueprint = build_blueprint(
                    catalogue, school_level, topic.code, question_count=question_count
                ).model_copy(update={"bank_id": current.bank_id})
                actual = Counter()
                for question_path in sorted((bank_root / "questions").glob("*.json")):
                    question = Question.model_validate_json(question_path.read_text())
                    actual[(question.primary_outcome, question.difficulty)] += 1
                target = {
                    (row.code, int(level)): count
                    for row in blueprint.outcome_distribution
                    for level, count in row.difficulty_counts.items()
                }
                exceeded = {
                    cell: count for cell, count in actual.items() if count > target.get(cell, 0)
                }
                if exceeded:
                    raise ValueError(
                        f"Existing questions exceed the upgraded blueprint cells: {exceeded}"
                    )
                _write_json(path, blueprint.model_dump(mode="json"))
                upgraded.append(str(path))
                continue
            blueprint = build_blueprint(
                catalogue, school_level, topic.code, question_count=question_count
            )
            _write_json(path, blueprint.model_dump(mode="json"))
            questions = bank_root / "questions"
            questions.mkdir(parents=True, exist_ok=True)
            (questions / ".gitkeep").touch()
            created.append(str(path))
    return {
        "created": created,
        "upgraded": upgraded,
        "preserved": preserved,
        "total": len(created) + len(upgraded) + len(preserved),
    }


def _batch_sizes(total: int, preferred: int = 26) -> list[int]:
    if total < 20:
        raise ValueError("A blueprint needs at least 20 questions for controlled batching")
    count = max(math.ceil(total / 30), round(total / preferred))
    while total // count < 20:
        count -= 1
    base, remainder = divmod(total, count)
    sizes = [base + (1 if index < remainder else 0) for index in range(count)]
    if any(size < 20 or size > 30 for size in sizes):
        raise ValueError(f"Cannot split {total} questions into batches of 20–30")
    return sizes


def _partition_allocations(
    cell_counts: dict[tuple[str, int], int], sizes: list[int]
) -> list[list[tuple[str, int]]]:
    batches: list[list[tuple[str, int]]] = [[] for _ in sizes]
    remaining = sizes.copy()
    cursor = 0
    for cell, count in cell_counts.items():
        for _ in range(count):
            while remaining[cursor] == 0:
                cursor = (cursor + 1) % len(batches)
            batches[cursor].append(cell)
            remaining[cursor] -= 1
            cursor = (cursor + 1) % len(batches)
    if any(remaining):
        raise ValueError(f"Batch partition left unused capacity: {remaining}")
    return batches


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_reference(repository_root: Path, relative: str, role: str) -> SourceReference:
    path = repository_root / relative
    if not path.is_file():
        raise FileNotFoundError(f"Missing authoring source reference: {relative}")
    return SourceReference(path=relative, sha256=_checksum(path), role=role)


def plan_blueprint_batches(
    blueprint_path: Path,
    repository_root: Path,
    syllabus_path: Path,
    house_rules_path: Path,
    *,
    preferred_batch_size: int = 26,
    prompt_version: str = "math-question-authoring-v1",
) -> list[Path]:
    blueprint = load_blueprint(blueprint_path)
    bank_root = blueprint_path.parent
    batch_root = bank_root / "batches"
    existing = sorted(batch_root.glob("*.json"))
    if existing:
        return existing
    existing_questions = [
        Question.model_validate_json(path.read_text())
        for path in sorted((bank_root / "questions").glob("*.json"))
    ]
    actual = Counter(
        (question.primary_outcome, question.difficulty)
        for question in existing_questions
    )
    remaining_cells: dict[tuple[str, int], int] = {}
    for row in blueprint.outcome_distribution:
        for level in DIFFICULTY_KEYS:
            cell = (row.code, int(level))
            remaining = row.difficulty_counts[level] - actual[cell]
            if remaining < 0:
                raise ValueError(f"Existing questions exceed blueprint allocation for {cell}")
            if remaining:
                remaining_cells[cell] = remaining
    remaining_count = sum(remaining_cells.values())
    if remaining_count == 0:
        return []
    sizes = _batch_sizes(remaining_count, preferred_batch_size)
    batches = _partition_allocations(remaining_cells, sizes)
    references = [
        _source_reference(
            repository_root,
            str(syllabus_path.resolve().relative_to(repository_root.resolve())),
            "syllabus",
        ),
        _source_reference(
            repository_root,
            str(house_rules_path.resolve().relative_to(repository_root.resolve())),
            "house_rules",
        ),
    ]
    references.extend(
        _source_reference(repository_root, path, "style")
        for path in blueprint.style_references
    )
    paths: list[Path] = []
    sequence = {
        int(level): (1 if blueprint.school_level == "secondary_1" else 501)
        for level in DIFFICULTY_KEYS
    }
    for question in existing_questions:
        suffix = int(question.stable_key.rsplit("-", 1)[1])
        sequence[question.difficulty] = max(sequence[question.difficulty], suffix + 1)
    for index, (size, chunk) in enumerate(zip(sizes, batches, strict=True), start=1):
        counts = Counter(chunk)
        question_keys: list[str] = []
        for _, difficulty in chunk:
            question_keys.append(
                f"{blueprint.topic.code.lower()}-l{difficulty}-{sequence[difficulty]:03d}"
            )
            sequence[difficulty] += 1
        manifest = QuestionBatchManifest(
            batch_id=(
                f"g3-sec{blueprint.school_level[-1]}-"
                f"{blueprint.topic.code.lower()}-b{index:03d}"
            ),
            bank_key=blueprint.bank_key,
            curriculum_version=blueprint.curriculum_version,
            school_level=blueprint.school_level,
            topic_code=blueprint.topic.code,
            status="planned",
            created_at=datetime.now(UTC),
            generator=GeneratorMetadata(
                provider="unassigned",
                model="unassigned",
                generator_version="unassigned",
                prompt_version=prompt_version,
            ),
            source_references=references,
            allocation=[
                BatchAllocation(outcome_code=outcome, difficulty=difficulty, count=count)
                for (outcome, difficulty), count in sorted(counts.items())
            ],
            expected_question_count=size,
            question_keys=question_keys,
        )
        path = batch_root / f"{manifest.batch_id}.json"
        _write_json(path, manifest.model_dump(mode="json"))
        paths.append(path)
    return paths


def plan_all_batches(
    bank_catalogue_root: Path,
    repository_root: Path,
    syllabus_path: Path,
    house_rules_path: Path,
    *,
    preferred_batch_size: int = 26,
) -> dict:
    planned: list[str] = []
    preserved: list[str] = []
    completed: list[str] = []
    for blueprint_path in sorted(bank_catalogue_root.glob("**/blueprint.json")):
        existing = sorted((blueprint_path.parent / "batches").glob("*.json"))
        paths = plan_blueprint_batches(
            blueprint_path,
            repository_root,
            syllabus_path,
            house_rules_path,
            preferred_batch_size=preferred_batch_size,
        )
        if not paths:
            completed.append(str(blueprint_path))
            continue
        target = preserved if existing else planned
        target.extend(str(path) for path in paths)
    return {
        "planned": planned,
        "preserved": preserved,
        "completed": completed,
        "batch_count": len(planned) + len(preserved),
    }


def _answer_candidates(question: Question):
    for part in question.parts:
        response = part.response
        if isinstance(response, NumericResponse):
            yield part.position, "canonical", response.canonical_answer, response
            for answer in response.accepted_answers:
                yield part.position, "accepted", answer, response
        elif isinstance(response, AlgebraicResponse):
            yield part.position, "canonical", (
                response.canonical_latex
                if response.comparison_mode == "prime_factorisation"
                else response.canonical_expression
            ), response
            for answer in response.accepted_equivalents:
                yield part.position, "accepted", answer, response


def validate_batch(
    manifest_path: Path,
    *,
    repository_root: Path,
    syllabus_path: Path,
) -> BatchValidationReport:
    report = BatchValidationReport()
    try:
        manifest = load_manifest(manifest_path)
        blueprint = load_blueprint(manifest_path.parent.parent / "blueprint.json")
        catalogue = load_catalogue(syllabus_path)
    except (OSError, ValueError, ValidationError) as exc:
        _issue(report, "error", "invalid_batch_contract", manifest_path, str(exc))
        return report
    report.manifest = manifest
    if manifest.bank_key != blueprint.bank_key:
        _issue(report, "error", "batch_bank_mismatch", manifest_path, blueprint.bank_key)
    if manifest.curriculum_version != blueprint.curriculum_version:
        _issue(
            report,
            "error",
            "batch_curriculum_mismatch",
            manifest_path,
            blueprint.curriculum_version,
        )
    topic = catalogue.topic(manifest.topic_code)
    allowed_outcomes = topic.outcome_codes(manifest.school_level) if topic else set()
    declared_cells = {
        (row.code, int(level)): count
        for row in blueprint.outcome_distribution
        for level, count in row.difficulty_counts.items()
    }
    for allocation in manifest.allocation:
        cell = (allocation.outcome_code, allocation.difficulty)
        if allocation.outcome_code not in allowed_outcomes:
            _issue(
                report,
                "error",
                "batch_unknown_outcome",
                manifest_path,
                allocation.outcome_code,
            )
        if allocation.count > declared_cells.get(cell, 0):
            _issue(
                report,
                "error",
                "batch_allocation_exceeds_blueprint",
                manifest_path,
                f"{cell}: {allocation.count} exceeds {declared_cells.get(cell, 0)}",
            )
    for reference in manifest.source_references:
        source = repository_root / reference.path
        if not source.is_file():
            _issue(report, "error", "missing_source_reference", source, reference.path)
        elif _checksum(source) != reference.sha256:
            _issue(report, "error", "source_checksum", source, reference.path)
    expected_difficulties = Counter()
    for item in manifest.allocation:
        expected_difficulties[item.difficulty] += item.count
    reserved_difficulties = Counter()
    for key in manifest.question_keys:
        match = re.fullmatch(r"([ngs][0-9]+)-l([1-5])-([0-9]{2,4})", key)
        if match is None or match.group(1).upper() != manifest.topic_code:
            _issue(report, "error", "invalid_reserved_question_key", manifest_path, key)
            continue
        reserved_difficulties[int(match.group(2))] += 1
    if reserved_difficulties != expected_difficulties:
        _issue(
            report,
            "error",
            "reserved_key_difficulty_distribution",
            manifest_path,
            f"Reserved {dict(reserved_difficulties)}, expected {dict(expected_difficulties)}",
        )
    if manifest.status == "planned":
        return report
    actual = Counter()
    question_root = manifest_path.parent.parent / "questions"
    for key in manifest.question_keys:
        path = question_root / f"{key}.json"
        try:
            question = Question.model_validate_json(path.read_text())
        except (OSError, ValueError, ValidationError) as exc:
            _issue(report, "error", "invalid_batch_question", path, str(exc))
            continue
        if question.stable_key != key:
            _issue(report, "error", "batch_question_key_mismatch", path, question.stable_key)
        if question.bank_key != manifest.bank_key:
            _issue(report, "error", "batch_question_bank_mismatch", path, question.bank_key)
        if question.curriculum_version != manifest.curriculum_version:
            _issue(
                report,
                "error",
                "batch_question_curriculum_mismatch",
                path,
                question.curriculum_version,
            )
        actual[(question.primary_outcome, question.difficulty)] += 1
        for position, kind, answer, response in _answer_candidates(question):
            result = check_answer(response, answer)
            if not result["correct"]:
                _issue(
                    report,
                    "error",
                    "answer_checker_rejected",
                    path,
                    f"Part {position} {kind} answer {answer!r}: {result['error'] or 'incorrect'}",
                )
        for asset in question.assets:
            asset_path = manifest_path.parent.parent / asset.path
            if not asset_path.is_file():
                _issue(report, "error", "missing_asset", asset_path, asset.asset_key)
            elif _checksum(asset_path) != asset.sha256:
                _issue(report, "error", "asset_checksum", asset_path, asset.asset_key)
        report.questions.append(question)
    if manifest.status != "planned":
        expected = {
            (item.outcome_code, item.difficulty): item.count
            for item in manifest.allocation
        }
        if actual != expected:
            _issue(
                report,
                "error",
                "batch_distribution",
                manifest_path,
                f"Found {dict(actual)}, expected {expected}",
            )
    return report


def _prompt_text(question: Question) -> str:
    parts = [question.title]
    for block in question.stem:
        parts.append(getattr(block, "text", getattr(block, "latex", "")))
    for part in question.parts:
        for block in part.prompt:
            parts.append(getattr(block, "text", getattr(block, "latex", "")))
    return " ".join(parts)


def _normalised_prompt(question: Question) -> str:
    text = unicodedata.normalize("NFKC", _prompt_text(question)).casefold()
    text = re.sub(r"(?<![a-z])[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?![a-z])", " <number> ", text)
    text = re.sub(r"\\[a-z]+", " ", text)
    return " ".join(re.findall(r"[a-z]+|<number>|[+*/=<>-]", text))


def _shingles(text: str, width: int = 3) -> set[tuple[str, ...]]:
    tokens = text.split()
    if len(tokens) < width:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def detect_prompt_duplicates(
    questions: list[Question], *, threshold: float = 0.82
) -> list[DuplicateMatch]:
    if not 0.5 <= threshold <= 1:
        raise ValueError("Near-duplicate threshold must be between 0.5 and 1")
    normalised = [_normalised_prompt(question) for question in questions]
    shingles = [_shingles(text) for text in normalised]
    matches: list[DuplicateMatch] = []
    for first_index, first in enumerate(questions):
        for second_index in range(first_index + 1, len(questions)):
            second = questions[second_index]
            if normalised[first_index] == normalised[second_index]:
                matches.append(
                    DuplicateMatch(
                        "exact_prompt",
                        first.stable_key,
                        second.stable_key,
                        first.bank_key,
                        second.bank_key,
                        1.0,
                    )
                )
                continue
            left, right = shingles[first_index], shingles[second_index]
            if not left or not right:
                continue
            score = len(left & right) / len(left | right)
            if score >= threshold:
                matches.append(
                    DuplicateMatch(
                        "near_prompt",
                        first.stable_key,
                        second.stable_key,
                        first.bank_key,
                        second.bank_key,
                        round(score, 4),
                    )
                )
    return matches


def validate_authoring_pipeline(
    bank_catalogue_root: Path,
    syllabus_path: Path,
    *,
    repository_root: Path,
    near_duplicate_threshold: float = 0.82,
) -> PipelineValidationReport:
    report = PipelineValidationReport()
    catalogue_report = validate_catalogue(bank_catalogue_root, syllabus_path)
    report.blueprint_count = len(catalogue_report.banks)
    report.question_count = len(catalogue_report.questions)
    report.issues.extend(catalogue_report.errors)
    expected_groups = (
        catalogue_report.syllabus.expected_topic_group_count
        if catalogue_report.syllabus
        else 0
    )
    if report.blueprint_count != expected_groups:
        _issue(
            report,
            "error",
            "blueprint_coverage",
            bank_catalogue_root,
            f"Found {report.blueprint_count} blueprints, expected {expected_groups}",
        )
    batch_ids: set[str] = set()
    authored_keys = {
        question.stable_key: question.bank_key for question in catalogue_report.questions
    }
    question_claims: dict[str, str] = {}
    claimed_keys_by_bank: dict[str, set[str]] = defaultdict(set)
    allocations: dict[str, Counter] = defaultdict(Counter)
    manifests_by_bank: dict[str, int] = defaultdict(int)
    for manifest_path in sorted(bank_catalogue_root.glob("**/batches/*.json")):
        batch_report = validate_batch(
            manifest_path,
            repository_root=repository_root,
            syllabus_path=syllabus_path,
        )
        report.batch_reports.append(batch_report)
        report.issues.extend(batch_report.issues)
        manifest = batch_report.manifest
        if manifest is None:
            continue
        if manifest.batch_id in batch_ids:
            _issue(report, "error", "duplicate_batch_id", manifest_path, manifest.batch_id)
        batch_ids.add(manifest.batch_id)
        manifests_by_bank[manifest.bank_key] += 1
        for item in manifest.allocation:
            allocations[manifest.bank_key][(item.outcome_code, item.difficulty)] += item.count
        for key in manifest.question_keys:
            authored_bank = authored_keys.get(key)
            if authored_bank is not None and (
                authored_bank != manifest.bank_key or manifest.status == "planned"
            ):
                _issue(
                    report,
                    "error",
                    "reserved_key_already_authored",
                    manifest_path,
                    f"{key} already exists in {authored_bank}",
                )
            previous = question_claims.get(key)
            if previous:
                _issue(
                    report,
                    "error",
                    "question_claimed_by_multiple_batches",
                    manifest_path,
                    f"{key} is also claimed by {previous}",
                )
            question_claims[key] = manifest.batch_id
            claimed_keys_by_bank[manifest.bank_key].add(key)
    for bank_report in catalogue_report.banks:
        blueprint = bank_report.blueprint
        if blueprint is None:
            continue
        unclaimed_actual = Counter(
            (question.primary_outcome, question.difficulty)
            for question in bank_report.questions
            if question.stable_key not in claimed_keys_by_bank[blueprint.bank_key]
        )
        expected = Counter()
        for row in blueprint.outcome_distribution:
            for level, target in row.difficulty_counts.items():
                remaining = target - unclaimed_actual[(row.code, int(level))]
                if remaining > 0:
                    expected[(row.code, int(level))] = remaining
        if not manifests_by_bank[blueprint.bank_key]:
            if not expected:
                continue
            _issue(
                report,
                "error",
                "missing_batch_plan",
                blueprint.bank_key,
                "Incomplete bank has no controlled batch manifests",
            )
            continue
        if allocations[blueprint.bank_key] != expected:
            _issue(
                report,
                "error",
                "batch_plan_coverage",
                blueprint.bank_key,
                f"Planned {dict(allocations[blueprint.bank_key])}, expected {dict(expected)}",
            )
    report.duplicate_matches = detect_prompt_duplicates(
        catalogue_report.questions, threshold=near_duplicate_threshold
    )
    for match in report.duplicate_matches:
        _issue(
            report,
            "error" if match.kind == "exact_prompt" else "warning",
            match.kind,
            match.second_key,
            f"Matches {match.first_key} with similarity {match.similarity:.4f}",
        )
    return report


def _blocks_html(blocks, question: Question) -> str:
    rendered: list[str] = []
    for block in blocks:
        if getattr(block, "type", None) == "text":
            rendered.append(html.escape(block.text))
        elif getattr(block, "type", None) in {"inline_math", "display_math"}:
            rendered.append(f"<code>{html.escape(block.latex)}</code>")
        else:
            asset = next(
                (item for item in question.assets if item.asset_key == block.asset_key), None
            )
            if asset:
                rendered.append(
                    f'<img src="assets/{html.escape(Path(asset.path).name)}" '
                    f'alt="{html.escape(asset.alt_text)}">'
                )
    return " ".join(rendered)


def export_reviewer_batch(
    manifest_path: Path,
    output: Path,
    *,
    repository_root: Path,
    syllabus_path: Path,
) -> dict:
    report = validate_batch(
        manifest_path,
        repository_root=repository_root,
        syllabus_path=syllabus_path,
    )
    if not report.valid:
        raise ValueError(json.dumps(report.as_dict(), indent=2))
    if not report.questions:
        raise ValueError("Cannot export a planned batch before its question files are authored")
    manifest = report.manifest
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "manifest.json", manifest.model_dump(mode="json"))
    _write_json(
        output / "questions.json",
        [question.model_dump(mode="json") for question in report.questions],
    )
    _write_json(output / "validation.json", report.as_dict())
    with (output / "review.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "question_key",
                "title",
                "outcome",
                "difficulty",
                "marks",
                "mathematics_decision",
                "editorial_decision",
                "reviewer_notes",
            ]
        )
        for question in report.questions:
            writer.writerow(
                [
                    question.stable_key,
                    question.title,
                    question.primary_outcome,
                    question.difficulty,
                    question.total_marks,
                    "",
                    "",
                    "",
                ]
            )
    review_lines = [
        f"# Review: {manifest.batch_id}",
        "",
        "Replace each `pending` decision with `approved` or `changes_requested`.",
        "Add a note whenever a change is requested. Keep question keys unchanged.",
        "",
        "- Mathematics reviewer:",
        "- Editorial reviewer:",
        "- Review date:",
        "",
    ]
    for question in report.questions:
        review_lines.extend(
            [
                f"## {question.stable_key} — {question.title}",
                "",
                f"[Open this question in the HTML preview](index.html#{question.stable_key})",
                "",
                f"- Outcome: `{question.primary_outcome}`",
                f"- Difficulty: `{question.difficulty}`",
                f"- Marks: `{question.total_marks}`",
                "- Mathematics decision: `pending`",
                "- Editorial decision: `pending`",
                "- Reviewer notes: _Replace this text with notes, or write `None`._",
                "",
            ]
        )
    (output / "review.md").write_text("\n".join(review_lines))

    cards: list[str] = []
    asset_output = output / "assets"
    for question in report.questions:
        parts: list[str] = []
        for part in question.parts:
            response = part.response
            answer = (
                response.canonical_answer
                if isinstance(response, NumericResponse)
                else response.canonical_expression
            )
            hints = "".join(
                f"<li>Hint {hint.stage}: {_blocks_html(hint.content, question)}</li>"
                for hint in part.hints
            )
            solution = "".join(
                f"<li>{_blocks_html(step.content, question)} "
                f"<small>{step.mark_type or ''}{step.mark_value or ''}</small></li>"
                for step in part.solution
            )
            parts.append(
                f"<section><h3>Part {part.position} · {part.marks} marks</h3>"
                f"<p>{_blocks_html(part.prompt, question)}</p>"
                f"<p><strong>Answer:</strong> {html.escape(answer)}</p>"
                f"<ul>{hints}</ul><ol>{solution}</ol></section>"
            )
        cards.append(
            f'<article id="{html.escape(question.stable_key)}"><h2>'
            f"{html.escape(question.stable_key)} · {html.escape(question.title)}</h2>"
            f"<p>Outcome {html.escape(question.primary_outcome)} · Difficulty "
            f"{question.difficulty} · {question.total_marks} marks</p>"
            f"<p>{_blocks_html(question.stem, question)}</p>{''.join(parts)}</article>"
        )
        for asset in question.assets:
            source = manifest_path.parent.parent / asset.path
            asset_output.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, asset_output / Path(asset.path).name)
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(manifest.batch_id)} reviewer packet</title>
<style>body{{font-family:system-ui,sans-serif;max-width:980px;margin:auto;padding:32px;color:#172033;background:#f4f6f8}}article{{background:white;border:1px solid #dce3e8;border-radius:14px;padding:24px;margin:20px 0}}section{{border-top:1px solid #e4e8ec;margin-top:18px}}code{{font-size:1rem;background:#f1f3f5;padding:2px 5px}}img{{max-width:100%}}small{{color:#65737e}}</style></head>
<body><h1>{html.escape(manifest.batch_id)}</h1><p>{len(report.questions)} questions · {html.escape(manifest.bank_key)} · {html.escape(manifest.generator.prompt_version)}</p>{''.join(cards)}</body></html>
"""
    (output / "index.html").write_text(document)
    return {
        "batch_id": manifest.batch_id,
        "question_count": len(report.questions),
        "output": str(output),
        "files": [
            "index.html",
            "manifest.json",
            "questions.json",
            "review.csv",
            "review.md",
            "validation.json",
        ],
    }
