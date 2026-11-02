# Secondary 1 N7 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_1/n7/v1/`
(batches B001–B004) and all four N7 lessons (`n7-lesson-01` to `n7-lesson-04`), plus every
diagram those files reference

**Decision boundary:** report-only technical pre-review. No question, lesson, SVG, manifest,
claim or review state was changed. No Mathematics or editorial approval is recorded here.

**Models:** `docs/plan/N2_CALIBRATION_PRE_REVIEW_AUDIT.md` (audit format);
`docs/plan/LESSON_NOTES_CONTENT_STANDARD.md` and `docs/plan/GEOMETRY_CONTENT_STANDARD.md`
(current standards); `backend_resources/question_bank/authoring/house-rules-v2.json` and
`question_bank/src/question_bank/difficulty.py` (hint and difficulty rules)

## Summary

| Item | Count |
| --- | ---: |
| Questions checked | 104 (26 per batch; all `draft`; all four batches `ready_for_review` with Mathematics and editorial review `pending`) |
| Lessons checked | 4 (all `draft`, revision 2) |
| Diagrams referenced | 1 (lesson asset `n7-lesson-01-equation-balance`); no question has assets |
| Diagrams rendered and viewed | 1 of 1 |
| Canonical answers recomputed by code | 104 of 104 — **0 mismatches** |
| Content findings | 52 entries (0 high, 24 medium, 28 low): 45 on questions, 7 on lessons. Some entries cover several items. |
| Diagram findings | 5 (0 accuracy errors, 2 medium neatness, 3 low) |

