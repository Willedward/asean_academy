# Secondary 2 N7 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_2/n7/v1/`
(batches B001–B004) and all six N7 lessons (`n7-lesson-05` to `n7-lesson-10`), which are stored
in `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/` and listed under unit
`g3-sec2-n7` in that folder's `course.json`.

**Audience:** students preparing for the Sec 3-entry ASEAN Scholarship test.

**Decision boundary:** this is a technical pre-review only and does not record any Mathematics or
editorial approval. No question, lesson, SVG, manifest, claim or review state was changed. All 104
questions and all six lessons are `draft`. All four batches are `ready_for_review`, with
`mathematics: pending` and `editorial: pending`. Rendered images were kept outside the repository.

## Counts

| Item | Count |
| --- | ---: |
| Questions checked | 104 (B001–B004, 26 each; 17–18 per outcome 7.5–7.10) |
| Questions with diagrams | 0 (every question has `assets: []`) |
| Lessons checked | 6 |
| Diagrams referenced by lessons | 3 (`n7-lesson-06`, `-07`, `-08`) |
| Diagrams rendered to PNG and viewed | 3 of 3, at 960 px and at 390 px (phone width) |
| `diagram_audit.json` for N7 | none exists |

The review packets (`review_packets/g3-sec2-n7-b00{1..4}/questions.json`) match the source
question JSON part for part, so the findings below apply to both. The N7 question pool
(`question_pools/n7.json`) allocates all 104 keys.

## Checks performed

- Recomputed all 104 canonical answers with a sympy script **before** reading the worked
  solutions. The script parses each prompt by template family and solves it independently. For
  word problems it also checks that every count is a whole number and not negative, and for
  "known intersection" items it checks that the stated point lies on the given line.
- Checked every worked step, both hint stages, the response configuration (all 104 use
  `numeric` / `exact_numeric` with no accepted alternatives, tolerance or unit) and the
  `primary_outcome` and difficulty of each item.
- Grouped the questions by template and compared them with each other and with the lesson
  examples and recall checks to find semantic duplicates.
- Recomputed every lesson example and recall check, and measured lesson depth with the validator's
  own formula and as plain prose.
- Inspected the SVG source coordinates and text bounding boxes, and checked the plotted geometry
  numerically. Rendered each SVG with headless Chromium and viewed the output.

## Severity scale

- **High:** the learner is shown something wrong or misleading, or the item cannot measure its
  target skill.
- **Medium:** weakens the item's validity, difficulty calibration or teaching value. Fix before
  approval.
- **Low:** wording, polish or consistency.

## Part 1 — Content findings

**Correctness:** no canonical answer is wrong. All 104 recomputed values match `canonical_answer`,
and every word problem resolves to non-negative whole counts. Every lesson example, verification
note and active-recall answer is also arithmetically correct. The findings below concern assessment
validity, calibration, duplication, hints and wording.

### Question findings

