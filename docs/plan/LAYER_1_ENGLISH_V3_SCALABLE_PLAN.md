# Layer 1 English V3: exam-aligned and scalable plan

**Prepared:** 28 October 2026
**Status:** V3-A merged; V3-B Sprint content, protected measurement, checkpoints, progress visibility and consolidated reviewer evidence structurally complete for human review
**Audience:** Secondary 1-entry ASEAN Scholarship candidates in Indonesia and Southeast Asia  
**Supersedes for decision-making:** the unapproved `docs/english-plans-v2` proposal  
**Integrated with:** the executable English catalogue without rewriting historical lesson or
question revisions

## Implementation status

V3-A now provides:

- a source-controlled reported exam profile with explicit evidence limits;
- explicit exclusion of an editing paper section and scored own-words short answers;
- Full-route metadata on all 51 stable lessons, while Core and Sprint membership remains
  intentionally unassigned pending outcome review;
- planned, protected 20-part baseline, matched endline and reserve-form contracts;
- part-level 75% proficiency scoring and persisted hint use;
- the checkpoint-ready `mastered` progress state;
- explicit parallel-form validation and one functional E1.1 parallel retry proving the
  end-to-end mechanism; and
- unchanged existing lesson and question revisions, with the retry form added as a new 42nd
  draft question.

The first V3-B milestone now additionally provides:

- fixed 32-lesson Core and 16-lesson Sprint routes, with Sprint a strict Core subset;
- coverage of E0 through E9 plus required orientation, baseline and timed-simulation anchors;
- automated route-size, subset, coverage and exact-membership regression checks; and
- route readiness reporting that distinguishes lesson, exit-ticket and parallel-retry coverage.

The Sprint-breadth increment now authors all five former gaps (E0.1, E0.2, E1.6, E2.2 and
E9.5) with complete lesson anatomy, five-decision exit tickets and distinct retry forms. The
current totals are 36 authored Full lessons, 25 authored Core lessons and all 16 Sprint
lessons. All Sprint lessons now have exit tickets and distinct parallel retries. The retry
increment adds ten question groups and six fresh passage assets. The protected-baseline
increment then adds four disjoint assessment groups and three passages. The matched-endline
increment adds eight more assessment groups and six fresh passages, bringing the draft
foundation to 74 question records and 29 passages. Baseline, endline and reserve each contain
exactly 20 scored parts—five each for vocabulary, banked cloze, open cloze and reading—and
withhold feedback until the form ends. Release remains blocked on checkpoints and human
approvals.

