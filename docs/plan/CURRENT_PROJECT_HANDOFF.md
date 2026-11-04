# Current project handoff

Updated: 3 November 2026 (Asia/Singapore)

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
- E9.2-E9.4 are merged through integration commit `1c3c49f` from PR #234.
- E1.2 is merged there at implementation commit `a382f84` from PR #235.
- E1.4 is merged there through integration commit `90379c2` from PR #237.
- The verified E1.5 starting baseline is integration commit `fe258595` from PR #256; hosted
  API and web reported that exact SHA with current schema/content before implementation.
- E1.5 is merged there at implementation commit `c3e6343` through integration commit
  `d2906581` from PR #262.
- The verified E2.3 starting baseline is integration commit `23490ca` from PR #263; hosted
  API and web reported that exact SHA with current schema/content before implementation.
- E2.3 is merged there at implementation commit `dd1bb5b` through integration commit
  `9ea8d059` from PR #269.
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

## E9.2 narrative-writing milestone

- E9.2 is implemented as draft-only Full-route content with one seven-section lesson and one
  six-decision deterministic composition-planning exit ticket.
- The lesson teaches learners to confirm that a prompt permits a story, build a causal
  situation–conflict–pressure–turning-point–resolution route, select purposeful detail and end
  with a bounded consequence rather than a coincidence rescue or generic moral.
- The new source records are `e9-lesson-02`, `ex-l2-013` and review batch
  `english-ex-b035`. English and editorial decisions remain pending; nothing is published.
- E9.2 is Full-route only. It does not change the fixed 121-record Sprint review scope or any
  protected baseline, endline, checkpoint or mock form.

## E9.3 opinion-and-discursive-writing milestone

- E9.3 is implemented as draft-only Full-route content with one seven-section lesson and one
  six-decision deterministic composition-planning exit ticket.
- The lesson teaches precise task-form checking, a qualified defensible position, complete
  claim–detail–explanation–significance chains, fair counterargument and concession-response.
- The practice record is explicitly fictional and cannot be presented as research evidence.
  Unsupported statistics, universal outcomes, straw-man objections and false balance are
  rejected by the deterministic feedback.
- The new source records are `e9-lesson-03`, `ex-l3-004` and review batch
  `english-ex-b036`. English and editorial decisions remain pending; nothing is published.
- E9.3 is Full-route only and does not change the fixed 121-record Sprint review scope or any
  protected form.

## E9.4 process-compression milestone

- E9.4 is implemented as draft-only Full-route content with one seven-section lesson and one
  six-decision deterministic composition-planning exit ticket.
- The lesson fades support from a 45-minute diagnostic rehearsal to a 35-minute reduced-support
  rehearsal and then a fresh 30-minute independent run. Every stage protects task fit, a compact
  plan, a complete ending and a meaning-first checking buffer.
- Advancement depends on complete, uncontaminated process evidence rather than speed or word
  count alone. Repeating an exposed prompt is not treated as proof of transfer, and a formative
  run is never presented as an official score or admission prediction.
- The new source records are `e9-lesson-04`, `ex-l4-007` and review batch
  `english-ex-b037`. English and editorial decisions remain pending; nothing is published.
- E9.4 is Full-route only and does not change the fixed 121-record Sprint review scope or any
  protected form.

## E1.2 word-class-and-family milestone

- E1.2 is implemented as draft-only Core-route content with one seven-section lesson, six
  deterministic guided/independent/exit-ticket questions and one disjoint parallel retry.
- The lesson teaches learners to identify a noun, verb, adjective or adverb slot before choosing
  among related forms, then confirm meaning and collocation in the complete sentence.
- Suffixes and sentence frames are treated as evidence rather than universal rules. The retry
  uses a fresh word family so an exposed answer is not mistaken for transfer.
- The new source records are `e1-lesson-02`, `ev-l2-001` through `ev-l2-007`, and review
  batches `english-ev-b009` and `english-ev-b010`. English and editorial decisions remain
  pending; nothing is published.
