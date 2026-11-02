# Secondary 1 N3 (Percentage) technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_1/n3/v1/`
(batches B001–B004) and all six N3 lessons (`n3-lesson-01` to `n3-lesson-06`)

**Lesson location:** the N3 lessons are not in an `n3/` course folder. Course metadata
(`backend_resources/courses/g3_math/secondary_1/n1/v1/course.json`, unit `g3-sec1-n3`)
places them in `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n3-lesson-0{1..6}.json`.
Their practice, checkpoint and reserve pools are in `.../n1/v1/question_pools/n3.json`.

**Decision boundary:** this audit only reports findings. It changes no questions, lessons,
manifests, claims or review states, and it records no Mathematics or editorial approval.
The four batches are `ready_for_review`. All 104 questions and six lessons are `draft`. The
review packets contain no decisions. No approvals were found in the repository, so none were
changed.

**Audience note:** the current audience standard is learners across Indonesia and Southeast
Asia preparing for the Sec 3-entry ASEAN Scholarship test
(`docs/plan/LESSON_NOTES_CONTENT_STANDARD.md`). Section 5 lists the places where this
conflicts with the Singapore-specific rules used in the N2 audit.

## 1. Counts

| Item | Checked | Notes |
| --- | ---: | --- |
| Questions | 104 | 109 response parts. Every canonical answer was recomputed with exact rational arithmetic. |
| Lessons | 6 | 12 worked examples and 6 active-recall checks recomputed |
| Diagrams, graphs or charts referenced | **0** | See section 4 |
| Diagrams rendered and viewed | **0** | Nothing to render |
| `diagram_audit.json` for N3 | none | Only the geometry banks (Sec 1 G1, G5 and Sec 2 G2) have one |

Validators run against this branch (read-only):

- `question-bank validate .../n3/v1`: 0 errors, 0 warnings
- `question-bank course-validate`: 0 errors, 0 warnings
- `question-bank authoring-validate`: 0 errors, 0 warnings

The validators pass, but they do not catch the problems in findings C-01, C-02 and L-01.

**Severity scale used:** **Critical**: a learner who answers correctly is marked wrong, or the
answer is wrong. **Major**: blocks a fair assessment (ambiguous task, a duplicate that
undermines a pool, or a standard not actually met). **Minor**: wording, calibration or
polish.

## 2. Answer verification summary

Every canonical answer was recomputed from the prompt alone, before reading the solution. The
script is in the session scratchpad and was not committed. All 109 parts match in magnitude.
All six lesson active-recall answers and all 12 worked-example results are correct. The
exceptions are n3-l3-018 and n3-l3-019. Both are decreases (−3.2% and −5%), but the canonical
answer stores only the size of the change, as positive 3.2 and 5. See C-02.

No `rounded_dp` answer sits near a rounding boundary. Every `exact_numeric` answer is a
terminating decimal. Worked solutions agree with the canonical answers, and no solution uses
an intermediate value that was rounded too early.

## 3. Content findings

### 3.1 Critical

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-01 | 65 percentage-answer parts in the bank, listed below. Also the active-recall checks in n3-lesson-01, -02, -03 and -06 | **Critical** | `checking._fraction` treats a trailing `%` as division by 100. So `"30%"` is read as 0.3, which does not equal the canonical `"30"`. I ran the live checker: n3-l1-001 marks `30` correct and marks `30%` and `0.3` wrong. n3-l2-007 marks `6%` wrong. The numeric input placeholder invites this mistake ("Enter a number, decimal, fraction, or percentage"). After a wrong answer, the practice player shows `canonical_latex` = `30\%`. In the lessons, the active-recall `unit` is `{"canonical": "%", "required": true}`, but `check_answer` ignores `unit`. So `30%` is still marked wrong, and `30 percent` gives a format error. | Choose one approach and apply it to the whole bank before review. **(b) is recommended.** (a) Add `"30%"` to `accepted_answers` for each part. This works, because the accepted value parses to 0.3, but it also accepts a bare `0.3`. That is questionable for an "express as a percentage" task. (b) Change the checker so that, for a response whose `canonical_latex` ends in `\%` or whose `unit.canonical` is `%`, `30` and `30%` are both accepted. Only this option also makes the lessons' `unit.required` setting work. (c) As a fallback, end every prompt with "Give your answer as a percentage, without the % sign". |

