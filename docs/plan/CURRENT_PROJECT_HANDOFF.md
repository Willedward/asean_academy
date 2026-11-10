# Current project handoff

Updated: 10 November 2026 (Asia/Singapore)

This is the short restart file for a new session or collaborator. Read it before loading
the larger plans; do not use the full chat transcript as project state.

## Start here: state on 10 November 2026

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
  other flagged topics are rewritten in scope. D8 C means fix categories 1-3 first, then the rest;
  both are now done for every batch except the held Sec 1 N2 batches.

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
  wrong answers, and with every form the old version accepted. A trailing `\%` in `canonical_latex`
  is what lets "40%" pass; removing it rejected correct answers on 18 Sec 1 N3 items until #568 and
  #603-#605. Grep `services/learning_api/tests` for changed keys, because tests can assert on
  content.
- Merge only when all 5 named checks pass on the PR's current head, using `gh pr merge --merge
  --match-head-commit`. A missing check counts as not passed. Don't use `--delete-branch` while a
  worktree depends on the branch, and never run agent git commands in the main checkout.
- Known CI noise: a browser-journey "socket hang up", the slow two-course-track spec, and "window is
  not defined" in the web job. Read the log, then rerun once.

### Done

- **Mathematics questions, all fix categories:** categories 1-3 first, then answer leaks and
  plain-text maths (#437-#508), then duplicates, teaching gaps and polish (76 batch PRs, #515-#633,
  including G4/G5 #610-#617). Every batch except the 4 held Sec 1 N2 batches was cleaned. Over
  400 answer keys changed, mostly where duplicates got new numbers; each PR body lists them old and
  new. Reviewers should treat these as new items.
- **Lessons:** 238 of 327 lesson findings fixed in 19 PRs (#558-#642), including the Sec 1 G5 figures
  D-22 to D-31, new worked examples under D7 A, and the D1 S$ gloss. New chart and polygon templates
  were added to the generators.
- **Checks on the final state (10 November):** `catalogue-validate` and `authoring-validate` 0 errors,
  0 duplicates, 2,052 questions; `review-readiness` 71 ready, 4 approved, 0 blocked, 0 in progress;
  all 8,995 maths blocks in questions, lessons and English parse in KaTeX (two `\pih` typos fixed in
  `g5-l5-501`); no answer form accepted before this pass is now rejected across 1,636 changed
  questions.
- **Ledger:** records carry a `resolution`: `fixed_in_content` or `left_open`, with batches and PRs.
  Statuses are never updated.
- **English:** quality findings 270 to 27 (#588-#631). Banked cloze keys no longer follow bank order,
  vocabulary targets appear in their sentences, the longest option is no longer the key, and the
  three diagnostic forms no longer share one key sequence. Six validator rules stop these recurring.
  The v2 diagnostic generator now refuses to overwrite the hand-fixed content (#636).
- **App:** hint maths renders inline (#525); diagnostic answers save on Next and resume at the first
  unanswered question (#526); tutor provider and model are deploy variables (#532); admin and learner
  accessibility (#432, #436, #637, #640), including animations that stop within 5 seconds and fixed
  heading order; the admin content status route (#442).
- **Tooling:** plain-text maths lint warns (#627, 23 questions flagged, 16 in Sec 1 N2); hint-leak lint
  no longer crashes on fractions (#624).
- **Diagnostic:** connected to the Mathematics course (#418-#431). Students wait on human approval of
  its 76 questions. The English diagnostic is 43 parts in 60 minutes (#370).
- **Release:** two-course gate (#313), single invitation (#280).

### Still to do, in suggested order

1. **Staging test on the review site.** William signs in with Google. Check the site loads first: its
   API timed out on 5 and 9 November. Click through review, a mock, the tutor and calibration, and do
   the B5 accessibility check with a phone screen reader. None of the rewritten content or the new
   lesson figures has been viewed in the app yet, so look at some.
2. **Start Mathematics review** with `docs/plan/MATH_REVIEWER_GUIDE.md`, from the 71 ready batches.
3. **Questions for William,** below.
4. **English educator:** the 27 baseline findings left (11 replacement vocabulary words, 16 lesson
   examples that copy assessment), vocabulary that looks too hard for Sec 1-2 (for example tenable,
   equivocal, circumspect, cogent), six editing-type practice items the real paper doesn't have, four
   diagnostic passages under 300 words, and form equivalence (plan: the educator rates each target
   word, swap outliers between forms, lengthen passages to 300-450 words, add a per-form equivalence
   report, and alternate baseline and endline forms in the pilot). `eb-l5-203` gap 5 may take "rapid" as well as "steady".
5. **Production:** Railway staging and production aren't set up and no GitHub secrets exist. See
   `docs/plan/RELEASE_OPERATIONS.md` and `docs/plan/HOSTED_STAGING.md`.

### Left open after the cleanup pass

Ledger records with `resolution.status` `left_open` (112). By kind:

- **Policy or tooling:** total_marks equal to difficulty, calculator flags, manifests citing house
  rules v1, generation_spec shape, diagram audits (Sec 1 S1 `diagram_audit.json`, CFL-426), the lesson
  length metric (CFL-547), and terminology policy records.
- **Difficulty relabels:** need blueprint rebalancing (for example CFL-386, 458, 461, 462, 472, 501).
- **Generators that don't exist:** the balance figure in `n7-lesson-01`, the angle-types figure in
  `g1-lesson-01`, the points-only figure in `n6-lesson-01`, sine and cosine templates (CFL-384), and
  optional figures for text-only items (CFL-465, 466, 474, 479, 481, 489, 504).
- **Pinned by tests:** `s1-l3-001`, `g5-l2-011`, `g5-l4-010`, `g5-l5-005`, `n3-l1-001`.
- **Held:** Sec 1 N2 (D4) and the five older calibration questions outside any batch (below).
- **Scope:** formal congruence and similarity tests (CFL-580) stay taught, because bank items
  `g2-l3-502`, `g2-l3-509`, `g2-l4-505` and `g2-l4-509` still use them; f(x) notation (CFL-406).

### Questions for William

New:

- **Locked lessons:** Learn and Progress link to locked lessons, where "Start draft practice" leads to
  an error page. Recommended: show the lock state up front.
- **Tutor plan sheet:** unreachable (the API never sends `tutor_plan_required`), links to `/plans`
  (404), and "Send this to my parent" does nothing. Recommended: hide it for the pilot.
- **Older calibration questions** `n1-l3-01`, `n1-l1-04`, `n1-l1-14`, `n1-l1-15`, `n1-l2-11`: live in
  Sec 1 N1 pools (practice, unit checkpoint, reserve), outside any batch, so pr-check blocks edits.
  `n1-l3-01`'s alt text reads its answers aloud. Recommended: a sanctioned seed-question path in
  pr-check, then fix them; or remove them from the pools.
- **Sec 1 N2:** D4 B says reopen after the ranked batches, which is now. Reopening cancels its human
  approvals, so it needs an explicit yes.
- `n5-l1-515` prints 5a/5b and the key agrees. 5a/6b (CFL-598) would change the answer: which was
  intended?

Earlier judgement calls, each easy to reverse:

- Sec 1 S1 coded items at difficulty 3+ now take a display code plus a reason code (D6 B).
- D3 A rewrites: Sec 1 N1 divisor counts, completing squares and cubes, bounds, scaled inequalities and
  the section formula; Sec 1 N6 composite functions; Sec 1 N5 factorising by grouping; Sec 2 N6 uses
  symmetry instead of x = -b/(2a); Sec 2 S2 uses listing and trees instead of the multiplication rule.
- GST glossed; n3-lesson-05's 9% GST example became a generic 8% sales tax.
- Text-only "is it right-angled?" items in Sec 2 G4 under D6 B.
- `simplified_fraction` on Sec 1 N5 "simplest form" items, and `expanded` rejecting `6(x+2)` on
  "Simplify" items.
- `s1-l2-015` replaced with an issue-code item; `g5-l3-011` asks for the perimeter (key 44).
- `g1-l4-011` stays text-only, because a drawn polygon shows its number of sides.
- Diagnostic outcome tags (B13, E13, B28, E27, E28) are wrong in `plan.json`. Recommended: per-item
  overrides in the generator.
- Diagnostic form design: 13 of 19 topic groups use different outcomes across the two forms.
  Recommended: report at topic level for the pilot.
- Diagnostic balance: recommended replacing B28 with a trigonometry item, B29 to 2 marks, E30 to 3, and
  relabelling B34, B35, E11 and E36 as difficulty 2. E35 (frequency density) needs confirming against
  the syllabus.

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
