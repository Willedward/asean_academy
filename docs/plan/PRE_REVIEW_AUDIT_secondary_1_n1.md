# Secondary 1 N1 technical pre-review audit

**Date:** 2 November 2026

**Scope:** every question in `backend_resources/question_bank/g3_math/secondary_1/n1/v1/`
and every N1 lesson in the Secondary 1 course

**Decision boundary:** report-only technical pre-review. No question, lesson, SVG,
manifest, claim or review state was changed. No Mathematics or editorial approval is
recorded by this audit.

**Model:** `docs/plan/N2_CALIBRATION_PRE_REVIEW_AUDIT.md`. **Standards applied:**
`docs/plan/LESSON_NOTES_CONTENT_STANDARD.md` and `docs/plan/GEOMETRY_CONTENT_STANDARD.md`.
N1 is not a `G` topic group, so the geometry standard applies only to how diagrams are
drawn and described, not to lesson depth.

## Coverage

| Item | Count | Notes |
| --- | ---: | --- |
| Questions checked | **104** | 64 in batches B001 (22), B002 (21) and B003 (21), all `ready_for_review` with Mathematics and editorial review `pending`. The other 40 are seed questions (`n1-l1-01` … `n1-l3-10`) that are in no batch manifest. All 104 are `draft`, revision 1. |
| Lessons checked | **7** | `n1-lesson-01` … `n1-lesson-07` (outcomes 1.1–1.7), all `draft`, revision 2. They are in `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/`, which is the whole Secondary 1 course folder, not an N1-only folder. They were identified through unit `g3-sec1-n1` (topic code N1) in `course.json`. No other lesson in the course lists an N1 outcome. |
| Diagrams referenced | **1** | `assets/n1-l3-01-number-line.svg`, used by question `n1-l3-01`. None of the N1 lessons references an asset (`"assets": []` in all seven). |
| Diagrams actually viewed | **1 of 1** | Rendered with the pre-installed Chromium (Playwright) to PNG in a scratch directory outside the repository. It was viewed at native size (760 × 180, 2× device scale) and at a 390-px phone viewport with 16-px gutters. |
| Approved content | **0** | Nothing in N1 has a recorded approval. All review states were left as found. |

### Checks performed

- Recomputed every canonical answer from the prompt alone, in code (exact `Fraction`
  arithmetic, prime factorisation, divisor counts, integer-solution enumeration and
  half-up rounding), before reading the solutions. **All 104 canonical answers and every
  part answer match.** Quoted intermediate values were also recomputed: all are correct
  except one hint (C-02).
- Checked every worked solution, both hint stages, accepted answers and stated
  conditions. Accepted answers and likely learner inputs were run through the real
  checker (`question_bank/src/question_bank/checking.py`).
- Checked outcome and difficulty allocation against `blueprint.json` difficulty
  definitions and outcome titles.
- Checked for semantic duplicates across the 104 questions and the lesson examples.
- Checked wording, notation, rendering and audience conventions.
- Ran `question-bank validate` on the N1 bank (valid, 0 errors, 0 warnings),
  `course-validate` (valid, 0 errors, 0 warnings) and `authoring-validate` (valid,
  0 duplicates). Several findings below pass all three validators.

Severity scale: **High** means a learner can be marked wrongly or sees broken or
incorrect content. **Medium** means it should be fixed before approval. **Low** means
polish or a judgement call for the reviewer.

---

## Part 1: Content findings

### High