C-01 affected parts. Every part whose `canonical_latex` ends in `\%`, 65 parts in all:
l1-001 to -003, -006 to -008, -011 to -013, -016 to -018. l2-001 to -005, -010 to -012,
-018 to -021, -026 to -028. l3-001 to -003, -007 to -012, -015 to -019, -023 to -027, -030.
l4-001 to -003, -004(b), -006, -007, -010 to -015. l5-001, -002(a, c), -003(b), -004, -005(b).
The percentage-point parts (l2-007, -014, -022, -029, l4-004(a), l4-016, l5-002(b)) have
`canonical_latex` without `%`. A learner may still type `6%` or `6 percentage points` on
those, and both are rejected. The out-of-scope v2 bank has four more affected parts, so the
root cause is not limited to v1.

### 3.2 Major

| ID | Stable key(s) | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-02 | n3-l3-012, n3-l3-018, n3-l3-019 (and n3-l3-027) | Major | Each prompt says "Find the overall percentage change". The direction is the key concept here, but the numeric answer cannot capture it. l3-018 (−3.2%) and l3-019 (−5%) store `3.2` and `5`. The live checker rejects `-3.2` and `-5`, even though these are the conventional signed answers. l3-012 stores `2` (an increase). A learner who answers "2" has not shown the direction. | Reword each prompt to name what is asked: "Find the overall percentage decrease" (l3-018, l3-019) and "…increase" (l3-012). Or keep "change", tell learners "enter a decrease as a negative number", and store `-3.2` and `-5`. Either way, make it consistent with the lesson-04 teaching. |
| C-03 | n3-l4-011 | Major | "By what percentage is Asha's new salary **greater than** Bala's new salary?" The answer is 0%: the salaries are equal (1.08x each). The question assumes something false, and the stage-2 hint ("compare 0.9(1.2x) with 1.08x") gives the result away. | Change the numbers so that the result is non-zero. For example, Asha first earns 25% more, then decreases by 10%, and Bala increases by 8%: 1.125x vs 1.08x, giving 4.2% (1 d.p.). Or reword it as "Compare the two new salaries" with a choice of answers. |
| C-04 | 10 practice items that repeat lesson worked examples (table below) | Major | These items use the same numbers and structure as a lesson worked example or explanation. A learner who has just read the lesson can copy the answer, which defeats the point of the practice and checkpoint pools. The worst cases are higher-difficulty items: n3-l4-002 (checkpoint, d4), n3-l4-004 (checkpoint, d4), n3-l4-005 (reserve, d4), n3-l3-017 and n3-l3-004 (d3). | Change the numbers (and, for d4 items, the structure) in the questions, or change the lesson examples. House rule v2 already bans repeating "context, operation pattern and numerical structure" across questions. Extend that rule to lesson examples against the bank. |
| C-05 | Template clusters (table below) | Major | Several clusters repeat one operation pattern with only the numbers changed. Some members sit in the same pool, so a learner meets the same item twice in one checkpoint. Examples: n3-l4-010 and n3-l4-014 are both in `n3-unit-checkpoint`. n3-l3-006 and n3-l3-014 both give **S$270 left from S$600, 45% remaining** in the same lesson-06 practice pool. | Rewrite one member of each pair as a different structure, or at least different numbers (see the table). |
| L-01 | n3-lesson-01 to -06 | Major (standard interpretation) | The lesson standard requires "at least 2,500 authored characters across its teaching sections". `course_validation.lesson_note_depth_shortfalls` counts the length of `json.dumps(section.model_dump())`. That figure includes JSON keys, nulls and full `response` specs. The learner-visible prose and LaTeX in the six N3 lessons is only **1,224 / 1,523 / 1,224 / 1,566 / 1,481 / 1,787** characters (lessons 01 to 06; lesson 03 is the shortest). Each lesson has exactly the minimum six sections, and none has a misconception section. | Reviewers should decide which measure the standard intends. If it means learner-visible text, every N3 lesson needs roughly 1,000 to 1,300 more characters. Good candidates are a misconception check per lesson (wrong denominator, percentage vs percentage point, adding successive percentages) and a third worked example. Change the validator metric so it measures text, not JSON. |
| L-02 | n3-lesson-06 (and the 3.6 bank) | Major | The 3.6 bank assesses simple interest (l2-024), commission (l2-017), GST (l2-025, l3-005, l3-029, l4-005, l5-005), mark-up and profit (l3-030, l4-006, l5-005) and discount. Lesson 06 only works a budget example and a dilution example. "Simple interest", "commission", "GST", "mark-up", "marked price" and "cost price" are never defined. The current standard says to "explain unfamiliar terminology". | Add a short terminology explanation and one worked financial example (mark-up, then discount, then tax) to lesson 06. Explain GST, or replace it with a generic "sales tax". |

