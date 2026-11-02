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
- ENG-T3.9 is merged there at integration commit `fd1448d` from PR #229.
- ENG-T3.10 is merged there at implementation commit `33b1d412` from PR #230.
- Do not overwrite unrelated work in the user's main checkout.

## English essay milestones

- ENG-T3.1–T3.10: implemented as draft/fail-closed infrastructure.
- ENG-T3.8 adds schema revision `202611010045`, owned submission history, feedback pinned to
  the exact immutable submission and rubric, exact evidence quotes, and one immutable learner
  usefulness response.
- ENG-T3.9 adds schema revision `202611010046`, a source-controlled bounded-calibration
  policy, an offline evaluator for 12–16 private educator anchors with two captured runs each,
  explicit quality/safety/cost/latency thresholds and immutable privacy-safe aggregate gate
  reports. Raw essays and provider responses stay outside Git and the gate table.
- A passing calibration report is evidence only: it always records
  `live_provider_released=false`.
- ENG-T3.10 adds schema revision `202611020047`, an academic-admin evidence page, immutable
  privacy/safeguarding reviews, explicit release/suspension events and append-only guardian
  consent evidence using only an opaque SHA-256 reference.
- Provider availability requires current exact calibration, current privacy review, explicit
  release, environment enablement and unexpired learner consent. New evidence invalidates an
  older release. Missing or failed evidence keeps the provider off.
- No real educator/provider report, privacy approval, release or consent was fabricated or
  recorded. No provider call or paid token was used. Render remains explicitly disabled.
- The learner contract intentionally excludes provider/model names, token use and cost data.
- Preparation estimates are formative guidance, never official scores or selection outcomes.
- Live provider invocation and paid calls remain disabled; Render now states this explicitly.

## Validation completed for ENG-T3.10

- Learning API suite: 272 passed; 22 opt-in PostgreSQL tests skipped in the non-DB run.
- Web test suite: 150 passed; web lint, TypeScript and webpack production build passed.
- Full PostgreSQL migration chain and validated content import through `202611020047`: passed
  on a fresh disposable database (revision 21, 1,040 mathematics questions, 102 English
  questions, 37 passages).
- Existing essay-submission regression plus calibration and release-gate PostgreSQL tests:
  3 passed. They cover immutability, RLS grants, exact evidence coupling, consent expiry and
  account-deletion preview.
- Migration safety check: passed.
- PR #230 and the post-merge integration CI run passed every web, API, PostgreSQL and browser
  gate. Render API readiness and the web API proxy reported exact implementation SHA
  `33b1d412eaf2966cc6d2f953b2ebfa2eb2380296`, required schema `202611020047`, and current
  database schema/content; the hosted web login returned HTTP 200.

## Immediate next milestone

The next operational step requires people, not more provider code: a qualified English educator
must execute the private ENG-T3.9 package against already-captured outputs, and the responsible
privacy/safeguarding owners must record genuine T3.10 evidence. Do not enable Render or invoke a
paid provider until those gates pass.

The next independently executable content milestone is **E9.2 narrative writing**, alongside
the existing Sprint human review and publication evidence. Human English/editorial curriculum
review is separate from essay-feedback calibration and is never replaced by it.

## Authoritative references

- `docs/plan/LAYER_1_ENGLISH_FOUNDATION_EXECUTION.md`
- `docs/plan/LAYER_1_ENGLISH_V3_SCALABLE_PLAN.md`
- `docs/plan/LAYER_1_ENGLISH_V3B_ROUTE_BLUEPRINT.md`
- `docs/plan/ENGLISH_ESSAY_CALIBRATION_GATE.md`
- `docs/plan/ENGLISH_ESSAY_LIVE_RELEASE_GATE.md`
- `docs/plan/CONTENT_REVIEW_PUBLICATION.md`
- `apps/web/src/beta-kit/HANDOFF.md`
