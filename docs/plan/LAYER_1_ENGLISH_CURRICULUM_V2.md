# Layer 1 English curriculum and learning design (v2)

> **v2 proposal.** This file sits beside William's original `LAYER_1_ENGLISH_CURRICULUM.md`, which is unchanged.
> Nothing here replaces v1 until it is reviewed and accepted.

**Prepared:** 18 October 2026
**Revised:** 26 October 2026 (v2 proposal for William and English-educator review)
**Status:** proposed v2 curriculum; not yet approved
**Audience:** secondary-school students in Indonesia and Southeast Asia preparing for
the ASEAN Scholarship selection process; the Beta default is **Secondary 1 entry**
**Depends on:** [LAYER_1_ENGLISH_SCOPE_V2.md](./LAYER_1_ENGLISH_SCOPE_V2.md)
**Executed by:** [LAYER_1_ENGLISH_FOUNDATION_EXECUTION_V2.md](./LAYER_1_ENGLISH_FOUNDATION_EXECUTION_V2.md)

## 0. What this revision changes

The v1 design (spiral modules, the seven-step lesson, deterministic objective marking,
the essay rubric approach and the review gate) is kept. This revision adds what v1
needed to be buildable and teachable for the Beta cohort:

1. a wider evidence base (eight public candidate and preparation reports from 2012–2026
   plus the Singapore PSLE English format as a difficulty reference) and a plan to
   collect more;
2. **entry level** as a first-class setting, because Secondary 1 and Secondary 3 reports
   differ (passage length, essay length, prompt genres);
3. **course length** routes (Full, Core, Sprint) because the Beta cohort has roughly
   16–18 weeks before an April test, and 51 lessons at two per week takes about 26;
4. four new lessons for formats the reports mention that v1 did not teach (editing,
   short answers in your own words, descriptive writing, personal letters), giving
   **55 lessons**;
5. a learner-language section for Indonesian and Malay speakers (common transfer
   errors, optional glosses, the paper-based test);
6. explicit rules for exit tickets, hints, lesson states and thresholds so English
   matches the shared progress model used by Mathematics;
7. a concrete writing plan: one composition chosen from two prompts, genres by entry
   level, a draft band-descriptor rubric, a human-feedback path for the Beta, an anchor
   set specification and handwriting practice;
8. passage, item and vocabulary standards, a minimum content inventory and an
   evaluation plan for the Beta.

Every change is listed with its reason in
[LAYER_1_ENGLISH_V2_CHANGES.md](./LAYER_1_ENGLISH_V2_CHANGES.md).

## 1. Purpose and evidence boundary

This curriculum converts the best available evidence about the English selection test
into teachable, measurable skills. It is a preparation curriculum, not a claim to
reproduce a confidential or officially published MOE syllabus. Learner-facing text must
say "past candidates report" rather than "the test has".

### 1.1 Working test blueprint

| Part | What candidates report | Working default (Sec 1) | Evidence strength |
| --- | --- | --- | --- |
| Section 1: Language use and comprehension | One paper of objective and short written answers | 90 minutes | Corroborated: 90 minutes in three independent accounts; 90–120 and 105 minutes in two others |
| Part 1 | Vocabulary in sentence contexts, often described as difficult | Multiple choice | Candidate-reported (2026), with "hard vocabulary" in three other accounts |
| Part 2 | A passage with blanks and a surplus word bank | Banked cloze | Candidate-reported (2026); "fill in the blank" sections reported in 2016 |
| Part 3 | A passage with blanks and no word bank | Open cloze | Candidate-reported (2026) |
| Part 4 | Two reading passages, described as "quite long", with reference, same-meaning-word and comprehension questions | Two passages | Corroborated (2013 Sec 1 and 2026) |
| Variant seen in some years | Error identification and correction; a grammar section in two parts | Editing items, configurable weight | Candidate-reported (2014, 2016) |
| Variant seen in some years | Short written answers with a word limit; "in your own words" | Constrained short answers, configurable weight | Candidate-reported (2020 Sec 3; 2012 Pre-U) |
| Section 2: Writing | One composition, chosen from **two** prompts | 30 minutes; about 300 words | 30 minutes corroborated in five accounts; choice of two in four accounts; length varies (see 1.3) |

Exact question counts, marks and the wording of the length rule remain configurable.
The reported conditions also matter for preparation:

- the test is **paper-based** (papers are handed out and collected);
- English has been taken **after the Mathematics paper on the same day**, with a short
  break; and
- in the Indonesian process the selection test sits alongside Mathematics and a General
  Ability test, followed by interviews. (The General Ability test is outside this
  curriculum.)

### 1.2 Evidence inventory

Every row becomes a record in `sources.json` with year, entry level, country, city,
authority and limitation. None of these sources may be copied into learner content.

| Source | Year, level, place | What it supports | Authority |
| --- | --- | --- | --- |
| Product-owner candidate report | 2026; entry level not yet recorded | The four-part Section 1 above; 30-minute, ~300-word composition | Candidate-reported |
| Public blog (Penang) | 2013; Sec 1; Malaysia | Comprehension 90 min, two long passages, "who or what the underlined word refers to", "same-meaning word in a given paragraph"; essay 30 min, ~200 words, choice of two, both prompts were letters | Candidate-reported |
| Public blog | 2014; senior-high entry; Indonesia (Surabaya) | A grammar test in two sections plus an essay; word-count discipline; a vocabulary sheet was provided | Candidate-reported |
| Public blog | 2016; Sec 1 and Sec 3 | Paper 1 of 90–120 min mixing objective and written answers: comprehension, error identification, fill-in-the-blank, hard words; essay 30 min, choice of two, "creative" topics | Candidate-reported |
| Public blog (Penang) | 2020; Sec 3; Malaysia | Comprehension 1 h 45 min with objective and word-limited short answers; essay 30 min, choice of two, ~300–500 words (author unsure), descriptive and reflective prompts; paper-based | Candidate-reported |
| Public blog | 2012; Pre-U; Malaysia | Comprehension and summary "in your own words"; essay 350 words in 30 min, choice of two discursive prompts | Candidate-reported; above our levels, used as an upper bound |
| Commercial prep article | Undated | English as two papers, 1 h 30 min plus 30 min (comprehension and composition) | Independent preparation summary |
| Indonesian scholarship information site | 2026; Sec 1 and Sec 3; Indonesia | Sec 1 is for students now in grade 6 SD or grade 7 SMP; Sec 3 for grade 8–9 SMP; tests 11–12 April 2026 in eight cities; English, Mathematics and General Ability; interviews in June | Independent summary of the official notice |
| SEAB PSLE English Language format (2022) | Singapore end of primary | A **difficulty and construct reference** for Sec 1 entry: grammar, vocabulary and vocabulary cloze, grammar cloze, editing for spelling and grammar, comprehension cloze, synthesis and transformation, open comprehension; situational and continuous writing | Official, but for a different examination |
| MOE ASEAN Scholarships applicant guide | 2026 | Selection-test administration exists | Official; no paper blueprint |

