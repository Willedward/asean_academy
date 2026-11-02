# Secondary 1 S1 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_1/s1/v1/`
(batches B001–B004) and the four S1 lessons, `s1-lesson-01` to `s1-lesson-04`. The lessons
were found through the `g3-sec1-s1` unit in `course.json` (outcomes 1.1–1.4). They are
stored in `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/`, not in a folder
named after S1.

**Decision boundary:** this is a report-only technical pre-review. No question, lesson, SVG,
manifest or claim was edited, and no Mathematics or editorial approval was recorded. All 104
questions are `draft`, and all four batches are `ready_for_review` with Mathematics and
editorial review `pending`. All four lessons are revision 2 `draft` with `reviewed_at: null`.
No S1 content is approved, so no approved item was affected.

**Model and standards:** this audit follows `N2_CALIBRATION_PRE_REVIEW_AUDIT.md` and checks
against `LESSON_NOTES_CONTENT_STANDARD.md`, `GEOMETRY_CONTENT_STANDARD.md` (S1 is not a G
topic, so only its diagram policy applies by analogy), house rules v2 and prompt contract v2.

## Counts

| Item | Count | Notes |
| --- | ---: | --- |
| Questions checked | 104 | 26 per outcome 1.1–1.4; difficulties 21 / 31 / 31 / 16 / 5 |
| Canonical answers independently recomputed in code | 104 | 0 mismatches |
| Lessons checked | 4 | All meet the baseline gate: 7 sections, 3 explanations, 2 worked examples, 1 recall, 1 summary, about 3,700–4,500 characters |
| Diagrams referenced | 4 | One per lesson. No S1 question references any asset. |
| Diagrams rendered and viewed | 4 of 4 | Each viewed at 940 px and at 358 px (a 390 px phone minus 16 px gutters) |
| Content findings | 20 | 3 High, 8 Medium, 8 Low, 1 process |
| Diagram findings | 11 | 0 High, 5 Medium, 6 Low |

Automated checks run (none edit content):

- `question-bank validate …/secondary_1/s1/v1`: 0 errors, 0 warnings.
- `question-bank course-validate`: valid, 0 issues.
- `question-bank authoring-validate …/secondary_1/s1/v1`: all four batches valid, 0 near
  duplicates. The single bank-level error (`learning_blueprint_coverage`, 1 of 19 blueprints)
  appears only because one bank was passed instead of the whole catalogue.
- SVG checksums match the `sha256` in each lesson manifest.

These checks passing is not evidence of correctness. The duplicate detector reported 0, yet
the semantic clusters in C-11 exist.

## Severity scale

- **High:** the item no longer assesses its outcome, for example because the answer is given
  in a hint or in the prompt.
- **Medium:** misalignment, ambiguity, inconsistency or a visible defect that could mislead or
  confuse a learner, or mark a correct answer wrong.
- **Low:** wording, polish or consistency.

## Part 1: Content findings

### Answers and worked solutions

The canonical answer of every question was recomputed from the prompt alone, in
`fractions.Fraction` arithmetic where it applies. All 104 agree. Every final worked step
ends at the canonical value, and the mark values of every part add up to its marks. No item
has `accepted_answers`. All lesson worked examples and active-recall answers were also
recomputed and are correct:

- L1: 9/10/11/12 → 2/1/2/3; the two-way margins 25/25/23/27/50; recall 30.
- L2: line changes +4, −2, +8, +4, overall 14; 72° of 150 = 30 = 20%; recall 15.
- L3: no numeric answers apart from the recall code.
- L4: 2 and 8 → 4 against 1.065; 9 and 36 → 4; recall 4.

No incorrect canonical answer or worked-solution result was found.

