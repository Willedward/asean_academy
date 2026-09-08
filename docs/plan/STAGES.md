# ASEAN Scholar Preparation Platform — Detailed Build Stages

**Document status:** Execution plan  
**Last updated:** 8 September 2026  
**Target:** Founder-ready system by 30 November 2026; invited beta begins in December 2026  
**Companion documents:** `plan.md` defines what to build; `ARCHI.md` defines how it is engineered  
**Team assumption:** Two founders, comfortable with TypeScript/JavaScript and Python, contributing 10–25 combined hours per week

## 1. Purpose of this document

This file converts the product requirements in `plan.md` and the technical design in `ARCHI.md` into an ordered implementation programme. It answers:

- What should be built first and why.
- What can be developed in parallel.
- What must wait for an earlier dependency.
- How long each stage is expected to take.
- Which deliverables, tests and exit criteria prove a stage is complete.
- What to cut first if the schedule slips.
- What must be ready before real students are invited.

This is an execution plan, not a promise that every estimate will be exact. At the end of each stage, compare estimated and actual hours and update all remaining estimates.

## 2. The central sequencing decision

Do **not** build the complete OCR pipeline first.

The critical path begins with a thin, manually seeded vertical slice:

1. Create the application and database.
2. Let an invited student sign in and select a track.
3. Seed a small set of real Mathematics questions manually.
4. Show a question crop and accept a final answer.
5. Mark it deterministically.
6. Enforce the two-error Give up rule and reveal a cached solution.
7. Record progress.
8. Only after this loop works, automate PDF ingestion and expand the question bank.

This order validates the student experience early. OCR is a content-production accelerator; it is not the product itself. If OCR is late, founders can still publish a limited number of manually prepared questions. If the student loop is late, a large extracted question bank has no usable destination.

## 3. Overall schedule

The schedule starts on 8 September 2026 and keeps the original delivery gates.

| Stage | Calendar target | Estimated team effort | Primary outcome |
|---|---|---:|---|
| 0. Scope lock and working agreements | 8–9 Sep | 6–10 hours | Decisions, backlog and acceptance criteria are frozen |
| 1. Repository and local foundation | 8–11 Sep | 10–16 hours | Deployable monorepo, CI and local services |
| 2. Data, authentication and application shells | 10–15 Sep | 18–30 hours | Secure invited-user onboarding and empty dashboards |
| 3. Manual Mathematics vertical slice | 14–21 Sep | 28–45 hours | Twenty real questions work end to end |
| 4. PDF ingestion proof of concept | 22 Sep–3 Oct | 25–40 hours | One representative paper becomes candidate question records |
| 5. Automated extraction, classification and verification | 4–19 Oct | 35–60 hours | Repeatable image-first ingestion pipeline and about 100 questions per track |
| 6. Curriculum, progression and Mathematics breadth | 13 Oct–2 Nov | 30–50 hours | Sequential chapters, checkpoints, retry logic and broader answer support |
| 7. English objective practice and writing | 20 Oct–9 Nov | 35–55 hours | Grammar/vocabulary plus both writing flows and AI feedback |
| 8. Admin, observability and operational controls | 27 Oct–13 Nov | 25–40 hours | Founders can operate and diagnose the system safely |
| 9. Content scale-up and quality freeze | 3–20 Nov | 30–55 hours | Approximately 150–200 verified Mathematics questions per track |
| 10. Beta hardening and founder pilot | 10–30 Nov | 35–55 hours | Mobile-tested, secure, recoverable release candidate |
| 11. December cohort rollout | December | 4–8 hours/week | Controlled launch to 10–30 students and weekly learning cycles |

The ranges overlap because two founders can work in parallel. At 10 combined hours per week, the full scope is unlikely to fit without cuts. At 20–25 hours per week, the plan is achievable if the team protects the P0 scope and reuses managed services.

## 4. Milestone gates

| Gate | Date | Non-negotiable evidence |
|---|---|---|
| First vertical slice | 21 September | Deployed app, Supabase, invitation login, track selection, 20 Mathematics questions, deterministic marking, two writing prompts and basic post-submission feedback |
| Content pipeline | 19 October | PDF rendering/cropping, question-solution pairing, categorisation, generated cached solutions, verification statuses and upload into Supabase |
| Learning product | 9 November | Topic practice, sequential progression, timed Mathematics mock, grammar/vocabulary, essay autosave/word count and stored AI outputs |
| Feature freeze | 20 November | No new P1/P2 features; only content, bugs, tests, performance and security changes |
| Release candidate | 30 November | Founder pilot passes, rate limits and budgets are active, mobile P0 flows work, beta invitations are ready |
| Beta | December | Start with 5–10 students; expand to 20–30 only after critical issues are resolved |

## 5. Workstreams and ownership

If there are two developers, divide work by stream while reviewing each other's changes.

