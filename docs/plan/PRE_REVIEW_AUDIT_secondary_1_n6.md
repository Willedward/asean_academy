# Secondary 1 N6 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in
`backend_resources/question_bank/g3_math/secondary_1/n6/v1/` (batches B001–B004), all five
N6 lessons, and every diagram these questions and lessons reference

**Decision boundary:** this is a report-only technical pre-review. No question, lesson,
SVG, manifest, claim or review state was changed, and no Mathematics or editorial approval
is recorded. All 104 questions are `draft` revision 1, all four batch manifests show
`mathematics: pending` and `editorial: pending`, and all five lessons are `draft` revision 2.

## Coverage

| Item | Count | Notes |
| --- | ---: | --- |
| Questions checked | 104 | 21 / 31 / 31 / 16 / 5 at difficulty 1–5; all single-part |
| Lessons checked | 5 | `n6-lesson-01` … `n6-lesson-05` |
| Diagrams referenced | 5 | All five belong to lessons. No N6 question references an asset. |
| Diagrams actually viewed | 5 | Each was rendered to PNG at 940 px and at a 358 px phone width (10 images), and each image was inspected |
| `diagram_audit.json` | none | N6 is not a geometry bank, so no per-question diagram decision exists |

The lessons are not stored in an `n6` folder. They live in the Secondary 1 course root
`backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/`. They were found through
`course.json` unit `g3-sec1-n6` (`topic_code: N6`, lessons `n6-lesson-01` … `05`, outcomes
6.1–6.5). The assets are in the same course's `assets/` folder.

`backend_resources/question_bank/g3_math/secondary_1/n6/v2/` contains four diagnostic
questions (`n6-l3-901` … `904`). They are outside the requested `v1` scope and were not
audited.

## Checks performed

- Recomputed every canonical answer from the prompt alone in an independent script
  (sympy and exact fractions) before reading the solution: **104 of 104 agree**.
- Ran every canonical answer, plus common equivalent learner inputs, through the production
  checker `question_bank.checking.check_answer`.
- Read every hint, solution step and stated condition. Checked outcome and difficulty
  against the blueprint rubric. Grouped semantic duplicates within the bank and against
  lesson examples.
- Checked the wording against `house-rules-v1/v2`, the N2 audit model and the audience
  statement in `LESSON_NOTES_CONTENT_STANDARD.md`.
- Recomputed every lesson worked example and active-recall answer. All are correct.
- Mapped every SVG point, line and label from its pixel coordinates to graph coordinates,
  measured text bounding boxes in Chromium, and visually inspected each render.
- Reran `question-bank validate` on the N6 bank, `authoring-validate` across the catalogue
  and `course-validate`. All three pass with 0 errors and 0 warnings. As the brief notes,
  passing validators does not show that the content is correct. Several findings below are
  invisible to them.

Severity scale: **Critical**, a learner is marked wrong for a correct answer, or a key is
wrong. **High**, blocks approval: the item is out of syllabus, untaught, or assesses the
wrong outcome. **Medium**, fix before approval. **Low**, polish or a reviewer's judgement call.

---

## Part 1 — Content findings

### C1. Correct expression answers are marked wrong (Critical, 9 questions)

**Keys:** n6-l2-011, n6-l2-020, n6-l3-004, n6-l3-005, n6-l3-006, n6-l3-007, n6-l3-012,
n6-l3-014, n6-l3-019

**Evidence.** These parts use `comparison_mode: symbolic_equivalence`, but
`question_bank/src/question_bank/checking.py:157-160` only compares the answer string with
`canonical_expression` (for example `4*x+2`) or with the listed `accepted_equivalents`.
Every one of these lists is empty. Results from running the production checker:

| Key | Canonical | Learner input → result |
| --- | --- | --- |
| n6-l2-011 | `4*x+2` | `4x+2` ✗, `4*x + 2` ✗, `2+4*x` ✗, `y=4x+2` ✗ |
| n6-l3-019 | `84-6*x` | `84-6x` ✗, `-6*x+84` ✗ |

