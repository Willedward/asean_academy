# Layer 1 English foundation execution

**Updated:** 27 October 2026
**Audience:** secondary-school students in Indonesia and Southeast Asia preparing for
ASEAN Scholarship selection tests  
**Curriculum status:** draft pending English educator review  
**Implementation branch:** `feature/english-e73-cohesion`

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
| E3b | English checkpoints and objective baseline/endline diagnostics | Implemented and deployed in preview with protected routing, deterministic scoring and learner UI; release remains draft-only |
| ENG-T3.1 | Versioned essay prompts, instructional rubrics and immutable database revisions | Implemented as draft; English/editorial review pending |
| ENG-T3.2 | Owned essay drafts, live word count, device recovery and revision-safe remote autosave | Implemented as draft |
| ENG-T3.3 | Deterministic pre-submit checks and immutable essay submission revisions | Implemented as draft; AI feedback and official scoring disabled |
| ENG-T3.4 | Learner self-review against the pinned instructional rubric | Implemented as draft; learner-authored, immutable and score-free |
| ENG-T3.5 | Asynchronous fixture marking jobs with no live provider calls | Not started |
| ENG-T3.6 | Server-owned essay feedback allowance and cost ceiling | Not started |
| ENG-T3.7 | Evidence-linked structured feedback with provider validation | Not started |
| ENG-T3.8 | Essay version history, feedback report and usefulness rating | Not started |
| ENG-T3.9 | Human-anchor calibration and provider quality/safety gate | Not started |
| ENG-T3.10 | Administrator evidence, privacy checks and live-provider release gate | Not started |
| E5 | Remaining lessons, banks, diagnostic forms, prompts, rubrics and essay anchors | Not started |
| E6 | Hosted import, accessibility, mobile, security, live essay evaluation and strict release gate | Not started |

The English design kit remains the visual reference. The authenticated learner routes at
`/english`, `/english/lessons/[lessonKey]`, `/english/practice/[sessionId]` and
`/english/diagnostics/[sessionId]` now connect the source contracts to production-shaped
APIs. The protected diagnostic pins four disjoint question groups and 20 scored parts,
withholds correctness until completion, records immutable evidence and unlocks the matched
endline only after the Sprint route is mastered. Draft content still fails closed when the
development content flag is disabled.

## Implemented repository contract

The foundation root is `backend_resources/english/v1`:

- `sources.json` records evidence type, authority, supported claims and limitations;
- `catalogue.json` defines the exam blueprint and all stable module, lesson and outcome
  identities;
- `lessons/` contains versioned lesson sources;
- `passages/` contains immutable checksum-bound passage revisions;
- `banks/` defines counts, outcomes and exposure-pool distributions; and
- `forms/` pins the disjoint baseline, endline, reserve, checkpoint and mock contracts; and
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
uv run question-bank english-route-review-export \
  ../build/reviewer-english/english-sprint-route-v3b \
  --route sprint
