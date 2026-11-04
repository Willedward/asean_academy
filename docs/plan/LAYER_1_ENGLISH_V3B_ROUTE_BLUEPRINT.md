# Layer 1 English V3-B route blueprint

**Prepared:** 28 October 2026
**Status:** fixed technical blueprint; Sprint content, protected measurement, checkpoints, progress visibility and consolidated reviewer evidence structurally complete; human review and release pending
**Exam profile:** `asean-english-sec3-id-reported-v1`

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
| Full | 51 | 51 | 0 |
| Core | 32 | 32 | 0 |
| Sprint | 16 | 16 | 0 |

The five former Sprint gaps—E0.1, E0.2, E1.6, E2.2 and E9.5—now have complete seven-section
lesson drafts, five-decision exit tickets and distinct five-decision retry forms. The remaining
No Core gaps remain. E1.2, E1.4, E1.5, E2.3, E2.6, E3.2 and E3.4 now each have a complete
seven-section lesson, six guided/independent/exit questions and one disjoint parallel retry.

Authored does not mean publishable. Every released lesson still needs its reviewed exit
ticket, distinct parallel retry form and the normal immutable academic/editorial approvals.
All 16 Sprint lessons now reference an exit ticket and have a distinct parallel retry form.
The retry increment adds ten question groups and six fresh passage assets without exposing
protected diagnostic or mock content. A separate protected-measurement increment now adds a
draft 20-part baseline: five vocabulary decisions, five banked-cloze gaps, five open-cloze
gaps and five reading decisions. Matched endline and reserve forms now repeat that exact
5–5–5–5 blueprint with disjoint question groups and fresh passages in the
`endline_diagnostic` and `protected_reserve` pools. Across all three protected forms, tutoring
is disabled and feedback is withheld until the form ends. The first checkpoint slice now
adds reciprocal E1 vocabulary forms with five fresh decisions each and an explicit mastery
scope covering Sprint lessons E1.1 and E1.6. The E1 vertical slice now has persisted,
idempotent checkpoint sessions; prerequisite locking; learner-safe delivery without hints or
answer feedback; deterministic 75% scoring; reciprocal form-B retry after failure; and an
atomic transition from `proficient` to `mastered` for both scoped lessons after a pass.
PostgreSQL persistence, evidence immutability and the prerequisite race guard are covered by
integration tests. The E0 checkpoint adds reciprocal two-group forms that sample both paper
knowledge and baseline integrity, proving that protected sessions sequence multiple question
groups without leaking interim correctness. The E2 checkpoint adds reciprocal five-decision
grammar forms scoped to Sprint lesson E2.2, with difficulty-4 agreement and reference transfer
rather than reused exit-ticket sentences. The E3 checkpoint adds reciprocal five-gap banked
cloze forms, each built around a fresh complete narrative passage, and scopes mastery to Sprint
lesson E3.1. The E4 checkpoint adds reciprocal two-passage open-cloze forms that divide five
scored gaps between function-word control and timed cross-sentence reasoning, with mastery
scoped to Sprint lessons E4.1 and E4.5. The E5 checkpoint adds reciprocal paired-passage
reading forms with five decisions spanning reference chains, synonym-in-context reasoning and
cross-passage comparison, with mastery scoped to Sprint lessons E5.2, E5.3 and E5.7.
The E6 checkpoint adds reciprocal two-group forms built around distinct original composition
prompts. Each form measures three prompt-decoding decisions and two compact-planning
decisions, with mastery scoped to Sprint lessons E6.1 and E6.5. It evaluates planning
judgement without asking an automated system to score a whole essay.
The E7 checkpoint adds reciprocal two-group forms that measure a complete paragraph evidence
chain: bounded assertion, relevant action or observation, consequence, significance and
honest limitation. Mastery is scoped to Sprint lesson E7.2, and both forms reject decorative
detail and invented precision.
The E8 checkpoint adds reciprocal five-decision composition self-editing forms scoped to
Sprint lesson E8.4. It measures revision priority from task fulfilment through organisation,
development and sentence control; it does not introduce the excluded standalone editing-paper
task type into the reported exam blueprint.
The E9 checkpoint completes Sprint checkpoint coverage with reciprocal five-decision
simulation-readiness forms scoped to E9.5. It measures separate clocks, whole-paper coverage,
composition pacing, interruption integrity and post-run interpretation. It remains a readiness
checkpoint and is explicitly not the protected full mock.
Learner progress now exposes readiness, attempt count, the active session and latest score for
every E0–E9 checkpoint. Administrator student detail exposes English lesson evidence and the
latest checkpoint result per attempted module without exposing submitted answers. Publication
remains blocked on the normal immutable review approvals.
The deterministic Sprint reviewer export now pins all 16 lessons, 16 parallel retries, 20
reciprocal checkpoint forms, 65 unique question groups and 20 referenced passages. The packet
contains exact revision fingerprints plus separate pending English and editorial decision
columns, and pull-request CI uploads the same protected evidence as an artifact.
The protected administrator queue now exposes the same records under route key
`english-sprint-route-v3b-review`. That route resolves to exactly 121 independently
fingerprinted review records: 16 lessons, 20 checkpoint forms, 65 question groups and
20 passages. Reviewers can exclude individual records, preview protected answers and form
composition, and append separate English and editorial decisions. Correction exports retain
the exact rejected fingerprint, and no review action changes learner publication state.
The administrator route view also exposes a deterministic, fail-closed release manifest.
It hashes the complete 121-record route, lists only revisions with both English and
editorial approval in its approved set, and reports separate review, publication-status
and lifecycle-request blockers. The gate cannot become `ready` until all 121 pinned
revisions are dual-approved, published and backed by an active publication request for the
same review fingerprint. Viewing the manifest never publishes content or enables routing.

