"""Application service for English essay drafts and immutable submissions."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

from .english_contracts import (
    EnglishEssayDraftResponse,
    EnglishEssayPreSubmitResponse,
    EnglishEssayPromptResponse,
    EnglishEssaySubmissionResponse,
)
from .english_essay_repository import EnglishEssayError

WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*")


def essay_word_count(body: str) -> int:
    return len(WORD_PATTERN.findall(body))


class EnglishEssayService:
    def __init__(
        self,
        repository_root: Path,
        repository,
        learner_id: str,
        *,
        allow_drafts: bool,
    ):
        self.repository = repository
        self.learner_id = learner_id
        self.allow_drafts = allow_drafts
        source = (
            repository_root
            / "backend_resources/english/v1/prompts/english-essay-prompt-school-learning-transfer-v1-v1.json"
        )
        self.prompt = json.loads(source.read_text())
        rubric_source = (
            repository_root
            / "backend_resources/english/v1/rubrics/english-essay-rubric-instructional-v1-v1.json"
        )
        self.rubric = json.loads(rubric_source.read_text())

    def current_prompt(self) -> EnglishEssayPromptResponse:
        if self.prompt["status"] != "published" and not self.allow_drafts:
            raise EnglishEssayError(
                "essay_prompt_not_found", "No essay prompt is currently available.", 404
            )
        return EnglishEssayPromptResponse(
            stable_key=self.prompt["stable_key"],
            revision=self.prompt["revision"],
            title=self.prompt["title"],
            prompt_family=self.prompt["prompt_family"],
            prompt_text=self.prompt["prompt_text"],
            instructions=self.prompt["instructions"],
            time_limit_minutes=self.prompt["time_limit_minutes"],
            time_limit_evidence=self.prompt["time_limit_evidence"],
            word_count_guidance=self.prompt["word_count_guidance"],
            word_count_status=self.prompt["word_count_status"],
            content_status=self.prompt["status"],
            development_preview=self.prompt["status"] != "published",
        )

    def create_or_resume(
        self,
        *,
        prompt_key: str,
        prompt_revision: int,
        idempotency_key: str,
    ) -> EnglishEssayDraftResponse:
        current = self.current_prompt()
        if (prompt_key, prompt_revision) != (current.stable_key, current.revision):
            raise EnglishEssayError(
                "essay_prompt_changed",
                "The essay prompt changed before the draft opened. Refresh and try again.",
                409,
            )
        row = self.repository.create_or_resume(
            self.learner_id,
            prompt=self.prompt,
            idempotency_key=idempotency_key,
        )
        return self._response(row)

    def get(self, draft_id: str) -> EnglishEssayDraftResponse:
        row = self.repository.get(self.learner_id, draft_id)
        return self._response(row)

    def update(
        self, draft_id: str, *, body: str, expected_edit_revision: int
    ) -> EnglishEssayDraftResponse:
        row = self.repository.update(
            self.learner_id,
            draft_id,
            body=body,
            word_count=essay_word_count(body),
            expected_edit_revision=expected_edit_revision,
        )
        return self._response(row)

    @staticmethod
    def _row_value(row: dict, key: str):
        if "prompt" in row:
            return row["prompt"].get(key)
        return row.get(key)

    def _evaluate(self, row: dict) -> dict:
        prompt_status = self._row_value(row, "status") or row.get("prompt_status")
        if prompt_status != "published" and not self.allow_drafts:
            raise EnglishEssayError(
                "essay_draft_not_found", "Essay draft not found.", 404
            )
        body = row["body"]
        word_count = essay_word_count(body)
        paragraphs = [part.strip() for part in re.split(r"\n+", body) if part.strip()]
        paragraph_count = len(paragraphs)
        malformed_controls = any(
            unicodedata.category(character) == "Cc" and character not in "\n\r\t"
            for character in body
        )
        checks = [
            {
                "check_key": "revision_snapshot",
                "status": "pass",
                "message": (
                    f"Saved draft revision {row['edit_revision']} will be snapshotted "
                    "without changing the working draft."
                ),
            },
            {
                "check_key": "content_present",
                "status": "pass" if word_count > 0 else "block",
                "message": (
                    "The saved draft contains visible words."
                    if word_count > 0
                    else "Write and remotely save some essay text before submitting."
                ),
            },
            {
                "check_key": "content_encoding",
                "status": "block" if malformed_controls else "pass",
                "message": (
                    "Remove unsupported control characters before submitting."
                    if malformed_controls
                    else "The saved text contains no unsupported control characters."
                ),
            },
            {
                "check_key": "word_count_integrity",
                "status": "pass" if row["word_count"] == word_count else "block",
                "message": (
                    f"Server word count confirmed: {word_count}."
                    if row["word_count"] == word_count
                    else "The saved word count is inconsistent; save the draft again."
                ),
            },
            {
                "check_key": "response_length",
                "status": "warning" if 0 < word_count < 50 else "info",
                "message": (
                    "This is a very short practice response; you may still submit it."
                    if 0 < word_count < 50
                    else f"The immutable snapshot will record {word_count} words."
                ),
            },
            {
                "check_key": "paragraph_structure",
                "status": "warning" if paragraph_count == 1 else "info",
                "message": (
                    "Only one text paragraph was detected; review the organisation before submitting."
                    if paragraph_count == 1
                    else f"The saved draft contains {paragraph_count} text paragraphs."
                ),
            },
            {
                "check_key": "timing_context",
                "status": "info",
                "message": (
                    f"The prompt carries {self._row_value(row, 'time_limit_minutes')} minutes "
                    f"of {self._row_value(row, 'time_limit_evidence').replace('_', ' ')} guidance. "
                    "Continuous writing time was not measured."
                ),
            },
            {
                "check_key": "revision_pins",
                "status": "pass",
                "message": (
                    f"Prompt revision {row['prompt_revision']} and instructional rubric "
                    f"revision {self._row_value(row, 'rubric_revision')} will be pinned."
                ),
            },
        ]
        return {
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "checks": checks,
            "can_submit": not any(check["status"] == "block" for check in checks),
        }

    def pre_submit(
        self, draft_id: str, *, expected_edit_revision: int
    ) -> EnglishEssayPreSubmitResponse:
        row = self.repository.get(self.learner_id, draft_id)
        self._response(row)
        if row["edit_revision"] != expected_edit_revision:
            raise EnglishEssayError(
                "essay_draft_conflict",
                "The saved draft changed before the checks ran. Review the latest copy and try again.",
                409,
            )
        evaluation = self._evaluate(row)
        rubric_key = self._row_value(row, "rubric_key") or self.rubric["stable_key"]
        rubric_revision = (
            self._row_value(row, "rubric_revision") or self.rubric["revision"]
        )
        return EnglishEssayPreSubmitResponse(
            draft_id=draft_id,
            edit_revision=row["edit_revision"],
            prompt_key=row["prompt_key"],
            prompt_revision=row["prompt_revision"],
            rubric_key=rubric_key,
            rubric_revision=rubric_revision,
            word_count=evaluation["word_count"],
            paragraph_count=evaluation["paragraph_count"],
            body_sha256=evaluation["body_sha256"],
            prompt_time_limit_minutes=self._row_value(row, "time_limit_minutes"),
            time_limit_evidence=self._row_value(row, "time_limit_evidence"),
            checks=evaluation["checks"],
            can_submit=evaluation["can_submit"],
        )

    def submit(
        self,
        draft_id: str,
        *,
        expected_edit_revision: int,
        idempotency_key: str,
    ) -> EnglishEssaySubmissionResponse:
        row = self.repository.submit(
            self.learner_id,
            draft_id,
            expected_edit_revision=expected_edit_revision,
            idempotency_key=idempotency_key,
            evaluate=self._evaluate,
        )
        public_row = {
            field: row[field]
            for field in EnglishEssaySubmissionResponse.model_fields
            if field in row
        }
        public_row["submission_id"] = str(public_row["submission_id"])
        public_row["draft_id"] = str(public_row["draft_id"])
        return EnglishEssaySubmissionResponse(**public_row)

    def _response(self, row: dict) -> EnglishEssayDraftResponse:
        if "prompt" in row:
            source = row["prompt"]
            prompt = EnglishEssayPromptResponse(
                stable_key=source["stable_key"],
                revision=source["revision"],
                title=source["title"],
                prompt_family=source["prompt_family"],
                prompt_text=source["prompt_text"],
                instructions=source["instructions"],
                time_limit_minutes=source["time_limit_minutes"],
                time_limit_evidence=source["time_limit_evidence"],
                word_count_guidance=source["word_count_guidance"],
                word_count_status=source["word_count_status"],
                content_status=source["status"],
                development_preview=source["status"] != "published",
            )
        elif "prompt_title" in row:
            prompt = EnglishEssayPromptResponse(
                stable_key=row["prompt_key"],
                revision=row["prompt_revision"],
                title=row["prompt_title"],
                prompt_family=row["prompt_family"],
                prompt_text=row["prompt_text"],
                instructions=row["instructions"],
                time_limit_minutes=row["time_limit_minutes"],
                time_limit_evidence=row["time_limit_evidence"],
                word_count_guidance=row["word_count_guidance"],
                word_count_status=row["word_count_status"],
                content_status=row["prompt_status"],
                development_preview=row["prompt_status"] != "published",
            )
        else:
            prompt = self.current_prompt()
        if prompt.content_status != "published" and not self.allow_drafts:
            raise EnglishEssayError(
                "essay_draft_not_found", "Essay draft not found.", 404
            )
        return EnglishEssayDraftResponse(
            draft_id=str(row["draft_id"]),
            prompt=prompt,
            body=row["body"],
            word_count=row["word_count"],
            edit_revision=row["edit_revision"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