### Findings

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-01 | s1-l1-001, s1-l1-012, s1-l1-013, s1-l1-019, s1-l2-001, s1-l2-015, s1-l3-017 | High | The stage-2 hint states the final answer or makes it immediate. This breaks house rules v2: "neither hint may state the final answer". Examples: l1-012 H2 "There are three entries equal to 38."; l1-013 H2 "The stated point is 27°C."; l1-019 H2 "The greatest of 5, 8, 11 and 6 is 11."; l2-001 H2 lists the four positions; l3-017 H2 lists the four qualifying values; l1-001 H2 names the three positions. | Replace each H2 with a setup that does not do the counting, e.g. l1-012 "Tick each 38 as you read from left to right, then count the ticks."; l3-017 "Test each time against 15 ≤ t ≤ 29." |
| C-02 | 23 of 26 outcome 1.3 items: s1-l1-004, l1-005, l1-010, l1-015, l1-020, l2-005, l2-006, l2-012, l2-013, l2-020, l2-021, l2-029, l3-005, l3-006, l3-013, l3-014, l3-021, l3-022, l3-028, l4-003, l4-007, l4-011, l4-015. Also 4 of 5 coded 1.4 items: s1-l1-011, l1-016, l1-017, l1-021 | High | The prompt maps each display name to a code, so a hint that names the display gives the answer. Examples: l1-004 H2 "A connected time sequence needs a line graph."; l4-015 H2 "A pie chart is suitable for…"; l1-017 H2 "The missing unit prevents…" (code 4 is "missing labels or units"). Only l2-028, l3-029 and l5-002 avoid naming the display. | Make H2 describe the data structure or the reader's task without the display name, e.g. "The readings are ordered in time and the reader must see each rise and fall. Which display joins consecutive readings?" |
| C-03 | s1-l2-015 | High | The prompt states that "Three units are plausible: items, kilograms and dollars" and then asks how many interpretations are listed (answer 3). This is counting words in the prompt and does not assess outcome 1.4. | Replace it with a quantified missing-unit task, e.g. the same bars read as tonnes or kilograms and the learner finds the factor between the two readings. Alternatively, convert it to an issue-code item with a different context from l1-017. |
| C-04 | s1-l2-018, s1-l3-003, s1-l3-012, s1-l2-031, s1-l3-023, s1-l4-012 | Medium | These ask for a percentage and say "Enter the numerical value only". The checker (`checking.py` `_fraction`) parses "25%" as 1/4. Calling `check_answer` with "25%" for l2-018 returned `correct: False` with no format error, so a learner who types the % sign is silently marked wrong. The same happens for "200%", "60%", "29%" and "35%". Degree items (l1-014, l3-004, l3-016, l3-026, l4-002) instead return a format error, which is safer. | Use the wording already in the s1-lesson-02 recall: "Enter the percentage without the % sign." For l4-012, say "in percentage points, without the % sign". Platform owners should decide whether a trailing % on a percentage-valued item should be accepted. |
| C-05 | s1-lesson-03 (`s1-13-recall`), s1-l1-004 and all coded 1.3 items | Medium | The lesson recall uses "1 table, 2 bar graph, 3 line graph, 4 pie chart". The bank uses "1 table, 2 bar graph, 3 pictogram, 4 line graph, 5 pie chart". s1-l1-004 (hourly temperature) is nearly the same task as the lesson recall, but the correct code is 4 instead of 3. The lesson diagram also omits pictograms (D-03). | Change the lesson recall to the bank's five-code scheme and add pictograms to the decision guide. |
| C-06 | d3: s1-l3-005, l3-006, l3-013, l3-014, l3-021, l3-022, l3-028, l3-029. d4: s1-l4-003, l4-007, l4-011, l4-015, l4-016, l4-013, l4-014. d5: s1-l5-002, l5-004 | Medium | Difficulty is inflated. The coded d3–d5 items are single-choice tasks with the same demand as d1 (l1-004, l1-015), but carry 3–5 marks. l4-016 is one multiplication. l4-013 and l4-014 are short arithmetic chains. In l5-004 the pie and bar data are redundant, because x = 16 ÷ 0.2 = 80 alone, and the 180 subtotal is only a check. Prompt v2 rule 2 says extra arithmetic alone does not raise difficulty. | Reclassify the coded items to d1–d2, or rewrite them so they need a choice plus a justification or constraint (e.g. "choose the display and the code of the reason the runner-up fails"). Rewrite l5-004 so that x must be found from the pie and bar data (e.g. not give the 20% and 16). |
| C-07 | 1.2 items s1-l1-003, l1-013, l1-019, l2-003, l2-011, l2-019, l2-027, l3-019, l3-020 | Medium | These are "interpret a display" items, but the display is described in words with its values already given ("A bar graph shows 6 … 9 … 7 … How many for Tuesday?"). No scale, key or sector has to be read, so l1-003 and l1-013 just restate the prompt. | Attach rendered charts (see "Questions that would clearly benefit from a diagram"), or rewrite them to need scale or key work. |
| C-08 | s1-l2-014, s1-l2-030 | Medium | These are 1.4 items whose task is a subtraction (2024 − 2021 = 3; 50 − 20 = 30) that never involves the misinterpretation. | Ask for the distortion instead, e.g. l2-030 "The 20→50 step is drawn the same length as each 10-unit step. By what factor is it compressed?" (3). |
| C-09 | Every coded 1.3 and 1.4 item (31) | Medium (judgment) | Outcome 1.3 covers "advantages and disadvantages" and 1.4 covers "explaining why". Every response is a single numeric code, and every worked solution is one line (e.g. "Best choice code = 4") with no reason. No item asks for a disadvantage or a least-suitable display. | Reviewers should decide how far numeric codes can assess these outcomes. At a minimum, add to each solution a one-sentence reason and a limitation of the nearest alternative. Consider "least suitable" or "reason" code items. |
| C-10 | s1-l3-001, s1-l4-001, s1-l3-002, s1-l4-006, s1-l3-021 | Medium | The prompts are under-specified. l3-001 does not say the table is 2 × 2 or which row the missing cell is in. l4-001 does not say chess and coding are the only columns. l3-002 uses the codes C, R and D without defining them ("chess choice C"). In l4-006, "The rest arrived on Wednesday" should refer to the rest of the before-noon visitors. In l3-021, "precise comparison" could point to a table (1) as well as a bar graph (2). | l3-001: "A 2 × 2 table has row totals 28 and 32. Row 1 contains 17 and 11; row 2 contains 14 and one missing cell." l4-001: state "each student chooses either chess or coding". l3-002: define the codes. l4-006: "The remaining before-noon visitors arrived on Wednesday." l3-021: "needs readers to compare sizes at a glance". |
| C-11 | Clusters listed in the cell to the right | Medium | Semantic duplicates (same context, operation pattern and numerical structure) that the detector missed. (a) s1-l1-006 and s1-l2-007 use the same scores 92 and 96 with a baseline of 90; s1-lesson-04 uses 92/98 above 90, and its recall gives the same displayed heights of 2 and 8. (b) s1-l3-014 and s1-l4-015: four sources totalling 100% → pie chart. (c) Exact lookup → table appears six times (l1-015, l2-013, l2-029, l3-005, l3-022, l4-003). (d) Time series → line graph appears six times (l1-004, l2-005, l2-021, l3-006, l3-028, l4-007). (e) Equally spaced irregular years appear four times (l1-011, l2-014, l3-030, l4-016; l1-011 and l3-030 share 2019/2023/2024). (f) Reverse-engineered baseline: s1-l4-004 and s1-l5-005. The Secondary 2 bank repeats l5-005's structure ("appear to be 60%") in s1-l3-504, 511, 512, 518 and 528. (g) l1-020 and l2-020 are both pictograms for a young audience, and the prompt itself names the symbols. (h) The total-minus-knowns structure appears at three difficulties: l1-007 (d1), l2-002 (d2), l3-020 (d3). | Keep one item per cluster at each difficulty. Replace the others with different contexts and structures, e.g. a disadvantage item, a two-series line-graph reading, or a pie chart with an angle that must be measured. Give l2-007 different values from l1-006. |
| C-12 | s1-l3-010, s1-l1-018, s1-l4-010, s1-l4-012, s1-l2-024, s1-l3-017 | Low | Questions use terms the lessons do not teach. "Relative frequency" (l3-010), "qualitative" (l1-018; the lesson says "categorical"), "cumulative line graph" (l4-010) and "percentage points" (l4-012) appear in none of the four lessons. The inclusive integer intervals 0–9 and 0–14 (l2-024, l3-017) differ from the lesson's advice to use inequality boundaries. The standard requires unfamiliar terms to be explained. | Add short definitions to s1-lesson-01 (relative frequency, qualitative = categorical) and s1-lesson-02 (cumulative graph, percentage point), or change the question wording. State "whole-minute times" in l3-017. |
| C-13 | s1-l3-002, l3-007, l3-008, l3-010, l3-012, l3-017, l3-020, l3-024, l3-025, l3-027, l3-031, l4-008, l4-016 | Low | Multi-mark items have a single A3 or B4 step with no method mark (prompt v2 rule 7). Mark types are also inconsistent: l2-028 gives A2 for a code choice while the other code items use B; l2-007 and l3-015 give B marks for calculations. | Split the solutions into M and A steps and use a consistent B or A convention for code choices. |
| C-14 | All 26 outcome 1.3 items | Low | Every stage-1 hint is the same sentence: "Match the information need to the main strength of each representation." | Write item-specific conceptual hints. |
| C-15 | s1-l3-027, s1-l4-013 | Low | Titles do not match the tasks. l3-027 is titled "Interpret a changing scale", but the scale is constant. l4-013 is titled "Stratified response count", a term that is not taught and is not what the task does. | Rename them, e.g. "Count scale intervals" and "Response totals across four levels". |
| C-16 | s1-l1-013 | Low | It is the only numeric item without "Enter the numerical value only", and it does not say how to handle the unit (°C). | Add "Enter the temperature in °C as a number only." |
| C-17 | s1-lesson-04 (`s1-14-recall`) | Low | The recall (72/78 above 70) gives the same displayed heights (2 and 8) and the same answer (4) as the worked example, so it tests recall of the example rather than the method. | Use different values, e.g. 85 and 91 above 80 (heights 5 and 11). |
| C-18 | s1-l1-005, s1-l1-017, s1-l2-015 | Low (standards conflict) | See "Audience standards" below. | Reviewer decision. |
| C-19 | s1-l2-008, s1-l2-023, s1-l3-008, s1-l3-031, s1-l1-016, s1-l4-008, s1-l5-003 | Low | Seven items test icon scaling. They vary in shape (square, cube, cylinder, sphere, circle), but l1-016, l2-023 and l3-031 all scale every linear dimension of a solid. | Keep this as variety, or swap one for a 1.4 issue not yet covered, such as sectors that do not total 360° or a missing sample size, both taught in s1-lesson-04. |
| C-20 | B001–B004 manifests | Process | Every batch manifest cites `house-rules-v1.json` and `math-question-authoring-v1`, although every question has `created_at` 13 October 2026. That is after the N2 audit (10 October) said later claims must move to house rules v2 and prompt v2. | Update the manifests to v2 references when the corrections are made, and regenerate the review packets. This audit applied the v2 rules. |

