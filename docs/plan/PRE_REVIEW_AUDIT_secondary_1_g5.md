# Secondary 1 G5 (Mensuration) technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_1/g5/v1/`
(batches B001–B004) and all five G5 lessons (`g5-lesson-01` to `g5-lesson-05`), which are
stored under `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/` and attached to
unit `g3-sec1-g5` in that folder's `course.json`.

**Decision boundary:** this audit only reports findings. No question, lesson, SVG, manifest,
claim or review state was changed, and no approval was recorded. All 104 questions are
`draft`, all four batches are `ready_for_review` with Mathematics and editorial review still
`pending`, and all five lessons are `draft`. No content in scope has been approved.

**Models and standards used:** `N2_CALIBRATION_PRE_REVIEW_AUDIT.md` (audit model),
`LESSON_NOTES_CONTENT_STANDARD.md` and `GEOMETRY_CONTENT_STANDARD.md` (current standards).
Audience: students preparing for the Sec 3-entry ASEAN Scholarship test.

## Coverage counts

| Item | Count | Notes |
| --- | ---: | --- |
| Questions checked | 104 | 104 parts; outcomes 5.1–5.5; difficulties 1–5 (21/31/31/16/5) |
| Lessons checked | 5 | 8 sections each, 3,642–4,065 characters of section JSON |
| Diagrams referenced | 20 | 15 question SVGs and 5 lesson SVGs |
| Diagrams rendered and viewed | 20 | All 20 viewed at 940 px and at 390 px phone width |
| Text-only questions reviewed against `diagram_audit.json` | 89 | |

All 15 review-packet SVG copies (`review_packets/*/assets/`) are byte-identical to the bank
assets. Every SHA-256 in the JSON matches its file, and every `asset_ref` resolves.

Automated validation passes: `question-bank validate …/secondary_1/g5/v1` reports 0 errors
and 0 warnings, and `question-bank course-validate` reports 0 issues. The diagram defects
below show that a passing validator does not mean a diagram is correct (see root cause RC5).

## Checks performed

- Recomputed all 104 canonical answers from the prompts in an independent script
  (sympy/fractions, π = 22/7 where stated) before reading the worked solutions. Result:
  **0 mismatches**.
- Checked each worked solution, mark allocation, accepted answer and stated condition.
- Checked outcome and difficulty fit against the blueprint's difficulty definitions and the
  Secondary 1 course sequence (`course.json`).
- Checked both hint stages for answer leakage. No hint contains a canonical answer. Hint
  boundary issues are listed under C-10.
- Compared contexts, numbers and operation patterns across the bank and the lessons to find
  semantic duplicates.
- Checked wording, units, number formatting and currency against both the N2 audit rules and
  the current audience standard.
- Recomputed every lesson worked example and active-recall answer. All are correct.
- Rendered all 20 SVGs with Playwright Chromium into a temporary directory outside the repo
  (no images committed). Looked at each image at full size and at 390 px width, then checked
  SVG coordinates and text positions against the question and lesson text.
- Traced the diagram defects to `scripts/recalibrate_geometry_content.py` and
  `question_bank/src/question_bank/geometry_validation.py`.

Severity scale: **Critical** means a wrong answer or an unsolvable item. **Major** means
ambiguous or contradictory content, content outside the course's scope, or a misleading
diagram. **Minor** means quality, consistency or wording. **Info** means a judgement call
for reviewers.

---

## Part 1: Content findings

No canonical answer, accepted answer or final worked-solution value is wrong.

### Item-level findings

