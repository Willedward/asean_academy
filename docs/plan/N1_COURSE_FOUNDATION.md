# N1 course foundation

This document records the first implementation step from `PLAN_V2.md`. The work lives on
`feature/n1-course-foundation` and provides versioned course contracts, the complete N1 course
map, draft lesson shells, question-pool allocation, validation, preview, and PostgreSQL import.

## Authored source

The source of truth is:

```text
backend_resources/courses/g3_math/secondary_1/n1/v1/
├── course.json
├── question_pools.json
└── lessons/
    ├── n1-lesson-01.json
    └── ... n1-lesson-07.json
```

`course.json` defines the course, N1 unit, ordered lessons, and the versioned mastery policy.
Each lesson file owns its objectives, prerequisites, sections, assets, status, and review
provenance. `question_pools.json` allocates all 40 existing questions once:

| Use | Questions |
|---|---:|
| Lesson practice | 19 |
| Unit checkpoint candidate pool | 11 |
| Adaptive reserve | 10 |
| Total | 40 |

The course is intentionally a draft. Empty section lists make the lesson shells easy to review,
but the publication validator rejects them until their explanations, worked examples, active
recall, and summaries have been authored and reviewed.

## Local review

From `question_bank`:

```bash
uv sync
uv run question-bank course-validate
uv run question-bank course-preview
```

Open <http://127.0.0.1:8767>. The preview shows the lesson order, objectives, prerequisites,
practice stages, pool sizes, and remaining publication warnings. It does not expose question
answers.

Run the strict publication gate separately:

```bash
uv run question-bank course-validate --publish
```

That command is expected to fail while any course, lesson, or question is still a draft.

## PostgreSQL import order

Apply the migrations in timestamp order:

1. `202609200001_n1_question_bank.sql`
2. `202609200002_practice_sessions.sql`
3. `202609200003_course_content.sql`

Then import the question bank before the course because pool items reference imported question
identities:

```bash
cd question_bank
uv sync --extra postgres
DATABASE_URL=postgresql://... uv run question-bank import-db
DATABASE_URL=postgresql://... uv run question-bank course-import-db
```

Both imports are transactional. Course and lesson hashes prevent an existing revision from being
silently overwritten. Review-state promotion can keep the same revision because it does not alter
the learner-visible content; a content change requires a new revision.

## Adopted defaults

The initial data uses the recommendations in `PLAN_V2.md`:

- 70% eventual-correctness proficiency threshold.
- 70% checkpoint pass threshold.
- Eight unseen questions drawn from the eleven-question checkpoint pool.
- Two committed incorrect attempts before Give up.
- Hint use is recorded without reducing marks.
- Course content is authored as versioned JSON in Git and imported transactionally.

The final frontend can replace the local preview because these files and the later `/api/v1`
contract own the learning structure. Visual components should not calculate mastery, unlocks, or
question eligibility.

## Next implementation step

Stage 3 starts with `n1-lesson-01`. It needs complete learning sections and an academic review of
the six outcome-1.1 questions. After that content exists, the production API can expose the course
map and Lesson 1, and the placeholder student screen can consume the same DTOs as the final
frontend.