### Audience standards (reported, not resolved)

The two standards disagree on audience, and S1 is affected in a few places:

- **House rules v1/v2 and prompt v2 rule 4** (applied in the N2 audit) set `locale: en-SG`,
  Singapore/British English, `currency: SGD`, and "S$ for learner-facing Singapore-dollar
  amounts".
- **LESSON_NOTES_CONTENT_STANDARD.md** names the audience as students across Indonesia and
  Southeast Asia, treats the Singapore syllabus as a calibration reference only, and asks
  for clear international English, explained terminology and contexts that work across the
  region.

S1 contains no money amounts, so the S$ rule never applies. Where the two standards point
different ways:

- s1-l1-017 and s1-l2-015 use "dollars" as an example unit. Under the house rules this
  would be S$. Under the audience standard, "dollars" alone is ambiguous for a learner who
  uses rupiah or ringgit. A neutral unit such as "kilograms" avoids the question entirely.
- s1-l1-005 uses "house teams", a school-house system that is common in Singapore and
  British schools but less familiar elsewhere. "Four school teams" would work for both
  audiences.

Spelling is consistently British (colour, favourable), which suits both standards. No
American spellings were found.

## Part 2: Diagrams and graphs

### What was checked

The S1 diagrams are the four lesson SVGs below. Each path was resolved from the lesson
JSON's `assets[].path` against `backend_resources/courses/g3_math/secondary_1/n1/v1/`. No S1
question references an asset, and the review packets contain only KaTeX assets.

