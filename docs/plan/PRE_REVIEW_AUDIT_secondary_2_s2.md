# Secondary 2 S2 (Probability) technical pre-review audit

**Date:** 2 November 2026

**Branch base:** `origin/feature/bulk-question-authoring-pipeline` at `90379c2`

**Decision boundary:** report-only technical pre-review. This audit edits no question,
lesson, SVG, manifest or claim. It records no approval and does not change any review state.

## Scope and counts

| Item | Count | Notes |
| --- | ---: | --- |
| Questions checked | 104 | `backend_resources/question_bank/g3_math/secondary_2/s2/v1/questions/`, batches B001–B004 (26 each). All are `draft`; the batch manifests are `ready_for_review`. |
| Lessons checked | 2 | `s2-lesson-01` (outcome 2.1) and `s2-lesson-02` (outcome 2.2). They are stored in `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/`, the shared Secondary 2 course folder, not in a folder named `s2`. Both are `draft`. |
| Diagrams referenced | 2 | Both are lesson assets. No S2 question references an asset (`assets: []` on all 104). |
| Diagrams rendered and viewed | 2 | Rendered with headless Chromium (Playwright) to PNG at 940 px and 390 px wide, in a scratch directory outside the repo. No images are committed. |
| Approved content | 0 | There are no approval records for any S2 question or lesson, so no review state was at risk. |

The S2 bank has no `diagram_audit.json`. The diagram-audit requirement in
`GEOMETRY_CONTENT_STANDARD.md` applies only to `G` topic groups.

The diagnostic bank `secondary_2/s2/v2` (4 questions) is outside the requested path and was
not audited.

## Checks performed

- **Answers.** I recomputed every canonical answer from its prompt before reading the
  solution. The script enumerates sample spaces with `itertools`, uses exact `Fraction`
  arithmetic and brute-forces the "solve for x" items. All 104 answers match (0 mismatches).
- **Lesson examples.** I recomputed every worked example and active-recall answer in both
  lessons. All are correct.
- **Solutions and hints.** I checked worked solutions, both hint stages, accepted answers and
  stated conditions, such as "at random", "fair", "without replacement" and "simplest form".
- **Answer checking.** I called the production checker
  (`question_bank/src/question_bank/checking.py`, also imported by
  `services/learning_api/.../postgres_practice.py`) with typical learner inputs.
