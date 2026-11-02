# Secondary 1 N2 technical pre-review audit (report only)

**Date:** 2 November 2026

**Scope:** every question in `backend_resources/question_bank/g3_math/secondary_1/n2/v1/`
(104 questions, batches B001–B004) and every lesson for unit `g3-sec1-n2`
(3 lessons, stored under `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/`
and found through `course.json` → `units[stable_key=g3-sec1-n2].lessons`).

**Decision boundary:** this is a technical pre-review only. It records no Mathematics or
editorial approval, and it changes no question, lesson, asset, manifest, claim or review
state. All four batches are already `approved` for Mathematics and editorial review, and all
three lessons are `reviewed`. The findings below are for human reviewers to triage; this
audit does not reopen those approvals.

**Standards applied:** `docs/plan/N2_CALIBRATION_PRE_REVIEW_AUDIT.md` (the model for this
audit), `docs/plan/LESSON_NOTES_CONTENT_STANDARD.md` and
`docs/plan/GEOMETRY_CONTENT_STANDARD.md`. The geometry standard applies only to `G` topic
groups, so for N2 it was used only for the diagram-policy checks.

## Counts

| Item | Checked | Notes |
| --- | ---: | --- |
| Questions | 104 | 26 per batch; 58 numeric `exact_numeric`, 46 `exact_ratio` |
| Question parts | 104 | Every question has one part |
| Lessons | 3 | `n2-lesson-01` (2.1), `n2-lesson-02` (2.2), `n2-lesson-03` (2.3) |
| Lesson worked examples and recall checks | 9 | 6 worked examples and 3 active-recall checks |
| Diagrams, graphs or charts referenced | **0** | No question or lesson declares an asset |
| Diagrams rendered and viewed | **0** | Nothing to render (see Part 2) |

## Checks performed

- Recomputed all 104 canonical answers from the prompt text, without reading the solutions
  first, using a script built on exact `fractions.Fraction` arithmetic. The script simplifies
  ratios, links ratios, shares totals and solves the linear equations in each part value.
  **Result: 104 of 104 match; 0 mismatches.**
- Recomputed every lesson worked example and active-recall answer in the same way. All 9 are
  correct.
- Read every worked step against the recomputed values. I also checked that every intermediate
  count in a change problem is a positive whole number (for example n2-l4-016: 28 adults and
  36 children, which become 24 and 48).
- Read `question_bank/src/question_bank/checking.py` to confirm how `exact_numeric` and
  `exact_ratio` judge responses.
- Checked outcome and difficulty tags against the blueprint definitions and against
  structurally similar items.
- Checked both hint stages for answer leakage against the blueprint `hint_policy`.
- Compared contexts, numbers and operation patterns across the bank, the lessons and the
  course pools (`question_pools/n2.json`) for semantic duplicates.
- Checked wording, terminology, currency and maths formatting.
- Reran the repository validators. `question-bank validate …/secondary_1/n2/v1`,
  `question-bank course-validate` and `question-bank catalogue-validate` all report
  `valid: true` with 0 errors and 0 warnings.
- Confirmed that the four review packets' `questions.json` files parse to exactly the same JSON as
  the current question files, so the packets reviewers approved are not stale.

Severity scale: **High**: a wrong answer, or an item a learner cannot answer as intended.
**Medium**: misleading teaching, assessment or tagging that a reviewer should fix before more
learners use the item. **Low**: consistency, style or polish.

---

## PART 1: CONTENT

### 1.1 Canonical answers, worked steps, accepted answers and conditions

No incorrect canonical answer, worked-solution result or stated condition was found in the
104 questions or the 3 lessons.

Accepted-answer behaviour (no change required):

- `exact_numeric` parses fractions, decimals and percentages exactly. So `5/2` is already
  accepted for n2-l1-008 (`2.5`), and the explicit `accepted_answers: ["3/2"]` on n2-l1-017
  is redundant but harmless.
- Mixed-number input such as `1 1/2` is rejected with a format error rather than marked wrong.
  No N2 numeric answer is a non-integer except n2-l1-008 and n2-l1-017, so this is acceptable.
