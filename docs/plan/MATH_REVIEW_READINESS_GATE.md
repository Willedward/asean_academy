# Mathematics review-readiness gate

Updated: 9 November 2026 (Asia/Singapore)

This gate answers one narrow question: **is a Mathematics batch technically safe to hand to a
human reviewer now?** It records no Mathematics or editorial decision and cannot approve or publish
content.

Run it from the repository root:

```bash
UV_CACHE_DIR=/private/tmp/asean-uv-cache \
  uv run --project question_bank question-bank review-readiness \
  --output /private/tmp/math-review-readiness
```

The command writes `report.json` for automation and `summary.md` for the reviewer handoff. It exits
successfully when the audit itself is structurally valid, even if some batches are not ready. Add
`--require-all-ready` when a release or CI job must fail until every learning batch is either ready
or already approved. Diagnostic batches are separate by default; add `--include-diagnostics` to
include them.

## What blocks assignment

A learning batch is marked `ready` only when all of these are true:

1. its manifest and questions pass the authoring validator;
2. its manifest status is `ready_for_review`;
3. it has no active authoring claim, so nobody is still changing its source;
4. its committed reviewer packet exists and exactly matches the current manifest, questions and
   referenced assets; and
5. every required figure named by `docs/plan/CONTENT_FIX_LEDGER.json` is present;
6. it has no category 1-3 ledger finding whose status explicitly remains `open`,
   `needs_checker_config` or `needs_founder_decision`; and
7. no question title or learner-visible prompt still contains a generated codename such as
   `<Colour> <Tree> Bay —` or `<Colour> <Tree> Bay dataset for ...`.

An active claim produces `in_progress`, not `ready`. Missing, incomplete, invalid or stale reviewer
evidence produces `blocked` once no author is actively working on the batch. An `approved` batch is
reported as `complete` and is not put back into the review queue.

Warnings remain visible but do not silently become approvals. Planned-figure evidence is
conservative: if the ledger and its explanatory note disagree, the batch stays out of the ready
list until the ledger is reconciled. This currently catches the stale `s2-l1-507` worklist entry;
the same ledger record says only `s2-l1-513` needed the new probability-scale chart.

The ledger's historical `confirmed` status is audit evidence, not an unresolved-state flag: earlier
content PRs deliberately preserved it after applying fixes. The readiness gate therefore blocks
only the explicit unresolved statuses above. Codename detection is live against current question
content, so a removed prefix stops blocking without rewriting the historical audit record.

## Initial result

The first run after Mathematics chart PRs #371 and #372 merged found the following historical
baseline, before the open-finding and codename gates were added:

- 75 learning batches inspected;
- 4 ready for assignment;
- 67 still carrying active claims;
- 4 already approved;
- 64 planned figures still absent; and
- no catalogue validation error.

The four batches then reported ready were Secondary 2 S1 B001–B004. Their learner-visible codenames
and three ambiguous centre questions were subsequently fixed in PRs #377, #379, #381 and #383.
This historical count must not be used as the current assignment list. Regenerate the report after
claim and packet cleanup before William assigns the next bank to a reviewer.

## Post-cleanup result on 9 November 2026

After releasing all 74 finished claims and regenerating the 50 stale plus 17 missing reviewer
packets, the gate reports:

- 75 learning batches inspected, all with current reviewer packets;
- 26 ready for assignment;
- 45 blocked by a live content, checker, codename or planned-figure gate;
- 4 already approved; and
- 0 active claims.

The 26 technically ready batches are:

- Secondary 1 G1: B001, B002 and B004;
- Secondary 1 G5: B001, B003 and B004;
- Secondary 1 N4: B001–B004;
- Secondary 1 N6: B001 and B003;
- Secondary 1 N7: B001–B003;
- Secondary 2 G2: B001–B004;
- Secondary 2 N2: B001–B004; and
- Secondary 2 N6: B001, B003 and B004.

This is still technical pre-flight evidence, not Mathematics approval. Re-run the command after
each content or chart PR because changing a question revision makes its reviewer packet stale until
it is exported again.

The pull-request policy permits a bulk reviewer-packet refresh only when every changed file inside
the Mathematics bank is under `review_packets/` and none of the affected batches has an active
claim. Any source question, manifest or source-asset change continues to require exactly one claimed
batch per PR.
