"""Owned persistence for mutable English essay working drafts."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row


class EnglishEssayError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def _now() -> str:
    return datetime.now(UTC).isoformat()


class InMemoryEnglishEssayRepository:
    """Development/test adapter with the same ownership and revision semantics as PostgreSQL."""

    def __init__(self):
        self.drafts: dict[str, dict] = {}
        self.idempotency: dict[tuple[str, str], str] = {}
        self._lock = Lock()

    def create_or_resume(
        self,
        learner_id: str,
        *,
        prompt: dict,
        idempotency_key: str,
    ) -> dict:
        with self._lock:
            prior_id = self.idempotency.get((learner_id, idempotency_key))
            if prior_id:
                prior = self.drafts[prior_id]
                if prior["prompt_key"] != prompt["stable_key"] or prior[
                    "prompt_revision"
                ] != prompt["revision"]:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for a different essay prompt.",
                        409,
                    )
                return dict(prior)
            existing = next(
                (
                    draft
                    for draft in self.drafts.values()
                    if draft["learner_id"] == learner_id
                    and draft["prompt_key"] == prompt["stable_key"]
                    and draft["prompt_revision"] == prompt["revision"]
                ),
                None,
            )
            if existing is None:
                timestamp = _now()
                draft_id = str(uuid4())
                existing = {
                    "draft_id": draft_id,
                    "learner_id": learner_id,
                    "prompt_key": prompt["stable_key"],
                    "prompt_revision": prompt["revision"],
                    "body": "",
                    "word_count": 0,
                    "edit_revision": 1,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "prompt": dict(prompt),
                }
                self.drafts[draft_id] = existing
            self.idempotency[(learner_id, idempotency_key)] = existing["draft_id"]
            return dict(existing)

    def get(self, learner_id: str, draft_id: str) -> dict:
        draft = self.drafts.get(draft_id)
        if draft is None or draft["learner_id"] != learner_id:
            raise EnglishEssayError("essay_draft_not_found", "Essay draft not found.", 404)
        return dict(draft)

    def update(
        self,
        learner_id: str,
        draft_id: str,
        *,
        body: str,
        word_count: int,
        expected_edit_revision: int,
    ) -> dict:
        with self._lock:
            current = self.get(learner_id, draft_id)
            if current["edit_revision"] != expected_edit_revision:
                raise EnglishEssayError(
                    "essay_draft_conflict",
                    "This draft changed in another tab. Your local text has been preserved.",
                    409,
                )
            updated = {
                **current,
                "body": body,
                "word_count": word_count,
                "edit_revision": expected_edit_revision + 1,
                "updated_at": _now(),
            }
            self.drafts[draft_id] = updated
            return dict(updated)


class PostgresEnglishEssayRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def create_or_resume(
        self,
        learner_id: str,
        *,
        prompt: dict,
        idempotency_key: str,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            prior = connection.execute(
                """
                select drafts.id as draft_id, prompts.stable_key as prompt_key,
                       versions.revision as prompt_revision, versions.title as prompt_title,
                       versions.prompt_family, versions.prompt_text, versions.instructions,
                       versions.time_limit_minutes, versions.time_limit_evidence,
                       versions.word_count_guidance, versions.word_count_status,
                       versions.status::text as prompt_status, drafts.body,
                       drafts.word_count, drafts.edit_revision,
                       drafts.created_at, drafts.updated_at
                  from english_essay_draft_idempotency_keys keys
                  join english_essay_drafts drafts on drafts.id = keys.draft_id
                  join english_essay_prompt_versions versions
                    on versions.id = drafts.prompt_version_id
                  join english_essay_prompts prompts on prompts.id = versions.prompt_id
                 where keys.student_id = %s and keys.idempotency_key = %s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if prior:
                if prior["prompt_key"] != prompt["stable_key"] or prior[
                    "prompt_revision"
                ] != prompt["revision"]:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for a different essay prompt.",
                        409,
                    )
                return dict(prior)
            prompt_version = connection.execute(
                """
                select versions.id
                  from english_essay_prompt_versions versions
                  join english_essay_prompts prompts on prompts.id = versions.prompt_id
                 where prompts.stable_key = %s and versions.revision = %s
                """,
                (prompt["stable_key"], prompt["revision"]),
            ).fetchone()
            if not prompt_version:
                raise EnglishEssayError(
                    "essay_prompt_not_imported",
                    "The selected essay prompt is awaiting its database import.",
                    503,
                )
            row = connection.execute(
                """
                insert into english_essay_drafts(student_id, prompt_version_id)
                values (%s, %s)
                on conflict (student_id, prompt_version_id) do nothing
                returning id as draft_id, body, word_count, edit_revision,
                          created_at, updated_at
                """,
                (learner_id, prompt_version["id"]),
            ).fetchone()
            if row is None:
                row = connection.execute(
                    """
                    select id as draft_id, body, word_count, edit_revision,
                           created_at, updated_at
                      from english_essay_drafts
                     where student_id = %s and prompt_version_id = %s
                    """,
                    (learner_id, prompt_version["id"]),
                ).fetchone()
            key_row = connection.execute(
                """
                insert into english_essay_draft_idempotency_keys(
                    student_id, idempotency_key, draft_id
                ) values (%s, %s, %s)
                on conflict (student_id, idempotency_key) do nothing
                returning draft_id
                """,
                (learner_id, idempotency_key, row["draft_id"]),
            ).fetchone()
            if key_row is None:
                keyed = connection.execute(
                    """
                    select drafts.id as draft_id, prompts.stable_key as prompt_key,
                           versions.revision as prompt_revision
                      from english_essay_draft_idempotency_keys keys
                      join english_essay_drafts drafts on drafts.id = keys.draft_id
                      join english_essay_prompt_versions versions
                        on versions.id = drafts.prompt_version_id
                      join english_essay_prompts prompts on prompts.id = versions.prompt_id
                     where keys.student_id = %s and keys.idempotency_key = %s
                    """,
                    (learner_id, idempotency_key),
                ).fetchone()
                if (
                    keyed["prompt_key"] != prompt["stable_key"]
                    or keyed["prompt_revision"] != prompt["revision"]
                ):
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for a different essay prompt.",
                        409,
                    )
                row = self.get(learner_id, str(keyed["draft_id"]))
                return row
            return {
                **dict(row),
                "prompt_key": prompt["stable_key"],
                "prompt_revision": prompt["revision"],
            }

    def get(self, learner_id: str, draft_id: str) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                """
                select drafts.id as draft_id, prompts.stable_key as prompt_key,
                       versions.revision as prompt_revision, versions.title as prompt_title,
                       versions.prompt_family, versions.prompt_text, versions.instructions,
                       versions.time_limit_minutes, versions.time_limit_evidence,
                       versions.word_count_guidance, versions.word_count_status,
                       versions.status::text as prompt_status, drafts.body,
                       drafts.word_count, drafts.edit_revision,
                       drafts.created_at, drafts.updated_at
                  from english_essay_drafts drafts
                  join english_essay_prompt_versions versions
                    on versions.id = drafts.prompt_version_id
                  join english_essay_prompts prompts on prompts.id = versions.prompt_id
                 where drafts.id = %s and drafts.student_id = %s
                """,
                (draft_id, learner_id),
            ).fetchone()
        if not row:
            raise EnglishEssayError("essay_draft_not_found", "Essay draft not found.", 404)
        return dict(row)

    def update(
        self,
        learner_id: str,
        draft_id: str,
        *,
        body: str,
        word_count: int,
        expected_edit_revision: int,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            row = connection.execute(
                """
                update english_essay_drafts
                   set body = %s,
                       word_count = %s,
                       edit_revision = edit_revision + 1,
                       updated_at = greatest(now(), updated_at + interval '1 microsecond')
                 where id = %s and student_id = %s and edit_revision = %s
                returning id as draft_id, body, word_count, edit_revision,
                          created_at, updated_at
                """,
                (body, word_count, draft_id, learner_id, expected_edit_revision),
            ).fetchone()
            if not row:
                exists = connection.execute(
                    "select 1 from english_essay_drafts where id = %s and student_id = %s",
                    (draft_id, learner_id),
                ).fetchone()
                if not exists:
                    raise EnglishEssayError(
                        "essay_draft_not_found", "Essay draft not found.", 404
                    )
                raise EnglishEssayError(
                    "essay_draft_conflict",
                    "This draft changed in another tab. Your local text has been preserved.",
                    409,
                )
            prompt = connection.execute(
                """
                select prompts.stable_key as prompt_key, versions.revision as prompt_revision,
                       versions.title as prompt_title, versions.prompt_family,
                       versions.prompt_text, versions.instructions,
                       versions.time_limit_minutes, versions.time_limit_evidence,
                       versions.word_count_guidance, versions.word_count_status,
                       versions.status::text as prompt_status
                  from english_essay_drafts drafts
                  join english_essay_prompt_versions versions
                    on versions.id = drafts.prompt_version_id
                  join english_essay_prompts prompts on prompts.id = versions.prompt_id
                 where drafts.id = %s
                """,
                (draft_id,),
            ).fetchone()
            return {**dict(row), **dict(prompt)}
