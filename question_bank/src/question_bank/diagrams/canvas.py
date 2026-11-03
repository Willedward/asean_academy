"""A small deterministic SVG canvas that records machine-checkable geometry as it draws."""

from __future__ import annotations

import html
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..svg_metrics import (
    Box,
    baseline_for_center,
    ellipse_points,
    phone_font_px,
    segment_box_distance,
    text_box,
    text_extents,
    text_width,
)

Point = tuple[float, float]

WIDTH = 600
INK = "#124e52"
FILL = "#e7f2f0"
FILL_ALT = "#fdf3e6"
LIQUID = "#cfe3f6"
LIQUID_INK = "#2563a6"
ACCENT = "#c2620a"
TEXT = "#153f42"
ANGLE_TEXT = "#8a4406"
MUTED = "#55696d"
BACKGROUND = "#f7faf9"
LIGHT = "#7d9799"

LABEL_SIZE = 26
CAPTION_SIZE = 24
NOTE_SIZE = 22
STROKE = 5
THIN = 3
DASH = "10 8"
MIN_LABEL_CLEARANCE = 4.0
LABEL_GAP = 6.0
EDGE_MARGIN = 6.0


class DiagramLayoutError(ValueError):
    """Raised when a label cannot be placed without touching strokes, labels or edges."""


