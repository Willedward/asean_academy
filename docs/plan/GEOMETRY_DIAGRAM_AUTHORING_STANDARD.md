# Geometry diagram authoring standard

Geometry diagrams are assessment content. Their visible labels, alternative text and
markings must preserve the intended reasoning while communicating every given fact
unambiguously.

## Required authoring rules

1. Draw angle arcs from the same mathematical centre and ray coordinates as the diagram.
   Do not estimate arc endpoints by eye.
2. Put every assessed arc in `generation_spec.angle_markers`. The validator checks its
   radius, sweep and contact with both declared rays against the SVG path.
3. Put final answers and intermediate values the learner must derive in
   `generation_spec.forbidden_visible_labels`. These values must not occur in visible SVG
   text or alternative text.
4. Keep labels outside the arc stroke and away from rays, vertices, tick marks and other
   labels. Use centred text anchors when a label is placed on an angle bisector.
5. Use mathematical coordinates for regular polygons, parallel lines, perpendicular lines
   and equal-length markings. A `not drawn to scale` note does not permit a diagram to show
   the wrong relationship.
6. Preserve the previous SVG when content changes. Increment the question or lesson
   revision and use a revisioned asset filename.
7. Review the rendered SVG at desktop and narrow widths before requesting Mathematics and
   editorial approval.

## Checked generators: right triangles and mensuration

`question_bank/src/question_bank/diagrams/` replaces the two fixed-template generators that
are not in the repository (`nextscholar-right-triangle-svg-v1` and
`nextscholar-mensuration-svg-v1`). The replacements are `nextscholar-right-triangle-svg-v2`
and `nextscholar-mensuration-svg-v2`. They read each question's prompt and answer key, compute
every coordinate, and return the SVG, the alternative text and a `generation_spec`. The same
input always gives byte-identical output.

### Supported templates

| Renderer | `diagram_kind` | Templates |
| --- | --- | --- |
| right-triangle v2 | `right_triangle` | `find_hypotenuse`, `missing_leg`, `right_angle_specification`, `tangent_adjacent`, `tangent_opposite`, `find_angle`, `sine_opposite`, `cosine_adjacent`, `sine_angle`, `cosine_angle`, `converse_test`, `perimeter_verify`, `rectangle_diagonal`, `diagonal_route`, `cable_allowance`, `elevation_observer`, `two_position`; lessons `lesson_pythagoras`, `lesson_converse`, `lesson_trigonometry` |
| mensuration v2 | `pyramid` | `rectangular_pyramid_volume`, `pyramid_base_area_volume`, `pyramid_height`, `pyramid_covering_cost`, `pyramid_volume_constraint`; lesson `lesson_pyramid` |
| mensuration v2 | `cone`, `cone_cylinder`, `inverted_cone_liquid` | `cone_volume`, `cone_curved_area`, `cone_total_area`, `cone_cylinder_factor`, `liquid_depth`; lesson `lesson_cone` |
| mensuration v2 | `sphere`, `hollow_sphere`, `hemisphere` | `sphere_surface_area`, `sphere_volume_radius`, `sphere_volume_diameter`, `sphere_percentage_change`, `hollow_shell`, `sphere_core_removed`, `hemisphere_curved_area`; lesson `lesson_sphere` |
| mensuration v2 | `cone_hemisphere`, `separate_solids` | `cone_hemisphere_volume`, `cone_hemisphere_area`, `equal_volume_cone_sphere`, `recast_spheres_cones` |

The four sine and cosine templates (hypotenuse given with an angle, or with one shorter side) have no
prompt pattern yet: store `generation_spec.template` and `inputs` (`angle`, `hypotenuse`, optional
`label` and `places`; or `hypotenuse` with `opposite` or `adjacent`).

Templates are matched on the mathematical wording of the prompt, not on the title or the
opening context sentence. If a reworded prompt no longer matches, store
`generation_spec.template` and `generation_spec.inputs` on the asset. A stored v2 template
takes precedence over the prompt. A question that matches no template is reported as
unsupported; it is never drawn from a guess.

### What the generators guarantee