All three protected measurement forms are now draft and structurally complete, but cannot be
served to learners until the existing review and release gates pass. Remaining lesson gaps and
checkpoint content belong to the next V3-B increments. The E1 checkpoint vertical slice adds
two reciprocal five-part forms, two disjoint `module_checkpoint` groups and explicit mastery
scope for E1.1 and E1.6. The E0 checkpoint adds four fresh exam-strategy groups across two
reciprocal forms and scopes mastery to E0.1 and E0.2. This brings the draft foundation to 80
question records. The E2 checkpoint contributes two fresh difficulty-4 grammar groups and
scopes mastery to Sprint lesson E2.2, bringing the draft foundation to 82 question records.
The E3 checkpoint adds two fresh difficulty-4 banked-cloze groups and two complete narrative
passages, scopes mastery to Sprint lesson E3.1 and brings the draft foundation to 84 question
records and 31 passages. The E4 checkpoint contributes four fresh open-cloze groups across
four complete passages, scopes mastery to Sprint lessons E4.1 and E4.5 and brings the draft
foundation to 88 question records and 35 passages. The E5 checkpoint
adds two reciprocal five-decision paired-passage forms, scopes mastery to Sprint lessons E5.2,
E5.3 and E5.7, and brings the draft foundation to 90 question records and 37 passages. The
E6 checkpoint adds four fresh composition-planning groups across two reciprocal forms. Each
form sequences three task-decoding decisions for E6.1 and two five-minute planning decisions
for E6.5, bringing the draft foundation to 94 question records and 37 passages. The E0–E6
forms run through persisted checkpoint sessions with prerequisite locking, no hints or
early feedback, deterministic part scoring, form-B retry and an atomic checkpoint-to-`mastered`
transition. The E7 checkpoint contributes four fresh paragraph-development groups across two
reciprocal forms, scopes mastery to Sprint lesson E7.2 and brings the draft foundation to 98
question records and 37 passages. The E0–E7 forms remain draft-gated and therefore
unavailable in production until academic
and editorial approval and publication. Exact route membership and rationale are recorded in
`docs/plan/LAYER_1_ENGLISH_V3B_ROUTE_BLUEPRINT.md`.
The E8 checkpoint adds two reciprocal five-decision composition self-editing groups, scopes
mastery to Sprint lesson E8.4 and brings the foundation to 100 question records and 37
passages. These decisions train revision priority inside composition and do not claim that the
reported exam contains a separate editing section.
The E9 checkpoint adds two reciprocal five-decision simulation-readiness groups, scopes
mastery to Sprint lesson E9.5 and brings the foundation to 102 question records, 37 passages
and 23 forms. All 16 Sprint lessons now have authored lessons, exit tickets, parallel retries
and a module checkpoint journey. This final checkpoint is not the protected full mock and does
not score a whole composition automatically.
Consolidated checkpoint progress now exposes locked, available, in-progress and passed states,
attempt counts and latest scores to learners. Administrator student detail shows English lesson
evidence and the latest checkpoint attempt per module without exposing learner answers.
The consolidated Sprint reviewer export pins 16 lessons, 16 parallel retries, 20 reciprocal
checkpoint forms, 65 unique question groups and 20 passages. It produces deterministic HTML,
JSON, Markdown and CSV evidence and is uploaded by pull-request CI without changing content
status or recording an approval.

## 1. V3 decision

V3 keeps the strongest operational ideas from V2 but removes tasks and workflows that are
not supported by the product owner's recent exam evidence or cannot scale economically.

The Beta English profile is built around the reported 2026 format supplied by the product
owner:

1. vocabulary in sentence contexts;
2. a story passage with blanks and a surplus word bank;
3. a passage with blanks and no word bank;
4. two reading-comprehension passages with synonym-in-context, reference and multiple-choice
   questions; and
5. one approximately 300-word composition completed in 30 minutes.

Editing questions and scored “answer in your own words” questions are **not** part of the V3
Beta blueprint. Older or different-entry reports that mention them remain evidence records,
but they do not create learner-facing task types unless newer evidence confirms that the
target Indonesian Secondary 1-entry paper uses them.

V3 retains the existing 10 modules and 51 planned lessons. It does not add E2.7, E5.8,
E9.6 or E9.7 as core lessons. Descriptive or letter prompts may be stored as optional prompt
variants later without expanding the core curriculum.

## 2. Product boundary

Layer 1 includes:

- the English course map, lessons, objective practice, retry and progress;
- a versioned exam profile matching the reported Beta format;
- fixed Full, Core and Sprint routes;
- an English baseline, endline, checkpoints and mocks using only supported task types;
- essay planning, submission, self-review and limited AI feedback;
- administrator content review, learner reports and release evidence; and
- privacy, consent and rare safeguarding escalation for essays written by minors.

Layer 2 continues to own XP, levels, streaks, freezes, quests, badges, leaderboards and the
personalised calendar or study planner.

## 3. What V3 takes from V2

