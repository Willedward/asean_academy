# Secondary 2 G4 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_2/g4/v1/`
(batches B001–B004) and all three G4 lessons, `g4-lesson-01` to `g4-lesson-03`, with every
diagram those files reference

**Decision boundary:** this is a report-only technical pre-review. It does not record any
Mathematics or editorial approval. No question, lesson, SVG, manifest, pool or claim was
changed. Review states were left as they are: all 104 questions are `draft`, all four batch
manifests are `ready_for_review` with Mathematics and editorial review `pending`, and all three
lessons are `draft`.

**Standards applied:** the model is `docs/plan/N2_CALIBRATION_PRE_REVIEW_AUDIT.md`. The current
standards are `docs/plan/LESSON_NOTES_CONTENT_STANDARD.md` and
`docs/plan/GEOMETRY_CONTENT_STANDARD.md`. `backend_resources/question_bank/authoring/house-rules-v2.json`
is quoted where the N2 audit relies on it.

## Summary for reviewers

The bank and course validators both pass with no errors, but the content is not ready for
human review. The main problems, in priority order:

1. **One wrong answer key.** `g4-l2-529` marks 55, 72, 89 as right-angled. In fact
   55² + 72² = 8209, but 89² = 7921. The question is in the `g4-lesson-02-practice` pool, so a
   learner who answers correctly is marked wrong.
2. **Diagrams give away answers.** 56 of the 104 question diagrams are critical:
   - all 28 single-answer outcome 4.1 questions print the value the learner must find;
   - all 28 outcome 4.2 "is it right-angled?" diagrams draw a right-angle marker. This gives
     the answer away in the 19 right-angled cases and contradicts it in the 9 that are not
     right-angled.
3. **Angle arcs are at the wrong corner.** In all 34 diagrams with an angle arc, the arc and its
   label are drawn at the right angle instead of at the acute angle. The template also always
   draws the acute angle at about 29.9°, so 22 diagrams show a clearly different angle from the
   one stated (for example, 60° drawn as about 30°).
4. **Sine and cosine are missing.** Outcome 4.3 covers sine, cosine and tangent. All 34 of its
   questions, and every worked example and recall check in `g4-lesson-03`, use tangent only.
5. **Five checkpoint items test the wrong outcome.** Five of the eight outcome 4.2 items in the
   unit checkpoint are forward Pythagoras calculations, which belong to outcome 4.1.
6. **Difficulty labels overstate many items.** Several level 4–5 items are routine one- or
   two-step tasks.
7. **Wording problems run through the whole bank.** Every prompt opens with an irrelevant,
   template-generated sentence, and many contexts are incoherent or implausibly sized.

Most of the diagram defects come from one fixed template. Correcting the renderer and its
metadata would clear 104 diagram rows at once (see *Root-cause patterns*).

## Counts

| Item | Count |
| --- | ---: |
| Questions checked | 104 (35 outcome 4.1, 35 outcome 4.2, 34 outcome 4.3) |
| Lessons checked | 3 (`g4-lesson-01`, `g4-lesson-02`, `g4-lesson-03`) |
| Diagrams referenced and checked | 107 (104 question SVGs + 3 lesson SVGs) |
| Diagrams rendered to PNG and viewed | **107 of 107** |
| Canonical answers recomputed in code | 104 of 104, plus all 9 lesson worked-example and recall answers |
| Canonical answers found wrong | 1 (`g4-l2-529`) |
| Questions with no diagram | 0. G4 has no `diagram_audit.json` (see C17) |

### Where the lessons are

The three G4 lessons are not stored in a `g4` folder. They were found through the unit
`g3-sec2-g4` in `backend_resources/courses/g3_math/secondary_2/g2/v1/course.json` and live in
that course's folder:

- `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/g4-lesson-0{1,2,3}.json`
- assets: `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/g4-lesson-0*.svg`

A search of every JSON file under `backend_resources/courses/g3_math/secondary_2/` for the G4
lesson keys found no other copies. The question pools are in `question_pools/g4.json` in the
same folder.

## Method

- **Answers.** Each canonical answer was recomputed in Python from the numbers in the prompt
  before reading the solution, using `math.hypot`, `tan`, `atan` and decimal half-up rounding
  for `rounded_dp`. Each worked solution's arithmetic was also checked separately, including
  every `a²+b²=…, c²=…` pair. Marks were checked to sum correctly.
- **Answer checker.** The comparison rules in `question_bank/src/question_bank/checking.py`
  were read to see which learner inputs are accepted.
- **Diagrams.**
  - Every SVG was rendered with the preinstalled Playwright Chromium into the session
    scratchpad, outside the repository. Each was rendered twice: at its native viewBox, and at
    390 CSS px wide at 2× pixel density to simulate a phone.
  - All 104 question diagrams were viewed in 3×3 contact sheets at about 55% scale. The three
    lesson diagrams and a sample of question diagrams (`g4-l2-501`, `g4-l2-506`, `g4-l4-504`,
    and `g4-l3-506` at phone width) were also viewed at full size.
  - The SVG source of every diagram was parsed to check the path coordinates, label positions
    and visible text.
  - No rendered image was committed.
- **Validators run, for reference only:**
  - `question-bank validate <bank>`: valid, 0 errors, 0 warnings.
  - `question-bank course-validate <course>`: valid, 0 errors, 0 warnings.
  - `question-bank authoring-validate <bank>`: `duplicate_count` 0. Its only error is the
    expected `learning_blueprint_coverage` error, which appears when one bank is validated on
    its own.

  None of these validators caught the wrong key, the answer leaks or the misplaced angle arcs.
- **Duplicates.** A semantic duplicate scan grouped questions by template and sorted numbers,
  after removing the template-generated opening sentence. Side triples were also grouped by
  primitive Pythagorean triple.

---

## Part 1 — Content findings

Severity scale:

- **critical:** a learner is marked wrong for a correct answer, or the item cannot assess its
  target;
- **major:** wrong or misleading mathematics, a gap in outcome coverage, or a misallocated
  outcome;
- **minor:** wording, format or rating problems that reduce quality;
- **low:** for the reviewer's judgement.

### C1 — Wrong canonical answer · critical

- **Key:** `g4-l2-529` (4.2, difficulty 2)
- **Evidence:**
  - The prompt gives sides 55 cm, 72 cm and 89 cm.
  - Recomputed: 55² + 72² = 3025 + 5184 = 8209, but 89² = 7921. The triangle is not
    right-angled, so the answer is **0**.
  - The stored `canonical_answer` is `"1"`. The stored solution even displays
    `55^2+72^2=8209, 89^2=7921` and then boxes `1`.
  - The question is in `g4-lesson-02-practice`.
  - The same false triple (55, 72, 89) was also used for the diagram of `g4-l3-508` (see D6).
    The generator appears to have treated 55-72-89 as a Pythagorean triple. 89 does belong to
    the triple 39-80-89, and 55 to 48-55-73.
- **Correction:** either set the canonical answer to `0` and box `0` in the solution, or keep
  the answer `1` and change the sides to a true triple. For example, 65, 72, 97 works:
  65² + 72² = 9409 = 97². That triple does not repeat any other item.

