"""Checks for Sec 1 G5 mensuration diagrams, measured from the SVG and its declared geometry.

Each check answers a defect the G5 pre-review audit reported: an extra or wrong figure, the height
labelled beside a slant, missing measurements, labels the question does not use, a cut-out drawn
for a joined shape, a "cube" that is not one, a solid back rim, hole rims off the face, stray marks
and alternative text that does not describe the drawing.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from typing import Any

from .svg_metrics import local_name, point_segment_distance

SEC1_MENSURATION_RENDERER = "nextscholar-sec1-mensuration-svg-v1"

LENGTH_TOLERANCE = 1.5
RIGHT_TOLERANCE = 0.5
PARALLEL_TOLERANCE = 0.5
COLLINEAR_TOLERANCE = 0.75
NEUTRAL_MARGIN = 0.1

# Which figures each template must draw, and no others.
TEMPLATE_FIGURES: dict[str, tuple[str, ...]] = {
    "parallelogram_area": ("parallelogram",),
    "parallelogram_and_trapezium": ("parallelogram", "trapezium"),
    "trapezium_and_parallelogram_algebra": ("parallelogram", "trapezium"),
    "rectangle_and_square": ("rectangle", "square"),
    "corner_removed": ("l_shape",),
    "corner_removed_algebra": ("l_shape",),
    "joined_rectangles": ("joined_rectangles",),
    "joined_rectangles_algebra": ("joined_rectangles",),
    "uniform_border": ("ring",),
    "track_algebra": ("ring",),
    "cuboid_volume": ("cuboid",),
    "open_box": ("cuboid",),
    "box_with_cube": ("cuboid", "cuboid"),
    "prism_right_triangle_legs": ("prism",),
    "prism_right_triangle_sides": ("prism",),
    "trapezoidal_prism": ("prism",),
    "two_cubes_joined": ("joined_cubes",),
    "block_on_cuboid": ("cuboid", "cuboid"),
    "cuboid_tunnel": ("cuboid", "rectangular_hole"),
    "cuboid_vertical_hole": ("cuboid", "rectangular_hole"),
    "cuboid_cylindrical_hole": ("cuboid", "cylindrical_hole"),
    "cube_cylindrical_hole": ("cuboid", "cylindrical_hole"),
    "open_cylinder": ("cylinder",),
    "open_cylinder_material": ("cylinder",),
}
# A drawn figure must be something the question describes.
FIGURE_WORDS: dict[str, tuple[str, ...]] = {
    "parallelogram": ("parallelogram",),
    "trapezium": ("trapezium",),
    "rectangle": ("rectangle",),
    "square": ("square",),
    "l_shape": ("corner",),
    "joined_rectangles": ("joined",),
    "ring": ("border", "track"),
    "cuboid": ("cuboid", "box", "cube"),
    "prism": ("prism",),
    "joined_cubes": ("cube",),
    "rectangular_hole": ("tunnel", "hole"),
    "cylindrical_hole": ("cylindrical hole",),
    "cylinder": ("cylind",),
}
# And a solid or shape the question names must be drawn.
REQUIRED_FIGURES: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (re.compile(r"parallelogram"), ("parallelogram",)),
    (re.compile(r"trapezium"), ("trapezium", "trapezium_section")),
    (re.compile(r"cuboid|\bbox\b"), ("cuboid",)),
    (re.compile(r"\bprism\b"), ("prism",)),
    (re.compile(r"cylind"), ("cylinder", "cylindrical_hole")),
    (re.compile(r"corner (?:is )?removed|cut from"), ("l_shape",)),
    (re.compile(r"rectangles?\b.*\bjoined|joined\b.*\brectangle"), ("joined_rectangles",)),
)
ALT_WORDS = {
    "parallelogram": ("parallelogram",),
    "two_quadrilaterals": ("trapezium",),
    "composite_plane": ("rectangle",),
    "rectilinear": ("l-shape",),
    "ring": ("rectangle",),
    "cuboid": ("cuboid",),
    "prism": ("prism",),
    "joined_solids": ("cub",),
    "drilled_solid": ("hole", "tunnel"),
    "cylinder": ("cylinder",),
}
ALLOWED_PATH_MARKS = (
    "data-right-angle-marker",
    "data-tick-mark",
    "data-ellipse",
    "data-leader-for",
)
_NUMBER = re.compile(r"(?<![\d.])\d+(?:\.\d+)?")

Point = tuple[float, float]


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _norm(a: Point) -> float:
    return math.hypot(a[0], a[1])


def _sine(a: Point, b: Point) -> float:
    lengths = _norm(a) * _norm(b)
    return abs(_cross(a, b)) / lengths if lengths else 1.0


def _parallel(a: Point, b: Point) -> bool:
    return _sine(a, b) <= math.sin(math.radians(PARALLEL_TOLERANCE))


def _angle(a: Point, b: Point) -> float:
    lengths = _norm(a) * _norm(b)
    if not lengths:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, _dot(a, b) / lengths))))


def _inside(point: Point, polygon: list[Point]) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        if (y1 > point[1]) != (y2 > point[1]):
            if point[0] < (x2 - x1) * (point[1] - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def _on_or_inside(point: Point, polygon: list[Point]) -> bool:
    if _inside(point, polygon):
        return True
    return any(
        point_segment_distance(point, a, b) <= COLLINEAR_TOLERANCE
        for a, b in zip(polygon, [*polygon[1:], polygon[0]], strict=True)
    )


def _normalise(text: str) -> str:
    return re.sub(r"\s+", "", text.replace("−", "-")).casefold()


def _label_is_stated(label: str, stated: str) -> bool:
    """True when the label occurs in the question as a whole token, ignoring spacing."""
    tokens = re.sub(r"\s+", "", label.replace("−", "-"))
    body = r"\s*".join(re.escape(character) for character in tokens)
    pattern = r"(?<![\w.])" + body + r"(?![\w²³])"
    return re.search(pattern, stated.replace("−", "-"), re.IGNORECASE) is not None


class _Sec1Checks:
    def __init__(self, checked: Any):
        self.checked = checked
        self.spec = checked.spec
        self.points: dict[str, Point] = checked.points
        self.figures = [item for item in self.spec.get("figures") or [] if isinstance(item, dict)]
        self.scale = float(self.spec.get("drawn_scale") or 0)

    def add(self, code: str, message: str) -> None:
        self.checked.add(code, message)

    # ------------------------------------------------------------------ small measurements
    def _names(self, names: Iterable[str], what: str) -> list[Point] | None:
        points = [self.points.get(name) for name in names]
        if None in points:
            self.add("geometry_figure_shape", f"The {what} uses undeclared points {list(names)}.")
            return None
        return points  # type: ignore[return-value]

    def _hidden(self, key: str) -> bool:
        return bool((self.checked.segments.get(key) or {}).get("hidden"))

    def _covering(self, start: Point, end: Point) -> list[str] | None:
        """Return the drawn segments that together cover ``start``–``end``, or ``None``."""
        direction = _sub(end, start)
        size = _norm(direction)
        if size == 0:
            return None
        spans = []
        keys = []
        for key in self.checked.segments:
            ends = self.checked.endpoints(key)
            if ends is None:
                continue
            a, b = ends
            if (
                point_segment_distance(a, start, end) > COLLINEAR_TOLERANCE
                and point_segment_distance(start, a, b) > COLLINEAR_TOLERANCE
            ):
                continue
            if not _parallel(_sub(b, a), direction):
                continue
            offset = abs(_cross(_sub(a, start), direction)) / size
            if offset > COLLINEAR_TOLERANCE:
                continue
            t0 = _dot(_sub(a, start), direction) / (size * size)
            t1 = _dot(_sub(b, start), direction) / (size * size)
            low, high = min(t0, t1), max(t0, t1)
            if high <= 0.001 or low >= 0.999:
                continue
            spans.append((low, high))
            keys.append(key)
        reach = 0.0
        for low, high in sorted(spans):
            if low > reach + LENGTH_TOLERANCE / size:
                return None
            reach = max(reach, high)
        return keys if reach >= 1 - LENGTH_TOLERANCE / size else None

    def _edges_drawn(self, names: list[str], what: str) -> None:
        for first, second in zip(names, [*names[1:], names[0]], strict=True):
            p, q = self.points.get(first), self.points.get(second)
            if p is None or q is None or self._covering(p, q) is None:
                self.add("geometry_figure_shape", f"The {what} has no drawn edge {first}{second}.")

    def _is_rectangle(self, names: list[str], what: str) -> bool:
        points = self._names(names, what)
        if points is None or len(points) != 4:
            return False
        for index in range(4):
            a, b, c = points[index - 1], points[index], points[(index + 1) % 4]
            if not math.isclose(_angle(_sub(a, b), _sub(c, b)), 90, abs_tol=RIGHT_TOLERANCE):
                self.add(
                    "geometry_figure_shape", f"The {what} {names} has a corner that is not 90°."
                )
                return False
        return True

    def _polygons_overlap(self, first: list[Point], second: list[Point]) -> bool:
        """True when the interiors of two rectangles overlap."""

        def shrink(polygon: list[Point]) -> list[Point]:
            cx = sum(p[0] for p in polygon) / len(polygon)
            cy = sum(p[1] for p in polygon) / len(polygon)
            return [(cx + (p[0] - cx) * 0.98, cy + (p[1] - cy) * 0.98) for p in polygon]

        a, b = shrink(first), shrink(second)
        if any(_inside(point, b) for point in a) or any(_inside(point, a) for point in b):
            return True
        for p, q in zip(a, [*a[1:], a[0]], strict=True):
            for r, s in zip(b, [*b[1:], b[0]], strict=True):
                d1, d2 = _cross(_sub(q, p), _sub(r, p)), _cross(_sub(q, p), _sub(s, p))
                d3, d4 = _cross(_sub(s, r), _sub(p, r)), _cross(_sub(s, r), _sub(q, r))
                if d1 * d2 < 0 and d3 * d4 < 0:
                    return True
        return False

    def _ellipse_nodes(self, key: str) -> dict[str, Any]:
        return {
            node.attrib.get("data-half"): node
            for node in self.checked.root.iter()
            if node.attrib.get("data-ellipse") == key
        }

    def _half_dashed(self, key: str, half: str) -> bool:
        node = self._ellipse_nodes(key).get(half)
        return node is not None and node.attrib.get("stroke-dasharray") not in {
            None,
            "none",
            "",
            "0",
        }

    def _interior_filled(self, ellipse_key: str, fill: str) -> bool:
        ellipse = (self.spec.get("ellipses") or {}).get(ellipse_key) or {}
        centre = self.points.get(ellipse.get("center"))
        if centre is None:
            return False
        for node in self.checked.root.iter():
            if local_name(node) != "ellipse" or node.attrib.get("fill") != fill:
                continue
            try:
                here = (float(node.attrib["cx"]), float(node.attrib["cy"]))
            except (KeyError, ValueError):
                continue
            if _norm(_sub(here, centre)) <= COLLINEAR_TOLERANCE:
                return True
        return False

    # ---------------------------------------------------------------------- figure shapes
    def figure_shapes(self) -> None:
        for figure in self.figures:
            kind = figure.get("type")
            check = getattr(self, f"_figure_{kind}", None)
            if check is None:
                self.add("geometry_figure_shape", f"Unknown figure type {kind!r}.")
                continue
            check(figure)

    def _heights(self, figure: dict[str, Any], what: str) -> None:
        heights = figure.get("heights") or []
        if not heights:
            self.add("geometry_height", f"The {what} declares no perpendicular height.")
        right_vertices = {
            item.get("vertex")
            for item in self.spec.get("right_angles") or []
            if isinstance(item, dict)
        }
        for height in heights:
            key = height.get("segment", "")
            ends = self.checked.endpoints(key)
            base = self._names(height.get("base", []), what)
            if ends is None or base is None or len(base) != 2:
                self.add("geometry_height", f"The height {key} of the {what} is not drawn.")
                continue
            if not self._hidden(key):
                self.add("geometry_height", f"The height {key} must be dashed.")
            measured = _angle(_sub(ends[1], ends[0]), _sub(base[1], base[0]))
            if not math.isclose(measured, 90, abs_tol=RIGHT_TOLERANCE):
                self.add(
                    "geometry_height",
                    f"The height {key} meets the base at {measured:.1f}°, not at a right angle.",
                )
            foot = self.points.get(height.get("foot", ""))
            if foot is None or point_segment_distance(foot, base[0], base[1]) > COLLINEAR_TOLERANCE:
                self.add("geometry_height", f"The height {key} does not end on its base.")
            if height.get("foot") not in right_vertices:
                self.add(
                    "geometry_height",
                    f"The foot of the height {key} has no right-angle mark.",
                )

    def _figure_parallelogram(self, figure: dict[str, Any]) -> None:
        names = figure.get("points", [])
        points = self._names(names, "parallelogram")
        if points is None or len(points) != 4:
            return
        a, b, c, d = points
        if (
            not _parallel(_sub(b, a), _sub(c, d))
            or not _parallel(_sub(c, b), _sub(d, a))
            or not math.isclose(_norm(_sub(b, a)), _norm(_sub(c, d)), abs_tol=LENGTH_TOLERANCE)
        ):
            self.add(
                "geometry_figure_shape", f"{names} is declared a parallelogram but is not one."
            )
        if math.isclose(_angle(_sub(b, a), _sub(d, a)), 90, abs_tol=5):
            self.add(
                "geometry_figure_shape",
                f"The parallelogram {names} is drawn as a rectangle, so its slant and height coincide.",
            )
        self._edges_drawn(names, "parallelogram")
        self._heights(figure, "parallelogram")

    def _figure_trapezium(self, figure: dict[str, Any]) -> None:
        names = figure.get("points", [])
        points = self._names(names, "trapezium")
        if points is None or len(points) != 4:
            return
        a, b, c, d = points
        if not _parallel(_sub(b, a), _sub(c, d)) or _parallel(_sub(c, b), _sub(d, a)):
            self.add(
                "geometry_figure_shape",
                f"{names} must have exactly one pair of parallel sides to be a trapezium.",
            )
        self._edges_drawn(names, "trapezium")
        self._heights(figure, "trapezium")

    def _figure_rectangle(self, figure: dict[str, Any]) -> None:
        names = figure.get("points", [])
        if self._is_rectangle(names, "rectangle"):
            self._edges_drawn(names, "rectangle")

    def _figure_square(self, figure: dict[str, Any]) -> None:
        names = figure.get("points", [])
        if not self._is_rectangle(names, "square"):
            return
        points = self._names(names, "square")
        assert points is not None
        lengths = [_norm(_sub(p, r)) for p, r in zip(points, [*points[1:], points[0]], strict=True)]
        if max(lengths) - min(lengths) > LENGTH_TOLERANCE:
            self.add("geometry_figure_shape", f"The square {names} has unequal sides.")
        self._edges_drawn(names, "square")
        other = figure.get("non_overlapping")
        if other:
            others = self._names(other, "rectangle")
            if others and self._polygons_overlap(points, others):
                self.add("geometry_figure_overlap", "The square overlaps the rectangle.")

    def _figure_l_shape(self, figure: dict[str, Any]) -> None:
        names = figure.get("points", [])
        points = self._names(names, "L-shape")
        if points is None or len(points) != 6:
            self.add("geometry_figure_shape", "An L-shape must have six vertices.")
            return
        turns = []
        for index in range(6):
            a, b, c = points[index - 1], points[index], points[(index + 1) % 6]
            if not math.isclose(_angle(_sub(a, b), _sub(c, b)), 90, abs_tol=RIGHT_TOLERANCE):
                self.add(
                    "geometry_figure_shape", f"The L-shape's corner {names[index]} is not 90°."
                )
                return
            turns.append(_cross(_sub(b, a), _sub(c, b)))
        positive = sum(turn > 0 for turn in turns)
        if min(positive, 6 - positive) != 1:
            self.add("geometry_figure_shape", "An L-shape must have exactly one inward corner.")
        self._edges_drawn(names, "L-shape")

    def _figure_joined_rectangles(self, figure: dict[str, Any]) -> None:
        first, second = figure.get("first", []), figure.get("second", [])
        if not (
            self._is_rectangle(first, "first rectangle")
            and self._is_rectangle(second, "second rectangle")
        ):
            return
        self._edges_drawn(first, "first rectangle")
        self._edges_drawn(second, "second rectangle")
        a, b = self._names(first, "rectangle"), self._names(second, "rectangle")
        if a and b and self._polygons_overlap(a, b):
            self.add("geometry_figure_overlap", "The joined rectangles overlap.")
        shared = figure.get("shared", "")
        ends = self.checked.endpoints(shared)
        if ends is None:
            self.add("geometry_shared_edge", "Joined rectangles must declare their shared edge.")
            return
        if not self._hidden(shared):
            self.add("geometry_shared_edge", f"The shared edge {shared} must be dashed.")
        for what, polygon in (("first", a), ("second", b)):
            if polygon and not any(
                point_segment_distance(ends[0], p, r) <= COLLINEAR_TOLERANCE
                and point_segment_distance(ends[1], p, r) <= COLLINEAR_TOLERANCE
                for p, r in zip(polygon, [*polygon[1:], polygon[0]], strict=True)
            ):
                self.add(
                    "geometry_shared_edge",
                    f"The shared edge {shared} does not lie along a side of the {what} rectangle.",
                )
        if b:
            sides = [_norm(_sub(p, r)) for p, r in zip(b, [*b[1:], b[0]], strict=True)]
            size = _norm(_sub(ends[1], ends[0]))
            if not any(math.isclose(size, side, abs_tol=LENGTH_TOLERANCE) for side in sides):
                self.add(
                    "geometry_shared_edge",
                    f"The shared edge {shared} is not a complete edge of the smaller rectangle.",
                )

    def _figure_ring(self, figure: dict[str, Any]) -> None:
        outer, inner = figure.get("outer", []), figure.get("inner", [])
        if not (
            self._is_rectangle(outer, "outer rectangle")
            and self._is_rectangle(inner, "inner rectangle")
        ):
            return
        self._edges_drawn(outer, "outer rectangle")
        self._edges_drawn(inner, "inner rectangle")
        o, i = self._names(outer, "ring"), self._names(inner, "ring")
        if not o or not i:
            return
        if not all(_inside(point, o) for point in i):
            self.add("geometry_figure_shape", "The inner rectangle must lie inside the outer one.")
        if figure.get("uniform"):
            xs_o, ys_o = [p[0] for p in o], [p[1] for p in o]
            xs_i, ys_i = [p[0] for p in i], [p[1] for p in i]
            gaps = [
                min(xs_i) - min(xs_o),
                max(xs_o) - max(xs_i),
                min(ys_i) - min(ys_o),
                max(ys_o) - max(ys_i),
            ]
            if max(gaps) - min(gaps) > LENGTH_TOLERANCE:
                self.add(
                    "geometry_figure_shape",
                    f"The band is declared uniform but its widths are {[round(g, 1) for g in gaps]}.",
                )

    def _figure_cuboid(self, figure: dict[str, Any]) -> None:
        names = figure.get("vertices") or {}
        groups = {
            "length": (("F1", "F2"), ("F4", "F3"), ("B4", "B3"), ("B1", "B2")),
            "height": (("F1", "F4"), ("F2", "F3"), ("B1", "B4"), ("B2", "B3")),
            "depth": (("F1", "B1"), ("F2", "B2"), ("F3", "B3"), ("F4", "B4")),
        }
        hidden_vertex = figure.get("hidden_vertex")
        occluded = {tuple(pair) for pair in figure.get("occluded") or []}
        lengths: dict[str, float] = {}
        for group, edges in groups.items():
            vectors = []
            for first, second in edges:
                p, r = self.points.get(names.get(first, "")), self.points.get(names.get(second, ""))
                if p is None or r is None:
                    continue
                vectors.append(_sub(r, p))
                keys = self._covering(p, r)
                if keys is None:
                    self.add(
                        "geometry_figure_shape",
                        f"The cuboid has no drawn edge {names[first]}{names[second]}.",
                    )
                    continue
                touches_hidden = hidden_vertex in (names[first], names[second])
                dashed = [key for key in keys if self._hidden(key)]
                if touches_hidden and len(dashed) != len(keys):
                    self.add(
                        "geometry_hidden_edge",
                        f"The hidden edge {names[first]}{names[second]} must be dashed.",
                    )
                if not touches_hidden and dashed:
                    allowed = {f"{first_name}{second_name}" for first_name, second_name in occluded}
                    if not set(dashed) <= allowed:
                        self.add(
                            "geometry_hidden_edge",
                            f"The visible edge {names[first]}{names[second]} must be solid.",
                        )
            if not vectors:
                self.add("geometry_figure_shape", f"The cuboid has no {group} edges.")
                continue
            for vector in vectors[1:]:
                if not _parallel(vectors[0], vector) or not math.isclose(
                    _norm(vectors[0]), _norm(vector), abs_tol=LENGTH_TOLERANCE
                ):
                    self.add(
                        "geometry_figure_shape",
                        f"The cuboid's {group} edges are not equal and parallel.",
                    )
                    break
            lengths[group] = _norm(vectors[0])
        if figure.get("cube"):
            factor = 1.0 if figure.get("projection") == "isometric" else 0.5
            expected = lengths.get("length", 0.0)
            if not math.isclose(
                lengths.get("height", -1.0), expected, abs_tol=LENGTH_TOLERANCE
            ) or (
                not math.isclose(
                    lengths.get("depth", -1.0), expected * factor, abs_tol=LENGTH_TOLERANCE
                )
            ):
                self.add(
                    "geometry_figure_shape",
                    f"The cube is drawn with edges {[round(v, 1) for v in lengths.values()]}.",
                )
        if figure.get("open_top"):
            if "open" not in self.checked.alt_text.casefold() or not any(
                "open" in text.text.casefold() for text in self.checked.texts
            ):
                self.add(
                    "geometry_open_top", "An open-top solid must say so in the image and alt text."
                )
        face = figure.get("on_top_of")
        if face:
            polygon = self._names(face, "top face")
            base = [self.points.get(names.get(key, "")) for key in ("F1", "F2", "B1", "B2")]
            if polygon and (None in base or not all(_on_or_inside(p, polygon) for p in base)):  # type: ignore[arg-type]
                self.add(
                    "geometry_figure_overlap",
                    "The attached block must rest wholly on the top face of the cuboid.",
                )

    def _figure_prism(self, figure: dict[str, Any]) -> None:
        front, back = figure.get("front", []), figure.get("back", [])
        f, b = self._names(front, "prism"), self._names(back, "prism")
        if not f or not b or len(f) != len(b):
            self.add("geometry_figure_shape", "A prism needs matching front and rear faces.")
            return
        offset = _sub(b[0], f[0])
        for p, r in zip(f, b, strict=True):
            if _norm(_sub(_sub(r, p), offset)) > LENGTH_TOLERANCE:
                self.add(
                    "geometry_figure_shape",
                    "The prism's rear face is not a translated copy of its front face.",
                )
                break
        hidden_vertex = figure.get("hidden_vertex")
        pairs = [(front[i], back[i]) for i in range(len(front))]
        pairs += [(back[i], back[(i + 1) % len(back)]) for i in range(len(back))]
        pairs += [(front[i], front[(i + 1) % len(front)]) for i in range(len(front))]
        for first, second in pairs:
            p, r = self.points.get(first), self.points.get(second)
            keys = self._covering(p, r) if p and r else None
            if keys is None:
                self.add("geometry_figure_shape", f"The prism has no drawn edge {first}{second}.")
                continue
            should_hide = hidden_vertex in (first, second)
            if should_hide != all(self._hidden(key) for key in keys):
                wanted = "dashed" if should_hide else "solid"
                self.add(
                    "geometry_hidden_edge", f"The prism edge {first}{second} must be {wanted}."
                )
        section = figure.get("cross_section") or {}
        kind = section.get("type")
        if kind == "right_triangle":
            at = section.get("right_at")
            names = section.get("points", [])
            points = self._names(names, "cross-section")
            if not points or at not in names:
                return
            index = names.index(at)
            vertex = points[index]
            others = [point for point in points if point is not vertex]
            measured = _angle(_sub(others[0], vertex), _sub(others[1], vertex))
            if not math.isclose(measured, 90, abs_tol=RIGHT_TOLERANCE):
                self.add(
                    "geometry_figure_shape",
                    f"The right-triangle cross-section measures {measured:.1f}° at {at}.",
                )
            if not any(item.get("vertex") == at for item in self.spec.get("right_angles") or []):
                self.add(
                    "geometry_right_angle_missing",
                    "The right-triangle cross-section must mark its right angle.",
                )
        elif kind == "trapezium":
            self._figure_trapezium(section)
        else:
            self.add("geometry_figure_shape", f"Unknown prism cross-section {kind!r}.")

    def _figure_joined_cubes(self, figure: dict[str, Any]) -> None:
        first, second = figure.get("first", []), figure.get("second", [])
        a, b = self._names(first, "first cube"), self._names(second, "second cube")
        if not a or not b or len(a) != 8 or len(b) != 8:
            self.add("geometry_figure_shape", "Joined cubes must declare eight vertices each.")
            return
        for what, cube in (("first", a), ("second", b)):
            front = cube[:4]
            sides = [_norm(_sub(p, r)) for p, r in zip(front, [*front[1:], front[0]], strict=True)]
            corner = _angle(_sub(front[1], front[0]), _sub(front[3], front[0]))
            if max(sides) - min(sides) > LENGTH_TOLERANCE or not math.isclose(
                corner, 90, abs_tol=RIGHT_TOLERANCE
            ):
                self.add(
                    "geometry_figure_shape",
                    f"The {what} cube's front face is not square: {[round(v, 1) for v in sides]}.",
                )
        size_a, size_b = _norm(_sub(a[1], a[0])), _norm(_sub(b[1], b[0]))
        if not math.isclose(size_a, size_b, abs_tol=LENGTH_TOLERANCE):
            self.add(
                "geometry_figure_shape",
                f"Identical cubes are drawn with edges {size_a:.1f} and {size_b:.1f}.",
            )
        if any(
            _norm(_sub(_sub(a[index + 4], a[index]), _sub(b[index + 4], b[index])))
            > LENGTH_TOLERANCE
            for index in range(4)
        ):
            self.add("geometry_figure_shape", "The two cubes have different depths.")
        shared = {first[1], first[2], first[5], first[6]} & {
            second[0],
            second[3],
            second[4],
            second[7],
        }
        if len(shared) != 4:
            self.add("geometry_figure_shape", "The cubes must share one complete face.")
        if figure.get("shared_face") not in (self.spec.get("shades") or []):
            self.add("geometry_shared_edge", "The shared face of joined cubes must be shaded.")

    def _hole_face(self, figure: dict[str, Any]) -> list[Point] | None:
        return self._names(figure.get("face", []), "face")

    def _figure_rectangular_hole(self, figure: dict[str, Any]) -> None:
        near, far = figure.get("near", []), figure.get("far", [])
        n, r = self._names(near, "hole"), self._names(far, "hole")
        face = self._hole_face(figure)
        if not n or not r or not face or len(n) != 4 or len(r) != 4:
            self.add(
                "geometry_hole", "A rectangular hole needs a near and a far rectangle on a face."
            )
            return
        if not all(_inside(point, face) for point in n):
            self.add("geometry_hole", "The hole's opening must lie inside its face.")
        for first, second in zip(near, [*near[1:], near[0]], strict=True):
            keys = self._covering(self.points[first], self.points[second])
            if keys is None or any(self._hidden(key) for key in keys):
                self.add("geometry_hole", f"The hole's opening edge {first}{second} must be solid.")
        hidden_pairs = list(zip(far, [*far[1:], far[0]], strict=True)) + list(
            zip(near, far, strict=True)
        )
        for first, second in hidden_pairs:
            keys = self._covering(self.points[first], self.points[second])
            if keys is None or not all(self._hidden(key) for key in keys):
                self.add("geometry_hole", f"The hole's hidden edge {first}{second} must be dashed.")
        offset = _sub(r[0], n[0])
        if any(
            _norm(_sub(_sub(b, a), offset)) > LENGTH_TOLERANCE for a, b in zip(n, r, strict=True)
        ):
            self.add(
                "geometry_hole", "The hole's far rectangle is not a translated copy of its opening."
            )

    def _figure_cylindrical_hole(self, figure: dict[str, Any]) -> None:
        near = figure.get("near", "")
        far = figure.get("far", "")
        ellipses = self.spec.get("ellipses") or {}
        rim, end = ellipses.get(near), ellipses.get(far)
        face = self._hole_face(figure)
        if not rim or not end or not face:
            self.add("geometry_hole", "A cylindrical hole needs two ellipses and a face.")
            return
        centre = self.points.get(rim.get("center"))
        if centre is None:
            self.add("geometry_hole", "The hole's rim has no centre.")
            return
        rx, ry = float(rim["rx"]), float(rim["ry"])
        extremes = [
            (centre[0] - rx, centre[1]),
            (centre[0] + rx, centre[1]),
            (centre[0], centre[1] - ry),
            (centre[0], centre[1] + ry),
        ]
        if not all(_inside(point, face) for point in extremes):
            self.add("geometry_hole", "The hole's rim must lie wholly inside its face.")
        if self._half_dashed(near, "back") or self._half_dashed(near, "front"):
            self.add("geometry_hole", "The hole's near rim must be solid.")
        if not (self._half_dashed(far, "back") and self._half_dashed(far, "front")):
            self.add("geometry_hole", "The hole's far rim must be dashed.")
        for key in figure.get("sides", []):
            if not self._hidden(key):
                self.add("geometry_hole", f"The hole's side {key} must be dashed.")
        self._radius(figure.get("radius", ""), near, "hole")

    def _radius(self, key: str, ellipse_key: str, what: str) -> None:
        ends = self.checked.endpoints(key)
        ellipse = (self.spec.get("ellipses") or {}).get(ellipse_key) or {}
        centre = self.points.get(ellipse.get("center"))
        if ends is None or centre is None:
            self.add("geometry_figure_shape", f"The {what} must draw its radius.")
            return
        if _norm(_sub(ends[0], centre)) > COLLINEAR_TOLERANCE:
            self.add("geometry_figure_shape", f"The {what}'s radius does not start at the centre.")
        rx, ry = float(ellipse["rx"]), float(ellipse["ry"])
        value = ((ends[1][0] - centre[0]) / rx) ** 2 + ((ends[1][1] - centre[1]) / ry) ** 2
        if abs(value - 1) > 0.03:
            self.add("geometry_figure_shape", f"The {what}'s radius does not reach its rim.")

    def _figure_cylinder(self, figure: dict[str, Any]) -> None:
        rim_key, base_key = figure.get("rim", ""), figure.get("base", "")
        ellipses = self.spec.get("ellipses") or {}
        rim, base = ellipses.get(rim_key), ellipses.get(base_key)
        if not rim or not base:
            self.add("geometry_figure_shape", "A cylinder needs a rim and a base ellipse.")
            return
        if not math.isclose(float(rim["rx"]), float(base["rx"]), abs_tol=0.5):
            self.add("geometry_figure_shape", "A cylinder's rim and base must have equal radii.")
        if not self._half_dashed(base_key, "back"):
            self.add("geometry_hidden_edge", "The far half of the cylinder's base must be dashed.")
        if self._half_dashed(base_key, "front") or self._half_dashed(rim_key, "back"):
            self.add("geometry_hidden_edge", "Visible cylinder arcs must be solid.")
        for key in figure.get("sides", []):
            ends = self.checked.endpoints(key)
            if ends is None or abs(ends[0][0] - ends[1][0]) > COLLINEAR_TOLERANCE:
                self.add("geometry_figure_shape", f"The cylinder's side {key} must be vertical.")
        self._radius(figure.get("radius", ""), rim_key, "cylinder")
        if figure.get("open_top"):
            if not self._interior_filled(rim_key, figure.get("interior", "")):
                self.add("geometry_open_top", "An open cylinder must shade the inside of its rim.")
            if "open" not in self.checked.alt_text.casefold() or not any(
                "open" in text.text.casefold() for text in self.checked.texts
            ):
                self.add(
                    "geometry_open_top", "An open cylinder must say so in the image and alt text."
                )

    # ----------------------------------------------------------------------- the right figure
    def figure_matches_template(self) -> None:
        template = self.spec.get("template")
        expected = TEMPLATE_FIGURES.get(template)
        drawn = tuple(sorted(figure.get("type", "") for figure in self.figures))
        if expected is None:
            self.add("geometry_figure_mismatch", f"Template {template!r} has no expected figures.")
        elif drawn != tuple(sorted(expected)):
            self.add(
                "geometry_figure_mismatch",
                f"Template {template} must draw {sorted(expected)}, but draws {list(drawn)}.",
            )

    def figure_matches_question(self) -> None:
        context = self.checked.context
        if context is None or not context.stated_text:
            return
        stated = context.stated_text.casefold()
        drawn = {figure.get("type") for figure in self.figures}
        for figure in self.figures:
            section = figure.get("cross_section") or {}
            if section.get("type") == "trapezium":
                drawn.add("trapezium_section")
            words = FIGURE_WORDS.get(figure.get("type"), ())
            if words and not any(word in stated for word in words):
                self.add(
                    "geometry_figure_not_in_question",
                    f"The figure {figure.get('type')} is not something the question describes.",
                )
        for pattern, kinds in REQUIRED_FIGURES:
            if pattern.search(stated) and not drawn & set(kinds):
                self.add(
                    "geometry_figure_not_in_question",
                    f"The question mentions {pattern.pattern!r} but the diagram does not draw it.",
                )

    # ------------------------------------------------------------------------ stray marks
    def stray_marks(self) -> None:
        owned = {key for figure in self.figures for key in figure.get("segments", [])}
        for key, segment in self.checked.segments.items():
            if segment.get("role") == "dimension":
                continue
            if key not in owned:
                self.add("geometry_stray_stroke", f"Segment {key} belongs to no declared figure.")
        shades = set(self.spec.get("shades") or [])
        ellipses = self.spec.get("ellipses") or {}
        centres = [self.points.get(item.get("center")) for item in ellipses.values()]
        for node in self.checked.root.iter():
            name = local_name(node)
            if name == "path":
                if not any(mark in node.attrib for mark in ALLOWED_PATH_MARKS):
                    self.add(
                        "geometry_stray_stroke", f"The path {node.attrib.get('d')!r} is undeclared."
                    )
            elif name == "polygon":
                if node.attrib.get("data-shape") not in shades:
                    self.add(
                        "geometry_stray_stroke", "A polygon in the SVG is not a declared shape."
                    )
            elif name == "rect":
                if node.attrib.get("data-role") != "background":
                    self.add(
                        "geometry_stray_stroke", "A rectangle in the SVG is not a declared shape."
                    )
            elif name == "ellipse":
                try:
                    here = (float(node.attrib["cx"]), float(node.attrib["cy"]))
                except (KeyError, ValueError):
                    here = None
                if here is None or not any(
                    centre and _norm(_sub(here, centre)) <= COLLINEAR_TOLERANCE
                    for centre in centres
                ):
                    self.add("geometry_stray_stroke", "An ellipse in the SVG is not declared.")
        captions = set(self.spec.get("captions") or [])
        for text in self.checked.texts:
            attrib = text.element.attrib
            if attrib.get("data-label-for") or attrib.get("data-role") == "note":
                continue
            if text.text not in captions:
                self.add("geometry_stray_text", f"The text {text.text!r} is not declared.")
            elif re.search(r"\d", text.text):
                self.add(
                    "geometry_stray_text", f"The caption {text.text!r} must not state a value."
                )

    def duplicate_strokes(self) -> None:
        keys = list(self.checked.segments)
        for index, first in enumerate(keys):
            ends = self.checked.endpoints(first)
            if ends is None:
                continue
            a, b = ends
            direction = _sub(b, a)
            size = _norm(direction)
            if not size:
                continue
            for second in keys[index + 1 :]:
                other = self.checked.endpoints(second)
                if other is None:
                    continue
                c, d = other
                if not _parallel(direction, _sub(d, c)):
                    continue
                if abs(_cross(_sub(c, a), direction)) / size > COLLINEAR_TOLERANCE:
                    continue
                t0 = _dot(_sub(c, a), direction) / size
                t1 = _dot(_sub(d, a), direction) / size
                overlap = min(size, max(t0, t1)) - max(0.0, min(t0, t1))
                if overlap > LENGTH_TOLERANCE:
                    self.add(
                        "geometry_duplicate_stroke",
                        f"Segments {first} and {second} are drawn over each other.",
                    )

    # ------------------------------------------------------------------- lengths and labels
    def measures(self) -> None:
        declared = [item for item in self.spec.get("measures") or [] if isinstance(item, dict)]
        neutral = {
            item.get("variable"): item
            for item in self.spec.get("neutral_lengths") or []
            if isinstance(item, dict)
        }
        labels = {
            (label.get("target"), label.get("text")) for label in self.spec.get("labels") or []
        }
        for item in declared:
            key, text = item.get("segment", ""), item.get("label", "")
            if (f"segment:{key}", text) not in labels:
                self.add(
                    "geometry_given_unlabelled", f"The length {text!r} is not labelled on {key}."
                )
            size = self.checked._length(key)
            if size is None:
                self.add("geometry_drawn_length", f"The length {text!r} measures undeclared {key}.")
                continue
            if "variable" in item:
                record = neutral.get(item["variable"])
                if record is None:
                    self.add(
                        "geometry_neutral_length",
                        f"The unknown {item['variable']} has no declared neutral size.",
                    )
                    continue
                value = float(record["drawn"]) + float(item.get("constant", 0))
            else:
                value = float(item.get("value") or 0)
            expected = value * self.scale * float(item.get("factor", 1))
            if abs(size - expected) > LENGTH_TOLERANCE:
                self.add(
                    "geometry_drawn_length",
                    f"{key}, labelled {text!r}, measures {size:.1f} but should measure {expected:.1f}.",
                )
        shown = {item.get("label") for item in declared}
        for name, value in (self.spec.get("dimensions") or {}).items():
            for label in _dimension_labels(value):
                if label not in shown and _normalise(label) not in {
                    _normalise(s or "") for s in shown
                }:
                    self.add(
                        "geometry_given_unlabelled",
                        f"The given {name} ({label}) is not labelled on the diagram.",
                    )
        for variable, record in neutral.items():
            avoid = float(record.get("avoid", 0))
            drawn = float(record.get("drawn", 0))
            if avoid and abs(drawn - avoid) < NEUTRAL_MARGIN * avoid:
                self.add(
                    "geometry_neutral_length",
                    f"The unknown {variable} is drawn at {drawn:g}, too close to its true value.",
                )

    def labels_are_stated(self) -> None:
        context = self.checked.context
        if context is None or not context.stated_text:
            return
        unknown = {item.get("label") for item in self.spec.get("unknowns") or []}
        for label in self.spec.get("labels") or []:
            text = label.get("text", "")
            if text in unknown:
                continue
            # A bare letter would match ordinary words such as "a", so it must be a declared unknown.
            if re.fullmatch(r"[A-Za-z]", text) or not _label_is_stated(text, context.stated_text):
                self.add(
                    "geometry_label_not_stated",
                    f"The label {text!r} is not a length the question states.",
                )

    def alternative_text(self) -> None:
        alt = self.checked.alt_text
        folded = alt.casefold()
        words = ALT_WORDS.get(self.spec.get("diagram_kind"), ())
        if not any(word in folded for word in words):
            self.add("geometry_alt_text_figure", f"The alternative text does not say {words!r}.")
        for label in self.spec.get("labels") or []:
            text = label.get("text", "")
            if text not in alt:
                self.add(
                    "geometry_alt_text_values",
                    f"The alternative text omits the label {text!r} shown on the diagram.",
                )
        shown = {number for text in self.checked.texts for number in _NUMBER.findall(text.text)}
        for number in _NUMBER.findall(alt):
            if number not in shown:
                self.add(
                    "geometry_alt_text_values",
                    f"The alternative text states {number}, which the diagram does not show.",
                )
        if bool(self.spec.get("right_angles")) != ("right angle" in folded):
            self.add(
                "geometry_alt_text_figure",
                "The alternative text must mention a right angle exactly when one is marked.",
            )
        if "dashed" in folded and not any(
            "stroke-dasharray" in node.attrib for node in self.checked.root.iter()
        ):
            self.add(
                "geometry_alt_text_figure",
                "The alternative text mentions dashes that are not drawn.",
            )

    def run(self) -> None:
        self.figure_matches_template()
        self.figure_matches_question()
        self.figure_shapes()
        self.stray_marks()
        self.duplicate_strokes()
        self.measures()
        self.labels_are_stated()
        self.alternative_text()
        self.checked.plane_markings()
        self.checked.plane_label_attachment()


def _dimension_labels(value: Any) -> list[str]:
    """Return the labels a stored dimension must appear as on the diagram."""
    if isinstance(value, dict) and "value" in value:
        unit_name = value.get("unit")
        amount = f"{float(value['value']):g}"
        return [f"{amount} {unit_name}" if unit_name else amount]
    if isinstance(value, list):
        labels: list[str] = []
        for item in value:
            labels.extend(_dimension_labels(item))
        return labels
    if isinstance(value, str):
        return [value]
    return []


def sec1_mensuration_issues(checked: Any) -> None:
    """Add the Sec 1 G5 issues to a ``_Checked`` run in ``diagram_checks``."""
    _Sec1Checks(checked).run()
