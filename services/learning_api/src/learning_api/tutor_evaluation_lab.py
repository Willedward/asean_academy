"""Durable administrator workflow for synthetic and live tutor evaluation."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from psycopg.types.json import Jsonb

from .admin_repository import BetaOperationsError
from .content_review import list_review_queue
from .tutor_evaluation import (
    TutorEvaluationCase,
    TutorEvaluationSuite,
    load_evaluation_suite,
    run_evaluation,
)
from .tutor_provider import (
    GeminiTutorProvider,
    SyntheticTutorProvider,
    TutorProvider,
    TutorProviderError,
    probe_gemini_connection,
)
from .tutor_service import select_tutor_mode

SUITE_PATH = Path("backend_resources/tutor_evaluations/g3_math/v1/n2_calibration_v1.json")
GROUNDING_KEY = "g3-sec1-n2-tutor-grounding-v1"
GEMINI_CONNECTION_MODEL = "gemini-3.5-flash-lite"


def _suite(settings) -> TutorEvaluationSuite:
    return load_evaluation_suite(settings.repository_root / SUITE_PATH)


def _case(suite: TutorEvaluationSuite, case_id: str) -> TutorEvaluationCase:
    case = next((value for value in suite.cases if value.case_id == case_id), None)
    if case is None:
        raise BetaOperationsError(
            "tutor_evaluation_case_not_found", "The evaluation case was not found.", 404
        )
    return case


def _provider(settings, provider_name: str, model_name: str | None = None) -> tuple[TutorProvider, str]:
    if provider_name == "gemini":
        if not settings.tutor_gemini_api_key:
            raise BetaOperationsError(
                "gemini_not_configured",
                "Set GEMINI_API_KEY on the API service before a live run.",
                503,
            )
        selected_model = model_name or settings.tutor_gemini_model
        return (
            GeminiTutorProvider(
                api_key=settings.tutor_gemini_api_key,
                model=selected_model,
                timeout_seconds=settings.tutor_provider_timeout_seconds,
                # Administrator actions are explicit retries. Keep each request
                # within the web gateway's request window.
                max_attempts=1,
                input_cost_per_million_micros_sgd=(
                    settings.tutor_gemini_input_cost_per_million_micros_sgd
                ),
                output_cost_per_million_micros_sgd=(
                    settings.tutor_gemini_output_cost_per_million_micros_sgd
                ),
            ),
            selected_model,
        )
    if provider_name == "synthetic":
        return SyntheticTutorProvider(), "synthetic-tutor-v1"
    raise BetaOperationsError(
        "tutor_evaluation_provider_invalid", "The tutor provider is invalid.", 422
    )


def _require_approved_grounding(repository, catalogue) -> dict:
    gate = _grounding_gate(repository, catalogue)
    if gate["review_state"] != "approved":
        raise BetaOperationsError(
            "tutor_grounding_not_approved",
            "Mathematics and editorial grounding approval are required before evaluation.",
            409,
        )
    return gate


def _grounding_gate(repository, catalogue) -> dict:
    queue = list_review_queue(
        repository,
        catalogue,
        kind="tutor_grounding",
        source_status=None,
        review_state=None,
        search=GROUNDING_KEY,
        limit=20,
        offset=0,
    )
    item = next((value for value in queue["items"] if value["stable_key"] == GROUNDING_KEY), None)
    if item is None:
        raise BetaOperationsError(
            "tutor_grounding_missing", "The N2 tutor grounding review item is missing.", 503
        )
    return item


def _reviews(connection, run_ids: list[str]) -> dict[str, list[dict]]:
    if not run_ids:
        return {}
    rows = connection.execute(
        """select reviews.*, profiles.email as reviewer_email, profiles.role::text as reviewer_role
           from tutor_evaluation_reviews reviews join profiles on profiles.id=reviews.reviewer_id
           where reviews.run_id = any(%s::uuid[])
           order by reviews.created_at desc, reviews.id desc""",
        (run_ids,),
    ).fetchall()
    result: dict[str, list[dict]] = {}
    for row in rows:
        result.setdefault(str(row["run_id"]), []).append(dict(row))
    return result


def lab_state(repository, catalogue, settings) -> dict:
    suite = _suite(settings)
    gate = _grounding_gate(repository, catalogue)
    with repository._connect() as connection:
        rows = connection.execute(
            """select distinct on (case_id) * from tutor_evaluation_runs
               where suite_id=%s and suite_version=%s
               order by case_id, created_at desc, id desc""",
            (suite.suite_id, suite.version),
        ).fetchall()
        by_case = {row["case_id"]: dict(row) for row in rows}
        reviews = _reviews(connection, [str(row["id"]) for row in rows])
    cases = []
    for case in suite.cases:
        run = by_case.get(case.case_id)
        if run:
            run["reviews"] = reviews.get(str(run["id"]), [])
        cases.append({**case.model_dump(mode="json"), "latest_run": run})
    return {
        "suite_id": suite.suite_id,
        "suite_version": suite.version,
        "description": suite.description,
        "case_count": len(cases),
        "grounding_gate": gate,
        "gemini_configured": bool(settings.tutor_gemini_api_key),
        "gemini_model": settings.tutor_gemini_model,
        "prompt_version": settings.tutor_prompt_version,
        "cases": cases,
    }


async def check_gemini_connection(settings) -> dict:
    """Verify credentials and generation independently from the tutor prompt."""

    if not settings.tutor_gemini_api_key:
        raise BetaOperationsError(
            "gemini_not_configured",
            "Set GEMINI_API_KEY on the API service before checking the connection.",
            503,
        )
    started = perf_counter()
    try:
        result = await probe_gemini_connection(
            api_key=settings.tutor_gemini_api_key,
            model=GEMINI_CONNECTION_MODEL,
            timeout_seconds=min(settings.tutor_provider_timeout_seconds, 12),
        )
    except TutorProviderError as exc:
        raise BetaOperationsError("gemini_connection_failed", str(exc), 503) from exc
    return {
        "connected": True,
        "probe_model": result.model_name,
        "configured_tutor_model": settings.tutor_gemini_model,
        "response_text": result.response_text,
        "latency_ms": max(0, round((perf_counter() - started) * 1000)),
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }


async def execute_case(
    repository,
    catalogue,
    settings,
    administrator,
    case_id: str,
    provider_name: str,
    request_id: str,
) -> dict:
    suite = _suite(settings)
    case = _case(suite, case_id)
    _require_approved_grounding(repository, catalogue)
    provider, model = _provider(settings, provider_name)
    one = suite.model_copy(update={"cases": [case]})
    report = await run_evaluation(
        provider,
        one,
        provider_name=model,
        prompt_version=settings.tutor_prompt_version,
        max_output_tokens=settings.tutor_max_output_tokens,
    )
    result = report.cases[0]
    with repository._connect() as connection:
        row = connection.execute(
            """insert into tutor_evaluation_runs
               (suite_id,suite_version,case_id,case_snapshot,provider,model_name,prompt_version,
                automated_pass,latency_ms,input_tokens,output_tokens,cost_micros_sgd,response_blocks,
                suggested_replies,recommended_next_action,automated_checks,provider_error,created_by,request_id)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning *""",
            (
                suite.suite_id,
                suite.version,
                case.case_id,
                Jsonb(case.model_dump(mode="json")),
                provider_name,
                result.model_name,
                result.model_name
                and settings.tutor_prompt_version
                or settings.tutor_prompt_version,
                result.automated_pass,
                result.latency_ms,
                result.input_tokens,
                result.output_tokens,
                result.cost_micros_sgd,
                Jsonb([b.model_dump(mode="json") for b in result.blocks]),
                Jsonb(result.suggested_replies),
                result.recommended_next_action,
                Jsonb([c.model_dump(mode="json") for c in result.checks]),
                result.provider_error,
                administrator.learner_id,
                request_id,
            ),
        ).fetchone()
        connection.execute(
            """insert into beta_audit_events(event_type,actor_user_id,request_id,metadata)
                              values ('tutor_evaluation_run_created',%s,%s,%s)""",
            (
                administrator.learner_id,
                request_id,
                Jsonb({"run_id": str(row["id"]), "case_id": case_id, "provider": provider_name}),
            ),
        )
    return {**dict(row), "reviews": []}


def _conversation(connection, conversation_id, administrator) -> dict:
    row = connection.execute(
        """select * from tutor_evaluation_conversations
           where id=%s and created_by=%s""",
        (conversation_id, administrator.learner_id),
    ).fetchone()
    if row is None:
        raise BetaOperationsError(
            "tutor_evaluation_conversation_not_found",
            "The tutor evaluation conversation was not found.",
            404,
        )
    turns = connection.execute(
        """select * from tutor_evaluation_conversation_turns
           where conversation_id=%s order by turn_index""",
        (conversation_id,),
    ).fetchall()
    return {**dict(row), "turns": [dict(turn) for turn in turns]}


def latest_conversation(repository, settings, administrator, case_id: str) -> dict | None:
    suite = _suite(settings)
    _case(suite, case_id)
    with repository._connect() as connection:
        row = connection.execute(
            """select id from tutor_evaluation_conversations
               where suite_id=%s and suite_version=%s and case_id=%s and created_by=%s
               order by created_at desc, id desc limit 1""",
            (suite.suite_id, suite.version, case_id, administrator.learner_id),
        ).fetchone()
        if row is None:
            return None
        return _conversation(connection, row["id"], administrator)


def get_conversation(repository, administrator, conversation_id) -> dict:
    with repository._connect() as connection:
        return _conversation(connection, conversation_id, administrator)


def create_conversation(
    repository,
    catalogue,
    settings,
    administrator,
    case_id: str,
    provider_name: str,
    request_id: str,
) -> dict:
    suite = _suite(settings)
    case = _case(suite, case_id)
    _require_approved_grounding(repository, catalogue)
    _, model = _provider(settings, provider_name)
    with repository._connect() as connection:
        row = connection.execute(
            """insert into tutor_evaluation_conversations
               (suite_id,suite_version,case_id,case_snapshot,provider,model_name,
                prompt_version,created_by,request_id)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning *""",
            (
                suite.suite_id,
                suite.version,
                case.case_id,
                Jsonb(case.model_dump(mode="json")),
                provider_name,
                model,
                settings.tutor_prompt_version,
                administrator.learner_id,
                request_id,
            ),
        ).fetchone()
        connection.execute(
            """insert into beta_audit_events(event_type,actor_user_id,request_id,metadata)
               values ('tutor_evaluation_conversation_created',%s,%s,%s)""",
            (
                administrator.learner_id,
                request_id,
                Jsonb(
                    {
                        "conversation_id": str(row["id"]),
                        "case_id": case_id,
                        "provider": provider_name,
                    }
                ),
            ),
        )
    return {**dict(row), "turns": []}


def _conversation_case(case: TutorEvaluationCase, turns: list[dict], message: str):
    history = list(case.recent_messages)
    for turn in turns:
        history.append(
            {
                "role": "student",
                "mode": None,
                "content": {"blocks": [{"type": "text", "content": turn["learner_message"]}]},
            }
        )
        if turn["response_blocks"]:
            history.append(
                {
                    "role": "assistant",
                    "mode": turn["mode"],
                    "content": {
                        "blocks": turn["response_blocks"],
                        "suggested_replies": turn["suggested_replies"],
                        "recommended_next_action": turn["recommended_next_action"],
                    },
                }
            )
    latest_incorrect = bool(case.latest_attempt and not case.latest_attempt.get("correct", False))
    mode = select_tutor_mode(message, case.solution_locked, int(latest_incorrect))
    return case.model_copy(
        update={
            "mode": mode,
            "learner_message": message,
            "recent_messages": history[-8:],
        }
    )


async def create_conversation_turn(
    repository,
    catalogue,
    settings,
    administrator,
    conversation_id,
    message: str,
    request_id: str,
) -> dict:
    _require_approved_grounding(repository, catalogue)
    conversation = get_conversation(repository, administrator, conversation_id)
    snapshot = TutorEvaluationCase.model_validate(conversation["case_snapshot"])
    dynamic_case = _conversation_case(snapshot, conversation["turns"], message)
    provider, model = _provider(
        settings, conversation["provider"], conversation["model_name"]
    )
    suite = TutorEvaluationSuite(
        suite_id=conversation["suite_id"],
        version=conversation["suite_version"],
        description="Durable multi-turn administrator tutor evaluation.",
        cases=[dynamic_case],
    )
    report = await run_evaluation(
        provider,
        suite,
        provider_name=model,
        prompt_version=conversation["prompt_version"],
        max_output_tokens=settings.tutor_max_output_tokens,
    )
    result = report.cases[0]
    with repository._connect() as connection:
        locked = connection.execute(
            """select id from tutor_evaluation_conversations
               where id=%s and created_by=%s for update""",
            (conversation_id, administrator.learner_id),
        ).fetchone()
        if locked is None:
            raise BetaOperationsError(
                "tutor_evaluation_conversation_not_found",
                "The tutor evaluation conversation was not found.",
                404,
            )
        next_index = connection.execute(
            """select coalesce(max(turn_index),0)+1 as value
               from tutor_evaluation_conversation_turns where conversation_id=%s""",
            (conversation_id,),
        ).fetchone()["value"]
        row = connection.execute(
            """insert into tutor_evaluation_conversation_turns
               (conversation_id,turn_index,learner_message,mode,automated_pass,latency_ms,
                input_tokens,output_tokens,cost_micros_sgd,response_blocks,suggested_replies,
                recommended_next_action,automated_checks,provider_error,created_by,request_id)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning *""",
            (
                conversation_id,
                next_index,
                message,
                dynamic_case.mode,
                result.automated_pass,
                result.latency_ms,
                result.input_tokens,
                result.output_tokens,
                result.cost_micros_sgd,
                Jsonb([block.model_dump(mode="json") for block in result.blocks]),
                Jsonb(result.suggested_replies),
                result.recommended_next_action,
                Jsonb([check.model_dump(mode="json") for check in result.checks]),
                result.provider_error,
                administrator.learner_id,
                request_id,
            ),
        ).fetchone()
        connection.execute(
            """insert into beta_audit_events(event_type,actor_user_id,request_id,metadata)
               values ('tutor_evaluation_conversation_turn_created',%s,%s,%s)""",
            (
                administrator.learner_id,
                request_id,
                Jsonb(
                    {
                        "conversation_id": str(conversation_id),
                        "turn_id": str(row["id"]),
                        "turn_index": next_index,
                        "mode": dynamic_case.mode,
                        "provider": conversation["provider"],
                    }
                ),
            ),
        )
    return dict(row)


def record_evaluation_review(repository, administrator, run_id, body, request_id: str) -> dict:
    if body.dimension == "mathematics" and administrator.role != "academic_admin":
        raise BetaOperationsError(
            "academic_review_required",
            "Only an academic administrator can record Mathematics review.",
            403,
        )
    with repository._connect() as connection:
        if (
            connection.execute(
                "select 1 from tutor_evaluation_runs where id=%s", (run_id,)
            ).fetchone()
            is None
        ):
            raise BetaOperationsError(
                "tutor_evaluation_run_not_found", "The evaluation run was not found.", 404
            )
        row = connection.execute(
            """insert into tutor_evaluation_reviews
               (run_id,dimension,decision,mathematics_correctness,pedagogical_quality,curriculum_fit,
                safety_and_leakage,notes,reviewer_id,request_id)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning *""",
            (
                run_id,
                body.dimension,
                body.decision,
                body.mathematics_correctness,
                body.pedagogical_quality,
                body.curriculum_fit,
                body.safety_and_leakage,
                body.notes.strip(),
                administrator.learner_id,
                request_id,
            ),
        ).fetchone()
        connection.execute(
            """insert into beta_audit_events(event_type,actor_user_id,request_id,metadata)
                              values ('tutor_evaluation_review_recorded',%s,%s,%s)""",
            (
                administrator.learner_id,
                request_id,
                Jsonb(
                    {"run_id": str(run_id), "dimension": body.dimension, "decision": body.decision}
                ),
            ),
        )
    return dict(row)