| # | Stable keys | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C1 | n7-l3-503, n7-l3-510, n7-l3-517, n7-l3-526, n7-l3-527 (7.6 D3, "reversing an inequality") | High | The prompt says "The answer has the form x<k", which tells the learner the sign is reversed. Only k is collected, and a learner who forgets to reverse gets the same k: for n7-l3-503, the wrong answer x>3 and the right answer x<3 both give k = 3. The learner-facing title also names the skill. The item cannot detect the misconception it targets. | Remove the stated form from the prompt. Collect the direction as well as the boundary, for example with a choice of x<3, x>3, x≤3 and x≥3, or an inequality response type. Retitle without naming the method. |
| C2 | n7-l1-502, n7-l1-507, n7-l1-511, n7-l1-517 (7.5 D1, "checking equality") | High | The prompt contains the answer. "When x=3, evaluate the left side of x+6=9. What common value do both sides have?" has the answer 9, which is the right-hand side already printed in the prompt. | Ask whether a given value satisfies the equation (include candidates that do not), or ask which of several values is a solution. |
| C3 | 7.6 D1 (n7-l1-503, -508, -512, -518) and 7.6 D2 (n7-l2-504, -512, -521, -522, -528) | Medium | The prompt supplies the form (x<k or x≤k), and D1 also says "open-circle boundary". Only the boundary number is assessed. None of the 18 questions for outcome 7.6 asks about the endpoint type or the shading direction, even though 7.6 is "representing solutions on a number line". | Add items where the learner chooses the number-line graph or the endpoint type and direction. These would be the first N7 question diagrams. Stop giving the form in the prompt. |
| C4 | n7-l1-510, n7-l1-514, n7-l1-520 (7.8 D1) | Medium | "The lines x+y=6 and x−y=2 intersect at (k,2)" gives y, so k comes from one equation. The pair of equations is never solved simultaneously. | Ask for the intersection point (p, q) without giving either coordinate, then collect p. |
| C5 | D4: n7-l4-502, -511, -514 (7.5); n7-l4-504, -513, -515 (7.7); n7-l4-505, -516 (7.8); n7-l4-506, -509 (7.9). D5: n7-l5-501, n7-l5-502, n7-l5-503, n7-l5-505 | Medium | Difficulty is overstated. Each 7.5 D4 item is two one-step solves. Each 7.7 D4 item is one substitution, plus a redundant clause ("has x-intercept 9/k"). Each 7.8 D4 item gives the intersection point, so finding k is a substitution, not simultaneous solving. Each 7.9 D4 item gives the roots, so k is their product. D5 n7-l5-501 reduces to k−3=4, n7-l5-502 is a plain x+y=9, 3x+2y=24 pair, n7-l5-503 is factorise-and-subtract (D3 demand), and n7-l5-505 repeats the D4 compound-inequality template. | Rewrite the D4–D5 items with real multi-step demand, for example: fractional or negative coefficients and solutions; brackets on both sides; a non-monic quadratic; forming a quadratic from a context and rejecting an invalid root; or simultaneous equations that need both equations scaled. |
| C6 | 7.10 D2 (n7-l2-501, -510, -518, -519, -526), D3 (n7-l3-501, -507, -515, -523, -524), D4 (n7-l4-501, -507, -510); 7.8 D5 n7-l5-502 | Medium | Four difficulty labels share one structure: x+y=n and ax+by=m with whole-number answers from 4 to 8 ("item prices", "admission model", "parcel allocation"). The difficulty label does not reflect any difference in demand. | Keep one family at D2 or D3. Make the higher levels use non-total relationships (ratio, "twice as many", age, digit, perimeter) or conditions with more than one step. |
| C7 | Whole bank: 104 questions from 29 templates (see the Template families table) | Medium | **Semantic duplicates.** Each template repeats with its numbers incremented, and within a family the answers run 4, 5, 6, 7, 8. All five 7.5 D2 equations are mirrored by 7.6 D2 inequalities with the same left side and right side: n7-l2-502/504 (3x+2, 14), n7-l2-503/512 (4x+3, 23), n7-l2-511/521 (5x+4, 34), n7-l2-520/522 (2x+5, 19) and n7-l2-527/528 (3x+1, 25). The N2 audit counts a repeated "values and operation pattern" as a duplicate. | Replace mirrored pairs with independent numbers. Within each family, vary the structure (variable on both sides, negative constant, fraction) rather than just shifting the numbers. |
| C8 | n7-l2-504 vs lesson 06 example 1; n7-l5-501 vs lesson 05 example 2; n7-l5-502 vs lesson 08 example 2; n7-l5-504 vs lesson 10 example 2; n7-l3-524 vs lesson 10 example 1; n7-l3-506 vs lesson 09 example 1; n7-l1-501 vs lesson 08 recall; n7-l2-509 vs lesson 09 recall | Medium | Some practice items copy lesson material. n7-l2-504 ("Solve 3x+2≤14") is identical to a worked example that shows the answer. The D5 items n7-l5-501, -502 and -504 change only one constant from a worked example: (k−3)x+5=4x+5 vs (k−1)x+5=3x+5; x+y=9 with 3x+2y=24 vs 3x+2y=23; digit sum 7 vs 11, both with a difference of 27. n7-l3-506 reduces to the example's x²−7x+12=0. n7-l1-501 uses the recall's x+y=7, x−y=1, x=4. n7-l2-509 has the recall's roots 2 and 6. | Change the numbers and structure of these practice items so that no item reproduces a lesson example or recall check. |
| C9 | All 104 | Medium | **Coverage and answer range.** 96 of 104 answers are whole numbers from 2 to 9. No answer is negative, fractional, zero, "no solution" or an identity, although lessons 06 and 09 teach x<−4 and x=−5. There is no non-monic quadratic, although the lesson 09 objective lists one. No 7.8 item uses the graphical method, although 7.8 names it. This is narrower than the Sec 3-entry scholarship test. | When rewriting under C5–C7, cover negative and fractional solutions, non-monic factorisation, graphical simultaneous solution and the special cases (no solution, infinitely many). |
| C10 | 7.10 all 17 (n7-l1-501 … n7-l5-504); 7.9 D1 n7-l1-505, -515, -521; 7.9 D2 n7-l2-509, -516, -517, -525, -531; 7.9 D4 n7-l4-506, -509; n7-l5-503; n7-l5-505; 7.5 D4 n7-l4-502, -511, -514 | Medium | **Stage-2 hints leak the answer.** In 7.10, H2 states both equations ("Use x+y=7 and x−y=1"), which removes the formulation demand that 7.10 assesses. In 7.9 D1 and D2, H2 gives the factors or the zero-factor equations, so the root can be read off. n7-l5-505 H2 gives the integer range ("from −3 inclusive to 8 exclusive"). In 7.5 D4, H2 gives x. The learner-facing titles (`question.title` is rendered in `apps/web/src/components/practice-player.tsx:304`) also name the method, for example "reversing an inequality", "read roots from factors" and "rearrange before factorising". | H2 should give the next step only. For 7.10, define the variables and give one equation. For 7.9, give the sum and product or the first factor. Use neutral titles. |
| C11 | n7-l2-509, -516, -517, -525, -531 (7.9 D2 H1) | Low | "Look for two numbers whose product is 12 and sum is 8" for x²−8x+12. The numbers are −2 and −6, whose sum is −8. Lesson 09 example 1 states this correctly ("sum −7"). | Change H1 to "product 12 and sum −8". |
| C12 | n7-l3-506, -514, -521, -522, -530, -531 (7.9 D3 solutions) | Low | The solution writes `x^2-7x+12=0=(x-3)(x-4)`, which incorrectly chains an equation and a factorisation. | Write `x²−7x+12=0 ⇒ (x−3)(x−4)=0 ⇒ x=3 or 4`. |
| C13 | 7.10 D2–D4 (13 items) and 7.8 D3 (5 items) | Low | The worked solutions jump from the equations to the answer ("x+y=7, 4x+2y=22 ⇒ x=4" and "3x+4(6−x)=21 ⇒ x=3"). The second step always says "State the requested value after checking it in the original condition" but never shows a check. | Show the elimination or substitution line and the check, for example 4(4)+2(3)=22. |
| C14 | n7-l1-513, n7-l2-518, n7-l2-523, n7-l3-512 | Low | A coefficient of 1 is printed: "5x+1y=6", "6x+1y=41" (H2 and solution), "3x+1y=18", "1x+5y=35". | Write `5x+y=6`, `x+5y=35`, and so on. |
| C15 | n7-l3-508, n7-l3-509, n7-l5-502 | Low | Proper nouns are lowercase: "For the mekong field station", "For the komodo research camp", "At the mekong field station". | Capitalise "Mekong" and "Komodo". |
| C16 | n7-l3-504, -511, -512, -518, -528 (7.7 D3) | Low | "A sensor point ( 3, k ) … Find k and hence locate the point on the graph." No graph is supplied and the location is not collected. The parentheses also contain stray spaces. | Remove "hence locate…", or add a graph and make the location part of the response. Write `(3, k)`. |
| C17 | n7-l1-501, -506, -516 (7.10 D1) | Low | "There are 7 helpers and 1 more seniors than juniors" is ungrammatical. H1 refers to "total", which the prompt does not use. | "There are 7 helpers altogether, and there is 1 more senior helper than junior helpers." |
| C18 | All 104 titles; for example n7-l1-504 "Jade Cedar Bay — Batik workshop: vertical-axis intercept" | Low | Learner-facing titles use invented place names and contexts that do not appear in the prompt (a batik workshop for a bare intercept question; "Heritage museum" for a stall in n7-l2-510). Several prompts add a context label that does nothing ("Cycling project check:", "For the kite festival, solve…"). | Use short neutral titles. Either use a context in the prompt or drop it. |