- E1.2 is Core-route but not Sprint-route content. It does not change the fixed 121-record
  Sprint review scope, existing E1 Sprint checkpoint mastery scope or any protected form.

## E1.4 synonym-precision milestone

- E1.4 is implemented as draft-only Core-route content with one seven-section lesson, six
  deterministic guided/independent/exit-ticket questions and one disjoint parallel retry.
- The lesson separates a near-synonym's core meaning, degree and attitude before requiring a
  complete-sentence check. A familiar or dramatic option is rejected when it changes the
  supported fact, exaggerates intensity or imports unsupported praise or criticism.
- The new source records are `e1-lesson-04`, `ev-l4-001` through `ev-l4-007`, and review
  batches `english-ev-b011` and `english-ev-b012`. English and editorial decisions remain
  pending; nothing is published.
- E1.4 is Core-route but not Sprint-route content. It does not change the fixed 121-record
  Sprint review scope, existing E1 Sprint checkpoint mastery scope or any protected form.

## E1.5 collocation-and-register milestone

- E1.5 is implemented as draft-only Core-route content with one seven-section lesson, six
  deterministic guided/independent/exit-ticket questions and one disjoint parallel retry.
- The lesson requires four checks: intended meaning, natural word partnership, audience and
  complete sentence. It treats neutral language as a valid register, rejects artificial
  formality and does not reward a familiar word when its grammatical partnership is wrong.
- The new source records are `e1-lesson-05`, `ev-l5-008` through `ev-l5-014`, and review
  batches `english-ev-b013` and `english-ev-b014`. English and editorial decisions remain
  pending; nothing is published.
- E1.5 is Core-route but not Sprint-route content. It does not change the fixed 121-record
  Sprint review scope, E1 checkpoint mastery scope or protected `ev-l5-006`/`ev-l5-007`
  records.

## Validation completed for E1.5

- English foundation and authoring validation: 42 authored lessons, 126 questions, 86 review
  batches and zero duplicate/template collisions. Full/Core/Sprint authored coverage is
  42/28/16, with 19/19/16 disjoint parallel-retry records respectively.
- Question-bank suite: 183 passed. Learning API suite: 278 passed, with 22 opt-in PostgreSQL
  tests skipped in the non-DB run. Ruff passed for both Python projects.
- Web generated-contract check, lint, TypeScript and 150 tests passed; the webpack production
  build passed across 204 generated static pages. The local Turbopack build stalled without an
  error and was stopped; both PR and exact post-merge CI passed the configured Turbopack build.
- A fresh disposable PostgreSQL database accepted the complete migration chain through
  `202611020047`, imported 1,040 mathematics questions, 126 English questions and 37 passages,
  and passed bootstrap preview/apply/repeat idempotency. All seven `EV1.5` questions remained
  draft and the two protected E1 checkpoint records were unchanged.
- Migration safety passed. No new schema migration was required because E1.5 uses the existing
  objective-question, learning-session and content-review contracts. No provider call or paid
  token was used.
- PR #262 and the exact post-merge integration run passed every reviewer, web, API, PostgreSQL
  and authenticated-browser gate. At milestone merge, Render API readiness and the web proxy
  reported integration SHA `d2906581ab37f02d82b54f68ab4e3c96c6981489`, required schema
  `202611020047`, and current database schema/content; the hosted login returned HTTP 200.

## E2.3 tense-and-aspect milestone

- E2.3 is implemented as draft-only Core-route content with one seven-section lesson, six
  deterministic guided/independent/exit-ticket questions and one disjoint parallel retry.
- The lesson uses an `Anchor -> Order -> View -> Verify` routine. Learners identify the time
  reference, order events, distinguish habit/completion/progress/continuing result, and reread
  the complete timeline rather than mechanically matching the nearest verb.
- The new source records are `e2-lesson-03`, `eg-l3-001` through `eg-l3-007`, and review
  batches `english-eg-b005` and `english-eg-b006`. English and editorial decisions remain
  pending; nothing is published.