C-04 lesson-to-question overlaps:

| Question | Pool | Lesson source | Overlap |
| --- | --- | --- | --- |
| n3-l1-001 | lesson-01 practice | lesson-01 WE1 | 18 of 60 → 30% |
| n3-l2-026 | reserve | lesson-01 WE2 | 45 cm of 1.8 m → 25% |
| n3-l2-003 | lesson-02 practice | lesson-02 WE1 | 54 vs 45 members → 20% |
| n3-l4-002 | **checkpoint** | lesson-02 WE2 | "25% more → what % less?" → 20% |
| n3-l2-004 | lesson-03 practice | lesson-03 WE1 | 84 of 60 → 140% |
| n3-l3-017 | lesson-03 practice | lesson-03 explanation and WE2 | 125% of 120% → 150% |
| n3-l3-004 | lesson-04 practice | lesson-04 WE1 | S$240, +12%, −5% → 255.36 |
| n3-l4-004(a) | **checkpoint** | lesson-04 explanation and WE2 | 64% → 76% = 12 percentage points |
| n3-l1-004 | lesson-05 practice | lesson-05 WE1 | S$64 after 20% discount → 80 |
| n3-l4-005 | reserve | lesson-05 WE2 | 10% discount, then 9% GST, S$196.20 → 200 |

