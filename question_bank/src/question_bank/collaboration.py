"""Git-coordinated batch claims and pull-request authoring evidence."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from pydantic import Field, ValidationError, model_validator

from .authoring import (
    BATCH_ID_PATTERN,
    PipelineValidationReport,
    export_reviewer_batch,
    load_manifest,
    validate_authoring_pipeline,
)
from .models import Model, Question
from .validation import Issue

CLAIM_SCHEMA_VERSION = "1.0.0"
AUTHORING_ROOT = PurePosixPath("backend_resources/question_bank")


class BatchClaim(Model):
    batch_id: str = Field(pattern=BATCH_ID_PATTERN)
    owner: str = Field(min_length=2, max_length=100)
    branch: str = Field(min_length=3, max_length=240, pattern=r"^[A-Za-z0-9._/-]+$")
    claimed_at: datetime
    released_at: datetime | None = None

    @model_validator(mode="after")
    def release_follows_claim(self):
        if self.released_at is not None and self.released_at < self.claimed_at:
            raise ValueError("released_at cannot precede claimed_at")
        return self

    @property
    def active(self) -> bool:
        return self.released_at is None


class BatchClaimRegistry(Model):
    schema_version: str = Field(pattern=r"^1\.0\.0$")
    claims: list[BatchClaim]

    @model_validator(mode="after")
    def active_claims_are_exclusive(self):
        active = [claim for claim in self.claims if claim.active]
        batch_counts = Counter(claim.batch_id for claim in active)
        duplicate_batches = sorted(batch for batch, count in batch_counts.items() if count > 1)
        if duplicate_batches:
            raise ValueError(
                "Each batch can have only one active claim: " + ", ".join(duplicate_batches)
            )
        branch_counts = Counter(claim.branch for claim in active)
        duplicate_branches = sorted(branch for branch, count in branch_counts.items() if count > 1)
        if duplicate_branches:
            raise ValueError(
                "Each branch can claim only one active batch: " + ", ".join(duplicate_branches)
            )
        return self

    def active_claim(self, batch_id: str) -> BatchClaim | None:
        return next(
            (
                claim
                for claim in reversed(self.claims)
                if claim.batch_id == batch_id and claim.active
            ),
            None,
        )


@dataclass
class CollaborationReport:
    changed_files: list[str] = field(default_factory=list)
    changed_batches: list[str] = field(default_factory=list)
    exported_batches: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    pipeline: PipelineValidationReport | None = None

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "changed_files": self.changed_files,
            "changed_batches": self.changed_batches,
            "exported_batches": self.exported_batches,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
            "pipeline": self.pipeline.as_dict() if self.pipeline else None,
        }


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def load_claim_registry(path: Path) -> BatchClaimRegistry:
    return BatchClaimRegistry.model_validate_json(path.read_text())


def _manifest_paths(bank_root: Path) -> dict[str, Path]:
    manifests: dict[str, Path] = {}
    for path in sorted(bank_root.glob("**/batches/*.json")):
        manifest = load_manifest(path)
        if manifest.batch_id in manifests:
            raise ValueError(f"Duplicate batch ID {manifest.batch_id}")
        manifests[manifest.batch_id] = path
    return manifests


def claim_batch(
    registry_path: Path,
    bank_root: Path,
    *,
    batch_id: str,
    owner: str,
    branch: str,
    now: datetime | None = None,
) -> dict:
    registry = load_claim_registry(registry_path)
    manifests = _manifest_paths(bank_root)
    path = manifests.get(batch_id)
    if path is None:
        raise ValueError(f"Unknown batch {batch_id}")
    manifest = load_manifest(path)
    if manifest.status not in {"planned", "draft", "ready_for_review", "changes_requested"}:
        raise ValueError(f"Batch {batch_id} cannot be claimed while {manifest.status}")
    existing = registry.active_claim(batch_id)
    if existing:
        if existing.owner == owner and existing.branch == branch:
            return {"changed": False, "claim": existing.model_dump(mode="json")}
        raise ValueError(
            f"Batch {batch_id} is already claimed by {existing.owner} on {existing.branch}"
        )
    if any(claim.active and claim.branch == branch for claim in registry.claims):
        raise ValueError(f"Branch {branch} already has an active batch claim")
    claim = BatchClaim(
        batch_id=batch_id,
        owner=owner,
        branch=branch,
        claimed_at=now or datetime.now(UTC),
    )
    updated = registry.model_copy(update={"claims": [*registry.claims, claim]})
    BatchClaimRegistry.model_validate(updated.model_dump(mode="json"))
    _write_json(registry_path, updated.model_dump(mode="json"))
    return {"changed": True, "claim": claim.model_dump(mode="json")}


def release_batch_claim(
    registry_path: Path,
    *,
    batch_id: str,
    owner: str,
    now: datetime | None = None,
) -> dict:
    registry = load_claim_registry(registry_path)
    active = registry.active_claim(batch_id)
    if active is None:
        raise ValueError(f"Batch {batch_id} has no active claim")
    if active.owner != owner:
        raise ValueError(f"Batch {batch_id} is claimed by {active.owner}, not {owner}")
    released = active.model_copy(update={"released_at": now or datetime.now(UTC)})
    claims = [released if claim is active else claim for claim in registry.claims]
    updated = registry.model_copy(update={"claims": claims})
    BatchClaimRegistry.model_validate(updated.model_dump(mode="json"))
    _write_json(registry_path, updated.model_dump(mode="json"))
    return {"changed": True, "claim": released.model_dump(mode="json")}


def validate_claim_registry(
    registry_path: Path, bank_root: Path
) -> tuple[BatchClaimRegistry | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        registry = load_claim_registry(registry_path)
        manifests = _manifest_paths(bank_root)
    except (OSError, ValueError, ValidationError) as exc:
        issues.append(Issue("error", "invalid_claim_registry", str(registry_path), str(exc)))
        return None, issues
    for claim in registry.claims:
        manifest_path = manifests.get(claim.batch_id)
        if manifest_path is None:
            issues.append(
                Issue(
                    "error",
                    "claim_unknown_batch",
                    str(registry_path),
                    f"{claim.batch_id} does not exist",
                )
            )
            continue
        manifest = load_manifest(manifest_path)
        if claim.active and manifest.status not in {
            "planned",
            "draft",
            "ready_for_review",
            "changes_requested",
            "approved",
        }:
            issues.append(
                Issue(
                    "error",
                    "claim_status_mismatch",
                    str(manifest_path),
                    f"Active claim remains while batch status is {manifest.status}",
                )
            )
    return registry, issues


def _question_ownership(
    bank_root: Path, repository_root: Path
) -> tuple[dict[str, str], dict[str, set[str]]]:
    question_batches: dict[str, str] = {}
    asset_batches: dict[str, set[str]] = {}
    for manifest_path in sorted(bank_root.glob("**/batches/*.json")):
        manifest = load_manifest(manifest_path)
        for key in manifest.question_keys:
            if key in question_batches:
                raise ValueError(f"Question key {key} belongs to multiple batches")
            question_batches[key] = manifest.batch_id
        question_root = manifest_path.parent.parent / "questions"
        for key in manifest.question_keys:
            path = question_root / f"{key}.json"
            if not path.is_file():
                continue
            question = Question.model_validate_json(path.read_text())
            for asset in question.assets:
                relative = (
                    (manifest_path.parent.parent / asset.path)
                    .resolve()
                    .relative_to(repository_root.resolve())
                )
                asset_batches.setdefault(relative.as_posix(), set()).add(manifest.batch_id)
    return question_batches, asset_batches


def changed_batch_ids(
    changed_files: list[str],
    *,
    repository_root: Path,
    bank_root: Path,
) -> tuple[set[str], list[Issue], set[str]]:
    manifests = _manifest_paths(bank_root)
    question_batches, asset_batches = _question_ownership(bank_root, repository_root)
    batches: set[str] = set()
    changed_question_batches: set[str] = set()
    issues: list[Issue] = []
    manifest_relatives = {
        path.resolve().relative_to(repository_root.resolve()).as_posix(): batch_id
        for batch_id, path in manifests.items()
    }
    for raw_path in changed_files:
        path = PurePosixPath(raw_path.strip())
        if not raw_path.strip() or AUTHORING_ROOT not in (path, *path.parents):
            continue
        relative = path.as_posix()
        if relative in manifest_relatives:
            batches.add(manifest_relatives[relative])
            continue
        parts = path.parts
        if "questions" in parts and path.suffix == ".json":
            key = path.stem
            batch_id = question_batches.get(key)
            if batch_id is None:
                issues.append(
                    Issue(
                        "error",
                        "changed_question_without_batch",
                        relative,
                        f"Question key {key} is not reserved by a batch manifest",
                    )
                )
            else:
                batches.add(batch_id)
                changed_question_batches.add(batch_id)
            continue
        if "review_packets" in parts:
            index = parts.index("review_packets")
            if index + 1 < len(parts):
                batch_id = parts[index + 1]
                if batch_id in manifests:
                    batches.add(batch_id)
                else:
                    issues.append(
                        Issue(
                            "error",
                            "changed_review_packet_without_batch",
                            relative,
                            f"Review packet batch {batch_id} does not exist",
                        )
                    )
            continue
        if "assets" in parts:
            owners = asset_batches.get(relative, set())
            if not owners:
                issues.append(
                    Issue(
                        "error",
                        "changed_asset_without_batch",
                        relative,
                        "Changed asset is not referenced by an authored batch question",
                    )
                )
            else:
                batches.update(owners)
    return batches, issues, changed_question_batches


def _summary(
    report: CollaborationReport,
    registry: BatchClaimRegistry | None,
    manifest_paths: dict[str, Path],
) -> str:
    pipeline = report.pipeline
    result = "PASS" if report.valid else "FAIL"
    lines = [
        "# Question authoring pull-request check",
        "",
        f"**Result: {result}**",
        "",
        f"- Changed files inspected: {len(report.changed_files)}",
        f"- Changed batches: {', '.join(report.changed_batches) or 'none'}",
        f"- Reviewer packets exported: {', '.join(report.exported_batches) or 'none'}",
    ]
    if pipeline:
        lines.extend(
            [
                f"- Catalogue: {pipeline.blueprint_count} blueprints, "
                f"{len(pipeline.batch_reports)} manifests, {pipeline.question_count} authored questions",
                f"- Duplicate findings: {len(pipeline.duplicate_matches)}",
                f"- Aggregate validation: {len(pipeline.errors)} errors, "
                f"{len(pipeline.warnings)} warnings",
            ]
        )
    if report.changed_batches:
        lines.extend(
            [
                "",
                "## Changed batch evidence",
                "",
                "| Batch | Status | Claim owner | Claim branch | Questions | Difficulty L1–L5 | Generator |",
                "| --- | --- | --- | --- | ---: | --- | --- |",
            ]
        )
        for batch_id in report.changed_batches:
            manifest = load_manifest(manifest_paths[batch_id])
            batch_report = next(
                (
                    item
                    for item in pipeline.batch_reports
                    if item.manifest and item.manifest.batch_id == batch_id
                ),
                None,
            )
            questions = batch_report.questions if batch_report else []
            distribution = Counter(question.difficulty for question in questions)
            difficulty = "/".join(str(distribution[level]) for level in range(1, 6))
            claim = registry.active_claim(batch_id) if registry else None
            generator = (
                f"{manifest.generator.provider}/{manifest.generator.model} "
                f"({manifest.generator.generator_version}; {manifest.generator.prompt_version})"
            )
            lines.append(
                f"| `{batch_id}` | {manifest.status} | "
                f"{claim.owner if claim else 'missing'} | "
                f"`{claim.branch if claim else 'missing'}` | "
                f"{len(questions)}/{manifest.expected_question_count} | {difficulty} | {generator} |"
            )
    lines.extend(["", "## Validation findings", ""])
    if not report.issues:
        lines.append("No errors or warnings.")
    else:
        lines.extend(
            [
                "| Severity | Code | Path | Message |",
                "| --- | --- | --- | --- |",
            ]
        )
        for issue in report.issues:
            message = issue.message.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {issue.severity} | `{issue.code}` | `{issue.path}` | {message} |")
    lines.append("")
    return "\n".join(lines)


def check_pull_request(
    *,
    changed_files: list[str],
    head_branch: str,
    repository_root: Path,
    bank_root: Path,
    syllabus_path: Path,
    registry_path: Path,
    output: Path,
) -> CollaborationReport:
    report = CollaborationReport(changed_files=sorted(set(changed_files)))
    pipeline = validate_authoring_pipeline(
        bank_root,
        syllabus_path,
        repository_root=repository_root,
    )
    report.pipeline = pipeline
    report.issues.extend(pipeline.issues)
    registry, claim_issues = validate_claim_registry(registry_path, bank_root)
    report.issues.extend(claim_issues)
    try:
        batches, ownership_issues, question_batches = changed_batch_ids(
            report.changed_files,
            repository_root=repository_root,
            bank_root=bank_root,
        )
    except (OSError, ValueError, ValidationError) as exc:
        batches, question_batches = set(), set()
        ownership_issues = [Issue("error", "authoring_ownership_error", str(bank_root), str(exc))]
    report.issues.extend(ownership_issues)
    report.changed_batches = sorted(batches)
    if len(batches) > 1:
        report.issues.append(
            Issue(
                "error",
                "multiple_batches_changed",
                "pull_request",
                "An authoring pull request must change exactly one batch",
            )
        )
    try:
        manifest_paths = _manifest_paths(bank_root)
    except (OSError, ValueError, ValidationError) as exc:
        manifest_paths = {}
        report.issues.append(Issue("error", "invalid_manifest_index", str(bank_root), str(exc)))
    for batch_id in sorted(batches):
        manifest = load_manifest(manifest_paths[batch_id])
        claim = registry.active_claim(batch_id) if registry else None
        if claim is None:
            report.issues.append(
                Issue(
                    "error",
                    "missing_active_claim",
                    str(manifest_paths[batch_id]),
                    f"Claim {batch_id} before changing its authored files",
                )
            )
        elif claim.branch != head_branch:
            report.issues.append(
                Issue(
                    "error",
                    "claim_branch_mismatch",
                    str(registry_path),
                    f"Claim belongs to {claim.branch}, but this branch is {head_branch}",
                )
            )
        if batch_id in question_batches and manifest.status == "planned":
            report.issues.append(
                Issue(
                    "error",
                    "planned_batch_has_changed_questions",
                    str(manifest_paths[batch_id]),
                    "Set concrete generator metadata and change status to draft",
                )
            )
    output.mkdir(parents=True, exist_ok=True)
    if not report.errors:
        for batch_id in sorted(batches):
            manifest_path = manifest_paths[batch_id]
            manifest = load_manifest(manifest_path)
            if manifest.status == "planned":
                continue
            export_reviewer_batch(
                manifest_path,
                output / "batches" / batch_id,
                repository_root=repository_root,
                syllabus_path=syllabus_path,
            )
            report.exported_batches.append(batch_id)
    _write_json(output / "report.json", report.as_dict())
    (output / "summary.md").write_text(_summary(report, registry, manifest_paths))
    return report
