"""Semantic checks for generated geometry diagrams.

``checked_diagram_issues`` applies to assets from the checked v2 renderers. Their
``generation_spec`` declares every point, segment, right angle, angle, label, unknown and
relationship, and these checks confirm each declaration against the SVG itself.

``legacy_diagram_issues`` applies to the fixed-template v1 renderers. They declare no
geometry, so only label layout, phone readability and a heuristic answer-leak check can run.
Validators report these as warnings until the assets are regenerated.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .svg_metrics import (
    MIN_PHONE_FONT_PX,
    Box,
    SvgText,
    arc_centre,
    iter_strokes,
    iter_texts,
    local_name,
    path_polylines,
    phone_font_px,
    point_segment_distance,
    segment_box_distance,
    viewbox,
)

POINT_TOLERANCE = 0.75
ANGLE_TOLERANCE = 1.0
RIGHT_ANGLE_TOLERANCE = 0.5
MAX_LABEL_GAP = 40.0
LABEL_STROKE_CLEARANCE = 1.0
CONVERSE_TASKS = frozenset({"converse_test", "perimeter_verify"})
PLANE_GEOMETRY_RENDERER = "nextscholar-plane-geometry-svg-v1"
# What the alternative text of each plane-geometry figure must name.
PLANE_FIGURE_WORDS = {
    "angles_on_line": "straight line",
    "right_angle_split": "right angle",
    "intersecting_lines": "lines",
    "parallel_lines": "parallel",
    "triangle": "triangle",
    "diagonals": "segments",
    "kite": "kite",
    "construction": "arc",
}
_ARC_D = re.compile(
    r"^\s*M\s*(-?[\d.]+)[ ,]+(-?[\d.]+)\s+A\s*(-?[\d.]+)[ ,]+(-?[\d.]+)[ ,]+0[ ,]+([01])[ ,]+([01])"
    r"[ ,]+(-?[\d.]+)[ ,]+(-?[\d.]+)\s*$"
)
SOLID_WORDS = {
    "pyramid": "pyramid",
    "cone": "cone",
    "sphere": "sphere",
    "hemisphere": "hemisphere",
    "cylinder": "cylinder",
}
_NUMBER = re.compile(r"(?<![\d.])\d+(?:\.\d+)?")
# Codes that legacy fixed-template assets may raise as warnings until they are regenerated.
LEGACY_ADVISORY_CODES = frozenset(
    {
        "geometry_legacy_unchecked",
        "geometry_answer_leak",
        "geometry_label_bounds",
        "geometry_label_overlap",
        "geometry_text_too_small",
    }
)

Issue = tuple[str, str]


@dataclass(frozen=True)
class DiagramContext:
    """What the validator knows about the content that shows the diagram."""

    answers: tuple[str, ...] = ()
    stated_text: str = ""


# --------------------------------------------------------------------------- answer leaks
def forbidden_label_pattern(label: str) -> re.Pattern[str]:
    """Match a withheld label as a whole token, so 4 does not match 45 or 4.5."""
    text = label.strip()
    body = r"\s*".join(re.escape(part) for part in text.split())
    prefix = r"(?<![\w.])" if text[:1].isalnum() else ""
    if text[-1:].isdigit():
        suffix = r"(?![\d²³]|[.,]\d)"
    elif text[-1:].isalnum():
        suffix = r"(?![\w²³])"
    else:
        suffix = ""
    return re.compile(prefix + body + suffix, re.IGNORECASE)


def svg_accessible_text(root: ET.Element) -> str:
    return " | ".join(
        "".join(node.itertext()) for node in root.iter() if local_name(node) in {"title", "desc"}
    )


def svg_visible_text(root: ET.Element) -> str:
    return " | ".join(text.text for text in iter_texts(root))


def answer_leak_locations(label: str, visible: str, alternative: str) -> list[str]:
    pattern = forbidden_label_pattern(label)
    locations = []
    if pattern.search(visible):
        locations.append("visible SVG text")
    if pattern.search(alternative):
        locations.append("alternative text")
    return locations


# -------------------------------------------------------------------------- text layout
def text_layout_issues(root: ET.Element, *, check_strokes: bool) -> list[Issue]:
    """Check that labels stay inside the viewBox, apart, clear of strokes and readable."""
    issues: list[Issue] = []
    bounds = viewbox(root)
    texts = list(iter_texts(root))
    if bounds is None or not texts:
        return issues
    inner = Box(bounds.x0 + 1, bounds.y0 + 1, bounds.x1 - 1, bounds.y1 - 1)
    for text in texts:
        if not text.box.inside(inner):
            issues.append(
                (
                    "geometry_label_bounds",
                    f"Label {text.text!r} extends beyond the {bounds.width:g} × {bounds.height:g} viewBox.",
                )
            )
    for index, first in enumerate(texts):
        for second in texts[index + 1 :]:
            if first.box.overlaps(second.box):
                issues.append(
                    (
                        "geometry_label_overlap",
                        f"Labels {first.text!r} and {second.text!r} overlap.",
                    )
                )
    if check_strokes:
        strokes = list(iter_strokes(root))
        for text in texts:
            for stroke in strokes:
                if stroke.distance_to_box(text.box) < stroke.half_width + LABEL_STROKE_CLEARANCE:
                    name = (
                        stroke.element.attrib.get("data-segment")
                        or stroke.element.attrib.get("data-role")
                        or local_name(stroke.element)
                    )
                    issues.append(
                        (
                            "geometry_label_collision",
                            f"Label {text.text!r} touches the stroke of {name}.",
                        )
                    )
    smallest = min(texts, key=lambda text: text.font_size)
    rendered = phone_font_px(smallest.font_size, bounds.width)
    if rendered < MIN_PHONE_FONT_PX:
        issues.append(
            (
                "geometry_text_too_small",
                f"Text {smallest.text!r} renders at {rendered:.1f} px on a 390 px screen "
                f"(minimum {MIN_PHONE_FONT_PX:g} px).",
            )
        )
    return issues


# ---------------------------------------------------------------------- legacy renderers
def legacy_diagram_issues(
    root: ET.Element, spec: dict[str, Any], alt_text: str, context: DiagramContext | None
) -> list[Issue]:
    renderer = spec.get("renderer")
    issues: list[Issue] = []
    if not spec.get("dimensions") or "forbidden_visible_labels" not in spec:
        issues.append(
            (
                "geometry_legacy_unchecked",
                f"Renderer {renderer} draws a fixed template and declares no dimensions or "
                "forbidden_visible_labels, so relationship and answer-leak checks cannot run. "
                "Regenerate the asset with question-bank diagrams-regenerate.",
            )
        )
    if context is not None and context.answers:
        visible = svg_visible_text(root)
        stated = {match.group(0) for match in _NUMBER.finditer(context.stated_text)}
        for answer in context.answers:
            if not _NUMBER.fullmatch(answer) or answer in {"0", "1"} or answer in stated:
                continue
            if forbidden_label_pattern(answer).search(visible):
                issues.append(
                    (
                        "geometry_answer_leak",
                        f"The answer {answer!r} appears in the diagram's visible text but is not "
                        "stated in the question.",
                    )
                )
    issues.extend(text_layout_issues(root, check_strokes=False))
    return issues


# --------------------------------------------------------------------- checked renderers
def _pair(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        return float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None


def _close(
    a: tuple[float, float], b: tuple[float, float], tolerance: float = POINT_TOLERANCE
) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tolerance


def _angle(vertex, first, second) -> float:
    u = (first[0] - vertex[0], first[1] - vertex[1])
    v = (second[0] - vertex[0], second[1] - vertex[1])
    lengths = math.hypot(*u) * math.hypot(*v)
    if lengths == 0:
        return 0.0
    cosine = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / lengths))
    return math.degrees(math.acos(cosine))


def _on_ray(point, vertex, through, distance: float, tolerance: float = POINT_TOLERANCE) -> bool:
    length = math.hypot(through[0] - vertex[0], through[1] - vertex[1])
    if length == 0:
        return False
    expected = (
        vertex[0] + (through[0] - vertex[0]) * distance / length,
        vertex[1] + (through[1] - vertex[1]) * distance / length,
    )
    return _close(point, expected, tolerance)


def _dashed(element: ET.Element, parents: dict[ET.Element, ET.Element]) -> bool:
    node: ET.Element | None = element
    while node is not None:
        dash = node.attrib.get("stroke-dasharray")
        if dash is not None:
            return dash not in {"none", "", "0"}
        node = parents.get(node)
    return False


class _Checked:
    def __init__(
        self, root: ET.Element, spec: dict[str, Any], alt_text: str, context: DiagramContext | None
    ):
        self.root = root
        self.spec = spec
        self.alt_text = alt_text
        self.context = context
        self.issues: list[Issue] = []
        self.parents = {child: parent for parent in root.iter() for child in parent}
        self.points: dict[str, tuple[float, float]] = {}
        for name, value in (spec.get("points") or {}).items():
            point = _pair(value)
            if point is None:
                self.add("geometry_spec_incomplete", f"Point {name} must be a pair of numbers.")
            else:
                self.points[name] = point
        self.segments = {
            segment.get("key"): segment
            for segment in spec.get("segments") or []
            if isinstance(segment, dict)
        }
        self.lines = {
            node.attrib["data-segment"]: node
            for node in root.iter()
            if local_name(node) == "line" and "data-segment" in node.attrib
        }
        self.texts = list(iter_texts(root))

    def add(self, code: str, message: str) -> None:
        self.issues.append((code, message))

    def point(self, name: str) -> tuple[float, float] | None:
        point = self.points.get(name)
        if point is None:
            self.add("geometry_spec_incomplete", f"Point {name} is used but not declared.")
        return point

    def endpoints(self, key: str) -> tuple[tuple[float, float], tuple[float, float]] | None:
        segment = self.segments.get(key)
        if segment is None:
            return None
        start, end = self.points.get(segment.get("from")), self.points.get(segment.get("to"))
        if start is None or end is None:
            return None
        return start, end

    # ------------------------------------------------------------------ metadata
    def metadata(self) -> None:
        required = (
            "dimensions",
            "points",
            "segments",
            "labels",
            "unknowns",
            "relationships",
            "forbidden_visible_labels",
            "viewbox",
        )
        for key in required:
            if key not in self.spec:
                self.add(
                    "geometry_spec_incomplete",
                    f"generation_spec.{key} is required for {self.spec.get('renderer')}.",
                )
        if not self.spec.get("dimensions"):
            self.add(
                "geometry_spec_incomplete",
                "generation_spec.dimensions must record the given dimensions.",
            )
        declared = _pair(self.spec.get("viewbox"))
        actual = viewbox(self.root)
        if declared and actual and not _close(declared, (actual.width, actual.height), 0.5):
            self.add(
                "geometry_spec_incomplete",
                "generation_spec.viewbox does not match the SVG viewBox.",
            )
        if (
            self.context
            and self.context.answers
            and self.spec.get("answer_kind") != "classification_code"
        ):
            withheld = [*self.spec.get("forbidden_visible_labels", [])]
            withheld.extend(
                item.get("value", "")
                for item in self.spec.get("forbidden_label_exemptions", [])
                if isinstance(item, dict)
            )
            for answer in self.context.answers:
                if not _NUMBER.fullmatch(answer):
                    continue
                if not any(_same_number(answer, value) for value in withheld):
                    self.add(
                        "geometry_answer_not_withheld",
                        f"The answer {answer} is not listed in forbidden_visible_labels.",
                    )

    # ------------------------------------------------------------------ segments
    def segment_elements(self) -> None:
        for key, segment in self.segments.items():
            node = self.lines.get(key)
            ends = self.endpoints(key)
            if node is None or ends is None:
                self.add(
                    "geometry_segment_mismatch",
                    f"Segment {key} has no matching SVG line or points.",
                )
                continue
            try:
                drawn = (
                    (float(node.attrib["x1"]), float(node.attrib["y1"])),
                    (float(node.attrib["x2"]), float(node.attrib["y2"])),
                )
            except (KeyError, ValueError):
                self.add("geometry_segment_mismatch", f"Segment {key} has non-numeric coordinates.")
                continue
            if not (_close(drawn[0], ends[0]) and _close(drawn[1], ends[1])):
                self.add(
                    "geometry_segment_mismatch",
                    f"Segment {key} is not drawn between its declared points.",
                )
            if bool(segment.get("hidden")) != _dashed(node, self.parents):
                expected = "dashed" if segment.get("hidden") else "solid"
                self.add("geometry_hidden_edge", f"Segment {key} must be drawn {expected}.")
        for key in self.lines:
            if key not in self.segments:
                self.add(
                    "geometry_segment_mismatch",
                    f"SVG line {key} is not declared in generation_spec.segments.",
                )

    # --------------------------------------------------------------- right angles
    def right_angles(self) -> None:
        markers = {
            node.attrib["data-right-angle-marker"]: node
            for node in self.root.iter()
            if "data-right-angle-marker" in node.attrib
        }
        declared = [item for item in self.spec.get("right_angles") or [] if isinstance(item, dict)]
        forbidden = (
            self.spec.get("forbid_right_angle_marker") or self.spec.get("task") in CONVERSE_TASKS
        )
        if forbidden and (markers or declared):
            self.add(
                "geometry_right_angle_marker_forbidden",
                "A right-angle test must not mark a right angle; the marker states the answer.",
            )
            return
        if self.spec.get("diagram_kind") == "right_triangle" and not forbidden and not declared:
            self.add(
                "geometry_right_angle_missing",
                "A right-angled triangle must declare and mark its right angle.",
            )
        names = set()
        for item in declared:
            vertex_name = item.get("vertex")
            arms = item.get("arms") or []
            names.add(vertex_name)
            vertex = self.point(vertex_name)
            if vertex is None or len(arms) != 2:
                continue
            first, second = self.point(arms[0]), self.point(arms[1])
            if first is None or second is None:
                continue
            measured = _angle(vertex, first, second)
            if not math.isclose(measured, 90, abs_tol=RIGHT_ANGLE_TOLERANCE):
                self.add(
                    "geometry_right_angle_measure",
                    f"The angle marked right at {vertex_name} measures {measured:.1f}°.",
                )
            node = markers.get(vertex_name)
            if node is None:
                self.add(
                    "geometry_right_angle_marker",
                    f"The right angle at {vertex_name} has no marker path.",
                )
                continue
            polylines = path_polylines(node.attrib.get("d", ""))
            size = float(item.get("marker_size", 0) or 0)
            if len(polylines) != 1 or len(polylines[0]) != 3 or size <= 0:
                self.add(
                    "geometry_right_angle_marker",
                    f"The right-angle marker at {vertex_name} must be one M-L-L path.",
                )
                continue
            p1, p2, p3 = polylines[0]
            corner = (p1[0] + p3[0] - vertex[0], p1[1] + p3[1] - vertex[1])
            if not (
                _on_ray(p1, vertex, first, size)
                and _on_ray(p3, vertex, second, size)
                and _close(p2, corner)
            ):
                self.add(
                    "geometry_right_angle_marker",
                    f"The right-angle marker at {vertex_name} does not sit on its two arms.",
                )
        for name in markers:
            if name not in names:
                self.add(
                    "geometry_right_angle_marker",
                    f"A right-angle marker at {name} is not declared.",
                )

    # -------------------------------------------------------------------- angles
    def angles(self) -> None:
        markers = {
            item.get("marker_key"): item
            for item in self.spec.get("angle_markers") or []
            if isinstance(item, dict)
        }
        right_vertices = {
            item.get("vertex")
            for item in self.spec.get("right_angles") or []
            if isinstance(item, dict)
        }
        for item in self.spec.get("angles") or []:
            vertex_name = item.get("vertex")
            arms = item.get("arms") or []
            vertex = self.point(vertex_name)
            if vertex is None or len(arms) != 2:
                continue
            first, second = self.point(arms[0]), self.point(arms[1])
            if first is None or second is None:
                continue
            measured = _angle(vertex, first, second)
            if "degrees" in item and not math.isclose(
                measured, float(item["degrees"]), abs_tol=ANGLE_TOLERANCE
            ):
                self.add(
                    "geometry_angle_measure",
                    f"The angle at {vertex_name} is drawn at {measured:.1f}°, not the stated {float(item['degrees']):g}°.",
                )
            if vertex_name in right_vertices and not math.isclose(
                measured, 90, abs_tol=RIGHT_ANGLE_TOLERANCE
            ):
                self.add(
                    "geometry_angle_marker_vertex",
                    f"An acute-angle arc is drawn at the right angle {vertex_name}.",
                )
            marker = markers.get(item.get("marker_key"))
            if marker is None:
                self.add(
                    "geometry_angle_marker_vertex",
                    f"The angle at {vertex_name} has no declared arc.",
                )
                continue
            centre = _pair(marker.get("center"))
            start, end = _pair(marker.get("start_ray_point")), _pair(marker.get("end_ray_point"))
            if not (
                centre
                and start
                and end
                and _close(centre, vertex)
                and _close(start, first)
                and _close(end, second)
            ):
                self.add(
                    "geometry_angle_marker_vertex",
                    f"The arc for the angle at {vertex_name} is not centred on that vertex and its arms.",
                )

    # -------------------------------------------------------------------- labels
    def _segment_label_distance(self, key: str, box: Box) -> float | None:
        ends = self.endpoints(key)
        if ends is None:
            return None
        return segment_box_distance(ends[0], ends[1], box)

    def labels(self) -> None:
        by_target: dict[str, list[SvgText]] = {}
        for text in self.texts:
            target = text.element.attrib.get("data-label-for")
            if target:
                by_target.setdefault(target, []).append(text)
        leaders = {
            item.get("target"): item
            for item in self.spec.get("leaders") or []
            if isinstance(item, dict)
        }
        dimension_for = {
            f"segment:{item.get('measures')}": item.get("segment")
            for item in self.spec.get("dimension_lines") or []
            if isinstance(item, dict)
        }
        for label in self.spec.get("labels") or []:
            target, text = label.get("target", ""), label.get("text", "")
            matches = [item for item in by_target.get(target, []) if item.text == text]
            if not matches:
                self.add(
                    "geometry_label_missing", f"Label {text!r} for {target} is not in the SVG."
                )
                continue
            box = matches[0].box
            if target in leaders:
                self._check_leader(target, leaders[target], box)
            elif target.startswith("segment:"):
                key = dimension_for.get(target, target.split(":", 1)[1])
                self._check_segment_label(text, key, box)
            elif target.startswith("angle:"):
                self._check_angle_label(text, target.split(":", 1)[1], box)

    def _check_segment_label(self, text: str, key: str, box: Box) -> None:
        distance = self._segment_label_distance(key, box)
        if distance is None:
            self.add("geometry_label_detached", f"Label {text!r} targets undeclared segment {key}.")
            return
        if distance > MAX_LABEL_GAP:
            self.add(
                "geometry_label_detached",
                f"Label {text!r} is {distance:.0f} px from segment {key}; attach it or use a leader.",
            )
        for other in self.segments:
            if other == key:
                continue
            other_distance = self._segment_label_distance(other, box)
            if other_distance is not None and other_distance + 1.0 < distance:
                self.add(
                    "geometry_label_detached",
                    f"Label {text!r} is closer to segment {other} than to its segment {key}.",
                )
                break

    def _check_angle_label(self, text: str, vertex_name: str, box: Box) -> None:
        item = next(
            (
                angle
                for angle in self.spec.get("angles") or []
                if angle.get("marker_key") == vertex_name or angle.get("vertex") == vertex_name
            ),
            None,
        )
        if item is None:
            self.add(
                "geometry_label_detached", f"Label {text!r} targets undeclared angle {vertex_name}."
            )
            return
        vertex = self.points.get(item.get("vertex"))
        arms = [self.points.get(name) for name in item.get("arms", [])]
        if vertex is None or None in arms or len(arms) != 2:
            return
        centre = box.center
        u = (arms[0][0] - vertex[0], arms[0][1] - vertex[1])
        v = (arms[1][0] - vertex[0], arms[1][1] - vertex[1])
        w = (centre[0] - vertex[0], centre[1] - vertex[1])
        cross_uv = u[0] * v[1] - u[1] * v[0]
        inside = (u[0] * w[1] - u[1] * w[0]) * cross_uv >= 0 and (
            w[0] * v[1] - w[1] * v[0]
        ) * cross_uv >= 0
        if not inside:
            self.add(
                "geometry_label_detached",
                f"Label {text!r} is not inside the angle at {vertex_name}.",
            )

    def _check_leader(self, target: str, leader: dict[str, Any], box: Box) -> None:
        key = target.split(":", 1)[1]
        start, end = _pair(leader.get("from")), _pair(leader.get("to"))
        ends = self.endpoints(key)
        paths = [node for node in self.root.iter() if node.attrib.get("data-leader-for") == target]
        if not (start and end and ends and paths):
            self.add("geometry_label_leader", f"The leader for {target} is incomplete.")
            return
        polylines = path_polylines(paths[0].attrib.get("d", ""))
        if not polylines or not (_close(polylines[0][0], start) and _close(polylines[0][-1], end)):
            self.add(
                "geometry_label_leader",
                f"The leader path for {target} does not match its declaration.",
            )
        if point_segment_distance(start, ends[0], ends[1]) > POINT_TOLERANCE:
            self.add(
                "geometry_label_leader", f"The leader for {target} does not start on its segment."
            )
        if segment_box_distance(end, end, box) > 8:
            self.add("geometry_label_leader", f"The leader for {target} does not reach its label.")

    def unknowns(self) -> None:
        labels = {
            label.get("target"): label.get("text", "") for label in self.spec.get("labels") or []
        }
        for unknown in self.spec.get("unknowns") or []:
            target, text = unknown.get("target"), unknown.get("label", "")
            if labels.get(target) != text:
                self.add(
                    "geometry_unknown_label", f"The unknown {target} must be labelled {text!r}."
                )
            if re.search(r"\d", text):
                self.add(
                    "geometry_unknown_shows_value",
                    f"The unknown {target} is labelled {text!r}; label a value the learner must find with its variable.",
                )

    # -------------------------------------------------------------- relationships
    def relationships(self) -> None:
        checks = {
            "length_ratio": self._ratio,
            "parallel": self._parallel,
            "collinear": self._collinear,
            "vertical": self._vertical,
            "midpoint": self._midpoint,
            "centroid": self._centroid,
            "inside_polygon": self._inside,
            "polygon_sides": self._polygon_sides,
            "parallelogram": self._parallelogram,
            "hidden_segment": self._hidden_segment,
            "same_point": self._same_point,
            "on_circle": self._on_circle,
            "circle_centre": self._circle_centre,
            "hidden_circle": self._hidden_circle,
            "circle_ratio": self._circle_ratio,
            "on_ellipse": self._on_ellipse,
            "ellipse_centre": self._ellipse_centre,
            "equal_lengths": self._equal_lengths,
            "perpendicular": self._perpendicular,
            "not_perpendicular": self._not_perpendicular,
            "unequal_segments": self._unequal_segments,
            "angle_sum": self._angle_sum,
            "corresponding_angles": self._corresponding_angles,
        }
        for relation in self.spec.get("relationships") or []:
            kind = relation.get("type") if isinstance(relation, dict) else None
            check = checks.get(kind)
            if check is None:
                self.add(
                    "geometry_relationship_unknown", f"Unknown declared relationship {relation!r}."
                )
                continue
            message = check(relation)
            if message:
                self.add("geometry_relationship", message)

    def _length(self, key: str) -> float | None:
        ends = self.endpoints(key)
        return (
            None if ends is None else math.hypot(ends[1][0] - ends[0][0], ends[1][1] - ends[0][1])
        )

    def _ratio(self, relation) -> str | None:
        first, second = (self._length(key) for key in relation.get("segments", [None, None]))
        if not first or not second:
            return f"Ratio relation {relation.get('segments')} uses undeclared segments."
        value, tolerance = float(relation["value"]), float(relation.get("tolerance", 0.02))
        if abs(first / second - value) > tolerance * max(1.0, value):
            return f"{relation['segments'][0]}:{relation['segments'][1]} is drawn as {first / second:.3f}, declared {value:g}."
        return None

    def _parallel(self, relation) -> str | None:
        ends = [self.endpoints(key) for key in relation.get("segments", [])]
        if len(ends) != 2 or None in ends:
            return f"Parallel relation {relation.get('segments')} uses undeclared segments."
        (a, b), (c, d) = ends
        u, v = (b[0] - a[0], b[1] - a[1]), (d[0] - c[0], d[1] - c[1])
        sine = abs(u[0] * v[1] - u[1] * v[0]) / (math.hypot(*u) * math.hypot(*v))
        if sine > math.sin(math.radians(0.5)):
            return f"Segments {relation['segments']} are declared parallel but are not."
        return None

    def _collinear(self, relation) -> str | None:
        points = [self.points.get(name) for name in relation.get("points", [])]
        if len(points) < 3 or None in points:
            return f"Collinear relation {relation.get('points')} uses undeclared points."
        start, end = points[0], points[-1]
        for point in points[1:-1]:
            if point_segment_distance(point, start, end) > POINT_TOLERANCE:
                return f"Points {relation['points']} are declared collinear but are not."
        return None

    def _vertical(self, relation) -> str | None:
        points = [self.points.get(name) for name in relation.get("points", [])]
        if len(points) < 2 or None in points:
            return f"Vertical relation {relation.get('points')} uses undeclared points."
        if max(p[0] for p in points) - min(p[0] for p in points) > POINT_TOLERANCE:
            return f"Points {relation['points']} are declared vertically aligned but are not."
        return None

    def _mean(self, names) -> tuple[float, float] | None:
        points = [self.points.get(name) for name in names]
        if not points or None in points:
            return None
        return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))

    def _midpoint(self, relation) -> str | None:
        point, mean = self.points.get(relation.get("point")), self._mean(relation.get("of", []))
        if point is None or mean is None or len(relation.get("of", [])) != 2:
            return f"Midpoint relation {relation} uses undeclared points."
        if not _close(point, mean):
            return f"{relation['point']} is not the midpoint of {relation['of']}."
        return None

    def _centroid(self, relation) -> str | None:
        point, mean = self.points.get(relation.get("point")), self._mean(relation.get("of", []))
        if point is None or mean is None:
            return f"Centroid relation {relation} uses undeclared points."
        if not _close(point, mean):
            return f"{relation['point']} is not the centre of {relation['of']}."
        return None

    def _inside(self, relation) -> str | None:
        point = self.points.get(relation.get("point"))
        polygon = [self.points.get(name) for name in relation.get("polygon", [])]
        if point is None or len(polygon) < 3 or None in polygon:
            return f"Inside relation {relation} uses undeclared points."
        inside = False
        for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1], strict=True):
            if (y1 > point[1]) != (y2 > point[1]):
                if point[0] < (x2 - x1) * (point[1] - y1) / (y2 - y1) + x1:
                    inside = not inside
        if not inside:
            return f"{relation['point']} lies outside the polygon {relation['polygon']}."
        return None

    def _polygon_sides(self, relation) -> str | None:
        names = relation.get("points", [])
        points = [self.points.get(name) for name in names]
        if None in points:
            return f"Polygon relation {names} uses undeclared points."
        distinct = {(round(p[0], 1), round(p[1], 1)) for p in points}
        if len(names) != int(relation.get("count", -1)) or len(distinct) != len(names):
            return f"The polygon {names} must have {relation.get('count')} distinct vertices."
        edges = {
            frozenset((segment.get("from"), segment.get("to")))
            for segment in self.segments.values()
        }
        for first, second in zip(names, names[1:] + names[:1], strict=True):
            if frozenset((first, second)) not in edges:
                return f"The polygon {names} has no drawn edge {first}{second}."
        return None

    def _parallelogram(self, relation) -> str | None:
        names = relation.get("points", [])
        points = [self.points.get(name) for name in names]
        if len(points) != 4 or None in points:
            return f"Parallelogram relation {names} uses undeclared points."
        a, b, c, d = points
        if not _close((a[0] + c[0], a[1] + c[1]), (b[0] + d[0], b[1] + d[1]), 2 * POINT_TOLERANCE):
            return f"{names} is declared a parallelogram (a projected rectangle) but is not."
        return None

    def _hidden_segment(self, relation) -> str | None:
        segment = self.segments.get(relation.get("segment"))
        if segment is None or not segment.get("hidden"):
            return f"Segment {relation.get('segment')} must be a declared hidden (dashed) segment."
        return None

    def _same_point(self, relation) -> str | None:
        points = [self.points.get(name) for name in relation.get("points", [])]
        if len(points) < 2 or None in points:
            return f"Same-point relation {relation.get('points')} uses undeclared points."
        if any(not _close(points[0], point) for point in points[1:]):
            return f"Points {relation['points']} are declared to coincide but do not."
        return None

    def _circle(self, key: str) -> tuple[tuple[float, float], float, dict[str, Any]] | None:
        circle = (self.spec.get("circles") or {}).get(key)
        if not isinstance(circle, dict):
            return None
        centre = self.points.get(circle.get("center"))
        nodes = [node for node in self.root.iter() if node.attrib.get("data-circle") == key]
        if centre is None or not nodes:
            return None
        node = nodes[0]
        try:
            drawn_centre = (float(node.attrib["cx"]), float(node.attrib["cy"]))
            drawn_radius = float(node.attrib["r"])
        except (KeyError, ValueError):
            return None
        if not _close(drawn_centre, centre) or not math.isclose(
            drawn_radius, float(circle["radius"]), abs_tol=0.5
        ):
            return None
        return centre, drawn_radius, {"node": node, **circle}

    def _on_circle(self, relation) -> str | None:
        circle = self._circle(relation.get("circle", ""))
        if circle is None:
            return f"Circle {relation.get('circle')} is not drawn as declared."
        centre, radius, _ = circle
        for name in relation.get("points", []):
            point = self.points.get(name)
            if point is None or not math.isclose(
                math.hypot(point[0] - centre[0], point[1] - centre[1]),
                radius,
                abs_tol=POINT_TOLERANCE,
            ):
                return f"{name} does not lie on circle {relation['circle']}."
        return None

    def _circle_centre(self, relation) -> str | None:
        circle = self._circle(relation.get("circle", ""))
        point = self.points.get(relation.get("point"))
        if circle is None or point is None or not _close(circle[0], point):
            return f"{relation.get('point')} is not the centre of circle {relation.get('circle')}."
        return None

    def _hidden_circle(self, relation) -> str | None:
        circle = self._circle(relation.get("circle", ""))
        if circle is None or not _dashed(circle[2]["node"], self.parents):
            return f"Hidden circle {relation.get('circle')} must be drawn dashed."
        return None

    def _circle_ratio(self, relation) -> str | None:
        circles = [self._circle(key) for key in relation.get("circles", [])]
        if len(circles) != 2 or None in circles:
            return f"Circle ratio {relation.get('circles')} uses undrawn circles."
        ratio = circles[0][1] / circles[1][1]
        if abs(ratio - float(relation["value"])) > float(relation.get("tolerance", 0.01)):
            return f"Circles {relation['circles']} are drawn in ratio {ratio:.3f}, declared {relation['value']}."
        return None

    def _ellipse(self, key: str):
        ellipse = (self.spec.get("ellipses") or {}).get(key)
        if not isinstance(ellipse, dict):
            return None
        centre = self.points.get(ellipse.get("center"))
        halves = [node for node in self.root.iter() if node.attrib.get("data-ellipse") == key]
        if centre is None or len(halves) != 2:
            return None
        rx, ry = float(ellipse["rx"]), float(ellipse["ry"])
        for node in halves:
            polylines = path_polylines(node.attrib.get("d", ""))
            for point in polylines[0] if polylines else []:
                value = ((point[0] - centre[0]) / rx) ** 2 + ((point[1] - centre[1]) / ry) ** 2
                if abs(value - 1) > 0.03:
                    return None
        return centre, rx, ry

    def _on_ellipse(self, relation) -> str | None:
        ellipse = self._ellipse(relation.get("ellipse", ""))
        if ellipse is None:
            return f"Ellipse {relation.get('ellipse')} is not drawn as declared."
        centre, rx, ry = ellipse
        for name in relation.get("points", []):
            point = self.points.get(name)
            if point is None:
                return f"Point {name} is not declared."
            value = ((point[0] - centre[0]) / rx) ** 2 + ((point[1] - centre[1]) / ry) ** 2
            if abs(value - 1) > 0.02:
                return f"{name} does not lie on ellipse {relation['ellipse']}."
        return None

    def _ellipse_centre(self, relation) -> str | None:
        ellipse = self._ellipse(relation.get("ellipse", ""))
        point = self.points.get(relation.get("point"))
        if ellipse is None or point is None or not _close(ellipse[0], point):
            return (
                f"{relation.get('point')} is not the centre of ellipse {relation.get('ellipse')}."
            )
        return None

    def _equal_lengths(self, relation) -> str | None:
        values = [float(value) for value in relation.get("values", [])]
        if len(values) < 2 or any(not math.isclose(values[0], value) for value in values[1:]):
            return f"Declared equal lengths {values} differ."
        return None

    def _cross_angle(self, keys: list[str]) -> float | None:
        ends = [self.endpoints(key) for key in keys]
        if len(ends) != 2 or None in ends:
            return None
        (a, b), (c, d) = ends
        return _angle((0.0, 0.0), (b[0] - a[0], b[1] - a[1]), (d[0] - c[0], d[1] - c[1]))

    def _perpendicular(self, relation) -> str | None:
        measured = self._cross_angle(relation.get("segments", []))
        if measured is None:
            return f"Perpendicular relation {relation.get('segments')} uses undeclared segments."
        if not math.isclose(measured, 90, abs_tol=RIGHT_ANGLE_TOLERANCE):
            return f"Segments {relation['segments']} are declared perpendicular but meet at {measured:.1f}°."
        return None

    def _not_perpendicular(self, relation) -> str | None:
        measured = self._cross_angle(relation.get("segments", []))
        if measured is None:
            return f"Relation {relation.get('segments')} uses undeclared segments."
        if abs(measured - 90) < 10:
            return f"Segments {relation['segments']} must not look perpendicular but meet at {measured:.1f}°."
        return None

    def _unequal_segments(self, relation) -> str | None:
        lengths = [self._length(key) for key in relation.get("segments", [])]
        if len(lengths) != 2 or None in lengths:
            return f"Relation {relation.get('segments')} uses undeclared segments."
        if abs(lengths[0] - lengths[1]) < 0.1 * max(lengths):
            return f"Segments {relation['segments']} are declared unequal but look equal."
        return None

    def _angle_by_marker(self, key: str) -> float | None:
        for item in self.spec.get("angles") or []:
            if item.get("marker_key") == key and len(item.get("arms") or []) == 2:
                vertex = self.points.get(item.get("vertex"))
                first, second = (self.points.get(name) for name in item["arms"])
                if vertex and first and second:
                    return _angle(vertex, first, second)
        return None

    def _angle_sum(self, relation) -> str | None:
        values = [self._angle_by_marker(key) for key in relation.get("angles", [])]
        if not values or None in values:
            return f"Angle sum {relation.get('angles')} uses undeclared angles."
        if not math.isclose(sum(values), float(relation["value"]), abs_tol=2 * ANGLE_TOLERANCE):
            return f"Angles {relation['angles']} are drawn summing to {sum(values):.1f}°, not {relation['value']}°."
        return None

    def _corresponding_angles(self, relation) -> str | None:
        rays = []
        for key in relation.get("angles", []):
            item = next(
                (
                    angle
                    for angle in self.spec.get("angles") or []
                    if angle.get("marker_key") == key
                ),
                None,
            )
            if item is None:
                return f"Corresponding angle {key} is not declared."
            vertex = self.points.get(item.get("vertex"))
            arms = [self.points.get(name) for name in item.get("arms", [])]
            if vertex is None or len(arms) != 2 or None in arms:
                return f"Corresponding angle {key} uses undeclared points."
            rays.append([(arm[0] - vertex[0], arm[1] - vertex[1]) for arm in arms])
        if len(rays) != 2 or any(
            _angle((0.0, 0.0), rays[0][index], rays[1][index]) > 2 * ANGLE_TOLERANCE
            for index in (0, 1)
        ):
            return f"Angles {relation.get('angles')} are not in corresponding positions."
        return None

    # ------------------------------------------------------------ plane-geometry figures
    def _on_drawn_segment(self, point: tuple[float, float]) -> set[str]:
        keys = set()
        for key in self.segments:
            ends = self.endpoints(key)
            if ends and point_segment_distance(point, ends[0], ends[1]) <= POINT_TOLERANCE:
                keys.add(key)
        return keys

    def plane_angle_rays(self) -> None:
        """Each arc must sit on real drawn rays, centred on its vertex and inside its angle."""
        declared = {
            item.get("marker_key"): item
            for item in self.spec.get("angles") or []
            if isinstance(item, dict)
        }
        for marker in self.spec.get("angle_markers") or []:
            key = marker.get("marker_key")
            item = declared.get(key)
            if item is None:
                self.add("geometry_angle_marker_vertex", f"Arc {key} has no declared angle.")
                continue
            vertex = self.points.get(item.get("vertex"))
            arms = [self.points.get(name) for name in item.get("arms", [])]
            if vertex is None or len(arms) != 2 or None in arms:
                self.add("geometry_angle_marker_vertex", f"Arc {key} uses undeclared points.")
                continue
            for name, arm in zip(item["arms"], arms, strict=True):
                if not (self._on_drawn_segment(vertex) & self._on_drawn_segment(arm)):
                    self.add(
                        "geometry_angle_ray_undrawn",
                        f"Arc {key} uses a ray from {item.get('vertex')} to {name} that is not drawn.",
                    )
            measured = _angle(vertex, arms[0], arms[1])
            if not math.isclose(
                float(item.get("drawn_degrees", -1)), measured, abs_tol=ANGLE_TOLERANCE
            ):
                self.add(
                    "geometry_angle_measure",
                    f"Arc {key} records {item.get('drawn_degrees')}° but its rays measure {measured:.1f}°.",
                )
            node = next(
                (
                    candidate
                    for candidate in self.root.iter()
                    if candidate.attrib.get("data-angle-marker") == key
                ),
                None,
            )
            match = _ARC_D.fullmatch(node.attrib.get("d", "")) if node is not None else None
            if match is None:
                self.add("geometry_angle_marker_path", f"Arc {key} must be one M … A … path.")
                continue
            start = (float(match[1]), float(match[2]))
            end = (float(match[7]), float(match[8]))
            centre = arc_centre(start, float(match[3]), int(match[5]), int(match[6]), end)
            if not _close(centre, vertex, 1.5):
                self.add(
                    "geometry_angle_marker_centre",
                    f"Arc {key} is centred at ({centre[0]:.1f}, {centre[1]:.1f}), not on its vertex "
                    f"{item.get('vertex')}.",
                )
                continue
            samples = path_polylines(node.attrib["d"])[0]
            middle = samples[len(samples) // 2]
            if (
                _angle(vertex, middle, arms[0]) > measured + ANGLE_TOLERANCE
                or _angle(vertex, middle, arms[1]) > measured + ANGLE_TOLERANCE
            ):
                self.add(
                    "geometry_angle_marker_sweep",
                    f"Arc {key} sweeps outside the angle between its rays.",
                )

    def plane_label_attachment(self) -> None:
        """A label must sit next to the arc or point it names."""
        radii = {
            item.get("marker_key"): item.get("radius")
            for item in self.spec.get("angle_markers") or []
            if isinstance(item, dict)
        }
        for text in self.texts:
            target = text.element.attrib.get("data-label-for") or ""
            kind, _, name = target.partition(":")
            if kind == "angle" and name in radii:
                item = next(
                    (a for a in self.spec.get("angles") or [] if a.get("marker_key") == name), {}
                )
                vertex = self.points.get(item.get("vertex"))
                if vertex and (
                    segment_box_distance(vertex, vertex, text.box) > float(radii[name]) + MAX_LABEL_GAP
                ):
                    self.add(
                        "geometry_label_detached",
                        f"Label {text.text!r} is too far from its arc {name}.",
                    )
            elif kind == "point":
                point = self.points.get(name)
                if point and segment_box_distance(point, point, text.box) > 30:
                    self.add(
                        "geometry_label_detached", f"Label {text.text!r} is too far from {name}."
                    )

    def plane_markings(self) -> None:
        """Equal ticks and parallel arrows must be on their segments and tell the truth."""
        drawn: dict[str, list[ET.Element]] = {}
        for node in self.root.iter():
            for attribute in ("data-tick-mark", "data-parallel-mark"):
                if attribute in node.attrib:
                    drawn.setdefault(f"{attribute}:{node.attrib[attribute]}", []).append(node)
        declared: set[str] = set()
        for group in self.spec.get("equal_marks") or []:
            keys = group.get("segments") or []
            lengths = [self._length(key) for key in keys]
            if len(keys) < 2 or None in lengths:
                self.add("geometry_marking", f"Equal marks {keys} use undeclared segments.")
                continue
            if max(lengths) - min(lengths) > 2 * POINT_TOLERANCE:
                self.add(
                    "geometry_marking",
                    f"Segments {keys} carry equal marks but measure {[round(v, 1) for v in lengths]}.",
                )
            for key in keys:
                name = f"data-tick-mark:{key}"
                declared.add(name)
                self._check_mark_on_segment(name, key, drawn, group.get("ticks"))
        for group in self.spec.get("parallel_marks") or []:
            keys = group.get("segments") or []
            measured = self._cross_angle(keys)
            if measured is None:
                self.add("geometry_marking", f"Parallel marks {keys} use undeclared segments.")
                continue
            if min(measured, 180 - measured) > 0.5:
                self.add(
                    "geometry_marking",
                    f"Segments {keys} carry parallel marks but meet at {measured:.1f}°.",
                )
            for key in keys:
                name = f"data-parallel-mark:{key}"
                declared.add(name)
                self._check_mark_on_segment(name, key, drawn, None)
        for name in drawn:
            if name not in declared:
                self.add("geometry_marking", f"The SVG has an undeclared marking {name}.")

    def _check_mark_on_segment(self, name, key, drawn, ticks) -> None:
        nodes = drawn.get(name)
        ends = self.endpoints(key)
        if not nodes or ends is None:
            self.add("geometry_marking", f"Segment {key} has no drawn marking.")
            return
        node = nodes[0]
        if ticks is not None and node.attrib.get("data-ticks") != str(ticks):
            self.add("geometry_marking", f"Segment {key} must carry {ticks} tick marks.")
        polylines = path_polylines(node.attrib.get("d", ""))
        if not polylines:
            self.add("geometry_marking", f"The marking on {key} has no path.")
            return
        # A tick crosses the segment at its middle; a parallel chevron touches it at its tip.
        centre = _mean_point(polylines[0]) if ticks is not None else polylines[0][1]
        if point_segment_distance(centre, ends[0], ends[1]) > 2 * POINT_TOLERANCE:
            self.add("geometry_marking", f"The marking on {key} is not on that segment.")

    def plane_arcs(self) -> None:
        """Compass arcs must be centred where declared and pass through the point they locate."""
        arcs = self.spec.get("arcs") or {}
        nodes = {
            node.attrib["data-arc"]: node for node in self.root.iter() if "data-arc" in node.attrib
        }
        for key, arc in arcs.items():
            node = nodes.get(key)
            centre = self.points.get(arc.get("center"))
            through = self.points.get(arc.get("through"))
            match = _ARC_D.fullmatch(node.attrib.get("d", "")) if node is not None else None
            if match is None or centre is None or through is None:
                self.add("geometry_arc", f"Compass arc {key} is not drawn as declared.")
                continue
            start, end = (float(match[1]), float(match[2])), (float(match[7]), float(match[8]))
            actual = arc_centre(start, float(match[3]), int(match[5]), int(match[6]), end)
            if not _close(actual, centre, 1.5) or not math.isclose(
                float(match[3]), float(arc.get("radius", -1)), abs_tol=POINT_TOLERANCE
            ):
                self.add(
                    "geometry_arc", f"Compass arc {key} is not centred on {arc.get('center')}."
                )
                continue
            samples = path_polylines(node.attrib["d"])[0]
            if min(math.hypot(p[0] - through[0], p[1] - through[1]) for p in samples) > 5:
                self.add(
                    "geometry_arc", f"Compass arc {key} does not pass through {arc.get('through')}."
                )
        for key in nodes:
            if key not in arcs:
                self.add("geometry_arc", f"The SVG has an undeclared compass arc {key}.")

    def plane_alternative_text(self) -> None:
        """The alternative text must describe what is drawn and nothing that is not."""
        alt = self.alt_text
        folded = alt.casefold()
        word = PLANE_FIGURE_WORDS.get(self.spec.get("diagram_kind"))
        if word is None:
            self.add(
                "geometry_alt_text_figure",
                f"Unknown plane figure {self.spec.get('diagram_kind')!r}.",
            )
        elif word not in folded:
            self.add("geometry_alt_text_figure", f"The alternative text does not say {word!r}.")
        for label in self.spec.get("labels") or []:
            text = label.get("text", "")
            target = label.get("target", "")
            if not target.startswith("point:") and text not in alt:
                self.add(
                    "geometry_alt_text_values",
                    f"The alternative text omits the label {text!r} shown on the diagram.",
                )
        shown = {number for text in self.texts for number in _NUMBER.findall(text.text)}
        for number in _NUMBER.findall(alt):
            if number not in shown:
                self.add(
                    "geometry_alt_text_values",
                    f"The alternative text states {number}, which the diagram does not show.",
                )
        marked_right = bool(self.spec.get("right_angles"))
        if marked_right != ("right angle" in folded):
            self.add(
                "geometry_alt_text_figure",
                "The alternative text must mention a right angle exactly when one is marked.",
            )
        marked_parallel = bool(self.spec.get("parallel_marks"))
        if marked_parallel != ("parallel" in folded):
            self.add(
                "geometry_alt_text_figure",
                "The alternative text must mention parallel lines exactly when they are marked.",
            )

    # ------------------------------------------------------------------- solids
    def solids(self) -> None:
        relations = [
            item for item in self.spec.get("relationships") or [] if isinstance(item, dict)
        ]

        def has(kind: str, **fields) -> bool:
            return any(
                item.get("type") == kind
                and all(item.get(key) == value for key, value in fields.items())
                for item in relations
            )

        for solid in self.spec.get("solids") or []:
            kind, names = solid.get("type"), solid.get("points") or {}
            if kind == "pyramid":
                base = [names.get(key) for key in ("P1", "P2", "P3", "P4")]
                apex, centre = names.get("V"), names.get("O")
                if not (
                    has("polygon_sides", points=base, count=4)
                    and has("centroid", point=centre, of=base)
                    and has("vertical", points=[apex, centre])
                ):
                    self.add(
                        "geometry_solid_relationship_missing",
                        "A pyramid must declare a four-sided base, its centre and the apex above that centre.",
                    )
                if f"{apex}{centre}" in self.segments and not has(
                    "inside_polygon", point=centre, polygon=base
                ):
                    self.add(
                        "geometry_solid_relationship_missing",
                        "A pyramid's perpendicular height must end inside its base.",
                    )
            elif kind == "cone":
                apex, centre = self.points.get(names.get("V")), self.points.get(names.get("O"))
                if not has("vertical", points=[names.get("V"), names.get("O")]):
                    self.add(
                        "geometry_solid_relationship_missing",
                        "A cone must declare its vertex above or below the base centre.",
                    )
                if apex and centre:
                    down = solid.get("orientation") == "vertex_down"
                    if (apex[1] > centre[1]) != down:
                        self.add(
                            "geometry_solid_orientation",
                            f"The cone is declared {solid.get('orientation')} but is drawn the other way up.",
                        )
            elif kind == "sphere":
                circle = f"{names.get('O', '')[:-1]}sphere" if names.get("O") else None
                if solid.get("given") == "diameter" and not (
                    has("on_circle", circle=circle, points=[names.get("D1"), names.get("D2")])
                    and has("midpoint", point=names.get("O"), of=[names.get("D1"), names.get("D2")])
                ):
                    self.add(
                        "geometry_solid_relationship_missing",
                        "A sphere given by its diameter must show a full diameter through the centre.",
                    )
                if solid.get("inner_sphere") and not has(
                    "hidden_circle", circle=solid["inner_sphere"]
                ):
                    self.add(
                        "geometry_solid_relationship_missing",
                        "An inner sphere must be declared hidden (dashed).",
                    )

    # ----------------------------------------------------------------- dimensions
    def dimension_lines(self) -> None:
        for item in self.spec.get("dimension_lines") or []:
            line = self.endpoints(item.get("segment", ""))
            measured = self.endpoints(item.get("measures", "")) or self._measured_points(
                item.get("measures", "")
            )
            if line is None or measured is None:
                self.add(
                    "geometry_dimension_line",
                    f"Dimension line {item.get('segment')} is incomplete.",
                )
                continue
            offset_a = (line[0][0] - measured[0][0], line[0][1] - measured[0][1])
            offset_b = (line[1][0] - measured[1][0], line[1][1] - measured[1][1])
            direction = (measured[1][0] - measured[0][0], measured[1][1] - measured[0][1])
            dot = offset_a[0] * direction[0] + offset_a[1] * direction[1]
            if not _close(offset_a, offset_b) or abs(dot) > POINT_TOLERANCE * math.hypot(
                *direction
            ):
                self.add(
                    "geometry_dimension_line",
                    f"Dimension line {item.get('segment')} is not parallel to, and as long as, {item.get('measures')}.",
                )

    def _measured_points(self, name: str):
        for split in range(1, len(name)):
            first, second = self.points.get(name[:split]), self.points.get(name[split:])
            if first and second:
                return first, second
        return None

    # ------------------------------------------------------------------- alt text
    def alternative_text(self) -> None:
        alt = self.alt_text
        if not alt.strip():
            self.add("geometry_alt_text_values", "Generated diagrams need alternative text.")
            return
        unknown_targets = {item.get("target") for item in self.spec.get("unknowns") or []}
        for label in self.spec.get("labels") or []:
            if label.get("target") in unknown_targets:
                continue
            for number in _NUMBER.findall(label.get("text", "")):
                if not forbidden_label_pattern(number).search(alt):
                    self.add(
                        "geometry_alt_text_values",
                        f"The alternative text omits the given value {number} shown on the diagram.",
                    )
        for solid in self.spec.get("solids") or []:
            word = SOLID_WORDS.get(solid.get("type"))
            if word and word not in alt.casefold():
                self.add(
                    "geometry_alt_text_solid", f"The alternative text does not name the {word}."
                )

    def run(self) -> list[Issue]:
        self.metadata()
        self.segment_elements()
        self.right_angles()
        self.angles()
        self.labels()
        self.unknowns()
        self.relationships()
        self.solids()
        self.dimension_lines()
        self.alternative_text()
        if self.spec.get("renderer") == PLANE_GEOMETRY_RENDERER:
            self.plane_angle_rays()
            self.plane_label_attachment()
            self.plane_markings()
            self.plane_arcs()
            self.plane_alternative_text()
        self.issues.extend(text_layout_issues(self.root, check_strokes=True))
        return _unique(self.issues)


def _mean_point(points) -> tuple[float, float]:
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def _same_number(first: str, second: str) -> bool:
    try:
        return math.isclose(float(first), float(second), abs_tol=1e-9)
    except ValueError:
        return False


def _unique(issues: Iterable[Issue]) -> list[Issue]:
    seen: set[Issue] = set()
    ordered = []
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            ordered.append(issue)
    return ordered


def checked_diagram_issues(
    root: ET.Element, spec: dict[str, Any], alt_text: str, context: DiagramContext | None
) -> list[Issue]:
    return _Checked(root, spec, alt_text, context).run()