| Asset | Referenced by | `diagram_kind` | Viewed |
| --- | --- | --- | --- |
| `assets/s1-lesson-01-frequency-table.svg` | s1-lesson-01 §2 | raw_data_to_frequency_table | Yes |
| `assets/s1-lesson-02-chart-reading.svg` | s1-lesson-02 §1 | bar_and_line_graph_reading | Yes |
| `assets/s1-lesson-03-display-choice.svg` | s1-lesson-03 §1 | statistical_display_decision_guide | Yes |
| `assets/s1-lesson-04-truncated-axis.svg` | s1-lesson-04 §1 | truncated_axis_comparison | Yes |

**Method:**

- Rendering: the pre-installed Playwright Chromium rendered each SVG to PNG in the
  session's scratchpad, outside the repo, at 940 px width and at 358 px width. Every image
  was inspected visually.
- Positions: plotted positions were recomputed from the SVG coordinates and compared with
  the data in the alt text and in the lesson text.
- Text bounds: each `<text>` element's `getBBox()` was measured in the browser to check
  overflow, overlap, viewBox clipping and centring.
- Font: `system-ui` resolved to Inter in this container.

### Accuracy verification

- **L1 frequency table:** the raw list walk, bus, bicycle, walk, bus, walk, bicycle, bus
  gives walk 3, bicycle 2, bus 3, total 8. This matches the table, the check line, the alt
  text and the `<desc>`.
