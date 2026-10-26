# Layer 1 English foundation execution (v2)

> **v2 proposal.** This file sits beside William's original `LAYER_1_ENGLISH_FOUNDATION_EXECUTION.md`, which is unchanged.
> Nothing here replaces v1 until it is reviewed and accepted.

**Updated:** 26 October 2026 (v2 proposal, pending William's approval)
**Audience:** secondary-school students in Indonesia and Southeast Asia preparing for
ASEAN Scholarship selection tests; the Beta is Secondary 1 entry
**Curriculum status:** v2 proposal; English-educator review pending
**Status read from:** `feature/bulk-question-authoring-pipeline` at `d3537be`
(26 October 2026, after E8.3 was merged)

Scope and boundaries: [LAYER_1_ENGLISH_SCOPE_V2.md](./LAYER_1_ENGLISH_SCOPE_V2.md).
Learning design: [LAYER_1_ENGLISH_CURRICULUM_V2.md](./LAYER_1_ENGLISH_CURRICULUM_V2.md).

## Naming

- **E0–E9** are curriculum modules and **E1.1** etc. are lessons.
- **P0–P6** are build phases. v1 called these E0–E6, which clashed with the modules.

## Product boundary

English is part of the Layer 1 invitation Beta. The academic product contains
Mathematics and English. Experience points, streaks, leaderboards, quests and the
personalised study planner remain Layer 2 work.

The English course prepares learners for the best-supported reported test constructs. It
does not claim to reproduce a confidential or official MOE syllabus. Durations, task
types, counts and writing length remain configurable per entry level until corroborated.

English ships in three releases tied to the test date (see the scope document): Release A
at Beta start in December 2026, Release B in mid-January 2027 and Release C by the end of
February 2027.

## Learner experience

Layer 1 English provides:

1. an English home and **module map** (islands, lesson stops, milestone crossings and the
   learner's route) with ordinary academic progress;
2. 55 core lessons across E0–E9 in a spiral curriculum, filtered by starting level and
   course length (Full, Core, Sprint);
3. sentence vocabulary, grammar and editing practice;
4. accessible banked-cloze and open-cloze passage groups;
5. reading comprehension with reference, synonym-in-context, retrieval, inference,
   purpose and tone, and constrained short-answer questions;
6. an English baseline with routing, and disjoint endline and reserve forms;
7. retry with parallel forms, module checkpoints with retry forms, milestones M1–M4,
   progress and reporting through the shared platform;
8. the **word chest** (vocabulary retrieval) and the **harbour board** (the four weekly
   strands);
9. a writing workflow: one composition chosen from two prompts, autosave, immutable
   submissions, **human feedback by trained markers** in the Beta, and AI feedback
   labelled as an estimate once it passes its gate; and
10. two full mocks and a reserve, run after a Mathematics paper.

Objective lessons and practice use authored explanations and deterministic marking. They
do not require a paid model call.

## Curriculum structure

| Stage | Modules | Purpose |
| --- | --- | --- |
| Orientation | E0 | Know the paper, establish the baseline and error language. |
| Build the toolkit | E1–E2 | Learn transferable vocabulary, grammar, editing and cohesion. |
| Apply it to the paper | E3–E5 | Practise banked cloze, open cloze and reading. |
| Compose and perform | E6–E9 | Plan, develop, edit and complete timed writing. |

The versioned catalogue at `backend_resources/english/v1/catalogue.json` is the
executable source of truth. v2 adds four lessons (E2.7, E5.8, E9.6, E9.7), a `position`
for display order, `entry_level`, and `route_tags` (`core`, `sprint`). **No existing
stable key, lesson code or outcome code changes meaning.** E6.1 keeps its title; its next
revision adds choosing between two prompts.

Every objective lesson follows this fixed sequence: retrieval warm-up, explicit model,
worked analysis, guided practice, independent application, error classification and exit
ticket. Writing lessons use the same contract with Model, Practise, Reflect content
inside the sections.

## Content and assessment rules

- All learner passages, prompts, questions and explanations are original or correctly
  licensed. Recalled live questions identify constructs only and may not be copied.
- Every curriculum claim points to a versioned source record and states its limitation.
- Passages are immutable revisions with paragraph numbers and optional underlined spans.
  A question pins the passage key, revision and SHA-256 checksum.
- Single choice and multiple response items use exact option keys. Short text accepts
  only human-approved alternatives after Unicode, whitespace, case and optional terminal
  punctuation normalisation. There is no fuzzy or semantic marking.
- Rejected short-text answers are logged; valid alternatives are added by a new revision
  with audited re-marking.
- Open "own words" answers are self-checked against a model answer and are never scored.
- Passage and cloze groups reveal feedback after the group.
- **Exit tickets:** five items for sentence lessons, one passage group for passage
  lessons, pass at 75% or more without a hint. Every exit ticket has a parallel retry
  form.
- Lesson examples, guided practice, independent practice, exit tickets and their retry
  forms, retry review, checkpoints and their retry forms, milestones, baseline, endline,
  mock and protected reserve items use explicit exposure pools.
- Difficulty uses levels 1–5 and describes reasoning and language demand, not rare
  vocabulary.
- Every item, passage, prompt and profile carries an `entry_level`.
- Draft content is never learner-visible. Publication requires immutable English and
  editorial approval records for the exact revision.
- Provenance records whether content was drafted with AI assistance.

## Current status

### Platform (build phases)

| Phase | Deliverable | Status |
| --- | --- | --- |
| P0 | Evidence inventory, configurable exam blueprint, 10-module, 51-lesson catalogue | Implemented for v1; v2 sources, entry levels, routes and four lessons proposed |
| P1a | Passage, objective response, lesson and bank source contracts | Implemented |
| P1b | Deterministic choice, multiple-response and approved short-text marking | Implemented |
| P1c | Generated JSON Schemas and cross-file validator | Implemented |
| P1d | Database migrations for outcomes, passage revisions, objective revisions, error categories and composition items (028–033) | Implemented; `202610250033` still to be applied in hosted Supabase |
| P1e | Constrained short answer, editing correction, self-checked open answer, word profile, form and essay contracts | Not started |
| P2 | Claims, duplicate detection, reviewer packets, bulk admin review and importer | Implemented for objective content; hosted deployment pending |
| P2b | Rejected-answer log and reviewer queue | Not started |
| P3a | Authenticated English map, lesson, deterministic practice, error reflection, exit-ticket retry and progress | Implemented; hosted import and human review pending |
| P3b | Checkpoints, milestones, baseline and routing, endline, word chest, harbour board | Not started |
| P4 | Writing workflow (human path, then AI) | Not started |
| P5 | Remaining content, forms, prompts, rubric, anchors and marker training | Not started |
| P6 | Hosted import, accessibility, mobile, security, AI evaluation and strict release gate | Not started |

### Content on the branch

28 of 55 lessons, 38 question records (28 exit-ticket groups, 4 guided and 6 independent
items), 14 passages. Everything is **draft** with no English or editorial review recorded
(`reviewed_by: null`), and the provenance shows AI-assisted drafting.

| Module | Drafted | Practice on the branch | Notes |
| --- | --- | --- | --- |
| E0 Orientation | 0 of 3 | none | Baseline not started |
| E1 Vocabulary | 1 of 6 (E1.1) | 6 single items: 2 guided, 3 independent, 1 exit | |
| E2 Sentences | 1 of 7 (E2.1) | 6 single items: 2 guided, 3 independent, 1 exit | E2.7 is new in v2 |
| E3 Banked cloze | 1 of 4 (E3.1) | 1 exit group (8 gaps, 12-word bank) | |
| E4 Open cloze | 5 of 5 | 1 exit group of 8 gaps per lesson | Hosted as draft |
| E5 Reading | 7 of 8 (E5.1–E5.7) | 1 exit group of 6–8 parts per lesson; E5.7 uses a two-passage pair | E5.8 is new in v2 |
| E6 Prompt to plan | 5 of 5 | 1 six-part exit group per lesson | Deterministic planning questions; no essay yet |
| E7 Paragraphs | 5 of 5 | 1 six-part exit group per lesson | Deterministic questions; no essay yet |
| E8 Essay language | 3 of 5 (E8.1–E8.3) | 1 six-part exit group per lesson | E8.4 is next on the branch |
| E9 Forms and performance | 0 of 7 | none | Needs the writing workflow and mocks; E9.6 and E9.7 are new in v2 |

Passages run from 70 to 427 words.

### Gaps found in the current content

1. **No retry forms.** A failed exit ticket can only return the same item or passage,
   which tests memory rather than skill.
2. **Only E1.1 and E2.1 have guided and independent practice.** The other 26 drafted
   lessons have only their exit-ticket group.
3. **Single-item exit tickets** in E1.1 and E2.1 decide proficiency on one answer.
4. **Hints on exit-ticket items** have no rule. v2 sets one: a hint can be shown, but
   using it prevents proficiency.
5. **Passage lengths** are 70–427 words. That is suitable for lessons, but mock passages
   need 450–700 words for Sec 1.
6. **Lessons are ahead of the assessment layer.** 28 lessons exist, but there is no
   baseline, checkpoint, retry form, milestone or mock, and no learner has written a
   composition yet. The writing workflow depends on markers and anchors outside
   engineering, so it needs the longest lead time.
7. **Evidence records.** `sources.json` has one candidate report with no entry level, and
   `claims.json` is empty.
8. **Kit mismatch.** The English kit screens still show two writing types, a 30-mark
   rubric, grammar units with stars, quests and XP.
9. **Document drift.** The v1 status table lists pilots only up to E6.1; later lessons are
   described in prose only.

## Repository contract

The foundation root is `backend_resources/english/v1`:

- `sources.json`: evidence type, authority, entry level, supported claims and
  limitations;
- `catalogue.json`: exam blueprint per entry level, and all stable module, lesson and
  outcome identities with position, entry level and route tags;
- `lessons/`: versioned lesson sources;
- `passages/`: immutable checksum-bound passage revisions;
- `banks/`: counts, outcomes and exposure-pool distributions;
- `questions/`: versioned objective questions with deterministic response specs.

Proposed additions:

- `word_profiles/`: reviewed word profiles in weekly sets;
- `forms/`: checkpoint, milestone, baseline, endline, reserve and mock blueprints and
  form definitions;
- `writing/prompts/`, `writing/rubrics/` and `writing/models/`: prompt pairs, versioned
  rubrics with band descriptors, and model essays;
- `evidence/recall-form.md`: the structured test recall form; and
- anchors and marked essays stay **outside Git** in private storage, referenced by
  checksum.

The Pydantic contracts, marking and validation live in
`question_bank/src/question_bank/english_models.py`, `english_checking.py` and
`english_validation.py`.

Run the foundation checks from `question_bank/`:

```bash
uv run question-bank english-schema
uv run question-bank english-foundation-validate
uv run question-bank english-authoring-validate
uv run question-bank english-authoring-export \
  ../backend_resources/english/v1/authoring/batches/english-ev-b001.json \
  ../build/reviewer-english/english-ev-b001
uv run pytest tests/test_english_foundation.py
```

Use `--publish` only on a human-reviewed release candidate. Draft content must fail that
gate.

Proposed new validator checks: every exit ticket has a retry form; sentence exit tickets
have five items; every item has an `entry_level`; passage length is inside its pool band;
no item appears in two pools; route tags cover the Core and Sprint lesson lists; and no
existing stable key changes meaning.

## Content and review budget

Estimates to plan people and time. The English content lead should refine them.

| Content | Total needed | On the branch | Review time each | Review hours |
| --- | --- | --- | --- | --- |
| Lessons | 55 | 28 drafts | 45 min | about 41 |
| Passage groups | about 85 | 14 | 30 min | about 43 |
| Sentence-level items | about 400 | 12 | 4 min | about 27 |
| Word profiles | 300–400 | 0 | 3 min | about 18 |
| Writing prompts | about 80 | a few inside lessons | 5 min | about 7 |
| Model essays | about 30 | 0 | 20 min | about 10 |
| Anchor essays, two raters plus adjudication | 32–40 | 0 | 30 min per essay | about 22 |
| Editorial pass | | | about 15% of the above | about 25 |
| **Total** | | | | **about 160–200 hours** |

What each release needs:

- **Release A:** the baseline (20 items), about 18 Core lessons (the 15 Core lessons
  already drafted plus E0.1, E0.3 and at least one more E2 lesson), their retry
  forms, E1–E4 checkpoints, 6–8 prompt pairs, the rubric and 16 anchors. About 55–70
  review hours.
- **Release B:** the remaining Core lessons, M1–M3, the rest of the anchors and the timed
  prompt bank. About 60 hours.
- **Release C:** mock forms and reserve, the endline, and Full-route lessons. About
  50–60 hours.

With two reviewers at eight to ten hours a week each, Release A is reachable by early
December. With one, it is not.

## Workstreams

Each workstream has an owner, deliverables and a check that proves it is done.

### W1 Review capacity and the five-slice gate (critical path)

- **Owner:** Alvaro (recruiting), William (tooling).
- **Deliverables:** two English reviewers and an editorial pass; three or more trained
  essay markers; reviewer onboarding using the existing packet export; the hosted
  five-slice review (E1.1, E2.1, E3.1, E4.1, E5.1) completed with corrections.
- **Done when:** the first five lessons have recorded English and editorial approvals
  and are importable as published revisions.

### W2 Evidence and blueprint v2

- **Owner:** Alvaro (recall form and outreach), William (`sources.json`, catalogue).
- **Deliverables:** the curriculum section 1.2 sources added; the 2026 report's entry
  level recorded; the recall form live; catalogue v2 with new lessons, positions, entry
  levels and route tags.
- **Done when:** the validator passes on catalogue v2 and at least five new recall forms
  are in.

### W3 Baseline and routing

- **Owner:** William, with the English content lead.
- **Deliverables:** a 20-item baseline form, its eight-item diagnostic subset with answer
  carry-over, strand bands, the starting-level rule and the weeks-to-test rule.
- **Done when:** a fixture learner is routed correctly in every starting level and
  course length, and the subset is never shown twice.

### W4 Breadth-first lessons and retry forms

- **Owner:** English content lead.
- **Deliverables:** a retry form for each of the 28 drafted lessons; five-item exit
  tickets for E1.1 and E2.1; guided and independent sets for the 26 drafted lessons that
  lack them; the prompt-choice step in E6.1's next revision; then E0.1, E0.3, E2.7 and
  E5.8; then the rest of the Core route in module order.
- **Done when:** every Core lesson in the release has all its pools and passes review.

### W5 Checkpoints, milestones and mocks

- **Owner:** William (forms and timers), English content lead (content).
- **Deliverables:** form assembly, section timers and breaks; checkpoint and retry forms
  per module; M1–M4; two mock forms and a reserve; a mock mode that follows a
  Mathematics paper.
- **Done when:** no item appears in more than one pool, and a full mock runs end to end
  in staging with both papers locked before marking.

### W6 Vocabulary system

- **Owner:** William (domain and word chest), English content lead (profiles).
- **Deliverables:** the word profile contract, template items with spot-check flow, the
  learner word record on the shared retry schedule, the word chest view, and the first
  six weekly sets.
- **Done when:** a learner meets words in E1, sees them due in the word chest and answers
  generated items that a reviewer has spot-checked.

### W7 Writing workflow

- **Owner:** William (P4), English content lead (prompts, rubric, models), Alvaro
  (markers), named founder (safeguarding).
- **Deliverables, in order:**
  1. prompt pairs, the rubric with band descriptors, and model essays for the four Sec 1
     genres;
  2. the autosaved editor, prompt choice, word count, immutable submission and allowance;
  3. the human-marking queue, marking view, double-marking, adjudication and turnaround
     tracking;
  4. the safeguarding procedure, flags and holds; consent at onboarding;
  5. the integrity overlap check;
  6. the anchor set scored by two raters; and
  7. the AI marking adapter, evaluated against the gate in the scope document, kept
     admin-only until it passes.
- **Done when:** a fixture essay goes from draft to human feedback in staging, a
  safeguarding fixture is held and routed, and the anchor set has adjudicated scores.

### W8 Web integration, design hooks and kit revisions

- **Owner:** William (integration), Alvaro (design).
- **Deliverables:** the module map with route and crossings; passage layouts (side by
  side, tabs on phones, paragraph numbers, underlines, highlighting); the word chest and
  harbour board; kit revisions (one composition, the new rubric, modules instead of
  grammar units, no Layer 2 elements on English routes).
- **Done when:** the English journey passes the mobile, keyboard, focus, screen-reader
  and error-state checks in hosted staging.

### W9 Measurement

- **Owner:** William.
- **Deliverables:** per-strand baseline and endline reporting, retention at 7 and 14
  days, item health flags (proportion correct, discrimination, distractor use, time),
  the rejected-answer queue, and blind ordering for early and late essays.
- **Done when:** an admin can see each measure for the pilot cohort without exposing
  individual essays in analytics.

## Sequence to Release A

Dates follow the current stage plan (feature freeze 20 November, release candidate
30 November). If those dates have moved, keep the order and shift the weeks.

| Week | Focus |
| --- | --- |
| 26 Oct–1 Nov | Approve v2 plans; recruit reviewers and markers; launch the recall form; catalogue v2; finish the E8 lessons in flight; start P1e contracts and the human-marking design |
| 2–8 Nov | Baseline form and routing; retry forms and five-item exit tickets for drafted lessons; prompt pairs and rubric descriptors; first 16 anchors |
| 9–15 Nov | E0.1, E0.3, E2.7 and E5.8; E1–E5 checkpoints; the human-marking path in staging; the word profile contract and first sets |
| 16–22 Nov | Feature freeze on 20 Nov for Release A features: baseline and routing, retry forms, checkpoints, the map, word chest and harbour board, writing with human feedback, safeguarding |
| 23–29 Nov | Hosted accessibility and mobile pass; finish Release A reviews; marker calibration on the anchors |
| 30 Nov | Release candidate with English evidence in the strict gate |

Then Release B (mid-January: rest of Core, E7–E9 Core, M1–M3, AI feedback if it passes)
and Release C (end of February: mocks, endline, Full-route lessons), leaving March for
mocks and timed practice before an April test.

## Immediate next milestone

1. Finish what is in flight: apply migration `202610250033`, import the exact draft
   revisions, verify the E6–E8.3 learner journeys, and confirm each `ex-` item appears
   once in the administrator queue with answers protected. Finishing E8.4 and E8.5 is
   reasonable, because it completes the module.
2. **Before starting E9, switch to the assessment layer:** retry forms for the drafted
   lessons, the baseline and routing (W3), checkpoints (W5) and the writing workflow with
   human feedback (W7). E9 teaches timed writing and the full simulation, so it needs real
   compositions, feedback and mocks to exist.
3. Start reviewer and marker recruiting (W1) in the same week, because review is the
   slowest dependency. 28 drafted lessons are waiting for review.

Human English and editorial approval remains a separate publication gate for every lesson,
passage, question, profile and prompt revision.
