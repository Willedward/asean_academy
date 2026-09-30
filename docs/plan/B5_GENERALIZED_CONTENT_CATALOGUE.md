# B5 generalized Mathematics content catalogue

**Implementation status (30 September 2026): engineering foundation complete; syllabus and content authoring remain incomplete.**

This milestone removes the N1-only constraints from the Git-authored question and course pipeline before the team expands the Beta bank to roughly 1,900–2,850 questions. Existing N1 source files remain valid and keep their current immutable content hashes.

## Implemented contracts

The canonical syllabus source is `backend_resources/syllabi/g3_math/v1/catalogue.json`. It currently contains the 13 topic groups and 87 outcomes that were supplied and confirmed in the repository. The catalogue records an expected total of 19 topics and remains `draft`; publication validation fails until the six missing topic definitions are supplied. No missing syllabus content was inferred.

Question identities now support any confirmed `N`, `G`, or `S` topic, both Secondary 1 and Secondary 2, and bank revisions such as `g3-sec2-g4-v1`. Stable question keys carry the topic and difficulty, while the validator checks those fields against the bank blueprint and syllabus catalogue. Calculator use may be either enabled or disabled.

Every bank blueprint has a `bank_role` of `learning` or `diagnostic`. The existing N1 bank is explicitly a learning bank. PostgreSQL migration `202609300015_generalized_question_catalogue.sql` adds that role and an index used to isolate student learning pools from diagnostic forms.

Course contracts now support multiple ordered topic units. Each unit has its own question-pool manifest and bank. The legacy single `question_pools.json` layout remains accepted; future multi-unit sources place one manifest per unit under `question_pools/*.json`. The collection preserves the legacy one-manifest serialization so N1 course revision hashes do not change.

## Validation and imports

Use these commands from the repository root:

```bash
uv run --project question_bank question-bank catalogue-validate
uv run --project question_bank question-bank catalogue-validate --publish
uv run --project question_bank question-bank catalogue-schema
```

Draft validation currently succeeds with a warning and reports:

- 13 confirmed topic definitions out of 19 expected;
- six unconfirmed topic definitions;
- one authored topic-level bank;
- 40 authored questions.

Publication validation is deliberately blocked by the incomplete syllabus, draft bank/questions, and incomplete course content.

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

## Remaining founder input and content work

Engineering can accept all 19 topics now, but the source of truth contains only 13. The team must supply the canonical codes, titles, strand ordering and Secondary 1/2 outcomes for the remaining six topics before the catalogue can become active. The team must then author and review the learning banks, the 76 isolated diagnostic items, lesson notes, examples, active-recall sections, hints and solutions.

The B5 release gate still measures authored course units and reviewed question inventory. A topic definition alone does not count as Beta coverage; it needs a valid bank, course unit and reviewed content.
