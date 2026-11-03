# Content fix ledger: Secondary 1 and 2 Mathematics

**Date:** 3 November 2026  
**Base:** `feature/bulk-question-authoring-pipeline` at `fe25859`  
**Machine-readable ledger:** [`CONTENT_FIX_LEDGER.json`](CONTENT_FIX_LEDGER.json)

This ledger turns the 19 pre-review audit reports (`PRE_REVIEW_AUDIT_secondary_*.md`) into one fix list. It is report-only: it changes no question, lesson, asset, manifest or review state, and it records no Mathematics or editorial approval. Founder decisions are listed with options and a recommendation; none is made here.

## At a glance

- 886 findings were extracted from the 19 reports. After merging 44 repeats and splitting partly-confirmed findings, the ledger has **845 records**.
- Every category 1 and 2 finding (166 records) was checked against the current files: **162 confirmed, 4 disputed**. Answers were recomputed independently, and SVG coordinates, labels and text positions were measured.
- **72 batches** need fixes. **4 batches** (Sec 1 N2 b001–b004, approved) are held for founder decision D4. **18 batches** have no recorded finding; all of these are diagnostic batches, and several audits did not cover the v2 diagnostic banks.
- 19 records are fixed by the open checker PR 261 alone; 10 more need a `checker_config` form or unit setting in content once it merges.

| Category (priority order) | Records | Confirmed | Disputed | Open | Checker config | Checker fix | Founder decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1. `wrong_or_unanswerable` | 46 | 45 | 1 |  |  |  |  |
| 2. `misleading_diagram` | 120 | 117 | 3 |  |  |  |  |
| 3. `checker_dependent` | 39 |  |  | 9 | 10 | 19 | 1 |
| 4. `answer_leak` | 68 |  |  | 61 |  |  | 7 |
| 5. `duplicate` | 100 |  |  | 90 |  |  | 10 |
| 6. `outcome_or_teaching_gap` | 207 |  |  | 173 |  |  | 34 |
| 7. `plain_text_math` | 22 |  |  | 21 |  |  | 1 |
| 8. `polish` | 243 |  |  | 198 |  |  | 45 |
| **Total** | **845** | | | | | | |

### Statuses

- `confirmed`: Category 1 or 2 finding reproduced against the current files (answers recomputed, SVG coordinates and text measured). Needs a fix.
- `disputed`: Category 1 or 2 claim that the files do not support, or only partly support. Not relied on; a reviewer may close or re-examine it.
- `open`: Category 3–8 finding accepted from the audit report as written. Not independently re-verified (spot checks are noted in the record).
- `needs_checker_config`: Fixable only in content: set checker_config.form and/or the response unit after PR 261 merges.
- `resolved_by_checker_fix`: Fixed by PR 261 (fix/answer-checker) alone, with no content change, once that PR merges. Still open until then.
- `needs_founder_decision`: The fix, or whether to fix, depends on a founder decision listed in this ledger.

### Categories

1. `wrong_or_unanswerable`: Wrong canonical or accepted answer, wrong worked result or hint, an item that cannot be answered as intended (missing or contradictory givens, two valid answers but one accepted), missing prompt, or corrupted learner-visible text.
2. `misleading_diagram`: An existing diagram contradicts the givens, draws the wrong relationship, misplaces markings or labels, or its alt text contradicts the figure.
3. `checker_dependent`: The content key is right but the checker misjudges answers: resolved by the PR 261 checker fix, or needs a checker_config form/unit setting in content.
4. `answer_leak`: A hint, title, prompt, stem, alt text or diagram label gives away the answer.
5. `duplicate`: Exact or semantic duplicates, repeated templates or numbers, lesson examples equal to bank items, answer clustering.
6. `outcome_or_teaching_gap`: Outcome or difficulty mis-tag, out-of-syllabus content, untaught methods, lesson coverage gaps, solutions that skip the key step, response formats that cannot capture the outcome, a diagram that would clearly help.
7. `plain_text_math`: Mathematics typed as plain text, unsimplified coefficients, math-mode rendering defects.
8. `polish`: Wording, terminology, spelling, mark labels, notation consistency, metadata.

A finding that fits several categories takes the highest-priority one. Each JSON record carries: `id`, `source_report`, `finding_id`, `also_reported_in` (merged repeats), `stable_keys` (questions, lessons, assets), `batches`, `courses`, `category`, `severity` (normalised) and `report_severity`, `status`, `verification`, `proposed_fix`, `needs_new_diagram`, `checker_fix` and `founder_decision`.

## Category 1: wrong or unanswerable (verified)

Every row was reproduced from the files. Corrupted-text rows are listed last within the table because they do not change the mathematics.

| ID | Source | Batch / course | Keys | Defect | Status |
| --- | --- | --- | --- | --- | --- |
| CFL-001 | Sec 2 G4 C1 | `g3-sec2-g4-b004` | `g4-l2-529` | **wrong maths, critical.** Wrong canonical answer: 55-72-89 marked right-angled | confirmed |
| CFL-002 | Sec 2 S1 C-01 | `g3-sec2-s1-b001` | `s1-l4-501` | **wrong maths, critical.** Canonical stored as float noise 4.000000000000002 | confirmed |
| CFL-003 | Sec 2 S1 C-02 | `g3-sec2-s1-b002` | `s1-l4-507` | **wrong maths, critical.** Canonical stored as float noise 3.333333333333332 (true 10/3, no rounding rule) | confirmed |
| CFL-004 | Sec 2 S1 C-03 | `g3-sec2-s1-b003` | `s1-l4-510` | **wrong maths, critical.** Canonical stored as float noise 2.8571428571428577 (true 20/7) | confirmed |
| CFL-009 | Sec 1 N1 C-02 | `g3-sec1-n1-b002` | `n1-l3-021` | **wrong maths, high.** n1-l3-021 hint 2 states a value 1000 times too large | confirmed |
| CFL-010 | Sec 1 N3 C-02 | `g3-sec1-n3-b003` | `n3-l3-018`, `n3-l3-019` | **wrong maths, high.** 'Overall percentage change' answers store unsigned values | confirmed |
| CFL-018 | Sec 2 N5 C-2 | `g3-sec2-n5-b001`, `g3-sec2-n5-b002`, `g3-sec2-n5-b003`, `g3-sec2-n5-b004` | `n5-l2-504`, `n5-l2-527`, `n5-l3-519`, `n5-l3-527` … (+6) | **wrong maths, high.** 'Factorise' keys are not complete factorisations | confirmed |
| CFL-022 | Sec 2 G4 L1 | `g3-sec2-math` | `g4-lesson-03` | **wrong maths, high.** Lesson calls elevation/depression angles "corresponding" instead of alternate | confirmed |
| CFL-023 | Sec 2 G5 C1 | `g3-sec2-g5-b002` | `g5-l4-507` | **wrong maths, high.** Wrong liquid-depth answer: 7 instead of 7.5 | confirmed |
| CFL-024 | Sec 2 G5 C2 | `g3-sec2-g5-b004` | `g5-l4-514` | **wrong maths, high.** Wrong liquid-depth answer: 10 instead of 10.5 | confirmed |
| CFL-046 | Sec 1 N3 C-02 (disputed part) | `g3-sec1-n3-b002`, `g3-sec1-n3-b004` | `n3-l3-012`, `n3-l3-027` | **wrong maths, high.** 'Overall percentage change' answers store unsigned values | disputed |
| CFL-029 | Sec 1 N1 C-12 | `g3-sec1-n1-b001` | `n1-l3-013` | **wrong maths, medium.** n1-l3-013 accepts the inexact decimal 0.6666666666666666 | confirmed |
| CFL-030 | Sec 1 N5 12b | `g3-sec1-n5-b001` | `n5-l3-008` | **wrong maths, medium.** 'Factorise completely' key 6(2x^2-3x+1) is not complete | confirmed |
| CFL-035 | Sec 2 N5 lesson-findings/1 | `g3-sec2-math` | `n5-lesson-15` | **wrong maths, medium.** Wrong value in lesson 15 example 2 check note | confirmed |
| CFL-040 | Sec 2 S2 C-19 | `g3-sec2-s2-b004` | `s2-l3-524` | **wrong maths, medium.** Stage-2 hint prescribes the wrong subtraction order | confirmed |
| CFL-042 | Sec 2 N5 lesson-findings/2 | `g3-sec2-math` | `n5-lesson-15` | **wrong maths, low.** Wrong cancelled factor in lesson 15 example 1 check note | confirmed |
| CFL-005 | Sec 2 S1 C-07 | `g3-sec2-s1-b001`, `g3-sec2-s1-b002` | `s1-l3-506`, `s1-l3-514` | **unanswerable or ambiguous, critical.** Mode equals median in "not pulled upward" items | confirmed |
| CFL-006 | Sec 2 S1 C-08 | `g3-sec2-s1-b003`, `g3-sec2-s1-b004` | `s1-l3-521`, `s1-l3-522`, `s1-l3-530`, `s1-l3-531` | **unanswerable or ambiguous, critical.** Mode equals median in "ordinary delivery" items | confirmed |
| CFL-007 | Sec 2 S1 C-09 | `g3-sec2-s1-b001`, `g3-sec2-s1-b002`, `g3-sec2-s1-b003`, `g3-sec2-s1-b004` | `s1-l2-504`, `s1-l2-512`, `s1-l3-503`, `s1-l3-510` … (+3) | **unanswerable or ambiguous, critical.** Stem-and-leaf vs dot-diagram keys for near-identical requirements | confirmed |
| CFL-008 | Sec 2 S1 C-10 | `g3-sec2-s1-b001`, `g3-sec2-s1-b002`, `g3-sec2-s1-b003` | `s1-l4-503`, `s1-l4-508`, `s1-l4-512` | **unanswerable or ambiguous, critical.** "Least suitable because overcrowded" also fits stem-and-leaf | confirmed |
| CFL-011 | Sec 1 N3 C-03 | `g3-sec1-n3-b003` | `n3-l4-011` | **unanswerable or ambiguous, high.** Salary comparison presupposes a difference that is zero | confirmed |
| CFL-014 | Sec 1 G1 C-01 | `g3-sec1-g1-b001`, `g3-sec1-g1-b002`, `g3-sec1-g1-b003`, `g3-sec1-g1-b004` | `g1-l2-005`, `g1-l2-013`, `g1-l2-021`, `g1-l3-006` … (+7) | **unanswerable or ambiguous, high.** Quadrilateral code legend missing from 11 questions | confirmed |
| CFL-015 | Sec 1 G5 C-01 | `g3-sec1-g5-b002` | `g5-l3-011` | **unanswerable or ambiguous, high.** Joined rectangles: answer x = 3 is not an edge length | confirmed |
| CFL-016 | Sec 1 G5 C-02 | `g3-sec1-g5-b002` | `g5-l4-005` | **unanswerable or ambiguous, high.** Parallelogram given only as "20 cm by 10 cm" (area undetermined) | confirmed |
| CFL-017 | Sec 2 N2 C-03 | `g3-sec2-n2-b002` | `n2-l2-516` | **unanswerable or ambiguous, high.** Degenerate inverse-proportion item: second speed equals the first | confirmed |
| CFL-021 | Sec 2 G4 C6b | `g3-sec2-g4-b001`, `g3-sec2-g4-b002`, `g3-sec2-g4-b003`, `g3-sec2-g4-b004` | `g4-l1-509`, `g4-l1-518`, `g4-l2-511`, `g4-l2-520` … (+5) | **unanswerable or ambiguous, high.** Stem asserts a right triangle for nine triangles that are not right-angled | confirmed |
| CFL-031 | Sec 1 G1 C-03 | `g3-sec1-g1-b002`, `g3-sec1-g1-b003` | `g1-l2-010`, `g1-l2-011`, `g1-l2-019`, `g1-l3-011` … (+3) | **unanswerable or ambiguous, medium.** Parallel-line condition missing from six questions (and lesson 03) | confirmed |
| CFL-032 | Sec 1 G1 C-04 | `g3-sec1-g1-b003` | `g1-l2-020` | **unanswerable or ambiguous, medium.** g1-l2-020 asks for an acute angle that does not exist | confirmed |
| CFL-033 | Sec 1 G1 C-05a | `g3-sec1-g1-b001` | `g1-l5-001` | **unanswerable or ambiguous, medium.** g1-l5-001 orientation of the two transversals is ambiguous | confirmed |
| CFL-034 | Sec 1 G1 L-01 | `g3-sec1-math` | `g1-lesson-03` | **unanswerable or ambiguous, medium.** Lesson 03 example and recall omit the parallel condition | confirmed |
| CFL-037 | Sec 2 G2 1.2/3 | `g3-sec2-g2-b003` | `g2-l2-521` | **unanswerable or ambiguous, medium.** Original and copy not identified, so two answers are valid | confirmed |
| CFL-038 | Sec 2 G2 1.2/5 | `g3-sec2-g2-b004` | `g2-l3-530` | **unanswerable or ambiguous, medium.** Mirror problem: "2 m from the mirror" is the eye distance; level-ground conditions missing | confirmed |
| CFL-045 | Sec 2 S1 C-11 | `g3-sec2-s1-b003`, `g3-sec2-s1-b004` | `s1-l2-521`, `s1-l2-522`, `s1-l2-528` | **unanswerable or ambiguous, low.** "Keep every age, arrange in order, reveal distribution" also fits a dot diagram | confirmed |
| CFL-012 | Sec 1 N5 6 | `g3-sec1-n5-b002` | `n5-l1-006` | **missing prompt, high.** Prompt never states the task | confirmed |
| CFL-027 | Sec 2 S1 X-03 | `g3-sec2-math` | `s1-lesson-06`, `s1-lesson-07`, `s1-lesson-09` | **pool exposure, high.** Defective items sit in live pools | confirmed |
| CFL-013 | Sec 1 N5 7 | `g3-sec1-n5-b001`, `g3-sec1-n5-b002`, `g3-sec1-n5-b003`, `g3-sec1-n5-b004` | `n5-l2-002`, `n5-l2-008`, `n5-l2-010`, `n5-l2-031` … (+5) | **corrupted text, high.** Tab-escape corruption in solution LaTeX (\times, \text) | confirmed |
| CFL-019 | Sec 2 N5 C-6 | `g3-sec2-n5-b001`, `g3-sec2-n5-b002`, `g3-sec2-n5-b003`, `g3-sec2-n5-b004` | `n5-l1-501`, `n5-l1-502`, `n5-l1-503`, `n5-l1-504` … (+100) | **corrupted text, high.** Generator codenames in every prompt and title | confirmed |
| CFL-020 | Sec 2 N6 C-6 | `g3-sec2-n6-b001`, `g3-sec2-n6-b002`, `g3-sec2-n6-b003`, `g3-sec2-n6-b004` | `n6-l1-501`, `n6-l1-502`, `n6-l1-503`, `n6-l1-504` … (+100) | **corrupted text, high.** Generator codenames in every title and prompt | confirmed |
| CFL-025 | Sec 2 S1 C-04 | `g3-sec2-s1-b001`, `g3-sec2-s1-b002`, `g3-sec2-s1-b003`, `g3-sec2-s1-b004` | `s1-l2-505`, `s1-l2-506`, `s1-l2-513`, `s1-l2-523` … (+1) | **corrupted text, high.** Raw TAB in solution LaTeX renders "\times" as "imes" | confirmed |
| CFL-026 | Sec 2 S1 W-01 | `g3-sec2-s1-b001`, `g3-sec2-s1-b002`, `g3-sec2-s1-b003`, `g3-sec2-s1-b004` | `s1-l1-501`, `s1-l1-502`, `s1-l1-503`, `s1-l1-504` … (+100) | **corrupted text, high.** Generator prefix "<Colour> <Tree> Bay dataset for <club>: <slug> —" in every prompt and title | confirmed |
| CFL-028 | Sec 1 N1 C-08 | `g3-sec1-n1-b001` | `n1-l2-016` | **corrupted text, medium.** n1-l2-016 solution contains mis-encoded 'Ò' | confirmed |
| CFL-036 | Sec 2 G2 1.2/1 | `g3-sec2-g2-b002` | `g2-l2-509` | **corrupted text, medium.** Badge described as both kite-shaped and triangular | confirmed |
| CFL-041 | Sec 1 G5 D-12a | `g3-sec1-g5-b001` | `g5-l3-007` | **corrupted text, low.** Alt text and <desc> state 500 cm² instead of 6 500 cm² | confirmed |
| CFL-043 | Sec 2 G2 1.2/2 | `g3-sec2-g2-b004` | `g2-l2-524` | **corrupted text, low.** Template residue "badge or pennant" in a pennant-only item | confirmed |
| CFL-044 | Sec 2 G2 1.2/6 | `g3-sec2-g2-b003` | `g2-l4-512` | **corrupted text, low.** Title "Shadow with sloping ground correction" contradicts "level ground" | confirmed |
| CFL-039 | Sec 2 G4 R3 | tooling | — | **tooling, medium.** No validator recomputes answers or checks answer form | confirmed |

