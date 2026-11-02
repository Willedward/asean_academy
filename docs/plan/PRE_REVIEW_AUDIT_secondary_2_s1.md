# Secondary 2 S1 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_2/s1/v1/`
(batches B001–B004) and all six S1 lessons (`s1-lesson-05` to `s1-lesson-10`). The lessons
are stored in `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/`, the course
folder named `g2`, and were found through the `g3-sec2-s1` unit in that folder's
`course.json`.

**Decision boundary:** this is a report-only technical pre-review. No question, lesson, SVG,
manifest, pool or claim was edited. No approval was recorded and no review state was changed.
All 104 questions and all six lessons are `draft`, and all four batches show
`mathematics: pending` and `editorial: pending`. No rendered images are committed.

**Audience:** students across Indonesia and Southeast Asia preparing for the Sec 3-entry
ASEAN Scholarship test (see `LESSON_NOTES_CONTENT_STANDARD.md`).

## Counts

| Item | Count |
| --- | ---: |
| Questions checked | 104 (21 / 31 / 31 / 16 / 5 at difficulty 1–5) |
| Questions recomputed numerically with code | 65 |
| Categorical (code-selection) questions checked by reasoning | 39 |
| Lessons checked | 6 |
| Diagrams referenced by questions | **0**. No S1 question has an asset. |
| Diagrams referenced by lessons | 6 |
| Diagrams rendered to PNG and viewed | **6 of 6**, at 960 px and at 390 px phone width |
| Lesson SVG checksums matching the lesson JSON | 6 of 6 |

The rendering method was headless Chromium (pre-installed Playwright). Each SVG was embedded
as an `<img>` and screenshotted into a session scratch directory outside the repository. The
author also read the SVG source coordinates and text positions directly.

## Severity scale

- **Critical:** a learner who gives a correct answer is marked wrong, or the answer key is
  wrong or ambiguous.
- **Major:** must be fixed before Mathematics or editorial approval. This covers rule
  violations, a misleading diagram, a learner-visible render defect, or an item that does
  not assess its outcome or difficulty.
- **Minor:** quality or consistency improvement.

## Summary

- **No canonical answer is mathematically wrong.** All 65 numeric answers match an
  independent recomputation.
- **Three d4 questions cannot be answered correctly.** Their canonical answers are stored as
  floating-point noise (for example `3.333333333333332`) with `exact_numeric`. Running the
  repository's own `checking.check_answer` rejects `4`, `10/3`, `3.33` and `20/7`. One of
  these questions is in the unit checkpoint pool.
- **Five solutions contain a raw TAB character** where `\times` should be. They render as
  "imes".
- **Seven questions are keyed ambiguously or inconsistently** in categorical choices. Three
  more have two defensible answers.
- **Stage-2 hints give away the answer in 38 questions.** This includes all 35 code-selection
  items in outcomes 1.6 and 1.9.
- **The bank is heavily templated.** 104 items reduce to about 35 templates. There are 8
  groups of word-for-word identical prompts (25 items), and several templates always have
  the same answer.
- **Every prompt starts with a machine-generated prefix.** The context it names is unrelated
  to the task, and its slug can hint at the answer.
- **All six lesson diagrams have defects.** These include a clipped key sentence, overlapping
  captions, misplaced median and mean markers, a non-uniform number line, a decision guide
  that contradicts its lesson, and text far too small at phone width.
- **Lesson prose is 1,386–1,835 characters, against the 2,500-character baseline.** The
  validator passes them because it counts the JSON serialisation, not authored text.

---

## Part 1 — Content findings

### 1.1 Answer correctness and checker behaviour