### Lesson findings

| # | Stable key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| L1 | n7-lesson-05 … n7-lesson-10 | Medium | **The lessons fall short of the 2,500-character baseline but pass the validator.** `lesson_note_depth_shortfalls` (`question_bank/src/question_bank/course_validation.py:109–136`) measures `len(json.dumps(sections))`, which counts JSON keys, `stable_key` values and response objects. The validator reports 3,042–3,361 characters per lesson, but the authored prose is 1,418–1,737 characters (05: 1,737; 06: 1,577; 07: 1,530; 08: 1,537; 09: 1,418; 10: 1,700). Each explanation is a single paragraph of about 300 characters. The coverage table in `LESSON_NOTES_CONTENT_STANDARD.md` records N7 as "meets the baseline". | Expand each lesson with misconception checks, a third example where several methods exist, and a fuller explanation per method. Separately, decide whether the validator should count prose rather than serialized JSON. That change affects every course and is outside this audit. |
| L2 | All six lessons | Low–Medium | The summary is the same boilerplate in every lesson ("Name the mathematical relationship, choose a method that preserves it…"). It is not a method checklist for the lesson's outcome. | Write a summary for each outcome, for example lesson 06: "reverse when multiplying or dividing by a negative; open circle for < and >, filled for ≤ and ≥; test a shaded value". |
| L3 | n7-lesson-09 | Medium | The objective "Factorise monic and simple non-monic quadratic expressions" has no non-monic example, and the bank has no non-monic item (C9). | Add a non-monic worked example, such as 2x²+5x−3=0, or remove the objective. |
| L4 | n7-lesson-05 | Low | The objective "identify their solution sets" and the title "meaning and solution sets" have no inequality example. Both examples are equations. | Add a short example testing candidate values in an inequality. |
| L5 | n7-lesson-08 (example 2), n7-lesson-10 (examples 1 and 2) | Low | Steps are skipped: "Substitute: 3x+2(9−x)=23. Then x=5 and y=4" and "Elimination gives x=5 and y=7". The standard requires explicit steps. | Show 3x+18−2x=23 ⇒ x=5, and the elimination line 8x+5y−5(x+y)=75−60 ⇒ 3x=15. |
| L6 | n7-lesson-05 recall | Low | The recall says "Enter 1 for yes or 0 for no". Encoding a yes/no answer as a number is awkward for learners. | Use a choice response if the schema supports one. Otherwise ask for the value of the left side. |

