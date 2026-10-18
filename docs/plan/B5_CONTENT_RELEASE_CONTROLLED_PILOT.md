# B5 content release and controlled pilot

**Engineering status: Mathematics release controls were implemented on 30 September
2026; the Beta remains blocked by content, the Layer 1 English extension and hosted
evidence.**

B5 turns the implemented application into a release that can be offered to real invited students. It is deliberately fail-closed: a healthy build or a successful local login does not mean that the content, staging environment or operating team is ready.

## What is implemented

The release gate at `services/learning_api/scripts/beta_release_gate.py` binds one candidate to:

- an exact 40-character Git SHA and a clean checkout;
- the course revision and deterministic complete-course content hash;
- the authored topic, lesson and question inventory;
- mutually exclusive practice, checkpoint and adaptive-reserve allocations;
- imported PostgreSQL content hashes;
- Mathematics and editorial review records plus publication requests;
- two current published 38-question diagnostic forms with no baseline/endline overlap;
- diagnostic isolation from lesson, checkpoint and adaptive-reserve pools;
- a named rollout phase and privacy-minimal cohort label;
- hosted OAuth, authenticated E2E, accessibility, restore, load/rate-limit, ownership, freeze and founder confirmations.

It writes JSON for machines and Markdown for humans. Both artifacts omit student emails, invitation codes, answers, database URLs and access tokens.

The manual **Beta release readiness** GitHub workflow adds protected staging checks. It verifies the deployed SHA, API readiness, web authentication gate and public Supabase Google provider; runs a 200-request bounded load smoke; restores the staging database into an empty isolated database and compares critical-table hashes; runs the content/database release gate; and retains all evidence for 90 days.

The 18 October 2026 scope decision moves English into Layer 1. The implemented gate is
still Mathematics-specific and must be extended to bind the English course, objective
question banks, baseline/endline forms, essay rubrics, prompt-policy revisions and
provider evaluation evidence. See
[LAYER_1_ENGLISH_SCOPE.md](LAYER_1_ENGLISH_SCOPE.md).

## Current evidence and blockers

The current Mathematics source contains every Secondary 1 and Secondary 2 unit in the
supplied syllabus. Secondary 1 N2 is reviewed; the other complete units remain behind
draft review gates. English currently has UI designs but no production domain or
reviewed content:

| Requirement                        |                         Current source |                              B5 minimum | State   |
| ---------------------------------- | -------------------------------------: | --------------------------------------: | ------- |
| Topic groups                       |                                     19 |                                      19 | Pass    |
| Mathematics learning questions     |                                  1,976 |                                   1,900 | Pass    |
| Mathematics diagnostic items       |                      76 authored drafts | 76, split into two disjoint forms of 38 | Authored; review blocked |
| Lessons                            |                                     87 |  All authored and planned Beta lessons | Pass    |
| Lessons meeting the note-depth gate |                                     87 |                   All authored lessons | Pass    |
| English production contracts       |                                      0 | Objective, passage, diagnostic and essay contracts | Blocked |
| English reviewed course content    |                                      0 | All strands in the approved Layer 1 blueprint | Blocked |
| English diagnostic forms           |                                      0 | Two disjoint reviewed objective forms | Blocked |
| Essay calibration evidence         |                                      0 | Human-scored anchors and passing provider evaluation | Blocked |
| Published course/lessons/questions |                        0 complete sets |           All student-visible revisions | Blocked |
| Local pool inventory               | 1,044 practice, 393 checkpoint, 475 reserve |        Complete and non-overlapping | Pass    |

The generalized course and question contracts now support multiple level/topic banks and multiple authored courses, and Secondary 1 N2 proves the complete reviewed path through lesson pools and catalogue import. Secondary 1 N3 through N7, G1, G5 and S1 plus every Secondary 2 topic group provide complete draft paths with 104 questions each, authored lessons and source pools, pending Mathematics and editorial approval. Secondary 1 N1 retains its 40-question calibration bank and independent lesson review gates. The full-syllabus source gate now passes, but that does not infer Beta readiness from draft content.

Secondary 2 G4 now has three full-depth lesson drafts, 104 questions and complete practice, checkpoint and adaptive-reserve pools in the deployable draft course snapshot. It remains unavailable to production learners until Mathematics and editorial review and the later publication gate pass.

