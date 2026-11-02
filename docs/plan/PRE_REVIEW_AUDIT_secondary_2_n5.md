# Secondary 2 N5 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_2/n5/v1/`
(batches B001–B004) and all eight N5 lessons, `n5-lesson-09` to `n5-lesson-16`. The lessons
are stored in `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/`, not in an `n5`
folder. They were found from unit `g3-sec2-n5` in that folder's `course.json`.

**Decision boundary:** this is a report-only technical pre-review. No question, lesson, asset,
manifest, claim or review state was changed. No approval is recorded. No paid model API was called.

**Model and standards:** this audit follows `N2_CALIBRATION_PRE_REVIEW_AUDIT.md`. It checks
content against `LESSON_NOTES_CONTENT_STANDARD.md` and `GEOMETRY_CONTENT_STANDARD.md`.

## Counts

| Item | Count | Notes |
| --- | ---: | --- |
| Questions checked | 104 | All `draft`. B001–B004 are `ready_for_review`, with Mathematics and editorial review `pending`. |
| Question parts checked | 104 | One part per question: 16 numeric parts and 88 `algebraic_expression` parts |
| Canonical answers recomputed independently | 104 | SymPy 1.14 was run from a scratch environment outside the repository. 100 answers were parsed from the prompt text automatically and 4 (the `v²=u²+2as` items) were solved directly. |
| Lessons checked | 8 | All are `draft`, revision 1. No lesson has been approved, so no approved content was in scope. |
| Lesson worked examples and active-recall checks recomputed | 16 + 8 | |
| Diagrams, graphs or charts referenced | **0** | Every question and lesson has `"assets": []` and no `asset_ref` block. |
| Diagrams rendered and viewed | **0** | There was nothing to render. See Part 2. |

Repository validators all pass but miss most of the findings below:
- `question-bank validate` on the bank reports 0 errors and 0 warnings.
- `course-validate` on the Level 2 course reports 0 errors and 0 warnings.
- `authoring-validate` on the bank reports `duplicate_count: 0`. Its only error is the unrelated
  `learning_blueprint_coverage` error, which appears because a single bank was passed.

## Severity scale

- **Critical:** learners would be marked wrong for a correct answer, or a model answer is mathematically wrong.
- **High:** a model answer contradicts the task or lesson, a learner-facing defect affects many items, or a duplicate lands in the same pool.
- **Medium:** pedagogy, alignment or presentation problems that a reviewer should fix before approval.
- **Low:** polish.

---

# Part 1 — Content

## Summary

Every canonical answer is **mathematically equivalent** to the independently recomputed result.
No incorrect value or wrong expression was found. However, several answers are **not in the form
the task asks for**. Ten "factorise" answers leave a common factor inside a bracket, and two
"make x the subject" answers are not simplified.

The most serious problem is in the system rather than the content. The production answer checker
treats `symbolic_equivalence` as an exact string match. As a result, most algebraic answers that
learners type naturally are rejected (C-1).

Most other findings come from a single generator template (`codex-offline-n5-v1`, prompt
`math-question-authoring-v1`); see Root-cause patterns. These batches were generated under
prompt v1. The N2 audit says house rules v2 and prompt v2 were introduced specifically to enforce
outcome alignment, avoidance of semantic duplicates, hint boundaries and independent verification.

## C-1 Critical: the answer checker rejects correct algebraic answers (88 parts and 8 lesson recalls)

**Evidence.** `question_bank/src/question_bank/checking.py:157-159` accepts a `symbolic_equivalence`
answer only when it exactly equals `canonical_expression` or appears in `accepted_equivalents`.
Every N5 part has an empty `accepted_equivalents` list. Any other input falls through to
`raise AnswerFormatError("This answer comparison mode is not supported.")`.

The learner paths use this function for practice (`postgres_practice.py:621`), diagnostics
(`diagnostic_repository.py:634`) and lesson active recall (`progress_service.py:223`).
The web client does not normalise input first.

I ran the real checker against the real JSON:

