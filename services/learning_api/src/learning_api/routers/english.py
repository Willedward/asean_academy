"""Authenticated learner routes for deterministic objective-English practice."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Path

from ..course_catalogue import CatalogueError
from ..dependencies import (
    EnglishDiagnosticServiceDependency,
    EnglishEssayFeedbackAllowanceServiceDependency,
    EnglishEssayServiceDependency,
    EnglishLearningServiceDependency,
    PracticeAttemptRateLimitDependency,
    PracticeSessionRateLimitDependency,
    PracticeSupportRateLimitDependency,
)
from ..english_contracts import (
    ClassifyEnglishErrorRequest,
    CreateEnglishCheckpointSessionRequest,
    CreateEnglishDiagnosticSessionRequest,
    CreateEnglishEssayDraftRequest,
    CreateEnglishEssaySelfReviewRequest,
    CreateEnglishEssaySubmissionRequest,
    CreateEnglishPracticeSessionRequest,
    EnglishAttemptResponse,
    EnglishCheckpointAttemptResponse,
    EnglishCheckpointNextQuestionResponse,
    EnglishCheckpointSessionResponse,
    EnglishCourseMapResponse,
    EnglishDiagnosticAttemptResponse,
    EnglishDiagnosticNextQuestionResponse,
    EnglishDiagnosticNextResponse,
    EnglishDiagnosticSessionResponse,
    EnglishErrorClassificationResponse,
    EnglishEssayDraftResponse,
    EnglishEssayFeedbackAllowanceResponse,
    EnglishEssayLatestSubmissionResponse,
    EnglishEssayMarkingWorkspaceResponse,
    EnglishEssayPreSubmitResponse,
    EnglishEssayPromptResponse,
    EnglishEssaySelfReviewResponse,
    EnglishEssaySelfReviewWorkspaceResponse,
    EnglishEssaySubmissionResponse,
    EnglishHintResponse,
    EnglishLessonResponse,
    EnglishNextQuestionResponse,
    EnglishPracticeSessionResponse,
    EnglishProgressResponse,
    PreSubmitEnglishEssayRequest,
    SubmitEnglishAttemptRequest,
    SubmitEnglishCheckpointAttemptRequest,
    SubmitEnglishDiagnosticAttemptRequest,
    UpdateEnglishEssayDraftRequest,
)
from ..english_essay_marking import process_essay_marking_job
from ..english_essay_repository import EnglishEssayError
from ..english_learning_repository import EnglishLearningError

router = APIRouter(prefix="/api/v1/english", tags=["english"])

IdempotencyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)]


def _safe(call):
    try:
        return call()
    except (EnglishLearningError, EnglishEssayError, CatalogueError) as exc:
        status_code = getattr(exc, "status", getattr(exc, "status_code", 400))
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.get(
    "/essay-prompts/current",
    operation_id="getCurrentEnglishEssayPrompt",
    response_model=EnglishEssayPromptResponse,
    summary="Get the current learner-safe English essay prompt revision",
)
async def current_essay_prompt(
    service: EnglishEssayServiceDependency,
) -> EnglishEssayPromptResponse:
    return _safe(service.current_prompt)


@router.post(
    "/essay-drafts",
    operation_id="createEnglishEssayDraft",
    response_model=EnglishEssayDraftResponse,
    status_code=201,
    summary="Create or resume an owned essay draft pinned to the current prompt revision",
)
async def create_essay_draft(
    body: CreateEnglishEssayDraftRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishEssayServiceDependency,
    _rate_limit: PracticeSessionRateLimitDependency,
) -> EnglishEssayDraftResponse:
    return _safe(
        lambda: service.create_or_resume(
            prompt_key=body.prompt_key,
            prompt_revision=body.prompt_revision,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/essay-drafts/{draft_id}",
    operation_id="getEnglishEssayDraft",
    response_model=EnglishEssayDraftResponse,
    summary="Resume an owned mutable English essay draft",
)
async def essay_draft(
    draft_id: UUID,
    service: EnglishEssayServiceDependency,
) -> EnglishEssayDraftResponse:
    return _safe(lambda: service.get(str(draft_id)))


@router.patch(
    "/essay-drafts/{draft_id}",
    operation_id="updateEnglishEssayDraft",
    response_model=EnglishEssayDraftResponse,
    summary="Autosave an owned essay draft with optimistic concurrency",
)
async def update_essay_draft(
    draft_id: UUID,
    body: UpdateEnglishEssayDraftRequest,
    service: EnglishEssayServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishEssayDraftResponse:
    return _safe(
        lambda: service.update(
            str(draft_id),
            body=body.body,
            expected_edit_revision=body.expected_edit_revision,
        )
    )


@router.post(
    "/essay-drafts/{draft_id}/pre-submit",
    operation_id="preSubmitEnglishEssayDraft",
    response_model=EnglishEssayPreSubmitResponse,
    summary="Run deterministic checks against one exact remotely saved draft revision",
)
async def pre_submit_essay_draft(
    draft_id: UUID,
    body: PreSubmitEnglishEssayRequest,
    service: EnglishEssayServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishEssayPreSubmitResponse:
    return _safe(
        lambda: service.pre_submit(
            str(draft_id), expected_edit_revision=body.expected_edit_revision
        )
    )


@router.post(
    "/essay-submissions",
    operation_id="createEnglishEssaySubmission",
    response_model=EnglishEssaySubmissionResponse,
    status_code=201,
    summary="Create an immutable essay snapshot after explicit learner confirmation",
)
async def create_essay_submission(
    body: CreateEnglishEssaySubmissionRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishEssayServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishEssaySubmissionResponse:
    return _safe(
        lambda: service.submit(
            str(body.draft_id),
            expected_edit_revision=body.expected_edit_revision,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/essay-drafts/{draft_id}/latest-submission",
    operation_id="getLatestEnglishEssaySubmission",
    response_model=EnglishEssayLatestSubmissionResponse,
    summary="Get the latest immutable submission for an owned essay draft",
)
async def latest_essay_submission(
    draft_id: UUID,
    service: EnglishEssayServiceDependency,
) -> EnglishEssayLatestSubmissionResponse:
    return _safe(lambda: service.latest_submission(str(draft_id)))


@router.get(
    "/essay-submissions/{submission_id}/self-review",
    operation_id="getEnglishEssaySelfReviewWorkspace",
    response_model=EnglishEssaySelfReviewWorkspaceResponse,
    summary="Get the pinned instructional rubric and learner self-review state",
)
async def essay_self_review_workspace(
    submission_id: UUID,
    service: EnglishEssayServiceDependency,
) -> EnglishEssaySelfReviewWorkspaceResponse:
    return _safe(lambda: service.self_review_workspace(str(submission_id)))


@router.post(
    "/essay-submissions/{submission_id}/self-review",
    operation_id="createEnglishEssaySelfReview",
    response_model=EnglishEssaySelfReviewResponse,
    status_code=201,
    summary="Complete an immutable learner-authored review against the pinned rubric",
)
async def create_essay_self_review(
    submission_id: UUID,
    body: CreateEnglishEssaySelfReviewRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishEssayServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishEssaySelfReviewResponse:
    return _safe(
        lambda: service.create_self_review(
            str(submission_id),
            criterion_reflections=body.criterion_reflections,
            overall_reflection=body.overall_reflection,
            idempotency_key=idempotency_key,
        )
    )


@router.post(
    "/essay-submissions/{submission_id}/marking-jobs",
    operation_id="createEnglishEssayMarkingJob",
    response_model=EnglishEssayMarkingWorkspaceResponse,
    status_code=202,
    summary="Queue deterministic fixture feedback without a live provider call",
)
async def create_essay_marking_job(
    submission_id: UUID,
    background_tasks: BackgroundTasks,
    idempotency_key: IdempotencyHeader,
    service: EnglishEssayServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishEssayMarkingWorkspaceResponse:
    workspace = _safe(
        lambda: service.enqueue_marking_job(
            str(submission_id), idempotency_key=idempotency_key
        )
    )
    if workspace.job and workspace.job.status in {"queued", "retryable_failed"}:
        background_tasks.add_task(
            process_essay_marking_job,
            service.repository,
            workspace.job.job_id,
        )
    return workspace


@router.get(
    "/essay-submissions/{submission_id}/marking",
    operation_id="getEnglishEssayMarkingWorkspace",
    response_model=EnglishEssayMarkingWorkspaceResponse,
    summary="Get durable fixture-marking job and feedback state",
)
async def essay_marking_workspace(
    submission_id: UUID,
    background_tasks: BackgroundTasks,
    service: EnglishEssayServiceDependency,
) -> EnglishEssayMarkingWorkspaceResponse:
    workspace = _safe(lambda: service.marking_workspace(str(submission_id)))
    if workspace.job and workspace.job.status in {"queued", "retryable_failed"}:
        background_tasks.add_task(
            process_essay_marking_job,
            service.repository,
            workspace.job.job_id,
        )
    return workspace


@router.get(
    "/essay-feedback/allowance",
    operation_id="getEnglishEssayFeedbackAllowance",
    response_model=EnglishEssayFeedbackAllowanceResponse,
    summary="Get the learner-safe live essay-feedback allowance state",
)
async def essay_feedback_allowance(
    service: EnglishEssayFeedbackAllowanceServiceDependency,
) -> EnglishEssayFeedbackAllowanceResponse:
    return _safe(service.current)


@router.get(
    "/course-map",
    operation_id="getEnglishCourseMap",
    response_model=EnglishCourseMapResponse,
    summary="Get the authenticated learner's English module map",
)
async def course_map(
    service: EnglishLearningServiceDependency,
) -> EnglishCourseMapResponse:
    return _safe(service.course_map)


@router.get(
    "/diagnostics/next",
    operation_id="getNextEnglishDiagnostic",
    response_model=EnglishDiagnosticNextResponse,
    summary="Get the server-owned next English baseline or endline action",
)
async def next_diagnostic(
    service: EnglishDiagnosticServiceDependency,
) -> EnglishDiagnosticNextResponse:
    return _safe(service.next)


@router.post(
    "/diagnostic-sessions",
    operation_id="createEnglishDiagnosticSession",
    response_model=EnglishDiagnosticSessionResponse,
    status_code=201,
    summary="Start or resume the eligible protected English diagnostic",
)
async def create_diagnostic_session(
    body: CreateEnglishDiagnosticSessionRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishDiagnosticServiceDependency,
    _rate_limit: PracticeSessionRateLimitDependency,
) -> EnglishDiagnosticSessionResponse:
    return _safe(
        lambda: service.create_session(
            expected_purpose=body.expected_purpose,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/diagnostic-sessions/{session_id}",
    operation_id="getEnglishDiagnosticSession",
    response_model=EnglishDiagnosticSessionResponse,
    summary="Resume an owned protected English diagnostic",
)
async def diagnostic_session(
    session_id: UUID,
    service: EnglishDiagnosticServiceDependency,
) -> EnglishDiagnosticSessionResponse:
    return _safe(lambda: service.session(str(session_id)))


@router.get(
    "/diagnostic-sessions/{session_id}/next",
    operation_id="getNextEnglishDiagnosticQuestion",
    response_model=EnglishDiagnosticNextQuestionResponse,
    summary="Get the next learner-safe English diagnostic question group",
)
async def next_diagnostic_question(
    session_id: UUID,
    service: EnglishDiagnosticServiceDependency,
) -> EnglishDiagnosticNextQuestionResponse:
    return _safe(lambda: service.next_question(str(session_id)))


@router.post(
    "/diagnostic-attempts",
    operation_id="submitEnglishDiagnosticAttempt",
    response_model=EnglishDiagnosticAttemptResponse,
    summary="Submit an English diagnostic group without early correctness feedback",
)
async def submit_diagnostic_attempt(
    body: SubmitEnglishDiagnosticAttemptRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishDiagnosticServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishDiagnosticAttemptResponse:
    return _safe(
        lambda: service.submit_attempt(
            session_id=body.session_id,
            question_key=body.question_key,
            question_revision=body.question_revision,
            answers=body.answers,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/diagnostic-sessions/{session_id}/result",
    operation_id="getEnglishDiagnosticResult",
    response_model=EnglishDiagnosticSessionResponse,
    summary="Get a completed English diagnostic skill profile",
)
async def diagnostic_result(
    session_id: UUID,
    service: EnglishDiagnosticServiceDependency,
) -> EnglishDiagnosticSessionResponse:
    return _safe(lambda: service.result(str(session_id)))


@router.get(
    "/lessons/{lesson_key}",
    operation_id="getEnglishLesson",
    response_model=EnglishLessonResponse,
    summary="Get one learner-safe English lesson revision",
)
async def lesson(
    lesson_key: Annotated[str, Path(pattern=r"^e[0-9]+-lesson-[0-9]{2}$")],
    service: EnglishLearningServiceDependency,
) -> EnglishLessonResponse:
    return _safe(lambda: service.lesson(lesson_key))


@router.post(
    "/practice-sessions",
    operation_id="createEnglishPracticeSession",
    response_model=EnglishPracticeSessionResponse,
    status_code=201,
    summary="Start or resume an idempotent English objective-practice session",
)
async def create_session(
    body: CreateEnglishPracticeSessionRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSessionRateLimitDependency,
) -> EnglishPracticeSessionResponse:
    return _safe(
        lambda: service.create_session(
            lesson_key=body.lesson_key,
            mode=body.mode,
            idempotency_key=idempotency_key,
        )
    )


@router.post(
    "/checkpoint-sessions",
    operation_id="createEnglishCheckpointSession",
    response_model=EnglishCheckpointSessionResponse,
    status_code=201,
    summary="Start or resume an idempotent protected English module checkpoint",
)
async def create_checkpoint_session(
    body: CreateEnglishCheckpointSessionRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSessionRateLimitDependency,
) -> EnglishCheckpointSessionResponse:
    return _safe(
        lambda: service.create_checkpoint_session(
            module_code=body.module_code,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/checkpoint-sessions/{session_id}",
    operation_id="getEnglishCheckpointSession",
    response_model=EnglishCheckpointSessionResponse,
    summary="Resume an owned English module checkpoint",
)
async def checkpoint_session(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishCheckpointSessionResponse:
    return _safe(lambda: service.checkpoint_session(str(session_id)))


@router.get(
    "/checkpoint-sessions/{session_id}/next",
    operation_id="getNextEnglishCheckpointQuestion",
    response_model=EnglishCheckpointNextQuestionResponse,
    summary="Get the next learner-safe protected checkpoint question",
)
async def next_checkpoint_question(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishCheckpointNextQuestionResponse:
    return _safe(lambda: service.next_checkpoint_question(str(session_id)))


@router.post(
    "/checkpoint-attempts",
    operation_id="submitEnglishCheckpointAttempt",
    response_model=EnglishCheckpointAttemptResponse,
    summary="Submit a protected English checkpoint response without early feedback",
)
async def submit_checkpoint_attempt(
    body: SubmitEnglishCheckpointAttemptRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishCheckpointAttemptResponse:
    return _safe(
        lambda: service.submit_checkpoint_attempt(
            session_id=body.session_id,
            question_key=body.question_key,
            question_revision=body.question_revision,
            answers=body.answers,
            idempotency_key=idempotency_key,
        )
    )


@router.get(
    "/practice-sessions/{session_id}",
    operation_id="getEnglishPracticeSession",
    response_model=EnglishPracticeSessionResponse,
    summary="Resume an owned English objective-practice session",
)
async def session(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishPracticeSessionResponse:
    return _safe(lambda: service.session(str(session_id)))


@router.get(
    "/practice-sessions/{session_id}/next",
    operation_id="getNextEnglishQuestion",
    response_model=EnglishNextQuestionResponse,
    summary="Get the next learner-safe English question",
)
async def next_question(
    session_id: UUID,
    service: EnglishLearningServiceDependency,
) -> EnglishNextQuestionResponse:
    return _safe(lambda: service.next_question(str(session_id)))


@router.post(
    "/practice-sessions/{session_id}/questions/{question_key}/hint",
    operation_id="revealEnglishHint",
    response_model=EnglishHintResponse,
    summary="Reveal the authored hint for the current English question",
)
async def hint(
    session_id: UUID,
    question_key: Annotated[str, Path(pattern=r"^(ev|eg|eb|eo|er|ex)-l[1-5]-[0-9]{3,4}$")],
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSupportRateLimitDependency,
) -> EnglishHintResponse:
    return _safe(lambda: service.hint(str(session_id), question_key))


@router.post(
    "/attempts",
    operation_id="submitEnglishAttempt",
    response_model=EnglishAttemptResponse,
    summary="Submit an English response for deterministic marking",
)
async def submit_attempt(
    body: SubmitEnglishAttemptRequest,
    idempotency_key: IdempotencyHeader,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> EnglishAttemptResponse:
    return _safe(
        lambda: service.submit_attempt(
            session_id=body.session_id,
            question_key=body.question_key,
            question_revision=body.question_revision,
            answers=body.answers,
            idempotency_key=idempotency_key,
        )
    )


@router.post(
    "/attempts/{attempt_id}/error-classification",
    operation_id="classifyEnglishAttemptError",
    response_model=EnglishErrorClassificationResponse,
    summary="Record one immutable learner error category for an incorrect attempt",
)
async def classify_error(
    body: ClassifyEnglishErrorRequest,
    attempt_id: UUID,
    service: EnglishLearningServiceDependency,
    _rate_limit: PracticeSupportRateLimitDependency,
) -> EnglishErrorClassificationResponse:
    return _safe(lambda: service.classify_error(str(attempt_id), body.category))


@router.get(
    "/progress",
    operation_id="getEnglishProgress",
    response_model=EnglishProgressResponse,
    summary="Get authenticated objective-English lesson progress and retry counts",
)
async def progress(
    service: EnglishLearningServiceDependency,
) -> EnglishProgressResponse:
    return _safe(service.progress)
