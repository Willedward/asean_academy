# Secondary 1 N4 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_1/n4/v1/`
(batches B001–B004) and the three N4 lessons, `n4-lesson-01` to `n4-lesson-03`. The lessons are
stored in `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/`, because unit
`g3-sec1-n4` in that folder's `course.json` owns them. No other lesson declares outcome 4.1, 4.2
or 4.3.

**Decision boundary:** this is a technical pre-review, and it is report-only. No question,
lesson, asset, manifest or claim was edited. No Mathematics or editorial approval was recorded,
and no paid model API was called. Its purpose is to let human reviewers spend their time on
judgement calls rather than basic errors.

## Counts

| Item | Count |
| --- | ---: |
| Questions checked | 104 (35 × 4.1, 35 × 4.2, 34 × 4.3) |
| Lessons checked | 3 |
| LaTeX strings parsed with KaTeX | 383 |
| Diagrams, graphs or charts referenced | **0** |
| Diagrams rendered and viewed | 0 (none exist) |

**Review state in the repository:** all four batch manifests are `ready_for_review`, with Mathematics
`pending` and editorial `pending`. All 104 questions are `draft`, revision 1. All three lessons are `draft`, revision 1,
with `reviewed_by: null`. No N4 content is recorded as approved, so no review state needed to be
preserved. Hosted review records in the database could not be inspected from this environment.

**Authoring provenance:** the manifests record prompt `math-question-authoring-v1` and
house rules v1. The N2 audit introduced house rules v2 after these batches were written, so
several findings below are v2 rules that the batches predate.

## Checks performed

- **Canonical answers:** recomputed every answer from the prompt alone, before reading any
  solution, as exact fractions in Python. All 104 matched the stored `canonical_answer`.
- **Solutions:** read every hint and worked step against the recomputed answer and the
  prompt's stated conditions.
- **Grading:** ran the production checker (`question_bank.checking.check_answer`, also imported
  by `learning_api.postgres_practice` and `progress_service`) on canonical answers and
  plausible learner forms.
- **Alignment:** checked each item's outcome and difficulty against the blueprint's difficulty
  definitions and house rules v2.
- **Duplicates:** compared contexts, operation patterns and numbers across the bank and
  against lesson worked examples. Pool placement came from `question_pools/n4.json`.
- **Lessons:** checked lesson depth against `LESSON_NOTES_CONTENT_STANDARD.md`, measuring both
  the validator's metric and the prose length.
- **Maths rendering:** parsed every LaTeX string with KaTeX 0.16.22 (vendored in
  `ocr_extractor`) using `throwOnError` and strict mode. Rendered every block in Chromium at a
  358 px content width (390 px phone minus 16 px gutters) and measured overflow. Result: 0
  parse errors and 0 overflows.
- **Repository validators:** `validate`, `course-validate` and `authoring-validate` all pass
  with 0 errors and 0 warnings. As the N2 audit model warns, this is not evidence of
  correctness. Several findings below pass every validator.

Severity scale:

- **High:** a learner sees a contradiction or a duplicate, or is graded wrongly.
- **Medium:** a calibration, alignment or teaching-quality defect that a reviewer would
  likely send back.
- **Low:** wording, metadata or consistency.

## Part 1: content findings

### Questions

| # | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| 1 | `n4-l4-001` (unit checkpoint) | High | The prompt says "Without using a specific distance between the towns, find the average speed". Yet H1 says "Choose a convenient one-way distance", H2 says "Let each direction be 180 km", and solution step 1 (B1) is "Let each one-way distance be 180 km". The model answer does exactly what the prompt forbids. The answer, 72, is correct. | Keep the condition and rewrite the hints and solution with a symbol. H1: "Let the one-way distance be d km." H2: "Write each travel time in terms of d and add them." Solution: total time = d/60 + d/90 = d/36 h; average = 2d ÷ (d/36) = 72 km/h. Alternatively, delete the condition and keep the 180 km method. |
| 2 | `n4-l1-004`, `n4-l1-010` | High | Exact semantic duplicate. "Convert 72 km/h to m/s" and "Express 72 km/h in metres per second" share the same outcome (4.2), difficulty (1) and answer (20). Both are in pool `n4-lesson-02-practice`, stage `guided`, so one learner meets the same question twice in one practice set. | Replace `n4-l1-010` with a different one-step 4.2 rate, for example "A tap fills a tank at 2.5 litres per second. Express this rate in litres per minute." (150). |
| 3 | `n4-l3-002` | Medium | The canonical answer is `40/3`. The prompt asks for "an exact fraction". `n4-lesson-01` presents the identical calculation as 13⅓. The checker removes spaces before parsing, so a learner who types `13 1/3` is silently graded as `131/3` and marked wrong, with no format error. Neither `13 1/3` nor any equivalent can be added to `accepted_answers`, because that list goes through the same parser. | Make the prompt say "Give your answer as an improper fraction, for example 7/2". Change the lesson example to show 40/3 alongside 13⅓. The checker gap is a root-cause pattern (R2 below). |
| 4 | `n4-l3-003`, `n4-l3-004`, `n4-l3-005` (all d3) | Medium | Each is a single ×3.6, ÷3.6 or ÷60 step. The same method appears at d1 in `n4-l1-009`/`l1-014` (m/s→km/h), `n4-l1-004`/`l1-010` (km/h→m/s) and `n4-l1-018` (m/min→m/s, 900→15 against 450→7.5). The rubric defines d3 as "multi-step application". | Replace them with genuine multi-step 4.2 tasks, such as a conversion followed by a comparison, or a two-unit rate like L/h→cm³/s. Relabelling would break the blueprint distribution, so replacement is preferable. |
| 5 | `n4-l4-003` (d4), `n4-l5-001` (d5), `n4-l4-014` (d4) | Medium | `n4-l4-003` (2.4 km/min→m/s) uses the same two steps as `n4-l2-011` (1.8 km/min→m/s, d2) and `n4-l3-013` (0.54 km/min→m/s, d3). `n4-l5-001` (2.7 m³/h→cm³/s) is the d4 item `n4-l4-006` with hours instead of minutes. `n4-l4-014` is a routine three-factor conversion. None needs the "method selection, constraints or justification" (d4) or "non-routine synthesis" (d5) that house rules v2 requires. | Replace each with a 4.2 task that has a decision in it. Examples: compare two speeds given in different units and justify which is faster; or find a missing time from a rate given in other units. |
| 6 | `n4-l4-004` (d4) against `n4-l3-015` (d3) | Medium | Difficulty inversion. `l4-004` gives the first-stage time directly ("takes 2 hours"), so it needs 240/80, 3−2 and 140/1. `l3-015` makes the learner compute the first-stage time (90/45) as well. The d4 item is easier. | Swap their difficulty levels, or add a stop or unit conversion to `l4-004`. |
| 7 | Bank-wide clusters | Medium | Repeated operation patterns, against house rules v2's "avoid repeating … operation pattern and numerical structure":<br>• two-stage average rate (add both amounts, add both times): `l2-010`, `l2-026` (d2) and `l3-010`, `l3-016`, `l3-024` (d3). The structure is identical, but the difficulty differs.<br>• average speed with a rest: `l3-002`, `l3-017`, `l3-025`.<br>• required speed to keep a schedule: `l3-015`, `l4-004`, `l4-011`.<br>• unknown stage distance from overall average speed: `l4-005`, `l5-002`, `l5-004`, `l5-005`. `l5-004` and `l5-005` are both d5 and both have "three sections, a 30-minute stop and an overall average".<br>• catch-up time of exactly 1 h: `l3-014`, `l3-029`. | Keep one or two items per cluster. Replace the rest with uncovered 4.3 situations, such as work rates with two machines, a rate given per unit cost, or reading a rate from a table. Give `l5-004` or `l5-005` a genuinely different structure. |
| 8 | `n4-l1-003` | Low | "Express 3.6 km in metres" is a length conversion, not a rate. Outcome 4.2 is "conversion of units such as km/h to m/s". | Use a rate instead, for example "Express 3 m/s in metres per minute" (180). |
| 9 | `n4-l3-019`, `n4-l3-011` | Low (judgement) | Both are labelled 4.2, but they compute an average speed from a distance and a time in minutes or seconds. That is the same task as the 4.1 items `l2-002`, `l2-009`, `l2-017` and `l2-025`. | Reviewer decision: keep them as 4.2 because the unit conversion is the difficulty, or move them to 4.1 and replace them with pure rate conversions. |
| 10 | Most of the 52 d1–d2 items | Low (judgement) | Stage-2 hints state the complete operation with both operands, for example `n4-l1-001` "Divide 36 km by 2 h" and `n4-l2-007` "Multiply 18 by 35". After hint 2, only the arithmetic remains. `n4-l1-019` H2 ("3600 metres in 3.6 kilometres and 60 minutes in one hour") gives the whole calculation 3600/60. `n4-l4-012` H2 states the key formula ("half the difference"). No hint states the final answer, so v1 and v2 are satisfied literally. | Reviewer decision on how much stage 2 may reveal for one-step items. One option is for stage 2 to name the operation without the second operand ("Divide the distance by the time taken"). |
| 11 | `n4-l4-004` | Low | This is the only prompt that does not name the answer unit: "Find the constant speed needed for the remaining 140 km…". Answers have no unit field. | Append "in kilometres per hour". |
| 12 | `n4-l4-016` | Low | "Passes completely through a 270 m platform in 30 seconds" is defined only in H1 ("from the moment the front enters … until the rear leaves"). | Move that definition into the prompt. |
| 13 | `n4-l4-010` | Low | "1 litre over 1 square metre = 1 millimetre of depth" is awkward and reads like an equation between unlike quantities. | Replace with "1 litre of water spread evenly over 1 square metre gives a depth of 1 millimetre". |
| 14 | `n4-l4-016`, `n4-l4-003` | Low | Mark scheme. In `l4-016`, step 3 (M1) already reaches 54 km/h, and step 4 (A1) only restates it ("∴ 54 km/h"). In `l4-003`, step 2 awards B1 for "1 min = 60 s". | Award A1 on the line that produces 54 km/h, and give the freed mark to the speed conversion. Merge the `l4-003` unit fact into the method mark. |
| 15 | `n4-l5-001` | Low | `canonical_latex` is `750\text{ cm}^3\!\!/\text{s}`. The double negative space makes the slash crowd the cube. `n4-l4-006` writes the same unit as `\text{ cm}^3\text{/s}`. | Use the `l4-006` form. |
| 16 | `n4-l2-014`, `n4-l3-031` against `n4-l3-023` | Low (rule conflict) | `l2-014` and `l3-031` say "travelator", a Singapore and British term. `l3-023` says "moving walkway". House rules v2 specifies `en-SG` "Singapore/British English". `LESSON_NOTES_CONTENT_STANDARD.md` says learner content should use "clear international English" for students across Indonesia and Southeast Asia, and should explain unfamiliar terms. | Use "moving walkway" consistently, or gloss it once as "moving walkway (travelator)". See the standards conflict section. |

