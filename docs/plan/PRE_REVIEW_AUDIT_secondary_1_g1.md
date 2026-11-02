# Secondary 1 G1 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_1/g1/v1/`
(batches B001–B004) and all seven G1 lessons (`g1-lesson-01` … `g1-lesson-07`). The
lessons are stored in the Secondary 1 course folder
`backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/` and belong to unit
`g3-sec1-g1` of course `g3-sec1-math`.

**Decision boundary:** this is a technical pre-review only. It records no Mathematics or
editorial approval and changes no review state. No question, lesson, SVG, manifest or
claim was edited. No paid model API was called.

**Review state found:** every G1 question is `draft` (83 at revision 1, 18 at revision 2,
3 at revision 3). All four batch manifests are `ready_for_review`, with Mathematics and
editorial review both `pending`. All seven lessons are `draft` (lesson 01 at revision 3,
the others at revision 2), and none has a reviewer recorded. No G1 content is approved yet,
so no approved item needed special handling.

## Counts

| Item | Count |
| --- | ---: |
| Questions checked | 104 |
| Lessons checked | 7 |
| Diagrams referenced (21 question + 7 lesson) | 28 |
| Diagrams rendered to PNG and viewed at 940 px | 28 |
| Diagrams also viewed at 390 px (phone width) | 28 |
| Superseded, unreferenced SVGs (not audited) | 4 |

The four superseded SVGs are `g1-l1-001-diagram.svg`, `g1-l2-001-diagram.svg`,
`g1-l3-001-diagram.svg` and course asset `g1-lesson-01-angle_types.svg`. They are kept for
immutable learner records under the revision-3 asset rule and are not referenced by
current JSON.

## Method

- **Answers:** every canonical answer was recomputed from the prompt alone, before
  reading the solution, using a SymPy script (equations solved symbolically, ratios and
  polygon formulas evaluated). All 104 matched. Intermediate values were substituted back
  into the original conditions: for example, g1-l3-021 gives exterior angles
  80°/120°/160° and interior angles 100°/60°/20°, and g1-l5-003 gives exterior angles
  24°/36° and 15/10 sides.
- **Content checks:** worked steps, accepted answers, stated conditions, outcome and
  difficulty (against `docs/plan/FIVE_LEVEL_DIFFICULTY_MIGRATION.md`), hint leakage
  (against house rules v2: "neither hint may state the final answer"), semantic
  duplicates and wording.
- **Duplicates:** checked by number-normalised template matching plus manual comparison
  of operation pattern and numerical structure, including the lesson worked examples.
- **Rendering:** every SVG was rendered with the preinstalled Chromium through
  Playwright, at 940 px and 390 px wide, into a scratch directory outside the repo. Each
  PNG was viewed.
- **Geometry checks:** coordinates were checked by hand and by a browser script that
  compares every text element's `getBBox()` against every stroke (sampled at 1 px), the
  viewBox and the computed font size.
- **Root cause:** traced through `scripts/recalibrate_geometry_content.py` and
  `question_bank/src/question_bank/geometry_validation.py`.
- **Existing validators:** `question-bank validate` on the G1 bank and
  `question-bank course-validate` both report 0 errors and 0 warnings. The diagram
  findings below are therefore all invisible to the current validators.

Severity: **High** means a learner cannot answer, is given wrong or misleading
information, or is handed the answer. **Medium** means it should be fixed before approval.
**Low** means polish or a reviewer judgement call.

---

## Part 1: Content findings

No canonical answer, accepted answer or final worked-solution result is wrong. Every
response is `exact_numeric` with no extra accepted answers, which is appropriate for the
integer and code answers here.

### C-01 · High · Quadrilateral code legend missing from 11 questions