Secondary 2 G5 now has one full-depth lesson draft, 104 diagram-backed questions and complete practice, checkpoint and adaptive-reserve pools in the deployable draft course snapshot. It remains unavailable to production learners until Mathematics and editorial review and the later publication gate pass.

Secondary 2 N5 now has eight full-depth lesson drafts, 104 questions and complete per-outcome practice, unit-checkpoint and adaptive-reserve pools in the deployable draft course snapshot. It remains unavailable to production learners until Mathematics and editorial review and the later publication gate pass.

Secondary 2 N6 now has two full-depth lesson drafts, 104 questions and complete per-outcome practice, unit-checkpoint and adaptive-reserve pools in the deployable draft course snapshot. Its two deterministic SVG diagrams connect quadratic rules, tables, graphs and graph properties. It remains unavailable to production learners until Mathematics and editorial review and the later publication gate pass.

Secondary 2 N7 now has six full-depth lesson drafts, 104 questions and complete per-outcome practice, unit-checkpoint and adaptive-reserve pools in the deployable draft course snapshot. Three deterministic SVG diagrams teach inequality endpoints, linear graphs and simultaneous-equation intersections. It remains unavailable to production learners until Mathematics and editorial review and the later publication gate pass.

Secondary 2 S1 now has six full-depth lesson drafts, 104 questions and complete per-outcome practice, unit-checkpoint and adaptive-reserve pools in the deployable draft course snapshot. Six deterministic SVG diagrams support distribution displays, representation choice, misleading axes, measures of centre and grouped-mean estimation. It remains unavailable to production learners until Mathematics and editorial review and the later publication gate pass.

## Development sequencing decision — 10 October 2026

Finish the authored questions, lessons, reviews and deterministic release tooling before
paying for the hosted Beta operating tier. This is an acceptable development sequence while:

- no real learners are invited and staging is treated as disposable;
- Git remains the authority for questions, lessons, migrations and configuration;
- database changes stay additive and continue to pass migration and restore tests in CI;
- any staging state that would be costly to recreate is exported with an operator-controlled
  `pg_dump` before a risky schema or data operation; and
- premium tutor routing remains disabled. Administrator shadow mode may remain available for
  engineering smoke tests.

A manual dump reduces the risk of losing useful development state, but it is not a substitute
for managed backups during a real learner cohort. Local exports contain database data and must
follow the same-session deletion rule in the operational retention plan.

## Controlled rollout

Each phase has a hard size range:

1. `founder_alpha`: 1–2 fresh accounts. Run the complete baseline → lesson → practice → retry → checkpoint → endline path twice.
2. `friendly_users`: 3–5 cooperative users. Observe onboarding and first-session completion, resolve blockers, then hold for at least one normal usage cycle.
3. `beta_cohort`: 10–30 invited students. Expand gradually and keep schema/content frozen except for documented incident fixes.

Use a non-PII label such as `founder-alpha-01`; never put student names or email addresses in workflow inputs or release artifacts. The actual invitation list remains in the protected admin/database workflow.

## First hosted run

The readiness workflow creates a fresh PostgreSQL 16 service for every run and restores the staging backup into it. No persistent restore credential is required, and the restore target cannot point at staging or production. Keep the existing staging secrets and variables in [HOSTED_STAGING.md](HOSTED_STAGING.md).

Deploy the exact candidate through **Staging release**. Complete the real private-window Google sign-in and the authenticated journey. Then open GitHub Actions → **Beta release readiness** → **Run workflow** and enter:

- the exact deployed 40-character SHA;
- the current rollout phase, non-PII cohort label and planned size;
- only confirmations backed by completed evidence.

The `staging` GitHub environment should require a founder/operator reviewer. A checked box records an attestation; it does not replace the actual test. A failed gate still uploads the JSON/Markdown evidence so the team can see every blocker.

## Local report

A local report is useful while content is being authored. It is not a release approval:

```bash
cd /home/william/asean_academy
DATABASE_URL='postgresql://SERVER_ONLY_STAGING_URL' \
  corepack pnpm release:beta -- \
  --phase founder_alpha \
  --cohort-label local-readiness \
  --cohort-size 1 \
  --report-only
```

The command writes `beta-release-evidence.json` and `beta-release-evidence.md`. These generated files are ignored by Git. Omit `--report-only` for a strict non-zero exit whenever any check blocks release.

## Content-to-pilot sequence