### Wording standard conflict (reported, not resolved)

The two standards disagree, and this audit does not decide between them:

- The **N2 audit** checked "Singapore/British English, unit wording and currency notation" and made
  money questions "use S$ consistently".
- **`LESSON_NOTES_CONTENT_STANDARD.md`** says the audience is "secondary-school students across
  Indonesia and Southeast Asia". It treats the Singapore syllabus as "a calibration and coverage
  reference" that "does not define the learner's country", and asks for "clear international
  English" and "contexts that work across Southeast Asia".

In N7, ten questions use S$ (7.10 D2: n7-l2-501, -510, -518, -519, -526; 7.10 D3: n7-l3-501,
-507, -515, -523, -524), and so does lesson 10 example 1. Their settings are Indonesian or regional
(an angklung club, a batik workshop, a Komodo research camp, a Mekong field station), so Singapore
dollars appear in an Indonesian setting. The British spellings ("factorise", "modelled") satisfy
both standards. Reviewers should choose one of three options: keep S$ as the N2 rule says (the
scholarship is Singapore-run), use a neutral "dollars", or use local currencies. Whichever they
choose should then go into house rules.

## Part 2 — Diagram findings

**Questions:** none of the 104 questions references a diagram.

**Lessons:** three SVGs, all from `generation_spec.renderer: nextscholar-chart-svg-v1`. Asset
paths are relative to `backend_resources/courses/g3_math/secondary_2/g2/v1/`, and all three
checksums match the lesson JSON.

| Asset | Lesson | `diagram_kind` | Viewed |
| --- | --- | --- | --- |
| `assets/n7-lesson-06-number-line.svg` | n7-lesson-06 | `inequality_number_line` | yes (960 px and 390 px) |
| `assets/n7-lesson-07-linear-graph.svg` | n7-lesson-07 | `linear_intercept_graph` | yes (960 px and 390 px) |
| `assets/n7-lesson-08-intersection.svg` | n7-lesson-08 | `simultaneous_intersection` | yes (960 px and 390 px) |

