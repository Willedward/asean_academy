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

To import a valid draft or reviewed bank into a database after applying the Supabase migration:

```bash
uv sync --extra postgres
DATABASE_URL=postgresql://... uv run question-bank import-db
```

Import is transactional. Existing question revisions are immutable: changing assessed content requires incrementing the question's `revision`.
