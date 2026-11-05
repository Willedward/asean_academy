# Current project handoff

Updated: 5 November 2026 (Asia/Singapore)

This is the short restart file for a new Codex or collaborator session. Read it before loading
the larger plans; do not use the full chat transcript as project state.

## Start here: state on 5 November 2026

This section replaces the older status notes further down, which are kept as history. Where they
disagree, trust this section and the repo.

### What we are building towards

A beta pilot for the ASEAN Scholarship Sec 3-entry test: Indonesian applicants entering Secondary 3
in Singapore, tested at Sec 1-2 level in Mathematics and English. Both Sec 1 and Sec 2 Mathematics
and English are in the pilot, and the AI tutor is on.

### Decisions already made by William

Don't ask about these again.

- **Work order:** Mathematics batches, then the Mathematics diagrams, the two-course gate and the
  staging test. English fixes come after that, because Mathematics review starts first.
- **English in the pilot:** required, so the two-course gate stays as it is.
- **English level:** the same Sec 3-entry test as Mathematics, Sec 1-2 level. The paper has no
  editing questions and no "answer in your own words" questions. See
  `docs/plan/ENGLISH_LEVEL_REVIEW_SEC3_2026_11.md`.
- **Tutor:** Gemini only for the pilot, no premium routing. Model switching must stay easy for the
  full launch (see "Switching tutor models").
- **Content fix decisions** in `docs/plan/CONTENT_FIX_LEDGER.md`: D1 A, D2 A, D3 A, D4 B, D5 B, D6 B,
  D7 A, D8 C, D9 A. For D3, area and volume scale factors and standard form stay, with teaching;
  other flagged topics are rewritten in scope. D8 C means fix categories 1-3 now and do duplicates
  and the rest later.

### Rules that CI or the release process depend on

- PRs target `feature/bulk-question-authoring-pipeline`. `main` is 750+ commits behind and
  unprotected. The Render review site deploys the integration branch automatically once checks pass.
- A content PR changes exactly one claimed batch, on the exact branch
  `fix/<batch-id>-willedward`. `question-bank authoring-pr-check` enforces this; run it locally with
  `--changed-files`, `--head-branch` and `--output`.
- Bump `revision` on every changed question. Keep `status` as `draft`. Never record a Mathematics or
  editorial approval, because only human reviewers do that.
- Diagrams: keep the old SVG, add a revisioned file (`-r2`), and update `sha256` and
  `generation_spec`. Draw only through the checked generators in
  `question_bank/src/question_bank/diagrams/`. A stored template overrides the prompt, so a rewritten
  prompt keeps its old figure unless the template changes too.
- Never edit an existing migration, force-push a shared branch, commit secrets or learner data, or
  use paid LLM APIs for content.
- Check every changed item through `question_bank.checking.check_answer` with right and plausible
  wrong answers. Grep `services/learning_api/tests` for changed keys, because tests can assert on
  content.
- Known CI noise: a browser-journey "socket hang up" and a web job that fails after all its tests pass
  have both cleared on rerun. Read the log before assuming that.

### Done

