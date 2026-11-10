"""Deterministic Sec 1 G1 diagrams (renderer ``nextscholar-plane-geometry-svg-v1``).

Each template reads the givens of one question and draws that question: angles on a line, crossing
lines, parallel lines, triangles, kites, diagonals and compass constructions. Every coordinate is
computed from the givens. Arcs are centred on their vertex between real rays, parallel and equal
markings are recorded so the validator can measure them, and a value the learner must find carries
a variable. A question whose accurate figure would show its answer is refused (``TEXT_ONLY``).
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from typing import Any

from .canvas import INK, LIGHT, STROKE, THIN, Canvas, add, fmt, length, scale, sub, unit
from .common import (
    PLANE_GEOMETRY_RENDERER,
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
from .right_triangle import arc_radius, q

Point = tuple[float, float]

NOT_TO_SCALE = "Not drawn to scale."
QUADRILATERAL_WORDS = ("square", "rectangle", "rhombus", "parallelogram", "kite", "trapezium")
COMPASS_SPAN = 14.0


def _polar(degrees: float, radius: float = 1.0, origin: Point = (0.0, 0.0)) -> Point:
    angle = math.radians(degrees)
    return (origin[0] + radius * math.cos(angle), origin[1] + radius * math.sin(angle))


def _degree(value: float) -> str:
    return f"{number(value)}°"


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


class _Figure:
    """A canvas plus the markings and relationships the validator measures."""

    renderer = PLANE_GEOMETRY_RENDERER

    def __init__(
        self,
        points: dict[str, Point],
        *,
        max_width: float = 440,
        max_height: float = 270,
        top: float = 48,
        bottom: float = 74,
    ):
        self.canvas: Canvas
        self.canvas, transform = layout(
            list(points.values()), max_width=max_width, max_height=max_height, top=top, bottom=bottom
        )
        for name, point in points.items():
            self.canvas.point(name, transform(point))
        self.relationships: list[dict[str, Any]] = []
        self.equal_marks: list[dict[str, Any]] = []
        self.parallel_marks: list[dict[str, Any]] = []
        self.arcs: dict[str, dict[str, Any]] = {}
        self._labels: list[Callable[[], Any]] = []

    # ---------------------------------------------------------------- strokes and markings
    def line(self, start: str, end: str, *, hidden: bool = False, thin: bool = False) -> str:
        key = f"{start}{end}"
        self.canvas.segment(key, start, end, hidden=hidden, width=THIN if thin else STROKE)
        return key

    def relate(self, kind: str, **fields: Any) -> None:
        self.relationships.append({"type": kind, **fields})

    def parallel(self, first: str, second: str, position: float = 0.88) -> None:
        """Mark two drawn segments as parallel with one chevron each."""
        for key in (first, second):
            p, r = self.canvas.segment_ends[key]
            direction = unit(sub(r, p))
            normal = (-direction[1], direction[0])
            tip = add(p, scale(sub(r, p), position))
            back = add(tip, scale(direction, -12))
            a, b = add(back, scale(normal, 9)), add(back, scale(normal, -9))
            self.canvas.raw_path(
                f"M{fmt(a[0])} {fmt(a[1])} L{fmt(tip[0])} {fmt(tip[1])} L{fmt(b[0])} {fmt(b[1])}",
                [[a, tip, b]],
                stroke=INK,
                width=THIN,
                attrs={"data-parallel-mark": key},
            )
        self.parallel_marks.append({"segments": [first, second]})

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

    def angle(
        self,
        key: str,
        vertex: str,
        first: str,
        second: str,
        label: str,
        *,
        degrees: float | None = None,
        radius: float | None = None,
    ) -> None:
        canvas = self.canvas
        measured = _measure(canvas, vertex, first, second)
        size = radius if radius is not None else arc_radius(measured)
        canvas.angle_arc(key, vertex, first, second, size, degrees)
        self._labels.append(
            lambda: canvas.angle_label(label, vertex, first, second, size, target=f"angle:{key}")
        )

    def compass(self, key: str, centre: str, through: Sequence[str]) -> None:
        """Draw a short compass arc around each point, centred on ``centre``."""
        canvas = self.canvas
        c = canvas.points[centre]
        radius = length(sub(canvas.points[through[0]], c))
        for index, name in enumerate(through):
            bearing = math.degrees(math.atan2(*reversed(sub(canvas.points[name], c))))
            start = _polar(bearing - COMPASS_SPAN, radius, c)
            end = _polar(bearing + COMPASS_SPAN, radius, c)
            samples = [
                _polar(bearing + COMPASS_SPAN * step / 6, radius, c) for step in range(-6, 7)
            ]
            canvas.raw_path(
                f"M{fmt(start[0])} {fmt(start[1])} A{fmt(radius)} {fmt(radius)} 0 0 1 "
                f"{fmt(end[0])} {fmt(end[1])}",
                [samples],
                stroke=LIGHT,
                width=THIN,
                attrs={"data-arc": f"{key}-{index + 1}"},
            )
            self.arcs[f"{key}-{index + 1}"] = {
                "center": centre,
                "radius": float(fmt(radius)),
                "through": name,
            }

    # ------------------------------------------------------------------------------ labels
    def vertex_label(self, name: str, *, away_from: Point, text: str | None = None) -> None:
        canvas = self.canvas

        def place() -> None:
            p = canvas.points[name]
            shown = text or name
            width, height = canvas.label_size(shown)
            base = math.degrees(math.atan2(*reversed(sub(p, away_from))))
            centres = []
            for gap in (10, 16, 24):
                for turn in (0, -35, 35, -70, 70, -110, 110):
                    d = _polar(base + turn)
                    support = (abs(d[0]) * width + abs(d[1]) * height) / 2
                    centres.append(add(p, scale(d, gap + support)))
            canvas.text(shown, centres, target=f"point:{name}")

        self._labels.append(place)

    def length_label(self, text: str, start: str, end: str, *, away_from: Point) -> None:
        self._labels.append(lambda: self.canvas.segment_label(text, start, end, away_from=away_from))

    def later(self, place: Callable[[], Any]) -> None:
        self._labels.append(place)

    def centre(self, names: Sequence[str]) -> Point:
        points = [self.canvas.points[name] for name in names]
        return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))

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
        words: Sequence[str] = (),
        unknowns: Sequence[tuple[str, str]] = (),
        findings: Sequence[str] = (),
        extra: dict[str, Any] | None = None,
    ) -> Diagram:
        canvas = self.canvas
        for place in self._labels:
            place()
        candidates: list[str] = [*answers, *words]
        for value in derived:
            candidates.extend(decimal_forms(value))
        forbidden, exemptions = withheld_labels(
            candidates, [label["text"] for label in canvas.placed_labels]
        )
        details: dict[str, Any] = dict(extra or {})
        if self.equal_marks:
            details["equal_marks"] = self.equal_marks
        if self.parallel_marks:
            details["parallel_marks"] = self.parallel_marks
        if self.arcs:
            details["arcs"] = self.arcs
        spec = base_spec(
            renderer=self.renderer,
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
            renderer=self.renderer,
            title=title,
            alt_text=f"{alt_text} {NOT_TO_SCALE}",
            spec=spec,
            content_findings=list(findings),
        )


def _measure(canvas: Canvas, vertex: str, first: str, second: str) -> float:
    v = canvas.points[vertex]
    a, b = unit(sub(canvas.points[first], v)), unit(sub(canvas.points[second], v))
    return math.degrees(math.acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1]))))


def _ratio_values(first: float, second: float) -> tuple[float, float, float]:
    k = 180 / (first + second)
    return first * k, second * k, k


def _ratio_labels(first: float, second: float) -> tuple[str, str]:
    return f"{number(first)}k", f"{number(second)}k"


# ------------------------------------------------------------------------- lines at a point
def _line_with_ray(angle: float, *, top: float = 40) -> _Figure:
    figure = _Figure(
        {"L": (-1.3, 0.0), "O": (0.0, 0.0), "R": (1.3, 0.0), "T": _polar(angle, 1.2)},
        max_width=480,
        max_height=220,
        top=top,
    )
    figure.line("L", "R")
    figure.line("O", "T")
    figure.relate("collinear", points=["L", "O", "R"])
    return figure


def straight_line_given(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    given = float(inputs["given"])
    _require(0 < given < 180, "An angle on a straight line must be between 0° and 180°.")
    other = 180 - given
    figure = _line_with_ray(given)
    figure.angle("angle-given", "O", "R", "T", _degree(given), degrees=given, radius=56)
    figure.angle("angle-x", "O", "T", "L", "x", degrees=other, radius=40)
    figure.relate("angle_sum", angles=["angle-given", "angle-x"], value=180)
    return figure.diagram(
        template="straight_line_given",
        inputs=inputs,
        kind="angles_on_line",
        dimensions={"angles": {"given": inputs["given"]}},
        title="Two adjacent angles on a straight line",
        alt_text=(
            "A straight line with one ray from a point on it. The angle to the right of the ray is "
            f"marked {_degree(given)} and the adjacent angle to its left is marked x."
        ),
        answers=answers,
        derived=[other],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(other, answers),
    )


def straight_line_ratio(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second = float(inputs["ratio"][0]), float(inputs["ratio"][1])
    smaller, larger, k = _ratio_values(first, second)
    figure = _line_with_ray(smaller)
    first_label, second_label = _ratio_labels(first, second)
    figure.angle("angle-first", "O", "R", "T", first_label, degrees=round(smaller, 2), radius=56)
    figure.angle("angle-second", "O", "T", "L", second_label, degrees=round(larger, 2), radius=40)
    figure.relate("angle_sum", angles=["angle-first", "angle-second"], value=180)
    return figure.diagram(
        template="straight_line_ratio",
        inputs=inputs,
        kind="angles_on_line",
        dimensions={"ratio": inputs["ratio"], "angle_sum": 180},
        title="Two adjacent angles in a ratio on a straight line",
        alt_text=(
            "A straight line with one ray from a point on it. The two adjacent angles are marked "
            f"{first_label} and {second_label}, where k is the size of one ratio part."
        ),
        answers=answers,
        derived=[smaller, larger, k],
        findings=_key_findings(max(smaller, larger), answers),
    )


def complement_split(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    given = float(inputs["given"])
    _require(0 < given < 90, "A complement needs an acute angle.")
    other = 90 - given
    figure = _Figure(
        {
            "V": (0.0, 0.0),
            "O": (0.0, 0.0),
            "A": (1.0, 0.0),
            "B": (0.0, 1.0),
            "R": _polar(given, 1.0),
        },
        max_width=300,
        max_height=280,
    )
    figure.line("V", "A")
    figure.line("V", "B")
    figure.line("V", "R")
    figure.canvas.right_angle("V", "A", "B", size=20)
    figure.relate("same_point", points=["V", "O"])
    figure.relate("perpendicular", segments=["VA", "VB"])
    figure.angle("angle-given", "O", "A", "R", _degree(given), degrees=given, radius=70)
    figure.angle("angle-x", "O", "R", "B", "x", degrees=other, radius=54)
    figure.relate("angle_sum", angles=["angle-given", "angle-x"], value=90)
    return figure.diagram(
        template="complement_split",
        inputs=inputs,
        kind="right_angle_split",
        dimensions={"angles": {"given": inputs["given"], "whole": 90}},
        title="A right angle split into two angles",
        alt_text=(
            "A right angle, shown with a corner mark, split in two by a ray. One part is "
            f"marked {_degree(given)} and the other part is marked x."
        ),
        answers=answers,
        derived=[other],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(other, answers),
    )


def _crossing(angle: float) -> _Figure:
    figure = _Figure(
        {
            "W": (-1.2, 0.0),
            "E": (1.2, 0.0),
            "O": (0.0, 0.0),
            "P": _polar(angle, 1.2),
            "Q": _polar(angle + 180, 1.2),
        },
        max_width=470,
        max_height=290,
    )
    figure.line("W", "E")
    figure.line("Q", "P")
    figure.relate("collinear", points=["W", "O", "E"])
    figure.relate("collinear", points=["Q", "O", "P"])
    return figure


def intersection_expressions(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    a, b = inputs["first"], inputs["second"]
    slope = a["coefficient"] + b["coefficient"]
    _require(slope != 0, "The two expressions do not determine x.")
    x = (180 - a["constant"] - b["constant"]) / slope
    first, second = a["coefficient"] * x + a["constant"], b["coefficient"] * x + b["constant"]
    _require(0 < first < 180 and 0 < second < 180, "The expressions give impossible angles.")

    def text(item: dict[str, Any]) -> str:
        sign = "−" if item["constant"] < 0 else "+"
        return f"({item['coefficient']}x {sign} {abs(item['constant'])})°"

    first_label, second_label = text(a), text(b)
    figure = _crossing(first)
    figure.angle("angle-1", "O", "E", "P", first_label, degrees=round(first, 2), radius=40)
    figure.angle("angle-2", "O", "P", "W", second_label, degrees=round(second, 2), radius=52)
    figure.angle("angle-3", "O", "W", "Q", first_label, degrees=round(first, 2), radius=40)
    figure.angle("angle-4", "O", "Q", "E", second_label, degrees=round(second, 2), radius=52)
    figure.relate("angle_sum", angles=["angle-1", "angle-2"], value=180)
    return figure.diagram(
        template="intersection_expressions",
        inputs=inputs,
        kind="intersecting_lines",
        dimensions={"expressions": [first_label, second_label]},
        title="Four angles at two crossing lines",
        alt_text=(
            "Two straight lines crossing at a point, with an arc in each of the four angles. Going "
            f"round the point, the angles are marked {first_label}, {second_label}, {first_label} "
            f"and {second_label}."
        ),
        answers=answers,
        derived=[x, first, second],
        words=("2a + 2b", "a + b", "360"),
        findings=_key_findings(x, answers),
    )


def intersection_obtuse(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    obtuse = float(inputs["obtuse"])
    _require(90 < obtuse < 180, "An obtuse angle must be between 90° and 180°.")
    acute = 180 - obtuse
    figure = _crossing(acute)
    figure.angle("angle-a", "O", "E", "P", "a", degrees=acute, radius=52)
    figure.angle("angle-1", "O", "P", "W", _degree(obtuse), degrees=obtuse, radius=36)
    figure.angle("angle-b", "O", "W", "Q", "b", degrees=acute, radius=52)
    figure.angle("angle-2", "O", "Q", "E", _degree(obtuse), degrees=obtuse, radius=36)
    figure.relate("angle_sum", angles=["angle-a", "angle-1"], value=180)
    return figure.diagram(
        template="intersection_obtuse",
        inputs=inputs,
        kind="intersecting_lines",
        dimensions={"angles": {"obtuse": inputs["obtuse"]}},
        title="Obtuse and acute angles at two crossing lines",
        alt_text=(
            f"Two straight lines crossing at a point. Each of the two obtuse angles is marked "
            f"{_degree(obtuse)}. The two acute angles are marked a and b."
        ),
        answers=answers,
        derived=[acute, 2 * acute],
        unknowns=[("angle:angle-a", "a"), ("angle:angle-b", "b")],
        findings=_key_findings(2 * acute, answers),
    )


# -------------------------------------------------------------------------- parallel lines
def _parallels(lowest: float, highest: float, gap: float = 1.0) -> dict[str, Point]:
    return {
        "L1": (lowest, gap),
        "L2": (highest, gap),
        "M1": (lowest, 0.0),
        "M2": (highest, 0.0),
    }


def _one_transversal(angle: float) -> _Figure:
    """Parallel lines cut by one transversal rising to the right at ``angle``."""
    run = 1 / math.tan(math.radians(angle))
    points = {
        **_parallels(-1.15, 1.35 + run),
        "D": (0.0, 0.0),
        "U": (run, 1.0),
        "T1": (-0.32 * run, -0.32),
        "T2": (1.32 * run, 1.32),
    }
    figure = _Figure(points, max_width=470, max_height=320, top=30)
    figure.line("L1", "L2")
    figure.line("M1", "M2")
    figure.line("T1", "T2")
    figure.parallel("L1L2", "M1M2", 0.1)
    figure.relate("collinear", points=["T1", "D", "U", "T2"])
    return figure


def parallel_corresponding(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    given = float(inputs["given"])
    _require(0 < given < 90, "This figure draws an acute given angle.")
    figure = _one_transversal(given)
    figure.angle("angle-given", "U", "L2", "T2", _degree(given), degrees=given)
    figure.angle("angle-x", "D", "M2", "U", "x", degrees=given)
    figure.relate("corresponding_angles", angles=["angle-given", "angle-x"])
    return figure.diagram(
        template="parallel_corresponding",
        inputs=inputs,
        kind="parallel_lines",
        dimensions={"angles": {"given": inputs["given"]}},
        title="Corresponding angles at parallel lines",
        alt_text=(
            "Two parallel horizontal lines, shown with arrow marks, cut by one transversal. At the "
            f"upper line, the angle above the line and to the right of the transversal is marked "
            f"{_degree(given)}. At the lower line, the angle in the same position is marked x."
        ),
        answers=answers,
        derived=[given],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(given, answers),
    )


def parallel_cointerior_ratio(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second = float(inputs["ratio"][0]), float(inputs["ratio"][1])
    lower, upper, k = _ratio_values(first, second)
    _require(lower < 90, "This figure draws the first ratio part as the acute co-interior angle.")
    figure = _one_transversal(lower)
    first_label, second_label = _ratio_labels(first, second)
    figure.angle("angle-first", "D", "M2", "U", first_label, degrees=round(lower, 2))
    figure.angle("angle-second", "U", "D", "L2", second_label, degrees=round(upper, 2))
    figure.relate("angle_sum", angles=["angle-first", "angle-second"], value=180)
    return figure.diagram(
        template="parallel_cointerior_ratio",
        inputs=inputs,
        kind="parallel_lines",
        dimensions={"ratio": inputs["ratio"], "angle_sum": 180},
        title="Co-interior angles in a ratio",
        alt_text=(
            "Two parallel horizontal lines, shown with arrow marks, cut by one transversal. The two "
            f"angles between the lines on the right of the transversal are marked {first_label} at "
            f"the lower line and {second_label} at the upper line, where k is the size of one ratio "
            "part."
        ),
        answers=answers,
        derived=[lower, upper, k],
        findings=_key_findings(max(lower, upper), answers),
    )


def two_transversals_meeting(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    left, right = float(inputs["left_angle"]), float(inputs["right_angle"])
    _require(0 < left < 90 and 0 < right < 90, "Both transversals must make acute angles.")
    between = 180 - left - right
    height, below = 0.68, 0.32
    tan_left, tan_right = math.tan(math.radians(left)), math.tan(math.radians(right))
    top_left, top_right = -height / tan_left, height / tan_right
    low_right, low_left = below / tan_left, -below / tan_right
    gap = height + below
    points = {
        **_parallels(top_left - 0.3, max(top_right, low_right) + 0.3, gap),
        "P": (0.0, below),
        "A": (top_left, gap),
        "B": (top_right, gap),
        "C": (low_right, 0.0),
        "D": (low_left, 0.0),
    }
    figure = _Figure(points, max_width=470, max_height=300, top=30)
    figure.line("L1", "L2")
    figure.line("M1", "M2")
    figure.line("A", "C")
    figure.line("B", "D")
    figure.parallel("L1L2", "M1M2", 0.07)
    figure.relate("collinear", points=["A", "P", "C"])
    figure.relate("collinear", points=["B", "P", "D"])
    figure.angle("angle-left", "A", "B", "P", _degree(left), degrees=left, radius=52)
    figure.angle("angle-right", "B", "A", "P", _degree(right), degrees=right, radius=40)
    figure.angle("angle-x", "P", "A", "B", "x", degrees=between, radius=34)
    figure.canvas.dot("P")
    figure.vertex_label("P", away_from=figure.canvas.points["B"])
    figure.relate("angle_sum", angles=["angle-left", "angle-right", "angle-x"], value=180)
    return figure.diagram(
        template="two_transversals_meeting",
        inputs=inputs,
        kind="parallel_lines",
        dimensions={"angles": {"left": inputs["left_angle"], "right": inputs["right_angle"]}},
        title="Two transversals meeting between parallel lines",
        alt_text=(
            "Two parallel horizontal lines, shown with arrow marks, and two transversals that cross "
            "at point P between them. Going up from P, one transversal reaches the upper line to "
            f"the left, making an angle marked {_degree(left)} with it, and the other reaches it to "
            f"the right, making an angle marked {_degree(right)}. The angle at P between the two "
            "upward rays is marked x."
        ),
        answers=answers,
        derived=[between],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(between, answers),
    )


def perpendicular_transversal(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    given = float(inputs["given"])
    _require(0 < given < 90, "The transversal must make an acute angle with the parallels.")
    other = 90 - given
    height, gap = 0.58, 1.0
    tan_given, tan_other = math.tan(math.radians(given)), math.tan(math.radians(other))
    points = {
        **_parallels(-height / tan_given - 0.42, height / tan_other + (gap - height) / tan_given, gap),
        "P": (0.0, height),
        "A": (-height / tan_given, 0.0),
        "B": (height / tan_other, 0.0),
        "E": ((gap - height) / tan_given, gap),
        "F": (-(gap - height) / tan_other, gap),
    }
    points["L2"] = (points["L2"][0] + 0.3, gap)
    points["M2"] = (points["L2"][0], 0.0)
    figure = _Figure(points, max_width=470, max_height=300, top=30)
    figure.line("L1", "L2")
    figure.line("M1", "M2")
    figure.line("A", "E")
    figure.line("B", "F")
    figure.parallel("L1L2", "M1M2", 0.07)
    figure.relate("collinear", points=["A", "P", "E"])
    figure.relate("collinear", points=["B", "P", "F"])
    figure.relate("perpendicular", segments=["AE", "BF"])
    figure.canvas.right_angle("P", "A", "B", size=20)
    figure.angle("angle-given", "A", "B", "P", _degree(given), degrees=given, radius=58)
    figure.angle("angle-x", "B", "A", "P", "x", degrees=other, radius=46)
    return figure.diagram(
        template="perpendicular_transversal",
        inputs=inputs,
        kind="parallel_lines",
        dimensions={"angles": {"given": inputs["given"]}},
        title="Perpendicular transversals across parallel lines",
        alt_text=(
            "Two parallel horizontal lines, shown with arrow marks, and two transversals that cross "
            "between them at a right angle, shown with a corner mark. At the lower line, one "
            f"transversal makes an angle marked {_degree(given)} and the other makes an angle marked "
            "x."
        ),
        answers=answers,
        derived=[other],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(other, answers),
    )


# ------------------------------------------------------------------------------- triangles
def _triangle(first: float, second: float, **options: Any) -> _Figure:
    """Triangle ABC on a horizontal base with the stated angles at A and B."""
    _require(first > 0 and second > 0 and first + second < 180, "The angles form no triangle.")
    third = 180 - first - second
    side = math.sin(math.radians(second)) / math.sin(math.radians(third))
    figure = _Figure(
        {"A": (0.0, 0.0), "B": (1.0, 0.0), "C": _polar(first, side)},
        **{"max_width": 460, "max_height": 290, **options},
    )
    figure.canvas.polygon(("A", "B", "C"), role="triangle")
    figure.line("A", "B")
    figure.line("B", "C")
    figure.line("A", "C")
    return figure


def triangle_third_angle(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second = float(inputs["angles"][0]), float(inputs["angles"][1])
    figure = _triangle(first, second)
    third = 180 - first - second
    figure.angle("angle-a", "A", "B", "C", _degree(first), degrees=first)
    figure.angle("angle-b", "B", "C", "A", _degree(second), degrees=second)
    figure.angle("angle-x", "C", "A", "B", "x", degrees=third)
    figure.relate("angle_sum", angles=["angle-a", "angle-b", "angle-x"], value=180)
    return figure.diagram(
        template="triangle_third_angle",
        inputs=inputs,
        kind="triangle",
        dimensions={"angles": {"given": inputs["angles"]}},
        title="A triangle with two given angles",
        alt_text=(
            f"A triangle with one base angle marked {_degree(first)}, the other base angle marked "
            f"{_degree(second)} and the top angle marked x."
        ),
        answers=answers,
        derived=[third],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(third, answers),
    )


def triangle_expressions(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    middle, largest = float(inputs["offsets"][0]), float(inputs["offsets"][1])
    x = (180 - middle - largest) / 3
    _require(x > 0, "The expressions give impossible angles.")
    # The widest angle goes at the top, where the widest label has room beside its arc.
    figure = _triangle(x + middle, x, max_height=320)
    middle_label = f"(x + {number(middle)})°"
    largest_label = f"(x + {number(largest)})°"
    figure.angle("angle-2", "A", "B", "C", middle_label, degrees=round(x + middle, 2), radius=56)
    figure.angle("angle-1", "B", "C", "A", "x°", degrees=round(x, 2), radius=66)
    figure.angle("angle-3", "C", "A", "B", largest_label, degrees=round(x + largest, 2), radius=70)
    figure.relate("angle_sum", angles=["angle-1", "angle-2", "angle-3"], value=180)
    return figure.diagram(
        template="triangle_expressions",
        inputs=inputs,
        kind="triangle",
        dimensions={"expressions": ["x°", middle_label, largest_label]},
        title="A triangle with angles written in x",
        alt_text=(
            f"A triangle with its three angles marked x°, {middle_label} and {largest_label}."
        ),
        answers=answers,
        derived=[x, x + middle, x + largest],
        findings=_key_findings(x + largest, answers),
    )


def triangle_angle_sum(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    figure = _triangle(48.0, 68.0)
    figure.angle("angle-a", "A", "B", "C", "a")
    figure.angle("angle-b", "B", "C", "A", "b")
    figure.angle("angle-c", "C", "A", "B", "c")
    figure.relate("angle_sum", angles=["angle-a", "angle-b", "angle-c"], value=180)
    return figure.diagram(
        template="triangle_angle_sum",
        inputs=inputs,
        kind="triangle",
        dimensions={"interior_angles": ["a", "b", "c"]},
        title="A triangle with three marked angles",
        alt_text="A triangle with its three interior angles marked a, b and c.",
        answers=answers,
        derived=[180],
        findings=_key_findings(180, answers),
    )


def isosceles_exterior(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    exterior = float(inputs["exterior"])
    _require(0 < exterior < 180, "An exterior angle must be between 0° and 180°.")
    apex = 180 - exterior
    base = exterior / 2
    half_base = 1.0
    height = half_base * math.tan(math.radians(base))
    side = math.hypot(half_base, height)
    a = (half_base, height)
    beyond = add(a, scale(unit((half_base, height)), side * 0.55))
    figure = _Figure(
        {"B": (0.0, 0.0), "C": (2 * half_base, 0.0), "A": a, "D": beyond},
        max_width=420,
        max_height=300,
    )
    figure.canvas.polygon(("A", "B", "C"), role="triangle")
    figure.line("B", "C")
    figure.line("A", "C")
    figure.line("B", "A")
    figure.line("A", "D", thin=True)
    figure.equal("BA", "AC")
    figure.relate("collinear", points=["B", "A", "D"])
    figure.angle("angle-exterior", "A", "D", "C", _degree(exterior), degrees=exterior, radius=40)
    figure.angle("angle-x", "B", "C", "A", "x", degrees=base)
    figure.angle("angle-y", "C", "A", "B", "x", degrees=base)
    return figure.diagram(
        template="isosceles_exterior",
        inputs=inputs,
        kind="triangle",
        dimensions={"angles": {"exterior_at_apex": inputs["exterior"]}},
        title="An isosceles triangle with an exterior angle at its apex",
        alt_text=(
            "An isosceles triangle with its two equal sides shown by tick marks. One equal side is "
            "extended beyond the apex, and the exterior angle between this extension and the other "
            f"equal side is marked {_degree(exterior)}. Each base angle is marked x."
        ),
        answers=answers,
        derived=[base, apex],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(base, answers),
    )


# ------------------------------------------------------------------- quadrilateral diagonals
def diagonals_equal_bisect(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    crossing = 58.0
    figure = _Figure(
        {
            "O": (0.0, 0.0),
            "A": _polar(180 + crossing / 2),
            "C": _polar(crossing / 2),
            "B": _polar(180 - crossing / 2),
            "D": _polar(-crossing / 2),
        },
        max_width=370,
        max_height=220,
        top=76,
    )
    for end in "ABCD":
        figure.line(end, "O")
        figure.canvas.dot(end, radius=4)
    figure.equal("AO", "CO", "BO", "DO")
    figure.relate("collinear", points=["A", "O", "C"])
    figure.relate("collinear", points=["B", "O", "D"])
    figure.relate("not_perpendicular", segments=["CO", "DO"])
    figure.later(lambda: figure.canvas.caption("Diagonals only; sides not drawn", (300, 36)))
    return figure.diagram(
        template="diagonals_equal_bisect",
        inputs=inputs,
        kind="diagonals",
        dimensions={"diagonals": "equal, bisecting, not perpendicular"},
        title="Two diagonals that bisect each other",
        alt_text=(
            "Only the diagonals of a quadrilateral are shown: two straight line segments crossing "
            "at a slant. Each of the four parts from the crossing point has the same tick mark, so "
            "the segments are equal and bisect each other. The sides are not drawn."
        ),
        answers=answers,
        words=QUADRILATERAL_WORDS,
        extra={"answer_kind": "classification_code", "forbid_right_angle_marker": True},
    )


def diagonals_perpendicular_one_bisected(
    inputs: dict[str, Any], answers: Sequence[str] = ()
) -> Diagram:
    figure = _Figure(
        {
            "O": (0.0, 0.0),
            "A": (0.0, 0.62),
            "C": (0.0, -1.18),
            "B": (-0.78, 0.0),
            "D": (0.78, 0.0),
        },
        max_width=340,
        max_height=270,
        top=76,
    )
    for end in "ABCD":
        figure.line(end, "O")
        figure.canvas.dot(end, radius=4)
    figure.canvas.right_angle("O", "D", "C", size=20)
    figure.equal("BO", "DO")
    figure.relate("collinear", points=["A", "O", "C"])
    figure.relate("collinear", points=["B", "O", "D"])
    figure.relate("perpendicular", segments=["AO", "BO"])
    figure.relate("midpoint", point="O", of=["B", "D"])
    figure.relate("unequal_segments", segments=["AO", "CO"])
    figure.later(lambda: figure.canvas.caption("Diagonals only; sides not drawn", (300, 36)))
    return figure.diagram(
        template="diagonals_perpendicular_one_bisected",
        inputs=inputs,
        kind="diagonals",
        dimensions={"diagonals": "perpendicular, only one bisects the other"},
        title="Perpendicular diagonals, one bisected",
        alt_text=(
            "Only the diagonals of a quadrilateral are shown: two straight line segments crossing "
            "at a right angle, shown with a corner mark. The two parts of the horizontal "
            "segment have the same tick mark. The two parts of the vertical segment have different "
            "lengths. The sides are not drawn."
        ),
        answers=answers,
        words=QUADRILATERAL_WORDS,
        extra={"answer_kind": "classification_code"},
    )


# ----------------------------------------------------------------------------------- kites
def _kite(
    top: float, bottom: float, *, axis_ends: tuple[float, float] | None = None, **options: Any
) -> _Figure:
    """Kite ABCD on a vertical axis, with half-angles ``top`` at A and ``bottom`` at C."""
    axis = 1.0
    apex = 180 - top - bottom
    _require(top > 0 and bottom > 0 and apex > 0, "The kite's angles are impossible.")
    upper = axis * math.sin(math.radians(bottom)) / math.sin(math.radians(apex))
    x = upper * math.sin(math.radians(top))
    y = axis - upper * math.cos(math.radians(top))
    points = {"A": (0.0, axis), "B": (-x, y), "C": (0.0, 0.0), "D": (x, y)}
    if axis_ends:
        points.update({"E": (0.0, axis_ends[0]), "F": (0.0, axis_ends[1])})
    figure = _Figure(points, **{"max_width": 320, "max_height": 310, **options})
    figure.canvas.polygon(("A", "B", "C", "D"), role="kite")
    figure.line("A", "B")
    figure.line("A", "D")
    figure.line("C", "B")
    figure.line("C", "D")
    figure.equal("AB", "AD", ticks=1)
    figure.equal("CB", "CD", ticks=2)
    figure.relate("unequal_segments", segments=["AB", "CB"])
    return figure


def kite_symmetry(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    figure = _kite(32.0, 58.0)
    return figure.diagram(
        template="kite_symmetry",
        inputs=inputs,
        kind="kite",
        dimensions={"sides": "two distinct pairs of adjacent equal sides"},
        title="A kite with its equal sides marked",
        alt_text=(
            "A kite with its upper pair of adjacent equal sides marked with a single tick and its "
            "lower pair of adjacent equal sides marked with double ticks. No diagonals are drawn."
        ),
        answers=answers,
        extra={"forbid_right_angle_marker": True},
    )


def kite_angles(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    a, c = float(inputs["angle_a"]), float(inputs["angle_c"])
    b = (360 - a - c) / 2
    _require(a > 0 and c > 0 and b > 0, "The kite's angles are impossible.")
    # The dashed axis stops short of both vertices, so each whole-angle label sits on the axis.
    figure = _kite(a / 2, c / 2, axis_ends=(0.72, 0.28))
    figure.line("E", "F", hidden=True, thin=True)
    figure.relate("collinear", points=["A", "E", "F", "C"])
    figure.angle("angle-a", "A", "B", "D", _degree(a), degrees=a, radius=44)
    figure.angle("angle-c", "C", "D", "B", _degree(c), degrees=c, radius=36)
    figure.angle("angle-x", "B", "C", "A", "x", degrees=round(b, 2), radius=34)
    centre = figure.centre("ABCD")
    for name in "ABCD":
        figure.vertex_label(name, away_from=centre)
    figure.relate("angle_sum", angles=["angle-a", "angle-c", "angle-x", "angle-x"], value=360)
    return figure.diagram(
        template="kite_angles",
        inputs=inputs,
        kind="kite",
        dimensions={"angles": {"A": inputs["angle_a"], "C": inputs["angle_c"]}},
        title="Kite ABCD",
        alt_text=(
            "Kite ABCD with A at the top, C at the bottom and the symmetry diagonal shown dashed. AB "
            "and AD have a single tick; CB and CD have double ticks. Angle A is marked "
            f"{_degree(a)}, angle C is marked {_degree(c)} and angle B is marked x."
        ),
        answers=answers,
        derived=[b],
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(b, answers),
        extra={"forbid_right_angle_marker": True},
    )


# ------------------------------------------------------------------------- regular polygons
POLYGON_NAMES = {
    4: ("square", "four"),
    5: ("pentagon", "five"),
    6: ("hexagon", "six"),
    7: ("heptagon", "seven"),
    8: ("octagon", "eight"),
    9: ("nonagon", "nine"),
    10: ("decagon", "ten"),
}
NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}


def regular_polygon_exterior(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """A regular polygon split into triangles from one vertex, with one exterior angle marked e."""
    sides = int(inputs["sides"])
    _require(4 <= sides <= 10, "Draw a regular polygon with 4 to 10 sides.")
    exterior = 360 / sides
    names = [f"P{index + 1}" for index in range(sides)]
    points = {
        name: _polar(-90 - exterior / 2 + index * exterior) for index, name in enumerate(names)
    }
    first, second = points[names[0]], points[names[1]]
    points["E"] = add(second, scale(sub(second, first), 0.75))
    figure = _Figure(points, max_width=400, max_height=290)
    figure.canvas.polygon(tuple(names), role="polygon")
    edges = [
        figure.line(names[index], names[(index + 1) % sides]) for index in range(sides)
    ]
    for index in range(2, sides - 1):
        figure.line(names[0], names[index], thin=True)
    figure.line(names[1], "E", thin=True)
    figure.equal(*edges)
    figure.relate("polygon_sides", points=names, count=sides)
    figure.relate("collinear", points=[names[0], names[1], "E"])
    figure.angle("angle-exterior", names[1], "E", names[2], "e", degrees=exterior, radius=34)
    shape, count = POLYGON_NAMES[sides]
    triangles = NUMBER_WORDS[sides - 2]
    return figure.diagram(
        template="regular_polygon_exterior",
        inputs=inputs,
        kind="polygon",
        dimensions={"sides": sides, "regular": True},
        title=f"A regular {shape} with one exterior angle",
        alt_text=(
            f"A regular polygon, a {shape}, with all {count} sides marked equal by tick marks. "
            f"Lines from one vertex divide it into {triangles} triangles. One side is extended "
            "beyond a vertex, and the exterior angle between the extension and the next side is "
            "marked e."
        ),
        answers=answers,
        derived=[exterior, 180 - exterior, (sides - 2) * 180],
        unknowns=[("angle:angle-exterior", "e")],
        findings=_key_findings(exterior, answers),
    )


# --------------------------------------------------------------------------- constructions
def perpendicular_bisector_midpoint(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side = q(inputs["segment"])
    half = 0.5
    rise = math.sqrt(0.72**2 - half**2)
    figure = _Figure(
        {
            "A": (0.0, 0.0),
            "B": (1.0, 0.0),
            "M": (half, 0.0),
            "P": (half, rise),
            "Q": (half, -rise),
            "T": (half, rise + 0.12),
            "S": (half, -rise - 0.12),
        },
        max_width=390,
        max_height=320,
    )
    figure.line("A", "B")
    figure.line("S", "T")
    figure.compass("arc-a", "A", ["P", "Q"])
    figure.compass("arc-b", "B", ["P", "Q"])
    figure.canvas.right_angle("M", "B", "T", size=20)
    figure.relate("midpoint", point="M", of=["A", "B"])
    figure.relate("perpendicular", segments=["AB", "ST"])
    middle = figure.centre("AB")
    for name in ("A", "B"):
        figure.vertex_label(name, away_from=middle)
    figure.vertex_label("M", away_from=figure.canvas.points["A"])
    figure.later(
        lambda: figure.canvas.dimension(
            "d", "A", "M", normal=(0, -1), offset=30, target="segment:AM"
        )
    )
    figure.later(
        lambda: figure.canvas.dimension(
            side.text, "A", "B", normal=(0, 1), offset=44, target="segment:AB"
        )
    )
    half_value = side.value / 2
    return figure.diagram(
        template="perpendicular_bisector_midpoint",
        inputs=inputs,
        kind="construction",
        dimensions={"segment": side.as_spec()},
        title="Perpendicular bisector of a segment",
        alt_text=(
            f"Segment AB marked {side.text}. Equal-radius compass arcs from A and B meet above and "
            "below the segment, and the line through these points crosses AB at M, with a right "
            "angle shown by a corner mark. The distance from A to M is marked d."
        ),
        answers=answers,
        derived=[half_value],
        unknowns=[("segment:AM", "d")],
        findings=_key_findings(half_value, answers),
    )


def safe_radius(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side = q(inputs["segment"])
    # The radius is drawn at a neutral size, well past half the segment and not at the answer.
    rise = math.sqrt(0.78**2 - 0.5**2)
    figure = _Figure(
        {"A": (0.0, 0.0), "B": (1.0, 0.0), "P": (0.5, rise), "Q": (0.5, -rise)},
        max_width=380,
        max_height=300,
    )
    figure.line("A", "B")
    figure.line("A", "P", hidden=True, thin=True)
    figure.line("B", "P", hidden=True, thin=True)
    figure.compass("arc-a", "A", ["P", "Q"])
    figure.compass("arc-b", "B", ["P", "Q"])
    figure.canvas.dot("P", radius=4)
    figure.canvas.dot("Q", radius=4)
    middle = figure.centre("AB")
    for name in ("A", "B"):
        figure.vertex_label(name, away_from=middle)
    figure.length_label(side.text, "A", "B", away_from=figure.canvas.points["P"])
    figure.length_label("r", "A", "P", away_from=figure.canvas.points["B"])
    figure.length_label("r", "B", "P", away_from=figure.canvas.points["A"])
    half_value = side.value / 2
    return figure.diagram(
        template="safe_radius",
        inputs=inputs,
        kind="construction",
        dimensions={"segment": side.as_spec()},
        title="Equal-radius arcs from the ends of a segment",
        alt_text=(
            f"Segment AB marked {side.text}. Compass arcs of equal radius centred at A and B meet "
            "at two points, one above and one below the segment. A dashed radius from each of A "
            "and B to the upper point is marked r."
        ),
        answers=answers,
        derived=[half_value],
        unknowns=[("segment:AP", "r"), ("segment:BP", "r")],
        extra={"neutral_radius_ratio": 0.78},
    )


def equilateral_on_ray(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    figure = _Figure(
        {"A": (0.0, 0.0), "B": (1.0, 0.0), "E": (1.42, 0.0), "C": _polar(60)},
        max_width=430,
        max_height=280,
    )
    figure.canvas.polygon(("A", "B", "C"), role="triangle")
    figure.line("A", "B")
    figure.line("B", "E", thin=True)
    figure.line("B", "C")
    figure.line("A", "C")
    figure.equal("AB", "BC", "AC")
    figure.compass("arc-a", "A", ["C"])
    figure.compass("arc-b", "B", ["C"])
    figure.relate("collinear", points=["A", "B", "E"])
    figure.angle("angle-x", "A", "B", "C", "x", degrees=60)
    centre = figure.centre("ABC")
    for name in "ABC":
        figure.vertex_label(name, away_from=centre)
    return figure.diagram(
        template="equilateral_on_ray",
        inputs=inputs,
        kind="construction",
        dimensions={"sides": "AB = BC = CA"},
        title="Equal-radius arcs on a ray",
        alt_text=(
            "A ray from endpoint A passes through B. Compass arcs of equal radius centred at A and "
            "B meet at C. The sides AB, BC and CA of the triangle have the same tick mark. The "
            "angle at A between the ray and AC is marked x."
        ),
        answers=answers,
        derived=[60],
        words=("sixty",),
        unknowns=[("angle:angle-x", "x")],
        findings=_key_findings(60, answers),
    )


def _sss_apex(ab: float, ac: float, bc: float) -> Point:
    _require(
        ab + ac > bc and ab + bc > ac and ac + bc > ab, "The three lengths form no triangle."
    )
    x = (ab**2 + ac**2 - bc**2) / (2 * ab)
    return (x / ab, math.sqrt(ac**2 - x**2) / ab)


def sss_arc_radius(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    ab, ac, bc = q(inputs["ab"]), q(inputs["ac"]), q(inputs["bc"])
    figure = _Figure(
        {"A": (0.0, 0.0), "B": (1.0, 0.0), "C": _sss_apex(ab.value, ac.value, bc.value)},
        max_width=360,
        max_height=300,
    )
    figure.line("A", "B")
    figure.line("A", "C", hidden=True, thin=True)
    figure.line("B", "C", hidden=True, thin=True)
    figure.compass("arc-a", "A", ["C"])
    figure.compass("arc-b", "B", ["C"])
    figure.canvas.dot("C", radius=4)
    figure.relate("length_ratio", segments=["AB", "AC"], value=round(ab.value / ac.value, 4))
    figure.relate("length_ratio", segments=["AB", "BC"], value=round(ab.value / bc.value, 4))
    centre = figure.centre("ABC")
    for name in "ABC":
        figure.vertex_label(name, away_from=centre)
    figure.length_label(ab.text, "A", "B", away_from=centre)
    figure.length_label(bc.text, "B", "C", away_from=centre)
    figure.length_label("r", "A", "C", away_from=centre)
    return figure.diagram(
        template="sss_arc_radius",
        inputs=inputs,
        kind="construction",
        dimensions={"AB": ab.as_spec(), "BC": bc.as_spec()},
        title="Locating C with two compass arcs",
        alt_text=(
            f"Segment AB marked {ab.text}. A compass arc centred at A and a compass arc centred at "
            f"B meet at C. The dashed line from B to C is marked {bc.text} and the dashed radius "
            "from A to C is marked r."
        ),
        answers=answers,
        derived=[ac.value],
        unknowns=[("segment:AC", "r")],
        findings=_key_findings(ac.value, answers),
    )


def sss_mirror_image(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second, third = (q(item) for item in inputs["sides"])
    apex = _sss_apex(first.value, second.value, third.value)
    figure = _Figure(
        {"A": (0.0, 0.0), "B": (1.0, 0.0), "C": apex, "D": (apex[0], -apex[1])},
        max_width=330,
        max_height=340,
    )
    figure.canvas.polygon(("A", "B", "C"), role="triangle")
    figure.line("A", "B")
    figure.line("A", "C")
    figure.line("B", "C")
    figure.line("A", "D", hidden=True, thin=True)
    figure.line("B", "D", hidden=True, thin=True)
    figure.compass("arc-a", "A", ["C", "D"])
    figure.compass("arc-b", "B", ["C", "D"])
    figure.relate("length_ratio", segments=["AC", "AD"], value=1)
    figure.relate("length_ratio", segments=["BC", "BD"], value=1)
    figure.relate("length_ratio", segments=["AB", "AC"], value=round(first.value / second.value, 4))
    figure.relate("length_ratio", segments=["AB", "BC"], value=round(first.value / third.value, 4))
    centre = figure.centre("AB")
    points = figure.canvas.points
    figure.vertex_label("A", away_from=points["B"])
    figure.vertex_label("B", away_from=points["A"])
    figure.vertex_label("C", away_from=centre)
    figure.vertex_label("D", away_from=centre, text="C′")
    apex_point = points["C"]
    figure.length_label(first.text, "A", "B", away_from=apex_point)
    figure.length_label(second.text, "A", "C", away_from=points["B"])
    figure.length_label(third.text, "B", "C", away_from=points["A"])
    return figure.diagram(
        template="sss_mirror_image",
        inputs=inputs,
        kind="construction",
        dimensions={"sides": [first.as_spec(), second.as_spec(), third.as_spec()]},
        title="Compass arcs meeting on both sides of a segment",
        alt_text=(
            f"Segment AB marked {first.text}. Compass arcs centred at A and B meet at C above the "
            f"segment and at C′ below it. Triangle ABC has AC marked {second.text} and BC marked "
            f"{third.text}. Triangle ABC′, the mirror image in AB, is dashed."
        ),
        answers=answers,
        words=("one triangle", "congruent"),
        extra={"mirror_image": True},
    )


TEMPLATES: dict[str, Callable[..., Diagram]] = {
    function.__name__: function
    for function in (
        straight_line_given,
        straight_line_ratio,
        complement_split,
        intersection_expressions,
        intersection_obtuse,
        parallel_corresponding,
        parallel_cointerior_ratio,
        two_transversals_meeting,
        perpendicular_transversal,
        triangle_third_angle,
        triangle_expressions,
        triangle_angle_sum,
        isosceles_exterior,
        diagonals_equal_bisect,
        diagonals_perpendicular_one_bisected,
        kite_symmetry,
        regular_polygon_exterior,
        kite_angles,
        perpendicular_bisector_midpoint,
        safe_radius,
        equilateral_on_ray,
        sss_arc_radius,
        sss_mirror_image,
    )
}


# ------------------------------------------------------------------------- reading a prompt
NUM = r"(\d+(?:\.\d+)?)"
UNIT = r"\s?(mm|cm|km|m)(?![\w²³])"


def _n(value: str) -> float | int:
    number_value = float(value)
    return int(number_value) if number_value.is_integer() else number_value


def _len(value: str, unit_name: str) -> dict[str, Any]:
    return Quantity(float(value), unit_name).as_spec()


def _expression(coefficient: str, sign: str, constant: str) -> dict[str, int]:
    return {
        "coefficient": int(coefficient),
        "constant": int(constant) * (-1 if sign in {"-", "−"} else 1),
    }


PATTERNS: list[tuple[str, re.Pattern[str], Callable[[re.Match[str]], dict[str, Any]]]] = [
    (
        "straight_line_given",
        re.compile(rf"One of two adjacent angles on a straight line is {NUM}°\. Find the other"),
        lambda m: {"given": _n(m[1])},
    ),
    (
        "straight_line_ratio",
        re.compile(
            r"Two adjacent angles (?:form a straight angle and are|on a straight line are) in the "
            r"ratio (\d+):(\d+)\. Find the larger"
        ),
        lambda m: {"ratio": [int(m[1]), int(m[2])]},
    ),
    (
        "complement_split",
        re.compile(rf"acute angle is {NUM}°\. Find its complement"),
        lambda m: {"given": _n(m[1])},
    ),
    (
        "intersection_expressions",
        re.compile(
            r"two intersecting lines alternate between \((\d+)x ([-+−]) (\d+)\)° and "
            r"\((\d+)x ([-+−]) (\d+)\)°\. Find x"
        ),
        lambda m: {
            "first": _expression(m[1], m[2], m[3]),
            "second": _expression(m[4], m[5], m[6]),
        },
    ),
    (
        "intersection_obtuse",
        re.compile(rf"Two lines intersect\. Each obtuse angle is {NUM}°\. Find the sum of the two"),
        lambda m: {"obtuse": _n(m[1])},
    ),
    (
        "parallel_corresponding",
        re.compile(
            rf"Parallel lines are cut by a transversal\. One angle is {NUM}°\. Find its corresponding"
        ),
        lambda m: {"given": _n(m[1])},
    ),
    (
        "parallel_cointerior_ratio",
        re.compile(
            r"Co-interior angles between parallel lines are in the ratio (\d+):(\d+)\. Find the larger"
        ),
        lambda m: {"ratio": [int(m[1]), int(m[2])]},
    ),
    (
        "two_transversals_meeting",
        re.compile(
            rf"two transversals that meet between them\. One transversal makes an acute angle of {NUM}° "
            rf".*?the other makes an acute angle of {NUM}° on the opposite side"
        ),
        lambda m: {"left_angle": _n(m[1]), "right_angle": _n(m[2])},
    ),
    (
        "perpendicular_transversal",
        re.compile(
            rf"transversal makes an acute angle of {NUM}° with one of two parallel lines\. "
            r"A second transversal is perpendicular to the first"
        ),
        lambda m: {"given": _n(m[1])},
    ),
    (
        "triangle_third_angle",
        re.compile(rf"triangle has angles of {NUM}° and {NUM}°\. Find its third"),
        lambda m: {"angles": [_n(m[1]), _n(m[2])]},
    ),
    (
        "triangle_expressions",
        re.compile(r"angles of a triangle are x°, \(x \+ (\d+)\)° and \(x \+ (\d+)\)°\. Find the largest"),
        lambda m: {"offsets": [int(m[1]), int(m[2])]},
    ),
    (
        "triangle_angle_sum",
        re.compile(r"sum of the interior angles of a triangle"),
        lambda m: {},
    ),
    (
        "isosceles_exterior",
        re.compile(
            rf"exterior angle at the (?:vertex|apex)[^.]*isosceles triangle is {NUM}°\. "
            r"Find either equal base angle"
        ),
        lambda m: {"exterior": _n(m[1])},
    ),
    (
        "diagonals_equal_bisect",
        re.compile(r"diagonals that are equal and bisect each other, but they are not perpendicular"),
        lambda m: {},
    ),
    (
        "diagonals_perpendicular_one_bisected",
        re.compile(r"perpendicular diagonals and only one diagonal bisects the other"),
        lambda m: {},
    ),
    (
        "kite_symmetry",
        re.compile(r"lines of symmetry does a kite with two distinct pairs of adjacent equal sides"),
        lambda m: {},
    ),
    (
        "kite_angles",
        re.compile(
            rf"Kite ABCD has AB = AD and CB = CD\..*angle A = {NUM}° and angle C = {NUM}°, find angle B"
        ),
        lambda m: {"angle_a": _n(m[1]), "angle_c": _n(m[2])},
    ),
    (
        "perpendicular_bisector_midpoint",
        re.compile(rf"perpendicular bisector is constructed for a line segment {NUM}{UNIT} long\. How far"),
        lambda m: {"segment": _len(m[1], m[2])},
    ),
    (
        "safe_radius",
        re.compile(rf"{NUM}{UNIT} segment is to be bisected using equal-radius arcs from its endpoints"),
        lambda m: {"segment": _len(m[1], m[2])},
    ),
    (
        "equilateral_on_ray",
        re.compile(r"Equal-radius arcs construct an equilateral triangle on a ray"),
        lambda m: {},
    ),
    (
        "sss_arc_radius",
        re.compile(
            rf"triangle ABC with AB = {NUM}{UNIT}, AC = {NUM}{UNIT} and BC = {NUM}{UNIT}, an arc centred at A"
        ),
        lambda m: {"ab": _len(m[1], m[2]), "ac": _len(m[3], m[4]), "bc": _len(m[5], m[6])},
    ),
    (
        "sss_mirror_image",
        re.compile(
            rf"three specified side lengths {NUM}{UNIT}, {NUM}{UNIT} and {NUM}{UNIT}\. Ignoring its mirror image"
        ),
        lambda m: {"sides": [_len(m[1], m[2]), _len(m[3], m[4]), _len(m[5], m[6])]},
    ),
]

# An accurate figure of these would show the answer, and an inaccurate one would draw a false
# relationship, so the question stays text-only.
TEXT_ONLY: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"Enter the code for an angle of \d"),
        "Classifying the angle is the task, and an accurate drawing of it shows the class.",
    ),
    (
        re.compile(r"four equal sides and four right angles"),
        "The givens describe only a square, so an accurate figure shows the answer shape.",
    ),
    (
        re.compile(r"parallelogram has four equal sides and equal diagonals"),
        "The givens describe only a square, so an accurate figure shows the answer shape.",
    ),
    (
        re.compile(r"interior-angle sum \d+°\. Find its number of sides"),
        "The number of sides is the answer. An accurate polygon shows it and any other polygon "
        "contradicts the given sum.",
    ),
    (
        re.compile(r"exterior angles of two regular polygons are in the ratio"),
        "The side counts are the answer. Accurate regular polygons show them and any others "
        "contradict the given ratio.",
    ),
    (
        re.compile(r"diagonals drawn from each vertex\. How many sides"),
        "The number of sides is the answer. An accurate polygon shows it and any other polygon "
        "contradicts the given number of diagonals.",
    ),
]


def text_only_reason(prompt: str) -> str | None:
    """Return why this prompt should have no figure, or ``None`` if it can have one."""
    for pattern, reason in TEXT_ONLY:
        if pattern.search(prompt):
            return reason
    return None