| Workstream | Typical owner | Responsibilities |
|---|---|---|
| Product/web | Founder A | Next.js UI, authentication, student flows, admin pages, analytics |
| Data/processing | Founder B | Supabase schema, Python ingestion, OCR anchors, verification, AI jobs |
| Shared | Both | Curriculum decisions, golden datasets, security review, browser testing and content QA |

No code area should have only one person who understands it. Each stage ends with a short walkthrough, updated documentation and at least one review by the other founder.

## 6. Stage 0 — Scope lock and working agreements

**Target:** 8–9 September  
**Estimate:** 6–10 team hours  
**Dependencies:** None

### Goal

Turn unresolved product choices into configuration or explicit temporary defaults so they do not block implementation.

### Tasks

1. Confirm the December P0 list in `plan.md`.
2. Mark payments, credits, mentors, leaderboards, open-ended AI chat, native mobile, handwriting input and full question re-typesetting as post-beta.
3. Finalise the first chapter sequence for both tracks.
4. Create the initial topic taxonomy. Each topic needs a stable machine key, display name, track, chapter and order.
5. Choose the provisional chapter-unlock policy:
   - Recommended default: complete the required practice set, then pass a checkpoint.
   - Store thresholds as data so the rule can change later.
6. Define the first supported answer formats:
   - integer;
   - decimal with tolerance;
   - fraction;
   - percentage;
   - short text or multiple choice;
   - simple algebraic expression;
   - coordinate pair;
   - value with unit.
7. Select 20 representative Sec 3 Mathematics questions for the first slice. Prefer variety over quantity.
8. Select or write one situational-writing and one continuous-writing prompt.
9. Create a golden-answer sheet for the 20 Mathematics questions.
10. Agree on Git conventions, review rules, naming and the issue template.
11. Create one board with `Backlog`, `Ready`, `In progress`, `Review`, `Blocked` and `Done`.
12. Give every P0 requirement from `plan.md` a ticket and acceptance test.

### Deliverables

- Frozen P0 scope.
- Version 1 curriculum and topic taxonomy.
- Twenty-question Mathematics golden set.
- Two writing prompts, their rubrics and at least one model response each.
- Prioritised issue board.

### Exit criteria

- Both founders can explain what is and is not in the beta.
- No Stage 1–3 ticket depends on an unresolved product choice.
- The 20-question set includes at least four different answer formats.

## 7. Stage 1 — Repository and local foundation

**Target:** 8–11 September  
**Estimate:** 10–16 team hours  
**Dependencies:** Stage 0 can overlap

### Goal

Create a boring, reproducible foundation that every later stage can build upon.

### Build tasks

1. Create the monorepo with `pnpm` workspaces.
2. Create `apps/web` using Next.js App Router and TypeScript strict mode.
3. Create shared packages for schemas, database access, UI and the question engine.
4. Create `workers/ingestion` using Python 3.12 and `uv`.
5. Add Tailwind CSS and a minimal shadcn/ui setup.
6. Add ESLint, Prettier, Vitest and pytest.
7. Add `.env.example` with variable names only—never real secrets.
8. Configure Supabase CLI and migration directories.
9. Create separate development and production environment records.
10. Configure GitHub Actions to run install, typecheck, lint, unit tests and build.
11. Deploy the empty web application to a preview URL.
12. Add a basic health endpoint that confirms the application is running without exposing secrets.
13. Add a pull-request template containing testing and migration checkboxes.

### Suggested file order

```text
package.json
pnpm-workspace.yaml
apps/web/package.json
apps/web/app/layout.tsx
apps/web/app/page.tsx
packages/schemas/package.json
workers/ingestion/pyproject.toml
supabase/config.toml
.github/workflows/ci.yml
.env.example
```

### Tests

- A fresh clone installs using documented commands.
- `pnpm build`, typecheck and lint pass.
- `pytest` runs, even if it initially contains only one smoke test.
- Preview deployment completes from the main branch.
- Missing environment variables fail with a readable error.

### Exit criteria

- Both founders can run the project locally.
- CI blocks a deliberately failing test.
- Preview deployment is repeatable.

## 8. Stage 2 — Database, authentication and application shells

**Target:** 10–15 September  
**Estimate:** 18–30 team hours  
**Dependencies:** Stage 1

### Goal

Produce a secure empty learning application: invited students can register, select a track and see the correct curriculum shell; admins can reach protected admin pages.

### Database tasks

1. Create migrations for:
   - `profiles`;
   - `invitations`;
   - `tracks`;
   - `curriculum_versions`;
   - `chapters`;
   - `topics`;
   - `chapter_topics`;
   - `enrollments`.
2. Add explicit enum/check constraints for roles, tracks and invitation states.
3. Seed Sec 1-entry and Sec 3-entry tracks.
4. Seed the first curriculum version and chapter order.
5. Generate TypeScript database types.
6. Add indexes for profile, invitation and curriculum lookups.