1. Generalize the N1-only authoring contract to all 19 supplied topic groups while preserving immutable revisions.
2. Commission and review the 1,900-question minimum, including enough independent practice, checkpoint and adaptive-reserve capacity.
3. Author 76 additional diagnostic-only questions: 38 baseline and 38 matched endline items, with two items per topic group per form.
4. N1.2–N1.7 were completed on 13 October 2026. N6.1–N6.5, N7.1–N7.4 and S1.1–S1.4
   were expanded on 14 October 2026. N5.1–N5.8 were expanded on 16 October 2026. All 87
   lessons now pass the structural note-depth gate and remain subject to Mathematics and
   editorial review before publication.
5. Record Mathematics and editorial decisions in the admin review workflow; publish through an audited lifecycle request.
6. Import exact revisions into staging and rerun the gate until source, hashes, reviews and diagnostic isolation pass.
7. Complete the Layer 1 English E0–E6 sequence: blueprint, contracts, objective pipeline,
   learner journey, essay workflow, reviewed content/calibration and hosted release evidence.
8. Complete hosted OAuth, authenticated E2E, keyboard/focus/contrast/mobile, rate-limit/load, restore and owner checks.
9. Run founder alpha, then 3–5 friendly users, then the 10–30 cohort. Do not skip a phase because automation is available.

## Pre-Beta hosted operations checklist

Complete this checklist after the content candidate is ready and before the first
`founder_alpha` invitation. These items are intentionally deferred during bulk content
authoring.

### Candidate and data recovery

- [ ] Freeze the exact Git SHA, course revision and content hash for the candidate.
- [ ] Run the strict Beta release gate and resolve every content, review, publication and
  database-hash failure.
- [ ] Upgrade the Supabase staging project to a tier with managed backups.
- [ ] Confirm a recent scheduled backup and record the actual retention and point-in-time
  recovery settings available on the selected plan.
- [ ] Restore the candidate backup into an empty isolated database, run
  `scripts/backup_restore_drill.py`, record the evidence and destroy the temporary restore.
- [ ] Repeat the backup and restore check after any material pre-Beta schema change.

### Hosted acceptance

- [ ] Verify the deployed SHA, database schema revision, readiness and content hashes.
- [ ] Complete private-window Google OAuth and the authenticated learner journey.
- [ ] Complete keyboard, focus, contrast and 390/768/1440-pixel visual checks.
- [ ] Run the bounded load and intentional rate-limit checks with test identities.
- [ ] Test alert delivery to the primary and backup operator.
- [ ] Rehearse an application rollback to the recorded known-good SHA.

### Tutor release decision

- [ ] Decide whether the first learner Beta ships with the tutor disabled, economy-only, or
  in a separately approved learner pilot. Live premium routing is not required for the core
  learning Beta.
- [ ] If premium routing will advance beyond administrator shadow mode, collect at least 100
  reconciled administrator shadow decisions under one unchanged policy version.
- [ ] Cover all seven tutor modes, difficulty levels 1–5, the approved 20-case calibration
  suite and at least three repeated-confusion paths.
- [ ] Confirm zero premium executions in shadow mode, independently recompute projected cost,
  review safety and pedagogy, and record a go/no-go decision before provisioning live premium
  access.

One shadow decision is one real provider-backed tutor turn, recorded automatically after an
administrator sends a message. It contains the selected teaching mode, question difficulty,
routing score and reasons, recommended model tier, economy tier actually executed, token use,
cost, latency and safety result. It is evidence for later human review, not a person making
100 manual approval decisions.

The seven modes are `clarify_question`, `diagnose_misconception`, `socratic_prompt`,
`alternative_explanation`, `analogous_example`, `solution_explanation` after the server
unlocks the solution, and `lesson_recommendation`. The 100-turn minimum provides a useful
first distribution across modes, difficulty and repeated confusion; it is a calibration
sample rather than a claim of statistical certainty.

The detailed tutor evidence requirements remain in
[TUTOR_SHADOW_ROUTING_STAGING_MILESTONE.md](TUTOR_SHADOW_ROUTING_STAGING_MILESTONE.md).

## Cohort measurements

Use existing immutable attempts, progress, diagnostics and reports to review:

- baseline/endline percentage and outcome changes;
- weekly activation and returning-user activity;
- lesson proficiency and checkpoint completion;
- due-retry completion;
- question reports per 100 attempted questions;
- operational errors and support load by request ID.

The release SHA, course revision/hash, evidence artifacts and final cohort label form the release record. Founder agreement is valid only when the strict gate reports `ready`.
