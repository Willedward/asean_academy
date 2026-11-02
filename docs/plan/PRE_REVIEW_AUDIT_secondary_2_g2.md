# Secondary 2 G2 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in
`backend_resources/question_bank/g3_math/secondary_2/g2/v1/questions/` (batches B001–B004),
the five G2 lessons `g2-lesson-01` to `g2-lesson-05`, and every diagram they reference

**Decision boundary:** this is a technical pre-review only. It records no Mathematics or
editorial approval and changes no content, review state, manifest or claim.

**Standards used:** `LESSON_NOTES_CONTENT_STANDARD.md` (audience: international English for
Southeast Asian learners), `GEOMETRY_CONTENT_STANDARD.md`, and
`GEOMETRY_DIAGRAM_AUTHORING_STANDARD.md`. The format follows
`N2_CALIBRATION_PRE_REVIEW_AUDIT.md`.

## Summary

| Item | Checked | Notes |
| --- | ---: | --- |
| Questions | 104 | All `draft`; every batch shows `mathematics: pending`, `editorial: pending`. No content has been approved. |
| Lessons | 5 | `g2-lesson-01`…`05`, all `draft` rev 2. They are stored in `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/`, which holds the **whole** Secondary 2 course. G2 lessons were identified from `unit_key: g3-sec2-g2` in `course.json`. No other Secondary 2 lesson lists a G2 outcome. |
| Diagrams referenced | 20 | 15 question SVGs and 5 lesson SVGs |
| Diagrams rendered and viewed | **20 of 20** | Rendered with the preinstalled Playwright Chromium at 940 px (native size) and 390 px (phone width) into a scratch directory outside the repo. I viewed every render, using ImageMagick contact sheets, and checked SVG coordinates numerically. |
| Canonical answers recomputed | 104 of 104 | Recomputed independently from the prompt text with Python and SymPy before reading the solutions. **0 mismatches.** |
| Lesson worked examples and recall answers | 15 of 15 | All correct |

The automated checks passed:

- `question-bank validate` on the bank: 0 errors, 0 warnings.
- `question-bank course-validate`: 0 errors, 0 warnings.

These passes are **not** evidence that the diagrams are correct. See root cause R1.

**Headline findings**

1. **The mathematics is correct.** No canonical answer, accepted answer or worked-solution
   result is wrong.
2. **Every one of the 20 diagrams is a generic placeholder.**
   - The 15 question SVGs are five fixed templates, one per outcome, each reused three
     times. Apart from the title, they are byte-identical.
   - No diagram shows any value, variable or vertex label taken from its question.
   - Several diagrams contradict the question: a pentagon question shows triangles, a ×2
     enlargement is drawn as ×3, and figures labelled "congruent" or "similar" are not.
   - One diagram reveals the answer.
   - All text is unreadable at phone width.
3. **Questions are heavily templated.** There are 35 near-duplicate items in 8 families.
   Several items repeat lesson worked examples or recall checks exactly.
4. **Hints leak answers.** About 18 stage-2 hints give the answer or leave only a copy step.
5. **Difficulty is inflated at levels 3–5**, and there is a syllabus-scope question for 16
   items covering area scale factors and congruence tests. Reviewers should decide this.

The batches were generated with `prompt_version: math-question-authoring-v1`. The N2
audit introduced house rules v2 and prompt v2 to control outcome alignment, semantic
duplicates and hint boundaries, but G2 was not regenerated under them. This explains most of
the content-pattern findings below.

Severity scale:

- **High:** wrong or misleading for a learner, or exposes the answer.
- **Medium:** materially weakens assessment or teaching value, or breaks a written standard.
- **Low:** polish.

---

## Part 1 — Content findings

### 1.1 Answer verification

All 104 canonical answers match independent recomputation from the prompt. The script
encodes each prompt's givens and uses `Fraction`/SymPy for every proportion, linear equation
and enlargement `P′ = C + k(P − C)`.

The worked solutions agree with their canonical answers, and the mark totals agree with part
marks (validator). No question uses `accepted_answers`. The checker parses fractions, so
`1/2` is accepted for `0.5`, `1/4` for `0.25`, and so on.

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| g2-l3-531, g2-l3-523 | Low | Answers `960000` and `10000`. `_fraction()` in `checking.py` strips spaces but not commas, so a learner who types `960,000` gets a format error. | Add "Enter the number without commas" to the prompt, or extend the parser to strip thousands separators. |

