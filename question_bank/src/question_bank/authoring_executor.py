"""Execute model-independent authoring work orders with deterministic gates."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .authoring import (
    GeneratorMetadata,
    detect_prompt_duplicates,
    export_reviewer_batch,
    load_manifest,
    validate_batch,
)
from .checking import check_answer
from .collaboration import load_claim_registry
from .models import AlgebraicResponse, NumericResponse, Question

EXECUTOR_VERSION = "question-authoring-executor-v1"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


class AuthoringExecutionError(ValueError):
    """A work order or generated batch failed a deterministic execution gate."""


@dataclass
class GenerationAttempt:
    number: int
    valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class GeneratedBatch:
    questions: list[Question]
    warnings: list[str]


GenerationCall = Callable[[str, dict[str, Any]], dict[str, Any] | list[Any]]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthoringExecutionError(f"Cannot read JSON from {path}: {exc}") from exc


def _verify_active_claim(
    batch_id: str,
    *,
    repository_root: Path,
    claim_registry_path: Path,
) -> None:
    registry = load_claim_registry(claim_registry_path)
    claims = [claim for claim in registry.claims if claim.batch_id == batch_id and claim.active]
    if len(claims) != 1:
        raise AuthoringExecutionError(
            f"Batch {batch_id} needs exactly one active claim before paid generation"
        )
    try:
        completed = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AuthoringExecutionError(f"Cannot determine the active Git branch: {exc}") from exc
    branch = completed.stdout.strip()
    if branch != claims[0].branch:
        raise AuthoringExecutionError(
            f"Batch {batch_id} is claimed for branch {claims[0].branch}, not {branch}"
        )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _strict_schema(node: Any) -> Any:
    """Make every object field required for Responses API strict structured output."""

    if isinstance(node, list):
        return [_strict_schema(item) for item in node]
    if not isinstance(node, dict):
        return node
    if node.get("title") == "Checker Config":
        node = {
            "type": "object",
            "properties": {
                "require_prime_bases": {"type": ["boolean", "null"]},
                "order": {
                    "type": ["string", "null"],
                    "enum": ["ascending", "descending", None],
                },
                "allowed_operators": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "null"},
                    ]
                },
                "terms": {"type": ["integer", "null"]},
                "require_simplest_integer_terms": {"type": ["boolean", "null"]},
            },
        }
    elif node.get("title") == "Generation Spec":
        node = {
            "type": "object",
            "properties": {"description": {"type": ["string", "null"]}},
        }
    cleaned = {
        key: _strict_schema(value)
        for key, value in node.items()
        if key not in {"default", "discriminator", "title"}
    }
    if "oneOf" in cleaned:
        cleaned["anyOf"] = cleaned.pop("oneOf")
    if "prefixItems" in cleaned:
        alternatives = cleaned.pop("prefixItems")
        unique = {json.dumps(item, sort_keys=True) for item in alternatives}
        cleaned["items"] = (
            alternatives[0] if len(unique) == 1 else {"anyOf": alternatives}
        )
    if cleaned.get("type") == "object" or "properties" in cleaned:
        properties = cleaned.get("properties", {})
        cleaned["additionalProperties"] = False
        cleaned["required"] = list(properties)
    return cleaned


def response_schema(question_schema: dict[str, Any]) -> dict[str, Any]:
    """Wrap the Question schema in the batch response object used by providers."""

    schema = {
        "$defs": question_schema.get("$defs", {}),
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    key: value
                    for key, value in question_schema.items()
                    if key not in {"$defs", "$schema"}
                },
            }
        },
        "required": ["questions"],
        "additionalProperties": False,
    }
    return _strict_schema(schema)


def _extract_openai_output(payload: dict[str, Any]) -> dict[str, Any] | list[Any]:
    if isinstance(payload.get("output_text"), str):
        return json.loads(payload["output_text"])
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise AuthoringExecutionError(
                    f"OpenAI refused the authoring request: {content.get('refusal', 'unknown')}"
                )
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return json.loads(content["text"])
    status = payload.get("status", "unknown")
    incomplete = payload.get("incomplete_details")
    raise AuthoringExecutionError(
        f"OpenAI response contained no structured output (status={status}, details={incomplete})"
    )


class OpenAIResponsesProvider:
    """Small dependency-free adapter for Responses API structured output."""

    def __init__(
        self,
        model: str,
        *,
        timeout_seconds: int = 300,
        max_output_tokens: int = 50_000,
    ):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise AuthoringExecutionError(
                "Set OPENAI_API_KEY before using the openai authoring provider"
            )
        if not model.strip():
            raise AuthoringExecutionError("An OpenAI model must be supplied")
        if max_output_tokens < 1:
            raise AuthoringExecutionError("max_output_tokens must be positive")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens

    def __call__(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any] | list[Any]:
        body = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": self.max_output_tokens,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "question_batch",
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        request = urllib.request.Request(
            OPENAI_RESPONSES_URL,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise AuthoringExecutionError(
                f"OpenAI Responses API returned HTTP {exc.code}: {detail[:2000]}"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise AuthoringExecutionError(f"OpenAI Responses API request failed: {exc}") from exc
        return _extract_openai_output(payload)


def response_file_provider(path: Path) -> GenerationCall:
    """Return a deterministic provider for a saved model response."""

    payload = _read_json(path)

    def generate(_prompt: str, _schema: dict[str, Any]):
        return payload

    return generate


def _canonical_candidates(question: Question):
    for part in question.parts:
        response = part.response
        if isinstance(response, NumericResponse):
            yield part.position, "canonical", response.canonical_answer, response
            for answer in response.accepted_answers:
                yield part.position, "accepted", answer, response
        elif isinstance(response, AlgebraicResponse):
            yield part.position, "canonical", response.canonical_expression, response
            for answer in response.accepted_equivalents:
                yield part.position, "accepted", answer, response


def _normalise_question(
    raw: dict[str, Any],
    slot: dict[str, Any],
    work_order: dict[str, Any],
    *,
    authored_by: str,
    created_at: datetime,
) -> dict[str, Any]:
    question = dict(raw)
    question.update(
        {
            "schema_version": "1.0.0",
            "revision": 1,
            "stable_key": slot["stable_key"],
            "bank_key": work_order["bank_key"],
            "curriculum_version": work_order["curriculum_version"],
            "school_level": work_order["school_level"],
            "topic_code": work_order["topic"]["code"],
            "primary_outcome": slot["primary_outcome"],
            "difficulty": slot["difficulty"],
            "question_type": "structured",
            "status": "draft",
        }
    )
    style_references = [
        reference["path"]
        for reference in work_order["source_references"]
        if reference["role"] == "style"
    ]
    question["provenance"] = {
        "authoring_method": "original_generated",
        "style_references": style_references,
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
        "authored_by": authored_by,
        "reviewed_at": None,
        "reviewed_by": None,
        "review_notes": None,
    }
    return question


def validate_generated_response(
    payload: dict[str, Any] | list[Any],
    work_order: dict[str, Any],
    *,
    repository_root: Path,
    authored_by: str,
    created_at: datetime | None = None,
) -> GeneratedBatch:
    """Validate and normalise a provider response without changing repository files."""

    raw_questions = payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(raw_questions, list):
        raise AuthoringExecutionError("Provider response must contain a questions array")
    slots = work_order.get("slots")
    if not isinstance(slots, list) or not slots:
        raise AuthoringExecutionError("Work order has no reserved question slots")
    if len(raw_questions) != len(slots):
        raise AuthoringExecutionError(
            f"Provider returned {len(raw_questions)} questions; expected {len(slots)}"
        )
    expected_keys = [slot["stable_key"] for slot in slots]
    received_keys = [item.get("stable_key") for item in raw_questions if isinstance(item, dict)]
    if received_keys != expected_keys:
        raise AuthoringExecutionError(
            "Provider questions must appear in reserved slot order with exact stable keys; "
            f"expected {expected_keys}, received {received_keys}"
        )

    timestamp = created_at or datetime.now(UTC)
    questions: list[Question] = []
    errors: list[str] = []
    for index, (raw, slot) in enumerate(zip(raw_questions, slots, strict=True), start=1):
        if not isinstance(raw, dict):
            errors.append(f"slot {index}: question must be an object")
            continue
        expected_metadata = {
            "stable_key": slot["stable_key"],
            "bank_key": work_order["bank_key"],
            "curriculum_version": work_order["curriculum_version"],
            "school_level": work_order["school_level"],
            "topic_code": work_order["topic"]["code"],
            "primary_outcome": slot["primary_outcome"],
            "difficulty": slot["difficulty"],
        }
        for field_name, expected in expected_metadata.items():
            if raw.get(field_name) != expected:
                errors.append(
                    f"{slot['stable_key']}: provider returned {field_name}="
                    f"{raw.get(field_name)!r}; expected {expected!r}"
                )
        normalised = _normalise_question(
            raw,
            slot,
            work_order,
            authored_by=authored_by,
            created_at=timestamp,
        )
        try:
            question = Question.model_validate(normalised)
        except ValidationError as exc:
            errors.append(f"{slot['stable_key']}: {exc}")
            continue
        if any(part.primary_outcome != slot["primary_outcome"] for part in question.parts):
            errors.append(
                f"{question.stable_key}: every part must use allocated outcome "
                f"{slot['primary_outcome']}"
            )
        for position, kind, answer, response in _canonical_candidates(question):
            result = check_answer(response, answer)
            if not result["correct"]:
                errors.append(
                    f"{question.stable_key} part {position} {kind} answer {answer!r} "
                    f"failed the checker: {result['error'] or 'incorrect'}"
                )
        for asset in question.assets:
            asset_path = (
                repository_root
                / Path(work_order["manifest_path"]).parent.parent
                / asset.path
            )
            if not asset_path.is_file():
                errors.append(
                    f"{question.stable_key}: generated asset does not exist: {asset.path}"
                )
            elif hashlib.sha256(asset_path.read_bytes()).hexdigest() != asset.sha256:
                errors.append(
                    f"{question.stable_key}: generated asset checksum mismatch: {asset.path}"
                )
        questions.append(question)
    if errors:
        raise AuthoringExecutionError("\n".join(errors))

    existing: list[Question] = []
    bank_root = repository_root / "backend_resources/question_bank/g3_math"
    for path in sorted(bank_root.glob("**/questions/*.json")):
        try:
            existing.append(Question.model_validate_json(path.read_text()))
        except (OSError, ValidationError):
            continue
    matches = detect_prompt_duplicates([*existing, *questions])
    new_keys = {question.stable_key for question in questions}
    relevant = [match for match in matches if match.second_key in new_keys]
    exact = [match for match in relevant if match.kind == "exact_prompt"]
    if exact:
        details = "; ".join(
            f"{match.second_key} duplicates {match.first_key}" for match in exact
        )
        raise AuthoringExecutionError(f"Exact prompt duplicates detected: {details}")
    warnings = [
        f"{match.second_key} resembles {match.first_key} ({match.similarity:.4f})"
        for match in relevant
        if match.kind == "near_prompt"
    ]
    return GeneratedBatch(questions=questions, warnings=warnings)


def _repair_prompt(prompt: str, payload: Any, errors: list[str]) -> str:
    error_text = "\n".join(f"- {error}" for error in errors)
    return f"""{prompt}