The active recall in lesson-04 ("Decrease 150 by 18%") is also close to n3-l1-009 ("Decrease
150 by 20%"). That is minor.

C-05 template clusters:

| Cluster | Items (outcome, difficulty, pool) | Recommendation |
| --- | --- | --- |
| Part vs whole when one part is k% of the other | n3-l4-001 (3.1 d4, reserve), n3-l4-010 (3.1 d4, checkpoint), n3-l4-014 (3.1 d4, checkpoint) | Keep one. Replace the others with different d4 3.1 structures, such as a part that changes over time or a percentage of a subgroup. |
| Two-stage spending, S$270 left = 45% of S$600 | n3-l3-006, n3-l3-014 (both 3.6 d3, lesson-06 practice) | They work as a contrast pair ("of remainder" vs "of original"), but identical numbers let a learner copy the answer. Change one set of numbers. |
| Fixed fee + percentage surcharge, reversed | n3-l3-005 (GST + delivery), n3-l3-029 (GST + delivery, checkpoint), n3-l3-020 (service charge + delivery) | l3-005 and l3-029 are the same task. Replace one with a different 3.5 structure, for example reversing a decrease and then an increase. |
| Chained "A is p% of B, B is q% of C" | n3-l3-011, n3-l3-017, n3-l3-026 (all 3.3 d3), plus the lesson-03 WE | Keep one. Replace the others with, for example, "A is 160% of B; express B as a percentage of A". |
| "After X is reduced by p%, it equals q% of Y" | n3-l4-012 (checkpoint), n3-l4-015 (reserve) | Change the structure of one. |
| Bare percentage-point subtraction | n3-l2-007, -014 (practice), n3-l2-022, -029 (checkpoint) | Four of the 17 items for 3.4 are a single subtraction. Replace two with items that contrast percentage points with relative change. |
| Express part as % of whole, answer 30% | n3-l1-001, -011, -016, plus lesson-01 WE1 and active recall | Five instances of the same answer in one pool. Vary the answers. |
| Repeated answer values in 3.2 | 20% appears 7 times and 10% appears 5 times across 19 parts | Vary the numbers so a learner cannot guess the answer. |

### 3.3 Minor

| ID | Stable key | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| C-06 | Several items, d2 and above | Minor | House rule v2 says "stage-two hints [give only] an intermediate setup". Several stage-2 hints do all the work except the final division. l3-009 gives both speeds (18 and 20 km/h). l3-016 gives 72 min and the 12-min difference. l3-022 gives 72 and 168. l3-024 gives 1250 and 250. l3-025 gives both areas. l4-007 gives 80 and 120 units. l4-016 gives "60 g of salt in 230 g". l4-002 gives 100 and 125 units. l5-002(c) stage 1 gives "8-point increase with 40%". l1-017 stage 2 says "compare the 10-card difference with 100 cards", which is the answer. l2-007 stage 2 says "Subtract 42 from 48", which is the whole task. | Cut each stage-2 hint back to the setup only. For example, for l3-009 say "find each speed in km/h". Nearly every d1 and d2 stage-2 hint has the form "Calculate a ÷ b, then × 100%". That may be acceptable for guided items, but reviewers should decide. |
| C-07 | n3-l3-016, n3-l3-024 | Minor (difficulty) | Both are labelled d3. The only extra step is a unit change (1 h 12 min → 72 min, "S$1.25 thousand" → 1250). That is d2 work. "S$1.25 thousand" is also unnatural wording. | Move them to d2, or add a real second step. Write S$1250 normally. |
| C-08 | n3-l1-010, n3-l1-021, n3-l1-005 | Minor (outcome) | These are allocated to 3.6 "problems involving percentages", but they are bare "find p% of N" calculations. l1-021 has no context at all. | Give them a real problem context, or accept them as d1 entry items. |
| C-09 | n3-l3-020 | Minor | A "restaurant bill" that includes a "delivery fee" is an inconsistent context. | Write "A food-delivery order costs…". |
| C-10 | n3-l3-022 | Minor | The final sentence adds a condition after the question ("…if all fiction books and the stated non-fiction books are borrowed"), and it reads awkwardly. | Write "All the fiction books are borrowed, and 25% of the other books are borrowed. How many books are borrowed altogether?" |
| C-11 | n3-l3-002 | Minor | "Parcel Q contains 1.5 kg of goods with no packaging included in its stated mass" is hard to read. | Write "Parcel Q contains 1.5 kg of goods (no packaging)". |
| C-12 | n3-l1-004 | Minor | Stage-1 hint "80% of the original price" contains the number 80, which is also the canonical answer. This is a coincidence, but it could mislead a learner. | Change the numbers (this also fixes the C-04 overlap). |
| L-03 | n3-lesson-06 explanation 1 | Minor | "tax is applied to the price specified after any earlier change" is vague. | Write "tax is calculated on the price after any discount". |
| L-04 | n3-lesson-03 explanation 1 heading | Minor | The heading "More than the whole can exceed 100%" repeats itself. | Write "Percentages above 100% are valid". |
| L-05 | n3-lesson-04 | Minor | The lesson shows a successive change as "6.4% above". It never models the wording "overall percentage change" with a decrease, which is the form used in l3-012, -018, -019 and -027. | Add a short note on stating direction. This connects to C-02. |

No incorrect canonical answer, worked-solution result or stated rounding condition was found.

## 4. Diagrams and graphs

**N3 has no diagrams.** No N3 question or lesson references a diagram, graph or chart:

- `assets` is `[]` in all 104 question files and all six lesson files.
- The only content block types are `text`, `display_math`, `inline_math`, `numeric`,
  `explanation`, `worked_example`, `active_recall` and `summary`. None is an image or diagram
  block.
- There are no `.svg` or `.png` files under `question_bank/g3_math/secondary_1/n3/`. No asset
  under `courses/.../n1/v1/assets/` belongs to N3. The `review_packets/*/assets/` folders hold
  only KaTeX files.

So no diagrams were rendered and none were viewed. There are no diagram accuracy or neatness
findings, and none of the diagram-template root-cause analysis
(`scripts/recalibrate_geometry_content.py`, `geometry_validation.py`) applies.

**Text-only questions that might benefit from a diagram.** N3 has no `diagram_audit.json`,
because the standard requires one only for geometry banks, so there are no recorded
decisions to check against. In my judgement, no N3 question *clearly* needs a diagram: every
relationship is stated in the text. These would be optional bar-model additions for
reviewers to consider:

- n3-l4-001, n3-l4-010, n3-l4-014: part and whole when one part is k% of the other
- n3-l5-001: transfer between two containers
- n3-lesson-02 explanation 2 ("Direction changes the denominator"): two bars sharing one
  difference would show why 25% more and 20% less are the same gap

## 5. Conflicts between the N2 audit's Singapore rules and the current audience standard

These are reported, not resolved. N2 audit check 6 and correction 3, together with house rules
v2 (`locale: en-SG`, `currency: SGD`, "Use S$…"), require Singapore/British English and S$.
The current `LESSON_NOTES_CONTENT_STANDARD.md` says the Singapore syllabus "does not define
the learner's country", and asks for "clear international English", explained terminology
and "contexts that work across Southeast Asia". The N3 content shows the conflict in four
ways:

| Item | Where | Under the N2/house rules | Under the current standard |
| --- | --- | --- | --- |
| `S$` currency | 28 questions | Compliant | A learner from Indonesia or another country may not know S$. It may still be justified because the target test is a Singapore admission test. |
| Bare `$` | Lessons 02, 04, 05 and 06 (12 occurrences); `S$` never appears in the N3 lessons | **Non-compliant.** The N2 audit corrected the N2 lessons to S$. | Ambiguous currency. This is inconsistent with the questions under either rule. |
| 9% GST | 5 questions (l2-025, l3-005, l3-029, l4-005, l5-005) and lesson-05 WE2 | Locally accurate | Singapore-specific tax and rate, and never explained (see L-02). |
| "Singapore stamps" | n3-l1-005 | Neutral | The context is centred on Singapore. A regional context would be easy to use. |

The decision needed is: does N3 follow the house rules (S$ everywhere, including lessons) or the
audience standard (a neutral or explained currency and tax)? Whichever is chosen, the N3
lessons and questions must agree. House rules v2 say they are "provisional until founder and
reviewer approval", so the house rules should be updated to match the decision.

No US spellings or other language-variant problems were found. Names (Aisha, Farid, Jia Min,
Nur, Ravi, Lina, Asha, Bala, Hana, Mei, Ben) and contexts are suitable across the region.

## 6. Root-cause patterns

1. **Percentage answers vs the numeric checker (C-01).** The cause is in
   `question_bank/src/question_bank/checking.py` (`_fraction`, `_check_numeric`). `%` is
   always read as ÷100, `NumericResponse.unit` is never consulted, and the authoring pipeline
   never adds `%` forms to `accepted_answers`. It affects 65 parts in v1, 4 in v2 and 4 lesson
   active-recall checks. No validator rule flags a percentage `canonical_latex` that has no
   matching accepted form. A validator check should be added.
2. **Unsigned "percentage change" (C-02).** The prompt template does not store direction in the
   response. There are 4 occurrences.
3. **Lesson examples reused as practice items (C-04).** The lessons and bank were authored at
   the same time (both on 12 October 2026). House rule v2 checks for duplicates only between
   questions, so it missed the 10 overlaps.
4. **Lesson-depth metric (L-01).** `lesson_note_depth_shortfalls` measures JSON size, so a
   lesson with about 1,200 to 1,800 visible characters passes the 2,500-character gate. This
   probably affects other non-geometry lessons too. That was not audited here.
5. **Template reuse within an outcome and difficulty cell (C-05).** The batch generator seems
   to fill each (outcome, difficulty) slot from one structural template. This is clearest at
   3.1 d4, 3.3 d3/d4, 3.4 d2 and 3.5 d3.

## 7. Not verified, or out of scope

- **No diagrams exist, so none were rendered or viewed.** No diagrams were skipped because
  they could not be rendered.
- **Front-end behaviour** was inferred from code (the placeholder text in `practice.py` and
  `canonical_latex` display in `practice-player.tsx`). It was not exercised in a running
  browser.
- **Database review state:** approvals recorded only in PostgreSQL could not be seen. The
  repository has no N3 decisions.
- **`n3/v2`** (4 questions: n3-l3-901, n3-l3-903, n3-l4-902, n3-l4-904) is outside the
  requested `v1` scope and was not audited, apart from noting that C-01 affects it.
- **Calculator flags** were checked only for plausibility. No inconsistency was found that
  needs action.
