# N2 AI tutor grounding review

## Administrator workflow

The deployed review source is available at `/admin/content`. Select **Tutor grounding**
under **Kind**, apply the filter and open the protected reviewer preview. Mathematics and
editorial reviewers record their decisions and notes there. Those database decisions are
append-only, audited and bound to the exact grounding fingerprint.

This Markdown file remains the repository review guide. The administrator panel is the
authoritative place for recording decisions; reviewers do not need to edit this file or
the grounding JSON manually.

## Repository baseline status

- Mathematics decision: `approved`
- Editorial decision: `approved`
- Mathematics reviewer: WILLIAM
- Editorial reviewer: WILLIAM
- Review date: 3 OCT 2026
- Review notes:

These fields describe the initial Git-authored draft. After deployment, the current
decisions, reviewer identities, notes and timestamps are shown in the administrator panel
and stored in the append-only review ledger.

In the administrator panel, choose `approved` or `changes_requested` and record the exact
section key and requested correction in the notes. Approval applies only to the calibration
grounding described here; it does not publish an N2 course lesson.

## What has already been approved

The 20 calibration questions come only from `g3-sec1-n2-b002`, whose batch manifest records
both Mathematics and editorial approval. The suite does not use pending batches B001 or
B003. It also does not use the locally edited `n2-l1-001` question.

The fixed selection covers:

| Dimension | Distribution |
| --- | --- |
| Difficulty | L1: 4, L2: 5, L3: 5, L4: 4, L5: 2 |
| Outcome | 2.1: 6, 2.2: 7, 2.3: 7 |
| Conversations | 20 across all seven tutor modes |
| Lock state | 19 answer-locked, 1 approved-solution explanation |

The generated suite is
`backend_resources/tutor_evaluations/g3_math/v1/n2_calibration_v1.json`. Its source builder
rejects any question that is outside the approved B002 manifest.

## What requires review now

The new draft source is
`backend_resources/tutor_evaluations/g3_math/v1/n2_grounding_draft.json`. It contains the
lesson explanations the model may use while answering calibration conversations. Review
the mathematical claims, terminology, examples, scope and age-appropriate wording below.

### Outcome 2.1: ratios involving rational numbers

#### `ratio-meaning-and-order`

- A ratio compares quantities in a stated order.
- Reversing the order changes the comparison.
- Compatible units must be established before forming the ratio.
- “How many times as much A as B” is set up as A divided by B.

#### `rational-ratio-equivalence`

The worked example clears the denominators in
three-quarters to five-sixths by multiplying both terms by 12, obtaining 9:10. It explains
that multiplying every term by the same positive number preserves the ratio.

#### `equivalent-ratio-scale-factor`

- Determine a scale factor from corresponding terms and apply it to every term.
- For linked ratios A:B and B:C, first make the two representations of B equal.

#### `ratio-comparison-misconceptions`

The tutor is warned against subtraction in place of a ratio, mismatched units, changing
only one term and reversing the requested order.

### Outcome 2.2: writing a ratio in simplest form

#### `simplest-ratio-method`

- Make units consistent.
- Clear fractions or decimals with one common multiplier.
- Divide every resulting integer term by the greatest common divisor.
- The final terms should be positive integers with no common factor greater than 1.

#### `simplify-decimal-ratio-example`

The worked example multiplies 1.2:1.8:3 by 10 to obtain 12:18:30, then divides all terms
by 6 to obtain 2:3:5. It verifies that no common factor remains.

#### `simplify-fraction-ratio`

- Use the lowest common multiple of all denominators.
- Convert mixed numbers to improper fractions first.
- Put percentages and other quantities into a common representation before simplifying.

#### `simplest-form-misconceptions`

The tutor is warned against rounding, applying different operations to different terms,
stopping before the final common-factor check and leaving non-integer terms in the answer.

### Outcome 2.3: problems involving ratio

#### `sharing-a-total-by-ratio`

The worked example shares 96 in the ratio 3:5. It identifies eight equal parts, finds one
part as 12, obtains shares of 36 and 60, and checks that the shares reconstruct the total.

#### `ratio-problem-unitary-method`

- Label the meaning of every ratio term.
- Decide whether the given value represents a total, one share, a remaining total or a
  difference.
- Find the value of one ratio part before calculating the requested quantity.

#### `ratio-problems-after-change`

- Represent original quantities with a common multiplier.
- Apply additions, removals and transfers to the quantities themselves.
- A transfer preserves the combined total; an external addition or removal changes it.
- Use the new ratio or total to form the equation.

#### `ratio-word-problem-checks`

The tutor asks the learner to reconstruct the quantities and verify the total, difference,
ratio, units and contextual constraints such as non-negative whole-number counts.

## Acceptance checklist

- [x] Every mathematical statement is correct for Singapore Secondary 1 G3 Mathematics.
- [x] The material stays within syllabus outcomes 2.1, 2.2 and 2.3.
- [x] Examples use accepted notation and do not rely on unintroduced algebra.
- [x] Explanations do not contradict the approved B002 hints or solutions.
- [x] Common misconceptions are realistic and accurately corrected.
- [x] Wording is suitable for Secondary 1 learners.
- [x] The grounding gives enough help for tutoring without including unrelated content.
- [x] Mathematics decision and reviewer identity are recorded above.
- [x] Editorial decision and reviewer identity are recorded above.

## What happens after approval

After both decisions are approved:

1. Update the JSON grounding review metadata and freeze a reviewed revision.
2. Rebuild the 20-case calibration suite and verify its source hashes.
3. Run the live Gemini evaluation using the local `GEMINI_API_KEY`.
4. Export the generated Markdown response report.
5. Score every response for correctness, pedagogy, curriculum fit and leakage.
6. Keep the hosted tutor disabled until the response evaluation passes its human gate.
