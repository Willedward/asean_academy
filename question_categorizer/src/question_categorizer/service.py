"""Load reviewed OCR output and classify questions against the fixed taxonomy."""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from .models import (
    CLASSIFIER_VERSION,
    CategorizationResult,
    Level,
    QuestionCategorization,
    QuestionPart,
    TopicAssignment,
)
from .rules import RuleClassifier
from .taxonomy import load_taxonomy

PART_MARKER = re.compile(r"(?<!\w)\((i{1,3}|iv|v|vi{0,3}|ix|x|[a-h])\)\s*", re.I)
INLINE_LATEX = re.compile(r"\\\((.*?)\\\)", re.S)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_fingerprint(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def parse_level(value) -> Level | None:
    if not value:
        return None
    normalized = re.sub(r"[^a-z0-9]", "", str(value).lower())
    if normalized in {"secondary1", "secondaryone", "sec1", "s1"}:
        return "secondary_1"
    if normalized in {"secondary2", "secondarytwo", "sec2", "s2"}:
        return "secondary_2"
    return None


def block_value(block: dict) -> str:
    kind = block.get("type")
    if kind == "text":
        return str(block.get("text", "")).strip()
    if kind == "math":
        latex = str(block.get("latex") or "").strip()
        return f"\\({latex}\\)" if latex else ""
    if kind == "table":
        return "\n".join(" | ".join(str(cell) for cell in row) for row in block.get("rows", []))
    if kind == "image":
        return "[diagram]"
    return ""


def split_parts(question: dict, content: list[dict], fingerprint: str, input_status: str):
    combined = "\n".join(filter(None, (block_value(block) for block in content))).strip()
    if not combined:
        combined = str(question.get("question_text", "")).strip()
    markers = list(PART_MARKER.finditer(combined))
    raw_parts = []
    if markers:
        preamble = combined[: markers[0].start()].strip()
        for index, marker in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(combined)
            body = combined[marker.end() : end].strip()
            value = "\n".join(piece for piece in (preamble, body) if piece)
            raw_parts.append((marker[1].lower(), value))
    elif question.get("subparts"):
        for subpart in question["subparts"]:
            value = str(subpart.get("text", "")).strip()
            latex = str(subpart.get("latex") or "").strip()
            if latex:
                value = f"{value}\n\\({latex}\\)".strip()
            raw_parts.append((str(subpart.get("label") or "").lower() or None, value))
    else:
        raw_parts.append((None, combined))

    question_id = UUID(str(question["id"]))
    parts = []
    for order, (label, value) in enumerate(raw_parts):
        latex = "\n".join(match[1].strip() for match in INLINE_LATEX.finditer(value))
        parts.append(
            QuestionPart(
                id=uuid5(
                    NAMESPACE_URL,
                    f"asean-academy:question-part:{question_id}:{order}:{label or 'whole'}",
                ),
                label=label,
                order=order,
                content=value,
                latex=latex,
                input_status=input_status,
                source_fingerprint=fingerprint,
                assignments=[],
                classification_status="unclassified",
                review_reasons=[],
            )
        )
    return parts


def latest_review(input_path: Path, document_id: str, run_key: str, question_id: str):
    # questions.json is OUTPUT/document/run/questions.json.
    if len(input_path.parents) < 3:
        return None
    directory = input_path.parents[2] / "reviews" / document_id / run_key / question_id
    records = []
    for path in directory.glob("*.json"):
        try:
            record = json.loads(path.read_text())
            if record.get("question_id") == question_id and record.get("run_key") == run_key:
                records.append(record)
        except (OSError, ValueError):
            continue
    return max(records, key=lambda record: record.get("created_at", ""), default=None)


class CategorizationService:
    def __init__(self, *, minimum_score: float = 3, minimum_margin: float = 0.75):
        self.taxonomy = load_taxonomy()
        self.minimum_score = minimum_score
        self.minimum_margin = minimum_margin
        self.classifier = RuleClassifier(
            self.taxonomy,
            minimum_score=minimum_score,
            minimum_margin=minimum_margin,
        )

    def categorize_file(
        self,
        path: Path | str,
        *,
        source_level: Level | None = None,
    ) -> CategorizationResult:
        path = Path(path).resolve()
        payload = json.loads(path.read_text())
        if not isinstance(payload.get("questions"), list) or not payload.get("document"):
            raise ValueError("Input must be an OCR extractor questions.json export")
        document = payload["document"]
        document_id = UUID(str(document["id"]))
        extraction_run_key = str(payload.get("run_key", ""))
        digest = file_sha256(path)
        level = source_level or parse_level(document.get("metadata", {}).get("source_level"))
        run_id = uuid5(
            NAMESPACE_URL,
            ":".join(
                (
                    "asean-academy:categorization",
                    digest,
                    self.taxonomy.version,
                    CLASSIFIER_VERSION,
                    str(self.minimum_score),
                    str(self.minimum_margin),
                    level or "unknown",
                )
            ),
        )
        questions = []
        unchecked = 0
        for question in payload["questions"]:
            question_id = str(question["id"])
            review = latest_review(path, str(document_id), extraction_run_key, question_id)
            if review and review.get("decision") == "rejected":
                questions.append(
                    QuestionCategorization(
                        question_id=question_id,
                        question_number=str(question.get("question_number", "")),
                        status="rejected",
                        primary_topic_code=None,
                        parts=[],
                        review_reasons=["question_rejected_during_transcription_review"],
                    )
                )
                continue
            checked = bool(review and review.get("decision") == "checked")
            content = review["content"] if checked else question.get("content", [])
            fingerprint = (
                str(review["source_fingerprint"]) if checked else canonical_fingerprint(question)
            )
            input_status = "checked" if checked else "machine_unchecked"
            unchecked += not checked
            parts = split_parts(question, content, fingerprint, input_status)
            for part in parts:
                candidates = self.classifier.classify(part.content, level)
                if not candidates:
                    part.review_reasons.append("classification_below_threshold")
                    if not checked:
                        part.review_reasons.append("unchecked_ocr_input")
                    continue
                for index, candidate in enumerate(candidates):
                    topic = next(t for t in self.taxonomy.topics if t.code == candidate.topic_code)
                    outcomes = [
                        outcome
                        for outcome in self.taxonomy.outcomes
                        if outcome.topic_id == topic.id and outcome.code == candidate.outcome_code
                    ]
                    outcome = next(
                        (entry for entry in outcomes if level and entry.level == level),
                        outcomes[0] if outcomes else None,
                    )
                    role = "primary" if index == 0 else "secondary"
                    part.assignments.append(
                        TopicAssignment(
                            id=uuid5(
                                run_id,
                                f"{part.id}:{role}:{topic.id}:{outcome.id if outcome else ''}",
                            ),
                            topic_id=topic.id,
                            topic_code=topic.code,
                            topic_name=topic.name,
                            outcome_id=outcome.id if outcome else None,
                            outcome_code=outcome.code if outcome else None,
                            outcome_level=outcome.level if outcome else None,
                            role=role,
                            confidence=candidate.confidence,
                            evidence=candidate.evidence,
                        )
                    )
                part.classification_status = "classified"
                if not checked:
                    part.review_reasons.append("unchecked_ocr_input")

            primary_codes = {
                assignment.topic_code
                for part in parts
                for assignment in part.assignments
                if assignment.role == "primary"
            }
            status = "classified" if any(p.assignments for p in parts) else "unclassified"
            reasons = []
            if len(primary_codes) > 1:
                reasons.append("mixed_question_topics")
            if not checked:
                reasons.append("unchecked_ocr_input")
            questions.append(
                QuestionCategorization(
                    question_id=question_id,
                    question_number=str(question.get("question_number", "")),
                    status=status,
                    primary_topic_code=(
                        next(iter(primary_codes))
                        if len(primary_codes) == 1
                        else "mixed"
                        if primary_codes
                        else None
                    ),
                    parts=parts,
                    review_reasons=reasons,
                )
            )
        warnings = ["taxonomy_is_draft"]
        if level is None:
            warnings.append("source_level_unknown")
        if unchecked:
            warnings.append(f"machine_unchecked_questions:{unchecked}")
        return CategorizationResult(
            taxonomy_version=self.taxonomy.version,
            classifier_version=CLASSIFIER_VERSION,
            minimum_score=self.minimum_score,
            minimum_margin=self.minimum_margin,
            run_id=run_id,
            created_at=datetime.now(UTC).isoformat(),
            input_path=str(path),
            input_sha256=digest,
            document_id=document_id,
            extraction_run_key=extraction_run_key,
            source_level=level,
            questions=questions,
            warnings=warnings,
        )
