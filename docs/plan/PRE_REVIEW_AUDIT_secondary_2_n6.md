# Secondary 2 N6 technical pre-review audit

**Date:** 2 November 2026

**Scope:**
- All 104 questions in `backend_resources/question_bank/g3_math/secondary_2/n6/v1/` (batches B001–B004).
- Both N6 lessons, `n6-lesson-06` (outcome 6.6) and `n6-lesson-07` (outcome 6.7).
- Both lesson SVGs.

The lessons are not in an `n6` folder. They are stored in
`backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/` and were found through unit
`g3-sec2-n6` in that folder's `course.json`.

**Decision boundary:** this audit is report-only and technical. No question, lesson, SVG,
manifest, claim or review state was changed. No approval was recorded, and no paid model API was
called. Rendered images were written to a scratch directory outside the repository and were not
committed.

**Model and standards:**
- The audit follows the method of `N2_CALIBRATION_PRE_REVIEW_AUDIT.md`.
- It checks content against `LESSON_NOTES_CONTENT_STANDARD.md`.
- It checks diagrams against `GEOMETRY_CONTENT_STANDARD.md`, which covers diagram policy for the
  geometry banks. N6 is not a geometry topic group, so that standard's lesson-depth rules do not
  apply. This report uses its diagram principles as the reference.

## Counts

| Item | Count | Notes |
| --- | ---: | --- |
| Questions checked | 104 | All `draft`. B001–B004 are `ready_for_review`, with Mathematics and editorial review `pending`. |
| Question parts | 104 | Every part is `numeric` / `exact_numeric`. There are no algebraic responses, so the exact-string checker defect reported for N5 (C-1 there) does not affect N6. |
| Canonical answers recomputed independently | 104 | I used SymPy 1.14 in a scratch environment. 102 answers were parsed automatically from the prompt text; the other 2 (n6-l4-512, n6-l4-515) were solved directly. All 104 match. |
| Lessons checked | 2 | Both `draft`, revision 1. No approved N6 content exists. |
| Lesson worked examples and active recalls recomputed | 4 + 2 | All correct. |
| Diagrams referenced | **2** | `n6-lesson-06-graph` and `n6-lesson-07-graph`. No question references any asset. |
| Diagrams rendered and **viewed** | **2 of 2** | I rendered each with CairoSVG at 1920 px and at 390 px wide, viewed both PNGs, and checked the SVG coordinates by computation. The SHA-256 of each file matches the lesson manifest. |
| `diagram_audit.json` | none | These exist only for the geometry banks. |

Repository validators pass, but they miss most of the findings below:
- `question-bank validate` and `course-validate` report no errors.
- Chart assets are checked only for path, checksum and revisioned filename. Their `generation_spec`
  carries no plotted data, so nothing checks the curves (see R-4).

## Severity scale

- **Critical:** a wrong answer is marked correct, or a correct answer is marked wrong.
- **High:** a learner-facing defect affecting many items, a duplicate inside one pool, or a lesson that does not teach a method the bank requires.
- **Medium:** pedagogy, alignment or presentation problems to fix before approval.
- **Low:** polish.

---

# Part 1 — Content

## Summary

No wrong canonical answer or wrong worked-solution result was found. The problems are the same
generator-template defects found in N5. Both banks use `codex-offline-n*-v1` with prompt
`math-question-authoring-v1`, which predates the house rules v2 described in the N2 audit.

The N6 problems are:
- generator codenames in learner-facing prompts;
- coefficients written as `1x²`, `+0x`, `-1x` and `(x-0)`;
- an exact duplicate repeated four times;
- duplicates that cross difficulty levels and land in the same checkpoint;
- answer values that cluster;
- generic hints and solutions;
- a method gap: the bank expects x = −b/(2a) and completing the square, but neither lesson teaches them.

## C-1 High: the bank requires methods the lessons never teach