- **L2 bar graph:** the scale is 10 px per unit from a baseline at y = 385. The bars for
  Club A, B and C have heights 120, 180 and 240 px, giving 12, 18 and 24, which match their
  labels.
- **L2 line graph:** the scale is 10 px per unit from 26 at y = 385. The points at y = 325,
  285, 305, 225 and 185 give 32, 36, 34, 42 and 46. This matches the worked example
  `s1-12-line-example`. Each x label is centred within 3 px of its point.
- **L3 decision guide:** the four task → display pairings match the alt text and §1–§2.
  The connector topology is wrong; see D-01.
- **L4 truncated axis:** the truncated panel uses 30 px per unit from 90. Bars of 60 and
  240 px give 92 and 98, so the displayed heights are 2 and 8 as labelled. The zero-based
  panel uses 2.4 px per unit; heights of 221 and 235 px give 92.1 and 97.9, which is
  correct to the pixel. The panel text, alt text and the lesson's numbers (2, 8, ratio 4,
  about 1.065) all agree.
- No diagram reveals the answer to a question that the lesson goes on to ask. The L4 recall
  uses different values from the diagram.

### Diagram findings

| ID | Stable key | Asset path | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- | --- |
| D-01 | s1-lesson-03 | `assets/s1-lesson-03-display-choice.svg` | accuracy | Medium | The connector path `M470 155v45M470 200H155v45M470 200h315v45M470 200v45` has no branch to "Ordered change", whose box centre is at 585. The branch that should reach "Compare groups" drops at x = 470, the right edge of that box, instead of its centre at 370. The right branch drops at 785, while that box and the arrow below it are centred at 800. In the image, "Ordered change → Line graph" looks disconnected from the root question. | Replace the path with `M470 155v45M155 200H800M155 200v45M370 200v45M585 200v45M800 200v45`. |
| D-02 | s1-lesson-03 | `assets/s1-lesson-03-display-choice.svg` | neatness | Medium | Root-box text runs past the box edge at x = 615. "What must the reader do?" overflows by 17.8 px and "Start with the comparison task." by 38.2 px, crossing the stroke (measured with Inter). Narrower or wider system fonts will change the amount. | Widen the box (`x="290" width="360"`, keeping its centre at 470). Set `text-anchor="middle" x="470"` on both lines. |
| D-03 | s1-lesson-03 | `assets/s1-lesson-03-display-choice.svg` | accuracy | Medium | Lesson §2 and all 26 outcome 1.3 questions treat the pictogram as a fifth representation, but the guide shows only four. This adds to the code-scheme mismatch in C-05. | Add a fifth branch, "Approximate counts for a general audience → Pictogram", or a footnote explaining where pictograms fit. Update the alt text to match. |
| D-04 | s1-lesson-03 | `assets/s1-lesson-03-display-choice.svg` | neatness | Low | Box labels are placed by hand at fixed x values and are off-centre by 10–16 px ("Compare groups", "distinct groups", "few categories", "Line graph"), which makes the row look uneven. | Use `text-anchor="middle"` at the centre of each box (x = 155, 370, 585 and 800 in both rows). |
| D-05 | s1-lesson-02 | `assets/s1-lesson-02-chart-reading.svg` | accuracy | Medium | The line graph's vertical axis starts at 26 with no break symbol, and its ticks (26, 32, 38, 44, 50) do not count from zero. s1-lesson-04 teaches that a truncated baseline "must be conspicuous" and that the break should be marked, so the course's own model breaks its own rule. | Draw an axis-break zig-zag just above the origin, and use ticks of 30–50 in steps of 5, or steps of 2. |
| D-06 | s1-lesson-02 | `assets/s1-lesson-02-chart-reading.svg` | accuracy | Low | The gridlines are 6 units apart, so 36, 34, 42 and 46 fall between them and cannot be read exactly. The worked example therefore depends on text the graph cannot support. The bars carry value labels, but the points do not. | Add gridlines every 2 units, or label each point with its value. |
| D-07 | s1-lesson-02 | `assets/s1-lesson-02-chart-reading.svg` | accuracy (alt text) | Low | The alt text and `<desc>` give no data values, so a screen-reader user cannot follow §1 or the worked example. | Add "Clubs A, B and C read 12, 18 and 24 books; attendance Monday to Friday was 32, 36, 34, 42 and 46." |
| D-08 | s1-lesson-01 | `assets/s1-lesson-01-frequency-table.svg` | accuracy | Low | The title says "Classify first, then tally…" and §2 says "The visual example shows the complete route…", but no tallies are drawn. The diagram goes straight from the list to frequencies. | Add a Tally column (`\|\|\|`, `\|\|`, `\|\|\|`) between Method and Frequency, or drop "tally" from the title. |
| D-09 | s1-lesson-01 | `assets/s1-lesson-01-frequency-table.svg` | neatness | Low | An orange dot (`circle cx=851 cy=375`) sits next to "Total 8" with no explanation. It reads as a stray mark. | Remove it, or replace it with a labelled check mark ("= 8 observations"). |
| D-10 | s1-lesson-01 | `assets/s1-lesson-01-frequency-table.svg` | neatness | Low | Method-column labels sit 12–21 px left of the cell centre, by a different amount for each row (Walk 16.7, Bicycle 20.6, Bus 12.0). | Use `text-anchor="middle" x="615"` for the Method column and `x="785"` for the Frequency column. |
| D-11 | s1-lesson-01 to 04 | all four SVGs | neatness | Medium | On a phone, each 940 × 500 canvas at 358 px content width is scaled by 0.381. Body text of 16–21 px becomes 6.1–8.0 CSS px, and the 28 px titles become 10.7 px. In the 358 px renders the two-panel figures (L2, L4) and the L3 guide are legible only when zoomed. Minimum readable sizes are around 11–12 px. | Provide narrow layouts: split L2 and L4 into two stacked figures, and lay L3 out vertically. Use a viewBox about 480 wide with text of at least 30 px, or support tap-to-zoom in the lesson viewer. |