Key evidence for the answer-changing rows:

- CFL-001: `g4-l2-529` 55² + 72² = 8209 ≠ 89² = 7921, so the triangle is not right-angled; key is 1, correct answer 0.
- CFL-002: `s1-l4-501` key stored as `4.000000000000002`; the exact difference of the grouped means is 4, which the checker rejects.
- CFL-003: `s1-l4-507` key `3.333333333333332`; true value 10/3 with no rounding instruction.
- CFL-004: `s1-l4-510` key `2.8571428571428577`; true value 20/7.
- CFL-005: `s1-l3-506` values 8, 9, 9, 10, 45 have median = mode = 9, so code 3 (mode) is as valid as the keyed code 2.
- CFL-009: `n1-l3-021` hint says the unrounded result is 1914.0625; (6.4×10⁵ − 2.75×10⁴) / (3.2×10⁵) = 1.9140625.
- CFL-010: `n3-l3-018` 500 → 550 → 484 is a 3.2% decrease, keyed as unsigned 3.2 so −3.2 is marked wrong (also `n3-l3-019`).
- CFL-011: `n3-l4-011` both new salaries equal 1.08x, so 'by what percentage is Asha's salary greater' presupposes a false difference (key 0).
- CFL-015: `g5-l3-011` rectangles 9×7 and 6×5 joined along an edge of length x with perimeter 48 gives x = 3, which is not an edge of either rectangle (full-edge joins give 44 or 42).
- CFL-016: `g5-l4-005` a parallelogram given only as '20 cm by 10 cm' has area 200 sin θ, so the item depends on reading 10 as the height.
- CFL-017: `n2-l2-516` asks for the time at 40 km/h when the original speed is already 40 km/h.
- CFL-018: 10 'factorise' keys leave a common factor inside a bracket, e.g. complete forms 9(x+1)(3x+8), 45(x+1)², 4(x+1)(x+7).
- CFL-021: Nine converse items whose triangles are not right-angled still say 'Use the labelled right-triangle schematic'.
- CFL-022: `g4-lesson-03` calls angles of elevation and depression 'corresponding'; they are alternate angles.
- CFL-023: `g5-l4-507` cone of height 15 filled to 1/8 of its volume: depth = 15 × ∛(1/8) = 7.5; key is 7.
- CFL-024: `g5-l4-514` same with height 21: depth 10.5; key is 10.
- CFL-029: `n1-l3-013` accepts the inexact decimal 0.6666666666666666 for an exact answer.
- CFL-030: `n5-l3-008` key 6(2x²−3x+1) is not complete: 6(2x−1)(x−1).
- CFL-032: `g1-l2-020` asks for the acute angle between the diagonals of a square; they are perpendicular.
- CFL-035: `n5-lesson-15` example 2 check note says 1.25 on both sides; both sides equal 1/2.
- CFL-037: `g2-l2-521` never says which arrowhead is the original, so 15 and 60 are both valid; only 15 is accepted.
- CFL-040: `s2-l3-524` stage-2 hint says expected − observed (120 − 132 = −12); key is 12.

## Category 2: misleading diagrams (verified)

| Report | Records | Confirmed | Disputed | Critical/high | Question diagrams affected | Lesson diagrams affected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sec 1 G1 | 21 | 20 | 1 | 7 | 21 | 4 |
| Sec 1 G5 | 21 | 21 | 0 | 11 | 15 | 5 |
| Sec 1 N6 | 2 | 1 | 1 | 0 | 0 | 1 |
| Sec 1 S1 | 2 | 2 | 0 | 0 | 0 | 2 |
| Sec 2 G2 | 31 | 30 | 1 | 13 | 15 | 5 |
| Sec 2 G4 | 8 | 8 | 0 | 6 | 43 | 0 |
| Sec 2 G5 | 13 | 13 | 0 | 4 | 104 | 1 |
| Sec 2 N2 | 3 | 3 | 0 | 3 | 0 | 2 |
| Sec 2 N6 | 3 | 3 | 0 | 0 | 0 | 2 |
| Sec 2 N7 | 4 | 4 | 0 | 1 | 0 | 2 |
| Sec 2 S1 | 8 | 8 | 0 | 8 | 0 | 5 |
| Sec 2 S2 | 4 | 4 | 0 | 0 | 0 | 2 |

Critical and high-severity diagram findings:

