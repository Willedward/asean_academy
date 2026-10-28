# Layer 1 English V3-B route blueprint

**Prepared:** 28 October 2026
**Status:** fixed technical blueprint; Sprint breadth and protected baseline authored in draft; review and release pending
**Exam profile:** `asean-english-sec1-id-reported-v1`

## 1. Decision

The existing 51-lesson English curriculum now has three fixed routes:

| Route | Intended runway | Lessons | Meaning |
| --- | --- | ---: | --- |
| Full | 28 weeks or more | 51 | Complete curriculum; every lesson remains accessible. |
| Core | 12–27 weeks | 32 | Release-A sequence covering every reported test strand and composition. |
| Sprint | Fewer than 12 weeks | 16 | Minimum coherent preparation route; always a subset of Core. |

Route membership controls recommendations and release planning. It does not publish draft
content, hide Full-route lessons, or personalise a learner's calendar.

## 2. Fixed membership

| Module | Core | Sprint |
| --- | --- | --- |
| E0 Orientation | E0.1, E0.2 | E0.1, E0.2 |
| E1 Vocabulary | E1.1, E1.2, E1.4, E1.5, E1.6 | E1.1, E1.6 |
| E2 Sentence control | E2.1, E2.2, E2.3, E2.6 | E2.2 |
| E3 Banked cloze | E3.1, E3.2, E3.4 | E3.1 |
| E4 Open cloze | E4.1, E4.2, E4.4, E4.5 | E4.1, E4.5 |
| E5 Reading | E5.1, E5.2, E5.3, E5.5, E5.6, E5.7 | E5.2, E5.3, E5.7 |
| E6 Composition planning | E6.1, E6.2, E6.5 | E6.1, E6.5 |
| E7 Paragraph development | E7.1, E7.2 | E7.2 |
| E8 Essay editing | E8.4 | E8.4 |
| E9 Timed composition | E9.1, E9.5 | E9.5 |

The Sprint route deliberately favours integrated strategies over isolated enrichment. The
Core route adds enough vocabulary, grammar, inference, planning and paragraph depth to build
transfer without requiring every Full-route lesson before Beta.

## 3. Coverage rationale

Both reduced routes contain:

- orientation and an untutored baseline through E0.1 and E0.2;
- vocabulary-in-context preparation through E1;
- grammar and reference foundations through E2;
- banked and open-cloze strategies through E3 and E4;
- reference, synonym-in-context and two-passage pacing through E5;
- prompt decoding, planning, paragraph development and editing through E6–E8; and
- a complete timed English simulation through E9.5.

Core additionally includes reflective/personal expository writing because that is the
best-supported reported composition form. Narrative and discursive modules remain available
in Full, but they are not allowed to delay Release A while the prompt evidence remains
provisional.

## 4. Enforced invariants

The catalogue validator now rejects a change when:

- a lesson is removed from Full;
- route tags are duplicated or out of canonical `full`, `core`, `sprint` order;
- Core contains fewer than 28 or more than 32 lessons;
- Sprint contains fewer than 14 or more than 16 lessons;
- a Sprint lesson does not also belong to Core;
- either reduced route omits any module from E0 through E9; or
- E0.1, E0.2 or the E9.5 timed simulation is absent from either reduced route.

Exact route membership is covered by regression tests so an intentional curriculum change
must update both the source catalogue and its evidence.

## 5. Current readiness

| Route | Selected | Authored | Still requiring lessons |
| --- | ---: | ---: | --- |
| Full | 51 | 36 | 15 |
| Core | 32 | 25 | 7 |
| Sprint | 16 | 16 | 0 |

The five former Sprint gaps—E0.1, E0.2, E1.6, E2.2 and E9.5—now have complete seven-section
lesson drafts, five-decision exit tickets and distinct five-decision retry forms. The remaining
Core gaps are E1.2, E1.4, E1.5, E2.3, E2.6, E3.2 and E3.4.

Authored does not mean publishable. Every released lesson still needs its reviewed exit
ticket, distinct parallel retry form and the normal immutable academic/editorial approvals.
All 16 Sprint lessons now reference an exit ticket and have a distinct parallel retry form.
The retry increment adds ten question groups and six fresh passage assets without exposing
protected diagnostic or mock content. A separate protected-measurement increment now adds a
draft 20-part baseline: five vocabulary decisions, five banked-cloze gaps, five open-cloze
gaps and five reading decisions. Its four question groups and three passages are isolated in
the `baseline_diagnostic` pool, tutoring is disabled and feedback is withheld until the form
ends. Publication remains blocked on the matched endline/reserve, checkpoints and the normal
immutable review approvals.

## 6. Next execution milestone

Complete the remaining **Sprint protected measurement and checkpoints**:

1. author matched endline and reserve forms against the now-active baseline blueprint;
2. enforce disjoint item ownership across all protected forms;
3. add checkpoint manifests for the represented modules;
4. generate consolidated reviewer evidence for the 16-lesson route; and
5. collect immutable English/editorial approvals before enabling learner routing.

Once Sprint is structurally complete, author the seven additional Core gaps and repeat the
same release checks. This sequencing shortens the critical path while preserving the Core
and Full curriculum.