| ID | Stable key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-01 | g5-l3-011 | Major | The prompt says the rectangles are "joined along an edge of length x cm". The edges are 9, 7, 6 and 5 cm, but the canonical answer is x = 3, which is not an edge of either rectangle. The perimeter equation 54 − 2x = 48 only holds if x is a *partial* contact length, which contradicts the wording. | Change the outside perimeter to **44 cm**, giving x = 5: the 5 cm edge of the smaller rectangle lies entirely along a side of the larger one, and 54 − 2(5) = 44. Update the canonical answer to 5, H2 to "Solve 32 + 22 − 2x = 44" and the solution. Alternatively, reword so that the rectangles touch along a common segment of length x cm. |
| C-02 | g5-l4-005 | Major | "Its area equals that of a 20 cm by 10 cm parallelogram." A parallelogram described by two lengths is ambiguous: with side lengths 20 cm and 10 cm, the area is anything up to 200 cm². This contradicts lesson 01, which warns against using a sloping side as the height. | Reword as "a parallelogram with base 20 cm and perpendicular height 10 cm". The answer x = 22 is unchanged. |
| C-03 | g5-l4-015 | Major | "Its volume plus its total surface area is 420 when numerical values are added." Adding cm³ to cm² is dimensionally meaningless, and lessons 02–03 state that measures with different units cannot be combined. | Give the surface area alone: "Its total surface area is 220 cm². Find its volume in cm³." This gives 40 + 18x = 220, so x = 10 and V = 200, which keeps a two-stage method suitable for d4. Update the canonical answer to 200 and update the hints and solution. |
| C-04 | g5-l4-001, g5-l4-010 | Major (judgement call) | Both items require solving a quadratic by factorisation: (x − 6)(x + 8) = 0 and (x − 6)(x + 14) = 0. The Secondary 1 course teaches only linear expressions (N5.6–N5.8) and linear equations (N7.1–N7.4). Quadratic factorisation is Secondary 2 content. These G5 items assume a skill the course has not taught. | Use linear versions that keep the answer: **l4-001** "a square of side 6 cm and a rectangle 6 cm by (x + 4) cm … total area 96 cm²", giving 36 + 6x + 24 = 96 and x = 6. **l4-010** "A rectangle measures 12 cm by (x + 3) cm. A 5 cm by 3 cm corner is removed, leaving 93 cm²", giving 12x + 21 = 93 and x = 6. Reviewers may keep the quadratics because the Sec 3-entry test assumes Secondary 2 algebra, but that conflicts with the Secondary 1 lesson sequence. |
| C-05 | g5-l4-001 | Minor | The solution goes from 2x² + 4x − 96 = 0 straight to (x − 6)(x + 8) = 0 without showing the division by 2. | Insert the step x² + 2x − 48 = 0, or remove it if C-04 is applied. |
| C-06 | g5-lesson-02 / g5-l2-002 | Major | Lesson 02 worked example 2 ("A 14 m by 10 m rectangle has a 6 m by 4 m corner removed … area = 116 m²") solves practice item l2-002 with the same numbers and answer. | Change the lesson example numbers, for example 15 m × 9 m minus a 5 m × 3 m corner (area 120 m², perimeter 48 m). |
| C-07 | g5-l1-013 | Minor | The item is allocated to 5.2 ("composite plane figures") but asks for the perimeter of a single rectangle. | Make it composite, for example the perimeter of a 12 cm × 7 cm rectangle with a 3 cm × 2 cm corner removed (answer 38 cm, which tests the same corner-cut insight). Otherwise reallocate it. |
| C-08 | g5-l1-006, g5-l1-016, g5-l1-021 | Minor | These are three 5.5 d1 items that only add two given volumes (120 + 80, 150 + 90, 308 + 420), with no composite-solid reasoning and the same structure. Lesson 05 worked example 1 (180 + 75) repeats the pattern. | Keep one. Change the others to compute one component volume from dimensions before adding, or to subtract a removed block. |
| C-09 | g5-l3-027 | Minor | The title is "Walkway beside two regions", but the prompt has no walkway. | Retitle, for example "Planting area in a park section". |
| C-10a | g5-l4-011 | Minor | The title "Number of slabs from mixed units" does not match the prompt, which has one slab and counts blocks. "How many blocks have the same total volume?" is awkward. | Title: "Blocks with the same volume as a slab". Prompt: "How many such blocks have a total volume equal to the slab's volume?" |
| C-10b | g5-l3-010, g5-l2-021 | Minor | Title and prompt do not match. l3-010's title says area, but it asks for a dimension. l2-021's title says box, but the prompt says tank. | Align each title with its prompt. |
| C-10c | g5-l3-023 | Minor | "find their total displacement" is not standard wording. | "find the total volume of water displaced". |
| C-10d | g5-l3-016 | Minor | H2 ends "check their sum carefully", which reads like a reviewer note. | "…then subtract twice the 12 cm² contact area." |
| C-10e | g5-l3-003 | Info | Square tiles of 0.5 m² have side √0.5 ≈ 0.707 m, so they cannot cover a 16 m × 12 m L-shape exactly. The answer relies on the "no wastage" assumption. | Use 0.25 m² (0.5 m × 0.5 m) tiles, giving 648 tiles, or rectangular 1 m × 0.5 m tiles. |
| C-11 | g5-l2-012 | Info | `calculator_allowed: true`, while all other d1–d2 items are false and the blueprint default is true. | Make the d2 setting consistent. |

### Difficulty alignment (pattern)

The blueprint defines d5 as "complex non-routine synthesis requiring several ideas, sustained
reasoning, or proof" and d4 as "an unfamiliar problem requiring method selection, constraints,
or justification".