- E2.3 is Core-route but not Sprint-route content. It does not change the fixed 121-record
  Sprint review scope, E2 checkpoint mastery scope or any protected form.

## Validation completed for E2.3

- English foundation and authoring validation: 43 authored lessons, 133 questions, 88 review
  batches and zero duplicate/template collisions. Full/Core/Sprint authored coverage is
  43/29/16, with 20/20/16 disjoint parallel-retry records respectively.
- Question-bank suite: 185 passed. Learning API suite: 279 passed, with 22 opt-in PostgreSQL
  tests skipped in the non-DB run. Ruff passed for both Python projects.
- Web generated-contract check, lint, TypeScript and 150 tests passed; the webpack production
  build passed across 204 generated static pages. The local Turbopack build stalled without an
  error and was stopped; both PR runs and a complete later integration run containing E2.3
  passed the configured Turbopack build.
- A fresh disposable PostgreSQL database accepted the complete migration chain through
  `202611020047`, imported 1,040 mathematics questions, 133 English questions and 37 passages,
  and passed repeated bootstrap idempotency. All seven `EG2.3` records remained current drafts
  in their intended guided, independent, exit and retry pools.
- Migration safety passed. No new schema migration was required because E2.3 uses the existing
  objective-question, learning-session and content-review contracts. No provider call or paid
  token was used.
- PR #269 passed every reviewer, web, API, PostgreSQL and authenticated-browser gate before
  merge. Integration run `41614042202` at `b303254f383e6033c7151ac5773fa297ee2f88c0`,
  which contains E2.3, then passed all four required post-merge jobs; later integration run
  `41615226913` at `7db46c48c588db94e2cd7bb4223604cb235249b1` also passed after one
  flaky web-test teardown rerun.
- Render API readiness and the web proxy reported exact containing integration SHA
  `7db46c48c588db94e2cd7bb4223604cb235249b1`, required schema `202611020047`, and
  current database schema/content; the hosted login returned HTTP 200.

## Validation completed for E1.4

- English foundation and authoring validation: 41 authored lessons, 119 questions, 84 review
  batches and zero duplicate/template collisions. Full/Core/Sprint authored coverage is
  41/27/16, with 18/18/16 disjoint parallel-retry records respectively.
- Question-bank suite: 181 passed. Learning API suite: 277 passed, with 22 opt-in PostgreSQL
  tests skipped in the non-DB run.
- Web generated-contract check, lint, TypeScript and 150 tests passed; the webpack production
  build passed across 204 generated static pages. The local Turbopack build stalled without an
  error and was stopped; hosted CI must independently pass the configured build before merge.
- A fresh disposable PostgreSQL database accepted the complete migration chain through
  `202611020047`, imported 1,040 mathematics questions, 119 English questions and 37 passages,
  and passed bootstrap preview/apply/repeat idempotency. All seven `EV1.4` questions remained
  draft.
- Migration safety passed. No new schema migration was required because E1.4 uses the existing
  objective-question, learning-session and content-review contracts.

## Validation completed for E1.2

- English foundation and authoring validation: 40 authored lessons, 112 questions, 82 review
  batches and zero duplicate/template collisions. Full/Core/Sprint authored coverage is
  40/26/16, with 17/17/16 disjoint parallel-retry records respectively.
- Question-bank suite: 179 passed. Learning API suite: 276 passed, with 22 opt-in PostgreSQL
  tests skipped in the non-DB run.
- Web generated-contract check, lint, TypeScript and 150 tests passed; the webpack production
  build passed across 204 generated static pages. The local Turbopack build stalled without an
  error and was stopped; both PR and post-merge CI passed the configured production build.
- A fresh disposable PostgreSQL database accepted the complete migration chain through
  `202611020047`, imported 1,040 mathematics questions, 112 English questions and 37 passages,
  and passed bootstrap preview/apply/repeat idempotency. All seven `EV1.2` questions remained
  draft.