### 1.3 What the evidence agrees on, varies on, and does not tell us

- **Agrees:** two English papers; a 30-minute composition; a choice between two prompts;
  two reading passages; vocabulary is the part candidates find hardest.
- **Varies by year or level:** Section 1 duration (90–120 minutes); whether editing or
  written short answers appear; composition length (about 200 words in a 2013 Sec 1
  account, about 300 in 2026, 300–500 in a 2020 Sec 3 account); prompt genres (letters,
  narrative, descriptive, reflective, opinion).
- **Unknown:** item counts, marks per part, the essay marking scheme, how strictly length
  is enforced, and whether any part has moved online.

### 1.4 Entry levels

Every outcome, passage, prompt and form carries an `entry_level` of `sec1`, `sec3` or
`both`. The Beta is invitation-assigned to Sec 1, so Sec 1 values are the defaults and
Sec 3 values are stored but not yet released.

| Setting | Sec 1 default | Sec 3 default |
| --- | --- | --- |
| Composition target | about 300 words; practise 250–350 | about 350 words; practise 300–450 |
| Reading passage length in mocks | 450–700 words each | 600–900 words each |
| Priority genres | narrative, reflective, descriptive, personal letter | the same, plus opinion |
| Section 1 timing | 90 minutes | 90 minutes, configurable to 105 |

These values are provisional estimates from the evidence above and must be confirmed by
the English educator and new candidate reports.

### 1.5 Evidence collection plan

The blueprint becomes more trustworthy only if new reports arrive in a consistent shape.

1. **A structured "test recall" form** collects format facts only: year, city, entry
   level, papers and timings, part types and rough counts, essay choices and genres,
   length wording, paper or computer, what felt hardest. It never asks for question
   wording.
2. **Who:** Beta students and families who have sat the test, the ASEAN-scholar alumni
   network, partner tutors, and every Beta student after the April 2027 sitting.
3. **Target:** at least ten Indonesian reports from the 2025 and 2026 sittings, at both
   entry levels, before the mock forms are frozen (end of January 2027).
4. **Corroboration rule:** a format fact is "corroborated" when at least three
   independent reports from the last three sittings at the same entry level agree. Until
   then it stays configurable.
5. **Recalled questions:** used only to identify constructs and genres. They are not
   stored verbatim in any learner-reachable system.

## 2. Curriculum model

English does not copy the Mathematics hierarchy of isolated content chapters. Language
skills accumulate and interact: vocabulary supports cloze and reading, reading provides
models for writing, and writing exposes grammar weaknesses. The course therefore uses a
spiral structure with three stages after orientation.

| Stage | Purpose | Modules |
| --- | --- | --- |
| Orientation | Know the paper, establish a baseline and the error language | E0 |
| A: Build the language toolkit | Learn reusable vocabulary, grammar and sentence-analysis strategies | E1–E2 |
| B: Apply it to the paper | Apply those tools to banked cloze, open cloze and reading | E3–E5 |
| C: Compose and perform | Plan, draft, revise and complete both papers under time pressure | E6–E9 |

Every later module retrieves earlier vocabulary and grammar. Learners do not "finish
vocabulary" before reading or writing; they meet high-value word families repeatedly in
sentences, passages and their own compositions.

### 2.1 Proposed Beta size

- 10 modules and **55 core lessons** of approximately 25–35 minutes (51 from v1 plus
  E2.7, E5.8, E9.6 and E9.7);
- 9 module checkpoints, each with a retry form;
- 4 cumulative milestone assessments;
- an English baseline, an endline and a protected reserve form;
- 2 full simulated English papers and a protected reserve paper;
- a prompt bank for guided, untimed and timed writing; and
- a reviewed vocabulary set of about 300–400 word families.

### 2.2 Two route settings

A learner's route is set by two deterministic choices. Neither is the Layer 2
personalised planner: they choose which lessons are in the route, not when to do them.

**Starting level**, from the E0 baseline (unchanged from v1):

- **Foundation:** all E1 and E2 lessons before exam-format modules;
- **Standard:** the route's lessons in order; or
- **Accelerated:** passing the E1 and E2 checkpoints validates those modules, but their
  words and structures keep returning in retrieval.

**Course length**, from the weeks remaining until the learner's test date:

| Length | When it is suggested | Lessons | At two new lessons a week |
| --- | --- | --- | --- |
| Full | 30 or more weeks | all 55 | about 28 weeks |
| Core | 12–29 weeks | 32 tagged **C** below | about 16 weeks |
| Sprint | under 12 weeks | 16 tagged **S** below | about 8 weeks |

A learner who starts on 1 December has about 18 weeks before a mid-April test, so the
Beta default is **Core**, which leaves two weeks for full mocks. Learners can always open
any other lesson. The thresholds are provisional and need review against real Beta
pacing.

### 2.3 Recurring strands between lessons

The modules provide explicit instruction, but four short strands continue throughout the
course so knowledge is retained and transferred:

1. **Vocabulary retrieval:** 5–10 minutes using due word profiles in new sentence and
   passage contexts, including recognition and production.
2. **Wide reading:** at least one short narrative and one informational text each week,
   followed by a brief summary, vocabulary inference and one reflection question. Texts
   must be original, openly licensed or properly licensed, and should sit at about 98%
   known-word coverage for the learner's level so they can be read without help (Hu and
   Nation, 2000).
3. **Sentence craft:** one weekly combine, expand or repair task based on common learner
   errors, including the transfer errors in section 3.
4. **Writing fluency:** one five-minute plan or ten-minute paragraph each week, even
   while the learner is studying the objective paper.

**How learners see them (design hooks, academic progress only):**

- The **module map** shows each module as an island and each lesson as a stop. The four
  milestones are crossings between stages. The route from section 2.2 is drawn on it.
- The **word chest** is the vocabulary strand. It shows the words a learner has met and
  how many are due today, and opens the review session.
- The **harbour board** is the weekly strands view: this week's word review, reading,
  sentence task and writing task, each with a tick.

None of these award points in Layer 1. Layer 2 may attach experience points, streaks and
quests to the same events.

### 2.4 Weekly rhythm

A sustainable schedule is four or five 30–45-minute sessions per week: two new lessons,
one application lesson, one retrieval and retry session and, when available, one timed or
writing session. English shares the learner's week with Mathematics, so the course must
not assume more than about three hours of English a week.

## 3. Learners and language priorities

### 3.1 Who the learners are

- Sec 1 applicants are usually 11–13 years old (grade 6 SD or grade 7 SMP); Sec 3
  applicants are usually 13–15.
- Most learn English as an additional language at school and through media. Reading and
  listening fluency is often ahead of grammatical accuracy.
- They will sit a paper-based test, by hand, after a Mathematics paper.

### 3.2 Common transfer patterns for Indonesian and Malay speakers

These patterns follow from differences between Indonesian or Malay and English. The same
patterns are common for many Thai and Vietnamese speakers. They set priorities, examples
and error categories; they are never used to label a learner.

| Pattern | Why it happens | Where it is taught |
| --- | --- | --- |
| Missing past or third-person endings ("Yesterday she walk", "He go") | Verbs do not change for tense or person; time words carry the meaning | E2.2, E2.3, E4.2 |
| Missing or misused articles ("I bought book") | There are no articles | E2.4, E4.1 |
| Missing plural endings after quantities ("many student") | Plural marking is optional | E2.4, E4.2 |
| Missing *be* ("She very kind") | No linking verb is needed before adjectives | E2.1 |
| *He* and *she* confused | One third-person pronoun covers both | E2.2, E5.2 |
| Preposition by translation ("at Monday", "in the bus") | One preposition covers several English ones | E2.5 |
| Loanwords with different meanings | Similar-looking words have shifted meanings | E1.4 |

Error classification (section 4) adds an optional **transfer** tag so reports can show
when one pattern recurs across strands.

### 3.3 Language support

- **Optional glosses:** a word profile may carry an educator-reviewed Bahasa Indonesia
  gloss, shown only after the learner has tried to infer the meaning. Glosses are
  available in the Foundation route and in vocabulary retrieval. They never appear in
  checkpoints, milestones, diagnostics or mocks.
- **Instructions:** learner instructions stay in English. A short Bahasa Indonesia help
  line may be added for E0 and for the first lesson of each module.
- **Cultural accessibility:** passages use settings and names from across Southeast Asia
  and Singapore school life. They avoid knowledge that only some learners have (a
  regional festival, a sport, an idiom) unless the passage explains it.

### 3.4 Paper-test conditions

- Passages show paragraph numbers and support underlined target words, because the
  reported questions refer to "the underlined word" and "paragraph 3".
- Learners can highlight and annotate passages in practice, as they would on paper.
- From E6 onwards, at least two timed compositions per route are handwritten. The
  learner writes on paper, records the time, estimates the length by counting lines,
  then types the essay for feedback and records that it was transcribed.
- Full mocks run after a Mathematics paper and a short break, with the composition paper
  handed out separately, to rehearse stamina.

## 4. Standard lesson anatomy

Each lesson follows a consistent learn, apply and retrieve cycle.

1. **Retrieval warm-up (3–5 minutes):** two to four previously taught words, grammar
   decisions or reading inferences.
2. **Explicit model (5–7 minutes):** explain one strategy and demonstrate the reasoning
   aloud on an original example.
3. **Worked analysis (5–7 minutes):** annotate why the correct response fits and why a
   plausible distractor fails.
4. **Guided practice (5–8 minutes):** scaffolded items with prompts that gradually fade.
5. **Independent exam application (8–12 minutes):** unseen items in the target format.
6. **Error classification (2–3 minutes):** identify the cause using the shared
   taxonomy below.
7. **Exit ticket:** an unseen transfer task that decides whether the lesson is
   proficient or enters the retry queue.

Writing lessons use the same structure as a **Model, Practise, Reflect** cycle: study a
model, practise one controllable move, apply it independently, then compare the result
against a criterion (US Institute of Education Sciences, *Teaching Secondary Students to
Write Effectively*).

Lesson explanations and answer rationales are authored and reviewed in advance. Objective
practice does not require a live AI call.

### 4.1 Shared error taxonomy

One taxonomy is used in every strand so reports can compare across strands. The existing
grammar and open-cloze categories map onto it.

| Code | Cause |
| --- | --- |
| `meaning` | Did not know or misjudged the word's meaning |
| `clue` | Missed a clue in the sentence or passage (contrast, cause, example, tone) |
| `word_class` | Chose the wrong part of speech or form |
| `agreement` | Tense, number, person or agreement error |
| `reference` | Lost track of what a word refers to |
| `inference` | Added an idea the text does not support |
| `question` | Misread what the question asked |
| `time` | Ran out of time or rushed |
| `careless` | Knew it, slipped |
| `transfer` (optional tag) | One of the patterns in section 3.2 |

### 4.2 Exit tickets, hints and lesson states

