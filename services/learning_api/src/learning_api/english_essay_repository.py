"""Owned persistence for mutable essay drafts and immutable submissions."""

from __future__ import annotations

import json
from collections.abc import Callable
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
        self.submissions: dict[str, dict] = {}
        self.submission_idempotency: dict[tuple[str, str], str] = {}
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

    def submit(
        self,
        learner_id: str,
        draft_id: str,
        *,
        expected_edit_revision: int,
        idempotency_key: str,
        evaluate: Callable[[dict], dict],
    ) -> dict:
        with self._lock:
            prior_id = self.submission_idempotency.get((learner_id, idempotency_key))
            if prior_id:
                prior = self.submissions[prior_id]
                if (
                    prior["draft_id"] != draft_id
                    or prior["draft_edit_revision"] != expected_edit_revision
                ):
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another essay submission.",
                        409,
                    )
                return dict(prior)
            current = self.get(learner_id, draft_id)
            if current["edit_revision"] != expected_edit_revision:
                raise EnglishEssayError(
                    "essay_draft_conflict",
                    "The saved draft changed before submission. Review the latest copy and try again.",
                    409,
                )
            if any(
                submission["draft_id"] == draft_id
                and submission["draft_edit_revision"] == expected_edit_revision
                for submission in self.submissions.values()
            ):
                raise EnglishEssayError(
                    "essay_revision_already_submitted",
                    "This exact saved draft revision was already submitted.",
                    409,
                )
            evaluation = evaluate(current)
            if not evaluation["can_submit"]:
                raise EnglishEssayError(
                    "essay_submission_blocked",
                    "Resolve the blocking pre-submission checks before submitting.",
                    422,
                )
            submission_revision = 1 + sum(
                submission["draft_id"] == draft_id
                for submission in self.submissions.values()
            )
            submitted_at = datetime.now(UTC)
            created_at = datetime.fromisoformat(str(current["created_at"]))
            submission_id = str(uuid4())
            submission = {
                "submission_id": submission_id,
                "learner_id": learner_id,
                "draft_id": draft_id,
                "prompt_key": current["prompt_key"],
                "prompt_revision": current["prompt_revision"],
                "rubric_key": current["prompt"]["rubric_key"],
                "rubric_revision": current["prompt"]["rubric_revision"],
                "draft_edit_revision": expected_edit_revision,
                "submission_revision": submission_revision,
                "body": current["body"],
                "body_sha256": evaluation["body_sha256"],
                "word_count": evaluation["word_count"],
                "paragraph_count": evaluation["paragraph_count"],
                "deterministic_checks": evaluation["checks"],
                "draft_created_at": current["created_at"],
                "draft_updated_at": current["updated_at"],
                "draft_age_seconds": max(
                    0, int((submitted_at - created_at).total_seconds())
                ),
                "submitted_at": submitted_at.isoformat(),
            }
            self.submissions[submission_id] = submission
            self.submission_idempotency[(learner_id, idempotency_key)] = submission_id
            return dict(submission)


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
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision,
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
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = versions.rubric_version_id
                  join english_essay_rubrics rubrics
                    on rubrics.id = rubric_versions.rubric_id
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
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision,
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
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = versions.rubric_version_id
                  join english_essay_rubrics rubrics
                    on rubrics.id = rubric_versions.rubric_id
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
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision,
                       versions.prompt_text, versions.instructions,
                       versions.time_limit_minutes, versions.time_limit_evidence,
                       versions.word_count_guidance, versions.word_count_status,
                       versions.status::text as prompt_status
                  from english_essay_drafts drafts
                  join english_essay_prompt_versions versions
                    on versions.id = drafts.prompt_version_id
                  join english_essay_prompts prompts on prompts.id = versions.prompt_id
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = versions.rubric_version_id
                  join english_essay_rubrics rubrics
                    on rubrics.id = rubric_versions.rubric_id
                 where drafts.id = %s
                """,
                (draft_id,),
            ).fetchone()
            return {**dict(row), **dict(prompt)}

    @staticmethod
    def _submission_by_id(connection, learner_id: str, submission_id: str) -> dict:
        row = connection.execute(
            """
            select submissions.id::text as submission_id,
                   submissions.draft_id::text as draft_id,
                   prompts.stable_key as prompt_key,
                   prompt_versions.revision as prompt_revision,
                   rubrics.stable_key as rubric_key,
                   rubric_versions.revision as rubric_revision,
                   submissions.draft_edit_revision,
                   submissions.submission_revision, submissions.body,
                   submissions.body_sha256, submissions.word_count,
                   submissions.paragraph_count,
                   submissions.deterministic_checks,
                   submissions.draft_created_at, submissions.draft_updated_at,
                   submissions.draft_age_seconds, submissions.submitted_at
              from english_essay_submissions submissions
              join english_essay_prompt_versions prompt_versions
                on prompt_versions.id = submissions.prompt_version_id
              join english_essay_prompts prompts
                on prompts.id = prompt_versions.prompt_id
              join english_essay_rubric_versions rubric_versions
                on rubric_versions.id = submissions.rubric_version_id
              join english_essay_rubrics rubrics
                on rubrics.id = rubric_versions.rubric_id
             where submissions.id = %s and submissions.student_id = %s
            """,
            (submission_id, learner_id),
        ).fetchone()
        if not row:
            raise EnglishEssayError(
                "essay_submission_not_found", "Essay submission not found.", 404
            )
        return dict(row)

    def submit(
        self,
        learner_id: str,
        draft_id: str,
        *,
        expected_edit_revision: int,
        idempotency_key: str,
        evaluate: Callable[[dict], dict],
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-essay-submission:{learner_id}:{idempotency_key}",),
            )
            prior = connection.execute(
                """
                select submission_id
                  from english_essay_submission_idempotency_keys
                 where student_id = %s and idempotency_key = %s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if prior:
                result = self._submission_by_id(
                    connection, learner_id, str(prior["submission_id"])
                )
                if (
                    result["draft_id"] != draft_id
                    or result["draft_edit_revision"] != expected_edit_revision
                ):
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another essay submission.",
                        409,
                    )
                return result

            draft = connection.execute(
                """
                select drafts.id as draft_id, drafts.student_id,
                       drafts.prompt_version_id, versions.rubric_version_id,
                       prompts.stable_key as prompt_key,
                       versions.revision as prompt_revision,
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision,
                       versions.word_count_guidance, versions.word_count_status,
                       versions.time_limit_minutes, versions.time_limit_evidence,
                       versions.status::text as prompt_status,
                       drafts.body, drafts.word_count, drafts.edit_revision,
                       drafts.created_at, drafts.updated_at
                  from english_essay_drafts drafts
                  join english_essay_prompt_versions versions
                    on versions.id = drafts.prompt_version_id
                  join english_essay_prompts prompts on prompts.id = versions.prompt_id
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = versions.rubric_version_id
                  join english_essay_rubrics rubrics
                    on rubrics.id = rubric_versions.rubric_id
                 where drafts.id = %s and drafts.student_id = %s
                 for update of drafts
                """,
                (draft_id, learner_id),
            ).fetchone()
            if not draft:
                raise EnglishEssayError(
                    "essay_draft_not_found", "Essay draft not found.", 404
                )
            if draft["edit_revision"] != expected_edit_revision:
                raise EnglishEssayError(
                    "essay_draft_conflict",
                    "The saved draft changed before submission. Review the latest copy and try again.",
                    409,
                )
            already_submitted = connection.execute(
                """
                select id from english_essay_submissions
                 where draft_id = %s and draft_edit_revision = %s
                """,
                (draft_id, expected_edit_revision),
            ).fetchone()
            if already_submitted:
                raise EnglishEssayError(
                    "essay_revision_already_submitted",
                    "This exact saved draft revision was already submitted.",
                    409,
                )
            evaluation = evaluate(dict(draft))
            if not evaluation["can_submit"]:
                raise EnglishEssayError(
                    "essay_submission_blocked",
                    "Resolve the blocking pre-submission checks before submitting.",
                    422,
                )
            submission_revision = connection.execute(
                """
                select coalesce(max(submission_revision), 0) + 1 as revision
                  from english_essay_submissions where draft_id = %s
                """,
                (draft_id,),
            ).fetchone()["revision"]
            submission = connection.execute(
                """
                insert into english_essay_submissions(
                    student_id, draft_id, prompt_version_id, rubric_version_id,
                    draft_edit_revision, submission_revision, body, body_sha256,
                    word_count, paragraph_count, deterministic_checks,
                    draft_created_at, draft_updated_at, draft_age_seconds
                ) values (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s::jsonb, %s, %s,
                    greatest(0, extract(epoch from (now() - %s::timestamptz))::integer)
                )
                returning id
                """,
                (
                    learner_id,
                    draft_id,
                    draft["prompt_version_id"],
                    draft["rubric_version_id"],
                    expected_edit_revision,
                    submission_revision,
                    draft["body"],
                    evaluation["body_sha256"],
                    evaluation["word_count"],
                    evaluation["paragraph_count"],
                    json.dumps(evaluation["checks"]),
                    draft["created_at"],
                    draft["updated_at"],
                    draft["created_at"],
                ),
            ).fetchone()
            connection.execute(
                """
                insert into english_essay_submission_idempotency_keys(
                    student_id, idempotency_key, submission_id
                ) values (%s, %s, %s)
                """,
                (learner_id, idempotency_key, submission["id"]),
            )
            return self._submission_by_id(
                connection, learner_id, str(submission["id"])
            )
