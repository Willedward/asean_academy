"""Learner-safe contracts for the Layer 1 objective-English vertical slice."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from .contracts import ApiModel

EnglishLessonState = Literal[
    "not_started", "in_progress", "practice_completed", "proficient", "mastered"
]
EnglishPracticeMode = Literal["guided_practice", "retry_review"]
EnglishErrorCategory = Literal[
    "unknown_meaning",
    "missed_clue",
    "option_trap",
    "tone_mismatch",
    "clause_structure",
    "boundary_choice",
    "agreement_control",
    "gap_role",
    "local_grammar",
    "cohesion_clue",
    "entry_accuracy",
    "task_topic",
    "command_word",
    "audience_scope",
    "evidence_plan",
        "paper_format",
        "instruction_control",
        "timing_control",
        "independent_conditions",
]


class EnglishLessonMap(ApiModel):
    stable_key: str
    lesson_code: str
    position: int
    title: str
    outcome_code: str
    outcome: str
    route_tags: list[Literal["full", "core", "sprint"]]
    content_status: Literal["planned", "draft", "reviewed", "published", "retired"]
    authored: bool
    available: bool
    href: str | None
    progress_state: EnglishLessonState = "not_started"
    retry_question_count: int = 0


class EnglishModuleMap(ApiModel):
    module_code: str
    position: int
    stage: Literal["orientation", "toolkit", "paper_application", "composition"]
    title: str
    purpose: str
    lessons: list[EnglishLessonMap]


class EnglishExamProfilePartResponse(ApiModel):
    position: int
    part_key: str
    title: str
    task_type: str
    reported_format: str
    reported_word_count: int | None
    word_count_status: Literal["not_applicable", "guidance", "strict"]
    configurable_fields: list[str]


class EnglishExamProfileSectionResponse(ApiModel):
    position: int
    section_key: str
    title: str
    reported_minutes: int
    parts: list[EnglishExamProfilePartResponse]


class EnglishExamProfileResponse(ApiModel):
    profile_key: str
    status: Literal["reported", "corroborated", "official"]
    evidence_boundary: str
    entry_level: Literal["secondary_1_entry"]
    effective_from: str
    review_due: str
    sections: list[EnglishExamProfileSectionResponse]
    excluded_task_types: list[str]


class EnglishCourseMapResponse(ApiModel):
    stable_key: Literal["asean-scholarship-english"] = "asean-scholarship-english"
    revision: int = 1
    title: str
    description: str
    subject: Literal["English"] = "English"
    content_status: Literal["draft", "reviewed", "published", "retired"]
    development_preview: bool
    exam_profile: EnglishExamProfileResponse
    modules: list[EnglishModuleMap]


class EnglishLessonSectionResponse(ApiModel):
    position: int
    section_type: Literal[
        "retrieval_warmup",
        "explicit_model",
        "worked_analysis",
        "guided_practice",
        "independent_application",
        "error_classification",
        "exit_ticket",
    ]
    title: str
    content: list[str]
    question_count: int


class EnglishPracticeEntry(ApiModel):
    lesson_key: str
    question_count: int = Field(ge=1, le=40)
    available: bool
    development_available: bool = False
    retry_question_count: int = 0


class EnglishLessonResponse(ApiModel):
    stable_key: str
    revision: int
    lesson_code: str
    outcome_code: str
    title: str
    summary: str
    estimated_minutes: int
    content_status: Literal["draft", "reviewed", "published", "retired"]
    development_preview: bool
    sections: list[EnglishLessonSectionResponse]
    practice: EnglishPracticeEntry


class CreateEnglishPracticeSessionRequest(ApiModel):
    lesson_key: str = Field(pattern=r"^e[0-9]+-lesson-[0-9]{2}$")
    mode: EnglishPracticeMode = "guided_practice"


class EnglishPracticeSessionResponse(ApiModel):
    session_id: str
    status: Literal["active", "completed"]
    exam_profile_key: str
    lesson_key: str
    lesson_revision: int
    mode: EnglishPracticeMode
    question_count: int
    assigned_count: int
    resolved_count: int
    correct_count: int
    incorrect_count: int
    development_drafts: bool


class EnglishChoiceOptionResponse(ApiModel):
    key: str
    text: str


class EnglishQuestionPartResponse(ApiModel):
    position: int
    prompt: str
    response_type: Literal["single_choice", "multiple_response", "short_text"]
    options: list[EnglishChoiceOptionResponse]


class EnglishPassageResponse(ApiModel):
    stable_key: str
    revision: int
    title: str
    text_type: str
    paragraphs: list[str]
    attribution: str


class EnglishPublicQuestionResponse(ApiModel):
    stable_key: str
    revision: int
    title: str
    difficulty: int = Field(ge=1, le=5)
    outcome_code: str
    question_type: str
    exposure_pool: str
    instructions: str
    passage: EnglishPassageResponse | None = None
    word_bank: list[EnglishChoiceOptionResponse] | None = None
    parts: list[EnglishQuestionPartResponse]


class EnglishNextQuestionResponse(ApiModel):
    status: Literal["active", "completed"]
    session: EnglishPracticeSessionResponse
    position: int | None = None
    question: EnglishPublicQuestionResponse | None = None


EnglishAnswerText = Annotated[str, StringConstraints(max_length=1000)]


class SubmitEnglishAttemptRequest(ApiModel):
    session_id: str
    question_key: str = Field(pattern=r"^(ev|eg|eb|eo|er|ex)-l[1-5]-[0-9]{3,4}$")
    question_revision: int = Field(ge=1)
    answers: dict[str, EnglishAnswerText | list[EnglishAnswerText]] = Field(
        min_length=1, max_length=20
    )


class EnglishAttemptPartResult(ApiModel):
    position: int
    correct: bool
    error: str | None
    feedback: str


class EnglishAttemptResponse(ApiModel):
    attempt_id: str
    attempt_number: int
    correct: bool
    correct_parts: int = Field(ge=0)
    total_parts: int = Field(ge=1)
    score: float = Field(ge=0, le=1)
    threshold_met: bool
    hint_used: bool
    parts: list[EnglishAttemptPartResult]
    question_finished: Literal[True] = True
    retry_queued: bool
    needs_error_classification: bool
    lesson_state: EnglishLessonState


class ClassifyEnglishErrorRequest(ApiModel):
    category: EnglishErrorCategory


class EnglishErrorClassificationResponse(ApiModel):
    attempt_id: str
    category: EnglishErrorCategory
    recorded: bool = True


class EnglishLessonProgressResponse(ApiModel):
    lesson_key: str
    lesson_revision: int
    state: EnglishLessonState
    question_count: int
    resolved_count: int
    correct_count: int
    incorrect_count: int
    retry_question_count: int
    last_session_id: str | None
    updated_at: str


class EnglishProgressResponse(ApiModel):
    learner_id: str
    lessons: list[EnglishLessonProgressResponse]


class EnglishHintResponse(ApiModel):
    question_key: str
    parts: list[str]
    hint_used: Literal[True] = True