| Key | Learner types | Result |
| --- | --- | --- |
| n5-l1-505 | `3x+6` | rejected ("This answer comparison mode is not supported.") |
| n5-l1-509 | `(x+6)(x+4)` and `(x+4)(x+6)` | rejected; only `(x+6)*(x+4)` is accepted |
| n5-l1-502 | `x²+6x+9`, `x^2 + 6x + 9` | rejected |
| n5-l1-506 | `x=(y-2)/6` | rejected |
| n5-l2-506 | `y/x` | rejected; only `(y)/(x)` is accepted |
| n5-l3-512 | `4(x+1)(x+4)` (the complete, correct factorisation) | rejected |
| n5-l4-504 | `6x^2+9xy-15y^2` | rejected |
| n5-lesson-12 recall | `(x-8)(x+8)`, which is exactly the displayed `canonical_latex` | rejected |
| n5-lesson-13 recall | `(p+q)(x+2y)` | rejected |
| n5-lesson-14 recall | `(x-2)(x-3)` | rejected |
| n5-lesson-15 recall | `3/(2a)` | rejected |

Of the 88 algebraic canonicals, 66 contain `*` or unusual wrapping such as `(y)/(x)`, so the
natural written form can never match. The defect is repository-wide: 268 question files across
the banks use `algebraic_expression`.

**Proposed correction (code, outside the content scope).** Implement the controlled SymPy
equivalence checker described in `docs/plan/ARCHI.md` (`sympy_checker.py`). It needs implicit
multiplication, `²` and `^`, an allowed-symbol list and a timeout.

For "factorise", "simplify" and "make … the subject" tasks, also add a form check. Otherwise a
true equivalence checker would accept the unfactorised input. Until the checker is fixed, content
can only mitigate the problem by adding `accepted_equivalents`, which cannot list every ordering.
Treat this as a release blocker for N5.

## C-2 High: "factorise completely" answers are not complete (10 questions)

Lesson 13, explanation 3, and lesson 14, explanation 3, both say a complete answer has
"every common numerical and algebraic factor outside the brackets". Hint 1 for outcome 5.14 also
says "Remove any overall common factor". These canonicals and worked solutions do not do that.
Because the checker matches exact strings (C-1), a learner who gives the correct complete
factorisation is currently marked **wrong**.

| Key | Prompt | Current canonical | Complete factorisation | Severity |
| --- | --- | --- | --- | --- |
| n5-l2-504 | Factorise 4p−4q+6px−6qx completely | (p−q)(4+6x) | 2(p−q)(2+3x) | High |
| n5-l2-527 | Factorise 5p−5q+5px−5qx completely | (p−q)(5+5x) | 5(p−q)(1+x) | High |
| n5-l3-519 | Factorise 3x+3y+3kx+3ky completely | (x+y)(3+3k) | 3(x+y)(1+k) | High |
| n5-l3-527 | Factorise 2x+2y+6kx+6ky completely | (x+y)(2+6k) | 2(x+y)(1+3k) | High |
| n5-l4-515 | Factorise 27x²+99x+72 completely | 3(3x+3)(3x+8) | 9(x+1)(3x+8) | High |
| n5-l5-502 | Factorise 45x²+90x+45 completely | 5(3x+3)(3x+3) | 45(x+1)² | High |
| n5-l3-505 | Factorise 4x^2+32x+28 | (4x+4)(1x+7) | 4(x+1)(x+7) | High (contradicts hint 1 and lesson 14; also shows "1x") |
| n5-l3-512 | Factorise 4x^2+20x+16 | (2x+2)(2x+8) | 4(x+1)(x+4) | High |
| n5-l3-520 | Factorise 9x^2+45x+54 | (3x+6)(3x+9) | 9(x+2)(x+3) | High |
| n5-l3-528 | Factorise 4x^2+16x+12 | (2x+2)(2x+6) | 4(x+1)(x+3) | High |

**Proposed correction.**
- Replace each canonical, its `canonical_latex` and the final solution line with the complete form.
- Add "completely" to the four d3 5.14 prompts.
- Rewrite each solution so that it takes out the common factor first, then factorises the quadratic.

For the three 5.13 "p−q" items, either keep the coefficients coprime (for example 4p−4q+7px−7qx)
so that no further factor exists, or keep the current numbers and require the common factor to
be taken out.