uv run pytest tests/test_english_foundation.py
```

The consolidated route export pins all 16 Sprint lessons, their parallel retries and both
checkpoint forms for every E0–E9 module. It writes exact fingerprints and separate pending
English/editorial decision columns without changing any content state.

The administrator content-review page exposes the identical scope as
`english-sprint-route-v3b-review`. Selecting it opens one consolidated 121-record session:
16 lessons, 20 checkpoint forms, 65 question groups and 20 passages. Every selected record
receives its own append-only English or editorial decision; excluded records remain pending
and appear in the fingerprint-bound correction export after changes are requested. Apply
migrations `202610290036_english_checkpoint_form_review.sql` and
`202610300037_english_diagnostic_sessions.sql` before using this scope and the protected
diagnostic in hosted staging. Approving the route does not publish it.

Use `--publish` only when checking a human-reviewed release candidate. The current pilot
must fail that gate because it is deliberately still draft content.

## Remaining execution order

### 1. Deploy and use E2: reviewable content pipeline

The source implementation now includes exclusive English batch claims, deterministic
exact and near-template duplicate checks, protected reviewer packet exports, passage-level
review, correction notes, subject-aware English and editorial decisions, consolidated
batch/unit/route review and an importer that refuses an invalid snapshot. Apply migrations
028–030, 036 and 037,
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
E7.2 develops those controlled paragraph jobs through a specificity ladder: assertion,
specific evidence, consequence and significance. Learners distinguish purposeful examples,
actions and observations from decorative detail; explain the local effect and its link to the
controlling insight; and select narrative details that change action or tension. The lesson also
rejects invented measurements and unsupported statistics as false precision. Six grouped,
deterministic questions assess relevant evidence chains, explanation, selective narrative
detail and honest specificity.
E7.3 connects those developed ideas without a rigid linking-word formula. Learners move from
given information to new information, maintain unmistakable reference chains, choose a
chronological, causal, problem-response or general-to-specific route, and select transitions
only when they reveal the real relationship. Thread words preserve the controlling concept
without synonym drift. Six grouped, deterministic questions assess ordering, reference,
cause-and-consequence language, connector repair and missing logical steps.
E7.4 frames the response with direct introductions and resolving conclusions. Learners use
the prompt as a contract, establish a focused route without a memorised hook, and finish by
showing what the developed evidence means rather than repeating the opening mechanically.
Six grouped deterministic questions assess orientation, scope, focus, proportionate insight
and genuine closure.
E7.5 teaches learners to read an original model for craft rather than copy its surface. A
reverse outline reduces the paragraph to functional moves, separates reusable structure from
topic-specific nouns and evidence, and adapts the causal sequence to a food-waste project.
Six grouped deterministic questions distinguish transfer from noun substitution, borrowed
evidence, structural mismatch and unsupported improvement.
E8.1 begins accurate and effective essay language with a four-part vocabulary check: meaning,
natural word partnership, register and evidence. Learners move from vague labels to observable
actions, strengthen load-bearing nouns and verbs, retain useful repetition for cohesion, and
reject thesaurus drift, inflated formality and unsupported absolutes. Its original reading-room
editing task supplies verified notes so all six grouped deterministic questions can distinguish
genuine precision from invented detail or exaggerated impact.
E8.2 builds sentence variety on clause control rather than decorative pattern changes. Learners
distinguish independent and dependent clauses, use coordination, subordination and relative
clauses according to the relationship between ideas, and create emphasis with deliberately
placed short sentences. A four-pass check catches fragments, run-ons or comma splices,
misleading connectors, agreement drift, unclear reference and overloaded sentences. Its
original media-club editing task uses six grouped deterministic questions to assess controlled
combination without changing the verified evidence.
E8.3 makes logical relationships explicit before a learner selects a connector. Cause and
consequence are separated from sequence, contrast is distinguished from concession, and
qualification names the precise population, setting, period or outcome beyond which a claim
cannot travel. Learners also check the grammar and punctuation required by clause markers,
noun-phrase markers and sentence connectors. Its original water-refill pilot supplies bounded
observations for six grouped deterministic questions that reject decorative linking phrases,
doubled markers and unsupported long-term causation.
E8.4 establishes a four-pass editing ladder: task and focus, organisation, development, then
sentence control and conventions. Learners compare a draft with the prompt contract, reverse-
outline paragraph jobs, repair evidence and explanation, remove irrelevant material and only
then correct grammar, spelling and punctuation. Its original basil-seedling response supplies
bounded notes for six grouped deterministic questions that distinguish higher-order revision
from surface correction and reject an unsupported universal conclusion.
E8.5 closes the language-control sequence with a personal error log grounded in dated attempt
evidence. Learners distinguish a one-off slip from a recurring pattern, select two priorities by
recurrence, impact and actionability, and apply a `Notice -> Name -> Correct -> Check -> Retest`
routine. Its original eight-entry review record supplies six grouped deterministic questions on
precise pattern labels, clause-boundary and evidence-scope checks, fresh transfer tasks and the
evidence required before a pattern can be retired.
E9.1 begins the essay-form sequence with reflective and personal expository writing. Learners
distinguish reflection from event recount and generic moralising, then build an
`experience -> insight -> transfer` chain from bounded, truthful evidence. Its original basil
experiment and prospective book-drive record supplies six grouped deterministic questions on
controlling focus, relevant evidence, the reflective hinge, credible conditional transfer,
thoughtful limitation and whole-response structure.

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

The technical milestone sequence uses `ENG-Tx.y` identifiers so it cannot be confused with
curriculum lesson identifiers such as `E8.1`. **ENG-T3.1** supplies the checksum-pinned
original prompt and instructional rubric. **ENG-T3.2** supplies learner-owned mutable drafts
pinned to an exact prompt revision, optimistic edit revisions, immediate local-device
recovery, debounced remote autosave and an authenticated editor at
`/english/essays/[draftId]`. Migration `202610300039` stores the drafts without granting
learner write access outside the API. Stale tabs receive a conflict rather than silently
overwriting newer work.

**ENG-T3.3** now adds deterministic server-side pre-submission checks and migration
`202610300040`. A learner must review the exact saved edit revision and explicitly confirm
before the API creates an immutable, owner-readable snapshot pinned to the exact prompt and
instructional-rubric revisions. Each later draft edit can become a separately numbered
submission revision; the same edit revision cannot be submitted twice. The checks report
structure and revision integrity only, continuous writing time is explicitly not claimed,
essay bodies remain out of application logs, and no model provider or official score is
involved.

**ENG-T3.4** now adds migration `202610310041` and a learner self-review workspace bound to
one exact immutable essay submission and its pinned instructional-rubric revision. For every
rubric criterion, the learner selects the closest descriptor, cites evidence from the submitted
essay and records one specific improvement action, then writes an overall reflection and
acknowledges that this is not an official ASEAN Scholarship score or prediction. The API checks
that every pinned criterion is covered, stores only one immutable review per submission and
allows a later submission revision to have its own review. The learner can restore both the
exact submitted essay and completed review after reload. No aggregate mark is calculated, the
essay snapshot is never changed, and no model provider is called.

The next independently executable engineering milestone is **ENG-T3.5 — asynchronous fixture
marking jobs with no live provider calls**. It should prove queue ownership, retries,
idempotency, failure recovery and structured feedback persistence using deterministic local
fixtures before any paid or external essay-marking provider is enabled.

E4.1–E4.5 form the complete hosted open-cloze learning sequence, E5.1–E5.7 complete the
first reading-comprehension progression, E6.1–E6.5 complete the first composition-planning
progression and E7.1–E7.5 complete the first paragraph-development, response-framing and
model-transfer sequence. E8.1–E8.5 now complete the language-control sequence with precise,
evidence-bounded vocabulary, purposeful sentence variety, explicit logical relationships and
a meaning-first editing order followed by a two-pattern correction-and-retest routine.
E9.1 now opens the final composition sequence with a complete experience–insight–transfer
lesson and protected deterministic exit ticket.
Apply migration `202610250033`, import the exact draft revisions, verify the authenticated
E6–E9.1 learner journeys, and
confirm `ex-l1-001` through `ex-l5-001`, `ex-l1-002` through `ex-l5-002`, and `ex-l1-003`
through `ex-l5-003`, plus `ex-l1-004`, each appear once in the administrator queue with answers
protected from learner responses. Then begin **E9.2 narrative writing**, teaching learners to
shape setting, conflict, purposeful detail, turning point and resolution without assuming that
every reported test sitting offers a narrative prompt. Human English and
editorial approval remains a separate publication gate for every lesson, passage and question
revision.