| ID | Stable key(s) | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-01 | `n1-l2-022`, `n1-l2-028`, `n1-l4-002` | The accepted answers `"1 3/4"`, `"1 1/4"` and `"2 5/24"` go through `_fraction()`, which deletes spaces. They therefore become 13/4, 11/4 and 25/24. When run through the real checker, the **wrong answers `13/4`, `11/4` and `25/24` are marked correct**. These are the only three mixed-number accepted answers in the whole question bank. | Remove the three mixed-number accepted answers now. Separately, the checker should parse `a b/c` as a mixed number or reject it with a format error. That is a code change outside this audit. Until it is made, prompts should ask for an improper fraction. |
| C-02 | `n1-l3-021` | Hint 2 says "The unrounded result is 1914.0625". The correct value is 612 500 ÷ 320 000 = **1.9140625**, so the hint is out by a factor of 1000. It also nearly states the answer. | Replace it with: "First find 640 000 − 27 500, then divide by 320 000. Keep the full display." |
| C-03 | `n1-l2-016` (B001) and `n1-l2-03` (seed) | Identical task: "Express 756 as a product of prime factors in index notation", with answer 2²×3³×7. | Replace `n1-l2-016` with a different integer and structure, for example one with a prime cubed and a two-digit prime. |
| C-04 | `n1-l3-019` (B002) and `n1-l3-02` (seed) | Identical task: smallest positive integer m/k such that 540m is a perfect cube, with answer 50. | Replace `n1-l3-019` with a different base number. For example, use 1500 = 2²×3×5³, which needs 2×3² = 18. |
| C-05 | `n1-l3-022` (B002) and `n1-l2-07` (seed) | Same context ("At dawn, the temperature…"), the same rise of 7.8 °C and fall of 5.6 °C, and the same operation order. Only the start value differs (−3.5 instead of −4.5). The B002 copy is also labelled D3 while the seed is D2. | Replace `n1-l3-022` with a new context and new numbers, and set its difficulty to D2. |
| C-06 | `n1-l4-007` (B002) and `n1-l2-06` (seed) | Same numbers (18, 24, 30), the same LCM (360) and the same method, with a context added. It is labelled **D4** although the identical computation is D2. | Replace it with a genuine D4 task. For example, combine an LCM with a constraint such as a time window or a count of meetings, or reverse the problem from the LCM. |
| C-07 | All 64 batch questions (B001–B003) | **None of the 64 batch questions contains a single `inline_math` or `display_math` block.** All their mathematics is plain text, for example `sqrt(324)-2.5^2`, `(4.86×10^7)(3.2×10^-4)`, `2 1/3 - 5/6 + 1/4`, `7 3/4 litres` and `-11/6<(2n-1)/5<=7/10`. `apps/web/src/components/math-content.tsx` renders text blocks exactly as written, so learners will see `^`, `sqrt(…)`, `<=` and slash fractions. Mixed numbers written as `2 1/3` can be read as 21/3. In contrast, the 40 seed questions all use KaTeX. | Convert prompts, hints and solutions to `inline_math`/`display_math` blocks, as in the seed questions. Do this first in prompts with mixed numbers (`n1-l2-022`, `n1-l4-002`) and standard form (`n1-l3-015`, `n1-l3-021`, `n1-l3-026`). |

### Medium: answer checking and stated conditions

| ID | Stable key(s) | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-08 | `n1-l2-016` | Solution step 1 reads `756=2Ò378=2^2×189`. "Ò" is mis-encoded text that should be "×". It also appears in the generated review packet `review_packets/g3-sec1-n1-b001/questions.json`. | Correct it to `756=2\times378=2^2\times189` and regenerate the packet. (If C-03 replaces the question, this goes with it.) |
| C-09 | `n1-l4-004` | A solution text block contains a literal LaTeX command: `7.13\times7=49.91<50`. It renders as `7.13\times7`. | Move it into a `display_math` block. |
| C-10 | `n1-l1-08`, `n1-l2-08`, `n1-l2-022`, `n1-l2-028`, `n1-l3-013`, `n1-l4-002`, `n1-l5-003` | Each prompt says "Give your answer in its simplest form" (or "exact value"), but `exact_numeric` accepts any equal value. Through the checker, `14/24`, `-2/12`, `8/12` and `198/238` are all marked correct. The stated condition is not enforced. | Either drop the "simplest form" wording or enforce it, for example with a lowest-terms option on `exact_numeric`. The reviewer should decide which; the item content alone cannot fix this. |
| C-11 | `n1-l1-017`, `n1-l1-020`, `n1-l3-030`, `n1-l4-004`, `n1-l4-010` | Each prompt says "Insert < or > …". The natural reply, `<`, gets the format error "Enter one complete relation". For `n1-l3-030`, the learner must type `-10.5<-10.4`, because the products as written in the prompt (`(-7/12)×18<(-2.6)×4`) are rejected. | Add a response instruction such as "Write the complete statement, for example −3 < 2". For `n1-l3-030`, ask the learner to compare the evaluated products. |
| C-12 | `n1-l3-013` | The accepted answer `"0.6666666666666666"` is a truncated float that only matches that exact string. It contradicts "simplest form" and does not help a learner who types `0.67`. | Remove it. |
| C-13 | `n1-l1-14`; lesson `n1-lesson-07` section `approximation-recall` | The question typesets `48\,372` with a thin space, but `rounded_sf` marks the answer `48 400` wrong (spaces are counted when checking significant figures). The lesson feedback shows `78,600`, which the checker rejects as a format error. | Show answers without digit separators in learner-visible feedback, or accept separators in the checker. |