- Responses typed with a unit or currency (for example `S$60` or `140 g`) are rejected with a
  format error. This conflicts mildly with lesson 3's checklist, which tells learners to
  "answer the named quantity with its unit" (see C-17).
- All 46 `exact_ratio` items use `require_simplest_integer_terms: true` with the correct term
  count. Every prompt asks for simplest form, so non-simplified equivalent ratios are rightly
  rejected.

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-01 n2-l4-003, n2-l4-014 | Low | The final A1 step is only `\gcd(6,10,7)=1` or `\gcd(2,3,5)=1`. The answer line never states `x:y:z=…`. | End each solution with `x:y:z=6:10:7` (or `2:3:5`) and keep the HCF check as a verification note. |
| C-02 n2-l1-007 to n2-l1-021 (15 items) | Low | One-step, 1-mark answers are marked `A1` with no preceding `M` mark. n2-l1-001 to n2-l1-006 use `B1` for the same kind of item. | Use `B1` consistently for independent 1-mark answers, or record the convention in the house rules. |

### 1.2 Outcome alignment

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-03 n2-l5-001, n2-l5-003 | Medium | Both are tagged 2.2 ("writing a ratio in its simplest form"). The work is forming and solving `(2k+C)/(3k+C)=5/6` or `(8k+t)/(15k+t)=3/4`, which is the changed-ratio method lesson 3 teaches under 2.3. n2-l5-001 is the only d5 item for 2.2 in `n2-unit-checkpoint`, so the checkpoint's 2.2 top-end evidence actually measures 2.3. | Retag both to 2.3 and author d5 items for 2.2 that are genuinely about simplest form, for example a hidden-unit three-term ratio. Alternatively, add 2.3 as a secondary outcome and swap the checkpoint item. |
| C-04 Linked-ratio items across all three outcomes | Medium (judgement call) | Combining A:B and B:C appears under 2.1 (n2-l3-001, -009, -016, -024, n2-l4-002, -005, -009), 2.2 (n2-l4-003, -006, -010, -014) and 2.3 (n2-l3-007, -030, n2-l5-003). The method is taught only in lesson 3's explanation "Scale and link ratios", and no lesson has a worked example of it. Lesson 1's practice pool includes n2-l3-001 and n2-l3-009, and lesson 2's pool includes n2-l4-003, all as `challenge`. Learners therefore meet linking before the lesson that teaches it. | Decide which outcome owns linking. Then either add a short linking worked example to lessons 1 and 2, or move those items to the lesson 3 pool or checkpoint. |
| C-05 n2-l4-001 (lesson 1 pool) | Low | This 2.1 item is a changed-ratio equation, `(5k+7)/8k=4/5`. That method is taught in lesson 3's worked example "reconstruct a changed ratio". | Keep it in the checkpoint or reserve rather than the lesson 1 practice pool, or add a forward reference. |

### 1.3 Difficulty alignment