### 1.2 Wording, stated conditions and context

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| g2-l2-509 | Medium | "Two **kite-shaped** badges … Each badge or pennant is **triangular**. One is congruent to a triangle with side lengths 11 cm, 13 cm and 14 cm." A kite is a quadrilateral, so the shape contradicts itself. "badge or pennant" is template residue, and "One" has no clear referent. | "Two triangular badges are congruent. One badge has side lengths 11 cm, 13 cm and 14 cm. Find the perimeter of the other badge in centimetres." |
| g2-l2-524 | Low | "Each badge or pennant is triangular" is template residue in a pennant-only item. "One is congruent to …" is vague. | "A triangular pennant with sides 18 cm, 20 cm and 21 cm is reflected. Find the perimeter of its image in centimetres." |
| g2-l2-521 | Medium | "Two similar arrowheads have one pair of matching edges 6 cm and 3 cm. Another original edge is 30 cm." The prompt never says which arrowhead is the original. If the 3 cm arrowhead is the original, y = 60, not 15. | "The original arrowhead's 6 cm edge matches a 3 cm edge on the copy. Another edge of the original is 30 cm. Find the matching edge y cm on the copy." |
| g2-l2-520 | Low | "Its first pair is 5 cm and 2 cm, and its second pair is 20 cm and y cm." The direction (original → copy) is implied, not stated. | State "original 5 cm ↔ copy 2 cm; original 20 cm ↔ copy y cm". |
| g2-l3-530 | Medium | "A student's eye is 1.6 m above the ground and **2 m from the mirror**." Eye-to-mirror distance is the slant (hypotenuse). The model needs the horizontal distance from the student's feet. The prompt also omits that the mirror lies flat on level ground and that the student and pole are vertical. | "A student stands 2 m from a mirror lying flat on level ground; the student's eyes are 1.6 m above the ground. The mirror is 10 m from the foot of a vertical flagpole …" |
| g2-l4-512 | Low | The title "Shadow with sloping ground correction" contradicts the prompt ("stand on level ground"). | Retitle it, for example "Shadow-length difference". |
| g2-l4-503 | Low | The title "Centre of enlargement on a line" does not describe the task, which is to find the centre from A and A′. | Retitle it "Finding the centre of enlargement". |
| g2-l2-529 | Low | The title "Origin image ordinate" uses "ordinate", which is unfamiliar to the audience under the current standard. | Use "y-coordinate of an image". |
| g2-l1-511 | Low | A wall drawn as 3 cm "represents a length 7 times as large", so the real wall is 21 cm. This is implausible. | Use a realistic scale, such as 1 : 200 with the answer in metres, or change the object. |
| g2-l3-523 | Low | The "square floor" has area 10 000 cm² = 1 m², which is implausible, and the answer is asked in cm². | Use scale 1 : 100 and ask for the answer in m², or change the context to a tile or table top. |
| g2-l1-506 | Low | "A toy car is enlarged from a 2 cm design segment using scale factor 5. Find the matching toy length" is awkward. | "On a design sketch, a toy car is 2 cm long. The toy is 5 times as long. Find its length in centimetres." |
| 30 items¹ | Low | The prompt states input units but ends with "Enter the numerical value only" and never names the answer unit, for example g2-l2-505 "Find the image length". | Append "in centimetres", "in metres" or "in cm²" to each request. |
| Lesson g2-lesson-01, worked example 1 | Low | "corresponding sides 3x + 1 cm and 16 cm" has no brackets. | Write "(3x + 1) cm". |

¹ g2-l2-505, 509, 510, 511, 513, 515, 518, 521, 524, 525, 526, 530; g2-l3-503, 510, 513,
517, 518, 521, 522, 524, 526, 527, 528; g2-l4-501, 510, 513, 515, 516; g2-l5-501, 504.

**Conflicts between the N2 audit's Singapore-specific rules and the current audience
standard.** These are reported for reviewers to decide, not resolved here.

- The N2 audit checked "Singapore/British English … and currency notation (S$)". The current
  `LESSON_NOTES_CONTENT_STANDARD.md` says the Singapore syllabus is "a calibration and
  coverage reference" only, and asks for "clear international English" and
  Southeast-Asia-neutral contexts.
- In G2, no question uses currency, so the S$ rule is not exercised. Spelling is
  consistently British (centimetres, metres, trapezium). This is compatible with
  "international English" but is not required by it.
- There is no Singapore-specific place or institution in any G2 learner text.
- The bank blueprint's `course` field still reads "Singapore G3 Mathematics", and all
  `style_references` are Singapore school papers. This metadata is not learner-facing.
  Reviewers should decide whether the label should match the "ASEAN Scholarship
  Mathematics" programme name.
- Unexplained terms that the current standard would want explained or avoided include
  "ordinate", "fabricator", "pennant" and "beacon". "Ordinate" appears in g2-l2-529; the
  others appear in prompt contexts. All are Low.

### 1.3 Outcome alignment and syllabus scope