- CFL-047 (Sec 2 G4 D3, critical): Non-right triangles drawn with a right-angle marker. Keys: `g4-l1-509`, `g4-l1-518`, `g4-l2-511`, `g4-l2-520` … (+5).
- CFL-048 (Sec 1 G1 D-01a, high): g1-l1-001: 35° question shows a 60/90/120/240 strip; alt text claims 35°. Keys: `g1-l1-001`.
- CFL-049 (Sec 1 G1 D-03a, high): g1-l5-001: two-transversal question drawn with one transversal. Keys: `g1-l5-001`.
- CFL-050 (Sec 1 G1 D-04a, high): g1-l1-004, g1-l5-004: hierarchy chart ends at 'square', the answer. Keys: `g1-l1-004`, `g1-l5-004`.
- CFL-051 (Sec 1 G1 D-05a, high): exterior template: exterior-angle arc mismarked; hexagon not regular. Keys: `g1-l1-005`, `g1-l3-007`, `g1-l5-003`, `g1-lesson-06`.
- CFL-052 (Sec 1 G1 D-07a, high): g1-l5-005: kite question shows triangle, trapezium and hexagon. Keys: `g1-l5-005`.
- CFL-053 (Sec 1 G1 part2-global/1, high): No question diagram shows its question's values or labels. Keys: `g1-l1-001`, `g1-l2-001`, `g1-l3-001`, `g1-l1-002` … (+12).
- CFL-054 (Sec 1 G5 D-01, high): Parallelogram diagram: unrelated trapezium and "h" beside the slant. Keys: `g5-l1-001`.
- CFL-055 (Sec 1 G5 D-03, high): Area-addition question shown as a cut-out (subtraction). Keys: `g5-l1-003`.
- CFL-056 (Sec 1 G5 D-04, high): Cuboid question shown as a house prism and a cylinder. Keys: `g5-l1-004`.
- CFL-057 (Sec 1 G5 D-11, high): Right-triangle prism drawn as an isosceles "house" prism. Keys: `g5-l3-005`.
- CFL-058 (Sec 1 G5 D-13, high): Two identical cubes drawn as unequal rectangles with partial contact. Keys: `g5-l3-008`.
- CFL-059 (Sec 1 G5 D-15, high): Labels a, b, h conflict with the question's variables. Keys: `g5-l5-001`.
- CFL-060 (Sec 1 G5 D-16, high): Joined-rectangles perimeter question shown as a cut-out L-shape. Keys: `g5-l5-002`.
- CFL-061 (Sec 1 G5 D-18, high): Box-packing question shown with grid, arrow and cube (no box). Keys: `g5-l5-004`.
- CFL-062 (Sec 1 G5 D-22, high): Lesson 01 area diagram: alt text claims marked heights; "h" on the slants. Keys: `g5-lesson-01`.
- CFL-063 (Sec 1 G5 D-26, high): Lesson 03: alt text says triangular prism; drawing is a pentagonal prism. Keys: `g5-lesson-03`.
- CFL-064 (Sec 1 G5 D-27, high): Lesson 04: alt text claims a metre square of centimetre squares; drawing is an unlabelled 4 x 4 grid. Keys: `g5-lesson-04`.
- CFL-065 (Sec 2 N2 D-01, high): Map lengths drawn at inconsistent scales (1 cm longer than 2 cm). Keys: `n2-lesson-04`.
- CFL-066 (Sec 2 N2 D-02, high): Side lengths written in the centre of each square. Keys: `n2-lesson-04`.
- CFL-067 (Sec 2 N2 D-06, high): "y = k/x" curve is a Bezier, not a hyperbola; dots do not keep xy constant. Keys: `n2-lesson-05`.
- CFL-068 (Sec 2 N7 D1, high): Lesson 08: solution marker is not at the crossing. Keys: `n7-lesson-08`.
- CFL-069 (Sec 2 G2 D-ALL-1, high): Question diagrams show none of the question's givens. Keys: `g2-l1-501`, `g2-l1-503`, `g2-l1-504`, `g2-l1-505` … (+11).
- CFL-070 (Sec 2 G2 D-C1, high): Congruent template: triangles are not congruent. Keys: `g2-l1-501`, `g2-l3-501`, `g2-l5-501`, `g2-lesson-01`.
- CFL-071 (Sec 2 G2 D-C4, high): g2-l1-501: caption reveals the answer; ABC drawn isosceles for a scalene tile. Keys: `g2-l1-501`.
- CFL-072 (Sec 2 G2 D-C5, high): g2-l3-501: no vertex letters or side labels for AB and PQ. Keys: `g2-l3-501`.
- CFL-073 (Sec 2 G2 D-C6, high): g2-l5-501: pentagon question shows triangles. Keys: `g2-l5-501`.
- CFL-074 (Sec 2 G2 D-E3, high): g2-l1-505: origin enlargement x2 drawn as centre C, factor 3. Keys: `g2-l1-505`.
- CFL-075 (Sec 2 G2 D-E5, high): g2-l5-504: three successive factors drawn as one x3 enlargement. Keys: `g2-l5-504`.
- CFL-076 (Sec 2 G2 D-P1, high): Proportion template: triangles shown as similar are not. Keys: `g2-l1-504`, `g2-l3-505`, `g2-l5-503`, `g2-lesson-03`.
- CFL-077 (Sec 2 G2 D-P5, high): g2-l5-503: ABC/ADE shared-vertex configuration drawn as separate ABC and PQR. Keys: `g2-l5-503`.
- CFL-078 (Sec 2 G2 D-S1, high): Similar template: "original" and "image" are not similar. Keys: `g2-l1-503`, `g2-l3-503`, `g2-l5-502`, `g2-lesson-02`.
- CFL-079 (Sec 2 G2 D-S4, high): g2-l5-502: three polygons in the question, two triangles in the diagram. Keys: `g2-l5-502`.
- CFL-080 (Sec 2 G2 D-S5, high): Lesson 02 alt text says rectangles; drawing shows triangles. Keys: `g2-lesson-02`.
- CFL-081 (Sec 2 G2 D-SC3, high): g2-l3-508: arrow points plan -> actual, question goes real garden -> model. Keys: `g2-l3-508`.
- CFL-082 (Sec 2 G4 D4, high): Angle arc and label drawn at the right-angle vertex. Keys: `g4-l1-505`, `g4-l1-506`, `g4-l1-511`, `g4-l1-515` … (+30).
- CFL-083 (Sec 2 G4 D5, high): Drawn acute angle is always 29.9° regardless of the stated angle. Keys: `g4-l1-505`, `g4-l1-506`, `g4-l1-511`, `g4-l1-515` … (+18).
- CFL-084 (Sec 2 G4 D6, high): g4-l3-508 labels an impossible hypotenuse of 89. Keys: `g4-l3-508`.
- CFL-085 (Sec 2 G4 D7, high): Two-position diagram shows only the far triangle. Keys: `g4-l5-505`.
- CFL-087 (Sec 2 G5 D1, high): Pyramid drawn with a triangular base. Keys: `g5-l2-503`, `g5-l2-507`, `g5-l2-509`, `g5-l2-513` … (+17).
- CFL-088 (Sec 2 G5 D2, high): Pyramid height foot outside the base; apex off-centre. Keys: `g5-l1-501`, `g5-l1-505`, `g5-l1-509`, `g5-l1-512` … (+23).
- CFL-089 (Sec 2 G5 D3, high): Slant height given but only the vertical height is drawn. Keys: `g5-l2-501`, `g5-l2-505`, `g5-l2-511`, `g5-l2-515` … (+9).
- CFL-090 (Sec 2 G5 D4, high): Wrong solid drawn for 15 items. Keys: `g5-l5-502`, `g5-l5-501`, `g5-l1-502`, `g5-l1-506` … (+11).
- CFL-091 (Sec 2 S1 D-01, high): Lesson 05 captions overlap ("frequency." prints over "A key"). Keys: `s1-lesson-05`.
- CFL-092 (Sec 2 S1 D-03, high): Lesson 05 figure lacks scale, class boundaries and key it tells learners to read. Keys: `s1-lesson-05`.
- CFL-093 (Sec 2 S1 D-04, high): Lesson 05 panels show three different datasets under "Three views of a distribution". Keys: `s1-lesson-05`.
- CFL-094 (Sec 2 S1 D-06, high): Lesson 06 guide maps "exact lookup" to frequency table. Keys: `s1-lesson-06`.
- CFL-095 (Sec 2 S1 D-10, high): Lesson 07 key message clipped at the viewBox edge. Keys: `s1-lesson-07`.
- CFL-096 (Sec 2 S1 D-11, high): Lesson 07 charts have no vertical axis or ticks. Keys: `s1-lesson-07`.
- CFL-097 (Sec 2 S1 D-13, high): Lesson 08 number line not uniform; mean marker misplaced. Keys: `s1-lesson-08`.
- CFL-098 (Sec 2 S1 D-15, high): Lesson 09 median marker between the 2nd and 3rd dots. Keys: `s1-lesson-09`.

Systemic records in category 2 with `fix_surface: tooling` (CFL-086, CFL-112, CFL-113, CFL-114, CFL-138, CFL-144) carry no batch and are listed under tooling below.

## Disputed findings

These are not relied on. Each was a category 1 or 2 claim that the files do not, or only partly, support.

- **CFL-046** (Sec 1 N3 C-02 (disputed part)): 'Overall percentage change' answers store unsigned values. Split from C-02: the files do not show the defect for these keys. Confirmed keys: ['n3-l3-018', 'n3-l3-019'].
- **CFL-164** (Sec 1 G1 part2-global/1 (disputed part)): No question diagram shows its question's values or labels. Split from part2-global/1: the files do not show the defect for these keys. Confirmed keys: ['g1-l1-001', 'g1-l1-002', 'g1-l1-004', 'g1-l1-005', 'g1-l1-009', 'g1-l2-001', 'g1-l3-001', 'g1-l3-002', 'g1-l3-004', 'g1-l3-006', 'g1-l3-007', 'g1-l3-008', 'g1-l5-001', 'g1-l5-003', 'g1-l5-004', 'g1-l5-005'].
- **CFL-165** (Sec 1 N6 D1): Unexplained dashed guides meet at (4, 8) on the intercept graph. Facts in the report are accurate (corner at (4, 8), never mentioned) but the guides do not contradict any given or draw a wrong relationship. Recommend treating this as polish (unexplained construction lines).
- **CFL-166** (Sec 2 G2 D-ALL-2 (disputed part)): Alt text lists measures that are not drawn. Split from D-ALL-2: the files do not show the defect for these keys. Confirmed keys: ['g2-l1-501', 'g2-l1-503', 'g2-l1-504', 'g2-l1-506', 'g2-l3-501', 'g2-l3-503', 'g2-l3-507', 'g2-l3-508', 'g2-l5-501', 'g2-l5-502', 'g2-l5-503', 'g2-l5-504', 'g2-l5-505'].

## Ordered batch fix list (Sec 1 and Sec 2 together)

Most serious first. Tier 1 has a confirmed wrong answer, unanswerable or ambiguous item, or missing prompt; tier 2 corrupted text only; tier 3 misleading diagrams; tiers 4–9 the highest remaining category. Within a tier, batches are ordered by severity-weighted affected keys. Counts are distinct question keys with actionable findings. The full finding list per batch is in `batch_fix_order` in the JSON.