Both lessons were searched in full. Neither teaches the formula x = −b/(2a) for the axis of
symmetry. Neither teaches completing the square either: lesson 07 only *reads* (h, k) from a
rule already written as y = a(x−h)² + k. Its objective 3 mentions "completed-square form", but no
section shows how to convert a rule into that form.

The bank depends on these methods in two ways:

- **x = −b/(2a):**
  - It is stage-1 hint text for every 6.7 d2 item.
  - It appears in the worked solutions of n6-l2-506, -513, -520 and -531, and of the d3 "extremum
    calculation" items n6-l3-506, -513, -520 and -531.
- **Completing the square:** n6-l4-516 ("complete-square feature" of y = x²+2x−1) is solved by
  completing the square. Its d4 hint names "completion of the square".

**Proposed correction:** add to lesson 07:
- an explanation section and a worked example deriving the axis from x = −b/(2a), or by averaging
  the roots, starting from standard form;
- a short worked example that completes the square for a monic quadratic, for example
  x²+2x−1 = (x+1)²−2.

Until that is done, either remove the formula from the hints and solutions or mark these items
as beyond the lesson.

## C-2 High: exact and cross-difficulty duplicates, including within one pool

| Keys | Duplicate | Pool placement | Proposed correction |
| --- | --- | --- | --- |
| n6-l3-504, n6-l3-511, n6-l3-518, n6-l3-525 | Exact, four times: "g(x)=(x-4)(x-8). One zero is x=4. Find the other zero." Answer 8 every time. | l3-504 in `n6-unit-checkpoint`; the other three in `n6-adaptive-reserve` | Keep one item and replace three. Also see C-4: this is a d1 task. |
| n6-l2-522 (d2) and n6-l3-507 (d3) | Same task and numbers: axis x=0 and x=−3, so the answer is 3. Only the wording differs ("points … equal y-values" against "one root"). | **Both in `n6-unit-checkpoint`** | Replace n6-l3-507 with a genuine d3 task, for example "roots at 2 and k; the turning point is at x=5; find k" combined with evaluating the turning value. |
| n6-l2-529 (d2) and n6-l3-514 (d3) | Same numbers: axis x=−2 and x=−5, so the answer is 1. | **Both in `n6-unit-checkpoint`** | Replace n6-l3-514. |
| n6-l4-504, n6-l4-508, n6-l4-511 | Same template, the same arithmetic step 9p=18, and the same answer p=2 | reserve | Vary the horizontal distance and the answer (include a negative and a fractional p). |
| n6-l4-512, n6-l4-515 | Same template −3(x−r₁)(x−r₂) with half-distance 4, so both answers are 48 | reserve | Change one leading coefficient or the distance between the roots. |
| n6-l1-501, n6-l1-515, n6-l1-519 | "Coefficient of x²" with answer 2 each time | `n6-lesson-06-practice` | Use different a values, including a negative and a fractional value. Ask for b or c in at least one item. |
| n6-l1-502, n6-l1-507 (6.6 d1 "y-intercept check", f(0)) and n6-l2-507, -514, -521, -528 (6.7 d2 "graph intercept") | The same skill (read c) appears at two difficulties and in two outcomes. | lesson-06 practice, lesson-07 practice, checkpoint | Keep the d1 items. Replace the four d2 items with intercept tasks that need work, for example finding the y-intercept from vertex form y = 2(x−3)²−5. |

`authoring-validate` does not flag any of these. The generator codename appears in both the title
and the prompt (C-6), which pushes the prompt-shingle similarity of identical tasks below the 0.82
threshold. This is the same root cause measured in the N5 audit.

## C-3 Medium: answer values cluster and become guessable

Values from the canonical answers:
- **6.7 d3:** all three "intercept count" items (n6-l3-505, -523, -530) have answer **2**.
- **6.6 d3:** 5 of the 16 answers are −2. These are the three "leading coefficient" items
  (n6-l3-502, -509, -516) and two "recover q" items (n6-l3-503, -510). Another 4 are the
  duplicate answer 8.