English uses the same lesson states as Mathematics.

| State | English rule |
| --- | --- |
| `not_started` | Lesson not opened |
| `in_progress` | Lesson opened; exit ticket not yet passed |
| `practice_completed` | Exit ticket attempted but not passed, or passed with a hint; the lesson is in the retry queue |
| `proficient` | Exit ticket passed at the threshold without a hint |
| `mastered` | The module checkpoint has been passed |

- **Exit ticket size:** sentence-level lessons use **five** items, because one item is
  too noisy to decide proficiency. Passage lessons use one passage group (six to eight
  parts).
- **Threshold:** at least 75% (4 of 5 items, 6 of 8 gaps, 5 of 6 parts).
- **Hints:** guided practice has one strategy hint per item. An exit ticket may show a
  hint, but using it records the attempt as `practice_completed`. Checkpoints,
  milestones, diagnostics and mocks have no hints.
- **Show answer:** in guided and independent sentence practice, an item can be revealed
  after two wrong tries, as in Mathematics. Passage groups reveal feedback only after the
  whole group is submitted.
- **Retry:** a failed or hinted exit ticket returns as a **parallel form** (different
  items, or a different passage) on the shared 2, 4, 7 and 14-day schedule. A passage
  group counts as one item toward the shared daily review limit.

## 5. Modules and lessons

Tags: **C** Core route, **S** Sprint route, **Sec 3** higher priority for Sec 3 entry,
**built** has draft content on the current branch. Lesson codes are stable identities,
not display order. New lessons take new codes, and the map shows lessons in the
**position** order listed.

### E0: Orientation, baseline and error language

**Purpose:** establish a trustworthy starting point and teach the learner how to use
feedback.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E0.1 Know the paper | Identify the purpose, format, timing and conditions of every reported part, including the choice of two prompts and the paper-based setting, without treating provisional counts as official facts. | C S |
| 2 | E0.2 Baseline objective check | Complete an untutored, mixed diagnostic covering vocabulary, grammar and editing, cloze and reading. | C S |
| 3 | E0.3 Diagnose the mistake | Classify errors with the shared taxonomy rather than recording only right or wrong. | C |

**The baseline (E0.2):** about 20 objective items in about 20 minutes, with at least four
items in each of vocabulary, grammar and editing, banked cloze, open cloze and reading.
It reports a band per strand and recommends a starting level. It does not estimate an
official score and excludes the essay.

**Relationship to the product diagnostic:** the combined Mathematics and English
diagnostic on the roadmap uses eight English items for the parent report. Those eight
items are a subset of the baseline form. A learner who has done them is not shown them
again: their answers carry into E0.2, which then asks only the remaining items.

### E1: Vocabulary that transfers

**Purpose:** build word knowledge while teaching learners how to reason about unfamiliar
words. This module supports Part 1 directly and supplies material for Parts 2–4 and
writing.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E1.1 Meaning from local context | Use definitions, examples, contrast, cause and tone around a word to test a possible meaning. | C, built |
| 2 | E1.2 Word class and word family | Use noun, verb, adjective and adverb forms to eliminate grammatically impossible options. | C |
| 3 | E1.3 Roots and affixes | Use common prefixes, roots and suffixes as evidence without assuming they always determine the whole meaning. | |
| 4 | E1.4 Synonym precision | Distinguish denotation, strength and connotation among near-synonyms, including loanwords whose meaning differs from Indonesian. | |
| 5 | E1.5 Collocation and register | Select words that naturally combine and fit formal, neutral or informal contexts. | |
| 6 | E1.6 Unknown-word protocol | Combine syntax, context, morphology and option elimination under a short time limit. | C S |

#### Vocabulary teaching policy

Vocabulary is not a random list, and the course must not promise that a fixed list
contains every tested word. Each selected word receives a reusable **word profile**:

- learner-friendly meaning, and an optional reviewed gloss (section 3.3);
- pronunciation support where needed;
- part of speech and useful word-family forms;
- two common collocations;
- synonym, contrast and connotation notes;
- one clear example and one non-example; and
- at least one later appearance in a cloze, reading passage or writing model.

**Selection:** prioritise broadly useful academic and descriptive word families,
connectives and high-value collocations, in frequency bands appropriate to the entry
level. Avoid rare words chosen only to look difficult. Any published word list used for
selection must have a licence that permits this use, recorded in `sources.json`.

**Size and rhythm:** about 8–10 target word families per set and about 300–400 families
across the Beta. Each family returns across expanding intervals in varied contexts.
Reviews require both recognition and production: choose the meaning, complete a new
sentence, distinguish a near-synonym and use the word in a short response.

**Review items from profiles:** recognition and completion items may be generated from a
reviewed profile by fixed templates, so reviewers check one profile instead of many
separate items. A reviewer spot-checks at least one generated item per profile before
publication.

The US Institute of Education Sciences adolescent-literacy guide recommends explicit
vocabulary instruction, repeated exposure in multiple contexts, meaningful use and
strategies for learning unfamiliar words independently. Research on second-language
vocabulary supports spacing retrieval instead of one concentrated study session (Kim and
Webb).

**E1 checkpoint:** infer unfamiliar meanings, distinguish near-synonyms and apply word
families and collocations in unseen sentences. Initial mastery targets: 80% untimed, then
75% on a short timed mixed set.

### E2: Sentence control and cohesion

**Purpose:** make the grammar needed for Parts 2 and 3, and for editing, visible and
usable. Teach grammar as meaning and sentence control rather than terminology.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E2.1 Sentence and clause boundaries | Recognise complete clauses, fragments, run-ons and relationships between clauses, including a missing *be*. | C, built |
| 2 | E2.2 Agreement and reference | Control subject–verb agreement, pronoun agreement (including *he* and *she*) and clear antecedents. | |
| 3 | E2.3 Time and viewpoint | Select tense and aspect from the passage timeline and maintain consistency. | C |
| 4 | E2.4 Noun phrases | Use articles, determiners, quantity, plurals and countability accurately. | C |
| 5 | E2.5 Prepositions and patterns | Choose common preposition, verb-complement and adjective-complement patterns in context. | |
| 6 | E2.6 Logical connections | Use conjunctions, transitions and relative structures to express contrast, cause, condition, addition and sequence. | C |
| 7 | **E2.7 Spot and fix the error** (new) | Find and correct grammar, word-form and spelling errors in a paragraph, and explain the rule each correction follows. | C S |

