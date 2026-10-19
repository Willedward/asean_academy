# Layer 1 English foundation execution

**Updated:** 19 October 2026  
**Audience:** secondary-school students in Indonesia and Southeast Asia preparing for
ASEAN Scholarship selection tests  
**Curriculum status:** draft pending English educator review  
**Implementation branch:** `feature/english-layer1-foundation`

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
| E2 | Claims, duplicate detection, reviewer packets, bulk admin review and importer | Not started |
| E3 | Authenticated English home, lesson, practice, retry, checkpoint, progress and diagnostic APIs/UI | Not started |
| E4 | Essay drafts, submissions, rubric jobs, quotas, feedback, reports and admin evidence | Not started |
| E5 | Remaining lessons, banks, diagnostic forms, prompts, rubrics and essay anchors | Not started |
| E6 | Hosted import, accessibility, mobile, security, live essay evaluation and strict release gate | Not started |

The existing English screens in `apps/web/src/beta-kit/screens/english.tsx` remain UI
prototypes. They are useful design references but are not yet connected to these source
contracts or production APIs.

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
uv run pytest tests/test_english_foundation.py
```

Use `--publish` only when checking a human-reviewed release candidate. The current pilot
must fail that gate because it is deliberately still draft content.

## Remaining execution order

### 1. Finish E2: reviewable content pipeline

Extend the existing batch-claim workflow with English manifests, semantic duplicate
checks, passage-level review, review notes attached to a question or passage, and bulk
approval that writes an immutable decision per included revision. Build an importer that
accepts only a clean validation report.

### 2. Deliver the first vertical slice

Have an English educator review the E0 blueprint and E1.1 pilot. Import the approved
revision, connect the English home to E1.1, persist attempts, classify errors and route a
failed exit ticket into retry. This proves the complete source-to-learner path before
high-volume authoring.

### 3. Add passage formats

Author E3.1 and E5.1 pilot lessons to exercise selectable word banks, keyboard-accessible
gaps, passage navigation, group feedback and passage checksum pins. Then implement E2
grammar and E4 open-cloze response patterns.

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

The next technical milestone after this foundation is **E2 English content pipeline and
administrator review integration**. It unlocks parallel authoring and review, gives the
user a place to flag passage or question problems, and prevents high-volume English work
from repeating the slow item-by-item process previously used for Mathematics.
