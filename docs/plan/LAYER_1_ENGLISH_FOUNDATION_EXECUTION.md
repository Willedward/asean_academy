# Layer 1 English foundation execution

**Updated:** 21 October 2026
**Audience:** secondary-school students in Indonesia and Southeast Asia preparing for
ASEAN Scholarship selection tests  
**Curriculum status:** draft pending English educator review  
**Implementation branch:** `feature/english-e5-reading-comprehension`

## Product boundary

English is part of the Layer 1 invitation Beta. The academic product contains
Mathematics and English. Experience points, streaks, leaderboards and the personalised
study planner remain Layer 2 work.

The English course prepares learners for the best-supported reported test constructs. It
does not claim to reproduce a confidential or official MOE syllabus. Durations, task
types and approximate writing length remain configurable until they are corroborated by
stronger evidence.

## Learner experience

Layer 1 English will provide:

1. an English home and module map with ordinary academic progress;
2. 51 core lessons across E0–E9, using a spiral curriculum rather than isolated chapters;
3. sentence vocabulary, grammar and editing practice;
4. accessible banked-cloze and open-cloze passage groups;
5. reading comprehension with synonym-in-context, reference, retrieval, inference,
   purpose and tone questions;
6. objective baseline and endline diagnostics with disjoint forms;
7. retry scheduling, module checkpoints, progress and reporting through the shared
   platform; and
8. a controlled writing workflow with autosave, immutable submissions and rubric-based
   AI feedback labelled as an estimate.

Objective lessons and practice use authored explanations and deterministic marking. They
do not require a paid model call. Essay feedback is the only planned learner-facing
English feature that may call an AI provider, and it remains disabled until a
human-scored anchor set passes the recorded quality, safety and cost gates.

## Curriculum structure

| Stage | Modules | Purpose |
| --- | --- | --- |
| Orientation | E0 | Establish the baseline, paper model and error language. |
| Build the toolkit | E1–E2 | Learn transferable vocabulary, grammar and cohesion. |
| Apply it to the paper | E3–E5 | Practise banked cloze, open cloze and reading. |
| Compose and perform | E6–E9 | Plan, develop, edit and complete timed writing. |

The versioned catalogue at
`backend_resources/english/v1/catalogue.json` is the executable source of truth. It
contains 10 modules and 51 stable lesson/outcome identities. The full learning rationale
and lesson descriptions remain in
[LAYER_1_ENGLISH_CURRICULUM.md](./LAYER_1_ENGLISH_CURRICULUM.md).

Every objective lesson follows this fixed sequence:

1. retrieval warm-up;
2. explicit model;
3. worked analysis;
4. guided practice;
5. independent application;
6. error classification; and
7. exit ticket.

Writing lessons use the same contract with Model–Practice–Reflect content inside the
sections.

## Content and assessment rules

- All learner passages, prompts, questions and explanations are original or correctly
  licensed. Recalled live questions identify constructs only and may not be copied.
- Every curriculum claim points to a versioned source record and states its limitation.
- Passages are immutable revisions. A question pins the passage key, revision and SHA-256
  checksum.
- Single choice and multiple response items use exact option keys. Short text accepts
  only human-approved alternatives after Unicode, whitespace, case and optional terminal
  punctuation normalisation. There is no fuzzy or semantic marking.
- Passage and cloze groups reveal feedback after the group, preventing an early answer
  explanation from disclosing later answers.
- Lesson examples, guided practice, independent practice, exit tickets, retry review,
  checkpoints, baseline, endline, mock and protected reserve items use explicit exposure
  pools.
- Difficulty uses levels 1–5. Difficulty describes reasoning and language demand, not
  merely rare vocabulary.
- Draft content is never learner-visible. Publication requires immutable English and
  editorial approval records for the exact revision.

## Feature and implementation status