| Key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| g2-l1-506, 511, 516, 521 (outcome 2.5) | Medium | Each is "length × factor" with no problem context involving congruence or similarity. They are indistinguishable from the 2.2 items g2-l2-502/510/511/518/519/525/526. | Rewrite as genuine 2.5 problems, for example "two buildings' shadows" or "a scale-plan route", or move them to 2.2 and author new 2.5 items. |
| g2-l3-518 (2.2) | Medium | "Regular hexagon side 4 cm is similar to regular hexagon side 10 cm. Find the perimeter of the larger." The answer 6 × 10 = 60 does not use similarity. The 4 cm value is irrelevant. | Ask for the larger perimeter given only the smaller perimeter and the side ratio, or ask for the scale factor. |
| g2-l4-513 (2.1, d4) | Medium | Width 13 cm and length 18 cm are given directly, so x is never needed for the perimeter 2(18 + 13) = 62. The algebra is decorative. | Make the requested quantity depend on x, for example give the second frame's length as (x + 12) cm. |
| g2-l4-502 (2.3) | Low | The side data (9 cm ↔ 15 cm) is unused. The hint says it "confirms the correspondence", which it cannot. | Remove the side data, or ask for a side as a second part. |
| **Syllabus-scope judgment call:** area and surface-area scale factors in g2-l3-504, 511, 519, 521, 523; g2-l4-507, 508, 510, 515, 516; g2-l5-502, 504; also lesson g2-lesson-02 ("area factor = k²", worked example 2), g2-lesson-04 and g2-lesson-05 | Medium (decision) | The repo catalogue lists Secondary 2 G2 as 2.1–2.5 only, with no area or volume clause. In the Singapore syllabus that the catalogue mirrors, ratios of areas of similar figures and volumes of similar solids are, to my knowledge, **Secondary 3** content. g2-l4-508 also scales the **surface area of 3-D boxes**, which goes beyond "plane figure". I could not verify this from repository files, because the catalogue holds no Secondary 3 G2 list. | Reviewers should decide whether the Sec 3-entry scholarship test expects area-factor reasoning. If not, re-target these items to linear-factor or perimeter tasks. If yes, keep them and record the decision in the blueprint. Either way, review g2-l4-508 (3-D). |
| **Syllabus-scope judgment call:** congruence tests SSS/SAS/ASA/RHS in g2-l3-502, 509; g2-l4-505, 509; and the g2-lesson-01 reasoning section; AA similarity in g2-lesson-03 | Low (decision) | This is the same consideration: formal congruence and similarity tests are, to my knowledge, Secondary 3 in the reference syllabus. | Reviewers should confirm the scope. |
| Cross-topic overlap: g2-l2-506 (map 1 cm : 4 km), g2-l2-531 (1 : 100 blueprint), g2-l3-531 (map area) | Low | The same course has `n2-lesson-04` "Map scales involving distance and area" (Sec 2 N2.4). The G2 2.5 items here are pure map-scale arithmetic. | Keep only the G2 2.5 items that use similarity reasoning, and leave map scales to N2. |
| g2-lesson-01, worked example 2 | Medium | This uses Pythagoras' theorem (√(13² − 5²) = 12). Pythagoras is taught in G4 (unit position 4), which comes after G2 (unit position 1) in this course. | Replace the third-side computation with a congruence-only deduction, or add a prerequisite note. |

### 1.4 Difficulty alignment

Difficulty definitions are taken from `blueprint.json`.

| Key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| g2-l2-501, 508, 516, 517 (d2) | Medium | Each is one-step recall: a corresponding side or angle is equal, so x = the given value. They are identical in demand to the d1 items g2-l1-504/509/514/519. | Re-label them d1, or add a second linked step, for example an algebraic side. |
| g2-l3-503 (d3) vs g2-l2-513 (d2) | Medium | Both ask "a triangle of perimeter P is enlarged by factor 3; find the new perimeter" (24 → 72 and 22 → 66). The same task appears at two difficulty levels. | Rewrite g2-l3-503 as a multi-step task, for example finding a side from the perimeter ratio, or drop it to d2 and replace it. |
| g2-l3-507, 524, 525, 527 (d3) | Low | Each is a single operation (3 × 5, ½ · ⅔ cancel, −2 + 5, 28 ÷ 4). | Re-label them d2, or extend them. |
| g2-l4-501, 505, 509, 513 (d4) | Medium | These are routine. g2-l4-501 is two factors multiplied. g2-l4-505 and 509 identify a congruence criterion. g2-l4-513 is covered in 1.3. None requires "method selection, constraints or justification". | Re-label them d2–d3, or add the d4 element, such as a justification or a constraint. |
| g2-l5-501, 503, 504 (d5) | Medium | These are respectively one linear equation plus a sum, one proportion equation, and three multiplied factors followed by squaring. That is not "complex non-routine synthesis … or proof". | Re-label them d3–d4, or author genuine d5 items, for example a two-triangle configuration requiring both congruence and similarity, or multi-part reasoning. |

### 1.5 Hint leakage

Hint policy, stage 2: "Give an explicit next method or intermediate setup **without giving
the final answer**."

