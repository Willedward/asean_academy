# English content audit — November 2026

**Audit date:** 2 November 2026
**Branch audited:** `feature/bulk-question-authoring-pipeline` at `fe25859`
**Content root:** `backend_resources/english/v1`
**Reference documents:** [LAYER_1_ENGLISH_SCOPE.md](./LAYER_1_ENGLISH_SCOPE.md),
[LAYER_1_ENGLISH_CURRICULUM.md](./LAYER_1_ENGLISH_CURRICULUM.md),
[LAYER_1_ENGLISH_FOUNDATION_EXECUTION.md](./LAYER_1_ENGLISH_FOUNDATION_EXECUTION.md) and
[LAYER_1_ENGLISH_V3B_ROUTE_BLUEPRINT.md](./LAYER_1_ENGLISH_V3B_ROUTE_BLUEPRINT.md)
**Detailed findings:** [english_content_audit_2026_11/](./english_content_audit_2026_11/)

## 0. Status and boundaries

This is an advisory pre-review audit. It is **not** an English-educator or editorial
approval, and it records no decision in the review pipeline.

- No content file, review record, approval, `reviewed_at` or `reviewed_by` field was changed.
  Every lesson, passage, question, form, prompt and rubric remains `draft`.
- Every correction below is a *proposal* for the human English educator and editor. They may
  accept, change or reject it. The decision to approve any revision stays with those people.
- No paid or external model API was called. The audit used static reading of the source files,
  local scripts over the JSON and the repository's own offline validators.
- The validators pass: `english-foundation-validate` and `english-authoring-validate` both report
  0 errors and 0 warnings. They check structure, so they cannot catch the language, ambiguity
  and validity defects below.

**Correction, 4 November 2026.** The product owner confirmed that English targets the Secondary
3-entry test at Secondary 1 and 2 level, not Secondary 1 entry. The level judgements in §4.6 and
§5.3 used the wrong band of about 11–12 and must be redone. The profile and form keys named here
now use `sec3` in place of `sec1`.

## 1. Scope and method

| Asset | Files | Audited |
| --- | --- | --- |
| Lessons | 41 | All sections, against curriculum §3–4 |
| Passages | 37 | All 36 that are linked to questions, read in context; 1 orphan noted |
| Objective questions | 119 files / 552 scored parts | Every part: key, options, short-text answer sets, hint, rationales |
| Forms | 23 (baseline, endline, reserve, 20 checkpoints) | Composition, comparability, cue exposure |
| Essay prompt / rubric | 1 / 1 | Consistency with the curriculum and the exam profile |

Method:

1. Every question was rendered with its passage, options, key, accepted answers, hint and
   rationales. Six content slices were then each reviewed by a separate pass (vocabulary and
   grammar, cloze, reading, two writing slices, lessons). Each reviewer answered every item
   *before* reading the key. For banked cloze, every bank word was tested at every gap. For open
   cloze, the reviewer listed every defensible one-word answer.
2. Every S1 claim, plus the cross-cutting claims about the rendering code, was then checked again
   by the coordinating reviewer against the source JSON and the learner player code.
3. Learner-facing exposure was taken from the code, not assumed:
   - The part `prompt`, the question `title` and `instructions` are shown in **every** mode,
     including the protected diagnostics and checkpoints.
     See `english_learning_service.py` `_public_part` / `_public_question`,
     `english-practice-player.tsx:785` and `english-diagnostic-player.tsx:300`.
   - In practice, one **Show hint** click shows the hints for *all* parts of a grouped
     question (`english_learning_service.py` `hint()`). Using a hint fails the mastery
     threshold.
   - Short-text marking is exact after NFKC normalisation, whitespace collapsing and
     case-folding. No item sets `strip_terminal_punctuation`, so an answer such as "an." is
     marked wrong.
4. **Level-fit basis.** The only exam profile, `exam_profiles/asean-english-sec1-id-reported-v1.json`,
   has `entry_level: secondary_1_entry`. Applicants for that entry are normally in their final
   primary year, about 11–12, and learn English as a second language. Level fit was judged
   against that band. If the Beta also targets later entry points, the educator should confirm
   the intended band per profile. Several level findings depend on this.

Severity scale:

- **S1 (blocker):** a wrong key, a second genuinely correct answer, or an answer given away in a
  diagnostic, checkpoint or reserve.
- **S2 (major):** material ambiguity, leakage in practice or exit tickets, a grammar error in
  learner-visible text, or a clear level mismatch.
- **S3 (minor):** polish.

## 2. Executive summary

| Slice | Detail file | S1 | S2 | S3 |
| --- | --- | ---: | ---: | ---: |
| Vocabulary and grammar items (`ev-*`, `eg-*`) | [A](./english_content_audit_2026_11/A_vocabulary_grammar.md) | 3 | 23 | 19 |
| Banked and open cloze (`eb-*`, `eo-*`) | [B](./english_content_audit_2026_11/B_cloze.md) | 21 | 14 | 17 |
| Reading comprehension (`er-*`) | [C](./english_content_audit_2026_11/C_reading.md) | 5 | 9 | 16 |
| Writing and orientation items (`ex-l1-*`, `ex-l2-*`) | [D](./english_content_audit_2026_11/D_writing_items_ex_l1_l2.md) | 0 | 21 | 20 |
| Writing items (`ex-l3-*` to `ex-l5-*`) | [E](./english_content_audit_2026_11/E_writing_items_ex_l3_l5.md) | 4 | 13 | 16 |
| Lessons (`e0`–`e9`) | [F](./english_content_audit_2026_11/F_lessons.md) | 1 | 45 | 18 |
| **Total finding entries** | | **34** | **125** | **106** |

Some entries bundle several gaps or items, so these counts understate the number of affected
parts.

**Overall judgement.** The content is carefully written, consistently uses British spelling, is
original, and handles the evidence boundary well: candidate-reported facts are almost always
labelled as provisional. Most single-choice keys are correct. However, the bank **is not ready
for English approval in its current revision**, for five reasons:

1. **Three wrong, unanswerable or misdirected keys**, two of them in the baseline diagnostic, plus
   two items with a second correct answer.
2. **About 20 open-cloze and reading short-text parts** would mark correct learners wrong,
   because a valid alternative is missing from the accepted answers.
3. **Strong test-wise cues.** In 265 of 352 single-choice parts (75%), the correct option is
   uniquely the longest. D is the key in only 22 parts (6%). With this strategy alone, a learner
   scores 5/5 on five of the twenty checkpoint forms and on every reading part of the baseline.
4. **Answers leak into protected measurement** through visible titles, open-cloze prompts that
   name the word class, checkpoint instructions that pre-diagnose the flaws, and reuse of taught
   words in the reserve and endline. In addition, lesson worked examples copy 36 of the 41
   lessons' exit tickets.
5. **The baseline, endline and reserve forms are not equivalent.** The endline is labelled and
   built easier than the baseline, so measured growth would be inflated.

Coverage stands at 41 of 51 lessons. Every Sprint lesson is present; the Core route lacks five
lessons. Real guided and independent practice items exist for only 4 lessons.

## 3. S1 blockers

Every row was checked again against the source by the coordinating reviewer. The detail files
give the full evidence and wording for each row.

### 3.1 Wrong, contradictory or unanswerable keys

| Item (pool) | Location | Evidence | Proposed correction |
| --- | --- | --- | --- |
| `eb-l1-003` gap 1 (**baseline**) | `questions/eb-l1-003.json` part 1; `passages/english-passage-baseline-club-noticeboard.json` P1 | "found its noticeboard unusually {{1}}. Posters from the previous term still covered every corner…". Key A = **bare**, and the rationale says "bare" shows "too little free space". | "Bare" means empty, the opposite of a board covered in posters, and no other bank word fits. Replace option A with **cluttered** (or *crowded*) and rewrite rationale A. |
| `eo-l5-002` gap 6 (retry) | `questions/eo-l5-002.json` part 6; `passages/english-passage-ridge-weather-station.json` P3 | "He checked the reading {{6}} the class left…". Canonical answer **again**. | "Again" leaves the sentence without a conjunction, so it is ungrammatical, and nothing earlier was checked. Key **before** and accept *as*, *when* and *after* only if the story allows them; otherwise rewrite to "He checked the reading once {{6}}…". |
| `eo-l5-003` gap 5 (**baseline**) | `questions/eo-l5-003.json` part 5 | The prompt reads "mark the time **before which** the second check occurred", but the key is **after** ("…and again {{5}} it was returned"). | The prompt points to the opposite answer. Rewrite it as "Gap 5: complete the time clause", and accept **after, when, once, as**. |
| `eb-l1-002` gap 1 (retry) | `questions/eb-l1-002.json` part 1; `english-passage-community-garden-opening` P1 | "Nara arrived {{1}} at the community garden." Key **early**; the bank also contains **calmly**, which no other gap needs. | Both complete the passage validly. Rewrite the frame so that only a time adverb fits (e.g. "Nara reached the garden {{1}} in the morning, an hour before the gates opened"), or replace distractor "calmly" with a non-adverb. |
| `eg-l2-001` part 3 (exit ticket) | `questions/eg-l2-001.json` part 3 | "Which compound-subject sentence is correct?" Options: A "The coach and captain **is** reviewing." / B "…**are** reviewing" (key). | "The coach and captain is…" is correct when one person holds both roles. Use "**The coach and the captain** ___ reviewing…". |