### Authentication tasks

1. Configure Supabase Auth.
2. Build login, registration and password-reset pages.
3. Validate invitation codes on the server.
4. Make invitation redemption transactional and single-use unless explicitly configured otherwise.
5. Create the profile and enrollment after account creation.
6. Enforce student/admin roles on the server.
7. Use Supabase sessions; do not implement custom JWT creation.
8. Add middleware only for coarse routing. Re-check authorisation inside every sensitive server action or route.

### UI tasks

1. Build the student layout, navigation and empty dashboard.
2. Show selected track and current chapter.
3. Show later chapters as locked.
4. Build the admin layout and an empty content dashboard.
5. Add accessible loading, error, empty and not-found states.

### Security tasks

1. Enable Row-Level Security on every new table.
2. Write tests proving Student A cannot read or update Student B's profile or enrollment.
3. Ensure browsers never receive the Supabase service-role key.
4. Prevent users from choosing an admin role through request payloads.

### Exit criteria

- A valid invite can create one student account.
- An invalid, expired or reused invite is rejected.
- The student sees only the selected track.
- A student cannot access admin data or another student's records.
- An administrator can access the protected admin shell.

## 9. Stage 3 — Manual Mathematics vertical slice

**Target:** 14–21 September  
**Estimate:** 28–45 team hours  
**Dependencies:** Stage 2 database and auth; can begin with seed scripts while Stage 2 UI is finishing

### Goal

Prove the complete learning loop with real content before investing heavily in automated ingestion.

### Content and schema tasks

1. Add migrations for:
   - `source_documents`;
   - `questions`;
   - `question_assets`;
   - `answer_keys`;
   - `solution_versions`;
   - `question_topics`;
   - `practice_sessions`;
   - `session_questions`;
   - `attempts`;
   - `question_progress`;
   - `chapter_progress`.
2. Create private storage buckets for source documents, question crops and solution crops.
3. Manually crop and import 20 questions from the representative paper.
4. Manually enter and verify each normalized final answer.
5. Add one cached worked solution per question.
6. Mark only approved records as `published`.

### Answer-engine tasks

1. Create one canonical `AnswerSpec` schema.
2. Separate display answer from normalized checking data.
3. Implement normalizers and comparators for the formats present in the 20-question set.
4. Use server-side checking only.
5. Add timeouts and an allowlist to symbolic parsing.
6. Reject unsupported answer types cleanly instead of guessing.
7. Store every attempt immutably.
8. Make answer submission idempotent so a double click cannot create two attempts.

### Student-flow tasks

1. Start or resume a practice session.
2. Select an eligible published question.
3. Render the original crop clearly with zoom support on small screens.
4. Render an answer input appropriate to the question's answer type.
5. On a wrong answer, show only `Incorrect, try again.`
6. Disable Give up before two incorrect attempts.
7. Enable Give up after the second incorrect attempt but allow unlimited further attempts.
8. Reveal the cached solution only after explicit Give up.
9. Mark correct questions complete.
10. Track first-attempt accuracy independently from eventual success.
11. Update the dashboard after an attempt or Give up event.

### Required tests

- Correct integer, fraction, decimal and percentage variants are accepted.
- Equivalent fractions such as `1/2` and `2/4` compare correctly.
- Unsupported or malformed input does not crash the route.
- Give up is forbidden by the server before two incorrect attempts, even if the UI is bypassed.
- The solution endpoint remains forbidden until Give up.
- An unpublished question is never selected.
- Replaying the same submission idempotency key does not duplicate an attempt.
- Two students' sessions and progress remain isolated.

### Exit criteria — 21 September gate

- The app is deployed.
- An invited student can register and select a track.
- Twenty real Mathematics questions are available.
- A student can answer, retry, give up and see the correct cached solution.
- Attempt and progress records survive sign-out and sign-in.
- One situational and one continuous writing prompt exist; basic submission and feedback may still be operationally simple at this gate.

## 10. Stage 4 — PDF ingestion proof of concept

**Target:** 22 September–3 October  
**Estimate:** 25–40 team hours  
**Dependencies:** Stage 3 content schema and storage conventions

### Goal

Turn one representative scanned paper and its solution pages into draft question records. Accuracy matters more than processing every page.

### Pipeline tasks

1. Implement document checksum and duplicate detection.
2. Save source metadata: school, year, paper, source level, target track and page count.
3. Render pages at a fixed 200–250 DPI using PyMuPDF.
4. Extract the existing OCR text layer for navigation anchors.
5. Store page-level text and image metadata.
6. Classify pages as cover, instructions, question, continuation, answer key, worked solution or blank.
7. Detect likely question-number anchors.
8. Generate candidate bounding boxes.
9. Support a question continuing onto another page.
10. Produce ordered question crops and solution crops.
11. Run image-quality checks for blank, tiny, truncated and low-resolution crops.
12. Upload accepted assets using deterministic storage paths.
13. Make reruns idempotent: processing the same document twice must not duplicate questions or files.

