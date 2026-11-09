# Codex to Claude handoff — Mathematics authoring cleanup

Updated: 9 November 2026 (Asia/Singapore)

This report records exactly where Codex stopped at William's request. No work described as pending
below has been applied or merged unless explicitly stated.

## Original instruction and status

The requested order was:

1. remove the learner-visible codenames from Sec 2 S1 B001–B004;
2. fix `s1-l1-505`, `s1-l1-515` and `s1-l1-521` so they are distinct and each has exactly one
   defensible centre code;
3. make `review_readiness` block known open category 1–3 findings and learner-visible codenames;
4. release finished claims and regenerate stale/missing reviewer packets;
5. continue charts in this order: Sec 2 N6 B002, Sec 2 S2, Sec 2 N7, Sec 1 S1; and
6. update the **Start here** section of `docs/plan/CURRENT_PROJECT_HANDOFF.md` before stopping.

Steps 1–4 are complete and merged. Step 5 has only reached the claim/preview stage for N6 B002.
Step 6 is not done.

Throughout the completed work, changed questions remained `draft`, revisions were bumped, and no
Mathematics or editorial approval was recorded.

## Merged work

### 1. Sec 2 S1 codename cleanup and CFL-530 fixes

All four content batches were claimed separately and changed in one-batch content PRs:

| Batch | Claim PR | Content PR | Result |
| --- | ---: | ---: | --- |
| `g3-sec2-s1-b001` | [#376](https://github.com/Willedward/asean_academy/pull/376) | [#377](https://github.com/Willedward/asean_academy/pull/377) | 19 remaining prefixes removed |
| `g3-sec2-s1-b002` | [#378](https://github.com/Willedward/asean_academy/pull/378) | [#379](https://github.com/Willedward/asean_academy/pull/379) | 16 remaining prefixes removed |
| `g3-sec2-s1-b003` | [#380](https://github.com/Willedward/asean_academy/pull/380) | [#381](https://github.com/Willedward/asean_academy/pull/381) | 17 remaining prefixes removed |
| `g3-sec2-s1-b004` | [#382](https://github.com/Willedward/asean_academy/pull/382) | [#383](https://github.com/Willedward/asean_academy/pull/383) | 18 remaining prefixes removed |

The 70 affected prompts/titles were not merely stripped. They were given distinct learner-facing
titles or contexts so the duplicate validator would not expose clones that differed only by the old
codename. A live scan after B004 found zero remaining `Bay dataset for` / generated `Bay —` prefixes
across all 104 Sec 2 S1 questions.

The three CFL-530 questions are now distinct and make one code defensible:

- `s1-l1-505`: median only, code `2`, using non-repeating values `6, 7, 8, 9, 40`;
- `s1-l1-515`: mean only, code `1`, using six non-repeating scores
  `62, 68, 71, 75, 80, 88`; and
- `s1-l1-521`: mode only, code `3`, using categorical transport labels
  `bus, walk, bus, cycle, bus`.

For every batch, the canonical answers were accepted, plausible wrong answers were rejected,
authoring validation returned zero errors and zero duplicate findings, focused authoring/chart tests
passed, the reviewer packet was regenerated, and CI was green before merge.

### 2. Review-readiness gate

[PR #384](https://github.com/Willedward/asean_academy/pull/384) is merged.

`question_bank/src/question_bank/review_readiness.py` now blocks a batch when:

- its ledger has a category 1–3 record explicitly marked `open`, `needs_checker_config` or
  `needs_founder_decision`; or
- a current learner-visible title/stem/prompt matches a generated codename such as
  `<Colour> <Tree> Bay —` or `<Colour> <Tree> Bay dataset for ...`.

Historical ledger records marked `confirmed` are deliberately not treated as open. Those records
describe the original audit baseline and were preserved even after earlier content-fix PRs merged.

Tests cover both the unresolved-status filter and live codename detection. The full question-bank
suite at this point passed 928 tests.

### 3. Claims and reviewer-evidence cleanup

[PR #385](https://github.com/Willedward/asean_academy/pull/385) is merged with all CI green.

It did the following:

- released all 74 finished/stale active claims;
- confirmed that all 50 stale packets differed because the exported packet manifest lacked the
  defaulted `bank_role` field;
- regenerated those 50 stale packets;
- generated the 17 packets that were genuinely missing; and
- added a narrow PR-policy path for bulk packet-only maintenance.

The packet-only policy allows multiple batches only when every changed Mathematics-bank file is
under `review_packets/` and none of the affected batches has an active claim. Any source question,
source asset or batch-manifest change still requires exactly one claimed batch per content PR.

Post-cleanup technical readiness was:

- 75 learning batches inspected;
- 75/75 reviewer packets current;
- 26 ready for assignment;
- 45 blocked by a live content, checker, codename or planned-figure gate;
- 4 already approved; and
- 0 active claims on the integration branch immediately after #385.

The 26 technically ready batches are also recorded in
`docs/plan/MATH_REVIEW_READINESS_GATE.md`:

- Sec 1 G1: B001, B002, B004;
- Sec 1 G5: B001, B003, B004;
- Sec 1 N4: B001–B004;
- Sec 1 N6: B001, B003;
- Sec 1 N7: B001–B003;
- Sec 2 G2: B001–B004;
- Sec 2 N2: B001–B004; and
- Sec 2 N6: B001, B003, B004.

This is technical pre-flight evidence only, not Mathematics approval.

Validation for #385 included 929 passing question-bank tests, zero authoring errors, zero duplicate
findings, a valid claim registry, a valid 67-batch packet-only PR check, and all GitHub CI jobs green.

## Current open work: Sec 2 N6 B002

### Git and PR state at stop time

- Integration branch: `feature/bulk-question-authoring-pipeline`.
- Local branch: `claim/g3-sec2-n6-b002-willedward`.
- Open PR: [#386 — claim g3-sec2-n6-b002](https://github.com/Willedward/asean_academy/pull/386).
- The claim reserves the exact future content branch
  `fix/g3-sec2-n6-b002-willedward` for owner `Willedward`.
- Local branch commits:
  - `ac82329b chore(math): claim g3-sec2-n6-b002`
  - `b032fc94 test(math): allow active readiness claims`

The first #386 CI run exposed a brittle repository test that asserted there could never be any
active claims. Production/content logic was not failing. Commit `b032fc94` replaces that assertion
with a stable pending-figure check (`g3-sec1-g1-b003`, `g1-l4-011`). Locally, the corrected readiness
test passed 3/3 and Ruff passed.

At the moment this handoff was written, the second #386 CI run was still in progress. The ownership
and reviewer-evidence job had passed; web, database, browser and domain jobs were still running.
Do not assume #386 is merged: check its current state first. If its second run is green, merge #386
before making any N6 content change.

### Uncommitted local file

The only chart-work file currently present is an untracked request file at repository root:

`/.n6-b002-chart-requests.json`

It contains checked quadratic-graph requests for:

| Question | Roots | Scale `a` | x-range | Keyed result |
| --- | --- | ---: | --- | ---: |
| `n6-l1-510` | `-7, 1` | 1 | `-9` to `3` | axis `x=-3` |
| `n6-l2-515` | `-1, 5` | 1 | `-3` to `7` | reflected root `q=5` |
| `n6-l5-501` | `-2, 6` | 3 | `-4` to `8` | minimum `-48` |

The generator was run **without** `--apply`, writing previews only to
`/private/tmp/n6-b002-chart-preview`. It reported 3 assets, 3 changes, 0 content findings and 0
validation errors. The three SVGs were rendered to PNG and visually checked. The roots, dashed axes
of symmetry and vertices matched the mathematics. Quick Look cropped the title in one thumbnail,
but the source SVG contains the normal title at `y=42`; re-render after applying as a precaution.

No N6 source question, source SVG or reviewer packet has been changed yet.

### Suggested safe resume for N6 B002

1. Check and, if green, merge #386.
2. Switch to updated integration, then create the exact branch
   `fix/g3-sec2-n6-b002-willedward`.
3. Preserve the untracked request file when switching branches.
4. Apply the checked generator request:

   ```bash
   UV_CACHE_DIR=/private/tmp/asean-academy-uv-cache \
     uv run --project question_bank question-bank diagrams-regenerate \
     backend_resources/question_bank/g3_math/secondary_2/n6/v1 \
     --batch g3-sec2-n6-b002 \
     --add n6-l1-510 --add n6-l2-515 --add n6-l5-501 \
     --renderer chart \
     --requests .n6-b002-chart-requests.json \
     --output /private/tmp/n6-b002-chart-apply \
     --apply
   ```

5. Rewrite the prompts/hints so learners actually use the graphs, following the already-merged N6
   examples:
   - `n6-l1-505` for midpoint/axis wording;
   - `n6-l2-508` for reflecting a root across an axis; and
   - `n6-l5-505` for finding a minimum from shown roots plus one supplied point.
6. Keep status `draft`, revision 3, and all review fields unapproved/null.
7. Check canonical and plausible wrong answers, export `g3-sec2-n6-b002`, run full authoring
   validation, chart tests, the staged-file PR check, and open one content PR.

## Remaining requested work after N6 B002

Continue in the user's specified order, one newly claimed batch per content PR.

### Sec 2 S2 — one ledger item

Current readiness flags `g3-sec2-s2-b002` / `s2-l1-507` as needing a figure. Reconcile this before
drawing: `docs/plan/MATH_REVIEW_READINESS_GATE.md` records that the ledger explanation previously
said only `s2-l1-513` needed the new probability-scale chart, and that chart was already added in
PR #371. Do not blindly add a redundant figure to `s2-l1-507`.

### Sec 2 N7 — 23 figures

- B001 (5): `n7-l1-503`, `n7-l2-504`, `n7-l3-503`, `n7-l3-504`, `n7-l4-503`
- B002 (6): `n7-l1-508`, `n7-l2-512`, `n7-l3-510`, `n7-l3-511`, `n7-l3-512`, `n7-l4-508`
- B003 (6): `n7-l1-512`, `n7-l2-521`, `n7-l2-522`, `n7-l3-517`, `n7-l3-518`, `n7-l4-512`
- B004 (6): `n7-l1-518`, `n7-l2-528`, `n7-l3-526`, `n7-l3-527`, `n7-l3-528`, `n7-l5-505`

The new readiness codename detector also finds learner-visible generated `Bay —` titles in Sec 2
N7. Chart work alone will not make these batches ready unless those codenames are separately
resolved in properly scoped content PRs.

### Sec 1 S1 — 32 figures

- B001 (11): `s1-l1-003`, `s1-l2-003`, `s1-l2-004`, `s1-l2-007`, `s1-l2-008`,
  `s1-l3-001`, `s1-l3-004`, `s1-l3-007`, `s1-l3-008`, `s1-l4-001`, `s1-l4-002`
- B002 (5): `s1-l1-009`, `s1-l1-011`, `s1-l2-011`, `s1-l3-012`, `s1-l3-015`
- B003 (6): `s1-l1-013`, `s1-l1-014`, `s1-l2-019`, `s1-l3-019`, `s1-l3-020`,
  `s1-l4-010`
- B004 (10): `s1-l1-019`, `s1-l2-025`, `s1-l2-026`, `s1-l2-027`, `s1-l2-030`,
  `s1-l2-031`, `s1-l3-026`, `s1-l3-027`, `s1-l3-030`, `s1-l4-016`

### Other pending figure blockers not included in the requested chart sequence

- `g3-sec1-g1-b003`: `g1-l4-011`
- `g3-sec1-g5-b002`: `g5-l3-011`

These were already documented as open content/diagram conflicts and should not be forced through
the chart generator without resolving the underlying question issue.

## Final documentation still required

The **Start here** section of `docs/plan/CURRENT_PROJECT_HANDOFF.md` is still outdated. It still says
that no chart generator exists and contains old chart counts/open-item notes. Update it only after
the chart work above reaches an honest stopping point. At minimum it should mention:

- the checked chart generator now exists in `question_bank/src/question_bank/diagrams/charts.py`;
- Sec 2 S1 CFL-026/CFL-530 work is complete;
- the new review-readiness gates;
- the all-current reviewer packets and post-cleanup readiness counts;
- the actual remaining chart batches/counts; and
- the current open PR/claim, if any.

## Non-negotiable workflow rules

- Target PRs at `feature/bulk-question-authoring-pipeline`, not `main`.
- For content: land a claim first, then use the exact branch
  `fix/<batch-id>-willedward`, and change exactly one batch per PR.
- Keep question status `draft`.
- Bump every changed question revision.
- Never write Mathematics/editorial approvals or populate `reviewed_at` / `reviewed_by`.
- Regenerate the affected reviewer packet after every content revision.
- Run `check_answer` with the canonical answer and a plausible wrong answer.
- Run authoring validation and the staged-file `authoring-pr-check` before pushing.
- Preserve unrelated user work and do not force-push shared branches.

## Working-tree snapshot

At stop time:

- current branch: `claim/g3-sec2-n6-b002-willedward`;
- tracked files: clean relative to that branch;
- untracked file: `.n6-b002-chart-requests.json`;
- this handoff file is intentionally created locally for Claude and is not committed or pushed;
- #386 remains open unless its state changes after this timestamp; and
- no local CI watcher or generation command is running.
