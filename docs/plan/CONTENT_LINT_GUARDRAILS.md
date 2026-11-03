# Content lint guardrails

**Status:** active as warnings (none fails CI yet)
**Code:** `question_bank/src/question_bank/content_lint.py`
**Policy:** `backend_resources/question_bank/authoring/content-lint-policy-v1.json`
(schema `backend_resources/question_bank/schema/question-content-lint-policy-v1.schema.json`)
**Tests and fixtures:** `question_bank/tests/test_content_lint.py`,
`question_bank/tests/fixtures/content_lint/`

## Why this exists

The 19 pre-review audits (`docs/plan/PRE_REVIEW_AUDIT_secondary_*.md`) found serious content
defects in banks that passed `validate`, `authoring-validate`, `course-validate` and
`authoring-pr-check` with zero findings. Their root-cause sections explain why: the validators
check structure, checksums and that each canonical answer passes the checker, but they never
read the content itself. These guardrails add checks for the content-level root causes that a
deterministic rule can detect.

| Audit root cause | Audits | Check |
| --- | --- | --- |
| An authoring path wrote `\t` (an escape) instead of `\\t`. KaTeX still renders, so `latex_fragments_render` passes. | Sec 1 N5 R2, Sec 2 S1 R4 | `content_control_character` |
| The generator wrote Python `float` reprs as canonical answers (`3.333333333333332`, `15.0`). | Sec 2 S1 R4, Sec 1 N1 C-12 | `content_float_noise` |
| The duplicate scan compares prompt shingles only. Context sentences, codename prefixes and LaTeX versus plain text defeat it, and lessons are never compared with questions. | Sec 1 N1 R2, N2 R2, N3 R3, N5 R5, N7 R4; Sec 2 G5 R4, N5 R-3, N6 R-2 | `content_math_duplicate` |
| The batch generator wrote plain-text mathematics, so `latex_fragments_render` passes vacuously. | Sec 1 N1 R1, N2 R3; Sec 2 N5 R-2, N6 R-1, S2 R2 | `content_plain_text_math` |
| A template produced a prompt with no task ("A number is represented by x."). | Sec 1 N5 finding 6 | `content_prompt_without_question` |
| v1 templates gave stage-2 hints that state the answer; house rules v2 forbid it but nothing enforced it. | Sec 1 G1 C-06, N7 R1, S1 C-01; Sec 2 S2 R2 | `content_hint_reveals_answer` |
| `canonical_and_accepted_answers_pass_checker` feeds the canonical answer back to itself, so nothing compares it with the worked solution. | Sec 2 G4 R3, G5 R5 | `content_answer_solution_mismatch` |

Diagram, renderer, checker (`checking.py`), lesson-depth and difficulty root causes are outside
this change. `checking.py` is being changed in another pull request.

## Where the checks run

| Command | Question checks | Lesson checks |
| --- | --- | --- |
| `question-bank validate` (one bank) | All single-item checks, plus duplicates within the bank | — |
| `question-bank catalogue-validate` and `authoring-validate` | As above, plus duplicates across banks | — |
| `question-bank course-validate` | Promoted (error) findings only, as `question_bank_content_*` | Control characters, float noise, plain-text maths, prompts without a task, and lesson worked examples or recall checks that repeat a bank question of the same topic |
| `question-bank authoring-pr-check` | Same as `authoring-validate`. The summary lists findings for the changed batch in full and shows catalogue totals per check. `report.json` keeps every finding. | — |

Every report's JSON now includes `content_lint_counts` (findings per check code).
One issue is reported per item and check. The message lists each occurrence with its
location, for example `parts[0].solution[0].content[0].latex`.

## The checks

### `content_control_character`

- **Flags:** C0 control characters, including TAB, in any learner-facing string of a question
  or lesson (title, blocks, responses and feedback). Provenance and asset metadata are
  skipped. It also flags newlines inside LaTeX and answer fields, because `\neq` written as
  `\n` + `eq` becomes a newline. Finally, it flags double-escaped commands such as `\\frac`
  in LaTeX, which render as a line break followed by the letters `frac`.
- **Message:** names the swallowed command, for example "TAB character before 'imes'
  (probably '\times' written with an unescaped '\t')".
- **Limits:** newlines in plain `text` blocks are allowed, because lessons use them as
  paragraph breaks. A double-escaped command is flagged only for a fixed list of common
  commands (`frac`, `times`, `sqrt`, `text`, `cdot`, `left`, `right` and others).