| Severity | Stable keys | Evidence | Proposed correction |
| --- | --- | --- | --- |
| Major | g5-l5-001 to g5-l5-005 | None of the five d5 items meets the definition. l5-003 is two routine steps, l5-004 is a box volume then 75% then a division, and l5-005 is cube minus cylinder, the same method as d4 item l4-008. l5-001 and l5-002 are a single linear equation followed by substitution. | Rewrite as non-routine items, for example optimisation under constraints, a reverse problem with two unknowns, or justifying which of two containers holds more. Otherwise relabel them d3/d4 and author new d5 items. |
| Minor | g5-l4-003, g5-l4-004, g5-l4-006, g5-l4-007, g5-l4-011 | Each is a familiar two-step routine (convert then divide; subtract then divide). That is d3 at most. | Raise the demand, for example with an unknown dimension in two units or a constraint check, or relabel them. |
| Minor | g5-l3-026 | 120 − 7 × 6 is one product and one subtraction, which is d1/d2. | Relabel, or require the trapezium area to be computed from dimensions. |
| Minor | g5-l2-002 vs g5-l1-008; g5-l2-016 vs g5-l1-002 / g5-l1-012; g5-l2-004, g5-l2-005 vs g5-l1-005, g5-l1-015 | The d2 items have the same structure and step count as the d1 items. | Differentiate the d2 items, for example with an inverse problem or mixed units. |

### Semantic duplicates (same structure and method; numbers differ)

| Cluster | Stable keys | Severity | Proposed correction |
| --- | --- | --- | --- |
| Add two given volumes | g5-l1-006, g5-l1-016, g5-l1-021 (+ lesson 05 WE1) | Minor | See C-08. |
| Two cuboids from dimensions, add volumes | g5-l2-006, g5-l2-014 (also g5-l3-024 with a 75% layer, g5-l4-004 inverse) | Minor | Vary one item, for example an exposed-surface or capacity-in-litres variant. |
| Cuboid minus rectangular through-hole | g5-l2-007, g5-l2-031 | Minor | Change one to a hole that does *not* pass through, or ask for surface area. |
| Cuboid/cube minus cylindrical hole, r = 3.5 cm, π = 22/7 | g5-l4-008 (d4), g5-l5-005 (d5) | Minor | Same method at two difficulty levels. See the difficulty findings. |
| Two identical cubes joined face to face, exposed area | g5-l3-008, g5-l3-031 | Minor | Change l3-031 to three cubes in an L, or to unequal solids. |
| Cylinder height from volume, r = 7 | g5-l2-028 (d2), g5-l3-006 (d3); g5-l4-006 (equal volume, r = 7) | Minor | Vary the radius or the unknown, for example finding the radius as in l3-019. |
| Direct parallelogram bh | g5-l1-001, g5-l1-007, g5-l1-017 | Info | Acceptable at d1, but one could use a figure where the sloping side is also given as a distractor. |
| Trapezium 8 cm / 14 cm, h = 6 cm reused | lesson 01 WE1, g5-l3-001, g5-l3-027 (and 8/14, h = 5 in g5-l2-019) | Minor | Vary the dimensions so that the lesson example is not reused verbatim inside practice items. |

### Hint boundaries (pattern; judgement call)

- **Minor / Info.** In 50 of 104 parts, H2 is a fully specified operation such as "Multiply 8 by
  5", "Divide 84 by 12" or "Calculate 70 − 12". The canonical answer never appears in a
  hint, but for d1–d2 items H2 leaves only one arithmetic operation. The house policy
  ("explicit next method or intermediate setup without giving the final answer") is met in a
  literal sense. Reviewers should decide whether that is acceptable.
- **Minor.** For these multi-mark items, H2 gives every intermediate value, so only a single
  addition or subtraction is left and all method marks are given away: g5-l2-019, g5-l3-023,
  g5-l3-024, g5-l3-027, g5-l3-030, g5-l4-008, g5-l4-011, g5-l4-012. Proposed correction: give
  one component value only, for example "The trapezium area is 55 m²; now find the rectangle
  area".

### Mark schemes (pattern)

- **Minor.** 51 multi-mark parts have a single solution step that carries all the marks as an
  A mark, with no M marks. Examples: g5-l5-005 is A5 on one line; g5-l4-003, g5-l4-007,
  g5-l4-008, g5-l4-011, g5-l4-012 and g5-l4-016 are each A4; g5-l3-001, g5-l3-005,
  g5-l3-007 and others are A3. The full list is in the appendix. If solution steps are shown
  to learners or used for partial-credit review, split them into M (method) and A (accuracy)
  steps, as items such as g5-l3-002 and g5-l4-009 already do.

### Wording, audience and convention conflicts

| ID | Stable keys | Severity | Evidence | Note / proposed decision |
| --- | --- | --- | --- | --- |
| W-01 | g5-l2-009, g5-l3-004, g5-l3-013, g5-l3-015, g5-l3-031 | Minor (conflict to resolve) | Money is written as a bare `$` ("Material costs $3 per m²"). The N2 audit made **S$** mandatory for money items. The current lesson-notes standard says the audience is learners across Indonesia and Southeast Asia, that the Singapore syllabus is "a calibration and coverage reference" and "does not define the learner's country", and that contexts should "work across Southeast Asia". | The two documents conflict. Applying S$ follows the N2 rule but signals a Singapore context. A bare `$` meets neither rule. Reviewers should choose one convention: S$ everywhere, or currency-neutral wording such as "costs 3 dollars per m²" or "3 units of money". This report does not choose. |
| W-02 | All items | Info | The N2 audit checked "Singapore/British English". The G5 content uses British spellings (metre, centimetre), which are also acceptable international English. | No conflict in practice. |
| W-03 | g5-lesson-04 vs bank | Minor | Lesson 04 groups digits with commas ("10,000", "1,000,000", "24,000"). The bank uses spaces ("45 000", "1 000 000"). | Use one convention. The bank's space grouping matches the N2 and SI-style convention. |