def fmt(value: float) -> str:
    """Format a coordinate or value deterministically with at most two decimals."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text


def rounded(point: Point) -> Point:
    return (float(fmt(point[0])), float(fmt(point[1])))


def add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def scale(a: Point, factor: float) -> Point:
    return (a[0] * factor, a[1] * factor)


def length(a: Point) -> float:
    return math.hypot(a[0], a[1])


def unit(a: Point) -> Point:
    size = length(a)
    return (a[0] / size, a[1] / size)


def lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def angle_between(vertex: Point, first: Point, second: Point) -> float:
    u, v = unit(sub(first, vertex)), unit(sub(second, vertex))
    cosine = max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))
    return math.degrees(math.acos(cosine))


def _attrs(values: dict[str, Any]) -> str:
    return "".join(
        f' {key}="{html.escape(str(value), quote=True)}"'
        for key, value in values.items()
        if value is not None
    )


@dataclass
class Canvas:
    height: float
    width: float = WIDTH
    figure: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    strokes: list[tuple[list[Point], float]] = field(default_factory=list)
    text_boxes: list[Box] = field(default_factory=list)
    points: dict[str, Point] = field(default_factory=dict)
    segments: list[dict[str, Any]] = field(default_factory=list)
    right_angles: list[dict[str, Any]] = field(default_factory=list)
    angles: list[dict[str, Any]] = field(default_factory=list)
    angle_markers: list[dict[str, Any]] = field(default_factory=list)
    circles: dict[str, dict[str, float]] = field(default_factory=dict)
    ellipses: dict[str, dict[str, float]] = field(default_factory=dict)
    placed_labels: list[dict[str, Any]] = field(default_factory=list)
    dimension_lines: list[dict[str, str]] = field(default_factory=list)
    leaders: list[dict[str, Any]] = field(default_factory=list)
    segment_ends: dict[str, tuple[Point, Point]] = field(default_factory=dict)
    segment_keys: dict[tuple[str, str], str] = field(default_factory=dict)

    # ----------------------------------------------------------------- geometry
    def point(self, name: str, xy: Point) -> Point:
        value = rounded(xy)
        if name in self.points and self.points[name] != value:
            raise ValueError(f"Point {name} redefined")
        self.points[name] = value
        return value

    def _register_stroke(self, polyline: Sequence[Point], width: float) -> None:
        self.strokes.append(([rounded(point) for point in polyline], width / 2))

    def segment(
        self,
        key: str,
        start: str,
        end: str,
        *,
        hidden: bool = False,
        stroke: str = INK,
        width: float = STROKE,
        role: str = "edge",
    ) -> None:
        p, q = self.points[start], self.points[end]
        self.figure.append(
            "<line"
            + _attrs(
                {
                    "data-segment": key,
                    "x1": fmt(p[0]),
                    "y1": fmt(p[1]),
                    "x2": fmt(q[0]),
                    "y2": fmt(q[1]),
                    "stroke": stroke,
                    "stroke-width": fmt(width),
                    "stroke-dasharray": DASH if hidden else None,
                }
            )
            + "/>"
        )
        self._register_stroke([p, q], width)
        self.segment_ends[key] = (p, q)
        self.segment_keys[(start, end)] = key
        self.segments.append({"key": key, "from": start, "to": end, "hidden": hidden, "role": role})

    def polygon(
        self,
        names: Sequence[str],
        *,
        fill: str = FILL,
        stroke: str | None = None,
        width: float = STROKE,
        role: str | None = None,
    ) -> None:
        points = [self.points[name] for name in names]
        self.figure.append(
            "<polygon"
            + _attrs(
                {
                    "data-shape": role,
                    "data-points": " ".join(names) if role else None,
                    "points": " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points),
                    "fill": fill,
                    "stroke": stroke or "none",
                    "stroke-width": fmt(width) if stroke else None,
                }
            )
            + "/>"
        )
        if stroke:
            self._register_stroke([*points, points[0]], width)

    def raw_path(
        self,
        d: str,
        polylines: Iterable[Sequence[Point]],
        *,
        stroke: str = INK,
        width: float = STROKE,
        fill: str = "none",
        hidden: bool = False,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        self.figure.append(
            "<path"
            + _attrs(
                {
                    **(attrs or {}),
                    "d": d,
                    "fill": fill,
                    "stroke": stroke,
                    "stroke-width": fmt(width),
                    "stroke-dasharray": DASH if hidden else None,
                }
            )
            + "/>"
        )
        if stroke != "none":
            for polyline in polylines:
                self._register_stroke(polyline, width)

    def ellipse(
        self,
        key: str,
        center: str,
        rx: float,
        ry: float,
        *,
        hidden_back: bool = True,
        hidden_front: bool = False,
        stroke: str = INK,
        width: float = STROKE,
        fill: str | None = None,
    ) -> None:
        """Draw a horizontal ellipse as front (lower) and back (upper) halves.

        ``hidden_back`` dashes the far half, as for the base of a cone or cylinder.
        """
        cx, cy = self.points[center]
        rx, ry = float(fmt(rx)), float(fmt(ry))
        left, right = (cx - rx, cy), (cx + rx, cy)
        if fill:
            self.figure.append(
                "<ellipse"
                + _attrs(
                    {
                        "cx": fmt(cx),
                        "cy": fmt(cy),
                        "rx": fmt(rx),
                        "ry": fmt(ry),
                        "fill": fill,
                        "stroke": "none",
                    }
                )
                + "/>"
            )
        for half, start_deg, end_deg, sweep, hidden in (
            ("back", 180, 0, 1, hidden_back),
            ("front", 180, 360, 0, hidden_front),
        ):
            d = (
                f"M{fmt(left[0])} {fmt(left[1])} A{fmt(rx)} {fmt(ry)} 0 0 {sweep} "
                f"{fmt(right[0])} {fmt(right[1])}"
            )
            self.raw_path(
                d,
                [ellipse_points(cx, cy, rx, ry, start_deg, end_deg)],
                stroke=stroke,
                width=width,
                hidden=hidden,
                attrs={"data-ellipse": key, "data-half": half},
            )
        self.ellipses[key] = {"center": center, "rx": rx, "ry": ry}

    def circle(
        self,
        key: str,
        center: str,
        radius: float,
        *,
        fill: str = FILL,
        stroke: str = INK,
        width: float = STROKE,
        hidden: bool = False,
    ) -> None:
        cx, cy = self.points[center]
        radius = float(fmt(radius))
        self.figure.append(
            "<circle"
            + _attrs(
                {
                    "data-circle": key,
                    "cx": fmt(cx),
                    "cy": fmt(cy),
                    "r": fmt(radius),
                    "fill": fill,
                    "stroke": stroke,
                    "stroke-width": fmt(width),
                    "stroke-dasharray": DASH if hidden else None,
                }
            )
            + "/>"
        )
        self._register_stroke(ellipse_points(cx, cy, radius, radius), width)
        self.circles[key] = {"center": center, "radius": radius, "hidden": hidden}

    def fill(self, points: Sequence[Point], fill: str) -> None:
        """Draw an unstroked filled region, such as the silhouette of a solid."""
        self.figure.append(
            "<polygon"
            + _attrs(
                {
                    "points": " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points),
                    "fill": fill,
                    "stroke": "none",
                }
            )
            + "/>"
        )

    def dot(self, name: str, radius: float = 5, fill: str = INK) -> None:
        x, y = self.points[name]
        self.figure.append(
            "<circle"
            + _attrs(
                {"data-point": name, "cx": fmt(x), "cy": fmt(y), "r": fmt(radius), "fill": fill}
            )
            + "/>"
        )
        self._register_stroke([(x - radius, y), (x + radius, y)], radius * 2)

    def right_angle(self, vertex: str, first: str, second: str, size: float = 22) -> None:
        v = self.points[vertex]
        u = unit(sub(self.points[first], v))
        w = unit(sub(self.points[second], v))
        p1 = rounded(add(v, scale(u, size)))
        p3 = rounded(add(v, scale(w, size)))
        p2 = rounded(add(add(v, scale(u, size)), scale(w, size)))
        d = f"M{fmt(p1[0])} {fmt(p1[1])} L{fmt(p2[0])} {fmt(p2[1])} L{fmt(p3[0])} {fmt(p3[1])}"
        self.raw_path(
            d,
            [[p1, p2, p3]],
            stroke=ACCENT,
            width=THIN + 0.5,
            attrs={"data-right-angle-marker": vertex},
        )
        self.right_angles.append({"vertex": vertex, "arms": [first, second], "marker_size": size})

    def angle_arc(
        self,
        key: str,
        vertex: str,
        first: str,
        second: str,
        radius: float,
        degrees: float | None = None,
    ) -> None:
        v = self.points[vertex]
        start = rounded(add(v, scale(unit(sub(self.points[first], v)), radius)))
        end = rounded(add(v, scale(unit(sub(self.points[second], v)), radius)))
        a, b = sub(start, v), sub(end, v)
        sweep = 1 if a[0] * b[1] - a[1] * b[0] > 0 else 0
        d = (
            f"M{fmt(start[0])} {fmt(start[1])} A{fmt(radius)} {fmt(radius)} 0 0 {sweep} "
            f"{fmt(end[0])} {fmt(end[1])}"
        )
        drawn = angle_between(v, self.points[first], self.points[second])
        samples = []
        start_angle = math.atan2(a[1], a[0])
        delta = math.radians(drawn) * (1 if sweep else -1)
        for index in range(25):
            t = start_angle + delta * index / 24
            samples.append((v[0] + radius * math.cos(t), v[1] + radius * math.sin(t)))
        self.raw_path(
            d, [samples], stroke=ACCENT, width=THIN + 0.5, attrs={"data-angle-marker": key}
        )
        self.angle_markers.append(
            {
                "marker_key": key,
                "center": list(v),
                "radius": float(fmt(radius)),
                "start_ray_point": list(self.points[first]),
                "end_ray_point": list(self.points[second]),
                "large_arc": 0,
                "sweep": sweep,
            }
        )
        record = {
            "vertex": vertex,
            "arms": [first, second],
            "marker_key": key,
            "drawn_degrees": round(drawn, 2),
        }
        if degrees is not None:
            record["degrees"] = degrees
        self.angles.append(record)

    # ------------------------------------------------------------------- labels
    def _nearest_is(self, box: Box, key: str) -> bool:
        """True when ``box`` is closer to segment ``key`` than to any other segment."""
        p, q = self.segment_ends[key]
        own = segment_box_distance(p, q, box)
        return all(
            segment_box_distance(a, b, box) + 1.0 >= own
            for other, (a, b) in self.segment_ends.items()
            if other != key
        )

    def _fits(self, box: Box, ignore_strokes: int = 0) -> bool:
        bounds = Box(EDGE_MARGIN, EDGE_MARGIN, self.width - EDGE_MARGIN, self.height - EDGE_MARGIN)
        if not box.inside(bounds):
            return False
        if any(box.overlaps(other.expanded(LABEL_GAP)) for other in self.text_boxes):
            return False
        for polyline, half_width in self.strokes:
            clearance = half_width + MIN_LABEL_CLEARANCE
            expanded = box.expanded(clearance)
            if any(
                _segment_hits(start, end, expanded)
                for start, end in zip(polyline, polyline[1:], strict=False)
            ):
                return False
        return True

    def text(
        self,
        text: str,
        candidates: Iterable[Point],
        *,
        target: str | None = None,
        size: float = LABEL_SIZE,
        weight: int = 700,
        fill: str = TEXT,
        attach: str | None = None,
    ) -> Point:
        """Place a centred label at the first candidate centre that keeps clear of everything.

        With ``attach``, the label must also be nearer that segment than any other segment, so
        a reader cannot attach it to the wrong edge.
        """
        for center in candidates:
            baseline = baseline_for_center(center[1], text, size)
            x, y = float(fmt(center[0])), float(fmt(baseline))
            box = text_box(x, y, text, size, "middle")
            if self._fits(box) and (attach is None or self._nearest_is(box, attach)):
                self.text_boxes.append(box)
                self.labels.append(
                    "<text"
                    + _attrs(
                        {
                            "data-label-for": target,
                            "x": fmt(x),
                            "y": fmt(y),
                            "font-size": fmt(size),
                            "font-weight": weight,
                            "text-anchor": "middle",
                            "fill": fill,
                        }
                    )
                    + f">{html.escape(text)}</text>"
                )
                if target is not None:
                    self.placed_labels.append({"text": text, "target": target})
                return (x, y)
        raise DiagramLayoutError(f"No clear position for label {text!r} ({target})")

    def label_size(self, text: str, size: float = LABEL_SIZE) -> tuple[float, float]:
        ascent, descent = text_extents(text, size)
        return text_width(text, size), ascent + descent

    def segment_label(
        self,
        text: str,
        start: str,
        end: str,
        *,
        away_from: Point,
        target: str | None = None,
        size: float = LABEL_SIZE,
        fill: str = TEXT,
        positions: Sequence[float] = (0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74),
        gaps: Sequence[float] = (8, 14, 22, 32),
    ) -> Point:
        """Place a label beside a segment on the side facing away from ``away_from``."""
        p, q = self.points[start], self.points[end]
        direction = unit(sub(q, p))
        normal = (-direction[1], direction[0])
        middle = lerp(p, q, 0.5)
        if (normal[0] * (away_from[0] - middle[0]) + normal[1] * (away_from[1] - middle[1])) > 0:
            normal = (-normal[0], -normal[1])
        width, height = self.label_size(text, size)
        support = (abs(normal[0]) * width + abs(normal[1]) * height) / 2
        candidates = [
            add(lerp(p, q, t), scale(normal, gap + support + STROKE / 2))
            for gap in gaps
            for t in positions
        ]
        attach = self.segment_keys.get((start, end)) or self.segment_keys.get((end, start))
        return self.text(
            text,
            candidates,
            target=target or f"segment:{start}{end}",
            size=size,
            fill=fill,
            attach=attach,
        )

    def angle_label(
        self,
        text: str,
        vertex: str,
        first: str,
        second: str,
        radius: float,
        *,
        target: str | None = None,
        size: float = LABEL_SIZE,
    ) -> Point:
        v = self.points[vertex]
        u = unit(sub(self.points[first], v))
        w = unit(sub(self.points[second], v))
        bisector = unit(add(u, w))
        width, height = self.label_size(text, size)
        candidates = []
        for spread in (0.0, -0.18, 0.18, -0.32, 0.32):
            direction = unit(add(bisector, scale(sub(w, u), spread)))
            support = (abs(direction[0]) * width + abs(direction[1]) * height) / 2
            for gap in (6, 12, 20, 30, 44, 60, 80, 100):
                candidates.append(add(v, scale(direction, radius + gap + support)))
        return self.text(
            text, candidates, target=target or f"angle:{vertex}", size=size, fill=ANGLE_TEXT
        )

    def dimension(
        self,
        text: str,
        start: str,
        end: str,
        *,
        normal: Point,
        offset: float,
        target: str | None = None,
        size: float = LABEL_SIZE,
        extension_from: tuple[str, str] | None = None,
    ) -> Point:
        """Draw a dimension line parallel to ``start``–``end`` and label it on the outside.

        The dimension line is offset by ``offset`` along ``normal`` and joined to the measured
        segment by thin extension lines. It is recorded so validators can confirm that it is
        parallel to, and exactly as long as, the segment it measures.
        """
        n = unit(normal)
        p, q = self.points[start], self.points[end]
        key = f"dim-{start}{end}"
        first = self.point(f"{key}-1", add(p, scale(n, offset)))
        second = self.point(f"{key}-2", add(q, scale(n, offset)))
        origins = (
            (self.points[extension_from[0]], self.points[extension_from[1]])
            if extension_from
            else (p, q)
        )
        for origin, tip in zip(origins, (first, second), strict=True):
            reach = add(tip, scale(n, 7))
            self.raw_path(
                f"M{fmt(origin[0] + n[0] * 6)} {fmt(origin[1] + n[1] * 6)} L{fmt(reach[0])} {fmt(reach[1])}",
                [[add(origin, scale(n, 6)), reach]],
                stroke=LIGHT,
                width=2,
                attrs={"data-role": "extension"},
            )
        self.segment(key, f"{key}-1", f"{key}-2", stroke=TEXT, width=THIN, role="dimension")
        for tip in (first, second):
            left = add(tip, scale(n, -8))
            right = add(tip, scale(n, 8))
            self.raw_path(
                f"M{fmt(left[0])} {fmt(left[1])} L{fmt(right[0])} {fmt(right[1])}",
                [[left, right]],
                stroke=TEXT,
                width=THIN,
                attrs={"data-role": "dimension-tick"},
            )
        self.dimension_lines.append({"segment": key, "measures": f"{start}{end}"})
        away = add(lerp(first, second, 0.5), scale(n, -100))
        return self.segment_label(
            text,
            f"{key}-1",
            f"{key}-2",
            away_from=away,
            target=target or f"segment:{start}{end}",
            size=size,
            gaps=(6, 12, 20),
        )

    def leader_label(
        self,
        text: str,
        start: str,
        end: str,
        *,
        directions: Sequence[Point],
        size: float = LABEL_SIZE,
        anchors: Sequence[float] = (0.5, 0.42, 0.58),
        distances: Sequence[float] = (60, 85, 110, 140, 170, 200),
    ) -> Point:
        """Place a label outside a crowded figure with a thin leader to its segment.

        The leader starts exactly on the segment, so validators can confirm the attachment.
        """
        target = f"segment:{start}{end}"
        p, q = self.points[start], self.points[end]
        width, height = self.label_size(text, size)
        for distance in distances:
            for t in anchors:
                anchor = lerp(p, q, t)
                for direction in directions:
                    d = unit(direction)
                    support = (abs(d[0]) * width + abs(d[1]) * height) / 2
                    centre = add(anchor, scale(d, distance + support))
                    baseline = baseline_for_center(centre[1], text, size)
                    x, y = float(fmt(centre[0])), float(fmt(baseline))
                    box = text_box(x, y, text, size, "middle")
                    if not self._fits(box):
                        continue
                    tip = _box_entry(anchor, box.center, box.expanded(5))
                    if any(
                        _segment_hits(anchor, tip, other.expanded(3)) for other in self.text_boxes
                    ):
                        continue
                    start_point = rounded(anchor)
                    tip = rounded(tip)
                    self.text(text, [box.center], target=target, size=size)
                    self.raw_path(
                        f"M{fmt(start_point[0])} {fmt(start_point[1])} L{fmt(tip[0])} {fmt(tip[1])}",
                        [[start_point, tip]],
                        stroke=TEXT,
                        width=2,
                        attrs={"data-leader-for": target},
                    )
                    self.figure.append(
                        "<circle"
                        + _attrs(
                            {
                                "data-leader-anchor": target,
                                "cx": fmt(start_point[0]),
                                "cy": fmt(start_point[1]),
                                "r": 3.5,
                                "fill": TEXT,
                            }
                        )
                        + "/>"
                    )
                    self.leaders.append(
                        {"target": target, "from": list(start_point), "to": list(tip)}
                    )
                    return box.center
        raise DiagramLayoutError(f"No clear leader position for label {text!r} ({target})")

    def length_label(
        self,
        text: str,
        start: str,
        end: str,
        *,
        away_from: Point,
        directions: Sequence[Point],
        size: float = LABEL_SIZE,
        positions: Sequence[float] = (0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74),
        gaps: Sequence[float] = (8, 14, 22),
        fill: str = TEXT,
    ) -> Point:
        """Label a segment beside itself, or outside the figure with a leader when crowded."""
        try:
            return self.segment_label(
                text,
                start,
                end,
                away_from=away_from,
                size=size,
                positions=positions,
                gaps=gaps,
                fill=fill,
            )
        except DiagramLayoutError:
            return self.leader_label(text, start, end, directions=directions, size=size)

    @property
    def has_note(self) -> bool:
        return any('data-role="note"' in label for label in self.labels)

    def note(self, text: str = "Not drawn to scale") -> None:
        baseline = self.height - 20
        box = text_box(self.width - 22, baseline, text, NOTE_SIZE, "end")
        self.text_boxes.append(box.expanded(6))
        self.labels.append(
            "<text"
            + _attrs(
                {
                    "data-role": "note",
                    "x": fmt(self.width - 22),
                    "y": fmt(baseline),
                    "font-size": NOTE_SIZE,
                    "font-weight": 500,
                    "text-anchor": "end",
                    "fill": MUTED,
                }
            )
            + f">{html.escape(text)}</text>"
        )

    def caption(
        self, text: str, center: Point, *, size: float = CAPTION_SIZE, weight: int = 600
    ) -> None:
        self.text(text, [center], size=size, weight=weight, fill=TEXT)

    # ------------------------------------------------------------------ output
    def min_phone_font_px(self) -> float:
        return phone_font_px(NOTE_SIZE, self.width)

    def svg(self, *, renderer: str, title: str, description: str) -> str:
        width, height = fmt(self.width), fmt(self.height)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc" '
            f'data-renderer="{renderer}">\n'
            f'<title id="title">{html.escape(title)}</title>'
            f'<desc id="desc">{html.escape(description)}</desc>\n'
            f'<rect data-role="background" width="{width}" height="{height}" rx="20" '
            f'fill="{BACKGROUND}"/>\n'
            f'<g data-layer="figure" stroke-linecap="round" stroke-linejoin="round">\n'
            + "\n".join(self.figure)
            + "\n</g>\n"
            + '<g data-layer="labels" font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" stroke="none">\n'
            + "\n".join(self.labels)
            + "\n</g>\n</svg>\n"
        )

    def geometry_spec(self) -> dict[str, Any]:
        spec: dict[str, Any] = {
            "viewbox": [float(fmt(self.width)), float(fmt(self.height))],
            "points": {name: list(point) for name, point in self.points.items()},
            "segments": self.segments,
        }
        if self.circles:
            spec["circles"] = self.circles
        if self.ellipses:
            spec["ellipses"] = self.ellipses
        spec["right_angles"] = self.right_angles
        if self.angles:
            spec["angles"] = self.angles
            spec["angle_markers"] = self.angle_markers
        if self.dimension_lines:
            spec["dimension_lines"] = self.dimension_lines
        if self.leaders:
            spec["leaders"] = self.leaders
        spec["labels"] = self.placed_labels
        return spec


def _segment_hits(start: Point, end: Point, box: Box) -> bool:
    return segment_box_distance(start, end, box) == 0.0


def _box_entry(origin: Point, centre: Point, box: Box) -> Point:
    """Return where the ray from ``origin`` towards ``centre`` first meets ``box``."""
    dx, dy = centre[0] - origin[0], centre[1] - origin[1]
    best = 1.0
    for edge, delta, low, high, other, other_delta in (
        (box.x0, dx, box.y0, box.y1, origin[1], dy),
        (box.x1, dx, box.y0, box.y1, origin[1], dy),
    ):
        if delta:
            t = (edge - origin[0]) / delta
            y = other + other_delta * t
            if 0 <= t < best and low <= y <= high:
                best = t
    for edge in (box.y0, box.y1):
        if dy:
            t = (edge - origin[1]) / dy
            x = origin[0] + dx * t
            if 0 <= t < best and box.x0 <= x <= box.x1:
                best = t
    return (origin[0] + dx * best, origin[1] + dy * best)


def fit_transform(model_points: Sequence[Point], area: Box, *, max_scale: float | None = None):
    """Return a function that maps y-up model coordinates into ``area`` (SVG, y-down)."""
    xs = [point[0] for point in model_points]
    ys = [point[1] for point in model_points]
    model_width = max(xs) - min(xs) or 1.0
    model_height = max(ys) - min(ys) or 1.0
    factor = min(area.width / model_width, area.height / model_height)
    if max_scale is not None:
        factor = min(factor, max_scale)
    offset_x = area.x0 + (area.width - model_width * factor) / 2 - min(xs) * factor
    offset_y = area.y0 + (area.height - model_height * factor) / 2 + max(ys) * factor

    def transform(point: Point) -> Point:
        return (offset_x + point[0] * factor, offset_y - point[1] * factor)

    transform.factor = factor  # type: ignore[attr-defined]
    return transform
