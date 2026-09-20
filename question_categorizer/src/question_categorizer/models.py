"""Versioned categorization contracts."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0.0"
TAXONOMY_VERSION = "g3_math_v1_draft"
CLASSIFIER_VERSION = "rules_v1"
Level = Literal["secondary_1", "secondary_2"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Topic(Model):
    id: UUID
    code: str = Field(pattern=r"^[NGS]\d+$")
    strand: Literal["number_and_algebra", "geometry_and_measurement", "statistics_and_probability"]
    name: str
    order: int = Field(ge=0)


class Outcome(Model):
    id: UUID
    topic_id: UUID
    level: Level
    code: str = Field(pattern=r"^\d+\.\d+$")
    description: str
    order: int = Field(ge=0)


class Taxonomy(Model):
    version: str
    title: str
    status: Literal["draft", "active"]
    source_reference: str
    topics: list[Topic]
    outcomes: list[Outcome]

    @model_validator(mode="after")
    def references_are_valid(self):
        topic_ids = {topic.id for topic in self.topics}
        if len(topic_ids) != len(self.topics):
            raise ValueError("Topic IDs must be unique")
        if any(outcome.topic_id not in topic_ids for outcome in self.outcomes):
            raise ValueError("Outcome references a missing topic")
        keys = {(outcome.topic_id, outcome.level, outcome.code) for outcome in self.outcomes}
        if len(keys) != len(self.outcomes):
            raise ValueError("Outcome keys must be unique within a topic and level")
        return self


class Evidence(Model):
    kind: Literal["phrase", "notation", "structure", "level"]
    value: str
    weight: float = Field(gt=0)
    outcome_code: str | None = None


class TopicAssignment(Model):
    id: UUID
    topic_id: UUID
    topic_code: str
    topic_name: str
    outcome_id: UUID | None = None
    outcome_code: str | None = None
    outcome_level: Level | None = None
    role: Literal["primary", "secondary"]
    status: Literal["suggested", "confirmed", "rejected"] = "suggested"
    confidence: float = Field(ge=0, le=1)
    source: Literal["rules", "local_model", "api_model", "human"] = "rules"
    evidence: list[Evidence]


class QuestionPart(Model):
    id: UUID
    label: str | None
    order: int = Field(ge=0)
    content: str
    latex: str
    input_status: Literal["checked", "machine_unchecked"]
    source_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    assignments: list[TopicAssignment]
    classification_status: Literal["classified", "unclassified"]
    review_reasons: list[str]

    @model_validator(mode="after")
    def assignment_roles(self):
        if sum(a.role == "primary" for a in self.assignments) > 1:
            raise ValueError("A part can have at most one primary topic")
        if self.classification_status == "classified" and not any(
            a.role == "primary" for a in self.assignments
        ):
            raise ValueError("A classified part needs a primary topic")
        return self


class QuestionCategorization(Model):
    question_id: UUID
    question_number: str
    status: Literal["classified", "unclassified", "rejected"]
    primary_topic_code: str | None
    parts: list[QuestionPart]
    review_reasons: list[str]


class CategorizationResult(Model):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    taxonomy_version: str
    classifier_version: str
    minimum_score: float = Field(gt=0)
    minimum_margin: float = Field(ge=0)
    run_id: UUID
    created_at: str
    input_path: str
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_id: UUID
    extraction_run_key: str
    source_level: Level | None
    questions: list[QuestionCategorization]
    warnings: list[str]

    @model_validator(mode="after")
    def unique_questions_and_parts(self):
        if len({q.question_id for q in self.questions}) != len(self.questions):
            raise ValueError("Question IDs must be unique")
        parts = [part.id for question in self.questions for part in question.parts]
        if len(set(parts)) != len(parts):
            raise ValueError("Part IDs must be unique")
        return self
