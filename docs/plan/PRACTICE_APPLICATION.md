# N1 practice application slice

This slice proves the student practice workflow while the final frontend is being designed. The durable boundary is the JSON API and question content contract. The included browser page is a replaceable localhost client.

## Current behaviour

- Creates a practice session with a fixed target count and scope.
- Persists assigned question order, so refreshing does not change the question.
- Pins every assignment and attempt to the authored question revision.
- Selects required retries first, then unseen questions, then least-recently-attempted questions. Within a priority it balances difficulty and uses random tie-breaking.
- Returns question prompts without answer specifications or worked solutions.
- Uses the existing deterministic Python answer checker.
- Stores immutable, idempotent attempts in the local adapter.
- Reveals two hints in order.
- Unlocks Give up and the worked solution after two incorrect attempts.
- Persists local progress in SQLite.

The local adapter has one development learner. The PostgreSQL migration adds authenticated, per-student `practice_sessions`, `session_questions`, `attempts`, and `question_progress` tables for Supabase.

## Run locally

All N1 questions are currently drafts, so draft access must be enabled explicitly:

```bash
cd /home/william/asean_academy/question_bank
uv sync
uv run question-bank practice --development-drafts
```

Open <http://127.0.0.1:8766>. Local state is saved in `question_bank/practice-local.sqlite3`, which is ignored by Git. Delete that file when you deliberately want a fresh local learner.

Without `--development-drafts`, the application selects only `published` questions and currently returns an empty-content error. This prevents the prototype from treating unreviewed content as production-ready.

## API contract used by the placeholder

### Create a session

`POST /api/practice-sessions`

```json
{
  "question_count": 5,
  "difficulties": [1, 2, 3],
  "outcomes": []
}
```

### Get or resume the current question

`GET /api/practice-sessions/{sessionId}/next`

The response contains student-visible content blocks and input metadata. It never contains canonical answers, accepted alternatives, checker configuration, or solution steps.

### Reveal a hint

`POST /api/practice-sessions/{sessionId}/questions/{stableKey}/hints/{stage}`

Stage 1 must be opened before stage 2.

### Submit all parts

`POST /api/attempts`

```json
{
  "session_id": "uuid",
  "stable_key": "n1-l1-01",
  "revision": 1,
  "idempotency_key": "uuid-generated-by-the-client",
  "answers": {
    "1": "2^3 * 3^2 * 5"
  }
}
```

The same `(session_id, idempotency_key)` safely replays the first result instead of creating another attempt.

### Give up

`POST /api/practice-sessions/{sessionId}/questions/{stableKey}/give-up`

The endpoint returns the canonical answer and worked solution only after two incorrect attempts.

## Frontend replacement boundary

The placeholder is contained in `question_bank/practice_web.py`. A replacement Next.js or React frontend should render the same ordered content blocks:

- `text` as escaped text;
- `inline_math` and `display_math` through KaTeX or MathJax;
- `asset_ref` by matching `asset_key` against the question's public assets.

The frontend should keep `stable_key`, `revision`, and `session_id` opaque and send them back unchanged. Selection, answer checking, solution authorization, attempt numbering, and progress updates remain server responsibilities.

For local development on another frontend origin, prefer a Next.js same-origin route proxy to this API. Production will replace the SQLite adapter with the Supabase repository while keeping these response shapes.

## Work still requiring people or infrastructure

- A person must mathematically and editorially review each of the 40 draft questions before changing their status.
- Reviewed questions must be imported into PostgreSQL before the Supabase adapter can be enabled.
- Supabase Auth must supply the production `student_id`.
- The final frontend design and accessibility review can replace the placeholder without moving checking logic into the browser.