- **Right triangles.** The angle arc is centred on the acute vertex it describes, between that
  vertex's two sides, and drawn at the stated size. Narrow angles get a wider arc so that the
  label fits inside the angle. A right-angle mark appears only where the right angle is
  given. "Is it right-angled?" items get no figure in the bank (see below). `perimeter_verify`
  draws the true triangle from its three sides with no mark, because the prompt says the
  triangle is right-angled and the learner verifies it. The unknown side or angle carries its
  variable (`c`, `b`, `x`, `d`, `h`, `θ`), never its value. Elevation items show the tower to the ground, the dashed eye-level line, the
  observer's eye height and the full height `h`. The two-position item shows both
  observation points, both sight lines and both angles.
- **Mensuration.** Pyramid bases have four sides. The apex is above the centre of the base,
  the dashed height ends at that centre with the right angle marked in the base plane, and
  hidden edges are dashed. A given slant height is drawn from the apex to the midpoint of a
  base edge and labelled `l`. A given diameter is drawn in full through the centre. Hollow
  and cored spheres show a dashed concentric inner sphere. "Same base and height" items draw
  the cone inside a cylinder. Liquid-depth items draw the cone vertex down, with the liquid
  surface at a neutral level so the figure does not encode the depth. Recast and
  equal-volume items draw separate solids side by side. Labels `r`, `h` and `l` sit beside
  the segment they measure. Where there is no room, a leader joins the label to that
  segment.
- **Shared.** Each viewBox is 600 units wide. Labels are 24 to 26 units and notes are 22,
  which renders at 13.1 px or more on a 390 px screen. A label is placed only where it stays
  inside the viewBox, clear of every stroke and every other label, and nearer to its own
  segment than to any other segment. The alternative text names the solid and every given
  value, and leaves out the answer. A value the learner must find is drawn at a neutral size
  whenever the drawn givens do not already fix it.

### Sec 2 G4: text-only items and extra checks

**Text-only test.** `right_triangle.TEXT_ONLY` lists the "is it right-angled?" prompts. A triangle
drawn from the three sides shows the answer, and any other triangle is a false figure, so founder
decision D6 B makes all 28 text-only. The `converse_test` template stays for tests and old assets,
and draws one fixed scalene triangle with no mark. The figure's stem sentence goes with the figure.

**Extra checks for this renderer** (`right_triangle_checks.py`; each failure is an error):

- `geometry_impossible_triangle`: labels at a right angle that break Pythagoras' theorem.
- `geometry_given_mismatch`: every number shown must be stated in the question, and every stated
  number must be shown. A right-angle mark counts as showing 90°.
- `geometry_label_notation`: `θ°`, because θ already names the angle.
- `geometry_method_named`: a title or label that names the ratio or theorem the learner must
  choose. Lesson figures may name them.

G4 keeps a `diagram_audit.json` like the other geometry banks. The last batch PR of a topic sets
`diagram_question_count`.

### `generation_spec` contract

Besides `renderer`, `diagram_kind`, `question_key` (or `lesson_key`), `outcome` and
`not_to_scale`, the spec records:

- `template` and `inputs`: the givens read from the prompt;
- `dimensions`: the given values and units;
- `forbidden_visible_labels`: the answer, its unrounded forms and the intermediate values the
  learner must derive. A value equal to a stated given goes in
  `forbidden_label_exemptions` instead, and the unknown still carries its variable;
- `unknowns`: each target and the variable that labels it;
- `points` and `segments` (including which segments are `hidden`), `circles`, `ellipses`,
  `right_angles`, `angles` and `angle_markers`, `labels`, `leaders` and `dimension_lines`;
- `relationships`: machine-checkable facts, such as `length_ratio`, `parallel`, `collinear`,
  `vertical`, `midpoint`, `centroid`, `inside_polygon`, `polygon_sides`, `parallelogram`,
  `on_circle`, `on_ellipse`, `hidden_circle` and `circle_ratio`;
- `solids`, `task` and `forbid_right_angle_marker` where they apply.

### Validation

