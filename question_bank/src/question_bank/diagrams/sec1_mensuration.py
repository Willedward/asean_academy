"""Deterministic Sec 1 G5 diagrams (renderer ``nextscholar-sec1-mensuration-svg-v1``).

Each template reads the givens of one question and draws that question and nothing else: a
parallelogram or trapezium with its dashed perpendicular height, an L-shape, joined rectangles, a
border, a cuboid, a prism, joined solids, a drilled solid or an open cylinder.

Every coordinate is computed from the givens, at one scale per figure, so equal lengths measure
equal and a cube's front face is square. A length the learner must find is drawn at a neutral size
and carries its variable. A question whose figure would add no spatial information, or could only
contradict its own wording, is refused (``TEXT_ONLY``).
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from ..svg_metrics import text_width
from .canvas import (
    BACKGROUND,
    FILL,
    FILL_ALT,
    INK,
    LABEL_SIZE,
    NOTE_SIZE,
    STROKE,
    THIN,
    WIDTH,
    add,
    fmt,
    scale,
    sub,
    unit,
)
from .common import (
    SEC1_MENSURATION_RENDERER,
    Diagram,
    Quantity,
    UnsupportedDiagram,
    base_spec,
    decimal_forms,
    finish,
    layout,
    number,
    withheld_labels,
)
from .right_triangle import q

Point = tuple[float, float]

NOT_TO_SCALE = "Not drawn to scale."
DEPTH = 0.5
DEPTH_ANGLE = math.radians(35)
ISO_COS = math.cos(math.radians(30))
ISO_SIN = math.sin(math.radians(30))
ISO_RX = ISO_COS * math.sqrt(2)
ISO_RY = ISO_SIN * math.sqrt(2)
RIM_RATIO = 0.3
INTERIOR = "#c5dcd8"
SHARED = "#f4c98f"
SIDE = "#d5e8e4"
TOP = "#f1f8f6"
UNIT_CM = {"mm": 0.1, "cm": 1.0, "m": 100.0, "km": 100000.0}
ROUND_ALL = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def _oblique(x: float, y: float, z: float) -> Point:
    """Front faces keep their true shape; depth recedes up and to the right at half length."""
    return (x + y * DEPTH * math.cos(DEPTH_ANGLE), z + y * DEPTH * math.sin(DEPTH_ANGLE))


def _iso(x: float, y: float, z: float) -> Point:
    """Isometric view, in which a circle on the top face is a horizontal ellipse."""
    return ((x - y) * ISO_COS, (x + y) * ISO_SIN + z)


def _require(condition: bool, message: str) -> None:
    """Refuse to draw givens that describe no figure, rather than draw a false one."""
    if not condition:
        raise UnsupportedDiagram(message)


def _key_findings(expected: float, answers: Sequence[str]) -> list[str]:
    numeric = []
    for answer in answers:
        try:
            numeric.append(float(answer))
        except ValueError:
            continue
    if not numeric or any(math.isclose(value, expected, abs_tol=1e-6) for value in numeric):
        return []
    return [
        f"The canonical answer {answers[0]} does not match the value recomputed from the prompt "
        f"({number(expected)}). Correct the answer key in the question, not the diagram."
    ]


def _neutral(true_value: float, factor: float = 1.3) -> float:
    """Return a drawn size for an unknown that does not encode its true value."""
    drawn = float(round(true_value * factor))
    if math.isclose(drawn, true_value):
        drawn = true_value + 2
    return drawn


def _algebra(coefficient_constant: float, unit_name: str) -> str:
    if coefficient_constant == 0:
        return f"x {unit_name}"
    sign = "−" if coefficient_constant < 0 else "+"
    return f"(x {sign} {number(abs(coefficient_constant))}) {unit_name}"


def _inside(point: Point, polygon: Sequence[Point]) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        if (y1 > point[1]) != (y2 > point[1]):
            if point[0] < (x2 - x1) * (point[1] - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def _runs(start: Point, end: Point, polygon: Sequence[Point]) -> list[tuple[float, float, bool]]:
    """Split a segment into runs, each entirely inside or outside a polygon."""
    cuts = [0.0, 1.0]
    dx, dy = end[0] - start[0], end[1] - start[1]
    for a, b in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        ex, ey = b[0] - a[0], b[1] - a[1]
        denominator = dx * ey - dy * ex
        if abs(denominator) < 1e-9:
            continue
        t = ((a[0] - start[0]) * ey - (a[1] - start[1]) * ex) / denominator
        u = ((a[0] - start[0]) * dy - (a[1] - start[1]) * dx) / denominator
        if 1e-6 < t < 1 - 1e-6 and -1e-9 <= u <= 1 + 1e-9:
            cuts.append(t)
    cuts = sorted(cuts)
    runs = []
    for first, second in zip(cuts, cuts[1:], strict=False):
        middle = (first + second) / 2
        point = (start[0] + dx * middle, start[1] + dy * middle)
        runs.append((first, second, _inside(point, polygon)))
    merged: list[tuple[float, float, bool]] = []
    for run in runs:
        if merged and merged[-1][2] == run[2]:
            merged[-1] = (merged[-1][0], run[1], run[2])
        else:
            merged.append(run)
    return merged


class _Sketch:
    """A canvas plus the figures, lengths and markings that the validator measures."""

    def __init__(
        self,
        points: dict[str, Point],
        *,
        max_width: float = 420,
        max_height: float = 270,
        top: float = 40,
        bottom: float = 88,
        max_scale: float | None = None,
        depth_factor: float = DEPTH,
        side_labels: Sequence[str] = (),
    ):
        if side_labels:
            room = max(text_width(text, LABEL_SIZE) for text in side_labels) + 26
            max_width = min(max_width, WIDTH - 2 * room)
        self.canvas, transform = layout(
            list(points.values()),
            max_width=max_width,
            max_height=max_height,
            top=top,
            bottom=bottom,
            max_scale=max_scale,
        )
        self.scale: float = transform.factor  # type: ignore[attr-defined]
        self.transform = transform
        self.depth_factor = depth_factor
        for name, point in points.items():
            self.canvas.point(name, transform(point))
        self.figures: list[dict[str, Any]] = []
        self.measures: list[dict[str, Any]] = []
        self.relationships: list[dict[str, Any]] = []
        self.equal_marks: list[dict[str, Any]] = []
        self.captions: list[str] = []
        self.shades: list[str] = []
        self.neutral: list[dict[str, Any]] = []
        self._pending: list[str] = []
        self._labels: list[Callable[[], Any]] = []

    # ---------------------------------------------------------------- strokes and figures
    def shade(self, names: Sequence[str], colour: str, role: str) -> None:
        self.canvas.polygon(names, fill=colour, role=role)
        self.shades.append(role)

    def edge(self, start: str, end: str, *, hidden: bool = False, thin: bool = False) -> str:
        key = f"{start}{end}"
        self.canvas.segment(key, start, end, hidden=hidden, width=THIN if thin else STROKE)
        self._pending.append(key)
        return key

    def figure(self, kind: str, **fields: Any) -> None:
        self.figures.append({"type": kind, **fields, "segments": self._pending})
        self._pending = []

    def relate(self, kind: str, **fields: Any) -> None:
        self.relationships.append({"type": kind, **fields})

    def equal(self, *keys: str, ticks: int = 1) -> None:
        """Mark drawn segments as equal with the same number of ticks on each."""
        for key in keys:
            p, r = self.canvas.segment_ends[key]
            direction = unit(sub(r, p))
            normal = (-direction[1], direction[0])
            parts, polylines = [], []
            for index in range(ticks):
                centre = add(
                    add(p, scale(sub(r, p), 0.5)), scale(direction, 8 * (index - (ticks - 1) / 2))
                )
                a, b = add(centre, scale(normal, 10)), add(centre, scale(normal, -10))
                parts.append(f"M{fmt(a[0])} {fmt(a[1])} L{fmt(b[0])} {fmt(b[1])}")
                polylines.append([a, b])
            self.canvas.raw_path(
                " ".join(parts),
                polylines,
                stroke=INK,
                width=THIN,
                attrs={"data-tick-mark": key, "data-ticks": ticks},
            )
        self.equal_marks.append({"segments": list(keys), "ticks": ticks})

    # ------------------------------------------------------------------------------ labels
    def _record(
        self,
        key: str,
        text: str,
        value: float | None,
        factor: float,
        variable: str | None,
        constant: float,
    ) -> None:
        item: dict[str, Any] = {"segment": key, "label": text, "factor": factor}
        if variable is not None:
            item["variable"] = variable
            item["constant"] = constant
        else:
            item["value"] = value
        self.measures.append(item)

    def length(
        self,
        text: str,
        start: str,
        end: str,
        *,
        away_from: str | Point,
        value: float | None = None,
        factor: float = 1.0,
        variable: str | None = None,
        constant: float = 0.0,
        directions: Sequence[Point] = ROUND_ALL,
        positions: Sequence[float] = (0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74),
    ) -> None:
        """Label a drawn length, and record what it measures so the validator can check it."""
        self._record(f"{start}{end}", text, value, factor, variable, constant)
        canvas = self.canvas

        def place() -> None:
            away = canvas.points[away_from] if isinstance(away_from, str) else away_from
            canvas.length_label(
                text, start, end, away_from=away, directions=directions, positions=positions
            )

        self._labels.append(place)

    def leader(
        self,
        text: str,
        start: str,
        end: str,
        *,
        directions: Sequence[Point],
        value: float | None = None,
        factor: float = 1.0,
        anchors: Sequence[float] = (0.5, 0.42, 0.58),
        distances: Sequence[float] = (30, 45, 60, 85, 110, 140, 170, 200),
    ) -> None:
        """Label a short length outside its crowded neighbourhood, joined by a leader line."""
        self._record(f"{start}{end}", text, value, factor, None, 0.0)
        self._labels.append(
            lambda: self.canvas.leader_label(
                text, start, end, directions=directions, anchors=anchors, distances=distances
            )
        )

    def caption(self, text: str, candidates: Iterable[Point]) -> None:
        points = list(candidates)
        self.captions.append(text)
        self._labels.append(lambda: self.canvas.text(text, points, size=NOTE_SIZE + 2, weight=600))

    def legend(self, text: str) -> None:
        """Explain a dashed or shaded mark at the bottom left, beside the scale note."""
        height = self.canvas.height
        size = NOTE_SIZE
        self.captions.append(text)

        def place() -> None:
            width, _ = self.canvas.label_size(text, size)
            self.canvas.text(text, [(22 + width / 2, height - 28)], size=size, weight=600)

        self._labels.append(place)

    # ------------------------------------------------------------------------------ output
    def diagram(
        self,
        *,
        template: str,
        inputs: dict[str, Any],
        kind: str,
        dimensions: dict[str, Any],
        title: str,
        alt_text: str,
        answers: Sequence[str],
        derived: Sequence[float] = (),
        unknowns: Sequence[tuple[str, str]] = (),
        findings: Sequence[str] = (),
    ) -> Diagram:
        canvas = self.canvas
        for place in self._labels:
            place()
        candidates: list[str] = [*answers]
        for value in derived:
            candidates.extend(decimal_forms(value))
        forbidden, exemptions = withheld_labels(
            candidates, [label["text"] for label in canvas.placed_labels]
        )
        details: dict[str, Any] = {
            "drawn_scale": round(self.scale, 4),
            "depth_factor": self.depth_factor,
            "figures": self.figures,
            "measures": self.measures,
            "captions": self.captions,
            "shades": self.shades,
        }
        if self.neutral:
            details["neutral_lengths"] = self.neutral
        if self.equal_marks:
            details["equal_marks"] = self.equal_marks
        spec = base_spec(
            renderer=SEC1_MENSURATION_RENDERER,
            diagram_kind=kind,
            template=template,
            inputs=inputs,
            dimensions=dimensions,
            canvas=canvas,
            forbidden=forbidden,
            exemptions=exemptions,
            unknowns=[{"target": target, "label": label} for target, label in unknowns],
            relationships=self.relationships,
            extra=details,
        )
        return finish(
            canvas,
            renderer=SEC1_MENSURATION_RENDERER,
            title=title,
            alt_text=f"{alt_text} {NOT_TO_SCALE}",
            spec=spec,
            content_findings=list(findings),
        )


def _given(inputs: dict[str, Any], *names: str) -> list[Quantity]:
    return [q(inputs[name]) for name in names]


def _same_unit(*quantities: Quantity) -> None:
    _require(
        len({item.unit for item in quantities}) == 1,
        "This figure draws all its lengths in one stated unit.",
    )


# ----------------------------------------------------------------------- plane figures
def _parallelogram_points(prefix: str, x0: float, base: float, height: float) -> dict[str, Point]:
    slant = min(height * 0.45, base * 0.3)
    return {
        f"{prefix}A": (x0, 0.0),
        f"{prefix}B": (x0 + base, 0.0),
        f"{prefix}C": (x0 + base + slant, height),
        f"{prefix}D": (x0 + slant, height),
        f"{prefix}F": (x0 + slant, 0.0),
    }


def _trapezium_points(
    prefix: str, x0: float, bottom: float, top: float, height: float
) -> dict[str, Point]:
    inset = (bottom - top) / 2
    return {
        f"{prefix}A": (x0, 0.0),
        f"{prefix}B": (x0 + bottom, 0.0),
        f"{prefix}C": (x0 + bottom - inset, height),
        f"{prefix}D": (x0 + inset, height),
        f"{prefix}F": (x0 + inset, 0.0),
    }


def _draw_height(sketch: _Sketch, prefix: str) -> None:
    a, b, d, f = (f"{prefix}{name}" for name in "ABDF")
    sketch.edge(d, f, hidden=True, thin=True)
    sketch.canvas.right_angle(f, b, d, size=18)
    sketch.relate("collinear", points=[a, f, b])


def _draw_parallelogram(
    sketch: _Sketch,
    prefix: str,
    base_label: str,
    height_label: str,
    height: float,
    *,
    base: float,
    variable: str | None = None,
    constant: float = 0.0,
    colour: str = FILL,
) -> None:
    a, b, c, d, f = (f"{prefix}{name}" for name in "ABCDF")
    sketch.shade([a, b, c, d], colour, f"{prefix}parallelogram")
    for start, end in ((a, b), (b, c), (c, d), (d, a)):
        sketch.edge(start, end)
    _draw_height(sketch, prefix)
    sketch.figure(
        "parallelogram",
        points=[a, b, c, d],
        heights=[{"segment": f"{d}{f}", "foot": f, "top": d, "base": [a, b]}],
    )
    sketch.length(
        base_label,
        a,
        b,
        away_from=d,
        value=None if variable else base,
        variable=variable,
        constant=constant,
    )
    sketch.length(height_label, d, f, away_from=a, value=height, positions=(0.5, 0.42, 0.58))


def _draw_trapezium(
    sketch: _Sketch,
    prefix: str,
    labels: tuple[str, str, str],
    values: tuple[float, float, float],
    *,
    variable: str | None = None,
    constants: tuple[float, float] = (0.0, 0.0),
    colour: str = FILL_ALT,
) -> None:
    a, b, c, d, f = (f"{prefix}{name}" for name in "ABCDF")
    sketch.shade([a, b, c, d], colour, f"{prefix}trapezium")
    for start, end in ((a, b), (b, c), (c, d), (d, a)):
        sketch.edge(start, end)
    _draw_height(sketch, prefix)
    sketch.figure(
        "trapezium",
        points=[a, b, c, d],
        heights=[{"segment": f"{d}{f}", "foot": f, "top": d, "base": [a, b]}],
    )
    bottom_label, top_label, height_label = labels
    bottom, top, height = values
    sketch.length(
        bottom_label,
        a,
        b,
        away_from=d,
        value=None if variable else bottom,
        variable=variable,
        constant=constants[0],
    )
    sketch.length(
        top_label,
        c,
        d,
        away_from=a,
        value=None if variable else top,
        variable=variable,
        constant=constants[1],
    )
    sketch.length(height_label, d, f, away_from=a, value=height, positions=(0.5, 0.42, 0.58))


def parallelogram_area(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    base, height = _given(inputs, "base", "height")
    _same_unit(base, height)
    area = base.value * height.value
    sketch = _Sketch(_parallelogram_points("", 0.0, base.value, height.value))
    _draw_parallelogram(sketch, "", base.text, height.text, height.value, base=base.value)
    return sketch.diagram(
        template="parallelogram_area",
        inputs=inputs,
        kind="parallelogram",
        dimensions={"base": inputs["base"], "height": inputs["height"]},
        title="Parallelogram with its perpendicular height",
        alt_text=(
            f"A parallelogram with base {base.text} and a dashed perpendicular height of "
            f"{height.text}, with a right angle marked where the height meets the base."
        ),
        answers=answers,
        derived=[area],
        findings=_key_findings(area, answers),
    )


def parallelogram_and_trapezium(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    base, height, top, bottom, depth = _given(
        inputs, "base", "height", "parallel_short", "parallel_long", "trapezium_height"
    )
    _same_unit(base, height, top, bottom, depth)
    _require(top.value < bottom.value, "A trapezium needs unequal parallel sides.")
    parallelogram_area_value = base.value * height.value
    trapezium_area_value = (top.value + bottom.value) / 2 * depth.value
    total = parallelogram_area_value + trapezium_area_value
    left = _parallelogram_points("P", 0.0, base.value, height.value)
    gap = max(left["PC"][0] * 0.14, 1.5)
    points = {
        **left,
        **_trapezium_points("T", left["PC"][0] + gap, bottom.value, top.value, depth.value),
    }
    sketch = _Sketch(points, max_width=530, max_height=250, top=56)
    _draw_parallelogram(sketch, "P", base.text, height.text, height.value, base=base.value)
    _draw_trapezium(
        sketch, "T", (bottom.text, top.text, depth.text), (bottom.value, top.value, depth.value)
    )
    return sketch.diagram(
        template="parallelogram_and_trapezium",
        inputs=inputs,
        kind="two_quadrilaterals",
        dimensions={key: inputs[key] for key in inputs},
        title="A parallelogram beside a trapezium",
        alt_text=(
            f"A parallelogram with base {base.text} and dashed perpendicular height {height.text}, "
            f"beside a trapezium with parallel sides {top.text} and {bottom.text} and dashed "
            f"perpendicular height {depth.text}. A right angle is marked at the foot of each height."
        ),
        answers=answers,
        derived=[parallelogram_area_value, trapezium_area_value, total],
        findings=_key_findings(total, answers),
    )


def trapezium_and_parallelogram_algebra(
    inputs: dict[str, Any], answers: Sequence[str] = ()
) -> Diagram:
    extra_long, extra_base = inputs["long_extra"], inputs["base_extra"]
    depth, height, total = _given(inputs, "trapezium_height", "height", "total_area")
    # (x + x + extra_long) / 2 × depth + (x + extra_base) × height = total
    slope = depth.value + height.value
    constant = extra_long * depth.value / 2 + extra_base * height.value
    x = (total.value - constant) / slope
    _require(x > 0, "The stated total area gives no positive length x.")
    drawn = _neutral(x, 0.75)
    unit_name = depth.unit or ""
    left = _trapezium_points("T", 0.0, drawn + extra_long, drawn, depth.value)
    gap = max(left["TB"][0] * 0.14, 1.5)
    points = {
        **left,
        **_parallelogram_points("P", left["TB"][0] + gap, drawn + extra_base, height.value),
    }
    sketch = _Sketch(points, max_width=530, max_height=250, top=56)
    sketch.neutral.append({"variable": "x", "drawn": drawn, "avoid": x})
    _draw_trapezium(
        sketch,
        "T",
        (_algebra(extra_long, unit_name), _algebra(0, unit_name), depth.text),
        (drawn + extra_long, drawn, depth.value),
        variable="x",
        constants=(float(extra_long), 0.0),
    )
    _draw_parallelogram(
        sketch,
        "P",
        _algebra(extra_base, unit_name),
        height.text,
        height.value,
        base=drawn + extra_base,
        variable="x",
        constant=float(extra_base),
        colour=FILL,
    )
    top_label, bottom_label = _algebra(0, unit_name), _algebra(extra_long, unit_name)
    base_label = _algebra(extra_base, unit_name)
    return sketch.diagram(
        template="trapezium_and_parallelogram_algebra",
        inputs=inputs,
        kind="two_quadrilaterals",
        dimensions={"expressions": [top_label, bottom_label, base_label]},
        title="A trapezium and a parallelogram with algebraic lengths",
        alt_text=(
            f"A trapezium with parallel sides {top_label} and {bottom_label} and dashed "
            f"perpendicular height {depth.text}, beside a parallelogram with base {base_label} and "
            f"dashed perpendicular height {height.text}. A right angle is marked at the foot of "
            "each height."
        ),
        answers=answers,
        derived=[x, x + extra_long, x + extra_base],
        findings=_key_findings(x, answers),
    )


def rectangle_and_square(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    width, height, side = _given(inputs, "width", "height", "side")
    _same_unit(width, height, side)
    _require(side.value <= height.value, "The square must fit along the rectangle's side.")
    w, h, s = width.value, height.value, side.value
    total = w * h + s * s
    points = {
        "A": (0.0, 0.0),
        "B": (w, 0.0),
        "J": (w, s),
        "C": (w, h),
        "D": (0.0, h),
        "S": (w + s, 0.0),
        "T": (w + s, s),
    }
    sketch = _Sketch(points, side_labels=(height.text, side.text))
    sketch.shade(["A", "B", "C", "D"], FILL, "rectangle")
    sketch.shade(["B", "S", "T", "J"], FILL_ALT, "square")
    for start, end in (("A", "B"), ("J", "C"), ("C", "D"), ("D", "A")):
        sketch.edge(start, end)
    sketch.figure("rectangle", points=["A", "B", "C", "D"])
    for start, end in (("B", "S"), ("S", "T"), ("T", "J"), ("B", "J")):
        sketch.edge(start, end)
    sketch.figure("square", points=["B", "S", "T", "J"], non_overlapping=["A", "B", "C", "D"])
    sketch.equal("BS", "ST", "TJ", "BJ")
    sketch.length(width.text, "A", "B", away_from="D", value=w)
    sketch.length(height.text, "D", "A", away_from="B", value=h)
    sketch.length(side.text, "S", "T", away_from="A", value=s)
    return sketch.diagram(
        template="rectangle_and_square",
        inputs=inputs,
        kind="composite_plane",
        dimensions={key: inputs[key] for key in inputs},
        title="A rectangle and a square side by side",
        alt_text=(
            f"A rectangle {width.text} by {height.text} with a square of side {side.text} attached "
            "along one edge. The two shapes do not overlap, and the four sides of the square carry "
            "equal marks."
        ),
        answers=answers,
        derived=[w * h, s * s, total],
        findings=_key_findings(total, answers),
    )


def _draw_l_shape(
    sketch: _Sketch,
    labels: tuple[str, str, str, str],
    values: tuple[float | None, float | None, float, float],
    *,
    variable: str | None = None,
    constants: tuple[float, float] = (0.0, 0.0),
    cut_label_inside: bool = False,
) -> None:
    names = ["A", "B", "C", "D", "E", "F"]
    sketch.shade(names, FILL, "l-shape")
    for start, end in zip(names, [*names[1:], names[0]], strict=True):
        sketch.edge(start, end)
    sketch.figure("l_shape", points=names)
    width_label, height_label, cut_width_label, cut_height_label = labels
    width_value, height_value, cut_width, cut_height = values
    sketch.length(
        width_label,
        "A",
        "B",
        away_from="E",
        value=width_value,
        variable=variable if width_value is None else None,
        constant=constants[0],
    )
    sketch.length(
        height_label,
        "F",
        "A",
        away_from="B",
        value=height_value,
        variable=variable if height_value is None else None,
        constant=constants[1],
    )
    sketch.length(
        cut_width_label,
        "C",
        "D",
        away_from="E" if cut_label_inside else "B",
        value=cut_width,
        positions=(0.5, 0.42, 0.58) if cut_label_inside else (0.38, 0.3, 0.46, 0.22),
    )
    sketch.length(cut_height_label, "D", "E", away_from="A", value=cut_height)


def _l_points(w: float, h: float, a: float, b: float) -> dict[str, Point]:
    return {
        "A": (0.0, 0.0),
        "B": (w, 0.0),
        "C": (w, h - b),
        "D": (w - a, h - b),
        "E": (w - a, h),
        "F": (0.0, h),
    }


def corner_removed(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    width, height, cut_width, cut_height = _given(
        inputs, "width", "height", "cut_width", "cut_height"
    )
    _same_unit(width, height, cut_width, cut_height)
    w, h, a, b = width.value, height.value, cut_width.value, cut_height.value
    _require(0 < a < w and 0 < b < h, "The removed corner must be smaller than the rectangle.")
    area = w * h - a * b
    perimeter = 2 * (w + h)
    derived = [area, w * h, a * b, w - a, h - b, perimeter]
    expected = None
    if inputs.get("tile_area") is not None:
        expected = area / float(inputs["tile_area"])
        derived.append(expected)
    elif inputs.get("asks") == "perimeter":
        expected = perimeter
    sketch = _Sketch(_l_points(w, h, a, b), side_labels=(height.text,))
    _draw_l_shape(
        sketch,
        (width.text, height.text, cut_width.text, cut_height.text),
        (w, h, a, b),
    )
    return sketch.diagram(
        template="corner_removed",
        inputs=inputs,
        kind="rectilinear",
        dimensions={key: inputs[key] for key in inputs if key not in {"asks", "tile_area"}},
        title="An L-shape left after a corner is removed",
        alt_text=(
            f"An L-shape. The full bottom edge is {width.text} and the full left edge is "
            f"{height.text}. The removed top-right corner has edges {cut_width.text} and "
            f"{cut_height.text}."
        ),
        answers=answers,
        derived=derived,
        findings=_key_findings(expected, answers) if expected is not None else (),
    )


def corner_removed_algebra(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """An L-shape whose sides are written in x, with a known corner removed.

    Either both sides are algebraic, ``(x + p)`` by ``(x + q)`` (a quadratic), or the width is a
    stated length and only the height is ``(x + q)``, which keeps the equation linear.
    """
    cut_width, cut_height, remaining = _given(inputs, "cut_width", "cut_height", "remaining_area")
    a, b = cut_width.value, cut_height.value
    unit_name = cut_width.unit or ""
    r = inputs["height_extra"]
    if "width" in inputs:
        (width,) = _given(inputs, "width")
        _same_unit(width, cut_width, cut_height)
        w = width.value
        # w(x + q) − ab = remaining
        x = (remaining.value + a * b) / w - r
        _require(x > 0, "The stated area gives no positive length x.")
        _require(a < w, "The removed corner must be narrower than the rectangle.")
        drawn = _neutral(x, 1.3)
        width_label, height_label = width.text, _algebra(r, unit_name)
        points = _l_points(w, drawn + r, a, b)
        values: tuple[float | None, float | None, float, float] = (w, None, a, b)
        constants = (0.0, float(r))
        expressions = [height_label]
        derived = [x, x + r, w * (x + r)]
    else:
        p = inputs["width_extra"]
        # (x + p)(x + q) − ab = remaining
        disc = (p + r) ** 2 - 4 * (p * r - a * b - remaining.value)
        _require(disc >= 0, "The stated area gives no real length x.")
        x = (-(p + r) + math.sqrt(disc)) / 2
        _require(x > 0, "The stated area gives no positive length x.")
        drawn = _neutral(x, 1.3)
        width_label, height_label = _algebra(p, unit_name), _algebra(r, unit_name)
        points = _l_points(drawn + p, drawn + r, a, b)
        values = (None, None, a, b)
        constants = (float(p), float(r))
        expressions = [width_label, height_label]
        derived = [x, x + p, x + r, (x + p) * (x + r)]
    sketch = _Sketch(points, side_labels=(height_label,))
    sketch.neutral.append({"variable": "x", "drawn": drawn, "avoid": x})
    _draw_l_shape(
        sketch,
        (width_label, height_label, cut_width.text, cut_height.text),
        values,
        variable="x",
        constants=constants,
        cut_label_inside=True,
    )
    return sketch.diagram(
        template="corner_removed_algebra",
        inputs=inputs,
        kind="rectilinear",
        dimensions={"expressions": expressions},
        title="An L-shape with algebraic side lengths",
        alt_text=(
            f"An L-shape. The full bottom edge is {width_label} and the full left edge is "
            f"{height_label}. The removed top-right corner has edges {cut_width.text} and "
            f"{cut_height.text}."
        ),
        answers=answers,
        derived=derived,
        findings=_key_findings(x, answers),
    )


def _joined_points(w: float, h: float, e: float, s: float) -> dict[str, Point]:
    return {
        "A": (0.0, 0.0),
        "B": (w, 0.0),
        "J": (w, s),
        "C": (w, h),
        "D": (0.0, h),
        "S": (w + e, 0.0),
        "T": (w + e, s),
    }


def _draw_joined(sketch: _Sketch) -> None:
    sketch.shade(["A", "B", "C", "D"], FILL, "first-rectangle")
    sketch.shade(["B", "S", "T", "J"], FILL_ALT, "second-rectangle")
    sketch.edge("B", "J", hidden=True)
    for start, end in (
        ("A", "B"),
        ("J", "C"),
        ("C", "D"),
        ("D", "A"),
        ("B", "S"),
        ("S", "T"),
        ("T", "J"),
    ):
        sketch.edge(start, end)
    sketch.figure(
        "joined_rectangles",
        first=["A", "B", "C", "D"],
        second=["B", "S", "T", "J"],
        shared="BJ",
    )
    sketch.relate("collinear", points=["A", "B", "S"])
    sketch.relate("collinear", points=["B", "J", "C"])
    sketch.legend("Dashed: shared edge")


def joined_rectangles(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    width, height, extension, shared = _given(inputs, "width", "height", "extension", "shared")
    _same_unit(width, height, extension, shared)
    w, h, e, s = width.value, height.value, extension.value, shared.value
    _require(s <= max(w, h), "The shared edge must fit along a side of the larger rectangle.")
    if s > h:
        w, h = h, w
        width, height = height, width
    perimeter = 2 * (w + h) + 2 * (e + s) - 2 * s
    sketch = _Sketch(_joined_points(w, h, e, s), bottom=92, side_labels=(height.text, shared.text))
    _draw_joined(sketch)
    sketch.length(width.text, "A", "B", away_from="D", value=w)
    sketch.length(height.text, "D", "A", away_from="B", value=h)
    sketch.length(extension.text, "B", "S", away_from="T", value=e)
    sketch.length(shared.text, "S", "T", away_from="A", value=s)
    return sketch.diagram(
        template="joined_rectangles",
        inputs=inputs,
        kind="composite_plane",
        dimensions={key: inputs[key] for key in inputs},
        title="Two rectangles joined along an edge",
        alt_text=(
            f"A rectangle {width.text} by {height.text} joined to a smaller rectangle "
            f"{extension.text} by {shared.text}. The whole {shared.text} edge of the smaller "
            "rectangle lies along a side of the larger one, and that shared edge is dashed."
        ),
        answers=answers,
        derived=[perimeter, 2 * (w + h), 2 * (e + s)],
        findings=_key_findings(perimeter, answers),
    )


def joined_rectangles_algebra(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side, shared, total = _given(inputs, "side", "shared", "total_area")
    less = inputs["less"]
    _same_unit(side, shared)
    h, s = side.value, shared.value
    _require(s <= h, "The shared edge must fit along the rectangle's side.")
    # x·h + (x − less)·s = total
    x = (total.value + less * s) / (h + s)
    _require(x > less, "The stated area gives no positive length.")
    perimeter = 2 * (x + h) + 2 * (x - less + s) - 2 * s
    drawn = _neutral(x, 1.3)
    unit_name = side.unit or ""
    x_label, second_label = _algebra(0, unit_name), _algebra(-less, unit_name)
    sketch = _Sketch(
        _joined_points(drawn, h, drawn - less, s), bottom=92, side_labels=(side.text, shared.text)
    )
    sketch.neutral.append({"variable": "x", "drawn": drawn, "avoid": x})
    _draw_joined(sketch)
    sketch.length(x_label, "A", "B", away_from="D", variable="x", constant=0.0)
    sketch.length(side.text, "D", "A", away_from="B", value=h)
    sketch.length(second_label, "B", "S", away_from="T", variable="x", constant=float(-less))
    sketch.length(shared.text, "S", "T", away_from="A", value=s)
    return sketch.diagram(
        template="joined_rectangles_algebra",
        inputs=inputs,
        kind="composite_plane",
        dimensions={"expressions": [x_label, second_label], "side": inputs["side"]},
        title="Two rectangles with algebraic lengths joined along an edge",
        alt_text=(
            f"A rectangle {x_label} by {side.text} joined to a rectangle {second_label} by "
            f"{shared.text}. The whole {shared.text} edge of the second rectangle lies along a "
            "side of the first, and that shared edge is dashed."
        ),
        answers=answers,
        derived=[x, x - less, perimeter, x * h, (x - less) * s],
        findings=_key_findings(perimeter, answers),
    )


def _ring_points(w: float, h: float, inner_w: float, inner_h: float) -> dict[str, Point]:
    x0, y0 = (w - inner_w) / 2, (h - inner_h) / 2
    return {
        "A": (0.0, 0.0),
        "B": (w, 0.0),
        "C": (w, h),
        "D": (0.0, h),
        "E": (x0, y0),
        "F": (x0 + inner_w, y0),
        "G": (x0 + inner_w, y0 + inner_h),
        "H": (x0, y0 + inner_h),
    }


def _draw_ring(sketch: _Sketch) -> None:
    sketch.shade(["A", "B", "C", "D"], FILL_ALT, "outer-rectangle")
    sketch.shade(["E", "F", "G", "H"], BACKGROUND, "inner-rectangle")
    names_outer, names_inner = ["A", "B", "C", "D"], ["E", "F", "G", "H"]
    for names in (names_outer, names_inner):
        for start, end in zip(names, [*names[1:], names[0]], strict=True):
            sketch.edge(start, end)


def uniform_border(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    width, height, border = _given(inputs, "width", "height", "border")
    _same_unit(width, height, border)
    w, h, b = width.value, height.value, border.value
    _require(2 * b < min(w, h), "The border is too wide for the frame.")
    inner_w, inner_h = w - 2 * b, h - 2 * b
    area = w * h - inner_w * inner_h
    points = {
        **_ring_points(w, h, inner_w, inner_h),
        "W1": (w / 2, h),
        "W2": (w / 2, h - b),
        "W3": (w / 2, 0.0),
        "W4": (w / 2, b),
        "W5": (0.0, h / 2),
        "W6": (b, h / 2),
        "W7": (w, h / 2),
        "W8": (w - b, h / 2),
    }
    sketch = _Sketch(points, max_height=280, side_labels=(height.text,))
    _draw_ring(sketch)
    for start, end in (("W1", "W2"), ("W3", "W4"), ("W5", "W6"), ("W7", "W8")):
        sketch.edge(start, end, thin=True)
    sketch.figure(
        "ring",
        outer=["A", "B", "C", "D"],
        inner=["E", "F", "G", "H"],
        uniform=True,
        widths=["W1W2", "W3W4", "W5W6", "W7W8"],
    )
    sketch.equal("W1W2", "W3W4", "W5W6", "W7W8")
    sketch.length(width.text, "A", "B", away_from="D", value=w)
    sketch.length(height.text, "D", "A", away_from="B", value=h)
    sketch.leader(border.text, "W1", "W2", directions=[(0.0, 1.0)], value=b, anchors=(1.0,))
    return sketch.diagram(
        template="uniform_border",
        inputs=inputs,
        kind="ring",
        dimensions={key: inputs[key] for key in inputs},
        title="A frame with a border of uniform width",
        alt_text=(
            f"A rectangular frame {width.text} by {height.text} outside, with a smaller rectangle "
            f"inside it. The shaded border between them is {border.text} wide, and equal marks "
            "show it has the same width on all four sides."
        ),
        answers=answers,
        derived=[inner_w, inner_h, w * h, inner_w * inner_h, area],
        findings=_key_findings(area, answers),
    )


def track_algebra(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    outer_w, outer_h, inner_h = (
        inputs["outer_width"],
        inputs["outer_height"],
        inputs["inner_height"],
    )
    area = q(inputs["area"])
    unit_name = inputs["unit"]
    # (x + p)(x + r) − x(x − s) = area
    slope = outer_w + outer_h + inner_h
    constant = outer_w * outer_h
    _require(slope > 0, "The expressions do not determine x.")
    x = (area.value - constant) / slope
    _require(x > inner_h, "The stated area gives no positive inside length.")
    drawn = _neutral(x, 1.3)
    points = _ring_points(drawn + outer_w, drawn + outer_h, drawn, drawn - inner_h)
    outer_h_label = _algebra(outer_h, unit_name)
    sketch = _Sketch(points, max_height=290, side_labels=(outer_h_label,))
    sketch.neutral.append({"variable": "x", "drawn": drawn, "avoid": x})
    _draw_ring(sketch)
    uniform = math.isclose(outer_w, outer_h + inner_h)
    sketch.figure(
        "ring", outer=["A", "B", "C", "D"], inner=["E", "F", "G", "H"], uniform=uniform, widths=[]
    )
    outer_w_label = _algebra(outer_w, unit_name)
    inner_w_label = _algebra(0, unit_name)
    inner_h_label = _algebra(-inner_h, unit_name)
    sketch.length(outer_w_label, "A", "B", away_from="D", variable="x", constant=float(outer_w))
    sketch.length(outer_h_label, "D", "A", away_from="B", variable="x", constant=float(outer_h))
    sketch.length(inner_w_label, "E", "F", away_from="A", variable="x", constant=0.0)
    sketch.length(inner_h_label, "H", "E", away_from="A", variable="x", constant=float(-inner_h))
    return sketch.diagram(
        template="track_algebra",
        inputs=inputs,
        kind="ring",
        dimensions={
            "expressions": [outer_w_label, outer_h_label, inner_w_label, inner_h_label],
        },
        title="A rectangular track with algebraic dimensions",
        alt_text=(
            f"A rectangular track shown as a shaded band between two rectangles. The outside "
            f"rectangle is {outer_w_label} by {outer_h_label} and the inside rectangle is "
            f"{inner_w_label} by {inner_h_label}."
        ),
        answers=answers,
        derived=[x, x + outer_w, x + outer_h, x - inner_h],
        findings=_key_findings(x, answers),
    )


# ------------------------------------------------------------------------------- solids
def _box_points(
    prefix: str,
    length: float,
    depth: float,
    height: float,
    project: Callable[[float, float, float], Point] = _oblique,
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    *,
    with_hidden_vertex: bool = True,
) -> dict[str, Point]:
    x, y, z = origin
    points = {
        f"{prefix}F1": project(x, y, z),
        f"{prefix}F2": project(x + length, y, z),
        f"{prefix}F3": project(x + length, y, z + height),
        f"{prefix}F4": project(x, y, z + height),
        f"{prefix}B2": project(x + length, y + depth, z),
        f"{prefix}B3": project(x + length, y + depth, z + height),
        f"{prefix}B4": project(x, y + depth, z + height),
    }
    if with_hidden_vertex:
        points[f"{prefix}B1"] = project(x, y + depth, z)
    return points


def _box_names(prefix: str) -> dict[str, str]:
    return {name: f"{prefix}{name}" for name in ("F1", "F2", "F3", "F4", "B1", "B2", "B3", "B4")}


def _shade_box(
    sketch: _Sketch, prefix: str, *, top: str = TOP, front: str = FILL, side: str = SIDE
) -> None:
    n = _box_names(prefix)
    sketch.shade([n["F2"], n["B2"], n["B3"], n["F3"]], side, f"{prefix}right-face")
    sketch.shade([n["F4"], n["F3"], n["B3"], n["B4"]], top, f"{prefix}top-face")
    sketch.shade([n["F1"], n["F2"], n["F3"], n["F4"]], front, f"{prefix}front-face")


def _hidden_box_edges(sketch: _Sketch, prefix: str) -> None:
    n = _box_names(prefix)
    for start, end in ((n["B1"], n["B2"]), (n["B1"], n["B4"]), (n["F1"], n["B1"])):
        sketch.edge(start, end, hidden=True, thin=True)


def _visible_box_edges(sketch: _Sketch, prefix: str, *, skip: Sequence[str] = ()) -> None:
    n = _box_names(prefix)
    for start, end in (
        ("F1", "F2"),
        ("F2", "F3"),
        ("F3", "F4"),
        ("F4", "F1"),
        ("F2", "B2"),
        ("B2", "B3"),
        ("F3", "B3"),
        ("B3", "B4"),
        ("F4", "B4"),
    ):
        if f"{start}{end}" not in skip:
            sketch.edge(n[start], n[end])


def _box_figure(sketch: _Sketch, prefix: str, *, hidden: bool = True, **fields: Any) -> None:
    n = _box_names(prefix)
    vertices = {key: value for key, value in n.items() if hidden or key != "B1"}
    sketch.figure("cuboid", vertices=vertices, hidden_vertex=n["B1"] if hidden else None, **fields)


def cuboid_volume(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, depth, height = _given(inputs, "length", "depth", "height")
    _same_unit(length, depth, height)
    volume = length.value * depth.value * height.value
    sketch = _Sketch(
        _box_points("", length.value, depth.value, height.value), side_labels=(height.text,)
    )
    _shade_box(sketch, "")
    _hidden_box_edges(sketch, "")
    _visible_box_edges(sketch, "")
    _box_figure(sketch, "")
    sketch.length(length.text, "F1", "F2", away_from="F4", value=length.value)
    sketch.length(height.text, "F4", "F1", away_from="F2", value=height.value)
    sketch.length(depth.text, "F2", "B2", away_from="F1", value=depth.value, factor=DEPTH)
    return sketch.diagram(
        template="cuboid_volume",
        inputs=inputs,
        kind="cuboid",
        dimensions={key: inputs[key] for key in inputs},
        title="A cuboid",
        alt_text=(
            f"A cuboid with edges {length.text}, {depth.text} and {height.text}. Hidden edges are "
            "dashed."
        ),
        answers=answers,
        derived=[volume],
        findings=_key_findings(volume, answers),
    )


def open_box(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, depth, height = _given(inputs, "length", "depth", "height")
    _same_unit(length, depth, height)
    ln, d, h = length.value, depth.value, height.value
    area = ln * d + 2 * ln * h + 2 * d * h
    sketch = _Sketch(_box_points("", ln, d, h), top=64, side_labels=(height.text,))
    _shade_box(sketch, "", top=INTERIOR)
    _hidden_box_edges(sketch, "")
    _visible_box_edges(sketch, "")
    _box_figure(sketch, "", open_top=True)
    sketch.length(length.text, "F1", "F2", away_from="F4", value=ln)
    sketch.length(height.text, "F4", "F1", away_from="F2", value=h)
    sketch.length(depth.text, "F2", "B2", away_from="F1", value=d, factor=DEPTH)
    back_left, back_right = sketch.canvas.points["B4"], sketch.canvas.points["B3"]
    centre = (back_left[0] + back_right[0]) / 2
    sketch.caption("Open top", [(centre, back_left[1] - gap) for gap in (24, 32, 40)])
    return sketch.diagram(
        template="open_box",
        inputs=inputs,
        kind="cuboid",
        dimensions={key: inputs[key] for key in inputs},
        title="An open-top cuboid",
        alt_text=(
            f"A cuboid with an open top, {length.text} long, {depth.text} wide and {height.text} "
            "high. The top is shaded darker to show that it is open, and hidden edges are dashed."
        ),
        answers=answers,
        derived=[area, ln * d, ln * h, d * h, 2 * ln * h, 2 * d * h],
        findings=_key_findings(area, answers),
    )


def box_with_cube(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, depth, height, cube = _given(inputs, "length", "depth", "height", "cube")
    ln, d, h, c = (
        item.value * UNIT_CM[item.unit or "cm"] for item in (length, depth, height, cube)
    )
    _require(c < min(ln, d, h), "The cube must fit inside the box.")
    percent = float(inputs["percent"])
    volume = ln * d * h
    used = volume * percent / 100
    count = used / c**3
    points = {
        **_box_points("", ln, d, h),
        **_box_points("c", c, c, c, with_hidden_vertex=False),
    }
    sketch = _Sketch(points, top=30, side_labels=(height.text,))
    _shade_box(sketch, "")
    _hidden_box_edges(sketch, "")
    _visible_box_edges(sketch, "")
    _box_figure(sketch, "")
    _shade_box(sketch, "c", front=FILL_ALT, side=SHARED, top=FILL_ALT)
    n = _box_names("c")
    for start, end in (
        ("F2", "F3"),
        ("F3", "F4"),
        ("F2", "B2"),
        ("B2", "B3"),
        ("F3", "B3"),
        ("B3", "B4"),
        ("F4", "B4"),
    ):
        sketch.edge(n[start], n[end], thin=True)
    sketch.figure(
        "cuboid",
        vertices={key: value for key, value in n.items() if key != "B1"},
        hidden_vertex=None,
        cube=True,
    )
    sketch.length(length.text, "F1", "F2", away_from="F4", value=ln)
    sketch.length(height.text, "F4", "F1", away_from="F2", value=h)
    sketch.length(depth.text, "F2", "B2", away_from="F1", value=d, factor=DEPTH)
    sketch.leader(
        cube.text,
        n["F2"],
        n["F3"],
        directions=[(1.0, -0.15), (1.0, -0.4), (1.0, 0.0)],
        value=c,
        distances=(35, 50, 70, 95, 120),
    )
    return sketch.diagram(
        template="box_with_cube",
        inputs=inputs,
        kind="cuboid",
        dimensions={key: inputs[key] for key in inputs if key != "percent"},
        title="A storage box with one small cube in a corner",
        alt_text=(
            f"A cuboid box with edges {length.text}, {depth.text} and {height.text}, and hidden "
            f"edges dashed. One small cube of side {cube.text} sits in the front bottom corner."
        ),
        answers=answers,
        derived=[count, volume, used, c**3, ln, ln / c, d / c, h / c, ln * d * h / c**3],
        findings=_key_findings(count, answers),
    )


def _prism_points(front: dict[str, Point], length: float) -> tuple[dict[str, Point], Point]:
    offset = _oblique(0.0, length, 0.0)
    points = dict(front)
    for name, point in front.items():
        points[f"{name}b"] = add(point, offset)
    return points, offset


def _draw_prism(sketch: _Sketch, outline: Sequence[str], hidden_vertex: str) -> None:
    """Draw a prism whose rear copy of ``hidden_vertex`` is the only hidden vertex."""
    back = [f"{name}b" for name in outline]
    sketch.shade(back, SIDE, "rear-face")
    count = len(outline)
    for index in range(count):
        start, end = outline[index], outline[(index + 1) % count]
        if hidden_vertex not in (start, end):
            sketch.shade([start, end, f"{end}b", f"{start}b"], TOP, f"side-{start}{end}")
    sketch.shade(outline, FILL, "cross-section")
    rear = f"{hidden_vertex}b"
    for index in range(count):
        start, end = back[index], back[(index + 1) % count]
        if rear in (start, end):
            sketch.edge(start, end, hidden=True, thin=True)
    sketch.edge(hidden_vertex, rear, hidden=True, thin=True)
    for index in range(count):
        start, end = back[index], back[(index + 1) % count]
        if rear not in (start, end):
            sketch.edge(start, end)
    for name in outline:
        if name != hidden_vertex:
            sketch.edge(name, f"{name}b")
    for index in range(count):
        sketch.edge(outline[index], outline[(index + 1) % count])


def _right_prism(
    inputs: dict[str, Any],
    answers: Sequence[str],
    *,
    template: str,
    base: Quantity,
    height: Quantity,
    length: Quantity,
    hypotenuse: Quantity | None,
    expected: float,
    derived: Sequence[float],
) -> Diagram:
    _same_unit(base, height, length)
    b, h = base.value, height.value
    front = {"A": (0.0, 0.0), "B": (b, 0.0), "C": (0.0, h)}
    points, _ = _prism_points(front, length.value)
    sketch = _Sketch(points, top=30, side_labels=(height.text,))
    _draw_prism(sketch, ["A", "B", "C"], "A")
    sketch.canvas.right_angle("A", "B", "C", size=20)
    sketch.figure(
        "prism",
        front=["A", "B", "C"],
        back=["Ab", "Bb", "Cb"],
        hidden_vertex="Ab",
        cross_section={"type": "right_triangle", "points": ["A", "B", "C"], "right_at": "A"},
    )
    sketch.length(base.text, "A", "B", away_from="C", value=b)
    sketch.length(height.text, "C", "A", away_from="B", value=h)
    sketch.length(length.text, "B", "Bb", away_from="A", value=length.value, factor=DEPTH)
    if hypotenuse is not None:
        sketch.length(
            hypotenuse.text,
            "B",
            "C",
            away_from="A",
            value=hypotenuse.value,
            positions=(0.74, 0.66, 0.82, 0.58),
        )
    sides = f"perpendicular sides {base.text} and {height.text}"
    if hypotenuse is not None:
        sides += f" and longest side {hypotenuse.text}"
    return sketch.diagram(
        template=template,
        inputs=inputs,
        kind="prism",
        dimensions={key: inputs[key] for key in inputs},
        title="A triangular prism with a right-triangle cross-section",
        alt_text=(
            f"A triangular prism. Its front face is a right triangle with {sides}, and the right "
            f"angle is marked. The prism is {length.text} long, and hidden edges are dashed."
        ),
        answers=answers,
        derived=derived,
        findings=_key_findings(expected, answers),
    )


def prism_right_triangle_legs(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    base, height, length = _given(inputs, "base", "height", "length")
    area = base.value * height.value / 2
    volume = area * length.value
    return _right_prism(
        inputs,
        answers,
        template="prism_right_triangle_legs",
        base=base,
        height=height,
        length=length,
        hypotenuse=None,
        expected=volume,
        derived=[area, volume],
    )


def prism_right_triangle_sides(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length = q(inputs["length"])
    sides = sorted((q(item) for item in inputs["sides"]), key=lambda item: item.value)
    short, middle, longest = sides
    _require(
        math.isclose(short.value**2 + middle.value**2, longest.value**2),
        "The stated sides do not form a right triangle.",
    )
    area = short.value * middle.value / 2
    perimeter = short.value + middle.value + longest.value
    surface = 2 * area + perimeter * length.value
    return _right_prism(
        inputs,
        answers,
        template="prism_right_triangle_sides",
        base=middle,
        height=short,
        length=length,
        hypotenuse=longest,
        expected=surface,
        derived=[area, perimeter, surface, perimeter * length.value],
    )


def trapezoidal_prism(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    short, long, height, length = _given(
        inputs, "parallel_short", "parallel_long", "height", "length"
    )
    _same_unit(short, long, height, length)
    _require(short.value < long.value, "A trapezium needs unequal parallel sides.")
    area = (short.value + long.value) / 2 * height.value
    volume = area * length.value
    front = {
        name: point
        for name, point in _trapezium_points("", 0.0, long.value, short.value, height.value).items()
        if name != "F"
    }
    points, _ = _prism_points(front, length.value)
    points["F"] = (points["C"][0], 0.0)
    sketch = _Sketch(points, top=30)
    outline = ["A", "B", "C", "D"]
    _draw_prism(sketch, outline, "A")
    sketch.edge("C", "F", hidden=True, thin=True)
    sketch.canvas.right_angle("F", "A", "C", size=18)
    sketch.relate("collinear", points=["A", "F", "B"])
    sketch.figure(
        "prism",
        front=outline,
        back=[f"{name}b" for name in outline],
        hidden_vertex="Ab",
        cross_section={
            "type": "trapezium",
            "points": outline,
            "heights": [{"segment": "CF", "foot": "F", "top": "C", "base": ["A", "B"]}],
        },
    )
    sketch.length(long.text, "A", "B", away_from="D", value=long.value)
    sketch.length(
        short.text, "C", "D", away_from="Db", value=short.value, positions=(0.74, 0.7, 0.78, 0.66)
    )
    sketch.length(
        height.text, "C", "F", away_from="B", value=height.value, positions=(0.72, 0.8, 0.64)
    )
    sketch.length(length.text, "B", "Bb", away_from="A", value=length.value, factor=DEPTH)
    return sketch.diagram(
        template="trapezoidal_prism",
        inputs=inputs,
        kind="prism",
        dimensions={key: inputs[key] for key in inputs},
        title="A prism with a trapezium cross-section",
        alt_text=(
            f"A prism whose front face is a trapezium with parallel sides {short.text} and "
            f"{long.text} and dashed perpendicular height {height.text}, with a right angle marked "
            f"at its foot. The prism is {length.text} long, and hidden edges are dashed."
        ),
        answers=answers,
        derived=[area, volume],
        findings=_key_findings(volume, answers),
    )


def two_cubes_joined(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side = q(inputs["side"])
    s = side.value
    total = 12 * s * s - 2 * s * s
    points = {
        "P0": _oblique(0, 0, 0),
        "P1": _oblique(s, 0, 0),
        "P2": _oblique(2 * s, 0, 0),
        "Q0": _oblique(0, 0, s),
        "Q1": _oblique(s, 0, s),
        "Q2": _oblique(2 * s, 0, s),
        "R0": _oblique(0, s, 0),
        "R1": _oblique(s, s, 0),
        "R2": _oblique(2 * s, s, 0),
        "S0": _oblique(0, s, s),
        "S1": _oblique(s, s, s),
        "S2": _oblique(2 * s, s, s),
    }
    sketch = _Sketch(points, top=30, bottom=92)
    sketch.shade(["P2", "R2", "S2", "Q2"], SIDE, "right-face")
    sketch.shade(["Q0", "Q2", "S2", "S0"], TOP, "top-face")
    sketch.shade(["P0", "P2", "Q2", "Q0"], FILL, "front-face")
    sketch.shade(["P1", "R1", "S1", "Q1"], SHARED, "shared-face")
    for start, end in (
        ("P0", "R0"),
        ("R0", "S0"),
        ("R0", "R1"),
        ("R1", "R2"),
        ("P1", "R1"),
        ("R1", "S1"),
    ):
        sketch.edge(start, end, hidden=True, thin=True)
    for start, end in (
        ("P0", "P1"),
        ("P1", "P2"),
        ("Q0", "Q1"),
        ("Q1", "Q2"),
        ("P0", "Q0"),
        ("P1", "Q1"),
        ("P2", "Q2"),
        ("Q0", "S0"),
        ("Q1", "S1"),
        ("Q2", "S2"),
        ("S0", "S1"),
        ("S1", "S2"),
        ("P2", "R2"),
        ("R2", "S2"),
    ):
        sketch.edge(start, end)
    sketch.figure(
        "joined_cubes",
        first=["P0", "P1", "Q1", "Q0", "R0", "R1", "S1", "S0"],
        second=["P1", "P2", "Q2", "Q1", "R1", "R2", "S2", "S1"],
        shared_face="shared-face",
    )
    sketch.equal("P0P1", "P1P2", "P0Q0", "P2Q2")
    sketch.length(side.text, "P0", "P1", away_from="Q0", value=s)
    sketch.legend("Shaded: shared face")
    return sketch.diagram(
        template="two_cubes_joined",
        inputs=inputs,
        kind="joined_solids",
        dimensions={"side": inputs["side"]},
        title="Two equal cubes joined face to face",
        alt_text=(
            f"Two equal cubes of side {side.text} joined face to face to make one long block. The "
            "shared face is shaded, the four marked edges are equal, and hidden edges are dashed."
        ),
        answers=answers,
        derived=[total, s * s, 6 * s * s, 12 * s * s],
        findings=_key_findings(total, answers),
    )


def _block_edge(
    sketch: _Sketch, start: str, end: str, pieces: Sequence[tuple[str, str, bool]]
) -> None:
    """Draw an edge in the runs that are in front of or behind the block on top of it."""
    if not pieces:
        sketch.edge(start, end)
        return
    for first, second, hidden in pieces:
        sketch.edge(first, second, hidden=hidden, thin=hidden)


def block_on_cuboid(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, depth, height = _given(inputs, "length", "depth", "height")
    block_l, block_d, block_h = _given(inputs, "block_length", "block_depth", "block_height")
    _same_unit(length, depth, height, block_l, block_d, block_h)
    ln, d, h = length.value, depth.value, height.value
    w, e, g = block_l.value, block_d.value, block_h.value
    _require(w < ln and e < d, "The block must sit inside the top face of the cuboid.")
    is_cube = math.isclose(w, e) and math.isclose(e, g)
    x0, y0 = (ln - w) / 2, (d - e) / 2
    base = _box_points("", ln, d, h)
    block = _box_points("k", w, e, g, origin=(x0, y0, h))
    points = {**base, **block}
    silhouette = [block[f"k{name}"] for name in ("F1", "F2", "B2", "B3", "B4", "F4")]
    back_pieces: list[tuple[str, str, bool]] = []
    runs = _runs(base["B4"], base["B3"], silhouette)
    if len(runs) > 1:
        names = ["B4"]
        start, end = base["B4"], base["B3"]
        for index, (_, stop, _inside_block) in enumerate(runs[:-1], start=1):
            name = f"Z{index}"
            points[name] = (start[0] + (end[0] - start[0]) * stop, start[1])
            names.append(name)
        names.append("B3")
        back_pieces = [(names[index], names[index + 1], run[2]) for index, run in enumerate(runs)]
    sketch = _Sketch(points, max_height=290, top=62, side_labels=(height.text,))
    _shade_box(sketch, "")
    _hidden_box_edges(sketch, "")
    n = _box_names("")
    _visible_box_edges(sketch, "", skip=("B3B4",))
    _block_edge(sketch, "B4", "B3", back_pieces)
    _box_figure(
        sketch, "", occluded=[[first, second] for first, second, hide in back_pieces if hide]
    )
    _shade_box(sketch, "k", front=FILL_ALT, side=SHARED, top=TOP)
    _hidden_box_edges(sketch, "k")
    _visible_box_edges(sketch, "k")
    _box_figure(sketch, "k", on_top_of=[n["F4"], n["F3"], n["B3"], n["B4"]], cube=is_cube)
    k = _box_names("k")
    sketch.length(length.text, n["F1"], n["F2"], away_from=n["F4"], value=ln)
    sketch.length(height.text, n["F4"], n["F1"], away_from=n["F2"], value=h)
    sketch.length(depth.text, n["F2"], n["B2"], away_from=n["F1"], value=d, factor=DEPTH)
    up_left = [(-1.0, -0.4), (-1.0, -0.9), (-0.4, -1.0)]
    if is_cube:
        sketch.equal(f"{k['F1']}{k['F2']}", f"{k['F2']}{k['F3']}", f"{k['F4']}{k['F1']}")
        sketch.length(block_l.text, k["B3"], k["B4"], away_from=k["F1"], value=w)
        block_words = f"a cube of side {block_l.text}"
        block_derived = [6 * w * w, w * w]
    else:
        sketch.length(block_l.text, k["B3"], k["B4"], away_from=k["F1"], value=w)
        sketch.length(block_d.text, k["F3"], k["B3"], away_from=k["F1"], value=e, factor=DEPTH)
        sketch.length(
            block_h.text, k["F4"], k["F1"], away_from=k["F2"], value=g, directions=up_left
        )
        block_words = (
            f"a smaller cuboid with edges {block_l.text}, {block_d.text} and {block_h.text}"
        )
        block_derived = [2 * (w * e + w * g + e * g), w * e]
    base_area = 2 * (ln * d + ln * h + d * h)
    total = base_area + 2 * (w * e + w * g + e * g) - 2 * w * e
    return sketch.diagram(
        template="block_on_cuboid",
        inputs=inputs,
        kind="joined_solids",
        dimensions={key: inputs[key] for key in inputs},
        title="A block attached on top of a cuboid",
        alt_text=(
            f"A cuboid with edges {length.text}, {depth.text} and {height.text}, with "
            f"{block_words} attached on its top face. Hidden edges are dashed."
        ),
        answers=answers,
        derived=[total, base_area, *block_derived],
        findings=_key_findings(total, answers),
    )


def cuboid_tunnel(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, height, run, hole_w, hole_h = _given(
        inputs, "length", "height", "run", "hole_width", "hole_height"
    )
    _same_unit(length, height, run, hole_w, hole_h)
    ln, h, d, a, b = length.value, height.value, run.value, hole_w.value, hole_h.value
    _require(a < ln and b < h, "The tunnel must fit inside the face it opens on.")
    volume = ln * h * d - a * b * d
    x0, z0 = (ln - a) / 2, (h - b) / 2
    points = {
        **_box_points("", ln, d, h, with_hidden_vertex=False),
        "H1": _oblique(x0, 0, z0),
        "H2": _oblique(x0 + a, 0, z0),
        "H3": _oblique(x0 + a, 0, z0 + b),
        "H4": _oblique(x0, 0, z0 + b),
        "J1": _oblique(x0, d, z0),
        "J2": _oblique(x0 + a, d, z0),
        "J3": _oblique(x0 + a, d, z0 + b),
        "J4": _oblique(x0, d, z0 + b),
    }
    sketch = _Sketch(points, max_height=280, top=30, side_labels=(height.text,))
    _shade_box(sketch, "")
    _visible_box_edges(sketch, "")
    _box_figure(sketch, "", hidden=False)
    sketch.shade(["H1", "H2", "H3", "H4"], INTERIOR, "tunnel-opening")
    near, far = ["H1", "H2", "H3", "H4"], ["J1", "J2", "J3", "J4"]
    for first, second in zip(far, [*far[1:], far[0]], strict=True):
        sketch.edge(first, second, hidden=True, thin=True)
    for first, second in zip(near, far, strict=True):
        sketch.edge(first, second, hidden=True, thin=True)
    for first, second in zip(near, [*near[1:], near[0]], strict=True):
        sketch.edge(first, second)
    sketch.figure("rectangular_hole", near=near, far=far, face=["F1", "F2", "F3", "F4"])
    sketch.length(length.text, "F1", "F2", away_from="F4", value=ln)
    sketch.length(height.text, "F4", "F1", away_from="F2", value=h)
    sketch.length(run.text, "F2", "B2", away_from="F1", value=d, factor=DEPTH)
    sketch.length(hole_w.text, "H1", "H2", away_from="H4", value=a)
    sketch.length(hole_h.text, "H4", "H1", away_from="H2", value=b)
    return sketch.diagram(
        template="cuboid_tunnel",
        inputs=inputs,
        kind="drilled_solid",
        dimensions={key: inputs[key] for key in inputs},
        title="A cuboid with a rectangular tunnel",
        alt_text=(
            f"A cuboid with a front face {length.text} by {height.text} and depth {run.text}. A "
            f"rectangular tunnel {hole_w.text} by {hole_h.text} opens on the front face and runs "
            f"through the {run.text} depth. The tunnel's hidden edges are dashed."
        ),
        answers=answers,
        derived=[volume, ln * h * d, a * b * d],
        findings=_key_findings(volume, answers),
    )


def _iso_points(ln: float, d: float, h: float) -> dict[str, Point]:
    return {
        "F": _iso(0, 0, 0),
        "R": _iso(ln, 0, 0),
        "L": _iso(0, d, 0),
        "TF": _iso(0, 0, h),
        "TR": _iso(ln, 0, h),
        "TL": _iso(0, d, h),
        "TB": _iso(ln, d, h),
    }


def _draw_iso_box(sketch: _Sketch) -> None:
    sketch.shade(["F", "R", "TR", "TF"], SIDE, "right-face")
    sketch.shade(["F", "L", "TL", "TF"], FILL, "left-face")
    sketch.shade(["TF", "TR", "TB", "TL"], TOP, "top-face")


def _iso_edges(sketch: _Sketch) -> None:
    for start, end in (
        ("F", "R"),
        ("F", "L"),
        ("F", "TF"),
        ("R", "TR"),
        ("L", "TL"),
        ("TF", "TR"),
        ("TF", "TL"),
        ("TR", "TB"),
        ("TL", "TB"),
    ):
        sketch.edge(start, end)


def _hole_position(ln: float, d: float, a: float, b: float) -> tuple[float, float]:
    """Centre the hole, shifted if a hidden corner edge would lie on the front vertical edge."""
    y0 = (d - b) / 2
    centred = (ln - a) / 2
    for shift in (0.0, 0.5, -0.5, 1.0, -1.0):
        x0 = centred + shift
        if 0 < x0 < ln - a and all(
            abs(x - y) * ISO_COS > 0.35
            for x, y in ((x0, y0), (x0 + a, y0), (x0 + a, y0 + b), (x0, y0 + b))
        ):
            return x0, y0
    return centred, y0


def cuboid_vertical_hole(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, depth, height, hole_w, hole_d = _given(
        inputs, "length", "depth", "height", "hole_width", "hole_depth"
    )
    _same_unit(length, depth, height, hole_w, hole_d)
    ln, d, h, a, b = length.value, depth.value, height.value, hole_w.value, hole_d.value
    _require(a < ln and b < d, "The hole must fit inside the top face.")
    volume = ln * d * h - a * b * h
    x0, y0 = _hole_position(ln, d, a, b)
    points = {
        **_iso_points(ln, d, h),
        "H1": _iso(x0, y0, h),
        "H2": _iso(x0 + a, y0, h),
        "H3": _iso(x0 + a, y0 + b, h),
        "H4": _iso(x0, y0 + b, h),
        "J1": _iso(x0, y0, 0),
        "J2": _iso(x0 + a, y0, 0),
        "J3": _iso(x0 + a, y0 + b, 0),
        "J4": _iso(x0, y0 + b, 0),
    }
    sketch = _Sketch(points, max_width=400, max_height=310, top=30, depth_factor=1.0)
    _draw_iso_box(sketch)
    _iso_edges(sketch)
    sketch.figure(
        "cuboid",
        vertices={
            "F1": "F",
            "F2": "R",
            "F3": "TR",
            "F4": "TF",
            "B1": "L",
            "B3": "TB",
            "B4": "TL",
        },
        projection="isometric",
        hidden_vertex=None,
    )
    sketch.shade(["H1", "H2", "H3", "H4"], INTERIOR, "hole-opening")
    near, far = ["H1", "H2", "H3", "H4"], ["J1", "J2", "J3", "J4"]
    for first, second in zip(far, [*far[1:], far[0]], strict=True):
        sketch.edge(first, second, hidden=True, thin=True)
    for first, second in zip(near, far, strict=True):
        sketch.edge(first, second, hidden=True, thin=True)
    for first, second in zip(near, [*near[1:], near[0]], strict=True):
        sketch.edge(first, second)
    sketch.figure("rectangular_hole", near=near, far=far, face=["TF", "TR", "TB", "TL"])
    sketch.length(length.text, "F", "R", away_from="TL", value=ln)
    sketch.length(depth.text, "F", "L", away_from="TR", value=d)
    sketch.length(height.text, "R", "TR", away_from="L", value=h)
    outward = [(0.0, -1.0), (0.5, -1.0), (-0.5, -1.0), (1.0, -1.0), (-1.0, -1.0)]
    sketch.leader(hole_w.text, "H3", "H4", directions=outward, value=a, distances=(40, 60, 85, 110))
    sketch.leader(
        hole_d.text, "H2", "H3", directions=[(1.0, -0.6), (1.0, -1.0), (1.0, 0.0)], value=b
    )
    return sketch.diagram(
        template="cuboid_vertical_hole",
        inputs=inputs,
        kind="drilled_solid",
        dimensions={key: inputs[key] for key in inputs},
        title="A cuboid with a rectangular hole through its height",
        alt_text=(
            f"A cuboid with edges {length.text}, {depth.text} and height {height.text}. A "
            f"rectangular hole {hole_w.text} by {hole_d.text} opens on the top face and passes down "
            f"through the {height.text} height, with its hidden edges dashed."
        ),
        answers=answers,
        derived=[volume, ln * d * h, a * b * h, a * b],
        findings=_key_findings(volume, answers),
    )


def _drilled(
    inputs: dict[str, Any],
    answers: Sequence[str],
    *,
    template: str,
    ln: float,
    d: float,
    h: float,
    radius: Quantity,
    title: str,
    alt_solid: str,
    labels: Callable[[_Sketch], None],
    pi: float,
) -> Diagram:
    r = radius.value
    _require(2 * r < min(ln, d), "The hole must fit inside the top face.")
    block = ln * d * h
    hole = pi * r * r * h
    remaining = block - hole
    top_centre = _iso(ln / 2, d / 2, h)
    far_centre = _iso(ln / 2, d / 2, 0)
    points = {
        **_iso_points(ln, d, h),
        "O": top_centre,
        "Y": far_centre,
        "M": _iso(ln / 2 + r, d / 2, h),
        "A1": (top_centre[0] - ISO_RX * r, top_centre[1]),
        "A2": (top_centre[0] + ISO_RX * r, top_centre[1]),
        "C1": (far_centre[0] - ISO_RX * r, far_centre[1]),
        "C2": (far_centre[0] + ISO_RX * r, far_centre[1]),
    }
    sketch = _Sketch(points, max_width=400, max_height=320, top=30, depth_factor=1.0)
    _draw_iso_box(sketch)
    _iso_edges(sketch)
    sketch.figure(
        "cuboid",
        vertices={
            "F1": "F",
            "F2": "R",
            "F3": "TR",
            "F4": "TF",
            "B1": "L",
            "B3": "TB",
            "B4": "TL",
        },
        projection="isometric",
        hidden_vertex=None,
        cube=math.isclose(ln, d) and math.isclose(d, h),
    )
    rx, ry = ISO_RX * r * sketch.scale, ISO_RY * r * sketch.scale
    canvas = sketch.canvas
    canvas.ellipse("far", "Y", rx, ry, hidden_back=True, hidden_front=True, width=THIN)
    canvas.ellipse("near", "O", rx, ry, hidden_back=False, fill=INTERIOR)
    sketch.edge("A1", "C1", hidden=True, thin=True)
    sketch.edge("A2", "C2", hidden=True, thin=True)
    sketch.edge("O", "M", thin=True)
    canvas.dot("O", radius=4)
    sketch.relate("ellipse_centre", ellipse="near", point="O")
    sketch.relate("ellipse_centre", ellipse="far", point="Y")
    sketch.relate("on_ellipse", ellipse="near", points=["M", "A1", "A2"])
    sketch.relate("on_ellipse", ellipse="far", points=["C1", "C2"])
    sketch.relate("vertical", points=["A1", "C1"])
    sketch.relate("vertical", points=["A2", "C2"])
    sketch.relate("vertical", points=["O", "Y"])
    sketch.figure(
        "cylindrical_hole",
        near="near",
        far="far",
        sides=["A1C1", "A2C2"],
        radius="OM",
        face=["TF", "TR", "TB", "TL"],
    )
    labels(sketch)
    sketch.leader(
        radius.text,
        "O",
        "M",
        directions=[(0.25, -1.0), (0.6, -1.0), (1.0, -1.0), (0.0, -1.0)],
        value=r,
        anchors=(0.7, 0.5),
        distances=(45, 60, 85, 110, 140),
    )
    return sketch.diagram(
        template=template,
        inputs=inputs,
        kind="drilled_solid",
        dimensions={key: inputs[key] for key in inputs},
        title=title,
        alt_text=(
            f"{alt_solid} A cylindrical hole of radius {radius.text} opens on the top face and "
            "passes straight down through the solid. The hole's far rim and sides are dashed."
        ),
        answers=answers,
        derived=[remaining, block, hole, pi * r * r],
        findings=_key_findings(remaining, answers),
    )


def cuboid_cylindrical_hole(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, depth, height, radius = _given(inputs, "length", "depth", "height", "radius")
    _same_unit(length, depth, height, radius)
    ln, d, h = length.value, depth.value, height.value

    def labels(sketch: _Sketch) -> None:
        sketch.length(length.text, "F", "R", away_from="TL", value=ln)
        sketch.length(depth.text, "F", "L", away_from="TR", value=d)
        sketch.length(height.text, "R", "TR", away_from="L", value=h)

    return _drilled(
        inputs,
        answers,
        template="cuboid_cylindrical_hole",
        ln=ln,
        d=d,
        h=h,
        radius=radius,
        title="A cuboid with a cylindrical hole through its height",
        alt_solid=f"A cuboid with edges {length.text}, {depth.text} and height {height.text}.",
        labels=labels,
        pi=float(inputs.get("pi", 22 / 7)),
    )


def cube_cylindrical_hole(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side, radius = _given(inputs, "side", "radius")
    _same_unit(side, radius)
    s = side.value

    def labels(sketch: _Sketch) -> None:
        sketch.equal("FR", "FL", "RTR")
        sketch.length(side.text, "F", "R", away_from="TL", value=s)

    return _drilled(
        inputs,
        answers,
        template="cube_cylindrical_hole",
        ln=s,
        d=s,
        h=s,
        radius=radius,
        title="A cube with a cylindrical hole through it",
        alt_solid=f"A cube of side {side.text}, with equal marks on three of its edges.",
        labels=labels,
        pi=float(inputs.get("pi", 22 / 7)),
    )


def _open_cylinder(
    inputs: dict[str, Any],
    answers: Sequence[str],
    *,
    template: str,
    radius: Quantity,
    drawn_height: float,
    height_label: str,
    height_value: float | None,
    neutral: dict[str, Any] | None,
    alt_height: str,
    dimensions: dict[str, Any],
    derived: Sequence[float],
    expected: float,
    unknowns: Sequence[tuple[str, str]] = (),
) -> Diagram:
    r = radius.value
    px = min(150 / r, 235 / drawn_height)
    ry = r * px * RIM_RATIO
    points = {
        "O": (0.0, drawn_height),
        "B": (0.0, 0.0),
        "A1": (-r, drawn_height),
        "A2": (r, drawn_height),
        "C1": (-r, 0.0),
        "C2": (r, 0.0),
    }
    sketch = _Sketch(
        points,
        max_width=2 * r * px,
        max_height=drawn_height * px,
        top=52 + ry,
        bottom=74 + ry,
        depth_factor=1.0,
    )
    canvas = sketch.canvas
    if neutral:
        sketch.neutral.append(neutral)
    rx = r * sketch.scale
    ry = rx * RIM_RATIO
    sketch.shade(["A1", "A2", "C2", "C1"], FILL, "curved-surface")
    canvas.ellipse("base", "B", rx, ry, hidden_back=True, fill=FILL)
    canvas.ellipse("rim", "O", rx, ry, hidden_back=False, fill=INTERIOR)
    sketch.edge("A1", "C1")
    sketch.edge("A2", "C2")
    sketch.edge("O", "A2", thin=True)
    canvas.dot("O", radius=4)
    sketch.relate("ellipse_centre", ellipse="rim", point="O")
    sketch.relate("ellipse_centre", ellipse="base", point="B")
    sketch.relate("on_ellipse", ellipse="rim", points=["A1", "A2"])
    sketch.relate("on_ellipse", ellipse="base", points=["C1", "C2"])
    sketch.relate("vertical", points=["A1", "C1"])
    sketch.relate("vertical", points=["A2", "C2"])
    sketch.figure(
        "cylinder",
        rim="rim",
        base="base",
        sides=["A1C1", "A2C2"],
        radius="OA2",
        open_top=True,
        interior=INTERIOR,
    )
    if height_value is None:
        sketch.length(height_label, "A2", "C2", away_from="A1", variable="h", constant=0.0)
    else:
        sketch.length(height_label, "A2", "C2", away_from="A1", value=height_value)
    sketch.leader(
        radius.text,
        "O",
        "A2",
        directions=[(0.0, 1.0), (0.3, 1.0)],
        value=r,
        anchors=(0.5, 0.42, 0.58),
        distances=(ry + 30, ry + 50, ry + 80),
    )
    top_of_rim = canvas.points["O"][1] - ry
    sketch.caption("Open top", [(canvas.points["O"][0], top_of_rim - gap) for gap in (20, 26, 32)])
    return sketch.diagram(
        template=template,
        inputs=inputs,
        kind="cylinder",
        dimensions=dimensions,
        title="A cylinder that is open at the top",
        alt_text=(
            f"A cylinder that is open at the top, with radius {radius.text} and {alt_height}. The "
            "inside of the rim is shaded, and the far half of the base is dashed."
        ),
        answers=answers,
        derived=derived,
        unknowns=unknowns,
        findings=_key_findings(expected, answers),
    )


def open_cylinder(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius, height = _given(inputs, "radius", "height")
    _same_unit(radius, height)
    pi = float(inputs.get("pi", 22 / 7))
    r, h = radius.value, height.value
    base, curved = pi * r * r, 2 * pi * r * h
    return _open_cylinder(
        inputs,
        answers,
        template="open_cylinder",
        radius=radius,
        drawn_height=h,
        height_label=height.text,
        height_value=h,
        neutral=None,
        alt_height=f"height {height.text}",
        dimensions={key: inputs[key] for key in inputs if key != "pi"},
        derived=[base + curved, base, curved],
        expected=base + curved,
    )


def open_cylinder_material(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius, material = _given(inputs, "radius", "material")
    pi = float(inputs.get("pi", 22 / 7))
    r = radius.value
    base = pi * r * r
    h = (material.value - base) / (2 * pi * r)
    _require(h > 0, "The stated metal area gives no positive height.")
    volume = base * h
    drawn = _neutral(h, 1.3)
    return _open_cylinder(
        inputs,
        answers,
        template="open_cylinder_material",
        radius=radius,
        drawn_height=drawn,
        height_label="h",
        height_value=None,
        neutral={"variable": "h", "drawn": drawn, "avoid": h},
        alt_height="an unknown height marked h",
        dimensions={"radius": inputs["radius"]},
        derived=[volume, h, base, 2 * pi * r, material.value - base],
        expected=volume,
        unknowns=[("segment:A2C2", "h")],
    )


TEMPLATES: dict[str, Callable[..., Diagram]] = {
    function.__name__: function
    for function in (
        parallelogram_area,
        parallelogram_and_trapezium,
        trapezium_and_parallelogram_algebra,
        rectangle_and_square,
        corner_removed,
        corner_removed_algebra,
        joined_rectangles,
        joined_rectangles_algebra,
        uniform_border,
        track_algebra,
        cuboid_volume,
        open_box,
        box_with_cube,
        prism_right_triangle_legs,
        prism_right_triangle_sides,
        trapezoidal_prism,
        two_cubes_joined,
        block_on_cuboid,
        cuboid_tunnel,
        cuboid_vertical_hole,
        cuboid_cylindrical_hole,
        cube_cylindrical_hole,
        open_cylinder,
        open_cylinder_material,
    )
}


# ------------------------------------------------------------------------- reading a prompt
NUM = r"(\d+(?:\.\d+)?)"
UNIT = r"\s?(mm|cm|km|m)(?![\w²³])"
N = NUM + UNIT


def _len(value: str, unit_name: str) -> dict[str, Any]:
    return Quantity(float(value), unit_name).as_spec()


def _area(value: str, unit_name: str) -> dict[str, Any]:
    return Quantity(float(value), unit_name).as_spec()


def _int(value: str) -> int:
    return int(value)


def _trapezoid_inputs(m: re.Match[str]) -> dict[str, Any]:
    return {
        "base": _len(m[1], m[2]),
        "height": _len(m[3], m[4]),
        "parallel_short": _len(m[5], m[6]),
        "parallel_long": _len(m[7], m[8]),
        "trapezium_height": _len(m[9], m[10]),
    }


PATTERNS: list[tuple[str, re.Pattern[str], Callable[[re.Match[str]], dict[str, Any]]]] = [
    (
        "parallelogram_area",
        re.compile(rf"parallelogram \w+ has base {N} and perpendicular height {N}\. Find its area"),
        lambda m: {"base": _len(m[1], m[2]), "height": _len(m[3], m[4])},
    ),
    (
        "parallelogram_and_trapezium",
        re.compile(
            rf"parallelogram \w+ has base {N} and height {N}\. Beside it is a trapezium with "
            rf"parallel sides {N} and {N} and height {N}\. Find their combined area"
        ),
        _trapezoid_inputs,
    ),
    (
        "trapezium_and_parallelogram_algebra",
        re.compile(
            rf"trapezium with parallel sides x cm and \(x \+ (\d+)\) cm and height {N}, together "
            rf"with a non-overlapping parallelogram of base \(x \+ (\d+)\) cm and height {N}\. "
            rf"The combined area is {NUM}\s?(cm²)"
        ),
        lambda m: {
            "long_extra": _int(m[1]),
            "trapezium_height": _len(m[2], m[3]),
            "base_extra": _int(m[4]),
            "height": _len(m[5], m[6]),
            "total_area": _area(m[7], m[8]),
        },
    ),
    (
        "rectangle_and_square",
        re.compile(
            rf"rectangle {N} by {N} and a non-overlapping square of side {N}\. Find its total area"
        ),
        lambda m: {"width": _len(m[1], m[2]), "height": _len(m[3], m[4]), "side": _len(m[5], m[6])},
    ),
    (
        "corner_removed",
        re.compile(
            rf"{N} by {N} \w+ has a {N} by {N} rectangular corner removed\. Square tiles each "
            rf"cover {NUM} m²"
        ),
        lambda m: {
            "width": _len(m[1], m[2]),
            "height": _len(m[3], m[4]),
            "cut_width": _len(m[5], m[6]),
            "cut_height": _len(m[7], m[8]),
            "tile_area": float(m[9]),
        },
    ),
    (
        "corner_removed",
        re.compile(
            rf"{N} by {N} rectangle has a {N} by {N} rectangle cut from its top-right corner\. "
            r"Find the perimeter"
        ),
        lambda m: {
            "width": _len(m[1], m[2]),
            "height": _len(m[3], m[4]),
            "cut_width": _len(m[5], m[6]),
            "cut_height": _len(m[7], m[8]),
            "asks": "perimeter",
        },
    ),
    (
        "corner_removed_algebra",
        re.compile(
            rf"rectangle measures \(x \+ (\d+)\) cm by \(x \+ (\d+)\) cm\. A {N} by {N} corner is "
            rf"removed, leaving area {NUM}\s?(cm²)"
        ),
        lambda m: {
            "width_extra": _int(m[1]),
            "height_extra": _int(m[2]),
            "cut_width": _len(m[3], m[4]),
            "cut_height": _len(m[5], m[6]),
            "remaining_area": _area(m[7], m[8]),
        },
    ),
    (
        "joined_rectangles",
        re.compile(
            rf"{N} by {N} rectangle is joined to a {N} by {N} rectangle along the smaller "
            rf"rectangle's {NUM}{UNIT} edge"
        ),
        lambda m: {
            "width": _len(m[1], m[2]),
            "height": _len(m[3], m[4]),
            "extension": _len(m[5], m[6]) if float(m[7]) == float(m[9]) else _len(m[7], m[8]),
            "shared": _len(m[9], m[10]),
        },
    ),
    (
        "joined_rectangles_algebra",
        re.compile(
            rf"rectangle x cm by {N} is joined to a rectangle \(x - (\d+)\) cm by {N} along a "
            rf"complete {NUM}{UNIT} edge\..*?total area is {NUM}\s?(cm²)"
        ),
        lambda m: {
            "side": _len(m[1], m[2]),
            "less": _int(m[3]),
            "shared": _len(m[4], m[5]),
            "total_area": _area(m[8], m[9]),
        },
    ),
    (
        "uniform_border",
        re.compile(rf"measures {N} by {N} outside\. Its border is {N} wide on every side"),
        lambda m: {
            "width": _len(m[1], m[2]),
            "height": _len(m[3], m[4]),
            "border": _len(m[5], m[6]),
        },
    ),
    (
        "track_algebra",
        re.compile(
            r"rectangular track has outside dimensions \(x \+ (\d+)\) m by \(x \+ (\d+)\) m and "
            rf"inside dimensions x m by \(x - (\d+)\) m\. Its area is {NUM}\s?(m²)"
        ),
        lambda m: {
            "outer_width": _int(m[1]),
            "outer_height": _int(m[2]),
            "inner_height": _int(m[3]),
            "area": _area(m[4], m[5]),
            "unit": "m",
        },
    ),
    (
        "cuboid_volume",
        re.compile(rf"cuboid measures {N} by {N} by {N}\. Find its volume"),
        lambda m: {
            "length": _len(m[1], m[2]),
            "depth": _len(m[3], m[4]),
            "height": _len(m[5], m[6]),
        },
    ),
    (
        "open_box",
        re.compile(rf"open-top cuboid is {N} long, {N} wide and {N} high"),
        lambda m: {
            "length": _len(m[1], m[2]),
            "depth": _len(m[3], m[4]),
            "height": _len(m[5], m[6]),
        },
    ),
    (
        "box_with_cube",
        re.compile(rf"box measures {N} by {N} by {N}\. Identical cubes of side {N} fill {NUM}% of"),
        lambda m: {
            "length": _len(m[1], m[2]),
            "depth": _len(m[3], m[4]),
            "height": _len(m[5], m[6]),
            "cube": _len(m[7], m[8]),
            "percent": float(m[9]),
        },
    ),
    (
        "prism_right_triangle_legs",
        re.compile(
            rf"right-triangle cross-section with base {N} and height {N}\. Its length is {N}"
        ),
        lambda m: {
            "base": _len(m[1], m[2]),
            "height": _len(m[3], m[4]),
            "length": _len(m[5], m[6]),
        },
    ),
    (
        "prism_right_triangle_sides",
        re.compile(rf"right-triangle cross-section with sides {N}, {N} and {N}, and length {N}"),
        lambda m: {
            "sides": [_len(m[1], m[2]), _len(m[3], m[4]), _len(m[5], m[6])],
            "length": _len(m[7], m[8]),
        },
    ),
    (
        "trapezoidal_prism",
        re.compile(
            rf"prism has a trapezium cross-section with parallel sides {N} and {N} and height {N}\. "
            rf"The prism is {N} long"
        ),
        lambda m: {
            "parallel_short": _len(m[1], m[2]),
            "parallel_long": _len(m[3], m[4]),
            "height": _len(m[5], m[6]),
            "length": _len(m[7], m[8]),
        },
    ),
    (
        "two_cubes_joined",
        re.compile(rf"Two cubes of side {N} are joined face to face"),
        lambda m: {"side": _len(m[1], m[2])},
    ),
    (
        "block_on_cuboid",
        re.compile(rf"{N} by {N} by {N} cuboid has a {N} by {N} by {N} cuboid attached on top"),
        lambda m: {
            "length": _len(m[1], m[2]),
            "depth": _len(m[3], m[4]),
            "height": _len(m[5], m[6]),
            "block_length": _len(m[7], m[8]),
            "block_depth": _len(m[9], m[10]),
            "block_height": _len(m[11], m[12]),
        },
    ),
    (
        "block_on_cuboid",
        re.compile(rf"cube of side {N} is attached by one face to a {N} by {N} by {N} cuboid"),
        lambda m: {
            "length": _len(m[3], m[4]),
            "depth": _len(m[5], m[6]),
            "height": _len(m[7], m[8]),
            "block_length": _len(m[1], m[2]),
            "block_depth": _len(m[1], m[2]),
            "block_height": _len(m[1], m[2]),
        },
    ),
    (
        "cuboid_tunnel",
        re.compile(
            rf"{N} by {N} by {N} cuboid has a rectangular tunnel {N} by {N} running through its full {N} length"
        ),
        lambda m: {
            "length": _len(m[1], m[2]),
            "height": _len(m[3], m[4]),
            "run": _len(m[11], m[12]),
            "hole_width": _len(m[7], m[8]),
            "hole_height": _len(m[9], m[10]),
        },
    ),
    (
        "cuboid_vertical_hole",
        re.compile(
            rf"cuboid measures {N} by {N} by {N}\. A rectangular hole {N} by {N} passes through the full {N} height"
        ),
        lambda m: {
            "length": _len(m[1], m[2]),
            "depth": _len(m[3], m[4]),
            "height": _len(m[11], m[12]),
            "hole_width": _len(m[7], m[8]),
            "hole_depth": _len(m[9], m[10]),
        },
    ),
    (
        "cuboid_cylindrical_hole",
        re.compile(
            rf"{N} by {N} by {N} cuboid has a cylindrical hole of radius {N} drilled through its "
            rf"{N} height\. Using π = 22/7"
        ),
        lambda m: {
            "length": _len(m[1], m[2]),
            "depth": _len(m[3], m[4]),
            "height": _len(m[9], m[10]),
            "radius": _len(m[7], m[8]),
        },
    ),
    (
        "cube_cylindrical_hole",
        re.compile(
            rf"cube of side {N} has a cylindrical hole of radius {N} drilled straight through it\. Using π = 22/7"
        ),
        lambda m: {"side": _len(m[1], m[2]), "radius": _len(m[3], m[4])},
    ),
    (
        "open_cylinder",
        re.compile(
            rf"cylindrical container has radius {N} and height {N} and is open at the top\. Using π = 22/7"
        ),
        lambda m: {"radius": _len(m[1], m[2]), "height": _len(m[3], m[4])},
    ),
    (
        "open_cylinder_material",
        re.compile(
            rf"open cylindrical tank has radius {N}\. The base and curved surface together use "
            rf"{NUM}\s?(cm²) of metal\. Using π = 22/7"
        ),
        lambda m: {"radius": _len(m[1], m[2]), "material": _area(m[3], m[4])},
    ),
]

# A figure would add no spatial information to these, or could only contradict the prompt, so the
# question stays text-only.
TEXT_ONLY: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^Convert \d+(?:\.\d+)? m² to cm²"),
        "The task is a unit conversion with no spatial arrangement, so a figure adds nothing "
        "(CFL-148, audit D-05). A grid of 100 by 100 squares is also too fine to draw legibly.",
    ),
    (
        re.compile(r"Two non-overlapping cuboids have volumes"),
        "Both volumes are stated and the task is to add them, so a figure adds no spatial "
        "information (CFL-149, audit D-06).",
    ),
    (
        re.compile(r"One sheet has area .*? and another has area"),
        "The two areas are stated with no shape or arrangement, so a figure adds no spatial "
        "information (CFL-151, audit D-12).",
    ),
    (
        re.compile(r"rectangle are joined along an edge of length x cm\. The outside perimeter"),
        "CFL-015: the key x = 3 is not an edge of either rectangle. A figure showing a full edge "
        "contradicts the key, and one showing a part of an edge contradicts the wording, so the "
        "prompt must be fixed before this question can have a figure.",
    ),
]


def text_only_reason(prompt: str) -> str | None:
    """Return why this prompt should have no figure, or ``None`` if it can have one."""
    for pattern, reason in TEXT_ONLY:
        if pattern.search(prompt):
            return reason
    return None