E2.3 and E2.4 carry the most frequent transfer patterns (section 3.2) and should receive
extra retrieval and sentence-craft items.

Grammar practice moves from one controlled contrast to mixed passage decisions. Every
explanation answers both "what form fits?" and "what meaning or relationship does it
express?"

**E2 checkpoint:** complete a mixed editing and gap set, justify the evidence for each
choice and correct recurring error categories.

### E3: Banked story cloze

**Purpose:** prepare for a passage with more candidate words than blanks.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E3.1 Read the whole story first | Track setting, characters, chronology, conflict and tone before filling gaps. | C S, built |
| 2 | E3.2 Apply the grammar filter | Use the words around a blank to identify the required word class and form. | |
| 3 | E3.3 Apply the meaning filter | Compare collocation, connotation and local meaning among grammatically possible words. | |
| 4 | E3.4 Solve globally | Reconsider earlier choices as the remaining bank and whole-passage coherence change the evidence. | C |

The learner interface treats one passage as one assessment object. Words are selectable
without drag-and-drop, used words remain visible, and answers can be cleared or changed.
Feedback explains local syntax and global narrative evidence.

**E3 checkpoint:** two unseen passages, one timed, without per-gap feedback until the
passage is submitted.

### E4: Open cloze without a word bank

**Purpose:** construct the missing word from grammatical and discourse evidence instead of
recognising it from options. All five lessons are built as drafts.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E4.1 Function-word gaps | Supply articles, pronouns, auxiliaries, prepositions and conjunctions from sentence structure. | C S, built |
| 2 | E4.2 Form and agreement gaps | Infer the required tense, number, comparison or derived word form. | C, built |
| 3 | E4.3 Collocation and lexical gaps | Retrieve a content word or fixed expression that fits the passage meaning. | built |
| 4 | E4.4 Cohesion across sentences | Use reference chains, repetition, contrast and chronology beyond the immediate sentence. | built |
| 5 | E4.5 Timed open cloze | Apply a first-pass, second-pass and final-read method to a complete passage. | C S, built |

Every gap must have one defensible canonical answer or an explicit accepted-answer set.
Reviewers must try to produce unintended valid alternatives. Broad semantic matching or
live AI judging is not permitted for objective scores. Rejected answers are logged and
reviewed (section 8.4).

**E4 checkpoint:** one mixed open-cloze passage under time, explaining the clue type for
selected answers.

### E5: Reading comprehension and reference

**Purpose:** prepare for two passages and questions about meaning, reference, detail,
inference and short written answers.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E5.1 Build a passage map | Identify topic, paragraph purpose, development and structure without over-annotating. | C S, built |
| 2 | E5.2 Track reference chains | Resolve what pronouns, demonstratives and descriptive phrases refer to. | C, built |
| 3 | E5.3 Meaning and synonym in context | Replace a word with a meaning that preserves its sense and grammatical role in that sentence. | built |
| 4 | E5.4 Retrieve stated evidence | Locate and paraphrase explicit information accurately. | C S, built |
| 5 | E5.5 Make bounded inferences | Combine textual clues without importing unsupported assumptions. | C, built |
| 6 | E5.6 Purpose, tone and main idea | Distinguish the writer's central purpose, attitude and supporting details. | built |
| 7 | **E5.8 Answer in your own words** (new) | Write a short answer within a word limit that keeps the passage's meaning without copying its wording, and quote exactly when a question asks for a word or phrase. | C S |
| 8 | E5.7 Two-passage pacing | Allocate time, mark uncertain items and keep a checking buffer across both passages. | C S, built |

The reading routine is **Locate, Link, Prove**: locate the relevant sentence or
paragraph, link it to the question and surrounding context, and prove the response with a
specific textual clue.

**Marking short answers (E5.8):**

- A question that asks for a word, phrase or number from the passage is marked
  deterministically with reviewed alternatives.
- A question that asks for an explanation in the learner's own words is **not
  auto-scored** in Layer 1. After answering, the learner compares the answer with a
  model answer and a two- or three-point checklist and ticks which points they made.
  This is recorded as practice, not as a score.

**E5 checkpoint:** an unseen two-passage set under a configurable time limit, attaching
evidence locations during review. Evidence locations teach reasoning but are not required
in the real-test simulation.

### E6: From prompt to organised response

**Purpose:** remove the blank-page problem before expecting polished language.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E6.1 Decode the task | Identify topic, command, audience, scope and genre. Its next revision adds choosing between two prompts within two minutes by asking which one you can develop best. | C, built |
| 2 | E6.2 Generate usable ideas | Produce relevant examples quickly from experience, observation, school learning and plausible scenarios. | built |
| 3 | E6.3 Choose and order | Select two or three developable ideas instead of many shallow points. | built |
| 4 | E6.4 Build the controlling focus | Write a clear central response that every paragraph advances. | built |
| 5 | E6.5 Plan in five minutes | Produce a compact introduction, body and conclusion plan with examples and transitions. | C S, built |

**E6 milestone:** a relevant, coherent plan for three unseen prompt pairs within five
minutes each, including the choice between the two prompts. At least one pair should
include the reported reflective use of school learning beyond school.

### E7: Paragraphs, evidence and cohesion

**Purpose:** turn a plan into developed writing rather than a sequence of assertions.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E7.1 Paragraph purpose | Give each paragraph one controlling point or narrative function. | C S, built |
| 2 | E7.2 Develop with specifics | Explain significance and use precise examples, actions, observations or consequences. | C, built |
| 3 | E7.3 Cohesion without formula | Connect ideas through reference, logical sequence and selective transitions rather than stock phrases. | built |
| 4 | E7.4 Introductions and endings | Open directly, establish direction and conclude by resolving the response rather than repeating it. | built |
| 5 | E7.5 Read like a writer | Analyse an original model and transfer one structural move into a new paragraph. | built |