- **Alignment.** I compared outcome and difficulty alignment against the S2 catalogue
  (2.1 "probability as a measure of chance"; 2.2 "probability of single events, including
  listing all possible outcomes…"), the difficulty rubric in `difficulty.py` and the lesson
  content.
- **Duplicates.** I looked for semantic and template duplicates within the bank and against
  the lesson worked examples.
- **Wording.** I checked wording against house rules v2 and the audience statement in
  `LESSON_NOTES_CONTENT_STANDARD.md`.
- **Validators (baseline).** `question-bank validate` on the bank and `course-validate` on
  the Secondary 2 course both pass with 0 issues. `authoring-validate` reports
  `duplicate_count: 0`. Its single error, `learning_blueprint_coverage`, appears only because
  one bank was passed on its own.

## Part 1 — Content findings

Severity: **High** means a learner is marked wrong when correct, or is asked to use a method
that was not taught or is outside the outcome. **Medium** means a reviewer should fix this
before approval. **Low** covers polish and consistency.

### Answer checking and response configuration

**C-01 — Medium — `s2-l1-507`, `s2-l1-513`, `s2-l2-504`**

- **Evidence:** These items ask for a probability "as a percentage" and set canonical answers
  of `20`, `35` and `65`. The checker reads a trailing `%` as division by 100, so
  `check_answer(canonical "20", "20%")` returns `correct: False` without a format error. The
  prompt does say "Enter the numerical value only", but a learner who types the natural
  answer `20%` is silently marked wrong.
- **Proposed correction:** Reword the prompts to "Enter the number without the % sign".
  Alternatively, add percentage-aware comparison to the checker, such as a `unit: "%"` that
  strips the sign before comparing. Re-test with `20`, `20%` and `0.2`.

**C-02 — Medium — format-conversion items `s2-l1-508`, `s2-l1-509`, `s2-l1-519`, `s2-l2-512`, `s2-l2-517`; and the 64 items that ask for "simplest form"**

- **Evidence:** `exact_numeric` compares values only. In the checker tests:
  - `s2-l1-509` ("express 65% as a decimal") accepts the unconverted input `65%`.
  - `s2-l1-508` and `s2-l1-519` ("as a decimal") accept `3/4` and `1/4`.
  - Every "simplest form" item accepts unsimplified answers, for example `2/4` for `1/2`.

  As a result, the conversion skill that outcome 2.1 lists, and that `s2-lesson-01` teaches,
  is never actually assessed.
- **Proposed correction:** This needs a product decision. Either add form-aware comparison
  modes (decimal-only, simplest-fraction-only) or remove the form demand from the prompts so
  they do not promise a check that is not made. Until then, reviewers should know that
  "simplest form" is advisory.

**C-03 — Low — `s2-l2-502`, `s2-l3-526`**

- **Evidence:** The prompts give decimals (0.08; 0.46 and 0.31) and do not name an answer
  form. The canonical answers are `23/25` and `23/100`, and the solutions convert the
  decimals to fractions without a reason (`1-23/50-31/100`). The checker accepts `0.92` and
  `0.23`, but the displayed model answer is in a different form from the data.
- **Proposed correction:** Set the canonical answers to `0.92` and `0.23`, and write the
  solutions in decimals.

### Outcome alignment and taught methods

**C-04 — High — `s2-l4-507`**

- **Evidence:** "Three draws with replacement… exactly two red". The solution is
  `3(2/5)^2(3/5) = 36/125`, which is a binomial-style multiplication of probabilities across
  three stages. The ordered sample space has 125 outcomes, so listing is not practical.
  Neither lesson teaches multiplying probabilities. `s2-lesson-02` explicitly says it
  "focuses on one stated event". Outcome 2.2 is single events.
- **Proposed correction:** Replace this with a single-event item at difficulty 4.
  Alternatively, rebase it on a small listable sample space with equally likely outcomes,
  such as one draw from a bag combined with a coin.

**C-05 — High — `s2-l4-515`**

- **Evidence:** The solution uses `\binom{3}{1}\binom{2}{2}/\binom{5}{3}`, and the hint says
  "all C(5,3) selections". Combinations notation is not taught in either lesson and is not
  part of the Secondary 2 syllabus outcomes. The answer, 3/10, is correct.
- **Proposed correction:** Rewrite the hint and solution to list the 10 unordered
  selections explicitly, or the 60 ordered ones. Alternatively, replace the item.

**C-06 — Medium — `s2-l3-514`, `s2-l3-520`, `s2-l4-504`, `s2-l5-503`, `s2-l5-501`, `s2-l5-505`**

- **Evidence:** The hints and solutions rely on methods the lessons never teach:
  - `s2-l3-514` H2: "3/5 times 2/4 plus 2/5 times 3/4".
  - `s2-l3-520` H2: "Subtract (5/6)^2".
  - `s2-l4-504`: `(3/6)^2`.
  - `s2-l5-503`: `×1/2`.
  - `s2-l5-501` and `s2-l5-505`: `3!/4^3` and `3!/3^3`.

  The answers are correct and each one can be reached by listing. However, the given method
  is the multiplication rule or factorial notation.

  This is a judgment call for reviewers. In the Singapore reference syllabus, "simple
  combined events" and the multiplication of probabilities sit in Secondary 3/4. The repo
  catalogue only covers Secondary 1–2, so this cannot be confirmed in-repo.
- **Proposed correction:** Rewrite the hints and solutions as listing or possibility-table
  methods, such as "count the 25 ordered pairs with no 6". Alternatively, decide explicitly
  that 2.2 at this level includes the multiplication rule and add it to `s2-lesson-02`.
  Note that `s2-l3-514` is in the `s2-lesson-02` practice pool.

**C-07 — Low — `s2-l1-518`**

- **Evidence:** "Seven of ten equally likely positions… write the probability" is a direct
  favourable/total count, which is the 2.2 skill. It is allocated to 2.1, and its title,
  "Recorded successes", describes an experimental context that the prompt does not contain.
- **Proposed correction:** Reallocate the item to 2.2, or rewrite it as a 2.1 task (scale
  placement, form, or complement). Retitle it to match.

### Semantic duplicates and template repetition

**C-08 — Medium — `s2-l3-505`**

- **Evidence:** "Two fair coins… exactly one head… 1/2" is the same task as the
  `s2-lesson-02` worked example "A fair coin is tossed twice. Find the probability of getting
  exactly one head", including the same answer and method. The item is in the
  `s2-lesson-02-practice` pool at the challenge stage and is labelled difficulty 3.
- **Proposed correction:** Replace it with a different two-stage listing task, such as a
  coin and a three-section spinner with a compound condition.

**C-09 — Low — `s2-l2-522`**

- **Evidence:** "A fair die… below 4 or even → 5/6" has the same structure, sample space and
  answer as the `s2-lesson-02` worked example "factor of 6 or greater than 4 → 5/6".
- **Proposed correction:** Change the conditions so that the union size and answer differ.

**C-10 — Low — `s2-l1-503` and `s2-l1-516`**

- **Evidence:** "One fair coin, P(heads)" and "one fair coin, P(tails)" are both 1/2 and
  both difficulty 1.
- **Proposed correction:** Replace one of them, for example with a fair die and a single
  face.

**C-11 — Low — `s2-l2-521` and `s2-l2-523`**

- **Evidence:** Both items pick from 1–12, take the union of two conditions, have 8
  favourable outcomes and give the answer 2/3. `s2-l2-520` follows the same pattern on 1–10.
- **Proposed correction:** Vary the range or the conditions so that the counts and answers
  differ.

**C-12 — Medium — template families (house rules v2: "avoid repeating context, operation pattern and numerical structure")**

- **Evidence:**
  - Complement then n·p: `s2-l3-501`–`504` and `s2-l4-505` (5 items).
  - Reverse n·p (find n): `s2-l3-509`–`512` (4).
  - Relative frequency then predict: `s2-l3-516`–`519` and the lesson-01 worked example (5).
  - n·p: `s2-l2-519` and `s2-l2-524`–`527` (5).
  - Relative frequency: `s2-l2-510`–`512` and `s2-l2-517`–`518` (5).
  - (a±x)/(b±x) = target: `s2-l4-501`, `s2-l4-502`, `s2-l5-504` (3).
  - Seed germination context: `s2-l1-509`, `s2-l2-511`, `s2-l2-524`, `s2-l3-503`,
    `s2-l3-512` (5).
  - Bus or ferry "within five minutes" context: `s2-l1-508`, `s2-l2-518`, lesson-01 worked
    example.

  The near-prompt detector passes all of these.
- **Proposed correction:** Keep at most two items per family. Replace the rest with 2.1
  tasks that are under-represented, such as placing events on the scale, comparing two
  probabilities, judging whether evidence suggests bias, and spotting invalid probabilities.

### Difficulty calibration (rubric in `question_bank/src/question_bank/difficulty.py`)

**C-13 — Medium — `s2-l4-505`**

- **Evidence:** "P(rain) 0.18; expected dry afternoons in 250" has the same operation
  pattern as the difficulty-3 items `s2-l3-501`–`504`. It involves no method selection or
  constraint.
- **Proposed correction:** Re-level it to 3 and replace the difficulty-4 slot.

**C-14 — Medium — `s2-l4-508`, `s2-l4-509`, `s2-l4-514`, `s2-l4-513`**

- **Evidence:**
  - `s2-l4-508` counts labelled sectors (2+3+2+4)/12, a routine level-2 task.
  - `s2-l4-509` and `s2-l4-514` adjust a count and then simplify, which is two linked
    steps (level 2–3).
  - `s2-l4-513` sets up one equation (level 3).

  None of them needs the "unfamiliar problem requiring method selection, constraints, or
  justification" that defines level 4.
- **Proposed correction:** Re-level them to 2–3, or add a genuine constraint or a
  justification part.

**C-15 — Medium — `s2-l5-502`, `s2-l5-504`**

- **Evidence:** Each item is one linear equation: `28+120p=82` and
  `(72+x)/(120+x)=5/8`. `s2-l5-504` has the same structure as the difficulty-4 item
  `s2-l4-501`. Level 5 calls for "complex non-routine synthesis".
- **Proposed correction:** Re-level them to 3–4, and author level-5 items that combine
  several ideas, for example designing a spinner to meet two probability conditions with a
  justification.

**C-16 — Low — `s2-l3-505`**

- **Evidence:** This is the lesson worked example (see C-08), labelled difficulty 3.
- **Proposed correction:** Covered by C-08.

### Hints

**C-17 — Medium — `s2-l1-504`, `s2-l1-506`, `s2-l1-510`, `s2-l1-514`, `s2-l1-516`, `s2-l1-518`, `s2-l1-520`, `s2-l1-521`, `s2-l2-518`**

- **Evidence:** Stage-2 hints state the final answer. For example, "Use 3 favourable outcomes
  out of 8" for answer 3/8, "Use 1 as the numerator and 5 as the denominator" for 1/5, and
  "Write 33/50 and check whether it simplifies" for 33/50. House rules v2: "neither hint may
  state the final answer." The batches were authored under house rules v1, before that rule
  was added.
- **Proposed correction:** Make stage 2 an intermediate setup without both numbers, for
  example "Count the red counters, then count all the counters."

**C-18 — Low — `s2-l1-501`, `s2-l1-502`, `s2-l1-503`, `s2-l1-515`, `s2-l2-513`**

- **Evidence:** Read together, H1 and H2 state the answer. For example, `s2-l1-501` H1 says
  "An impossible outcome has probability 0" and H2 says "Red does not occur". `s2-l2-513` H2
  says "The vowel positions contain O and A", which gives 2/7.
- **Proposed correction:** Make H1 conceptual without the value, for example "Where does an
  impossible event sit on the scale?"

**C-19 — Medium — `s2-l3-524`**

- **Evidence:** The prompt asks "How many **more** heads were observed than expected?", but
  H2 says "Subtract the observed frequency from the expected frequency". That gives
  120 − 132 = −12. The hint was shared with `s2-l3-525` ("fewer"), where it is correct. The
  solution hides the problem with `|132−120|`.
- **Proposed correction:** Change H2 to "Subtract the expected frequency from the observed
  frequency." Change the solution to `132 − 120 = 12`, without the absolute value.

**C-20 — Low — `s2-l2-513`**

- **Evidence:** H1 says "Treat repeated positions, rather than distinct letter types, as
  outcomes", but SCHOLAR has no repeated letters, so the hint is misleading.
- **Proposed correction:** Use a word with a repeated vowel, such as "PROBABILITY", or
  change H1 to "Each of the 7 letter positions is one outcome."

**C-21 — Medium — `s2-l2-501`, `s2-l2-503`, `s2-l2-509`, `s2-l2-519`, `s2-l2-525`, `s2-l2-526`**

- **Evidence:** The stage-2 hints are `text` blocks that contain raw LaTeX, such as
  `1-\frac{3}{20}` and `Calculate 64\times\frac{3}{8}.`. They are not `inline_math` or
  `display_math`, so learners see the backslash commands literally.
- **Proposed correction:** Move the math into `inline_math` blocks, or write it as plain
  text, for example "1 − 3/20".

### Worked solutions

**C-22 — Medium — `s2-l3-520`, `s2-l3-528`, `s2-l3-529`, `s2-l3-530`**

- **Evidence:** These are 3-mark items whose only solution step is `P=\frac{a}{b}=\frac{a}{b}`.
  No listing or complement working supports the M2. For example, `s2-l3-520` never shows the
  25 "no 6" outcomes.
- **Proposed correction:** Add the favourable list or the complement count as the M-step,
  for example "No 6: 5×5 = 25 of 36; 36 − 25 = 11".

**C-23 — Low — 17 items, including `s2-l1-504` and `s2-l2-506`**

- **Evidence:** The solution template prints an identical equality, `P=\frac{3}{8}=\frac{3}{8}`.
  The full list is `s2-l1-504`, `506`, `510`, `516`, `520`, `521`; `s2-l2-506`, `508`, `513`,
  `518`, `522`, `528`, `530`; and `s2-l3-520`, `528`, `529`, `530`.
- **Proposed correction:** Drop the repeated right-hand side, or show the unsimplified
  count.

### Wording and stated conditions

**C-24 — Low — 16 items: `s2-l1-512`, `s2-l2-507`, `s2-l2-514`, `s2-l2-515`, `s2-l2-516`, `s2-l2-523`, `s2-l3-514`, `s2-l3-515`, `s2-l3-531`, `s2-l4-501`, `s2-l4-502`, `s2-l4-503`, `s2-l4-507`, `s2-l4-511`, `s2-l4-515`, `s2-l5-503`**

- **Evidence:** The selection is "chosen", "selected" or "drawn" with no "at random".
  Equally likely outcomes are therefore assumed but not stated, which `s2-lesson-02`
  specifically warns about.
- **Proposed correction:** Add "at random".

**C-25 — Low — `s2-l1-513`**

- **Evidence:** "A point marked on a probability scale has value 0.35" and the title
  "Probability scale reading" suggest a scale diagram, but none exists. The task is only a
  decimal-to-percentage conversion, which duplicates `s2-l1-507`.
- **Proposed correction:** Either add a scale diagram and ask the learner to read or place
  the point (see the diagram suggestions below), or rewrite and retitle the item.

**C-26 — Low — titles on `s2-l2-516` and `s2-l2-528`**

- **Evidence:** The title "Non-primary colour" is used for an item that asks for P(white).
  The title "Two-colour sample space" is used for an item with three colours (R, B, G).
- **Proposed correction:** Retitle both.

**C-27 — Low — `s2-l1-516`, `s2-l1-520`**

- **Evidence:** "Use 1 favourable outcomes out of…" is ungrammatical.
- **Proposed correction:** Change to "outcome", or rewrite as part of C-17.

**C-28 — Low — `s2-l3-519`**

- **Evidence:** "pupil-days" is unexplained jargon, and "pupil" is UK/Singapore usage. The
  audience standard asks for "clear international English" and says unfamiliar terminology
  must be explained.
- **Proposed correction:** "Over 150 student school days, 9 absences are recorded…"

**C-29 — Low — `s2-l1-508`**

- **Evidence:** "on time on 3 out of every 4 comparable journeys" uses the vague word
  "comparable" and blends experimental and theoretical framing in a 2.1 item.
- **Proposed correction:** "A bus is on time with probability 3/4. Write this probability as
  a decimal."

### Lessons

**L-01 — Medium — `s2-lesson-02`**

- **Evidence:** The lesson scopes itself to "one stated event". It mentions without
  replacement and trees but gives no example. Its practice and checkpoint pools nevertheless
  contain items whose method is the multiplication rule or combinations (C-04 to C-06).
- **Proposed correction:** Either add a worked example on listing ordered outcomes without
  replacement, with no multiplication rule, and align the items to it, or remove
  out-of-scope methods from the items.

**L-02 — Low — `s2-lesson-02`, section `s2-22-sample-space`**

- **Evidence:** The text "there is one ordered outcome producing 2 and six producing 7"
  gives the count needed for `s2-l3-506` (sum of 7 → 6/36).
- **Proposed correction:** Use a different illustrative total, such as 4 with 3 outcomes,
  or keep the text and replace `s2-l3-506`.

**L-03 — Low — `s2-lesson-01`, section `s2-21-scale`**

- **Evidence:** The text says "unlikely and likely describe regions rather than exact
  values", but the lesson diagram pins them to the 1/4 and 3/4 ticks (D-03).
- **Proposed correction:** Fix in the diagram.

**L-04 — Low — `s2-lesson-01`**

- **Evidence:** The `s2-lesson-01-practice` pool includes the reverse-expectation items
  `s2-l3-509` and `s2-l3-510` (find the number of trials). The lesson only teaches the
  forward n·p calculation.
- **Proposed correction:** Add one sentence or a recall check on rearranging
  "expected frequency = n × p", or swap those items for forward tasks.

**L-05 — Low — both lessons**

- **Evidence:** `provenance.review_notes` still reads "…awaiting… the complete S2 question
  bank before course integration", but the unit is already integrated with all four
  batches and the pools.
- **Proposed correction:** Update the note at the next revision.

All lesson mathematics is correct. I recomputed 3/8 = 0.375 = 37.5%; 0.68 and 0.32; 18/80 =
0.225 and ×200 = 45; P(exactly one head) = 2/4; {1,2,3,6} ∪ {5,6} → 5/6; and the active
recall answers 0.63 and 6. Both lessons meet the baseline lesson-note gate: seven sections,
three explanations, two worked examples with verification notes, active recall and a summary.

### Standards conflict to resolve (reported, not resolved)

House rules v2 (`backend_resources/question_bank/authoring/house-rules-v2.json`) set:

- `locale: en-SG`;
- "Singapore/British English";
- `currency: SGD`; and
- "Use S$…".

The N2 audit applied these rules. `LESSON_NOTES_CONTENT_STANDARD.md` instead says that
learners are across Indonesia and Southeast Asia, that the Singapore syllabus is a
calibration reference only, and that content should use "clear international English" and
contexts that work across the region.

In S2, the only visible instance of the conflict is "pupil-days" (C-28). There are no
currency items, so the S$ rule is not triggered. British spellings ("colour", "favourable")
appear throughout, and neither standard says whether these count as acceptable
international English.

The bank `blueprint.json` still names the course "Singapore G3 Mathematics", and every item
cites Singapore school papers as style references. Reviewers should decide which rule
governs before approving wording.

## Part 2 — Diagrams

Both assets are at `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/`. I resolved
each path from the lesson JSON (`assets[].path`), and both SHA-256 values match. Each was
rendered at 940 px (native) and at 390 px (phone width, scale 0.415) and viewed. I also
measured text bounding boxes with `getBBox()` in Chromium.

### `s2-lesson-01-probability-scale.svg` (lesson `s2-lesson-01`, section `s2-21-scale`)

The ticks are placed correctly: 0, 1/4, 1/2, 3/4 and 1 sit at x = 100, 285, 470, 655 and 840
on a 740-unit scale, which is exact. The alt text matches the drawing. The diagram reveals
no answer to any question.

**D-01 — neatness — Medium**

- **What is wrong:** The dashed "increasing likelihood" arc runs through its own label. The
  path is `M155 145 C285 92 655 92 785 145`, which peaks at y ≈ 105 at x = 470, while the
  text box spans y 99–123 and x 373–566. The render shows the dashes striking through the
  tops of the letters, at both 940 px and 390 px.
- **Specific fix:** Replace the arc with a straight arrow (see D-02), or lower the curve to
  `M155 150 C285 128 655 128 785 150` (peak y ≈ 134) and keep the text at y = 118.

**D-02 — accuracy — Medium**

- **What is wrong:** The arc has no arrowhead and is symmetric, rising and then falling.
  It does not show which direction likelihood increases, and its shape can read as "more
  likely in the middle".
- **Specific fix:** Use a straight horizontal arrow at y ≈ 150 from x = 155 to x = 785, with
  a `marker-end` arrowhead at the "1" end. Put the label above it.

**D-03 — accuracy — Low**

- **What is wrong:** "unlikely" and "likely" sit directly under the 1/4 and 3/4 ticks, in the
  same style as "impossible" and "certain", so they read as exact values. The lesson text
  says they are regions.
- **Specific fix:** Draw bracketed regions, with "unlikely" spanning 0 to 1/2 and "likely"
  spanning 1/2 to 1, or centre the words between ticks in a lighter style. Update the alt
  text to match.

**D-04 — neatness — Low**

- **What is wrong:** `stroke-linecap="round"` on the 8-px scale line makes it extend about
  4 px beyond the 0 and 1 ticks. These show as small dark stubs outside the end ticks.
- **Specific fix:** Use `stroke-linecap="butt"`.

**D-05 — neatness — Low**

- **What is wrong:** The labels under 1/2 sit lower than the others: baselines y = 68 and
  102 against 62 and 96. "even chance" is therefore out of line with "unlikely" and
  "likely".
- **Specific fix:** Use the same baselines (62 and 96) for every tick, and keep the bold
  weight for emphasis.

**D-06 — neatness — Medium**

- **What is wrong:** At 390 px wide, the 18–20 px labels render at about 7.5–8.3 px.
  "unlikely" and "likely" are the hardest to read.
- **Specific fix:** Raise label sizes to at least 28 px (about 11.6 px on a phone), or
  narrow the viewBox to about 640 and move the long title into the lesson text.

**D-07 — accuracy (metadata) — Low**

- **What is wrong:** The SVG `<desc>` omits the "unlikely" and "likely" labels and the
  footer note, while the lesson `alt_text` includes them.
- **Specific fix:** Bring `<desc>` in line with `alt_text` after D-03.

### `s2-lesson-02-sample-space.svg` (lesson `s2-lesson-02`, section `s2-22-systematic-listing`)

The table content is correct: RH, BH, GH, RT, BT and GT, with 3 × 2 = 6 outcomes. The
footer's 2/6 = 1/3 matches the lesson text. The diagram reveals no answer to any question.

**D-08 — neatness — Medium**

- **What is wrong:** The highlight `<rect x=160 y=70 w=160 h=190 fill=#fff0dc>` is drawn after
  the grid `<path>`. It therefore hides the H/T divider (y = 165) in the red column and half
  of that column's side borders. In the render, RH and RT appear to share one merged cell.
  That undermines the figure's message, "List every outcome exactly once".
- **Specific fix:** Move the highlight `<rect>` before the grid `<path>`, or draw two cell
  rectangles (160,70,160,95 and 160,165,160,95).

**D-09 — accuracy — Low**

- **What is wrong:** The legend marker is a solid orange circle (`#d07a16`), but the
  highlighted cells are pale peach (`#fff0dc`), so the key does not match what it labels.
- **Specific fix:** Make the legend swatch a square filled `#fff0dc` with a `#d07a16`
  stroke, or give the highlight a `#d07a16` outline.

**D-10 — accuracy — Low**

- **What is wrong:** The subtitle says "Choose one colour, then toss a fair coin." There is
  no "at random", yet the alt text and the lesson both describe six equally likely outcomes.
- **Specific fix:** Change it to "Choose one colour at random, then toss a fair coin."

**D-11 — neatness — Low**

- **What is wrong:** The top-left header "coin" labels only the row headers (H and T). The
  colour columns have no axis label.
- **Specific fix:** Use a split header such as "coin ↓ / colour →", or add a "colour" label
  above the column headers.

**D-12 — neatness — Medium**

- **What is wrong:** At 390 px wide, the 19–22 px text renders at about 7.9–9.1 px.
- **Specific fix:** Raise the table text to at least 28 px and the footer to at least 26 px,
  or reduce the canvas width.

Nothing in either diagram is clipped or outside the viewBox. The titles and footers do not
collide with the figures.

### Text-only questions that would benefit from a diagram

S2 has no `diagram_audit.json`. The following text-only items would clearly benefit from a
figure without the figure revealing the answer:

- `s2-l1-513`: draw a probability scale with a marked point and ask the learner to read it
  (see C-25).
- `s2-l4-508`: draw the 12-sector spinner with repeated labels. Reading the labels from a
  picture is the authentic task.
- `s2-l2-528`: draw the four-sector R, R, B, G spinner. It illustrates "equal sectors, repeated
  labels".

Two-dice and product-table items (`s2-l3-506`, `s2-l3-513`, `s2-l3-530`, `s2-l4-512`,
`s2-l4-516`) should stay text-only. A completed possibility table would give away the
listing the item assesses.

## Root-cause patterns

1. **No generator and no meaningful validation for probability diagrams (2 of 2
   diagrams).**
   - Both assets declare `generation_spec.renderer: "nextscholar-probability-svg-v1"`
     (`diagram_kind` `probability_scale` and `two_stage_sample_space`). No renderer with that
     name exists anywhere in the repo, so the SVGs are hand-authored and cannot be
     regenerated.
   - `scripts/recalibrate_geometry_content.py` only generates geometry shapes.
   - `geometry_validation.geometry_diagram_issues` runs from `course_validation.py` on every
     lesson asset, but its checks only activate when `diagram_kind == "angle_types"` or
     when `angle_markers` or `forbidden_visible_labels` are present. None of these is true
     here, so the only effective check is the SHA-256 match.
   - The D-findings above are therefore not caused by those two files. They are individual
     hand-authoring errors that no tool could catch, especially draw order (D-08) and
     label/curve collision (D-01).
   - **Suggested remedy:** Add a small deterministic probability renderer, or at minimum a
     text-bounding-box collision check and a minimum rendered font size at 390 px for all
     lesson SVGs.
2. **Authoring template defects shared across batches.** These come from the v1 authoring
   prompt (`math-question-authoring-v1`, house rules v1) that all four manifests cite:
   - hints that state numerator and denominator (C-17, 9 items);
   - raw LaTeX in text hints (C-21, 6 items);
   - the identical-equality solution template (C-23, 17 items);
   - "1 favourable outcomes" (C-27);
   - a shared observed-vs-expected hint that is wrong for the "more" variant (C-19); and
   - missing "at random" (C-24, 16 items).

   House rules v2 address hint leakage and template repetition, but these batches predate
   v2 and were not regenerated.
3. **Checker semantics against prompt wording.** `exact_numeric` value comparison means that
   "simplest form" and "as a decimal" are not enforced (64 + 5 items), and percentage tasks
   reject `%` input (3 items) (C-01, C-02). This affects every topic that uses those prompt
   forms, not only S2.
4. **Scope creep at difficulty 3–5 for outcome 2.2.** The multiplication rule, binomial-style
   counting, combinations and factorials (C-04 to C-06) appear in hints and solutions, while
   the lesson deliberately avoids them.

## Could not verify

- **Fonts.** The renders use Chromium's `system-ui` fallback font. The app's actual font,
  container padding, and dark-mode or theme treatment could change text widths and
  contrast. I checked phone readability at exactly 390 px image width, with no outer
  padding.
- **Learner UI.** I did not open the review-packet `index.html` pages or the learner UI. The
  raw-LaTeX finding (C-21) is inferred from the block type (`text`). It is not a
  screenshot.
- **Combined-events scope.** The claim that combined events belong to Secondary 3/4
  (C-06) relies on the external Singapore syllabus. The repo catalogue contains only
  Secondary 1–2 outcomes.
- **Pool difficulty balance.** I did not audit the checkpoint and adaptive pool
  compositions beyond their outcome and difficulty counts (12/12 by outcome; difficulty
  4/6/6/6/2 for the checkpoint).
- **Out-of-scope bank.** The `s2/v2` diagnostic bank (4 items) was not checked.

## Human review outcome

None recorded. All 104 questions and both lessons remain `draft`, and every batch manifest
remains `ready_for_review`. This audit changes no review state.
