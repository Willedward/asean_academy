# N1 question bank storage and schema

## Storage decision

PostgreSQL is the authoritative production store for generated and reviewed questions. It stores curriculum mappings, question versions, multipart parts, marks, answer-checking rules, two-stage hints, worked solutions, and diagram metadata.

The repository also keeps question JSON files. These files are the review and interchange format: they can be code-reviewed, validated in CI, and loaded into PostgreSQL by a seed/import command. They are not a second production database.

Diagram binaries belong in object storage. The first N1 diagrams will normally be SVG number lines. PostgreSQL stores their object path, accessibility text, checksum, dimensions, and a JSON specification that can be used to reproduce them.

```text
reviewed JSON in Git
        |
        | validate + import
        v
PostgreSQL question bank ----> backend practice API ----> application
        |
        +---- asset metadata ----> object storage (SVG/PNG/WebP)
```

The application should obtain question content from the backend API. Answer specifications and worked solutions must not be included in the unanswered-question response.

## N1 scope

The initial bank is `g3-sec1-n1-v1`, aligned to Singapore Secondary 1 G3 Mathematics, topic N1: Numbers and their operations. It contains 40 fixed, calculator-allowed, structured questions:

| Syllabus outcome | Level 1 | Level 2 | Level 3 | Total |
| --- | ---: | ---: | ---: | ---: |
| 1.1 Primes and prime factorisation | 3 | 2 | 1 | 6 |
| 1.2 HCF, LCM, squares, cubes and roots | 3 | 3 | 2 | 8 |
| 1.3 Number sets and four operations | 3 | 3 | 2 | 8 |
| 1.4 Calculator calculations | 1 | 2 | 1 | 4 |
| 1.5 Representation and ordering on a number line | 2 | 1 | 1 | 4 |
| 1.6 Inequality symbols | 1 | 1 | 1 | 3 |
| 1.7 Approximation and estimation | 2 | 3 | 2 | 7 |
| **Total** | **15** | **15** | **10** | **40** |

Difficulty is a bank-design level, not a predicted student ability:

- Level 1: direct use of one taught idea, with familiar representation and little interpretation.
- Level 2: two or more linked steps, a less direct representation, or a routine word problem.
- Level 3: unfamiliar structure, justification, constraints, or a multi-step problem requiring a choice of method.

## Relational model

The migration at `supabase/migrations/202609200001_n1_question_bank.sql` creates these groups.

### Curriculum

- `curriculum_versions` identifies the syllabus snapshot used to author a bank.
- `syllabus_topics` stores stable topic codes such as `N1`, shared across school levels.
- `syllabus_outcomes` stores assessable outcome codes such as `1.1` through `1.7` and the school level at which each outcome is taught.

The N1 identifiers match the deterministic UUIDs already used by `question_categorizer`, so imported categorisation records can be joined without matching free-form labels.

### Bank and versioned question content

- `math_question_banks` defines the 40-question collection and its intended difficulty distribution.
- `math_questions` holds stable question identity, its blueprint-level primary outcome, difficulty, and lifecycle status.
- `math_question_versions` holds an immutable reviewable revision of the title, calculator policy, question type, stem, and related assessed content. Exactly one version can be current.
- `math_question_parts` holds independently answered multipart prompts and their marks.
- `math_question_outcomes` maps each part to one primary and optional secondary syllabus outcomes.

A revision is created when assessed content changes. Existing attempts continue to point to the version they saw. The question-level primary outcome is used to measure the bank's 40-question allocation; individual parts can map to that outcome or another relevant outcome.

### Hints, answers, and solutions

- `math_question_hints` stores exactly two progressive hints for each part. Stage 1 points to the relevant idea; stage 2 gives a more explicit method without revealing the final answer.
- `math_answer_specs` stores deterministic answer-checking rules.
- `math_solution_steps` stores a worked solution and optional `B`, `M`, or `A` mark annotations.

The initial response types are:

1. `numeric`: integers, terminating decimals, fractions, percentages, values with tolerances, and answers rounded to decimal places or significant figures.
2. `algebraic_expression`: content entered through the math-expression field. Its checker mode can require symbolic equivalence, prime-factor form, an ordered numeric list, or an exact relation. This covers algebraic expressions as well as N1 ordering and inequality tasks without adding another UI control.

The checker mode is separate from the input control. For example, a prime-factorisation checker verifies that every base is prime and that the product has the required value; plain numeric equivalence would incorrectly accept the original composite number. Checker-specific options live in `checker_config` and must be validated by the importer.

Multipart questions use one `math_question_parts` row and one answer specification per input field. Marks are awarded per part. Hint use is recorded separately from correctness and does not automatically reduce marks.

### Content and mathematics rendering

Prompts, hints, and solutions use ordered rich-content blocks rather than a complete LaTeX document:

```json
[
  {"type": "text", "text": "Express "},
  {"type": "inline_math", "latex": "360"},
  {"type": "text", "text": " as a product of prime factors."}
]
```

This keeps prose separate from mathematics. The client renders `inline_math` and `display_math` with KaTeX or MathJax, escapes ordinary text, and resolves `asset_ref` blocks through question asset metadata. Raw HTML and executable LaTeX commands are not part of the contract.

## Repository format

The source format is defined by:

- `backend_resources/question_bank/schema/question-v1.schema.json`
- `backend_resources/question_bank/g3_math/secondary_1/n1/v1/blueprint.json`

Generated questions should be placed under:

```text
backend_resources/question_bank/g3_math/secondary_1/n1/v1/questions/
```

One file per question keeps review diffs small. Suggested names are `n1-l1-01.json` through `n1-l3-10.json`. The database importer will derive content checksums, create UUIDs, and upsert by `bank_key`, `stable_key`, and question version.

## Publication checks

A bank must remain in `draft` until an application validator confirms all of the following:

- exactly 40 questions with the required 15/15/10 difficulty split;
- the outcome allocation in the blueprint;
- at least one primary outcome per part;
- part marks sum to the question total;
- exactly two hints, in stages 1 and 2, per part;
- one compatible answer specification per part;
- worked-solution mark values do not exceed the part marks;
- all referenced assets exist and have matching checksums;
- all LaTeX fragments render successfully;
- every numeric and algebraic checker passes positive, equivalent-form, boundary, and incorrect-answer tests;
- every question has completed mathematical and editorial review.

Row-level security is enabled by the migration without browser-facing table policies. The backend service imports and reads the full records. A later API endpoint should expose prompts first, then return hints or solutions according to the attempt state.

## Implementation status and next slice

The `question_bank` package now provides JSON Schema and cross-record validation, deterministic checking for the N1 answer formats, a local KaTeX reviewer preview, and transactional PostgreSQL import. All 40 fixed questions exist as drafts with the required 15/15/10 difficulty distribution. They exercise exact numbers, significant figures, prime-factor form, ordered values, inequalities, multipart marking, two-stage hints, worked solutions, and an SVG number line.

The next content step is founder mathematical and editorial review in the local preview. The next application step is an attempt schema and practice API that reference `math_question_versions` and `math_question_parts`, preserving exactly which revision the learner answered. Runtime question selection belongs in that API; the OCR extractor remains an optional offline pipeline for converting permitted PDFs into candidate source records.