## 6. Next execution milestone

Complete the remaining **Sprint review and release evidence**:

1. apply migration `202610290036_english_checkpoint_form_review.sql`, deploy the protected
   route session, and collect immutable English and editorial approvals against its 121
   pinned records;
2. correct and re-export any excluded items without approving changed fingerprints;
3. run the protected baseline/endline and checkpoint journey in hosted staging; and
4. enable learner routing only after the route manifest reports `ready`, confirming that
   every referenced revision is approved, publication-requested and published.

Once Sprint is structurally complete, author the Core gaps and repeat the
same release checks. This sequencing shortens the critical path while preserving the Core
and Full curriculum.

The separate essay path does not change this route manifest. ENG-T3.9 calibration
infrastructure is implemented under schema revision `202611010046`, but no live essay provider
is released. ENG-T3.10 release infrastructure is implemented under `202611020047`; it requires
current exact calibration, privacy/safeguarding evidence, explicit release, the environment
switch and learner consent. A qualified educator and the responsible privacy owners must still
record real evidence, so the hosted provider remains disabled.

The E9.2 narrative-writing lesson is a separate Full-route, draft-only content increment. It
does not change the 16 Sprint lessons, 20 checkpoint forms or 121-record Sprint review scope;
its lesson and exit ticket require their own English, editorial and publication evidence.

The E9.3 opinion-and-discursive-writing lesson follows the same Full-route boundary. Its
fictional policy record, lesson and exit ticket remain outside the Sprint scope and require
their own English, editorial and publication evidence.

The E9.4 process-compression lesson completes the authored E9 sequence as a separate
Full-route, draft-only increment. It moves from supported 45-minute evidence through a
reduced-support 35-minute run to a fresh 30-minute independent rehearsal without treating speed
alone or repeated prompts as transfer. Its lesson and exit ticket remain outside the fixed
Sprint scope and require their own English, editorial and publication evidence. The next
content-expansion sequence now moves to mock forms and the open audit findings.

The E1.2 word-class-and-family lesson is the first completed Core-expansion increment. It
identifies sentence slots before testing form, meaning and collocation, and its retry uses a
fresh family rather than an exposed answer. E1.2 remains outside Sprint, so the 16 Sprint
lessons, E1 checkpoint mastery scope and 121-record Sprint review packet are unchanged. Its
lesson and seven questions require their own English, editorial and publication evidence.

The E1.4 synonym-precision lesson is the second completed Core-expansion increment. It tests
core meaning, degree and attitude before substitution and refuses stronger or more critical
language that the sentence does not support. Its retry uses a fresh context and synonym set.
E1.4 remains outside Sprint, so the 16 Sprint lessons, E1 checkpoint mastery scope and
121-record Sprint review packet are unchanged. Its lesson and seven questions require their
own English, editorial and publication evidence.

The E1.5 collocation-and-register lesson is the third completed Core-expansion increment. It
checks intended meaning, natural word partnership, audience and the complete sentence without
treating inflated formality as improvement. Its retry uses a different formal collocation.
E1.5 remains outside Sprint, so the 16 Sprint lessons, protected forms, E1 checkpoint mastery
scope and 121-record Sprint review packet are unchanged. Its lesson and seven questions require
their own English, editorial and publication evidence.

The E2.3 tense-and-aspect lesson is the fourth completed Core-expansion increment. It uses
explicit time anchors, event order and viewpoint to distinguish habits, temporary arrangements,
ongoing actions, completed events and results that continue to the present. Its retry uses a
different past sequence rather than the exposed exit sentence. E2.3 remains outside Sprint, so
the 16 Sprint lessons, protected forms, E2 checkpoint mastery scope and 121-record Sprint review
packet are unchanged. Its lesson and seven questions require their own English, editorial and
publication evidence.

The E2.6 logical-connections lesson is the fifth Core-expansion increment and the first written to
[ENGLISH_LEVEL_REVIEW_SEC3_2026_11.md](./ENGLISH_LEVEL_REVIEW_SEC3_2026_11.md). It stays outside
Sprint, and its lesson and seven questions need their own English, editorial and publication
evidence.

The E3.2 grammar-filter lesson is the sixth increment, with its own seven passages and word banks.
E3.4 solve-globally completes Core lesson coverage. E0.3, E1.3, E2.4, E2.5 and E3.3 complete Full lesson coverage. All remain draft and need human review.