### Important design rule

Embedded OCR is used to find page regions; it is not the mathematical source of truth. The original crop remains the student-visible source. Symbols, fractions, exponents, inequalities and diagrams must not be trusted solely from OCR text.

### Admin proof-of-concept page

Show:

- uploaded document metadata;
- job state;
- rendered page thumbnails;
- candidate question boundaries;
- generated question and solution crops;
- rejection reason when a crop fails quality checks.

### Tests and fixtures

- Keep two small fixture PDFs: one normal question and one multi-page/diagram question.
- Snapshot crop dimensions and page associations.
- Confirm repeated jobs produce the same stable records.
- Confirm a corrupt or password-protected PDF ends in a readable terminal failure.
- Confirm temporary failures can retry without losing document state.

### Exit criteria

- One representative paper runs end to end without manual file copying.
- At least 80% of ordinary question boundaries are useful candidates.
- Multi-page questions remain associated with one question record and ordered assets.
- Failures are visible and never auto-published.

## 11. Stage 5 — Automated extraction, classification and verification

**Target:** 4–19 October  
**Estimate:** 35–60 team hours  
**Dependencies:** Stage 4 crops; Stage 0 taxonomy; Stage 3 answer schema

### Goal

Create the reliable, image-first content pipeline that transforms crops into hidden candidate questions, verifies them and makes only safe questions eligible for publication.

### Structured extraction

1. Define a versioned Zod/JSON schema for model output.
2. Send the original question crop and matched marking-scheme crop as image inputs.
3. Extract:
   - question number and subpart;
   - text and optional LaTeX;
   - marks;
   - diagram presence;
   - answer type;
   - official answer;
   - worked steps;
   - uncertainty flags.
4. Pin the selected model snapshot.
5. Validate every response against the schema.
6. Store prompt version, model, token usage, latency, input hash and output version.
7. Retry only transient failures; schema failures should use bounded corrective retries.

### Question-solution pairing

1. Use question number, paper section, page order and solution headings as matching signals.
2. Calculate a pairing confidence.
3. Reject ambiguous one-to-many or many-to-one matches unless the question structure explicitly allows them.
4. Preserve every source asset so a failed pairing can be inspected.

### Topic classification

1. Map only into the fixed taxonomy created in Stage 0.
2. Return primary topic, optional secondary topic and confidence.
3. Do not let the model invent new production topic keys.
4. Add an `unclassified` result when evidence is weak.
5. Measure accuracy against a founder-labelled golden set before setting the threshold.

### Verification layers

1. Schema and required-field validation.
2. Crop-quality validation.
3. Question-number and source-page agreement.
4. Official-answer extraction agreement.
5. Independent solution attempt using a separate prompt/run.
6. Deterministic numeric or SymPy verification where the format allows it.
7. Unit and tolerance validation.
8. Classification-confidence threshold.
9. Complete-solution presence.
10. Final publication-eligibility calculation.

### Status model

```text
uploaded -> rendering -> segmented -> extracted -> classified -> verifying
verifying -> verified | rejected | needs_review
verified -> published
published -> unpublished
```

`needs_review` is hidden. Because the team selected automatic-only publication quality control, it does not become student-visible unless a later automated rerun passes every gate or a founder explicitly changes the policy.

### Quality targets

- 100% schema-valid stored records.
- No question is published without a verified answer and cached solution.
- At least 95% topic accuracy on the labelled golden set before auto-classification controls production ordering.
- No known incorrect final answer in the published regression set.
- Record the percentage rejected; do not lower thresholds merely to increase quantity.

### Exit criteria — 19 October gate

- A new supported paper can be uploaded without changing application code.
- The worker renders, segments, extracts, pairs, classifies and verifies it.
- Each rejected question has a machine-readable reason.
- Only `verified` questions are eligible for founder publication.
- The combined pipeline has produced approximately 100 usable questions per track, or the team has an explicit manual-import fallback plan for any shortfall.

## 12. Stage 6 — Curriculum progression and Mathematics breadth

**Target:** 13 October–2 November  
**Estimate:** 30–50 team hours  
**Dependencies:** Stage 3 loop; can run alongside late Stage 5 work

### Goal

Turn a one-topic demonstration into the intended fixed learning path.

### Progression tasks

1. Store unlock policies by curriculum version rather than in UI code.
2. Add required practice-set membership.
3. Add checkpoint sessions and pass thresholds.
4. Make chapter completion transactional.
5. Unlock only the next chapter in sequence.
6. Record the rule version used for each unlock decision.
7. Decide how a gave-up question affects practice completion.
8. Add a retry queue without permanently trapping a student.
9. Handle curriculum updates without moving existing students unpredictably.