| # | Batch | Topic | Tier | Category 1 keys | Diagram keys (cat 2) | Checker config keys | Diagrams to redraw / add | Main category 1 records | Existing claim |
| ---: | --- | --- | ---: | --- | ---: | ---: | --- | --- | --- |
| 1 | `g3-sec2-s1-b003` | Sec 2 S1 Data handling and analysis | 1 | 1 wrong; 6 ambiguous/unanswerable; 26 corrupted text | — | 1 | 0 / 8 | CFL-004, CFL-006, CFL-007, CFL-008, CFL-025 | — |
| 2 | `g3-sec2-s1-b001` | Sec 2 S1 Data handling and analysis | 1 | 1 wrong; 4 ambiguous/unanswerable; 26 corrupted text | — | 2 | 0 / 10 | CFL-002, CFL-005, CFL-007, CFL-008, CFL-025 | — |
| 3 | `g3-sec2-s1-b002` | Sec 2 S1 Data handling and analysis | 1 | 1 wrong; 4 ambiguous/unanswerable; 26 corrupted text | — | 1 | 0 / 9 | CFL-003, CFL-005, CFL-007, CFL-008, CFL-025 | — |
| 4 | `g3-sec2-s1-b004` | Sec 2 S1 Data handling and analysis | 1 | 5 ambiguous/unanswerable; 26 corrupted text | — | 1 | 0 / 8 | CFL-006, CFL-007, CFL-045, CFL-025 | — |
| 5 | `g3-sec1-g1-b003` | Sec 1 G1 Angles, triangles and polygons | 1 | 7 ambiguous/unanswerable | 1 | — | 1 / 2 | CFL-014, CFL-031, CFL-032 | — |
| 6 | `g3-sec1-g1-b002` | Sec 1 G1 Angles, triangles and polygons | 1 | 6 ambiguous/unanswerable | 3 | — | 3 / 3 | CFL-014, CFL-031 | — |
| 7 | `g3-sec2-g4-b004` | Sec 2 G4 Pythagoras' theorem and trigonometry | 1 | 1 wrong; 3 ambiguous/unanswerable | 12 | 3 | 26 / 0 | CFL-001, CFL-021 | — |
| 8 | `g3-sec2-n5-b004` | Sec 2 N5 Algebraic expressions and formulae | 1 | 4 wrong; 26 corrupted text | — | 22 | 0 / 0 | CFL-018, CFL-019 | — |
| 9 | `g3-sec1-g1-b001` | Sec 1 G1 Angles, triangles and polygons | 1 | 4 ambiguous/unanswerable | 16 | — | 16 / 1 | CFL-014, CFL-033 | — |
| 10 | `g3-sec2-g4-b002` | Sec 2 G4 Pythagoras' theorem and trigonometry | 1 | 3 ambiguous/unanswerable | 11 | 2 | 26 / 0 | CFL-021 | — |
| 11 | `g3-sec1-n3-b003` | Sec 1 N3 Percentage | 1 | 2 wrong; 1 ambiguous/unanswerable | — | 1 | 0 / 0 | CFL-010, CFL-011 | — |
| 12 | `g3-sec2-n5-b002` | Sec 2 N5 Algebraic expressions and formulae | 1 | 2 wrong; 26 corrupted text | — | 23 | 0 / 0 | CFL-018, CFL-019 | — |
| 13 | `g3-sec2-n5-b001` | Sec 2 N5 Algebraic expressions and formulae | 1 | 2 wrong; 26 corrupted text | — | 22 | 0 / 0 | CFL-018, CFL-019 | — |
| 14 | `g3-sec2-n5-b003` | Sec 2 N5 Algebraic expressions and formulae | 1 | 2 wrong; 26 corrupted text | — | 21 | 0 / 0 | CFL-018, CFL-019 | — |
| 15 | `g3-sec2-g4-b003` | Sec 2 G4 Pythagoras' theorem and trigonometry | 1 | 2 ambiguous/unanswerable | 11 | 2 | 26 / 0 | CFL-021 | — |
| 16 | `g3-sec1-g1-b004` | Sec 1 G1 Angles, triangles and polygons | 1 | 2 ambiguous/unanswerable | 1 | — | 1 / 2 | CFL-014 | — |
| 17 | `g3-sec1-g5-b002` | Sec 1 G5 Mensuration | 1 | 2 ambiguous/unanswerable | 1 | — | 1 / 5 | CFL-015, CFL-016 | — |
| 18 | `g3-sec1-n5-b002` | Sec 1 N5 Algebraic expressions and formulae | 1 | 1 no prompt; 2 corrupted text | — | 23 | 0 / 0 | CFL-012, CFL-013 | — |
| 19 | `g3-sec2-g5-b004` | Sec 2 G5 Mensuration | 1 | 1 wrong | 26 | 2 | 26 / 0 | CFL-024 | — |
| 20 | `g3-sec2-g5-b002` | Sec 2 G5 Mensuration | 1 | 1 wrong | 26 | 1 | 26 / 0 | CFL-023 | — |
| 21 | `g3-sec2-g4-b001` | Sec 2 G4 Pythagoras' theorem and trigonometry | 1 | 1 ambiguous/unanswerable | 9 | 3 | 26 / 0 | CFL-021 | — |
| 22 | `g3-sec1-n1-b002` | Sec 1 N1 Numbers and their operations | 1 | 1 wrong | — | — | 0 / 0 | CFL-009 | `questions/g3-sec1-n1-b002-willedward` |
| 23 | `g3-sec2-n2-b002` | Sec 2 N2 Ratio and proportion | 1 | 1 ambiguous/unanswerable | — | — | 0 / 0 | CFL-017 | — |
| 24 | `g3-sec1-n5-b001` | Sec 1 N5 Algebraic expressions and formulae | 1 | 1 wrong; 4 corrupted text | — | 23 | 0 / 0 | CFL-030, CFL-013 | — |
| 25 | `g3-sec2-g2-b004` | Sec 2 G2 Congruence and similarity | 1 | 1 ambiguous/unanswerable; 1 corrupted text | 2 | — | 2 / 1 | CFL-038, CFL-043 | — |
| 26 | `g3-sec2-g2-b003` | Sec 2 G2 Congruence and similarity | 1 | 1 ambiguous/unanswerable; 1 corrupted text | 1 | — | 1 / 5 | CFL-037, CFL-044 | — |
| 27 | `g3-sec1-n1-b001` | Sec 1 N1 Numbers and their operations | 1 | 1 wrong; 1 corrupted text | — | — | 0 / 0 | CFL-029, CFL-028 | `questions/g3-sec1-n1-b001-willedward` |
| 28 | `g3-sec2-s2-b004` | Sec 2 S2 Probability | 1 | 1 wrong | — | — | 0 / 0 | CFL-040 | — |
| 29 | `g3-sec2-n6-b001` | Sec 2 N6 Functions and graphs | 2 | 26 corrupted text | — | — | 0 / 2 | CFL-020 | — |
| 30 | `g3-sec2-n6-b003` | Sec 2 N6 Functions and graphs | 2 | 26 corrupted text | — | — | 0 / 1 | CFL-020 | — |
| 31 | `g3-sec2-n6-b002` | Sec 2 N6 Functions and graphs | 2 | 26 corrupted text | — | — | 0 / 3 | CFL-020 | — |
| 32 | `g3-sec2-n6-b004` | Sec 2 N6 Functions and graphs | 2 | 26 corrupted text | — | — | 0 / 2 | CFL-020 | — |
| 33 | `g3-sec1-n5-b004` | Sec 1 N5 Algebraic expressions and formulae | 2 | 2 corrupted text | — | 23 | 0 / 0 | CFL-013 | — |
| 34 | `g3-sec1-g5-b001` | Sec 1 G5 Mensuration | 2 | 1 corrupted text | 10 | — | 11 / 2 | CFL-041 | — |
| 35 | `g3-sec2-g2-b002` | Sec 2 G2 Congruence and similarity | 2 | 1 corrupted text | 1 | — | 1 / 2 | CFL-036 | — |
| 36 | `g3-sec1-n5-b003` | Sec 1 N5 Algebraic expressions and formulae | 2 | 1 corrupted text | — | 22 | 0 / 0 | CFL-013 | — |
| 37 | `g3-sec2-g5-b001` | Sec 2 G5 Mensuration | 3 | — | 26 | 1 | 26 / 0 | — | — |
| 38 | `g3-sec2-g5-b003` | Sec 2 G5 Mensuration | 3 | — | 26 | 1 | 26 / 0 | — | — |
| 39 | `g3-sec2-g2-b001` | Sec 2 G2 Congruence and similarity | 3 | — | 11 | — | 11 / 2 | — | — |
| 40 | `g3-sec1-g5-b004` | Sec 1 G5 Mensuration | 3 | — | 2 | — | 2 / 4 | — | — |
| 41 | `g3-sec1-g5-b003` | Sec 1 G5 Mensuration | 3 | — | 1 | — | 1 / 4 | — | — |
| 42 | `g3-sec2-s2-b002` | Sec 2 S2 Probability | 4 | — | — | 1 | 0 / 1 | — | — |
| 43 | `g3-sec2-s2-b003` | Sec 2 S2 Probability | 4 | — | — | 1 | 0 / 1 | — | — |
| 44 | `g3-sec2-s2-b001` | Sec 2 S2 Probability | 4 | — | — | 1 | 0 / 0 | — | — |
| 45 | `g3-sec1-s1-b003` | Sec 1 S1 Data handling and analysis | 4 | — | — | 4 | 0 / 6 | — | — |
| 46 | `g3-sec1-n1-b003` | Sec 1 N1 Numbers and their operations | 4 | — | — | — | 0 / 0 | — | `questions/g3-sec1-n1-b003-willedward` |
| 47 | `g3-sec1-n3-b004` | Sec 1 N3 Percentage | 4 | — | — | 2 | 0 / 0 | — | — |
| 48 | `g3-sec1-n3-b001` | Sec 1 N3 Percentage | 4 | — | — | 2 | 0 / 0 | — | — |
| 49 | `g3-sec1-n3-b002` | Sec 1 N3 Percentage | 4 | — | — | 2 | 0 / 0 | — | — |
| 50 | `g3-sec1-s1-b001` | Sec 1 S1 Data handling and analysis | 4 | — | — | 1 | 0 / 11 | — | — |
| 51 | `g3-sec1-s1-b002` | Sec 1 S1 Data handling and analysis | 4 | — | — | 1 | 0 / 5 | — | — |
| 52 | `g3-sec1-s1-b004` | Sec 1 S1 Data handling and analysis | 4 | — | — | 1 | 0 / 10 | — | — |
| 53 | `g3-sec1-n7-b004` | Sec 1 N7 Equations and inequalities | 4 | — | — | — | 0 / 0 | — | — |
| 54 | `g3-sec1-n6-b004` | Sec 1 N6 Functions and graphs | 4 | — | — | — | 0 / 0 | — | — |
| 55 | `g3-sec1-n6-b002` | Sec 1 N6 Functions and graphs | 4 | — | — | — | 0 / 0 | — | — |
| 56 | `g3-sec1-n3-diagnostic-b001` | Sec 1 N3 Percentage | 4 | — | — | 1 | 0 / 0 | — | — |
| 57 | `g3-sec2-n7-b004` | Sec 2 N7 Equations and inequalities | 5 | — | — | — | 0 / 6 | — | — |
| 58 | `g3-sec2-n7-b003` | Sec 2 N7 Equations and inequalities | 5 | — | — | — | 0 / 6 | — | — |
| 59 | `g3-sec2-n7-b001` | Sec 2 N7 Equations and inequalities | 5 | — | — | — | 0 / 5 | — | — |
| 60 | `g3-sec2-n7-b002` | Sec 2 N7 Equations and inequalities | 5 | — | — | — | 0 / 6 | — | — |
| 61 | `g3-sec1-n7-b001` | Sec 1 N7 Equations and inequalities | 5 | — | — | — | 0 / 0 | — | — |
| 62 | `g3-sec1-n7-b002` | Sec 1 N7 Equations and inequalities | 5 | — | — | — | 0 / 0 | — | — |
| 63 | `g3-sec2-n2-b004` | Sec 2 N2 Ratio and proportion | 5 | — | — | — | 0 / 0 | — | — |
| 64 | `g3-sec2-n2-b003` | Sec 2 N2 Ratio and proportion | 5 | — | — | — | 0 / 0 | — | — |
| 65 | `g3-sec2-n2-b001` | Sec 2 N2 Ratio and proportion | 5 | — | — | — | 0 / 0 | — | — |
| 66 | `g3-sec1-n7-b003` | Sec 1 N7 Equations and inequalities | 5 | — | — | — | 0 / 0 | — | — |
| 67 | `g3-sec1-n6-b001` | Sec 1 N6 Functions and graphs | 5 | — | — | — | 0 / 0 | — | — |
| 68 | `g3-sec1-n6-b003` | Sec 1 N6 Functions and graphs | 6 | — | — | — | 0 / 0 | — | — |
| 69 | `g3-sec1-n4-b002` | Sec 1 N4 Rate and Speed | 6 | — | — | — | 0 / 0 | — | — |
| 70 | `g3-sec1-n4-b004` | Sec 1 N4 Rate and Speed | 6 | — | — | — | 0 / 0 | — | — |
| 71 | `g3-sec1-n4-b001` | Sec 1 N4 Rate and Speed | 6 | — | — | — | 0 / 0 | — | — |
| 72 | `g3-sec1-n4-b003` | Sec 1 N4 Rate and Speed | 6 | — | — | — | 0 / 0 | — | — |

### Held for founder decision D4 (not on the fix list)

| Batch | Status | Findings waiting on D4 | Fixed by PR 261 | Existing claim |
| --- | --- | ---: | --- | --- |
| `g3-sec1-n2-b001` | approved | 18 | — | `review/g3-sec1-n2-b001-approval` |
| `g3-sec1-n2-b002` | approved | 14 | CFL-196 | none |
| `g3-sec1-n2-b003` | approved | 22 | — | `review/g3-sec1-n2-b003-approval` |
| `g3-sec1-n2-b004` | approved | 19 | CFL-196 | `review/g3-sec1-n2-b004-approval` |

### Not on the list