All other items had a correct answer, consistent working, stated conditions that match the
solution, and outcome and difficulty labels within the rubric. Prompts consistently use metric
units and 24-hour times. No N4 item uses money, so the S$ rule from the N2 audit is not triggered.

### Lessons

| # | Stable key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| L1 | `n4-lesson-01`, `n4-lesson-02` | Medium | Worked examples reproduce practice questions exactly. `n4-lesson-01`'s example "average speed including a stop" (24 km in 1.5 h, a 30-minute rest, then 16 km in 1 h) is `n4-l3-002`, which sits in the same lesson's practice pool as a `challenge` item. `n4-lesson-02`'s example "90 km/h to m/s" is `n4-l2-005`, an `independent` item in `n4-lesson-02-practice`. The lesson example solves those items in full. | Change the numbers in both worked examples, or swap the two questions for fresh ones. The other worked examples (0.018 m³/s→L/min, the 15 km catch-up, the 180 km schedule) resemble `l3-028`, `l3-029` and `l4-011` but use different numbers, which is acceptable modelling. |
| L2 | All three lessons | Medium | Depth gate. The standard asks for "at least 2,500 authored characters across its teaching sections", and `LESSON_NOTES_CONTENT_STANDARD.md` reports that N4 "meets the baseline". `lesson_note_depth_shortfalls` measures `len(json.dumps(sections))`, which counts keys, stable keys and `null` fields. On that metric the lessons score 3,626, 3,311 and 3,766. Their teaching prose (titles, blocks, prompts, steps, notes, feedback) is only **1,751, 1,533 and 1,839** characters. Each lesson also has exactly the minimum six sections, and none has a misconception section. | Expand each N4 lesson to the N5 pattern: three explanations, including one on common errors (for example averaging the speeds; forgetting a stop; converting one unit only), two worked examples, recall and a summary. Fix the validator to measure prose; this is out of scope here and noted under R3. |
| L3 | All three lessons | Low | Each active-recall response declares `unit: {canonical: "km/h", required: true}` (or `h`). The checker ignores `unit`. Typing `60 km/h` returns "Enter a number, decimal, fraction, or percentage." and is marked incorrect. The unit spec does not reach the web lesson UI. | Either set `required: false`, or add "Give a number only" to each recall prompt, matching the practice items, whose `unit` is `null` throughout. |
| L4 | `n4-lesson-01` | Low (judgement) | Outcome 4.1 names "constant speed" as a concept, but the lesson covers it in one sentence, and no question asks the learner to distinguish constant speed from average speed. | Consider one short recall or question that contrasts the two, for example "Could the car have travelled at a constant 60 km/h for the whole trip? Explain." |