### Lesson findings

All five lessons meet the structural gate: 8 sections, 2 worked examples, active recall, a
summary, at least 3,000 characters and one diagram. Every worked example and active-recall
answer recomputes correctly.

| ID | Stable key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| L-01 | g5-lesson-01 to 05 | Minor | In every lesson, the verification note on the first worked example is the same boilerplate: "The result uses compatible units and agrees with the dimensions and component structure." It verifies nothing. The geometry standard requires worked examples "with explicit reasoning and verification". These examples also have only two steps (formula, then answer). | Write a real check for each lesson. For example, lesson 01 WE1: "66 lies between 8 × 6 = 48 and 14 × 6 = 84". Add one reasoning step to each first example. |
| L-02 | g5-lesson-01 to 05 | Minor | Every summary ends with the same appended sentence: "…use the diagram markings to check that every correspondence is consistent." "Correspondence" refers to congruence and similarity, not mensuration, and the G5 diagrams have no markings. The script adds this sentence at `scripts/recalibrate_geometry_content.py:421` for all geometry lessons. The first sentence of the summary also mentions "squared or cubed" in the area-only lessons 01–02. | Write a summary for each outcome. |
| L-03 | g5-lesson-02 | Major | See C-06: worked example 2 duplicates practice item g5-l2-002. | See C-06. |
| L-04 | g5-lesson-03 | Minor | 12 bank items use "π = 22/7", but the lesson never shows the 22/7 convention or when to use it. Its cylinder example is "in terms of π". | Add one worked example or a short explanation using π = 22/7 with r = 7 (for example, base area 154 cm²). |
| L-05 | g5-lesson-04 | Minor | The objectives cover only cm² ↔ m² and cm³ ↔ m³. Practice items g5-l2-029 (mm² → cm²) and g5-l2-030 (mm³ → cm³) and worked example 2 (litres) use units the lesson does not teach. The outcome text says "including cm² and m²…", so mm is in scope. | Add one sentence and one recall item on mm² and mm³ (×100 and ×1 000), and define 1 litre = 1 000 cm³ before using it. |
| L-06 | g5-lesson-04 | Minor | "A linear conversion factor is applied once, a square-unit factor twice and a cubic-unit factor three times" confuses the factor with the unit. | "For lengths, apply the factor once; for areas, apply it twice (square it); for volumes, apply it three times (cube it)." |
| L-07 | g5-lesson-01 | Minor | "Choose either parallel side as the parallelogram base" is unclear, because a parallelogram has two pairs of parallel sides. | "Any side can be the base; pair it with the perpendicular height to that side." |
| L-08 | g5-lesson-01 to 05 | Minor | Each "Read the diagram" section describes properties that the diagram does not show (right angles, highlighted lengths, a shaded contact face). | Fix the diagrams (Part 2), or make the text match what is drawn. |

---

## Part 2: Diagram findings

**Summary.** All 20 diagrams come from five fixed templates, one per `diagram_kind`. Apart from
the title, every question diagram is byte-identical to the other diagrams of its kind and to
the matching lesson diagram. No diagram carries any question-specific measurement, variable or
unit. Six of the 15 question diagrams show a different object or relationship from the one in
the question. The stem tells learners to "Use the schematic together with the measurements
stated in the question", but none of the schematics shows a measurement.

No diagram reveals a requested answer. None of them carries numeric labels.

### Question diagrams

All paths are relative to `backend_resources/question_bank/g3_math/secondary_1/g5/v1/`.

