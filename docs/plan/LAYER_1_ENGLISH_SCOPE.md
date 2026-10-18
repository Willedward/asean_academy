# Layer 1 English scope

**Decision date:** 18 October 2026  
**Product phase:** Layer 1 invitation Beta  
**Audience:** Secondary-school students in Indonesia and Southeast Asia preparing for the ASEAN Scholarship selection process

**Curriculum:** [LAYER_1_ENGLISH_CURRICULUM.md](./LAYER_1_ENGLISH_CURRICULUM.md)

## Decision

Layer 1 includes both Mathematics and English as the academic product. English is a
Beta release requirement rather than a V2 add-on. Experience points, streaks,
leaderboards and the personalised study planner remain Layer 2 work and must not block
the Layer 1 release.

The existing English screens are a design and component foundation. They do not yet
have production English APIs, persistent domain models, deterministic marking, reviewed
content or essay-evaluation evidence. Moving English into Layer 1 therefore adds a real
engineering and content programme to the Beta critical path.

## Layer 1 boundary

The English Beta must provide these five learning strands:

1. grammar and usage;
2. vocabulary in context;
3. editing and cloze;
4. reading comprehension; and
5. essay writing with rubric-based feedback.

Objective English must support lessons, guided practice, hints, explanations, retry,
checkpoints, progress and reporting through the shared learning platform. The English
diagnostic uses objective questions only. Essay writing is excluded from baseline and
endline diagnostic scoring because a small Beta cannot yet establish a sufficiently
stable automated writing scale.

Essay feedback is a controlled Layer 1 feature:

- drafts autosave and remain editable;
- submission creates an immutable version;
- feedback is generated against a versioned, human-approved rubric;
- criterion feedback cites evidence from the submitted essay;
- the interface labels the result as an AI estimate rather than an official grade;
- a learner can report poor feedback and an administrator can inspect the associated
  rubric, model and prompt-policy versions;
- provider calls have server-owned quotas, idempotency, bounded retries and a disabled
  fallback; and
- raw essays, prompts and feedback are excluded from application logs and analytics.

Learners see a concrete essay-review allowance, such as reviews remaining for the Beta
period. They do not see model tokens or an abstract AI-credit balance.

## Source-scarcity policy

The English programme does not require a large collection of teacher-marked papers
before engineering can begin. Sparse papers are used to identify tested constructs and
style, not as a question bank to copy.

The content process is:

1. inventory every available paper, prompt, answer key, rubric and marked script;
2. create a versioned skills blueprint and record which source supports each construct;
3. have an English educator review the blueprint before high-volume authoring;
4. author original questions, passages, prompts and explanations against that blueprint;
5. keep practice, checkpoint, reserve and diagnostic exposure pools separate;
6. review every learner-visible item for English accuracy, editorial quality, ambiguity,
   cultural accessibility and answer determinism; and
7. use Beta response data to recalibrate difficulty without rewriting historical
   revisions.

Teacher-marked essays are most valuable for calibrating rubric judgements. Until enough
authentic scripts exist, build a small human-scored anchor set containing original essays
across several proficiency bands and common error patterns. AI essay feedback may not
advance from administrator evaluation to learners until it meets the agreed consistency,
safety, evidence and cost thresholds on that set.

## Technical architecture

### Shared platform

English reuses authentication, invitations, enrolment, courses, lessons, progress,
retry scheduling, checkpoints, content review, publication, audit, reports and release
identity. Subject-specific rules stay behind English domain interfaces rather than being
added as special cases to Mathematics checking.

### Objective-question domain

Add versioned contracts for:

- multiple choice and multiple response;
- approved short-text alternatives;
- passage-linked question groups;
- cloze gaps and editing corrections;
- deterministic answer normalisation; and
- authored explanations for correct and incorrect choices.

Passages are immutable, checksum-bound content revisions. A question pins one passage
revision so later edits cannot change a previously reviewed assessment silently.

### Essay domain

Add versioned essay prompts, rubrics, draft snapshots, immutable submissions, marking
jobs, criterion results, evidence spans, usage reservations and report/escalation state.
Essay marking runs asynchronously and must be replay-safe: retrying one job cannot spend
the allowance twice or create competing results for the same submission and policy.

The provider adapter uses structured output validation and records the provider, model,
rubric revision, prompt-policy revision, token use, cost, latency and safety result.
Development and browser tests use deterministic fixtures; live calls are reserved for
the hosted evaluation and invited Beta allowance.

### Web integration

Connect the existing English kit to generated API contracts for:

- English home and module map;
- lesson and objective-practice journeys;
- passage and cloze layouts;
- writing prompt, autosaved editor, submission and feedback;
- English diagnostic results and progress; and
- administrator content, essay-evidence and report views.

Remove XP, quest, streak and leaderboard dependencies from the Layer 1 English routes.
Those areas may remain hidden or display ordinary academic progress until Layer 2.

## Execution order

1. **E0 — Source inventory and blueprint:** define strands, outcomes, difficulty,
   assessment formats, review rubric and diagnostic coverage.
2. **E1 — English contracts:** implement passage, objective-response and deterministic
   marking schemas with migrations, generated clients and tests.
3. **E2 — Objective content pipeline:** extend claims, validation, duplicate checks,
   reviewer packets and the administrator review queue to English.
4. **E3 — Objective learner journey:** wire English home, lessons, practice, retry,
   checkpoints, progress and the objective diagnostic.
5. **E4 — Essay workflow:** implement prompts, autosave, immutable submission, rubric
   jobs, quotas, feedback, reports and the administrator evidence view.
6. **E5 — Content and calibration:** author and review the Beta course, diagnostic forms,
   writing prompts, rubrics and human-scored essay anchors.
7. **E6 — Hosted release:** import exact revisions, evaluate live essay marking, complete
   authenticated English journeys and add English evidence to the strict Beta gate.

Objective content authoring can continue while E1–E4 are implemented, once E0 freezes
the first blueprint and file contracts.

## Layer 1 exit criteria

English is ready for the invitation Beta only when:

- every Beta strand has reviewed lessons and sufficient isolated practice, checkpoint,
  reserve and diagnostic content;
- objective responses are marked deterministically and ambiguous alternatives have been
  resolved through review;
- the baseline and endline English diagnostic forms are disjoint, reviewed and versioned;
- the existing English UI runs against real authenticated APIs and persists progress;
- essay drafts survive refresh, submissions are immutable and marking jobs are
  idempotent;
- the essay evaluation set passes the recorded quality, safety, latency and cost gates;
- the full English journey passes mobile, keyboard, focus, screen-reader and error-state
  checks in hosted staging; and
- the strict release evidence binds the English course, question, diagnostic, rubric and
  prompt-policy revisions to the deployed Git SHA.

## Layer 2 boundary

Layer 2 owns:

- experience points and levels;
- streaks, freezes and the calendar;
- leaderboards and leagues;
- quests, badges, cosmetics and celebrations; and
- the personalised study planner.

Layer 1 continues recording immutable academic events so Layer 2 can derive rewards and
plans later without changing historical attempts or progress.
