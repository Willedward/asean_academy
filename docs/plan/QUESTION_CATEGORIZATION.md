# Mathematics question categorization plan

**Implementation status (16 September 2026):** The local `rules_v1` implementation
is in [`question_categorizer`](../../question_categorizer/README.md) on the
`question_categorier` branch. It contains the 13 supplied topic codes, 87
Secondary One/Two outcomes, question-part splitting, checked-review selection,
SQLite/PostgreSQL persistence, evidence and version tracking, and human assignment
confirmation/rejection. The taxonomy remains draft until the complete official
syllabus and a founder-labelled golden set are available.

## Decision

Categorize against the fixed syllabus codes supplied by the founder, for example
`N1 Numbers and their operations`, `N2 Ratio and proportion`, and
`G1 Angles, triangles and polygons`. Store the taxonomy and assignments in
PostgreSQL. Do not introduce a vector database for this taxonomy.

The first classifier should be local and reviewable:

1. deterministic phrase, notation and content-type rules produce candidates;
2. an optional local text-embedding model reranks those few candidates in memory;
3. weak or conflicting results remain `unclassified` for a human to resolve;
4. a text-model API is an optional later experiment, not a dependency of ingestion.

This is a separate backend feature from OCR and is implemented on the requested
`question_categorier` branch. It remains a module/job in the backend repository;
it does not need to become a separately deployed service.

## Taxonomy represented by the supplied syllabus pages

Use `secondary_1` and `secondary_2` for levels so that the syllabus topic code
`S1` cannot be confused with Secondary One.

| Strand | Code | Display name | Supplied outcomes by level |
| --- | --- | --- | --- |
| Number and Algebra | N1 | Numbers and their operations | Secondary 1: 1.1–1.7 |
| Number and Algebra | N2 | Ratio and proportion | Secondary 1: 2.1–2.3; Secondary 2: 2.4–2.5 |
| Number and Algebra | N3 | Percentage | Secondary 1: 3.1–3.6 |
| Number and Algebra | N4 | Rate and Speed | Secondary 1: 4.1–4.3 |
| Number and Algebra | N5 | Algebraic expressions and formulae | Secondary 1: 5.1–5.8; Secondary 2: 5.9–5.16 |
| Number and Algebra | N6 | Functions and graphs | Secondary 1: 6.1–6.5; Secondary 2: 6.6–6.7 |
| Number and Algebra | N7 | Equations and inequalities | Secondary 1: 7.1–7.4; Secondary 2: 7.5–7.10 |
| Geometry and Measurement | G1 | Angles, triangles and polygons | Secondary 1: 1.1–1.7 |
| Geometry and Measurement | G2 | Congruence and similarity | Secondary 2: 2.1–2.5 |
| Geometry and Measurement | G4 | Pythagoras' theorem and trigonometry | Secondary 2: 4.1–4.3 |
| Geometry and Measurement | G5 | Mensuration | Secondary 1: 5.1–5.5; Secondary 2: 5.6 |
| Statistics and Probability | S1 | Data handling and analysis | Secondary 1: 1.1–1.4; Secondary 2: 1.5–1.10 |
| Statistics and Probability | S2 | Probability | Secondary 2: 2.1–2.2 |

This is a draft subset based on the supplied images. Import the complete official
syllabus before calling taxonomy version 1 complete. A question about a concept
absent from this subset, such as a later-level circle theorem, must remain
`unclassified`; the classifier must not force it into the nearest available code.

## Stable identifiers

Keep the printed codes as data, not as the only primary key. Examples:

```text
topic key:     g3_math.n5
outcome key:   g3_math.secondary_2.n5.5_16
display:       N5 Algebraic expressions and formulae
outcome:       5.16 Addition and subtraction of algebraic fractions ...
version:       g3_math_v1
```

`N5` remains the same broad topic across levels. The outcome carries its level.
This lets a question be categorized broadly as `N5` while also recording the
specific Secondary Two learning outcome `5.16`.

## Data model

The application database should contain:

```text
syllabus_versions
  id, key, title, status, source_reference, effective_date

syllabus_topics
  id, syllabus_version_id, code, strand, name, order

syllabus_outcomes
  id, topic_id, level, outcome_code, description, keywords, examples, order

question_parts
  id, question_id, label, checked_text, checked_latex, source_fingerprint

question_topics
  id, question_id, question_part_id nullable, topic_id, outcome_id nullable,
  role, status, confidence, source, classifier_version, taxonomy_version,
  evidence jsonb, reviewed_by, reviewed_at, created_at
```

Use `role = primary | secondary`, `status = suggested | confirmed | rejected`,
and `source = rules | local_model | api_model | human`. Keep past assignments so
a taxonomy upgrade or classifier rerun remains auditable.

Question parts matter. One source question can test unrelated outcomes. Assigning
only one topic to the whole question would make questions 6 and 7 in Beasiswa
misleading.

## Classifier input and output

Classification should consume the latest human-checked OCR revision when one
exists. Machine OCR may produce suggestions before review, but those suggestions
must not become confirmed curriculum data.

Example output:

```json
{
  "question_id": "...",
  "question_part_id": "...",
  "taxonomy_version": "g3_math_v1",
  "source_level": "secondary_2",
  "primary": {
    "topic_code": "N5",
    "outcome_code": "5.16",
    "confidence": 0.93
  },
  "secondary": [],
  "evidence": [
    {"kind": "phrase", "value": "single fraction"},
    {"kind": "notation", "value": "algebraic denominators"}
  ],
  "status": "suggested",
  "classifier_version": "rules_v1"
}
```