| Key(s) | Severity | Stage-2 hint (evidence) | Proposed correction |
| --- | --- | --- | --- |
| g2-l1-504, 509, 514, 519 | High | "Set x equal to the stated 48° angle." This is the answer. | Stage 2: "Which angle in the first figure is in the same position as x? Its size is not changed by similarity." |
| g2-l2-508, 517 | High | "Set the corresponding angle measures equal." For these items that is the answer. | Point the learner to the correspondence without equating the values. |
| g2-l2-501, 516 | High | "Corresponding lengths in congruent figures are equal." The answer follows directly (x = 7 or x = 13). | Same as above. |
| g2-l1-501 | High | "Both triangles have exactly the same three side lengths." This decides code 1. | "List each triangle's sides in increasing order and compare." |
| g2-l1-517 | High | "Their corresponding sides are proportional but unequal." This decides code 2. | "Are the side lengths equal? Are all angles of a regular hexagon the same?" |
| g2-l3-502 | High | "The stated pattern is side-angle-side." This gives code 2. | "Where is the equal angle relative to the two equal sides?" |
| g2-l3-509 | High | "Match right angle, hypotenuse and one side." This names RHS. | "Which test is only for right-angled triangles?" |
| g2-l4-505 | High | "Use AC = AC as the third side equality." With the given AB = AD and BC = DC, this is SSS. | "Is there a side the two triangles share?" |
| g2-l4-509 | High | "AB and AC meet at A; PQ and PR meet at P." This gives code 1 (∠A = ∠P). | "SAS needs the angle between the two known sides. Which vertex is between AB and AC?" Keep the PQR half for the learner. |
| g2-l3-524 | Medium | "The factors 2/3 and 3/2 cancel." This gives 90. | "Multiply the two scale factors first." |
| g2-l2-504, g2-l3-515 | Low | "B′ = (6, 10), then add" and "Q′ = (9, −6), then add" leave one addition. | Give only the method for one coordinate. |
| g2-l1-512 | Low | "All three corresponding side lengths agree." This restates the prompt and gives code 1. | "What does a reflection do to lengths?" |

**Structural cause.** In a one-step d1 question, any concrete next step reveals the answer.
Either accept a conceptual-only stage 2 for d1 items, or make d1 items two-step.

### 1.6 Semantic duplicates

These were grouped by identical stage-1 hint and identical operation pattern. Values differ;
the task is the same.

| Family | Items | Severity | Proposed correction |
| --- | --- | --- | --- |
| "length × factor" (2.2, d2) | g2-l2-502, 510, 511, 518, 519, 525, 526 (7) | Medium | Keep at most 2. Replace the rest with direction-of-factor, reverse-factor, or mixed-unit variants. |
| "length × factor" (2.5, d1) | g2-l1-506, 511, 516, 521 (4); same task as above | Medium | See 1.3. |
| "corresponding side or angle equals" (2.1, d2) | g2-l2-501, 508, 516, 517 (4) | Medium | Merge. Replace with SSS/SAS reasoning or algebraic correspondence. |
| "congruent-to-triangle perimeter" | g2-l2-509, 524 | Low | Keep one. |
| "one proportion y/a = b/c" (2.3, d2) | g2-l2-503, 512, 520, 521, 527, 528 (6) | Medium | Keep 2–3. Vary the structure: an unknown in the denominator, three-term correspondence, or the vertex-order trap. |
| "scale factor = image ÷ original" (2.2, d1) | g2-l1-503, 508, 513, 518 | Low | Keep 2–3 and add a reduction-direction trap. |
| "corresponding angle equals" (2.3, d1) | g2-l1-504, 509, 514, 519 | Low | Keep 2. |
| "coordinate × factor about origin" (2.4, d1) | g2-l1-505, 510, 515, 520 | Low | Keep 2–3. |
| enlarged perimeter | g2-l2-513 ≈ g2-l3-503 | Medium | See 1.4. |
| **Lesson ↔ question exact repeats** | g2-l2-507 = g2-lesson-05 worked example 1 (2 m pole, 3 m shadow, 12 m tree shadow → 8 m)<br>g2-l3-501 = g2-lesson-01 worked example 1 (3x + 1 = 16 → x = 5)<br>g2-l2-526 = g2-lesson-04 active recall (12 cm × 1/3 → 4)<br>g2-lesson-02 recall (perimeter 20 × 3) ≈ g2-l2-513/g2-l3-503<br>g2-lesson-04 example 1 (P(2, 3) × 4) ≈ g2-l1-505 (A(2, 3) × 2) | Medium | A learner who has read the lesson already knows the answers. Change the numbers in either the lesson or the question. |

### 1.7 Lesson findings (content)

All five lessons pass the structural gate: 8 sections, 2 worked examples, active recall and a
summary. All worked examples and recall answers are correct.

| Lesson | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| All 5 | Medium | Every first worked example has the same `verification_note`: "Check that every side and angle was matched in the stated corresponding order." This is generic boilerplate, not a verification. It is meaningless for lesson 04 (coordinates) and lesson 05 (shadow). The standard requires "explicit reasoning and verification". | Write a real check, for example "3(5) + 1 = 16 ✓", "(8, 12) lies on the ray from O through (2, 3) ✓", or "2/3 = 8/12 ✓". |
| All 5 | Low | The "Lesson checklist" text is identical in all five. In lesson 01 (congruence) it talks about scale factors and "linear or squared factor", which do not apply. | Write a topic-specific checklist for each lesson. |
| g2-lesson-01 | Medium | Section 2 says "equal arc marks identify corresponding angles", but the lesson diagram has no arcs. | See diagram finding D-L1. |
| g2-lesson-01 | Medium | Worked example 2 relies on Pythagoras (see 1.3). | Replace it. |
| g2-lesson-04 | Low | "Linear dimensions use \|k\|" implies negative scale factors, which are outside the stated scope. "Positive fractional factors create reductions" is false for factors such as 3/2. | "Factors between 0 and 1 give reductions; linear dimensions are multiplied by k." |
| g2-lesson-04 | Low | "On a coordinate grid, P′ = C + k(P − C)", but the lesson diagram's grid has no axes or coordinates. | See D-L4. |
| g2-lesson-03 | Low | Worked example 2: "Find QR and AC if AC corresponds to PR" is redundant after "similar in that order". | Drop the "if" clause. |