**E7 checkpoint:** revise an underdeveloped response and independently write a coherent
multi-paragraph response from a supplied plan.

### E8: Accurate and effective essay language

**Purpose:** improve clarity and control while preventing forced "advanced vocabulary".

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E8.1 Precise vocabulary | Replace vague or repetitive words with accurate choices that fit meaning and register. | built |
| 2 | E8.2 Sentence variety with control | Combine and vary sentences without fragments, agreement errors or unclear reference. | built |
| 3 | E8.3 Show relationships | Express cause, contrast, qualification, sequence and consequence explicitly. | built |
| 4 | E8.4 Edit by priority | Check task fulfilment and organisation before grammar, spelling and punctuation, in the last three minutes of a timed essay. | C |
| 5 | E8.5 Personal error log | Identify two recurring error patterns, including any transfer pattern, and apply a short correction routine. | |

The curriculum never rewards an uncommon word merely for being uncommon. A simple,
precise word earns more credit than a sophisticated word used incorrectly.

**E8 checkpoint:** improve a flawed draft, explain each major revision and show the same
control on a new paragraph.

### E9: Composition forms and 30-minute performance

**Purpose:** transfer the writing process across the reported genres, then compress it to
the reported test time.

| Pos | Lesson | Outcome | Tags |
| --- | --- | --- | --- |
| 1 | E9.1 Reflective and personal expository writing | Connect experience or school learning to a clear insight, explanation or application. | C |
| 2 | E9.2 Narrative writing | Shape setting, conflict, purposeful detail, turning point and resolution. | C S |
| 3 | **E9.6 Descriptive writing** (new) | Describe a place, person, object or event with an organising impression and precise sensory and factual detail. | |
| 4 | **E9.7 Personal letters as compositions** (new) | Write a personal letter to a named reader with a clear purpose, a suitable tone and letter conventions, developed like any composition. | C |
| 5 | E9.3 Opinion and discursive writing | State a defensible position, develop reasons and acknowledge complexity. | Sec 3 |
| 6 | E9.4 Compress the process | Move from 45-minute supported writing to 35-minute and then 30-minute independent writing, including at least one handwritten essay. | C S |
| 7 | E9.5 Full English simulation | Complete Section 1 and Section 2 under their reported limits, after a Mathematics paper, with no hints or immediate marking. | C S |

Prompt genres remain provisional until the evidence collection plan confirms which are
used for the relevant entry level and year. Do not assume every sitting offers every
genre. The letter in E9.7 is one genre of the single composition, not a separate
situational-writing paper.

## 6. Writing and the feedback system

### 6.1 The writing task

- One composition chosen from two prompts, in 30 minutes.
- Working length: about 300 words, practised in the range 250–350 for Sec 1 (section
  1.4). Learners are taught that writing far beyond or below the guidance can cost
  marks and that quality matters more than length.
- Every timed prompt pair in the bank pairs two different genres, as the reports
  describe.
- The drafted E6–E8 lessons practise task analysis, planning, paragraphing and editing
  through deterministically marked questions. Learners write their first full
  compositions when the human-feedback path (section 6.4) is live.

### 6.2 Internal formative rubric

No official public rubric exists, so NextScholar uses a versioned internal rubric and
labels all feedback as preparation guidance. Five criteria, four bands each. The
descriptors below are a starting draft for the English educator to rewrite and test
against the anchor set.

| Criterion | 1 Limited | 2 Developing | 3 Secure | 4 Strong |
| --- | --- | --- | --- | --- |
| Task fulfilment and ideas | Partly off-task or memorised; ideas listed with little detail | Answers the prompt; some relevant detail; uneven development | Every part answered; clear focus; relevant specific detail | Purposeful focus; well-chosen detail developed with intent |
| Organisation and cohesion | Order hard to follow | Basic paragraphs; some jumps | Logical paragraphs; clear links | Purposeful structure; smooth, varied links |
| Vocabulary and register | Basic or repeated words; misused words | Adequate; some imprecise choices | Precise and mostly suitable for the reader | Precise, varied and natural; register controlled |
| Sentence control and grammar | Frequent errors block meaning | Errors common but meaning clear | Mostly accurate with some variety | Accurate and varied; errors rare and minor |
| Mechanics | Spelling and punctuation errors distract | Some errors | Few errors | Almost error-free; clear paragraphing |

Do not publish a probability of winning the scholarship or convert the rubric into an
"official ASEAN score". Criterion evidence and the learner's next action matter more than
any overall indicator.

### 6.3 Feedback sequence

Feedback is limited enough to act on:

- two evidence-linked strengths;
- one primary content or organisation priority;
- one primary language priority;
- selected corrections that illustrate a repeated pattern rather than every line;
- one short revision task; and
- one transfer goal for the next unseen prompt.

After feedback, the learner revises one paragraph or planning decision before attempting a
new prompt. Resubmitting the same essay only to raise an estimate does not count as
independent improvement.

### 6.4 Who gives feedback

- **Layer 1 Beta default: trained human markers.** Former ASEAN scholars or English
  teachers mark against the rubric, using the anchor set, within 72 hours. At least 20%
  of essays are double-marked to check agreement. For a cohort of 10–30 learners this is
  practical, and every marked essay adds calibration evidence.
- **AI feedback** is added when it passes the evaluation gate in the scope document. It
  uses the same rubric, the same feedback sequence and the same "estimate" labelling.
- **Self-review** is always available: the learner compares the draft with model essays
  for the same genre and a short checklist for each criterion.

### 6.5 Anchor set

- Original essays written for each Sec 1 priority genre (reflective, narrative,
  descriptive, personal letter), plus opinion for Sec 3.
- Two essays per band per genre (at least 32 for Sec 1), including deliberately
  off-topic, memorised-template and too-short or too-long essays.
