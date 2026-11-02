# Secondary 2 G5 technical pre-review audit

**Date:** 2 November 2026

**Scope:** all 104 questions in `backend_resources/question_bank/g3_math/secondary_2/g5/v1/`
(batches B001–B004) and the one G5 lesson in the Secondary 2 course,
`g5-lesson-06` (stored in `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/`,
found through `course.json` unit `g3-sec2-g5`). The four v2 diagnostic items
(`g5-l3-951`, `g5-l3-953`, `g5-l4-952`, `g5-l4-954`) are out of scope.

**Decision boundary:** technical pre-review only. This audit is report-only. No question,
lesson, SVG, manifest, claim or review state was changed. No Mathematics or editorial
approval is recorded.

**Review state found:** all 104 questions are `draft` revision 1, all four batches are
`ready_for_review` with Mathematics and editorial review `pending`, and the lesson is `draft`.
No approved content exists in this scope.

**Audience:** students preparing for the Sec 3-entry ASEAN Scholarship test.

## Counts

| Item | Count |
| --- | ---: |
| Questions checked | 104 |
| Lessons checked | 1 |
| Diagrams checked (104 question SVGs + 3 lesson SVGs) | 107 |
| Diagrams rendered to PNG and viewed | 107 |
| Diagrams also viewed at phone width (358 px content width for a 390 px screen) | 6 representative (all 5 question drawings + 3 lesson diagrams) |
| Distinct question drawings (geometry identical apart from the text panel) | 5 |
| Canonical answers recomputed by code | 104 |
| Canonical answers found wrong | 2 |
| Distinct mathematical tasks after removing context sentences | 65 of 104 |

## Checks performed

- Recomputed every canonical answer from the prompt with a per-template Python solver
  before reading the solution, and applied the stated rounding.
- Checked each worked solution, mark allocation, hint pair and response configuration.
- Checked each item against outcome 5.6, the syllabus catalogue and its difficulty level.
- Grouped items by their mathematical core (the prompt with context sentences removed) to
  find semantic duplicates, and checked duplicates against the course pools.
- Checked wording against `LESSON_NOTES_CONTENT_STANDARD.md`, `GEOMETRY_CONTENT_STANDARD.md`,
  `GEOMETRY_DIAGRAM_AUTHORING_STANDARD.md`, house rules v2 and the N2 audit model.
- Rendered every SVG to PNG with Playwright Chromium in a temporary directory outside the
  repository, at native size and at 358 px width. I viewed every image: the 104 question
  diagrams on 18 labelled contact sheets at native 760 × 430 resolution, and the lesson
  diagrams at native 940 × 500 resolution.
- Measured every text bounding box in the browser (`getBBox`) for clipping, overlap and
  panel overflow, and inspected SVG path coordinates for each of the five drawings.
- Cross-checked every panel value against its prompt by script.
- Ran `question-bank validate` on the bank, `course-validate` on the Secondary 2 course and
  `authoring-validate` on the bank.

### Validator results

| Command | Result |
| --- | --- |
| `question-bank validate …/secondary_2/g5/v1` | valid, 0 errors, 0 warnings |
| `question-bank course-validate …/secondary_2/g2/v1 --bank …/secondary_2` | valid, 0 errors, 0 warnings |
| `question-bank authoring-validate …/secondary_2/g5/v1` | `duplicate_count: 0`. Its only error was `learning_blueprint_coverage`, expected when one bank is run alone. |

Every validator passes, but this audit still found two wrong answers, 39 duplicate items and
systemic diagram errors. The validators' blind spots are explained under root causes R2 and R4.

---

## Part 1 — Content findings

Severity: **High** means a learner is marked wrong for a correct answer, the hint gives away
the answer, or the item misleads. **Medium** means it breaks a standard or house rule, or
needs a reviewer's judgement. **Low** means polish.

### C1–C2. Wrong canonical answers (High)

Volume scale factor is 1/8, so the depth = H × ∛(1/8) = H/2. For odd heights, the stored
answer appears to have been truncated to an integer.

| Key | Batch | Prompt values | Stored answer and solution | Correct | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| `g5-l4-507` | B002 | H = 15 cm, 1/8 full | `7`, solution `h=7` | **7.5** | Set `canonical_answer`/`canonical_latex` to `7.5`, solution to `h=7.5`. Alternatively, change H to an even height not used elsewhere (e.g. 16 → 8). |
| `g5-l4-514` | B004 | H = 21 cm, 1/8 full | `10`, solution `h=10` | **10.5** | Set the answer to `10.5`, solution `h=10.5`. Alternatively, change H to 22 → 11. |