### Selection tasks

The next-question query should:

1. Restrict to the student's track and unlocked chapter.
2. Restrict to `published` questions.
3. Exclude questions already used in the current session.
4. Prefer unseen questions.
5. Reintroduce gave-up questions according to the retry policy.
6. Avoid very recent repeats.
7. Balance configured difficulty.
8. Randomise only among equally suitable candidates.

### Answer-type expansion

Add and test only formats needed by the content bank:

- signed integers;
- exact decimals and tolerance decimals;
- fractions and mixed numbers;
- percentages;
- algebraic expressions;
- equations or multiple roots;
- coordinate pairs;
- unordered sets;
- values with units;
- multiple choice;
- multi-part final answers.

Graph-drawing, construction and proof questions should remain hidden unless the beta has an explicit reliable submission and marking design.

### Timed mock

1. Create a fixed session manifest at the start.
2. Store start, deadline and submitted timestamps server-side.
3. Autosave final answers.
4. Allow normal page navigation without revealing correctness during the mock.
5. Mark after submission or expiry.
6. Keep mock behavior separate from practice behavior.

### Exit criteria

- Chapters unlock sequentially according to stored configuration.
- Practice and mock modes cannot leak behavior into one another.
- Every published answer type has golden tests.
- A student can leave and resume a session safely.

## 13. Stage 7 — English objective practice and writing

**Target:** 20 October–9 November  
**Estimate:** 35–55 team hours  
**Dependencies:** Stage 2 auth; shared question engine from Stage 3; background jobs from Stage 5

### Goal

Deliver deterministic grammar/vocabulary practice and both essay formats with reliable post-submission AI feedback.

### Objective English

1. Add components and units for grammar and vocabulary.
2. Support multiple choice, fill-in-the-blank, error correction, sentence transformation and vocabulary in context.
3. Reuse immutable attempts and progress where possible.
4. Store explanations with content so normal practice does not call AI.
5. Add founder import forms for objective questions.

### Essay data model

Create:

- `english_prompts`;
- `rubrics`;
- `rubric_criteria`;
- `model_essays`;
- `essay_drafts`;
- `essay_submissions`;
- `essay_feedback`;
- `essay_criterion_scores`.

### Essay editor

1. Display prompt, requirements and timer where applicable.
2. Provide a plain writing area with accessible keyboard behavior.
3. Show word count.
4. Autosave after a short debounce and on page visibility change.
5. Display saved/saving/offline state.
6. Recover the latest server draft after refresh or sign-in.
7. Warn before leaving with unsaved changes.
8. Disable AI assistance during drafting.
9. Require submission confirmation.
10. Freeze an immutable copy on submit.

### Marking job

1. Load the exact immutable submission, prompt, rubric version and permitted model essays.
2. Run structured marking against each criterion.
3. Require evidence grounded in the student's text.
4. Produce strengths, priority improvements and selected corrections.
5. Run a consistency/sanity check before saving.
6. Reject invalid score totals or criterion ranges.
7. Store model, prompt version, usage and latency.
8. Show `queued`, `processing`, `complete` or `failed` status.
9. Never expose partial output.
10. Label scores as AI-generated estimates.

### Evaluation

Use a small versioned set of essays spanning weak, average and strong performance. Measure:

- score spread across repeated runs;
- rubric adherence;
- unsupported claims;
- feedback usefulness;
- tone and age appropriateness;
- agreement with founder judgement.

### Exit criteria — 9 November gate

- Grammar/vocabulary questions are deterministically marked.
- Drafts survive refresh and reconnect.
- Submission is immutable and cannot be edited afterward.
- Both situational and continuous writing produce persisted criterion-level feedback.
- Failed jobs can be safely retried without creating a second submission.

## 14. Stage 8 — Admin, observability and operational controls

**Target:** 27 October–13 November  
**Estimate:** 25–40 team hours  
**Dependencies:** Runs alongside Stages 6 and 7

### Goal

Allow the two founders to operate the beta without editing production database rows by hand.

### Admin pages

- Paper upload and document inventory.
- Ingestion timeline and per-stage status.
- Question preview with all ordered assets.
- Extracted answer, topic and solution preview.
- Verification evidence and rejection codes.
- Publish/unpublish controls.
- Reprocess selected stage without duplicating question identity.
- Curriculum, chapter and topic ordering.
- English prompt, rubric and model-essay management.
- Invitation creation, expiry and revocation.
- Student progress summary.
- Failed-job and cost views.

### Observability