The arithmetic in every lesson is correct, and each verification note checks its result.
The lesson notes contain no `$` or `S$` contexts.

## Part 2: diagrams and graphs

**This topic has no diagrams, graphs or charts.** None of the 104 questions has an `assets` entry or an image or diagram block. The only block types are `text` and `display_math`. All three lessons have `assets: []`, and their sections contain only `text`, `inline_math` and `display_math` blocks. No SVG for N4 exists under the course `assets/` folder or the bank. Diagrams checked: 0. Diagrams viewed: 0. Since nothing was referenced, the renderer templates in `scripts/recalibrate_geometry_content.py` and `question_bank/src/question_bank/geometry_validation.py` do not apply to N4.

The N4 bank has no `diagram_audit.json`; only the G1 and G5 banks and Secondary 2 G2 have one. Text-only items where a simple schematic would clearly help, offered for a later recommendation and not as defects:

- `n4-l4-016` (train and platform): a front-enters/rear-leaves sketch shows why the distance is 180 + 270 m. This is the most common error on this question type.
- `n4-l4-007` (meeting point after a delayed departure): a line from A to B showing the 08:00–08:30 head start and the closing gap.
- `n4-l3-023`, `n4-l3-031` and the closing-speed explanation in `n4-lesson-03`: arrows for walkway and walker velocities, with and against.
- `n4-lesson-01`'s multi-stage example: a journey timeline in which the rest is visible as time with zero distance.

## Root-cause patterns

- **R1, authored under v1 rules.** Findings 4–7 and 10 (calibration, duplicate operation
  patterns, hint depth) are what house rules v2 now forbids. All four N4 manifests record
  `math-question-authoring-v1`. A v2 regeneration of the affected items, or targeted
  replacement, is the efficient fix.
- **R2, numeric checker parses mixed numbers as concatenated digits.** `_fraction()` removes
  all spaces before `Fraction()`, so `13 1/3` becomes `131/3`. This affects any item whose exact
  answer is a non-integer fraction (`n4-l3-002` here) and is a silent wrong-grade, not a format
  error. The fix belongs in `question_bank/src/question_bank/checking.py`, which is outside this
  audit's edit scope.
- **R3, lesson depth gate measures JSON size.** `course_validation.lesson_note_depth_shortfalls`
  counts serialised JSON, so a lesson with about 1,500 characters of prose passes a 2,500-character
  rule. It affects all three N4 lessons (finding L2) and may affect other topics whose lessons
  sit near the threshold.
- **R4, lesson examples copied from the bank.** Lesson examples were written with the bank
  at hand and reused exact numbers (L1). The same pattern is much more widespread in N5; see
  `PRE_REVIEW_AUDIT_secondary_1_n5.md`.

## Standards conflict for reviewers

The N2 audit model and house rules v2 call for "Singapore/British English", locale `en-SG` and
S$ currency. The current `LESSON_NOTES_CONTENT_STANDARD.md` says the Singapore syllabus "does not
define the learner's country, school system or classroom vocabulary". It asks for international
English, explained terminology and contexts that work across Southeast Asia. The blueprint's
`course` field also still reads "Singapore G3 Mathematics". For N4, the conflict shows up only in
the term "travelator" (finding 16). This audit does not choose between the rules; the content
owner should decide which rule governs learner-facing vocabulary.

## Not verified

- Hosted review state in the database. Only repository files were inspected.
- Rendering with the web app's KaTeX version. `apps/web` depends on `katex ^0.18.7`, but
  rendering here used the vendored 0.16.22. No N4 string uses a construct that changed between
  those versions.
- Whether these items match the actual ASEAN Scholarship test format. No source paper for that
  test is in the repository, so alignment was judged against the course's own outcomes and
  difficulty rubric.
- Cross-bank semantic duplicates beyond `authoring-validate`'s exact and near-duplicate scan,
  which reported 0.
