# Secondary 1 N5 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_1/n5/v1/`
(batches B001–B004) and the eight N5 lessons, `n5-lesson-01` to `n5-lesson-08`. The lessons are
stored in `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/`, because unit
`g3-sec1-n5` in that folder's `course.json` owns them. No other lesson declares outcomes
5.1–5.8.

**Decision boundary:** this is a technical pre-review, and it is report-only. No question,
lesson, asset, manifest or claim was edited. No Mathematics or editorial approval was recorded,
and no paid model API was called. Its purpose is to let human reviewers spend their time on
judgement calls rather than basic errors.

## Counts

| Item | Count |
| --- | ---: |
| Questions checked | 104: 91 `algebraic_expression` (`symbolic_equivalence`) and 13 `numeric` (`exact_numeric`), across 5.1–5.8 |
| Lessons checked | 8 |
| LaTeX strings parsed with KaTeX | 426 |
| Diagrams, graphs or charts referenced | **0** |
| Diagrams rendered and viewed | 0 (none exist) |
| Maths renders viewed as images | 12 (the corrupted LaTeX strings in finding 3) |

**Review state in the repository:** all four batch manifests are `ready_for_review`, with Mathematics
`pending` and editorial `pending`. All 104 questions are `draft`, revision 1. All eight lessons are `draft`, revision 2,
with `reviewed_by: null`. No N5 content is recorded as approved, so no review state needed to be
preserved. Hosted review records in the database could not be inspected from this environment.

**Authoring provenance:** the manifests record prompt `math-question-authoring-v1` and
house rules v1. The N2 audit introduced house rules v2 after these batches were written.

## Checks performed

- **Canonical answers:** recomputed every answer from the prompt alone, before reading any
  solution. Expressions were compared symbolically with sympy 1.14. All 104 canonical answers
  are mathematically correct.
- **Grading:** ran the production checker (`question_bank.checking.check_answer`, imported by
  `learning_api.postgres_practice` for practice and by `learning_api.progress_service` for
  lesson active recall) on each canonical answer. It was also run on natural equivalent forms:
  the same expression with spaces, with its terms reordered, and simplified or unsimplified
  where the prompt allows.
- **Solutions:** read every hint and worked step against the recomputed answer.
- **Alignment:** checked outcome and difficulty against the blueprint rubric and house rules v2.
- **Duplicates:** compared operation patterns and numbers across the bank and against all
  eight lessons. Pool placement came from `question_pools/n5.json`.
- **Lessons:** checked lesson depth against `LESSON_NOTES_CONTENT_STANDARD.md`.
- **Maths rendering:** scanned every string for control characters. Parsed every LaTeX string
  with KaTeX 0.16.22 (`throwOnError`, strict) and rendered each block in Chromium at a 358 px
  content width (390 px phone minus 16 px gutters). Result: 0 parse errors and 0 overflows. The
  12 strings containing a control character were rendered to PNG and viewed.
- **Repository validators:** `validate`, `course-validate` and `authoring-validate` all pass
  with 0 errors and 0 warnings. Findings 1–5 below pass every validator.

Severity scale:

- **Critical:** blocks release of the topic, because correct learner answers are marked wrong
  at scale.
- **High:** a learner sees a broken or contradictory item, or a checkpoint question is solved
  in the lesson.
- **Medium:** a calibration, alignment or teaching-quality defect.
- **Low:** wording, metadata or consistency.

## Part 1: content findings

### Grading (affects questions and lessons)

| # | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| 1 | All 91 algebraic questions, plus the active recall in `n5-lesson-01`, `-02`, `-04`, `-05`, `-06`, `-07` and `-08` | **Critical** | The checker does not test symbolic equivalence. For `symbolic_equivalence`, `_check_expression` accepts only `answer.strip() == canonical_expression.strip()` or an exact member of `accepted_equivalents`. Anything else falls through to `raise AnswerFormatError("This answer comparison mode is not supported.")`, and that message is shown to the learner. **All 91 items have `accepted_equivalents: []`.** Probing the real checker, **85 of 91** items reject an equivalent correct answer. Examples: `n5-l1-001` rejects `n + 1` and `1+n`; `n5-l1-003` rejects `6*x`; `n5-l2-004` rejects `1.8d+4`; `n5-l2-020` rejects `12a+sn`; `n5-l4-009` rejects `(2x-3y)(3a+2b)`. The remaining 6 are single-term answers where only one natural spelling exists. | Do not release N5 practice or the N5 lesson recall until the checker parses both expressions and compares them symbolically. Items that require a form ("simplest form", "factorise completely", "as repeated addition") need a form constraint in `checker_config`. Listing orderings in `accepted_equivalents` cannot cover the space of correct answers and is not a fix. The defect is in code, so see R1. |
| 2 | `n5-l2-001` | High | The canonical answer is the unsimplified `n+(n+1)+(n+2)`. `3n+3` and `3(n+1)` are rejected. `n5-lesson-01`'s first worked example is this exact question, and it tells the learner to simplify to 3n+3. A learner who follows the lesson is marked wrong. | Make the canonical `3n+3`. Add "in simplest form" to the prompt, as `n5-l3-001` does, or accept both forms once the checker is fixed. |
| 3 | `n5-l3-017` | High | The canonical answer is `2(x+5)-3`. `2x+7`, the simplified form taught throughout 5.6–5.7, is rejected. | Accept `2x+7`, or make it canonical. |
| 4 | `n5-lesson-04` (recall) | High | The prompt says "$2.50 plus $0.80 per kilometre". The canonical answer is `2.5+0.8d`, so `2.50+0.80d`, the form the prompt invites, is rejected, as is `0.8d+2.5`. The feedback says "The fixed fare is 2.50", which disagrees with the canonical form. | Covered by finding 1. Until then, write the prompt values as 2.5 and 0.8, or list `2.50+0.80d`. |
| 5 | `n5-l3-026` (17/4), `n5-l4-006` (17/2) | Low | `exact_numeric` removes spaces before parsing, so the mixed number `4 1/4` is graded as `41/4`, which is silently wrong with no format error. Decimals (4.25, 8.5) are accepted. | Add "Give your answer as a fraction or a decimal" to both prompts. See R4. |

### Questions

| # | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| 6 | `n5-l1-006` | High | The prompt never states the question. The full learner-facing prompt is "A number is represented by *x*." The stem is empty, and the title "Seven less than a number" is not shown to learners as the task. The canonical answer is `x-7`. The item is the second `guided` question in `n5-lesson-01-practice`. | Use "A number is represented by *x*. Write an expression for the number that is seven less than *x*." |
| 7 | `n5-l2-002`, `n5-l2-008`, `n5-l2-010`, `n5-l2-031`, `n5-l3-002`, `n5-l3-016`, `n5-l3-024`, `n5-l4-001`, `n5-l4-005` | High | 14 control characters across 12 solution LaTeX strings. A JSON `\t` escape replaced the backslash and `t` of `\times` and `\text`, leaving `<TAB>imes` and `<TAB>ext`. KaTeX treats the tab as whitespace, so the parse succeeds and `latex_fragments_render` passes. Rendering and viewing all 12 strings at phone width showed what learners see in the worked solution: `6m = 6imesm`, `4imes3a − 4imes5`, `yimesy = y²`, `−3imes2p + (−3)(−7)`, `3imesaimesb = 3ab`, `5imesc = 5c`, `texttens = 10t`, `uextunits = u`, `rextpupilstakers`, `cexthundreds = 100c`, `bexttens = 10b`, and `5/2 imesr(p − q)`. | Replace each tab+`imes` with `\times` and each tab+`ext` with `\text` (written `\\times` and `\\text` in JSON). Add a validator rule that rejects control characters in `latex` fields; see R2. |
| 8 | `n5-l3-014` (5.7), `n5-l3-015` (5.8) | Medium | Semantic duplicate. `5(2a−3)−2(3a+4)` and `3(2a−5)−2(a+4)` have the same structure (expand two brackets, subtract, collect) and the same answer, 4a − 23. They are `challenge` items in consecutive lesson pools (07 and 08). `l3-015` ("expand and simplify") also does not assess 5.8's "extraction of common factors". | Replace `l3-015` with an extraction task, for example "Factorise 18a − 24ab completely" (answer 6a(3 − 4b)). |
| 9 | All 104 items | Medium | Hints are generic outcome templates rather than item-specific. There are only **9 distinct hint pairs** across 104 items, and many do not fit their item. Examples: `n5-l1-005` "Expand 5(x + 2)" gets "Check a factorisation by multiplying the bracket back out". `n5-l1-010` "Simplify 3x + 5x" gets "When subtracting a bracket, change the sign of every term". `n5-l1-002` (x = 4) gets "Use brackets around negative substituted values". `n5-l2-017` (four less than y²), `n5-l3-009` (mean of a, b and c) and `n5-l3-024` (counters) get "Check the place value or spacing between consecutive integers". `n5-l1-003` (6x) gets "Apply the events in the order in which they occur, using brackets where needed". None of these stage-2 hints gives the "intermediate setup" that house rules v2 requires. | Write item-specific hints. Stage 1 should be conceptual; stage 2 should give the first line of working without the answer, for example `n5-l3-005`: "The difference over 5 term intervals is 39 − 19." |
| 10 | `n5-l4-009` (unit checkpoint), `n5-l5-005` (adaptive reserve) | Medium (judgement) | Both are factorisation by grouping, of the form ax + ay + bx + by. `n5-lesson-08` teaches only single common-factor extraction, so learners meet grouping first in the checkpoint. Grouping is commonly placed in the following year (the Singapore Secondary 2 syllabus lists ax + bx + kay + kby), so these items may exceed outcome 5.8. | Either add a grouping section and worked example to `n5-lesson-08`, or replace both items with harder single-factor extractions, for example −12x²y + 18xy² − 6xy. |
| 11 | `n5-l4-012`, `n5-l4-015` (d4); `n5-l5-001` (d5); `n5-l4-006` (d4); `n5-l4-002`, `n5-l4-005` (d4); `n5-l3-027` (d3) | Medium | Difficulty calibration against the rubric and house rules v2 ("Levels 4 and 5 must require method selection…"):<br>• `l4-012` and `l4-015` use the same nth-term-from-two-terms method as `n5-l3-005` (d3).<br>• `l5-001` is `l4-015` plus adding 5n − 2.<br>• `l4-006` is direct substitution.<br>• `l4-002` and `l4-005` are routine notation translations.<br>• `l3-027` only adds an expression that the prompt supplies, xy + 2(x + y). | Replace them, or re-grade with replacements, to keep the blueprint distribution. For example, a d4 nth-term item could ask whether a given value is a term and require a justification. |
| 12 | `n5-l3-008`, `n5-l3-009`, `n5-l3-023`, `n5-l3-024`, `n5-l4-009`, `n5-l5-005` | Low | Mark scheme. The last two solution steps are identical lines, so the learner gets M1 and then A1 for writing the same answer twice. For example, `n5-l3-008` has step 2 `6(2x^2-3x+1)` (M1) and step 3 `6(2x^2-3x+1)` (A1). | Replace the M line with real working, for example `12x^2\div6=2x^2,\ 18x\div6=3x,\ 6\div6=1`. |
| 13 | 21 d1 algebraic and numeric items, e.g. `n5-l1-001`, `n5-l1-020` | Low | Each one-mark solution is a single A1 line with no working. N4 marks the same structure B1. An A mark normally depends on a method mark. | Use B1 for one-mark items, and show one line of working where the operation is not obvious, for example `-2(y-5)=-2y+10` for `n5-l1-020`. |
| 14 | `n5-l3-002`, `n5-l3-004`, `n5-l3-025`, `n5-l4-002`, `n5-l2-009` | Low | `domain_constraints` is empty although the expression divides by a variable (c ≠ 0, n ≠ 0, m, n ≠ 0). In `n5-l2-009`, "An odd integer is represented by 2k + 1" does not say k is an integer. | Fill in `domain_constraints`, and add "where k is an integer" to `n5-l2-009`. |
| 15 | `n5-l4-007` | Low | "How much more Plan A costs than Plan B" gives 0.05m − 7, which is negative for m < 140, where Plan A is the cheaper plan. | Use "Write an expression for the cost of Plan A minus the cost of Plan B." |
| 16 | `n5-l1-005`, `n5-l2-008`, `n5-l2-031` (5.8) against `n5-l1-016`, `n5-l1-020` (5.7) | Low (judgement) | The same task, expanding one bracket, is split across 5.7 and 5.8. | Reviewer decision on the 5.7/5.8 boundary. Consider reserving 5.8 for tasks that move between bracketed and expanded forms in both directions. |
| 17 | `n5-l2-004`, `n5-l2-020`, `n5-l3-004`, `n5-l3-019`, `n5-l4-007`, `n5-l5-004`, `n5-lesson-04` | Low (rule conflict) | These use unqualified `$`. House rules v2 says "Use S$ in learner-facing Singapore-dollar contexts". The current audience standard targets learners across Indonesia and Southeast Asia, where S$ localises the question to Singapore, while a bare `$` is ambiguous. | Content-owner decision: S$, a neutral "dollars", or a regional currency mix. Apply it consistently to questions and lessons. See the standards conflict section. |
| 18 | `n5-l3-016`, `n5-l4-014` against `n5-lesson-01`; HCF in `n5-l2-016`, `n5-l2-023`, `n5-l3-008`, `n5-l3-023`, `n5-l3-031` against GCF/gcd in `n5-lesson-08` | Low (rule conflict) | Terminology is inconsistent between questions and lessons. Questions say "units digit" and "t tens and u units", while the lesson says "ones digit". Question solutions write `\operatorname{HCF}`, while the lesson writes GCF and `\gcd`, and the course's own N1.2 lesson is titled "HCF, LCM…". "Pupils" (`n5-l3-024`) and "trapezium" (`n5-lesson-03`) are British usage. | Choose one term per concept course-wide and gloss the alternative once, for example "highest common factor (HCF), also called the greatest common factor". |

