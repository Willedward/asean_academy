"""Application service for draft-only English essay writing."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .english_contracts import EnglishEssayDraftResponse, EnglishEssayPromptResponse
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