Each answer was recomputed from the prompt with a Python script, using exact `Fraction`
arithmetic, before reading the solution. Every value was also passed through
`question_bank.checking.check_answer` with the stored response spec.

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-01 | s1-l4-501 | **Critical** | Canonical `4.000000000000002`, `exact_numeric`. True value 265/15 − 205/15 = 4. The checker rejects `4` and `4.0` and accepts only `4.000000000000002`. The solution also prints `4.000000000000002`. In `s1-unit-checkpoint`. | Set canonical `4` and update the solution's A-step. |
| C-02 | s1-l4-507 | **Critical** | Canonical `3.333333333333332`. True value 310/18 − 250/18 = 10/3, which does not terminate. The checker rejects `10/3`, `3.33`, `3.333` and `3.3333333333`. The prompt gives no rounding instruction. In `s1-adaptive-reserve`. | Either change the frequencies to give a terminating difference, or set canonical `10/3` with `comparison_mode: rounded_sf` (3 s.f.) or `absolute_tolerance` and state "correct to 3 significant figures" in the prompt. House rules v2 require exact answers by default and explicit rounding. |
| C-03 | s1-l4-510 | **Critical** | Canonical `2.8571428571428577`. True value 355/21 − 295/21 = 20/7. The checker rejects `20/7`, `2.86` and `2.857`. In `s1-adaptive-reserve`. | Same fix as C-02. Canonical `20/7`, state the rounding, and use `rounded_sf`. |
| C-04 | s1-l2-505, s1-l2-506, s1-l2-513, s1-l2-523, s1-l2-529 | Major | The solution LaTeX holds a literal TAB (U+0009) followed by `imes100`, because `\t` in `\times` was read as an escape. It shows as "… imes100 = 100" in the solution. All five are in `s1-lesson-07-practice`. | Replace the TAB plus `imes` with `\times`. Add a validator check that rejects control characters in LaTeX strings. |
| C-05 | s1-l2-505, s1-l2-506, s1-l2-513, s1-l2-523, s1-l2-529 | Minor | The task asks for a "percentage increase". The answer is `100` with `unit: null`. The checker turns `100%` into 1 and marks it wrong. | Add "Give your answer as a number without the % sign", or support a `%` unit. |
| C-06 | s1-l4-505, s1-l4-516; s1-l2-501, s1-l2-510, s1-l2-518, s1-l2-519, s1-l2-526 | Minor | Canonical answers are `2.0` and `15.0`. The checker still accepts `2` and `15`, but the solution displays the float form. | Store integers. |

All other numeric keys were confirmed. This includes s1-l3-501/507/515/523/524, where f always
equals the first frequency, the baseline items s1-l3-504/511/512/518/528 (105–125), and
s1-l5-501 (2.5), s1-l5-502 (y = 11, order 5 ≤ 7 ≤ 9 ≤ 11 ≤ 13 holds) and s1-l5-504 (k = 11).

### 1.2 Ambiguous or inconsistent categorical keys

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-07 | s1-l3-506, s1-l3-514 | **Critical** | Data 8, 9, 9, 10, 45 (46). The task asks for the measure "not pulled upward by the extreme observation". The **mode is also 9**, equal to the median, so code 3 is just as defensible as the key, 2. | Use data where the mode is not central (for example 8, 9, 10, 10.5 … or a bimodal set), or accept both answers and ask a reasoning question instead. |
| C-08 | s1-l3-521, s1-l3-522, s1-l3-530, s1-l3-531 | **Critical** | Data 11, 12, 12, 13, 75–78. The **mode is 12, equal to the median**, so codes 2 and 3 are both defensible. | Same as C-07. |
| C-09 | s1-l2-504, s1-l2-512 (key 3) vs s1-l3-503, s1-l3-510, s1-l3-517, s1-l3-526, s1-l3-527 (key 1) | **Critical** | "24 integer scores … recover every score while also seeing the distribution" is keyed to stem-and-leaf. "18 whole-number results … clusters and gaps while retaining individual observations" is keyed to dot diagram. Both displays keep every value and show shape, so the requirements are nearly the same but the keys differ. For s1-l3-526/527 (comparing two classes), a back-to-back stem-and-leaf diagram is the standard Singapore syllabus answer. | Add the deciding constraint to each prompt. For stem-and-leaf, use a wide two-digit range (as s1-l5-505 does well). For dot diagram, use a narrow range of small integers. Alternatively, ask the learner to reject a stated unsuitable option. |
| C-10 | s1-l4-503, s1-l4-508, s1-l4-512 | **Critical** | The task asks which display is "least suitable because it would become overcrowded" for 2,400 heights. A stem-and-leaf diagram (code 3) would hold 2,400 leaves and is equally overcrowded, but only 1 is keyed. | Restrict the options (for example histogram vs dot diagram), or accept {1, 3} and make the task a two-part justification. |
| C-11 | s1-l2-521, s1-l2-522, s1-l2-528 | Minor | "Keep every recorded age, arrange them in order and reveal the distribution" also fits a dot diagram. The prompt does not say how widely the 31 ages range. | State a wide range of values (for example 120–480 years). |
| C-12 | s1-l1-505, s1-l1-515, s1-l1-521 | Minor | "Most resistant" to one long delay. The mode is also unaffected by an extreme value, although it is a weak choice for continuous times. | Add "continuous travel times with no repeated values". |