### C2 — Outcome 4.3 has no sine or cosine · major

- **Keys:** all 34 outcome 4.3 questions, and `g4-lesson-03`
- **Evidence:**
  - The outcome reads "use of sine, cosine **and** tangent".
  - No question file contains sine or cosine. Every 4.3 item is one of:
    - tan 45° (7 items);
    - opposite = adjacent × tan (10);
    - tan⁻¹(opposite/adjacent) (10);
    - elevation with tan (6);
    - a two-position problem with tan (1).
  - The lesson defines sin and cos, but its two worked examples and its recall check all use
    tan.
  - No item gives a hypotenuse together with an angle, or asks for an angle from a hypotenuse.
- **Correction:**
  - Re-author at least a third of the 4.3 allocation so that choosing the ratio matters. For
    example:
    - a ladder or ramp with a given hypotenuse and angle (sin or cos);
    - finding an angle from hypotenuse and adjacent (cos⁻¹);
    - a mixed set where learners must choose among sin, cos and tan.
  - Add a sine or cosine worked example and recall check to `g4-lesson-03` (see L2).

### C3 — Five outcome 4.2 items assess outcome 4.1 · major

- **Keys:** `g4-l4-503`, `g4-l4-506`, `g4-l4-510`, `g4-l4-514`, `g4-l4-515` (4.2, difficulty 4,
  titled "Complete a right-angled specification")
- **Evidence:**
  - Each prompt states that the angle between two given sides "must be 90°" and asks for the
    hypotenuse. That is forward Pythagoras (outcome 4.1), not deciding from three sides whether
    a triangle is right-angled.
  - All five are in `g4-unit-checkpoint`, so 5 of the checkpoint's 8 outcome 4.2 items do not
    test 4.2.
  - This is the same failure the N2 audit corrected in `n2-l1-017` and others, and it is what
    the v2 house rule "Make the task itself assess its declared primary outcome" forbids.
- **Correction:** rewrite each as a converse task with genuine method selection, for example:
  - give three candidate lengths for the third side and ask which one makes the frame
    right-angled, with justification; or
  - give a frame whose sides almost form a right triangle and ask whether the largest angle is
    acute, right or obtuse.

  Alternatively, reallocate them to 4.1 and author five new 4.2 difficulty-4 items.

### C4 — Difficulty does not match the rubric · major

- **Keys and evidence:**
  - **4.2 converse items** at difficulty 1 (`l1-503`, `-504`, `-509`, `-510`, `-514`, `-518`,
    `-519`), difficulty 2 (`l2-504`, `-505`, `-511`, `-512`, `-518`, `-520`, `-527`, `-528`,
    `-529`) and difficulty 3 (`l3-503`, `-504`, `-505`, `-511`, `-512`, `-513`, `-519`,
    `-520`, `-521`, `-527`, `-528`) all use one identical template and differ only in their
    marks (1, 2 or 3). For example, 45-60-75 is difficulty 1 in `l1-503` and difficulty 2 in
    `l2-518`.
  - **Difficulty 3** `tan⁻¹(o/a)` (`l3-506` … `l3-531`) and the rectangle-diagonal items
    (`l3-501` …) are one-step routine tasks (difficulty 2).
  - **Difficulty 4** cable items (`l4-501`, `-502`, `-505`, `-509`, `-513`) are "hypotenuse
    + 2" (difficulty 2–3).
  - **Difficulty 5** perimeter items (`l5-501`, `l5-503`) need only a subtraction for the
    assessed answer, and the verification step is never captured. The difficulty 5
    composite-route items (`l5-502`, `l5-504`) are diagonal + addition (difficulty 3).
  - Only `g4-l5-505` (two observation points) fits difficulty 5.
  - These are the items that v2 rule "Levels 4 and 5 must require the method selection,
    constraints, justification or sustained synthesis" targets.
- **Correction:**
  - Re-rate each item to the rubric, or rewrite it to meet its level.
  - Example rewrites for difficulty 4–5: unknown sides expressed algebraically, such as
    (x, x+7, x+8); a two-stage 3D diagonal; a choice between a right-angle test and an
    acute/obtuse classification; elevation and depression combined.
  - Separate difficulty 1, 2 and 3 converse items by task structure rather than by marks. For
    example: difficulty 1, sides given in order; difficulty 2, sides out of order and in mixed
    units; difficulty 3, find which side length would make the triangle right-angled.

### C5 — The 4.2 response format cannot capture the required justification · major (judgement call)

- **Keys:** all 28 converse items listed in C4
- **Evidence:**
  - "Enter 1 if it is right-angled and 0 if it is not" is a binary guess with a 50% chance of
    being right, yet it carries up to 3 marks (M2 A1).
  - `g4-lesson-02` §2 and §6 say "show both numerical totals" and "Write the side ordering,
    both square calculations and a conclusion", but the response captures only the conclusion.
    Method marks therefore cannot be awarded independently.
- **Correction:** use a structured response. Either:
  - part (a) enter a² + b² for the two shorter sides; part (b) enter c²; part (c) the 0/1
    classification; or
  - ask for the value of a² + b² − c² and its sign interpretation.

  Reviewers should decide whether 0/1 entry is acceptable at all for difficulty 2–3.

### C6 — Stems presuppose the answer · major

