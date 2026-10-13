# Geometry content and diagram standard

This standard applies to Mathematics topic groups whose syllabus code begins with `G`.
It keeps geometry lessons visually useful and prevents future notes from falling back to the
minimum four-section scaffold.

## Lesson depth

Every authored geometry lesson must contain:

- at least seven substantive sections;
- at least two worked examples with explicit reasoning and verification;
- at least 3,000 characters of authored section content;
- at least one referenced, accessible diagram;
- a concept explanation, misconception checks, active recall and a summary.

The course validator enforces these minimums. A geometry lesson that misses one of them fails
validation before it can be integrated.

## Diagram policy

Diagrams should carry spatial information that helps a learner interpret an angle, shape,
construction, transformation, length, area or solid. They must include meaningful alternative
text, explicit dimensions in their metadata and a reminder when they are not drawn to scale.

Questions remain text-only when every relationship and measurement is already unambiguous and a
schematic would merely repeat the calculation. Each geometry bank records this decision for every
question in `diagram_audit.json`.

SVG assets are deterministic source files stored beside the lesson or question bank. Their
checksums are validated during authoring. The authenticated content-asset endpoint serves them to
the lesson, practice, checkpoint, diagnostic and administrator review interfaces.

## October 2026 recalibration

The initial recalibration covers all currently authored geometry material:

| Topic group | Lessons expanded | Questions audited | Questions with diagrams |
| --- | ---: | ---: | ---: |
| Secondary 1 G1 | 7 | 104 | 21 |
| Secondary 1 G5 | 5 | 104 | 15 |
| Secondary 2 G2 | 5 | 104 | 15 |
| **Total** | **17** | **312** | **51** |

All 17 lessons now have eight sections, two worked examples and one core teaching diagram. The 51
question diagrams give representative visual coverage across every authored geometry outcome and
difficulty range. The remaining 261 questions have an explicit text-sufficient audit decision.

All changed lessons and questions return to draft review because their revision and content
fingerprints changed. Mathematics and editorial approval must therefore be recorded against the
new revisions before publication.