### 1.3 Hint leakage (house rules v2: "neither hint may state the final answer")

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-13 | All 35 code-selection items in outcomes 1.6 and 1.9: s1-l1-503, 505, 508, 512, 515, 518, 521; s1-l2-504, 509, 512, 516, 517, 521, 522, 525, 528, 531; s1-l3-503, 506, 510, 514, 517, 521, 522, 526, 527, 530, 531; s1-l4-503, 506, 508, 509, 512; s1-l5-503, 505 | Major | The stage-2 hint names the keyed representation or measure, so the code follows immediately. Examples: "That definition identifies the mode." (s1-l2-509), "The median is resistant to one very large observation." (s1-l1-505), "A stem-and-leaf diagram retains every age…" (s1-l2-521), "The mean uses all values…" (s1-l4-506). | Stage 2 should narrow the choice without naming the answer. For example, "Which displays keep exact values? Of those, which stays readable for a wide range?" |
| C-14 | s1-l4-504, s1-l4-513, s1-l4-515 | Major | The stage-2 hint "Subtract 10 from 30." (or from 45 or 60) is the whole one-step computation. | Remove it, or replace it with a conceptual prompt. See also C-18. |
| C-15 | All 104 (prefix slug) | Major | The title slug is copied into each prompt and can telegraph the answer. Examples: "most common category" (mode, s1-l2-509 group), "typical value with an outlier" (median), "preserve exact values" / "retain archaeological measurements" (stem-and-leaf), "reject an unsuitable display". | See W-01. |

### 1.4 Outcome and difficulty alignment

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-16 | s1-l1-502, 507, 511, 517; s1-l2-502, 503, 511, 520, 527; s1-l3-502, 508, 509, 516, 525; s1-l4-502, 511, 514; s1-l5-501 (outcome 1.5) | Major | Outcome 1.5 is "analysis and interpretation of dot diagrams, histograms and stem-and-leaf diagrams", but no S1 question shows a diagram. For example, "A dot diagram represents the values 3, 5, 6, 5, 7, 5, 4. How many dots are positioned at 5?" is counting in a list. | Supply the diagram (see Part 2, "Text-only questions that need diagrams") and ask the learner to read it. |
| C-17 | s1-l1-504, 509, 513, 519; s1-l2-505, 506, 513, 523, 529; s1-l3-504, 511, 512, 518, 528; s1-l4-504, 513, 515 (outcome 1.7) | Major | Outcome 1.7 is "explaining why a statistical diagram leads to misinterpretation", but no misleading diagram is ever shown. The flaw is described in words, which gives away the diagnosis. | Show the flawed chart and ask for the flaw, or for its quantitative effect. |
| C-18 | s1-l4-504, s1-l4-513, s1-l4-515 | Major | Labelled d4 and 4 marks (M3 A1), but the task is "30 − 10". It never assesses the misinterpretation: the line "Use this calculation before judging the misleading heights" is followed by no judging. This violates house rules v2 ("Levels 4 and 5 must require method selection, constraints, justification or sustained synthesis"). | Rewrite. For example: "Heights 10 and 30 are drawn for widths 5 and 15. By what factor does the chart exaggerate the second class's density?" (answer: the visual ratio 3 vs the true density ratio 1). |
| C-19 | s1-l4-503, 508, 512, 506, 509; s1-l5-503, 505 | Major | Single code-selection answers carry 4–5 marks (M3/M4 + A1) and d4–d5 labels. The "M" marks cannot be earned separately. | Re-grade these to d2–d3 with 1–2 marks, or turn them into multi-part tasks that compute and then justify. |
| C-20 | s1-l3-502, 508, 509, 516, 525 | Minor | d3 and 3 marks for adding two frequencies. | Re-grade to d1–d2, or add a reading-from-histogram step. |
| C-21 | All 83 multi-step solutions | Minor | Every M-step text is "Extract the relevant values and apply the stated statistical method." and every A-step is "State the requested value and check that it matches the data and representation." Neither explains anything or performs a check. | Write item-specific steps with a real verification step (for example, substitute f back into the mean). |