The learning API (`services/learning_api/.../postgres_practice.py:621`) and the diagnostic
repository call this same checker. The web input is a plain text box with no normalisation.
A learner who types the natural answer `4x+2` therefore loses the marks.

**Proposed correction.** Fix this in the checker rather than per question: parse both sides
with implicit multiplication allowed, strip a leading `y=`, and compare symbolically or by
evaluating at several random points. Until then, do not approve these nine questions. As
a stopgap, list `4x+2`, `2+4x`, `y=4x+2` and the spaced variants in `accepted_equivalents`.
The defect reaches beyond N6: 194 `symbolic_equivalence` parts in 6 banks all have empty
`accepted_equivalents`.

### C2. Composite functions are out of syllabus and untaught (High)

| Key | Issue | Proposed correction |
| --- | --- | --- |
| n6-l4-006 | Asks for x with f(g(x)) = 19. Composite functions are not in N6 outcomes 6.1–6.5 (`catalogue.json`) and no N6 lesson teaches them. | Replace with a 6.3 task at difficulty 4, such as finding a and b from two conditions in a context and then interpreting them. |
| n6-l5-003 | Builds f from two values, then solves f(g(x)) = 60. Same scope problem. | Keep the "find the rule from two values" stage and replace the composition with a contextual constraint, such as the input at which two linear models first differ by a given amount. |

### C3. Function notation is used but never taught (Medium)

