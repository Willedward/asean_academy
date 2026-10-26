# Layer 1 English foundation execution

**Updated:** 26 October 2026
**Audience:** secondary-school students in Indonesia and Southeast Asia preparing for
ASEAN Scholarship selection tests  
**Curriculum status:** draft pending English educator review  
**Implementation branch:** `feature/english-e71-paragraph-purpose`

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
| E2.1 pilot | Original sentence-boundary lesson, deterministic clause and editing items, grammar-specific error reflection and exit-ticket retry | Implemented as draft; English and editorial review pending |
| E5.1 pilot | Original informational passage, paragraph map, passage navigation and grouped main-idea, structure, synonym, reference, inference and evidence questions | Implemented as draft; English and editorial review pending |
| E5.2 pilot | Original informational passage and grouped pronoun, demonstrative, descriptive-phrase and cross-paragraph reference-chain questions | Implemented as draft; English and editorial review pending |
| E6.1 pilot | Prompt decoding through topic, command, audience, scope and personal-application analysis, with composition-specific error reflection | Implemented as draft; English and editorial review pending |
| E4.1 pilot | Original eight-gap function-word open cloze, inline entry, delayed feedback and reviewed alternatives | Implemented and hosted as draft; English and editorial review pending |
| E4.2 pilot | Original form-and-agreement open cloze covering tense, number, agreement, comparison, derivation and reflexive reference | Implemented and hosted as draft; English and editorial review pending |
| E4.3 pilot | Original lexical open cloze covering common collocations and fixed expressions with explicitly reviewed equivalents | Implemented and hosted as draft; English and editorial review pending |
| E4.4 pilot | Original cross-sentence open cloze covering reference chains, contrast, sequence and repeated actions | Implemented and hosted as draft; English and editorial review pending |
| E4.5 pilot | Original timed open-cloze checkpoint integrating grammatical, lexical and cohesion evidence | Implemented and hosted as draft; English and editorial review pending |
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
structure, synonym-in-context, reference, inference and evidence questions. E2.1 adds
sentence-boundary modelling, deterministic clause and editing questions, and
grammar-specific error reflection. E4.1 adds inline, keyboard-accessible open-cloze gaps,
exact reviewed short-text answers, explicit accepted alternatives, delayed group feedback,
passage revision pins and open-cloze-specific error reflection. Its hosted release requires
schema revision 202610220032. E4.2 reuses that interaction for controlled transformations:
learners identify an anchor word, locate the grammatical controller and supply the exact
tense, number, agreement, comparison, derived or reflexive form. It adds no paid model call
and requires no schema change beyond the deployed E4.1 revision.
E4.3 reuses the same learner and reviewer interaction for lexical retrieval. Learners read
the full word frame, state the intended meaning, check paragraph cohesion and then test
whether the completed expression is natural. Marking remains deterministic: only the
canonical completion and explicitly listed equivalents receive credit.
E4.4 makes paragraph-level evidence the assessed construct. Learners follow names,
pronouns and demonstratives, identify contrast, and reconstruct sequence or repeated
actions before completing each gap. Its original repair-café passage includes eight gaps,
delays feedback until the complete group is submitted and uses only deterministic marking.
E4.5 closes the module with an eight-minute, difficulty-5 checkpoint. Learners use a
complete-passage first pass, a targeted second pass and a final read while integrating
function words, fixed expressions, lexical fit, tense sequence and cross-paragraph cohesion.
The platform records the complete deterministic attempt; the eight-minute target is a
self-managed practice routine until the later full-mock timing milestone.
E5.2 builds directly on the E5.1 passage map. Learners locate a reference expression, match
candidate anchors for number, person and meaning, and substitute the selected anchor back
into the sentence. Its original mangrove-nursery passage assesses pronouns, demonstratives,
descriptive phrases and labels that continue across paragraph boundaries. All six responses
are marked together with exact choices or explicitly reviewed short-text alternatives.
E5.3 teaches learners to infer one precise word sense from the sentence frame and wider
paragraph, identify the word's grammatical role, compare the strength and tone of possible
replacements, then substitute a candidate into the original sentence. Its original
river-town archive passage assesses direct contextual meaning, exact word retrieval and
synonym replacements across adjective, verb and multiple-response formats. All six
responses use deterministic marking and reveal feedback only after the complete group.
E5.4 teaches a `Locate -> Link -> Prove` routine for retrieving stated evidence without
adding an inference. Learners parse the question target, locate the relevant sentence,
preserve the actor, action, cause, quantity and limitation, then check that their answer is
fully supported. Its original school heat-mapping report assesses purpose, controlled
procedures, an explicit cause, an approved proposal, and the distinction between a measured
result and an unproven causal claim. The six-part group uses deterministic marking and keeps
answers protected until submission.
E5.5 teaches a `Claim -> Clues -> Limit` routine for combining textual evidence without
importing an outside assumption. Learners connect at least two clues, run removal and
strength tests, distinguish association from causation, and preserve the observed population,
place and period. Its original reusable-container trial assesses combined interventions,
operational intent, limits on market-wide claims, useful comparison data and the most
proportionate overall conclusion. All six responses are deterministic multiple-choice or
multiple-response items with grouped feedback.
E5.6 separates the main idea, writer's purpose and tone through a `Topic -> Message -> Job ->
Attitude` routine. Learners test a main idea against whole-passage coverage and emphasis,
identify purpose through the work the writer performs, and support tone with clusters of
evaluative and qualifying language. Its original library quiet-hour report balances rising
participation with examination timing, survey selection and inclusion concerns. Six grouped,
deterministically marked questions assess the central message, evaluative purpose, cautious
tone, the role of an observed detail, supporting evidence and the function of the conclusion.
E5.7 completes the reading module with a `Survey -> Solve -> Park -> Return` routine across
two passages. Its eighteen-minute rehearsal target reserves one minute for route planning,
seven minutes per passage and a three-minute return-and-check buffer; this is explicitly a
training target rather than an official exam allocation. Original informational and reflective
harbour texts supply four questions each, integrating comparison control, contextual meaning,
main idea, bounded inference, attitude change, detail function and tone. All eight responses
are deterministic and reveal feedback only after the complete two-passage group.
E6.1 begins the composition sequence without requiring an essay-marking provider. Learners
apply a `Topic -> Command -> Audience -> Scope -> Personal application` check to an original
practice prompt, distinguish requirements from optional choices and write a one-sentence
task contract before planning. Its six-part exit ticket is marked deterministically as one
group. Composition-specific reflection records topic drift, command loss, audience or scope
errors, and missing evidence plans. This milestone does not yet create or score an essay;
draft autosave, immutable submission and calibrated feedback remain behind later gates.
E6.2 turns the decoded task contract into a usable idea pool. Learners search experience,
observation, school learning and honestly signalled plausible scenarios, then develop each
candidate with an `Idea -> Situation -> Action -> Result or learning` frame. The lesson keeps
generation separate from later selection and ordering, rejects topic drift and vague claims,
and explicitly prevents invented events from being presented as true memories. Its six-part
exit ticket remains deterministic and groups feedback until every response is submitted.
E6.3 screens that pool with a `Relevant -> Developable -> Linked` test. Learners preserve
one central school-learned skill, combine overlapping candidates, assign each retained idea
a distinct job and order the result by what the reader needs first. Its worked sequence uses
two connected moments from one charity-sale example to replace shallow list planning with
depth. Six grouped, deterministic questions assess selection, overlap, sequence and focus.
E6.4 converts the selected sequence into one central response. Learners name the transferred
school learning, its different application and the insight their evidence will demonstrate;
assign each paragraph a distinct job; and run a link-back check against the focus. Thread-word
variation maintains unity without mechanical repetition. Six grouped deterministic questions
assess the focus statement, paragraph contributions, detail drift and unsupported overclaiming.
E6.5 completes the planning sequence with a five-minute rehearsal routine. The target is
explicitly instructional rather than an official exam allocation: learners check the task and
focus, plan two evidence-bearing body jobs, sketch the introduction and conclusion, add
relationship transitions and audit coverage. Its worked plan carries the charity-sale example
from initial organisation through a rain disruption to a bounded future transfer. Six grouped,
deterministic questions assess the routine, compact notes, paragraph development, conclusion
job and final plan audit without requiring an essay-marking provider.
E7.1 begins paragraph development by turning each plan job into one paragraph promise.
Learners organise explanatory paragraphs through purpose, evidence and meaning; recognise
dominant narrative functions; place boundaries where the controlling job changes; and apply a
short reverse outline to expose repetition, mixed purposes and purposeless detail. Its worked
examples continue the E6 charity-sale route so that the instructional change—from planning to
draft control—is visible. Six grouped deterministic questions assess purpose, evidence
selection, boundaries, narrative function and reverse-outline repair.

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

E4.1–E4.5 form the complete hosted open-cloze learning sequence, E5.1–E5.7 complete the
first reading-comprehension progression and E6.1–E6.5 complete the first composition-planning
progression. E7.1 is the first paragraph-development review candidate. Apply migration
`202610250033`, import the exact draft revisions, verify the authenticated E6 and E7.1 learner
journeys, and confirm `ex-l1-001` through `ex-l5-001` plus `ex-l1-002` each appear once in the
administrator queue with answers protected from learner responses. Then begin **E7.2 develop
with specifics**, teaching learners to explain significance through precise examples, actions,
observations and consequences. Human English and editorial approval remains a separate
publication gate for every lesson, passage and question revision.