- Batches with no recorded finding (all diagnostic): `g3-sec1-g1-diagnostic-b001`, `g3-sec1-g5-diagnostic-b001`, `g3-sec1-n1-diagnostic-b001`, `g3-sec1-n2-diagnostic-b001`, `g3-sec1-n4-diagnostic-b001`, `g3-sec1-n5-diagnostic-b001`, `g3-sec1-n6-diagnostic-b001`, `g3-sec1-n7-diagnostic-b001`, `g3-sec1-s1-diagnostic-b001`, `g3-sec2-g2-diagnostic-b001`, `g3-sec2-g4-diagnostic-b001`, `g3-sec2-g5-diagnostic-b001`, `g3-sec2-n2-diagnostic-b001`, `g3-sec2-n5-diagnostic-b001`, `g3-sec2-n6-diagnostic-b001`, `g3-sec2-n7-diagnostic-b001`, `g3-sec2-s1-diagnostic-b001`, `g3-sec2-s2-diagnostic-b001`. Sec 1 N3 and Sec 2 S2 explicitly left their v2 diagnostic banks unaudited (CFL records with `fix_surface: tooling` note this), so this is not a clean bill of health; schedule a diagnostic audit.
- The 40 Sec 1 N1 pilot questions (keys such as `n1-l1-01`) have no batch manifest, so they cannot be claimed. 25 of them have findings: `n1-l1-01`, `n1-l1-04`, `n1-l1-07`, `n1-l1-08`, `n1-l1-11`, `n1-l1-12`, `n1-l1-14`, `n1-l1-15`, `n1-l2-02`, `n1-l2-03`, `n1-l2-04`, `n1-l2-05`, `n1-l2-06`, `n1-l2-07`, `n1-l2-08`, `n1-l2-11`, `n1-l2-12`, `n1-l2-14`, `n1-l2-15`, `n1-l3-01`, `n1-l3-02`, `n1-l3-03`, `n1-l3-08`, `n1-l3-09`, `n1-l3-10`. Decide whether to retire them or bring them under a manifest before fixing.

## Batches that need new diagrams

Diagram fixes need revisioned SVG filenames (GEOMETRY_DIAGRAM_AUTHORING_STANDARD.md rule 6). The renderers for these diagrams are not in the repository (CFL-086) and the validators do not check them (CFL-138), so either build a data-driven renderer first or hand-author each SVG. 'Needed' counts come from audit lists of text-only questions that clearly need a diagram; 'optional' counts are suggestions the reports mark as optional or 'would benefit'.

| # | Batch | Existing diagrams to redraw | New diagram needed | New diagram optional | Driving records |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | `g3-sec2-s1-b003` | — | 8 | — | CFL-389, CFL-390, CFL-393 |
| 2 | `g3-sec2-s1-b001` | — | 10 | — | CFL-389, CFL-390, CFL-393 |
| 3 | `g3-sec2-s1-b002` | — | 9 | — | CFL-389, CFL-390, CFL-393 |
| 4 | `g3-sec2-s1-b004` | — | 8 | — | CFL-389, CFL-390, CFL-393 |
| 5 | `g3-sec1-g1-b003` | 1 | 2 | — | CFL-050, CFL-053, CFL-106, CFL-494, CFL-604 |
| 6 | `g3-sec1-g1-b002` | 3 | 3 | — | CFL-051, CFL-053, CFL-108, CFL-110, CFL-208, CFL-494 … |
| 7 | `g3-sec2-g4-b004` | 26 | — | — | CFL-047, CFL-082, CFL-083, CFL-085, CFL-137, CFL-206 … |
| 9 | `g3-sec1-g1-b001` | 16 | 1 | — | CFL-048, CFL-049, CFL-050, CFL-051, CFL-053, CFL-099 … |
| 10 | `g3-sec2-g4-b002` | 26 | — | — | CFL-047, CFL-082, CFL-083, CFL-137, CFL-206, CFL-207 … |
| 11 | `g3-sec1-n3-b003` | — | — | 1 | CFL-466 |
| 15 | `g3-sec2-g4-b003` | 26 | — | — | CFL-047, CFL-082, CFL-083, CFL-137, CFL-206, CFL-207 … |
| 16 | `g3-sec1-g1-b004` | 1 | 2 | — | CFL-052, CFL-053, CFL-494, CFL-604, CFL-702 |
| 17 | `g3-sec1-g5-b002` | 1 | 5 | — | CFL-060, CFL-504, CFL-605, CFL-717 |
| 18 | `g3-sec1-n5-b002` | — | — | 2 | CFL-479 |
| 19 | `g3-sec2-g5-b004` | 26 | — | — | CFL-087, CFL-088, CFL-089, CFL-090, CFL-139, CFL-141 … |
| 20 | `g3-sec2-g5-b002` | 26 | — | — | CFL-087, CFL-088, CFL-089, CFL-090, CFL-139, CFL-141 … |
| 21 | `g3-sec2-g4-b001` | 26 | — | — | CFL-047, CFL-082, CFL-083, CFL-084, CFL-137, CFL-206 … |
| 22 | `g3-sec1-n1-b002` | — | — | 1 | CFL-465 |
| 25 | `g3-sec2-g2-b004` | 2 | 1 | — | CFL-069, CFL-075, CFL-126, CFL-127, CFL-134, CFL-136 … |
| 26 | `g3-sec2-g2-b003` | 1 | 5 | — | CFL-069, CFL-076, CFL-077, CFL-454, CFL-609, CFL-629 … |
| 27 | `g3-sec1-n1-b001` | — | — | 2 | CFL-465 |
| 28 | `g3-sec2-s2-b004` | — | — | 1 | CFL-546 |
| 29 | `g3-sec2-n6-b001` | — | 2 | — | CFL-436 |
| 30 | `g3-sec2-n6-b003` | — | 1 | — | CFL-436 |
| 31 | `g3-sec2-n6-b002` | — | 3 | — | CFL-436 |
| 32 | `g3-sec2-n6-b004` | — | 2 | — | CFL-436 |
| 33 | `g3-sec1-n5-b004` | — | — | 4 | CFL-479 |
| 34 | `g3-sec1-g5-b001` | 11 | 2 | — | CFL-041, CFL-054, CFL-055, CFL-056, CFL-057, CFL-058 … |
| 35 | `g3-sec2-g2-b002` | 1 | 2 | — | CFL-069, CFL-078, CFL-079, CFL-454, CFL-609, CFL-770 |
| 36 | `g3-sec1-n5-b003` | — | — | 1 | CFL-479 |
| 37 | `g3-sec2-g5-b001` | 26 | — | — | CFL-087, CFL-088, CFL-089, CFL-090, CFL-139, CFL-141 … |
| 38 | `g3-sec2-g5-b003` | 26 | — | — | CFL-087, CFL-088, CFL-089, CFL-090, CFL-139, CFL-141 … |
| 39 | `g3-sec2-g2-b001` | 11 | 2 | — | CFL-069, CFL-070, CFL-071, CFL-072, CFL-073, CFL-074 … |
| 40 | `g3-sec1-g5-b004` | 2 | 4 | — | CFL-061, CFL-153, CFL-504, CFL-605, CFL-717 |
| 41 | `g3-sec1-g5-b003` | 1 | 4 | — | CFL-152, CFL-504, CFL-605, CFL-717 |
| 42 | `g3-sec2-s2-b002` | — | 1 | 1 | CFL-362, CFL-546 |
| 43 | `g3-sec2-s2-b003` | — | 1 | — | CFL-362, CFL-546 |
| 45 | `g3-sec1-s1-b003` | — | 6 | — | CFL-422, CFL-426 |
| 46 | `g3-sec1-n1-b003` | — | — | 1 | CFL-465 |
| 47 | `g3-sec1-n3-b004` | — | — | 1 | CFL-466 |
| 48 | `g3-sec1-n3-b001` | — | — | 1 | CFL-466 |
| 49 | `g3-sec1-n3-b002` | — | — | 1 | CFL-466 |
| 50 | `g3-sec1-s1-b001` | — | 11 | — | CFL-422, CFL-426 |
| 51 | `g3-sec1-s1-b002` | — | 5 | — | CFL-422, CFL-426 |
| 52 | `g3-sec1-s1-b004` | — | 10 | — | CFL-422, CFL-426 |
| 53 | `g3-sec1-n7-b004` | — | — | 1 | CFL-489 |
| 54 | `g3-sec1-n6-b004` | — | — | 2 | CFL-481 |
| 55 | `g3-sec1-n6-b002` | — | — | 1 | CFL-481 |
| 57 | `g3-sec2-n7-b004` | — | 6 | — | CFL-437, CFL-444, CFL-519 |
| 58 | `g3-sec2-n7-b003` | — | 6 | — | CFL-437, CFL-444, CFL-519 |
| 59 | `g3-sec2-n7-b001` | — | 5 | — | CFL-437, CFL-444, CFL-519 |
| 60 | `g3-sec2-n7-b002` | — | 6 | — | CFL-437, CFL-444, CFL-519 |
| 63 | `g3-sec2-n2-b004` | — | — | 2 | CFL-510 |
| 64 | `g3-sec2-n2-b003` | — | — | 2 | CFL-510 |
| 66 | `g3-sec1-n7-b003` | — | — | 1 | CFL-489 |
| 68 | `g3-sec1-n6-b003` | — | — | 1 | CFL-481 |
| 69 | `g3-sec1-n4-b002` | — | — | 1 | CFL-474 |
| 70 | `g3-sec1-n4-b004` | — | — | 2 | CFL-474 |
| 72 | `g3-sec1-n4-b003` | — | — | 1 | CFL-474 |

Total: 259 question diagrams to redraw, 133 text-only questions where an audit says a diagram is needed, and 31 where one is optional. The redraw count includes diagrams whose only defect is legibility or an answer-revealing label. Batches with whole-bank template defects (Sec 2 G4 and G5: every question diagram) are the largest jobs. Sec 1 N6 also needs new graph-reading items for outcomes 6.2, 6.4 and 6.5 (no item is assessed from a graph); that is a bank-level authoring gap rather than a per-question redraw.

Lesson diagrams to redraw:

- `g3-sec1-math`: `g1-lesson-01`, `g1-lesson-02`, `g1-lesson-03`, `g1-lesson-04`, `g1-lesson-05`, `g1-lesson-06`, `g1-lesson-07`, `g5-lesson-01`, `g5-lesson-02`, `g5-lesson-03`, `g5-lesson-04`, `g5-lesson-05`, `n6-lesson-01`, `n6-lesson-02`, `n6-lesson-03`, `n6-lesson-04`, `n6-lesson-05`, `n7-lesson-01`, `s1-lesson-01`, `s1-lesson-02`, `s1-lesson-03`, `s1-lesson-04`
- `g3-sec2-math`: `g2-lesson-01`, `g2-lesson-02`, `g2-lesson-03`, `g2-lesson-04`, `g2-lesson-05`, `g4-lesson-01`, `g4-lesson-02`, `g4-lesson-03`, `g5-lesson-06`, `n2-lesson-04`, `n2-lesson-05`, `n6-lesson-06`, `n6-lesson-07`, `n7-lesson-06`, `n7-lesson-07`, `n7-lesson-08`, `s1-lesson-05`, `s1-lesson-06`, `s1-lesson-07`, `s1-lesson-08`, `s1-lesson-09`, `s1-lesson-10`, `s2-lesson-01`, `s2-lesson-02`

## Lesson fixes by course

Lessons are not claimed through the batch registry; fix them in course PRs. Confirmed category 1–2 records are listed by ID. Other counts are records by category; `D` marks lessons with findings waiting on a founder decision.

### Sec 1 course (`g3-sec1-math`)

