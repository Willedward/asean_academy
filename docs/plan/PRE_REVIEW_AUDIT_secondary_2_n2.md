# Secondary 2 N2 (Ratio and proportion) technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_2/n2/v1/`
(batches B001–B004), both Secondary 2 N2 lessons (`n2-lesson-04`, `n2-lesson-05`) and both
diagrams those lessons reference

**Lesson location:** there is no `n2/` course folder for Secondary 2. Course metadata
(`backend_resources/courses/g3_math/secondary_2/g2/v1/course.json`, unit `g3-sec2-n2`,
position 3) places the lessons in `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/`
as `n2-lesson-04.json` (outcome 2.4) and `n2-lesson-05.json` (outcome 2.5). The pools are in
`.../g2/v1/question_pools/n2.json` and the SVGs are in `.../g2/v1/assets/`.

**Out of scope:** `.../secondary_2/n2/v2/` holds four diagnostic questions (n2-l2-951, n2-l2-953,
n2-l3-952, n2-l3-954). The audit was limited to v1, so they were not audited.

**Decision boundary:** this audit only reports findings. It changes no questions, lessons,
SVGs, manifests, claims or review states, and records no Mathematics or editorial approval.
All 104 questions and both lessons are `draft`. All four batches are `ready_for_review`, with
`mathematics: pending` and `editorial: pending`. No approvals exist, so none were changed.

**Audience note:** the current audience standard (`docs/plan/LESSON_NOTES_CONTENT_STANDARD.md`)
is secondary students across Indonesia and Southeast Asia. Here they are preparing for the
Sec 3-entry ASEAN Scholarship test. Section 6 lists where this conflicts with the
Singapore-specific rules behind the N2 calibration audit.

**Severity scale:**

- **Critical:** a learner who answers correctly is marked wrong, or the answer is wrong.
- **Major:** blocks a fair assessment (an ambiguous or degenerate task, a duplicate inside a
  pool, a difficulty label the task does not earn, a hint that does the method, or a diagram
  that shows a wrong relationship).
- **Minor:** wording, notation, calibration or polish.

## 1. Counts

| Item | Checked | Notes |
| --- | ---: | --- |
| Questions | 104 | One part each; 52 for outcome 2.4 and 52 for 2.5. Difficulty mix: d1 21, d2 31, d3 31, d4 16, d5 5 |
| Lessons | 2 | 4 worked examples, 2 active-recall checks and both verification notes recomputed |
| Diagrams, graphs or charts referenced | **2** | Both are lesson assets. No N2 question references an asset (`assets: []` in all 104) |
| Diagrams rendered and viewed | **2 of 2** | Rendered with the pre-installed Playwright Chromium to PNG in the session scratchpad (outside the repo). Viewed at 940 px and at a 390 px CSS width (phone) |
| `diagram_audit.json` for N2 | none | Only the geometry banks (Sec 1 G1, G5 and Sec 2 G2) have one |

Validators run on this branch (read-only, with the virtual environment outside the repo):

- `question-bank validate .../secondary_2/n2/v1`: 104 questions, 0 errors, 0 warnings
- `question-bank course-validate`: 0 errors, 0 warnings

The validators pass, but they do not catch any finding below.

## 2. Answer verification summary

I recomputed every canonical answer with exact rational arithmetic (`fractions.Fraction`). A
script parsed the numbers straight from each prompt and did not read the solutions. The script
is in the session scratchpad and was not committed. The first pass had 8 mismatches. All 8
were errors in my parser, for example reading "Two landmarks" as the number 2. I checked each
by hand and fixed the parser, and the final run shows **104 of 104 match**.

All 104 worked solutions reach the canonical answer. No solution rounds an intermediate value
too early. Every stated condition is used as the solution uses it ("equally productive",
"continuous operation", "divisible task"). No `accepted_answers` list is wrong; all 104 are
empty.

Lesson checks, all correct:

| Lesson item | Result |
| --- | --- |
| L04 worked example 1: 7.4 cm at 1 : 50 000 | 3.7 km |
| L04 worked example 2: 3.2 cm × 2.4 cm at 1 : 25 000 | 0.48 km². The verification note (7.68 cm² × 25 000² = 0.48 km²) is correct |
| L04 active recall: 6 cm at 1 : 20 000 | 1.2 km, and the accepted `6/5` is valid |
| L05 worked example 1: 210 g per 75 cm, so for 130 cm | k = 2.8 g/cm, giving 364 g |
| L05 worked example 2: 8 pumps × 15 h, so for 12 pumps | 10 h |
| L05 active recall: 12 workers × 15 days, so for 20 workers | 9 days |

