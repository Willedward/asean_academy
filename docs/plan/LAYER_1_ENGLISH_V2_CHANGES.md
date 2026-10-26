# English plans v2: what changed and why

**Date:** 26 October 2026
**For:** William (to accept, edit or reject) and Alvaro
**Files:** [LAYER_1_ENGLISH_CURRICULUM_V2.md](./LAYER_1_ENGLISH_CURRICULUM_V2.md),
[LAYER_1_ENGLISH_SCOPE_V2.md](./LAYER_1_ENGLISH_SCOPE_V2.md) and
[LAYER_1_ENGLISH_FOUNDATION_EXECUTION_V2.md](./LAYER_1_ENGLISH_FOUNDATION_EXECUTION_V2.md),
saved beside the v1 files, which are unchanged
**Based on:** `feature/bulk-question-authoring-pipeline` at `d3537be` (26 Oct 2026, 28 lessons drafted)

No existing file was changed or removed. These are proposals for William to accept, edit
or reject; if accepted, the v2 text can replace v1 in a separate change.

## What stays the same

- The spiral design and the 10 modules, E0–E9.
- The seven-step lesson.
- Deterministic objective marking with no AI.
- Feedback only after a whole passage is submitted.
- Separate content pools.
- The five-criterion rubric idea, "AI estimate" labelling and no fake scholarship score.
- The review gate: nothing reaches learners unreviewed.
- XP, streaks, quests and the planner stay in Layer 2.

## The changes

### 1. More evidence, and a way to collect it

- **What:** the evidence table grows from one candidate report to six candidate accounts
  (2012–2026, Malaysia and Indonesia, Sec 1, Sec 3 and Pre-U), two preparation
  summaries, and the PSLE English format as a difficulty reference for Sec 1. A
  structured "test recall" form is added, with a rule for when a fact counts as
  confirmed (three independent recent reports at the same entry level).
- **Why:** v1 rested on one account whose entry level is not recorded. The extra
  accounts agree on some things (two papers, a 30-minute essay, a choice of two prompts,
  two reading passages, hard vocabulary). They also reveal parts v1 did not cover
  (editing, short written answers) and show that essay length changes with entry level.
- **Files:** curriculum section 1, scope "Evidence" section.

### 2. Entry level becomes a setting

- **What:** every lesson, passage, prompt and form is tagged Sec 1, Sec 3 or both. Sec 1
  is the Beta default.
- **Why:** a 2013 Sec 1 account reports a 200-word essay, while a 2020 Sec 3 account
  reports 300–500. One set of numbers cannot fit both.
- **Files:** curriculum 1.4, scope "Included", execution content rules.

### 3. Course length routes: Full, Core and Sprint

- **What:** lessons are tagged Core (32) and Sprint (16). The weeks to the test suggest a
  length. Beta learners default to Core.
- **Why:** this is simple arithmetic. 51 lessons at two a week is about 26 weeks, but a
  learner starting in December has about 18 weeks before an April test. Without a
  shorter route, Beta learners would never reach writing or mocks.
- **Note:** these are fixed lesson lists, not the Layer 2 planner.
- **Files:** curriculum 2.2 and the lesson tables.

### 4. Four new lessons (51 to 55)

| New lesson | Why |
| --- | --- |
| E2.7 Spot and fix the error | Error identification is reported in 2016, and editing is a PSLE component. v1 had no lesson for mixed editing. |
| E5.8 Answer in your own words | Word-limited short answers are reported in 2020, and "in your own words" in 2012. |
| E9.6 Descriptive writing | Reported as a prompt in 2020 ("describe your ideal house"). |
| E9.7 Personal letters as compositions | Both prompts were letters in the 2013 Sec 1 account. The letter is a genre of the one composition, not a second writing task. |

- **Kept safe:** new lessons get new keys. No existing key or code changes meaning. The
  map uses a new `position` field for order, so E5.8 sits before E5.7 (pacing) and E9.6
  and E9.7 before E9.4 (compress the process).
- **Also changed:** E6.1 keeps its title, but its next revision adds choosing between two
  prompts. E9.3 Opinion is marked as a Sec 3 priority.

### 5. A section on the learners themselves