### Medium: duplicates and repeated templates

House rule v2 says: "Avoid repeating a prior question's context, operation pattern and
numerical structure." `authoring-validate` reported 0 duplicates. All of the following
passed it, including the identical pairs in C-03 and C-04. One likely reason: seed
questions write their mathematics in LaTeX and batch questions in plain text, so
text-similarity checks do not see them as the same.

| ID | Stable keys | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-14 | `n1-l2-017`, `n1-l2-05`, `n1-l3-025` | All three use **168 and 252** with HCF 84. The tiles in `n1-l2-05`(b) and the ribbons in `n1-l3-025` also share the same follow-up (2 + 3 or 2 × 3 pieces). | Keep `n1-l2-05`. Change the numbers in `n1-l2-017` and `n1-l3-025`. |
| C-15 | `n1-l2-02`(b), `n1-l2-15`, `n1-l2-026`, `n1-l3-018`, `n1-l3-031` | Five questions estimate (a × b)/c to 1 s.f. `n1-l3-031` reuses 398 and 1.98 from `n1-l2-15`. `n1-l3-018` reuses 19.8 and 0.503 from the lesson 7 worked example. The tasks are labelled D2 and D3 with no difference in demand. | Keep two. Replace the rest with other estimation forms, such as square roots, sums inside a quotient, or checking a given calculator result. |
| C-16 | `n1-l2-018`, `n1-l2-025`, `n1-l2-031` (also `n1-l1-11`, `n1-l2-12`) | Each asks to order 3–4 negative values between about −1.5 and −1.8. Most include −7/4 or −13/8. | Vary the range and the form, for example a mix of positive and negative values, recurring decimals or percentages. |
| C-17 | `n1-l4-008`, `n1-l4-015`, `n1-l5-002` | The same template three times: define A, then calculate 100(A − k)/(A + k). Two are D4 and one is D5. | Keep one at D4. Replace the D5 copy with a genuinely non-routine calculator task. |
| C-18 | `n1-l4-001`, `n1-l4-006`, `n1-l4-012` | The same template three times: N = 2ᵃ×3ᵇ(×p), divisible by X, with exactly Y factors. | Keep one. Replace the others with different 1.1 reasoning. |
| C-19 | `n1-l4-003`, `n1-l4-009`, `n1-l5-004`; `n1-l1-12`, `n1-l3-016` | Three "fraction of the way from A to B" questions (D4, D4, D5) and two midpoint questions (D1 and D3 for the same task). | Keep one of each. Make the difficulty labels consistent. |

### Medium: outcome and difficulty alignment

