# Five-level mathematics difficulty model

## Decision

All G3 Mathematics question banks use the same five-level authoring scale. Difficulty describes the reasoning demand of a question. It is not a permanent label for a learner and must not be inferred only from the number of steps or marks.

| Level | Authoring definition |
| --- | --- |
| 1 | Direct recall or one familiar taught step with little interpretation. |
| 2 | Routine application using one or two linked steps in a familiar representation. |
| 3 | Multi-step application or interpretation requiring a routine choice of method. |
| 4 | An unfamiliar problem requiring method selection, constraints, or justification. |
| 5 | Complex non-routine synthesis requiring several ideas, sustained reasoning, or proof. |

Reviewers should judge the complete question as seen by the learner. More arithmetic alone does not make a question Level 4 or 5. Scaffolding, familiar wording, diagrams, and explicit method prompts can lower the effective demand.

## Practice-stage policy

The practice stages intentionally overlap:

| Stage | Allowed levels |
| --- | --- |
| Guided | 1–2 |
| Independent | 2–4 |
| Challenge | 3–5 |
| Checkpoint | 1–5, constrained by its own blueprint |
| Adaptive/retry reserve | 1–5, selected from learner evidence |

The overlap lets a Level 2 question close guided practice or open independent practice, and lets existing Level 3 N1 challenge questions remain valid. Stage is a teaching role; difficulty is a content property.

## Backward compatibility

The original N1 pilot remains a 40-question bank with the distribution `15/15/10/0/0`. No stable key, revision, answer specification, or learner attempt changes. Existing Level 1–3 records satisfy the expanded database constraint.

Every blueprint now declares all five keys, including zero counts. New files use stable keys containing `l1` through `l5`. The JSON Schema, Pydantic contracts, learning API, PostgreSQL practice selector, and admin analytics filter accept only integer levels 1–5.

## Database migration

`202609300016_five_level_difficulty.sql` performs an additive transition:

1. Backfill missing `4` and `5` bank distribution keys with zero.
2. Require all five distribution keys on future bank rows.
3. Add and validate a `1 <= difficulty <= 5` question constraint.
4. Remove the superseded `1 <= difficulty <= 3` constraint only after validation succeeds.

Apply the migration before importing a bank that contains Level 4 or Level 5 questions. A rollback should first confirm that no rows use those levels; otherwise reducing the allowed range would discard valid new content.

## Content-production rule

Each topic blueprint chooses its distribution from syllabus weight, question purpose, and review evidence. Do not force equal fifths. Before bulk generation, reviewers should calibrate a small batch containing adjacent levels and record disagreements. Diagnostic forms use their own balanced blueprint and never reuse exposed practice questions.
