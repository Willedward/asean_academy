"""Regenerate the checked geometry diagrams for one question batch or a set of lessons.

A batch run can also add a figure to a text-only question that needs one (``add``). When the
generator says an accurate figure would show a question's answer, that question becomes text-only
instead. Both decisions are recorded in the bank's ``diagram_audit.json``.

Without ``apply`` nothing in the repository changes: each SVG is rendered, validated and, when
an output directory is given, written there with a manifest for review. With ``apply`` the SVG
is written beside the existing asset under a revisioned filename (``…-r2.svg``), the previous
file is kept for immutable learner records, and the question or lesson JSON gets the new
revision, path, checksum, alternative text and ``generation_spec``. Review provenance is reset
because the content fingerprint changes.

Findings that belong in a question's text rather than its diagram (a wrong answer key, or a
stem that presupposes the answer) are reported, never applied.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..diagram_checks import DiagramContext
from ..geometry_validation import geometry_diagram_findings
from .canvas import DiagramLayoutError
from .common import CHECKED_RENDERERS, PLANE_GEOMETRY_RENDERER, Diagram, answer_values
from .questions import (
    LESSON_TEMPLATES,
    UnsupportedDiagram,
    diagram_assets,
    question_text,
    render_lesson_asset,
    render_question_asset,
    text_only_reason,
)

REVIEW_NOTE = (
    "Diagram regenerated from the content data with {renderer}; awaiting Mathematics and "
    "editorial review."
)
TEXT_ONLY_NOTE = "Diagram removed; text-only. Awaiting Mathematics and editorial review."
SCHEMATIC_STEM = (
    "Use the schematic together with the measurements stated in the question. "
    "The diagram is not drawn to scale."
)


@dataclass
class RegeneratedAsset:
    owner_key: str
    asset_key: str
    renderer: str
    template: str
    current_revision: int
    target_revision: int
    current_path: str
    target_path: str
    sha256: str
    width: int
    height: int
    alt_text: str
    unchanged: bool
    content_findings: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class RegenerationReport:
    source: str
    scope: str
    applied: bool
    output: str | None
    assets: list[RegeneratedAsset] = field(default_factory=list)
    unsupported: list[dict[str, str]] = field(default_factory=list)
    text_only: list[dict[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unsupported and not any(asset.validation_errors for asset in self.assets)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source": self.source,
            "scope": self.scope,
            "applied": self.applied,
            "output": self.output,
            "asset_count": len(self.assets),
            "changed_count": sum(not asset.unchanged for asset in self.assets),
            "content_finding_count": sum(len(asset.content_findings) for asset in self.assets),
            "assets": [asdict(asset) for asset in self.assets],
            "unsupported": self.unsupported,
            "text_only": self.text_only,
        }


def revisioned_path(current: str, revision: int) -> str:
    path = Path(current)
    stem = re.sub(r"-r\d+$", "", path.stem)
    return (path.parent / f"{stem}-r{revision}{path.suffix}").as_posix()


def find_batch_manifest(bank_root: Path, batch: str) -> Path:
    """Accept ``B001``, ``b001`` or a full batch id such as ``g3-sec2-g4-b001``."""
    batches = sorted((bank_root / "batches").glob("*.json"))
    wanted = batch.lower().removesuffix(".json")
    for path in batches:
        name = path.stem.lower()
        if name == wanted or name.endswith(f"-{wanted}"):
            return path
    names = ", ".join(path.stem for path in batches) or "none"
    raise FileNotFoundError(f"No batch {batch!r} in {bank_root / 'batches'} (found: {names}).")


def _validate(diagram: Diagram, context: DiagramContext | None) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.svg"
        path.write_text(diagram.svg, encoding="utf-8")
        return [
            f"{finding.code}: {finding.message}"
            for finding in geometry_diagram_findings(
                path, diagram.generation_spec, diagram.alt_text, context, strict=True
            )
            if finding.severity == "error"
        ]


def _check_output(output: Path | None, source_root: Path) -> None:
    if output is None:
        return
    output = output.resolve()
    if output == source_root or source_root in output.parents:
        raise ValueError("Write previews outside the bank or course directory.")


def _unchanged(root: Path, asset: dict[str, Any], diagram: Diagram) -> bool:
    if asset.get("generation_spec", {}).get("renderer") not in CHECKED_RENDERERS:
        return False
    path = root / asset["path"]
    return (
        path.is_file()
        and path.read_text(encoding="utf-8") == diagram.svg
        and asset.get("alt_text") == diagram.alt_text
        and asset.get("generation_spec") == diagram.generation_spec
    )


def _write_preview(output: Path, report: RegenerationReport, files: dict[str, str]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, svg in files.items():
        (output / name).write_text(svg, encoding="utf-8")
    (output / "manifest.json").write_text(
        json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [f"# Diagram regeneration: {report.scope}", ""]
    findings = [
        (asset.owner_key, item) for asset in report.assets for item in asset.content_findings
    ]
    if findings:
        lines += ["## Findings for the question or lesson text (not applied)", ""]
        lines += [f"- `{key}`: {item}" for key, item in findings]
        lines.append("")
    if report.text_only:
        lines += ["## Text-only: an accurate figure would show the answer", ""]
        lines += [f"- `{item['key']}`: {item['reason']}" for item in report.text_only]
        lines.append("")
    if report.unsupported:
        lines += ["## Unsupported", ""]
        lines += [
            f"- `{item['key']}` {item['asset_key']}: {item['reason']}"
            for item in report.unsupported
        ]
        lines.append("")
    (output / "findings.md").write_text("\n".join(lines), encoding="utf-8")


def _apply_asset(root: Path, asset: dict[str, Any], diagram: Diagram, target_path: str) -> None:
    target = root / target_path
    if target.exists() and target.read_text(encoding="utf-8") != diagram.svg:
        raise FileExistsError(f"{target} already exists with different content.")
    target.write_text(diagram.svg, encoding="utf-8")
    asset["path"] = target_path
    asset["alt_text"] = diagram.alt_text
    asset["generation_spec"] = diagram.generation_spec
    asset["sha256"] = hashlib.sha256(diagram.svg.encode("utf-8")).hexdigest()
    asset["width"] = diagram.width
    asset["height"] = diagram.height


def _reset_review(document: dict[str, Any], renderer: str) -> None:
    document["revision"] = int(document.get("revision", 1)) + 1
    if document.get("status") != "draft":
        document["status"] = "draft"
    provenance = document.setdefault("provenance", {})
    provenance["reviewed_at"] = None
    provenance["reviewed_by"] = None
    provenance["review_notes"] = REVIEW_NOTE.format(renderer=renderer)


def _regenerate_document(
    *,
    root: Path,
    path: Path,
    document: dict[str, Any],
    assets: list[dict[str, Any]],
    render,
    context: DiagramContext | None,
    report: RegenerationReport,
    files: dict[str, str],
    apply: bool,
) -> None:
    key = document["stable_key"]
    planned: list[tuple[dict[str, Any], Diagram, RegeneratedAsset]] = []
    for asset in assets:
        try:
            diagram = render(document, asset)
        except (UnsupportedDiagram, DiagramLayoutError) as exc:
            report.unsupported.append(
                {"key": key, "asset_key": asset.get("asset_key", ""), "reason": str(exc)}
            )
            continue
        unchanged = _unchanged(root, asset, diagram)
        revision = int(document.get("revision", 1))
        target_revision = revision if unchanged else revision + 1
        target_path = (
            asset["path"] if unchanged else revisioned_path(asset["path"], target_revision)
        )
        record = RegeneratedAsset(
            owner_key=key,
            asset_key=asset["asset_key"],
            renderer=diagram.generation_spec["renderer"],
            template=diagram.generation_spec.get("template", ""),
            current_revision=revision,
            target_revision=target_revision,
            current_path=asset["path"],
            target_path=target_path,
            sha256=hashlib.sha256(diagram.svg.encode("utf-8")).hexdigest(),
            width=diagram.width,
            height=diagram.height,
            alt_text=diagram.alt_text,
            unchanged=unchanged,
            content_findings=diagram.content_findings,
            validation_errors=_validate(diagram, context),
        )
        report.assets.append(record)
        files[Path(target_path).name] = diagram.svg
        planned.append((asset, diagram, record))
    changed = [item for item in planned if not item[2].unchanged]
    if not apply or not changed:
        return
    if any(record.validation_errors for _, _, record in planned):
        return
    if any(item["key"] == key for item in report.unsupported):
        return
    for asset, diagram, record in changed:
        _apply_asset(root, asset, diagram, record.target_path)
    _reset_review(document, changed[0][1].generation_spec["renderer"])
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _record_audit_decision(
    bank_root: Path, key: str, reason: str, asset_key: str | None = None
) -> None:
    """Record one question's diagram decision in the bank's audit, when the bank has one.

    ``diagram_question_count`` is left alone: every batch would otherwise change the same line.
    """
    path = bank_root / "diagram_audit.json"
    if not path.is_file():
        return
    audit = json.loads(path.read_text(encoding="utf-8"))
    for decision in audit.get("decisions", []):
        if decision.get("question_key") == key:
            decision.clear()
            decision["question_key"] = key
            decision["decision"] = "diagram_added" if asset_key else "text_sufficient"
            if asset_key:
                decision["asset_key"] = asset_key
            decision["reason"] = reason
    path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _new_asset(question: dict[str, Any]) -> dict[str, Any]:
    """Attach an empty asset to a text-only question so a template can draw it."""
    key = question["stable_key"]
    asset = {
        "asset_key": f"{key}-diagram",
        "kind": "geometry",
        "format": "svg",
        "path": f"assets/{key}-diagram.svg",
        "alt_text": "",
        "generation_spec": {"renderer": PLANE_GEOMETRY_RENDERER},
    }
    question.setdefault("assets", []).append(asset)
    question["stem"] = [
        {"type": "text", "text": SCHEMATIC_STEM},
        {"type": "asset_ref", "asset_key": asset["asset_key"]},
        *question.get("stem", []),
    ]
    return asset


def _make_text_only(question: dict[str, Any], assets: list[dict[str, Any]]) -> None:
    keys = {asset["asset_key"] for asset in assets}
    question["assets"] = [
        asset for asset in question.get("assets", []) if asset["asset_key"] not in keys
    ]
    question["stem"] = [
        block
        for block in question.get("stem", [])
        if not (block.get("type") == "asset_ref" and block.get("asset_key") in keys)
        and not (block.get("type") == "text" and block.get("text") == SCHEMATIC_STEM)
    ]
    _reset_review(question, "")
    question["provenance"]["review_notes"] = TEXT_ONLY_NOTE


def regenerate_batch(
    bank_root: Path,
    batch: str,
    *,
    output: Path | None = None,
    apply: bool = False,
    add: list[str] | None = None,
) -> RegenerationReport:
    """Regenerate every checked-renderer diagram in one question batch.

    ``add`` names text-only questions in the batch that need a new figure.
    """
    bank_root = bank_root.resolve()
    _check_output(output, bank_root)
    manifest_path = find_batch_manifest(bank_root, batch)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = RegenerationReport(
        source=str(bank_root),
        scope=manifest.get("batch_id", manifest_path.stem),
        applied=apply,
        output=str(output) if output else None,
    )
    files: dict[str, str] = {}
    additions = set(add or [])
    outside = additions - set(manifest.get("question_keys", []))
    if outside:
        raise ValueError(f"Not in batch {report.scope}: {', '.join(sorted(outside))}.")
    for key in manifest.get("question_keys", []):
        path = bank_root / "questions" / f"{key}.json"
        question = json.loads(path.read_text(encoding="utf-8"))
        assets = diagram_assets(question)
        added = key in additions and not assets
        reason = text_only_reason(question) if assets or added else None
        if reason is not None:
            report.text_only.append({"key": key, "reason": reason})
            if apply:
                if assets:
                    _make_text_only(question, assets)
                    path.write_text(
                        json.dumps(question, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                    )
                _record_audit_decision(bank_root, key, reason)
            continue
        if added:
            assets = [_new_asset(question)]
        if not assets:
            continue
        context = DiagramContext(tuple(answer_values(question)), question_text(question))
        _regenerate_document(
            root=bank_root,
            path=path,
            document=question,
            assets=assets,
            render=render_question_asset,
            context=context,
            report=report,
            files=files,
            apply=apply,
        )
        if apply and any(item.owner_key == key for item in report.assets):
            planned = next(item for item in report.assets if item.owner_key == key)
            if not planned.validation_errors and not planned.unchanged:
                _record_audit_decision(
                    bank_root,
                    key,
                    f"Drawn from the question with {planned.renderer} ({planned.template}).",
                    planned.asset_key,
                )
    if output is not None:
        _write_preview(output, report, files)
    return report


def regenerate_lessons(
    course_root: Path,
    lesson_keys: list[str],
    *,
    output: Path | None = None,
    apply: bool = False,
) -> RegenerationReport:
    """Regenerate the registered teaching diagrams of the named lessons."""
    course_root = course_root.resolve()
    _check_output(output, course_root)
    report = RegenerationReport(
        source=str(course_root),
        scope=", ".join(lesson_keys),
        applied=apply,
        output=str(output) if output else None,
    )
    files: dict[str, str] = {}
    for key in lesson_keys:
        path = course_root / "lessons" / f"{key}.json"
        lesson = json.loads(path.read_text(encoding="utf-8"))
        assets = [
            asset
            for asset in lesson.get("assets", [])
            if asset.get("asset_key") in LESSON_TEMPLATES
            or asset.get("generation_spec", {}).get("renderer") in CHECKED_RENDERERS
        ]
        if not assets:
            report.unsupported.append(
                {"key": key, "asset_key": "", "reason": "No registered lesson diagram template."}
            )
            continue
        _regenerate_document(
            root=course_root,
            path=path,
            document=lesson,
            assets=assets,
            render=render_lesson_asset,
            context=None,
            report=report,
            files=files,
            apply=apply,
        )
    if output is not None:
        _write_preview(output, report, files)
    return report