| # | Stable key | Asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | n7-lesson-08 | `assets/n7-lesson-08-intersection.svg` | Accuracy | **High** | The solution marker is not at the crossing. The marker is `circle cx=480 cy=210`. The orange line (180,330)→(780,90) passes through (480,210), but the teal line (180,110)→(790,355) is at y≈230.5 when x=480. The true crossing is ≈(454.4, 220.2), so the marker is about 28 px away (2.8 marker radii) and sits visibly on the orange line only. The title says "The intersection satisfies both equations", and the point shown satisfies only one. The alt text says the lines cross "at their common simultaneous-equation solution". | Move the marker to (454, 220). The better fix is to redraw from data (see D2) so that the point is computed rather than placed by hand. |
| D2 | n7-lesson-08 | same | Accuracy | Medium | There are no axis labels, ticks, scale, origin or line equations, and the label "common solution (x, y)" is generic. Neither line matches the lesson's examples, although explanation 3 tells learners to "read the intersection using the stated scale". The alt text and `generation_spec` contain no data, so nothing can be checked against the lesson. | Plot lesson example 2, x+y=9 and 3x+2y=23, which meet at (5, 4) and both lie in the first quadrant. Use unit ticks from 0 to 12 on both axes, label each line with its equation and label the point "(5, 4)". Put the equations, window and point in `generation_spec`, and describe them in `alt_text`. |
| D3 | n7-lesson-08 | same | Neatness | Medium | The label collides with a line. The bounding box of "common solution (x, y)" is x 500–701, y 182–205. The orange line runs from y=202 to y=194 across x 500–520, so it cuts through the first letters. This is visible in the render. | Place the label in the clear wedge below the crossing, for example `text-anchor="middle"` at (454, 305) with a short leader line to the point. Both lines are clear of y 283–305 between x 355 and 555. |
| D4 | n7-lesson-07 | `assets/n7-lesson-07-linear-graph.svg` | Accuracy | Medium | The two axes have different scales and no ticks. The x-axis uses 183.3 px per unit ((3,0) is 550 px from the origin) and the y-axis uses 46.7 px per unit ((0,6) is 280 px up), a ratio of 3.9 to 1. The line 2x+y=6 has gradient −2 but is drawn with a visual slope of −0.51, so a steep line looks shallow. Lesson explanation 3 discusses gradient, which makes this misleading. | Use equal unit scales, for example 45 px per unit with x from −1 to 7 and y from −1 to 7. Add numbered unit ticks and an origin label. |
| D5 | n7-lesson-07 | same | Accuracy | Medium | The line is drawn only between the intercepts, from (170,110) to (720,390). Explanation 2 of the same lesson says "extend the line rather than drawing only the segment between the points". The diagram contradicts the text. | Extend the line beyond both intercepts, for example from x = −0.5 to x = 3.5, and keep the two plotted points marked. |
| D6 | n7-lesson-07 | same | Neatness | Low | There is no origin label and there are no arrowheads on the axes. The y-axis has a stub below the origin (y 390→420) but the x-axis has no matching stub on the left. | Add an origin label and arrowheads, and make the axis extents symmetric. |
| D7 | n7-lesson-06 | `assets/n7-lesson-06-number-line.svg` | Accuracy | Low | Correct as drawn: the open circle is at 3 and the shading goes left, which matches the alt text and the title. However, ticks appear only at 0, 3 and 6 (200 px per 3 units), with no unit ticks and no negative labels. The axis has an arrowhead on the left but not on the right, so the right end looks like a closed segment. | Add unit ticks from −3 to 7 with labels, and an arrowhead at both ends. |
| D8 | n7-lesson-06 | same | Accuracy (teaching match) | Low | The diagram shows x<3, which none of the lesson's examples uses. Example 1 asks learners to "describe its number-line graph" for x≤4 (a filled circle) and example 2 gives x<−4. No diagram shows a closed endpoint, although explanation 3 contrasts the two. | Draw two panels from the lesson's examples: x≤4 with a filled circle and x<−4 with an open circle. Update the alt text. |
| D9 | n7-lesson-06, n7-lesson-07 | both | Neatness | Low | Tick labels are not centred on their ticks. The SVG has no `text-anchor`, so "0" spans x 270–281 for a tick at 280, and "3" and "6" have the same offset (each about 5 px left of centre). | Use `text-anchor="middle"` with x equal to the tick position. |
| D10 | all three | all three | Neatness | Medium | They are hard to read on a phone. At a width of 390 px the scale factor is 0.406, so 20 px labels render at about 8 px and 26 px titles at about 11 px. The tick numbers in the 390 px renders are barely legible. On the number line, the content covers y 38–269 of a 460 px height, leaving the lower 40% empty and shrinking everything further. | Use labels of at least 28 px on the 960-wide canvas and crop the number-line `viewBox` to about 960×300. |
| D11 | all three | all three | Accuracy (metadata) | Low | The SVG `<desc>` is generic ("… teaching diagram") and is what screen readers get through `aria-labelledby`. The alt text for lesson 08 is not specific. `generation_spec` holds only `renderer`, `diagram_kind` and `lesson_key`, so there is no plotted data to validate against. | Write a specific `<desc>` and alt text. Store the plotted equations, window and key points in `generation_spec`. |