| Milestone | Deliverable | Status on this branch |
| --- | --- | --- |
| E0 | Evidence inventory, configurable exam blueprint, 10-module/51-lesson catalogue | Implemented; educator review pending |
| E1a | Passage, objective response, lesson and bank source contracts | Implemented |
| E1b | Deterministic choice, multiple-response and approved short-text marking | Implemented |
| E1c | Generated JSON Schemas and cross-file validator | Implemented |
| E1d | Database migration for English outcomes, passage revisions and objective question revisions | Implemented; not applied to hosted Supabase |
| E1 pilot | Original E1.1 lesson and six vocabulary-in-context items | Authored as draft; human review pending |
| E2 | Claims, duplicate detection, reviewer packets, bulk admin review and importer | Implemented for English objective content; hosted migration/deployment pending |
| E3a | Authenticated English map, E1.1 lesson, deterministic practice, error reflection, exit-ticket retry and progress | Implemented; hosted migration/import/deployment and human review pending |
| E3.1 pilot | Original banked story-cloze lesson, checksum-pinned passage, shared word bank, keyboard-accessible gaps and passage-level feedback | Implemented as draft; English and editorial review pending |
| E5.1 pilot | Original informational passage, paragraph map, passage navigation and grouped main-idea, structure, synonym, reference, inference and evidence questions | Implemented as draft; English and editorial review pending |
| E3b | English checkpoints and objective baseline/endline diagnostics | Not started |
| E4 | Essay drafts, submissions, rubric jobs, quotas, feedback, reports and admin evidence | Not started |
| E5 | Remaining lessons, banks, diagnostic forms, prompts, rubrics and essay anchors | Not started |
| E6 | Hosted import, accessibility, mobile, security, live essay evaluation and strict release gate | Not started |

The English design kit remains the visual reference. The authenticated learner routes at
`/english`, `/english/lessons/[lessonKey]` and `/english/practice/[sessionId]` now connect
the E1.1 source contracts to production-shaped APIs. Draft content still fails closed
when the development content flag is disabled.

## Implemented repository contract

The foundation root is `backend_resources/english/v1`:

- `sources.json` records evidence type, authority, supported claims and limitations;
- `catalogue.json` defines the exam blueprint and all stable module, lesson and outcome
  identities;
- `lessons/` contains versioned lesson sources;
- `passages/` contains immutable checksum-bound passage revisions;
- `banks/` defines counts, outcomes and exposure-pool distributions; and
- `questions/` contains versioned objective questions with deterministic response specs.

The Pydantic contracts, marking and validation live in:

- `question_bank/src/question_bank/english_models.py`;
- `question_bank/src/question_bank/english_checking.py`; and
- `question_bank/src/question_bank/english_validation.py`.

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

Use `--publish` only when checking a human-reviewed release candidate. The current pilot
must fail that gate because it is deliberately still draft content.

## Remaining execution order

### 1. Deploy and use E2: reviewable content pipeline

The source implementation now includes exclusive English batch claims, deterministic
exact and near-template duplicate checks, protected reviewer packet exports, passage-level
review, correction notes, subject-aware English and editorial decisions, consolidated
batch review and an importer that refuses an invalid snapshot. Apply migrations 028–030
and deploy this branch before expecting these items in the hosted administrator queue.

### 2. Deliver the first vertical slice

Have an English educator review the E0 blueprint and E1.1 pilot, then import the approved
revision. The code path from English home to E1.1, deterministic attempts, error
classification, progress and failed-exit-ticket retry is implemented. Apply migrations,
import the approved revision and verify the authenticated hosted journey before
high-volume authoring.

### 3. Add passage formats

E3.1 exercises a selectable shared word bank, keyboard-accessible gaps, whole-passage
submission, group feedback and passage checksum pins. E5.1 adds a complete original
informational passage, paragraph navigation, a passage map and grouped main-idea,
structure, synonym-in-context, reference, inference and evidence questions. Implement
E2 grammar and editing next, followed by E4 open-cloze response patterns.

### 4. Build the objective diagnostic

Freeze a coverage matrix, author separate baseline and endline forms plus a protected
reserve, and reuse the deterministic scoring and recommendation service. Report outcomes
and starting path without presenting an official scholarship score.

### 5. Build writing without exposing uncalibrated grades

Implement prompt/rubric revisions, draft autosave, immutable submissions and a fixture
provider first. Create a human-scored anchor set before enabling live provider calls.
Show criterion evidence and actions, label the result as an AI estimate, and keep raw
essays out of application logs and analytics.

### 6. Complete content and hosted Beta evidence

Author in small batches while review continues independently. Before invitation Beta,
complete the original content inventory, accessibility checks, authenticated journeys,
rate limits, privacy checks, recovery states, exact revision imports and deployment
evidence bound to the Git SHA.

## Immediate next milestone

The next technical milestone is the **E2.1 grammar-and-editing vertical slice**. Build one
complete lesson and deterministic item group around sentence boundaries and agreement,
using the same protected review and draft-only learner path. Verify E1.1, E3.1 and E5.1
together on hosted review before scaling authoring. Human English and editorial approval
remains a separate publication gate for every lesson, passage and question revision.