All other items have a correct answer, consistent working and a reasonable outcome label.

### Lessons

| # | Stable key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| L1 | All eight lessons | High | Every lesson's first worked example reproduces a bank question exactly, and several explanations print a question's answer. The pool is shown in brackets.<br>• `-01`: example 1 = `n5-l2-001` (lesson-01 practice).<br>• `-02`: example 1 = `n5-l4-002` (**unit checkpoint**).<br>• `-03`: example 1 = `n5-l3-018` (adaptive reserve); its first explanation substitutes p = −2 into 2p² − 3p + 1, which is `n5-l2-026` (lesson-03 practice).<br>• `-04`: example 1 = `n5-l3-004` (lesson-04 practice, challenge).<br>• `-05`: example 1 = `n5-l3-005` (lesson-05 challenge); its explanation solves 4, 7, 10, 13 → 3n + 1, which is `n5-l1-004` (lesson-05 guided); example 2, matchstick squares 4, 7, 10 → 3n + 1, is `n5-l2-028` (lesson-05 independent).<br>• `-06`: example 1 = `n5-l2-014` (lesson-06 independent).<br>• `-07`: example 1 = `n5-l3-022` (adaptive reserve); example 2 contains all of `n5-l3-007` as an intermediate line (lesson-07 challenge).<br>• `-08`: example 1 = `n5-l3-023` (adaptive reserve); its explanation states `8m²+12m=4m(2m+3)`, which is `n5-l2-023`'s answer (lesson-08 independent). | Change the numbers and contexts in every affected lesson example and explanation so that no practice or checkpoint item is pre-solved. `n5-l4-002` is the priority, because it is a checkpoint item. |
| L2 | `n5-lesson-07` against `n5-l3-022` | Medium | The lesson says `(15−x)/3` and `5 − x/3` are both acceptable final forms. The question accepts only the string `(15-x)/3`. | Covered by finding 1. Until then, list `5-x/3`. |
| L3 | `n5-lesson-03` | Low | The first worked example's verification note is circular: "Evaluating 3² first gives 39. Substitution into the original formula with a calculator produces the same value." | Verify by an independent route, for example t(u + at/2) = 3(4 + 9) = 39. |
| L4 | `n5-lesson-05` | Low | The visual-pattern explanation and worked example 2 (joined squares) are described only in words. A learner has to picture which side is shared. | Add the first three stages as a deterministic SVG. See the diagram opportunities below. |

Depth: all eight lessons have seven sections (three explanations, two worked examples, one
recall and one summary). Their prose ranges from 2,739 to 3,272 characters, which meets the
baseline even when measured as prose rather than validator JSON. All lesson arithmetic and
verification notes are otherwise correct.

## Part 2: diagrams and graphs