| ID | Stable key(s) | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-20 | `n1-l1-019`, `n1-l2-024`, `n1-l3-022`, `n1-l3-027`, `n1-l3-028` | These are allocated to **1.5** (number line and ordering), but each task is plain signed arithmetic (−8 + 13, −2.7 − (−4.35) + 1.2, the temperature and elevator sums, a mean). That is **1.3**. A hint that mentions the number line does not make it a 1.5 task. | Rewrite each so it assesses representation or ordering on a number line, or move it to 1.3 and rebalance the allocation. |
| C-21 | `n1-l2-025`, `n1-l2-031` | These are allocated to **1.6** (use of <, >, ≤, ≥), but the task is to order values in a list, which is **1.5**. (`n1-l2-018` is the same task and is correctly 1.5.) | Rewrite them to require inequality notation, or move them to 1.5. |
| C-22 | `n1-l3-027` (D3), `n1-l3-022` (D3), `n1-l3-026` (D3), `n1-l3-016` (D3) | Each is one or two routine steps (−3 + 8 − 11; one standard-form division plus √625; a midpoint, which `n1-l1-12` labels D1). This fits D1–D2 under the rubric. | Relabel them D1 or D2, or raise their demand. |
| C-23 | `n1-l5-003` (D5), `n1-l5-004` (D5), `n1-l5-002` (D5) | D5 is defined as "complex non-routine synthesis…". `n1-l5-003` is routine fraction arithmetic with harder numbers. `n1-l5-004` repeats the D4 template from `n1-l4-003` and `n1-l4-009`. `n1-l5-002` repeats the D4 template from `n1-l4-008` and `n1-l4-015`. Only `n1-l5-001` and `n1-l5-005` require synthesis. | Relabel them D3/D4, or rewrite them to need several ideas combined. |
| C-24 | Outcome scope (judgement call) | Several questions go beyond the outcome titles in `blueprint.json` and are not taught in the matching lesson: **(a)** the divisor-count formula (`n1-l2-04`, `n1-l4-001/006/012`), not in `n1-lesson-01`; **(b)** completing a perfect square or cube (`n1-l3-011/012/019/02/024/03`), not in lessons 1–2; **(c)** upper and lower bounds of sums, products and quotients (`n1-l2-14`, `n1-l3-09`, `n1-l3-10`, `n1-l4-005/011/016`); outcome 1.7 lists rounding and estimation only, and `n1-lesson-07` gives the bounds of a single value but has no worked example combining bounds; **(d)** solving scaled linear inequalities (`n1-l3-017/023/029`, `n1-l5-005`); the Secondary 2 N7 lessons cover inequalities, and `n1-lesson-06` does not teach multiplying through; **(e)** standard form (`n1-l3-015/021/026`), not taught in `n1-lesson-04`; **(f)** the section formula P = A + t(B − A) (`n1-l4-003/009`, `n1-l5-004`), not in `n1-lesson-05`. | A Mathematics reviewer should decide whether each is in scope for the Sec 3-entry scholarship test. If yes, add a worked example to the matching lesson. If no, reallocate or replace the questions. |
| C-25 | Batch manifests B001–B003 | All three manifests list `house-rules-v1.json` as their `house_rules` source while declaring prompt `math-question-authoring-v2`. The N2 audit required that new claims "update [their] manifest to house rules v2". | Update the manifest source references to v2 when the batches are regenerated. |

### Low: hint leakage

Stage-two hints may give "an intermediate setup without the final answer". These hints
either state the decisive rounding digit or leave only one trivial operation:

| ID | Stable key | Hint text (stage) | Proposed correction |
| --- | --- | --- | --- |
| C-26 | `n1-l1-018` | "The hundredths digit is 7 and the next digit is 6, so round the 7 upward." (2) | Stop at "Look at the thousandths digit to decide." |
| C-27 | `n1-l1-15` | H1 "The hundredths digit is 8." and H2 "The next digit is 4, so the hundredths digit stays unchanged." | Make H1 conceptual. In H2, name the digit to inspect without stating the outcome. |
| C-28 | `n1-l1-04` | "Check 23, 29, 31 and 37." (2). This lists exactly the four primes, so the answer is a count of the hint. | "Test each odd number from 21 to 39 for divisibility by 3, 5 and 7." |
| C-29 | `n1-l1-14` | "Use the fourth significant digit, 7, to round the third digit." (2). H1 "first three non-zero-place digits" is also unclear wording. | H1: "Count significant figures from the first non-zero digit." H2: "Look at the fourth significant figure." |
| C-30 | `n1-l2-11`, `n1-l3-014`, `n1-l3-015` | H2 gives the unrounded value (7.2228…, 45.2672…, 20.736 "whose fifth significant digit is 6"). For a 2-mark calculator item, that is the answer. | Give the bracket or entry structure instead of the value. |
| C-31 | `n1-l3-030` | H2 gives both products (−10.5 and −10.4). | Give only the first product, or only the method. |
| C-32 | `n1-l1-021`, `n1-l2-023`, `n1-l2-029`, `n1-l3-026`, `n1-l3-028` | H2 evaluates every term ("sqrt(324)=18 and 2.5^2=6.25"; "sum is 2.0 … four measurements"), leaving one obvious operation. | Evaluate only one term in H2. |

