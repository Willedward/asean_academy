# Checkpoint, mastery, and retry backend handoff

**Branch:** `feature/checkpoint-mastery-retry`

**Parent:** `feature/beta-operations`

**Status:** Implemented for SQLite development and PostgreSQL deployment. Lesson media may remain blank while the frontend and academic content are in progress.

## Goal

Complete the server-owned learning loop after answer-only lesson practice:

1. Unlock lessons in prerequisite order.
2. Record lesson proficiency from deterministic marking.
3. Re-present unresolved questions in a targeted retry session.
4. Unlock the N1 checkpoint only after every N1 lesson is proficient.
5. Mark the unit mastered only after the checkpoint passes.
6. Return all decisions through OpenAPI so the final frontend never calculates progression itself.

The authored N1 policy in `backend_resources/courses/g3_math/secondary_1/n1/v1/course.json` is authoritative:

| Rule | Value |
|---|---:|
| Lesson proficiency threshold | 70% |
| Checkpoint question count | 8 |
| Checkpoint pass threshold | 70% |
| Checkpoint required for mastery | Yes |
| Guided Give up unlock | After 2 incorrect attempts |

## Practice modes

The existing `POST /api/v1/practice-sessions` endpoint accepts three modes.

### Guided lesson practice

```json
{
  "lesson_key": "n1-lesson-01",
  "mode": "guided_practice"
}
```

- Questions come from the lesson's authored practice pool.
- Two hints and Give up remain available according to the existing answer lock.
- A completed session at or above 70%, with no Give up, makes the lesson `proficient`.

### Retry review

```json
{
  "lesson_key": "n1-lesson-01",
  "mode": "retry_review"
}
```

- Only unresolved questions in that lesson are selected.
- The API returns `409 retry_queue_empty` if no question requires review.
- Returned questions use `selection_reason: "required_retry"` and `stage: "adaptive"`.
- The client may optionally send `question_count`; omitting it selects all currently unresolved questions.

### Unit checkpoint

```json
{
  "unit_key": "g3-sec1-n1",
  "mode": "checkpoint"
}
```

- The request must target a unit and cannot target a lesson.
- The server uses exactly the configured eight questions. A client cannot shorten the checkpoint.
- Every question has one attempt.
- A wrong answer resolves that question as `incorrect` and queues it for later review.
- Hints and Give up return `403 checkpoint_support_locked`.
- No solution is returned during the checkpoint.
- At least 70% passes. Seven of eight correct is 87.5% and passes; five of eight is 62.5% and fails.
- A failed checkpoint leaves lessons `proficient` and allows another checkpoint session.
- A passed checkpoint changes every lesson in the unit to `mastered` and cannot be repeated.

Every session-creation request requires a unique `Idempotency-Key` header. Replaying the same key with the same request returns the same session. A second active session for the same learner and target is not created.

## State returned to the frontend

`GET /api/v1/progress` returns lesson and checkpoint state. A checkpoint item has this shape:

```json
{
  "unit_key": "g3-sec1-n1",
  "state": "available",
  "available": true,
  "question_count": 8,
  "passing_percentage": 70,
  "last_session_id": null,
  "last_percentage": null
}
```

Checkpoint `state` is one of:

- `locked`: one or more unit lessons are not proficient.
- `available`: prerequisites are proficient and no checkpoint is active or passed.
- `in_progress`: resume `last_session_id`.
- `passed`: the unit is mastered.

Each lesson includes:

```json
{
  "state": "proficient",
  "unlocked": true,
  "unlock_reason": null,
  "retry_question_count": 0,
  "checkpoint_passed": false
}
```

`unlock_reason` is `prerequisite_not_proficient` for a locked lesson. The first N1 lesson is unlocked by default. The backend rejects attempts to bypass a lock with `409 lesson_locked`.

`GET /api/v1/learning-home` supplies the server-recommended action. New action types are:

- `retry_practice` (including remediation for missed checkpoint questions)
- `start_checkpoint`
- `resume_checkpoint`
- `course_complete`

The frontend should use `next_action.href`, `lesson_key`, `unit_key`, and `session_id` rather than infer the next screen from percentages.