1. Configure Sentry for web, API and worker exceptions.
2. Give each request/job a correlation ID.
3. Add product events without raw answers or essays.
4. Track AI tokens, estimated cost and latency by job type.
5. Track ingestion acceptance/rejection by reason.
6. Track essay-marking queue age and failure rate.
7. Add alerts for repeated job failure, spending thresholds and elevated API errors.

### Cost and abuse controls

1. Apply per-student essay submission limits.
2. Rate-limit login, attempts, Give up and expensive admin jobs.
3. Set a hard monthly AI budget alert and a soft warning threshold.
4. Cap job retries.
5. Prevent identical input from triggering repeated model calls when a valid cached result exists.
6. Restrict PDF size, MIME type and page count.

### Exit criteria

- Founders can understand why a document or question failed.
- A failed job can be retried safely.
- AI spend and queue status are visible.
- No normal beta operation requires direct production SQL.

## 15. Stage 9 — Content scale-up and quality freeze

**Target:** 3–20 November  
**Estimate:** 30–55 team hours, highly dependent on source quality  
**Dependencies:** Stages 5, 6 and 8

### Goal

Reach useful coverage while preserving the rule that low-confidence content stays hidden.

### Tasks

1. Inventory topic coverage for each track.
2. Prioritise missing core chapters rather than processing papers chronologically.
3. Process sources in small batches so systemic failures are caught early.
4. Run the complete verification suite after every pipeline change.
5. Measure accepted questions per source and time per accepted question.
6. Deduplicate near-identical questions using source metadata and normalized text/image hashes.
7. Ensure every published question has:
   - clear crop;
   - correct track/chapter/topic;
   - supported answer type;
   - verified normalized answer;
   - cached complete solution;
   - source provenance;
   - passing verification record.
8. Stop publishing new answer formats after feature freeze unless they are P0 blockers.
9. Aim for approximately 150–200 published Mathematics questions per track.
10. If the target cannot be met safely, launch with fewer reliable questions and document coverage gaps.

### Content freeze rule

After 20 November, new content may be added only through the already tested pipeline. No new parser design, answer type or student interaction should be introduced unless it fixes a release-blocking issue.

### Exit criteria

- Each unlocked beta chapter has enough questions for a meaningful session and checkpoint.
- No published record is missing a solution or verification result.
- The golden suite passes against the exact production content export.
- Coverage gaps are visible in an admin report.

## 16. Stage 10 — Beta hardening and founder pilot

**Target:** 10–30 November  
**Estimate:** 35–55 team hours  
**Dependencies:** All P0 feature stages

### Goal

Convert a feature-complete system into a safe release candidate.

### Full journey tests

Run these with clean accounts in the production-like environment:

1. Admin creates an invitation.
2. Student registers and selects a track.
3. Student completes a correct Mathematics answer.
4. Student submits two incorrect answers, continues, then gives up.
5. Solution access is forbidden before Give up and allowed afterward.
6. Progress survives refresh and sign-in.
7. Student reaches a checkpoint and unlocks the next chapter.
8. Student completes objective English.
9. Student starts an essay, refreshes, recovers the draft and submits.
10. AI feedback arrives and is shown only to the correct student.
11. Admin uploads a paper and sees its processing outcome.

### Security checks

- Test RLS for every student-data table.
- Test private asset access and signed-URL expiry.
- Confirm no service or OpenAI keys are bundled into browser code.
- Validate admin checks server-side.
- Test malicious answer strings and symbolic-parser timeouts.
- Add dependency and secret scanning.
- Verify account deletion and minimal data retention behavior.

### Reliability checks

- Test double-clicks, refreshes and network retries.
- Kill a worker mid-job and confirm safe retry.
- Verify idempotency for attempts, submissions and ingestion.
- Test database backup and restore instructions.
- Confirm alerts reach the founders.
- Confirm an AI provider failure leaves essays queued/failed without data loss.

### Mobile and accessibility checks

- Test common 360–430 px mobile widths.
- Verify question crops can zoom and pan.
- Ensure answer inputs remain visible above the mobile keyboard.
- Check focus order, labels, contrast and error announcements.
- Test Chrome, Safari and Edge on at least one real device where possible.

### Performance checks

- Dashboard and question pages should feel responsive on ordinary mobile connections.
- Use appropriately sized images rather than full PDF pages.
- Avoid blocking a page request on an AI or ingestion call.
- Inspect slow database queries and add evidence-based indexes.
- Run a modest load simulation above the expected 10–30 concurrent beta users.

### Release criteria — 30 November

- All P0 acceptance tests pass.
- No open severity-1 or severity-2 bug remains.
- Every table/bucket access policy is tested.
- Budgets, rate limits, error monitoring and backups are active.
- Founder pilot succeeds twice using fresh accounts.
- Known limitations and support procedures are documented.
- Rollback instructions exist for web, database migration and worker releases.

## 17. Stage 11 — December beta rollout