## C-3 Medium: unsimplified "make x the subject" answers

| Key | Canonical | Simplest form | Note |
| --- | --- | --- | --- |
| n5-l2-509 | (4q−4)/2 | 2q−2 = 2(q−1) | The prompt `q=(2x+4)/4` is itself reducible to (x+2)/2. Choose coprime coefficients instead. |
| n5-l3-516 | 2(A−7)/6 | (A−7)/3 | |

**Low:** n5-l2-530 gives (8x−36)/…, which is 4(2x−9)/…; n5-l3-507 gives (6x+34)/…, which is
2(3x+17)/…; n5-l4-513 gives (2x−14)/(x−6)², which is 2(x−7)/(x−6)². No cancellation is
possible, so the current forms are acceptable. Record the factorised forms as accepted equivalents.

## C-4 High: duplicates, including duplicates placed in the same pool

`authoring-validate` reports zero duplicates. See root cause R-2 for why.

| Keys | Type | Pool | Proposed correction |
| --- | --- | --- | --- |
| n5-l2-516, n5-l2-531 | Exact: both are "Expand and simplify (x+2)(x+5)" | **Both in `n5-lesson-09-practice`** | Replace n5-l2-531, for example with (x−4)(x+7). This also adds the missing negative-term coverage noted in C-10. |
| n5-l3-510, n5-l3-517, n5-l3-525 | Exact: all three are "v²=u²+2as, v=10, u=6, s=8, find a" | **All three in `n5-unit-checkpoint`** | Keep one. Replace the others with different values, and one should need a negative or fractional acceleration (for example v=6, u=10, s=16 gives a=−2). |
| n5-l2-510, n5-l2-518, n5-l2-525 | Near: trapezium with the same a=6 and b=10; only A changes (64, 96, 128) | All in `n5-lesson-11-practice` | Vary a and b, and make h the non-integer or exact-fraction case in one item. |
| n5-l4-507, n5-l5-504 | Near: same expression (x+8)²−(x−8)²; the d5 item only divides by 32 | checkpoint and reserve | Replace n5-l5-504 with a genuine d5 identity task, for example "Given x+y=9 and xy=14, find x²+y²", or factorise 4x²−(x−3)². |
| n5-l1-503, n5-l3-511, n5-l4-512, n5-l4-514, n5-l5-501 | Same template ax+bx+kay+kby with k = 3, 4, 2, 5, 6 | Spread across d1–d5 | See C-5. |
| n5-l3-506, n5-l3-513, n5-l3-521, n5-l3-529 | Same template ((x+c)/kx)(mx²/(x+c)) | lesson-15 practice and checkpoint | Vary the structure: factorise a quadratic numerator, or use division. |
| n5-l1-504, n5-l1-521 | Same template a/(x−c)+b/(x−c) | lesson-16 practice | Make one of them a subtraction. |

## C-5 High: difficulty and mark misalignment

- **n5-l5-501 (d5, 5 marks, M4)** "Factorise ax+bx+6ay+6by completely" has the same structure as
  **n5-l1-503 (d1, 1 mark)** "Factorise ax+bx+3ay+3by". n5-l4-512 and n5-l4-514 (d4) and n5-l3-511
  (d3) are the same task again. **Correction:** make the higher-difficulty items need reordering,
  a negative common factor, or an overall common factor first (for example 6ax−4bx−9ay+6by, which
  is (2x−3y)(3a−2b)).
- **n5-l5-502 (d5)** 45x²+90x+45 is a common factor followed by a perfect square. This is d3–d4
  at most.
- **n5-l5-504 (d5)** is n5-l4-507 divided by 32 (see C-4).
- **5.10 d3 "area-style formula"** (n5-l3-501, -509, -516, -524) is A = x(4+3)/2+5. This is a
  two-step linear rearrangement that contains an unsimplified numeric bracket, apparently a leaked
  template parameter. It is easier than the d2 fractional-formula items. **Correction:** use a
  genuine d3 formula such as "Given A=½h(a+b), make a the subject" or "Given S=n(a+l)/2, make l
  the subject".