- Each anchor is scored independently by two trained raters; disagreements are
  adjudicated and the reason recorded.
- Anchors stay private: they are evaluation and training material, not learner content.

### 6.6 Writing milestones

| Milestone | Evidence |
| --- | --- |
| W1 Relevant | The response addresses every part of the prompt and is not a memorised off-topic essay. |
| W2 Planned | The learner chooses a prompt and creates a usable plan within five minutes. |
| W3 Developed | Body paragraphs contain specific development rather than lists of claims. |
| W4 Controlled | Meaning stays clear despite ambitious sentence and vocabulary choices. |
| W5 Timed | The learner plans, drafts about the required length and checks within 30 minutes, at least once by hand. |
| W6 Transferable | Improvements appear on a new prompt without copying feedback wording. |

### 6.7 Integrity

Memorised template essays are a known risk in scholarship preparation. The platform
compares each submission with the learner's earlier submissions and the published model
essays, and flags very high overlap so the marker can apply W1. Learners are told why
this matters: an essay that does not answer the prompt cannot score well, however
polished it is.

## 7. Practice, checkpoints, diagnostics and mocks

### 7.1 Modes

| Mode | Hints | Feedback timing | Purpose |
| --- | --- | --- | --- |
| Learn | Strategy prompts and explanations | During the activity | Acquire one method |
| Guided practice | One hint per item, fading | After each item or passage | Stabilise the method |
| Independent practice | None by default | After each item or passage | Apply without help |
| Exit ticket | Visible, but use prevents proficiency | After submission | Decide proficiency |
| Checkpoint | None | After submission | Verify module mastery |
| Timed practice | None | After the complete part | Build pacing and concentration |
| Full mock | None | After both papers are locked | Rehearse performance conditions |

Passage tasks never reveal one answer while other blanks or questions remain active. The
system scores each blank or question for analytics but keeps passage-level presentation
and timing.

### 7.2 Cumulative milestones

1. **M1 Language toolkit:** E1 and E2 mixed checkpoint, including editing.
2. **M2 Cloze control:** one banked and one open cloze back-to-back.
3. **M3 Reading control:** two passages with stable accuracy and pacing, including
   constrained short answers.
4. **M4 Exam readiness:** two separate full simulations using no practice or diagnostic
   item, each run after a Mathematics paper.

### 7.3 Thresholds

Initial internal thresholds: 75% for exit tickets, 80% untimed and 75% timed for
checkpoints and milestones. These are product defaults, not scholarship cut-offs. Beta
data calibrates difficulty and thresholds without rewriting historical attempts.

### 7.4 Forms

- Every checkpoint and milestone has an initial form and a retry form.
- Baseline, endline and reserve forms are built from the same blueprint with matched
  difficulty, so baseline-to-endline change means something.
- Mock forms include a configurable editing section and constrained short answers so
  learners meet the variants reported in some years.

## 8. Content-authoring blueprint

Every learner-visible item is tagged with one primary outcome, an entry level and, where
useful, secondary skills and transfer patterns.

| Prefix | Domain | Example outcomes |
| --- | --- | --- |
| `EV` | Vocabulary | context clue, synonym precision, word family, collocation, register |
| `EG` | Grammar, editing and cohesion | clause, agreement, tense, determiner, preposition, connector, editing |
| `EB` | Banked cloze | grammar filter, meaning filter, global coherence |
| `EO` | Open cloze | function word, form, lexical choice, cross-sentence cohesion |
| `ER` | Reading | reference, vocabulary in context, detail, inference, purpose and tone, own-words answers |
| `EW` | Writing | prompt choice, plan, development, cohesion, vocabulary, grammar, editing, genres |
| `EX` | Integrated exam | orientation, pacing, part completion, full-paper simulation |

### 8.1 Exposure pools

Content pools remain separate: lesson examples; guided practice; independent practice;
exit tickets; exit-ticket retry forms; retry review; module checkpoints and retry forms;
milestones; baseline; endline; full mocks; and protected reserve items.

### 8.2 Passage standards

| Pool | Sec 1 length | Notes |
| --- | --- | --- |
| Lesson example | 80–200 words | May be reused across lessons in the lesson pool only |
| Guided, exit ticket, retry form | 200–400 words | One new passage per group |
| Checkpoint and milestone | 300–500 words | Two passages where the part has two |
| Full mock and reserve | 450–700 words each | Two reading passages plus a banked and an open cloze |

- Every passage has paragraph numbers and can mark underlined target words.
- Each reading set covers at least three question types (for example reference,
  meaning in context and inference).
- The mix across a module includes narrative and informational texts, and over the
  course at least one letter, report or diary-style text.
- Settings follow section 3.3. Passages are original or licensed, with attribution in
  the passage record.

### 8.3 Item standards

- **Distractors:** every distractor is plausible for a stated reason (wrong word class,
  wrong connotation, supported by the topic but not the sentence) and has an authored
  rationale.
- **One best answer:** reviewers try to argue for each distractor. If one can be
  defended, the item is revised.
- **Difficulty:** levels 1–5 describe reasoning and language demand, not rare
  vocabulary.
- **Word-limited answers:** the limit is stated in the question and checked
  automatically before submission.

### 8.4 Accepted alternatives and the rejected-answer log

Deterministic marking can wrongly reject a valid answer. Therefore:

- every rejected short-text answer is logged with its item revision;
- learners can tap "I think my answer is also right", which adds a note to the log;
- a reviewer checks the log weekly. A valid alternative is added through a new item
  revision, and affected attempts are re-marked under that new revision with an audit
  record.

### 8.5 Review gate

The English review gate checks: language accuracy; one-best-answer determinism;
unintended accepted answers; cultural accessibility; passage coherence and length band;
distractor plausibility; original authorship or licence; alignment to the declared
outcome and entry level; and age-appropriate content. Content drafted with AI assistance
is reviewed to the same standard and its provenance records the method.

## 9. Minimum content inventory for the Beta

These are planning estimates for running every pool once without repeats. The English
educator should adjust them.

