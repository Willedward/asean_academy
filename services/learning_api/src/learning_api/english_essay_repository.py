"""Owned persistence for essay drafts, submissions and learner self-reviews."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
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
        self.self_reviews: dict[str, dict] = {}
        self.self_review_idempotency: dict[tuple[str, str], str] = {}
        self.marking_jobs: dict[str, dict] = {}
        self.marking_job_idempotency: dict[tuple[str, str], str] = {}
        self.marking_feedback: dict[str, dict] = {}
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

    def get_submission(self, learner_id: str, submission_id: str) -> dict:
        submission = self.submissions.get(submission_id)
        if submission is None or submission["learner_id"] != learner_id:
            raise EnglishEssayError(
                "essay_submission_not_found", "Essay submission not found.", 404
            )
        return dict(submission)

    def latest_submission(self, learner_id: str, draft_id: str) -> dict | None:
        self.get(learner_id, draft_id)
        owned = [
            submission
            for submission in self.submissions.values()
            if submission["learner_id"] == learner_id
            and submission["draft_id"] == draft_id
        ]
        if not owned:
            return None
        return dict(max(owned, key=lambda row: row["submission_revision"]))

    def get_self_review(self, learner_id: str, submission_id: str) -> dict | None:
        self.get_submission(learner_id, submission_id)
        review = next(
            (
                row
                for row in self.self_reviews.values()
                if row["submission_id"] == submission_id
                and row["learner_id"] == learner_id
            ),
            None,
        )
        return dict(review) if review else None

    def create_self_review(
        self,
        learner_id: str,
        submission_id: str,
        *,
        rubric_key: str,
        rubric_revision: int,
        criterion_reflections: list[dict],
        overall_reflection: str,
        idempotency_key: str,
    ) -> dict:
        with self._lock:
            submission = self.get_submission(learner_id, submission_id)
            prior_id = self.self_review_idempotency.get(
                (learner_id, idempotency_key)
            )
            if prior_id:
                prior = self.self_reviews[prior_id]
                if prior["submission_id"] != submission_id:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another essay self-review.",
                        409,
                    )
                return dict(prior)
            if self.get_self_review(learner_id, submission_id):
                raise EnglishEssayError(
                    "essay_self_review_already_completed",
                    "This submission already has a completed self-review.",
                    409,
                )
            if (
                submission["rubric_key"] != rubric_key
                or submission["rubric_revision"] != rubric_revision
            ):
                raise EnglishEssayError(
                    "essay_rubric_changed",
                    "The self-review rubric does not match the submitted essay.",
                    409,
                )
            self_review_id = str(uuid4())
            review = {
                "self_review_id": self_review_id,
                "learner_id": learner_id,
                "submission_id": submission_id,
                "rubric_key": rubric_key,
                "rubric_revision": rubric_revision,
                "criterion_reflections": json.loads(
                    json.dumps(criterion_reflections)
                ),
                "overall_reflection": overall_reflection,
                "disclaimer_acknowledged": True,
                "completed_at": _now(),
            }
            self.self_reviews[self_review_id] = review
            self.self_review_idempotency[(learner_id, idempotency_key)] = (
                self_review_id
            )
            return dict(review)

    def enqueue_marking_job(
        self,
        learner_id: str,
        submission_id: str,
        *,
        rubric_key: str,
        rubric_revision: int,
        rubric_criteria: list[dict],
        idempotency_key: str,
    ) -> dict:
        with self._lock:
            submission = self.submissions.get(submission_id)
            if submission is None or submission["learner_id"] != learner_id:
                raise EnglishEssayError(
                    "essay_submission_not_found", "Essay submission not found.", 404
                )
            if not any(
                review["submission_id"] == submission_id
                and review["learner_id"] == learner_id
                for review in self.self_reviews.values()
            ):
                raise EnglishEssayError(
                    "essay_self_review_required",
                    "Complete the learner self-review before requesting fixture feedback.",
                    409,
                )
            prior_id = self.marking_job_idempotency.get(
                (learner_id, idempotency_key)
            )
            if prior_id:
                prior = self.marking_jobs[prior_id]
                if prior["submission_id"] != submission_id:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another marking job.",
                        409,
                    )
                return dict(prior)
            existing = next(
                (
                    job
                    for job in self.marking_jobs.values()
                    if job["submission_id"] == submission_id
                ),
                None,
            )
            if existing:
                self.marking_job_idempotency[(learner_id, idempotency_key)] = existing[
                    "job_id"
                ]
                return dict(existing)
            if (
                submission["rubric_key"] != rubric_key
                or submission["rubric_revision"] != rubric_revision
            ):
                raise EnglishEssayError(
                    "essay_rubric_changed",
                    "The marking rubric does not match the submitted essay.",
                    409,
                )
            timestamp = _now()
            job_id = str(uuid4())
            job = {
                "job_id": job_id,
                "learner_id": learner_id,
                "submission_id": submission_id,
                "rubric_key": rubric_key,
                "rubric_revision": rubric_revision,
                "rubric_criteria": json.loads(json.dumps(rubric_criteria)),
                "submission_body": submission["body"],
                "mode": "deterministic_fixture",
                "status": "queued",
                "attempt_count": 0,
                "max_attempts": 3,
                "run_after": timestamp,
                "lease_token": None,
                "leased_at": None,
                "worker_id": None,
                "last_error_code": None,
                "last_error_message": None,
                "created_at": timestamp,
                "updated_at": timestamp,
                "completed_at": None,
            }
            self.marking_jobs[job_id] = job
            self.marking_job_idempotency[(learner_id, idempotency_key)] = job_id
            return dict(job)

    def get_marking_workspace(self, learner_id: str, submission_id: str) -> dict:
        self.get_submission(learner_id, submission_id)
        job = next(
            (
                row
                for row in self.marking_jobs.values()
                if row["learner_id"] == learner_id
                and row["submission_id"] == submission_id
            ),
            None,
        )
        feedback = (
            next(
                (
                    row
                    for row in self.marking_feedback.values()
                    if row["submission_id"] == submission_id
                    and row["learner_id"] == learner_id
                ),
                None,
            )
            if job
            else None
        )
        return {
            "submission_id": submission_id,
            "job": dict(job) if job else None,
            "feedback": json.loads(json.dumps(feedback)) if feedback else None,
        }

    def claim_marking_job(
        self, job_id: str, *, worker_id: str, lease_seconds: int = 300
    ) -> dict | None:
        with self._lock:
            job = self.marking_jobs.get(job_id)
            if job is None:
                return None
            now = datetime.now(UTC)
            run_after = datetime.fromisoformat(str(job["run_after"]))
            stale = (
                job["status"] == "processing"
                and job["leased_at"] is not None
                and datetime.fromisoformat(str(job["leased_at"]))
                <= now - timedelta(seconds=lease_seconds)
            )
            if stale and job["attempt_count"] >= job["max_attempts"]:
                job.update(
                    status="permanent_failed",
                    lease_token=None,
                    leased_at=None,
                    updated_at=now.isoformat(),
                    last_error_code="fixture_worker_lease_expired",
                    last_error_message="The final worker lease expired before completion.",
                )
                return None
            due = job["status"] in {"queued", "retryable_failed"} and run_after <= now
            if not due and not stale:
                return None
            lease_token = str(uuid4())
            job.update(
                status="processing",
                attempt_count=job["attempt_count"] + 1,
                lease_token=lease_token,
                leased_at=now.isoformat(),
                worker_id=worker_id,
                updated_at=now.isoformat(),
            )
            return dict(job)

    def complete_marking_job(
        self, job_id: str, *, lease_token: str, feedback: dict
    ) -> dict:
        with self._lock:
            job = self.marking_jobs.get(job_id)
            if (
                job is None
                or job["status"] != "processing"
                or job["lease_token"] != lease_token
            ):
                raise EnglishEssayError(
                    "essay_marking_lease_lost",
                    "The marking job lease is no longer owned by this worker.",
                    409,
                )
            timestamp = _now()
            feedback_id = str(uuid4())
            stored = {
                "feedback_id": feedback_id,
                "job_id": job_id,
                "learner_id": job["learner_id"],
                "submission_id": job["submission_id"],
                "rubric_key": job["rubric_key"],
                "rubric_revision": job["rubric_revision"],
                **json.loads(json.dumps(feedback)),
                "created_at": timestamp,
            }
            self.marking_feedback[feedback_id] = stored
            job.update(
                status="succeeded",
                lease_token=None,
                leased_at=None,
                updated_at=timestamp,
                completed_at=timestamp,
                last_error_code=None,
                last_error_message=None,
            )
            return dict(stored)

    def fail_marking_job(
        self,
        job_id: str,
        *,
        lease_token: str,
        error_code: str,
        error_message: str,
        retry_delay_seconds: int = 5,
    ) -> dict:
        with self._lock:
            job = self.marking_jobs.get(job_id)
            if (
                job is None
                or job["status"] != "processing"
                or job["lease_token"] != lease_token
            ):
                raise EnglishEssayError(
                    "essay_marking_lease_lost",
                    "The marking job lease is no longer owned by this worker.",
                    409,
                )
            now = datetime.now(UTC)
            permanent = job["attempt_count"] >= job["max_attempts"]
            job.update(
                status="permanent_failed" if permanent else "retryable_failed",
                run_after=(now + timedelta(seconds=retry_delay_seconds)).isoformat(),
                lease_token=None,
                leased_at=None,
                updated_at=now.isoformat(),
                last_error_code=error_code,
                last_error_message=error_message[:1000],
            )
            return dict(job)


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

    def get_submission(self, learner_id: str, submission_id: str) -> dict:
        with self._connect() as connection:
            return self._submission_by_id(connection, learner_id, submission_id)

    def latest_submission(self, learner_id: str, draft_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                select submissions.id::text as submission_id
                  from english_essay_submissions submissions
                  join english_essay_drafts drafts on drafts.id = submissions.draft_id
                 where submissions.draft_id = %s and drafts.student_id = %s
                 order by submissions.submission_revision desc
                 limit 1
                """,
                (draft_id, learner_id),
            ).fetchone()
            if row:
                return self._submission_by_id(
                    connection, learner_id, row["submission_id"]
                )
            owned_draft = connection.execute(
                "select 1 from english_essay_drafts where id = %s and student_id = %s",
                (draft_id, learner_id),
            ).fetchone()
            if not owned_draft:
                raise EnglishEssayError(
                    "essay_draft_not_found", "Essay draft not found.", 404
                )
            return None

    @staticmethod
    def _self_review_by_id(
        connection, learner_id: str, self_review_id: str
    ) -> dict:
        row = connection.execute(
            """
            select reviews.id::text as self_review_id,
                   reviews.submission_id::text as submission_id,
                   rubrics.stable_key as rubric_key,
                   rubric_versions.revision as rubric_revision,
                   reviews.criterion_reflections, reviews.overall_reflection,
                   reviews.disclaimer_acknowledged, reviews.completed_at
              from english_essay_self_reviews reviews
              join english_essay_rubric_versions rubric_versions
                on rubric_versions.id = reviews.rubric_version_id
              join english_essay_rubrics rubrics
                on rubrics.id = rubric_versions.rubric_id
             where reviews.id = %s and reviews.student_id = %s
            """,
            (self_review_id, learner_id),
        ).fetchone()
        if not row:
            raise EnglishEssayError(
                "essay_self_review_not_found", "Essay self-review not found.", 404
            )
        return dict(row)

    def get_self_review(self, learner_id: str, submission_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                select reviews.id::text as self_review_id
                  from english_essay_self_reviews reviews
                 where reviews.submission_id = %s and reviews.student_id = %s
                """,
                (submission_id, learner_id),
            ).fetchone()
            if row:
                return self._self_review_by_id(
                    connection, learner_id, row["self_review_id"]
                )
            self._submission_by_id(connection, learner_id, submission_id)
            return None

    def create_self_review(
        self,
        learner_id: str,
        submission_id: str,
        *,
        rubric_key: str,
        rubric_revision: int,
        criterion_reflections: list[dict],
        overall_reflection: str,
        idempotency_key: str,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-essay-self-review:{learner_id}:{idempotency_key}",),
            )
            prior = connection.execute(
                """
                select self_review_id
                  from english_essay_self_review_idempotency_keys
                 where student_id = %s and idempotency_key = %s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if prior:
                result = self._self_review_by_id(
                    connection, learner_id, str(prior["self_review_id"])
                )
                if result["submission_id"] != submission_id:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another essay self-review.",
                        409,
                    )
                return result

            submission = connection.execute(
                """
                select submissions.id, submissions.rubric_version_id,
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision
                  from english_essay_submissions submissions
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = submissions.rubric_version_id
                  join english_essay_rubrics rubrics
                    on rubrics.id = rubric_versions.rubric_id
                 where submissions.id = %s and submissions.student_id = %s
                 for update of submissions
                """,
                (submission_id, learner_id),
            ).fetchone()
            if not submission:
                raise EnglishEssayError(
                    "essay_submission_not_found", "Essay submission not found.", 404
                )
            if (
                submission["rubric_key"] != rubric_key
                or submission["rubric_revision"] != rubric_revision
            ):
                raise EnglishEssayError(
                    "essay_rubric_changed",
                    "The self-review rubric does not match the submitted essay.",
                    409,
                )
            existing = connection.execute(
                "select id from english_essay_self_reviews where submission_id = %s",
                (submission_id,),
            ).fetchone()
            if existing:
                raise EnglishEssayError(
                    "essay_self_review_already_completed",
                    "This submission already has a completed self-review.",
                    409,
                )
            created = connection.execute(
                """
                insert into english_essay_self_reviews(
                    student_id, submission_id, rubric_version_id,
                    criterion_reflections, overall_reflection,
                    disclaimer_acknowledged
                ) values (%s, %s, %s, %s::jsonb, %s, true)
                returning id
                """,
                (
                    learner_id,
                    submission_id,
                    submission["rubric_version_id"],
                    json.dumps(criterion_reflections),
                    overall_reflection,
                ),
            ).fetchone()
            connection.execute(
                """
                insert into english_essay_self_review_idempotency_keys(
                    student_id, idempotency_key, self_review_id
                ) values (%s, %s, %s)
                """,
                (learner_id, idempotency_key, created["id"]),
            )
            return self._self_review_by_id(
                connection, learner_id, str(created["id"])
            )

    @staticmethod
    def _marking_job_by_id(connection, learner_id: str, job_id: str) -> dict:
        row = connection.execute(
            """
            select jobs.id::text as job_id,
                   jobs.submission_id::text as submission_id,
                   rubrics.stable_key as rubric_key,
                   rubric_versions.revision as rubric_revision,
                   jobs.mode, jobs.status, jobs.attempt_count, jobs.max_attempts,
                   jobs.run_after, jobs.last_error_code, jobs.last_error_message,
                   jobs.created_at, jobs.updated_at, jobs.completed_at
              from english_essay_marking_jobs jobs
              join english_essay_rubric_versions rubric_versions
                on rubric_versions.id = jobs.rubric_version_id
              join english_essay_rubrics rubrics
                on rubrics.id = rubric_versions.rubric_id
             where jobs.id = %s and jobs.student_id = %s
            """,
            (job_id, learner_id),
        ).fetchone()
        if not row:
            raise EnglishEssayError(
                "essay_marking_job_not_found", "Essay marking job not found.", 404
            )
        return dict(row)

    @staticmethod
    def _marking_feedback_for_submission(
        connection, learner_id: str, submission_id: str
    ) -> dict | None:
        row = connection.execute(
            """
            select feedback.id::text as feedback_id,
                   feedback.job_id::text as job_id,
                   feedback.submission_id::text as submission_id,
                   rubrics.stable_key as rubric_key,
                   rubric_versions.revision as rubric_revision,
                   feedback.fixture_version, feedback.criterion_feedback,
                   feedback.overall_summary, feedback.strengths,
                   feedback.priorities, feedback.learner_disclaimer,
                   feedback.created_at
              from english_essay_marking_feedback feedback
              join english_essay_rubric_versions rubric_versions
                on rubric_versions.id = feedback.rubric_version_id
              join english_essay_rubrics rubrics
                on rubrics.id = rubric_versions.rubric_id
             where feedback.submission_id = %s and feedback.student_id = %s
            """,
            (submission_id, learner_id),
        ).fetchone()
        return dict(row) if row else None

    def enqueue_marking_job(
        self,
        learner_id: str,
        submission_id: str,
        *,
        rubric_key: str,
        rubric_revision: int,
        rubric_criteria: list[dict],
        idempotency_key: str,
    ) -> dict:
        del rubric_criteria
        with self._connect() as connection, connection.transaction():
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"english-essay-marking:{learner_id}:{idempotency_key}",),
            )
            prior = connection.execute(
                """
                select job_id from english_essay_marking_job_idempotency_keys
                 where student_id = %s and idempotency_key = %s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if prior:
                result = self._marking_job_by_id(
                    connection, learner_id, str(prior["job_id"])
                )
                if result["submission_id"] != submission_id:
                    raise EnglishEssayError(
                        "idempotency_conflict",
                        "That idempotency key was already used for another marking job.",
                        409,
                    )
                return result
            source = connection.execute(
                """
                select submissions.rubric_version_id,
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision,
                       reviews.id as self_review_id
                  from english_essay_submissions submissions
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = submissions.rubric_version_id
                  join english_essay_rubrics rubrics
                    on rubrics.id = rubric_versions.rubric_id
                  left join english_essay_self_reviews reviews
                    on reviews.submission_id = submissions.id
                 where submissions.id = %s and submissions.student_id = %s
                 for update of submissions
                """,
                (submission_id, learner_id),
            ).fetchone()
            if not source:
                raise EnglishEssayError(
                    "essay_submission_not_found", "Essay submission not found.", 404
                )
            if not source["self_review_id"]:
                raise EnglishEssayError(
                    "essay_self_review_required",
                    "Complete the learner self-review before requesting fixture feedback.",
                    409,
                )
            if (
                source["rubric_key"] != rubric_key
                or source["rubric_revision"] != rubric_revision
            ):
                raise EnglishEssayError(
                    "essay_rubric_changed",
                    "The marking rubric does not match the submitted essay.",
                    409,
                )
            created = connection.execute(
                """
                insert into english_essay_marking_jobs(
                    student_id, submission_id, rubric_version_id
                ) values (%s, %s, %s)
                on conflict (submission_id) do nothing
                returning id
                """,
                (learner_id, submission_id, source["rubric_version_id"]),
            ).fetchone()
            if created:
                job_id = str(created["id"])
            else:
                existing = connection.execute(
                    """
                    select id::text as job_id from english_essay_marking_jobs
                     where submission_id = %s and student_id = %s
                    """,
                    (submission_id, learner_id),
                ).fetchone()
                if not existing:
                    raise EnglishEssayError(
                        "essay_marking_job_conflict",
                        "The existing marking job is not owned by this learner.",
                        409,
                    )
                job_id = existing["job_id"]
            connection.execute(
                """
                insert into english_essay_marking_job_idempotency_keys(
                    student_id, idempotency_key, job_id
                ) values (%s, %s, %s)
                """,
                (learner_id, idempotency_key, job_id),
            )
            return self._marking_job_by_id(connection, learner_id, job_id)

    def get_marking_workspace(self, learner_id: str, submission_id: str) -> dict:
        with self._connect() as connection:
            owned = connection.execute(
                """
                select id from english_essay_submissions
                 where id = %s and student_id = %s
                """,
                (submission_id, learner_id),
            ).fetchone()
            if not owned:
                raise EnglishEssayError(
                    "essay_submission_not_found", "Essay submission not found.", 404
                )
            job = connection.execute(
                """
                select id::text as job_id from english_essay_marking_jobs
                 where submission_id = %s and student_id = %s
                """,
                (submission_id, learner_id),
            ).fetchone()
            return {
                "submission_id": submission_id,
                "job": (
                    self._marking_job_by_id(
                        connection, learner_id, job["job_id"]
                    )
                    if job
                    else None
                ),
                "feedback": self._marking_feedback_for_submission(
                    connection, learner_id, submission_id
                ),
            }

    def claim_marking_job(
        self, job_id: str, *, worker_id: str, lease_seconds: int = 300
    ) -> dict | None:
        with self._connect() as connection, connection.transaction():
            connection.execute(
                """
                update english_essay_marking_jobs
                   set status = 'permanent_failed',
                       lease_token = null, leased_at = null,
                       last_error_code = 'fixture_worker_lease_expired',
                       last_error_message = 'The final worker lease expired before completion.',
                       updated_at = now()
                 where id = %s and status = 'processing'
                   and attempt_count >= max_attempts
                   and leased_at <= now() - (%s * interval '1 second')
                """,
                (job_id, lease_seconds),
            )
            row = connection.execute(
                """
                with claimable as (
                    select id from english_essay_marking_jobs
                     where id = %s
                       and attempt_count < max_attempts
                       and (
                           (status in ('queued', 'retryable_failed') and run_after <= now())
                           or (status = 'processing'
                               and leased_at <= now() - (%s * interval '1 second'))
                       )
                     for update skip locked
                )
                update english_essay_marking_jobs jobs
                   set status = 'processing',
                       attempt_count = jobs.attempt_count + 1,
                       lease_token = gen_random_uuid(),
                       leased_at = now(),
                       worker_id = %s,
                       updated_at = now()
                  from claimable
                 where jobs.id = claimable.id
                returning jobs.id::text as job_id,
                          jobs.student_id::text as learner_id,
                          jobs.submission_id::text as submission_id,
                          jobs.lease_token::text as lease_token,
                          jobs.attempt_count, jobs.max_attempts
                """,
                (job_id, lease_seconds, worker_id),
            ).fetchone()
            if not row:
                return None
            source = connection.execute(
                """
                select submissions.body as submission_body,
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision,
                       rubric_versions.criteria as rubric_criteria
                  from english_essay_marking_jobs jobs
                  join english_essay_submissions submissions
                    on submissions.id = jobs.submission_id
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = jobs.rubric_version_id
                  join english_essay_rubrics rubrics
                    on rubrics.id = rubric_versions.rubric_id
                 where jobs.id = %s
                """,
                (job_id,),
            ).fetchone()
            return {**dict(row), **dict(source)}

    def complete_marking_job(
        self, job_id: str, *, lease_token: str, feedback: dict
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            job = connection.execute(
                """
                select * from english_essay_marking_jobs
                 where id = %s and status = 'processing' and lease_token = %s
                 for update
                """,
                (job_id, lease_token),
            ).fetchone()
            if not job:
                raise EnglishEssayError(
                    "essay_marking_lease_lost",
                    "The marking job lease is no longer owned by this worker.",
                    409,
                )
            created = connection.execute(
                """
                insert into english_essay_marking_feedback(
                    student_id, job_id, submission_id, rubric_version_id,
                    fixture_version, criterion_feedback, overall_summary,
                    strengths, priorities, learner_disclaimer
                ) values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb,
                          %s::jsonb, %s)
                returning id::text as feedback_id
                """,
                (
                    job["student_id"],
                    job_id,
                    job["submission_id"],
                    job["rubric_version_id"],
                    feedback["fixture_version"],
                    json.dumps(feedback["criterion_feedback"]),
                    feedback["overall_summary"],
                    json.dumps(feedback["strengths"]),
                    json.dumps(feedback["priorities"]),
                    feedback["learner_disclaimer"],
                ),
            ).fetchone()
            connection.execute(
                """
                update english_essay_marking_jobs
                   set status = 'succeeded', lease_token = null, leased_at = null,
                       last_error_code = null, last_error_message = null,
                       completed_at = now(), updated_at = now()
                 where id = %s
                """,
                (job_id,),
            )
            result = self._marking_feedback_for_submission(
                connection, str(job["student_id"]), str(job["submission_id"])
            )
            if not result or result["feedback_id"] != created["feedback_id"]:
                raise EnglishEssayError(
                    "essay_marking_feedback_missing",
                    "The completed fixture feedback could not be restored.",
                    500,
                )
            return result

    def fail_marking_job(
        self,
        job_id: str,
        *,
        lease_token: str,
        error_code: str,
        error_message: str,
        retry_delay_seconds: int = 5,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            row = connection.execute(
                """
                update english_essay_marking_jobs
                   set status = case
                           when attempt_count >= max_attempts then 'permanent_failed'
                           else 'retryable_failed'
                       end,
                       run_after = now() + (%s * interval '1 second'),
                       lease_token = null, leased_at = null,
                       last_error_code = %s, last_error_message = %s,
                       updated_at = now()
                 where id = %s and status = 'processing' and lease_token = %s
                returning student_id::text as learner_id
                """,
                (
                    retry_delay_seconds,
                    error_code,
                    error_message[:1000],
                    job_id,
                    lease_token,
                ),
            ).fetchone()
            if not row:
                raise EnglishEssayError(
                    "essay_marking_lease_lost",
                    "The marking job lease is no longer owned by this worker.",
                    409,
                )
            return self._marking_job_by_id(
                connection, row["learner_id"], job_id
            )