| ID | Stable key | Asset path | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- | --- |
| D-01 | g5-l1-001 | assets/g5-l1-001-diagram.svg | Accuracy | Major | The question is one parallelogram (8 cm, 5 cm), but the diagram also draws an unrelated trapezium. No measurements are shown. The label "h" is at (125,180), beside the *sloping* side, which crosses x ≈ 121.6 at y = 180, rather than beside the dashed height. That suggests the slant is the height, the misconception the lesson warns against. There is no right-angle mark at the foot of the height. | Draw only the parallelogram. Put "8 cm" under the base and "5 cm" to the right of the dashed height, at about (170,175). Add a 12 px right-angle square at (160,250). |
| D-02 | g5-l1-001 | same | Neatness | Minor | The "h" glyph sits on the sloping edge and is partly hidden by the stroke, which is worse at 390 px. | Move the label off the edge, as in D-01. |
| D-03 | g5-l1-003 | assets/g5-l1-003-diagram.svg | Accuracy | Major | The question is a rectangle (8 × 5) *plus* a separate 3 cm square, so the areas are added. The diagram shows a rectangle with a corner *cut out* and labels "remaining region" and "cut-out", which shows subtraction instead. | Draw an 8 × 5 rectangle with a 3 × 3 square attached along one edge. Label 8 cm, 5 cm and 3 cm, and remove the arrow and the empty rectangle. |
| D-04 | g5-l1-004 | assets/g5-l1-004-diagram.svg | Accuracy | Major | The question is a cuboid (8 × 5 × 3 cm). The diagram shows a pentagonal "house" prism and a cylinder, and no cuboid. | Draw a cuboid in oblique projection with hidden edges dashed and edges labelled 8 cm, 5 cm and 3 cm. Alternatively, mark the item `text_sufficient`. |
| D-05 | g5-l1-005 | assets/g5-l1-005-diagram.svg | Accuracy | Minor | The 4 × 4 grid suggests a factor of 16 rather than 100². No "1 m" or "100 cm" labels are shown. The cube and the arrow from the square to the cube are unrelated to an area conversion and suggest area turns into volume. | Label the square "1 m = 100 cm" on two sides, with a caption such as "100 × 100 small squares". Do not state 10 000 if H2 is meant to give it. Remove the arrow and the cube. |
| D-06 | g5-l1-006 | assets/g5-l1-006-diagram.svg | Accuracy | Minor | The cuboids are drawn as 2D rectangles with no 120 cm³ / 80 cm³ labels. The "removed core" figure is unrelated. The diagram adds no spatial information. | Mark the item `text_sufficient` (preferred), or draw two 3D cuboids labelled 120 cm³ and 80 cm³. |
| D-07 | g5-l1-006 | same | Neatness | Minor | "contact face" (x = 280, y = 175, about 100 px wide) is crossed by the vertical edge at x = 330. A 2 px grey `faint` line is drawn over the 4 px dark edge (M330 190 V285), which looks like a stray double line. | Move the label above the joint with a leader line. Delete the redundant faint path. |
| D-08 | g5-l3-001 | assets/g5-l3-001-diagram.svg | Accuracy | Minor | The two shapes are correct (parallelogram and trapezium), but the labels are the generic "base b", "h", "a" and "b" instead of 12 cm, 6 cm, 8 cm, 14 cm and 6 cm. The "h" labels sit on the sloping sides, as in D-01, and there are no right-angle marks. | Label each dimension with its value. Move the h labels next to the dashed lines and add right-angle squares. |
| D-09 | g5-l3-003 | assets/g5-l3-003-diagram.svg | Accuracy | Minor | The L-shape matches, but 16 m, 12 m, 6 m and 5 m are not labelled. The arrow and the empty rectangle captioned "decompose or subtract" are meaningless. | Label the outer sides 16 m and 12 m and the cut-out 6 m and 5 m. Remove the arrow and the rectangle. |
| D-10 | g5-l3-003 | same | Neatness | Minor | "remaining region" (starting at x = 170, 17 px bold) runs up to the vertical edge at x = 310. The dashed cut-out top edge (M310 170 H470) is drawn over the solid boundary segment, so the dashes appear on a dark line. | Shorten the label to "L-shape" or move it to x ≈ 150, y ≈ 120. Remove the duplicated dashed segment. |
| D-11 | g5-l3-005 | assets/g5-l3-005-diagram.svg | Accuracy | Major | The question's cross-section is a **right triangle** with sides 3, 4 and 5 cm. The diagram shows an isosceles triangle on a rectangle (a pentagonal prism), with an internal line at y = 235 that makes it look like a composite solid. There is no right-angle mark and no labels. A cylinder is added for no reason. | Draw a right triangular prism. Mark the right angle on the end face, label the sides 3 cm, 4 cm and 5 cm, and label the length 10 cm. Remove the cylinder. |
| D-12 | g5-l3-007 | assets/g5-l3-007-diagram.svg | Accuracy | Minor | The alt text and `<desc>` say "Stated measures include 2.4 m², **500 cm²**", but the question says 6 500 cm² (see RC3). The square, the cube and the arrow carry no information about two sheets. | Correct the alt text to "2.4 m², 6 500 cm²". Mark the item `text_sufficient`, since a diagram adds no spatial information. |
| D-13 | g5-l3-008 | assets/g5-l3-008-diagram.svg | Accuracy | Major | The question has **two identical 4 cm cubes** joined face to face. The diagram shows two different-sized 2D rectangles (230 × 135 and 170 × 95), so the contact appears partial. This misleads the "subtract two full faces" step. The "removed core" figure is unrelated. | Draw two equal cubes in oblique projection, shade the shared face, and label one edge 4 cm. Remove the core figure. |
| D-14 | g5-l3-008 | same | Neatness | Minor | Same label collision and stray faint line as D-07. | As D-07. |
| D-15 | g5-l5-001 | assets/g5-l5-001-diagram.svg | Accuracy | Major | The labels "a", "b", "base b" and "h" conflict with the question's variables x, (x + 4), (x + 3), 10 and 8. "b" is not defined in the question, and the same letter is used for different lengths in both shapes. | Label the trapezium sides "x cm" (top) and "(x + 4) cm" (bottom), with height "10 cm". Label the parallelogram base "(x + 3) cm" and height "8 cm". Add right-angle marks. |
| D-16 | g5-l5-002 | assets/g5-l5-002-diagram.svg | Accuracy | Major | The question has two rectangles (x × 8 and (x − 2) × 5) **joined** along a full 5 cm edge, so the perimeter is P₁ + P₂ − 2(5). The diagram shows a rectangle with a corner **cut out**. The perimeter of that shape equals the bounding rectangle's perimeter, so the picture points to the wrong method for this perimeter question. | Draw an x × 8 rectangle with an 8 × 5 rectangle attached so that its 5 cm edge lies on the larger rectangle's side. Label x cm, 8 cm, (x − 2) cm and 5 cm, and mark the shared edge. Do not reveal x = 10. |
| D-17 | g5-l5-003 | assets/g5-l5-003-diagram.svg | Accuracy | Minor | The unrelated prism is drawn. The cylinder does not show that the tank is open. The back half of the bottom ellipse is solid where it should be dashed (hidden), and the radius of 7 cm is not labelled. | Draw only the open cylinder: top rim with inner shading, bottom back arc dashed, and a radius line labelled 7 cm. Remove the prism. |
| D-18 | g5-l5-004 | assets/g5-l5-004-diagram.svg | Accuracy | Major | The question is about a box (1.2 m × 80 cm × 50 cm) packed with 10 cm cubes. The diagram shows a 4 × 4 grid square, an arrow and a cube, and no box. | Draw a cuboid labelled 1.2 m, 80 cm and 50 cm, with one small cube labelled 10 cm in a corner. Remove the grid square and the arrow. |
| D-19 | g5-l5-005 | assets/g5-l5-005-diagram.svg | Accuracy | Minor | The "cube" is a 200 × 185 front-view rectangle, which is not square. The hole's ellipses straddle the top and bottom edges, mixing a 2D front view with 3D rims, so the hole looks as if it sticks out of the solid. The joined-cuboid figure is unrelated, and 14 cm and 3.5 cm are not labelled. | Draw a cube in oblique projection with a circular opening on the top face, dashed hidden cylinder sides, and labels 14 cm (edge) and 3.5 cm (radius). Remove the left-hand figure. |
| D-20 | all 15 | all question SVGs | Neatness | Major | At 390 px width the 940-wide viewBox scales by 0.41. Labels (17 px) render at about 7 px, the note (13 px) at about 5 px and the heading (22 px) at about 9 px, which is not readable on a phone. Most of these templates put two side-by-side figures in the viewBox. | Use one figure per question diagram. Use a font of at least 30 px in a 940 px viewBox (at least 12 px rendered), or a narrower viewBox (for example 600 × 400) with labels of at least 20 px. |
| D-21 | all 15 | all question SVGs | Accuracy | Minor | The alt text and `<desc>` give the question's numbers ("Stated measures include 8 cm, 5 cm"), but none of these appear in the drawing. They list given totals such as 260 cm² as "measures", miss algebraic labels, and repeat values ("8 cm, 5 cm, 5 cm, 120 cm²" for l5-002). | Generate the alt text from the labels actually drawn, for example "Parallelogram with base 8 cm and dashed perpendicular height 5 cm, right angle marked". |