`g5-l4-507` and `g5-l4-514` are both in `g5-adaptive-reserve-b`. The other 102 canonical
answers match the recomputation, including rounding. Worked-solution values match their
canonical answers for all 102.

### C3. Semantic duplicates (High, systemic)

The 104 items come from **21 templates** and reduce to **65 distinct mathematical tasks**.
In **39 items**, the mathematics is identical to another item; only the context sentences
differ. House rules v2 prohibits repeating "context, operation pattern and numerical structure,
even when wording changes enough to pass the near-prompt detector". The authoring duplicate
scan reports 0.

| Identical task | Keys |
| --- | --- |
| Pyramid, base area 12, h 6 | `g5-l1-501`, `g5-l1-519` |
| Cone/cylinder factor numerator | `g5-l1-502`, `g5-l1-506`, `g5-l1-510`, `g5-l1-513`, `g5-l1-520` |
| Sphere SA, r 5 | `g5-l1-503`, `g5-l1-507`, `g5-l1-521` |
| Hemisphere curved area, r 6 | `g5-l1-504`, `g5-l1-508` |
| Sphere SA, r 9 | `g5-l1-511`, `g5-l1-514`, `g5-l1-517` |
| Hemisphere curved area, r 10 | `g5-l1-515`, `g5-l1-518` |
| Cone CSA, r 12, l 20 | `g5-l2-501`, `g5-l2-511`, `g5-l2-521`, `g5-l2-531` |
| Sphere volume, d 20 | `g5-l2-502`, `g5-l2-508`, `g5-l2-522`, `g5-l2-528` |
| Cone volume, r 4, h 18 | `g5-l2-504`, `g5-l2-530` |
| Cone CSA, r 8, l 17 | `g5-l2-505`, `g5-l2-515` |
| Sphere volume, d 12 | `g5-l2-506`, `g5-l2-512`, `g5-l2-518`, `g5-l2-524` |
| Cone CSA, r 6, l 10 | `g5-l2-517`, `g5-l2-527` |
| Cone + hemisphere volume, r 3, h 4 | `g5-l3-502`, `g5-l3-512`, `g5-l3-522` |
| Sphere r 100 cm → m³ | `g5-l3-503`, `g5-l3-509` |
| Closed cone TSA, r 6, h 8 | `g5-l3-504`, `g5-l3-514`, `g5-l3-524` |
| Cone + hemisphere volume, r 7, h 24 | `g5-l3-506`, `g5-l3-516` |
| Sphere r 200 cm → m³ | `g5-l3-507`, `g5-l3-513`, `g5-l3-519`, `g5-l3-525` |
| Closed cone TSA, r 9, h 12 | `g5-l3-510`, `g5-l3-520`, `g5-l3-530` |
| Cone + hemisphere volume, r 8, h 15 | `g5-l3-518`, `g5-l3-528` |
| Sphere r 300 cm → m³ | `g5-l3-523`, `g5-l3-529` |
| Hollow shell, R 5, r 3 | `g5-l4-501`, `g5-l4-516` |
| Sphere radius +50 % | `g5-l4-503`, `g5-l4-509` |
| Sphere radius +20 % | `g5-l4-506`, `g5-l4-513` |

Some duplicate pairs fall in the same course pool, so a learner can meet the same task twice
in one sitting:

- `g5-lesson-06-practice` (20 items): 4 pairs: `l1-502/506`, `l1-503/507`, `l1-504/508`,
  `l2-502/508`.
- `g5-adaptive-reserve-a` (30): 7 pairs: `l1-513/520`, `l1-514/517`, `l1-515/518`,
  `l2-517/527`, `l2-518/524`, `l2-521/531`, `l2-522/528`.
- `g5-adaptive-reserve-b` (30): 4 pairs: `l3-519/525`, `l3-520/530`, `l3-523/529`,
  `l4-506/513`.
- `g5-unit-checkpoint` (24): no pairs.

Even the non-identical items vary little. For example, all 8 "Find a pyramid's height" items
have the form 3V ÷ (a × b). All 4 "Liquid depth" items use the same 1/8 fraction.

**Proposed correction:** keep one item from each duplicate group. Rewrite the other 39 as new
structures that suit their level: for example, frustum-free cone problems with a given slant
height and an unknown radius, square-pyramid surface area from a given vertical height, a
hemisphere-topped cylinder, or a sphere in a cube. Start with the 15 pairs that share a pool.