For assets from the two v2 renderers, `question-bank validate` and `course-validate` check
every declaration against the SVG, and any failure is an **error**:

- **Answer leaks.** Withheld labels are matched as whole tokens, so `4` does not match `45`
  or `4.5`. They are checked in visible text, `<title>`, `<desc>` and the alternative text
  (`geometry_answer_leak`). The question's canonical answer must be withheld or exempted
  (`geometry_answer_not_withheld`). An unknown must be labelled with a variable
  (`geometry_unknown_shows_value`).
- **Declared geometry.**
  - `geometry_segment_mismatch` and `geometry_hidden_edge` check that each segment is drawn
    between its points, and dashed only if it is hidden.
  - `geometry_right_angle_measure` and `geometry_right_angle_marker` check that marked right
    angles are 90° and that each marker sits on both arms.
  - `geometry_right_angle_marker_forbidden` rejects any right-angle mark on a right-angle
    test.
  - `geometry_angle_measure` and `geometry_angle_marker_vertex` check that each arc is at its
    stated size and centred on its own acute vertex, not the right angle.
  - `geometry_relationship` checks each declared relationship.
  - `geometry_solid_relationship_missing` and `geometry_solid_orientation` check the solid
    rules: a four-sided pyramid base with the apex over its centre, a full diameter, a
    dashed inner sphere, and the cone the right way up.
  - `geometry_dimension_line` and `geometry_label_leader` check dimension lines and leaders.
- **Label layout.**
  - `geometry_label_bounds`: a label extends outside the viewBox.
  - `geometry_label_overlap`: two labels overlap.
  - `geometry_label_collision`: a label touches a stroke.
  - `geometry_label_detached`: a label is more than 40 units from its segment, outside its
    angle, or nearer another segment.
  - `geometry_text_too_small`: text renders below 12 px on a 390 px screen.
- **Alternative text.** It must name the solid (`geometry_alt_text_solid`) and include every
  given value shown on the diagram (`geometry_alt_text_values`).

### Existing assets: warnings now, errors later

Assets from `nextscholar-geometry-svg-v1`, `nextscholar-right-triangle-svg-v1` and
`nextscholar-mensuration-svg-v1` declare no geometry, so they raise **warnings** only:

- `geometry_legacy_unchecked`: no dimensions or forbidden labels are declared.
- `geometry_answer_leak`: a canonical answer that the prompt does not state appears in the
  SVG text.
- `geometry_label_bounds`, `geometry_label_overlap` and `geometry_text_too_small`: the
  label-layout checks above.

None of these warnings makes a bank or course invalid. Tighten them in three steps:

1. Each batch fix PR runs `question-bank validate <bank> --strict-geometry` after applying
   its regenerated diagrams, so the batch's new assets add no warnings.
2. When every G4 and G5 batch has been regenerated, move
   `nextscholar-right-triangle-svg-v1` and `nextscholar-mensuration-svg-v1` from
   `LEGACY_GEOMETRY_RENDERERS` to `RETIRED_GEOMETRY_RENDERERS` in `geometry_validation.py`.
   Any remaining asset from either renderer then fails with `geometry_retired_renderer`.
3. When G1, Sec 1 G5 and G2 have been regenerated with checked generators, retire
   `nextscholar-geometry-svg-v1` the same way. Then remove the `non_legacy_diagram_warnings`
   filter from the course and catalogue tests, so they again assert no warnings.

### Regenerating a batch

```bash
cd question_bank
uv run question-bank diagrams-regenerate ../backend_resources/question_bank/g3_math/secondary_2/g5/v1 --batch B002 --output /tmp/g5-b002-diagrams
uv run question-bank diagrams-regenerate ../backend_resources/question_bank/g3_math/secondary_2/g5/v1 --batch B002 --apply
uv run question-bank lesson-diagrams-regenerate ../backend_resources/courses/g3_math/secondary_2/g2/v1 --lesson g5-lesson-06 --apply
```

The preview writes the SVGs, `manifest.json` and `findings.md` to a directory outside the
bank; it never changes the repository. `--apply` does five things:

- validates each new SVG strictly;
- writes it beside the old asset as `<name>-r<revision>.svg`, keeping the old file;
- updates the asset's path, checksum, size, alternative text and `generation_spec`;
- increments the question or lesson revision;
- resets review provenance.

A second run makes no changes. `findings.md` lists problems that belong in the question
text, such as wrong answer keys and stems that presuppose the answer. The command never
edits those.

## Checked generator: Sec 1 G1 plane geometry

`nextscholar-plane-geometry-svg-v1` (`diagrams/plane_geometry.py`) replaces the fixed templates of
`nextscholar-geometry-svg-v1` for Sec 1 G1. It follows the same contract as the generators above.
It does not cover Sec 1 G5 or lesson figures, and their prompts are reported as unsupported.
Sec 2 G2 has its own generator, described below. `nextscholar-geometry-svg-v2`, used by the G1 v2 diagnostic bank, is a separate set of
hand-made assets and is unaffected.

| `diagram_kind` | Templates |
| --- | --- |
| `angles_on_line` | `straight_line_given`, `straight_line_ratio` |
| `right_angle_split` | `complement_split` |
| `intersecting_lines` | `intersection_expressions`, `intersection_obtuse` |
| `parallel_lines` | `parallel_corresponding`, `parallel_cointerior_ratio`, `two_transversals_meeting`, `perpendicular_transversal` |
| `triangle` | `triangle_third_angle`, `triangle_expressions`, `triangle_angle_sum`, `isosceles_exterior` |
| `diagonals` | `diagonals_equal_bisect`, `diagonals_perpendicular_one_bisected` |
| `kite` | `kite_symmetry`, `kite_angles` |
| `construction` | `perpendicular_bisector_midpoint`, `safe_radius`, `equilateral_on_ray`, `sss_arc_radius`, `sss_mirror_image` |
| `angle_types` | lesson `lesson_angle_types` (acute, right, obtuse and reflex angles drawn to size; the reflex arc takes the long way round) |

**Text-only test.** If every accurate figure of a question shows its answer, and any other figure
would draw a false relationship, the question has no figure. `plane_geometry.TEXT_ONLY` lists these
prompts with the reason: classifying a stated angle, and any polygon whose side count is the answer.
A classification by diagonals can still have a figure, because the diagonals alone do not show the
shape, so those templates draw the diagonals and not the sides.

**Extra checks for this renderer** (each failure is an error):

- `geometry_angle_ray_undrawn`: both rays of an arc must lie on drawn segments.
- `geometry_angle_marker_centre` and `geometry_angle_marker_sweep`: the centre computed from the
  SVG arc's endpoints and flags must be the vertex, and the arc must stay inside the angle.
- `geometry_marking`: segments with equal ticks must measure equal, and segments with parallel
  arrows must be parallel. Every mark must be declared and sit on its segment.
- `geometry_relationship`: adds the measured relationships `perpendicular`, `not_perpendicular`,
  `unequal_segments`, `angle_sum` and `corresponding_angles`.
- `geometry_arc`: a compass arc must be centred on its declared point and pass through the point
  it locates.
- `geometry_alt_text_values`: the alternative text must include every label and state no number
  that the diagram does not show.
- `geometry_alt_text_figure`: it must name the figure, and mention a right angle or parallel lines
  exactly when they are marked.

**Regenerating.** Add `--add <question key>` for a text-only question that needs a new figure.
Questions the generator refuses become text-only when applied. Both decisions go in the bank's
`diagram_audit.json`. The command leaves `diagram_question_count` alone, because every batch would
otherwise change the same line.

```bash
uv run question-bank diagrams-regenerate ../backend_resources/question_bank/g3_math/secondary_1/g1/v1 --batch B003 --add g1-l3-020 --add g1-l4-011 --apply
```

## Checked generator: Sec 1 G5 mensuration

`nextscholar-sec1-mensuration-svg-v1` (`diagrams/sec1_mensuration.py`) replaces the fixed templates of
`nextscholar-geometry-svg-v1` for Sec 1 G5. It follows the same contract as the generators above, and
its checks are in `sec1_mensuration_checks.py`. It does not cover the G5 lesson figures. Questions with
`school_level` `secondary_1` and `topic_code` `G5` are routed to it, so Sec 2 G5 is unaffected.

