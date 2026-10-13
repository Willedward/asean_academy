# Parallel friend work handoff

**Prepared:** 13 October 2026  
**Shared integration branch:** `feature/bulk-question-authoring-pipeline`  
**Audience:** the teammate operating a separate Codex or Claude session  
**Product audience:** secondary-school students across Indonesia and Southeast Asia preparing for ASEAN Scholarship selection tests

## Purpose

This handoff divides work so the founder and teammate can make progress without editing
the same files or silently overwriting each other. GitHub is the coordination source of
truth. Each deliverable uses a separate branch and pull request; no agent should push
directly over another agent's branch.

The teammate's primary assignment is the Layer 2 gamification foundation: experience
points, levels, streaks and the opt-in weekly leaderboard. The optional content assignment
is to expand the eight N5 lesson notes and author one separately claimed N1 question batch.

This handoff contains the complete operational scope for the teammate. Also read these
already-versioned repository documents before changing code or content:

1. [`LESSON_NOTES_CONTENT_STANDARD.md`](./LESSON_NOTES_CONTENT_STANDARD.md)
2. [`MULTI_AUTHOR_QUESTION_PIPELINE.md`](./MULTI_AUTHOR_QUESTION_PIPELINE.md)
3. [`CONTENT_REVIEW_PUBLICATION.md`](./CONTENT_REVIEW_PUBLICATION.md)
4. [`apps/web/AGENTS.md`](../../apps/web/AGENTS.md) before editing the Next.js app

## Non-negotiable coordination rules

1. Start every new branch from the latest
   `origin/feature/bulk-question-authoring-pipeline` after running `git fetch origin`.
2. Keep gamification code, lesson-note work and question authoring in separate branches.
3. Do not combine several question manifests in one pull request. One manifest is the
   smallest question-authoring ownership unit.
4. Do not edit a file already owned by another active branch. Ask the founder to resolve
   ownership before beginning if a file boundary is unclear.
5. Rebase or merge the latest integration branch before final validation. Never force-push
   a shared branch and never rewrite an approval or review branch.
6. Do not record Mathematics approval, editorial approval or publication on behalf of a
   human reviewer. New content remains `draft` or `ready_for_review`.
7. Do not use paid LLM API calls to generate content. Codex or Claude may author repository
   files directly, and all output must pass the local deterministic validators.
8. Do not commit credentials, `.env` files, production learner data or generated caches.
9. Open pull requests into `feature/bulk-question-authoring-pipeline`. Let CI pass before
   merge. The founder decides the final merge order and hosted-review deployment.

## Work allocation

Replace `<github-user>` with the teammate's actual GitHub username, in lowercase where
practical.

| Order | Branch | Scope | May run in parallel with |
| --- | --- | --- | --- |
| 1 | `feature/gamification-ledger-player-<github-user>` | XP ledger, levels and player read API/UI | N5 lessons and N1 questions |
| 2 | `feature/gamification-streaks-<github-user>` | Activity days, streaks, freezes and calendar UI | N5 lessons and N1 questions |
| 3 | `feature/gamification-league-<github-user>` | Private opt-in weekly leaderboard | N5 lessons and N1 questions |
| 4 | `content/g3-sec1-n5-lessons-<github-user>` | Expand N5.1–N5.8 lesson notes | Any gamification branch and N1 questions |
| 5 | `questions/g3-sec1-n1-b001-<github-user>` | Author only N1 batch B001 (22 questions) | Any gamification branch and N5 lessons |

Gamification branches 1–3 are sequential. Branch 2 begins from the merged result of branch
1, and branch 3 begins from the merged result of branch 2. They must not be implemented as
three concurrent branches because they share migrations, reward contracts and UI adapters.

The N5 lesson branch and N1 question branch are optional. They must remain separate from
each other and from gamification even if the same person operates all three sessions.

## Clean checkout

Use a separate clone or worktree so the teammate never operates in the founder's working
directory. A new clone is the simplest option:

```bash
git clone https://github.com/Willedward/asean_academy.git asean_academy_friend
cd asean_academy_friend
git fetch origin --prune --tags
git switch --track origin/feature/bulk-question-authoring-pipeline
git status --short --branch
```

The status must be clean before creating a work branch. Install dependencies using the
versions and lockfiles already committed to the repository; do not upgrade frameworks as
part of these assignments.

## Assignment A — XP ledger and player vertical slice