### `content_float_noise`

- **Flags:**
  - A canonical or accepted answer (or `canonical_latex`) containing a decimal with 10 or more
    fractional digits, or a run of repeated digits ending in noise (`2.9999998`).
  - An `exact_numeric` canonical answer stored as an integer-valued float (`15.0`).
  - Any learner-visible text showing a decimal with 12 or more fractional digits.
- **Limits:** a deliberately long exact decimal answer would be flagged. That is acceptable,
  because house rules v2 require an explicit rounding instruction. `rounded_dp` answers such as
  `15.0` are not flagged.

### `content_math_duplicate`

- **How it works:** each prompt is reduced to a mathematical signature:
  - LaTeX and plain text are converted to one notation, so `\frac{3}{4}` and `3/4` agree, as
    do `\times` and `×`, `\sqrt{x}` and `√x`, and `x^2` and `x²`.
  - Sentences with no numbers, variables or operators (context) are dropped.
  - Units after numbers and `\text{…}` groups are ignored.
  - The signature is the multiset of numbers, the variables, the special operators, concept
    words such as mean, median, area or discount, and the canonical answer.
  - For code-selection prompts ("Use code 1 for …", "Enter 1 if …"), the task is in the words.
    For those, the scenario's content words replace the code numbers. A codename prefix such
    as "Azure Willow Bay dataset …:" is removed first.
- **Pairs compared:**
  - Question with question, within a bank and across banks, including the diagnostic (v2)
    banks.
  - Lesson worked example or active-recall check with bank questions of the same topic.
  - A worked example has no answer field. It matches when its numbers appear in the same
    order with the same operator skeleton.