| Unit | Lesson | Confirmed cat 1–2 | Other findings | Redraw diagram | Decision |
| --- | --- | --- | --- | --- | --- |
| sec1-g1 | `g1-lesson-01` | — | outcome or teaching gap 2, polish 4 | yes | D2 |
| sec1-g1 | `g1-lesson-02` | — | outcome or teaching gap 1, polish 4 | yes | D2 |
| sec1-g1 | `g1-lesson-03` | CFL-031, CFL-034, CFL-104 | outcome or teaching gap 1, polish 5 | yes | D2 |
| sec1-g1 | `g1-lesson-04` | CFL-111 | outcome or teaching gap 1, polish 4 | yes | D2 |
| sec1-g1 | `g1-lesson-05` | CFL-106 | duplicate 2, outcome or teaching gap 3, polish 5 | yes | D2 |
| sec1-g1 | `g1-lesson-06` | CFL-051 | duplicate 2, outcome or teaching gap 1, polish 3 | yes | D2 |
| sec1-g1 | `g1-lesson-07` | — | duplicate 2, outcome or teaching gap 3, polish 5 | yes | D2, D3 |
| sec1-g5 | `g5-lesson-01` | CFL-062, CFL-114, CFL-155 | duplicate 1, outcome or teaching gap 2, polish 4 | yes |  |
| sec1-g5 | `g5-lesson-02` | CFL-114, CFL-155 | duplicate 1, outcome or teaching gap 2, polish 4 | yes |  |
| sec1-g5 | `g5-lesson-03` | CFL-063, CFL-114, CFL-155 | outcome or teaching gap 3, polish 2 | yes |  |
| sec1-g5 | `g5-lesson-04` | CFL-064, CFL-114, CFL-155 | outcome or teaching gap 3, polish 4 | yes |  |
| sec1-g5 | `g5-lesson-05` | CFL-114, CFL-154, CFL-155 | duplicate 1, outcome or teaching gap 2, polish 3 | yes |  |
| sec1-n1 | `n1-lesson-01` | — | checker dependent 2, outcome or teaching gap 3 |  | D3 |
| sec1-n1 | `n1-lesson-02` | — | outcome or teaching gap 3, plain text math 1, polish 2 |  | D3 |
| sec1-n1 | `n1-lesson-03` | — | polish 1 |  |  |
| sec1-n1 | `n1-lesson-04` | — | outcome or teaching gap 1 |  | D3 |
| sec1-n1 | `n1-lesson-05` | — | outcome or teaching gap 3 |  | D3 |
| sec1-n1 | `n1-lesson-06` | — | outcome or teaching gap 3 |  | D3 |
| sec1-n1 | `n1-lesson-07` | — | checker dependent 2, duplicate 2, outcome or teaching gap 2, polish 1 |  | D3 |
| sec1-n2 | `n2-lesson-01` | — | duplicate 2, outcome or teaching gap 3, polish 3 |  | D4, D7 |
| sec1-n2 | `n2-lesson-02` | — | outcome or teaching gap 2, polish 3 |  | D4, D7 |
| sec1-n2 | `n2-lesson-03` | — | checker dependent 1, duplicate 1, outcome or teaching gap 3, polish 1 |  | D4, D7 |
| sec1-n3 | `n3-lesson-01` | — | checker dependent 1, duplicate 2, outcome or teaching gap 1 |  | D7 |
| sec1-n3 | `n3-lesson-02` | — | checker dependent 1, duplicate 1, outcome or teaching gap 2, polish 1 |  | D1, D7 |
| sec1-n3 | `n3-lesson-03` | — | checker dependent 1, duplicate 2, outcome or teaching gap 1, polish 1 |  | D7 |
| sec1-n3 | `n3-lesson-04` | — | duplicate 1, outcome or teaching gap 2, polish 1 |  | D1, D7 |
| sec1-n3 | `n3-lesson-05` | — | duplicate 1, outcome or teaching gap 1, polish 2 |  | D1, D2, D7 |
| sec1-n3 | `n3-lesson-06` | — | checker dependent 1, outcome or teaching gap 2, polish 2 |  | D1, D7 |
| sec1-n4 | `n4-lesson-01` | — | checker dependent 2, duplicate 1, outcome or teaching gap 4 |  | D7 |
| sec1-n4 | `n4-lesson-02` | — | checker dependent 1, duplicate 2, outcome or teaching gap 2 |  | D7 |
| sec1-n4 | `n4-lesson-03` | — | checker dependent 1, outcome or teaching gap 3 |  | D7 |
| sec1-n5 | `n5-lesson-01` | — | checker dependent 2, duplicate 1, polish 1 |  | D2 |
| sec1-n5 | `n5-lesson-02` | — | checker dependent 1, duplicate 1 |  |  |
| sec1-n5 | `n5-lesson-03` | — | duplicate 1, outcome or teaching gap 1, polish 1 |  | D2 |
| sec1-n5 | `n5-lesson-04` | — | checker dependent 2, duplicate 1, polish 1 |  | D1 |
| sec1-n5 | `n5-lesson-05` | — | checker dependent 1, duplicate 1, outcome or teaching gap 2 |  |  |
| sec1-n5 | `n5-lesson-06` | — | checker dependent 1, duplicate 1 |  |  |
| sec1-n5 | `n5-lesson-07` | — | checker dependent 2, duplicate 1 |  |  |
| sec1-n5 | `n5-lesson-08` | — | checker dependent 1, duplicate 1, outcome or teaching gap 1, polish 1 |  | D2, D3 |
| sec1-n6 | `n6-lesson-01` | — | duplicate 1, polish 4 | yes |  |
| sec1-n6 | `n6-lesson-02` | — | duplicate 2, polish 2 | yes |  |
| sec1-n6 | `n6-lesson-03` | — | duplicate 2, outcome or teaching gap 2, polish 4 | yes |  |
| sec1-n6 | `n6-lesson-04` | CFL-147 | duplicate 2, outcome or teaching gap 1, polish 2 | yes |  |
| sec1-n6 | `n6-lesson-05` | — | duplicate 2, polish 4 | yes | D1 |
| sec1-n7 | `n7-lesson-01` | — | answer leak 1, outcome or teaching gap 2, polish 6 | yes |  |
| sec1-n7 | `n7-lesson-02` | — | duplicate 1 |  |  |
| sec1-n7 | `n7-lesson-03` | — | duplicate 1 |  |  |
| sec1-n7 | `n7-lesson-04` | — | duplicate 1, outcome or teaching gap 1, polish 1 |  | D1 |
| sec1-s1 | `s1-lesson-01` | — | outcome or teaching gap 2, polish 3 | yes |  |
| sec1-s1 | `s1-lesson-02` | CFL-116 | outcome or teaching gap 1, polish 3 | yes |  |
| sec1-s1 | `s1-lesson-03` | CFL-115 | outcome or teaching gap 2, polish 3 | yes |  |
| sec1-s1 | `s1-lesson-04` | — | duplicate 2, polish 1 | yes |  |

### Sec 2 course (`g3-sec2-math`)

| Unit | Lesson | Confirmed cat 1–2 | Other findings | Redraw diagram | Decision |
| --- | --- | --- | --- | --- | --- |
| sec2-g2 | `g2-lesson-01` | CFL-070, CFL-123, CFL-124, CFL-125, CFL-157 | duplicate 1, outcome or teaching gap 3, plain text math 1, polish 4 | yes | D3 |
| sec2-g2 | `g2-lesson-02` | CFL-078, CFL-080 | duplicate 1, outcome or teaching gap 2, polish 4 | yes | D3 |
| sec2-g2 | `g2-lesson-03` | CFL-076 | outcome or teaching gap 2, polish 6 | yes | D3 |
| sec2-g2 | `g2-lesson-04` | CFL-126, CFL-127, CFL-129 | duplicate 1, outcome or teaching gap 3, polish 4 | yes | D3 |
| sec2-g2 | `g2-lesson-05` | CFL-134, CFL-158 | duplicate 1, outcome or teaching gap 2, polish 4 | yes | D3 |
| sec2-g4 | `g4-lesson-01` | — | polish 1 | yes |  |
| sec2-g4 | `g4-lesson-02` | — | outcome or teaching gap 4, polish 1 | yes | D6 |
| sec2-g4 | `g4-lesson-03` | CFL-022 | duplicate 2, outcome or teaching gap 2, polish 2 | yes |  |
| sec2-g5 | `g5-lesson-06` | CFL-087, CFL-088, CFL-139, CFL-140, CFL-144, CFL-159, CFL-160 | duplicate 1, outcome or teaching gap 3, polish 3 | yes | D3 |
| sec2-n2 | `n2-lesson-04` | CFL-065, CFL-066 | checker dependent 1, outcome or teaching gap 2, polish 4 | yes |  |
| sec2-n2 | `n2-lesson-05` | CFL-067 | checker dependent 1, duplicate 1, outcome or teaching gap 1, polish 2 | yes |  |
| sec2-n5 | `n5-lesson-09` | — | checker dependent 1, outcome or teaching gap 3 |  | D7 |
| sec2-n5 | `n5-lesson-10` | — | checker dependent 1, outcome or teaching gap 3 |  | D7 |
| sec2-n5 | `n5-lesson-11` | — | checker dependent 2, outcome or teaching gap 2, polish 2 |  | D2, D7 |
| sec2-n5 | `n5-lesson-12` | — | checker dependent 1, outcome or teaching gap 3 |  | D7 |
| sec2-n5 | `n5-lesson-13` | — | checker dependent 1, outcome or teaching gap 3, polish 1 |  | D7 |
| sec2-n5 | `n5-lesson-14` | — | checker dependent 1, outcome or teaching gap 3 |  | D7 |
| sec2-n5 | `n5-lesson-15` | CFL-035, CFL-042 | checker dependent 1, outcome or teaching gap 1 |  | D7 |
| sec2-n5 | `n5-lesson-16` | — | checker dependent 1, outcome or teaching gap 2 |  | D7 |
| sec2-n6 | `n6-lesson-06` | CFL-117, CFL-118, CFL-156 | outcome or teaching gap 3, polish 1 | yes | D2, D7 |
| sec2-n6 | `n6-lesson-07` | CFL-118 | outcome or teaching gap 4, polish 5 | yes | D2, D7 |
| sec2-n7 | `n7-lesson-05` | — | duplicate 1, outcome or teaching gap 4, polish 1 |  | D7 |
| sec2-n7 | `n7-lesson-06` | — | duplicate 1, outcome or teaching gap 5, polish 4 | yes | D7 |
| sec2-n7 | `n7-lesson-07` | CFL-120, CFL-121 | outcome or teaching gap 3, polish 4 | yes | D7 |
| sec2-n7 | `n7-lesson-08` | CFL-068, CFL-119 | duplicate 1, outcome or teaching gap 5, polish 3 | yes | D7 |
| sec2-n7 | `n7-lesson-09` | — | duplicate 1, outcome or teaching gap 5 |  | D7 |
| sec2-n7 | `n7-lesson-10` | — | duplicate 1, outcome or teaching gap 4, polish 1 |  | D1, D7 |
| sec2-s1 | `s1-lesson-05` | CFL-091, CFL-092, CFL-093 | outcome or teaching gap 4, polish 6 | yes | D2, D7 |
| sec2-s1 | `s1-lesson-06` | CFL-027, CFL-094 | duplicate 1, outcome or teaching gap 4, polish 7 | yes | D2, D7 |
| sec2-s1 | `s1-lesson-07` | CFL-027, CFL-095, CFL-096 | duplicate 1, outcome or teaching gap 3, polish 3 | yes | D7 |
| sec2-s1 | `s1-lesson-08` | CFL-097 | outcome or teaching gap 3, polish 3 | yes | D7 |
| sec2-s1 | `s1-lesson-09` | CFL-027, CFL-098 | duplicate 1, outcome or teaching gap 4, polish 2 | yes | D7 |
| sec2-s1 | `s1-lesson-10` | — | duplicate 1, outcome or teaching gap 3, polish 3 | yes | D7 |
| sec2-s2 | `s2-lesson-01` | CFL-145, CFL-162, CFL-163 | duplicate 1, outcome or teaching gap 1, polish 7 | yes | D2 |
| sec2-s2 | `s2-lesson-02` | CFL-146 | duplicate 3, outcome or teaching gap 5, polish 5 | yes | D2, D3 |