**This topic has no diagrams, graphs or charts.** None of the 104 questions has an `assets` entry or an image or diagram block. The only block types are `text`, `inline_math` and `display_math`. All eight lessons have `assets: []`, and their sections contain only text and maths blocks. No N5 SVG exists in the course `assets/` folder or the bank. Diagrams checked: 0. Diagrams viewed: 0. The geometry renderer templates in `scripts/recalibrate_geometry_content.py` and `question_bank/src/question_bank/geometry_validation.py` do not apply.

The N5 bank has no `diagram_audit.json`. Text-only items where a figure would clearly help, offered for a later recommendation:

- `n5-lesson-05` and `n5-l2-028` (joined matchstick squares), `n5-l3-012` (tile pattern),
  `n5-l3-028` (chain of triangles) and `n5-l4-015` (border tiles): stages 1–3 of each pattern.
  The 5.5 outcome explicitly concerns *recognising* patterns, and the words alone leave the
  shared-edge structure for the learner to imagine.
- `n5-l4-011` (frame extending 3 cm beyond every edge): a labelled x by y rectangle inside an
  (x + 6) by (y + 6) rectangle. This prevents the common x + 3 misreading.
- `n5-l2-012` (garden with sides x + 3 and x) and `n5-l3-027` (lawn and path): labelled
  rectangles.

## Root-cause patterns

- **R1, the `symbolic_equivalence` checker is a string match** (finding 1). The cause is in
  `question_bank/src/question_bank/checking.py::_check_expression`. It affects all 91 N5
  algebraic items, 7 N5 lesson recall checks, 9 Secondary 1 N6 items and 88 Secondary 2 N5
  items: **188 bank items in total, all with empty `accepted_equivalents`**. The blueprint
  publication check `canonical_and_accepted_answers_pass_checker` cannot catch it, because it
  feeds the canonical string back to itself. Findings 2–4 and L2 are local symptoms of it.
- **R2, LaTeX escape corruption is not caught.** At least one authoring path wrote `\t` (an
  escape) where `\\t` (a literal backslash and t) was intended. KaTeX accepts the result, so
  `latex_fragments_render` passes. The defect affects 9 questions and 12 strings in N5 and 0
  in N4. A validator rule rejecting `[\x00-\x08\x0b-\x1f\t]` in `latex` fields would catch it
  catalogue-wide. Similar `\b` and `\f` corruptions would not even be visible as text:
  `\frac` would become a form feed plus `rac`.
- **R3, template hints and thin mark schemes from the v1 executor.** The 9 hint pairs
  (finding 9), single-line A1 solutions (finding 13) and duplicated final lines (finding 12)
  are uniform across batches, which points to the authoring generator rather than
  item-by-item error. A v2 regeneration of the hints and solutions only, keeping the verified
  prompts and answers, would clear findings 9, 12 and 13 together.
- **R4, `exact_numeric` parses mixed numbers as concatenated digits** (finding 5): `4 1/4`
  becomes `41/4`. This is the same defect recorded in the N4 audit.
- **R5, lesson examples copied from the bank** (L1). All eight lessons reuse bank items
  exactly. Lesson authoring should draw its examples from a reserved list that the bank does
  not use.

## Standards conflict for reviewers

The N2 audit model and house rules v2 call for locale `en-SG`, "Singapore/British English" and
S$ currency. The current `LESSON_NOTES_CONTENT_STANDARD.md` says the Singapore syllabus is "a
calibration and coverage reference" only, and that learner content should use "clear
international English, explain unfamiliar terminology and use contexts that work across
Southeast Asia". The blueprint's `course` field still reads "Singapore G3 Mathematics". In N5
the conflict appears in currency (finding 17) and in terminology: HCF against GCF, units against
ones, pupils, trapezium (finding 18). This audit does not choose between the rules. The content
owner should decide which governs learner-facing text and record the decision in house rules v3.

## Not verified

- Hosted review state in the database. Only repository files were inspected.
- Rendering with the web app's KaTeX version. `apps/web` depends on `katex ^0.18.7`, but
  rendering here used the vendored 0.16.22. Whitespace handling of a tab character is the same
  in both, but the screenshots were produced with 0.16.22.
- Whether the web client normalises algebraic input before calling the API. No normalisation
  was found in `apps/web/src` or `learning_api`; the raw answer string reaches `check_answer`.
- Whether these items match the actual ASEAN Scholarship test format. No source paper for that
  test is in the repository.
- Cross-bank semantic duplicates beyond `authoring-validate`'s exact and near-duplicate scan,
  which reported 0.
