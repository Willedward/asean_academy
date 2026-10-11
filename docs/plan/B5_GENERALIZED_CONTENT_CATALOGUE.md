# B5 generalized Mathematics content catalogue

**Implementation status (10 October 2026): engineering foundation complete; N1 and N2 are integrated drafts, while the remaining syllabus content is incomplete.**

This milestone removes the N1-only constraints from the Git-authored question and course pipeline before the team expands the Beta bank to roughly 1,900–2,850 questions. Existing N1 source files remain valid and keep their current immutable content hashes.

## Implemented contracts

The canonical machine-readable syllabus source is `backend_resources/syllabi/g3_math/v1/catalogue.json`, with a permanent human-readable transcription in `docs/reference/G3_MATHEMATICS_SYLLABUS.md`. The supplied official pages confirm 13 unique topic codes, 19 level-specific topic groups and 87 outcomes. The catalogue is complete and active. A topic taught at both Secondary One and Secondary Two counts as two groups for authoring and diagnostic coverage.

Question identities now support any confirmed `N`, `G`, or `S` topic, both Secondary 1 and Secondary 2, and bank revisions such as `g3-sec2-g4-v1`. Stable question keys carry the topic and difficulty, while the validator checks those fields against the bank blueprint and syllabus catalogue. Calculator use may be either enabled or disabled.

Every bank blueprint has a `bank_role` of `learning` or `diagnostic`. The existing N1 bank is explicitly a learning bank. PostgreSQL migration `202609300015_generalized_question_catalogue.sql` adds that role and an index used to isolate student learning pools from diagnostic forms.

The full course registry now defines two courses, 19 ordered level-specific topic groups, and 87 outcome-linked lesson slots. Course contracts also support multiple ordered authored topic units. Each authored unit has its own question-pool manifest and bank. The legacy single `question_pools.json` layout remains accepted; future multi-unit sources place one manifest per unit under `question_pools/*.json`. The collection preserves the legacy one-manifest serialization so N1 course revision hashes do not change.

## Validation and imports

Use these commands from the repository root:

```bash
uv run --project question_bank question-bank catalogue-validate
uv run --project question_bank question-bank catalogue-validate --publish
uv run --project question_bank question-bank catalogue-schema
```

Catalogue validation succeeds and reports:

- 13 of 13 unique topic definitions;
- 19 of 19 level-specific topic groups;
- 87 syllabus outcomes;
- two authored topic-level banks;
- 144 authored questions.

The 104-question N2 bank matches its complete blueprint distribution. The remaining catalogue warnings describe the intentionally partial 40-question N1 blueprint.

Publication validation remains deliberately blocked by the draft bank/questions and incomplete course content.

Once `DATABASE_URL` points to a migrated database, the catalogue-wide import is:

```bash
uv run --project question_bank question-bank catalogue-import-db
```

The importer runs one transaction that upserts the curriculum, topics, outcomes, bank metadata and immutable question revisions. The ordinary `import-db` command now uses the same metadata-aware path for one bank. Local API bootstrap also uses this importer, so adding a valid bank no longer requires hand-written topic or outcome seed SQL.

## Adding the next bank

1. Add the confirmed topic and outcome definitions to the syllabus catalogue if they are not already present.
2. Create `backend_resources/question_bank/g3_math/<school_level>/<topic>/v1/blueprint.json`.
3. Set `bank_role` to `learning` or `diagnostic`.
4. Add question JSON under the bank's `questions/` directory using generic stable keys such as `n2-l1-001`.
5. Run `catalogue-validate` after every batch. Cross-bank stable-key and authored-content duplicates fail validation.
6. For a learning unit, add its lesson files and one pool manifest. Course validation checks unit/topic/bank alignment, pool capacity, lesson outcomes and complete non-overlapping allocation.
7. Import only after validation and human review pass. Published validation remains the release gate.

## Remaining content work

No additional syllabus definitions are required for the supplied Secondary One and Secondary Two Beta scope. The team must now author and review the remaining 17 level-specific topic groups, review the pending N2 batches and lessons, create the 76 isolated diagnostic items, and complete the remaining lesson notes, examples, active-recall sections, hints and solutions.

The B5 release gate still measures authored course units and reviewed question inventory; planned registry entries do not count as released content. A topic definition alone does not count as Beta coverage; it needs a valid bank, course unit and reviewed content.

The registry contract, coverage, identifiers and rollout rules are documented in [FULL_SEC1_SEC2_COURSE_REGISTRY.md](FULL_SEC1_SEC2_COURSE_REGISTRY.md).