Every returned topic and outcome ID must exist in the active taxonomy version.
The classifier cannot create labels.

## Local candidate generation

Normalize prose and LaTeX without discarding mathematical operators. Generate
candidates from evidence such as:

| Evidence | Candidate |
| --- | --- |
| prime, HCF, LCM, square root, cube root | N1 |
| ratio, proportion, map scale, inversely proportional | N2 |
| percentage increase/decrease, profit, discount, reverse percentage | N3 |
| average speed, m/s, km/h | N4 |
| expand, factorise, algebraic fraction, change the subject | N5 |
| gradient, coordinates, graph, maximum point, quadratic function | N6 |
| solve, equation, inequality, simultaneous equations | N7 |
| angles, triangle, polygon, parallel lines, quadrilateral | G1 |
| congruent, similar, enlargement, scale factor | G2 |
| Pythagoras, sine, cosine, tangent, right-angled triangle | G4 |
| perimeter, area, volume, surface area | G5 |
| histogram, stem-and-leaf, mean, median, grouped data | S1 |
| probability, possible outcomes, chance | S2 |

Also extract structural signals: tables, graphs, geometry diagrams, degree signs,
inequality symbols, coordinate pairs, units and formula shapes. Require more than
one weak signal where terms are ambiguous. For example, “rate” by itself is not
enough to select N4 because interest rates and work rates appear elsewhere.

Apply level compatibility after candidate generation. A source marked Secondary
Two may use Secondary One prerequisites, so level is a ranking signal rather than
an absolute rejection rule.

## Optional semantic reranker

If deterministic rules leave several candidates, a small local sentence-embedding
model can compare the checked question with each outcome description and a few
founder-labelled examples. There are only dozens of outcomes, so all vectors fit
in process memory and ordinary PostgreSQL rows are sufficient. A dedicated vector
database adds operational work without improving this use case.

Do not let semantic similarity override a strong exact rule silently. Store the
rule matches, similarity scores and selected candidates in `evidence`.

## When an API model may help

A schema-constrained text-model call can be tested later for questions that remain
ambiguous after local rules. It would receive only the checked question and the
small allowed candidate list, and it must return one of those IDs or
`unclassified`. This is separate from the OCR vision backend.

Do not make that API call the initial design. It adds per-question cost, external
data processing and model-version drift. Introduce it only if a labelled evaluation
shows that local classification cannot meet the target and the improvement is
large enough to justify those costs.

## Confidence and review gate

Start with conservative rules and calibrate thresholds on labelled questions.
Send a suggestion to review when:

- no topic has sufficient evidence;
- the first and second candidates are too close;
- the source level conflicts with the chosen outcome;
- different subparts have different topics but parts were not segmented;
- OCR or formula blocks used for classification are still unchecked;
- the concept is absent from the active taxonomy.

Only a human confirmation or a classifier version that has passed the production
quality gate should set a current assignment to `confirmed`. The existing target
is at least 95% primary-topic accuracy on a founder-labelled golden set. Measure
fine outcome accuracy separately; it will usually be lower than broad-code accuracy.

## Provisional Beasiswa mapping

This mapping illustrates the schema and needs founder review:

| Question/part | Broad topic | Outcome candidate | Notes |
| --- | --- | --- | --- |
| 1 | N5 | Secondary 2, 5.16 | Addition/subtraction of algebraic fractions |
| 2 | G1 | Secondary 1, 1.6 | Interior-angle sum of a convex polygon; triangle reasoning may be secondary |
| 3 | N5 | Secondary 2, 5.12 | Algebraic identities |
| 4 | N7 | Secondary 2, 7.6 | Inequality bounds; N1 operations may be secondary |
| 5 | unclassified | — | Circle theorem outcome is not present in the supplied subset |
| 6(i) | N3 | Secondary 1, 3.6 | Percentage/profit problem |
| 6(ii) | N3 | Secondary 1, 3.6 | Interest context; confirm against later syllabus pages |
| 7(i) | N2 | Secondary 2, 2.5 | Inverse proportion/workers and days |
| 7(ii) | N2 | Secondary 2, 2.5 | Inverse proportion; N3 is secondary because the answer is a percentage decrease |
| 8 | N6 | Secondary 2, 6.6–6.7 | Quadratic function and graph properties |

## Implementation sequence

1. Import and founder-check the complete syllabus; publish `g3_math_v1`.
2. Add taxonomy, question-part and assignment migrations with seed data.
3. Add manual part splitting and topic confirmation to the review/admin workflow.
4. Implement `rules_v1` with stored evidence and an `unclassified` outcome.
5. Label a golden set covering every topic and common cross-topic confusion.
6. Report broad-topic accuracy, outcome accuracy, coverage and review rate.
7. Add a local semantic reranker only for unresolved candidates and reevaluate.
8. Consider a bounded text-model experiment only if the measured result justifies it.
9. Run categorization after checked transcription and before answer verification and publication.

## Branch and acceptance criteria

The implementation is isolated on `question_categorier`, created from the current
OCR work as requested. Keep future curriculum migrations and classifier evaluation
on this branch until review, then merge it independently from later OCR model work.

The categorizer is ready for production ordering when:

- every assignment references the active taxonomy version;
- unknown concepts remain unclassified;
- multi-part questions can have part-level assignments;
- classifier evidence and versions are stored;
- reruns do not overwrite human confirmations;
- the founder-labelled golden set reaches the agreed accuracy threshold;
- no low-confidence classification controls student-visible ordering.
