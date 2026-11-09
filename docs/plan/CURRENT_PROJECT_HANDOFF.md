# Current project handoff

Updated: 9 November 2026 (Asia/Singapore)

This is the short restart file for a new session or collaborator. Read it before loading
the larger plans; do not use the full chat transcript as project state.

## Start here: state on 9 November 2026

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

- **Mathematics fixes:** categories 1-3 are merged for every batch on the fix list. All 19
  Mathematics banks report 0 errors under `validate --strict-geometry`, and `catalogue-validate` and
  `authoring-validate` are clean (0 errors, 0 duplicate findings).
- **Diagrams:** checked figures for all geometry topics, and data charts for Sec 2 S1, S2, N6, N7 and
  Sec 1 S1, from the generator in `question_bank/src/question_bank/diagrams/charts.py`.
- **Answer forms under D9 A:** `simplest_fraction` and `require_index_notation` (#397) are applied to
  Sec 2 S2 and Sec 1 N1.
- **Answer leaks and plain-text maths:** ledger categories 4 and 7 are merged for 67 batches
  (#437-#508), 1,269 questions changed, under D5 B. Every maths block parses in KaTeX. Most of the
  conversion was only checked by script and has not been viewed in the app. Sec 1 N2 stays closed
  under D4 B. On questions with figures, expressions that match a label and lone letters stay as text,
  because the geometry checks read only text blocks.
- **Readiness:** `question-bank review-readiness` lists what can go to a reviewer. A ledger record's
  `resolution` shows which batches were fixed and by which PRs, because statuses are never updated.
  All 75 reviewer packets are current.
- **Diagnostic:** connected to the Mathematics course, with the audit's fixable findings merged
  (#418-#431). Students wait on human approval of its 76 questions. The English diagnostic is 43 parts
  in 60 minutes (#370).
- **English:** all 51 lessons and both Section 1 mocks exist as drafts, retargeted to Sec 3 entry, with
  a learner mock runtime.
- **App:** `/progress` no longer opens a connection per unit (#416), one `main` per page (#417), the
  learner accessibility findings in `docs/plan/ACCESSIBILITY_AUDIT_2026_11.md` (#432), the admin ones
  (#436), and the admin content status route (#442).
- **Release:** two-course gate (#313), single invitation (#280), Gemini-only tutor deploy settings.

### Still to do, in suggested order

1. **Staging test on the review site.** William signs in with Google, since this needs a person. Check
   the site loads first: its API timed out or returned errors on 5 and 9 November. Click through the
   review flow and a small review batch, a mock, and the tutor, including calibration. Also run the
   accessibility check still open in B5, including a phone screen reader; #432 was only tested in
   Chromium.
2. **Start Mathematics review** using `docs/plan/MATH_REVIEWER_GUIDE.md`, from the batches
   `review-readiness` lists as ready.
3. **Diagnostic decisions for William,** listed under "Questions for William".
4. **Later content passes:** ledger categories 5, 6 and 8 (duplicates, teaching gaps and polish), 87
   lesson fix groups, and the Sec 1 G5 lesson figures (D-22 to D-31). Doing these after review cancels
   approvals on the questions changed. Sec 1 S1 still needs a `diagram_audit.json` (CFL-426).
   Leftovers from categories 4 and 7:
   - Real leaks the pass missed or left: `n7-l1-513`, `n6-l1-012`, `n6-l1-021`, `n6-l1-015`,
     `n6-l2-008`, `n1-l1-019`, `g1-l1-012`, and the title of `s1-l1-017`.
   - Outside the batches: CFL-230, CFL-248, CFL-249, CFL-250 and `n1-l2-11` (older calibration
     questions), and lesson items CFL-234, CFL-595 and CFL-601.
   - A check that flags plain-text maths (CFL-586).
   - Sec 2 G4 b004 keeps `x` and `θ` as inline maths on 19 figure prompts while b001-b003 use text.
   - Stage-2 hints such as "Calculate tan⁻¹(48/55)" on difficulty 3+ items weren't on the worklist.
5. **English, after the staging test:** 270 quality findings
   (`backend_resources/english/v1/authoring/quality_baseline.json`), form equivalence, practice depth,
   and 8-12 essay prompts. The educator's review blocks the pilot, so their start date matters. The new
   diagnostic's vocabulary is mostly B2-C1, which the level review flagged as hard; the educator should
   judge it.
6. **Remaining accessibility:** P2-11, P2-12 and P3 in the audit.
7. **Production:** Railway staging and production aren't set up and no GitHub secrets exist. Needs
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
- `s1-l2-015` replaced with an issue-code item (key 4), because the old one counted words in its own
  prompt. `n3-l1-004` has new numbers (S$72, key 90).
- Prompts rewritten so the value must be derived, keys unchanged: `g1-l3-008`, `g1-l2-023`, `g1-l3-031`,
  `n7-l1-001`, and the four Sec 2 N7 "x+6=k has the solution x=3" items (CFL-214).
- `n5-l1-515` prints 5a/5b and the key agrees. Changing it to 5a/6b (CFL-598) would change the answer, so
  it was left: which was intended?
- `g5-l3-011` changed from "find x" to "find the perimeter", key 44, because its old givens contradicted
  each other.
- `g1-l4-011` stays text-only, because a drawn polygon shows its number of sides, which is the answer.
  `s2-l1-507` only converts 0.2 to a percentage, so it was taken off the figure list.
- Diagnostic outcome tags (B13, E13, B28, E27, E28) are wrong in `plan.json`, and those tags are what
  gets imported. Recommended: per-item overrides in the generator.
- Diagnostic form design: 13 of 19 topic groups use different outcomes across the two forms.
  Recommended: report at topic level for the pilot and re-pair once item statistics exist.
- Diagnostic balance: recommended replacing B28 with a trigonometry item, setting B29 to 2 marks and E30
  to 3, and relabelling B34, B35, E11 and E36 as difficulty 2.
- E35 (frequency density): needs confirming against the syllabus.

### Switching tutor models

Provider and model are chosen by GitHub Actions variables, read by both deploy workflows through
`services/learning_api/scripts/tutor_deploy_settings.py`. Set them on the `staging` or `production`
environment (or the repository for both), then redeploy. With none set, deploys stay on today's pilot:
Gemini `gemini-3.5-flash-lite`, premium routing off.

| Variable | Value |
| --- | --- |
| `TUTOR_PROVIDER` | `gemini` (default) or `openai` |
| `TUTOR_MODEL` | Model name; needed for `openai` or any Gemini model other than the default |
| `TUTOR_INPUT_COST_PER_MILLION_MICROS_SGD` | Price per million input tokens; needed unless on the default model |
| `TUTOR_OUTPUT_COST_PER_MILLION_MICROS_SGD` | Price per million output tokens; same rule |

Keys are secrets named `<STAGING|PRODUCTION>_<GEMINI|OPENAI>_API_KEY`, matching the provider.

1. Rerun tutor safety and calibration for the new provider or model before switching. The calibration
   lab at `/admin/tutor-evaluation` can only run Gemini or synthetic today, so OpenAI needs the lab extended
   or a manual review first.
2. Add the key secret for the new provider, then set the variables above and redeploy staging.
3. The deploy fails before changing anything if a combination is wrong: unknown provider, missing model,
   missing key, missing or non-numeric prices, or a model that doesn't belong to the provider. The API
   applies the same checks at start-up (`learning_api/config.py`).
4. Check a tutor turn on staging, then do the same for production.

Deploys always set hybrid and shadow routing off; turning those on is a separate release decision.
To add another company, add a provider class in `services/learning_api/src/learning_api/tutor_provider.py`,
allow it in `config.py` and add it to `_PROVIDERS` in the deploy script.

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