The blueprint defines d4 as "an unfamiliar problem requiring method selection, constraints, or
justification" and d5 as "complex non-routine synthesis".

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-06 n2-l4-014 | Medium | Tagged d4, but once each ratio is simplified the B terms already match (2:3 and 3:5), so no alignment is needed. This is easier than d3 n2-l3-024, which needs 3→9 alignment. | Retag to d2/d3, or alter the numbers so that alignment is needed. |
| C-07 n2-l4-003 | Medium | Tagged d4, but it uses integer ratios 3:5 and 10:7 with a single ×2 alignment. It is easier than d3 n2-l3-001 and n2-l3-007. | Retag to d2, or rewrite with rational terms and an LCM alignment. |
| C-08 n2-l4-002 | Medium | Tagged d4, but the simplified ratios 4:5 and 5:8 share B = 5, so the three-term ratio is read off directly. Stage 2 says so ("giving a three-term ratio directly"). | Retag to d3, or change B:C so that alignment is needed. |
| C-09 n2-l3-018 | Low | Tagged d3, but it is structurally identical to the d2 items n2-l2-024 (`3/4:5/6`, given P, find Q) and n2-l2-017. n2-l2-003 uses the same ratio, 2/3:5/6, at d2 with added context. | Retag to d2, or add a second step. |
| C-10 Linked three-term clusters | Low | n2-l3-024 (d3) has the same structure and difficulty as n2-l4-006, n2-l4-009 and n2-l4-010 (all d4). | Align the tags across the cluster. |
| C-11 Changed-ratio clusters | Low | n2-l3-031 (d3), n2-l4-004 (d4) and n2-l4-011 (d4) all use money in ratio 3:5, two changes, a new ratio and an original total. n2-l3-029 (d3) and n2-l4-001 (d4) are also near-identical in method. | Align the tags, or make the d4 items require an extra constraint. n2-l4-011's fixed-total transfer is the strongest d4 candidate. |
| C-12 n2-l5-002, n2-l5-004 vs n2-l4-013 | Low | All three combine two mixtures in the same way (simplify each ratio, share each volume, add, simplify). n2-l4-013 is d4, while n2-l5-002 and n2-l5-004 are d5 and differ only in harder simplification. | Retag n2-l5-004 to d4, or add a genuinely non-routine element to the d5 items, for example a required top-up volume to reach a target ratio. |

### 1.4 Hint leakage

Stage 2 must "give an explicit next method or intermediate setup without giving the final
answer". All 208 hints avoid stating the final value (checked by script). In the cases below, however, the answer
can be read off stage 2 with no further method.

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-13 n2-l4-014 | Medium | Stage 2: "The ratios simplify to x:y=2:3 and y:z=3:5." The answer, 2:3:5, is these two ratios written together. | Replace with method only, for example "Simplify each ratio, then check whether the y terms already match." |
| C-14 n2-l3-009, n2-l3-016 | Medium | Stage 2 gives "3:7 and 7:9" and "5:7 and 7:10". The B terms already match, so A:C (3:9 = 1:3, 5:10 = 1:2) is immediate. | Give only one of the two simplified ratios, or describe the alignment step without values. |
| C-15 Near-complete stage 2 hints | Low | n2-l4-002 (gives 4:5:8), n2-l4-015 (gives all three rates 4, 5 and 15/4), n2-l3-001, n2-l4-006, n2-l4-009 and n2-l4-010 (give the simplified ratios and the common term), n2-l2-019 and n2-l2-028 ("becomes 6:9"), n2-l1-015 and n2-l2-023 (give the value of one part). | Acceptable under the policy, but reviewers should decide whether d4 items may reveal three of their four method marks in stage 2. |
| C-16 n2-lesson-01 active recall | Medium | The recall check (`1.5 kg:600 g`, answer 5:2) is the example from section 1, which already shows the conversion to `1500 g:600 g`. The check is not independent recall. | Use a fresh pair, for example `2.5 kg:750 g` (answer 10:3). |

### 1.5 Lesson coverage against `LESSON_NOTES_CONTENT_STANDARD.md`