Both lessons meet the baseline lesson-note gate. Each has 8 sections, at least 3 explanations,
2 worked examples with verification notes, 1 deterministic active recall and 1 summary. They
have 4,266 and 4,555 characters of learner-visible prose and LaTeX (minimum 2,500).

## 3. Content findings

### 3.1 Critical

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-01 | 14 questions with non-terminating answers: n2-l1-517 (63/13), n2-l2-508 (32/3), n2-l2-514 (72/7), n2-l3-505 (95/9), n2-l3-506 (77/9), n2-l3-507 (88/7), n2-l3-508 (30/11), n2-l3-520 (2/3), n2-l3-528 (14/3), n2-l3-530 (105/13), n2-l3-531 (120/7), n2-l4-503 (70/13), n2-l4-511 (40/9), n2-l4-516 (44/7) | **Critical** | Each prompt says "Enter the exact numerical value only" but does not say a fraction is expected. `checking._fraction` removes every space before parsing. So a correct mixed number is read as a different number and **silently marked wrong, with no format error**. I ran the live checker: `10 2/3` against 32/3 is read as 102/3 and returns `correct: False`. `4 11/13` against 63/13 does the same. A rounded decimal (`10.67`, `0.67`) is also marked wrong. These are time, mass and day answers, where a learner would naturally give a mixed number or a decimal. Seven of the 14 are in pools: l1-517 and l3-520 (checkpoint); l2-508, l2-514, l3-505 to l3-508 (lesson-05 practice); the rest are in reserve. | Pick one, apply it to all 14, and decide before review. **(a)** Change the numbers so each answer terminates, which is preferred for d1–d2 (l1-517, l2-508, l2-514). **(b)** Switch to `rounded_sf` with precision 3 and say "Give your answer correct to 3 significant figures". **(c)** Keep the exact answer and say "Give your answer as an improper fraction in its simplest form". Separately, the checker should reject input of the form `<int> <int>/<int>` with a format error instead of joining the digits. Today that same bug affects every bank. |