**Keys:** n6-l3-013, n6-l3-028, n6-l4-002 (and C2's n6-l4-006, n6-l5-003)

**Evidence.** The prompts use f(x) and g(x). The outcomes and lessons use y = ax + b. The
only appearance of f(x) in the lessons is one unexplained display line in n6-lesson-04,
section 3 (`y=f(x), y=g(x) ⇒ f(x)=g(x)`).

**Proposed correction.** Either rewrite these prompts in y = ax + b form (for example "y = kx
+ 2 gives y = 14 when x = 3"), or add a short explanation of f(x) notation to
n6-lesson-03. Reviewers should decide which.

### C4. Some questions assess a different outcome from the one allocated (Medium)

| Key | Allocated | What it actually assesses | Proposed correction |
| --- | --- | --- | --- |
| n6-l1-003 | 6.2 | Reading the second number of an ordered pair, which is 6.1 and the same task as n6-l1-002 | Use a 6.2 task: read y for a given x from a short table or plotted relationship. |
| n6-l1-008 | 6.2 | Reading the first coordinate, which is 6.1 and the same task as n6-l1-001 | As above, with an input-output interpretation. |
| n6-l4-010 | 6.2 | Solving two simultaneous linear equations (3x + 2y = 31, x = y + 2). This is an equation skill with no graph or relationship interpretation. | Ask which listed ordered pair satisfies both relationships, or interpret the shared point on a graph. |
| n6-l2-005 | 6.4 | Finding c from one point, the same operation as n6-l2-027 (6.3) | Reframe as a graph task: decide whether a plotted point lies on the line, or read c from a drawn graph. |

**Coverage gap (Medium).** None of the 104 questions shows a graph, so outcomes 6.2 ("graph
of ordered pairs"), 6.4 ("graphs of linear functions") and 6.5 ("gradient of a linear
graph") are never assessed through reading a graph. Every gradient item gives the
coordinates in the text. Add graph-reading items, as suggested under "Diagram opportunities"
below.

### C5. Difficulty is set too high (Medium)

The rubric defines level 4 as an unfamiliar problem requiring method selection, constraints
or justification, and level 5 as complex non-routine synthesis.

| Key | Labelled | Why it is lower | Proposed |
| --- | --- | --- | --- |
| n6-l5-001 | 5 | Width × height = 72 is one linear equation, and hint 2 states the equation in full. | 3, or add a real constraint |
| n6-l5-002 | 5 | Two routine steps: find the rule from two points, then equate it with another rule. | 4 |
| n6-l4-013 | 4 | The midpoint of two x-values; 2 marks; the same task as n6-l2-017 (difficulty 2). | 2, or replace |
| n6-l4-005 | 4 | Area of a right triangle with axis-aligned legs; hint 1 points out the right angle. | 3 |
| n6-l4-016 | 4 | Substitute x = 3 into both lines and solve one equation. | 3 |
| n6-l3-001 | 3 | One sum, −5 + 8 − 2. | 2 |
| n6-l3-010 | 3 | 72 ÷ 9. | 1 or 2 |
| n6-l2-001 | 2 | One sign change, given directly in hint 1. | 1 |

Lowering these labels will change the blueprint's difficulty counts, so each needs a
replacement item at the original level.

### C6. Worked solutions skip the key step (Medium)

In the "line through two points" questions, the M1 step uses a gradient that the solution
never calculates. The solution shown to learners therefore skips the method being assessed.

| Key | Missing step | Proposed correction |
| --- | --- | --- |
| n6-l3-004 | a = (3 − 9)/(1 − (−2)) = −2 | Insert this as the M1 step before `y=-2x+b`. |
| n6-l3-005 | a = (15 − 6)/(4 − 1) = 3 | Same |
| n6-l3-006 | a = (0 − 12)/(3 − (−1)) = −3 | Same |
| n6-l3-014 | a = (−5 − 7)/(4 − (−2)) = −2 | Same |
| n6-l4-002 | a = (−3 − 11)/(5 − (−2)) = −2 | Same |
| n6-l4-003 | gradient = (5 − (−7))/6 = 2 before `y=2x-7` | Same |
| n6-l4-004 | m_AB = (−3 − 9)/(2 − (−4)) = −2 | Same |
| n6-l3-030 | m_A = (20 − 2)/(7 − 1) = 3 | Same |
| n6-l4-012 | m_RS = 4/4 = 1, so the required gradient is 2 | Same |
| n6-l4-011 | x + 2 = −x + 8 ⇒ (3, 5) | Show the intersection before "height = 3". |
| n6-l5-002 | a = (36 − 18)/(10 − 4) = 3 | Same |
| n6-l5-003 | f(x) = 3x + 3 from (2, 9) and (7, 24) | Same |
| n6-l5-005 | ½ × 2 × b = 9 ⇒ b = 9 | Show the area equation that S1 assumes. |
| n6-l2-024 | S1 (M1) states "Quadrant IV", which is the answer itself. | Make M1 the image J′ = (3, −3). |

### C7. Hints give away the answer (Medium for the first five, Low for the rest)

| Key | Hint | Problem | Proposed correction |
| --- | --- | --- | --- |
| n6-l1-007 | H2: "…place a point in Quadrant II." | States the answer. | "Use the sign table: which quadrant has x < 0 and y > 0?" |
| n6-l3-009 | H2: "S … shares P's x-coordinate." | P's x-coordinate is given, so the hint is the answer. | "Which given vertex is S vertically aligned with?" |
| n6-l3-025 | H2: "After both reflections the point is (3, 7)…" | Gives the final image, leaving only 3 + 7. | Give only the first image, (3, −7). |
| n6-l2-024 | H2: "The image is (3, −3)…" | Gives away the translation, which is the skill assessed. | "Add 5 to x and subtract 9 from y, then check the signs." |
| n6-l5-001 | H2 states the full equation (k + 3)(8) = 72. | At difficulty 5, the hint removes all the reasoning. | Keep H2 to "height = 8; write the width in terms of k". |
| Pattern (Low): n6-l1-001, -002, -003, -004, -006, -008, -017, -018, -020; n6-l2-021, -022, -029, -031 | H2 is the complete final calculation ("Calculate 3(2) + 1", "Read the first number in (−4, 3)"). | At difficulty 1–2 this is the answer. House rules v2 allow an "intermediate setup", so reviewers should decide whether this is acceptable. | Make H2 a partial setup. |

### C8. Semantic duplicates (Medium)

These were authored under house rules v1 and prompt v1. The v2 rule against repeating a
context, operation and number structure did not yet exist.

| Cluster | Keys | Note |
| --- | --- | --- |
| Identical points (−2, 7), (4, −5) | n6-l2-007 (gradient), n6-l3-014 (equation), n6-lesson-05 worked example 1 (gradient) | The lesson works through n6-l2-007 in full before practice starts. Change the numbers in at least two of the three. |
| Same constant-from-one-point task | n6-l2-005 (y = 2x + c through (3, 7)), n6-l2-027 (y = 2x + b through (3, 13)) | Same coefficient, same x-value, same operation. Replace one, preferably n6-l2-005 (see C4). |
| Equal outputs / intersection | n6-l3-013, n6-l3-018, n6-l3-021, n6-l3-015, n6-l4-015, plus the n6-lesson-04 example | Six "set two linear expressions equal" items at difficulty 3–4 |
| Equation from two points | n6-l3-004, -005, -006, -007, -014, plus the n6-lesson-03 example | n6-l3-005 uses exactly the lesson 3 worked-example pairs (1, 6), (4, 15). |
| Substitute x into a linear rule | n6-l1-004, -010, -018, -019, -020; n6-l2-003, -010, -013, -018, -019, -021, -026, -029 | Thirteen near-identical evaluation items across 6.2, 6.3 and 6.4 |
| Solve for x given y | n6-l2-012 (6.3), n6-l2-025 (6.2) | Same structure |
| Draining or filling tank | n6-l3-019, n6-l3-022, n6-l3-027, n6-lesson-02 example 2, n6-lesson-03 example 2 | Five tank contexts. Vary them (phone battery, savings, travel). |
| Midpoint of two x-values | n6-l2-017, n6-l4-013 | n6-l4-013 is labelled difficulty 4 (see C5). |
| Practice item = lesson example | n6-l3-026 = n6-lesson-01 example 1 (same rectangle); n6-l2-011 = n6-lesson-02 example 1 and its diagram; n6-l3-029 uses the line from the n6-lesson-04 example and diagram; n6-l3-031 uses the 15 / 5 numbers from the n6-lesson-05 recall | Learners see the solved practice item in the lesson. Change the practice numbers. |

### C9. Wording and presentation (Low)

| Key | Issue | Proposed correction |
| --- | --- | --- |
| n6-l1-016 | H1 says "Compare … with y = mx + c". The outcome and lessons use y = ax + b, so this is the only place y = mx + c appears. | "Compare with y = ax + b; the gradient is a." |
| n6-l1-007, n6-l2-024 | "Give the quadrant number", but the lessons use Roman numerals (I–IV). A learner who types `II` gets a format error. | "Enter 2 for Quadrant II" or similar, or accept Roman numerals. |
| n6-l2-031 | "Enter 1 for line A or 2 for line B" is an awkward numeric code for a choice. | Acceptable, but reviewers may prefer a choice response when one is supported. |
| n6-l3-022 | Asks the learner to "interpret it as the emptying time", but only the number 15 is checked and no unit is requested. | "Find how many minutes the tank takes to empty." |
| n6-l2-013 | "passes through (0, −3) and follows y = 4x − 3" repeats itself. | Drop the point. |
| n6-l5-005 | Q(4, k) is never used (k = 27 is not asked for). | Remove Q, or ask for k. |
| n6-l4-008 | Uses x both as the coordinate axis and as point B's unknown, B(x, 10). | Rename it B(p, 10). |
| n6-l5-002 | "the distance x" has no unit, and the costs have no currency or unit. | State km and the currency (see C10). |
| Titles: n6-l2-019 "Temperature conversion table" (no table), n6-l2-022 "Parallel vertical change" (nothing parallel), n6-l3-031 "Gradient after scaling axes" (no scaling), n6-l4-013 "Equidistant point on an axis" (P lies on y = 2, not an axis) | The titles do not match the tasks. | Retitle them. |

### C10. Singapore-specific rules conflict with the audience standard (reviewers to decide)

The N2 audit and house rules v1/v2 set `locale: en-SG`, Singapore/British English and **S$**
for money. `LESSON_NOTES_CONTENT_STANDARD.md` says the audience is students across
**Indonesia and Southeast Asia**, that Singapore's syllabus "does not define the learner's
country", and that contexts should use clear international English that works across the
region. These rules disagree on money:

| Location | Current text | Under the N2 / house-rules reading | Under the audience-standard reading |
| --- | --- | --- | --- |
| n6-l2-018 | "taxi fare y dollars" | "S$y" | A currency-neutral unit or a regional currency |
| n6-l3-003 | "y = 12 + 3x dollars … the bill is $33" | "S$33" | As above. A bare `$` is wrong under both readings. |
| n6-l3-010 | "y dollars for a $72 booking" | "S$72" | As above |
| n6-l5-002 | Costs with no unit | Add S$ | Add a neutral unit |
| n6-lesson-05 §2 | "dollars per item" | "S$ per item" | Neutral |

This audit does not pick a side. The house rules need to be reconciled with the audience
standard before these five items are edited. Otherwise the wording is British-compatible
(litres, kilometres) and contains no Singapore-only idioms.

### C11. Lessons

All worked-example and active-recall answers recompute correctly (n6-lesson-01: P = 28,
A = 48; Q(2, −1), R(2, 1), M(2, 0); recall 4. n6-lesson-02: y = 4x + 2, 34; V = 39 and t = 10;
recall 14. n6-lesson-03: y = 3x + 3, −3; 17; V = 8 and t = 6; recall −1. n6-lesson-04: (0, 8)
and (4, 0); (2, 5); recall 4. n6-lesson-05: −2; k = 5; recall 3). All five pass the baseline
lesson gate in `course-validate`. Content findings:

| Lesson | Severity | Finding | Proposed correction |
| --- | --- | --- | --- |
| n6-lesson-03 / 04 | Medium | f(x) notation appears without explanation (see C3), and composite functions are never taught (see C2). | Add a short notation paragraph, or remove f(x) from the questions. |
| n6-lesson-01 … 05 | Medium | Four worked examples reuse practice-question data (see C8). | Change the example numbers or the question numbers. |
| n6-lesson-01 | Low | Section 1 tells learners to "identify the value represented by one grid interval", but the diagram has no scale numbers to practise on (see D3). | Add tick labels to the diagram. |
| n6-lesson-03 | Low | The context example (V = −2.5t + 18) says "the physical domain ends when the container becomes empty" but never states t ≤ 7.2. | State 0 ≤ t ≤ 7.2. |

---

## Part 2 — Diagram findings

All five diagrams are lesson assets in
`backend_resources/courses/g3_math/secondary_1/n1/v1/assets/`, use renderer
`nextscholar-coordinate-svg-v1` with `diagram_kind: coordinate_graph`, and have a 940 × 500
viewBox. Every checksum matches its lesson JSON.

**Accuracy summary.** Every plotted point, intercept and line is mathematically correct
when mapped from pixels to the implied scale, and every alt text and title matches what is
drawn:

| Asset | Implied scale (px per unit, x / y) | Checked |
| --- | --- | --- |
| n6-lesson-01-coordinate-plane.svg | 50 / 50, origin (470, 250) | A(−4, 3) → (270, 100) ✓; A′(4, 3) → (670, 100) ✓ |
| n6-lesson-02-ordered-pairs.svg | 150 / 22, origin (150, 430) | (0, 2), (1, 6), (2, 10), (3, 14) all on y = 4x + 2 ✓; tick labels match ✓ |
| n6-lesson-03-function-parts.svg | unlabelled; both lines pass through (470, 240) | Shared intercept ✓; one rising and one falling ✓ |
| n6-lesson-04-linear-graph.svg | 90 / 40, origin (140, 420) | (0, 8) ✓, (4, 0) ✓, line passes through both ✓ |
| n6-lesson-05-gradient.svg | 100 / 80, origin (140, 420) | (1, 1) ✓, (5, 3) ✓, y-intercept 0.5 ✓, run 4 and rise 2 ✓ |

No lesson diagram reveals an answer to its own active-recall check.

| ID | Lesson / asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D1 | n6-lesson-04 / `n6-lesson-04-linear-graph.svg` | Accuracy | Medium | Two dashed guides run from (0, 8) to (4, 8) and down to (4, 0). They form a corner at (4, 8), a point that is not on the line and is never mentioned. They look like a rise/run triangle drawn on the wrong side of the line and could be read as marking a point (4, 8). | Delete both `class="guide"` lines (`x1=140 y1=100 x2=500 y2=100` and `x1=500 y1=100 x2=500 y2=420`). If the intercepts need emphasis, add tick labels "8" on the y-axis and "4" on the x-axis instead. |
| D2 | n6-lesson-04 | Accuracy | Low | No axis scale is shown, and the implied scales are unequal (90 px per unit horizontally, 40 vertically). The line therefore looks like gradient ≈ −0.9 although its gradient is −2. n6-lesson-03 tells learners that a larger \|a\| looks steeper, which this drawing contradicts. | Use equal scales (for example 40 px per unit on both axes, which puts (4, 0) at x = 300) or add numbered ticks 1–4 and 2–8 so the stretch is visible. |
| D3 | n6-lesson-01 / `n6-lesson-01-coordinate-plane.svg` | Accuracy | Low | Only "0" is labelled. There are no tick numbers, so A(−4, 3) can only be checked by counting grid squares, even though the lesson text stresses reading the axis scale. | Add tick labels −6 … 6 on x and −3 … 3 on y (or every second value). |
| D4 | n6-lesson-01 | Neatness | Low | The note "same distance from the y-axis" (bbox x 350–610, y 120–141) is struck through by the y-axis at x = 470 (confirmed in the render). | Move the text to `x="485" y="130"` (bbox about 485–745 × 113–134). This clears the axis, the guide at y = 100 and the "Quadrant I" label below it. |
| D5 | n6-lesson-01 | Neatness | Low | The grid is ragged. Horizontal grid lines cover only y = −3 … 3 (px 100–400), but vertical lines run from px 70 to 450, and A and A′ sit on the top edge of the grid. | Extend the horizontal grid to px 50 and 450 (y = ±4), or trim the vertical lines to 100–400 and enlarge the plot range. |
| D6 | n6-lesson-03 / `n6-lesson-03-function-parts.svg` | Neatness | Medium | The purple falling line passes through the label "a < 0: falls" (bbox x 650–760, y 383–409; the line crosses at x ≈ 689–716). This is clearly visible in the render. | Move the label to `x="540" y="420"`, which sits below the line and clear of both lines and the axes. |
| D7 | n6-lesson-03 | Neatness | Low | The label "b = 1" (starting at x = 495, top at y = 203) touches the teal line, which is at x ≈ 494 when y = 203. | Move it to `x="505"`. |
| D8 | n6-lesson-03 | Accuracy | Low | There is no scale and neither line has an equation, so "b = 1" cannot be read from the axes and a is only qualitative. The implied lines are y = 1.5x + 1 and y = −(2/3)x + 1 at 60 px per unit. | Add a y-axis tick labelled 1 at px 240, and optionally label the lines y = 1.5x + 1 and y = −⅔x + 1. |
| D9 | n6-lesson-04 | Neatness | Low | The "(0, 8)" label's lower-left corner touches the line (bbox 170–227 × 99–125; the line is at y ≈ 127 when x = 170). The equation label "y = −2x + 8" at (590, 190) is about 350 px from the line, floating in empty space. | Move "(0, 8)" to the left of the y-axis (`x="60" y="108"`). Move the equation label to `x="320" y="230"` (about 25 px above the line). |
| D10 | n6-lesson-05 / `n6-lesson-05-gradient.svg` | Neatness | Low | The "(5, 3)" label's lower-right corner touches the line (bbox 650–695 × 136–157; the line is at y ≈ 158 when x = 695). | Move it to `x="600" y="152"`. |
| D11 | n6-lesson-05 | Accuracy | Low | The alt text describes a "right triangle", but no right-angle mark is drawn at the corner (640, 340). The implied scales are slightly unequal (100 px vs 80 px per unit). | Add a 14 px right-angle square at (640, 340), using equal scales if the SVG is regenerated. |
| D12 | n6-lesson-02 / `n6-lesson-02-ordered-pairs.svg` | Neatness | Low | The x tick labels are left-aligned at their ticks (the "1" sits 0–7 px right of x = 300), and there are no tick marks. Otherwise the diagram is clean and correct. | Add `text-anchor="middle"` to the x tick labels and draw 8 px tick marks. |
| D13 | All five | Neatness (phone) | Medium | In a 940-unit viewBox shown 358 px wide, the `.small` 18 px text renders at about 6.9 px and the 22 px labels at about 8.4 px. In the phone renders, the quadrant labels (lesson 1), tick numbers (lesson 2), "(1, 1)" and "(5, 3)" (lesson 5), and the lesson 1 note are hard to read. | Use at least 28 px for labels in this viewBox (about 10.7 px on the phone), or narrow the viewBox and tighten the margins so that the same labels render larger. |

### Diagram opportunities (no `diagram_audit.json` exists)

All 104 N6 questions are text-only. A diagram would clearly help the following, provided it
does not show the requested value:

- n6-l4-011, n6-l5-004 (triangle enclosed by two lines and an axis) and n6-l3-029 (triangle
  under intercepts): sketch the lines and shade the triangle, without labelling the
  intersections or intercepts.
- n6-l4-008 (right triangle described entirely in words): sketch A, B and the horizontal
  and vertical legs, without labelling lengths.
- New graph-reading items for 6.2, 6.4 and 6.5 (see C4): gradient or intercept read from a
  plotted line with labelled scales.

A per-question `diagram_audit.json` for N6 would make these decisions explicit, as it does
for the G banks.

---

## Root-cause patterns

1. **Checker mode name and behaviour disagree (C1).** `checking.py` implements
   `symbolic_equivalence` as an exact string match. Every author has relied on the mode name,
   so 9 N6 parts and 194 parts across 6 banks reject `4x+2`-style answers. The validator
   only checks that the canonical string passes itself, so it reports nothing.
2. **Coordinate graphs have no generator and no semantic validation (D1–D13).** The
   renderer `nextscholar-coordinate-svg-v1` named in all five `generation_spec`s does not
   exist anywhere in the repository. `scripts/recalibrate_geometry_content.py` only produces
   `nextscholar-geometry-svg-v1` assets for `g*` lessons. The SVGs were therefore
   hand-written. The `generation_spec` holds only `renderer`, `diagram_kind` and
   `lesson_key`, with no plotted data, scale or forbidden labels. `geometry_validation.py`
   checks only `angle_types`, opt-in `angle_markers` and opt-in
   `forbidden_visible_labels`, so `coordinate_graph` assets receive only a checksum check.
   All five N6 diagrams share the same hand-made template: a 940 × 500 viewBox,
   left-anchored labels with no collision check, 18/22 px fonts, and no tick scale. That
   template explains the label collisions (D4, D6, D7, D9, D10), the missing scales (D2, D3,
   D8) and the phone readability problem (D13). Recommended fix: add a small deterministic
   coordinate-graph renderer whose spec stores the axis ranges, points and lines; derive the
   pixels from those values; and have validation recompute point positions and check text
   bounding-box overlaps.
3. **Batches predate house rules v2 (C4, C7, C8).** All four batch manifests cite
   `house-rules-v1` and `math-question-authoring-v1`. These lack the v2 rules on outcome
   alignment, semantic duplicates and hint boundaries that the N2 audit introduced, which
   explains the outcome drift, the duplicate clusters and the stage-two hints that give the
   answer.
4. **Generator template for two-point problems (C6).** Every "find the rule or gradient
   from two points" solution opens with `known point = a(x) + b` and never shows the
   gradient, which points to a fixed solution template in the v1 generator.

## Not verified

- **Rendering surface:** the SVGs were rendered in headless Chromium with its fallback
  `system-ui` font, both on their own and at a simulated 358 px width. They were not viewed
  inside the production lesson page or on a physical phone, and production fonts may change
  label widths slightly. The overlap measurements came from Chromium `getBBox()`.
- **KaTeX output** of question and lesson LaTeX was not rendered visually. Only the
  validator's `latex_fragments_render` check was relied on.
- **Display of question titles to learners:** it is unclear whether titles are learner-facing,
  which affects the priority of the title findings in C9.
- **Checker fix effects:** C1 was confirmed by running the checker. The effect of any
  proposed checker change on other banks was not tested.
- **N6 v2 diagnostic questions** (`n6-l3-901` … `904`) were outside the scope.
