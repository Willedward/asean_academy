"""Versioned source contracts for course, lesson, and question-pool authoring."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .models import OUTCOMES, Asset, ContentBlock, Model, Response

COURSE_SCHEMA_VERSION = "1.0.0"
ContentStatus = Literal["draft", "reviewed", "published", "retired"]
LessonSectionType = Literal["explanation", "worked_example", "active_recall", "summary"]
PoolType = Literal["lesson_practice", "unit_checkpoint", "adaptive_reserve"]
PoolStage = Literal["guided", "independent", "challenge", "checkpoint", "adaptive"]


class CourseProvenance(Model):
    authoring_method: Literal["original_authored"]
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


class MasteryPolicy(Model):
    key: str = Field(pattern=r"^[a-z0-9-]+-v[0-9]+$")
    minimum_eventual_correct_percentage: int = Field(ge=0, le=100)
    mastery_requires_checkpoint: bool
    checkpoint_passing_percentage: int = Field(ge=0, le=100)
    give_up_after_incorrect_attempts: int = Field(ge=1, le=10)
    hints_penalize_marks: bool


class CourseLessonReference(Model):
    stable_key: str = Field(pattern=r"^n1-lesson-[0-9]{2}$")
    position: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    outcomes: list[str] = Field(min_length=1)
    required_practice_count: int = Field(ge=1, le=20)

    @model_validator(mode="after")
    def outcomes_are_supported(self):
        if not set(self.outcomes).issubset(OUTCOMES):
            raise ValueError("Lesson reference contains an unsupported N1 outcome")
        if len(set(self.outcomes)) != len(self.outcomes):
            raise ValueError("Lesson reference outcomes must be unique")
        return self


class CourseUnit(Model):
    stable_key: str = Field(pattern=r"^[a-z0-9-]+$")
    position: int = Field(ge=1)
    topic_code: Literal["N1"]
    title: str = Field(min_length=1, max_length=160)
    checkpoint_question_count: int = Field(ge=1, le=40)
    lessons: list[CourseLessonReference] = Field(min_length=1)

    @model_validator(mode="after")
    def lesson_order_is_consistent(self):
        positions = [lesson.position for lesson in self.lessons]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Unit lesson positions must be consecutive from 1")
        keys = [lesson.stable_key for lesson in self.lessons]
        if len(keys) != len(set(keys)):
            raise ValueError("Unit lesson keys must be unique")
        return self


class Course(Model):
    schema_version: Literal["1.0.0"] = COURSE_SCHEMA_VERSION
    revision: int = Field(ge=1)
    stable_key: Literal["g3-sec1-math"]
    programme_key: Literal["asean-scholarship-preparation"]
    curriculum_version: Literal["g3_math_v1_draft"]
    school_level: Literal["secondary_1"]
    subject: Literal["Mathematics"]
    status: ContentStatus
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)
    mastery_policies: list[MasteryPolicy] = Field(min_length=1)
    units: list[CourseUnit] = Field(min_length=1)
    question_allocation_counts: dict[Literal["lesson_practice", "unit_checkpoint", "adaptive_reserve"], int]
    provenance: CourseProvenance

    @model_validator(mode="after")
    def course_is_consistent(self):
        if len(self.units) != 1:
            raise ValueError("The N1 v1 course contract requires exactly one unit")
        positions = [unit.position for unit in self.units]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Course unit positions must be consecutive from 1")
        policy_keys = [policy.key for policy in self.mastery_policies]
        if len(policy_keys) != len(set(policy_keys)):
            raise ValueError("Mastery policy keys must be unique")
        if set(self.question_allocation_counts) != {
            "lesson_practice",
            "unit_checkpoint",
            "adaptive_reserve",
        }:
            raise ValueError("Question allocation counts must declare every pool type")
        if any(count < 0 for count in self.question_allocation_counts.values()):
            raise ValueError("Question allocation counts cannot be negative")
        if self.status in {"reviewed", "published"} and self.provenance.reviewed_at is None:
            raise ValueError("Reviewed and published courses require review provenance")
        return self


class ExplanationSection(Model):
    stable_key: str = Field(pattern=r"^[a-z0-9-]+$")
    position: int = Field(ge=1)
    type: Literal["explanation"]
    title: str = Field(min_length=1, max_length=160)
    blocks: list[ContentBlock] = Field(min_length=1)


class WorkedExampleStep(Model):
    position: int = Field(ge=1)
    content: list[ContentBlock] = Field(min_length=1)


class WorkedExampleSection(Model):
    stable_key: str = Field(pattern=r"^[a-z0-9-]+$")
    position: int = Field(ge=1)
    type: Literal["worked_example"]
    title: str = Field(min_length=1, max_length=160)
    prompt: list[ContentBlock] = Field(min_length=1)
    steps: list[WorkedExampleStep] = Field(min_length=1)
    verification_note: str = Field(min_length=1)

    @model_validator(mode="after")
    def steps_are_ordered(self):
        positions = [step.position for step in self.steps]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Worked-example steps must be consecutive from 1")
        return self


class ActiveRecallSection(Model):
    stable_key: str = Field(pattern=r"^[a-z0-9-]+$")
    position: int = Field(ge=1)
    type: Literal["active_recall"]
    title: str = Field(min_length=1, max_length=160)
    prompt: list[ContentBlock] = Field(min_length=1)
    response: Response
    feedback: list[ContentBlock] = Field(min_length=1)


class SummarySection(Model):
    stable_key: str = Field(pattern=r"^[a-z0-9-]+$")
    position: int = Field(ge=1)
    type: Literal["summary"]
    title: str = Field(min_length=1, max_length=160)
    blocks: list[ContentBlock] = Field(min_length=1)


LessonSection = Annotated[
    ExplanationSection | WorkedExampleSection | ActiveRecallSection | SummarySection,
    Field(discriminator="type"),
]


def _section_blocks(section):
    if isinstance(section, (ExplanationSection, SummarySection)):
        return section.blocks
    if isinstance(section, WorkedExampleSection):
        return [section.prompt, *(step.content for step in section.steps)]
    return [section.prompt, section.feedback]


class Lesson(Model):
    schema_version: Literal["1.0.0"] = COURSE_SCHEMA_VERSION
    revision: int = Field(ge=1)
    stable_key: str = Field(pattern=r"^n1-lesson-[0-9]{2}$")
    course_key: Literal["g3-sec1-math"]
    unit_key: Literal["g3-sec1-n1"]
    position: int = Field(ge=1)
    status: ContentStatus
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1)
    outcomes: list[str] = Field(min_length=1)
    prerequisite_lessons: list[str]
    estimated_minutes: int = Field(ge=1, le=180)
    objectives: list[str] = Field(min_length=1)
    mastery_policy_key: str = Field(pattern=r"^[a-z0-9-]+-v[0-9]+$")
    sections: list[LessonSection]
    assets: list[Asset]
    provenance: CourseProvenance

    @model_validator(mode="after")
    def lesson_is_consistent(self):
        if not set(self.outcomes).issubset(OUTCOMES):
            raise ValueError("Lesson contains an unsupported N1 outcome")
        if len(set(self.outcomes)) != len(self.outcomes):
            raise ValueError("Lesson outcomes must be unique")
        if self.stable_key in self.prerequisite_lessons:
            raise ValueError("A lesson cannot require itself")
        if len(set(self.prerequisite_lessons)) != len(self.prerequisite_lessons):
            raise ValueError("Lesson prerequisites must be unique")
        positions = [section.position for section in self.sections]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Lesson section positions must be consecutive from 1")
        section_keys = [section.stable_key for section in self.sections]
        if len(section_keys) != len(set(section_keys)):
            raise ValueError("Lesson section keys must be unique")
        asset_keys = [asset.asset_key for asset in self.assets]
        if len(asset_keys) != len(set(asset_keys)):
            raise ValueError("Lesson asset keys must be unique")
        referenced_assets = {
            block.asset_key
            for section in self.sections
            for blocks in _section_blocks(section)
            for block in (blocks if isinstance(blocks, list) else [blocks])
            if block.type == "asset_ref"
        }
        missing = referenced_assets - set(asset_keys)
        if missing:
            raise ValueError(f"Missing lesson assets for references: {sorted(missing)}")
        if self.status in {"reviewed", "published"} and self.provenance.reviewed_at is None:
            raise ValueError("Reviewed and published lessons require review provenance")
        return self


class QuestionPoolItem(Model):
    position: int = Field(ge=1)
    question_key: str = Field(pattern=r"^n1-l[1-3]-[0-9]{2}$")
    stage: PoolStage
    weight: int = Field(default=1, ge=1, le=100)


class QuestionPool(Model):
    stable_key: str = Field(pattern=r"^[a-z0-9-]+$")
    type: PoolType
    lesson_key: str | None = Field(default=None, pattern=r"^n1-lesson-[0-9]{2}$")
    expected_question_count: int = Field(ge=1, le=40)
    items: list[QuestionPoolItem] = Field(min_length=1)

    @model_validator(mode="after")
    def pool_is_consistent(self):
        if (self.type == "lesson_practice") != (self.lesson_key is not None):
            raise ValueError("Only lesson-practice pools must identify a lesson")
        if len(self.items) != self.expected_question_count:
            raise ValueError("Pool item count must match expected_question_count")
        positions = [item.position for item in self.items]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Question-pool positions must be consecutive from 1")
        keys = [item.question_key for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("A question cannot appear twice in one pool")
        allowed_stages = {
            "lesson_practice": {"guided", "independent", "challenge"},
            "unit_checkpoint": {"checkpoint"},
            "adaptive_reserve": {"adaptive"},
        }
        if any(item.stage not in allowed_stages[self.type] for item in self.items):
            raise ValueError(f"Pool stage does not match pool type {self.type}")
        return self


class QuestionPools(Model):
    schema_version: Literal["1.0.0"] = COURSE_SCHEMA_VERSION
    course_key: Literal["g3-sec1-math"]
    unit_key: Literal["g3-sec1-n1"]
    bank_key: Literal["g3-sec1-n1-v1"]
    pools: list[QuestionPool] = Field(min_length=1)

    @model_validator(mode="after")
    def pool_keys_are_unique(self):
        keys = [pool.stable_key for pool in self.pools]
        if len(keys) != len(set(keys)):
            raise ValueError("Question-pool keys must be unique")
        question_keys = [item.question_key for pool in self.pools for item in pool.items]
        if len(question_keys) != len(set(question_keys)):
            raise ValueError("Every question must be allocated to exactly one source pool")
        return self