### 3.2 Major

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-02 | n2-l1-502, n2-l1-508, n2-l1-514; n2-l2-501, n2-l2-509, n2-l2-517, n2-l2-525 | Major | **Exact duplicates.** Once the meaningless "Use the data from…" prefix is removed (M-01), the prompts are word-for-word identical. The first three are "1 cm represents 6 km" (answer 600000). The other four are "1 : 125,000, a heritage walk measures 10 cm" (answer 12.5). Each copy came from a different batch. **The `n2-lesson-04-practice` pool contains two duplicate pairs:** l1-502 and l1-508 (positions 2 and 5), and l2-501 and l2-509 (positions 7 and 11). The `n2-unit-checkpoint` then repeats l1-514 and l2-517, so the checkpoint reuses lesson practice items verbatim. l2-525 is a fifth copy, in the reserve pool. | Keep one of each and rewrite the others with a different numerical structure. For example: a statement scale given in metres ("1 cm represents 250 m", so 1 : 25 000), a reverse task (find the map length), or a non-integer scale denominator. Make sure the practice and checkpoint pools no longer share any prompt. |
| C-03 | n2-l2-516 | Major | **Degenerate task.** "…covers a fixed route in 3 hours at a constant speed of 40 km/h… find the time in hours at **40 km/h**." The speed does not change, so the answer, 3, is in the prompt. The task cannot assess inverse proportion. The item is in `n2-lesson-05-practice`. | Change the second speed, e.g. to 60 km/h for an answer of 2 h, or 50 km/h for 2.4 h. |
| C-04 | Difficulty ladder (lists below) | Major | **The labelled difficulty is not earned.** (1) The d3 groups "Scale a direct proportion" (l3-505, -513, -521, -529) and "Test and extend a proportional table" (l3-507, -515, -523, -531) are the same one-step y = (y₁/x₁)·x₂ as the d1 group "Direct proportion value" (l1-504, -510, -516, -520). l3-513 (10 tiles, then 20) and l3-523 (x = 5, then 10) only double. (2) The "remaining worker-days ÷ new team size" structure appears at **d3** (l3-508, -520, -528), **d4** (l4-503, -508, -512, -516) and **d5** (l5-501, -503, -505), with no increase in demand. House rule v2 requires d4–d5 to involve "method selection, constraints, justification or sustained synthesis". (3) The d4 group "Workload, team size and time" (l4-507, -511, -515) is the single step t = total ÷ (workers × rate). | Re-label or redesign. Suggestions: move the one-step d3 items to d1–d2. For d4–d5 2.5 items, build in a genuine extra step. Examples: workers join **and** leave at different times; find the number of extra workers needed to meet a deadline (with a ceiling and a justification); a joint direct/inverse model. Either re-label the workload group d2, or add a constraint such as a deadline or a minimum team size. |
| C-05 | n2-l3-503, -511, -519, -527; n2-l3-504, -512, -516, -524; n2-l4-502, -506; n2-l4-503, -508, -512, -516; n2-l5-501, -503, -505 | Major | **Stage-2 hints carry out the method-marked steps.** House rule v2 limits stage 2 to "an intermediate setup". Examples: l3-503 H2 "The real side lengths are 3 km and 3.5 km", which leaves one multiplication for a 3-mark item. l4-502 H2 "The actual side is 6 km and the map side is 2 cm". l5-501 H2 "Remaining work is 10 × (12 − 6) worker-days and is shared by 8 workers", which is the whole M4 of a d5 item. More generally, most d1–d2 stage-2 hints give the complete calculation ("Calculate 54 ÷ 6", "First calculate 4 × 9, then divide by 8"). | For d3–d5 items, make stage 2 a setup prompt that leaves the method to the learner. Examples: "Write the real length of each side in kilometres." "Work out how many worker-days were completed before the change." Do not state the resulting values. For d1–d2 items, consider naming the operation without the numbers. |
| C-06 | Near-duplicate clusters (table below) | Major | **Same structure, and often the same answer, in the same or linked pools.** House rule v2 bans repeating "context, operation pattern and numerical structure". | See the table. |
| L-01 | n2-lesson-04 (`n2-24-recall`), n2-lesson-05 (`n2-25-recall`) | Major | **The active-recall `unit.required: true` setting has no effect.** `progress_service` passes the section response to `check_answer`, which never reads `unit`. I ran the live checker: `1.2` is correct, but `1.2 km` and `1.2km` return "Enter a number, decimal, fraction, or percentage." `9 days` returns the same. The prompt "Enter the real length in kilometres" does not say whether to type the unit. A learner who follows `required: true` and types the unit gets an error message. The sibling Secondary 1 N3 audit (finding C-01) found the same root cause. | Fix it in the checker by stripping and validating an accepted unit when `unit` is present. Until then, set `required: false` and append "Enter the number only" to both prompts. |

C-04 and C-06 near-duplicate clusters:

| Cluster | Items (pool) | Evidence | Recommendation |
| --- | --- | --- | --- |
| Compare two map scales, ratio 5 : 4 | l4-501 (checkpoint), l4-505 (checkpoint), l4-510 (reserve), l4-514 (reserve) | All four have denominators in the ratio 5 : 4. l4-505 (7 cm, 1 : 100 000 to 1 : 80 000) and l4-510 (7 cm, 1 : 50 000 to 1 : 40 000) both give **8.75**. Two of the four are in the checkpoint. | Vary the denominator ratio (for example 1 : 25 000 to 1 : 60 000, which makes the map length shrink). Give l4-510 a different answer. |
| 3–4–5 map offset | l4-509, l4-513 (both reserve) | Both say "3 cm east and 4 cm north". | Use a different Pythagorean triple (5–12–13 or 8–15–17) or a non-integer hypotenuse with a stated rounding. |
| 250 m per map cm | l3-502 (L04 practice), l3-510 (L04 practice), l3-518, l3-526 (reserve) | All four infer 1 cm = 250 m. Two are in the same practice pool. | Vary the scale (for example 1 cm = 400 m, or 5 cm represents 3 km). |
| Three-section journey at 1 : 50 000 | l3-501, l3-509 (L04 practice), l3-517, l3-525 (reserve) | Same scale and structure. l3-525 ("3 cm each") is easier than the others. | Vary the scale. Mix units in one item (for example one section given in mm). |
| Direct proportion, k = 2, 12 items, answer 24 | l2-505 (L05 practice), l2-521 (checkpoint) | 6 → 12 units and 8 → 16 units, then 12 items in both. Same answer. | Change the l2-521 numbers. |
| Direct proportion, k = 6, 15 items, answer 90 | l2-513 (L05 practice), l2-529 (reserve) | 42 / 7 and 54 / 9, then 15. Same answer. | Change one. |
| Square site, map area 4 cm² | l3-504 (L04 practice), l3-524 (reserve) | Both answers are 4. | Change one. |
| Lesson-05 worked example 2 against a question | n2-lesson-05 WE2 (8 pumps, 15 h, then 12 pumps), n2-l3-530 (7 pumps, 15 h, then 13 pumps; reserve) | Same context, the same 15 h and the same structure. | Change the context or numbers of l3-530. |