Create the first branch:

```bash
git switch feature/bulk-question-authoring-pipeline
git pull --ff-only origin feature/bulk-question-authoring-pipeline
git switch -c feature/gamification-ledger-player-<github-user>
```

Implement the **G1 ledger and player vertical slice**. The pull request must:

- add an append-only, idempotent XP ledger and learner reward state in a new migration;
- use the next available migration number rather than renaming an existing migration;
- award the versioned `+10` first-try, `+6` assisted and `+20` retry-review rules inside
  the existing PostgreSQL practice transaction;
- derive level and rank fields from total XP instead of storing independently drifting
  values;
- expose authenticated player summary and cursor-paginated XP history contracts;
- connect the existing top-bar/player UI to live contracts behind
  `ASEAN_ACADEMY_GAMIFICATION`;
- preserve existing academic responses while adding a typed `rewards` envelope where
  appropriate;
- prove duplicate and concurrent submissions create one XP event; and
- include account-deletion and row-level-security coverage for all new learner data.

Likely code ownership for this branch:

- a new `supabase/migrations/*_gamification_ledger.sql` migration;
- new `gamification_*` policy, contract, repository and router modules under
  `services/learning_api/src/learning_api/`;
- focused changes to `postgres_practice.py`, practice contracts and application router
  registration;
- generated OpenAPI artifacts when the API changes;
- live adapters for existing player/XP components in `apps/web/src/beta-kit/`; and
- focused API, PostgreSQL, frontend and browser tests.

Do not implement streaks, league, quests, badges, wardrobe or notifications in this branch.
The exit condition is one correct answer producing exactly one durable award under request
retries, with the live player UI updating after refresh.

## Assignment B — streak calendar

Begin only after Assignment A is merged:

```bash
git fetch origin
git switch -c feature/gamification-streaks-<github-user> \
  origin/feature/bulk-question-authoring-pipeline
```

Implement **G2 streaks and settings**:

- materialize qualifying activity days from eligible XP events;
- calculate current and best streaks using `Asia/Singapore` for the first Beta;
- earn one freeze after activity on five distinct Monday–Sunday dates, capped at two;
- consume freezes deterministically without a midnight scheduler;
- expose the month calendar and game-settings contracts;
- wire the existing streak chip, dashboard week and streak screen to live data; and
- test date, month, year, missed-day, freeze and time-zone boundaries.

The exit condition is a server-authoritative calendar that survives reloads and cannot be
advanced by browser-only state or non-qualifying bonus events.

## Assignment C — private weekly leaderboard

Begin only after Assignment B is merged:

```bash
git fetch origin
git switch -c feature/gamification-league-<github-user> \
  origin/feature/bulk-question-authoring-pipeline
```

Implement the **G3 weekly Beta League**:

- make league participation explicitly opt-in and hidden by default;
- run weeks Monday 00:00 to Monday 00:00 in `Asia/Singapore`;
- hide the board when fewer than five learners opt in;
- redact display names and never expose email addresses;
- cap competitive score at 200 eligible XP per learner per local date;
- give equal scores equal visible ranks with deterministic display ordering;
- remove opted-out learners from subsequent responses immediately; and
- wire the existing dashboard league card and full league screen to live contracts.

The exit condition is a privacy-safe leaderboard whose score can be recomputed from the XP
ledger and whose enablement does not affect academic access or marks.

## Assignment D — N5 lesson-note expansion

Create this branch directly from the current integration branch:

```bash
git fetch origin
git switch -c content/g3-sec1-n5-lessons-<github-user> \
  origin/feature/bulk-question-authoring-pipeline
```

Own only these lesson files and the minimum course/fixture metadata required by their new
revision:

```text
backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n5-lesson-01.json
...
backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n5-lesson-08.json
```

Each lesson currently has four short sections and is flagged `lesson_notes_thin`. Expand
each to at least the baseline in `LESSON_NOTES_CONTENT_STANDARD.md`: six substantive
sections, two explanations, two explicit worked examples with verification, one
deterministic active-recall check, one summary, and at least 2,500 authored characters.

Requirements:

- preserve the exact outcome scope and stable key;
- increment every changed lesson revision;
- bump the enclosing course revision once for the complete N5 change;
- use clear international English and Southeast-Asia-neutral contexts;
- treat Singapore syllabus labels as internal calibration references, not the learner's
  country or school system;