### Lesson diagrams

All paths are relative to `backend_resources/courses/g3_math/secondary_1/n1/v1/`.

| ID | Lesson key | Asset path | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- | --- |
| D-22 | g5-lesson-01 | assets/g5-lesson-01-area.svg | Accuracy | Major | The alt text says "bases and perpendicular heights clearly marked", but there are no right-angle marks. The "h" labels sit against the sloping sides at (125,180) and (540,180), which contradicts the lesson text ("Do not use a sloping side as the height"). The same letter "b" is used for the parallelogram base and for the trapezium's bottom parallel side. | Put the h labels next to the dashed segments, add right-angle squares at (160,250) and (575,250), and label the slant "s (not used)" as a distractor. Label the trapezium sides a and b and the parallelogram base b. |
| D-23 | g5-lesson-01 | same | Neatness | Minor | The "h" labels overlap the slanted strokes. | As D-22. |
| D-24 | g5-lesson-02 | assets/g5-lesson-02-composite_plane.svg | Accuracy | Minor | The arrow points to an empty rectangle captioned "decompose or subtract", which has no meaning. The lesson's main perimeter idea (trace the outside boundary; ignore internal edges) is not shown. | Replace the right-hand figure with the same L-shape split by a dashed internal line into two rectangles, with the outside boundary highlighted and labelled "perimeter: outside edges only". |
| D-25 | g5-lesson-02 | same | Neatness | Minor | "remaining region" runs into the edge at x = 310. The dashed segment is drawn over the solid one at y = 170. | As D-10. |
| D-26 | g5-lesson-03 | assets/g5-lesson-03-solids.svg | Accuracy | Major | The alt text says "A triangular prism and a cylinder with their cross-sections and lengths highlighted". The drawing is a pentagonal "house" prism with an internal line across the end face, and nothing is highlighted. The back arc of the cylinder's bottom ellipse is solid. | Draw a triangular prism with the cross-section shaded and the length labelled ℓ, and a cylinder with r and h labelled and the hidden arc dashed. |
| D-27 | g5-lesson-04 | assets/g5-lesson-04-conversion.svg | Accuracy | Major | The alt text says "A metre square divided into centimetre squares and a metre cube", but the drawing is a 4 × 4 grid with no units, an unlabelled cube, and an arrow that suggests the square turns into the cube. | Label the square "1 m = 100 cm" on both sides with a caption "100 × 100 = 10 000 cm²". Label the cube "1 m = 100 cm" on three edges with "100³ = 1 000 000 cm³". Remove the arrow, or replace it with two separate panels. |
| D-28 | g5-lesson-05 | assets/g5-lesson-05-composite_solid.svg | Accuracy | Minor | The alt text says "Two cuboids joined at a shaded contact face", but the drawing has 2D rectangles and no shading. The cube-with-hole figure has rims straddling the edges and is not square (200 × 185). | Draw 3D cuboids with a shaded contact rectangle and a cube in oblique projection with a top opening, as D-19. |
| D-29 | g5-lesson-05 | same | Neatness | Minor | Same "contact face" collision and stray faint line as D-07. | As D-07. |
| D-30 | all 5 lessons | all lesson SVGs | Neatness | Major | Readability at 390 px is the same problem as D-20. | As D-20. |
| D-31 | all 5 lessons | all lesson SVGs | Accuracy | Minor | Unlike the question SVGs, the lesson SVGs have no "not drawn to scale" note. The geometry standard requires a reminder when a diagram is not drawn to scale. | Add the note, which the regenerated template will do automatically (see RC6). |

