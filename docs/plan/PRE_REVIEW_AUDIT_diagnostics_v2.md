# Pre-review audit: 76 readiness diagnostic items

**Date:** 4 November 2026
**Scope:** the 76 v2 diagnostic questions in `backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json`

This is a technical check to reduce what the Mathematics reviewer has to catch. It is not an
approval and records no decision. B and E are the baseline and endline, followed by the form
position.

## Result

All 76 keys and worked solutions matched an independent solution. 16 items had no finding: B1-4,
B17, B26, B30, B33, E4, E12, E15, E17, E20-22 and E29.

Fixes were checked by reading the code and running the real checker. Diagrams were checked from
source and a headless render, not inside the learner app. Scope rests on one-line catalogue outcomes,
and no item statistics exist yet.

## Fixed in draft revisions

These still need human review.

| Item | Problem | Change |
| --- | --- | --- |
| All items | A format error silently scored 0, so `3,8`, `260°` and `q=...` counted as wrong (decision D9-A). | The diagnostic refuses to save the answer and shows how to fix it. |
| All items | Authored titles appeared as headings, and B37, E7, E33, E34, E35 and E37 cued the answer. | Learners see "Question N". |
| B16 `n6-l3-902` | The line missed all four points, so reading it gave x = 5, not the key 7. | Redrawn through the points in a new `-r2` SVG, with the `y` label moved off the heading. |
| E13 `n5-l2-953` | Retyping the prompt `(3x-4)(2x+5)` earned full marks. | Requires the expanded form. |
| B11 `n5-l3-901` | "Simplest form" accepted `(2n+1)(2n+5)`. | Prompt says "expanded form", and that form is required. |
| E8(b) `n3-l4-904` | `20%` was marked wrong (D9-A). | Accepts `%` and `percentage points`. |

## Open for the reviewer

### Major

| Item | Problem | Proposal |
| --- | --- | --- |
| B13, E13 | Outcomes are swapped. 5.9 is expansion and 5.11 is an unknown in a formula, and tags drive lesson recommendations. | B13 to 5.11, E13 to 5.9. |
| B28, E27, E28 | B28 (Pythagoras) is tagged 4.2, E27 (converse) 4.3, E28 (trigonometry) 4.1. | Change to 4.1, 4.2 and 4.3. |
| G4 forms | Once retagged, the baseline is Pythagoras twice and the endline is converse plus trigonometry. | Replace one baseline item with trigonometry. |
| B38, E38 | "Simplest form" is not enforced, so `12/16` and `15/36` pass. | Use symbolic mode with a simplified-fraction form, or drop the demand. |
| B38 | Near-copy of `s2-l3-508`, and its solution uses the multiplication rule, against D3-A. | One spinner 1-4 and one 1-5, solved by listing 20 outcomes: 7/10. |
| B31, B32, E32 | The value of π is unstated and matching is exact, while E29 states 22/7. | Add "use the calculator's π". |
| B18, E18 | B18 uses completing the square, which no lesson teaches. E18 is an average of two numbers. | B18: y = x²−6x+8 crosses at 2 and 4, find the minimum (−1). E18: y = x²−12x+20 crosses at 2 and 10, find the minimum (−16). |
| E14 | Tagged 5.12 but uses no standard identity, and `≡` appears in no lesson. | (2x+a)² ≡ 4x²+bx+49, a > 0, find a+b (35). Gloss `≡`. |
| E26, B26 | Both are difficulty 4, but E26 is given the factor and multiplies, while B26 derives it and inverts. | E26: reduced area 27, factor 3/4, find the original (48). |
| B19, B22 | Same form and algebra, so one cues the other. | B22: 2(3x−4) ≤ 2x+13, greatest integer 5. |
| Form design | 13 of 19 topic groups use different outcomes across the forms, so gains there compare different skills. Clearest in Sec 1 N1, Sec 2 N7 and Sec 1 G5. | Founder decision: report at topic level only, or re-pair the forms. |

Outcome and form changes need the generated plan updated, not only the questions.

### Minor

- **Near-copies of v1:** B6 and `n2-l3-530`; E3 and `n2-l3-022`.
- **Same arithmetic across forms:** B24 and E23 both reduce to 8x+4 = 180. Change E23 to (5x−20)° and (3x+16)°, giving y = 85.
- **Marks and difficulty:** B29 is difficulty 2 with 3 marks and E30 is difficulty 3 with 2, so Sec 1 G5 totals 6 and 4. B34, B35, E11 and E36 read as difficulty 2, and B32 is easier than E32.
- **Diagrams:** E25 places `BC = 10 cm` under side AC, and its triangles aren't similar as drawn. Labels cross edges in B25, E25 and E31. E28 has θ on the hypotenuse. B15 describes y up to 6, but the grid stops at 5.
- **No visual to read:** B34 and B35 describe a graph and a stem-and-leaf diagram in text, though the outcomes are about reading them.
- **Terms:** B36 says "dot plot" and the syllabus says "dot diagram". "Co-interior" in E23 is unglossed. E36 says "outlier", but 12 isn't shown to be one. E28 mixes "point on level ground" with "eye level".
- **Scope to confirm:** E35 uses frequency density. Lessons and seven v1 items teach it, but the syllabus may limit histograms to equal intervals.