### Low: wording, notation and audience

| ID | Stable key(s) | Evidence | Proposed correction |
| --- | --- | --- | --- |
| C-33 | `n1-l3-011` | The stem "A positive integer is written in prime-factor form." does not match the prompt; no integer is given in prime-factor form. | Delete the stem sentence. |
| C-34 | `n1-l2-06`, `n1-l3-012` (titles), `n1-l3-024` | Titles say "Least common multiple" and "Least square multiple". The lessons and other questions use "lowest common multiple". "least positive integer" elsewhere is fine. | Use "lowest common multiple" consistently. |
| C-35 | `n1-l1-01` and other prime-factorisation items | The prompt requires index notation, but the checker accepts `2×2×2×3×3×5`. `2³×3²×5` (Unicode superscripts) is rejected with a format error. | Judgement call: either state that repeated factors are accepted, or require exponents. Mention in the prompt how to type powers (`^`). |
| C-36 | `n1-l4-014` | Uses an unqualified `$80` / `$168`. **Conflict between the standards, reported, not resolved:** house rules v2 (`locale: en-SG`, "Use S$ … in Singapore-dollar contexts"), which the N2 audit applied, would require `S$80`. `LESSON_NOTES_CONTENT_STANDARD.md` says the audience is "secondary-school students across Indonesia and Southeast Asia", that the Singapore syllabus "does not define the learner's country", and that contexts should "work across Southeast Asia". Under that standard, an S$ context is arguably less suitable than a currency-neutral one. The bare `$` satisfies neither standard. | Either write `S$` (following house rules v2) or rephrase without a currency ("has 80 dollars left" or "80 units of money"). The founder or reviewer should settle which standard governs, and house rules v2 should then be updated. The blueprint's course name, "Singapore G3 Mathematics", raises the same question. |
| C-37 | `n1-l2-022`, `n1-l4-002` | Plain-text mixed numbers (`2 1/3`, `7 3/4`, `1 5/6`) are ambiguous for learners outside Singapore and Britain. See C-07. | Typeset as `2\tfrac13`, or use improper fractions. |

## Lesson findings

All seven lessons pass the baseline structural gate: 7 sections, 3 explanations,
2 worked examples with verification notes, 1 deterministic active-recall item and
1 summary each. `course-validate` passes with 0 warnings. Every worked-example and
active-recall answer was recomputed: 91 = 7×13 and 97 prime; 360 = 2³3²5; 84 = 2²·3·7;
HCF/LCM(84, 126) = 42/252; √196 + ∛216 − 3² = 11; HCF(72, 120) = 24; −3 + 4(2 − 5/2) = −5;
−6 + 3(4 − 5) = −9; (3.6² − √49)/2 = 2.98; 17/6 + √5 = 5.069401…; √225 + 2³ = 23;
the ordering −1.6 < −3/2 < −1.45 < −7/5; |1.5 − (−2.75)| = 4.25; −0.65 greatest;
−4 < T ≤ 3; k = −2…3; 5 integers in −3 < n ≤ 2; 38.746 → 38.75; 0.004836 → 0.00484;
0.007846 → 0.00785; the estimate 2; 78 649 → 78 600. **All are correct.**