### Root-cause patterns

| ID | Root cause | Where | Diagrams affected |
| --- | --- | --- | --- |
| RC1 | **Fixed per-kind templates.** `svg_shape(kind)` returns one hard-coded SVG fragment per `diagram_kind`, and the kind is chosen from `OUTCOME_KIND[primary_outcome]`, not from the question. No question measurements or variables are passed to the renderer, so every 5.2 question gets a cut-out L-shape, every 5.3 question gets a house prism and a cylinder, and so on. | `scripts/recalibrate_geometry_content.py:255-297`, `:497-515` | All 20 (15 questions + 5 lessons). This causes D-01, D-03, D-04, D-05, D-06, D-08, D-09, D-11, D-13, D-15, D-16, D-17, D-18, D-19 and D-21. |
| RC2 | **Defects inside the templates** are copied to every diagram of that kind: `area` puts the h labels on the slants with no right-angle marks; `composite_plane` has a label collision, a dashed-over-solid segment and a meaningless arrow and rectangle; `solids` draws a pentagonal prism with an internal line and a solid hidden arc; `conversion` uses a 4 × 4 grid with an unrelated cube; `composite_solid` has a label collision, a stray faint line, 2D cuboids and mixed-projection rims. | same, `svg_shape` | 4 diagrams per kind (3 questions + 1 lesson) |
| RC3 | **Alt text built by regex from the prompt** rather than from the drawing. The pattern `(?<![A-Za-z0-9.])\d+(?:\.\d+)?\s*(?:cm³\|cm²\|m³\|m²\|cm\|km\|m\|°)` splits digit groups separated by a space ("6 500 cm²" becomes "500 cm²"), ignores algebraic dimensions, does not remove duplicates, and lists values that are never drawn. | `scripts/recalibrate_geometry_content.py:503-512` | 15 question alt texts and `<desc>` elements (D-12, D-21) |
| RC4 | **Mechanical selection of which questions get diagrams.** For each outcome, the script takes the first question of difficulty 1, then 3, then 5, in filename order. Every other question is marked `text_sufficient` with the same boilerplate reason. This is why diagrams were added to items with no spatial content (l1-005, l1-006, l3-007), while spatially demanding items were left text-only (see below). | `scripts/recalibrate_geometry_content.py:469-497`, `:552-561` | 15 diagram choices; 89 `text_sufficient` decisions |
| RC5 | **The validator has no checks for mensuration diagrams.** `geometry_diagram_issues` only checks `angle_types` rays, declared `angle_markers` and declared `forbidden_visible_labels`. No G5 asset declares any of these, so all 20 G5 diagrams pass with nothing checked beyond file existence and checksums. | `question_bank/src/question_bank/geometry_validation.py:41-356` | All 20 |
| RC6 | **The lesson SVGs are stale and the script will not regenerate them.** The current `svg_document` adds a "not drawn to scale" note that the lesson SVGs lack, so they came from an earlier version of the template. `recalibrate_lessons` skips any lesson that already has a `nextscholar-geometry-svg-v1` asset, so fixing `svg_shape` alone will not update the lessons. | `scripts/recalibrate_geometry_content.py:351-357` | 5 lesson diagrams |