- Migration safety passed. No new schema migration was required because E1.2 uses the existing
  objective-question, learning-session and content-review contracts.
- PR #235 and the exact post-merge integration CI run passed every web, API, PostgreSQL and
  authenticated-browser gate. At milestone merge, Render API readiness and the web API proxy
  reported integration SHA `e85b8e041d3f859886496038b43ea2f309564e96`, required schema
  `202611020047`, and current database schema/content; the hosted root and login returned 200.

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

## Validation completed for E9.2

- English foundation and authoring validation: 37 authored lessons, 103 questions, 78 review
  batches and zero duplicate/template collisions.
- Question-bank suite: 173 passed. Learning API suite: 273 passed, with 22 opt-in PostgreSQL
  tests skipped in the non-DB run.
- Web generated-contract check, lint, TypeScript and 150 tests passed; the webpack production
  build passed.
- A fresh disposable PostgreSQL database accepted the complete migration chain through
  `202611020047`, imported 1,040 mathematics questions, 103 English questions and 37 passages,
  and passed bootstrap preview/apply/repeat idempotency. E9.2 and `ex-l2-013` remained draft.
- No new schema migration was required because E9.2 uses the existing composition-planning and
  content-review contracts.

## Validation completed for E9.3

- English foundation and authoring validation: 38 authored lessons, 104 questions, 79 review
  batches and zero duplicate/template collisions.
- Question-bank suite: 175 passed. Learning API suite: 274 passed, with 22 opt-in PostgreSQL
  tests skipped in the non-DB run.
- Web generated-contract check, lint, TypeScript and 150 tests passed; the webpack production
  build passed.
- A fresh disposable PostgreSQL database accepted the complete migration chain through
  `202611020047`, imported 1,040 mathematics questions, 104 English questions and 37 passages,
  and passed bootstrap preview/apply/repeat idempotency. E9.3 and `ex-l3-004` remained draft.
- No new schema migration was required because E9.3 uses the existing composition-planning and
  content-review contracts.

## Validation completed for E9.4

- English foundation and authoring validation: 39 authored lessons, 105 questions, 80 review
  batches and zero duplicate/template collisions.
- Question-bank suite: 177 passed. Learning API suite: 275 passed, with 22 opt-in PostgreSQL
  tests skipped in the non-DB run.
- Web generated-contract check, lint, TypeScript and 150 tests passed; the webpack production
  build passed.
- A fresh disposable PostgreSQL database accepted the complete migration chain through
  `202611020047`, imported 1,040 mathematics questions, 105 English questions and 37 passages,
  and passed bootstrap preview/apply/repeat idempotency. `EW9.4` and `ex-l4-007` remained draft.
- Migration safety passed. No new schema migration was required because E9.4 uses the existing
  composition-planning and content-review contracts.

## Immediate next milestone

The next operational step requires people, not more provider code: a qualified English educator
must execute the private ENG-T3.9 package against already-captured outputs, and the responsible
privacy/safeguarding owners must record genuine T3.10 evidence. Do not enable Render or invoke a
paid provider until those gates pass.

The next independently executable content sequence now moves to mock forms and the open audit
findings; all 51 lessons are authored as drafts, alongside the existing Sprint human
review and publication evidence. Human
English/editorial curriculum review is separate from essay-feedback calibration and is never
replaced by it.

## Authoritative references

- `docs/plan/LAYER_1_ENGLISH_FOUNDATION_EXECUTION.md`
- `docs/plan/LAYER_1_ENGLISH_V3_SCALABLE_PLAN.md`
- `docs/plan/LAYER_1_ENGLISH_V3B_ROUTE_BLUEPRINT.md`
- `docs/plan/ENGLISH_ESSAY_CALIBRATION_GATE.md`
- `docs/plan/ENGLISH_ESSAY_LIVE_RELEASE_GATE.md`
- `docs/plan/CONTENT_REVIEW_PUBLICATION.md`
- `apps/web/src/beta-kit/HANDOFF.md`