- **Keys:** all 28 converse items, and `g4-l5-501` and `g4-l5-503` ("verify that the triangle
  is right-angled")
- **Evidence:** every stem begins "Use the labelled **right-triangle** schematic". For a
  question that asks whether the triangle is right-angled, the stem states the answer. For the
  9 non-right cases (C1 plus the eight with answer 0), it states something false.
- **Correction:** change the stem to "Use the labelled triangle. The diagram is not drawn to
  scale." and fix the diagrams as in D2, D3 and D8.

### C7 — Semantic duplicates and low numerical variety · minor

- **Evidence:**
  - **Exact repeats** (same template and same numbers, only the opening sentence and context
    changed):

    | First item | Repeat | Sides |
    | --- | --- | --- |
    | `g4-l1-503` | `g4-l2-518` | 45-60-75 |
    | `g4-l1-504` | `g4-l2-519` | 60-63-87 |
    | `g4-l1-509` | `g4-l2-527` | 48-55-74 |
    | `g4-l1-510` | `g4-l2-528` | 51-68-85 |
    | `g4-l2-505` | `g4-l3-519` | 17-144-145 |
    | `g4-l2-512` | `g4-l3-527` | 75-100-125 |

    `authoring-validate` reported `duplicate_count: 0`, because the varying opening sentence
    defeats the near-prompt detector.
  - **Same answer, same structure:** `g4-l3-507`, `-522`, `-523` and `-530` are all multiples
    of 3-4-5 and all give θ = 36.9°. `g4-lesson-03` worked example 2 (9 and 12 → 36.9°) is the
    same again.
  - **Triple reuse:** 29 question diagrams use a multiple of 3-4-5. Other triples recur too:

    | Triple | Diagrams |
    | --- | ---: |
    | 20-21-29 | 6 |
    | 8-15-17 | 5 |
    | 5-12-13 | 4 |
    | 24-143-145 | 3 |
    | 7-24-25 | 3 |

    Several items reuse the same triple across templates, for example 24-143-145 in `l1-507`,
    `l2-524` and `l3-528`.
  - Under the v2 rule, repeating "context, operation pattern and numerical structure" is
    disallowed.
- **Correction:**
  - Replace one item in each exact pair.
  - Give the four 36.9° items different angles.
  - Draw from a wider set of triples (for example 13-84-85, 33-56-65, 39-80-89, 65-72-97,
    which the bank does not use yet) and from non-integer cases (√ answers to 1 d.p. or 3 s.f.).
  - Extend the duplicate detector to compare `(template, sorted numbers)` after stripping the
    opening sentence.

### C8 — Hint leakage · minor

- **Keys and evidence:**
  - **tan 45° items** `g4-l1-505`, `-506`, `-511`, `-515`, `-516`, `-520`, `-521`: hint 2 says
    "Use tan 45° = 1". With the opposite side given, that gives x = opposite immediately, so
    the 1-mark answer is revealed.
  - `g4-l5-501` and `g4-l5-503`: hint 2 says "Calculate 108 − 27 − 36" (and "84 − 21 − 28").
    That is the entire computation for the only assessed answer.
  - **Pattern (low):** the stage 2 hint of every hypotenuse, missing-side, diagonal, cable and
    specification item writes out the full final expression, for example
    "Evaluate the square root of 5² + 12²". These hints do not state the number, so they are
    within the letter of the v2 hint rule. But together with the diagram leaks (D1), they leave
    nothing for the learner to do.
- **Correction:**
  - tan 45°: hint 2 should be "Write tan 45° as a fraction using the opposite and adjacent
    sides".
  - Perimeter items: hint 2 should be "Use the perimeter to write an equation for x, then
    compare the squares".
  - Elsewhere, limit hint 2 to the setup equation (for example `c² = 5² + 12²`) rather than the
    final evaluation.

### C9 — Template-generated wording and incoherent contexts · major (editorial pattern)

- **Keys:** all 104 questions
- **Evidence:**
  - Every prompt opens with a sentence of the form "<team> noted <site condition> while
    preparing a replacement frame." Examples: "Survey crew noted salt exposure near the coast…".
    It has no mathematical role, adds reading load for second-language learners, and often
    clashes with the object named next: a "replacement frame" for a "volleyball court marking",
    a "community garden plot" or a "drainage inspection route".
  - Other incoherent phrases:
    - "A triangular support at the market canopy support" (`l3-503`);
    - "An inspection route at the drainage inspection route" (`l5-504`);
    - "a vertical tower at the emergency radio tower" (`l4-516`);
    - "An inspection route at the training-camp flagpole crosses a rectangular floor"
      (`l5-502`);
    - "Two observation points … at the recycling-centre conveyor … with a vertical mast"
      (`l5-505`);
    - "From an acute 45° angle in a right-triangle model of the library staircase" (`l1-520`).
  - Implausible sizes:
    - a 145 m "safety brace" in a marine laboratory pier (`l2-524`);
    - a 41 m brace in a "laboratory equipment stand" (`l2-508`);
    - a 35 m brace in a "school robotics platform" (`l2-503`), which also appears as
      24 m × 32 m in `l3-526`;
    - a 20 m × 21 m "rectangular section of the weather-sensor mast" (`l3-516`);
    - a 5 cm × 12 cm panel for a "harbour access ramp" (`l1-501`);
    - a 34 m brace in an "airport luggage frame" (`l2-510`).
- **Correction:**
  - Remove the opening sentence from all 104 prompts.
  - Rewrite each context so the object, its size and its unit agree (for example, a ramp
    brace in cm, a building diagonal in m).
  - Check one sentence per item for coherence.

### C10 — Missing units and answer-format instructions · minor

- **Keys and evidence:**
  - `g4-l4-504`, `-507`, `-508`, `-511`, `-512`, `-516` ("Find the tower height correct to 1
    decimal place") and `g4-l5-505` ("Find the mast height…") give no unit.
  - The ten θ items `g4-l3-506` … `g4-l3-531` do not say "Enter the number only". If a learner
    types `41.1°`, `_fraction()` in `checking.py` raises an answer-format error.
- **Correction:**
  - Append "in metres" to the height prompts.
  - Append "Enter the number of degrees only" to the angle prompts, or strip a trailing `°` in
    the checker.

### C11 — Strict `rounded_dp` on exact integers · low (judgement call)

- **Keys:** `g4-l2-513` (15.0), `g4-l2-523` (7.0), `g4-l2-522` (5.0), `g4-l4-504` (29.0),
  `g4-l5-505` (34.0)
- **Evidence:**
  - `checking.py` requires at least 1 decimal place for `rounded_dp`, so `15`, `7`, `5`, `29`
    and `34` are rejected.
  - The prompts do say "correct to 1 decimal place", so this is defensible. However,
    `g4-l2-513` and `g4-l2-523` are tan 45° items whose exact answers are integers. They also
    duplicate the difficulty 1 tan 45° items.
- **Correction:** replace the two tan 45° difficulty 2 items with non-45° angles. For the rest,
  reviewers decide whether to add the integer forms to `accepted_answers`.

### C12 — Rounding boundary · low

- **Key:** `g4-l3-531`
- **Evidence:**
  - tan⁻¹(16/63) = 14.25003°. The canonical answer 14.3 is correct.
  - However, a learner who rounds the angle to 2 d.p. first gets 14.25, and a calculator using
    round-half-to-even gives 14.2.
- **Correction:** choose sides whose angle is not within 0.001° of a rounding boundary.

### C13 — Generic solutions · low

- **Keys:** all difficulty 2–5 items, and the difficulty 1 converse items
- **Evidence:**
  - Every M step reads "Select and apply the right-triangle relationship."
  - Converse solutions box `1` or `0` without stating the conclusion in words.
  - Difficulty 1 converse solutions have no conclusion at all.
  - `g4-lesson-02` §6 asks learners for "a conclusion linked to equality or inequality".
- **Correction:** name the relationship in each M step, and end converse solutions with "equal,
  so right-angled (right angle opposite the c-cm side)" or "not equal, so not right-angled".

### C14 — Conflict between the N2 rules and the current audience standard · for reviewer decision

- **Evidence:**
  - **N2 rules:** the N2 audit checks "Singapore/British English, unit wording and currency
    notation", and `house-rules-v2.json` sets `locale: en-SG`,
    `language_variant: Singapore/British English` and `currency: SGD`.
  - **Current standard:** `LESSON_NOTES_CONTENT_STANDARD.md` defines the audience as "students
    across Indonesia and Southeast Asia". It treats the Singapore syllabus as "a calibration
    and coverage reference" and asks for "clear international English" with contexts that
    "work across Southeast Asia".
  - **What G4 contains:**
    - The learner-facing text uses British spellings ("harbour" ×3, "centre" ×3, "metres"),
      which are acceptable in international English.
    - G4 has no currency.
    - No Singapore-specific terms were found.
    - The non-learner metadata is Singapore-specific: `blueprint.json` has
      `course: "Singapore G3 Mathematics"`, and its style references are Singapore school
      papers.

  So G4 shows no learner-facing conflict yet, but the two rule sets still disagree. G4's
  manifests cite `house-rules-v1.json` and prompt `math-question-authoring-v1`, not v2.
- **Correction:** none proposed. Reviewers should decide whether house rules v2 should move to
  an international-English locale, and whether to keep the Singapore labels in bank metadata.

### C15 — Correct items

All other canonical answers recomputed exactly, and every worked-solution value and mark total
is consistent:

- 7 hypotenuse items;
- 11 missing-side items;
- 27 other converse items;
- 10 diagonal items;
- 5 cable items;
- 5 specification items;
- 7 tan 45° items;
- 10 tan items;
- 10 tan⁻¹ items;
- 6 elevation items;
- 2 perimeter items, both confirmed right-angled;
- 2 route items;
- the two-position item: h = 20 / (1/tan 35° − 1/tan 50°) = 33.953 → 34.0.

### Lesson content findings

All lesson answers were recomputed:

- **L1:** 9-12 → 15; 5-13 → 12; 8-15 → 17.
- **L2:** 676 = 676; 289 ≠ 324; 1369 = 37².
- **L3:** 7.5 tan 28° = 3.988 → 3.99; tan⁻¹ 0.75 = 36.87°; tan⁻¹ 1 = 45°.

All three lessons pass `course-validate`. Each has 8 sections, 2 worked examples, 1 active
recall check, 1 summary and 1 diagram, which meets both the baseline and the geometry gate.

| ID | Lesson | Severity | Evidence | Proposed correction |
| --- | --- | --- | --- | --- |
| L1 | `g4-lesson-03` §5 "Angles of elevation and depression" | major | "Parallel horizontal lines make the corresponding acute angles equal." The angle of elevation from A to B equals the angle of depression from B to A because they are **alternate** angles, not corresponding angles. | Replace with "…make the angle of elevation from one point equal to the angle of depression from the other (alternate angles)." |
| L2 | `g4-lesson-03` §3, §4, §7 | major | Both worked examples and the recall check use tangent only. Outcome 4.3 explicitly includes sine and cosine (see C2). | Add a worked example with a hypotenuse, for example a 6 m ladder at 70° to the ground, height = 6 sin 70° = 5.64 m. Add an angle found with cos⁻¹. Make the recall check require choosing the ratio. |
| L3 | `g4-lesson-03` §4 | minor | The worked example 9/12 → 36.9° repeats the structure and answer of four practice items (C7). | Use a different triple or non-triple data in the example or the items. |
| L4 | `g4-lesson-02` §2 / §6 compared with the bank | minor | The lesson requires both square totals and a reasoned conclusion, but every 4.2 item accepts only 0/1 (C5). | Align the response design with the lesson, or soften the lesson wording. |
| L5 | `g4-lesson-01` | — | No content error found. | — |

---

## Part 2 — Diagram findings

### Finding definitions

The template has fixed coordinates:

- vertices A(170, 320) at the right angle, B(170, 90) at the top and C(570, 320) at the
  base-right;
- label slots for the vertical leg at (116, 210), the base at (350, 356) and the hypotenuse at
  (378, 188);
- an optional angle arc `M210 320 A40 40 0 0 1 232 285`, with its label at (226, 300).

The coordinates below refer to that template.

| Code | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- |
| **D1** | accuracy | critical | The required answer is printed on the figure. The hypotenuse items show the hypotenuse (for example 5, 12, **13** in `l1-501`). The missing-side items show the missing leg (for example 12, **16**, 20 in `l2-501`). The diagonal items show the diagonal (for example 11, 60, **61** in `l3-501`). | Replace the unknown's label with its variable (`c`, `b`, `d`), as `l4-503` already does with `x`. Add `forbidden_visible_labels: ["<answer>"]` to each `generation_spec` so that `_answer_leak_issues` enforces it. |
| **D1b** | accuracy | major | The figure prints the hypotenuse, which is the intermediate result that the answer is built on (answer = label + 2 m, or label + corridor length). Examples: `l4-501` shows 70, answer 72; `l5-502` shows 58, answer 98. | Label the hypotenuse `c` or `d`. For the cable items, also draw the 2 m allowance; for the route items, draw the corridor segment. |
| **D2** | accuracy | critical | A converse test of a triangle that is right-angled draws a right-angle marker, which states the answer. The stem also calls the figure a "right-triangle schematic" (C6). | Remove the marker path `M170 286 L204 286 L204 320` from every outcome 4.2 test figure. Draw a general triangle, for example `M170 320 L250 90 L570 320 Z`, so that the right-angled and non-right cases look alike. Update the alt text. |
| **D3** | accuracy | critical | A triangle that is **not** right-angled is drawn with a right-angle marker and labelled as a right triangle. This contradicts the correct answer and misleads learners. 8 items have answer 0, plus `g4-l2-529`, whose correct answer is 0. | Apply the D2 fix. |
| **D4** | accuracy | major | The angle arc and its degree or θ label are drawn at the **right-angle vertex A**: the arc starts 40 px right of A, and its end (232, 285) is 71 px from A, not 40. They should be at the acute reference vertex. Relative to the arc as drawn, there is no "opposite" or "adjacent" side. The `g4-lesson-03` diagram puts θ at the correct vertex, which shows the question template is the outlier. | Centre the arc on C: `M530 320 A40 40 0 0 1 535.3 300.1`, with the label at `x="522" y="312" text-anchor="end"`. This was verified by a scratch render: the arc sits at the base-right vertex between the base and the hypotenuse. For "angle at the top" contexts, centre it on B instead. |
| **D5** | accuracy | major | The drawn acute angle at C is always atan(230/400) = **29.9°**, whatever the stated angle. 22 figures differ by at least 10°: 45° (9), 50° (3), 55° (1), 60° (3), 40° (2), and θ = 41.1°, 43.6°, 16.3° and 14.3°. At 60° the height x = 1.73 × the base is drawn as 0.58 × the base. "Not drawn to scale" does not excuse a figure that suggests the wrong relationship. | Compute the vertical leg from the data: height = base_px × tan(angle) for angle items, or height = base_px × opposite/adjacent for θ items. Clamp it to the viewBox, rescaling the base when tan is above about 1.3. |
| **D6** | accuracy | major | `g4-l3-508` labels the hypotenuse **89** for legs 55 and 72. The true hypotenuse is √8209 ≈ 90.6, so the labels describe an impossible right triangle (the same false triple as C1). | Remove the hypotenuse label (it is not needed for tan), or label it `√8209` / `90.6`. Better, change the data to a true triple. |
| **D7** | accuracy | major | `g4-l5-505` draws only the far triangle (h, x+20, 35°, "far sight line"). The nearer observation point, the 50° angle, the 20 m gap and x are all missing, although they are the core of the two-position problem. It is also a unit checkpoint item. | Draw the mast, both observation points on one baseline, both sight lines, both angles at their own vertices, and the segments `x` and `20 m`. |
| **D8** | accuracy | minor | `g4-l5-501` and `g4-l5-503` ask the learner to "verify that the triangle is right-angled", but the figure already draws the right-angle marker. | Remove the marker, and label the sides 27, 36, x (and 21, 28, x). |
| **D9** | accuracy | minor | The elevation items label the vertical leg `h−1.6` but never show the tower, the ground, the eye-level line or the 1.6 m eye height. The figure does not show where `h` or 1.6 m come from. | Draw the tower to the ground, a dashed horizontal eye-level line, the observer with a 1.6 m segment, and the angle of elevation at the eye. Label the full tower `h`. |
| **D10** | accuracy | minor | The angle label reads `θ°`. θ already names the angle, so the degree sign is wrong notation. The lesson diagram uses `θ`. | Render `θ`. |
| **D11** | accuracy | minor | The alt text is the same for all 104 diagrams: "<title>: right-triangle schematic with labelled sides and a right-angle marker; not drawn to scale". It omits every value, variable and angle. It never mentions the angle arc in the 34 figures that have one, and it calls the 9 non-right figures right triangles. `generation_spec` records only the renderer, kind, key, outcome and `not_to_scale`. It has no side labels, angle or vertex, which falls short of the geometry standard's "explicit dimensions in their metadata". | Generate alt text from the same data as the labels, for example "Triangle with sides 55 cm, 72 cm and 89 cm; not drawn to scale". Add `side_labels`, `reference_angle` (vertex and value) and `angle_markers` to `generation_spec`. |
| **D12** | accuracy | minor | The SVG `<title>`, drawn as the figure heading, names the method: "Use tangent at 45 degrees" (7) and "Calculate a side using tangent" (10). Choosing the ratio is part of what outcome 4.3 assesses. | Use neutral headings, such as "Right-angled triangle". |
| **N1** | neatness | minor | The angle arc (from x = 210) and its label at (226, 300) crowd the right-angle marker (x 170–204) inside the bottom-left corner. The arc nearly touches the marker. | This is resolved by the D4 fix. |
| **N2** | neatness | minor | The `h−1.6` label starts at x = 116 in a 21 px bold font. Its right edge reaches about x = 172, overlapping the 6 px vertical side at x = 170 (confirmed in the render of `g4-l4-504`). | `x="150" text-anchor="end"`. |
| **N3** | neatness | minor | **Phone readability.** At a 390 px display width, the 760 px figure scales by 0.51. Side labels become about 10.8 px, angle labels about 9.2 px, and "Not drawn to scale" about 7.7 px, all below a 12 px readable minimum. About 190 px of the right-hand side (x 575–760) is empty. | Crop the viewBox to about `0 0 620 400`. Raise the side labels to 26 px, the angle labels to 24 px and the note to 20 px, so they render at 12 px or more on a 390 px screen. |

### Lesson diagram findings

| Lesson | Asset path | Category | Severity | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| `g4-lesson-01` | `backend_resources/courses/g3_math/secondary_2/g2/v1/assets/g4-lesson-01-pythagoras.svg` | — | — | Accurate. The 6-8-10 triangle is drawn to scale: legs of 240 px and 320 px, ratio 0.75. The labels sit on the correct sides, the right-angle marker is at the correct vertex, and the alt text matches. | — |
| `g4-lesson-01` | same | neatness | minor | At 390 px (scale 0.41), the 23 px labels render at about 9.5 px and the 19 px caption "c is opposite the right angle" at about 7.9 px. | Stack the equations under the triangle, or enlarge the fonts to at least 29 px. |
| `g4-lesson-02` | `…/assets/g4-lesson-02-converse.svg` | accuracy | low | The values are correct (7² + 24² = 625; 25² = 625; 26² = 676). However, the asset is two text cards with no figure, so it carries no spatial information, which the geometry standard expects of a diagram. | Add sketches of the two triangles above the cards, with a right-angle marker only on the 7-24-25 triangle (opposite 25). |
| `g4-lesson-02` | same | neatness | minor | At 390 px the 22 px card text renders at about 9 px. | Stack the cards vertically on narrow screens, or enlarge the fonts. |
| `g4-lesson-03` | `…/assets/g4-lesson-03-trigonometry.svg` | neatness | minor | The "opposite" label at (54, 255) in 21 px extends to about x = 139, overlapping the vertical side at x = 135 (visible in the render). | `x="122" text-anchor="end"`. |
| `g4-lesson-03` | same | neatness | minor | At 390 px, the 22 px ratio lines and side names render at about 9 px. | Move the ratio list under the triangle and enlarge the fonts. |
| `g4-lesson-03` | same | accuracy | — | θ is correctly at the acute base vertex: the arc is centred at (500, 370) with radius 56, and its endpoint lies on the hypotenuse. Opposite, adjacent and hypotenuse are correctly assigned relative to θ. | — |

### Per-diagram results (question bank)

Every asset path is relative to `backend_resources/question_bank/g3_math/secondary_2/g4/v1/`,
as resolved from each question's `assets[].path`. Every file exists. The triangle, marker and
label slots are byte-identical across all 104 files. The SHA-256 checksums were not altered
(the bank validator reports them as matching).

| Stable key | Asset (relative to bank) | Outcome / diff. | Visible labels | Findings | Worst severity |
| --- | --- | --- | --- | --- | --- |
| g4-l1-501 | `assets/g4-l1-501-diagram.svg` | 4.1 / 1 | 5, 12, 13 | D1, D11, N3 | critical |
| g4-l1-502 | `assets/g4-l1-502-diagram.svg` | 4.1 / 1 | 8, 15, 17 | D1, D11, N3 | critical |
| g4-l1-503 | `assets/g4-l1-503-diagram.svg` | 4.2 / 1 | 45, 60, 75 | D2, D11, N3 | critical |
| g4-l1-504 | `assets/g4-l1-504-diagram.svg` | 4.2 / 1 | 60, 63, 87 | D2, D11, N3 | critical |
| g4-l1-505 | `assets/g4-l1-505-diagram.svg` | 4.3 / 1 | 6, x, hypotenuse, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l1-506 | `assets/g4-l1-506-diagram.svg` | 4.3 / 1 | 7, x, hypotenuse, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l1-507 | `assets/g4-l1-507-diagram.svg` | 4.1 / 1 | 24, 143, 145 | D1, D11, N3 | critical |
| g4-l1-508 | `assets/g4-l1-508-diagram.svg` | 4.1 / 1 | 6, 8, 10 | D1, D11, N3 | critical |
| g4-l1-509 | `assets/g4-l1-509-diagram.svg` | 4.2 / 1 | 48, 55, 74 | D3, D11, N3 | critical |
| g4-l1-510 | `assets/g4-l1-510-diagram.svg` | 4.2 / 1 | 51, 68, 85 | D2, D11, N3 | critical |
| g4-l1-511 | `assets/g4-l1-511-diagram.svg` | 4.3 / 1 | 8, x, hypotenuse, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l1-512 | `assets/g4-l1-512-diagram.svg` | 4.1 / 1 | 88, 105, 137 | D1, D11, N3 | critical |
| g4-l1-513 | `assets/g4-l1-513-diagram.svg` | 4.1 / 1 | 3, 4, 5 | D1, D11, N3 | critical |
| g4-l1-514 | `assets/g4-l1-514-diagram.svg` | 4.2 / 1 | 25, 60, 65 | D2, D11, N3 | critical |
| g4-l1-515 | `assets/g4-l1-515-diagram.svg` | 4.3 / 1 | 9, x, hypotenuse, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l1-516 | `assets/g4-l1-516-diagram.svg` | 4.3 / 1 | 10, x, hypotenuse, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l1-517 | `assets/g4-l1-517-diagram.svg` | 4.1 / 1 | 60, 80, 100 | D1, D11, N3 | critical |
| g4-l1-518 | `assets/g4-l1-518-diagram.svg` | 4.2 / 1 | 28, 45, 54 | D3, D11, N3 | critical |
| g4-l1-519 | `assets/g4-l1-519-diagram.svg` | 4.2 / 1 | 39, 52, 65 | D2, D11, N3 | critical |
| g4-l1-520 | `assets/g4-l1-520-diagram.svg` | 4.3 / 1 | 11, x, hypotenuse, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l1-521 | `assets/g4-l1-521-diagram.svg` | 4.3 / 1 | 4, x, hypotenuse, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-501 | `assets/g4-l2-501-diagram.svg` | 4.1 / 2 | 12, 16, 20 | D1, D11, N3 | critical |
| g4-l2-502 | `assets/g4-l2-502-diagram.svg` | 4.1 / 2 | 20, 21, 29 | D1, D11, N3 | critical |
| g4-l2-503 | `assets/g4-l2-503-diagram.svg` | 4.1 / 2 | 21, 28, 35 | D1, D11, N3 | critical |
| g4-l2-504 | `assets/g4-l2-504-diagram.svg` | 4.2 / 2 | 60, 80, 100 | D2, D11, N3 | critical |
| g4-l2-505 | `assets/g4-l2-505-diagram.svg` | 4.2 / 2 | 17, 144, 145 | D2, D11, N3 | critical |
| g4-l2-506 | `assets/g4-l2-506-diagram.svg` | 4.3 / 2 | x, 14, sight line, 60° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-507 | `assets/g4-l2-507-diagram.svg` | 4.3 / 2 | x, 15, sight line, 30° | D4, N1, D12, D11, N3 | major |
| g4-l2-508 | `assets/g4-l2-508-diagram.svg` | 4.1 / 2 | 9, 40, 41 | D1, D11, N3 | critical |
| g4-l2-509 | `assets/g4-l2-509-diagram.svg` | 4.1 / 2 | 12, 35, 37 | D1, D11, N3 | critical |
| g4-l2-510 | `assets/g4-l2-510-diagram.svg` | 4.1 / 2 | 16, 30, 34 | D1, D11, N3 | critical |
| g4-l2-511 | `assets/g4-l2-511-diagram.svg` | 4.2 / 2 | 65, 72, 98 | D3, D11, N3 | critical |
| g4-l2-512 | `assets/g4-l2-512-diagram.svg` | 4.2 / 2 | 75, 100, 125 | D2, D11, N3 | critical |
| g4-l2-513 | `assets/g4-l2-513-diagram.svg` | 4.3 / 2 | x, 15, sight line, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-514 | `assets/g4-l2-514-diagram.svg` | 4.3 / 2 | x, 16, sight line, 50° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-515 | `assets/g4-l2-515-diagram.svg` | 4.3 / 2 | x, 17, sight line, 55° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-516 | `assets/g4-l2-516-diagram.svg` | 4.1 / 2 | 8, 15, 17 | D1, D11, N3 | critical |
| g4-l2-517 | `assets/g4-l2-517-diagram.svg` | 4.1 / 2 | 10, 24, 26 | D1, D11, N3 | critical |
| g4-l2-518 | `assets/g4-l2-518-diagram.svg` | 4.2 / 2 | 45, 60, 75 | D2, D11, N3 | critical |
| g4-l2-519 | `assets/g4-l2-519-diagram.svg` | 4.2 / 2 | 60, 63, 87 | D2, D11, N3 | critical |
| g4-l2-520 | `assets/g4-l2-520-diagram.svg` | 4.2 / 2 | 20, 99, 102 | D3, D11, N3 | critical |
| g4-l2-521 | `assets/g4-l2-521-diagram.svg` | 4.3 / 2 | x, 17, sight line, 35° | D4, N1, D12, D11, N3 | major |
| g4-l2-522 | `assets/g4-l2-522-diagram.svg` | 4.3 / 2 | x, 6, sight line, 40° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-523 | `assets/g4-l2-523-diagram.svg` | 4.3 / 2 | x, 7, sight line, 45° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-524 | `assets/g4-l2-524-diagram.svg` | 4.1 / 2 | 24, 143, 145 | D1, D11, N3 | critical |
| g4-l2-525 | `assets/g4-l2-525-diagram.svg` | 4.1 / 2 | 6, 8, 10 | D1, D11, N3 | critical |
| g4-l2-526 | `assets/g4-l2-526-diagram.svg` | 4.1 / 2 | 9, 12, 15 | D1, D11, N3 | critical |
| g4-l2-527 | `assets/g4-l2-527-diagram.svg` | 4.2 / 2 | 48, 55, 74 | D3, D11, N3 | critical |
| g4-l2-528 | `assets/g4-l2-528-diagram.svg` | 4.2 / 2 | 51, 68, 85 | D2, D11, N3 | critical |
| g4-l2-529 | `assets/g4-l2-529-diagram.svg` | 4.2 / 2 | 55, 72, 89 | D3, D11, N3 | critical |
| g4-l2-530 | `assets/g4-l2-530-diagram.svg` | 4.3 / 2 | x, 7, sight line, 60° | D4, D5, N1, D12, D11, N3 | major |
| g4-l2-531 | `assets/g4-l2-531-diagram.svg` | 4.3 / 2 | x, 8, sight line, 30° | D4, N1, D12, D11, N3 | major |
| g4-l3-501 | `assets/g4-l3-501-diagram.svg` | 4.1 / 3 | 11, 60, 61 | D1, D11, N3 | critical |
| g4-l3-502 | `assets/g4-l3-502-diagram.svg` | 4.1 / 3 | 36, 48, 60 | D1, D11, N3 | critical |
| g4-l3-503 | `assets/g4-l3-503-diagram.svg` | 4.2 / 3 | 6, 8, 10 | D2, D11, N3 | critical |
| g4-l3-504 | `assets/g4-l3-504-diagram.svg` | 4.2 / 3 | 9, 12, 15 | D2, D11, N3 | critical |
| g4-l3-505 | `assets/g4-l3-505-diagram.svg` | 4.2 / 3 | 12, 16, 21 | D3, D11, N3 | critical |
| g4-l3-506 | `assets/g4-l3-506-diagram.svg` | 4.3 / 3 | 48, 55, 73, θ° | D4, D5, N1, D10, D11, N3 | major |
| g4-l3-507 | `assets/g4-l3-507-diagram.svg` | 4.3 / 3 | 51, 68, 85, θ° | D4, N1, D10, D11, N3 | major |
| g4-l3-508 | `assets/g4-l3-508-diagram.svg` | 4.3 / 3 | 55, 72, 89, θ° | D4, N1, D6, D10, D11, N3 | major |
| g4-l3-509 | `assets/g4-l3-509-diagram.svg` | 4.1 / 3 | 27, 36, 45 | D1, D11, N3 | critical |
| g4-l3-510 | `assets/g4-l3-510-diagram.svg` | 4.1 / 3 | 28, 45, 53 | D1, D11, N3 | critical |
| g4-l3-511 | `assets/g4-l3-511-diagram.svg` | 4.2 / 3 | 3, 4, 6 | D3, D11, N3 | critical |
| g4-l3-512 | `assets/g4-l3-512-diagram.svg` | 4.2 / 3 | 7, 24, 25 | D2, D11, N3 | critical |
| g4-l3-513 | `assets/g4-l3-513-diagram.svg` | 4.2 / 3 | 9, 40, 41 | D2, D11, N3 | critical |
| g4-l3-514 | `assets/g4-l3-514-diagram.svg` | 4.3 / 3 | 25, 60, 65, θ° | D4, N1, D10, D11, N3 | major |
| g4-l3-515 | `assets/g4-l3-515-diagram.svg` | 4.3 / 3 | 40, 42, 58, θ° | D4, D5, N1, D10, D11, N3 | major |
| g4-l3-516 | `assets/g4-l3-516-diagram.svg` | 4.1 / 3 | 20, 21, 29 | D1, D11, N3 | critical |
| g4-l3-517 | `assets/g4-l3-517-diagram.svg` | 4.1 / 3 | 21, 28, 35 | D1, D11, N3 | critical |
| g4-l3-518 | `assets/g4-l3-518-diagram.svg` | 4.1 / 3 | 14, 48, 50 | D1, D11, N3 | critical |
| g4-l3-519 | `assets/g4-l3-519-diagram.svg` | 4.2 / 3 | 17, 144, 145 | D2, D11, N3 | critical |
| g4-l3-520 | `assets/g4-l3-520-diagram.svg` | 4.2 / 3 | 5, 12, 14 | D3, D11, N3 | critical |
| g4-l3-521 | `assets/g4-l3-521-diagram.svg` | 4.2 / 3 | 8, 15, 17 | D2, D11, N3 | critical |
| g4-l3-522 | `assets/g4-l3-522-diagram.svg` | 4.3 / 3 | 39, 52, 65, θ° | D4, N1, D10, D11, N3 | major |
| g4-l3-523 | `assets/g4-l3-523-diagram.svg` | 4.3 / 3 | 42, 56, 70, θ° | D4, N1, D10, D11, N3 | major |
| g4-l3-524 | `assets/g4-l3-524-diagram.svg` | 4.1 / 3 | 12, 35, 37 | D1, D11, N3 | critical |
| g4-l3-525 | `assets/g4-l3-525-diagram.svg` | 4.1 / 3 | 16, 30, 34 | D1, D11, N3 | critical |
| g4-l3-526 | `assets/g4-l3-526-diagram.svg` | 4.1 / 3 | 24, 32, 40 | D1, D11, N3 | critical |
| g4-l3-527 | `assets/g4-l3-527-diagram.svg` | 4.2 / 3 | 75, 100, 125 | D2, D11, N3 | critical |
| g4-l3-528 | `assets/g4-l3-528-diagram.svg` | 4.2 / 3 | 24, 143, 145 | D2, D11, N3 | critical |
| g4-l3-529 | `assets/g4-l3-529-diagram.svg` | 4.3 / 3 | 14, 48, 50, θ° | D4, D5, N1, D10, D11, N3 | major |
| g4-l3-530 | `assets/g4-l3-530-diagram.svg` | 4.3 / 3 | 33, 44, 55, θ° | D4, N1, D10, D11, N3 | major |
| g4-l3-531 | `assets/g4-l3-531-diagram.svg` | 4.3 / 3 | 16, 63, 65, θ° | D4, D5, N1, D10, D11, N3 | major |
| g4-l4-501 | `assets/g4-l4-501-diagram.svg` | 4.1 / 4 | 42, 56, 70 | D1b, D11, N3 | major |
| g4-l4-502 | `assets/g4-l4-502-diagram.svg` | 4.1 / 4 | 45, 60, 75 | D1b, D11, N3 | major |
| g4-l4-503 | `assets/g4-l4-503-diagram.svg` | 4.2 / 4 | 16, 30, x | D11, N3 | minor |
| g4-l4-504 | `assets/g4-l4-504-diagram.svg` | 4.3 / 4 | h−1.6, 23, line of sight, 50° | D4, D5, N1, D9, N2, D11, N3 | major |
| g4-l4-505 | `assets/g4-l4-505-diagram.svg` | 4.1 / 4 | 16, 63, 65 | D1b, D11, N3 | major |
| g4-l4-506 | `assets/g4-l4-506-diagram.svg` | 4.2 / 4 | 15, 20, x | D11, N3 | minor |
| g4-l4-507 | `assets/g4-l4-507-diagram.svg` | 4.3 / 4 | h−1.6, 20, line of sight, 35° | D4, N1, D9, N2, D11, N3 | major |
| g4-l4-508 | `assets/g4-l4-508-diagram.svg` | 4.3 / 4 | h−1.6, 21, line of sight, 40° | D4, D5, N1, D9, N2, D11, N3 | major |
| g4-l4-509 | `assets/g4-l4-509-diagram.svg` | 4.1 / 4 | 36, 48, 60 | D1b, D11, N3 | major |
| g4-l4-510 | `assets/g4-l4-510-diagram.svg` | 4.2 / 4 | 12, 16, x | D11, N3 | minor |
| g4-l4-511 | `assets/g4-l4-511-diagram.svg` | 4.3 / 4 | h−1.6, 18, line of sight, 60° | D4, D5, N1, D9, N2, D11, N3 | major |
| g4-l4-512 | `assets/g4-l4-512-diagram.svg` | 4.3 / 4 | h−1.6, 19, line of sight, 30° | D4, N1, D9, N2, D11, N3 | major |
| g4-l4-513 | `assets/g4-l4-513-diagram.svg` | 4.1 / 4 | 28, 45, 53 | D1b, D11, N3 | major |
| g4-l4-514 | `assets/g4-l4-514-diagram.svg` | 4.2 / 4 | 7, 24, x | D11, N3 | minor |
| g4-l4-515 | `assets/g4-l4-515-diagram.svg` | 4.2 / 4 | 9, 40, x | D11, N3 | minor |
| g4-l4-516 | `assets/g4-l4-516-diagram.svg` | 4.3 / 4 | h−1.6, 16, line of sight, 50° | D4, D5, N1, D9, N2, D11, N3 | major |
| g4-l5-501 | `assets/g4-l5-501-diagram.svg` | 4.2 / 5 | 27, 36, x | D8, D11, N3 | minor |
| g4-l5-502 | `assets/g4-l5-502-diagram.svg` | 4.1 / 5 | 40, 42, 58 | D1b, D11, N3 | major |
| g4-l5-503 | `assets/g4-l5-503-diagram.svg` | 4.2 / 5 | 21, 28, x | D8, D11, N3 | minor |
| g4-l5-504 | `assets/g4-l5-504-diagram.svg` | 4.1 / 5 | 42, 56, 70 | D1b, D11, N3 | major |
| g4-l5-505 | `assets/g4-l5-505-diagram.svg` | 4.3 / 5 | h, x+20, far sight line, 35° | D4, N1, D7, D11, N3 | major |

Severity totals across the 104 question diagrams, counting each diagram's worst finding: **56
critical**, **41 major**, **7 minor**. No question diagram was free of findings, because D11 and
N3 apply to all of them. The 5 "Complete a right-angled specification" diagrams (`l4-503`,
`-506`, `-510`, `-514`, `-515`) are geometrically accurate. Their only findings are D11 and N3.

---

## Root-cause patterns

### R1 — One fixed template for all 104 question diagrams

- **Source:** renderer `nextscholar-right-triangle-svg-v1`, `diagram_kind: right_triangle`.
- **Not in the repository:**
  - The renderer is not in `scripts/recalibrate_geometry_content.py`. That script covers only
    Secondary 1 G1/G5 and Secondary 2 G2, using `nextscholar-geometry-svg-v1`, and its
    `OUTCOME_KIND` map has no `4.x` entries.
  - It is not anywhere else in the repository either.
  - Git history is squashed into one root commit (`958925e`), so its source cannot be traced.
    The batch manifests name the generator `codex-offline-g4-v1`.
- **Evidence from the SVGs:** all 104 files share the same triangle path, the same right-angle
  marker and the same three label slots (vertical leg, base, hypotenuse). In 34 files they also
  share the same arc path, `M210 320 A40 40 0 0 1 232 285`.
- **What it explains:**
  - D4 and N1 (34 diagrams): the arc is hard-coded next to the right-angle vertex.
  - D5 (22): the shape does not depend on the data.
  - D2 and D3 (28): the marker is always drawn, even for converse tests.
  - D1 and D1b (35): the template fills every label slot with a number whenever one exists.
  - D12 (17): the question title is copied into the heading.
  - D10 (10): `θ°` is built from an angle-label slot that adds a degree sign.
  - N2 (6) and N3 (104): fixed slot positions and font sizes.
- **Likely fix:** re-implement the G4 renderer inside `scripts/recalibrate_geometry_content.py`
  (or a sibling script), taking the following as inputs:
  - the side lengths or variables;
  - the reference-angle vertex and value;
  - a `show_right_angle_marker` flag, set false for 4.2 test items;
  - the label to withhold.

  The vertices should be computed from the data. Re-rendering all 104 diagrams then clears
  every D and N row except D7, D9 and D6, which need data or design changes.

### R2 — The geometry validators are opt-in, and G4 opts into none of them

- In `question_bank/src/question_bank/geometry_validation.py`, `geometry_diagram_issues` runs
  three checks:
  - `angle_diagram_issues`, which only runs when `diagram_kind == "angle_types"`;
  - `_angle_marker_issues`, which returns `[]` when `generation_spec.angle_markers` is absent;
  - `_answer_leak_issues`, which returns `[]` when `generation_spec.forbidden_visible_labels`
    is absent.
- G4's `generation_spec` declares none of these, so `validate` and `course-validate` run **no**
  geometry or leak checks on the 104 G4 diagrams. That is why the bank passes with 0 issues.
- **Likely fix:**
  - Make `forbidden_visible_labels` required for every question asset whose part has a numeric
    canonical answer. It defaults to the canonical answer and its unrounded form.
  - Make `angle_markers` required whenever the SVG contains an arc.
  - Add a `right_triangle` checker that confirms:
    - the marker vertex is the declared right angle;
    - the arc is centred on the declared vertex;
    - the drawn angle is within ±10° of the declared value;
    - no right-angle marker is drawn when `outcome == 4.2` and the item is a classification
      task.

### R3 — The answer checker validates format, not correctness

- The publication check `canonical_and_accepted_answers_pass_checker` only confirms that each
  canonical answer parses and matches itself. Nothing recomputes the answer from the prompt, so
  C1 passed.
- **Likely fix:** for templated banks like this one, store the generator parameters (for
  example `{"sides": [55, 72, 89]}`) in the question provenance, and add a recomputation check
  per template. At minimum, add a lint for converse items: `a²+b²==c²` must equal
  `canonical_answer == "1"`.

### R4 — The authoring template predates the v2 rules

- All four G4 batch manifests cite `house-rules-v1.json` and `math-question-authoring-v1`.
- The v2 rules introduced after the N2 audit target exactly the content issues found here:
  - outcome alignment (C3);
  - semantic duplicates (C7);
  - hint boundaries (C8);
  - independent verification (C1);
  - level 4–5 demand (C4).
- The opening sentence (C9), the generic M-step text (C13) and the heavy reuse of triples (C7)
  are all signs of one fill-in-the-blanks generator.
- **Likely fix:** regenerate or hand-revise the bank under house rules v2 and prompt v2 before
  requesting Mathematics review, as the N2 audit required for N3 onward.

## Text-only questions and `diagram_audit.json`

- G4 has **no `diagram_audit.json`**. `GEOMETRY_CONTENT_STANDARD.md` says "Each geometry bank
  records this decision for every question in `diagram_audit.json`", and
  `backend_resources/question_bank/g3_math/secondary_2/g2/v1/diagram_audit.json` exists for G2.
  This is a minor process gap.
- Every G4 question already has a diagram, so no text-only question needs one.
- The opposite applies to some items. For the 28 converse tests, a correct general-triangle
  figure adds little beyond the three numbers in the prompt. Reviewers may prefer to make these
  text-only, recording "text-sufficient" in a new `diagram_audit.json`, rather than redraw them.
  The 5 specification items are in the same position.
- The items where a diagram is essential, and must be correct, are the angle-of-elevation
  items, the two-position item, and the cable and route items.

## What could not be verified

- **Renderer source.** `nextscholar-right-triangle-svg-v1` is not in the repository and Git
  history is squashed. The R1 root cause is inferred from the byte-identical SVG structure and
  the manifest generator name, not from the generator's code.
- **Viewing resolution.** All 107 diagrams were rendered and viewed. The 104 question diagrams
  were viewed in 3×3 contact sheets at about 55% scale, plus individual full-size views of a
  sample. Fine details such as the N2 overlap were confirmed with a full-size render and with
  SVG coordinates.
- **Phone rendering.** The 390 px renders were produced for all 107 diagrams but viewed only for
  a sample (`g4-l3-506`, `g4-lesson-02`). The N3 and lesson phone findings are computed from the
  scale factor (390 / viewBox width) and the font sizes, which applies uniformly because the
  template is uniform.
- **Fonts.** Text widths for the overlap findings (N2, `g4-lesson-03` "opposite") were measured
  in headless Chromium's default system-ui font. Learner devices may use a different font, so
  the exact overlap may differ slightly. The labels are close enough to the lines to collide in
  common sans-serif fonts.
- **Learner apps.** How the web app frames the SVG (padding, maximum width) was not checked, so
  the phone-width estimate assumes the figure fills 390 px.
- **Review status.** No review decision was made. All findings need Mathematics and editorial
  confirmation.
