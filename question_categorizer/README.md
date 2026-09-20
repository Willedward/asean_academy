# Question categorizer

Local, reviewable classification of OCR-extracted Mathematics questions into the
fixed syllabus codes supplied for ASEAN Academy (`N1`, `N2`, `G1`, and so on).

The categorizer uses deterministic phrases, mathematical notation and structural
signals. It does not call GPT, use a vision API, or require a vector database.
Uncertain questions remain `unclassified`. All machine assignments are
`suggested`; a human or a future classifier that passes the golden-set gate must
confirm them before they control student-visible ordering.

## Install and run

```bash
uv sync --project question_categorizer --group dev
uv run --project question_categorizer question-categorize categorize \
  ocr_extractor/output/hybrid-refined/c2b033b0-a276-526d-8594-783c56d38d0f/6126d14aa7b9b92b43f73606/questions.json \
  --source-level secondary_2
```

The command writes `categorization.json` beside the OCR export and persists to
`question_categorizer/output/categorizations.sqlite3`. Use `--json-only` to skip
database persistence, `--database PATH` for another SQLite file, or `--postgres`
with `DATABASE_URL` for PostgreSQL.

```bash
uv run --project question_categorizer question-categorize init-db \
  --database question_categorizer/output/categorizations.sqlite3
uv run --project question_categorizer --extra postgres question-categorize init-db --postgres
```

Print the bundled taxonomy or result schema:

```bash
uv run --project question_categorizer question-categorize taxonomy
uv run --project question_categorizer question-categorize schema
```

Confirm a reviewed assignment without allowing later reruns to overwrite it:

```bash
uv run --project question_categorizer question-categorize confirm ASSIGNMENT_UUID \
  --reviewer william --database question_categorizer/output/categorizations.sqlite3
```

Use the review command when the assignment should instead be rejected:

```bash
uv run --project question_categorizer question-categorize review ASSIGNMENT_UUID \
  --decision rejected --reviewer william \
  --database question_categorizer/output/categorizations.sqlite3
```

## Processing rules

1. Read an OCR extractor `questions.json`.
2. Use the latest review revision only when its decision is `checked`; otherwise
   classify machine OCR only as a suggestion. Skip rejected questions.
3. Split `(i)`, `(ii)`, `(a)` and similar subparts. Each part receives its own
   stable ID and assignments.
4. Match fixed local rules and record every phrase, notation and level signal.
5. Return one primary topic and optional secondary topics. A close tie or weak
   score becomes `unclassified`.
6. Store the taxonomy version, classifier version, confidence, evidence and source
   fingerprint with every run. The score and ambiguity thresholds are also part
   of the deterministic run ID, so differently configured runs retain separate
   histories.

The taxonomy is deliberately marked `g3_math_v1_draft`: the supplied images cover
the Secondary One and Two subset. Concepts absent from it, such as the circle
theorem question in Beasiswa, remain unclassified until the complete official
syllabus is imported and founder-checked.

## Database tables

- `syllabus_versions`
- `syllabus_topics`
- `syllabus_outcomes`
- `categorization_runs`
- `question_categorizations`
- `question_parts`
- `question_topics`

PostgreSQL tables live in the `question_categorizer` schema. Confirmed or rejected
assignments survive a deterministic rerun; only machine suggestions for that run
are replaced.

## Tests

```bash
uv run --project question_categorizer --group dev pytest question_categorizer/tests
uv run --project question_categorizer --group dev ruff check \
  question_categorizer/src question_categorizer/tests
```