Confirmed lesson defects that change the mathematics or mislead:

- CFL-022 `g4-lesson-03`: Lesson calls elevation/depression angles "corresponding" instead of alternate
- CFL-027 `s1-lesson-06`, `s1-lesson-07`, `s1-lesson-09`: Defective items sit in live pools
- CFL-034 `g1-lesson-03`: Lesson 03 example and recall omit the parallel condition
- CFL-035 `n5-lesson-15`: Wrong value in lesson 15 example 2 check note
- CFL-042 `n5-lesson-15`: Wrong cancelled factor in lesson 15 example 1 check note
- CFL-062 `g5-lesson-01`: Lesson 01 area diagram: alt text claims marked heights; "h" on the slants
- CFL-063 `g5-lesson-03`: Lesson 03: alt text says triangular prism; drawing is a pentagonal prism
- CFL-064 `g5-lesson-04`: Lesson 04: alt text claims a metre square of centimetre squares; drawing is an unlabelled 4 x 4 grid
- CFL-065 `n2-lesson-04`: Map lengths drawn at inconsistent scales (1 cm longer than 2 cm)
- CFL-066 `n2-lesson-04`: Side lengths written in the centre of each square
- CFL-067 `n2-lesson-05`: "y = k/x" curve is a Bezier, not a hyperbola; dots do not keep xy constant
- CFL-068 `n7-lesson-08`: Lesson 08: solution marker is not at the crossing
- CFL-080 `g2-lesson-02`: Lesson 02 alt text says rectangles; drawing shows triangles
- CFL-091 `s1-lesson-05`: Lesson 05 captions overlap ("frequency." prints over "A key")
- CFL-092 `s1-lesson-05`: Lesson 05 figure lacks scale, class boundaries and key it tells learners to read
- CFL-093 `s1-lesson-05`: Lesson 05 panels show three different datasets under "Three views of a distribution"
- CFL-094 `s1-lesson-06`: Lesson 06 guide maps "exact lookup" to frequency table
- CFL-095 `s1-lesson-07`: Lesson 07 key message clipped at the viewBox edge
- CFL-096 `s1-lesson-07`: Lesson 07 charts have no vertical axis or ticks
- CFL-097 `s1-lesson-08`: Lesson 08 number line not uniform; mean marker misplaced
- CFL-098 `s1-lesson-09`: Lesson 09 median marker between the 2nd and 3rd dots
- CFL-104 `g1-lesson-03`: Lesson 03 alt text says angle positions are 'highlighted'; nothing is
- CFL-111 `g1-lesson-04`: Lesson 04 alt text promises a parallelogram and markings that are not drawn
- CFL-115 `s1-lesson-03`: Decision-guide connectors miss "Ordered change" and mis-target two boxes
- CFL-116 `s1-lesson-02`: Line graph axis starts at 26 with no break mark
- CFL-117 `n6-lesson-06`: Lesson 06 graph: curve runs through the coordinate labels
- CFL-118 `n6-lesson-06`, `n6-lesson-07`: Both N6 lesson graphs unreadable at phone width
- CFL-119 `n7-lesson-08`: Lesson 08: no axes labels, ticks, scale or equations
- CFL-120 `n7-lesson-07`: Lesson 07: unequal axis scales make gradient −2 look like −0.5
- CFL-121 `n7-lesson-07`: Lesson 07: line drawn only between the intercepts, contrary to the text
- CFL-125 `g2-lesson-01`: Lesson 01: alt text and lesson text promise angle arcs that are not drawn
- CFL-129 `g2-lesson-04`: Lesson 04: alt text promises construction rays; centre on an object vertex; no coordinates
- CFL-140 `g5-lesson-06`: Lesson pyramid: clipped note and label struck through by edges
- CFL-145 `s2-lesson-01`: Arc has no arrowhead and is symmetric
- CFL-146 `s2-lesson-02`: Highlight rectangle hides the red column's H/T divider
- CFL-147 `n6-lesson-04`: Unequal unmarked axis scales make gradient -2 look shallow
- CFL-154 `g5-lesson-05`: Lesson 05: alt text claims a shaded contact face; drawing has 2D rectangles, no shading
- CFL-155 `g5-lesson-01`, `g5-lesson-02`, `g5-lesson-03`, `g5-lesson-04`: "Read the diagram" sections describe what the diagrams do not show
- CFL-156 `n6-lesson-06`: Lesson 06 curve is hand-placed Béziers, not y = x² - 4
- CFL-157 `g2-lesson-01`: Lesson 01 diagram lacks the "not drawn to scale" note
- CFL-158 `g2-lesson-05`: Lesson 05 alt text says scale factors are shown; only the words appear
- CFL-159 `g5-lesson-06`: Lesson pyramid note refers to a slant height that is not drawn
- CFL-162 `s2-lesson-01`: 'unlikely' and 'likely' drawn as exact values at 1/4 and 3/4
- CFL-163 `s2-lesson-01`: Lesson says likely/unlikely are regions; diagram pins them to ticks

## Checker-dependent findings

PR 261 (`fix/answer-checker`, open) implements `symbolic_equivalence`, reads mixed numbers and percentages correctly, accepts digit separators and units, and adds `checker_config.form`. Its `ANSWER_CHECKER_FORM_SETTINGS.md` lists 135 parts that need a form, 69 percentage parts that should declare `unit: %`, and 11 incomplete factorisation keys (CFL records for Sec 2 N5 C-2 and Sec 1 `n5-l3-008`, both category 1).

- **Resolved by PR 261 alone:** CFL-187 (Sec 1 N3 C-01a); CFL-188 (Sec 1 N6 C1); CFL-189 (Sec 2 N2 C-01); CFL-190 (Sec 1 N1 C-01); CFL-191 (Sec 1 N5 2); CFL-192 (Sec 1 N5 3); CFL-193 (Sec 1 N5 4); CFL-194 (Sec 2 N2 L-01); CFL-195 (Sec 1 N1 C-13); CFL-196 (Sec 1 N2 1.1/2); CFL-197 (Sec 1 N4 3); CFL-198 (Sec 1 N5 L2); CFL-199 (Sec 2 N5 C-3a); CFL-200 (Sec 1 N1 C-35a); CFL-201 (Sec 1 N4 L3); CFL-202 (Sec 1 N5 5); CFL-203 (Sec 2 N2 6/2b); CFL-204 (Sec 2 N5 lesson-findings/7); CFL-205 (Sec 2 G2 1.1/1).
- **Need a content-side `checker_config` or unit:** CFL-167 (Sec 1 N5 1); CFL-168 (Sec 2 N5 C-1); CFL-169 (Sec 1 N3 C-01b); CFL-170 (Sec 1 S1 C-04); CFL-171 (Sec 2 G4 C10b); CFL-172 (Sec 2 S2 C-01); CFL-173 (Sec 1 S1 C-16); CFL-174 (Sec 2 N5 C-3b); CFL-175 (Sec 2 G5 C12b); CFL-176 (Sec 2 S1 C-05).
- **Not covered by PR 261:** CFL-177 (Sec 1 N1 C-10: 'Simplest form' / 'exact value' is never enforced); CFL-178 (Sec 1 N1 C-11: 'Insert < or >' items reject the natural reply '<'); CFL-179 (Sec 1 N7 C6/1: Fraction answer 76/7 with no form instruction); CFL-180 (Sec 2 S2 C-02: 'Simplest form' and 'as a decimal' demands are not enforced by exact_numeric); CFL-181 (Sec 1 N1 C-35b: Index notation required but repeated factors accepted); CFL-182 (Sec 1 N1 L-07: Lesson 07 s.f. recall does not check significant figures); CFL-183 (Sec 1 N6 C9b: Quadrant answers: Roman numeral input rejected); CFL-184 (Sec 2 N2 6/3: Decimal-comma input gets a generic error message); CFL-185 (Sec 2 G4 C11a: rounded_dp rejects integer forms of exact answers); CFL-186 (Sec 1 N2 C-22: Lesson 3 says "answer with its unit" but numeric inputs reject units).
- Found while verifying, not in PR 261's list: Sec 2 S2 `s2-l1-507`, `s2-l1-513`, `s2-l2-504` and five Sec 2 G5 percentage parts store `canonical_latex` without `\%`, so '20%' stays wrong until the content declares `unit: %`.

## Tooling and process records (no batch claim)

- CFL-039 (Sec 2 G4 R3, wrong_or_unanswerable): No validator recomputes answers or checks answer form. Also in: Sec 2 G5 R5, Sec 2 N5 R-4.
- CFL-086 (Sec 2 G4 R1, misleading_diagram): Diagram renderers are missing from the repository and draw fixed templates. Also in: Sec 2 G5 R1, Sec 1 G5 RC1, Sec 2 G2 R1, Sec 1 G1 root-cause/6, Sec 2 G2 spread/1, Sec 1 S1 RC-1, Sec 2 S1 RC-2-3, Sec 2 S2 root-cause-1, Sec 2 N2 RC-5, Sec 1 N6 RC2, Sec 2 N6 R-4, Sec 2 N7 root-cause/1.
- CFL-113 (Sec 1 G5 RC3, misleading_diagram): Alt text generated by regex from the prompt.
- CFL-114 (Sec 1 G5 RC6, misleading_diagram): Lesson SVGs are stale and the script will not regenerate them.
- CFL-138 (Sec 2 G4 R2, misleading_diagram): Diagram validators are opt-in and cannot detect the reported defects. Also in: Sec 2 G5 R2, Sec 1 G1 root-cause/5, Sec 1 G5 RC5, Sec 2 G2 R3, Sec 1 N7 RC5, Sec 1 N1 part2-root-cause/1.
- CFL-144 (Sec 2 G5 R3a, misleading_diagram): Recalibration script does not cover Sec 2 G5.
- CFL-298 (Sec 1 N2 RC-2, duplicate): Duplicate detection is exact-match only and is defeated by titles and codenames. Also in: Sec 1 N7 RC4, Sec 2 G5 R4, Sec 2 N5 R-3, Sec 2 N6 R-2, Sec 1 N1 root-cause/2.
- CFL-419 (Sec 1 G1 root-cause/4, outcome_or_teaching_gap): Diagram selection is mechanical, not need-based. Also in: Sec 1 G5 RC4, Sec 2 G2 R2.
- CFL-517 (Sec 2 N6 R-3, outcome_or_teaching_gap): No validator compares solution methods with the lesson.
- CFL-586 (Sec 1 N1 root-cause/1, plain_text_math): Plain-text batch maths passes the 'latex_fragments_render' check vacuously.
- CFL-656 (Sec 1 N3 7/1, polish): N3 diagnostic bank (v2) not audited.
- CFL-800 (Sec 2 S2 not-verified/1, polish): S2 diagnostic bank (v2) not audited.
- CFL-818 (Sec 1 N2 P-4, polish): Bank blueprints still name the course 'Singapore G3 Mathematics'. Also in: Sec 2 G2 1.2-conflicts/2, Sec 2 N5 C-14b.

## Decisions for the founder

None of these is decided here. Records whose fix depends on a decision have status `needs_founder_decision` and do not, on their own, put a batch on the fix list.

### D1. Currency notation

**Question.** Which money notation should every question and lesson use?

**Context.** house-rules-v2.json says 'Use S$ in learner-facing Singapore-dollar contexts' (currency SGD), and the Sec 1 N2 audit made S$ mandatory. LESSON_NOTES_CONTENT_STANDARD.md says the audience is students across Indonesia and Southeast Asia and asks for contexts that work across the region. The content currently mixes S$, 'SGD 72', a bare '$', the word 'dollars' and no unit at all, sometimes inside one bank (for example Sec 1 N3 uses S$ in 28 questions but a bare $ in its lessons; Sec 2 N7 uses S$ in Indonesian settings).