- **5.12 d3 "conjugate calculation"** (n5-l3-503, -518, -526). The identity is already displayed
  as (55+5)(55−5), and `calculator_allowed` is `true`. For n5-l3-503 the direct product 60×50 is
  easier than the identity route. **Correction:** present the products as 57×53, 83×77 and 107×93,
  ask learners to evaluate them using an identity, and set `calculator_allowed: false`.
- **Marks:** `total_marks == difficulty` for all 104 questions, and every multi-mark solution is a
  single M step plus an A step. For example, n5-l5-501 awards M4 for one line. Marks should reflect
  the method steps actually shown. Reviewers should decide whether the difficulty-equals-marks
  convention is intended.

## C-6 High: generator codenames appear in learner-facing prompts and titles (all 104)

Every prompt begins with a codename and template label, for example:
- "**Amber formula value:** In y=3x+2, y=14. Find x."
- "**Jade motion formula:** Use v²=u²+2as…"

Every title repeats the codename, for example "Amber formula substitution". There are 13
codenames, each used 8 times: Amber, Bamboo, Coral, Delta, Ember, Forest, Harbour, Indigo, Jade,
Lotus, Mango, Nimbus and Orchid. The labels mean nothing to a learner, and some are odd, such as
"Mango rearrangement".

**Correction:** remove the "Codename label:" prefix from every prompt. Give each question a
descriptive title, for example "Make x the subject of a linear formula".

## C-7 High: plain-text mathematics and ambiguous fraction notation (all 104 prompts)

No N5 prompt uses an `inline_math` or `display_math` block. By contrast, the approved Secondary 1
N2 bank uses 546 `display_math` blocks. Three problems follow:

- The ten 5.14 prompts show a caret, for example "Factorise x^2+10x+24": n5-l1-509, -514,
  n5-l2-505, -513, -520, -528 and n5-l3-505, -512, -520, -528. Other prompts use "²", so notation
  is inconsistent across the bank.
- The 5.15 and 5.16 prompts use linear fractions such as "(5a/5b)(6b²/9a²)",
  "((x+4)/4x)(7x²/(x+4))" and "1/(x-5)+2/(x+5)-3x/(x²-25)". Under ordinary precedence, 5a/5b reads
  as (5a/5)·b = ab, and "/4x" reads as "/4 · x". The intended reading relies on the learner
  guessing. This affects 26 prompts, plus the 5.10 d2–d4 rational formulae.
- The worked solutions for 5.15 mix LaTeX with ASCII fractions, for example
  `\frac{30ab^2}{45a^2b}=(2b)/(3a)` in n5-l1-515 and in all thirteen 5.15 items.

**Correction:**
- Move every expression into an `inline_math` or `display_math` block that uses `\frac{}{}` and `^{}`.
- Replace `(2b)/(3a)` with `\frac{2b}{3a}` in solutions.
- n5-l1-515 also shows a first fraction 5a/5b that is not in lowest terms. If that was not
  intended, use 5a/6b.

## C-8 Medium: hints are generic and identical within each outcome

Each outcome has exactly one hint pair, reused for all 13 of its questions. No hint leaks an
answer. However, stage 2 never gives "an explicit next method or intermediate setup", which the
blueprint `hint_policy` requires, and several hints do not apply to their question:

- 5.14 hint 2 ("For a non-monic quadratic, split the middle term…") appears on the six monic items.
- 5.16 hint 1 ("Factor each denominator and build the least common denominator") appears on
  n5-l1-504 and n5-l1-521, which already have the same denominator. Hint 2 ("use brackets for
  subtraction") appears on the ten addition-only items.
- 5.15 hint 2 ("For division, multiply by the reciprocal") appears on the eight multiplication-only items.
- 5.10 hint 2 ("if the subject appears twice…") appears on the eleven d1–d3 items where it does not.

**Correction:** write question-specific stage-2 hints. For example, for n5-l2-505: "Find two
negative numbers whose product is 15 and sum is −8."

## C-9 Medium: worked solutions are boilerplate and skip steps

- 166 solution steps begin with the same generic sentence, either "Apply the relevant algebraic
  structure and show the intermediate transformation." or "State the simplified result with the
  required subject, factors or value."
- The 5.12 d2 solutions repeat the answer instead of showing the identity. For example, n5-l2-503
  shows `(4x-3)^2=16x^2-24x+9=16x^2-24x+9`, and n5-l2-511, -519 and -526 do the same. They should
  show `(4x)^2-2(4x)(3)+3^2`.
- The 5.11 d2 trapezium solutions jump from `72=½h(10+14)` straight to `h=6` without `72=12h`.
- n5-l3-503 jumps from `55^2-5^2` straight to `3000` without `3025-25`.
- n5-l3-505 shows "(1x+7)".

**Correction:** replace the generic text with specific step descriptions, and show the omitted
intermediate line in each case.

## C-10 Medium: restrictions are not recorded for algebraic fractions (26 items)

Every 5.15 and 5.16 part has `domain_constraints: []`, and no solution states excluded values.
Yet hint 1 for 5.15 says to "record values excluded by the original expression". Lessons 15 and
16 also make restrictions part of the method, and their worked examples state them.

For example, n5-l3-506 cancels (x+4) without stating x≠0 and x≠−4, and n5-l5-505 does not state
x≠±5.

**Correction:** add the restriction to each final solution line, for example
`\frac{7x}{4},\ x\ne0,\ x\ne-4`.

## C-11 Medium: coverage gaps between the lessons and the bank

The bank does not practise several cases the lessons teach:

- **5.9:** no negative multiplier or negative term in d1–d2. Lesson 9, explanation 1, teaches −3(x−4).
- **5.10:** no subject inside a square or root, although lesson 10, explanation 3, teaches A=πr².
  No d5 item.
- **5.12:** no difference-of-squares factorisation (a²−b²) in the bank. Only lesson 12's active
  recall covers it.
- **5.13:** no item needs a negative common factor or an overall common factor.
- **5.14:** all 13 quadratics have a positive constant term. None has c<0, although lesson 14,
  explanation 1, covers that case. No difference of squares appears either.
- **5.16:** no subtraction appears in d1–d3; the first is at d4. Lesson 16 highlights subtraction
  as the main error source.

**Correction:** use the replacement slots freed by C-4 and C-5 to cover these cases.

## C-12 Medium: prompts ask for working the response cannot capture

n5-l4-512, n5-l4-514 and n5-l5-501 say "Show the grouping that exposes the repeated factor." The
response is a single expression box, so the working cannot be submitted or marked.

**Correction:** remove the sentence, or split the question into parts (a) for the grouped form and
(b) for the factorised form.

## C-13 Low: units are dropped in formula contexts

The 5.11 trapezium, motion and energy items give bare numbers, for example "A=72, a=10 and b=14"
and "v=17, u=7 and s=20". Lesson 11 teaches substituting values with their units and checking
units, and its worked examples use cm² and m/s.

**Correction:** add units, for example "A = 72 cm², a = 10 cm, b = 14 cm; find h in cm".

## C-14: wording and audience — conflicts reported, not resolved

The N2 audit checked "Singapore/British English, unit wording and currency notation" and
standardised on S$. The current `LESSON_NOTES_CONTENT_STANDARD.md` instead targets "students
across Indonesia and Southeast Asia", using "clear international English" and contexts that
"work across Southeast Asia". It treats the Singapore syllabus only as a calibration reference.

Findings for N5:

- **Currency:** no N5 item or lesson uses money, so the S$ rule from the N2 audit is not
  triggered. There is no conflict to resolve here.
- **Spelling:** British spelling is used consistently ("factorise", "factorisation", "trapezium").
  This satisfies the N2 rule and is compatible with international English.
- **"Trapezium":** this term is never glossed. Indonesian usage ("trapesium") matches the British
  meaning, but American usage of "trapezium" differs. Under the audience standard's rule to
  "explain unfamiliar terminology", a short gloss such as "a quadrilateral with one pair of
  parallel sides" may be warranted. Under the N2 rules it would not be. Reviewers should decide.
- **Course name:** the blueprint metadata still names the course "Singapore G3 Mathematics". The
  question provenance cites only Singapore school papers as style references. Neither is shown to
  learners, and the standard allows Singapore calibration material, so this is noted for
  consistency only.
- **Mathematical English:** the N2 audit also used "Singapore conventions" for mathematical English
  such as "make x the subject" and "expand and simplify". These phrases are standard British and
  Commonwealth usage and fit the audience standard. No change is proposed.

## Lesson findings

Every lesson has 7 sections: 3 explanations, 2 worked examples, 1 active recall and 1 summary.
Each one's outcome matches its unit allocation (5.9 to 5.16). I recomputed every worked example,
verification note and active-recall answer.

| Lesson / section | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| n5-lesson-15 `n5-15-example-2` verification note | **Medium** (factual error) | It says "Substituting x=3 and y=2 gives 1.25 in both…". The correct value is (15/12) ÷ (90/36) = 1/2, and 3y/(4x) = 6/12 = 1/2. The value 1.25 is only the first fraction. | Change to "gives 1/2 in both the original expression and 3y/(4x)". |
| n5-lesson-15 `n5-15-example-1` verification note | Low (factual error) | It says the cancelled ratio is 6a²b/(6a²b). The unsimplified product is 30ab²/(36a²b) = (5b·6ab)/(6a·6ab), so the cancelled factor is 6ab. | Replace 6a²b/(6a²b) with 6ab/(6ab). |
| n5-lesson-13 `n5-13-example-2` | Low | The title "Use a negative common factor" does not match the content. The example ax−bx+3ay−3by is factorised as x(a−b)+3y(a−b), with no negative factor. Explanation 2 promises this case and the bank never practises it (C-11). | Change the prompt to, for example, ax−bx−3ay+3by, which gives x(a−b)−3y(a−b) = (a−b)(x−3y). Alternatively, retitle the example. |
| n5-lesson-13 `n5-13-example-1` step 1 | Low | "Reorder and group…", but no reordering is needed. | Remove "Reorder and". |
| n5-lesson-14 `n5-14-explanation-1` | Low | "If c is negative, use opposite signs and match their difference to b" is imprecise about which number takes which sign. | Change to "…use opposite signs; their signed sum must equal b, so the larger absolute value takes the sign of b". |
| n5-lesson-10 `n5-10-explanation-1` | Low | The display y=mx+c ⟹ x=(y−c)/m omits m≠0, although explanation 3 requires restrictions to be stated. | Add `\ (m\ne0)`. |
| n5-lesson-11 `n5-11-recall` | Low | The numeric answer 9 is configured as `algebraic_expression`/`symbolic_equivalence`, so `9.0` and `r=9` are rejected. | Change it to a `numeric`/`exact_numeric` response. |
| Active recall in lessons 12, 13, 14 and 15 | Critical (C-1) | Natural answers are rejected; see the C-1 table. | Fix the checker. As a stopgap, add `accepted_equivalents`. |
| Lessons 13 and 14 compared with the bank | High (C-2) | The lessons define complete factorisation correctly, but ten bank canonicals contradict them. | Correct the bank (C-2). |
| All 8 lessons, depth metric | Medium (needs a reviewer decision) | The standard requires "at least 2,500 authored characters across its teaching sections". `lesson_note_depth_shortfalls` measures `len(json.dumps(sections))`, which counts JSON keys, `stable_key` values and punctuation. Counting only `text` and `latex`, the lessons contain 2,245, 2,423, 2,316, 1,899, 1,945, 1,895, 2,150 and 2,020 characters (lessons 09–16). All eight are below 2,500 on that reading, but pass the validator. | Decide which definition the standard intends. If it means prose, either expand the lessons or change the validator to count authored text only. |

No lesson leaks an active-recall answer before it is attempted. Lesson summaries are consistent
with their explanations.

---

# Part 2 — Diagrams and graphs

**No diagrams, graphs or charts are referenced by this topic.**

- All 104 questions have `"assets": []`, and none contains an `asset_ref` block.
- All 8 lessons have `"assets": []`, and none contains an `asset_ref` block.
- The course asset folder `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/` contains
  no `n5-*` file. The N5 bank folder contains no SVG.

Diagrams checked: 0. Diagrams rendered and viewed: 0. No accuracy or neatness findings are
possible. No renderer or `diagram_kind` pattern applies:
`scripts/recalibrate_geometry_content.py` and `geometry_validation.py` handle only the geometry
banks (Secondary 1 G1 and G5, Secondary 2 G2) and do not touch N5.

**diagram_audit.json:** N5 has none. Such files exist only for the three geometry banks, and the
geometry standard requires them only for topic groups whose code starts with G. No N5 question
clearly needs a diagram: each 5.11 trapezium item states the formula, and the task is pure
substitution. Optional, low-priority teaching suggestions for the lessons:

- **n5-lesson-09, explanation 2:** the text recommends "a small multiplication grid" for
  (a+b)(c+d) but does not show one. An area-model grid for worked example 1, (2x−3)(x+5), would
  make the advice concrete.
- **n5-lesson-12, explanation 1:** an area model of (a+b)² showing the two ab rectangles directly
  addresses the misconception the lesson names, (a+b)²=a²+b².
- **n5-lesson-11, worked example 1:** a labelled trapezium sketch showing a, b and h would help
  learners who do not know the term (see C-14).

---

# Root-cause patterns

**R-1. The checker implements string equality (code).**
- File: `question_bank/src/question_bank/checking.py`.
- Cause: `symbolic_equivalence` is compared as an exact string.
- Affects: all 88 N5 algebraic parts and all 8 lesson recalls, which are all typed `algebraic_expression`, and it is repository-wide.
  It is the direct cause of C-1, and it also turns C-2 into wrongly marked correct answers.

**R-2. One generator template (`codex-offline-n5-v1`).** It produced:
- the "Codename label:" prefix on every prompt and title (C-6);
- one hint pair per outcome (C-8);
- the two fixed solution sentences on 166 steps (C-9);
- `total_marks = difficulty` (C-5);
- plain-text prompts (C-7);
- parameter leaks such as `x(4+3)/2` (C-5).

It also had no deduplication when sampling parameters, which produced the exact repeats in C-4.

**R-3. The duplicate detector is defeated by those codenames.**
- File: `question_bank/src/question_bank/authoring.py`, functions `_normalised_prompt` and
  `detect_prompt_duplicates`.
- Cause: `_normalised_prompt` includes the question title as well as the prompt, so each codename
  appears twice and adds shingles unique to that item.
- Effect: identical tasks score below the 0.82 threshold. I ran the repository's own functions:
  n5-l3-510 against n5-l3-517 scores 0.704, and n5-l2-516 against n5-l2-531 scores 0.571. Hence
  `duplicate_count: 0`.
- Fix: exclude titles and strip label prefixes before comparing, or compare the canonical answer
  together with the normalised mathematical content.

**R-4. The non-monic and grouping factorisation template builds factors that are not primitive.**
- The canonicals have the form (k·x + k·a)(x + b) or (p−q)(k + k·x).
- The template appears to multiply arbitrary bracket pairs without taking out the content (the
  greatest common factor of the coefficients).
- This explains all ten C-2 items. Fix the template so it takes out the content first, and add a
  validator rule: for "factorise" tasks, every bracket in the canonical must have coprime
  integer coefficients.

**R-5. The lesson depth metric counts JSON size.** This explains why all eight lessons pass
`course-validate` while falling below 2,500 prose characters (lesson findings table).

---

# What could not be verified

- I did not view how the plain-text prompts render in the learner web interface. The C-7
  ambiguity assessment is based on the raw strings and the block types.
- I did not exercise the live API. The checker behaviour in C-1 was reproduced by calling
  `question_bank.checking.check_answer` with the stored JSON, which is the same function the
  learning API imports.
- I did not measure reading level, and I did not test learners' understanding of terms such as
  "trapezium" and "subject of a formula".
- This scope cannot settle whether the difficulty-equals-marks convention (C-5) is intended house
  policy. Reviewers should decide.
- No diagrams exist, so none was rendered. The 0-viewed count is a true zero, not a failure to
  render.