- **Mathematics fixes:** categories 1-3 are merged for every batch on the fix list that has them
  (PRs #299-#361). All 19 Mathematics banks report 0 errors under `validate --strict-geometry`, and
  `catalogue-validate` and `authoring-validate` are clean (2,052 questions, 0 duplicate findings).
- **Diagrams:** checked figures for Sec 1 G1 and G5 and Sec 2 G2, G4 and G5.
- **Diagnostic:** connected to the Mathematics course. Students wait on human approval of its 76
  questions, which are imported to staging.
- **English:** all 51 lessons and both Section 1 mocks exist as drafts, retargeted to Sec 3 entry, with
  a learner mock runtime.
- **Release:** two-course gate (#313), single invitation (#280), Gemini-only tutor deploy settings.

### Still to do, in suggested order

1. **Staging test on the review site.** William signs in with Google, since this needs a person. Click
   through the review flow and a small review batch, a mock, and the tutor, including calibration.
   Never clicked through on hosted: the review flow, the mock, and #272, #274 and #277.
2. **Data charts.** Questions the ledger marks as needing a new diagram and which still have none: Sec 2
   S1 35, Sec 1 S1 32, Sec 2 N7 23, Sec 2 N6 8, Sec 2 S2 2. `g1-l4-011` and `g5-l3-011` (below) also have
   none. No chart generator exists yet.
   Adding a figure changes the question and cancels approvals, so finish these before those banks go
   to review.
3. **Start Mathematics review** using `docs/plan/MATH_REVIEWER_GUIDE.md`. Banks without pending charts
   can go first: G1, G2, G4, G5, N1-N5. Tell the reviewer which batches are ready.
4. **Mathematics items left open:**
   - Prompts: `g2-l3-530`, `g2-l4-512`, `g2-l5-503`.
   - CFL-530: `s1-l1-505`, `-515` and `-521` may have two right answers.
   - CFL-015: `g5-l3-011`, where any figure contradicts the prompt or the key. Rewording to "the
     smaller rectangle's 5 cm edge" already draws.
   - CFL-189: 13 N2 items in `g3-sec2-n2-b001`, `b003` and `b004` still say "exact numerical value only".
   - `g1-l5-004` hint leak; a `90°` answer is a format error in practice; `s1` lesson 06 diagram conflict.
   - CFL-026: codename prefixes remain on 77 Sec 2 S1 questions.
   - Lesson figures, including all five Sec 1 G5 lesson figures (D-22 to D-31).
5. **Checker changes that would let prompts mean what they say:** a lowest-terms option for numeric
   answers (CFL-180, 69 Sec 2 S2 parts, which D9 A needs, and CFL-177, where N1 prompts were reworded
   instead); requiring index notation on prime factorisation (CFL-181); promoting
   `content_control_character` in the lint policy.
6. **Later content passes:** categories 4-8 in the ledger, which are hint leaks, duplicates, teaching
   gaps, plain-text maths and polish, plus 87 lesson fix groups. Number-shifted clones remain. The Sec 2
   N5 and N6 codenames were replaced with distinct titles, so the duplicate scan can't see them
   (CFL-286, 287, 298). True duplicates include `n6-l3-504`, `-511`, `-518`, `-525`.
7. **Diagnostic:** S2 and S3 items and the form-design decision in
   `docs/plan/PRE_REVIEW_AUDIT_diagnostics_v2.md`.
8. **English, after the staging test:** 270 quality findings
   (`backend_resources/english/v1/authoring/quality_baseline.json`), form equivalence, practice depth,
   and 8-12 essay prompts. The educator's review blocks the pilot, so their start date matters.
9. **App fixes:** two `main` elements on some pages, about 19 database connections on `/progress`, and
   the accessibility findings.
10. **Production:** Railway staging and production aren't set up and no GitHub secrets exist. Needs
    `STAGING_GEMINI_API_KEY` and `PRODUCTION_GEMINI_API_KEY` among others. See
    `docs/plan/RELEASE_OPERATIONS.md` and `docs/plan/HOSTED_STAGING.md`.

### Questions for William

Judgement calls made in PRs, each easy to reverse:

- Text-only "is it right-angled?" items in Sec 2 G4 under D6 B (28 items).
- Whole-number answers: `15` passes for 15 tan 45°, but `34` fails on 33.95 because the prompt asks for
  1 decimal place.
- `simplified_fraction` on Sec 1 N5 "simplest form" items, and `expanded` rejecting `6(x+2)` on
  "Simplify" items.
- Distinct titles to remove codenames in Sec 2 N5 and N6, which leaves the clones in place for now.
- `n5-l2-002` changed from "write as repeated addition" to "write as a single term".

### Switching tutor models

Read from the code, not yet run end to end.

- **Another Gemini model:** change the model and cost settings in `.github/workflows/deploy-staging.yml`
  and `deploy-production.yml`, which set them directly.
- **OpenAI:** `OpenAITutorProvider` exists. Set `ASEAN_ACADEMY_TUTOR_PROVIDER=openai`,
  `OPENAI_API_KEY` and `ASEAN_ACADEMY_TUTOR_OPENAI_MODEL`, and update the two deploy files, which are
  written for Gemini only.
- **Another company:** add a provider class in `services/learning_api/src/learning_api/tutor_provider.py`
  and allow it in `config.py`.
- Whichever you choose, rerun tutor safety and calibration first.

### Local setup notes

- CI order for the database: `check_migration_safety.py`, `validate_migrations.sh`,
  `catalogue-import-db`, `course-import-db`, `english-import-db`, `diagnostic-import-db`,
  `pytest -m postgres`.
- For web, run `corepack pnpm openapi:generate`, then `next typegen` before `tsc`, and delete
  `apps/web/.next-e2e` before lint.

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

## Essay-feedback next milestone (older note; overall order is under "Start here")

The next operational step requires people, not more provider code: a qualified English educator
must execute the private ENG-T3.9 package against already-captured outputs, and the responsible
privacy/safeguarding owners must record genuine T3.10 evidence. Do not enable Render or invoke a
paid provider until those gates pass.

The next independently executable content sequence now moves to the open audit findings; all 51
lessons and two Section 1 full mocks are authored as drafts, alongside the existing Sprint human
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
