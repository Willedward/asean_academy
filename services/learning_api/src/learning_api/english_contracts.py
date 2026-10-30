"""Learner-safe contracts for the Layer 1 objective-English vertical slice."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from .contracts import ApiModel

EnglishLessonState = Literal[
    "not_started", "in_progress", "practice_completed", "proficient", "mastered"
]
EnglishPracticeMode = Literal["guided_practice", "retry_review"]
EnglishDiagnosticPurpose = Literal["baseline", "endline"]
EnglishDiagnosticTaskType = Literal[
    "vocabulary_in_context", "banked_cloze", "open_cloze", "reading_comprehension"
]
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


class EnglishEssayPromptResponse(ApiModel):
    stable_key: str = Field(pattern=r"^english-essay-prompt-[a-z0-9-]+$")
    revision: int = Field(ge=1)
    title: str
    prompt_family: Literal[
        "reflective_personal_expository",
        "narrative",
        "opinion_discursive",
        "general_expository",
    ]
    prompt_text: str
    instructions: list[str]
    time_limit_minutes: int = Field(ge=10, le=120)
    time_limit_evidence: Literal["official", "candidate_reported", "inferred"]
    word_count_guidance: int | None = Field(default=None, ge=50, le=2000)
    word_count_status: Literal["not_stated", "guidance", "strict"]
    content_status: Literal["draft", "reviewed", "published", "retired"]
    development_preview: bool


class EnglishEssayDraftResponse(ApiModel):
    draft_id: str
    prompt: EnglishEssayPromptResponse
    body: str
    word_count: int = Field(ge=0)
    edit_revision: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime
    submission_available: Literal[False] = False
    ai_feedback_available: Literal[False] = False


class CreateEnglishEssayDraftRequest(ApiModel):
    prompt_key: str = Field(pattern=r"^english-essay-prompt-[a-z0-9-]+$")
    prompt_revision: int = Field(ge=1)


class UpdateEnglishEssayDraftRequest(ApiModel):
    body: Annotated[str, StringConstraints(max_length=20000)]
    expected_edit_revision: int = Field(ge=1)


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


class CreateEnglishCheckpointSessionRequest(ApiModel):
    module_code: str = Field(pattern=r"^E(?:0|[1-9][0-9]*)$")


class CreateEnglishDiagnosticSessionRequest(ApiModel):
    expected_purpose: EnglishDiagnosticPurpose | None = None


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


class EnglishCheckpointSessionResponse(ApiModel):
    session_id: str
    status: Literal["active", "completed"]
    exam_profile_key: str
    form_key: str
    form_revision: int
    module_code: str
    mastery_lesson_keys: list[str]
    question_count: int
    assigned_count: int
    resolved_count: int
    correct_parts: int
    total_parts: int
    score: float | None
    passed: bool | None
    development_drafts: bool


class EnglishDiagnosticTaskScoreResponse(ApiModel):
    task_type: EnglishDiagnosticTaskType
    correct_parts: int = Field(ge=0)
    total_parts: int = Field(ge=1)
    percentage: float = Field(ge=0, le=100)
    recommended_lesson_key: str
    recommended_lesson_title: str


class EnglishDiagnosticSessionResponse(ApiModel):
    session_id: str
    status: Literal["active", "completed"]
    purpose: EnglishDiagnosticPurpose
    exam_profile_key: str
    form_key: str
    form_revision: int
    title: str
    question_count: int = Field(ge=1)
    expected_part_count: int = Field(ge=1)
    resolved_count: int = Field(ge=0)
    correct_parts: int = Field(ge=0)
    total_parts: int = Field(ge=0)
    score: float | None = Field(default=None, ge=0, le=1)
    percentage: float | None = Field(default=None, ge=0, le=100)
    band: Literal["foundation", "developing", "secure"] | None = None
    task_scores: list[EnglishDiagnosticTaskScoreResponse]
    development_drafts: bool
    started_at: datetime
    completed_at: datetime | None = None


class EnglishDiagnosticNextResponse(ApiModel):
    status: Literal["content_pending", "start", "resume", "baseline_complete", "completed"]
    purpose: EnglishDiagnosticPurpose | None = None
    session_id: str | None = None
    result_session_id: str | None = None
    title: str
    message: str
    estimated_minutes: int | None = None
    question_count: int | None = None


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


class EnglishCheckpointNextQuestionResponse(ApiModel):
    status: Literal["active", "completed"]
    session: EnglishCheckpointSessionResponse
    position: int | None = None
    question: EnglishPublicQuestionResponse | None = None


class EnglishDiagnosticNextQuestionResponse(ApiModel):
    status: Literal["active", "completed"]
    session: EnglishDiagnosticSessionResponse
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


class SubmitEnglishCheckpointAttemptRequest(ApiModel):
    session_id: str
    question_key: str = Field(pattern=r"^(ev|eg|eb|eo|er|ex)-l[1-5]-[0-9]{3,4}$")
    question_revision: int = Field(ge=1)
    answers: dict[str, EnglishAnswerText | list[EnglishAnswerText]] = Field(
        min_length=1, max_length=20
    )


class SubmitEnglishDiagnosticAttemptRequest(SubmitEnglishCheckpointAttemptRequest):
    pass


class EnglishCheckpointAttemptResponse(ApiModel):
    attempt_id: str
    accepted: Literal[True] = True
    checkpoint_completed: bool
    session: EnglishCheckpointSessionResponse


class EnglishDiagnosticAttemptResponse(ApiModel):
    attempt_id: str
    accepted: Literal[True] = True
    diagnostic_completed: bool
    session: EnglishDiagnosticSessionResponse


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


class EnglishCheckpointProgressResponse(ApiModel):
    module_code: str = Field(pattern=r"^E(?:0|[1-9][0-9]*)$")
    module_title: str
    state: Literal["locked", "available", "in_progress", "passed"]
    mastery_lesson_keys: list[str]
    question_count: int = Field(ge=1)
    passing_percentage: Literal[75] = 75
    attempt_count: int = Field(ge=0)
    last_session_id: str | None
    last_form_key: str | None
    last_percentage: float | None = Field(default=None, ge=0, le=100)


class EnglishProgressResponse(ApiModel):
    learner_id: str
    lessons: list[EnglishLessonProgressResponse]
    checkpoints: list[EnglishCheckpointProgressResponse]


class EnglishHintResponse(ApiModel):
    question_key: str
    parts: list[str]
    hint_used: Literal[True] = True