### 3.2 Short-text answer sets that reject correct answers

| Item | Missing accepted answers (examples) | Proposed correction |
| --- | --- | --- |
| `er-l2-001` part 2 | Key "Dr Arun". Rejected: "Dr. Arun", "Arun", "the ecologist". | Add these variants. |
| `er-l2-001` part 3 | The passage's own clause; "…to **a** covered walkway" in the short form. | Convert to single choice (event referents cannot be marked by exact match). |
| `er-l1-001` part 4 | "the soil had absorbed the pooled water", "Within a few hours, the soil had absorbed the pooled water". | Convert to single choice. |
| `er-l4-001` part 2 | "one metre", "1 metre", "1 m", "one meter". | Add these variants, or ask "How many metres above the ground…?". |
| `er-l4-001` part 5 | "shade sails near the main gate" (the passage's own wording), "shade sails". | Add both. |
| Open cloze, concession gaps: `eo-l1-001` g5, `eo-l1-002`, `eo-l5-001` g2, `eo-l5-002`, `eo-l5-003` g4, `eo-l5-004` | **while/whilst**, and **though** where it is missing. *But* and *yet* where the clause order allows. | Use one agreed concession set for all parallel forms. "Though" is accepted in `eo-l1-001` and `eo-l5-004` but not in `eo-l1-002` or `eo-l5-002`. |
| `eo-l1-002` | **till** (accepted in the sibling `eo-l1-001` and `eo-l1-003`), **This**. | Add these. |
| `eo-l5-003` g3 (**baseline**) | "worried {{3}} bicycles…". *Some* and *the* are valid because "that" is optional. | Rewrite the frame so that only the complementiser fits, or accept all three. |
| `eo-l3-001` | **standstill** ("came to a ___"), **care / control**. | Add these, or tighten the frames. |
| `eo-l4-001` g4 | "Only {{4}} did he notice…": **later / afterwards**. | Add these. |
| `eo-l2-001` g3 | Several verbs fit the frame; the key simply repeats "checks". | Tighten the frame, or accept the valid verbs. |
| `eo-l5-002` | **when / once**, **others**. | Add these. |

All five reading rows are in exit tickets. Appendix B lists every cloze gap with its full
alternative set, including the "conditional" alternatives that become correct once the
leaking prompts in §4.3 are removed.

### 3.3 Answers revealed inside protected forms

| Item (form) | Evidence | Proposed correction |
| --- | --- | --- |
| `ex-l5-008` part 1 (E6 checkpoint form B) | The stem names "the community-court **booking-board** focus", which is the keyed answer of `ex-l1-011` part 3 in the same form. | Use a neutral stem: "Which pair of body-paragraph jobs best develops the focus you chose in the previous task?". Or move the item to a separate form. |
| `ex-l4-005`, `ex-l4-006` (E8 checkpoint forms A and B) | The instructions list the draft's defects: "begins with book-cover colours", "one agreement error", "comma splice", "opens with supermarket music". | Give only the verified notes and the flawed draft. The learner must find the defects. |
| `ex-l5-007` part 2 (E6 checkpoint form A) | The stem says the plan "never explains how they solved the problem", and the key is the only option that adds that explanation. | Ask "What is the most important gap in this plan?" without naming it. |
| `eg-l2-004` part 2 (E2 checkpoint form B) | The prompt asks which sentence "identifies the **plural** head subject", and only one option has a plural verb. | Ask "Which sentence is grammatically correct?". |
| `ev-l5-004` part 2 (**endline**) | It reuses the baseline word **reluctant** with the identical key "unwilling or hesitant", and the baseline's post-form feedback has already shown that key. | Replace it with an unseen word of matched frequency. |
| `ev-l5-005` parts 1, 2, 3, 5 (**protected reserve**) | Taught or practised words with identical keys: *tentative → provisional* (worked example in `e5-lesson-03`, exit ticket `er-l3-001`), *scarce* (exit ticket `ev-l5-001`), *coherent* (exit ticket `ev-l1-006`), *verify* (practice `ev-l2-004`). | Re-author the reserve from words that appear in no other pool. |
| Protected open-cloze prompts: `eo-l5-003` (baseline), `eo-l5-004` (endline), `eo-l5-005` (reserve), `eo-l1-003`, `eo-l1-004`, `eo-l5-006`, `eo-l5-007` (checkpoints) | The prompts name the word class or define the answer: "indefinite article", "relative pronoun referring to Mr Sadiq", "earlier than the presentation" (= *before*), "show that Niko repeated" (= *again*). | Use a uniform protected prompt such as "Gap *n*: write one word." Then expand the accepted sets to the alternatives this opens (Appendix B lists them as "conditional"). |

## 4. Cross-cutting findings

### 4.1 Option length and key position cue the answer (S2; S1 when it decides protected forms)

These figures come from a script run over all non-banked single-choice parts.

| Measure | Result |
| --- | --- |
| Single-choice parts (all have 4 options) | 352 |
| Key position distribution | A 119 · B 143 · C 68 · **D 22** |
| Key is uniquely the longest option | **265 / 352 (75%)**. By type: writing (`ex`) 178/196, reading 58/75, vocabulary 25/56, grammar 11/25 |
| Multiple-response key patterns | 13 of the 22 writing multiple-response parts are keyed exactly A+B+C; 28 of all 29 multiple-response keys include A |
| Option shuffling at delivery | None. Options are served in authored order. |

Effect of always choosing the longest option:

| Form | Score |
| --- | --- |
| E0 checkpoint A and B | 5/5 |
| E6 checkpoint B | 5/5 |
| E9 checkpoint A and B | 5/5 |
| E7 checkpoint B, E8 checkpoint A and B | 4/5 |
| Baseline reading set (`er-l5-005`) | 5/5 (B, B, A, D, B — all longest) |
| Vocabulary checkpoints `ev-l5-006` and `ev-l5-007` | Every part is keyed **A** |

The distractors are mostly absolutes ("always", "proved", "guarantees scholarship admission") or
self-refuting. The key is usually the only hedged option, so the bank also teaches the heuristic
"choose the cautious long answer".

**Proposed correction:**

- Revise distractors so that every option has comparable length and hedging.
- Include at least one plausible near-miss per part.
- Balance key positions within each form and across each bank.
- Add a validator warning when the key is uniquely longest by more than about 30%, and when a
  form's key positions are unbalanced.
- Decide as a product matter whether options should be shuffled per attempt. A shuffle would
  need rationales that reference option text rather than position; several retry items refer to
  options "by position".

### 4.2 Visible titles name the answer (S2 by the scale; recommend treating it as release-blocking)

Both learner players render `question.title` as the heading. Every EV1.2 and EV1.4 title names
the keyed word, for example "Adverb slot: **clearly**", "Transfer item: **provisional**" and
"Parallel transfer item: **frank**". This affects `ev-l2-001`–`007` and `ev-l4-001`–`007`,
including the exit tickets `ev-l2-006` and `ev-l4-006`.

**Proposed correction:** adopt an authoring rule that titles never contain the target word, form
or answer (for example "Word-family item 3"). Alternatively, render a neutral learner title and
keep the descriptive title for reviewers only.

### 4.3 Open-cloze prompts turn construction into recall (S1 in protected pools, S2 elsewhere)

Every open-cloze item uses part prompts such as:

- "enter the article required before 'unopened wooden box'";
- "enter the auxiliary that completes the past-perfect verb phrase";
- "enter the pronoun that refers to the wooden box".

The curriculum (E4 purpose) requires learners to "construct the missing word from grammatical
and discourse evidence". The prompt does that analysis for them, and it uses grammar terms
("past-perfect", "possessive determiner", "inversion") that are beyond the 11–12 band. Many
gaps are uniquely answerable *only because of* the prompt.

**Proposed correction:**

- Use neutral prompts in all pools: "Gap *n*: write one word."
- Keep clue-type guidance in the hint (practice only) and in the post-submission explanation.
- Re-run the alternative search per gap once the prompts are neutral (Appendix B).

### 4.4 Lessons copy the assessed items (S2, 36 lessons; S1 where it reaches the reserve)

Worked examples, warm-ups and models reuse the linked exit ticket or practice items, often word
for word. Examples:

- `e7-lesson-04`: the model introduction and ending are the keys of `ex-l4-002` parts 1 and 4.
- `e3-lesson-01`: the story map solves about 5 of the 8 exit-ticket gaps.
- `e4-lesson-01` to `e4-lesson-05`: each gives 4–5 of its exit passage's 8 answers.
- `e1-lesson-02` and `e1-lesson-04`: give the keys of every guided and independent item.
- `e2-lesson-02`: contains the exact correct sentences of `eg-l2-001` parts 1 and 4.

The E6–E9 exit tickets reuse the lesson's own scenario (mostly the charity sale), so none is
the "one unseen transfer item" that curriculum §3 step 7 requires. The E3 and E4 checkpoints
(`eb-l1-006`, `eo-l5-006`, `eo-l5-007`) reuse the same frames and answers (*deserted, explained,
again, unless, had*).

Only `e5-lesson-02` and `e5-lesson-07` have worked examples that are independent of their exit
ticket.

**Proposed correction:** for each lesson, keep the worked example on a different topic, word set
and passage from the exit ticket. Re-author the exit tickets that cannot be separated. Extend the
duplicate checker to compare lesson text with question stems and keys.

### 4.5 Baseline, endline and reserve are not equivalent (S2, validity of the growth claim)

| Strand | Baseline | Endline | Reserve |
| --- | --- | --- | --- |
| Vocabulary | `ev-l5-003`: difficulty 3, 0/5 words seen before | `ev-l5-004`: difficulty 3, **3/5 words already practised**, 1 repeats the baseline word | `ev-l5-005`: difficulty 3, **4/5 words already practised** |
| Banked cloze | `eb-l1-003`: difficulty 3, **gap 1 unanswerable** | `eb-l1-004`: difficulty 3 | `eb-l1-005`: difficulty 3 |
| Open cloze | `eo-l5-003`: **difficulty 4**, gap 5 prompt wrong | `eo-l5-004`: difficulty 3 | `eo-l5-005`: difficulty 3 |
| Reading | `er-l5-005`: **difficulty 4, 163 words**, 5/5 longest-option | `er-l5-006`: difficulty 3, 129 words, 3/5 | `er-l5-007`: difficulty 3, 129 words, 3/5 |

The endline is easier by label, by length and by word exposure. The baseline also contains two
defective parts that depress baseline scores. Together these would overstate learner growth,
which conflicts with the scope requirement that the forms be "disjoint, reviewed and versioned"
and matched.

The format is also an issue (S3, validity). The profile describes Part 1 as "choose the word whose
meaning best completes or fits a sentence". All diagnostic and checkpoint vocabulary sets use the
reverse "What does X most nearly mean?" gloss format.

**Proposed correction:**

- Fix the baseline defects.
- Build the endline and reserve against a written specification shared with the baseline:
  outcome mix, word frequency band, passage length, number of gaps per clue type, and option
  length profile.
- Use only words that appear in no practice, lesson or other diagnostic pool.
- Add at least one sentence-completion vocabulary format to each form.

### 4.6 Level fit for the `secondary_1_entry` band (S2)

Vocabulary items:

- Targets and glosses are often C1–C2: *gregarious* (labelled difficulty 2), *conciliatory*,
  *scrutinised*, *negligible*, *sporadic*, *corroborated*, *cryptic*.
- Some keys are harder than the word tested: *tentative → provisional*,
  *meticulous → painstaking*.

Reading passages:

- They lean heavily on research and method vocabulary: *salinity*, *median*, *consecutive*,
  *deferred*, *self-selection*.
- About 13 of 19 passage texts follow one genre, "students run a trial and report its limits",
  even though the paper reportedly includes narrative and descriptive texts.

Writing lessons and items (E6–E9):

- The text reads at an estimated school grade of 10–13.
- It relies on about 20 named routines and acronyms (T-C-A-S-P, I-S-A-R, "reverse outline",
  "reflective hinge", "process compression").
- E2 uses "finite verb", "head subject" and "antecedent" without defining them.
- The E0.2 items assess the platform's own test-integrity policy ("matched form", "blueprint",
  "construct", "confounds") rather than the learner outcome.