- keep all new content in draft review state;
- verify every active-recall canonical answer through the repository checker; and
- do not edit N1–N4, N6–N7, geometry, statistics or question files in this branch.

Validate with:

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank question-bank course-registry-validate
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank question-bank course-validate
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank pytest question_bank/tests
```

The exit condition is N5.1–N5.8 producing no `lesson_notes_thin` warning while remaining
unapproved drafts in the admin review queue.

## Assignment E — one N1 question batch

The first available allocation is `g3-sec1-n1-b001`, containing 22 reserved questions.
Question ownership must be registered before any question or manifest is edited.

First determine the authenticated GitHub username:

```bash
gh api user --jq .login
```

From a short claim branch based on the latest integration branch, run:

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank question-bank authoring-claim \
  g3-sec1-n1-b001 \
  --owner <github-user> \
  --branch questions/g3-sec1-n1-b001-<github-user>
```

Commit only
`backend_resources/question_bank/authoring/batch-claims-v1.json`, open a small pull request
into `feature/bulk-question-authoring-pipeline`, and wait for that claim to merge. Then
create the exact registered question branch from the refreshed integration branch.

On the question branch:

- author only the 22 keys reserved by `g3-sec1-n1-b001`;
- change its manifest from `planned` to `draft` while working, then
  `ready_for_review` only when all slots validate;
- record truthful generator provenance naming the teammate's Codex or Claude workflow;
- use the existing house rules and schema without paying for or invoking a live model API;
- execute all canonical and accepted answers;
- scan the complete catalogue for exact and near duplicates;
- export the reviewer packet; and
- leave Mathematics and editorial decisions unset.

Run all authoring checks before opening the one-batch pull request:

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank question-bank authoring-claims-validate
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank question-bank authoring-validate
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank ruff check question_bank/src question_bank/tests
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank pytest question_bank/tests
```

Release the claim in a small follow-up pull request after the authored batch merges.

## Validation for every code pull request

Run the smallest relevant checks while developing, then the full affected suites before
opening a pull request:

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project services/learning_api ruff check \
  services/learning_api/src services/learning_api/tests
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project services/learning_api pytest services/learning_api/tests
corepack pnpm --filter @asean-academy/web lint
corepack pnpm --filter @asean-academy/web typecheck
corepack pnpm --filter @asean-academy/web test
corepack pnpm --filter @asean-academy/web build
```

When a migration changes, also apply all migrations to an empty disposable PostgreSQL
database and run the repository integration suite. When an API contract changes, regenerate
and commit the OpenAPI client/types using the existing repository command; CI rejects stale
generated contracts.

## Pull-request and handback format

Every pull request must state:

- concrete before/after behaviour;
- target integration branch;
- exact owned scope and any files changed outside the expected boundary;
- migration and API-contract effects;
- commands run and their results;
- remaining risks or intentionally deferred work; and
- screenshots or browser-test evidence for visible UI changes.

The teammate should send the founder the pull-request URL and commit SHA. The founder reviews
and merges one branch at a time. If CI or a rebase creates a conflict, stop and report the
files involved; do not resolve a semantic conflict by choosing one entire side.

## Copy-paste prompt for the teammate's Codex or Claude

```text
You are working in Willedward/asean_academy as the teammate implementation agent.
Read docs/plan/PARALLEL_FRIEND_WORK_HANDOFF.md completely, then read every document it
lists for your selected assignment. Obey apps/web/AGENTS.md for any web change.

Start from the latest origin/feature/bulk-question-authoring-pipeline in a clean clone.
Work on exactly one assignment and its exact branch. Do not edit files owned by another
assignment, do not record human content approvals, do not publish learner content, do not
use a paid model API, and do not commit secrets or learner data.

Persist until the assignment's exit condition is met. Run all affected validation, commit
the complete change, push only your branch, and open a pull request targeting
feature/bulk-question-authoring-pipeline. Report the PR URL, commit SHA, validations and
any unresolved risk. Never merge or force-push a shared branch yourself.
```

## Founder-side ownership while these branches are active

While the teammate owns a listed branch, the founder's Codex should avoid its files and
continue in a disjoint unit. Good founder-side work includes N7 or S1 lesson expansion,
another separately claimed question manifest, content review, tutor calibration, or release
verification. Before either side starts new work, fetch the integration branch and check
open claims and pull requests again.