| V2 proposal | V3 decision | V3 form |
| --- | --- | --- |
| Wider evidence inventory | Keep | Record source, year, country, entry level, authority and limitation. Treat reports as format evidence, never as questions to copy. |
| Structured post-test recall | Keep | A short form collects format, timing and task types without collecting verbatim questions. |
| Entry-level configuration | Simplify | Use one versioned Beta exam profile for Secondary 1 entry. Add other profiles only when the product supports them. |
| Full, Core and Sprint routes | Keep | Fixed lesson subsets chosen from the existing 51 lessons; no personalised scheduling. |
| Indonesian/Malay transfer patterns | Keep carefully | Use them as teaching and error-analysis cues, never as assumptions about an individual learner. |
| Editing lesson | Reject for Beta | No learner-facing editing section without current target-exam evidence. Editing remains an essay-revision skill inside E8. |
| Own-words answer lesson | Reject for Beta | Reading practice remains synonym, reference, stated meaning, bounded inference, purpose, tone and MCQ. |
| Descriptive and letter lessons | Defer | Support them as optional prompt packs if stronger evidence appears; do not expand the core catalogue now. |
| Paper-test rehearsal | Keep | Include handwriting and at least one mock after a Mathematics practice paper. |
| Five-item exit tickets | Keep for sentence tasks | Passage tasks use one grouped passage; writing-planning tasks use a grouped decision set. |
| Parallel retry forms | Keep | A retry must assess the same outcome using new material rather than repeat the failed question. |
| Human marking for every essay | Replace | AI feedback is the scalable default after a small calibration gate; humans handle safety, appeals and sampling. |
| 20% double marking | Reject as routine | Use a small one-time calibration set and a 5% Beta audit, not blanket double marking. |
| 32–40 essay anchors | Reduce | Begin with 12–16 deliberately varied calibration essays. Expand only when evidence shows a gap. |
| 300–400 full word profiles | Defer | Begin with 120–180 high-value families represented by compact reviewed records. |
| 400 sentence items and 85 passages | Reduce and stage | Build enough disjoint Core-route forms for Beta, then expand from usage and item-health evidence. |
| Rejected-answer log | Keep | Aggregate rejected open-cloze answers and learner reports; review recurring cases in batches. |
| Safeguarding and consent | Keep | These are mandatory exceptions to automation, not a routine marking workflow. |
| Staged releases | Keep | Release reviewed Core breadth first; add depth, mocks and Full-route content progressively. |
| Word chest and harbour board | Defer presentation | Preserve the academic events and data hooks; elaborate UI can follow the core journeys. |

## 4. Versioned exam profile

Do not hard-code a universal “ASEAN English exam”. Store a profile such as
`asean-english-sec1-id-reported-2026-v1` with:

- audience and entry level;
- source references and evidence status;
- Section 1 and Section 2 timing;
- enabled task types;
- approximate composition length and whether it is guidance or a strict limit;
- passage-count and prompt-choice assumptions; and
- an effective date and review date.

The first profile enables only the task types listed in section 1. New reports may create a
new profile revision. Historical attempts retain the profile revision under which they were
assigned.

This is smaller and safer than adding `entry_level` to every existing object immediately.
Questions and passages need an explicit profile restriction only when they are not usable
across all supported profiles.

## 5. Curriculum and routes

### 5.1 Curriculum

Keep the existing E0–E9 catalogue and 51 stable lesson identities:

- E0 orientation and baseline;
- E1 vocabulary;
- E2 sentence control and cohesion;
- E3 banked cloze;
- E4 open cloze;
- E5 reading comprehension;
- E6 planning;
- E7 paragraph development;
- E8 accurate essay language; and
- E9 composition forms and timed performance.

Existing authored lessons and questions remain valid drafts. New metadata creates new
catalogue or content revisions; it does not overwrite historical revisions.

E9.1 reflective and personal expository writing already aligns with V3. E8 editing remains
revision instruction for composition, not evidence of a separate exam editing section.

### 5.2 Routes

Routes control which lessons are recommended, not which lessons learners are allowed to
open.

| Route | Intended use | Size target |
| --- | --- | --- |
| Full | 28 or more weeks before the test | All 51 lessons |
| Core | 12–27 weeks | Approximately 28–32 lessons |
| Sprint | Fewer than 12 weeks | Approximately 14–16 lessons |

Exact Core and Sprint membership is fixed in the V3-B route blueprint after an outcome-level
review. The validator counts route tags, requires Sprint to remain a Core subset and ensures
both routes cover E0 through E9, the baseline and the timed simulation. Changes must update the
catalogue, blueprint and regression evidence together.