### 1.5 Semantic duplicates

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-22 | {s1-l1-503, 508, 512, 518}, {s1-l1-505, 515, 521}, {s1-l2-504, 512}, {s1-l2-509, 516, 517, 525, 531}, {s1-l2-521, 522, 528}, {s1-l3-503, 510, 517}, {s1-l3-526, 527}, {s1-l4-503, 508, 512} | Major | The prompts are word-for-word identical once the prefix is removed: 8 groups, 25 items, 17 redundant. `s1-lesson-06-practice` contains only 4 distinct tasks among its 10 items, and `s1-lesson-09-practice` only 3. | Replace the redundant items with original tasks. |
| C-23 | All 104 | Major | There are only about 35 templates. Several always return the same answer: two-class mean always 10; three-class grouped mean always 15.0; stem-and-leaf range always 7; displayed bar increase always 100%; mean increase always 2; and in the missing-frequency items f always equals the first frequency. This breaks house rules v2 ("Avoid repeating a prior question's … operation pattern and numerical structure"). | Vary the structure and answers. The near-prompt detector does not catch number-shifted clones. |
| C-24 | s1-lesson-09 WE2 ↔ s1-l2-509 group; s1-lesson-06 WE1 ↔ s1-l2-504, s1-l2-512; s1-lesson-07 WE1 and diagram ↔ s1-l1-504; s1-lesson-10 active recall ↔ s1-l1-506 | Major | Lesson worked examples and active recall repeat practice items exactly. The lesson therefore solves the practice question before the learner meets it. | Change the lesson numbers or contexts, or replace the practice items. |

### 1.6 Wording and audience

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| W-01 | All 104 | Major | Every prompt starts "‹Colour› ‹Tree› Bay dataset for ‹club›: ‹title slug› — …". The named context has nothing to do with the task. For example, s1-l2-509 "Komodo field camp" is about a shoe shop, and s1-l1-503 "Mekong ecology club" is about a teacher's reaction-time data. The text reads as machine output and leaks hints (C-15). | Remove the prefix and write one coherent context sentence. Keep Southeast Asian contexts where they relate to the data. |
| W-02 | 39 code-selection items (C-13 list plus s1-l1-504, 509, 513, 519) | Major (judgment) | "Use code 1 for … Enter the code" changes a choice of representation or measure into numeric entry. This allows a 20–33% guessing rate and does not match how the scholarship test asks or how reasoning is shown. | Reviewer decision: use MCQ or ordered-option support if the platform has it, or turn these into compute-and-interpret tasks. |
| W-03 | s1-l3-502, 508, 509, 516, 525 | Minor | "How many observations lie from 10 up to 30?" leaves the inclusion of 30 ambiguous, and no class-boundary convention is stated. | "… in the classes 10 ≤ x < 20 and 20 ≤ x < 30". |
| W-04 | s1-l5-501 | Minor | "Three bars have frequencies … The missing class …" never says there are four classes. | "A histogram has four classes…". |
| W-05 | Lessons 05–06 and their diagrams vs the question bank | Minor | Terminology is mixed: "dot diagram" (syllabus and bank, lesson 05 text) and "dot plot" (lesson 05 SVG and alt text, lesson 06 text and active recall). | Use one term and gloss the other once. See conflict X-01. |
| W-06 | s1-lesson-05 to s1-lesson-10 summaries | Minor | All six summaries are the same generic paragraph. It mentions "class boundaries" and "key" even in lessons 08–09, where they do not apply. | Write lesson-specific checklists. |
| W-07 | s1-lesson-05 WE2; s1-lesson-06 WE1, WE2; s1-lesson-08 WE2; s1-lesson-09 WE1, WE2 | Minor | The `verification_note` restates the method rather than checking the answer (for example "Each result follows a different definition."). The standard requires "a verification note". | Add a real check, for example recompute the total from the mean. |
| W-08 | s1-lesson-07 active recall | Minor | "Enter 1 if this can mislead or 0 if it is fair" is a 50% guess. | Ask for the issue code or the corrected spacing. |