| Content | Basis | Approximate total | On the branch now |
| --- | --- | --- | --- |
| Lessons | 55 lessons | 55 | 28 drafts |
| Sentence-level items | 13 sentence lessons × (2 guided + 3 independent + 5 exit + 5 retry form); E1/E2 checkpoints and retry forms; M1; diagnostics; mock vocabulary and editing | about 400 | 12 |
| Passages | 17 passage lessons × 3 (guided, exit, retry form); checkpoints; M2 and M3; diagnostics; 3 mock forms | about 85 | 14 |
| Writing models | 1–2 original models per writing lesson | about 30 | 0 |
| Writing prompts | lesson practice, timed bank, checkpoint and mock pairs | about 80 | a few practice prompts inside E6–E8 lessons |
| Word profiles | 8–10 families per weekly set | 300–400 | 0 |
| Anchor essays | 4 genres × 4 bands × 2, plus edge cases | 32–40 | 0 |

Passages are the largest authoring and review cost. Sentence-level review items can
partly come from word profiles (section E1).

## 10. Measuring whether it works

The Beta has 10–30 learners, so results are descriptive, not proof. The plan still
records:

- **Learning gain:** baseline to endline change per strand on matched forms.
- **Retention:** how often items returning after 7 and 14 days are answered correctly.
- **Writing transfer:** early and late essays on unseen prompts, scored blind by human
  markers who do not know which came first.
- **Item health:** proportion correct (target 30–90% outside diagnostics), whether
  stronger learners outperform weaker ones on the item, how often each distractor is
  chosen, and time taken. Items outside the targets are reviewed.
- **Rejected answers and learner reports** (section 8.4).
- **Completion:** lessons proficient per week against the route's expected pace.
- **After the test:** a recall form from every Beta learner who sits the April test,
  feeding the next blueprint revision.

## 11. What the learner should be able to do at completion

An English-ready learner can:

- infer and test unfamiliar vocabulary instead of depending on memorised definitions;
- retrieve a growing bank of useful word families and collocations across contexts;
- find and fix common errors, including their own recurring transfer patterns;
- use syntax and discourse clues to solve banked and open cloze passages;
- trace references, locate evidence, distinguish stated meaning from inference and
  answer in their own words within a word limit;
- manage two reading passages without losing a checking buffer;
- choose between two prompts quickly and produce a focused plan within five minutes;
- write a developed, organised composition of about the required length in 30 minutes,
  by hand;
- revise high-impact content and language weaknesses using an evidence-linked rubric;
  and
- explain recurring errors and apply the correction on a new task.

## 12. Approval and implementation order

Before high-volume authoring:

1. English-educator review of the outcomes, the four new lessons, the route tags,
   terminology, the error taxonomy and the draft rubric;
2. add the section 1.2 sources to `sources.json`, including the entry level of the 2026
   report;
3. confirm or leave configurable the counts, marks, prompt choices and length rule per
   entry level;
4. freeze v2 stable outcome keys and question-type contracts, adding the new lessons with
   new keys and leaving every existing key unchanged; and
5. build the assessment layer before E9: the E0 baseline, a retry form for every drafted
   exit ticket, module checkpoints and the human-feedback writing path. E9 (compressing the
   process and the full simulation) depends on learners writing real compositions.

## 13. Open questions

1. What entry level, year and country was the 2026 candidate report?
2. Has the Indonesian test been paper-based in every recent sitting?
3. Does the Indonesian Section 1 still include editing or written short answers?
4. What length wording appears on the essay paper at each entry level?
5. Should glosses in Bahasa Indonesia be offered, and who reviews them?
6. Who are the Beta essay markers, and how many essays per learner can they handle?
7. When is the 2027 selection test? (The 2026 sitting was 11–12 April.)

## 14. Evidence references

- Singapore Ministry of Education,
  [ASEAN Scholarships Applicant Guide 2026](https://www.moe.gov.sg/-/media/files/asean-scholarship/asean-scholarships-applicant-guide-2026.pdf).
- Singapore Examinations and Assessment Board,
  [PSLE English Language syllabus and examination format (2022)](https://www.seab.gov.sg/docs/default-source/national-examinations/syllabus/psle/2022_psle_subject_info/0001_y22_sy.pdf).
- Candidate accounts used to identify constructs only:
  [2013 Sec 1, Penang](http://isy-glowz.blogspot.com/2013/06/asean-scholarship-selection-test.html);
  [2014, Surabaya](http://bakagamidiot.blogspot.com/2014/11/pengalaman-ikut-seleksi-beasiswa-asean.html);
  [2016 Sec 1 and Sec 3](http://miscellaneousfragments.blogspot.com/2016/06/asean-scholarship-singapore.html);
  [2020 Sec 3, Penang](https://zoestudyingabroad.blogspot.com/2020/12/asean-scholarship-selection-test-how-to.html);
  [2012 Pre-U](https://michelleteoh.com/2012/06/18/asean-scholarships-for-malaysia-selection-tests/).
- Preparation summaries:
  [Geniebook](https://geniebook.com/exam-preparation/asean/article/asean-scholarship-selection-test-interview-how-prepare-it);
  [indbeasiswa 2026 notice summary](https://indbeasiswa.com/beasiswa-sma-di-singapura/).
- US Institute of Education Sciences,
  [Improving Adolescent Literacy: Effective Classroom and Intervention Practices](https://ies.ed.gov/ncee/wwc/practiceguide/8).
- US Institute of Education Sciences,
  [Teaching Secondary Students to Write Effectively](https://ies.ed.gov/ncee/WWC/PracticeGuide/22).
- Education Endowment Foundation,
  [Improving Literacy in Secondary Schools](https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/literacy-ks3-ks4).
- Kim and Webb,
  [Does spaced practice have the same effects on different second-language vocabulary learning activities?](https://onlinelibrary.wiley.com/doi/10.1111/modl.12879).
- Hu and Nation (2000), "Unknown vocabulary density and reading comprehension",
  *Reading in a Foreign Language* 13(1).
