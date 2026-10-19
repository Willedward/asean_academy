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