### C4. Lesson worked example duplicates a bank item (Medium)

`g5-lesson-06`, section `g5-56-cone-example` (closed cone, r = 5, h = 12, total surface area
90π ≈ 282.7 cm²) is the same task as **`g5-l3-526`**, which is in `g5-adaptive-reserve-b`.
**Correction:** change `g5-l3-526` to r = 8, h = 15 (l = 17, TSA = 200π ≈ 628.3), or
another Pythagorean triple not used elsewhere.

### C5. Stage-2 hint states the answer; trivially guessable response (High)

`g5-l1-502`, `g5-l1-506`, `g5-l1-510`, `g5-l1-513`, `g5-l1-520`: H2 says *"The required
fraction is 1/3; enter its numerator."* This gives the answer `1`, which breaks house rules v2
("neither hint may state the final answer"). The answer `1` is also guessable without
understanding. **Correction:** keep one item. Ask for a quantity, for example: "A cylinder
has volume 150 cm³. A cone has the same base and perpendicular height. Find the cone's
volume." (50). Use H2: "Write the cone's volume as a fraction of the cylinder's volume."

### C6. Stage-2 hints that reduce higher-level items to one operation (Medium)

| Keys | H2 text | Effect |
| --- | --- | --- |
| `g5-l5-503`, `g5-l5-504` (d5) | "Because the base side is halved, its area is quartered, so the height must become four times as large." | The answer becomes 4 × 15 or 4 × 9, so the d5 reasoning is given away. Use: "Write the volume of each pyramid and set them equal." |
| `g5-l5-501` (d5) | "Cancel πr² from both sides and solve h = 4r." | The answer becomes 4 × 3. Use: "Cancel the common factors π and r² before substituting r = 3." |
| `g5-l4-504`, `-507`, `-510`, `-514` (d4) | "The cube root of 1/8 is 1/2; apply this to the height." | The answer becomes H/2. Use: "Write the volume ratio as (h/H)³." |
| 21 d1 items (`l1-*`) and the d2 `Cone volume`/`Rectangular pyramid volume` items | "Calculate (12 × 6) ÷ 3." / "Evaluate 2 × 6²." | Only arithmetic remains (Low). Give the formula with symbols rather than the substituted expression. |

### C7. Difficulty inflation at levels 4–5 (Medium, reviewer judgement)

House rules v2 says levels 4–5 must require method selection, constraints, justification or
sustained synthesis. All five d5 items have a one-line solution:

- `g5-l5-501`: equate two formulas.
- `g5-l5-502`: divide two volumes, with an exact integer result.
- `g5-l5-503` and `-504`: equate two pyramid volumes.
- `g5-l5-505`: (R³ − r³)/R³.

The d4 items `g5-l4-502`/`-505` (cost of covering) are routine d3 surface-area tasks.

**Proposed correction:** either re-band these items (d5 to d3/d4, cost items to d3), or
redesign the d5 items to need several ideas. For example, a recast where the cone count
leaves a remainder and the learner must also find the surface area of the leftover material,
or a constraint on both the volume and the slant height.

### C8. Outcome alignment: volume ratio of similar solids (Medium, reviewer judgement)

`g5-l4-504`, `-507`, `-510`, `-514` depend on "the volume ratio is the cube of the length
ratio" (stated in H1). The syllabus catalogue has no Secondary 2 outcome for area or volume
ratios of similar solids. G2.2–G2.5 cover similar plane figures, and enlargement of a
plane figure. The lesson does not teach it either. `g5-l4-503`, `-506`, `-509`, `-513`
can be solved directly from V = 4/3πr³, but their hints also teach the scale-factor
shortcut.

**Decision needed:** either add a short teaching section on volume scale factors to the
lesson, or rewrite the liquid-depth items so they can be solved from the cone formula plus
similar triangles. For example, give the liquid surface radius and ask for the volume.

### C9. Physical set-up missing from the liquid-depth prompts (Medium)

`g5-l4-504`, `-507`, `-510`, `-514`: "filled to one eighth … forms a smaller similar cone at
the tip". Liquid forms a cone at the tip only when the cone is held vertex down, and the
prompt never says so. **Correction:** "A conical container is held with its vertex pointing
down …".

### C10. Mark schemes not supported by worked steps (Medium, systemic)