All three lessons have exactly 6 sections: 2 explanations, 2 worked examples with
verification notes, 1 deterministic active-recall check and 1 summary. Each meets the
structural baseline.

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-17 Lesson length metric | Medium | The validator passes all three lessons on "≥ 2,500 authored characters". It measures `len(json.dumps(sections))` (`course_validation.py:lesson_note_depth_shortfalls`), which counts JSON keys, `stable_key` values and punctuation. The learner-visible text and LaTeX total is about 1,884, 1,717 and 1,889 characters (lessons 1–3). The JSON sizes are 4,062, 3,584 and 4,371. | Decide whether the standard means visible text. If it does, the three N2 lessons are below the baseline and the metric should be corrected (this affects every lesson, not only N2). |
| C-18 n2-lesson-01 | Medium | 7 of the 20 items in lesson 1's practice pool are "how many times as much/long/heavy" division comparisons (n2-l1-001, -002, -007, -008, -012, -013, -017). The lesson never teaches this reading of a ratio. It also has no worked example with fractional terms, although n2-l2-003, -017 and -024 and n2-l3-018 use them. | Add a worked example: "how many times as much" as `a÷b`, with a fraction-term ratio such as `2/3:5/6 = 4:5`. |
| C-19 n2-lesson-01 | Low | Section 1 says, "Ratios have no unit only after the quantities have been expressed in the same unit." This is hard to parse and suggests that ratios carry units before conversion. | Use: "A ratio has no unit. Before comparing, express both quantities in the same unit; for example…" |
| C-20 n2-lesson-01 | Low | The worked example is titled "compare decimal lengths", but the prompt `0.75:1.2` has no lengths or context. It is also a simplest-form task (2.2) placed before lesson 2 teaches HCF reduction. | Retitle it "simplify a decimal ratio", and either add a context or cross-reference lesson 2. |
| C-21 n2-lesson-02 summary | Low | The summary says "divide every term by the common highest factor". | Change to "highest common factor". |
| C-22 n2-lesson-03 summary | Low | "Answer the named quantity with its unit" conflicts with numeric responses, which reject a unit or currency symbol. | Add: "type only the number in the answer box". |

### 1.6 Semantic duplicates

`catalogue-validate` detects only exact content-fingerprint matches across banks
(`validation.py`, `cross_bank_duplicate_content`). It does not detect any of the following.

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-23 n2-l1-002 / n2-l1-013 | Medium | Both use the same numbers (3/4 and 1/4), the same operation and the same answer (3). Their stage 2 hints are word-for-word identical ("Dividing by 1/4 is the same as multiplying by 4."). Both are in the lesson 1 guided pool. | Rewrite n2-l1-013 with a different fraction pair and an answer that is not a whole number, for example 5/8 kg and 1/4 kg (answer 2.5). |
| C-24 2.1 d1 answer clustering | Low | 5 of the 7 guided items in lesson 1's pool have the answer 3 (n2-l1-001, -002, -007, -012, -013). n2-l1-012 also repeats the ribbon context of n2-l1-002. | Vary the answers and contexts. |
| C-25 n2-l3-014 / n2-l3-022 | Medium | Both use red:blue counters in ratio 4:7 and both answer **6:7** (one removes blue counters, the other adds red ones). Both are lesson 3 items: one is in the practice pool and the other is in the checkpoint. | Change the context, ratio or target in one of them. |
| C-26 n2-l4-012 / n2-l4-016 | Medium | Both use adults:children, a fraction of adults leaving, children arriving, a new ratio of **1:2** and "find the original total attendance". Both are d4 and both are in the adaptive reserve. | Rewrite one with a different structure, such as a transfer or a known difference. |
| C-27 n2-l2-014 / n2-l2-023 | Low | Both use "flour and sugar" with the same scale-from-one-part pattern (5:8 and 30 g; 5:2 and 350 g), and both are in lesson 3's independent pool. The N2 audit fixed the recipe duplicate between n2-l2-030 and n2-l2-023 but left this pair. | Change one context. |
| C-28 n2-l1-015 / n2-l1-020 | Low | Both use ratio 3:5 with one known first term ("find the second"). | Vary the ratio. |
| C-29 n2-l3-031 / n2-l4-004 | Low | Both use Ali, money in ratio 3:5, Ali's amount changes, and a new ratio gives the original total. | Change the names or structure in one item. |
| C-30 n2-lesson-01 worked example / n2-l2-025 | Medium | The worked example "find a missing term" (`1.2:1.8 = x:15`, x = 10) has the same numbers, unknown and answer as practice item n2-l2-025 (blue 1.2 L : white 1.8 L, 15 L white → 10 L). That item is in the adaptive reserve. | Change the lesson example's numbers, for example `1.2:1.8 = x:24`. |
| C-31 n2-lesson-03 active recall / n2-l2-006 | Low | The recall check is S$84 shared in ratio 2:5 (smaller share 24). n2-l2-006 is S$84 shared in ratio 2:5 (larger share 60). | Change the recall total or ratio. |

### 1.7 Wording and formatting