| ID | Lesson / section | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| L-01 | `n1-lesson-02` (whole lesson) | Medium | Outcome 1.2 is "… squares, cubes, square roots and cube roots **by prime factorisation**". The roots worked example (`roots-example`) evaluates √196 and ∛216 by recall. No section shows pairing or tripling prime factors, which `n1-l1-07` (√1764 "using prime factorisation") requires. | Add a worked example such as √1764 = √(2²3²7²) = 42, or ∛2744 = 14. |
| L-02 | `n1-lesson-01`, `n1-lesson-02`, `n1-lesson-05`, `n1-lesson-06`, `n1-lesson-07` | Medium | Coverage gaps for question types in the bank; see C-24 (a)–(f). | Add a worked example for each method the reviewer keeps in scope. |
| L-03 | `n1-lesson-03` / `number-set-hierarchy`, `classify-numbers-example` | Low | The lesson defines whole numbers as including 0 (so non-negative), then calls −4 "a negative whole number" and says integers include "negative whole numbers". This contradicts its own definition. | Say "the negatives of the counting numbers", and "−4 is a negative integer". |
| L-04 | `n1-lesson-02` / `hcf-lcm-recall` | Low | The feedback uses US spelling ("factorizations") and plain-text powers (`2^3 × 3^2`), while the rest of the lesson uses KaTeX and "factorisation". | Use "factorisations" and `inline_math`. |
| L-05 | `n1-lesson-02` / `squares-cubes-roots` | Low | "For positive numbers, the symbol √x means the non-negative square root" excludes x = 0. | "For x ≥ 0, √x means …". |
| L-06 | `n1-lesson-07` / `rounding-negative-values` | Low | "4.50 to three significant figures is more precise than 4.5" compares a rounding instruction with a number. | "Writing 4.50 (3 s.f.) shows greater precision than 4.5 (2 s.f.)." |
| L-07 | `n1-lesson-07` / `approximation-recall` | Low | The accepted answer `"78600.0"` is a 6-s.f. representation, accepted in a lesson about significant figures. | Remove it. |
| L-08 | `n1-lesson-07` / `significant-figures-example`, `estimation-example` | Low | The worked examples (0.007846 → 0.00785; 19.8 × 0.503 / 4.98) are near copies of `n1-l2-02`(a) (0.007856) and `n1-l3-018` (19.8 × 0.503 / 0.0997). A learner practises the exact example they just read. | Change the numbers in either the lesson or the questions. |
| L-09 | `n1-lesson-05`, `n1-lesson-06` | Low (suggestion) | Both lessons describe visuals (positions, open and filled endpoints) but have no diagram. The non-geometry standard does not require one. | Consider a number-line SVG for each. |

---

## Part 2: Diagrams and graphs

**One diagram is in scope, and it was viewed.** The N1 lessons reference no diagrams.

### `n1-l3-01` → `assets/n1-l3-01-number-line.svg`

The path was resolved from `questions/n1-l3-01.json` → `assets[0].path`. The checksum
matches the declared sha256 (`3e4e7ad2…`), and the declared width and height (760 × 180)
match the SVG.

**Coordinate check (from the SVG source):** the axis is `x1=70 … x2=690` at `y=100`.
Major ticks sit at x = 80, 180, … 680, with labels −3 … 3 at the same x values. That
gives 100 px per unit and x = 380 + 100·v. Minor (half-unit) ticks sit at 130, 230, … 630.
The points are P at x = 130 (−2.5), Q at 330 (−0.5), R at 480 (1) and S at 630 (2.5).
Each point label is centred on its point at y = 72. This matches `generation_spec`
(min −3, max 3, interval 0.5, P/Q/R/S), the stem ("equal intervals"), the solution
(−2.5, −0.5, 1, 2.5) and part (b) (Q = −0.5 < S = 2.5). **No label is swapped or
misplaced, and the scale is uniform.** Nothing extends outside the viewBox or is
clipped.