## Frontend integration

Generated TypeScript contracts live in `apps/web/src/lib/api/schema.d.ts`. The stable helper functions are in `apps/web/src/lib/api/practice.ts`:

```ts
createPracticeSession(lessonKey, questionCount?, accessToken?)
createRetryReviewSession(lessonKey, questionCount?, accessToken?)
createCheckpointSession(unitKey, accessToken?)
getPracticeSession(sessionId, accessToken?)
getNextQuestion(sessionId, accessToken?)
submitAttempt(sessionId, questionKey, revision, answers, accessToken?)
```

The same question player can render all three modes. It should vary its controls from `session.mode`:

| Mode | Hints | Give up | Wrong-answer behavior |
|---|---|---|---|
| `guided_practice` | Show | Show after server permits | Keep question active until correct or given up |
| `retry_review` | Show | Show after server permits | Same as guided practice |
| `checkpoint` | Hide | Hide | Advance after the first submitted attempt |

For a completed checkpoint, refresh `/api/v1/progress` or `/api/v1/learning-home`. Do not derive a pass from local answer state. This also handles refresh, another browser tab, and replayed requests correctly.

The current frontend remains a placeholder. It does not need lesson videos to use these endpoints, and the final Figma implementation can replace its components while keeping these generated types and helpers.

## Persistence and evidence

SQLite development adds:

- `learner_checkpoint_sessions`
- `learner_mastery_events`
- `incorrect` session-question status

PostgreSQL uses the existing learner and practice tables plus migration:

```text
supabase/migrations/202609260006_checkpoint_mastery_retry.sql
```

Mastery evidence is append-only. The adapters write:

- `lesson_proficient` when a completed lesson practice first satisfies policy.
- `checkpoint_passed` when a completed checkpoint satisfies policy.
- `lesson_mastered` for the unit promotion caused by that checkpoint.

Database triggers reject updates and deletes to mastery events.

## Deployment order

1. Apply all Supabase migrations through `202609260006_checkpoint_mastery_retry.sql`.
2. Import the validated question bank and course snapshot using the existing import commands.
3. Deploy the learning API.
4. Regenerate or consume the committed OpenAPI TypeScript client.
5. Deploy the web app with its existing authenticated same-origin gateway.
6. Exercise one invited student through lesson practice, retry, checkpoint failure, checkpoint retake, and checkpoint pass.

Run migration validation against an empty disposable PostgreSQL database before applying it to the hosted project:

```bash
DATABASE_URL=postgresql://... bash scripts/validate_migrations.sh
```

Then run the PostgreSQL behavior suite:

```bash
TEST_DATABASE_URL=postgresql://... \
  uv run --project services/learning_api --locked \
  pytest services/learning_api/tests/test_postgres_stage4.py
```

Without `TEST_DATABASE_URL`, the PostgreSQL-only tests skip; SQLite still covers the same progression behavior locally.

## Expected errors for frontend handling

| Code | HTTP | Meaning |
|---|---:|---|
| `lesson_locked` | 409 | A prerequisite lesson is not proficient. |
| `retry_queue_empty` | 409 | No unresolved question exists for the selected lesson. |
| `checkpoint_locked` | 409 | Not every lesson in the unit is proficient. |
| `checkpoint_already_passed` | 409 | The checkpoint and unit are already mastered. |
| `invalid_checkpoint_question_count` | 400 | A client tried to override the authored checkpoint size. |
| `checkpoint_support_locked` | 403 | A hint or Give up was requested during a checkpoint. |
| `practice_session_not_owned` | 404 | The authenticated learner does not own the session. |

Render the API's user-safe `message`, then refresh learning-home state. Do not unlock controls in response to a client-side guess.

## Verification scope

Automated coverage includes:

- prerequisite lesson and checkpoint locks;
- targeted retry selection;
- checkpoint hint and Give up rejection;
- one-attempt checkpoint answers;
- failed checkpoint and retake;
- passing threshold and unit mastery;
- immutable SQLite mastery evidence;
- PostgreSQL ownership, idempotency, passing mastery, and immutable evidence when a disposable database is configured;
- generated OpenAPI/TypeScript compatibility.
