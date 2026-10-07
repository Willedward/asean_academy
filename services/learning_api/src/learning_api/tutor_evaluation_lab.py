"""Durable administrator workflow for synthetic and live tutor evaluation."""

from __future__ import annotations

from pathlib import Path

from psycopg.types.json import Jsonb

from .admin_repository import BetaOperationsError
from .content_review import list_review_queue
from .tutor_evaluation import TutorEvaluationSuite, load_evaluation_suite, run_evaluation
from .tutor_provider import GeminiTutorProvider, SyntheticTutorProvider

SUITE_PATH = Path("backend_resources/tutor_evaluations/g3_math/v1/n2_calibration_v1.json")
GROUNDING_KEY = "g3-sec1-n2-tutor-grounding-v1"


def _suite(settings) -> TutorEvaluationSuite:
    return load_evaluation_suite(settings.repository_root / SUITE_PATH)


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
    case = next((value for value in suite.cases if value.case_id == case_id), None)
    if case is None:
        raise BetaOperationsError(
            "tutor_evaluation_case_not_found", "The evaluation case was not found.", 404
        )
    gate = _grounding_gate(repository, catalogue)
    if gate["review_state"] != "approved":
        raise BetaOperationsError(
            "tutor_grounding_not_approved",
            "Mathematics and editorial grounding approval are required before evaluation.",
            409,
        )
    if provider_name == "gemini":
        if not settings.tutor_gemini_api_key:
            raise BetaOperationsError(
                "gemini_not_configured",
                "Set GEMINI_API_KEY on the API service before a live run.",
                503,
            )
        provider = GeminiTutorProvider(
            api_key=settings.tutor_gemini_api_key,
            model=settings.tutor_gemini_model,
            timeout_seconds=settings.tutor_provider_timeout_seconds,
            # The administrator explicitly retries evaluation runs. Keep one live
            # attempt below the web gateway's request window instead of holding the
            # browser through two provider timeouts.
            max_attempts=1,
            input_cost_per_million_micros_sgd=settings.tutor_gemini_input_cost_per_million_micros_sgd,
            output_cost_per_million_micros_sgd=settings.tutor_gemini_output_cost_per_million_micros_sgd,
        )
        model = settings.tutor_gemini_model
    else:
        provider = SyntheticTutorProvider()
        model = "synthetic-tutor-v1"
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