### 3.3 Minor

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| M-01 | 61 questions | Minor (widespread) | Each opens with "Use the data from a community planning study." (26), "…an environmental field study." (23) or "…a regional logistics study." (12). No data or study follows. Even pure algebra items carry it, e.g. n2-l1-510 "…y is directly proportional to x…". A learner may look for missing information. This generator artefact also hid the exact duplicates in C-02. | Delete the sentence from all 61 prompts. If a context is wanted, write it into the task itself. |
| M-02 | n2-l2-503, -511, -519, -527 ("4 cm = 400 m"); n2-l3-502, -510, -518, -526 ("1 cm = 250 m"); n2-lesson-04 `n2-24-meaning` ("1 : 50 000 = … = 1 cm : 500 m") | Minor | These solutions write an equals sign between a map length and a real length. The lesson itself says to keep the two separate ("prevents the common error of comparing centimetres directly with kilometres"), and its first display ends in a ratio with different units on each side. | Write "4 cm represents 400 m" (or use `\mapsto`). End the lesson display at `1\text{ cm}:50\,000\text{ cm}` and give "1 cm represents 500 m" in the text. |
| M-03 | 29 solutions with comma thousands separators (l1-501, -503, -507, -509, -513, -515, -518; l2-501, -502, -509, -510, -517, -518, -525, -526; l3-501, -504, -509, -512, -516, -517, -524, -525; l4-501, -502, -505, -506, -510, -514) | Minor | KaTeX treats `,` in maths mode as punctuation, so `1,250,000` renders as "1, 250, 000". I confirmed this in a KaTeX render. The same lines mix `100\,000` and `600000` (e.g. n2-l1-502). | Use `\,` grouping (`1\,250\,000`) everywhere, matching the lessons. Also see section 6, conflict 2. |
| M-04 | n2-l1-517, n2-l2-514, n2-l3-506, n2-l3-508, n2-l3-530, n2-l4-503 | Minor | Solutions contain a step that says nothing, such as `y=\frac{63}{13}=\frac{63}{13}`. | Delete the repeated term. |
| M-05 | n2-l3-507, -515, -523, -531 | Minor | The title is "Test and extend a proportional table". The prompt gives one pair, says "the relationship is direct proportion", and shows no table. There is nothing to test. | Give a 3- or 4-row table. Ask the learner to confirm y/x is constant, or to identify the row that breaks it, before extending it. This also fixes C-04 for these items. |
| M-06 | n2-l3-505, -513, -521 ("ceramic tiles … mass of 19 items"); n2-l3-529 ("shipping tiles") | Minor | The noun changes from "tiles" to "items" within one prompt. "Shipping tiles" is not a natural phrase. | Use "tiles" throughout. Use "floor tiles" or "ceramic tiles". |
| M-07 | n2-l2-503, -511, -519, -527; n2-lesson-04 | Minor | Hectares are defined only in stage-2 hint 2. The lesson never mentions hectares. The current standard asks lessons to "explain unfamiliar terminology". | Add "1 hectare (ha) = 10 000 m²" to lesson 04, section `n2-24-area`, or state it in the prompts. |
| M-08 | n2-lesson-05 | Minor | 10 bank items (d3–d5, C-04) depend on "the team changes part-way through". l4-504 uses joint proportion (output ∝ machines × time). The lesson teaches neither: both worked examples are single-step. | Add a short worked example: work done before the change, then the remaining worker-days, then the new team. Add one sentence on proportion to two variables. |
| M-09 | n2-lesson-04 `n2-24-errors` | Minor | The lesson says "Give a sensible number of significant figures based on the map measurement". Every 2.4 question asks for an exact value and none asks for rounding. | Either add a 2.4 item that requires rounding, or soften the advice. |
| M-10 | Batches g3-sec2-n2-b001 to b004 | Minor (process) | All four batches cite `house-rules-v1.json` and `math-question-authoring-v1`. They were created on 30 September 2026, before the N2 calibration audit introduced house rules v2. v2 makes outcome alignment, duplicate avoidance, hint boundaries and independent verification explicit. C-02 to C-06 are exactly those v2 categories. | Before review, re-check the corrected items against v2. Record the rules version used for the corrections in the batch manifests. |