---

## Part 2 — Diagram findings

### 2.0 Method and what was viewed

- I resolved every `asset_ref` through the referencing JSON's `assets[].path`. For questions
  that is `…/g2/v1/assets/<key>-diagram.svg`. For lessons it is
  `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/g2-lesson-0N-*.svg`. All 20
  files exist, and their checksums are validated by the bank and course validators.
- I rendered all 20 at 940 px and at 390 px, giving 40 PNGs in a scratch directory that is
  not committed, and looked at every image.
- I recomputed the side lengths and angles of every drawn polygon from the SVG path
  coordinates.
- Removing the `<title>`, `<desc>` and heading lines leaves **five distinct SVG bodies**
  across the 15 question diagrams. Each lesson diagram uses the same body as its matching
  question template, minus the "not drawn to scale" note.

| Template (`diagram_kind`) | Question assets | Lesson asset |
| --- | --- | --- |
| `congruent` (outcome 2.1) | g2-l1-501, g2-l3-501, g2-l5-501 | g2-lesson-01-congruent.svg |
| `similar` (2.2) | g2-l1-503, g2-l3-503, g2-l5-502 | g2-lesson-02-similar.svg |
| `proportion` (2.3) | g2-l1-504, g2-l3-505, g2-l5-503 | g2-lesson-03-proportion.svg |
| `enlargement` (2.4) | g2-l1-505, g2-l3-507, g2-l5-504 | g2-lesson-04-enlargement.svg |
| `scale` (2.5) | g2-l1-506, g2-l3-508, g2-l5-505 | g2-lesson-05-scale.svg |

### 2.1 Findings shared by every diagram (all 20)

| ID | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- |
| D-ALL-1 | accuracy | High | No question-specific content. None of the 15 question diagrams shows any given length, angle, variable, coordinate or vertex label from its prompt (for example 4/6/7 cm, 48°, x, (2, 3), 24 m × 15 m). The figures cannot be "used together with the measurements stated", as the stem instructs. | Generate each SVG from the question's own givens: label sides and angles and use the prompt's vertex letters. Where a diagram adds nothing, remove it and record `text_sufficient`. |
| D-ALL-2 | accuracy | Medium | The alt text claims content that is not drawn. The pattern is "Schematic for <title>. Not drawn to scale. Stated measures include 4 cm, 6 cm, 7 cm, 7 cm, 4 cm." None of those measures appears in the image. The list is truncated to 5 by `re.findall(...)[:5]`, which is why g2-l1-501 omits the second "6 cm". Lesson alt texts also describe features that are absent (see D-L1, D-L2 and D-L4). | Write alt text that describes the figure actually drawn: shapes, labels and marked equalities. |
| D-ALL-3 | accuracy | Medium | `generation_spec` contains only `renderer`, `diagram_kind`, `question_key`/`lesson_key`, `outcome` and `not_to_scale`. `GEOMETRY_CONTENT_STANDARD.md` requires "explicit dimensions in their metadata". There is no `forbidden_visible_labels`, so the answer-leak validator never runs. | Add dimensions, vertex labels and `forbidden_visible_labels` (the final answer) to each spec. |
| D-ALL-4 | neatness | High | Unreadable on a phone. The viewBox is 940 wide, and at 390 px the scale is 0.415. Body labels at 17 px render at about 7 px, the heading at about 9 px, and the "not drawn to scale" note at about 5.4 px. This was confirmed in the 390 px renders. | Use label fonts of at least 30–34 viewBox units (about 13–14 px at 390 px), or a narrower viewBox (about 600) with stacked figures. Drop the in-SVG heading, because the question title already shows above it. |
| D-ALL-5 | neatness | Low | The in-SVG heading duplicates the question title and uses space at the top of the figure. | Remove it, or keep it only for lessons. |

### 2.2 Template `congruent`

Assets:

- `assets/g2-l1-501-diagram.svg`
- `assets/g2-l3-501-diagram.svg`
- `assets/g2-l5-501-diagram.svg`
- `courses/…/assets/g2-lesson-01-congruent.svg`