All 83 multi-mark items have the same structure. Step 1 begins with the boilerplate *"Select
the relevant dimensions and apply the mensuration relationship."*, followed by one combined
line worth M2–M4 that already contains the final value. Step 2 (A1) just repeats the answer in
a box. For example, `g5-l3-504` awards M2 for `l=√(6²+8²)=10, S=π(6)(10)+π(6)²=301.6`, and
`g5-l5-501` awards M4 for one equation. A marker cannot tell which method earns which mark.
**Correction:** write one step per method mark. For `g5-l3-504`: M1 slant height 10, M1
πrl + πr², A1 301.6. Remove the boilerplate sentence.

### C11. Templated, non-functional contexts (Medium, systemic)

Every prompt opens with a templated sentence, *"⟨Subject⟩ considered ⟨constraint⟩ while preparing
⟨a replacement design | a capacity check⟩ for the ⟨object⟩."*. The template has 8 subjects × 32
objects, and 78 items add one or two filler sentences. The most common fillers are:

- *"A later inspection will compare the finished dimensions with this record."* (32 items)
- *"The design must also be explained clearly in the safety briefing."* (32 items)
- *"A scale model will be stored with the project documentation."* (8 items)

These add about 25–45 words of reading load without affecting the mathematics. Specific
problems:

- **The stated purpose contradicts the task in 11 items.** The context says "capacity check",
  but the item asks for an area: `g5-l1-517`, `g5-l1-518`, `g5-l1-521`, `g5-l2-527`,
  `g5-l2-531`, `g5-l3-520`, `g5-l3-524`, `g5-l3-526`, `g5-l3-530`, `g5-l4-511`, `g5-l4-515`.
- **The object does not match the solid.** For example, "museum planet model" for a cone
  (`g5-l3-504`), "sports hall roof model" for a cone (`g5-l3-524`), and "ferry terminal sign"
  for a pyramid height (`g5-l3-501`).
