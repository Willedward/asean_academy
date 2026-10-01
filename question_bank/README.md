# Authored question-bank tools

This package validates original question JSON, checks supported answers deterministically, provides a local reviewer preview, and imports reviewed versions into PostgreSQL. PDF OCR is a separate offline source pipeline and is not used when students request questions.

## Setup

```bash
cd /home/william/asean_academy/question_bank
uv sync
```

Validate the complete 40-question draft:

```bash
uv run question-bank validate
```

Run the local reviewer preview:

```bash
uv run question-bank preview --port 8765
```

Then visit <http://127.0.0.1:8765>. The preview includes KaTeX rendering, multipart inputs, deterministic answer checks, both hints, and worked solutions. It is a local author/reviewer tool and intentionally exposes answers.

Run the persistent student-practice prototype with the current draft content:

```bash
uv run question-bank practice --development-drafts
```

Then visit <http://127.0.0.1:8766>. This separate application hides answers, persists sessions and attempts in local SQLite, selects retries/unseen questions with difficulty balancing, reveals hints progressively, and unlocks Give up after two incorrect attempts. Its frontend is intentionally replaceable; the API contract and integration notes are in [`docs/plan/PRACTICE_APPLICATION.md`](../docs/plan/PRACTICE_APPLICATION.md).

Publication validation remains unsuccessful until all 40 draft questions receive human mathematical and editorial review:

```bash
uv run question-bank validate --publish
```

Validate the N1 course structure, seven lesson shells, and all 40 pool mappings:

```bash
uv run question-bank course-validate
```

Preview the draft course map at <http://127.0.0.1:8767>:

```bash
uv run question-bank course-preview
```

The six `lesson_content_required` warnings are expected while teaching sections for
Lessons 2–7 are authored and reviewed. Publication validation deliberately fails while course,
lesson, or question content remains in `draft` state:

```bash
uv run question-bank course-validate --publish
```

Regenerate the committed course-authoring JSON Schemas after changing a Pydantic contract:

```bash
uv run question-bank course-schema
```

To import a valid draft or reviewed bank into a database after applying the Supabase migration:

```bash
uv sync --extra postgres
DATABASE_URL=postgresql://... uv run question-bank import-db
DATABASE_URL=postgresql://... uv run question-bank course-import-db
```

Apply migrations `202609200001` through `202609200003` before importing. Import the question
bank first because course pools reference stable question identities. Imports are transactional.
Existing question, course, and lesson revisions are immutable: changed content requires an
incremented `revision`; review-state promotion may retain the same revision.

## Controlled bulk authoring

The bulk authoring workflow is model-independent. It creates all missing topic blueprints,
allocates unfinished banks into reviewable batches, validates provenance and generated content,
scans every bank for prompt duplicates, and exports reviewer packets:

```bash
uv run --project question_bank question-bank authoring-schema
uv run --project question_bank question-bank authoring-blueprints
uv run --project question_bank question-bank authoring-plan
uv run --project question_bank question-bank authoring-validate
```

A planned manifest contains an exact outcome/difficulty allocation of 20–30 questions and
reserves every stable question key. Claim it through the registry before changing its source.
On the exact claimed branch, replace the manifest's `unassigned` generator fields with the
actual provider/model, generator version, and prompt version, then change its status to `draft`.
Validation executes every canonical and accepted answer and checks the batch distribution and
assets.

Before editing a manifest or its reserved questions, register the owner and exact target branch:

```bash
uv run --project question_bank question-bank authoring-claim \
  g3-sec1-n2-b002 \
  --owner YOUR_GITHUB_USERNAME \
  --branch questions/g3-sec1-n2-b002-YOUR_GITHUB_USERNAME
```

Merge that small claim first, then create the named branch from the updated integration
branch. Pull requests verify the claim, restrict authoring changes to one batch, run the
aggregate validator and upload a reviewer packet. Release the claim after the batch merges:

```bash
uv run --project question_bank question-bank authoring-release \
  g3-sec1-n2-b002 --owner YOUR_GITHUB_USERNAME
```

See [`docs/plan/BULK_QUESTION_AUTHORING_PIPELINE.md`](../docs/plan/BULK_QUESTION_AUTHORING_PIPELINE.md)
for the lifecycle, repository layout, reviewer export command, and parallel Codex workflow.
The complete claim and CI workflow is in
[`docs/plan/MULTI_AUTHOR_QUESTION_PIPELINE.md`](../docs/plan/MULTI_AUTHOR_QUESTION_PIPELINE.md).
