"""Versioned syllabus and question-bank blueprint contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from .difficulty import DIFFICULTY_DEFINITIONS, DIFFICULTY_KEYS
from .models import Model

SchoolLevel = Literal["secondary_1", "secondary_2"]
ContentStatus = Literal["draft", "active", "retired"]
BankStatus = Literal["draft", "reviewed", "published", "retired"]
BankRole = Literal["learning", "diagnostic"]
Strand = Literal[
    "number_and_algebra",
    "geometry_and_measurement",
    "statistics_and_probability",
]


class SyllabusOutcome(Model):
    school_level: SchoolLevel
    code: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    description: str = Field(min_length=1)
    position: int = Field(ge=1)


class SyllabusTopic(Model):
    code: str = Field(pattern=r"^[NGS][0-9]+$")
    title: str = Field(min_length=1, max_length=160)
    strand: Strand
    position: int = Field(ge=1)
    outcomes: list[SyllabusOutcome] = Field(min_length=1)

    @model_validator(mode="after")
    def outcomes_are_unique(self):
        keys = [(item.school_level, item.code) for item in self.outcomes]
        if len(keys) != len(set(keys)):
            raise ValueError("Outcome keys must be unique within a topic and school level")
        for level in {item.school_level for item in self.outcomes}:
            positions = sorted(item.position for item in self.outcomes if item.school_level == level)
            if positions != list(range(1, len(positions) + 1)):
                raise ValueError(f"{level} outcome positions must be consecutive from 1")
        return self

    def outcome_codes(self, school_level: str) -> set[str]:
        return {
            outcome.code
            for outcome in self.outcomes
            if outcome.school_level == school_level
        }


class SyllabusCatalogue(Model):
    schema_version: Literal["1.0.0"] = "1.0.0"
    version_key: str = Field(pattern=r"^[a-z0-9_]+$")
    title: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    subject: Literal["Mathematics"]
    status: ContentStatus
    source_reference: str = Field(min_length=1)
    expected_topic_count: int = Field(ge=1)
    expected_topic_group_count: int = Field(ge=1)
    topics: list[SyllabusTopic] = Field(min_length=1)

    @model_validator(mode="after")
    def topics_are_consistent(self):
        if len(self.topics) > self.expected_topic_count:
            raise ValueError("Catalogue cannot contain more topics than expected_topic_count")
        codes = [topic.code for topic in self.topics]
        if len(codes) != len(set(codes)):
            raise ValueError("Topic codes must be unique")
        positions = [topic.position for topic in self.topics]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Topic positions must be consecutive from 1")
        topic_groups = {
            (topic.code, outcome.school_level)
            for topic in self.topics
            for outcome in topic.outcomes
        }
        if len(topic_groups) > self.expected_topic_group_count:
            raise ValueError(
                "Catalogue cannot contain more level-specific topic groups than expected"
            )
        if self.status == "active":
            if len(self.topics) != self.expected_topic_count:
                raise ValueError("An active catalogue must contain every expected topic")
            if len(topic_groups) != self.expected_topic_group_count:
                raise ValueError(
                    "An active catalogue must contain every expected level-specific topic group"
                )
        return self

    @property
    def topic_group_count(self) -> int:
        return len(
            {
                (topic.code, outcome.school_level)
                for topic in self.topics
                for outcome in topic.outcomes
            }
        )

    def topic(self, code: str) -> SyllabusTopic | None:
        return next((topic for topic in self.topics if topic.code == code), None)


class BankTopic(Model):
    code: str = Field(pattern=r"^[NGS][0-9]+$")
    title: str = Field(min_length=1, max_length=160)


class OutcomeDistribution(Model):
    code: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    title: str = Field(min_length=1)
    difficulty_counts: dict[str, int]
    total: int = Field(ge=0)

    @model_validator(mode="after")
    def counts_add_up(self):
        if set(self.difficulty_counts) != set(DIFFICULTY_KEYS):
            raise ValueError("Outcome difficulty_counts must contain levels 1 through 5")
        if any(value < 0 for value in self.difficulty_counts.values()):
            raise ValueError("Outcome difficulty counts cannot be negative")
        if sum(self.difficulty_counts.values()) != self.total:
            raise ValueError("Outcome difficulty counts must add up to total")
        return self


class BankBlueprint(Model):
    schema_version: Literal["1.0.0"] = "1.0.0"
    bank_id: UUID
    bank_key: str = Field(pattern=r"^g3-sec[12]-[ngs][0-9]+-v[0-9]+$")
    bank_role: BankRole = "learning"
    curriculum_version: str = Field(pattern=r"^[a-z0-9_]+$")
    school_level: SchoolLevel
    course: str = Field(min_length=1)
    topic: BankTopic
    status: BankStatus
    question_count: int = Field(ge=1)
    difficulty_distribution: dict[str, int]
    outcome_distribution: list[OutcomeDistribution] = Field(min_length=1)
    defaults: dict
    difficulty_definitions: dict[str, str]
    style_references: list[str]
    publication_checks: list[str]

    @model_validator(mode="after")
    def blueprint_is_consistent(self):
        if set(self.difficulty_distribution) != set(DIFFICULTY_KEYS):
            raise ValueError("difficulty_distribution must contain levels 1 through 5")
        if any(value < 0 for value in self.difficulty_distribution.values()):
            raise ValueError("Difficulty counts cannot be negative")
        if sum(self.difficulty_distribution.values()) != self.question_count:
            raise ValueError("Difficulty distribution must add up to question_count")
        if sum(item.total for item in self.outcome_distribution) != self.question_count:
            raise ValueError("Outcome distribution must add up to question_count")
        aggregated = {
            level: sum(item.difficulty_counts[level] for item in self.outcome_distribution)
            for level in DIFFICULTY_KEYS
        }
        if aggregated != self.difficulty_distribution:
            raise ValueError("Outcome difficulty counts must match difficulty_distribution")
        if self.difficulty_definitions != DIFFICULTY_DEFINITIONS:
            raise ValueError("difficulty_definitions must match the canonical five-level rubric")
        codes = [item.code for item in self.outcome_distribution]
        if len(codes) != len(set(codes)):
            raise ValueError("Outcome distribution codes must be unique")
        expected_prefix = f"g3-sec{self.school_level[-1]}-{self.topic.code.lower()}-v"
        if not self.bank_key.startswith(expected_prefix):
            raise ValueError("Bank key must match its school level and topic code")
        return self


def load_catalogue(path: Path) -> SyllabusCatalogue:
    return SyllabusCatalogue.model_validate_json(path.read_text())


def load_blueprint(path: Path) -> BankBlueprint:
    return BankBlueprint.model_validate_json(path.read_text())


def schema_documents() -> dict[str, dict]:
    return {
        "syllabus-catalogue-v1.schema.json": SyllabusCatalogue.model_json_schema(),
        "bank-blueprint-v1.schema.json": BankBlueprint.model_json_schema(),
    }


def write_schemas(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for filename, schema in schema_documents().items():
        (output / filename).write_text(json.dumps(schema, indent=2) + "\n")