| ID | Key / asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D-C1 | all 4 | accuracy | High | The figures labelled "same shape and size" are **not congruent**. △ABC has sides 238.5, 238.5 and 260.0 (isosceles, perimeter 737). △PQR has sides 230.9, 217.1 and 211.0 (scalene, perimeter 659). | Draw PQR as an exact rotated or reflected copy of ABC's coordinates. |
| D-C2 | all 4 | accuracy | Medium | The tick marks are wrong. Each triangle has a single tick on two different sides. This implies ABC is isosceles and that four sides are equal, and it does not show a three-pair SSS correspondence. | Use 1, 2 and 3 ticks on the three corresponding side pairs. |
| D-C3 | all 4 | neatness | Medium | The tick at `M705 230 l18 5` does not touch side QR. It runs 5.9–21.0 px off the line, at about 54° to it, and looks like a stray mark. The tick at `M160 175 l18 10` starts on AB and extends only to one side (−1.5 to +19.1 px). | Centre each tick on the midpoint of its side and make it perpendicular, for example ±9 px along the normal. |
| D-C4 | g2-l1-501 | accuracy | High | **Reveals the answer.** The question asks whether the tiles are congruent (code 1), and the diagram text says "same shape and size". The drawn ABC is also isosceles, which contradicts the scalene 4/6/7 cm tile. | Remove the caption. Label the sides 4, 6, 7 and 7, 4, 6 cm on scalene triangles, and add `forbidden_visible_labels: ["congruent", "same shape and size"]`. |
| D-C5 | g2-l3-501 | accuracy | High | The question refers to AB = (3x + 1) cm and PQ = 16 cm, but the figure has no vertex letters A, B, P or Q (only "△ABC" and "△PQR" captions) and no side labels. | Add vertex letters and label AB "(3x + 1) cm" and PQ "16 cm" with matching ticks. |
| D-C6 | g2-l5-501 | accuracy | High | The question is about **pentagons**, but the diagram shows **triangles**. None of the side lengths (3x + 2, 12, 15, 17, 18, 5x − 10) is shown. | Draw two congruent pentagons with the five sides labelled and the (3x + 2) ↔ (5x − 10) pair marked. |
| D-C7 | g2-lesson-01 | accuracy | Medium | The alt text and lesson text say "matching side ticks **and angle arcs**", but no arcs are drawn. | Add matching arcs (1, 2 and 3 strokes) at corresponding vertices, or edit the text. |
| D-C8 | g2-lesson-01 | accuracy | Low | There is no "not drawn to scale" note, and the drawing is not to scale (D-C1). | Fix D-C1 so the drawing is exact. |

### 2.3 Template `similar`

Assets:

- `assets/g2-l1-503-diagram.svg`
- `assets/g2-l3-503-diagram.svg`
- `assets/g2-l5-502-diagram.svg`
- `courses/…/assets/g2-lesson-02-similar.svg`

| ID | Key / asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D-S1 | all 4 | accuracy | High | The "original" and "image" are **not similar**. The original's angles are 57.1°, 65.8° and 57.1° (isosceles). The image's angles are 52.2°, 72.5° and 55.2° (scalene). Side ratios are 1.53, 1.47 and 1.64, so no single k fits. | Draw the image as an exact k-multiple of the original's coordinates. |
| D-S2 | g2-l1-503 | accuracy | Medium | The stated k is 2 (3 cm → 6 cm), but the drawing implies k ≈ 1.5–1.6. No edge lengths are labelled, and "scale k" carries no value. | Label the corresponding edges "3 cm" and "6 cm" and draw them at a 1 : 2 ratio. Do not show "k = 2", because k is the answer. |
| D-S3 | g2-l3-503 | accuracy | Medium | The perimeter of 24 cm is not shown, and nothing distinguishes perimeter from side. | Label "perimeter 24 cm" inside the original and "k = 3" on the arrow. Do not show 72. |
| D-S4 | g2-l5-502 | accuracy | High | The question has **three** polygons A, B and C, with factors 3/2 and 4/3, perimeter 27 cm and area 45 cm². The diagram shows two triangles labelled "original" and "image". | Draw A → B → C with the arrows labelled 3/2 and 4/3, and mark A's area as 45 cm². Alternatively, make it text-only. |
| D-S5 | g2-lesson-02 | accuracy | High | The alt text says "A small rectangle and an enlarged similar **rectangle**", but the drawing shows **triangles**. | Make the alt text match the figure, or redraw it as the rectangles that worked example 2 uses. |

### 2.4 Template `proportion`

Assets:

- `assets/g2-l1-504-diagram.svg`
- `assets/g2-l3-505-diagram.svg`
- `assets/g2-l5-503-diagram.svg`
- `courses/…/assets/g2-lesson-03-proportion.svg`