## 6. Lesson, exit-ticket and retry rules

Retain the seven-section lesson anatomy already implemented.

Use these assessment rules:

- sentence-level exit tickets: five independently scored decisions;
- banked and open cloze: one complete passage group with feedback after submission;
- reading: one complete passage group with feedback after submission;
- composition-planning lessons: one grouped set of five or six decisions;
- proficiency: at least 75% of scored parts without using an exit-ticket hint;
- hinted or failed work: `practice_completed`, followed by a parallel retry form;
- checkpoint success: `mastered`; and
- retry intervals: reuse the shared 2, 4, 7 and 14-day schedule.

Current implementation work required:

1. persist hint use;
2. calculate part-level thresholds instead of requiring an entirely perfect group or
   accepting any one correct exit item;
3. add the `mastered` state when checkpoints exist;
4. map each exit ticket to a parallel retry form; and
5. preserve the original attempt and item revision for audit.

## 7. Scalable content model

V3 uses breadth first and expands according to learner evidence.

### Release A target

- reviewed Core-route lessons available across every exam strand;
- one exit ticket and one parallel retry form for every released lesson;
- an approximately 20-item baseline and matched endline/reserve forms;
- one checkpoint per released module, with one retry form;
- enough original passages to prevent immediate repetition in the Core route;
- 12–16 original composition prompt pairs;
- 8–12 short model or annotated exemplar texts; and
- 12–16 private calibration essays covering weak, developing, secure, strong and edge
  cases.

### Expansion target

- add content when retry demand, exposure frequency or item-health data shows a real need;
- prioritise new passage groups because learners remember passage answers easily;
- generate only from reviewed templates and reviewed source records;
- never use recalled live questions as learner content; and
- keep practice, retry, diagnostic, checkpoint and mock pools disjoint.

V3 does not require 400 sentence items, 85 passages or 300–400 full word profiles before
Beta. Those may remain long-term capacity targets after usage justifies them.

## 8. Risk-based content review

English still needs human accountability, but V3 caps and targets it.

### Automated checks on every asset

- schema and cross-reference validation;
- exact-answer and option-key validation;
- duplicate and near-duplicate detection;
- passage checksum and revision pinning;
- exposure-pool isolation;
- spelling, punctuation and house-style linting;
- word-count and passage-length bands;
- answer-leak and learner-safe contract tests; and
- generated reviewer packets with all answers and rationales.

### Human review by risk

| Risk tier | Content | Review rule |
| --- | --- | --- |
| High | Open-cloze accepted answers, reading answer logic, essay prompts, rubric and model essays | Review every batch before publication. |
| Medium | Vocabulary MCQ, banked cloze and lesson explanations | Review one consolidated batch, with at least 25% item sampling and the ability to exclude any item. |
| Low | Metadata-only revisions and generated variants from an already reviewed template | Automated regression plus small random sample. |

Use the current batch/unit approval workflow. The reviewer approves a batch and excludes
specific questions requiring correction; immutable approval records remain item-level.

Target human review effort:

- Release A: approximately 15–25 total hours;
- complete Core Beta content: approximately 30–50 cumulative hours; and
- ongoing operation: one short batched audit each month plus exception handling.

These are capacity limits, not promises that unsafe or ambiguous content may bypass review.
If the high-risk queue exceeds capacity, publish less content rather than weaken the gate.

### 8.1 Practice-bank scale and learner loop

The six questions currently visible in a pilot lesson prove delivery, marking, hint and retry
behaviour; they are not the final amount of practice. Production practice is bank-backed and
separate from the short lesson sequence:

1. learn one explicit method in the lesson;
2. complete a five-decision exit ticket;
3. receive a fresh retry form only when the threshold is missed;
4. enter targeted mixed practice drawing unseen items from the relevant skill bank; and
5. revisit the skill through spaced mixed sets and later checkpoint forms.

Count practice in **decisions**, not only JSON question records. A banked-cloze record may
contain 10–15 independently marked gaps, while a reading record contains a passage and several
questions that must remain grouped. The proposed targets are:

| Strand | Release A minimum | Mature bank target |
| --- | ---: | ---: |
| Sentence vocabulary in context | 100 decisions | 250–300 decisions |
| Banked cloze | 20 passages / at least 200 gaps | 50–70 passages / 600–900 gaps |
| Open cloze | 20 passages / at least 200 gaps | 50–70 passages / 600–900 gaps |
| Reading comprehension | 24 passages / at least 150 questions | 60–80 passages / 450–650 questions |
| Grammar and sentence control | 120 decisions | 250–300 decisions |
| Composition planning and editing | 60 decision groups plus 30 prompts | 150–200 groups plus 100–150 prompts |

These are staged inventory targets, not a requirement to author 200–300 questions for every
lesson or to delay Beta until the mature bank exists. Every prompt still passes schema,
duplicate, answer-leak and batched review gates. Protected baseline, endline and mock items are
disjoint from ordinary practice and never used as unlimited drills.

Reading is essential but should be directed. The learner experience should include a
10–20-minute reading habit three to five days per week, using age-appropriate articles, short
stories and expository texts. Each reading session asks for a brief gist, one evidence-backed
inference, two words inferred from context and one sentence explaining the writer's choice.
The product may store completion and reflections without copying third-party texts. This habit
builds background knowledge and language exposure, while the question bank teaches the exact
exam operations and provides measurable practice.

## 9. Scalable essay feedback

### 9.1 Default learner path

1. The learner chooses one of two prompts.
2. The draft autosaves locally and remotely.
3. Submission creates an immutable essay revision.
4. Deterministic checks record word count, time, prompt and missing or malformed content.
5. An asynchronous AI provider returns structured feedback against the versioned five-
   criterion rubric.
6. The service verifies that every quoted evidence span exists exactly in the essay.
7. The learner sees an **AI preparation estimate**, evidence-linked strengths, two
   priorities, one revision task and one transfer goal.
8. A finite essay-review allowance controls cost. Learners never see model tokens.

The provider is not allowed to assign an official scholarship score or admission
probability. Essay text is always treated as data, never as instructions.

### 9.2 Small calibration gate

Before learner release, evaluate on 12–16 private essays scored once by a qualified English
educator. Include off-topic, memorised, very short, error-heavy and prompt-injection examples.

Minimum release checks:

- quoted evidence exists word-for-word;
- feedback follows the requested rubric and age-appropriate tone;
- no official-score or scholarship-probability claims;
- off-topic and memorised answers are recognised;
- repeated runs do not move more than one band on any criterion;
- safety fixtures are held; and
- cost and latency remain within the founder-set ceiling.

This is a one-time bounded calibration exercise, not a permanent human-marking service.

### 9.3 Human exceptions only

Human attention is limited to:

- safeguarding flags involving possible harm to a child;
- learner or parent appeals;
- a random 5% Beta quality audit; and
- rubric/prompt revisions when audit evidence shows a systematic problem.

There is no 72-hour human-marking promise and no routine 20% double marking in V3.

Self-review with a checklist and exemplars remains available when the AI allowance is
exhausted or the provider is unavailable.

## 10. Rejected objective answers

Open cloze can reject a valid alternative even with careful authoring.

V3 therefore records rejected short-text answers by item revision and normalised response.
Learners may flag “my answer may also be valid”. The system groups identical responses and
alerts an administrator only when:

- the same alternative is reported repeatedly;
- a high-performing learner supplies it; or
- an automated audit detects that the accepted-answer set changed.

Valid alternatives create a new immutable question revision and an audited re-mark. Review is
batched monthly during Beta rather than requiring a weekly manual queue when no pattern exists.

## 11. Privacy and safeguarding

Scalability does not remove the following minimum controls:

- guardian consent for storing and processing essays by minors;
- a retention and deletion policy;
- raw essays excluded from ordinary analytics and application logs;
- provider agreements and regional privacy review before production;
- automated safety classification before feedback; and
- one named adult who receives rare safeguarding holds.

Safeguarding cannot be fully automated. It is intentionally a low-volume human exception.

