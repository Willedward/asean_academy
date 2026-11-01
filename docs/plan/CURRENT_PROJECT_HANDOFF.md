# Current project handoff

Updated: 2 November 2026 (Asia/Singapore)

This is the short restart file for a new Codex or collaborator session. Read it before loading
the larger plans; do not use the full chat transcript as project state.

## Product boundary

NextScholar prepares students in Indonesia and Southeast Asia for the ASEAN Scholarship
selection tests. Layer 1 is Mathematics and English. XP, streaks, leaderboards and a
personalised planner remain Layer 2. Draft content must not reach learners until the existing
review and publication gates pass.

## Git and working state

- Integration branch: `feature/bulk-question-authoring-pipeline`.
- ENG-T3.8 is merged there at integration commit `02f7173` from PR #228.
- ENG-T3.9 is implemented on `feature/english-essay-calibration-gate` in the isolated
  worktree `/private/tmp/nextscholar-english-calibration`.
- Do not overwrite unrelated work in the user's main checkout.

## English essay milestones

- ENG-T3.1–T3.9: implemented as draft.
- ENG-T3.8 adds schema revision `202611010045`, owned submission history, feedback pinned to
  the exact immutable submission and rubric, exact evidence quotes, and one immutable learner
  usefulness response.
- ENG-T3.9 adds schema revision `202611010046`, a source-controlled bounded-calibration
  policy, an offline evaluator for 12–16 private educator anchors with two captured runs each,
  explicit quality/safety/cost/latency thresholds and immutable privacy-safe aggregate gate
  reports. Raw essays and provider responses stay outside Git and the gate table.
- A passing calibration report is evidence only: it always records
  `live_provider_released=false`. No real educator/provider report has been fabricated or
  recorded; that private execution and the explicit release decision remain gated.
- The learner contract intentionally excludes provider/model names, token use and cost data.
- Preparation estimates are formative guidance, never official scores or selection outcomes.
- Live provider invocation and paid calls remain disabled; Render now states this explicitly.

## Validation completed for ENG-T3.9

- Learning API suite: 267 passed; 21 opt-in PostgreSQL tests skipped in the non-DB run.
- Web test suite: 148 passed; web lint, TypeScript and webpack production build passed.
- Full PostgreSQL migration chain and validated content import through `202611010046`: passed
  on a disposable database.
- The existing full English essay PostgreSQL regression and the new calibration privacy,
  idempotency and immutability test passed.
- Migration safety check: passed.

## Immediate next milestone

**ENG-T3.10 — administrator evidence, privacy checks and explicit live-provider release
gate.** Use a qualified English educator to execute the private ENG-T3.9 package against
already-captured candidate outputs, store only its privacy-safe report, expose evidence to
authorised administrators, complete consent/retention/provider/privacy checks and require a
separate explicit release decision. Any missing or failed evidence must keep the provider off.
Human English/editorial review of curriculum content continues in parallel and is not replaced
by essay-feedback calibration.

## Authoritative references

- `docs/plan/LAYER_1_ENGLISH_FOUNDATION_EXECUTION.md`
- `docs/plan/LAYER_1_ENGLISH_V3_SCALABLE_PLAN.md`
- `docs/plan/LAYER_1_ENGLISH_V3B_ROUTE_BLUEPRINT.md`
- `docs/plan/ENGLISH_ESSAY_CALIBRATION_GATE.md`
- `docs/plan/CONTENT_REVIEW_PUBLICATION.md`
- `apps/web/src/beta-kit/HANDOFF.md`