**Recommended remediation (for the authoring owner, not done here):** replace `svg_shape(kind)`
with renderers that take parameters for each kind (parallelogram, trapezium, rectilinear
composite, cuboid, right prism, cylinder, joined solids, drilled solid). Each renderer should
take the question's dimensions and labels from a `generation_spec` (for example
`{"shape": "cuboid", "edges": {"l": "8 cm", "w": "5 cm", "h": "3 cm"}}`). Generate the alt text
from the same spec. Extend `geometry_validation.py` to check that each declared label appears
as SVG text, that each label's position is within a set distance of its target segment and
does not cross another segment, that right-angle markers sit at declared feet, and that the
minimum font size scaled to 390 px is at least 12 px. Remove the `continue` skip for lessons,
or bump the revision so that lesson assets are regenerated. Because asset bytes would change,
the regenerated assets need revision-suffixed filenames (`…-r3.svg`), as the geometry
standard requires.

### Text-only questions that a diagram would clearly help (from `diagram_audit.json`)

These are currently `text_sufficient` with the boilerplate reason "all measurements are fully
stated". In each case the spatial arrangement is described in words only, and a figure would
remove real ambiguity or support the key insight:

| Stable key | Why a diagram would help |
| --- | --- |
| g5-l2-011 | The L-shape perimeter depends on which edges are 7, 4, 5 and 6. "top-right corner" plus the hint's edge list needs a picture. |
| g5-l2-026, g5-l3-011 | Joined rectangles: where the shared edge is matters to the perimeter. l3-011 also has the wording defect C-01, which a figure would make obvious. |
| g5-l3-016, g5-l4-012 | Step solid and cube on cuboid: the exposed-face audit is spatial. |
| g5-l2-007, g5-l2-031 | Rectangular tunnel or hole through a cuboid: which dimension the hole runs along. |
| g5-l4-008 | Cylindrical hole drilled through the 10 cm height. |
| g5-l3-018, g5-l4-014 | Uniform border or track: the inner dimension is outer minus twice the width. |
| g5-l2-003, g5-l3-012 | Triangular or trapezoidal prism: which length is the prism length and which the cross-section height. |
| g5-l2-027, g5-l3-020 | Open-top box or cylinder: which faces are counted. |
| g5-l4-010 | Algebraic L-shape: where the 5 × 3 corner sits relative to (x + 5) and (x + 3). |

The audit also recommends changing g5-l1-005, g5-l1-006 and g5-l3-007 to `text_sufficient`,
since a diagram there adds no spatial information.

---

## Not verified / limitations

- All 20 diagrams were rendered with Chromium (Playwright) and viewed. No diagram is left
  unviewed. Rendering used the system-ui font available in the container. On a device with
  wider fonts, the label collisions above (D-02, D-07, D-10, D-14, D-23, D-25, D-29) would be
  the same or worse.
- The deployed lesson, practice and review UIs were not rendered. Phone readability was judged
  by scaling each SVG to a 390 CSS-px container at a device-pixel ratio of 2. The real app may
  add padding or allow zoom.
- Cross-bank semantic duplicates (for example against Secondary 2 G5) were not compared in
  detail. Duplicates were checked within this bank and against the five G5 lessons only. The
  validator's cross-bank duplicate scan passes.
- Whether quadratics (C-04) and the S$ convention (W-01) are acceptable are policy questions
  for the Mathematics and editorial reviewers. Both are reported, not decided.
- KaTeX rendering of LaTeX fragments was not visually checked. The validator reports that all
  fragments parse.

## Appendix: multi-mark parts with a single all-A solution step (51)

g5-l2-001, 002, 003, 004, 005, 006, 007, 010, 011, 012, 013, 014, 015, 016, 017, 018, 019,
020, 021, 022, 023, 025, 026, 027, 028, 029, 030, 031; g5-l3-001, 005, 006, 007, 008, 014,
018, 020, 021, 022, 023, 024, 026, 027, 029, 030; g5-l4-003, 007, 008, 011, 012, 016;
g5-l5-005.