## 12. Staged delivery

### V3-A: foundation correctness

- approve the exam profile;
- add route metadata without changing existing lesson meanings;
- fix threshold, hint and retry semantics;
- add the baseline/form contract; and
- keep the current 31 authored lessons and 41 question records intact as drafts.

### V3-B: Core learner release

- review and publish Core breadth across all supported parts;
- add parallel retry forms and checkpoints;
- release baseline routing and progress;
- ship essay drafts, immutable submissions and self-review; and
- enable AI essay feedback only after the small calibration gate.

### V3-C: exam readiness

- timed paper sections and breaks;
- matched endline and reserve forms;
- two full mocks plus a reserve;
- at least one handwritten composition rehearsal; and
- hosted mobile, accessibility, privacy, recovery and exact-release evidence.

## 13. Engineering additions

The smallest compatible implementation adds:

1. a versioned `english_exam_profile` contract;
2. optional route tags on curriculum lessons;
3. form manifests for baseline, checkpoint, endline and mocks;
4. part-level score thresholds and recorded hint use;
5. explicit parallel-form relationships;
6. a checkpoint-backed `mastered` state;
7. rejected-answer aggregation and audited re-marking;
8. prompt, rubric, draft, submission and feedback-job contracts;
9. essay allowance and provider-cost records; and
10. safety hold, appeal and audit records.

Do not mutate V1 history in place. Add new catalogue/content revisions and keep stable lesson
keys unchanged. E9.1 remains valid under V3.

## 14. Effort estimate

| Work | Approximate implementation size |
| --- | --- |
| V3-A profile, metadata and progress/retry corrections | 1–2 engineering weeks |
| Baseline, form assembly, checkpoints and routing | 1–2 engineering weeks |
| Essay submission and AI-feedback vertical slice | 1–2 engineering weeks |
| Hosted UI, accessibility and release evidence | 1–2 engineering weeks |
| Content expansion and review | Continuous in parallel; bounded by the 15–25 hour Release-A review budget |

These ranges assume reuse of the current English domain, admin review workflow, deployment
pipeline and AI-provider patterns. Calendar time increases if the English educator, privacy
review or safeguarding owner is unavailable.

## 15. Decisions required before implementation

1. Confirm that the five-part profile in section 1 is the Beta target.
2. Confirm that editing and scored own-words answers are excluded until new evidence appears.
3. Full/Core/Sprint are approved as fixed lesson subsets; exact tags are now implemented in
   the V3-B route blueprint.
4. Set the essay-feedback allowance and provider-cost ceiling.
5. Name one qualified English educator for the bounded calibration and high-risk review.
6. Name the safeguarding contact and approve the retention policy.
7. Set the actual Beta date; V3 uses sequence rather than the expired V2 November calendar.

## 16. Current next milestone

Complete the remaining **V3-B Sprint review and release evidence** before expanding
optional Full-route lessons:

1. deploy the protected `english-sprint-route-v3b-review` session and collect English and
   editorial decisions against its 121 pinned lesson, checkpoint-form, question and passage
   fingerprints;
2. correct and re-export excluded items, then complete the immutable approvals;
3. deploy migration `202610300037`, then run the implemented protected baseline/endline and
   checkpoint learner journey in hosted staging;
4. confirm the Sprint release manifest contains only approved immutable revisions; and
5. keep every item draft-only until the release gates pass.

The release-manifest mechanism is now implemented in the protected administrator route view.
It pins the fixed 121-record Sprint scope, exposes review and publication progress without
revealing answers, and remains `review_pending` until human decisions are recorded. It then
remains `publication_pending` until every approved revision is publication-requested and
published; only that complete state can report `ready`.

The objective diagnostic runtime is also implemented locally. It uses the four-group,
20-part baseline and matched endline contracts, keeps group correctness hidden until form
completion, reports task-level skill evidence rather than an official scholarship score and
keeps the endline locked until all fixed Sprint lessons are mastered. Hosted migration and
authenticated staging acceptance remain outstanding; no draft content was approved or
published by this implementation.