| ID | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- |
| D-01 | Accuracy (answer reveal) | Medium | `alt_text` ("…with P at negative 2.5, Q at negative 0.5, R at 1 and S at 2.5") and the SVG `<desc>` give the four values part (a) asks for. The web app puts `alt_text` on the `<img>`, so a screen-reader learner hears the answer. | Describe positions as a sighted learner sees them, without values. For example: "Number line from −3 to 3. The integers are labelled, and there is an unlabelled tick halfway between each pair of consecutive integers. P is on the unlabelled tick between −3 and −2, Q is on the unlabelled tick between −1 and 0, R is on the tick labelled 1, and S is on the unlabelled tick between 2 and 3." Update `<desc>` to match. |
| D-02 | Neatness | Medium | Legibility on phones. The asset is displayed at `max-w-full` inside a card with 12-px padding (`math-content.tsx`), so on a 390-px screen it is about 330–358 px wide (scale ≈ 0.44–0.47). In the 390-px render, the integer labels (16 px) appear at about 7 px and the point labels (18 px bold) at about 8 px. Both are below comfortable reading size. | Raise the integer labels to about 28 px and the point labels to about 30 px. Thicken ticks to a 3-px stroke. Alternatively, crop the empty margins (for example `viewBox="40 40 690 120"`) so the drawing scales up. |
| D-03 | Neatness | Low | The arrowhead (`M690 100l-12-7v14z`, spanning x = 678–690) is drawn over the major tick at 3 (x = 680). In the render, the "3" tick is mostly hidden and the arrow tip looks like the endpoint. | Extend the axis to `x2=720`, move the arrowhead to `M720 100l-12-7v14z`, and keep the tick at 680. |
| D-04 | Neatness | Low | There is an arrowhead only at the positive end, so the line looks as if it starts at −3.1. Number lines in the other N1 contexts (lesson text) imply both directions continue. | Add a left arrowhead (`M40 100l12-7v14z`) and start the axis at x = 40, or remove both arrowheads. |
| D-05 | Neatness | Low | The point markers (r = 8, white 3-px stroke) are drawn after the ticks and cover the half ticks under P, Q and S. The integer tick under R shows only as short stubs above and below the dot, which looks like a dashed mark. | Draw the ticks after the circles, or use r = 6 without the white stroke, so every tick stays visible. |

**Root cause:** this is a single hand-authored asset. `kind: "number_line"` is not
produced by `scripts/recalibrate_geometry_content.py`, and
`question_bank/src/question_bank/geometry_validation.py` validates only geometry
diagrams (angles and rays). For a number line, the authoring checks confirm only that
the file exists and its checksum matches. Nothing cross-checks `generation_spec` against
the drawn coordinates, so a mislabelled point would pass. There is no multi-diagram
template pattern in N1. A small number-line validator would close the gap for future
banks: parse major ticks and labels, derive px-per-unit, and confirm each named point's x
against `generation_spec.points`.

**Text-only questions that a diagram would clearly help:** N1 has **no
`diagram_audit.json`**; one exists only for the geometry banks G1, G5 and Secondary 2 G2.
These candidates are from reading the questions:

- `n1-l3-08` and `n1-l2-019`: integers in a compound inequality, with open and filled
  endpoints on a number line.
- `n1-l4-003` and `n1-l4-009`: dividing a directed interval. A diagram would make
  "measured from A" unambiguous.
- `n1-l3-027`: elevator levels. A vertical number line would help.

---

## Root-cause patterns

1. **The batch generator wrote plain-text mathematics** (`codex-offline-n1-v1`): this
   affects all 64 B001–B003 questions (C-07, C-08, C-09). The `latex_fragments_render`
   publication check passes vacuously when no LaTeX is present.
2. **The duplicate scan misses semantic duplicates across encodings** (C-03 to C-06,
   C-14 to C-19): seed questions use KaTeX and batch questions use plain text, so the
   same task looks different to a text-similarity check. Batch generation also reused
   seed tasks and numbers (756, 540, 18/24/30, 168/252, 7.8/5.6, 398/1.98).
3. **Checker parsing** (C-01, C-10, C-11, C-13): spaces are deleted before fractions are
   parsed, "simplest form" is never enforced, and relation answers require a full
   statement the prompt does not ask for.
4. **Outcome allocation was filled to meet counts** (C-20, C-21, C-23): arithmetic tasks
   were placed in 1.5 and 1.6, and difficulty labels were raised on repeated templates to
   fill D4/D5 slots.
5. **Number-line assets have no semantic validator** (Part 2 root cause).

## Not verified

- **Official scope of the ASEAN Scholarship Sec 3-entry test** for bounds, standard form,
  linear inequalities and the divisor-count formula (C-24). This audit checked them only
  against the blueprint outcome titles and the lessons.
- **Rendering on real devices.** Phone legibility was assessed in headless Chromium at a
  390-px viewport with 16-px gutters, not on a physical phone. The SVG specifies Arial;
  Chromium used its default sans-serif substitute, which could shift text widths
  slightly.
- **How learner-facing practice and checkpoint screens show `alt_text`** beyond the
  `<img alt>` in `math-content.tsx`.
- No paid model APIs were called, and no images were committed.
