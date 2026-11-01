# Current project handoff

Updated: 1 November 2026 (Asia/Singapore)

This is the short restart file for a new Codex or collaborator session. Read it before loading
the larger plans; do not use the full chat transcript as project state.

## Product boundary

NextScholar prepares students in Indonesia and Southeast Asia for the ASEAN Scholarship
selection tests. Layer 1 is Mathematics and English. XP, streaks, leaderboards and a
personalised planner remain Layer 2. Draft content must not reach learners until the existing
review and publication gates pass.

## Git and working state

- Integration branch: `feature/bulk-question-authoring-pipeline`.
- ENG-T3.7 is already merged there at base commit `1b61df5`.
- ENG-T3.8 is implemented on `feature/english-essay-feedback-report` in the isolated worktree
  `/private/tmp/nextscholar-english-feedback-report`.
- Do not overwrite unrelated work in the user's main checkout.

## English essay milestones

- ENG-T3.1–T3.8: implemented as draft.
- ENG-T3.8 adds schema revision `202611010045`, owned submission history, feedback pinned to
  the exact immutable submission and rubric, exact evidence quotes, and one immutable learner
  usefulness response.
- The learner contract intentionally excludes provider/model names, token use and cost data.
- Preparation estimates are formative guidance, never official scores or selection outcomes.
- Live provider invocation remains disabled.

## Validation already completed for ENG-T3.8

- Focused and related API tests: 110 passed.
- Web test suite: 148 passed; web lint and TypeScript checks passed.
- Full PostgreSQL migration chain through `202611010045`: passed on a disposable database.
- PostgreSQL integration tests: 10 passed, including history, exact report ownership,
  idempotency and database-level immutability.
- Migration safety check: passed.

## Immediate next milestone

**ENG-T3.9 — human-anchor calibration and provider quality/safety gate.** Create a small,
bounded educator-anchor set; compare the disabled provider candidate on evidence fidelity,
instructional usefulness, false claims and safety; define explicit release thresholds; and
keep learner/provider invocation off when any gate fails. This is calibration infrastructure,
not mass manual review.

After ENG-T3.9, complete ENG-T3.10 administrator evidence, privacy checks and the explicit
live-provider release gate. Human English/editorial review of curriculum content continues in
parallel and is not replaced by essay-feedback calibration.

## Authoritative references

- `docs/plan/LAYER_1_ENGLISH_FOUNDATION_EXECUTION.md`
- `docs/plan/LAYER_1_ENGLISH_V3_SCALABLE_PLAN.md`
- `docs/plan/LAYER_1_ENGLISH_V3B_ROUTE_BLUEPRINT.md`
- `docs/plan/CONTENT_REVIEW_PUBLICATION.md`
- `apps/web/src/beta-kit/HANDOFF.md`
