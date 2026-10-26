# Layer 1 English scope (v2)

> **v2 proposal.** This file sits beside William's original `LAYER_1_ENGLISH_SCOPE.md`, which is unchanged.
> Nothing here replaces v1 until it is reviewed and accepted.

**Decision date:** 18 October 2026
**Revised:** 26 October 2026 (v2 proposal, pending William's approval)
**Product phase:** Layer 1 invitation Beta
**Audience:** secondary-school students in Indonesia and Southeast Asia preparing for the
ASEAN Scholarship selection process; Beta learners are Secondary 1 entry

**Curriculum:** [LAYER_1_ENGLISH_CURRICULUM_V2.md](./LAYER_1_ENGLISH_CURRICULUM_V2.md)
**Execution:** [LAYER_1_ENGLISH_FOUNDATION_EXECUTION_V2.md](./LAYER_1_ENGLISH_FOUNDATION_EXECUTION_V2.md)

## Decision

Layer 1 includes both Mathematics and English as the academic product. English is a Beta
release requirement rather than a V2 add-on. Experience points, streaks, leaderboards,
quests and the personalised study planner remain Layer 2 work and must not block the
Layer 1 release.

Moving English into Layer 1 adds a real engineering, content and review programme to the
Beta critical path. This revision makes that programme deliverable by:

- releasing English in **three stages** tied to the test date rather than all at once;
- giving essay feedback a **human-marking path** so the Beta does not depend on the AI
  evaluation passing first;
- naming the **roles and review hours** the content needs; and
- turning the exit criteria into checks with numbers.

## Naming

- **E0–E9** are curriculum modules (for example E4 Open cloze).
- **P0–P6** are build phases (for example P4 Writing workflow).

v1 used E0–E6 for both, which made "E4" ambiguous.

## Layer 1 boundary

### Strands

The English Beta provides six learning strands:

1. grammar, usage and editing;
2. vocabulary in context, with a vocabulary retrieval strand;
3. banked and open cloze;
4. reading comprehension, including constrained short answers;
5. composition writing with rubric-based feedback; and
6. orientation, the baseline and full mocks.

### Included

- Lessons, guided practice, hints, explanations, retry, checkpoints, milestones, progress
  and reporting through the shared learning platform.
- **Entry level** as a content and configuration setting. Only Sec 1 is released in the
  Beta; Sec 3 content may be authored and stored.
- **Routes:** starting level (Foundation, Standard, Accelerated) from the baseline, and
  course length (Full, Core, Sprint) from weeks to the test date. These are fixed lesson
  sets, not a schedule.
- **The English baseline** (about 20 objective items) and the eight-item English part of
  the combined product diagnostic, which is a subset of the baseline.
- **Design hooks that show academic progress only:** the module map (islands, lesson
  stops, milestone crossings, the learner's route), the word chest (words met and words
  due), and the harbour board (the four weekly strands with ticks).

### Excluded from Layer 1

- XP, levels, streaks, freezes, quests, badges, leagues and celebrations on English
  routes. The existing English kit screens that show them are revised (see Web
  integration).
- The personalised planner (week-by-week scheduling).
- Automated scoring of open-ended "own words" answers. These are practised with a model
  answer and a self-check list.
- Speaking and listening, which no candidate report mentions.
- The General Ability test that also forms part of the selection process. This is
  recorded as a product question, outside English.

### Writing in Layer 1

- One composition chosen from **two prompts**, in 30 minutes, at the configured length.
  Letters, narrative, reflective and descriptive writing are genres of that composition.
  There is no separate situational-writing task.
- Drafts autosave and remain editable. A submission creates an immutable version.
- **Feedback path 1, human markers (Beta default):** trained markers (former ASEAN
  scholars or English teachers) mark against the versioned rubric within 72 hours, with
  at least 20% of essays double-marked.
- **Feedback path 2, AI estimate:** enabled only when it passes the evaluation gate
  below. It is labelled an AI estimate rather than an official grade, cites evidence from
  the essay, and can be reported by the learner.
- **Self-review:** model essays and a checklist per criterion are always available.
- Learners see a concrete allowance, such as "4 essay reviews left in the Beta". They do
  not see model tokens or an abstract AI-credit balance.
- At least two timed compositions in each route are handwritten and then typed, because
  the test is on paper.

### The English diagnostic

The baseline and endline use objective questions only. Essay writing is excluded from
diagnostic scoring because a small Beta cannot establish a stable automated writing
scale. Baseline, endline and reserve forms are disjoint and built from the same
blueprint with matched difficulty.

## Safeguarding and privacy

Learners are children, and essays invite personal writing.

- **Safeguarding:** a submission that suggests a learner may be at risk (self-harm,
  abuse, danger at home) is held from automated feedback and routed to a named adult on
  the team within one working day, following a written procedure. The learner sees a
  kind message that a person will read their writing. Prompts avoid inviting disclosures
  of trauma.
- **Consent:** a parent or guardian consents to essay storage and marking during Beta
  onboarding. Retention periods for essays are set and enforced.
- **Logs and analytics:** raw essays, prompts and feedback are excluded from application
  logs and analytics. Markers see only what marking needs.
- **Legal check:** confirm obligations for minors' data under Singapore's PDPA and
  Indonesia's Personal Data Protection Law before inviting learners.

## Evidence and source-scarcity policy

The English programme does not need a large collection of teacher-marked papers before
engineering can begin. Sparse papers and reports identify constructs and style. They are
not a question bank to copy.

The content process is:

1. inventory every available paper, prompt, answer key, rubric, marked script and
   candidate report, each with year, entry level, country, city and authority;
2. keep a versioned skills blueprint recording which source supports each construct, and
   whether that construct is corroborated (at least three independent reports from the
   last three sittings at the same entry level) or configurable;
3. run the structured **test recall form** with Beta families, alumni and partner tutors
   (target: ten Indonesian reports from the 2025 and 2026 sittings by the end of
   January 2027), and again with every Beta learner after the 2027 test;
4. have an English educator review the blueprint before high-volume authoring;
5. author original questions, passages, prompts and explanations against that
   blueprint;
6. keep practice, retry, checkpoint, milestone, reserve, diagnostic and mock exposure
   pools separate;
7. review every learner-visible item for English accuracy, editorial quality, ambiguity,
   cultural accessibility, age-appropriateness and answer determinism; and
8. use Beta response data to recalibrate difficulty without rewriting historical
   revisions.

Teacher-marked essays are most valuable for calibrating rubric judgements. Until enough
authentic scripts exist, build an anchor set of original essays (at least two per band
per Sec 1 genre, plus edge cases), each scored by two trained raters.

## Roles

| Role | Responsibility | Proposed owner |
| --- | --- | --- |
| Engineering lead | Contracts, platform, learner and admin journeys, release evidence | William |
| English content lead | Authoring standards, lesson and passage authoring, model essays | To recruit |
| English reviewers (at least two) | Academic review of every lesson, passage, item and prompt; one must be a qualified English teacher | To recruit |
| Editorial reviewer | Clarity, consistency and age-appropriateness | To recruit, or one of the reviewers on a separate pass |
| Essay markers | Beta feedback, anchor scoring, double-marking | Former ASEAN scholars and teachers |
| Product and design | Learner experience, design hooks, the evidence collection plan, recruiting reviewers and markers | Alvaro |
| Safeguarding lead | The safeguarding procedure and response | Named founder |

The full course needs roughly 160–200 hours of English review (see the execution plan).
One reviewer at ten hours a week cannot finish before the Beta, so review capacity is a
release dependency, not an afterthought.

## Staged release

English learners need the full course and mocks before the test, not on Beta day one.
Releases follow the test date (the 2026 sitting was 11–12 April; the 2027 date must be
confirmed).

| Release | Target | What learners get |
| --- | --- | --- |
| A, Beta start | December 2026 | E0 baseline and routing; reviewed Core lessons for E1–E7 that are ready; retry; E1–E5 checkpoints as they pass review; writing with human feedback; module map, word chest and harbour board |
| B | Mid-January 2027 | The rest of the Core route, including E7–E9 Core lessons; milestones M1–M3; AI feedback only if the gate has passed |
| C | End of February 2027 | Two full mocks and a reserve; the endline; remaining Full-route lessons as they pass review |

Unreviewed content never appears to learners in any release. If a release target slips,
learners keep what is published and the map shows the next lessons as "coming soon".

## Technical architecture

### Shared platform

English reuses authentication, invitations, enrolment, courses, lessons, progress, retry
scheduling, checkpoints, content review, publication, audit, reports and release
identity. Subject-specific rules stay behind English domain interfaces rather than being
added as special cases to Mathematics checking. English lesson states and thresholds use
the shared model (`not_started` to `mastered`).

### Objective-question domain

Versioned contracts for:

- multiple choice and multiple response;
- approved short-text alternatives;
- **constrained short answers** (a word, phrase or number from the passage) with a word
  limit checked before submission;
- **self-checked open answers** (model answer and checklist; recorded, never scored);
- passage-linked question groups;
- cloze gaps and **editing corrections** (find the error, type the correction);
- deterministic answer normalisation;
- authored explanations for correct and incorrect choices; and
- a **rejected-answer log** with learner "my answer is also right" notes and a reviewer
  queue. Adding an alternative creates a new revision, and re-marking under it is
  audited.

Passages are immutable, checksum-bound content revisions with paragraph numbers and
optional underlined target spans. A question pins one passage revision.

### Vocabulary domain

- **Word profiles** (meaning, optional reviewed gloss, word class and family, two
  collocations, synonym and contrast notes, example and non-example, appearances in
  later content), each with a revision and review state.
- Template-generated recognition and completion items from reviewed profiles, with
  reviewer spot-checks.
- A per-learner word record on the shared retry schedule, which powers the word chest.

### Forms and routes

- **Form assembly:** checkpoints, milestones, diagnostics and mocks are versioned forms
  built from a blueprint, with no item in more than one pool.
- **Timed sections:** a section timer, an optional break between papers, and mocks that
  run after a Mathematics paper.
- **Routes:** lesson tags for Core and Sprint, the baseline's starting-level rule, and
  the weeks-to-test rule. All are deterministic and versioned.

### Essay domain

- Versioned prompts and prompt pairs, rubrics with band descriptors, model essays, draft
  snapshots, immutable submissions, marking jobs, criterion results, evidence spans,
  allowance reservations, and report and escalation state.
- **Human marking:** a marker queue, a marking view with rubric and anchors, double
  marking, adjudication and turnaround tracking.
- **AI marking:** asynchronous and replay-safe. Retrying one job cannot spend the
  allowance twice or create competing results for the same submission and policy. The
  provider adapter validates structured output and records provider, model, rubric
  revision, prompt-policy revision, token use, cost, latency and safety result.
- **Robustness:** the essay text is treated as data, never as instructions, so an essay
  that says "ignore the rubric" cannot change the marking. Anchors include such essays.
- **Integrity:** overlap checks against the learner's earlier essays and published model
  essays.
- **Safeguarding flags** that hold a submission and notify the safeguarding lead.

Development and browser tests use deterministic fixtures. Live calls are reserved for the
hosted evaluation and the invited Beta allowance.

### AI feedback evaluation gate

AI feedback may move from administrator evaluation to learners only when all of these
hold on the anchor set and a held-out set of Beta essays:

| Check | Threshold (initial, adjustable by the team) |
| --- | --- |
| Agreement with the adjudicated human band, per criterion | Exact agreement no more than 10 points below human–human exact agreement on the same essays; within one band at least 95% |
| Bias | No criterion more than 0.3 of a band higher or lower than humans on average |
| Consistency | Same band on at least 90% of criterion judgements across five reruns |
| Evidence | 100% of quoted spans found word-for-word in the essay |
| Edge cases | Every off-topic, memorised, too-short and "ignore the rubric" anchor handled correctly |
| Safety and tone | No unkind, unsafe or age-inappropriate output in a full human read of the evaluation outputs; every safeguarding anchor held and routed |
| Latency and cost | p95 under two minutes; cost per review below the ceiling agreed by the founders |

If the gate does not pass, the Beta continues with human feedback.

### Web integration

Connect the English kit to generated API contracts for:

- the English home and **module map** (islands, stops, crossings, route) with ordinary
  academic progress;
- lesson and objective-practice journeys;
- passage and cloze layouts: passage and questions side by side on wide screens and as
  tabs on phones, paragraph numbers, underlined targets, highlighting, a visible word
  bank without drag-and-drop;
- the **word chest** and **harbour board**;
- the writing prompt pair, prompt choice, autosaved editor with word count, submission,
  marking status and feedback;
- the English baseline, results, route and progress; and
- administrator views for content, rejected answers, marking queues, essay evidence,
  safeguarding holds and reports.

The existing kit screens need these revisions:

- replace "Situational writing" and "Continuous writing" with one composition and a
  choice of two prompts;
- replace the 30-mark rubric (task fulfilment 10, language and organisation 20) with the
  five-criterion, four-band rubric;
- replace grammar units with stars by modules and lessons; and
- remove English quests, XP chips, "+XP when you submit" and badges from Layer 1 routes.
  They return in Layer 2.

## Build phases

1. **P0 Evidence and blueprint:** strands, outcomes, entry levels, routes, difficulty,
   assessment formats, review rubric, diagnostic coverage and the evidence collection
   plan.
2. **P1 Contracts:** passage, objective-response, constrained-answer, editing, word
   profile, form and essay schemas, with migrations, generated clients and tests.
3. **P2 Content pipeline:** claims, validation, duplicate checks, reviewer packets, the
   administrator review queue and the rejected-answer queue.
4. **P3 Objective learner journey:** English home and map, lessons, practice, retry,
   checkpoints, milestones, progress, the baseline and routing, the word chest and the
   harbour board.
5. **P4 Writing workflow:** prompts, prompt choice, autosave, immutable submission,
   human marking, allowance, safeguarding, reports and the evidence view; then AI
   marking behind the gate.
6. **P5 Content and calibration:** author and review the course by release stage, the
   diagnostic and mock forms, prompts, rubric descriptors, anchors and marker training.
7. **P6 Hosted release:** import exact revisions, run the AI evaluation, complete
   authenticated English journeys and add English evidence to the strict Beta gate.

Objective content authoring continues while P1–P4 are implemented. P4 and the anchor set
start now, in parallel, because they depend on people outside engineering.

## Layer 1 exit criteria

English is ready for Release A only when:

- the baseline form, its routing rule and the eight-item diagnostic subset are reviewed
  and versioned;
- at least one reviewed lesson exists in every Core-route module from E1 to E6, with
  reviewed exit tickets and retry forms;
- objective responses are marked deterministically, the rejected-answer queue works, and
  ambiguous alternatives found in review are resolved;
- the human-marking path works end to end (submission, queue, marking, feedback,
  double-marking) with at least three trained markers;
- the safeguarding procedure is written, owned and tested with a fixture essay;
- essay drafts survive refresh, submissions are immutable and marking jobs are
  idempotent;
- the English journey passes mobile, keyboard, focus, screen-reader and error-state
  checks in hosted staging; and
- the strict release evidence binds the English course, question, form, rubric and
  prompt-policy revisions to the deployed Git SHA.

Release B additionally requires every Core-route lesson and milestones M1–M3 to be
reviewed. Release C additionally requires two reviewed mock forms and a reserve, and the
endline. AI feedback is an addition to any release once its gate passes, never a
precondition.

## Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| The format evidence is thin and varies by year | Practice targets the wrong parts | Configurable blueprint, variants in mocks, the recall form, post-test debrief |
| Review capacity | Content cannot be published in time | Recruit two or more reviewers now; staged release; breadth before depth |
| Passage volume (about 85 needed, 14 drafted) | Retry and mocks repeat or are missing | Passage production plan in the execution document; reuse lesson examples within the lesson pool only |
| AI essay feedback fails its gate | No essay feedback | Human marking is the Beta default |
| Content is drafted with AI assistance | Plausible but wrong English, or unnatural passages | Full human review; provenance recorded; reviewers try to break every item |
| Deterministic marking rejects valid answers | Learners lose trust | Rejected-answer log, weekly review, audited re-marking |
| Typed practice for a handwritten test | Timing and length surprises on the day | Handwritten timed essays in every route |
| Essays by minors include disclosures | Harm if mishandled | Safeguarding procedure and holds |
| Memorised template essays | Learners practise the wrong thing | Integrity check and W1 Relevant |
| 51 to 55 lessons do not fit the weeks to the test | Learners never reach writing or mocks | Core and Sprint routes; Releases B and C by date |

## Layer 2 boundary

Layer 2 owns:

- experience points and levels;
- streaks, freezes and the calendar;
- leaderboards and leagues;
- quests, badges, cosmetics and celebrations; and
- the personalised study planner.

For English, Layer 2 attaches these to events Layer 1 already records: lessons proficient,
words reviewed in the word chest, harbour-board strands completed, essays submitted and
improved on a new prompt. Layer 1 records immutable academic events so Layer 2 can derive
rewards and plans later without changing historical attempts or progress.