## 4. Diagram findings

Both N2 diagrams are lesson assets. **No N2 question has a diagram.**

| Asset key | Path | Referenced by | Rendered | Viewed |
| --- | --- | --- | --- | --- |
| `n2-lesson-04-map-scales` | `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/n2-lesson-04-map-scales.svg` | n2-lesson-04, section `n2-24-distance` | yes (940 px and 390 px) | yes |
| `n2-lesson-05-proportion-models` | `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/n2-lesson-05-proportion-models.svg` | n2-lesson-05, section `n2-25-recognise` | yes (940 px and 390 px) | yes |

Both SHA-256 hashes match the lesson JSON. Each alt text and `<desc>` agrees with what is
drawn. Neither diagram shows an answer the learner must find: the lesson-04 values (500 m,
1 km²) are not the active-recall answer (1.2 km).

**Values checked in n2-lesson-04-map-scales**, all correct:

- 1 cm × 50 000 = 50 000 cm = 500 m.
- 2 cm × 50 000 = 100 000 cm = 1 km.
- 4 cm² × 50 000² = 10¹⁰ cm² = 1 km².

**Values checked in n2-lesson-05-proportion-models:**

- The direct-proportion line runs from (80, 380) to (380, 125), a slope of 0.85.
- Both orange dots, (180, 295) and (280, 210), lie exactly on the line. Their x-offsets are
  100 and 200, so x doubles and y doubles.