**Proposed correction:**

- Ask the educator to confirm the target band.
- Set vocabulary from a declared frequency list (for example, high-frequency academic word
  families appropriate to the entry year).
- Cap the metalanguage, and teach each routine as a plain-English question rather than a named
  acronym.
- Rewrite E0.2 items around learner behaviour ("work alone", "don't look up answers", "finish
  every part").
- Add narrative and general informational passages.

### 4.7 Writing outcomes are measured only by recognition (S2, validity)

Every E6–E9 exit ticket and checkpoint is deterministic multiple choice or multiple response.
No lesson asks the learner to produce a plan, paragraph or revision, yet the curriculum
milestones (E6: "create a relevant, coherent plan for three unseen prompts within five minutes";
E7: "independently write a coherent multi-paragraph response"; W1–W6) are production outcomes.

This is a defensible Beta constraint while essay marking stays disabled. It should be stated
explicitly in the curriculum, and the MCQ checkpoints should not be reported as evidence of the
production milestones.

**Proposed correction:**

- Add short production tasks, such as a five-minute plan or one paragraph, that are self-checked
  against the pinned rubric (the ENG-T3.4 self-review pattern).
- Label E6–E9 mastery as "planning and editing judgement" rather than writing mastery.

### 4.8 "Use only the verified notes" items keyed beyond the notes (S2)

Four items instruct learners to use only the supplied notes, then key answers that contain
facts the notes do not include. Distractors are rejected for exactly that reason. The items are
`ex-l2-006` part 3, `ex-l2-009` part 2, `ex-l2-011` part 1 and `ex-l2-012` part 1.

Related model-text overclaims:

- `ex-l3-004` part 3 says "prevents", where the record says "makes … difficult".
- `er-l4-001` part 6 says the sails "reduced" the temperature, where the passage only compares a
  shaded surface with exposed pavement.

**Proposed correction:** add the missing facts to the notes, or re-key. The exact wording is in
Appendices C–E.

### 4.9 Passage presentation and internal consistency

- In the two-passage sets (`er-l5-003`, `er-l5-004`, `er-l5-008`, `er-l5-009`), the
  "PASSAGE A —" and "PASSAGE B —" headings are stored as `paragraphs`. Paragraph references in
  the questions therefore miscount when the player numbers paragraphs (S2). Store the headings
  outside `paragraphs`, or number paragraphs per sub-passage.
- `eb-l1-001` calls the studio "deserted" while Mr Lim stands in it. `eb-l1-006` calls the
  rooftop "deserted" while Ms Hana is present (S2). Use "unusually quiet" or similar.
- `eb-l1-005` rationales mention "Silently", which is not in its bank (S3).
- Several banked-cloze distractor rationales are copy-paste boilerplate. Some claim that words
  are ungrammatical when they are grammatical (`eb-l1-001`, `eb-l1-002`) (S3).
- `passages/english-passage-neighbourhood-garden.json` is learner-quality text but is referenced
  only by tests (S3). Either mark it as a fixture or link it to content.

### 4.10 Hints (S3, with one product note)

Many hints give the answer away or are identical boilerplate. Examples:

- "Say the phrase aloud and listen to the first sound in 'unopened'".
- Multiple-response hints that list the keyed categories.

The impact is limited because hint use voids mastery. However, one click reveals the hints for
every part of a grouped passage. For an 8-gap cloze, that means asking for help on gap 1 also
gives away gaps 2–8.

**Proposed correction:** write hints as strategy prompts that point to the clue location, not
the answer. Consider (as a product decision) per-part hint reveal for passage groups.

### 4.11 Smaller language corrections in learner-visible text (S2 grammar; selected)

| Location | Text | Proposed |
| --- | --- | --- |
| `ex-l1-006` part 3 | "Which activity best prepares open cloze?" | "Which activity best prepares you for open cloze?" |
| `e8-lesson-02` section 3 | Calls a non-defining (comma) relative clause an "identifying detail". | "a non-identifying (extra-information) detail" |
| `ex-l1-002`, `ex-l2-002` models | "exposed that…" | "showed that…" / "revealed that…" |
| `er-l2-002` part 5 | "The devices" is ambiguous between the dryers and the paper streamers. | Name the referent class in the stem, or change the passage noun. |
| `er-l3-002` part 6 | The correct option contains "meticulous → painstaking", which gives away part 3. | Remove the overlap. |

The remaining S2 and S3 language notes are in the appendices, with exact text.

## 5. Coverage against the curriculum

### 5.1 Lessons and items per outcome

| Module | Curriculum lessons | Authored | Missing | Items with real guided/independent practice |
| --- | --- | --- | --- | --- |
| E0 | 3 | E0.1, E0.2 | **E0.3** (Diagnose the mistake) | — |
| E1 | 6 | E1.1, E1.2, E1.4, E1.6 | **E1.3**, **E1.5** (Core) | E1.1, E1.2, E1.4 (5 items each) |
| E2 | 6 | E2.1, E2.2 | **E2.3** (Core), **E2.4**, **E2.5**, **E2.6** (Core) | E2.1 (5 items) |
| E3 | 4 | E3.1 | **E3.2** (Core), **E3.3**, **E3.4** (Core) | — |
| E4 | 5 | E4.1–E4.5 | — | — |
| E5 | 7 | E5.1–E5.7 | — | — |
| E6 | 5 | E6.1–E6.5 | — | — |
| E7 | 5 | E7.1–E7.5 | — | — |
| E8 | 5 | E8.1–E8.5 | — | — |
| E9 | 5 | E9.1–E9.5 | — | — |
| **Total** | **51** | **41** | **10** | **4 lessons** |

By route:

- **Sprint:** 16/16 lessons authored.
- **Core:** 27/32 authored. It lacks E1.5, E2.3, E2.6, E3.2 and E3.4, which matches the V3b
  blueprint.
- **Full:** 41/51 authored.

**Practice depth.** 37 of 41 lessons link no items in their guided-practice or
independent-application sections. In E3–E5 the independent task is the exit-ticket passage
itself, so the exit ticket is not unseen. The curriculum's anatomy (§3, steps 4–5) and "sufficient
isolated practice" exit criterion (scope document) are not yet met for any strand except E1 and
E2.1.

Several lessons are only outlines, at 120–180 words for a 30-minute estimate: `e0-lesson-01`,
`e0-lesson-02`, `e1-lesson-06`, `e2-lesson-02` and `e9-lesson-05`. E9.5 "Full English simulation"
contains no simulation.

### 5.2 Checkpoints and milestones against the curriculum's stated evidence

| Checkpoint | Curriculum expectation | Authored form | Gap |
| --- | --- | --- | --- |
| E1 | Infer meanings, distinguish near-synonyms, apply word families and collocations; 80% untimed then 75% timed | 5 gloss items (EV1.6), every key **A** | No near-synonym, word-family or collocation coverage; no timed set |
| E2 | Mixed editing and gap set, with justification | EG2.2 agreement/reference only | No clause-boundary, tense, determiner, preposition or connector items |
| E3 | Two unseen passages, one of them timed | One 5-gap passage per form | Single passage; frames reused from the exit ticket |
| E4 | One mixed timed open-cloze passage | 3 + 2 gaps from two passages | Very short; prompts leak (§4.3) |
| E5 | Unseen two-passage set | 5 questions over about 430 words, 18-minute target | Adequate in form; generous timing |
| E6 | Plans for three unseen prompts, five minutes each | MCQ judgements | Recognition only (§4.7) |
| E7 | Revise a response, then write from a plan | MCQ on EW7.2 only | Recognition only; EW7.1/7.3–7.5 untested |
| E8 | Improve a flawed draft and explain the revisions | MCQ on EW8.4; instructions pre-diagnose the flaws | Leakage (§3.3); EW8.1–8.3 and 8.5 untested |
| E9 | Full simulation | Protocol MCQs | No simulation form |

Assets the curriculum requires that do not exist yet:

- full mock forms and the M1–M4 cumulative milestones;
- the second full Section 1 form (only one baseline/endline pair and one reserve exist);
- vocabulary word profiles;
- the four recurring strands (vocabulary retrieval, wide reading, sentence craft, writing
  fluency).

The execution plan already lists these as E5/E6 work. They are recorded here as coverage gaps,
not defects.

### 5.3 Essay prompt and rubric

- **One prompt only:** `prompts/english-essay-prompt-school-learning-transfer-v1-v1.json`, which
  is reflective/personal expository. The text is clear and age-appropriate, and its 30-minute
  and 300-word guidance is correctly labelled candidate-reported. The curriculum's prompt bank
  for guided, untimed and timed writing does not exist yet. There are no narrative or opinion
  prompts even though E9.2 and E9.3 teach those forms.
- **Rubric shape differs from the curriculum (decision for the educator).**
  - Curriculum §5 specifies **five criteria × four bands**: task fulfilment and ideas;
    organisation and cohesion; vocabulary and register; sentence control and grammar; mechanics.
  - `rubrics/english-essay-rubric-instructional-v1-v1.json` has **four criteria × five bands**:
    task fulfilment; organisation and cohesion; development and evidence; language control.
    Vocabulary, grammar and mechanics are merged.
  - Either shape is defensible. However, the curriculum and the rubric should agree before the
    T3.9 anchor set is scored, because band anchors cannot be transferred between shapes.
- **Descriptor language** (e.g. "proportionate material", "economical structure", "qualification")
  is educator-facing. If learners see the rubric in self-review, learner-facing descriptors are
  needed for the 11–12 band.

## 6. Recommended sequence for the human reviewers

1. **Fix the S1 rows in §3** before any English approval decision is recorded. Most of them sit
   in the baseline, endline, reserve or checkpoints.
2. **Adopt four authoring rules and add validator warnings for them:**
   - no answer in titles;
   - neutral open-cloze prompts in protected pools;
   - option-length and key-position balance;
   - no reuse of lesson, practice or exit content in protected pools.
3. **Re-author the endline and reserve** to a shared specification with the baseline (§4.5).
4. **Separate lesson worked examples from exit tickets** (§4.4), and populate guided and
   independent practice for the Sprint lessons first.
5. **Confirm the target age band and the rubric shape** (§4.6, §5.3). Then make one level-fit
   pass over the E6–E9 metalanguage and the EV word lists.
6. **Close the Core gaps** (E1.5, E2.3, E2.6, E3.2, E3.4) and the checkpoint coverage gaps
   (§5.2).

Each proposed correction should produce a new content revision with its own English and
editorial decision. This audit does not substitute for that review.

## Appendices

| Appendix | Scope |
| --- | --- |
| [A — Vocabulary and grammar items](./english_content_audit_2026_11/A_vocabulary_grammar.md) | `ev-*`, `eg-*`, and lessons e1-01/02/04/06 and e2-01/02 for leakage |
| [B — Banked and open cloze](./english_content_audit_2026_11/B_cloze.md) | `eb-*`, `eo-*` and their passages; full per-gap alternative sets |
| [C — Reading comprehension](./english_content_audit_2026_11/C_reading.md) | `er-*` and their passages; timing of the two-passage sets |
| [D — Writing and orientation items, set 1](./english_content_audit_2026_11/D_writing_items_ex_l1_l2.md) | `ex-l1-*`, `ex-l2-*` |
| [E — Writing items, set 2](./english_content_audit_2026_11/E_writing_items_ex_l3_l5.md) | `ex-l3-*`, `ex-l4-*`, `ex-l5-*` |
| [F — Lessons](./english_content_audit_2026_11/F_lessons.md) | All 41 lessons |

Each appendix entry gives the location (file and part, gap, option or section), severity,
category, the quoted evidence, the problem and a concrete proposed correction. Each appendix
ends with a slice summary and a list of items judged sound.
