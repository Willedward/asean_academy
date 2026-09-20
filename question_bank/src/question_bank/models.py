"""Strict source contracts for authored mathematics questions."""

import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0.0"
OUTCOMES = frozenset({"1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7"})


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TextBlock(Model):
    type: Literal["text"]
    text: str = Field(min_length=1)


class InlineMathBlock(Model):
    type: Literal["inline_math"]
    latex: str = Field(min_length=1)


class DisplayMathBlock(Model):
    type: Literal["display_math"]
    latex: str = Field(min_length=1)


class AssetReferenceBlock(Model):
    type: Literal["asset_ref"]
    asset_key: str = Field(min_length=1)


ContentBlock = Annotated[
    TextBlock | InlineMathBlock | DisplayMathBlock | AssetReferenceBlock,
    Field(discriminator="type"),
]


class UnitSpec(Model):
    canonical: str = Field(min_length=1)
    accepted: list[str] = Field(min_length=1)
    required: bool

    @model_validator(mode="after")
    def canonical_is_accepted(self):
        if self.canonical not in self.accepted:
            raise ValueError("The canonical unit must be included in accepted units")
        if len(set(self.accepted)) != len(self.accepted):
            raise ValueError("Accepted units must be unique")
        return self


NumericMode = Literal["exact_numeric", "absolute_tolerance", "rounded_dp", "rounded_sf"]
ExpressionMode = Literal[
    "symbolic_equivalence",
    "prime_factorisation",
    "ordered_numeric_list",
    "exact_relation",
]


class NumericResponse(Model):
    type: Literal["numeric"]
    comparison_mode: NumericMode
    canonical_answer: str = Field(min_length=1)
    canonical_latex: str = Field(min_length=1)
    accepted_answers: list[str] = Field(default_factory=list)
    absolute_tolerance: str | None = Field(
        default=None, pattern=r"^(0|[0-9]+(?:\.[0-9]+)?)$"
    )
    rounding_precision: int | None = Field(default=None, ge=0, le=15)
    unit: UnitSpec | None = None

    @model_validator(mode="after")
    def mode_has_configuration(self):
        if self.comparison_mode == "absolute_tolerance" and self.absolute_tolerance is None:
            raise ValueError("absolute_tolerance mode requires absolute_tolerance")
        if self.comparison_mode in {"rounded_dp", "rounded_sf"}:
            if self.rounding_precision is None:
                raise ValueError("A rounded answer requires rounding_precision")
        if len(set(self.accepted_answers)) != len(self.accepted_answers):
            raise ValueError("Accepted answers must be unique")
        return self


class AlgebraicResponse(Model):
    type: Literal["algebraic_expression"]
    comparison_mode: ExpressionMode
    canonical_expression: str = Field(min_length=1)
    canonical_latex: str = Field(min_length=1)
    variables: list[str]
    domain_constraints: list[str]
    accepted_equivalents: list[str]
    checker_config: dict

    @model_validator(mode="after")
    def checker_is_configured(self):
        if len(set(self.variables)) != len(self.variables):
            raise ValueError("Variables must be unique")
        if len(set(self.accepted_equivalents)) != len(self.accepted_equivalents):
            raise ValueError("Accepted equivalents must be unique")
        if self.comparison_mode == "prime_factorisation":
            if self.checker_config.get("require_prime_bases") is not True:
                raise ValueError("Prime factorisation must require prime bases")
        if self.comparison_mode == "ordered_numeric_list":
            if self.checker_config.get("order") not in {"ascending", "descending"}:
                raise ValueError("Ordered list checker requires ascending or descending order")
        if self.comparison_mode == "exact_relation":
            allowed = self.checker_config.get("allowed_operators")
            if not isinstance(allowed, list) or not allowed:
                raise ValueError("Exact relation checker requires allowed_operators")
        return self


Response = Annotated[NumericResponse | AlgebraicResponse, Field(discriminator="type")]


class Hint(Model):
    stage: Literal[1, 2]
    content: list[ContentBlock] = Field(min_length=1)


class SolutionStep(Model):
    position: int = Field(ge=1)
    content: list[ContentBlock] = Field(min_length=1)
    mark_type: Literal["B", "M", "A"] | None
    mark_value: int = Field(ge=0, le=5)

    @model_validator(mode="after")
    def mark_annotation_is_consistent(self):
        if (self.mark_type is None) != (self.mark_value == 0):
            raise ValueError("A marked step needs a mark type and a positive mark value")
        return self