| `diagram_kind` | Templates |
| --- | --- |
| `parallelogram` | `parallelogram_area` |
| `two_quadrilaterals` | `parallelogram_and_trapezium`, `trapezium_and_parallelogram_algebra` |
| `composite_plane` | `rectangle_and_square`, `joined_rectangles`, `joined_rectangles_algebra` |
| `rectilinear` | `corner_removed`, `corner_removed_algebra` |
| `ring` | `uniform_border`, `track_algebra` |
| `cuboid` | `cuboid_volume`, `open_box`, `box_with_cube` |
| `prism` | `prism_right_triangle_legs`, `prism_right_triangle_sides`, `trapezoidal_prism` |
| `joined_solids` | `two_cubes_joined`, `block_on_cuboid` |
| `drilled_solid` | `cuboid_tunnel`, `cuboid_vertical_hole`, `cuboid_cylindrical_hole`, `cube_cylindrical_hole` |
| `cylinder` | `open_cylinder`, `open_cylinder_material` |

**What it draws.** One scale per figure, so every stated length measures true against the others. An
unknown is drawn at a neutral size and labelled with its variable. Solids use an oblique view, with
depth at half length, so a front face keeps its true shape and its right angle measures 90°. A
cylindrical hole on a top face uses an isometric view, where the circle is a true horizontal ellipse.

**Text-only test.** `sec1_mensuration.TEXT_ONLY` lists prompts with no figure: a unit conversion or a
sum of stated values, which have no spatial content, and a prompt that any figure would contradict.

**Extra checks for this renderer** (each failure is an error):

- `geometry_figure_mismatch`: the template must draw exactly its own figures.
- `geometry_figure_not_in_question`: each figure must be one the question describes, and each shape the
  question names must be drawn. A cut-out cannot stand in for a joined shape.
- `geometry_figure_shape` and `geometry_figure_overlap`: each shape is measured, including parallel
  sides, right angles, equal cube edges, and a rear face that is a copy of the front.
- `geometry_height`: a height is dashed, perpendicular to its base and ends on it, with a right-angle
  mark at its foot.
- `geometry_given_unlabelled`, `geometry_drawn_length` and `geometry_neutral_length`: every given is
  labelled on its own segment at the drawn scale, and an unknown is not drawn at its true size.
- `geometry_label_not_stated`: a label must be a length the question states, or a declared unknown.
- `geometry_shared_edge`: a shared edge is dashed and a complete edge of the smaller rectangle, and a
  shared face is shaded.
- `geometry_hole` and `geometry_open_top`: a hole's rim lies inside its face with its far side dashed,
  and an open solid shades its opening and says that it is open.
- `geometry_stray_stroke`, `geometry_stray_text` and `geometry_duplicate_stroke`: no undeclared arrow,
  box, faint line or caption, and no stroke drawn over another.
- `geometry_alt_text_figure` and `geometry_alt_text_values`: as for the plane-geometry renderer.