- **Reported item:** the later item of each pair. The message names the earlier one.
- **Limits:**
  - These are heuristics, so review each pair before rewriting.
  - Items whose prompt adds an instruction sentence with numbers ("Clear denominators 3 and
    2…") differ from the plain version and are missed. For example, n7-lesson-03 and
    n7-l3-005.
  - Near-duplicates are not detected: the same template with one number changed, or the same
    numbers in a different order with a different answer.
  - Across topics, a pair with only two numbers needs a shared concept word, because results
    such as 3 × 4 = 12 are too common.
  - Lesson-to-lesson repeats are not compared.

### `content_plain_text_math`

- **Flags** `text` blocks (prompt, stem, hints, solution steps and lesson blocks) that contain:
  - a raw LaTeX command (`\frac`, `\times`, `\,`);
  - function-call roots (`sqrt(`);
  - caret exponents (`2^3`, `(5/6)^2`);
  - ASCII relations (`<=`, `>=`, `!=`, `=>`);
  - `*` used for multiplication;
  - bracketed slash fractions (`(x+3)/(x-2)`, `2/(x-6)`).
- **Limits:**
  - Simple prose such as `x = 5`, `3/4 of 120` or `5x + 4 = 34` is deliberately not flagged.
    It is too common in hints and lessons to flag without a high false-positive rate.
  - Titles are not checked.
  - This check measures the clearest cases only. The audits' "all prompts are plain text"
    findings (Sec 1 N1, Sec 2 N5) are larger than the flagged count.

### `content_prompt_without_question`

- **Flags** a question part whose learner-visible stem plus prompt has no question mark, no
  instruction verb (find, calculate, write, enter, simplify, …) and no question word (what,
  which, how many, …). It also flags lesson worked-example and active-recall prompts with the
  same problem.
- **Limits:**
  - Detection is vocabulary-based.
  - A prompt that contains an instruction verb but asks for the wrong thing passes, such as
    Sec 1 N6 n6-l5-005, where Q(4, k) is never used.
  - A prompt can also pass when the verb appears only in a context clause.

### `content_hint_reveals_answer`

- **Flags** a hint, for numeric answers, when any of these hold:
  - It states the canonical value as a result: after `=`, "is", "are", "equals", "gives",
    "make(s)", "becomes" or "leaves".
  - It repeats a non-integer exact answer as a fraction literal, for example "Write 33/50 …".
  - It gives the unsimplified form of the answer, for example "Form the fraction 28/80 and
    simplify" for 7/20.
  - For `symbolic_equivalence` answers of at least five characters, it contains the full
    canonical expression.
- **Ignored** to keep false positives low:
  - answers 0, 1 and −1;
  - a value that is an operand (`3/5 times 2/4`, `100-90`);
  - an assignment to a different variable from the one asked for (`Substitute x=3 and
    y=4`);
  - a percentage that is not the asked quantity ("80% of the original price" when the
    answer is the price, S$80).
- **Limits:**
  - Answers named in words are missed: code-selection items ("That definition identifies the
    mode", Sec 2 S1 C-13) and named shapes (Sec 1 G1 "Only the square has both properties").
  - Hints that give the whole computation without its result are missed ("Subtract 10 from
    30.").
  - When the answer is already printed in the prompt, a hint that points at it is flagged
    only if it states the value as a result.

### `content_answer_solution_mismatch`

For numeric responses, the check reports a part when:

1. **Final value:** the value the worked solution ends with differs from the canonical
   answer. The value comes from a `\boxed{…}` in the last step, or else the right-hand side of
   the last `=` or `≈`, or "is N". Rounding modes, `absolute_tolerance`, accepted answers,
   "in terms of π" coefficients and `%` are respected. To avoid false positives from
   verification steps ("Check: 54 + 46 + 80 = 180"), it is reported only when the canonical
   value never appears as a stated result anywhere in the solution.
2. **Substitution:** the final assignment (`h = 10`) does not satisfy a one-variable equation
   that the solution solved, for example `(h/21)^3 = 1/8`.
3. **False arithmetic:** a purely numerical equality in the solution is false (`12 × 5 = 70`).
   A rounded right-hand side is accepted (to its decimal places, or 1% for floats). Sides with
   different units (`1 km = 1000 m`) are skipped.
4. **1/0 decision:** for "Enter 1 if … and 0 if …" equality decisions, the canonical code
   contradicts the two values the solution compares. For example, `55²+72²=8209, 89²=7921` →
   1 (Sec 2 G4 C1).

- **Limits:**
  - The check verifies the solution against itself and the canonical answer. It does not
    recompute the answer from the prompt. A wrong answer with consistent working, such as
    Sec 1 G5 C-01 g5-l3-011 (the wording contradicts the arithmetic), is missed.
  - Algebraic responses (ratios, relations, lists, expressions) are skipped until the checker
    pull request lands.
  - Expressions that the small evaluator cannot parse are skipped. It handles `+ − × ÷`,
    powers, `\frac`, `\sqrt`, π, sin/cos/tan in degrees, percentages and implicit
    multiplication, and stays silent on anything else.
  - Lesson active-recall feedback is not compared.

## Severity policy and promoting a check to an error

Every check is a **warning** in the committed policy. Warnings appear in all reports and in the
`authoring-pr-check` summary, but they do not change any exit code. Existing content still
triggers every check (see the baseline below).

Severity is decided per finding by `content-lint-policy-v1.json`:

```json
{
  "schema_version": "1.0.0",
  "checks": {
    "content_control_character": { "severity": "error", "error_scopes": [] },
    "content_float_noise": { "severity": "warning", "error_scopes": ["g3-sec2-s1-v1"] },
    "content_plain_text_math": { "severity": "warning", "error_scopes": ["g3-sec1-n*", "n5-lesson-*"] }
  }
}
```

- `severity: "error"` makes the check an error for every question and lesson.
- `error_scopes` makes it an error only for matching content. Matching is exact, or by prefix
  when the entry ends in `*`.
- Questions match their bank key (`g3-sec2-s1-v1`) or stable key (`s1-l4-507`). Lessons match
  their course key (`g3-sec1-math`) or stable key (`n5-lesson-03`).
- Unknown check codes are rejected. An invalid or missing explicit policy file raises a
  `content_lint_policy_invalid` error rather than silently downgrading checks.

**To promote a check once content is fixed:**

1. Fix the content in a normal authoring pull request. Do not edit `checking.py` to hide a
   finding.
2. Run the validators and confirm the check's count is 0 in `content_lint_counts` for the
   scope you will promote. Run `authoring-validate`, and `course-validate` for each course:

   ```bash
   uv run --project question_bank question-bank authoring-validate | jq '.content_lint_counts'
   ```

   ```bash
   uv run --project question_bank question-bank course-validate \
     backend_resources/courses/g3_math/secondary_2/g2/v1 | jq '.content_lint_counts'
   ```

3. Edit `backend_resources/question_bank/authoring/content-lint-policy-v1.json`.
   - Add the clean bank keys, course keys or lesson-key prefixes to the check's
     `error_scopes`. This ratchets one bank at a time.
   - Once every scope is clean, set `"severity": "error"` and empty `error_scopes`.
   - Update the check's `notes` with the date and the pull request.
4. Open a pull request with only the policy change. CI runs `authoring-validate` (and
   `authoring-pr-check` on authoring pull requests), which fail if the promoted scope still
   has a finding. That run is the proof that the promotion is safe.

**To preview a promotion locally** without editing the committed file, point
`QUESTION_BANK_CONTENT_LINT_POLICY` at a scratch policy:

```bash
cat > /tmp/strict-policy.json <<'JSON'
{"schema_version": "1.0.0", "checks": {"content_control_character": {"severity": "error"}}}
JSON
```

```bash
QUESTION_BANK_CONTENT_LINT_POLICY=/tmp/strict-policy.json \
  uv run --project question_bank question-bank authoring-validate
```

New content is not automatically held to errors. If you want new batches to be strict before
the backlog is fixed, add the new bank keys to `error_scopes` when their batches are planned.

## Baseline (3 November 2026, `feature/bulk-question-authoring-pipeline` at `fe25859`)

These are warning counts from `authoring-validate`, plus `course-validate` for both courses.
There is one finding per item and check. "Bank" means the v1 learning bank, and "diagnostic
bank" means the v2 bank. Lesson rows come from `course-validate`. All commands exit 0 with 0
errors.

| Content | Control chars | Float noise | Math duplicate | Plain-text math | No question | Hint leak | Answer ≠ solution | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sec 1 G1 bank |  |  | 2 |  |  | 6 |  | 8 |
| Sec 1 N1 bank |  | 1 | 1 | 36 |  | 1 |  | 39 |
| Sec 1 N1 lessons |  |  |  | 1 |  |  |  | 1 |
| Sec 1 N2 bank |  |  | 1 | 4 |  |  |  | 5 |
| Sec 1 N3 lessons |  |  | 4 |  |  |  |  | 4 |
| Sec 1 N4 bank |  |  |  | 3 |  |  |  | 3 |
| Sec 1 N5 bank | 9 |  |  | 3 | 1 |  |  | 13 |
| Sec 1 N5 diagnostic bank |  |  |  | 1 |  |  |  | 1 |
| Sec 1 N5 lessons |  |  | 4 | 1 |  |  |  | 5 |
| Sec 1 N6 bank |  |  |  | 5 |  | 1 |  | 6 |
| Sec 1 N6 lessons |  |  | 2 | 1 |  |  |  | 3 |
| Sec 1 N7 bank |  |  | 1 | 3 |  | 4 |  | 8 |
| Sec 1 N7 lessons |  |  |  | 1 |  |  |  | 1 |
| Sec 1 S1 bank |  |  | 1 |  |  | 2 |  | 3 |
| Sec 2 G2 bank |  |  | 1 | 4 |  |  |  | 5 |
| Sec 2 G2 lessons |  |  | 1 |  |  |  |  | 1 |
| Sec 2 G4 bank |  |  | 6 |  |  |  | 1 | 7 |
| Sec 2 G4 diagnostic bank |  |  | 1 |  |  |  |  | 1 |
| Sec 2 G4 lessons |  |  | 1 |  |  |  |  | 1 |
| Sec 2 G5 bank |  |  | 29 |  |  |  | 2 | 31 |
| Sec 2 G5 lessons |  |  | 1 |  |  |  |  | 1 |
| Sec 2 N2 bank |  |  | 5 |  |  |  |  | 5 |
| Sec 2 N5 bank |  |  | 3 | 41 |  |  |  | 44 |
| Sec 2 N5 diagnostic bank |  |  |  | 1 |  |  |  | 1 |
| Sec 2 N5 lessons |  |  |  | 3 |  |  |  | 3 |
| Sec 2 N6 bank |  |  | 3 | 16 |  |  |  | 19 |
| Sec 2 N6 lessons |  |  |  | 1 |  |  |  | 1 |
| Sec 2 N7 bank |  |  | 2 |  |  | 1 |  | 3 |
| Sec 2 S1 bank | 5 | 10 | 17 |  |  |  |  | 32 |
| Sec 2 S1 lessons |  |  | 1 | 1 | 5 |  |  | 7 |
| Sec 2 S2 bank |  |  |  | 15 |  | 2 |  | 17 |
| **Total** | **14** | **11** | **87** | **141** | **6** | **17** | **3** | **279** |

Banks and lessons not listed have no findings. Cross-bank duplicates are counted against the
bank of the later item (for example, Sec 1 N7 n7-l2-030 repeats Sec 1 N3 n3-l1-004).

### Comparison with the audit findings

| Check | Flagged | Audit findings | Notes |
| --- | --- | --- | --- |
| Control characters | 14 | 14 | Every audited item: Sec 1 N5 R2 (9 questions, 12 strings) and Sec 2 S1 C-04 (5). No others exist. |
| Float noise | 11 | 11 | Sec 2 S1 C-01 to C-03 and C-06 (10), and Sec 1 N1 C-12 accepted answer `0.6666666666666666` (1). |
| Answer ≠ solution | 3 | 3 wrong answers in audits that recomputed answers | Sec 2 G4 C1 g4-l2-529, and Sec 2 G5 g5-l4-507 and g5-l4-514. Not caught: Sec 1 G5 C-01 g5-l3-011, where the wording, not the arithmetic, is wrong. Audits that reported 0 mismatches get 0 here. |
| No question | 6 | 1 | Sec 1 N5 n5-l1-006, plus 5 Sec 2 S1 lesson worked examples whose prompts state data but no task (s1-06-example-2, s1-07-example-2, s1-09-example-2, s1-10-example-1, s1-10-example-2). The audit did not raise those 5. |
| Hint leak | 17 | About 89 across 5 audits (Sec 1 G1 20, Sec 1 N7 15, Sec 1 S1 7, Sec 2 S2 9, Sec 2 S1 38) | 12 match audit rows: Sec 1 G1 C-06 (6 of 20), Sec 1 N7 C1 (4 of 15), Sec 1 S1 C-01 (s1-l1-019) and Sec 2 S2 C-17 (s2-l2-518). The other 5 are not in an audit hint table and need reviewer judgement: n1-l1-019, Sec 1 n6-l1-015, Sec 1 s1-l3-008, Sec 2 n7-l1-513, and Sec 2 s2-l2-510 (an unsimplified 28/80 for 7/20). Leaks stated in words, such as the 35 Sec 2 S1 code-selection hints, are out of reach (see limits). |
| Plain-text maths | 141 | Several bank-wide findings | This is a lower bound by design. Sec 1 N1: 36 flagged; the audit says all 64 B001–B003 items use plain text. Sec 2 N5 C-7 (all 104 prompts): 41. Sec 2 N6 C-5 (34 plain-text prompts with unsimplified coefficients): 16. Sec 2 S2: all 6 C-21 raw-LaTeX hints, plus 9 items with carets or bracketed fractions. Sec 1 N2 C-32 (32 items with slash fractions): 4, because simple `a/b` is not flagged. |
| Math duplicates | 87 | See notes | Exact matches: Sec 2 S1 C-22 17 of 17 redundant items. Sec 2 N2 C-02 5 of 5. Sec 2 N5 C-4 exact pairs 3 of 3. Sec 2 N6 C-2 exact repeat 3 of 3. Sec 1 G1 C-02 2 of 2. Lower recall: Sec 2 G5 C3 29 of 39. Lesson overlaps: Sec 1 N3 C-04 4 of 10, Sec 1 N5 L1 4 of 8 lessons, Sec 2 S1 C-24 1 of 4, Sec 1 N7 0 of 2. Also found: 6 Sec 2 G4 repeated side-length triples (C7), one Sec 2 G4 diagnostic item that repeats a learning item, and Sec 1 N7 n7-l2-030, which repeats Sec 1 N3 n3-l1-004 across banks. Template near-duplicates are not flagged. |

## Rerun

From the repository root:

```bash
uv run --project question_bank pytest question_bank/tests
```

```bash
uv run --project question_bank ruff check question_bank/src question_bank/tests
```

```bash
uv run --project question_bank question-bank authoring-validate
```

```bash
uv run --project question_bank question-bank course-validate backend_resources/courses/g3_math/secondary_1/n1/v1
```

```bash
uv run --project question_bank question-bank course-validate backend_resources/courses/g3_math/secondary_2/g2/v1
```