| ID | Key / asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D-P1 | all 4 | accuracy | High | The triangles shown as similar (A↔P, B↔Q, C↔R) **are not**. The angles are A 66.5° vs P 73.7°, B 59.7° vs Q 57.6°, and C 53.8° vs R 48.7°. Side ratios are 1.02, 1.15 and 1.07. | Generate PQR as k·(ABC) about a common origin, translated. |
| D-P2 | all 4 | neatness | Medium | Label "A" (`x=200 y=55`, cap height ≈ 12) touches the heading's descenders (baseline 38, about 43 with descenders). The gap is about 0 px. This is visible in the renders, especially under "Corresponding acute angles" and "Angle expression in similar triangles". | Move the figures down about 20 px, or remove the heading (D-ALL-5). |
| D-P3 | g2-l1-504 | accuracy | Medium | Neither the 48° angle nor x° is marked, so the diagram cannot show which angles correspond. | Mark 48° at one vertex and x° at its corresponding vertex with matching arcs. |
| D-P4 | g2-l3-505 | accuracy | Medium | The angle expressions (3x + 5)° and (5x − 35)° are not shown. | Mark both expressions at a corresponding vertex pair with matching arcs. |
| D-P5 | g2-l5-503 | accuracy | High | The question uses triangles **ABC and ADE**, with AB ↔ AD and BC ↔ DE. The diagram labels the second triangle **PQR**, has no D or E, and shows two separate triangles instead of the shared-vertex configuration. No lengths are labelled. | Draw △ADE sharing vertex A with △ABC, with D on ray AB and E on ray AC so that DE ∥ BC. Label AB (x + 2), AD (2x − 1), BC 12 and DE 21. |

### 2.5 Template `enlargement`

Assets:

- `assets/g2-l1-505-diagram.svg`
- `assets/g2-l3-507-diagram.svg`
- `assets/g2-l5-504-diagram.svg`
- `courses/…/assets/g2-lesson-04-enlargement.svg`

| ID | Key / asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D-E1 | all 4 | neatness | Medium | The "object" label (`x=300 y=190`) is crossed by the image triangle's hypotenuse (y = 195 → 166 across x = 300–358). It also sits outside the object triangle, so its reference is unclear. | Place "object" inside or under the small triangle, for example at (215, 280). |
| D-E2 | all 4 | accuracy | Medium | Grid lines are at y = 80, 130, 180, 230, 280, but the vertices sit at y = 205 and 255, mid-cell. The grid has no axes or coordinates, so a learner cannot read positions. | Snap vertices to grid intersections and add numbered x and y axes when coordinates are involved. |
| D-E3 | g2-l1-505 | accuracy | High | The question is an enlargement **about the origin with factor 2** of A(2, 3). The drawing shows centre "C" (not O), no axes, no A, and a **factor of 3** (legs 100 → 300 px). The drawing contradicts the stated factor. | Draw axes with O, plot A(2, 3) and leave A′ unlabelled, or show the ray only. Add `forbidden_visible_labels: ["4", "(4, 6)"]`. |
| D-E4 | g2-l3-507 | accuracy | Medium | The question names the centre **O**, but the diagram labels it "C". Neither A nor A′ is labelled, and OA = 5 cm is not shown. | Label O, A and A′, mark OA = 5 cm, and leave OA′ unlabelled. |
| D-E5 | g2-l5-504 | accuracy | High | The question has **three successive** factors (3/2, then 2/3, then 5/2; net 5/2) and area 32 cm². The diagram shows a single ×3 enlargement. | Show a chain of three arrows labelled with the factors, or make it text-only. Do not show 5/2 or 200. |
| D-E6 | g2-lesson-04 | accuracy | Medium | The alt text promises "construction rays through corresponding vertices", but none are drawn. The centre coincides with an object vertex, so the rays degenerate. The lesson text refers to a coordinate grid, but there are no coordinates. | Move the centre off the object, draw dashed rays from C through each vertex pair, and number the axes. |

### 2.6 Template `scale`

Assets:

- `assets/g2-l1-506-diagram.svg`
- `assets/g2-l3-508-diagram.svg`
- `assets/g2-l5-505-diagram.svg`
- `courses/…/assets/g2-lesson-05-scale.svg`

| ID | Key / asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D-SC1 | all 4 | accuracy | Medium | The "plan" (210 × 140, aspect 1.50) and "actual" (290 × 220, aspect 1.32) rectangles are **not similar**, even though the template illustrates similarity and scale. | Draw the actual rectangle as an exact multiple of the plan rectangle. |
| D-SC2 | g2-l1-506 | accuracy | Medium | The labels and arrow say "plan or model → actual object", but here the 2 cm design is enlarged *to* the toy, which is the model. "area scale²" does not apply to a length-only d1 item. | Label "design 2 cm" → "toy", with the arrow marked "× 5", and remove the area line. Do not show 10. |
| D-SC3 | g2-l3-508 | accuracy | High | The arrow points plan → actual, but the question goes from the real garden (24 m × 15 m) to the model at 1 : 300. Neither the dimensions nor the scale are shown. The real aspect ratio is 1.6. | Draw the real garden labelled 24 m × 15 m → the model at 1 : 300, with the model sides unlabelled. |
| D-SC4 | g2-l5-505 | accuracy | Medium | The question involves a plan (7.5 cm × 4.8 cm, 1 : 400), the courtyard, and a stage at 3/5. The diagram shows two generic rectangles, with no stage and no dimensions. | Show plan → courtyard → stage with the 1 : 400 and × 3/5 arrows, and the plan dimensions only. |
| D-SC5 | g2-lesson-05 | accuracy | Low | The alt text says "linear and area scale factors shown", but only the words "linear scale" and "area scale²" appear, with no values. | Show "1 : 600" and "area 1 : 600²" to match worked example 2, or edit the alt text. |

