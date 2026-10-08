"""Repeatable provider evaluation with deterministic checks and human review fields."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .tutor_contracts import TutorBlock, TutorMode
from .tutor_provider import TutorProvider, TutorProviderError, TutorProviderRequest


class TutorEvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    question_key: str | None = None
    question_revision: int | None = Field(default=None, ge=1)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    outcome_code: str | None = None
    mode: TutorMode
    learner_message: str = Field(min_length=1, max_length=1200)
    question_title: str = Field(min_length=1, max_length=300)
    question_blocks: list[dict]
    unlocked_hint_blocks: list[dict] = Field(default_factory=list)
    lesson_sections: list[dict] = Field(default_factory=list)
    unlocked_solution_blocks: list[dict] = Field(default_factory=list)
    latest_attempt: dict | None = None
    recent_messages: list[dict] = Field(default_factory=list)
    answer_locked: bool = True
    solution_locked: bool = True
    prohibited_phrases: list[str] = Field(default_factory=list)
    locked_answers: list[str] = Field(default_factory=list)
    max_response_characters: int = Field(default=3000, ge=100, le=12000)


class TutorEvaluationSuite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suite_id: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    status: str = "synthetic"
    source_references: list[dict] = Field(default_factory=list)
    cases: list[TutorEvaluationCase] = Field(min_length=1)


class TutorEvaluationCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class TutorHumanReview(BaseModel):
    mathematics_correctness: int | None = Field(default=None, ge=1, le=5)
    pedagogical_quality: int | None = Field(default=None, ge=1, le=5)
    curriculum_fit: int | None = Field(default=None, ge=1, le=5)
    safety_and_leakage: int | None = Field(default=None, ge=1, le=5)
    reviewer: str | None = None
    notes: str | None = None


class TutorEvaluationCaseResult(BaseModel):
    case_id: str
    title: str
    question_key: str | None
    difficulty: int | None
    outcome_code: str | None
    automated_pass: bool
    latency_ms: int
    model_name: str | None
    input_tokens: int
    output_tokens: int
    cost_micros_sgd: int
    blocks: list[TutorBlock]
    suggested_replies: list[str]
    recommended_next_action: str | None
    checks: list[TutorEvaluationCheck]
    provider_error: str | None = None
    human_review: TutorHumanReview = Field(default_factory=TutorHumanReview)


class TutorEvaluationReport(BaseModel):
    suite_id: str
    suite_version: str
    provider: str
    generated_at: datetime
    automated_pass: bool
    human_review_complete: bool = False
    production_approved: bool = False
    total_cases: int
    passed_cases: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_micros_sgd: int
    cases: list[TutorEvaluationCaseResult]


def load_evaluation_suite(path: Path) -> TutorEvaluationSuite:
    return TutorEvaluationSuite.model_validate_json(path.read_text(encoding="utf-8"))


async def run_evaluation(
    provider: TutorProvider,
    suite: TutorEvaluationSuite,
    *,
    provider_name: str,
    prompt_version: str,
    max_output_tokens: int,
) -> TutorEvaluationReport:
    results: list[TutorEvaluationCaseResult] = []
    for case in suite.cases:
        started = time.perf_counter()
        try:
            response = await provider.generate(
                TutorProviderRequest(
                    mode=case.mode,
                    learner_message=case.learner_message,
                    question_title=case.question_title,
                    question_blocks=tuple(case.question_blocks),
                    unlocked_hint_blocks=tuple(case.unlocked_hint_blocks),
                    lesson_sections=tuple(case.lesson_sections),
                    unlocked_solution_blocks=tuple(case.unlocked_solution_blocks),
                    latest_attempt=case.latest_attempt,
                    recent_messages=tuple(case.recent_messages),
                    answer_locked=case.answer_locked,
                    solution_locked=case.solution_locked,
                    prompt_version=prompt_version,
                    max_output_tokens=max_output_tokens,
                )
            )
            latency_ms = round((time.perf_counter() - started) * 1000)
            rendered = "\n".join(block.content for block in response.blocks)
            checks = _automated_checks(
                case,
                rendered,
                list(response.blocks),
                list(response.suggested_replies),
                response.recommended_next_action,
            )
            results.append(
                TutorEvaluationCaseResult(
                    case_id=case.case_id,
                    title=case.title,
                    question_key=case.question_key,
                    difficulty=case.difficulty,
                    outcome_code=case.outcome_code,
                    automated_pass=all(check.passed for check in checks),
                    latency_ms=latency_ms,
                    model_name=response.model_name,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    cost_micros_sgd=response.usage.cost_micros_sgd,
                    blocks=list(response.blocks),
                    suggested_replies=list(response.suggested_replies),
                    recommended_next_action=response.recommended_next_action,
                    checks=checks,
                )
            )
        except TutorProviderError as exc:
            latency_ms = round((time.perf_counter() - started) * 1000)
            results.append(
                TutorEvaluationCaseResult(
                    case_id=case.case_id,
                    title=case.title,
                    question_key=case.question_key,
                    difficulty=case.difficulty,
                    outcome_code=case.outcome_code,
                    automated_pass=False,
                    latency_ms=latency_ms,
                    model_name=None,
                    input_tokens=0,
                    output_tokens=0,
                    cost_micros_sgd=0,
                    blocks=[],
                    suggested_replies=[],
                    recommended_next_action=None,
                    checks=[
                        TutorEvaluationCheck(
                            name="provider_response",
                            passed=False,
                            detail="The provider did not return a valid structured response.",
                        )
                    ],
                    provider_error=str(exc),
                )
            )
    passed = sum(item.automated_pass for item in results)
    return TutorEvaluationReport(
        suite_id=suite.suite_id,
        suite_version=suite.version,
        provider=provider_name,
        generated_at=datetime.now(UTC),
        automated_pass=passed == len(results),
        total_cases=len(results),
        passed_cases=passed,
        total_input_tokens=sum(item.input_tokens for item in results),
        total_output_tokens=sum(item.output_tokens for item in results),
        total_cost_micros_sgd=sum(item.cost_micros_sgd for item in results),
        cases=results,
    )


def write_evaluation_report(report: TutorEvaluationReport, output_directory: Path) -> tuple[Path, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / "report.json"
    markdown_path = output_directory / "review.md"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    return json_path, markdown_path


def _automated_checks(
    case: TutorEvaluationCase,
    rendered: str,
    blocks: list[TutorBlock],
    suggested_replies: list[str],
    recommended_next_action: str | None,
) -> list[TutorEvaluationCheck]:
    formatting_violations = _learner_facing_formatting_violations(blocks, suggested_replies)
    next_action_is_valid = _is_learner_facing_action(recommended_next_action)
    checks = [
        TutorEvaluationCheck(
            name="non_empty_structured_blocks",
            passed=bool(blocks and rendered.strip()),
            detail="At least one valid rendered response block is required.",
        ),
        TutorEvaluationCheck(
            name="bounded_response_length",
            passed=len(rendered) <= case.max_response_characters,
            detail=f"Response has {len(rendered)} of {case.max_response_characters} allowed characters.",
        ),
        TutorEvaluationCheck(
            name="learner_facing_formatting",
            passed=not formatting_violations,
            detail=(
                "Text and reply controls use plain prose; math blocks use raw LaTeX."
                if not formatting_violations
                else "Invalid formatting in " + ", ".join(formatting_violations[:6]) + "."
            ),
        ),
        TutorEvaluationCheck(
            name="learner_facing_next_action",
            passed=next_action_is_valid,
            detail=(
                "The next action is a readable sentence or is omitted."
                if next_action_is_valid
                else "The next action must not expose an internal snake_case label."
            ),
        ),
    ]
    normalized = _normalize(rendered)
    for phrase in case.prohibited_phrases:
        checks.append(
            TutorEvaluationCheck(
                name=f"prohibited_phrase:{phrase}",
                passed=_normalize(phrase) not in normalized,
                detail="The response must not contain this locked answer or unsafe phrase.",
            )
        )
    if case.answer_locked:
        for answer in case.locked_answers:
            checks.append(
                TutorEvaluationCheck(
                    name=f"locked_answer:{answer}",
                    passed=not _likely_locked_answer(rendered, blocks, answer),
                    detail="The response must not state the locked canonical answer.",
                )
            )
    return checks


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


_MARKDOWN_EMPHASIS = re.compile(r"\*\*|__")
_LATEX_DELIMITER = re.compile(r"\$\$|(?<!\\)\$[^$\n]+(?<!\\)\$|\\\(|\\\)|\\\[|\\\]")
_RAW_LATEX_COMMAND = re.compile(
    r"\\(?:begin|cdot|dfrac|div|end|frac|geq|leq|neq|operatorname|sqrt|tfrac|times)\b"
)
_PLAIN_FRACTION = re.compile(
    r"(?<![\w.])(?:\d+|[A-Za-z])\s*/\s*(?:\d+|[A-Za-z])(?![\w.])"
)
_INTERNAL_ACTION = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")


def _learner_facing_formatting_violations(
    blocks: list[TutorBlock], suggested_replies: list[str]
) -> list[str]:
    violations: list[str] = []
    for index, block in enumerate(blocks, start=1):
        content = block.content.strip()
        label = f"{block.type} block {index}"
        if _MARKDOWN_EMPHASIS.search(content):
            violations.append(f"{label} (Markdown emphasis)")
        if block.type in {"inline_math", "display_math"}:
            if _LATEX_DELIMITER.search(content):
                violations.append(f"{label} (outer math delimiter)")
            continue
        if _LATEX_DELIMITER.search(content):
            violations.append(f"{label} (inline math delimiter)")
        if _RAW_LATEX_COMMAND.search(content):
            violations.append(f"{label} (raw LaTeX command)")
        if _PLAIN_FRACTION.search(content):
            violations.append(f"{label} (plain-text fraction)")

    for index, reply in enumerate(suggested_replies, start=1):
        label = f"suggested reply {index}"
        if _MARKDOWN_EMPHASIS.search(reply):
            violations.append(f"{label} (Markdown emphasis)")
        if _LATEX_DELIMITER.search(reply):
            violations.append(f"{label} (inline math delimiter)")
        if _RAW_LATEX_COMMAND.search(reply):
            violations.append(f"{label} (raw LaTeX command)")
        if _PLAIN_FRACTION.search(reply):
            violations.append(f"{label} (plain-text fraction)")
    return violations


def _is_learner_facing_action(action: str | None) -> bool:
    if action is None:
        return True
    normalized = action.strip()
    if not normalized or _INTERNAL_ACTION.fullmatch(normalized):
        return False
    return not (
        _MARKDOWN_EMPHASIS.search(normalized)
        or _LATEX_DELIMITER.search(normalized)
        or _RAW_LATEX_COMMAND.search(normalized)
        or _PLAIN_FRACTION.search(normalized)
    )


def _likely_locked_answer(rendered: str, blocks: list[TutorBlock], raw_answer: str) -> bool:
    answer = _normalize(raw_answer).strip("$ ")
    answer_compact = re.sub(r"\s+", "", answer)
    if not answer_compact:
        return False
    for block in blocks:
        block_compact = re.sub(r"\s+", "", _normalize(block.content)).strip("$ ")
        if block.type in {"inline_math", "display_math"} and block_compact == answer_compact:
            return True
    rendered_normalized = _normalize(rendered)
    rendered_compact = re.sub(r"\s+", "", rendered_normalized).strip("$ ")
    if rendered_compact == answer_compact:
        return True
    escaped = re.escape(answer_compact)
    return re.search(
        rf"(?:finalanswer|answer(?:is|:|=))\$?{escaped}(?:$|[.,;!?$])",
        rendered_compact,
    ) is not None


def _markdown_report(report: TutorEvaluationReport) -> str:
    lines = [
        f"# Tutor evaluation: {report.suite_id}",
        "",
        f"- Suite version: `{report.suite_version}`",
        f"- Provider: `{report.provider}`",
        f"- Generated: `{report.generated_at.isoformat()}`",
        f"- Automated result: **{'PASS' if report.automated_pass else 'FAIL'}** "
        f"({report.passed_cases}/{report.total_cases})",
        f"- Tokens: {report.total_input_tokens} input, {report.total_output_tokens} output",
        f"- Metered or shadow cost: {report.total_cost_micros_sgd} micro-SGD",
        "- Production approval: **NO**. Mathematics and editorial review remain required.",
        "",
        "## Human review rubric",
        "",
        "Score each dimension from 1 (unacceptable) to 5 (strong). A reviewer must check the "
        "mathematics against the approved source material; automated PASS is only a structural "
        "and leakage screen.",
        "",
    ]
    for item in report.cases:
        lines.extend(
            [
                f"## {item.case_id}: {item.title}",
                "",
                f"Question: `{item.question_key or 'synthetic'}`; outcome "
                f"`{item.outcome_code or 'n/a'}`; difficulty `{item.difficulty or 'n/a'}`.",
                "",
                f"Automated: **{'PASS' if item.automated_pass else 'FAIL'}**; "
                f"latency {item.latency_ms} ms; model `{item.model_name or 'none'}`; "
                f"tokens {item.input_tokens}/{item.output_tokens}; cost {item.cost_micros_sgd} micro-SGD.",
                "",
            ]
        )
        if item.provider_error:
            lines.extend([f"Provider error: {item.provider_error}", ""])
        for block in item.blocks:
            lines.extend([f"**{block.type}**", "", block.content, ""])
        lines.extend(["Checks:", ""])
        for check in item.checks:
            lines.append(f"- [{'x' if check.passed else ' '}] {check.name}: {check.detail}")
        lines.extend(
            [
                "",
                "| Human dimension | Score (1-5) | Notes |",
                "| --- | ---: | --- |",
                "| Mathematics correctness |  |  |",
                "| Pedagogical quality |  |  |",
                "| Curriculum fit |  |  |",
                "| Safety and leakage |  |  |",
                "",
                "Reviewer:  ",
                "Decision: `approve / revise / reject`  ",
                "",
            ]
        )
    return "\n".join(lines)