There is no incorrect canonical answer, accepted answer or worked-solution result. The issues
are hint leakage, inflated difficulty, overlap between items and between lessons and questions,
a few wording and answer-format problems, and one diagram where a line runs through a label.
Most of the question issues come from a single cause: N7 was written under house rules v1
before the N2 audit introduced v2 (see [Root-cause patterns](#root-cause-patterns)).

### Where the files are

- Questions: `backend_resources/question_bank/g3_math/secondary_1/n7/v1/questions/n7-l{1..5}-NNN.json`.
  The `lN` in each key is the difficulty level, **not** the lesson. Lessons map to outcomes
  7.1–7.4.
- Lessons: these are **not** in an `n7` course folder. All four are in
  `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n7-lesson-0{1..4}.json`.
  They were found through unit `g3-sec1-n7` in `.../n1/v1/course.json`, which maps
  lesson 01 to outcome 7.1, 02 to 7.2, 03 to 7.3 and 04 to 7.4.
- The only diagram: `backend_resources/courses/g3_math/secondary_1/n1/v1/assets/n7-lesson-01-equation-balance.svg`.
  This path comes from the asset `path` (`assets/n7-lesson-01-equation-balance.svg`) in
  `n7-lesson-01.json`, resolved against the course root. Its sha256 matches the manifest.

## Checks performed

- Recomputed every canonical answer from the prompt alone, before reading the solution. Each
  prompt was encoded as an independent SymPy equation (or as direct arithmetic for the
  "find k" items) and the result compared as a `Fraction` with `canonical_answer` and every
  `accepted_answers` entry. Script and output are in [Appendix A](#appendix-a-answer-verification).
- Read every worked solution and hint against the answer, the stated conditions and the
  house-rules-v2 hint boundary ("neither hint may state the final answer").
- Checked each item's difficulty against the five-level rubric in `difficulty.py`, and its
  outcome against the blueprint and lessons.
- Compared items across the N7 bank (operation pattern, numbers, context, answer) and against
  lesson worked examples and active recall. Also checked for exact display-math duplicates
  across every Mathematics bank in the catalogue (none found).
- Checked wording, spelling, units and currency, and compared the N2 audit's
  Singapore-specific rules with the current audience statement.
- Read `checking.py` to confirm how `exact_numeric` parses decimal and fraction input.
- Re-ran the validators. All pass for N7:
  `question-bank validate .../n7/v1` (0 errors, 0 warnings), `question-bank course-validate`
  (0 errors, 0 warnings, 52 lessons) and catalogue-wide `question-bank authoring-validate`
  (2,052 questions, 0 duplicates, 0 errors). Validator passes are **not** used here as
  evidence of correctness.
- Rendered the SVG to PNG with the pre-installed Playwright Chromium, at 940 px and at 358 px
  (the content width of a 390 px phone with 16 px gutters). Viewed both images, read text
  bounding boxes with `getBBox()`, and checked the line and text coordinates by hand. Renders
  were written to a scratch directory outside the repository and not committed.

Severity scale: **high** means a learner is marked or taught incorrectly. **Medium** means a
defect that weakens assessment or teaching validity (for example, a leaked answer or wrong
tier). **Low** means polish, consistency or metadata.

---

## Part 1 — Content findings

### C1. Stage-2 hints that state the final answer (house rules v2 breach)

House rules v2: "Keep stage-one hints conceptual and stage-two hints to an intermediate
setup; neither hint may state the final answer." The blueprint `hint_policy.stage_2` says the
same.

| Stable key | Sev. | Evidence (stage-2 hint → answer) | Proposed stage-2 hint |
| --- | --- | --- | --- |
| n7-l1-002 | medium | "Since 2(3) + 1 = 7, the two sides are equal." → 1 | "Compare your left-hand value with the right-hand side, 7." |
| n7-l1-004 | medium | "Seven groups of 5 make 35." → 35 | "Write x = 7 × 5." |
| n7-l1-008 | medium | "The right-hand side is the single number 19." → 19 | "Ignore 4y − 9; read only the term after =." |
| n7-l1-012 | medium | "Subtracting 8 reverses adding 8." → 8 | "Which operation is applied to x on the left-hand side?" |
| n7-l1-013 | medium | "42 divided by 6 is 7." → 7 | "Write p = 42 ÷ 6." |
| n7-l1-014 | medium | "Five groups of 8 make 40." → 40 | "Write q = 5 × 8." |
| n7-l2-001 | medium | "The same 9 must be subtracted from 17." → k = 9 | "Whatever you remove from the left must also be removed from 17." |
| n7-l2-002 | medium | "Divide both 3x and 21 by 3." → divisor 3 | "Which number multiplies x?" |
| n7-l2-024 | medium | "The term added on the right is 1x." → k = 1 | "Write 7 − x + x = 3 + x and compare it with 3 + kx." |
| n7-l2-025 | medium | "Subtract 4 from each side." → k = 4 | "Which constant must disappear from the left to leave 3x?" |
| n7-l4-013 | medium | "The coefficient of x must equal 3…" → a = 3 | "Expand a(x + 2) and compare the x-terms on both sides." |
| n7-l1-007 | low | "Read the number immediately before p." (near-leak) | "Rewrite 5p as a product of a number and p." |
| n7-l3-009 | low | "The constant term is 5 times 1." (near-leak) | "Multiply each term inside the bracket by 5." |
| n7-l4-005 | low | "The left side becomes 16, so 11 + k = 16." (leaves only subtraction) | "Evaluate 2(11 − 3) first." |
| n7-l5-001 | low | "Set k − 2 equal to 4." (a d5 item reduced to one step) | "In an identity, the x-coefficients on both sides must match." |

### C2. Answer visible in the prompt

| Stable key | Sev. | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n7-l1-001 | medium | Asks for the "common value" of the two sides of x + 7 = 11 when x = 4. The answer (11) is the printed right-hand side, so it can be copied without substituting. | Use a non-solution and ask for the computed side: "Substitute x = 4 into x + 7 = 12. What is the value of the left-hand side?" (answer 11), with a hint to compare it with 12. Lesson active recall `n7-71-recall` has the same defect (see L1). |

### C3. Difficulty does not match the rubric

Rubric (`difficulty.py`): **d3** is a multi-step application with a routine choice of method.
**d4** is an unfamiliar problem requiring method selection, constraints or justification.
**d5** is complex non-routine synthesis.

| Stable key(s) | Sev. | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n7-l3-001, n7-l3-002, n7-l3-009, n7-l3-024 | medium | Each is d3 with 3 marks but needs one arithmetic step that the prompt already names: 19 − 7, 7 × 3, 5 × 1, "double 13". By the rubric these are d1–d2. | Re-tier to d1/d2 (and fix the blueprint counts), or rewrite as genuine d3 items, for example "which of these equations are equivalent to 2x + 7 = 19?" across several transformations. |
| n7-l2-001, n7-l2-002, n7-l2-024, n7-l2-025 | low | One-glance identification of a constant or coefficient already in the prompt (d1 demand marked d2). | Re-tier to d1, or require two linked transformations. |
| n7-l4-002, n7-l4-004, n7-l4-006, n7-l4-008, n7-l4-010, n7-l4-014 | medium (judgement) | Routine expand-and-collect or one-context linear models. The method is given in the prompt ("Expand both bracketed expressions…", "Remove both brackets…") and no method choice or constraint is needed. This matches d3. | Reviewer decision. Either re-tier to d3 or add a d4 demand (an unknown to choose, an integer or validity constraint, or a justification part). |
| n7-l5-001 vs n7-l4-013 | medium | d5 `(k−2)x+6=4x+6` reduces to k − 2 = 4. It is easier than the d4 identity item `a(x+2)=3x+6`, which needs expansion and two matches. | Swap the tiers, or make l5-001 need synthesis (for example, a parameter that makes the equation have **no** solution, with justification). |
| n7-l5-003, n7-l5-005 | low (judgement) | Routine single-equation models (18x = 24(x−4); ⅔(x−48)+20 = 100). These are d4 at most, not "complex non-routine synthesis". | Reviewer decision on re-tiering. Alternatively, add a second condition or ask for an interpretation or validity check. |

### C4. Outcome alignment

| Stable key(s) | Sev. | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n7-l1-014 | medium | `q/8 = 5` is allocated to 7.2 but is a fractional equation (the 7.3 skill). It also repeats n7-l1-004 (`x/5 = 7`, 7.3) and n7-l2-017 (`x/5 = 6`, 7.1). | Replace with a non-fractional 7.2 one-step item, for example `9 − q = 4`. |
| n7-l3-027 vs n7-l1-020, n7-l2-013 | low (judgement) | `3x/4 + 5 = 17` is classed as 7.2, while `2x/7 = 6` and `¾x = 18` are classed as 7.3. The split between 7.2 and 7.3 for fractional coefficients is inconsistent. | Reviewers should fix one convention. The simplest is that any denominator means 7.3. |
| n7-l4-013, n7-l5-001 | low (judgement) | Both need coefficient matching for identities. `n7-lesson-01` section `n7-71-truth-checks` mentions that an identity is "true for every value" but never teaches matching coefficients. | Either add a short identity-matching example to lesson 01 or move these items to a later level. |
| n7-l1-007, n7-l1-008 | low (judgement) | Vocabulary reading (coefficient; right-hand constant). These test algebraic-expression terms rather than the concept of an equation. | Reviewer decision. One option is to replace them with "is this an equation or an expression?" or substitution-check items. |
| 7.4 bank (16 items, e.g. n7-l1-006, -011, -016, -017, -021, n7-l2-007, -008, -015, -022, -023, -030, -031, n7-l3-008, -016, -023, n7-l4-004) | medium (judgement) | Outcome 7.4 is *formulating* the equation. In these items the variable is defined in the prompt, stage 2 hands over the full equation ("Solve 4 + 2x = 18"), and only the numeric x is scored. A hinted attempt therefore assesses 7.2, not 7.4. | Reviewer decision. Options: limit stage 2 to one relationship (for example, "Write the fare for x km"), or add an `algebraic_expression` part for the equation on higher-tier items. |

### C5. Semantic duplicates and overused templates

| Stable key(s) | Sev. | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n7-l2-009 / n7-l3-001 | medium | `2x+5=17`, subtract 5, giving 2x = 12, versus `2x+7=19`, subtract 7, giving 2x = 12. Same operation, same answer (12), different tier (d2 vs d3). | Replace n7-l3-001 (see C3). |
| n7-l3-016 / n7-l3-031 (and n7-l1-021) | medium | `x + (x + d) = S` at the same tier and outcome (d3, 7.4): S$18 more / S$126 versus 1.5 m longer / 8.7 m. | Replace n7-l3-031 with a different structure, for example three related quantities, or a ratio-based relationship. |
| n7-l1-004 / n7-l1-014 / n7-l2-017 | low | `x/5=7`, `q/8=5` and `x/5=6`: the same single-step multiply-out across three outcomes. | See C4 (n7-l1-014). Keep at most two. |
| n7-l4-012 / n7-l5-005 | low | Both are "remove a fixed amount, then one third of the remainder, then compare" (tank 78 L; class fund S$168). | Change the structure of one, for example a fraction taken first and then a fixed amount. |
| n7-l3-010 / n7-l4-001 | low | Both are "solve the first equation, then substitute into the second to find k", at d3 and d4. | Differentiate n7-l4-001, for example by requiring a coefficient condition. |
| 7.1 "find k" template (14 of 26 7.1 items: l1-012, l1-018, l2-001, l2-002, l2-009, l2-016, l2-017, l2-024, l2-025, l3-001, l3-002, l3-009, l3-024, l3-025) | medium | More than half of 7.1 uses one template: apply a named balance step, then report the resulting constant. It drives the leakage in C1 and the inflation in C3. | Rebalance 7.1 towards solution testing, equation versus expression, choosing an equivalent equation, and having no or infinitely many solutions. |
| Parameter-from-solution cluster (n7-l3-017, n7-l3-018, n7-l4-005, n7-l4-009) | low | Four of 26 7.1 items substitute a given x and solve for a constant. | Keep two and vary the rest. |
| Answer distribution | low | Canonical answer 7 appears 12 times and 8 appears 10 times in 104 items. The 7.4 d2 items n7-l2-014, n7-l2-015 and n7-l2-023 all have answer 7. | Vary the numbers when replacing items. |

### C6. Wording, answer format and worked solutions

| Stable key | Sev. | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n7-l3-029 | medium | Answer `76/7` under `exact_numeric` with no accepted alternatives. `checking.py` parses with `Fraction`, so 10.86 or 10.857 is marked wrong and the mixed number "10 6/7" fails to parse. The prompt does not ask for an exact fraction. The title "decimal-free reduction" adds confusion. | Change the right-hand side 7 to 5 (2(3x−4)+(x+2) = 50, so 7x − 6 = 50 and x = 8; check: 20/5 + 10/10 = 5). Otherwise, add "Give your answer as an exact fraction." |
| n7-l4-016 | low | "The number is 4 times the sum of its digits plus 9" can be read as 4 × (sum + 9). That reading gives x = 15, which is not a digit, so it confuses rather than leads to a wrong answer. | "The number is 9 more than 4 times the sum of its digits." |
| n7-l4-004 | low | Title "Purchase followed by a refund", but the prompt describes change, not a refund. | Title: "Pen price from change received". |
| n7-l3-016 | low | Title "Comparing two savings accounts", but the prompt mentions no accounts. | Title: "Two amounts with a known difference". |
| n7-l5-005 | low | "After receiving an additional S$20, it has S$100 left": "left" does not fit after money is received. The item also mixes "x dollars" with "S$48". | "…After receiving another S$20, the class has S$100." Use one currency style (see C7). |
| n7-l4-012 | low | The solution omits the modelling equation ⅔(x − 18) = 40. The first line is already x − 18 = 60, so the M1 for forming the equation has no written step. | Insert S1 `\frac{2}{3}(x-18)=40` (M1) before `x-18=60`. |
| n7-l3-012, n7-l4-005, n7-l4-009, n7-l4-012, n7-l5-001 | low | The final A1 is on a verification line, and the line stating the answer gets M1. | Put A1 on the answer line. Keep the check as an unmarked step or a verification note. |
| n7-l3-011, n7-l4-014 | low | M1 awarded for restating `16 = 4x` as `4x = 16` (and `22 = 11x` as `11x = 22`). | Replace the restatement with a real step, for example collecting terms. |
| n7-l4-013 | low | Solution order is `a = 3` (M1), `2a = 6` (M1), `a = 3` (A1): the answer comes before its justification. | S1 `ax + 2a = 3x + 6`; S2 `a = 3` (x-terms) and `2a = 6` (constants); S3 `a = 3` (A1). |
| n7-l1-002 | low (judgement) | A yes/no decision is encoded as numeric 1/0. | Reviewer decision. If the response schema has no boolean or choice type, keep it, but word it "Enter 1 for yes, 0 for no." |

### C7. Audience and locale: conflict to be resolved, not assumed

| Source | Rule |
| --- | --- |
| N2 audit and `house-rules-v2.json` | `locale: en-SG`, "Singapore/British English", `currency: SGD`, "Use S$ in learner-facing Singapore-dollar contexts" |
| `LESSON_NOTES_CONTENT_STANDARD.md` (current) | Audience is "students across Indonesia and Southeast Asia". The Singapore syllabus "does not define the learner's country…". Use "clear international English" and "contexts that work across Southeast Asia". |

N7 evidence:

- **S$ in 9 questions:** n7-l1-006, n7-l1-017, n7-l2-007, n7-l2-014, n7-l2-023, n7-l2-030,
  n7-l3-016, n7-l4-004, n7-l5-005.
- **Lesson 04 uses plain "dollars"** with no S$ (`n7-74-ticket-example`, `n7-74-recall`). So the
  bank and its lesson already disagree.
- **Spelling is consistently British** (no American spellings found). Names are regionally
  neutral (Maya, Ravi, Lina, Amir, Noah). There is no Singapore-only vocabulary beyond S$.

Severity: low. **This needs an owner decision.** Either (a) keep S$, on the grounds that the
target test is a Singapore-run scholarship and the amounts are Singapore prices, and align
lesson 04 to S$. Or (b) follow the current audience standard, change the house rules to a
neutral currency style ("dollars" or unit-free), and update the 9 questions. The audit did
not apply either rule.

### Lesson findings

All four lessons pass the structural gate: 7 sections each (3 explanations, 2 worked examples
with verification notes, 1 deterministic active recall, 1 summary), with 4,643–5,092
characters as measured by the validator. All worked-example arithmetic and verification notes
were recomputed and are correct.

| Lesson / section key | Sev. | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n7-lesson-01 / `n7-71-recall` | medium | "For 4x + 1 = 21, what value does the left-hand side have when x = 5?" The answer (21) is the printed right-hand side, so the recall can be answered without substituting. | Use `4x + 1 = 23`: the left-hand side at x = 5 is 21, which shows x = 5 is **not** a solution. Feedback: "21 ≠ 23, so x = 5 is not a solution." |
| n7-lesson-02 / `n7-72-recall` | medium | "Solve 5x − 8 = 22" is exactly the equation solved on screen in section `n7-72-method` (`5x−8=22⇒5x=30⇒x=6`). | Use a fresh equation, for example `6x − 5 = 31` (x = 6) or `3x + 7 = −8` (x = −5). |
| n7-lesson-03 / `n7-73-example` and `n7-73-check-original` | medium | Both use `(x+2)/3 + (x−1)/2 = 6` with x = 7, which is identical to practice question **n7-l3-005**, including its hints and solution lines. | Change the lesson example to `(x+1)/3 + (x−1)/2 = 4`: 2(x+1) + 3(x−1) = 24, so 5x − 1 = 24 and x = 5; check 6/3 + 4/2 = 4. Or replace n7-l3-005. |
| n7-lesson-04 / `n7-74-example` | low | "Length 3 cm more than twice the width, perimeter 42 cm" is a number-swap of **n7-l3-023** ("5 cm more than twice, 58 cm"). | Vary the question, for example length 4 cm less than three times the width. |
| n7-lesson-01 / `n7-71-candidate-example` | low | Titled "choose a solution from candidates", but it solves the equation instead of testing the candidates. The verification note says "the other candidates fail substitution" without showing it. | Add a step: x = −2 gives 1 vs −5; x = 1 gives 7 vs 4; x = 4 gives 13 vs 13. |
| n7-lesson-04 | low | Currency style differs from the bank (see C7). | Follow the owner decision in C7. |
| n7-lesson-01 asset metadata | low | `kind: "chart"` for a balance-scale diagram. | Use the diagram kind the course schema provides, if it has one. |

---

## Part 2 — Diagram findings

**Diagrams in scope: 1. Viewed: 1.** None of the 104 questions has assets (`"assets": []`),
and lessons 02–04 have no assets.

### `n7-lesson-01-equation-balance`

- **Asset path:** `backend_resources/courses/g3_math/secondary_1/n1/v1/assets/n7-lesson-01-equation-balance.svg`
- **Referenced by:** `n7-lesson-01.json`, section `n7-71-method` (`asset_ref`)
- **Rendered:** Chromium at 940 px and 358 px (390 px phone)
- **generation_spec:** `{renderer: nextscholar-balance-svg-v1, diagram_kind: equation_balance, lesson_key: n7-lesson-01}`

**Accuracy checks passed:**

- The left pan shows `2x + 3` and the right pan shows `11`. This matches `2x+3=11` in the
  section text, the alt text and the SVG `<desc>`.
- The beam is level (both ends at y = 150), which matches "balanced".
- The pivot is centred (470, 150), and the pans are symmetric about x = 470 (pan centres
  260 and 680).
- No answer is revealed: x = 4 is not drawn. It is a lesson figure and the text states x = 4
  anyway.
- Title and caption do not contradict the text.

| ID | Category | Sev. | What is wrong | Specific fix |
| --- | --- | --- | --- | --- |
| D1 | neatness | medium | The left suspension line `(260,150)→(205,270)` runs through the "2" of the `2x + 3` label. Measured label bbox: x 212.3–307.7, y 214–252. At those rows the line is at x ≈ 213–231, so it overlaps the first glyph by up to 19 px, and this is visible in both renders. The right side is clear: the "11" bbox is x 662–698 and the line is at x ≈ 709–723. | Move both hangers outwards and widen the pan rims to the bowl width: left line `x1=230 y1=150 x2=175 y2=270`; right line `x1=710 y1=150 x2=765 y2=270`; left rim `x1=175 … x2=345`; right rim `x1=595 … x2=765`. Test-rendered in scratch: the left line is then at x 183–201 on the label rows, an 11.6 px gap, and the right gap is 41 px. Labels and pans keep their positions. |
| D2 | neatness | medium | Not readable on a phone. At 358 px wide the 940-unit viewBox scales by 0.38. The caption (22 units) renders at about **8.4 px** and the title (28) at about 10.7 px, both below a readable minimum of about 12 px. The pan labels (34) render at about 13 px. The caption repeats the section text. | Remove the caption and title from the SVG (they repeat `n7-71-equivalent-equations` and the section heading), then crop the viewBox to the figure, about `viewBox="155 115 630 280"`. The pan labels then render at about 19 px on a phone. If the caption stays, make it at least 32 units and shorten it to "Same operation on both sides". |
| D3 | neatness | low | Each pan rim (205–315; 625–735) is narrower than its bowl (175–345; 595–765) and offset towards the hanger. With one slanted string attached at the rim end, the pans look lopsided. | Fixed by the rim changes in D1. Optionally draw two strings per pan, from the hanger to both rim ends. |
| D4 | neatness | low | The post starts at y = 130, above the pivot circle (top at y = 132), leaving a small dark tip above the orange pivot. | Change the post to `y1="150"`. |
| D5 | accuracy (metadata) | low | `generation_spec` does not record the drawn content (expressions, balanced state). The renderer `nextscholar-balance-svg-v1` does not exist in the repository: neither `scripts/recalibrate_geometry_content.py` nor any other tracked file implements it. The asset therefore cannot be regenerated deterministically, and no validator can check the labels against the equation. | Add `left_expression: "2x + 3"`, `right_expression: "11"`, `balanced: true` to `generation_spec`, and either commit the renderer or mark the asset as hand-authored. Any byte change also needs the revisioned filename required by `GEOMETRY_CONTENT_STANDARD.md` (for example `n7-lesson-01-equation-balance-r3.svg` when the lesson moves to revision 3) and a new sha256. |

Judgement note (not counted as a finding): the pan label shows `2x + 3` as one upright Arial
string, while the lesson body sets x in italic KaTeX. A balance drawn with two "x" bags and
three unit weights would show the "subtract 3 from both sides" step that section 2 teaches.
This is for reviewers to decide.

### Text-only questions that a diagram would clearly help

N7 has **no `diagram_audit.json`**. Only the G1, G5 and Secondary 2 G2 banks have one, because
`GEOMETRY_CONTENT_STANDARD.md` requires it only for `G` topics. A manual pass found **no** N7
question where a diagram is clearly needed, because every relationship is fully stated in
words. These are optional candidates for reviewers:

- n7-l4-012 and n7-l5-005: multi-stage "fixed amount, then a fraction of the remainder"
  models, where a bar model would support the formulation step.
- n7-l3-023 and n7-l4-008: perimeter with algebraic sides. Here the text is enough.
- n7-lesson-04 has no diagram. A bar model for `n7-74-ticket-example` would support outcome 7.4.

---

## Root-cause patterns

1. **N7 was written under house rules v1 and prompt v1.** All four batches cite
   `backend_resources/question_bank/authoring/house-rules-v1.json` in `source_references`, and
   their generator is `prompt_version: math-question-authoring-v1`. The batches were created
   on 30 September 2026, before the N2 audit (10 October) introduced v2. v2 added exactly the
   rules N7 breaks: no final answer in either hint (C1), outcome alignment (C4), avoiding
   repeated operation patterns and numbers (C5), real d4/d5 demand (C3), and answer
   verification. This one cause accounts for 29 of the 45 question-level entries (all of C1, C3 and C5, plus n7-l1-014 in C4). A v2
   revision pass over N7 would fix the class rather than individual items.

2. **The 7.1 "apply a named step, report k" template.** 14 of 26 outcome-7.1 items use it.
   Because the prompt names the step and the answer is a number already in the equation or
   one operation away, the stage-2 hint tends to name the answer (5 of the 11 medium leaks
   in C1, plus the near-leak in n7-l3-009). The same template is tiered up to d3 with no change in demand (C3).

3. **7.4 stage-2 hints give the whole equation** (16 items). This is allowed by the letter of
   the "intermediate setup" rule, but it removes the formulation skill that 7.4 assesses.
   The house rules need an outcome-specific hint boundary for 7.4.

4. **Lesson examples reused as bank items** (lesson 03 = n7-l3-005; lesson 04 ≈ n7-l3-023;
   lesson 02 recall = lesson 02 method line). Lessons and questions were authored separately,
   and the duplicate detector compares questions only with questions. The catalogue run
   reported 0 duplicates, so it does not catch overlap between lessons and questions.

5. **Diagram validation does not check layout.** `course_validation._validate_assets`
   runs `geometry_diagram_issues` (in `question_bank/src/question_bank/geometry_validation.py`)
   on every lesson asset. That function checks only angle rays, angle markers and
   `forbidden_visible_labels`. It has no text-versus-line collision check and no minimum
   rendered font size for a 390 px viewport. So D1 and D2 pass validation. The renderer is
   absent from the repository (D5), so the cause cannot be traced into
   `recalibrate_geometry_content.py`, whose `svg_shape` and `svg_document` handle only
   geometry kinds. **Affected here: 1 diagram (the only one in N7).** The same full-width
   940-unit layout with a 22-unit caption is likely in the other non-geometry lesson SVGs
   (N6, S1), but they are outside this audit's scope and were not checked.

## Could not verify

- **Renderer source:** `nextscholar-balance-svg-v1` is not in the repository, so it was not
  possible to check whether D1–D4 come from a shared template.
- **Review-packet rendering:** the HTML review packets under `review_packets/` were not opened
  in a browser. KaTeX rendering of question LaTeX was not checked visually. All LaTeX was read
  as source and looks syntactically valid (`\xrightarrow` in lesson 03 is supported by KaTeX).
- **Calibration against the actual scholarship test:** difficulty judgements use the internal
  five-level rubric only, not past ASEAN Scholarship papers.
- **Pedagogical choices** marked "judgement" above are for the Mathematics reviewer and are
  not treated as defects.

## Appendix A: answer verification

The verification script was run from the repository root with SymPy 1.x. It is kept outside
the repository. For each key it states the equation **as written in the prompt**, solves it
independently, and compares the result as a `Fraction` with `canonical_answer` and every
accepted answer.

```text
checked 104 mismatches 0
answer frequency [('7', 12), ('8', 10), ('3', 6), ('5', 6), ('4', 6), ('12', 4), ('9', 4), ('6', 4)]
l4-016 alt reading [15]
```

Representative encodings: `n7-l3-029: (3x−4)/5 + (x+2)/10 = 7 → 76/7`;
`n7-l4-011: (x+5)/6 − (x−1)/8 = x/4 → 23/5`; `n7-l5-002: ⅔((x−5)/4 + 3) − (x+1)/8 = 5/2 → 35`;
`n7-l5-004: 3[2x − 5(x−4)] − 2(x+7) = 13 → 3`; `n7-l4-013` and `n7-l5-001` were solved by
checking which integer makes the two sides identical after expansion.