- **What:** common mistakes Indonesian and Malay speakers make in English, mapped to the
  lessons that fix them (for example "Yesterday she walk", "I bought book", "many
  student", mixing up he and she). There are also optional reviewed Bahasa Indonesia
  glosses, never shown in tests, and rules about settings and cultural knowledge.
- **Why:** these patterns are predictable from how Indonesian works (verbs don't change
  for tense, there are no articles, one word covers both he and she). Targeting them is
  the fastest way to raise accuracy for this audience.
- **Files:** curriculum section 3.

### 6. Practising for a paper test

- **What:** passages get paragraph numbers, underlined words and highlighting. Every
  route includes at least two handwritten timed essays, which are then typed for
  feedback. Mocks run after a Mathematics paper.
- **Why:** candidates report a paper test, sat after the Mathematics paper. Typing is
  faster than handwriting, so typed-only practice gives a false sense of timing and
  length.
- **Files:** curriculum 3.4, scope "Writing in Layer 1".

### 7. Clear rules for exit tickets, hints and lesson states

- **What:**
  - sentence exit tickets grow from one item to five;
  - the pass mark is 75%;
  - using a hint on an exit ticket means "not proficient yet";
  - English uses the same five lesson states as Mathematics;
  - every exit ticket needs a parallel retry form.
- **Why:** one item is too noisy to decide whether a lesson is learned. Today a failed
  exit ticket can only come back as the same item or passage, which tests memory, not
  skill.
- **Files:** curriculum 4.2, execution "Gaps found".

### 8. Essay feedback has a human path

- **What:** in the Beta, trained markers (former ASEAN scholars or English teachers)
  mark essays within 72 hours, with 20% double-marked. AI feedback is added only after it
  passes a gate with actual numbers (agreement close to human markers, consistency,
  quoted evidence that really exists, safety, cost).
- **Why:** in v1 the Beta could not ship until the AI passed an evaluation that has no
  thresholds yet and depends on an anchor set that doesn't exist. With 10–30 learners,
  human marking is practical, builds trust and creates the data the AI evaluation needs.
- **Files:** curriculum 6.4, scope "Writing in Layer 1" and "AI feedback evaluation
  gate".

### 9. A draft rubric with band descriptors, plus an anchor-set spec

- **What:** a 5 × 4 table of short descriptors for the English educator to rewrite. The
  anchor set is defined as two essays per band per genre (at least 32), including
  off-topic, memorised and wrong-length essays, each scored by two raters.
- **Why:** v1 named the criteria but not what each band looks like, and said "several
  prompt families" without a size.
- **Files:** curriculum 6.2 and 6.5.

### 10. Safeguarding, consent and integrity

- **What:**
  - a written procedure when an essay suggests a child may be at risk;
  - parent consent for storing essays;
  - a check on Singapore and Indonesian data laws for minors;
  - a check for memorised template essays;
  - essays treated as data, so an essay saying "ignore the rubric" cannot change the
    marking.
- **Why:** the learners are 11–15 years old and the prompts invite personal writing. v1
  covered logging and privacy but not what to do if a child discloses harm.
- **Files:** scope "Safeguarding and privacy", curriculum 6.7.

### 11. Short "own words" answers are practised, not auto-scored

- **What:** answers that are a word or phrase from the passage are marked exactly.
  Explanation answers are compared with a model answer and a checklist, and are not
  scored.
- **Why:** deterministic marking can't fairly score free sentences, and AI marking here
  would add cost and risk to objective practice.
- **Files:** curriculum E5, scope objective domain.

### 12. A log of answers the marker rejected

- **What:** every rejected typed answer is logged. Learners can say "I think my answer
  is also right". A reviewer checks the log weekly, adds valid alternatives in a new
  revision, and re-marks with an audit record.
- **Why:** open cloze is marked only against an approved list, so a valid answer the
  reviewers didn't think of would be marked wrong for every learner.
- **Files:** curriculum 8.4, scope objective domain.

### 13. Content and review numbers

- **What:** a minimum inventory (about 400 sentence items, about 85 passages, about 80
  prompts, 300–400 word profiles, 32–40 anchors) and about 160–200 hours of English
  review.
- **Why:** 14 passages and 12 sentence-level items exist today, and 28 drafted lessons
  are waiting for review. Without numbers, review capacity looks like a detail when it is
  the slowest dependency.
- **Files:** curriculum 9, execution "Content and review budget".

### 14. Three releases tied to the test date

- **What:**
  - **Release A** (December): baseline, Core lessons ready so far, writing with human
    feedback.
  - **Release B** (mid-January): rest of Core, milestones M1–M3.
  - **Release C** (end of February): mocks, endline.
- **Why:** learners need mocks in March, not in December. Staging lets the Beta start on
  time without publishing unreviewed content.
- **Files:** scope "Staged release", execution "Sequence to Release A".

### 15. Roles, workstreams and a week-by-week plan

- **What:** named roles (with gaps marked "to recruit"), nine workstreams (W1–W9), each
  with an owner, deliverables and a "done when" check, and a week-by-week plan to the
  30 November release candidate.
- **Why:** v1 had an order of phases but no owners or dates.
- **Files:** scope "Roles", execution "Workstreams" and "Sequence".

### 16. Build the assessment layer before E9

- **What:** finish E8, then before E9 build retry forms, the baseline, checkpoints and the
  writing workflow with human feedback.
- **Why:** 28 lessons exist, but there is no baseline, checkpoint, retry form, milestone
  or mock, and no learner has written a composition yet. E9 teaches timed writing and the
  full simulation, so it needs those pieces. Writing also depends on people outside
  engineering (markers, anchor scoring), so it needs the most lead time.
- **Files:** execution "Immediate next milestone".

### 17. Design hooks, academic progress only

- **What:** the module map (islands, stops, crossings, route), the word chest and the
  harbour board are part of Layer 1, showing progress only. The existing English kit
  screens are revised to remove the two writing types, the 30-mark rubric, grammar units
  with stars, quests and XP.
- **Why:** this keeps William's Layer 1 boundary while giving the design a home.
  Layer 2 can attach rewards to the same events later.
- **Files:** curriculum 2.3, scope "Included" and "Web integration".

### 18. Housekeeping

- **What:**
  - build phases are renamed P0–P6, so E0–E9 only ever means modules;
  - the status covers all 28 drafted lessons by module;
  - the header points at the current branch and commit;
  - provenance records AI-assisted drafting;
  - new validator checks are listed.
- **Files:** all three.

## What William would change in code if he accepts

1. `catalogue.json`: add E2.7, E5.8, E9.6, E9.7; add `position`, `entry_level` and
   `route_tags`; retitle E6.1; add a per-entry-level blueprint.
2. `sources.json`: add the new sources and the 2026 report's entry level.
3. Contracts (P1e): constrained short answer, editing correction, self-checked open
   answer, word profiles, forms, essay and human marking, rejected-answer log.
4. Content: five-item exit tickets for E1.1 and E2.1; retry forms for all 28 drafted
   lessons; guided and independent sets for the 26 lessons without them.
5. The validator checks listed in the execution document.
6. Kit revisions for English screens.

## Decisions needed

1. Accept the Core and Sprint routes, or keep one full route?
2. Accept the four new lessons?
3. Human marking as the Beta default for essays: who marks, and how many essays per
   learner?
4. Bahasa Indonesia glosses: yes or no, and who reviews them?
5. Who are the English reviewers, and when can they start?
6. Are the 20 November freeze and 30 November release-candidate dates still current?
7. When is the 2027 test, and what entry level was the 2026 report?

## Evidence used

- [MOE ASEAN Scholarships applicant guide 2026](https://www.moe.gov.sg/-/media/files/asean-scholarship/asean-scholarships-applicant-guide-2026.pdf)
- [SEAB PSLE English Language format (2022)](https://www.seab.gov.sg/docs/default-source/national-examinations/syllabus/psle/2022_psle_subject_info/0001_y22_sy.pdf)
- [2013 Sec 1 candidate account, Penang](http://isy-glowz.blogspot.com/2013/06/asean-scholarship-selection-test.html)
- [2014 candidate account, Surabaya](http://bakagamidiot.blogspot.com/2014/11/pengalaman-ikut-seleksi-beasiswa-asean.html)
- [2016 Sec 1 and Sec 3 candidate account](http://miscellaneousfragments.blogspot.com/2016/06/asean-scholarship-singapore.html)
- [2020 Sec 3 candidate account, Penang](https://zoestudyingabroad.blogspot.com/2020/12/asean-scholarship-selection-test-how-to.html)
- [2012 Pre-U candidate account](https://michelleteoh.com/2012/06/18/asean-scholarships-for-malaysia-selection-tests/)
- [Geniebook preparation summary](https://geniebook.com/exam-preparation/asean/article/asean-scholarship-selection-test-interview-how-prepare-it)
- [indbeasiswa summary of the 2026 notice](https://indbeasiswa.com/beasiswa-sma-di-singapura/)
- Hu and Nation (2000), "Unknown vocabulary density and reading comprehension",
  *Reading in a Foreign Language* 13(1)