s1-lesson-04 has no material finding beyond D-11. Its bar value labels sit about 5 px left
of centre, which is not noticeable at normal size.

### Root-cause patterns

1. **The renderer has no source in the repo, and the spec carries no data. This affects all
   4 S1 diagrams; 6 more diagrams carry the same label.**
   - The four assets declare `renderer: nextscholar-statistics-svg-v1`, but no code anywhere
     in the repo produces it. A search for the renderer name and its `diagram_kind` values
     outside JSON found nothing. Six Secondary 2 S1 lessons (s1-lesson-05 to 10) carry the
     same label; they were not audited here.
   - `scripts/recalibrate_geometry_content.py` emits only `nextscholar-geometry-svg-v1`
     assets for G topics, so it is not the source of these SVGs.
   - Each `generation_spec` holds only `renderer`, `diagram_kind` and `lesson_key`, with no
     data values, axis limits or connector targets.
   - `course_validation._validate_assets` checks that the file exists, the checksum, the
     revision-suffixed path, and `geometry_diagram_issues()`. That function, in
     `question_bank/src/question_bank/geometry_validation.py`, only acts on
     `diagram_kind == "angle_types"`, `angle_markers` and `forbidden_visible_labels`, none
     of which these assets declare.
   - As a result, no automated check can compare bar heights, points or connectors with
     data. D-01, D-03, D-05 and D-06 could only be found by eye.
   - Recommendation: commit a statistics renderer that builds the SVG from data in
     `generation_spec` (values, axis minimum and maximum, tick step), and add a
     statistics-diagram validator. One option is to reuse the angle-validator approach:
     read declared `data-value` attributes and compare them with rectangle heights and
     point coordinates.