- **d4:** 6 of the 16 answers are 2. That covers every "find a" item (n6-l4-502, -505, -509) and
  every "find p" item (n6-l4-504, -508, -511).

**Proposed correction:**
- Vary the intercept-count items so the answers include 0 and 1, for example y = (x+2)²+3 and
  y = (x−1)².
- Re-sample the coefficient-recovery items so that values differ within each template.

## C-4 High: difficulty misalignment

- **n6-l3-504, -511, -518, -525 (d3, 3 marks):** reading the second zero from (x−4)(x−8) is a d1
  task. Replace them with zeros that need a solution step, for example g(x) = (2x−3)(x+5), and ask
  for the positive zero.
- **n6-l3-507 and n6-l3-514 (d3)** are the same as d2 items (C-2).
- **n6-l2-507, -514, -521, -528 (d2)** read c directly, which is easier than the d1 items that
  evaluate f(4) (C-2).
- **Marks:** `total_marks == difficulty` for all 104 items. Every solution is one M step followed by
  an A step. For example, n6-l5-501 awards M4 for one line. Reviewers should decide whether this
  convention is intended.
- **Coverage gap in 6.7:** the outcome title includes "coefficient sign, maximum and minimum
  points". No item asks the learner to decide whether a parabola opens up or down, or whether a
  turning point is a maximum or a minimum. Each item that needs this states it ("opens upward"),
  or the response is a single number. For example, n6-l4-516 asks for "the minimum or maximum
  y-value", but the learner never states which it is. **Correction:** add multi-part items, for
  example (a) the turning value and (b) "maximum or minimum?". Alternatively, ask the learner to
  give the sign of a from a stated property.

## C-5 High: unsimplified coefficients in learner-facing prompts (34 items)

Template values are printed without simplification. Examples:
- `f(x)=3x²-1x+0` (n6-l1-502)
- `f(x)=-4x²+0x+2` (n6-l1-503)
- `y=1(x-0)²+1` (n6-l1-506)
- `y=3(x-3)²+0` (n6-l1-521)
- `f(x)=1x²+1x+4` (n6-l2-501)
- `y=-1x²+6x-13` (n6-l2-507)
- `y=3(x+6)(x-0)` (n6-l3-522)
- `y=1(x-0)(x-4)` (n6-l4-503)
- `y=1x²+2x-1` (n6-l4-516)

The 34 affected keys are:
n6-l1-502, -503, -506, -509, -514, -515, -518, -521;
n6-l2-501, -507, -509, -510, -512, -513, -514, -517, -519, -521, -526, -527, -528, -531;
n6-l3-501, -502, -506, -512, -513, -519, -520, -522, -526;
n6-l4-503, -507, -516.