**Target:** December 2026  
**Estimate:** 4–8 founder hours per week plus bug-fix time  
**Dependencies:** Stage 10 release criteria

### Rollout sequence

1. Invite 5 internal or highly cooperative testers.
2. Observe registration and first-session completion directly where consent allows.
3. Fix onboarding, marking and content blockers.
4. Expand to 10 students.
5. Wait for at least one week of usage and review system metrics.
6. Expand gradually to 20–30 students only if error rate and support load remain manageable.

### Weekly beta routine

- Review activation and returning-user rates.
- Review questions reported as incorrect within 24 hours.
- Review ingestion and essay-marking failures.
- Check AI spend against the cap.
- Interview at least two students or collect structured feedback.
- Choose no more than three high-impact changes for the next week.
- Avoid large architectural changes during the active cohort.

### Beta success evidence

- At least 70% of registrants begin a practice session.
- At least 50% return in a later week.
- At least 60% complete one chapter or equivalent.
- Fewer than 1% of served Mathematics questions are reported as technically wrong.
- Median essay-feedback usefulness reaches at least 4/5.
- Founders can ingest another supported source without application-code changes.

## 18. Critical path and parallel work

### Critical path

```text
Scope lock
-> repository
-> schema/auth
-> manual Mathematics loop
-> ingestion crops
-> structured extraction and verification
-> sufficient published content
-> hardening
-> beta
```

Any delay on this path threatens the beta directly.

### Safe parallel work

| While this is happening | The other founder can work on |
|---|---|
| Repository setup | Curriculum taxonomy and golden content |
| Auth/schema | Manual question crops and solution preparation |
| Mathematics UI | Answer-normalization tests |
| PDF segmentation | Admin document-status UI |
| AI extraction | Curriculum progression and selection query |
| Mathematics breadth | Essay editor and English schemas |
| Content scale-up | Mobile QA, analytics and security tests |

### Work that should not start too early

- Do not build payments before beta learning is validated.
- Do not build automated source scraping before manual PDF upload works reliably.
- Do not fine-tune a model before prompt/schema evaluation proves a real need.
- Do not add embeddings or vector search for a relational topic bank.
- Do not create microservices before measured scaling or deployment constraints require them.
- Do not perfect visual design before the end-to-end flows and mobile layouts work.

## 19. Definition of ready for a ticket

A ticket may enter `Ready` only when it includes:

- a user or operator outcome;
- scope and explicit non-scope;
- dependency list;
- affected data and permissions;
- acceptance criteria;
- required tests;
- analytics/error behavior when relevant;
- design reference or simple wireframe for UI work.

## 20. Definition of done for a ticket

A ticket is done only when:

- code is reviewed and merged;
- types, lint and relevant tests pass;
- migrations and generated types are committed when applicable;
- empty, loading, error and permission states are handled;
- no secret or personal student content appears in logs;
- monitoring or analytics is added when needed;
- documentation is updated;
- the feature works in the preview environment;
- acceptance criteria are demonstrated, not merely coded.

## 21. Testing pyramid by stage

| Level | What it protects | When introduced |
|---|---|---|
| Pure unit tests | normalizers, comparators, progression and parsers | Stages 1–3 |
| Database/RLS tests | constraints, isolation and transactions | Stages 2–3 |
| Python fixtures | rendering, segmentation, extraction and verification | Stages 4–5 |
| AI evaluations | transcription, pairing, classification and essay consistency | Stages 5 and 7 |
| Integration tests | API, storage, database and jobs | Stages 3–8 |
| Playwright journeys | student/admin critical paths | Stages 3, 7 and 10 |
| Founder acceptance | academic correctness and usability | Every milestone; intensive in Stage 10 |

No automated test replaces academic evaluation of the golden content set. Conversely, founder spot checks do not replace deterministic regression tests.

## 22. Time-estimation rules

Each estimate includes implementation, review, tests and deployment. It does not include extended curriculum writing or sourcing/licensing negotiations.

Use these rules when updating the plan:

- Multiply the first estimate for unfamiliar external APIs by 1.5.
- Keep 20% of weekly capacity unallocated for bugs and integration.
- Time-box investigations to two hours before documenting the blocker and choosing a simpler fallback.
- Split tickets estimated above eight hours.
- Treat content-processing time separately from engineering time.
- Reforecast after the first paper, first 20 questions and first 10 essay markings.

### Capacity scenarios

| Combined capacity | September–November capacity | Practical implication |
|---|---:|---|
| 10 hours/week | about 120 hours | Ship the manual Mathematics loop, minimal English writing and a semi-automatic ingestion process; cut timed mock and richer admin views first |
| 17 hours/week | about 204 hours | Reasonable P0 path with a constrained content bank and careful reuse of managed services |
| 25 hours/week | about 300 hours | Full proposed beta scope is plausible, including stronger automation, admin diagnostics and better hardening |