```bash
uv run question-bank diagrams-regenerate ../backend_resources/question_bank/g3_math/secondary_1/g5/v1 --batch B002 --add g5-l2-011 --add g5-l3-011 --add g5-l3-012 --add g5-l3-016 --add g5-l4-008 --apply
## Checked generator: Sec 2 G2 congruence and similarity
`nextscholar-similarity-svg-v1` (`diagrams/similarity.py`) replaces the fixed templates of
`nextscholar-geometry-svg-v1` for Sec 2 G2. A question uses it when its `school_level` is
`secondary_2` and its `topic_code` is `G2`. It follows the same contract as the generators above,
and adds its own checks in `similarity_checks.py`. It does not draw lesson figures.
| `congruent_triangles` | `scalene_tiles`, `congruent_algebra`, `sas_condition` |
| `congruent_pentagons` | `congruent_pentagons` |
| `shared_side` | `shared_side` |
| `similar_triangles` | `similar_edges`, `similar_perimeter`, `similar_angle`, `similar_angle_expressions` |
| `similar_polygons` | `similar_chain` |
| `nested_triangles` | `nested_parallel`, `nested_shared_vertex` |
| `shadow`, `mirror`, `survey` | `shadow_pair`, `mirror_method`, `river_survey` |
| `coordinate_grid` | `origin_point_ray`, `centre_unknown_line`, `centre_given_ray` |
| `enlargement_line` | `enlargement_line` |
| `scale_segments`, `scale_rectangles` | `scale_segments`, `scale_model`, `scale_plan_stage` |
**How it draws.**
- Figures called congruent or similar are one set of vertices transformed, drawn at the stated
  factor. When the shape is free, it uses one fixed scalene shape.
- A question that fixes its lengths is drawn in those proportions, including the value the learner
  finds, which carries a variable. A scale such as 1 : 300 cannot fit on one screen, so that
  figure keeps the shape and its arrow carries the ratio.
- Where equality of sides or angles is the question, the figure does not state it. `scalene_tiles`
  has side labels and no ticks. `sas_condition` draws different included angles and marks no angle.
- On a coordinate grid only the coordinates in the question are numbered, and the point the learner
  must find is not plotted, because a plotted point on a numbered grid shows its coordinates.
- A figure too small to hold marks carries none, so the `shadow_pair` stick has no corner mark or
  arc, and it keeps the true factor.
**Text-only test.** `similarity.TEXT_ONLY` lists prompts whose accurate figure shows the step that
is assessed. It holds the successive factors 3/2 and 2/3, which an accurate chain draws back at the
original size.
**Extra checks for this renderer** (each failure is an error, and the `plane_*` checks above also
run):
- `geometry_figure_proportion`: figures declared `congruent` or `similar` must measure so, at any
  declared factor. `to_scale` lengths must be in the proportion of their stated values, and an
  `enlargement` must sit at its factor from its centre.
- `geometry_figure_shape`: every side of a declared figure must be drawn, and a figure must have the
  side count of the shape the question names, so a pentagon question cannot show triangles.
- `geometry_correspondence`: ticks must join corresponding sides, one from each figure, and matching
  arcs must be equal and at corresponding vertices.
- `geometry_given_mismatch`: every number shown must be stated in the question, and every stated
  number must be shown or listed in `generation_spec.omitted_givens` with a reason.
- `geometry_arrow`: a scaling arrow must run from its declared source to its target, and its factor
  must match the figures as drawn.
- `geometry_grid`: points, grid lines and axis numbers must be at their coordinates.
uv run question-bank diagrams-regenerate ../backend_resources/question_bank/g3_math/secondary_2/g2/v1 --batch B004 --add g2-l3-530 --apply
```

## Sec 2 G5: extra checks

`nextscholar-mensuration-svg-v2` also has its own checks in `mensuration_checks.py`. Each failure is
an error:

- `geometry_slant_unmarked`: a given slant height must be labelled `l` on the edge from the apex to
  the base, and that figure must not draw the vertical height.
- `geometry_wrong_solid`: every solid the question names must be drawn, and no other. A hollow or
  cored solid must show its inner sphere, and liquid must be in a cone with its vertex down.
- `geometry_cone_proportion`: a cone is drawn from its given height and radius, with height to
  radius limited to 0.6 to 3.5.
- `geometry_given_mismatch`: every number shown must be stated in the question, and every stated
  number must be shown. A cost rate isn't a measurement, so it stays in the prompt.

G5 keeps a `diagram_audit.json` like the other geometry banks. All 104 questions keep a figure.

## Review feedback

The admin reviewer lists every diagram's immutable asset key. Select **Comment on diagram**
to switch the item to **Request changes** and start a structured note:

```text
Diagram g1-l3-904-regular-octagon: remove the displayed central-angle value because the
student must derive it from the regular octagon.
```

The note remains attached to the exact question revision and review fingerprint. The
correction export therefore identifies the affected question and SVG without requiring a
separate image-annotation database. If several diagrams need different changes, review the
items individually rather than applying one shared bulk note.