### 2.7 Text-only questions that clearly need a diagram

These are taken from `diagram_audit.json`. Every one of the 89 `text_sufficient` decisions
carries the same boilerplate reason, and selection was mechanical (see R2). The following
items would clearly benefit from a figure:

| Key | Why a diagram would help |
| --- | --- |
| g2-l3-520 | Triangle ABC with DE ∥ BC, D on AB and E on AC: the classic nested-triangle figure. Learners must see why AD/AB, not AD/DB, is used. |
| g2-l3-530 | Mirror method. The geometry, including which distance is horizontal, is exactly what the wording gets wrong (1.2). |
| g2-l2-523 | River-width survey with two similar triangles. The "baseline" and "offset" correspondence is hard to picture from text. |
| g2-l4-505 | Triangles ABC and ADC sharing AC (a kite). The shared side is the key insight. |
| g2-l4-503, g2-l4-511 | Finding or using a centre of enlargement not at the origin. A grid figure supports P′ = C + k(P − C). |
| g2-l2-507, g2-l3-516, g2-l4-512 | Shadow problems. One labelled pole/tree figure would serve all three, and the lesson has none. |
| g2-l4-509 | SAS with named vertices. A figure showing which angle is "included" teaches the criterion. |

Conversely, several diagrams were added to items where a figure adds nothing, for example
g2-l1-506, g2-l3-503 and g2-l5-504. Those slots would be better spent on the items above.

---

## Root-cause patterns

**R1 — Fixed per-outcome SVG templates. This affects all 15 question diagrams and all 5
lesson diagrams.**

- In `scripts/recalibrate_geometry_content.py`, `OUTCOME_KIND` maps each G2 outcome to one
  `diagram_kind` (2.1 → `congruent`, 2.2 → `similar`, 2.3 → `proportion`,
  2.4 → `enlargement`, 2.5 → `scale`).
- `svg_shape(kind)` (lines 276–296) returns a **hard-coded** SVG fragment for each kind.
- `svg_document()` injects only the question or lesson title.
- The script never reads question values. The only per-question data, the regex-extracted
  "givens", goes into `<desc>` and the alt text and is truncated to five items.
- The template coordinates were never constructed to be congruent or similar, which
  produces D-C1, D-S1, D-P1 and D-SC1.
- **Every accuracy finding in 2.2–2.6 follows from this.**

**R2 — Mechanical diagram selection.** `recalibrate_questions()` picks, for each outcome,
the first question at difficulty 1, then 3, then 5. It writes the same "representative
visual item" reason for those and the same "fully stated" reason for every other item. This
explains why g2-l5-501 (pentagons) received the triangle template, and why the items in 2.7
were left text-only.

**R3 — Validators cannot catch template errors.**
`question_bank/src/question_bank/geometry_validation.py` checks only:

- `angle_types` diagrams;
- declared `generation_spec.angle_markers`; and
- declared `forbidden_visible_labels`.

The G2 kinds declare none of these, so `geometry_diagram_issues()` returns no issues. The
validators do not check that:

- labels match the prompt;
- congruent or similar figures correspond; or
- the question's own givens appear at all.

This is why the bank and course validators report 0 issues.

**R4 — Prompt-contract version.** All four G2 batches use `math-question-authoring-v1`.
House rules and prompt v2, introduced after the N2 audit, address the hint boundaries
(1.5), semantic duplicates (1.6) and outcome alignment (1.3) found here.

**Likely spread beyond this audit (not verified here).** The same
`recalibrate_questions()` and `svg_shape()` generated the Secondary 1 G1 and G5 question
diagrams. Removing titles collapses their SVGs to 8 distinct bodies out of 24 files (G1)
and 5 out of 15 (G5), which suggests the same templating. Those banks should get the same
audit.

## Not verified

- **Syllabus scope (1.3).** Whether areas of similar figures and congruence/similarity tests
  belong to Secondary 2 or Secondary 3 in the reference syllabus comes from my knowledge.
  The repository catalogue lists only Secondary 1–2 outcomes, so I could not confirm it from
  repository files. What the target test expects is a reviewer judgment.
- **Platform rendering.** Diagrams were rendered in headless Chromium with system fonts.
  Exact text widths, and therefore the precise overlap margins in D-E1 and D-P2, may differ
  slightly in the production client's font stack. I assessed phone readability by scaling
  the SVG to 390 px, not inside the actual app.
- **Review packets.** The review packets under `review_packets/` were checked only for
  revision currency (all 104 items match the source revisions). Their HTML was not
  re-rendered.
- **Cross-bank duplicates.** I checked these only against the same course's N2 map-scale
  lesson by topic. I did not run a catalogue-wide near-duplicate search.

No content, review state, SVG, manifest or claim was modified. No approval was recorded and
no paid model API was called. Rendered PNGs were kept outside the repository.