Lesson 06 itself tells learners that the coefficient 1 and zero terms are left unwritten ("For
y=x²-4x+1, the unwritten coefficient of x² is 1"). The prompts therefore contradict the notation
being taught. The same raw notation appears in the solutions, for example `1(2)(-2)` in
n6-l4-503.

**Proposed correction:** write the simplified forms. For example:
- `3x²−x`
- `−4x²+2`
- `y=x²+1`
- `y=3(x−3)²`
- `y=3x(x+6)`
- `y=x(x−4)`

Also move the expressions into `inline_math` blocks. All 104 prompts are plain `text` blocks.

## C-6 High: generator codenames in learner-facing prompts and titles (all 104)

There are 13 codenames, each used 8 times: Acacia, Batik, Cendana, Dahlia, Equator, Flora, Garuda,
Heliconia, Intan, Jelutong, Kenari, Lontar and Meranti. Every title includes one, for example
"Acacia quadratic function". Every prompt carries one either as a label prefix, as in
"Acacia coefficient check: …", or as an invented context:

- "A **Batik design** follows y=(x+2)²+3" (n6-l1-511)
- "The **Acacia curve** has equation …" (n6-l1-516)
- "For the **Lontar quadratic** …" (n6-l4-505)
- "For a **Meranti model** …" (n6-l5-502)

Several are Indonesian or Malay cultural or natural words, such as batik, garuda (a national
emblem), lontar and meranti. Using them as meaningless labels may read as tokenistic to the target
audience.

**Proposed correction:**
- Remove every prefix and every pseudo-context.
- Give each question a descriptive title, for example "Axis of symmetry from two roots".
- If context is wanted, write a genuine one, such as the height of a thrown ball or the area of a
  garden plot, where the quadratic models something.

## C-7 Medium: solution text inside math mode renders incorrectly (4 items)

n6-l2-507, -514, -521 and -528 put English prose into a `display_math` block, for example
`At the y-intercept x=0, so y=-13.`. LaTeX renders this as run-together italic letters.

**Proposed correction:** split each into a `text` block ("At the y-intercept, x = 0, so") and a
`display_math` block (`y=-13`), or wrap the words in `\text{}`.

## C-8 Medium: hints and solutions are generic

- **Hints:** there is exactly one hint pair per (outcome, difficulty) cell, 10 pairs for 104 items.
  No hint leaks an answer, but several do not apply to the item they appear on:
  - The 6.6 d2 stage-2 hint, "…then isolate the one unknown coefficient", appears on the four
    "compare outputs" items (n6-l2-501, -512, -519, -526), which have no unknown coefficient.
  - The 6.7 d2 stage-2 hint, "Once the axis input is known, substitute it … to find the turning
    value", appears on the four intercept items and the four reflected-input items, which do not
    ask for a turning value.
  - The 6.7 d2 stage-1 hint relies on x = −b/(2a), which the lessons do not teach (C-1).
  - The blueprint `hint_policy` requires stage 2 to give "an explicit next method or intermediate
    setup". Write item-specific stage-2 hints.
- **Solutions:** 166 steps begin with one of two template sentences, "Translate the supplied
  function information into the relevant equation or graph feature." or "State the requested
  exact value and check it against the original function or symmetry condition.". The second
  sentence promises a check that is never shown. Several steps also skip working:
  - n6-l3-506 gives `y(-1)=2` with no substitution shown.
  - n6-l2-502 jumps straight to `=1`.
  
  Replace the template sentences with specific step descriptions, and show the substitution
  arithmetic.

## C-9 Low: calculator setting

`calculator_allowed` is `true` for every d3–d5 item. The arithmetic is small-integer and
mental-friendly throughout, so this does no harm. However, the ASEAN Scholarship tests are commonly
non-calculator. Reviewers should confirm the intended policy.

## C-10: wording and audience conflicts, reported rather than resolved

The N2 audit applied "Singapore/British English" and Singapore conventions. The current audience
standard instead asks for "clear international English" for Southeast Asian learners and says
unfamiliar terminology should be explained.

| Item | Observation | Rule from the N2 audit | Current audience standard |
| --- | --- | --- | --- |
| "turning point" and "vertex" | Most prompts and both lessons say "turning point", which is Singapore and UK usage. n6-l1-511 and n6-l1-516 say "vertex", and the lesson 06 SVG alt text and description also say "vertex". The lessons never connect the two terms. | "Turning point" is the expected term. | Both terms are common internationally, and "vertex" is standard in many SEA textbooks. The lessons should say once that "the turning point is also called the vertex". |
| "ordinate" (n6-l1-511) | This word appears nowhere else in the course. | Acceptable in Singapore usage, but rare. | Unfamiliar, unexplained jargon. Use "y-coordinate". |
| "What output does the function take at its vertex?" (n6-l1-516) | The phrasing is non-standard. | — | Use "Find the y-coordinate of the turning point (vertex)". |
| Currency and units | N6 has no money and no units, so the S$ rule is not triggered. | — | — |
| Codename contexts | See C-6. | — | These raise a cultural-appropriateness question for reviewers. |

## Lesson findings

Both lessons have 7 sections: 3 explanations, 2 worked examples, 1 active recall and 1 summary.
Each lesson's outcome matches its unit allocation. I recomputed every value:
- the lesson 06 table: 3, −2, −3, 0;
- b = −3 in lesson 06 example 2;
- f(−2) = −17 in the lesson 06 recall;
- (3, 8) in lesson 07 example 1;
- (3, −4) in lesson 07 example 2;
- 3 in the lesson 07 recall.

All are correct.

| Lesson / section | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n6-lesson-07 (whole lesson) | **High** (C-1) | x = −b/(2a) and completing the square are not taught, but the bank requires them. | Add an explanation section and worked examples. |
| n6-lesson-07, objective 3 | Medium | "Use … completed-square form" is listed as an objective, but the lesson only reads already-completed forms. | Either teach the conversion or reword the objective to "read". |
| n6-lesson-07, `n6-07-explanation-1` | Low | "A larger absolute value of a **usually** produces a narrower curve." For y = ax² + bx + c, a larger \|a\| always gives a narrower parabola, because the shape depends only on a. | Delete "usually". Optionally add a third panel to the SVG showing two different \|a\| values. |
| n6-lesson-07, `n6-07-explanation-1` | Low | "The b and c terms can shift the graph horizontally and vertically" is loose: b affects both the horizontal and the vertical position, and c gives only the y-intercept. | Change to "Together with a, the values of b and c determine where the turning point lies; c is the y-intercept." |
| Both lessons, depth metric | Medium (reviewer decision) | Counting only `text` and `latex`, the lessons have 2,410 and 2,368 authored characters, below the standard's 2,500. They pass `course-validate` because it measures `len(json.dumps(sections))`, which is 4,797 and 4,798. This is the same issue as N5's R-5. | Decide which definition the standard intends. |
| Both lessons, terminology | Low | "Turning point" is never connected to "vertex" (C-10). | Add one sentence. |

No lesson leaks the active-recall answer before it is attempted.

---

# Part 2 — Diagrams and graphs

Both diagrams were rendered and **viewed**, at full size and at 390 px wide. Their SVG coordinates
were checked by computation.

| Asset key | Path (resolved from the lesson JSON) | Referenced by |
| --- | --- | --- |
| n6-lesson-06-graph | `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/n6-lesson-06-quadratic-function.svg` | n6-lesson-06, section `n6-06-explanation-3` |
| n6-lesson-07-graph | `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/n6-lesson-07-quadratic-properties.svg` | n6-lesson-07, section `n6-07-explanation-1` |

**Accuracy checks that passed:**

*Lesson 06 graph*
- The table values are correct for y = x² − 4: (−3, 5), (−2, 0), (−1, −3), (0, −4), (1, −3),
  (2, 0) and (3, 5).
- The marked points match.
- The scale is consistent: 78.5 px per x-unit and 28.75 px per y-unit.
- The roots are at px 128 and 442, which is x = ±2.
- The vertex is at px 260, which is y = −4.
- The drawn curve crosses the x-axis at x = −2.009.
- The alt text, title and description match the drawing, and nothing in it reveals a question
  answer.

*Lesson 07 graph*
- The left panel is an upward parabola with its minimum marked.
- The right panel is a downward parabola with its maximum marked.
- The panel titles "a > 0: minimum" and "a < 0: maximum" are correct, and the alt text matches.

## Diagram findings

| ID | Stable key | Asset path | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- | --- |
| D-1 | n6-lesson-07 | `assets/n6-lesson-07-quadratic-properties.svg` | Accuracy (misleading relationship) | **Medium** | In both panels, the dashed axis of symmetry is drawn exactly on top of the y-axis: left panel x = 202 and right panel x = 230, which are the vertical axes. The figure therefore suggests that the axis of symmetry *is* the y-axis. The same section says that b and c shift the turning point, and lesson 07's example 2 has its axis at x = 3. The lesson 06 graph also shows the axis on the y-axis, which is correct there because y = x² − 4. As a result, learners never see an axis of symmetry anywhere else. | In at least one panel, move the vertex off the y-axis. For example, in the right panel put the vertex at panel x ≈ 290 and keep the y-axis at x = 230. Draw the dashed line through the vertex and label the y-axis "y" separately. |
| D-2 | n6-lesson-07 | `assets/n6-lesson-07-quadratic-properties.svg` | Neatness | Medium | In the right panel, the "maximum" label (text at x = 244, y = 88) is drawn on the curve, so the orange stroke crosses the word. The "axis of symmetry" label (x = 240, y = 160) runs into the right arm of the curve, which crosses the letters "met". Both collisions are visible in the render. | Move "maximum" above the point, for example x = 244, y = 66. Move "axis of symmetry" to the left of the dashed line, for example `text-anchor="end"` at x = 220, y = 160, or above the panel title area. |
| D-3 | n6-lesson-06 | `assets/n6-lesson-06-quadratic-function.svg` | Neatness | Medium | All three point labels collide with the curve. The curve passes through the "0)" of "(−2, 0)" (text at x = 104, y = 170), through the "(2" of "(2, 0)" (x = 422, y = 170), and through the "(0" of "(0, −4)" (x = 300, y = 267), next to the vertex dot. | Place root labels outside the parabola, for example "(−2, 0)" with `text-anchor="end"` at x = 120, y = 136, and "(2, 0)" at x = 450, y = 136. Place "(0, −4)" below the vertex, for example x = 285, y = 290, `text-anchor="middle"`. |
| D-4 | n6-lesson-06 | `assets/n6-lesson-06-quadratic-function.svg` | Accuracy and neatness | Low | The last table row "1, 2, 3 \| −3, 0, 5" packs three ordered pairs into one row. That contradicts the explanation it illustrates ("Each row in a value table gives one point"). Only 3 of the 7 table points are plotted. | Use a horizontal table (x: −3 … 3, y: 5 … 5) with one column per point, and plot all seven points. |
| D-5 | n6-lesson-06 | `assets/n6-lesson-06-quadratic-function.svg` | Accuracy | Low | The path is two hand-placed cubic Béziers, not a sampled parabola. Compared with y = x² − 4 at this scale, it is 0.24 units (6.9 px) too low at x = −1 and 0.57 units (16 px) too high at x = −2.6. Because the axes have no ticks the error is not obvious, but the graph is meant to model plotting from a table. | Generate the path by sampling y = x² − 4, for example 40 points with a polyline or a fitted quadratic Bézier. One quadratic Bézier per half is exact for a parabola. |
| D-6 | n6-lesson-06 | `assets/n6-lesson-06-quadratic-function.svg` | Accuracy and pedagogy | Low | The section text stresses "use a consistent scale", but the axes have no tick marks or numbers, so the scale cannot be read. An unlabelled dashed axis of symmetry is also drawn on top of the y-axis, although lesson 06 does not discuss symmetry. | Add integer ticks with labels (−3 … 3 on x, −4 … 5 on y). Remove the dashed line, or label it. |
| D-7 | n6-lesson-07 | `assets/n6-lesson-07-quadratic-properties.svg` | Accuracy | Low | The right-hand parabola, which illustrates symmetry, is not exactly symmetric. Its endpoints are 155 px and 152 px from the axis (x = 75 and 382 about x = 230). | Make the endpoint x = 385. |
| D-8 | Both lessons | both SVGs | Neatness (phone) | Medium | Each SVG is 960 px wide. At a 390 px phone width it scales by 0.41, so the 16–18 px labels render at about 6.5–7.4 px, and the table and point labels are hard to read. This was confirmed on the 390 px renders. The side-by-side two-panel layout causes this. | Provide a stacked portrait variant (one panel per row, about 480 px wide) or raise the label font size to 26–28 px. |

No diagram reveals an answer to an N6 question. No question references either diagram.

## Text-only questions a diagram would clearly help

There is no `diagram_audit.json` for N6. It is not required, because N6 is not a geometry group.
However, outcome 6.7 is "graphs of quadratic functions and their properties", and not one of its
52 questions shows a graph. Every item is algebraic. The following would clearly benefit from a
graph:

- **Sign and direction:** a new item showing a sketched parabola and asking for the sign of a, or
  whether the turning point is a maximum or a minimum. This also closes the coverage gap in C-4.
- **Roots and axis of symmetry:** for example n6-l1-505, n6-l1-510 and the reflected-input items
  n6-l2-508, -515, -522 and -529. A graph-reading variant ("the graph crosses the x-axis at the
  points shown") would test reading from a graph, which is what 6.7 describes.
- **Reconstruction from a graph:** for example n6-l5-501 and n6-l5-505. Presenting the roots and
  the extra point on a graph would fit the scholarship-test style.

---

# Root-cause patterns

**R-1. Generator template `codex-offline-n6-v1`.** It produced:
- the codename prefixes and pseudo-contexts (C-6);
- unsimplified printing of coefficients (C-5);
- one hint pair per difficulty cell (C-8);
- the two template solution sentences (C-8);
- `total_marks = difficulty` (C-4);
- plain-text prompts (C-5).

It also sampled parameters without deduplication, giving exact repeats and clustered answers
(C-2, C-3).

This is the same template family as N5 (`codex-offline-n5-v1`), and the N5 audit found the same
patterns. A single fix to the generator would cover both banks.

**R-2. Codenames defeat the duplicate detector.** `_normalised_prompt` in
`question_bank/src/question_bank/authoring.py` includes the question title. The codename then
appears twice in each item's text, which lowers the shingle similarity of identical tasks below
0.82. This was measured in the N5 audit, and the mechanism is the same here. The detector also
compares prompts only, so it cannot catch duplicates with different wording but the same numbers
(n6-l2-522 and n6-l3-507). Comparing (outcome, normalised mathematical content, canonical answer)
would catch these.

**R-3. The bank template and the lessons were authored separately.** The 6.7 template uses
x = −b/(2a) and completing the square, which lesson 07 does not teach (C-1). No validator compares
the methods used in solutions with the lesson that a practice pool belongs to.

**R-4. Chart SVGs are hand-written and nothing validates them.**
- Both N6 SVGs name `renderer: nextscholar-chart-svg-v1` with `diagram_kind` values of
  `quadratic_table_graph` and `quadratic_properties`.
- No renderer with that name, and no handler for either `diagram_kind`, exists anywhere in the
  repository. `scripts/recalibrate_geometry_content.py` and
  `question_bank/src/question_bank/geometry_validation.py` handle only geometry angle diagrams.
- For charts, `course_validation._validate_assets` runs `geometry_diagram_issues`, whose angle
  and answer-leak checks find nothing to check, because `generation_spec` contains no function,
  domain or plotted points.
- The curves are therefore hand-placed Béziers (D-5), and the label positions are hand-set (D-2,
  D-3).

The same renderer name appears in the Secondary 2 N7 lessons `n7-lesson-06`, `-07` and `-08`.
I did not audit those, but they probably have the same weaknesses.

**Fix:** add the plotted function and domain to `generation_spec`, for example
`{"function": "x^2-4", "x_range": [-3, 3], "marked_points": [...]}`. Then generate the path from
that spec and add a validator that samples the SVG path against the function. Label placement
should also avoid the curve.

**R-5. The lesson depth metric counts JSON size.** This is the same as N5's R-5.

---

# What could not be verified

- I did not see how the plain-text prompts, or the four broken `display_math` solution blocks,
  render in the learner web interface. C-5 and C-7 are based on the raw JSON and on how LaTeX
  treats prose.
- The 390 px check used a CairoSVG render scaled to 390 px. I did not test it in the app's actual
  lesson layout, which may add padding or allow zoom.
- Whether the difficulty-equals-marks convention and the calculator policy for d3–d5 are intended
  (C-4, C-9) is a reviewer decision.
- I did not audit the N7 SVGs that share the `nextscholar-chart-svg-v1` renderer name (R-4). They
  are outside this scope.