class QuestionPart(Model):
    position: int = Field(ge=1)
    label: str | None = Field(default=None, pattern=r"^[a-z](?:\([ivx]+\))?$")
    prompt: list[ContentBlock] = Field(min_length=1)
    marks: int = Field(ge=1, le=15)
    primary_outcome: str
    secondary_outcomes: list[str]
    response: Response
    hints: tuple[Hint, Hint]
    solution: list[SolutionStep] = Field(min_length=1)

    @model_validator(mode="after")
    def part_is_consistent(self):
        if self.primary_outcome not in OUTCOMES:
            raise ValueError(f"Unsupported N1 outcome: {self.primary_outcome}")
        if not set(self.secondary_outcomes).issubset(OUTCOMES):
            raise ValueError("A secondary outcome is outside N1")
        if self.primary_outcome in self.secondary_outcomes:
            raise ValueError("The primary outcome cannot also be secondary")
        if len(set(self.secondary_outcomes)) != len(self.secondary_outcomes):
            raise ValueError("Secondary outcomes must be unique")
        if [hint.stage for hint in self.hints] != [1, 2]:
            raise ValueError("Hints must contain stage 1 followed by stage 2")
        positions = [step.position for step in self.solution]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Solution-step positions must be consecutive from 1")
        if sum(step.mark_value for step in self.solution) != self.marks:
            raise ValueError("Solution-step marks must add up to the part marks")
        return self


class Asset(Model):
    asset_key: str = Field(min_length=1)
    kind: Literal["number_line", "geometry", "chart", "table", "image"]
    format: Literal["svg", "png", "webp"]
    path: str = Field(min_length=1)
    alt_text: str = Field(min_length=1)
    generation_spec: dict
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def path_is_relative(self):
        path = PurePosixPath(self.path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Asset paths must be relative and cannot contain '..'")
        if path.suffix.lower() != f".{self.format}":
            raise ValueError("Asset path extension must match its format")
        return self


class Provenance(Model):
    authoring_method: Literal["original_generated"]
    style_references: list[str] = Field(min_length=1)
    created_at: datetime
    authored_by: str = Field(min_length=1)
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None
    review_notes: str | None = None

    @model_validator(mode="after")
    def review_fields_match(self):
        if (self.reviewed_at is None) != (self.reviewed_by is None):
            raise ValueError("reviewed_at and reviewed_by must be supplied together")
        return self


class Question(Model):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    revision: int = Field(ge=1)
    stable_key: str = Field(pattern=r"^n1-l[1-3]-[0-9]{2}$")
    bank_key: Literal["g3-sec1-n1-v1"]
    curriculum_version: Literal["g3_math_v1_draft"]
    school_level: Literal["secondary_1"]
    topic_code: Literal["N1"]
    primary_outcome: str
    title: str = Field(min_length=1, max_length=160)
    difficulty: int = Field(ge=1, le=3)
    calculator_allowed: Literal[True]
    question_type: Literal["structured"]
    status: Literal["draft", "reviewed", "published", "retired"]
    stem: list[ContentBlock]
    parts: list[QuestionPart] = Field(min_length=1)
    total_marks: int = Field(ge=1, le=30)
    assets: list[Asset]
    provenance: Provenance

    @model_validator(mode="after")
    def question_is_consistent(self):
        if self.primary_outcome not in OUTCOMES:
            raise ValueError(f"Unsupported N1 outcome: {self.primary_outcome}")
        key_difficulty = int(re.fullmatch(r"n1-l([1-3])-[0-9]{2}", self.stable_key).group(1))
        if key_difficulty != self.difficulty:
            raise ValueError("Stable-key level must match difficulty")
        positions = [part.position for part in self.parts]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Part positions must be consecutive from 1")
        labels = [part.label for part in self.parts if part.label is not None]
        if len(labels) != len(set(labels)):
            raise ValueError("Part labels must be unique")
        if sum(part.marks for part in self.parts) != self.total_marks:
            raise ValueError("Part marks must add up to total_marks")
        if self.primary_outcome not in {part.primary_outcome for part in self.parts}:
            raise ValueError("At least one part must assess the question's primary outcome")
        asset_keys = [asset.asset_key for asset in self.assets]
        if len(asset_keys) != len(set(asset_keys)):
            raise ValueError("Asset keys must be unique")
        references = {
            block.asset_key
            for blocks in [self.stem, *(part.prompt for part in self.parts)]
            for block in blocks
            if isinstance(block, AssetReferenceBlock)
        }
        missing = references - set(asset_keys)
        if missing:
            raise ValueError(f"Missing assets for references: {sorted(missing)}")
        if self.status in {"reviewed", "published"} and self.provenance.reviewed_at is None:
            raise ValueError("Reviewed and published questions require review provenance")
        return self