**Answer leakage:** none. These are teaching diagrams, and no lesson recall check or practice
question asks for a value that a diagram displays.

### Questions that would benefit from a diagram

N7 has no `diagram_audit.json`, so no question records a decision to stay text-only. These clearly
need a diagram:

- **7.6 number-line representation:** no question shows or asks about a number line (see C3).
  Add number-line choice items, starting with the D2 "closed endpoint" and D3 "reversing an
  inequality" families.
- **7.7 D3 "coordinate on a line"** (n7-l3-504, -511, -512, -518, -528): the prompt says
  "locate the point on the graph", but there is no graph (see C16).
- **7.8 graphical method:** no question uses it. Add at least one item at D2 or D3 that reads an
  intersection from a scaled graph and checks it algebraically.

If diagrams are added, create `backend_resources/question_bank/g3_math/secondary_2/n7/v1/diagram_audit.json`
in the same form as the G2 file.

## Root-cause patterns

1. **Hand-placed chart template with no data model or validation (affects 3 of 3 N7 diagrams,
   and 9 diagrams across the repository).** All three N7 SVGs share one template: the same
   `<style>` block (`.a`, `.b`, `.t`, `.s`), `rx="28"`, a generic `<desc>…teaching diagram</desc>`
   and no `text-anchor`. The same template is used by six Secondary 2 S1 diagrams
   (`s1-lesson-05-distributions.svg` … `s1-lesson-10-grouped-mean.svg`). None of the source for
   `nextscholar-chart-svg-v1` is in the repository: `scripts/recalibrate_geometry_content.py` only
   emits `nextscholar-geometry-svg-v1` with hard-coded path strings. The coordinates therefore
   appear to be placed by hand rather than computed from equations, which explains D1 (the marker
   is off the crossing), D4 (unequal axis scales) and D9 (labels off-centre).
   `geometry_validation.geometry_diagram_issues` runs only angle checks (when `diagram_kind ==
   "angle_types"` or `angle_markers` is declared) and forbidden-label checks, so chart diagrams
   receive only checksum and path validation. **Likely fix:** a small chart renderer that takes
   equations, a window and points from `generation_spec`, plus a validator that recomputes
   intersections, intercepts and point positions from that spec. The six S1 diagrams were **not**
   audited here and should be checked for the same problems.
2. **Template-generated question bank.** One offline generator (`codex-offline-n7-v1`, prompt
   `math-question-authoring-v2`) produced 29 templates and filled each with consecutive numbers.
   This explains C2–C9 together: the prompts give the answer form, difficulty labels share
   structures, numbers are mirrored across outcomes, the answer range is narrow, and the solutions
   and titles are boilerplate. Rewriting the templates fixes these more efficiently than editing
   each item.
3. **Validator counts serialized JSON as authored characters** (L1). This affects every course,
   not just N7.

### Template families

| Outcome | D1 | D2 | D3 | D4 | D5 |
| --- | --- | --- | --- | --- | --- |
| 7.5 | checking equality ×4 | balanced equation ×5 | brackets ×5 | equivalent solution sets ×3 | identity ×1 |
| 7.6 | inequality boundary ×4 | closed endpoint ×5 | reversing ×5 | compound integer count ×3 | compound integer count ×1 |
| 7.7 | y-intercept ×4 | x-intercept ×5 | coordinate on a line ×5 | parameter through point ×3 | — |
| 7.8 | symmetric pair ×3 | eliminate (add) ×6 | substitution ×5 | known intersection ×2 | count pair ×1 |
| 7.9 | roots from factors ×3 | monic factorise ×5 | rearrange then factorise ×6 | roots → constant ×2 | root difference ×1 |
| 7.10 | count pair ×3 | item prices ×5 | admission ×5 | parcels ×3 | two-digit ×1 |

## Not verified

- The six S1 diagrams that share the chart template are outside this topic's scope and were not
  rendered or checked.
- Rendering used headless Chromium only. Glyph positions may differ slightly in other renderers,
  but the collision in D3 is visible in the source coordinates as well as in the render.
- No live in-app rendering of the lessons or questions (KaTeX or the app layout) was checked. The
  390 px check scaled each SVG on its own.
- Difficulty judgements against the Sec 3-entry scholarship test are a reviewer's assessment from
  the item demands, not a statistical calibration.