**Options.**

- A. S$ everywhere. Replace SGD, bare $ and unit-less sums with S$, and add a one-line gloss ('S$ means Singapore dollars') in the first lesson that uses money.
- B. Currency-neutral money: write amounts as '72 dollars' or use non-money quantities, so no country is implied.
- C. Regional currencies (Rp, RM, ₱, S$, ฿) chosen to match each context, with the currency named in words.

**Recommendation.** A. The target is a Singapore-run scholarship test, most money items already use S$, and it is the smallest change. Whatever you choose, apply one notation bank-wide and tell learners to type only the number (the PR 261 checker still rejects a currency symbol typed before the number).

**Affected:** 11 records, 27 batches.

### D2. Language variety, terminology and local contexts

**Question.** Which English variety, terms and contexts are the house standard?

**Context.** house-rules-v2.json sets locale en-SG and 'Singapore/British English'; the audience standard asks for clear international English with unfamiliar terms explained. Reports flag British spellings (colour, litres), Singapore-classroom terms used without a gloss (highest common factor vs GCF/FPB, trapezium, co-interior, dot diagram vs dot plot, ordinate, travelator, pupil-days), Singapore-only contexts (9% GST, Singapore stamps, house teams) and blueprints that still say 'Singapore G3 Mathematics'.

**Options.**

- A. Keep British spelling, relabel the house variety 'international English (British spelling)', keep Singapore syllabus terms but gloss each on first use, and replace or explain Singapore-only contexts.
- B. Keep en-SG exactly as the house rules say (no glosses needed beyond what exists).
- C. Switch to US spelling and international terms (GCF, trapezoid, dot plot) throughout.

**Recommendation.** A. British spelling is accepted as international English, the syllabus terms are what the target test uses, and a gloss costs one sentence per term. Update house rules to v3 and rename the blueprints so future batches follow the same rule.

**Affected:** 19 records, 30 batches.

### D3. Out-of-syllabus topics

**Question.** For each topic the audits flagged as outside the catalogue outcomes or untaught, should items be rewritten in scope, kept with new teaching, or moved out of assessed pools?

**Context.** The repository catalogue lists Secondary 1–2 outcomes only, so several of these calls rely on the auditors' knowledge of the Singapore syllabus rather than on repository files.

| Bank | Topic | Items | Records |
| --- | --- | --- | --- |
| Sec 1 N6 | Composite functions f(g(x)) | n6-l4-006, n6-l5-003 | CFL-548 |
| Sec 1 N1 | Divisor-count formula; completing a perfect square/cube; bounds of combined values; scaled linear inequalities; standard form; section formula | 26 items (20 in b001–b003, 6 in the unbatched pilot set), n1-lesson-01, 02, 04–07 | CFL-554, CFL-555, CFL-556, CFL-557, CFL-558, CFL-559 |
| Sec 1 N5 | Factorisation by grouping (in checkpoint/reserve, not taught) | 2 items, n5-lesson-08 | CFL-566 |
| Sec 1 G1 | Circumcentre | g1-l4-012, g1-lesson-07 | CFL-579 |
| Sec 1 G5 | Quadratic factorisation inside mensuration items | 2 items | CFL-549 |
| Sec 2 G2 | Area and surface-area scale factors (k², 3-D boxes); formal congruence/similarity tests (SSS, SAS, ASA, RHS, AA) | 16 items in b001–b004, g2-lesson-01 to 05 | CFL-569, CFL-580 |
| Sec 2 G5 | Volume ratio of similar solids (k³) | 8 liquid-depth items, g5-lesson-06 | CFL-570 |
| Sec 2 S2 | Combinations notation; multiplication rule, combined events and factorials | 8 items (s2-l4-515 uses combinations), s2-lesson-02 | CFL-552, CFL-553, CFL-571, CFL-572 |

**Options.**

- A. Rewrite to in-scope methods (for example, list outcomes instead of multiplying probabilities; remove composition; solve liquid depth from the cone formula).
- B. Keep the topic, add a taught section and worked example to the lesson, and record the scope extension in the blueprint.
- C. Keep the items but move them to an enrichment pool that is excluded from checkpoints and diagnostics.

**Recommendation.** A by default, especially for items in checkpoint or diagnostic pools. Choose B only for a topic you know the scholarship test assesses at Sec 3 entry. The strongest candidates for B are area/volume scale factors (Sec 2 G2/G5) and standard form (Sec 1 N1). Please rule topic by topic.

**Affected:** 17 records, 22 batches.

### D4. Reopen approved Sec 1 N2 content

**Question.** Should the approved Sec 1 N2 batches (b001–b004) and reviewed N2 lessons be reopened for the audit findings?

**Context.** The Sec 1 N2 audit recomputed all 104 answers and the lesson examples and found them correct; there is no category 1 or 2 finding. The open findings are medium/low: 2 hint leaks (n2-l4-014; n2-l3-009/016), duplicates (n2-l1-002/013, n2-l3-014/022, n2-l4-012/016, a lesson example equal to n2-l2-025), outcome and difficulty tags (n2-l5-001/003, linked-ratio teaching gap), 32 plain-text fraction prompts and 3 'SGD' items. The mixed-number mis-marking ('2 1/2' read as 21/2) is fixed by PR 261 with no content change. Reopening changes the review fingerprint, so Mathematics and editorial approval must be recorded again. The claim CLI refuses approved batches, so each batch must first return to changes_requested in a reviewed PR (b001, b003 and b004 still hold active review claims; b002 has none).

**Options.**

- A. Leave N2 approved and log the findings for the next scheduled revision.
- B. Targeted reopen after the higher-priority batches: fix the hint leaks, duplicates, outcome/difficulty tags and SGD items only, then re-review.
- C. Full reopen, including converting the 32 plain-text fraction prompts to inline maths.

**Recommendation.** B, scheduled after the 72 ranked batches in this ledger. The duplicates and hint leaks sit in checkpoint and reserve pools, so they affect measurement, but nothing is wrong enough to pull approved content now. Fold the plain-text maths into the same pass only if D1/D2 also require edits.

**Affected:** 42 records, 4 batches.

### D5. How much a stage-2 hint may reveal

**Question.** May a stage-2 hint state the complete final calculation?

**Context.** House rules v2 say neither hint may state the final answer. Many difficulty 1–2 hints state the full calculation with both operands (Sec 1 N4: 48 items; G5: 53; N6: 13; N7 7.4: 18; Sec 2 G2: one-step d1 items where any setup is the answer). Hints that state the answer outright are recorded separately as answer leaks and are not part of this decision.

**Options.**

- A. Strict: stage 2 gives the method or setup but never the complete final operation (rewrite about 130 hints plus most Sec 2 G2 difficulty 1 hints).
- B. Graded: d1–d2 may show the full operation; d3 and above may not give the simplified result or a value that ends the task.
- C. Leave as is.

**Recommendation.** B. It matches how one-step items work and focuses rewriting on the higher-difficulty items where leakage changes what is measured.

**Affected:** 5 records, 20 batches.

### D6. Response formats for choice and justification outcomes

**Question.** How should outcomes that ask for a choice or a justification be answered?

**Context.** Statistics representation and measure choices are answered with numeric codes ('1 for mean, 2 for median…'; Sec 1 S1 31 items, Sec 2 S1 39 items) and the Pythagoras converse with 0/1 (Sec 2 G4, 28 items). These cannot capture the justification the outcome asks for, and several coded items have two valid codes. The G4 converse diagrams also show a right-angle marker on triangles that are not right-angled, or give the answer away when they are.

**Options.**

- A. Add a proper multiple-choice response type with labelled options, and keep reasoning items as choose-then-compute (for example, ask for a² + b² and c² before the yes/no).
- B. Keep numeric codes and 0/1 but rewrite every prompt so exactly one code is defensible; make converse items text-only.
- C. Keep the current format.

**Recommendation.** B now (it is needed anyway to clear the category 1 ambiguous-key findings), with A as a product follow-up. Converse items should be text-only or use a diagram with no right-angle marker.

**Affected:** 5 records, 12 batches.

### D7. Lesson length baseline

**Question.** Does the 2,500-character lesson baseline mean learner-visible text?

**Context.** The validator measures len(json.dumps(sections)), so lessons pass on JSON overhead. Measured as visible text, 34 lessons across both courses are below 2,500 characters (for example, Sec 1 N2 lessons are about 1,700–1,900).

**Options.**

- A. Yes: change the metric to visible text and extend the short lessons.
- B. Keep the JSON metric but lower the visible-text expectation in the standard.
- C. Keep both as they are.

**Recommendation.** A, but extend lessons where a teaching gap is already recorded (missing worked examples) rather than padding for length.

**Affected:** 1 records.

### D8. Patch or regenerate the templated Sec 2 banks

**Question.** Should the template-generated Sec 2 banks be patched item by item or regenerated?

**Context.** Sec 2 N5, N6 and S1 put generator codenames in every prompt and title; N7 puts them in every title. G2, G4 and G5 draw diagrams from fixed templates whose renderers are not in the repository, and 15 of the 19 learning banks were generated wholly or mostly under prompt v1 (all but Sec 1 N1 and N3 and Sec 2 N7 and S1; Sec 1 N2 has one v2 batch), several with templated, non-functional contexts. Patching fixes the verified defects quickly; regenerating would also remove the template repetition but needs a full re-review.

**Options.**

- A. Patch: fix category 1–3 items, strip codename prefixes, and hand-author revisioned SVGs.
- B. Regenerate whole banks under prompt v2 and house rules v2 with a data-driven renderer, then re-review.
- C. Hybrid: patch categories 1–3 now; build the renderer and regenerate diagrams next; rewrite templated contexts and duplicates in a later pass.

**Recommendation.** C. It removes wrong or misleading content first without waiting for tooling.

**Affected:** 1 records.

### D9. Answer-form strictness

**Question.** How strict should numeric answer checking be about form?

**Context.** exact_numeric accepts any equal value, so 'simplest form', 'as a decimal' and 'index notation' demands are not enforced (Sec 1 N1, Sec 2 S2: 69 parts). rounded_dp rejects an integer typed for an exact answer (Sec 2 G4). PR 261 leaves open: percentage-point parts still read '6%' as 0.06, a decimal comma is a format error, and format errors count as wrong attempts. Thousands separators are written three ways.

**Options.**

- A. Enforce form only where the prompt demands it (add form settings for numeric parts), accept '6%' on percentage-point parts, and do not count format errors as attempts.
- B. Accept any equal value everywhere and remove form demands from prompts.
- C. Leave the checker as PR 261 makes it.

**Recommendation.** A. Keep the prompt and the marking consistent; reword prompts where enforcement is not worth building.

**Affected:** 5 records, 15 batches.

## Method and limits

- Each report was read in full and every finding recorded with its report ID. Findings bundling defects of different categories were split (suffixes a/b). Root-cause and summary sections were recorded only when they named an actionable issue not already recorded.
- Category 1 and 2 findings were verified against the current question, lesson and SVG files: answers recomputed with exact arithmetic or SymPy before reading solutions, checker behaviour run on both the current checker and PR 261's, SVG coordinates and arc centres computed, and text boxes measured in headless Chromium. A second pass re-checked a sample of the category 1 rows and the critical/high diagram rows directly.
- Category 3–8 findings are recorded as the reports state them (status `open`). Spot checks and report errors found along the way are in each record's `notes`.
- Repeats were merged when several reports raised the same root cause or policy conflict (renderers, validators, duplicate detection, answer recomputation, lesson length metric, language variety, blueprint naming); merged sources are in `also_reported_in`.
- Not done: rendering inside the learner app; full re-derivation of every duplicate and difficulty claim; hosted review state.
