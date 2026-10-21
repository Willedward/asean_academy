"""Strict source contracts for the Layer 1 English foundation."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ENGLISH_SCHEMA_VERSION = "1.0.0"
LESSON_CODE_PATTERN = r"^E[0-9]+\.[0-9]+$"
OUTCOME_CODE_PATTERN = r"^(EX|EV|EG|EB|EO|ER|EW)[0-9]+\.[0-9]+$"
LESSON_KEY_PATTERN = r"^e[0-9]+-lesson-[0-9]{2}$"
QUESTION_KEY_PATTERN = r"^(ev|eg|eb|eo|er|ex)-l[1-5]-[0-9]{3,4}$"
BANK_KEY_PATTERN = r"^english-(ev|eg|eb|eo|er|ex)-v[0-9]+$"
PASSAGE_KEY_PATTERN = r"^english-passage-[a-z0-9-]+$"


class EnglishModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EnglishProvenance(EnglishModel):
    authoring_method: Literal["original_authored"]
    source_refs: list[str] = Field(min_length=1)
    created_at: datetime
    authored_by: str = Field(min_length=1)
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None
    review_notes: str | None = None

    @model_validator(mode="after")
    def review_fields_match(self):
        if (self.reviewed_at is None) != (self.reviewed_by is None):
            raise ValueError("reviewed_at and reviewed_by must be supplied together")
        if len(set(self.source_refs)) != len(self.source_refs):
            raise ValueError("source_refs must be unique")
        return self


class SourceRecord(EnglishModel):
    source_key: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    title: str = Field(min_length=1)
    evidence_kind: Literal[
        "official_administration_guide",
        "candidate_report",
        "independent_preparation_summary",
        "research_guidance",
    ]
    authority: Literal["official", "candidate_reported", "research", "inferred"]
    url: str | None = None
    observed_at: str | None = None
    test_year: int | None = Field(default=None, ge=2000, le=2100)
    entry_level: str | None = None
    country: str | None = None
    city: str | None = None
    supports: list[str] = Field(min_length=1)
    limitations: str = Field(min_length=1)


class SourceInventory(EnglishModel):
    schema_version: Literal["1.0.0"] = ENGLISH_SCHEMA_VERSION
    inventory_key: Literal["asean-scholarship-english-evidence-v1"]
    evidence_boundary: str = Field(min_length=1)
    sources: list[SourceRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def source_keys_are_unique(self):
        keys = [source.source_key for source in self.sources]
        if len(keys) != len(set(keys)):
            raise ValueError("Source keys must be unique")
        return self


class CurriculumLesson(EnglishModel):
    position: int = Field(ge=1)
    lesson_code: str = Field(pattern=LESSON_CODE_PATTERN)
    stable_key: str = Field(pattern=LESSON_KEY_PATTERN)
    title: str = Field(min_length=1, max_length=120)
    outcome_code: str = Field(pattern=OUTCOME_CODE_PATTERN)
    outcome: str = Field(min_length=1)


class CurriculumModule(EnglishModel):
    position: int = Field(ge=0)
    module_code: str = Field(pattern=r"^E[0-9]+$")
    stage: Literal["orientation", "toolkit", "paper_application", "composition"]
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    lessons: list[CurriculumLesson] = Field(min_length=1)

    @model_validator(mode="after")
    def lessons_are_ordered(self):
        if [lesson.position for lesson in self.lessons] != list(range(1, len(self.lessons) + 1)):
            raise ValueError("Lesson positions must be consecutive from 1")
        for lesson in self.lessons:
            if not lesson.lesson_code.startswith(f"{self.module_code}."):
                raise ValueError("Lesson code must belong to its module")
            if not lesson.stable_key.startswith(f"{self.module_code.lower()}-lesson-"):
                raise ValueError("Lesson stable key must belong to its module")
        return self


class ExamPart(EnglishModel):
    part_key: str = Field(pattern=r"^section-[12](?:-part-[1-4])?$")
    title: str = Field(min_length=1)
    reported_minutes: int = Field(ge=1, le=180)
    format: str = Field(min_length=1)
    evidence_status: Literal["official", "candidate_reported", "inferred"]
    configurable_fields: list[str]


class EnglishCurriculumCatalogue(EnglishModel):
    schema_version: Literal["1.0.0"] = ENGLISH_SCHEMA_VERSION
    version_key: Literal["asean_scholarship_english_v1_draft"]
    title: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    status: Literal["draft", "reviewed", "published", "retired"]
    evidence_boundary: str = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)
    exam_blueprint: list[ExamPart] = Field(min_length=1)
    modules: list[CurriculumModule] = Field(min_length=1)

    @model_validator(mode="after")
    def catalogue_is_complete_and_unique(self):
        if [module.position for module in self.modules] != list(range(10)):
            raise ValueError("The v1 catalogue must contain ordered modules E0 through E9")
        if [module.module_code for module in self.modules] != [f"E{index}" for index in range(10)]:
            raise ValueError("The v1 catalogue must contain modules E0 through E9")
        lessons = [lesson for module in self.modules for lesson in module.lessons]
        if len(lessons) != 51:
            raise ValueError("The v1 catalogue must contain exactly 51 core lessons")
        for attr in ("lesson_code", "stable_key", "outcome_code"):
            values = [getattr(lesson, attr) for lesson in lessons]
            if len(values) != len(set(values)):
                raise ValueError(f"Curriculum {attr} values must be unique")
        return self

    def outcome_codes(self) -> set[str]:
        return {lesson.outcome_code for module in self.modules for lesson in module.lessons}

    def lesson_keys(self) -> set[str]:
        return {lesson.stable_key for module in self.modules for lesson in module.lessons}


class EnglishPassage(EnglishModel):
    schema_version: Literal["1.0.0"] = ENGLISH_SCHEMA_VERSION
    revision: int = Field(ge=1)
    stable_key: str = Field(pattern=PASSAGE_KEY_PATTERN)
    title: str = Field(min_length=1)
    text_type: Literal["narrative", "informational", "argumentative", "reflective"]
    paragraphs: list[str] = Field(min_length=1)
    attribution: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["draft", "reviewed", "published", "retired"]
    provenance: EnglishProvenance

    @model_validator(mode="after")
    def reviewed_content_has_provenance(self):
        if self.status in {"reviewed", "published"} and self.provenance.reviewed_at is None:
            raise ValueError("Reviewed and published passages require review provenance")
        if any(not paragraph.strip() for paragraph in self.paragraphs):
            raise ValueError("Passage paragraphs cannot be blank")
        return self


def passage_content_hash(passage: EnglishPassage | dict) -> str:
    if isinstance(passage, EnglishPassage):
        payload = {
            "stable_key": passage.stable_key,
            "revision": passage.revision,
            "title": passage.title,
            "text_type": passage.text_type,
            "paragraphs": passage.paragraphs,
            "attribution": passage.attribution,
        }
    else:
        payload = {
            key: passage[key]
            for key in ("stable_key", "revision", "title", "text_type", "paragraphs", "attribution")
        }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PassageReference(EnglishModel):
    stable_key: str = Field(pattern=PASSAGE_KEY_PATTERN)
    revision: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ChoiceOption(EnglishModel):
    key: str = Field(pattern=r"^[A-T]$")
    text: str = Field(min_length=1)


class SingleChoiceResponse(EnglishModel):
    type: Literal["single_choice"]
    options: list[ChoiceOption] = Field(min_length=2, max_length=20)
    correct_key: str = Field(pattern=r"^[A-T]$")
    choice_rationales: dict[str, str]

    @model_validator(mode="after")
    def response_is_deterministic(self):
        keys = [option.key for option in self.options]
        if len(keys) != len(set(keys)):
            raise ValueError("Choice keys must be unique")
        if self.correct_key not in keys:
            raise ValueError("correct_key must identify an option")
        if set(self.choice_rationales) != set(keys):
            raise ValueError("Every option requires one authored rationale")
        if any(not value.strip() for value in self.choice_rationales.values()):
            raise ValueError("Choice rationales cannot be blank")
        return self


class MultipleResponse(EnglishModel):
    type: Literal["multiple_response"]
    options: list[ChoiceOption] = Field(min_length=2, max_length=20)
    correct_keys: list[str] = Field(min_length=1)
    choice_rationales: dict[str, str]

    @model_validator(mode="after")
    def response_is_deterministic(self):
        keys = [option.key for option in self.options]
        if len(keys) != len(set(keys)):
            raise ValueError("Choice keys must be unique")
        if len(self.correct_keys) != len(set(self.correct_keys)):
            raise ValueError("correct_keys must be unique")
        if not set(self.correct_keys) <= set(keys):
            raise ValueError("Every correct key must identify an option")
        if set(self.choice_rationales) != set(keys):
            raise ValueError("Every option requires one authored rationale")
        return self


class TextNormalisation(EnglishModel):
    unicode_form: Literal["NFKC"] = "NFKC"
    collapse_whitespace: bool = True
    case_sensitive: bool = False
    strip_terminal_punctuation: bool = False


class ShortTextResponse(EnglishModel):
    type: Literal["short_text"]
    canonical_answer: str = Field(min_length=1)
    accepted_alternatives: list[str] = Field(default_factory=list)
    normalisation: TextNormalisation = Field(default_factory=TextNormalisation)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def alternatives_are_unique(self):
        answers = [self.canonical_answer, *self.accepted_alternatives]
        if len(answers) != len(set(answers)):
            raise ValueError("Approved short-text answers must be unique before normalisation")
        return self


EnglishResponse = Annotated[
    SingleChoiceResponse | MultipleResponse | ShortTextResponse,
    Field(discriminator="type"),
]


class EnglishQuestionPart(EnglishModel):
    position: int = Field(ge=1)
    prompt: str = Field(min_length=1)
    response: EnglishResponse
    hint: str = Field(min_length=1)
    correct_explanation: str = Field(min_length=1)


class EnglishObjectiveQuestion(EnglishModel):
    schema_version: Literal["1.0.0"] = ENGLISH_SCHEMA_VERSION
    revision: int = Field(ge=1)
    stable_key: str = Field(pattern=QUESTION_KEY_PATTERN)
    bank_key: str = Field(pattern=BANK_KEY_PATTERN)
    curriculum_version: Literal["asean_scholarship_english_v1_draft"]
    audience_band: Literal["secondary_school"]
    outcome_code: str = Field(pattern=OUTCOME_CODE_PATTERN)
    title: str = Field(min_length=1, max_length=160)
    difficulty: int = Field(ge=1, le=5)
    question_type: Literal[
        "vocabulary_in_context",
        "grammar_usage",
        "banked_cloze",
        "open_cloze",
        "reading_comprehension",
        "editing",
    ]
    exposure_pool: Literal[
        "lesson_example",
        "guided_practice",
        "independent_practice",
        "exit_ticket",
        "retry_review",
        "module_checkpoint",
        "baseline_diagnostic",
        "endline_diagnostic",
        "full_mock",
        "protected_reserve",
    ]
    feedback_timing: Literal["after_item", "after_group"]
    status: Literal["draft", "reviewed", "published", "retired"]
    passage_ref: PassageReference | None = None
    instructions: str = Field(min_length=1)
    parts: list[EnglishQuestionPart] = Field(min_length=1)
    provenance: EnglishProvenance

    @model_validator(mode="after")
    def question_is_consistent(self):
        positions = [part.position for part in self.parts]
        if positions != list(range(1, len(self.parts) + 1)):
            raise ValueError("Question part positions must be consecutive from 1")
        passage_types = {"banked_cloze", "open_cloze", "reading_comprehension"}
        if self.question_type in passage_types and self.passage_ref is None:
            raise ValueError("Passage and cloze questions must pin a passage revision")
        if self.question_type in passage_types and self.feedback_timing != "after_group":
            raise ValueError("Passage groups reveal feedback only after the complete group")
        if self.question_type == "banked_cloze":
            if len(self.parts) < 2:
                raise ValueError("Banked cloze questions require at least two gaps")
            if not all(isinstance(part.response, SingleChoiceResponse) for part in self.parts):
                raise ValueError("Every banked cloze gap must use a single-choice response")
            option_banks = [
                [(option.key, option.text) for option in part.response.options]
                for part in self.parts
            ]
            if any(bank != option_banks[0] for bank in option_banks[1:]):
                raise ValueError("Every banked cloze gap must use the same word bank")
            if len(option_banks[0]) <= len(self.parts):
                raise ValueError("A banked cloze requires more words than gaps")
            correct_keys = [part.response.correct_key for part in self.parts]
            if len(correct_keys) != len(set(correct_keys)):
                raise ValueError("Each banked cloze word may fill only one gap")
        if self.status in {"reviewed", "published"} and self.provenance.reviewed_at is None:
            raise ValueError("Reviewed and published questions require review provenance")
        return self


class EnglishBankManifest(EnglishModel):
    schema_version: Literal["1.0.0"] = ENGLISH_SCHEMA_VERSION
    bank_key: str = Field(pattern=BANK_KEY_PATTERN)
    revision: int = Field(ge=1)
    title: str = Field(min_length=1)
    curriculum_version: Literal["asean_scholarship_english_v1_draft"]
    status: Literal["draft", "reviewed", "published", "retired"]
    expected_question_count: int = Field(ge=1)
    outcome_codes: list[str] = Field(min_length=1)
    pool_distribution: dict[str, int]
    source_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def totals_match(self):
        if any(re.fullmatch(OUTCOME_CODE_PATTERN, code) is None for code in self.outcome_codes):
            raise ValueError("Manifest outcome codes must use the English outcome format")
        if len(set(self.outcome_codes)) != len(self.outcome_codes):
            raise ValueError("Manifest outcome codes must be unique")
        if any(count < 0 for count in self.pool_distribution.values()):
            raise ValueError("Pool counts cannot be negative")
        if sum(self.pool_distribution.values()) != self.expected_question_count:
            raise ValueError("Pool distribution must add up to expected_question_count")
        return self


class LessonSection(EnglishModel):
    position: int = Field(ge=1)
    section_type: Literal[
        "retrieval_warmup",
        "explicit_model",
        "worked_analysis",
        "guided_practice",
        "independent_application",
        "error_classification",
        "exit_ticket",
    ]
    title: str = Field(min_length=1)
    content: list[str] = Field(min_length=1)
    question_keys: list[str] = Field(default_factory=list)


class EnglishLesson(EnglishModel):
    schema_version: Literal["1.0.0"] = ENGLISH_SCHEMA_VERSION
    revision: int = Field(ge=1)
    stable_key: str = Field(pattern=LESSON_KEY_PATTERN)
    curriculum_version: Literal["asean_scholarship_english_v1_draft"]
    lesson_code: str = Field(pattern=LESSON_CODE_PATTERN)
    outcome_code: str = Field(pattern=OUTCOME_CODE_PATTERN)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    estimated_minutes: int = Field(ge=25, le=35)
    status: Literal["draft", "reviewed", "published", "retired"]
    sections: list[LessonSection] = Field(min_length=7, max_length=7)
    provenance: EnglishProvenance

    @model_validator(mode="after")
    def anatomy_is_complete(self):
        required = [
            "retrieval_warmup",
            "explicit_model",
            "worked_analysis",
            "guided_practice",
            "independent_application",
            "error_classification",
            "exit_ticket",
        ]
        if [section.position for section in self.sections] != list(range(1, 8)):
            raise ValueError("Lesson section positions must be consecutive from 1")
        if [section.section_type for section in self.sections] != required:
            raise ValueError("Lesson must follow the complete learn-apply-retrieve anatomy")
        question_keys = [key for section in self.sections for key in section.question_keys]
        if len(question_keys) != len(set(question_keys)):
            raise ValueError("A question cannot appear twice in one lesson")
        return self
