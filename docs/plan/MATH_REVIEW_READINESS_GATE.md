# Mathematics review-readiness gate

Updated: 6 November 2026 (Asia/Singapore)

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
5. every required figure named by `docs/plan/CONTENT_FIX_LEDGER.json` is present.

An active claim produces `in_progress`, not `ready`. Missing, incomplete, invalid or stale reviewer
evidence produces `blocked` once no author is actively working on the batch. An `approved` batch is
reported as `complete` and is not put back into the review queue.

Warnings remain visible but do not silently become approvals. Planned-figure evidence is
conservative: if the ledger and its explanatory note disagree, the batch stays out of the ready
list until the ledger is reconciled. This currently catches the stale `s2-l1-507` worklist entry;
the same ledger record says only `s2-l1-513` needed the new probability-scale chart.

## Initial result

The first run after Mathematics chart PRs #371 and #372 merged found:

- 75 learning batches inspected;
- 4 ready for assignment;
- 67 still carrying active claims;
- 4 already approved;
- 64 planned figures still absent; and
- no catalogue validation error.

The four technically ready batches were Secondary 2 S1 B001–B004. This does **not** mean the other
content is mathematically unsuitable. It means its editing claim, reviewer evidence or planned
figure work is not yet closed. The next readiness-cleanup pass should release completed claims,
refresh stale or missing packets, and reconcile worklist exceptions before William assigns the
next bank to a reviewer.