- **Grammar:** all 104 begin with a singular count noun and no article ("Survey crew
  considered…", "Maintenance team considered…").
- **Odd or region-specific phrasing:** "Snow-free tropical mountain conditions still bring
  strong crosswinds." (`g5-l5-505` and 2 others).

**Correction:** either drop the context and state the solid directly, or write one sentence
of context that sets the quantity asked for. For example: "How much fabric covers the cone's
curved surface?" for curved surface area, or "How much water does the bowl hold?" for
capacity. The current standard calls for clear international English and contexts that work
across Southeast Asia.

### C12. Smaller wording and response issues (Low)

- **Stem says "labelled" but the solids are unlabelled.** All 104 stems read "Use the labelled
  mensuration schematic", but no label is attached to any solid (see D7).
- **Composite volume items:** `g5-l3-502`, `-506`, `-512`, `-516`, `-518`, `-522`, `-528`
  say "a cone of radius 3 cm and height 4 cm"; specify "perpendicular height of the cone".
  The title is "capacity", but the prompt asks for the volume of a solid; either retitle or
  make the object a container.
- **"Enter the numerical value only"** appears only in the six `Volume of a pyramid` items.
  Apply one convention bank-wide.
- **Percentage answers** (`g5-l4-503`, `-506`, `-509`, `-513`, `g5-l5-505`) do not say
  whether to type the % sign. Say "Enter the number without the % sign", or accept both forms.
- **Currency:** `g5-l4-502` and `g5-l4-505` use a bare "$" in the prompt, H2 and the SVG panel
  ("$5/m²"). See Standards conflicts.

### Lesson `g5-lesson-06`

All lesson mathematics was recomputed and is correct:

- Pyramid example: 10/12/13 gives V = 400 and S = 360; the slant height √(5² + 12²) = 13 is
  consistent.
- Cone example: V = 100π ≈ 314.2 and S = 90π ≈ 282.7.
- Hemisphere example: V = 486π ≈ 1526.8 and A = 162π ≈ 508.9.
- Active recall: 144π.

The lesson meets the structural gates: 10 sections, 3 worked examples with verification
notes, 4,715 authored characters and 3 referenced diagrams.

| ID | Severity | Finding | Proposed correction |
| --- | --- | --- | --- |
| L1 | Medium | Objective 3 promises "reverse and composite-solid problems", but there is no worked example of either. The bank has 8 reverse items (find a height), 10 composite items, 1 recast item and 4 similar-cone items, plus cost-per-area items, none of which have a worked model. | Add a worked example finding a pyramid's height from its volume, and one on a cone + hemisphere composite (volume and exposed area). Decide C8 before adding scale-factor content. |
| L2 | Low | `GEOMETRY_CONTENT_STANDARD.md` lists "misconception checks"; the lesson has none as a section. Radius versus diameter and h versus l appear only inside explanations. | A reviewer may accept this as embedded. Otherwise, add a short misconception-check section. |
| L3 | Medium | The cone worked example duplicates `g5-l3-526` (C4). | See C4. |

---

## Part 2 — Diagram findings

### How the diagrams are built

All 104 question SVGs (760 × 430, renderer `nextscholar-mensuration-svg-v1`) use **one fixed
drawing per `diagram_kind`**. The geometry is byte-identical across all items of a kind:

| diagram_kind | Items | Drawing |
| --- | ---: | --- |
| pyramid | 26 | Triangular-based pyramid, dashed vertical height, right-angle mark |
| cone | 33 | Upright cone, dashed vertical height and radius, right-angle mark |
| sphere | 30 | Sphere, dashed equator, one radius |
| composite | 11 | Cone on a hemisphere, dashed cone height and radius |
| hemisphere | 4 | Open bowl, one radius on the rim |

Every value appears only in a right-hand "Given dimensions" panel. **No label is attached to
any segment.** Every panel value matches its prompt (checked by script). No diagram shows a
canonical answer.

### Findings

| ID | Category | Severity | Affected keys / assets | What is wrong | Specific fix |
| --- | --- | --- | --- | --- | --- |
| D1 | Accuracy | High | **Rectangular base (16):** `g5-l2-503`, `-507`, `-509`, `-513`, `-519`, `-523`, `-525`, `-529`; `g5-l3-501`, `-505`, `-511`, `-515`, `-517`, `-521`, `-527`, `-531`. **Square base (4):** `g5-l4-502`, `-505`; `g5-l5-503`, `-504`. **Lesson:** `courses/…/g2/v1/assets/g5-lesson-06-pyramid.svg`. Assets: `assets/<key>-diagram.svg`. | The pyramid has three base vertices, (95,340), (365,340) and (445,275), so it is a triangular pyramid. The prompts say rectangular or square base. The lesson diagram is titled "Square-based pyramid" and says "= base + four triangles", but it shows three lateral faces. | Draw a quadrilateral base, for example front edge (95,340)–(365,340) and back edge (175,275)–(445,275), with four lateral edges. Dash the hidden back edges. The six `Volume of a pyramid` items (`g5-l1-501`, `-505`, `-509`, `-512`, `-516`, `-519`; base unspecified) are not contradicted, but they share the template. |
| D2 | Accuracy | High | All 26 pyramid question SVGs, plus the lesson pyramid. | The foot of the height, (230,310), lies **outside** the drawn base: the back base edge (95,340)→(445,275) is at y = 314.9 at x = 230. So the right-angle mark (230–260, 280–310) sits off the base plane. The apex (x = 230) is 72 px left of the base centroid (301.7, 318.3), so the solid reads as oblique, but `l2-*` prompts say "right pyramid". The hidden base edge is drawn solid and crosses the front face and the height line. Lesson: foot (245,325) versus back edge y = 333.9 at x = 245, the same fault. | Put the apex directly above the centre of the base. End the dashed height at that centre, and draw the right-angle mark in the base plane. Dash hidden edges. |
| D3 | Accuracy | High | **Cone CSA (8):** `g5-l2-501`, `-505`, `-511`, `-515`, `-517`, `-521`, `-527`, `-531`. **Composite external area (3):** `g5-l4-508`, `-511`, `-515`. **Pyramid covering cost (2):** `g5-l4-502`, `-505`. | The panel gives the slant height (`l = 20 cm`, `slant = 12 m`), but the only drawn length is the dashed **vertical** height with a right-angle mark. That is the dimension the learner must *not* use, and nothing marks the slant edge. This reinforces the h-versus-l misconception the items test. | Mark the slant edge (cone: apex (250,75) to rim (395,340); pyramid: apex to the midpoint of a base edge) and label it `l` on the figure. Remove the vertical height, or draw it unlabelled and faint. |
| D4 | Accuracy | High | **Recast:** `g5-l5-502`. **Equal-volume:** `g5-l5-501`. **Cone/cylinder:** `g5-l1-502`, `-506`, `-510`, `-513`, `-520`. **Hollow shell:** `g5-l4-501`, `-512`, `-516`. **Core removed:** `g5-l5-505`. **Liquid depth:** `g5-l4-504`, `-507`, `-510`, `-514`. | The wrong solid is drawn (15 items): <br>• `l5-502` uses the composite drawing (a cone *joined* to a hemisphere), which suggests a single joined solid; the task has four separate spheres recast into separate cones. <br>• `l5-501` shows only a cone; the sphere is missing. <br>• The cone/cylinder items say "same radius / same height", but no cylinder is drawn. <br>• The shell and core items show one filled solid sphere with one radius; "inner r" and "removed core r" match nothing drawn, and the fill implies a solid. <br>• The liquid-depth items show an apex-up cone with no liquid; the task needs a vertex-down cone with a liquid surface. | • `l5-502`: draw a sphere and a separate cone side by side. <br>• `l5-501`: draw a cone and a sphere side by side, each with r = 3. <br>• Cone/cylinder items: draw the cone inside a dashed cylinder. <br>• Shell and core items: draw concentric spheres with the inner one dashed, labelled R and r. <br>• Liquid depth: draw an inverted cone with a horizontal liquid surface, label H, and leave the depth unlabelled. |
| D5 | Accuracy | Medium | **Sphere from diameter (8):** `g5-l2-502`, `-506`, `-508`, `-512`, `-518`, `-522`, `-524`, `-528`. | The panel says "diameter = 20 cm", but the only drawn segment is a radius from the centre. A learner may attach 20 cm to the radius, which is exactly the error the item targets. | Draw a full diameter through the centre and label it `d = 20 cm`. |
| D6 | Accuracy / neatness | Low | All 30 sphere question SVGs; lesson `g5-lesson-06-sphere.svg`. | The radius stops short of the surface. Question SVGs: endpoint (365,165) is 134.2 px from the centre (245,225), but the circle has r = 145, leaving a visible gap of about 8 px. Lesson: (360,210) is 138.7 px from (235,270) versus r = 145. | Compute the endpoint on the circle: (245 + 145 cos θ, 225 − 145 sin θ), for example (374.7, 160.1) for θ = 26.6°. Lesson: (365.7, 207.2). |
| D7 | Accuracy | Medium | All 104 question SVGs. | No r, h or l label is attached to any segment. Values are listed only in the side panel, so the learner cannot tell which drawn segment is which. This is what makes D3 and D5 misleading. The stems and alt text call the figure "labelled". | Place r, h and l labels next to their segments, as the lesson cone diagram does. Keep the panel optional. |
| D8 | Accuracy | Low | `g5-l2-526` (r 8, h 6), `g5-l2-504`, `-510`, `-530` (h/r 3.75–4.5), `g5-l3-506`, `-516` (h/r 3.43), `g5-l5-502` (h/r 4.5). | The fixed cone draws h/r ≈ 1.8 for every item. `l2-526` describes a squat cone (h < r) but shows a tall one; the others are much taller than drawn. "Not drawn to scale" is stated, so the severity is low. | Set the apex height from the spec ratio, clamped to about 0.6–3.5. |
| D9 | Accuracy (alt text and generation_spec) | Medium | All 104 question SVGs. | The alt text is the same template everywhere: "⟨title⟩: a labelled ⟨kind⟩ mensuration schematic; not drawn to scale." It contains no dimensions, wrongly says "labelled", and names the wrong solid for the D4 items. `generation_spec` holds only renderer, kind, key, outcome and `not_to_scale`. There are no dimensions, though the geometry standard requires "explicit dimensions in their metadata", and no `forbidden_visible_labels`, so the answer-leak check never runs. | Write alt text that names the solid(s) and the given values, for example: "Cone with radius 12 cm and slant height 20 cm marked; not drawn to scale." Add the dimensions and `forbidden_visible_labels: [<canonical answer>]` to the spec. |
| D10 | Neatness | Medium | All 107 SVGs. | Text is unreadable on a phone. At 390 px (358 px content), the 760-wide question SVGs scale by 0.47: panel values at 17 → 8.0 px, and "Not drawn to scale" and the footnote at 14 → 6.6 px. The 940-wide lesson SVGs scale by 0.38: notes at 19–20 → 7.2–7.6 px, and formulas at 25 → 9.5 px. All fall below a legible ~11 px. | Use a portrait layout below 600 px, with the panel stacked under the solid, or enlarge the type to at least 26 user units in the 760 box. The lesson formulas could move into the lesson text, which already contains them as `display_math`. |
| D11 | Neatness | Medium | `courses/…/g2/v1/assets/g5-lesson-06-pyramid.svg` | The note "Use the perpendicular height for volume." spans x = 560–946, past the 940 viewBox, so its full stop is clipped. The label "vertical height h" (x 258–425, y 199–225) is drawn across the front-right edge, which crosses x ≈ 318 at y = 212, so the edge strikes through the text. | Move the label to the left of the dashed height (text-anchor end, x ≈ 235), or shorten it to "h". Wrap the note or reduce it to 18 px. |
| D12 | Accuracy | Low | `g5-lesson-06-pyramid.svg` | The note says "Use each face's slant height for area", but no slant height is drawn. The worked example uses a slant height of 13. | Draw and label `l` from the apex to the midpoint of the front base edge. |
| D13 | Neatness | Low | `g5-lesson-06-sphere.svg` | The "r" label's box (302–310, 203–229) is 4–9 px from the radius stroke and touches it at phone width. The title is "Sphere and hemisphere", but no hemisphere is drawn. | Move "r" to about (290, 222) with a 12 px clearance above the stroke. Add a small hemisphere, or retitle "Sphere". |
| D14 | Neatness | Low | Composite (11): `g5-l3-502`, `-506`, `-512`, `-516`, `-518`, `-522`, `-528`; `g5-l4-508`, `-511`, `-515`; `g5-l5-502`. Cone (33), for the apex notch only. | The cone apex (y ≈ 52.5) is about 5 px below the title's descenders (title box bottom y = 48), which looks cramped. Both sides of each apex are separate subpaths (`M245 55 L115 285 M245 55 L375 285`), so the butt caps leave a notched tip. | Lower the composite figure about 15 px (the hemisphere bottom has 12 px of room, so scale by about 0.95). Draw each apex as one path, `M115 285 L245 55 L375 285`, with `stroke-linejoin="round"`. |
| D15 | Neatness | Low | **Third panel line (13):** `g5-l3-504`, `-508`, `-510`, `-514`, `-520`, `-524`, `-526`, `-530`; `g5-l4-502`, `-505`, `-508`, `-511`, `-515`. **Panel width:** `g5-l5-502`. | A third value line ("closed base", "join hidden", "$5/m²") ends at y = 265, only 6 px above the grey footnote (y = 271), which looks crowded. In `l5-502`, "cones: r = 2 cm, h = 9 cm" ends at x = 711, 4 px from the panel edge (715); it could overflow with a wider device font. | Remove the boilerplate footnote "Select the dimensions required by the formula." (it appears on all 104), or size the panel to its content. Split the `l5-502` line in two. |
| D16 | Neatness | Low | Cone (33), sphere (30), lesson cone and sphere. | Hidden-line conventions are wrong. The back half of each cone base ellipse is drawn solid, and the whole sphere equator is dashed, including its visible front half. | Dash only the hidden halves. |

No diagram reveals an answer the learner must find. For example, the "Find a pyramid's height"
panels omit h, and the liquid-depth panels omit the depth. In `g5-l3-511`, the answer 9 also
appears as the base dimension "10 × 9 cm"; that is coincidental, not a leak.

### Text-only questions that need a diagram

This bank has no `diagram_audit.json` (see R3). Every question already has a diagram, so there
are no text-only candidates. Some current diagrams add almost nothing, though. The
`Choose the cone volume factor` and `Percentage change in sphere volume` items would need the
redesign in D4 or D7 to be worth showing.

---

## Root-cause patterns

**R1: A fixed template per `diagram_kind` (affects all 104 question diagrams).**
`nextscholar-mensuration-svg-v1` draws one hard-coded solid per kind and injects values only
into the panel. Its 21 question templates are squeezed into 5 kinds, so templates that need a
cylinder, an inner sphere, an inverted cone with liquid, two separate solids, a quadrilateral
base or a slant-height marking all get an unsuitable drawing.

- This one choice explains D1–D5, D7 and D8: 60 items with at least one High or Medium
  accuracy error (26 pyramid, 18 cone, 4 composite and 12 sphere), and all 104 without
  on-figure labels.
- **The renderer's source is not in the repository.** The string occurs only in question JSON.
  `scripts/recalibrate_geometry_content.py` does not generate it: that script's
  `svg_document` produces 940 × 390 lesson diagrams with no pyramid, cone or sphere shapes.
  The template therefore cannot be corrected and regenerated from repository code.
- **The lesson pyramid repeats the same fault.** It has the same triangular base and the same
  height foot outside the base (D1, D2), which suggests the question pyramid was derived from
  it.

**R2: The geometry validator never runs on this bank.**
`question_bank/src/question_bank/geometry_validation.py` checks:

- ray geometry only for `diagram_kind == "angle_types"`;
- `angle_markers` only when declared;
- `forbidden_visible_labels` only when declared.

No G5 asset declares any of these, so `geometry_diagram_issues` returns nothing for all 107
diagrams. Nothing checks solid shape, base type, label attachment, point-on-surface or text
fit. A passing validator is therefore no evidence about these diagrams.

**R3: The bank is not covered by the recalibration script.**
`recalibrate_questions()` lists only `secondary_1/g1`, `secondary_1/g5` and `secondary_2/g2`,
so no `diagram_audit.json` exists for `secondary_2/g5`. `recalibrate_lessons()` iterates
`g*-lesson-*.json` in the Secondary 2 course, but `LESSONS` has no `g4-*` or `g5-lesson-06`
entry. The script's own code suggests a rerun would fail with a `KeyError` at
`g4-lesson-01`; I did not run it. The lesson assets declare renderer
`nextscholar-geometry-svg-v1`, but they are 940 × 500 hand-authored files, not that
template's output, so the provenance is inaccurate.

**R4: Template-driven question generation without semantic deduplication.**
The batches use generator `codex-offline-g5-v1` with prompt `math-question-authoring-v1`.
The N2 audit required v2 for later batches. Contexts are slot-filled (8 subjects × 32 objects
plus fillers), and parameters are reused across batches. Because each context sentence
differs, the 0.82 near-duplicate threshold sees each item as unique (`duplicate_count: 0`),
so 39 math-identical items get through (C3). The duplicate scan should compare the
mathematical core (numbers + operation) as well as the full prompt.

**R5: Integer handling in the liquid-depth template.**
Only odd heights (15, 21) fail, and they fail by exactly 0.5. This is consistent with integer
division or truncation of H/2 while generating `exact_numeric` answers. A regression check that
recomputes the answers (as this audit did) would catch it.

---

## Standards conflicts (reported, not resolved)

| Topic | N2 audit / house rules v2 | Current audience standard (`LESSON_NOTES_CONTENT_STANDARD.md`) | G5 bank today | Decision needed |
| --- | --- | --- | --- | --- |
| Currency | "Use S$ in learner-facing Singapore-dollar contexts"; currency `SGD`. The N2 audit made S$ consistent. | Learners across Indonesia and Southeast Asia; Singapore syllabus is "a calibration and coverage reference" only; use contexts that work across Southeast Asia. | Bare `$` in `g5-l4-502` and `g5-l4-505` (prompt, H2, SVG panel `$5/m²`, `$6/m²`). | Choose S$, a neutral wording ("costs 5 per m²; give the cost in the same currency units"), or a regional currency, and apply it bank-wide. |
| Language variant | `language_variant: "Singapore/British English"`. | "Clear international English"; explain unfamiliar terminology. | British spelling ("harbour", "centre", "metre") throughout. This satisfies both standards, so no change is needed unless the owner decides otherwise. | Confirm that British spelling is acceptable as "international English". |
| Contexts | "Age-appropriate, culturally neutral contexts." | "Contexts that work across Southeast Asia." | Templated contexts (C11); some are region-specific or odd ("Snow-free tropical mountain conditions…"). | Decide whether to keep context at all for routine mensuration items. |
| Prompt and house-rule version | The N2 audit requires prompt v2 and house rules v2 for later batches. | — | All four G5 batches record `math-question-authoring-v1`. | Decide whether to regenerate these batches under v2 or correct them by hand. |

---

## What could not be verified

- **The renderer's source code** is not in the repository, so the root causes R1 and R5 are
  inferred from the outputs, not traced in code.
- **Fonts:** I rendered with Playwright Chromium using the container's `system-ui` fallback.
  Device fonts may be wider or narrower, so the near-edge measurements in D11 and D15 may
  differ on real devices.
- **Production rendering:** I did not render diagrams through the authenticated asset
  endpoint or the admin and learner UIs, and did not check KaTeX rendering of the solution
  LaTeX.
- **Answer checker:** I did not run the bank's checker against the corrected values `7.5` and
  `10.5`.
- **Phone width:** I viewed only 6 representative PNGs at phone width. Because every question
  diagram of a kind shares the same geometry and panel layout, the D10 measurements apply to
  all 104 question diagrams, but the other 101 were not viewed individually at that size.
- **Difficulty and outcome calibration** against the actual ASEAN Scholarship Sec 3-entry
  test is a reviewer judgement (C7, C8). This audit only reports the rubric mismatch.
- The four v2 diagnostic items are out of scope and were not audited.

## Files changed by this audit

This report only. No content, asset, manifest, claim or review record was modified, and no
rendered image was committed.
