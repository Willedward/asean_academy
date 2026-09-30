# B5 content release and controlled pilot

**Engineering status: release controls implemented on 30 September 2026; the Beta remains blocked by content and hosted evidence.**

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

## Current evidence and blockers

The current authored source is a valid N1 pilot, not the full Beta catalogue:

| Requirement                        |                         Current source |                              B5 minimum | State   |
| ---------------------------------- | -------------------------------------: | --------------------------------------: | ------- |
| Topic groups                       |                                      1 |                                      19 | Blocked |
| Questions                          |                                     40 |                                   1,900 | Blocked |
| Diagnostic items                   |              No published source forms | 76, split into two disjoint forms of 38 | Blocked |
| Lessons                            |                                      7 |                            7 N1 lessons | Present |
| Lessons with notes                 |                                      1 |                                       7 | Blocked |
| Published course/lessons/questions |                        0 complete sets |           All student-visible revisions | Blocked |
| Local pool inventory               | 19 practice, 11 checkpoint, 10 reserve |            Complete and non-overlapping | Pass    |

The N1 v1 authoring models currently constrain the catalogue to one N1 unit and N1-shaped keys. The 19-topic bank therefore requires a generalized course/question contract before bulk authoring can be imported. The gate exposes this as `source.full_syllabus`; it does not weaken the requirement or infer readiness from a large file count.

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
4. Complete the six remaining N1 lesson notes and confirm all seven include explanation, worked examples, active recall and summary material.
5. Record Mathematics and editorial decisions in the admin review workflow; publish through an audited lifecycle request.
6. Import exact revisions into staging and rerun the gate until source, hashes, reviews and diagnostic isolation pass.
7. Complete hosted OAuth, authenticated E2E, keyboard/focus/contrast/mobile, rate-limit/load, restore and owner checks.
8. Run founder alpha, then 3–5 friendly users, then the 10–30 cohort. Do not skip a phase because automation is available.

## Cohort measurements

Use existing immutable attempts, progress, diagnostics and reports to review:

- baseline/endline percentage and outcome changes;
- weekly activation and returning-user activity;
- lesson proficiency and checkpoint completion;
- due-retry completion;
- question reports per 100 attempted questions;
- operational errors and support load by request ID.

The release SHA, course revision/hash, evidence artifacts and final cohort label form the release record. Founder agreement is valid only when the strict gate reports `ready`.
