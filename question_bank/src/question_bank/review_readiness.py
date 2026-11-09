"""Objective pre-review readiness checks for Mathematics authoring batches."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from .authoring import BatchValidationReport, load_manifest, validate_authoring_pipeline
from .collaboration import BatchClaim, load_claim_registry
from .models import Question

PacketStatus = Literal["current", "missing", "incomplete", "invalid", "stale"]
BatchState = Literal["ready", "in_progress", "blocked", "complete"]

REQUIRED_PACKET_FILES = (
    "index.html",
    "manifest.json",
    "questions.json",
    "review.csv",
    "review.md",
    "validation.json",
)

OPEN_CONTENT_FINDING_STATUSES = {
    "open",
    "needs_checker_config",
    "needs_founder_decision",
}
LEARNER_VISIBLE_CODENAME = re.compile(
    r"\b[A-Z][a-z]+ [A-Z][a-z]+ Bay(?:\s+dataset for\b|\s+—)"
)


@dataclass(frozen=True)
class ReadinessFinding:
    code: str
    path: str
    message: str


@dataclass
class BatchReadiness:
    batch_id: str
    bank_key: str
    school_level: str
    topic_code: str
    manifest_status: str
    question_count: int
    packet_status: PacketStatus
    state: BatchState
    active_claim: dict | None = None
    pending_asset_keys: list[str] = field(default_factory=list)
    blockers: list[ReadinessFinding] = field(default_factory=list)
    warnings: list[ReadinessFinding] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.state == "ready"

    def as_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "bank_key": self.bank_key,
            "school_level": self.school_level,
            "topic_code": self.topic_code,
            "manifest_status": self.manifest_status,
            "question_count": self.question_count,
            "packet_status": self.packet_status,
            "state": self.state,
            "ready": self.ready,
            "active_claim": self.active_claim,
            "pending_asset_keys": self.pending_asset_keys,
            "blockers": [asdict(item) for item in self.blockers],
            "warnings": [asdict(item) for item in self.warnings],
        }


@dataclass
class ReviewReadinessReport:
    generated_at: str
    batches: list[BatchReadiness]
    catalogue_errors: list[ReadinessFinding] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.catalogue_errors

    @property
    def ready_batches(self) -> list[BatchReadiness]:
        return [batch for batch in self.batches if batch.state == "ready"]

    @property
    def blocked_batches(self) -> list[BatchReadiness]:
        return [batch for batch in self.batches if batch.state == "blocked"]

    @property
    def in_progress_batches(self) -> list[BatchReadiness]:
        return [batch for batch in self.batches if batch.state == "in_progress"]

    @property
    def complete_batches(self) -> list[BatchReadiness]:
        return [batch for batch in self.batches if batch.state == "complete"]

    @property
    def all_ready_or_complete(self) -> bool:
        return self.valid and all(
            batch.state in {"ready", "complete"} for batch in self.batches
        )

    def as_dict(self) -> dict:
        pending_assets = sum(len(batch.pending_asset_keys) for batch in self.batches)
        return {
            "valid": self.valid,
            "all_ready_or_complete": self.all_ready_or_complete,
            "generated_at": self.generated_at,
            "batch_count": len(self.batches),
            "ready_count": len(self.ready_batches),
            "in_progress_count": len(self.in_progress_batches),
            "blocked_count": len(self.blocked_batches),
            "complete_count": len(self.complete_batches),
            "pending_asset_count": pending_assets,
            "catalogue_errors": [asdict(item) for item in self.catalogue_errors],
            "batches": [batch.as_dict() for batch in self.batches],
        }


def _manifest_paths(bank_root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for path in sorted(bank_root.glob("**/batches/*.json")):
        manifest = load_manifest(path)
        if manifest.batch_id in paths:
            raise ValueError(f"Duplicate batch ID {manifest.batch_id}")
        paths[manifest.batch_id] = path
    return paths


def _planned_assets(worklist_path: Path | None) -> dict[str, list[str]]:
    if worklist_path is None or not worklist_path.is_file():
        return {}
    payload = json.loads(worklist_path.read_text(encoding="utf-8"))
    result: dict[str, list[str]] = {}
    for item in payload.get("batch_fix_order", []):
        keys = item.get("questions_needing_new_diagram") or []
        if keys:
            result[item["batch_id"]] = sorted(set(keys))
    return result


def _open_content_findings(worklist_path: Path | None) -> dict[str, list[dict]]:
    """Return explicitly unresolved category 1-3 findings by owned batch.

    Historical ``confirmed`` findings describe the audit baseline and are not a
    reliable unresolved-state marker because completed content PRs intentionally
    preserve that evidence. The statuses below are the ledger's explicit signal
    that work or a decision is still outstanding, unless the record's
    ``resolution`` lists the batch as fixed.
    """

    if worklist_path is None or not worklist_path.is_file():
        return {}
    payload = json.loads(worklist_path.read_text(encoding="utf-8"))
    result: dict[str, list[dict]] = {}
    for record in payload.get("records", []):
        if record.get("category_rank") not in {1, 2, 3}:
            continue
        if record.get("status") not in OPEN_CONTENT_FINDING_STATUSES:
            continue
        resolved_batches = set(record.get("resolution", {}).get("batches", []))
        for batch_id in record.get("batches", []):
            if batch_id not in resolved_batches:
                result.setdefault(batch_id, []).append(record)
    for records in result.values():
        records.sort(key=lambda item: item.get("id", ""))
    return result


def _question_has_learner_visible_codename(question: Question) -> bool:
    learner_text = [question.title]
    learner_text.extend(
        block.text for block in question.stem if getattr(block, "type", None) == "text"
    )
    for part in question.parts:
        learner_text.extend(
            block.text
            for block in part.prompt
            if getattr(block, "type", None) == "text"
        )
    return any(LEARNER_VISIBLE_CODENAME.search(text) for text in learner_text)


def _packet_status(
    report: BatchValidationReport,
    manifest_path: Path,
) -> tuple[PacketStatus, list[ReadinessFinding]]:
    manifest = report.manifest
    if manifest is None:
        return "invalid", [
            ReadinessFinding(
                "invalid_batch_manifest", str(manifest_path), "Batch manifest could not be loaded."
            )
        ]
    bank_root = manifest_path.parent.parent
    packet = bank_root / "review_packets" / manifest.batch_id
    if not packet.is_dir():
        return "missing", [
            ReadinessFinding(
                "missing_reviewer_packet",
                str(packet),
                "Generate the consolidated reviewer packet before assigning this batch.",
            )
        ]
    missing = [name for name in REQUIRED_PACKET_FILES if not (packet / name).is_file()]
    if missing:
        return "incomplete", [
            ReadinessFinding(
                "incomplete_reviewer_packet",
                str(packet),
                "Missing required files: " + ", ".join(missing),
            )
        ]
    try:
        packet_manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
        packet_questions = json.loads((packet / "questions.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return "invalid", [
            ReadinessFinding("invalid_reviewer_packet", str(packet), str(exc))
        ]

    findings: list[ReadinessFinding] = []
    if packet_manifest != manifest.model_dump(mode="json"):
        findings.append(
            ReadinessFinding(
                "stale_packet_manifest",
                str(packet / "manifest.json"),
                "Packet manifest no longer matches its source batch manifest.",
            )
        )
    expected_questions = [question.model_dump(mode="json") for question in report.questions]
    if packet_questions != expected_questions:
        findings.append(
            ReadinessFinding(
                "stale_packet_questions",
                str(packet / "questions.json"),
                "Packet questions no longer match the current source revisions.",
            )
        )
    for question in report.questions:
        for asset in question.assets:
            source = bank_root / asset.path
            exported = packet / "assets" / Path(asset.path).name
            if not exported.is_file():
                findings.append(
                    ReadinessFinding(
                        "missing_packet_asset",
                        str(exported),
                        f"Reviewer packet is missing asset {asset.asset_key}.",
                    )
                )
            elif source.is_file() and source.read_bytes() != exported.read_bytes():
                findings.append(
                    ReadinessFinding(
                        "stale_packet_asset",
                        str(exported),
                        f"Reviewer packet asset {asset.asset_key} differs from the source asset.",
                    )
                )
    return ("stale", findings) if findings else ("current", [])


def _claim_dict(claim: BatchClaim | None) -> dict | None:
    if claim is None:
        return None
    return {
        "owner": claim.owner,
        "branch": claim.branch,
        "claimed_at": claim.claimed_at.isoformat(),
    }


def audit_review_readiness(
    bank_root: Path,
    syllabus_path: Path,
    claims_path: Path,
    *,
    repository_root: Path,
    worklist_path: Path | None = None,
    include_diagnostics: bool = False,
    now: datetime | None = None,
) -> ReviewReadinessReport:
    """Classify batches without recording any review or approval decision."""

    pipeline = validate_authoring_pipeline(
        bank_root,
        syllabus_path,
        repository_root=repository_root,
    )
    manifests = _manifest_paths(bank_root)
    registry = load_claim_registry(claims_path)
    planned_assets = _planned_assets(worklist_path)
    open_content_findings = _open_content_findings(worklist_path)
    catalogue_errors = [
        ReadinessFinding(issue.code, issue.path, issue.message) for issue in pipeline.errors
    ]
    batches: list[BatchReadiness] = []

    for batch_report in pipeline.batch_reports:
        manifest = batch_report.manifest
        if manifest is None:
            continue
        if not include_diagnostics and manifest.bank_role == "diagnostic":
            continue
        manifest_path = manifests[manifest.batch_id]
        claim = registry.active_claim(manifest.batch_id)
        packet_status, packet_findings = _packet_status(batch_report, manifest_path)
        blockers = list(packet_findings)
        warnings = [
            ReadinessFinding(issue.code, issue.path, issue.message)
            for issue in batch_report.warnings
        ]
        blockers.extend(
            ReadinessFinding(issue.code, issue.path, issue.message)
            for issue in batch_report.errors
        )

        for record in open_content_findings.get(manifest.batch_id, []):
            blockers.append(
                ReadinessFinding(
                    "open_content_finding",
                    str(worklist_path) if worklist_path else manifest.batch_id,
                    f"{record['id']} (category {record['category_rank']}, "
                    f"{record['status']}): {record['title']}",
                )
            )

        codename_keys = sorted(
            question.stable_key
            for question in batch_report.questions
            if _question_has_learner_visible_codename(question)
        )
        if codename_keys:
            blockers.append(
                ReadinessFinding(
                    "learner_visible_codename",
                    str(manifest_path.parent.parent / "questions"),
                    "Remove generated learner-visible codename prefixes from: "
                    + ", ".join(codename_keys),
                )
            )

        questions = {question.stable_key: question for question in batch_report.questions}
        pending_asset_keys = [
            key
            for key in planned_assets.get(manifest.batch_id, [])
            if key in questions and not questions[key].assets
        ]
        missing_worklist_keys = [
            key for key in planned_assets.get(manifest.batch_id, []) if key not in questions
        ]
        if pending_asset_keys:
            blockers.append(
                ReadinessFinding(
                    "planned_assets_missing",
                    str(worklist_path) if worklist_path else manifest.batch_id,
                    "Planned figures are still missing for: " + ", ".join(pending_asset_keys),
                )
            )
        if missing_worklist_keys:
            warnings.append(
                ReadinessFinding(
                    "stale_asset_worklist",
                    str(worklist_path) if worklist_path else manifest.batch_id,
                    "Worklist keys are not owned by this batch: "
                    + ", ".join(missing_worklist_keys),
                )
            )
        if claim is not None:
            blockers.append(
                ReadinessFinding(
                    "active_batch_claim",
                    str(claims_path),
                    f"{claim.owner} is still editing this batch on {claim.branch}.",
                )
            )
        if manifest.status not in {"ready_for_review", "approved"}:
            blockers.append(
                ReadinessFinding(
                    "manifest_not_ready",
                    str(manifest_path),
                    f"Manifest status is {manifest.status}, not ready_for_review.",
                )
            )

        if manifest.status == "approved":
            state: BatchState = "complete"
        elif claim is not None:
            state = "in_progress"
        elif blockers:
            state = "blocked"
        else:
            state = "ready"
        batches.append(
            BatchReadiness(
                batch_id=manifest.batch_id,
                bank_key=manifest.bank_key,
                school_level=manifest.school_level,
                topic_code=manifest.topic_code,
                manifest_status=manifest.status,
                question_count=len(batch_report.questions),
                packet_status=packet_status,
                state=state,
                active_claim=_claim_dict(claim),
                pending_asset_keys=pending_asset_keys,
                blockers=blockers,
                warnings=warnings,
            )
        )

    batches.sort(key=lambda item: (item.school_level, item.topic_code, item.batch_id))
    generated = (now or datetime.now(UTC)).astimezone(UTC).isoformat()
    return ReviewReadinessReport(generated, batches, catalogue_errors)


def readiness_markdown(report: ReviewReadinessReport) -> str:
    """Render a concise human handoff without implying approval."""

    data = report.as_dict()
    lines = [
        "# Mathematics pre-review readiness",
        "",
        f"Generated: {report.generated_at}",
        "",
        "This is a technical pre-flight report only. It records no Mathematics or editorial approval.",
        "",
        "## Summary",
        "",
        f"- Ready for assignment: {data['ready_count']}",
        f"- In progress (active claim): {data['in_progress_count']}",
        f"- Blocked: {data['blocked_count']}",
        f"- Already complete: {data['complete_count']}",
        f"- Planned figures still missing: {data['pending_asset_count']}",
        "",
        "## Ready batches",
        "",
    ]
    if report.ready_batches:
        lines.extend(f"- `{batch.batch_id}` ({batch.question_count} questions)" for batch in report.ready_batches)
    else:
        lines.append("No batch currently passes every technical pre-flight gate.")
    lines.extend(["", "## Not yet assignable", ""])
    pending = [
        *report.in_progress_batches,
        *report.blocked_batches,
    ]
    if pending:
        lines.extend(
            [
                "| Batch | State | Packet | Missing figures | Blocking reasons |",
                "| --- | --- | --- | ---: | --- |",
            ]
        )
        for batch in pending:
            reasons = "; ".join(item.message for item in batch.blockers).replace("|", "\\|")
            lines.append(
                f"| `{batch.batch_id}` | {batch.state} | {batch.packet_status} | "
                f"{len(batch.pending_asset_keys)} | {reasons} |"
            )
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def write_readiness_report(report: ReviewReadinessReport, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output / "summary.md").write_text(readiness_markdown(report), encoding="utf-8")