**Keys:** g1-l2-005, g1-l2-013, g1-l2-021 ("Using the same codes 1–6"); g1-l3-006,
g1-l3-013, g1-l3-020, g1-l3-028, g1-l3-029, g1-l4-003, g1-l4-007, g1-l5-004 ("Using codes
1–6").

**Evidence:** only g1-l1-004, g1-l1-010 and g1-l1-015 define the legend (square = 1 …
trapezium = 6). Questions are served individually: the practice player renders each item
alone (`apps/web/src/components/practice-player.tsx`). Several of these items appear in
the unit checkpoint (g1-l3-028, g1-l3-029) or the adaptive reserve (g1-l4-003,
g1-l4-007, g1-l5-004), where no legend-bearing item comes first. Without the legend these
items cannot be answered.

**Proposed correction:** replace the prefix in all 11 prompts with the full legend used in
g1-l1-004: "Use this code: square = 1, non-square rectangle = 2, non-square rhombus = 3,
other parallelogram = 4, kite = 5, trapezium = 6."

### C-02 · High · g1-l3-001 duplicates g1-l3-002, and g1-l3-003 repeats the structure

**Evidence:**
- g1-l3-001 (outcome 1.1): "Two adjacent angles form a straight angle and are in the
  ratio 2:3. Find the larger angle." Answer 108.
- g1-l3-002 (outcome 1.2): "Two adjacent angles on a straight line are in the ratio 2:3.
  Find the larger angle." Answer 108.
- g1-l3-003 (outcome 1.3): co-interior angles in the ratio 2:3. Answer 108, with the same
  180 ÷ 5 × 3 computation.

These are the challenge items of the lesson 01, 02 and 03 practice pools, so a learner
meets the same task three times in a row. g1-l3-001 also tests straight-line angles
(outcome 1.2), not angle types.

**Proposed correction:**
- Rewrite g1-l3-001 as a genuine 1.1 task, for example: "A reflex angle and the
  smaller angle between the same two rays are in the ratio 7:2. Find the reflex angle."
  (Answer 280.)
- Change g1-l3-003 to a different ratio and answer, for example 4:5 giving 100°, or make
  it ask for the smaller angle.

### C-03 · Medium · Parallel-line condition missing from six questions and one lesson

**Keys:** g1-l2-010, g1-l2-011, g1-l2-019, g1-l3-011, g1-l3-018, g1-l4-010.

**Evidence:** each prompt starts "Alternate interior angles are …", "Co-interior angles
are …", "Corresponding angles are …" or "Same-side interior angles are …" but never
states that the lines are parallel. The equal and supplementary relationships only hold
for parallel lines. g1-l4-010's hint even says "because the lines are parallel". Lesson
03's own pitfall section says "Do not use a parallel-line fact unless parallel arrows are
shown or parallelism has been proved". g1-l4-014 shows the correct form.

**Proposed correction:** start each prompt with "Two parallel lines are cut by a
transversal." Apply the same fix to `g1-lesson-03` worked example `g1-13-example` and
active recall `g1-13-recall` (see L-01).

### C-04 · Medium · g1-l2-020 asks for an angle that does not exist

**Evidence:** "The diagonals of a square intersect. Find the acute angle between them."
Square diagonals meet at 90°, so there is no acute angle. The canonical answer 90 is right,
but the wording is wrong.

**Proposed correction:** "Find the angle between them in degrees."

### C-05 · Medium · g1-l5-001 has an ambiguous prompt and a faulty justification

**Evidence:**
- "The other makes an acute angle of 67° on the opposite side" does not fix the
  orientation. If both transversals lean the same way, the angle between the upward rays
  is 67° − 38° = 29°, not 75°. Only a correct diagram can settle it, and the current
  diagram is wrong (see D-03).
- Hint 2 and step S1 say "the three angles across the upper straight line total 180°",
  but the unknown angle x is at the meeting point P, not on the upper line.

**Proposed correction:**
- Prompt: "One transversal slopes up to the left and makes an acute angle of 38° with
  the parallel lines. The other slopes up to the right and makes an acute angle of 67°
  with them."
- Justification: draw a line through P parallel to the given lines. Alternate angles give
  38° and 67° at P, so 38° + x + 67° = 180°. Alternatively, use the triangle formed by the
  upward rays and the upper line.

### C-06 · Medium · Hints state the final answer (house rules v2)

**Stage-2 hints that state or name the answer:**

| Key | Hint text |
| --- | --- |
| g1-l1-004 | "Only the square has both properties." |
| g1-l1-006 | "Half of 8 cm is 4 cm." |
| g1-l1-007 | "A 90° angle uses code 2." |
| g1-l1-011 | "Two lots of 180° make 360°." |
| g1-l1-015 | "This is a trapezium …" |
| g1-l1-019 | "A pentagon has five vertices." |
| g1-l1-020 | "A complete turn is 360°." |
| g1-l2-007 | "… is 60°." |
| g1-l2-015 | "A right angle measures 90°." |
| g1-l2-020 | "… form right angles." |
| g1-l2-021 | "… identifies a kite." |
| g1-l2-023 | "the given 48°" |
| g1-l2-028 | "Use n = 6." |
| g1-l3-008 | "AC = 6 cm" |
| g1-l3-012 | "Only that diagonal …" |
| g1-l3-019 | "… form right angles." |
| g1-l3-027 | "eight equal positions" |
| g1-l3-029 | "Their intersection is the square." |
| g1-l3-031 | "Copy the full given 58° angle." |

g1-l1-005's stage-1 hint, "Use (n − 2) × 180° with n = 3", already completes the
calculation.

**Note:** G1 was authored with prompt `math-question-authoring-v1`. House rules v1 had no
hint rule, so this is a gap against the current v2 rule rather than an authoring error.

**Proposed correction:** keep stage 2 at the set-up step, for example "Write the
condition the arcs must satisfy" or "Which family has four right angles?" Never name the
result. For g1-l1-005, stage 1 should be "How many triangles can a triangle be split
into?"

### C-07 · Medium · Answer appears in the learner-visible title

**Evidence:** titles are rendered to learners (`practice-player.tsx:304`,
`live-practice-view.tsx:208`).
- g1-l3-023: "Constructing a 75-degree angle". Answer 75.
- g1-l4-016: "Composite 105-degree construction". Answer 105.
- g1-l2-007: "Constructing a sixty-degree angle". Answer 60. This title is also drawn as
  the diagram heading (see D-06).

**Proposed correction:** "Combining two constructed angles" (l3-023 and l4-016) and
"Angle from an equilateral construction" (l2-007).

### C-08 · Medium · Difficulty overstated

The rubric (Level 4 = unfamiliar problem needing method selection, constraints or
justification; Level 5 = non-routine synthesis) is not met by these items:

| Key | Labelled | Effective | Reason |
| --- | ---: | ---: | --- |
| g1-l4-016 | 4 | 1 | 60° + 45° |
| g1-l3-023 | 3 | 1 | 45° + 30° |
| g1-l3-031 | 3 | 1 | Answer is stated in the prompt |
| g1-l2-023 | 2 | 1 | Answer is stated in the prompt |
| g1-l3-008 | 3 | 1–2 | Reads AC from the prompt |
| g1-l3-019 | 3 | 1 | Rhombus diagonal fact |
| g1-l3-027 | 3 | 1 | Octagon order of rotational symmetry |
| g1-l2-027 | 2 | 1 | Same single step as d1 item g1-l1-013 |
| g1-l4-001, l4-004, l4-005, l4-009, l4-010, l4-013, l4-014 | 4 | 2–3 | Routine one-equation angle sums; no method selection |
| g1-l4-007 | 4 | 2 | Identical to lesson 05 worked example 1 |
| g1-l5-002 | 5 | 2–3 | One linear equation; adjacent-pair form 5x + 10 = 180 |
| g1-l5-004 | 5 | 3 | Same chain as g1-l3-029 |
| g1-l5-005 | 5 | 3 | B = D, then quadrilateral sum |

**Proposed correction:** either relabel these items (the blueprint distribution would
then need rebalancing) or raise their demand. For example, g1-l5-005 could withhold
angle C and give a relation between angles B and C instead.

### C-09 · Medium · Semantic duplicates and repeated numerical structure

These are in addition to C-02:

| Items | What repeats |
| --- | --- |
| g1-l2-018 and g1-l3-009 | Both reduce to 2x + 220 = 360, x = 70 |
| g1-l3-004 and g1-l4-005 | Same expressions x, x + 20, x + 40 (triangle versus point) |
| g1-l1-016 (74°), g1-l2-024 (86°), g1-l2-031 (126°), lesson 07 example (92°) | Same "halve the angle" task four times |
| g1-l1-013 and g1-l2-027 | Alternate interior angle copied |
| g1-l2-020 and g1-l3-019 | Diagonals meet at 90° |
| g1-l3-023 and g1-l4-016 | Add two constructed angles |
| g1-l3-013 and g1-l4-003 | Rhombus via perpendicular diagonals |
| g1-l3-029 and g1-l5-004 | Square as rectangle ∩ rhombus |
| g1-l3-028, g1-l4-007 and lesson 05 worked example 1 | Parallelogram plus equal diagonals gives a rectangle |
| g1-l3-030 and lesson 06 worked examples 1 and 2 | Regular 15-gon with 24° exterior angle (same numbers); the checkpoint item is answerable from memory |
| g1-l1-014, lesson 05 active recall and g1-l2-029 | Non-square rectangle symmetry |
| g1-l2-009, g1-l2-019, g1-l3-011, g1-l3-017, g1-l3-018, g1-l4-002 | All six solve to x = 20 |

**Proposed correction:** keep one item per structure. Rewrite the others with a new
operation pattern and solution value (house rules v2: "avoid repeating … operation
pattern and numerical structure"). Change lesson 06's examples to a polygon that is not
in the bank, for example 20 sides with an 18° exterior angle.

### C-10 · Low · Outcome alignment

- g1-l3-009 and g1-l4-005 are tagged 1.1 but are angles-at-a-point equations (1.2).
- g1-l2-029 (rotational order of a rectangle) is tagged 1.5 but symmetry belongs to 1.4.
  The same applies to the lesson 05 active recall.
- g1-l4-012 (number of perpendicular bisectors needed to locate a circumcentre) goes
  beyond "construction of simple geometrical figures". The term "non-degenerate" is not
  taught. This is a reviewer judgement call on scope.

**Proposed correction:** retag, or rewrite to the tagged outcome. For example, make
g1-l4-005 ask learners to classify the largest angle. For g1-l4-012, either keep it with a
lesson 07 sentence introducing the circumcentre, or replace it.

### C-11 · Low · Wording

- **g1-l1-012:** the stem already defines reflex ("more than a straight angle but less
  than a complete turn"). Drop that clause.
- **g1-l3-005:** "the exterior angle at the vertex" is ambiguous. Use "at the apex (the
  vertex where the two equal sides meet)".
- **g1-l4-002:** hint 1 calls the angles "obtuse" before the learner has computed them.
  Use "Equate the vertically opposite angles".
- **g1-l1-005:** hint 2, "A triangle can be treated as one triangle", is circular.
- **Missing "in degrees":** g1-l2-016, g1-l3-009, g1-l3-026 and g1-l5-001 omit it, while
  the numeric field has no unit.
- **g1-l2-007:** "construct an equilateral triangle on a ray" is unclear. Use "on a
  segment AB drawn along a ray from A".

### C-12 · Low · Regional rules conflict (reported, not resolved)

The N2 audit applied house rules v2: `locale: en-SG`, "Singapore/British English", S$
currency. The current lesson standard (`LESSON_NOTES_CONTENT_STANDARD.md`) says the
audience is Indonesia and Southeast Asia, that the Singapore syllabus is "a calibration
and coverage reference" only, and that content should use clear international English
and explain unfamiliar terms.

G1 has no currency contexts. The conflict shows up in terminology:
- "co-interior" (lesson 03, g1-l1-018, g1-l2-011, g1-l3-003, g1-l4-010) sits beside
  "same-side interior" (g1-l3-018), and lesson 03 does not introduce the second name.
- "trapezium" is defined in lesson 05 only as "under the syllabus convention used here"
  or "in this course classification". That is opaque to non-Singapore learners, and US
  English calls the shape a trapezoid.
- The blueprint names the course "Singapore G3 Mathematics".

**Suggestion for reviewers:**
- In lessons 03 and 05, name both terms once ("co-interior (same-side interior)
  angles") and state "a trapezium has exactly one pair of parallel sides (called a
  trapezoid in American English)".
- Then use one term consistently in the bank.
- Decide whether house rules v2's `en-SG` locale should be updated to match the audience
  standard.

### Lesson content findings

All seven lessons pass the course validator's structural gate (seven or more sections,
two worked examples, at least 3,000 characters, one diagram).

| ID | Lesson | Severity | Finding | Proposed correction |
| --- | --- | --- | --- | --- |
| L-01 | g1-lesson-03 | Medium | Worked example `g1-13-example` ("A co-interior angle is 117°…") and recall `g1-13-recall` ("A corresponding angle is 68°…") omit the parallel condition, contradicting the lesson's own pitfall. | Add "Two parallel lines are cut by a transversal." |
| L-02 | all seven | Medium | Each lesson's first worked example has one step and the same boilerplate verification note ("The result follows the stated property and satisfies the original geometric conditions."). The summary text is identical in all seven, including "construction relationship" and "with units" in angle-only lessons. This meets the letter of the standard ("worked examples with explicit steps and a verification note") but not its intent. | Give each first example two or more reasoned steps and a specific check, for example "232° + 128° = 360° and 232° > 180°". Tailor each summary to its outcome. |
| L-03 | g1-lesson-05 | Low | `square ⊂ rectangle ∩ rhombus ⊂ parallelogram` is imprecise: a square *is* the intersection. "Trapezium … one pair" should say "exactly one pair". | Use `square = rectangle ∩ rhombus` and `rectangle, rhombus ⊂ parallelogram`. Define the trapezium explicitly (C-12). |
| L-04 | g1-lesson-05 | Low | The active recall tests rectangle symmetry (1.4), not classification (1.5). It duplicates g1-l1-014. | Replace it with a classification recall, for example "A parallelogram has perpendicular diagonals and no right angle. Name it." |
| L-05 | g1-lesson-06 | Low | The worked examples use the regular 15-gon and 24°, the same numbers as checkpoint item g1-l3-030 (C-09). | Use a polygon that is not in the bank. |
| L-06 | g1-lesson-01 | Low | "Straight angle" and "complete turn" are used in g1-l1-012 and g1-l3-001 but are not named in the lesson. | Add the 180° = straight angle and 360° = complete turn names to `g1-11-method`. |
| L-07 | g1-lesson-07 | Low | Worked example 1 (bisect 92°) is arithmetic only and duplicates three bank items. | Replace it with a construction-decision example, for example which radius is valid. |

---

## Part 2: Diagram and graph findings

There are no graphs or charts in G1. Every question and lesson diagram is an output of
`nextscholar-geometry-svg-v1`, through one of seven fixed `diagram_kind` templates.

**Global finding.** No question diagram depicts its own question. Each one is a copy of
the lesson's generic reference figure for that outcome, differing only in the heading
text. As a result:
- question measures (35°, 68°, 64°, 8 cm, 50°/60°, 1260°, 38°/67°, 70°/110° and so on)
  are never drawn;
- alt texts claim "Stated measures include …" for values that are not in the image; and
- `generation_spec` records no dimensions, although `GEOMETRY_CONTENT_STANDARD.md` requires
  "explicit dimensions in their metadata".

The per-asset findings follow.

### D-01 · `angle_types` template

Assets: `assets/g1-l1-001-diagram-r3.svg`, `assets/g1-l2-001-diagram-r3.svg`,
`assets/g1-l3-001-diagram-r3.svg`, and lesson asset `assets/g1-lesson-01-angle_types-r3.svg`.

| Key | Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- | --- |
| g1-l1-001 | accuracy | High | Titled "Classifying a 35-degree angle", but it draws 60°/90°/120°/240° and no 35° angle. The alt text says "Stated measures include 35°". The acute example shown is 60°, not the question's angle. | Draw one 35° angle: vertex (300,260), base ray to (560,260), second ray to (300 + 260·cos35°, 260 − 260·sin35°) = (513,111), arc r = 50, label "35°" at the arc bisector (r = 75). Remove the four-type reference strip. Set `angle_measures: {"given": 35}` and update the alt text to describe it. Alternatively, mark the question text-sufficient and drop the asset. |
| g1-l2-001 | accuracy | Medium | A complement question gets the four-type strip, with no 38° and no right angle split into 38° + x. | Draw a right angle (square corner mark) split by a ray at 38° from one arm. Label 38° and x. Do not label 52°. |
| g1-l3-001 | accuracy | Medium | A straight-angle ratio question gets the four-type strip. Nothing in the figure relates to the task, and the item duplicates g1-l3-002 (C-02). | Redraw once C-02 is fixed. For the proposed 7:2 reflex rewrite, draw two rays with the reflex arc labelled 7k and the smaller arc labelled 2k. |
| all four | neatness | Medium | The reflex arc runs through the "240°" label (label box 675–716 × 254–274; 21 px of arc inside it). The obtuse arc touches "120°" (8 px). Type captions sit on two baselines (y = 305 and y = 325). | Move "240°" outside the arc, for example `x="652" y="236"` with `text-anchor="end"`, or to radius 75 on the reflex bisector. Move "120°" to (578, 200). Put all four captions on y = 325. |

### D-02 · `intersection` template

Assets: `assets/g1-l1-002-diagram.svg`, `assets/g1-l3-002-diagram.svg`,
`assets/g1-l5-002-diagram.svg`, and lesson asset `assets/g1-lesson-02-intersection.svg`.

| Key | Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- | --- |
| g1-l5-002 | accuracy (answer leak) | High | The side panel prints "2a + 2b = 360°", which is the solution's first step (S1: 2(3x − 5) + 2(2x + 15) = 360) for a Level 5 item. The expressions (3x − 5)° and (2x + 15)° are not shown. | Remove the formula panel. Label the four angles (3x − 5)°, (2x + 15)°, (3x − 5)°, (2x + 15)° alternately, each at radius about 45 on its angle bisector from the intersection (305, 175), with small arcs. |
| g1-l1-002 | accuracy | Medium | The question is one ray on a straight line (68° and an unknown), but the figure is two crossing lines with no 68°. The panel "a + b = 180°" gives the method (hint 1). | Draw a horizontal line with one ray from a point on it. Mark 68° and x with arcs. Remove the panel. |
| g1-l3-002 | accuracy | Medium | The ratio 2:3 is not shown. The panel gives the method. | Draw a line with one ray. Label the angles 2k and 3k. Remove the panel. |
| all four | accuracy | Low | The letters a and b float with no arcs, so it is not shown which angle each names. "a = a" is a tautology. | Add an arc for each angle. In the lesson asset, replace "a = a" with "vertically opposite: equal". |

### D-03 · `parallel` template

Assets: `assets/g1-l1-003-diagram.svg`, `assets/g1-l3-003-diagram.svg`,
`assets/g1-l5-001-diagram.svg`, and lesson asset `assets/g1-lesson-03-parallel.svg`.

| Key | Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- | --- |
| g1-l5-001 | accuracy | High | The question has **two** transversals meeting between the parallels with acute angles 38° and 67°. The figure has **one** transversal, no 38°, no 67° and no meeting point, so it contradicts the question. Given C-05, the diagram is also the only way to fix the orientation. | Draw parallels at y = 100 and y = 290 (arrow marks), with P = (470, 195). Draw transversal 1 through P and A = (348, 100) (up-left at 38°), extended to (592, 290). Draw transversal 2 through P and B = (510, 100) (up-right at 67°), extended to (430, 290). Mark 38° at A and 67° at B inside triangle PAB, and x at P between PA and PB. Do not print 75°. Alt text: "Two parallel horizontal lines; two transversals cross at P between them; one meets the upper line at 38°, the other at 67°; x is the angle at P between the upward rays." |
| g1-l1-003, g1-l3-003 | accuracy | Medium | 64° (l1-003) and the 2:3 ratio (l3-003) are not drawn. The words "corresponding", "alternate" and "co-interior" each sit in a single region, although each relationship is a *pair* of angles, so the figure does not show which angles correspond. | Mark the given angle with an arc and label (64°, or 2k). Mark the target angle as x, also with an arc. Remove the three relationship words. |
| lesson 03 | accuracy | Medium | The alt text says the angle positions are "highlighted". Nothing is highlighted; there are only three floating words. | Draw three colour-coded arc pairs (F, Z and C) at the two intersections (536, 115) and (355, 255), with a small legend. Make the alt text match. |
| all four | neatness | Low | "corresponding" touches the transversal (1 px at x ≈ 570, y ≈ 100). | Move the label to x = 590. |

### D-04 · `quadrilateral` template

Assets: `assets/g1-l1-004-diagram.svg`, `assets/g1-l3-006-diagram.svg`,
`assets/g1-l5-004-diagram.svg`, and lesson asset `assets/g1-lesson-05-quadrilateral.svg`.

| Key | Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- | --- |
| g1-l1-004, g1-l5-004 | accuracy (answer leak) | High | The hierarchy chart ends at a single "square" box. Both questions' answer is square (code 1), so the figure points to it. | Do not attach the hierarchy chart to classification questions. Either mark both text-sufficient, or draw the described figure with tick marks for equal sides and diagonals and right-angle marks, without naming it. |
| g1-l3-006 | accuracy | Medium | It asks about diagonals, but no diagonals are drawn; the chart shows boxes only. | Draw a non-square rectangle with both diagonals, equal-length ticks on the four half-diagonals, and no right-angle mark at the centre. |
| all four | accuracy | Medium | The arrows are broken. All three arrows are one `<path class="arrow">` with three subpaths, so `marker-end` renders only once, on the rhombus→square curve. The parallelogram connector `M260 132 H330` stops 15 px short of the rectangle box (x = 345) at y = 132, which is between the rectangle (y 65–120) and rhombus (y 195–250) boxes. It has no arrowhead and no parallelogram→rhombus branch. Kite, trapezium and "other parallelogram" (codes 4–6) are absent, although the lesson alt text says "kite and trapezium shown separately". | Use separate `<path>` elements: parallelogram→rectangle `M260 120 L345 95`, parallelogram→rhombus `M260 145 L345 220`, rectangle→square, rhombus→square, each with its own marker. Add separate kite and trapezium boxes, or change the alt text. |

### D-05 · `exterior` template

Assets: `assets/g1-l1-005-diagram.svg`, `assets/g1-l3-007-diagram.svg`,
`assets/g1-l5-003-diagram.svg`, and lesson asset `assets/g1-lesson-06-exterior.svg`.

| Key | Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- | --- |
| all four | accuracy | High | The exterior-angle arc is mismarked. At vertex (390, 70), the arc `M390 105 A35 35 0 0 1 425 70` starts directly below the vertex, inside the hexagon, and sweeps 90° to the extension. The true exterior angle, between the extension (towards (520, 70)) and side (390, 70)→(470, 175), is 52.7°. The arc crosses the side into the interior angle. The hexagon is also not regular: the interior angle there is 127.3°, where a regular hexagon's exterior angle is 60°. | Use a regular hexagon centred at (325, 175) with circumradius 105: vertices (377.5, 84.1), (430, 175), (377.5, 265.9), (272.5, 265.9), (220, 175), (272.5, 84.1). Extend the top side beyond (377.5, 84.1) to (480, 84.1). Draw the arc from the extension point (412.5, 84.1) to (395, 114.4), radius 35, the 60° wedge between the extension and the side towards (430, 175). |
| g1-l1-005 | accuracy | Medium | A triangle question shows a hexagon. | Draw a triangle, or mark the item text-sufficient. |
| g1-l5-003 | accuracy | Medium | Two related regular polygons are described, but one hexagon is shown. | Draw two regular polygons with exterior angles labelled 2k and 3k (no side counts), or mark it text-sufficient. |
| g1-l1-005, g1-l3-007 | accuracy (method leak) | Low | The panel "sum = (n−2)×180°" is the solution formula. | Remove the formula panel from question diagrams; keep it in the lesson figure only. |

### D-06 · `construction` template

Assets: `assets/g1-l1-006-diagram.svg`, `assets/g1-l2-007-diagram.svg`,
`assets/g1-l3-008-diagram.svg`, and lesson asset `assets/g1-lesson-07-construction.svg`.

| Key | Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- | --- |
| all four | neatness | High | The full compass circles (r = 205 at A(110, 245) and B(430, 245)) are clipped by the viewBox (bounding boxes −95…315 and 225…635 by 40…450). Their tops cross the heading (40 px of stroke inside the heading box on l1-006, l3-008 and lesson 07; it touches on l2-007). | Replace the full circles with short arcs (about ±20°) around the two intersection points only, and move the figure down 20 px. |
| all four | accuracy | Medium | The perpendicular bisector `V55–310` does not reach the lower arc intersection at (270, 373), so the construction evidence is incomplete. The right-hand "equilateral" triangle has sides 170, 170 and 174.9, and its arcs are not centred on the base endpoints (an r = 170 arc through (690, 95) cannot be centred at (780, 245), which is 174.9 away). Only C is labelled, so the base vertices are unnamed. | With r = 180, the intersections are (270, 162.5) and (270, 327.5); run the bisector from 140 to 350. Make the triangle exactly equilateral, apex (695, 97.8) for base 610–780, with arcs centred on the base endpoints. Label the base vertices. |
| g1-l3-008 | accuracy | Medium | SSS with AB = 5, AC = 6, BC = 7 is drawn as an equal-arc equilateral construction, which suggests equal radii, and no lengths are labelled. | Draw AB = 5 units with an arc of radius 6 centred at A and an arc of radius 7 centred at B. Label AB = 5 cm and BC = 7 cm. Leave the A-arc radius unlabelled, because that is the asked value. |
| g1-l1-006 | accuracy | Low | The 8 cm segment and the midpoint are not labelled. | Label AB = 8 cm and the crossing point M. Do not label 4 cm. |
| g1-l2-007 | accuracy (answer leak) | Medium | The heading prints "Constructing a sixty-degree angle", and the answer is 60. No angle is marked at the ray's endpoint. | Fix the title (C-07). Mark the unknown angle at the endpoint as x. |

### D-07 · `polygons` template

Assets: `assets/g1-l1-009-diagram.svg`, `assets/g1-l3-004-diagram.svg`,
`assets/g1-l5-005-diagram.svg`, and lesson asset `assets/g1-lesson-04-polygons.svg`.

| Key | Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- | --- |
| g1-l5-005 | accuracy | High | The question is about kite ABCD (AB = AD, CB = CD, A = 70°, C = 110°). The figure shows a triangle, a trapezium labelled "quadrilateral" and a hexagon, with no kite, no vertex letters and no angles. | Draw kite ABCD with A at the top and C at the bottom, and axis AC. Add equal-side ticks on AB/AD (one tick) and CB/CD (two ticks). Mark A = 70° and C = 110°. Mark B as x. Do not mark 90°. Check the drawn angles roughly match: B = D = 90° means the kite is cyclic. |
| g1-l1-009, g1-l3-004 | accuracy | Medium | A near-equilateral triangle (base 200, sides 201.6, so about 60°/60°/60°) is drawn with no angle labels. For l1-009 the angles are 50°, 60° and x (70°); for l3-004 they are x, x + 20, x + 40 (40°, 60°, 80°). The trapezium and hexagon are irrelevant. | Draw one triangle with roughly the stated angles and label the given angles and x. Remove the other two shapes. |
| lesson 04 | accuracy | Medium | The alt text promises "a triangle, parallelogram, trapezium and regular hexagon with standard equality and parallel markings". There is no parallelogram and there are no markings, and the trapezium is captioned "quadrilateral". | Add the parallelogram and the tick and arrow markings, and caption the trapezium. Alternatively, correct the alt text. |
| all four | neatness | Low | The captions are left-aligned at fixed x values, so they sit off-centre under their shapes (for example "triangle" is centred at 151 under a shape centred at 180). | Use `text-anchor="middle"` at each shape's centre x. |

### D-08 · All 28 diagrams: phone readability and metadata

| Category | Severity | What is wrong | Fix |
| --- | --- | --- | --- |
| neatness | High | The canvas is 940 × 390 with 17 px labels, a 22 px heading and a 13 px note. At a 390 px phone width (scale 0.415) these render at about 7.1 px, 9.1 px and 5.4 px, which the 390 px renders confirm are unreadable. | Author at a phone-first viewBox (for example 480 × 360), or keep 940 wide with labels of at least 34 px (about 14 px on a phone). Drop the in-image heading, which repeats the question title. |
| accuracy | Medium | All 21 question alt texts are "Schematic for {title}. Not drawn to scale. Stated measures include …" and describe nothing that is drawn. | Generate the alt text from the drawn elements. |
| accuracy | Low | The lesson SVGs other than lesson 01 r3 have no "not drawn to scale" note or `not_to_scale` flag, which the geometry standard asks for. | Add both. |

---

## Root-cause patterns

1. **Question-blind templates.** All 28 diagrams come from
   `scripts/recalibrate_geometry_content.py`. `OUTCOME_KIND` maps the outcome code to one
   of seven kinds, and `svg_shape(kind)` returns a fixed SVG string. No value, label or
   figure from the question reaches the renderer; only the `<title>` heading and `<desc>`
   change (`svg_document`). Every question diagram is therefore the lesson's reference
   figure under a new heading. This explains every "does not depict the question" finding
   (21 question diagrams, plus D-02, D-04, D-05 and D-07 leaking method or answer through
   their reference panels).
2. **Template defects copy to every use.** Each defect in a template string affects
   exactly four assets (three questions and one lesson):
   - `angle_types`: label and arc overlap (4 assets, including lesson 01).
   - `exterior`: the mismarked exterior arc and irregular hexagon (4).
   - `construction`: clipped circles colliding with the heading, a short bisector and a
     non-equilateral triangle (4).
   - `quadrilateral`: one `marker-end` on a multi-subpath path, and a disconnected
     connector (4).
   - `parallel`, `intersection`, `polygons`: unattached labels and mismatched alt text
     (12).
3. **Alt text and metadata are synthesised, not described.** `recalibrate_questions()`
   builds the alt text by regex-extracting the first five measures from the prompt, so it
   claims measures the SVG does not contain. `asset()` adds `angle_measures` only for
   `angle_types` (always 60/90/120/240) and records no other dimensions.
4. **Diagram selection is not need-based.** `recalibrate_questions()` picks, per
   outcome, the first item at difficulty 1, 3 and 5 (then 2 and 4) until three are
   chosen. The other 83 receive the same boilerplate `text_sufficient` reason in
   `diagram_audit.json`. That is why spatial items such as g1-l3-026 remain text-only
   while the triangle-sum item g1-l1-005 got a hexagon.
5. **The validator cannot see any of this.** `geometry_diagram_issues()` checks only:
   - `angle_types` ray-versus-label geometry (which passes, because the 60/90/120/240
     strip is internally consistent);
   - angle markers declared in `generation_spec` (none in G1); and
   - opt-in `forbidden_visible_labels` (none in G1).

   It has no check for question/diagram agreement, text-on-stroke collisions, viewBox
   clipping, markers on multi-subpath paths, or minimum rendered font size. Adding the
   collision, clipping and font-size checks used in this audit (bounding box against
   sampled stroke points, viewBox containment, computed font size × 390/940) would catch
   D-01, D-06 and D-08 automatically. Making `forbidden_visible_labels` mandatory
   (populated with the canonical answer) would catch D-06 l2-007.
6. **Likely wider impact (not audited here).** The same script generated the question
   diagrams for Secondary 1 G5 (15) and Secondary 2 G2 (15). A spot check found that each
   bank's SVG bodies collapse to five distinct template bodies, each used three times. The
   same question-blind pattern is therefore very likely there too, but those 30 diagrams
   were not rendered or viewed in this audit.

### Text-only questions where a diagram would clearly help

Every text-only decision in `diagram_audit.json` carries the same boilerplate reason. On
reading them, these items would clearly benefit from a figure:

| Key | Why a figure would help |
| --- | --- |
| g1-l3-026 | Two transversals, one perpendicular to the other; the spatial relationship drives the answer. |
| g1-l3-005 | Which vertex's exterior angle is meant is ambiguous in text (C-11). |
| g1-l4-011 | Diagrams from one vertex make n − 3 visible. |
| g1-l3-015 | Arcs that fail to meet at r ≤ 5 versus r > 5. |
| g1-l4-008 | The two mirror-image intersection points. |
| g1-l3-012, g1-l3-020 | Kite diagonals and which one is the symmetry axis. |
| g1-l2-026 | Which pair is acute. |

g1-l5-001 has a diagram but needs a correct one (D-03).

## Not verified

- I did not judge whether the remaining 83 text-only decisions are right beyond the list
  above.
- I did not test learner-facing rendering inside the actual app shell (CSS scaling,
  dark mode). Images were rendered standalone in Chromium.
- The four superseded, unreferenced SVGs were not reviewed.
- The Secondary 1 G5 and Secondary 2 G2 diagrams were only spot-checked for template
  reuse, not rendered.
- Font metrics come from Chromium's fallback for `system-ui` in this container. Exact
  overlap distances may differ by a few pixels on learner devices, but the overlaps
  reported (8–40 px of stroke inside label boxes) exceed that margin.
- No rendered images or scripts were committed. The rendering and checking scripts lived
  only in the session scratch directory.