The stage totals are larger than calendar capacity because some work is optional depth, ranges overlap and content operations can run beside engineering. The team must reforecast weekly.

## 23. Scope-cut order if behind schedule

Cut in this order while preserving the core learning test:

1. Rich analytics dashboards; keep essential event and error logging.
2. Automated pulling from external paper sites; retain manual upload.
3. Sophisticated admin editing; retain upload, status and publish/unpublish.
4. Retry-queue sophistication; retain basic progress and Give up history.
5. Timed Mathematics mock; retain topic practice.
6. Secondary English objective formats; retain core grammar/vocabulary types.
7. Submission-history polish; retain latest feedback.
8. Sec 1 content breadth if sources are not ready; keep the schema and clearly limit cohort recruitment.

Do not cut:

- authentication and RLS;
- deterministic Mathematics marking;
- source crops and verified answers;
- solution-access enforcement;
- immutable attempts and essay submissions;
- rate limits and AI spending controls;
- error monitoring and recovery of student work.

## 24. Main risks and stage responses

| Risk | Earliest detection | Planned response |
|---|---|---|
| OCR corrupts mathematics | Stage 4 fixtures | Keep crop as source, use OCR only for anchors, vision-extract structured data |
| Question/solution mismatch | Stage 5 golden set | Multi-signal pairing, independent verification, hide ambiguity |
| Answer checker rejects valid forms | Stage 3 tests | Typed `AnswerSpec`, golden variants, gradual format expansion |
| Symbolic parser abuse or hangs | Stage 3 security tests | Allowlist, input limits, isolated timeout |
| Essay scores vary too much | Stage 7 evaluations | Versioned rubric prompt, structured criteria, repeat-run consistency check |
| AI cost loop | Stage 8 metrics | Idempotency, caching, retry cap and hard budget |
| Schedule consumed by OCR | Stage 4 review | Keep manual-import fallback and prioritise high-value chapters |
| Too little content per topic | Stage 9 coverage report | Process by coverage gap, launch with fewer chapters if necessary |
| Student loses essay draft | Stage 7 browser tests | Server autosave, visible status, recovery tests |
| Student accesses answer early | Stage 3 API tests | Server-side entitlement check; never trust UI state |
| One founder becomes bottleneck | Every stage review | Pairing, written runbooks and cross-review |

## 25. Weekly execution cadence

### Monday or start of work week

- Review the next milestone and available hours.
- Pull only the highest-priority ready tickets into the week.
- Confirm dependencies and one accountable owner per ticket.
- Reserve capacity for integration and bugs.

### During the week

- Merge small changes frequently.
- Keep main deployable.
- Demonstrate integrated behavior, not isolated components.
- Record actual hours or rough effort against estimates.
- Escalate a blocker after a two-hour investigation rather than silently losing days.

### End of week

- Run the milestone demo using a fresh account.
- Review failed tests, ingestion quality, AI cost and user-visible defects.
- Update the risk list and remaining estimates.
- Decide whether scope must be cut.
- Choose the next week's single most important user journey.

## 26. First 14 days — concrete checklist

This is the recommended immediate sequence from 8 September.

### Days 1–2

- Freeze P0 scope and provisional unlock rule.
- Create repository, workspaces, CI and preview deployment.
- Create Supabase projects and environment conventions.
- Select the 20-question golden set and two English prompts.

### Days 3–5

- Add identity/curriculum migrations and RLS.
- Implement invitation registration and track selection.
- Build student/admin shells.
- Manually prepare question and solution crops.

### Days 6–8

- Add Mathematics content, attempts and progress migrations.
- Implement the first four answer types and tests.
- Import the first five questions.
- Build the question player and attempt endpoint.

### Days 9–11

- Implement Give up and protected solution access.
- Complete all 20 question imports.
- Add dashboard progress.
- Add minimum essay submission and asynchronous feedback path.

### Days 12–14

- Run invitation-to-solution browser tests.
- Test RLS with two students and one admin.
- Fix deployment/mobile blockers.
- Demonstrate the 21 September vertical-slice gate.
- Reforecast Stages 4–10 using actual team velocity.

## 27. Final build-order summary

The recommended priority is:

1. Decisions and golden content.
2. Repository, CI and environments.
3. Database, RLS, invitations and track selection.
4. Manually seeded Mathematics vertical slice.
5. PDF rendering and cropping.
6. Vision extraction, topic classification and automated verification.
7. Curriculum progression, question breadth and timed mock.
8. Grammar/vocabulary and the complete essay flow.
9. Admin operations, monitoring, budgets and security controls.
10. Content scale-up.
11. Feature freeze, mobile QA, recovery testing and founder pilot.
12. Gradual December beta rollout.

When choosing between more automation and a working student journey, protect the working journey. When choosing between more questions and reliable questions, protect reliability.