| Key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-32 32 questions | Medium | Every question prompt and hint is plain `text`. Fractions and mixed numbers are typed with slashes, while the lessons use `inline_math`. The mixed-number items are the hardest to read: n2-l3-004 shows "1 1/2:2 1/4", n2-l3-019 "1 1/4:2 1/2:3 3/4" and n2-l3-012 "2 1/3 km". A learner can read "2 1/4" as "21/4". The affected items are n2-l1-002, -008, -013; n2-l2-003, -004, -009, -011, -017, -019, -024, -028; n2-l3-002, -004, -009, -010, -012, -013, -016, -018, -019, -024, -026, -028; n2-l4-002, -005, -006, -009, -010, -013, -015; n2-l5-002, -004. | Use `inline_math` blocks (`\frac34`, `1\frac12`) in prompts and hints, as the lessons and solutions already do. |
| C-33 n2-l1-016, n2-l3-023, n2-l4-011 | Medium | These three B003 items use "SGD 72", "SGD 160" and "SGD 24/14". The N2 audit made S$ consistent only in B004. Six other questions and lesson 3 use "S$". | Use one notation bank-wide; see the policy conflict P-1. |
| C-34 n2-l1-006 | Low | "A sum of 40 is divided…" gives no currency or unit. | Add the unit or context, for example "S$40", "40 stickers" or "40 litres". |
| C-35 n2-l1-016 | Low | "SGD 72 is shared in the ratio 5:4" does not say who shares it. | Name the two recipients, so the order of the ratio terms has meaning. |
| C-36 n2-l2-025 | Low | "…find the volume x litres of blue paint needed" is awkward. | Use "Let the volume of blue paint be x litres. Find x." |
| C-37 n2-l4-001 | Low | A and B are never introduced as masses, yet the item asks for "B in kilograms". | Use "Two masses, A kg and B kg, are in the ratio 0.75:1.2…" |
| C-38 n2-l1-015 | Low | Stage 2 says "one part represents 5 items". | Use "5 apples". |
| C-39 Terminology | Low | The same concept is named in three ways: "greatest common factor" (n2-l1-003, -004, n2-l2-005), "highest common factor" (n2-l1-009, -014, -018, n2-l2-027, n2-l3-021 and both lessons) and `\gcd` (n2-l2-004, n2-l3-027, n2-l4-003, -014). Likewise, "lowest common denominator" (n2-l2-004, -019) appears alongside "lowest common multiple of the denominators". Neither lesson glosses HCF. | Standardise on one term and gloss it once in lesson 2, for example "highest common factor (HCF), also called the greatest common factor". |

### 1.8 Conflicts between the N2 audit's Singapore-specific rules and the current audience standard

These are reported, not resolved. They need a policy decision from the content owners.

- **P-1 Currency.** The N2 audit (finding 3) made "S$" the required notation and asked for
  numeric responses in dollars. `LESSON_NOTES_CONTENT_STANDARD.md` defines the audience as
  "secondary-school students across Indonesia and Southeast Asia". It treats the Singapore
  syllabus as "a calibration and coverage reference", not the learner's school system, and
  asks for "contexts that work across Southeast Asia". The bank currently mixes S$ (6
  questions and lesson 3), SGD (3 questions) and no currency (n2-l1-006). There is a
  case for keeping S$, because the target is a Singapore-run scholarship test, and a case for
  neutral or regional contexts. Either way, the bank should use one notation.
- **P-2 Language variety.** The N2 audit checked "Singapore/British English". The current
  standard asks for "clear international English". The N2 items use British spellings
  ("colour" in n2-l1-014, n2-l4-007 and n2-l5-004; "litres"), which are usually acceptable
  in international English. Reviewers should confirm whether British spelling remains the
  house variety.
- **P-3 Terminology.** "Highest common factor" is the Singapore and UK classroom term.
  Indonesian learners typically meet it as FPB, and international texts often use GCF or GCD.
  The audience standard asks for unfamiliar terminology to be explained, but the lessons use
  HCF without a gloss (see C-39).