| ID | Lesson / asset | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D-01 | n2-lesson-04 / `n2-lesson-04-map-scales` | Accuracy | Major | The two map lengths are drawn at inconsistent scales. The "1 cm on map" bar runs from x = 60 to 240 (**180 units**), but the side of the "2 cm" map square is **120 units** (x = 70 to 190). The learner sees 1 cm drawn half as long again as 2 cm, in a figure whose purpose is to compare lengths. | Use one scale for both map lengths, for example 60 units per cm. Draw the bar from x = 60 to x = 120 and move the tick at x = 240 to x = 120. Then start the arrow at x ≈ 160 and keep the 120-unit square. |
| D-02 | n2-lesson-04 / `n2-lesson-04-map-scales` | Accuracy / neatness | Major | The side lengths are written at the centre of each square: "2 cm" at (100, 360) and "1 km" at (493, 364). A label in the middle of a filled square reads as the square's area or name, not its side, and the figure is about the difference between length and area. The real square has no area label inside it, and the map square shows "2 cm" where the area would normally go. | Move each length onto a side, with a dimension line. For example, put "2 cm" centred above the top edge at (130, 290), and "1 km" above the real square's top edge at (530, 276). Put the areas at the centres: "4 cm²" and "1 km²". The captions below can then be shortened to "on map" and "in reality". |
| D-03 | n2-lesson-04 / `n2-lesson-04-map-scales` | Neatness | Major | It is not readable on a 390-px phone. The 940-wide viewBox is scaled by 0.415, so the 17–18-unit labels ("1 cm on map", "length factor: 50 000", "area factor: 50 000²") render at about **7 px**. I confirmed this in the 390-px render. | Either raise the minimum font size to about 28 units (12 px at 390), or rebuild the figure as a narrower stacked layout (viewBox about 600 × 640) with the length row above the area row and the "Use both dimensions" notes below. |
| D-04 | n2-lesson-04 / `n2-lesson-04-map-scales` | Neatness | Minor | The caption "1 km² in reality" has its baseline at y = 462. Its glyph box ends at y = 466, inside the 24-unit rounded corner of the 470-high background. It is not clipped, but it touches the lower edge. | Raise the real square by about 16 units (y = 270) or make the viewBox 490 high. |
| D-05 | n2-lesson-04 / `n2-lesson-04-map-scales` | Accuracy | Minor | The two squares are schematic (the real 1 km square is drawn only 25% larger than the 2 cm map square), but there is no "not drawn to scale" note. The geometry diagrams generated by `scripts/recalibrate_geometry_content.py` carry one. | Add the note "Not drawn to scale" at the lower right. |
| D-06 | n2-lesson-05 / `n2-lesson-05-proportion-models` | Accuracy | Major | The curve labelled "xy = k" and "y = k/x" is a hand-placed cubic Bézier, `M575 130 C600 235 660 315 850 355`, not a hyperbola. Taking the origin as (545, 380) and sampling 41 points along the path, x·y varies from **7 500** at both ends to **about 12 000** in the middle, a spread of more than ±20%. The two teal dots are also about 5 units off the curve. Dot (625, 245) gives 80 × 135 = 10 800 and dot (745, 329) gives 200 × 51 = 10 200, so even they do not quite keep xy constant. The lesson says "x doubling makes y halve", and the figure is the learner's model of that. | Generate the path from y = k/x. For example, use k = 9 600 (in plot units), with x from 40 to 320 (y from 240 down to 30), sampled every 10 units as a polyline. Place the two dots at x = 60 and x = 120, giving (605, 220) and (665, 300), so x doubles and y halves exactly. This mirrors the direct graph's dots, where x doubles and y doubles. |
| D-07 | n2-lesson-05 / `n2-lesson-05-proportion-models` | Neatness / accuracy | Minor | The note "passes through (0, 0)" sits at (270–422, 79–98), next to the **top end** of the line. That is about 330 units from the origin, so it reads as a description of the line's top end. There is no "O" or "(0, 0)" label at the origin. "does not meet an axis" also floats above the right-hand plot instead of beside the curve's tails. | Label the origin "O" at about (62, 402). Replace the top note with "passes through O", placed below the axis row at about (92, 456). It then sits about 10 units below "y = kx" and stays inside the 470-unit viewBox. Move "does not meet an axis" to sit just above the curve's right-hand tail, at about (700, 285). The curve there is at y ≈ 303–329, which leaves a gap of at least 14 units. |
| D-08 | n2-lesson-05 / `n2-lesson-05-proportion-models` | Neatness | Major | It is not readable on a 390-px phone. At 0.415 scale, the 15-unit notes render at about **6 px** and the 17–18-unit labels (`y ÷ x = k`, `xy = k`, `y = kx`, axis letters) at about 7 px. | As in D-03: use at least about 28-unit text, or stack the two graphs vertically in a viewBox about 470 wide. |

No overlaps, clipped text or stray marks were found in either SVG. I checked every `<text>`
bounding box against every shape and every other label at 940 px.

## 5. Root-cause pattern

**Hand-authored "renderers" with no generator.** The two N2 SVGs declare `renderer:
nextscholar-scale-svg-v1` and `nextscholar-proportion-svg-v1`. Neither renderer exists
anywhere in the repo: I searched `scripts/`, `question_bank/src/` and `services/`.
`scripts/recalibrate_geometry_content.py` only emits `nextscholar-geometry-svg-v1`, for G
topics. Its "scale" and "proportion" kinds are similarity templates for the Sec 2 G2 outcomes,
not these N2 files. The coordinates were therefore typed in by hand, which explains each
accuracy finding:

- nothing ties drawn lengths to one units-per-cm scale (D-01);
- nothing computes the curve from y = k/x (D-06);
- nothing enforces label anchoring or font sizes (D-02, D-03, D-07, D-08).

**The validator does not check these diagram kinds.** `geometry_validation.geometry_diagram_issues`
runs on every asset but only checks three things:

- angle geometry when `diagram_kind == "angle_types"`;
- arcs listed in `generation_spec.angle_markers`;
- `forbidden_visible_labels`.