### 1.7 Lesson-note depth

| ID | Lesson(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| L-01 | s1-lesson-05 (1,630), 06 (1,835), 07 (1,774), 08 (1,386), 09 (1,588), 10 (1,545). Figures are authored characters, summing text, LaTeX and title fields. | Major (judgment) | The standard requires "at least 2,500 authored characters across its teaching sections". `course_validation.lesson_note_depth_shortfalls` measures `len(json.dumps(sections))`, which includes keys, stable keys and response metadata. So `course-validate` reports 0 warnings, and the coverage table in `LESSON_NOTES_CONTENT_STANDARD.md` lists Secondary 2 S1 as "Meets the baseline". | Expand each lesson (for example a dot-diagram and a back-to-back stem-and-leaf worked example in lesson 05). Separately, decide whether the validator should count authored text only. |
| L-02 | s1-lesson-05 | Minor | Objective 1 ("Read frequencies, clusters, gaps and spread from dot diagrams") and the back-to-back stem-and-leaf idea have no worked example. | Add one. |

All lesson worked examples and active-recall answers were confirmed. Lesson 05 gives 20, 20,
median 34 and range 7. Lesson 07 gives 4/96 ≈ 4.2%. Lesson 08 gives 17, and 6 / 4 / 4.
Lesson 10 gives 340/14 ≈ 24.29 and f = 2 (check: 220/10 = 22).

### 1.8 Process and standards conflicts

| ID | Severity | Evidence | Proposed action |
| --- | --- | --- | --- |
| X-01 | Judgment for reviewers | The N2 audit and `house-rules-v2.json` (`locale: en-SG`, "Singapore/British English", `currency: SGD`, "Use S$") conflict with `LESSON_NOTES_CONTENT_STANDARD.md`. That standard says the Singapore syllabus "does not define the learner's country … use clear international English … contexts that work across Southeast Asia". In S1 the conflict is small: there is no currency, and the British spellings (centre, recognise) suit both. The live cases are (a) "dot diagram" (Singapore syllabus term) vs "dot plot" (international), and (b) the blueprint's `course: "Singapore G3 Mathematics"` vs the course title "ASEAN Scholarship Mathematics — Level 2". The target test is Singapore-administered, which argues for keeping syllabus terms with an international gloss. This audit does not decide either way. | Reviewers decide, then update house rules v3 or the lesson standard so the two agree. |
| X-02 | Minor | All four S1 batch manifests list `house-rules-v1.json` in `source_references` while declaring `prompt_version: math-question-authoring-v2`. The N2 audit required manifests to move to house rules v2. Several v2 rules (hints, duplicates, d4/d5 rigour, exact answers) are broken above. | Re-point the manifests to v2 when the batches are regenerated. |
| X-03 | Major | Pool impact. `s1-unit-checkpoint` contains C-01 (unanswerable). `s1-adaptive-reserve` contains C-02 and C-03. `s1-lesson-07-practice` contains all five C-04 items. Lesson-06 and lesson-09 practice pools are mostly duplicates (C-22). | Rebuild the pools after the fixes. |

---

## Part 2 — Diagrams and graphs

**Question diagrams:** none. No S1 question has an `assets` entry, and there is no
`diagram_audit.json` for this bank. Only the geometry banks (Sec 1 G1, Sec 1 G5, Sec 2 G2)
have one.

**Lesson diagrams:** 6, all resolved from `asset.path` relative to
`backend_resources/courses/g3_math/secondary_2/g2/v1/`. All 6 were viewed. None of them
reveals the answer to an assessed task. Lesson 08 and lesson 10 show the data of their own
worked examples, which is acceptable.

| ID | Asset path | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D-01 | assets/s1-lesson-05-distributions.svg (s1-lesson-05) | Neatness | Major | The caption "Histogram area shows grouped frequency." starts at x=355 and is about 345 px wide at 19 px, so it runs to about x=700. It overlaps "A key gives place value." at x=670, so in the render "frequency" and "A key" print on top of each other. | Centre the three captions under their panels (x≈180, 490, 790, `text-anchor="middle"`), each at most 260 px wide. Shorten to "Bar area shows frequency." or wrap to two lines. |
| D-02 | assets/s1-lesson-05-distributions.svg | Neatness | Minor | The orange accent line (x=710, y 110–195) sits on top of the typed "\|" in "2 \| 1 4 7" and "3 \| 0 3 3 8", giving a doubled separator that touches the leaves. | Remove the "\|" characters from the text and keep one separator line, with stems right-aligned to x≈700 and leaves starting at x≈722. |
| D-03 | assets/s1-lesson-05-distributions.svg | Accuracy | Major | There is no number-line scale on the dot diagram, no class boundaries or frequency axis on the histogram, and no stem-and-leaf key. Yet the diagram's own caption ("A key gives place value") and footer ("Always read the axis scale, class boundaries and key") tell learners to read exactly these. | Add value ticks under the dots, x-boundaries and a frequency axis to the histogram, and "Key: 2 \| 1 means 21" under the stem-and-leaf. |
| D-04 | assets/s1-lesson-05-distributions.svg | Accuracy | Major | The title "Three views of a distribution" implies one dataset, but each panel shows a different one. The dots have frequencies 1, 2, 3, 1 (7 values). The histogram bars are in the ratio 5 : 9 : 7. The stem-and-leaf lists 21, 24, 27, 30, 33, 33, 38, which would group as 3 and 4. | Draw one dataset in all three panels (for example the 7 stem-and-leaf values, with a histogram of 20–25, 25–30, 30–35, 35–40 at frequencies 2, 1, 3, 1). Otherwise, retitle it "Three kinds of display". |
| D-05 | assets/s1-lesson-05-distributions.svg | Accuracy | Minor | The panel label and alt text say "dot plot", while the lesson text and the bank say "dot diagram". | Use "dot diagram" (or whichever term X-01 settles on). |
| D-06 | assets/s1-lesson-06-representation-choice.svg (s1-lesson-06) | Accuracy | Major | "exact lookup → frequency table" contradicts the lesson ("Stem-and-leaf diagrams retain exact ordered values. … Frequency tables support compact lookup and calculation") and the bank keys (exact recovery → stem-and-leaf, s1-l2-504 and s1-l5-505). A grouped frequency table loses exact values. | Relabel to "compact counts / calculation → frequency table". Add or move "exact ordered values → stem-and-leaf". |
| D-07 | assets/s1-lesson-06-representation-choice.svg | Accuracy | Minor | "small discrete data → dot or stem-and-leaf" gives no way to choose between the two, which is the distinction the bank tests with opposite keys (C-09). | Split it into "repeats, gaps, small range → dot diagram" and "exact two-digit values in order → stem-and-leaf". |
| D-08 | assets/s1-lesson-06-representation-choice.svg | Neatness | Minor | The orange bracket (`M175 250v70h610v-70`) joins boxes 1 and 3, skips box 2, and points at nothing. The line "detail • shape • scale • audience" below it has no visible link to it. This looks like a stray element. | Remove the bracket, or draw a connector from all three boxes to a labelled "Also consider: detail, shape, scale, audience" panel. |
| D-09 | assets/s1-lesson-06-representation-choice.svg | Neatness | Minor | Box text is positioned with hand-tuned left offsets (x=95/98, 402/435, 714/722) rather than centred. "dot or stem-and-leaf" ends about 8 px from the box edge. | Use `text-anchor="middle"` at the box centres x=175, 480 and 785. |
| D-10 | assets/s1-lesson-07-misleading-axis.svg (s1-lesson-07) | Neatness | Major | The key message "Visible heights double although the values rise only about 4.2%." starts at x=540 and is about 560 px wide. It runs past the 960 viewBox and is cut off after "rise onl" in the render. | Place it at x=480 with `text-anchor="middle"`, or start at x=60, or wrap it to two lines. |
| D-11 | assets/s1-lesson-07-misleading-axis.svg | Accuracy | Major | Neither chart has a vertical axis or tick values. "baseline at 92" appears only as a panel caption, so the figure never shows what a truncated vertical axis looks like, although the lesson says "Inspect both axes". The bar heights themselves are correct: 2.5 px per unit from 0 gives 240 and 250, and 20 px per unit above 92 gives 80 and 160. | Add y-axes with ticks: 0, 20 … 100 on the left chart, and 92, 94 … 100 with an axis-break mark on the right chart. |
| D-12 | assets/s1-lesson-07-misleading-axis.svg | Accuracy | Minor | The values 96 and 100 are written as x-axis category labels, which mixes up category and value. | Use category labels (for example "Shop A", "Shop B") with value labels above the bars. |
| D-13 | assets/s1-lesson-08-centre.svg (s1-lesson-08) | Accuracy | Major | The number-line scale is not uniform. 2→x 210, 4→330 and 7→510 give 60 px per unit, but 13→810 is only 50 px per unit beyond 7. The mean marker at x=460 equals 6.17 on the 60 px scale, not 6. The picture therefore distorts the "balance point" idea the lesson teaches. | Map v → x = 100 + 55v: 2→210, 4→320, 7→485, 13→815, mean 6→430, all within the axis 100–860. Add ticks 0–13. |
| D-14 | assets/s1-lesson-08-centre.svg | Accuracy | Minor | There are no axis ticks, and the mean has no tick or value on the axis. Its marker floats below the line. | Add a tick and the label "6" at the mean. |
| D-15 | assets/s1-lesson-09-resistant-centre.svg (s1-lesson-09) | Accuracy | Major | The "median" marker is at x=250, between the 2nd (230) and 3rd (270) of five dots. For five values the median is the 3rd ordered value, at x=270. The mean marker at x=360 = (190+230+270+310+800)/5 is correct. | Move the median line to x=270. |
| D-16 | assets/s1-lesson-09-resistant-centre.svg | Accuracy | Minor | There are no numbers, scale or units, although the title says "times". The figure cannot be linked to the lesson or bank data (11, 12, 12, 13, 75). | Plot real values on a minutes axis and label the median (12) and mean (24.6). |
| D-17 | assets/s1-lesson-10-grouped-mean.svg (s1-lesson-10) | Accuracy | Minor | The title says "Estimate with midpoint × frequency", but the table has no fx column and no totals. The classes "10–20, 20–30" share endpoints and no boundary convention is given. The values match lesson WE1 (15, 25, 35; 4, 7, 3). | Add an fx column (60, 175, 105) with Σf = 14 and Σfx = 340, and label the classes "10 ≤ x < 20" and so on. |
| D-18 | All six S1 lesson SVGs | Neatness | Major | They do not read well at phone width. The 960×480 canvas is scaled by 0.406 at 390 px, so the 19 px `.s` labels become about 7.7 px and the 25 px `.t` titles about 10.2 px, well below a readable 12 px. This was confirmed in the 390 px renders. | Author at a viewBox of about 600 wide with label text of at least 28 px, or stack the panels vertically (lessons 05 and 07). |
| D-19 | s1-lesson-06 and s1-lesson-10 SVGs | Neatness | Minor | Slate text (#334155) on teal fill (#65b7ad) has a contrast ratio of 4.4:1, below WCAG AA 4.5:1, and is worse at phone scale. | Use a pale fill (for example #d7efeb) behind the text. |
| D-20 | All six S1 lesson SVGs and their JSON | Accuracy (alt text and spec) | Minor | Each SVG `<desc>` is boilerplate ("… teaching diagram"). The alt texts do not give the plotted data (for example lesson 08 omits 2, 4, 4, 7, 13 and mean 6). Every `generation_spec` holds only renderer, kind and lesson key, with no data. The alt texts do agree in general terms with what is drawn. | Put the plotted data in `generation_spec` and in the alt text, and write a real `<desc>`. |

### Root-cause patterns

1. **One hand-placed template behind all six SVGs.** All six share the same `<style>` block,
   960×480 canvas, `rx=28` backdrop, 25 px and 19 px fonts and absolute x coordinates with no
   text-width measurement. This produces the overlap and clipping (D-01, D-10), the
   off-centre text (D-09), phone illegibility (D-18) and low contrast (D-19). **All 6
   diagrams are affected.**
2. **The renderer named in the metadata is not in the repository.** The JSON names
   `renderer: nextscholar-statistics-svg-v1`, but no code by that name exists.
   `scripts/recalibrate_geometry_content.py` only emits `nextscholar-geometry-svg-v1`. The
   SVGs were added as finished 3-line files in commit `958925e`. Because `generation_spec`
   carries no data, plotted positions cannot be regenerated or checked. This is how the
   misplaced markers and uneven scale (D-13, D-15) and the mismatched panels (D-04) got
   through. **6 diagrams.**
3. **Validators do not cover statistics diagrams.**
   `question_bank/src/question_bank/geometry_validation.py::geometry_diagram_issues` runs on
   every lesson asset. But `angle_diagram_issues` returns `[]` unless
   `diagram_kind == "angle_types"`, `_angle_marker_issues` returns `[]` without
   `angle_markers`, and `_answer_leak_issues` returns `[]` without
   `forbidden_visible_labels`. Course validation only adds a checksum check. So every
   statistics SVG "passes" without any check of geometry, text bounds or data. A
   statistics-chart validator should check that text bounding boxes stay inside the
   viewBox and do not overlap, and that data maps to coordinates on a uniform scale.
4. **Question-bank generator artefacts.** The generator (`codex-offline-s1-v1`) is not in the
   repository, but its output shows four patterns:
   - It fills about 35 templates with colour × tree "Bay" names and puts the title slug
     into the prompt (W-01, C-15, C-22, C-23).
   - It writes Python `float` results using `repr` as canonical answers (C-01 to C-03,
     C-06).
   - It escapes `\\frac` but not `\times` in a non-raw string, which produces the TAB
     (C-04).
   - It applies one boilerplate M/A step text to every multi-step item (C-21).
5. **The lesson-depth metric counts JSON, not prose** (L-01).

### Text-only questions that need diagrams

There is no `diagram_audit.json` for Secondary 2 S1. The geometry standard only requires one
for `G` topics. A diagram would clearly help, and is effectively needed for the outcome, in
the following questions:

- **Outcome 1.5 (read the display):**
  - Dot diagrams: s1-l1-502, s1-l1-507, s1-l1-511, s1-l1-517.
  - Stem-and-leaf diagrams with key: s1-l2-502, s1-l2-503, s1-l2-511, s1-l2-520, s1-l2-527.
  - Equal-width histograms: s1-l3-502, s1-l3-508, s1-l3-509, s1-l3-516, s1-l3-525.
  - Frequency-density histograms: s1-l4-502, s1-l4-511, s1-l4-514, s1-l5-501.
- **Outcome 1.7 (diagnose the flawed chart):**
  - Truncated bar charts: s1-l2-505, s1-l2-506, s1-l2-513, s1-l2-523, s1-l2-529, s1-l3-504,
    s1-l3-511, s1-l3-512, s1-l3-518, s1-l3-528.
  - Misleading histograms: s1-l4-504, s1-l4-513, s1-l4-515.
  - Flaw identification from a picture, not a description: s1-l1-504, s1-l1-509, s1-l1-513,
    s1-l1-519.

That is 35 questions. The recommendation is to create an S1 `diagram_audit.json` that
records a decision for each question, as the geometry banks do.

## Could not verify

- **Exact KaTeX output of the TAB in C-04.** The control character is confirmed in the
  JSON. The "imes" display is inferred from how KaTeX handles whitespace, not taken from a
  screenshot of the learner UI.
- **Text widths.** These were estimated from Arial metrics and confirmed visually in the
  Chromium renders. The production app may use a different fallback font, which could make
  D-01 and D-10 better or worse.
- **Live learner, admin and review UIs** were not run. How the app scales the SVGs, and
  whether it shows a percent unit, is assumed from the asset size and the response schema.
- **The `codex-offline-s1-v1` generator** and the `nextscholar-statistics-svg-v1` renderer
  are not in the repository. Their root causes above are inferred from their output.
- **Pedagogical judgements** are flagged for human review and not settled here: the
  code-response format (W-02), the dot-diagram vs stem-and-leaf criteria (C-09) and the
  locale policy (X-01).