## Correction request

The previous response failed deterministic validation. Return the complete corrected
`questions` object, keeping all reserved keys in their original order.

Validation failures:
{error_text}

Previous response:
{json.dumps(payload, ensure_ascii=False)}
"""


def generate_batch(
    work_order: dict[str, Any],
    prompt: str,
    provider_call: GenerationCall,
    *,
    repository_root: Path,
    authored_by: str,
    max_repairs: int,
) -> tuple[GeneratedBatch, list[GenerationAttempt]]:
    """Generate a complete batch, retrying only on deterministic validation failures."""

    schema = response_schema(work_order["question_json_schema"])
    attempts: list[GenerationAttempt] = []
    current_prompt = prompt
    payload: Any = None
    for number in range(1, max_repairs + 2):
        payload = provider_call(current_prompt, schema)
        try:
            batch = validate_generated_response(
                payload,
                work_order,
                repository_root=repository_root,
                authored_by=authored_by,
            )
        except AuthoringExecutionError as exc:
            errors = str(exc).splitlines()
            attempts.append(GenerationAttempt(number, False, errors))
            if number > max_repairs:
                raise AuthoringExecutionError(
                    f"Generation failed after {number} attempt(s): {exc}"
                ) from exc
            current_prompt = _repair_prompt(prompt, payload, errors)
            continue
        attempts.append(GenerationAttempt(number, True))
        return batch, attempts
    raise AssertionError("generation attempt loop exited unexpectedly")


def materialise_batch(
    work_order: dict[str, Any],
    batch: GeneratedBatch,
    *,
    repository_root: Path,
    provider: str,
    model: str,
    generator_version: str,
    review_output: Path,
) -> dict[str, Any]:
    """Write a validated batch transactionally and export its review packet."""

    manifest_path = repository_root / work_order["manifest_path"]
    manifest = load_manifest(manifest_path)
    if manifest.status != "planned":
        raise AuthoringExecutionError(
            f"Batch {manifest.batch_id} is {manifest.status}; only planned batches can execute"
        )
    if [question.stable_key for question in batch.questions] != manifest.question_keys:
        raise AuthoringExecutionError("Validated questions no longer match the manifest keys")
    question_root = manifest_path.parent.parent / "questions"
    target_paths = [question_root / f"{question.stable_key}.json" for question in batch.questions]
    collisions = [str(path) for path in target_paths if path.exists()]
    if collisions:
        raise AuthoringExecutionError(f"Question files already exist: {collisions}")
    if review_output.exists():
        raise AuthoringExecutionError(f"Review output already exists: {review_output}")

    updated = manifest.model_copy(
        update={
            "status": "ready_for_review",
            "generator": GeneratorMetadata(
                provider=provider,
                model=model,
                generator_version=generator_version,
                prompt_version=manifest.generator.prompt_version,
            ),
        }
    )
    original_manifest = manifest_path.read_text()
    written: list[Path] = []
    try:
        for path, question in zip(target_paths, batch.questions, strict=True):
            _write_json(path, question.model_dump(mode="json"))
            written.append(path)
        _write_json(manifest_path, updated.model_dump(mode="json"))
        report = validate_batch(
            manifest_path,
            repository_root=repository_root,
            syllabus_path=repository_root
            / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        )
        if not report.valid:
            raise AuthoringExecutionError(json.dumps(report.as_dict(), indent=2))
        export = export_reviewer_batch(
            manifest_path,
            review_output,
            repository_root=repository_root,
            syllabus_path=repository_root
            / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        )
    except Exception:
        manifest_path.write_text(original_manifest)
        for path in written:
            path.unlink(missing_ok=True)
        if review_output.exists():
            shutil.rmtree(review_output)
        raise
    return {
        "batch_id": manifest.batch_id,
        "question_count": len(batch.questions),
        "manifest": str(manifest_path),
        "review_output": str(review_output),
        "review_files": export["files"],
        "warnings": batch.warnings,
    }


def execute_authoring_work_order(
    work_order_path: Path,
    provider_call: GenerationCall,
    *,
    repository_root: Path,
    provider: str,
    model: str,
    authored_by: str,
    max_repairs: int = 2,
    review_output: Path | None = None,
    dry_run: bool = False,
    claim_registry_path: Path | None = None,
) -> dict[str, Any]:
    """Generate, validate and optionally materialise one complete authoring batch."""

    if max_repairs < 0 or max_repairs > 5:
        raise AuthoringExecutionError("max_repairs must be between 0 and 5")
    work_order = _read_json(work_order_path)
    if work_order.get("schema_version") != "1.0.0":
        raise AuthoringExecutionError("Unsupported work-order schema version")
    if not dry_run:
        if claim_registry_path is None:
            raise AuthoringExecutionError(
                "A claim registry is required before materialising generated content"
            )
        _verify_active_claim(
            work_order["batch_id"],
            repository_root=repository_root,
            claim_registry_path=claim_registry_path,
        )
    prompt_path = work_order_path.parent / "prompt.md"
    try:
        prompt = prompt_path.read_text()
    except OSError as exc:
        raise AuthoringExecutionError(f"Cannot read work-order prompt: {exc}") from exc
    batch, attempts = generate_batch(
        work_order,
        prompt,
        provider_call,
        repository_root=repository_root,
        authored_by=authored_by,
        max_repairs=max_repairs,
    )
    result: dict[str, Any] = {
        "status": "validated" if dry_run else "ready_for_review",
        "batch_id": work_order["batch_id"],
        "question_count": len(batch.questions),
        "provider": provider,
        "model": model,
        "attempts": [attempt.__dict__ for attempt in attempts],
        "warnings": batch.warnings,
        "dry_run": dry_run,
    }
    if dry_run:
        return result
    output = review_output or (
        repository_root / "build/reviewer-packets" / work_order["batch_id"]
    )
    materialised = materialise_batch(
        work_order,
        batch,
        repository_root=repository_root,
        provider=provider,
        model=model,
        generator_version=EXECUTOR_VERSION,
        review_output=output,
    )
    result.update(materialised)
    _write_json(work_order_path.parent / "execution-report.json", result)
    return result