2. **Text is placed at hard-coded x positions with no `text-anchor` (all 4 S1 SVGs).** None
   of the four S1 SVGs uses `text-anchor`, and only 6 of the 49 SVGs under
   `backend_resources/courses/g3_math/*/*/v1/assets/` do. Text width therefore depends on
   the `system-ui` font on each device, which produces the overflow in D-02 and the
   off-centre labels in D-04 and D-10. The fix is to centre text with `text-anchor` in the
   renderer.

3. **A fixed 940 × 500 landscape canvas is used for phone delivery (all 4 S1 SVGs, D-11).**

4. **The question bank has no diagrams and no diagram audit.** No S1 question has an asset,
   and there is no `diagram_audit.json` for S1, because `GEOMETRY_CONTENT_STANDARD.md`
   requires one only for G topics. Outcome 1.2 is about reading displays, so the missing
   diagrams weaken it (C-07).

### Questions that would clearly benefit from a diagram

No `diagram_audit.json` exists for S1, so the candidates below are based on this audit's own
reading. Creating an S1 diagram audit, as the geometry banks have, would record the
decision for every question.

- **1.2, read a display:**
  - Bar charts: s1-l1-003, s1-l2-003, s1-l2-019, s1-l3-020.
  - Pictograms with a key or half symbol: s1-l1-009, s1-l2-004, s1-l2-026, s1-l3-012.
  - Line graphs: s1-l1-013, s1-l2-011, s1-l2-027, s1-l3-019, s1-l4-010.
  - Scale counting: s1-l3-027. This one cannot really be done without a scale.
  - Pie charts: s1-l1-014, s1-l3-004, s1-l3-026, s1-l4-002.
- **1.4, see the distortion:**
  - Truncated axes: s1-l2-007, s1-l2-031, s1-l3-007.
  - Irregular year spacing: s1-l1-011, s1-l3-030, s1-l4-016.
  - Unequal vertical ticks: s1-l2-030.
  - Icon scaling: s1-l2-008, s1-l3-008, s1-l3-015.
- **1.1, two-way tables:** s1-l3-001, s1-l4-001, s1-l2-025. A KaTeX `array` table, as used
  in s1-lesson-01, would be enough here.

When adding diagrams to questions, follow the geometry precedent and declare
`forbidden_visible_labels`, so that the asked-for value (for example the missing bar in
l3-020 or the Tuesday value in l1-003) is not printed on the figure.

## Could not verify

- **Fonts:** the renders used Inter as the `system-ui` fallback. On learner devices (SF Pro,
  Roboto, Segoe UI) text widths will differ, so the overflow sizes in D-02 and the offsets
  in D-04 and D-10 are indicative. The overflow itself should persist.
- **Lesson viewer:** the production lesson viewer's CSS was not inspected. D-11 assumes the
  image is scaled to the content width with no zoom, which matches the reviewer preview's
  plain `<img>`.
- **Secondary 2 diagrams:** the six Secondary 2 S1 diagrams that share the
  `nextscholar-statistics-svg-v1` label are outside this scope and were not viewed.
- **Judgment calls:** C-06 and C-09 (whether coded single-choice items can assess
  "advantages and disadvantages" and "explaining why") and the audience conflict need
  human review.
- **Validation scope:** `authoring-validate` was run on this bank only. A catalogue-wide run
  would show only the expected blueprint-coverage difference.

## Rerun

Read-only commands used. Rendering and recomputation scripts were kept outside the repo,
and no rendered images were committed.

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache uv run --project question_bank --no-dev question-bank validate backend_resources/question_bank/g3_math/secondary_1/s1/v1
```

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache uv run --project question_bank --no-dev question-bank course-validate
```

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache uv run --project question_bank --no-dev question-bank authoring-validate backend_resources/question_bank/g3_math/secondary_1/s1/v1
```