Neither N2 asset declares any of these, so validation confirms only that the SVG parses and
that its SHA-256 matches. Passing validation is no evidence of correctness here.

**Scope of the pattern:** both N2 diagrams (2 of 2). Across all lesson JSON in
`backend_resources/courses/g3_math/`, 25 assets declare renderers that have no code in the
repo: statistics ×10, chart ×5, coordinate ×5, probability ×2, scale, proportion and balance.
They are likely to share the same weaknesses. D-03 and D-08 (a 940-wide canvas with
17–18-unit text) probably affect any lesson diagram built on that canvas. They were not
audited here.

**Recommended fix:**

- Add a small data-driven chart renderer, so plotted points come from the function or data
  with one declared units-per-unit scale.
- Add a `chart_validation` check for `kind: chart` assets. It should check declared points
  against the path, require a minimum font size of 28 units for a 940 viewBox, and reject text
  bounding boxes outside the viewBox.
- Regenerate both N2 SVGs under revisioned filenames, as the geometry standard requires.

**Question-side pattern:** findings C-02, C-04, C-05, C-06 and M-01 all come from a
30-template generator. Every template was instantiated 2–4 times, and the generator varied
only the numbers and a context sentence. They were authored under house rules v1 (M-10).

## 6. Conflicts between the N2 audit's Singapore-specific rules and the current audience standard

These are reported for a decision; neither side is assumed to be right.

1. **Locale and currency.** House rules v2 set `locale: en-SG`, `language_variant:
   Singapore/British English` and `currency: SGD` ("Use S$…"). The N2 calibration audit
   applied these rules. `LESSON_NOTES_CONTENT_STANDARD.md` says the Singapore syllabus "does
   not define the learner's country" and asks for "clear international English" with
   Southeast Asian contexts. **Effect on this topic: none yet.** No N2 question or lesson uses
   currency, Singapore place names or Singapore-only terms. The British spellings (centimetre,
   kilometre, programme) fit both rules. The blueprint's `"course": "Singapore G3
   Mathematics"` and its Singapore school papers as style references are consistent with the
   standard's "calibration reference" role.
2. **Thousands separators.** 35 prompts use commas ("1 : 25,000"), 4 use spaces ("1 : 10
   000") and 3 use none ("6250000 m²"). Both lessons use spaces. Neither rule set names a
   convention, but this matters for this audience. In Indonesia and Vietnam, the comma is the *decimal* separator, so "1 : 25,000" can be read as
   1 : 25. The checker also rejects comma input: `300,000` gets a format error, while `300 000`
   is accepted. **Suggested decision:** use SI space grouping (`25 000`, `1\,250\,000`) in all
   learner-facing text, as the lessons already do. Optionally, show "use a space or no
   separator" near numeric inputs.
3. **Decimal comma input.** `1,2` returns a format error rather than being marked wrong. That
   is acceptable, but the error message does not say to use a decimal point. Consider "Use a
   decimal point (1.2), not a comma" for this audience.

## 7. Text-only questions where a diagram would clearly help

No `diagram_audit.json` exists for N2, which is not a geometry topic, so none of the 104
questions has a recorded diagram decision. All are text-only and every relationship is stated
unambiguously, so none *needs* a diagram. Optional candidates:

- n2-l5-502 and n2-l5-504: a reserve containing an inner rectangle, where the area outside is
  asked for. A schematic would help learners see the subtraction.
- n2-l4-509 and n2-l4-513: map offsets 3 cm east and 4 cm north, where a right-triangle sketch
  supports the Pythagoras step.

If diagrams are added, the answers (17, 12, 1.25, 2.5) and the intermediate map distances
(5 cm, 68 cm², 48 cm²) belong in `forbidden_visible_labels`.

## 8. Not verified

- The learner-facing apps were not run. KaTeX output and checker behaviour were checked
  directly (KaTeX from the repo's vendored copy; `question_bank.checking.check_answer`), not
  through the practice or lesson UI. Whether question `title` values are shown to learners
  (relevant to M-05) was not confirmed.
- The diagrams were rendered in Chromium with its default `system-ui` font. Glyph widths, and
  so the label bounding boxes, may differ slightly on iOS and Android.
- The v2 diagnostic questions (see **Out of scope** at the top) and the other 25 lesson diagrams with unimplemented
  renderers (section 5) are outside this audit.