- **P-4 Bank metadata.** `blueprint.json` still names the course "Singapore G3 Mathematics",
  while `course.json` uses "ASEAN Scholarship Mathematics — Level 1". This is not
  learner-facing as far as I can tell, but it is inconsistent with the audience standard.

---

## PART 2: DIAGRAMS AND GRAPHS

**This topic has no diagrams.**

- All 104 question files have `"assets": []`, and every prompt, hint and solution block is
  `text`, `inline_math` or `display_math`.
- All three N2 lessons have `"assets": []`, and no section references an image.
- `backend_resources/courses/g3_math/secondary_1/n1/v1/assets/` has no `n2-*` file.
- The only `<svg` strings in the N2 review packets are inside the bundled KaTeX JavaScript in
  `index.html`, not authored figures.

Consequently, 0 diagrams were rendered or viewed, and no diagram was reported as visually
checked. No rendering tool was installed, because there was nothing to render.

**Root-cause tracing.** Not applicable, because no N2 diagram exists. For context,
`scripts/recalibrate_geometry_content.py` targets only the Secondary 1 G1 and G5 banks, and
`geometry_validation.py` runs only on declared assets. Neither touches N2. No
`diagram_audit.json` exists for N2, and the geometry standard does not require one for an
`N` topic group.

**Text-only questions a diagram would help.** No N2 item requires a figure; every relationship
is stated unambiguously in text. One optional suggestion is left to reviewers. Bar or part
models are the conventional teaching aid for multi-step ratio change problems. A
deterministic part-model diagram in `n2-lesson-03` (the "reconstruct a changed ratio" worked
example) would likely help the d4–d5 transfer items most (n2-l4-011, n2-l5-005). Adding one
would also bring a diagram-authoring and validation pass into N2.

---

## Root-cause patterns

1. **Linking ratios has no teaching home** (C-04, C-05, C-14, and C-06 to C-08). Items from
   all three outcomes rely on combining A:B and B:C, but only lesson 3's explanation covers
   it, with no worked example. The same gap also explains the inconsistent difficulty tags:
   whether the B terms already match decides most of the difficulty, and the tags do not
   reflect that.
2. **Duplicate detection is exact-match only** (C-23 to C-31). `cross_bank_duplicate_content`
   compares fingerprints, so items with the same numbers, the same context or the same answer
   pass. The duplicates are spread across B001–B003. The N2 audit's v2 house rules add
   semantic-duplicate checks only for future batches.
3. **Prompt formatting differs between authoring paths** (C-32). Question prompts and hints
   are plain `text` with slash fractions, while lessons and solutions use LaTeX blocks. This
   affects 32 of the 104 questions.
4. **The B004-only currency fix** (C-33) left the three SGD items in B003 untouched.
5. **The lesson-length metric counts JSON** (C-17). All three N2 lessons pass the 2,500-character
   gate only because of serialisation overhead. Every lesson validated by
   `lesson_note_depth_shortfalls` is affected.

## Could not verify

- Whether the learner UI renders plain-text slash fractions differently from the review packet
  (C-32). The review was done on JSON and packet text, not in the learner app.
- The intended owner outcome for linked-ratio items (C-04). This is a curriculum decision.
- The house policy on currency, language variety and terminology (P-1 to P-3).
- Whether the gap between `checkpoint_question_count: 15` in `course.json` and the 20-item
  `n2-unit-checkpoint` pool is intentional sampling. Validators accept it.
- No diagram checks were possible, because the topic has no diagrams.

## Summary for reviewers

- **No High-severity findings.** All 104 answers and all lesson examples are mathematically
  correct, and all validators pass.
- **Fix first (Medium):**
  - outcome tags: C-03, C-04;
  - difficulty tags: C-06, C-07, C-08;
  - hint leakage: C-13, C-14, C-16;
  - lesson coverage and length metric: C-17, C-18;
  - duplicates: C-23, C-25, C-26, C-30;
  - formatting and currency: C-32, C-33.
- **Policy decision needed:** P-1 to P-4.
