"""Deterministic Sec 2 G2 diagrams (renderer ``nextscholar-similarity-svg-v1``).

Each template reads the givens of one question and draws that question: congruent and similar
figures, nested triangles, shadows, a mirror, a river survey, enlargements and scale drawings.
Figures that the question calls congruent or similar are one set of vertices transformed, so they
cannot drift apart. Corresponding sides carry matching marks, an unknown carries a variable, and
every number shown is stated in the question. A question whose accurate figure would show the
step it assesses is refused (``TEXT_ONLY``).
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from typing import Any

from .canvas import (
    BACKGROUND,
    CAPTION_SIZE,
    FILL,
    FILL_ALT,
    INK,
    LIQUID,
    THIN,
    add,
    fmt,
    scale,
    sub,
    unit,
)
from .common import SIMILARITY_RENDERER, Diagram, number
from .plane_geometry import (
    NUM,
    UNIT,
    _expression,
    _Figure,
    _key_findings,
    _len,
    _n,
    _polar,
    _require,
)
from .right_triangle import q

Point = tuple[float, float]

CODE_REASON = "A response code in the question, not a measurement of the figure."
CLASSIFICATION_WORDS = ("congruent", "same shape", "same size", "similar", "not congruent")
TEST_NAMES = ("SSS", "SAS", "ASA", "RHS", "included")
# A scalene triangle for figures whose shape the question leaves free: A, B, C on a level base.
FREE_TRIANGLE: tuple[Point, Point, Point] = ((0.0, 0.0), (1.0, 0.0), (0.34, 0.68))
# An irregular quadrilateral for "polygons" whose side count the question leaves free.
FREE_POLYGON: tuple[Point, ...] = ((0.0, 0.0), (1.0, 0.0), (1.15, 0.62), (0.35, 0.85))
GRID_COLOUR = "#d5e0df"


def _rotated(points: Sequence[Point], degrees: float, about: Point = (0.0, 0.0)) -> list[Point]:
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    result = []
    for x, y in points:
        dx, dy = x - about[0], y - about[1]
        result.append((about[0] + dx * cosine - dy * sine, about[1] + dx * sine + dy * cosine))
    return result


def _scaled(points: Sequence[Point], factor: float) -> list[Point]:
    return [(x * factor, y * factor) for x, y in points]


def _moved(points: Sequence[Point], x: float, y: float = 0.0) -> list[Point]:
    return [(px + x, py + y) for px, py in points]


def _span(points: Sequence[Point]) -> tuple[float, float, float, float]:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _placed_right_of(points: Sequence[Point], gap_from: float) -> list[Point]:
    """Move a figure so its left edge is at ``gap_from`` and its lowest point at height 0."""
    x0, y0, _, _ = _span(points)
    return _moved(points, gap_from - x0, -y0)


def _triangle_from_sides(ab: float, ac: float, bc: float) -> list[Point]:
    _require(ab + ac > bc and ab + bc > ac and ac + bc > ab, "The lengths form no triangle.")
    x = (ab**2 + ac**2 - bc**2) / (2 * ab)
    return [(0.0, 0.0), (ab, 0.0), (x, math.sqrt(ac**2 - x**2))]


def _cyclic_polygon(sides: Sequence[float]) -> list[Point]:
    """A convex polygon with exactly these sides in order, with its vertices on one circle."""
    longest = max(sides)
    _require(longest < sum(sides) - longest, "The lengths form no polygon.")

    def total(radius: float) -> float:
        return sum(2 * math.asin(min(1.0, side / (2 * radius))) for side in sides) - 2 * math.pi

    low, high = longest / 2 + 1e-9, 1000 * longest
    _require(total(low) > 0, "This figure draws a polygon that encloses its circle's centre.")
    for _ in range(200):
        middle = (low + high) / 2
        if total(middle) > 0:
            low = middle
        else:
            high = middle
    radius = (low + high) / 2
    points, bearing = [], 0.0
    for side in sides:
        points.append((radius * math.cos(bearing), radius * math.sin(bearing)))
        bearing += 2 * math.asin(side / (2 * radius))
    return points


def _solve_equal(first: dict[str, int], second: dict[str, int]) -> float:
    slope = first["coefficient"] - second["coefficient"]
    _require(slope != 0, "The two expressions do not determine x.")
    return (second["constant"] - first["constant"]) / slope


def _text(item: dict[str, int], suffix: str = "") -> str:
    sign = "−" if item["constant"] < 0 else "+"
    coefficient = "" if item["coefficient"] == 1 else item["coefficient"]
    return f"({coefficient}x {sign} {abs(item['constant'])}){suffix}"


class _Scene(_Figure):
    """Adds named figures, scaling arrows and a coordinate grid to the shared figure."""

    renderer = SIMILARITY_RENDERER

    def __init__(self, points: dict[str, Point], **options: Any):
        super().__init__(points, **{"bottom": 110, **options})
        self.figures: dict[str, list[str]] = {}
        self.arrows: list[dict[str, Any]] = []
        self.omitted: list[dict[str, str]] = []
        self.grid: dict[str, Any] | None = None

    def shape(self, name: str, vertices: Sequence[str], *, fill: str = FILL) -> None:
        """Draw a closed figure with one segment per side and record its vertex order."""
        self.canvas.polygon(tuple(vertices), fill=fill, role="figure")
        for index, vertex in enumerate(vertices):
            self.line(vertex, vertices[(index + 1) % len(vertices)])
        self.figures[name] = list(vertices)

    def side(self, first: str, second: str) -> str:
        """Return the key of the drawn side joining two vertices, whichever way it was drawn."""
        keys = self.canvas.segment_keys
        return keys.get((first, second)) or keys[(second, first)]

    def side_label(self, text: str, first: str, second: str, *, away_from: Point) -> None:
        keys = self.canvas.segment_keys
        start, end = (first, second) if (first, second) in keys else (second, first)
        self.length_label(text, start, end, away_from=away_from)

    def corner(self, name: str) -> Point:
        return self.canvas.points[name]

    def caption_at(
        self,
        text: str,
        centre: Callable[[], Sequence[Point]],
        *,
        key: str,
    ) -> None:
        """Place a label from a list of candidate centres, kept inside the canvas."""

        def place() -> None:
            width, _ = self.canvas.label_size(text, CAPTION_SIZE)
            half = width / 2 + 8
            limit = self.canvas.width - half
            spots = [(min(max(x, half), limit), y) for x, y in centre()]
            self.canvas.text(text, spots, target=f"caption:{key}", size=CAPTION_SIZE)

        self.later(place)

    def under(self, text: str, names: Sequence[str], *, key: str, drop: float = 26) -> None:
        """Caption below the lowest point of the named vertices."""

        def spots() -> list[Point]:
            points = [self.corner(name) for name in names]
            x0, _, x1, y1 = _span(points)
            middle = (x0 + x1) / 2
            return [
                (middle + shift, y1 + drop + extra)
                for extra in (0, 12, 26, 40, 56, 72)
                for shift in (0, 30, -30, 60, -60)
            ]

        self.caption_at(text, spots, key=key)

    def above(self, text: str, names: Sequence[str], *, key: str, rise: float = 26) -> None:
        def spots() -> list[Point]:
            points = [self.corner(name) for name in names]
            x0, y0, x1, _ = _span(points)
            middle = (x0 + x1) / 2
            return [
                (middle + shift, y0 - rise - extra)
                for extra in (0, 8, 16, 24)
                for shift in (0, 24, -24, 48, -48)
            ]

        self.caption_at(text, spots, key=key)

    def arrow(
        self,
        key: str,
        tail: str,
        head: str,
        *,
        source: str,
        target: str,
        label: str,
        factor: float | None = None,
    ) -> None:
        """Draw a scaling arrow from one figure towards another, with its label beside it."""
        canvas = self.canvas
        start, tip = canvas.points[tail], canvas.points[head]
        direction = unit(sub(tip, start))
        normal = (-direction[1], direction[0])
        back = add(tip, scale(direction, -14))
        left, right = add(back, scale(normal, 9)), add(back, scale(normal, -9))
        canvas.raw_path(
            f"M{fmt(start[0])} {fmt(start[1])} L{fmt(tip[0])} {fmt(tip[1])} "
            f"M{fmt(left[0])} {fmt(left[1])} L{fmt(tip[0])} {fmt(tip[1])} "
            f"L{fmt(right[0])} {fmt(right[1])}",
            [[start, tip], [left, tip, right]],
            stroke=INK,
            width=THIN,
            attrs={"data-arrow": key},
        )
        record: dict[str, Any] = {"key": key, "from": source, "to": target}
        if factor is not None:
            record["factor"] = factor
        self.arrows.append(record)
        middle = scale(add(start, tip), 0.5)

        def spots() -> list[Point]:
            width, height = canvas.label_size(label, CAPTION_SIZE)
            # Beside a vertical arrow, above a horizontal one.
            if abs(direction[1]) > abs(direction[0]):
                return [
                    add(middle, (side * (width / 2 + gap), 0))
                    for gap in (14, 22, 32)
                    for side in (1, -1)
                ]
            return [
                add(middle, (shift, -(height / 2 + gap)))
                for gap in (12, 20, 30, 42, 56, 72, 90, 110)
                for shift in (0, 10, -10)
            ]

        self.caption_at(label, spots, key=f"arrow-{key}")

    def omit(self, value: str, reason: str) -> None:
        self.omitted.append({"value": value, "reason": reason})

    def omit_codes(self, *values: str) -> None:
        for value in values:
            self.omit(value, CODE_REASON)

    def scene(self, **options: Any) -> Diagram:
        extra = dict(options.pop("extra", None) or {})
        if self.figures:
            extra["figures"] = self.figures
        if self.arrows:
            extra["arrows"] = self.arrows
        if self.omitted:
            extra["omitted_givens"] = self.omitted
        if self.grid:
            extra["grid"] = self.grid
        return self.diagram(extra=extra, **options)


def _named(prefix: str, points: Sequence[Point]) -> dict[str, Point]:
    return {f"{prefix}{index + 1}": point for index, point in enumerate(points)}


def _names(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{index + 1}" for index in range(count)]


def _mean(points: Sequence[Point]) -> Point:
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


# ------------------------------------------------------------------------- congruent figures
def scalene_tiles(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first = [q(item) for item in inputs["first"]]
    second = [q(item) for item in inputs["second"]]
    _require(
        sorted(item.value for item in first) == sorted(item.value for item in second),
        "This figure draws two tiles with the same three lengths.",
    )
    a, b, c = (item.value for item in first)
    # Vertices 1, 2, 3 with side 12 = c (the longest listed last), side 13 = a and side 23 = b.
    tile = _triangle_from_sides(c, a, b)
    x0, _, x1, _ = _span(tile)
    turned = _placed_right_of(_rotated(tile, 200), x1 + 0.5 * (x1 - x0))
    figure = _Scene(
        {**_named("S", tile), **_named("T", turned)}, max_width=400, max_height=230, top=64
    )
    tile_names, turned_names = _names("S", 3), _names("T", 3)
    figure.shape("first", tile_names)
    figure.shape("second", turned_names, fill=FILL_ALT)
    figure.relate("congruent", figures=["first", "second"])
    figure.relate(
        "to_scale",
        lengths=[
            [["S1", "S2"], c],
            [["S1", "S3"], a],
            [["S2", "S3"], b],
            [["T1", "T2"], c],
            [["T1", "T3"], a],
            [["T2", "T3"], b],
        ],
    )
    centre = _mean([figure.corner(name) for name in tile_names])
    other = _mean([figure.corner(name) for name in turned_names])
    sides = {
        round(a, 6): ("1", "3"),
        round(b, 6): ("2", "3"),
        round(c, 6): ("1", "2"),
    }
    for prefix, middle, items in (("S", centre, first), ("T", other, second)):
        for item in items:
            start, end = sides[round(item.value, 6)]
            figure.side_label(item.text, f"{prefix}{start}", f"{prefix}{end}", away_from=middle)
    figure.omit_codes("1", "2", "3")
    return figure.scene(
        template="scalene_tiles",
        inputs=inputs,
        kind="congruent_triangles",
        dimensions={
            "first": [item.as_spec() for item in first],
            "second": [item.as_spec() for item in second],
        },
        title="Two triangular tiles with labelled sides",
        alt_text=(
            f"Two triangles. The sides of the first are marked {first[0].text}, {first[1].text} and "
            f"{first[2].text}. The second triangle is turned, and its sides are marked "
            f"{second[0].text}, {second[1].text} and {second[2].text}."
        ),
        answers=answers,
        words=CLASSIFICATION_WORDS,
        extra={"answer_kind": "classification_code", "forbid_right_angle_marker": True},
    )


def congruent_algebra(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side = q(inputs["pq"])
    expression = inputs["ab"]
    x = (side.value - expression["constant"]) / expression["coefficient"]
    label = f"{_text(expression)} cm"
    base = _scaled(FREE_TRIANGLE, side.value)
    _, _, x1, _ = _span(base)
    # PQR is ABC turned through 180°, so every side keeps its length and its partner.
    copy = _placed_right_of(_rotated(base, 180), x1 + 0.55 * side.value)
    points = {
        "A": base[0],
        "B": base[1],
        "C": base[2],
        "P": copy[0],
        "Q": copy[1],
        "R": copy[2],
    }
    figure = _Scene(points, max_width=500, max_height=230, top=48)
    figure.shape("ABC", "ABC")
    figure.shape("PQR", "PQR", fill=FILL_ALT)
    figure.relate("congruent", figures=["ABC", "PQR"])
    figure.equal("AB", "PQ", ticks=1)
    figure.equal("BC", "QR", ticks=2)
    figure.equal(figure.side("C", "A"), figure.side("R", "P"), ticks=3)
    first = figure.centre("ABC")
    second = figure.centre("PQR")
    for name in "ABC":
        figure.vertex_label(name, away_from=first)
    for name in "PQR":
        figure.vertex_label(name, away_from=second)
    figure.length_label(label, "A", "B", away_from=first)
    figure.length_label(side.text, "P", "Q", away_from=second)
    return figure.scene(
        template="congruent_algebra",
        inputs=inputs,
        kind="congruent_triangles",
        dimensions={"PQ": side.as_spec(), "AB": label},
        title="Congruent triangles ABC and PQR",
        alt_text=(
            f"Two triangles ABC and PQR, with PQR turned upside down. AB is marked {label} and PQ "
            f"is marked {side.text}. AB and PQ have one tick, BC and QR have two ticks, and CA and "
            "RP have three ticks."
        ),
        answers=answers,
        derived=[x],
        findings=_key_findings(x, answers),
        extra={"forbid_right_angle_marker": True},
    )


def congruent_pentagons(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first_side, second_side = inputs["first"], inputs["second"]
    others = [q(item) for item in inputs["others"]]
    x = _solve_equal(first_side, second_side)
    side = first_side["coefficient"] * x + first_side["constant"]
    _require(side > 0, "The expressions give an impossible side.")
    total = side + sum(item.value for item in others)
    lengths = [side, *[item.value for item in others]]
    pentagon = _cyclic_polygon(lengths)
    # Turn the pentagon so that its unknown side lies level along the bottom.
    (ax, ay), (bx, by) = pentagon[0], pentagon[1]
    level = _rotated(pentagon, -math.degrees(math.atan2(by - ay, bx - ax)))
    x0, y0, _, y1 = _span(level)
    level = _moved(level, -x0, -y0)
    height = y1 - y0
    copy = _moved(_rotated(level, 180), 0.0, 0.0)
    cx0, cy0, _, _ = _span(copy)
    copy = _moved(copy, -cx0, -cy0 - height - 0.6 * height)
    pad = {"PadL": (-0.32 * height, 0.0), "PadR": (_span(level)[2] + 0.32 * height, 0.0)}
    figure = _Scene(
        {**_named("V", level), **_named("W", copy), **pad},
        max_width=470,
        max_height=520,
        top=44,
    )
    first_names, second_names = _names("V", 5), _names("W", 5)
    figure.shape("first", first_names)
    figure.shape("second", second_names, fill=FILL_ALT)
    figure.relate("congruent", figures=["first", "second"])
    figure.relate(
        "to_scale",
        lengths=[
            [[first_names[index], first_names[(index + 1) % 5]], length_value]
            for index, length_value in enumerate(lengths)
        ],
    )
    figure.equal("V1V2", "W1W2")
    first_label = f"{_text(first_side)} cm"
    second_label = f"{_text(second_side)} cm"
    first_centre = figure.centre(first_names)
    second_centre = figure.centre(second_names)
    figure.length_label(first_label, "V1", "V2", away_from=first_centre)
    for index, item in enumerate(others, start=2):
        following = index % 5 + 1
        figure.length_label(item.text, f"V{index}", f"V{following}", away_from=first_centre)
    figure.length_label(second_label, "W1", "W2", away_from=second_centre)
    given_text = ", ".join(item.text for item in others[:-1]) + f" and {others[-1].text}"
    return figure.scene(
        template="congruent_pentagons",
        inputs=inputs,
        kind="congruent_pentagons",
        dimensions={
            "first": first_label,
            "second": second_label,
            "others": [item.as_spec() for item in others],
        },
        title="Two congruent pentagons",
        alt_text=(
            f"Two pentagons, the second turned upside down below the first. The sides of the first "
            f"are marked {first_label}, {given_text}. One side of the second is marked "
            f"{second_label}. These two sides correspond, and each has one tick."
        ),
        answers=answers,
        derived=[x, side, total],
        findings=_key_findings(total, answers),
        extra={"forbid_right_angle_marker": True},
    )


def sas_condition(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    # The extra equality is the question, so the included angles are drawn different: 42° and 68°.
    ab, ac = 1.0, 0.8
    first = [(0.0, 0.0), (ab, 0.0), _polar(42, ac)]
    second = _placed_right_of([(0.0, 0.0), (ab, 0.0), _polar(68, ac)], 1.42)
    points = {
        "A": first[0],
        "B": first[1],
        "C": first[2],
        "P": second[0],
        "Q": second[1],
        "R": second[2],
    }
    figure = _Scene(points, max_width=490, max_height=230, top=44)
    figure.shape("ABC", "ABC")
    figure.shape("PQR", "PQR", fill=FILL_ALT)
    figure.relate("correspondence", figures=["ABC", "PQR"])
    figure.equal("AB", "PQ", ticks=1)
    figure.equal(figure.side("C", "A"), figure.side("R", "P"), ticks=2)
    figure.relate("unequal_segments", segments=["BC", "QR"])
    first_centre, second_centre = figure.centre("ABC"), figure.centre("PQR")
    for name in "ABC":
        figure.vertex_label(name, away_from=first_centre)
    for name in "PQR":
        figure.vertex_label(name, away_from=second_centre)
    figure.omit_codes("1", "2", "3", "4")
    return figure.scene(
        template="sas_condition",
        inputs=inputs,
        kind="congruent_triangles",
        dimensions={"sides": "AB = PQ and AC = PR"},
        title="Triangles ABC and PQR with two pairs of equal sides",
        alt_text=(
            "Two triangles ABC and PQR. AB and PQ have one tick, and AC and PR have two ticks. "
            "No angle is marked as equal."
        ),
        answers=answers,
        words=(*TEST_NAMES, "∠A = ∠P"),
        extra={"answer_kind": "classification_code", "forbid_right_angle_marker": True},
    )


def _angle_text(item: dict[str, int]) -> str:
    """Write an angle expression in x, such as (2x + 10)° or 2x°."""
    if item["constant"] == 0:
        coefficient = "" if item["coefficient"] == 1 else item["coefficient"]
        return f"{coefficient}x°"
    return _text(item, "°")


def congruent_angle_expressions(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """Congruent triangles ABC and PQR whose angles A, P and Q are given in x; find angle C.

    The figure shows the correspondence: one arc at A and at P, two arcs at B and at Q. The
    expressions themselves stay in the question (recorded in ``omitted_givens``), because a label
    such as (2x + 10)° does not fit inside the angle beside its arc. Both triangles are drawn with
    their true angles; angle C, the answer, is not labelled.
    """
    a_expr, p_expr, q_expr = inputs["a"], inputs["p"], inputs["q"]
    x = _solve_equal(a_expr, p_expr)
    angle_a = a_expr["coefficient"] * x + a_expr["constant"]
    angle_b = q_expr["coefficient"] * x + q_expr["constant"]
    angle_c = 180 - angle_a - angle_b
    _require(min(angle_a, angle_b, angle_c) > 0, "The expressions give an impossible triangle.")
    ra, rb = math.radians(angle_a), math.radians(angle_b)
    ac = math.sin(rb) / math.sin(ra + rb)
    base = [(0.0, 0.0), (1.0, 0.0), (ac * math.cos(ra), ac * math.sin(ra))]
    _, _, x1, _ = _span(base)
    # PQR is ABC turned through 180°, so every angle keeps its size and its partner.
    copy = _placed_right_of(_rotated(base, 180), x1 + 0.45)
    points = {"A": base[0], "B": base[1], "C": base[2], "P": copy[0], "Q": copy[1], "R": copy[2]}
    figure = _Scene(points, max_width=500, max_height=230, top=48)
    figure.shape("ABC", "ABC")
    figure.shape("PQR", "PQR", fill=FILL_ALT)
    figure.relate("congruent", figures=["ABC", "PQR"])
    canvas = figure.canvas
    canvas.angle_arc("angle-A", "A", "B", "C", 34, round(angle_a, 2))
    canvas.angle_arc("angle-P", "P", "Q", "R", 34, round(angle_a, 2))
    for vertex, first, second in (("B", "C", "A"), ("Q", "R", "P")):
        canvas.angle_arc(f"angle-{vertex}", vertex, first, second, 30, round(angle_b, 2))
        canvas.angle_arc(f"angle-{vertex}2", vertex, first, second, 38, round(angle_b, 2))
    figure.relate("matching_angles", angles=["angle-A", "angle-P"], figures=["ABC", "PQR"])
    figure.relate("matching_angles", angles=["angle-B", "angle-Q"], figures=["ABC", "PQR"])
    first, second = figure.centre("ABC"), figure.centre("PQR")
    for name in "ABC":
        figure.vertex_label(name, away_from=first)
    for name in "PQR":
        figure.vertex_label(name, away_from=second)
    labels = {key: _angle_text(inputs[key]) for key in ("a", "p", "q")}
    reason = "An angle expression stated in the question; the arcs show which angles correspond."
    for key in ("a", "p", "q"):
        for value in (inputs[key]["coefficient"], abs(inputs[key]["constant"])):
            if value and not any(item["value"] == number(value) for item in figure.omitted):
                figure.omit(number(value), reason)
    return figure.scene(
        template="congruent_angle_expressions",
        inputs=inputs,
        kind="congruent_triangles",
        dimensions={"A": labels["a"], "P": labels["p"], "Q": labels["q"]},
        title="Congruent triangles ABC and PQR",
        alt_text=(
            "Two triangles ABC and PQR, with PQR turned upside down. Angles A and P each have one "
            "arc, and angles B and Q each have two arcs."
        ),
        answers=answers,
        derived=[x, angle_a, angle_b, angle_c],
        findings=_key_findings(angle_c, answers),
        extra={"forbid_right_angle_marker": True},
    )


def shared_side(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """Triangles ABC and ADC on either side of their shared side AC.

    With no inputs the sides carry only their equal-length ticks. With ``ab``, ``ad`` and ``dc``
    expressions in x, the congruence AB = AD and BC = DC fixes x, and the figure labels those
    three sides; the perimeter of ABCD is the value withheld.
    """
    points = {"A": (0.0, 1.0), "C": (0.0, -0.72), "B": (-0.74, 0.28), "D": (0.74, 0.28)}
    figure = _Scene(points, max_width=340, max_height=320, top=44)
    figure.canvas.polygon(("A", "B", "C", "D"), role="figure")
    figure.line("A", "B")
    figure.line("A", "D")
    figure.line("B", "C")
    figure.line("D", "C")
    figure.line("A", "C")
    figure.figures = {"ABC": ["A", "B", "C"], "ADC": ["A", "D", "C"]}
    figure.relate("congruent", figures=["ABC", "ADC"])
    figure.equal("AB", "AD", ticks=1)
    figure.equal("BC", "DC", ticks=2)
    centre = figure.centre("ABCD")
    for name in "ABCD":
        figure.vertex_label(name, away_from=centre)
    if "ab" not in inputs:
        figure.omit_codes("1", "2", "3", "4")
        return figure.scene(
            template="shared_side",
            inputs=inputs,
            kind="shared_side",
            dimensions={"sides": "AB = AD and BC = DC, with AC shared"},
            title="Triangles ABC and ADC sharing side AC",
            alt_text=(
                "Two triangles ABC and ADC, on either side of their shared side AC. AB and AD have "
                "one tick, and BC and DC have two ticks."
            ),
            answers=answers,
            words=TEST_NAMES,
            extra={"answer_kind": "classification_code", "forbid_right_angle_marker": True},
        )
    ab, ad, dc = inputs["ab"], inputs["ad"], inputs["dc"]
    x = _solve_equal(ab, ad)
    long_side = ab["coefficient"] * x + ab["constant"]
    short_side = dc["coefficient"] * x + dc["constant"]
    _require(long_side > 0 and short_side > 0, "The expressions give an impossible side.")
    perimeter = 2 * (long_side + short_side)
    labels = {key: f"{_text(inputs[key])} cm" for key in ("ab", "ad", "dc")}
    figure.length_label(labels["ab"], "A", "B", away_from=centre)
    figure.length_label(labels["ad"], "A", "D", away_from=centre)
    figure.length_label(labels["dc"], "D", "C", away_from=centre)
    return figure.scene(
        template="shared_side",
        inputs=inputs,
        kind="shared_side",
        dimensions={"AB": labels["ab"], "AD": labels["ad"], "DC": labels["dc"]},
        title="Congruent triangles ABC and ADC sharing side AC",
        alt_text=(
            f"Two triangles ABC and ADC, on either side of their shared side AC. AB is marked "
            f"{labels['ab']}, AD is marked {labels['ad']} and DC is marked {labels['dc']}. AB and "
            "AD have one tick, and BC and DC have two ticks."
        ),
        answers=answers,
        derived=[x, long_side, short_side, perimeter],
        findings=_key_findings(perimeter, answers),
        extra={"forbid_right_angle_marker": True},
    )


# --------------------------------------------------------------------------- similar figures
def _similar_pair(factor: float, *, gap: float = 0.9, **options: Any) -> tuple[_Scene, Point, Point]:
    base = list(FREE_TRIANGLE)
    image = _placed_right_of(_scaled(base, factor), 1.0 + gap)
    points = {
        **_named("S", base),
        **_named("T", image),
        "Tail": (1.0 + 0.16 * gap, 0.34),
        "Tip": (1.0 + 0.84 * gap, 0.34),
    }
    figure = _Scene(points, **{"max_width": 510, "max_height": 250, "top": 44, **options})
    figure.shape("first", _names("S", 3))
    figure.shape("second", _names("T", 3), fill=FILL_ALT)
    figure.relate("similar", figures=["first", "second"], value=round(factor, 4))
    return figure, figure.centre(_names("S", 3)), figure.centre(_names("T", 3))


def similar_edges(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    small, large = q(inputs["small"]), q(inputs["large"])
    factor = large.value / small.value
    figure, first, second = _similar_pair(factor)
    figure.arrow("scale", "Tail", "Tip", source="first", target="second", label="× k", factor=factor)
    figure.relate("to_scale", lengths=[[["S1", "S2"], small.value], [["T1", "T2"], large.value]])
    figure.length_label(small.text, "S1", "S2", away_from=first)
    figure.length_label(large.text, "T1", "T2", away_from=second)
    return figure.scene(
        template="similar_edges",
        inputs=inputs,
        kind="similar_triangles",
        dimensions={"small": small.as_spec(), "large": large.as_spec()},
        title="A triangle and its similar enlargement",
        alt_text=(
            f"Two similar triangles, with an arrow marked × k from the smaller to the larger. The "
            f"corresponding base edges are marked {small.text} and {large.text}."
        ),
        answers=answers,
        derived=[factor],
        findings=_key_findings(factor, answers),
        extra={"forbid_right_angle_marker": True},
    )


def similar_perimeter(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    perimeter = q(inputs["perimeter"])
    factor = float(inputs["factor"])
    result = perimeter.value * factor
    figure, _, _ = _similar_pair(factor, gap=1.05)
    arrow_label = f"× {number(factor)}"
    figure.arrow(
        "scale", "Tail", "Tip", source="first", target="second", label=arrow_label, factor=factor
    )
    first_label = f"perimeter {perimeter.text}"
    figure.under(first_label, _names("S", 3), key="first")
    figure.under("perimeter p", _names("T", 3), key="second")
    return figure.scene(
        template="similar_perimeter",
        inputs=inputs,
        kind="similar_triangles",
        dimensions={"perimeter": perimeter.as_spec(), "factor": inputs["factor"]},
        title="A triangle enlarged to a similar triangle",
        alt_text=(
            f"Two similar triangles, with an arrow marked {arrow_label} from the smaller to the "
            f"larger. The smaller is marked {first_label} and the larger is marked perimeter p."
        ),
        answers=answers,
        derived=[result],
        unknowns=[("caption:second", "perimeter p")],
        findings=_key_findings(result, answers),
        extra={"forbid_right_angle_marker": True},
    )


def _apex_pair(angle: float, *, factor: float = 1.25, **options: Any) -> _Scene:
    """Two similar triangles with the marked angle at the top of each."""
    half = angle / 2
    base = [(0.0, 0.0), _polar(-90 - half, 1.0), _polar(-90 + half, 0.95)]
    x0, _, x1, _ = _span(base)
    image = _placed_right_of(_scaled(base, factor), x1 - x0 + 0.3)
    base = _placed_right_of(base, 0.0)
    figure = _Scene(
        {**_named("S", base), **_named("T", image)},
        **{"max_width": 530, "max_height": 290, "top": 44, **options},
    )
    figure.shape("first", _names("S", 3))
    figure.shape("second", _names("T", 3), fill=FILL_ALT)
    figure.relate("similar", figures=["first", "second"], value=factor)
    return figure


def similar_angle(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    given = float(inputs["given"])
    _require(0 < given < 120, "This figure draws the angle at the top of a triangle.")
    figure = _apex_pair(given)
    first_label = f"{number(given)}°"
    figure.angle("angle-given", "S1", "S2", "S3", first_label, degrees=given, radius=70)
    figure.angle("angle-x", "T1", "T2", "T3", "x°", degrees=given, radius=87.5)
    figure.relate(
        "matching_angles", angles=["angle-given", "angle-x"], figures=["first", "second"]
    )
    return figure.scene(
        template="similar_angle",
        inputs=inputs,
        kind="similar_triangles",
        dimensions={"angles": {"given": inputs["given"]}},
        title="Corresponding angles of two similar triangles",
        alt_text=(
            f"Two similar triangles in the same position, the second larger. The top angle of the "
            f"first is marked {first_label} and the top angle of the second is marked x°, each with "
            "one arc."
        ),
        answers=answers,
        derived=[given],
        unknowns=[("angle:angle-x", "x°")],
        findings=_key_findings(given, answers),
        extra={"forbid_right_angle_marker": True},
    )


def similar_angle_expressions(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first_side, second_side = inputs["first"], inputs["second"]
    x = _solve_equal(first_side, second_side)
    size = first_side["coefficient"] * x + first_side["constant"]
    _require(0 < size < 120, "This figure draws the angle at the top of a triangle.")
    figure = _apex_pair(size, max_height=320)
    first_label, second_label = _text(first_side, "°"), _text(second_side, "°")
    figure.angle("angle-first", "S1", "S2", "S3", first_label, degrees=round(size, 2), radius=96)
    figure.angle("angle-second", "T1", "T2", "T3", second_label, degrees=round(size, 2), radius=120)
    figure.relate(
        "matching_angles", angles=["angle-first", "angle-second"], figures=["first", "second"]
    )
    return figure.scene(
        template="similar_angle_expressions",
        inputs=inputs,
        kind="similar_triangles",
        dimensions={"expressions": [first_label, second_label]},
        title="Corresponding angles written in x",
        alt_text=(
            f"Two similar triangles in the same position, the second larger. The top angle of the "
            f"first is marked {first_label} and the top angle of the second is marked "
            f"{second_label}, each with one arc."
        ),
        answers=answers,
        derived=[x, size],
        findings=_key_findings(x, answers),
        extra={"forbid_right_angle_marker": True},
    )


def similar_chain(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first_factor = inputs["first_factor"]
    second_factor = inputs["second_factor"]
    k1 = first_factor[0] / first_factor[1]
    k2 = second_factor[0] / second_factor[1]
    net = k1 * k2
    perimeter, area = q(inputs["perimeter"]), q(inputs["area"])
    result = area.value * net**2
    gap = 1.42
    a = list(FREE_POLYGON)
    width = _span(a)[2]
    b = _placed_right_of(_scaled(a, k1), width + gap)
    c_start = width + gap + width * k1 + gap
    c = _placed_right_of(_scaled(a, net), c_start)
    points = {
        **_named("A", a),
        **_named("B", b),
        **_named("C", c),
        "Tail1": (width + 0.14 * gap, 0.28),
        "Tip1": (width + 0.86 * gap, 0.28),
        "Tail2": (width + gap + width * k1 + 0.14 * gap, 0.28),
        "Tip2": (width + gap + width * k1 + 0.86 * gap, 0.28),
    }
    figure = _Scene(points, max_width=540, max_height=200, top=70, bottom=134)
    figure.shape("A", _names("A", 4))
    figure.shape("B", _names("B", 4), fill=FILL_ALT)
    figure.shape("C", _names("C", 4))
    figure.relate("similar", figures=["A", "B"], value=round(k1, 4))
    figure.relate("similar", figures=["B", "C"], value=round(k2, 4))
    first_label = f"× {first_factor[0]}/{first_factor[1]}"
    second_label = f"× {second_factor[0]}/{second_factor[1]}"
    figure.arrow("a-b", "Tail1", "Tip1", source="A", target="B", label=first_label, factor=k1)
    figure.arrow("b-c", "Tail2", "Tip2", source="B", target="C", label=second_label, factor=k2)
    for name in "ABC":
        names = _names(name, 4)
        figure.later(
            lambda name=name, names=names: figure.canvas.text(
                name, [figure.centre(names)], target=f"caption:name-{name}"
            )
        )
    perimeter_label = f"A: perimeter {perimeter.text}"
    area_label = f"A: area {area.text}"
    figure.under(perimeter_label, _names("A", 4), key="perimeter", drop=30)
    figure.under(area_label, _names("A", 4), key="area", drop=64)
    figure.under("C: area y", _names("C", 4), key="unknown", drop=30)
    return figure.scene(
        template="similar_chain",
        inputs=inputs,
        kind="similar_polygons",
        dimensions={
            "factors": [first_factor, second_factor],
            "perimeter": perimeter.as_spec(),
            "area": area.as_spec(),
        },
        title="Three similar polygons A, B and C",
        alt_text=(
            f"Three similar polygons A, B and C in a row, each larger than the last. An arrow marked "
            f"{first_label} runs from A to B and an arrow marked {second_label} runs from B to C. "
            f"Labels read {perimeter_label}, {area_label} and C: area y."
        ),
        answers=answers,
        derived=[net, net**2, result],
        unknowns=[("caption:unknown", "C: area y")],
        findings=_key_findings(result, answers),
        extra={"forbid_right_angle_marker": True},
    )


# ---------------------------------------------------------------------------- nested triangles
def _outward(figure: _Scene, start: str, end: str, opposite: str) -> Point:
    """The unit normal of a side that points away from the opposite vertex."""
    direction = unit(sub(figure.corner(end), figure.corner(start)))
    normal = (-direction[1], direction[0])
    towards = sub(figure.corner(opposite), figure.corner(start))
    if normal[0] * towards[0] + normal[1] * towards[1] > 0:
        return (-normal[0], -normal[1])
    return normal


def nested_parallel(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    ad, ab, de = q(inputs["ad"]), q(inputs["ab"]), q(inputs["de"])
    _require(0 < ad.value < ab.value, "D must lie between A and B.")
    bc = de.value * ab.value / ad.value
    ratio = ad.value / ab.value
    apex = _polar(68, ab.value)
    b, c = (0.0, 0.0), (bc, 0.0)
    points = {
        "A": apex,
        "B": b,
        "C": c,
        "D": add(apex, scale(sub(b, apex), ratio)),
        "E": add(apex, scale(sub(c, apex), ratio)),
        "PadL": (-0.42 * bc, 0.0),
    }
    figure = _Scene(points, max_width=500, max_height=330, top=44, bottom=96)
    figure.canvas.polygon(("A", "B", "C"), role="figure")
    figure.line("A", "B")
    figure.line("A", "C")
    figure.line("B", "C")
    figure.line("D", "E")
    figure.canvas.dot("D", radius=4)
    figure.canvas.dot("E", radius=4)
    figure.figures = {"ADE": ["A", "D", "E"], "ABC": ["A", "B", "C"]}
    figure.relate("similar", figures=["ADE", "ABC"], value=round(1 / ratio, 4))
    figure.relate("collinear", points=["A", "D", "B"])
    figure.relate("collinear", points=["A", "E", "C"])
    figure.relate("parallel", segments=["DE", "BC"])
    figure.relate(
        "to_scale",
        lengths=[
            [["A", "D"], ad.value],
            [["A", "B"], ab.value],
            [["D", "E"], de.value],
            [["B", "C"], bc],
        ],
    )
    figure.parallel("DE", "BC", 0.72)
    centre = figure.centre("ABC")
    outward = _outward(figure, "A", "B", "C")
    # The shorter length goes further out, so the longer one's label fits below its end.
    figure.later(lambda: figure.canvas.dimension(ad.text, "A", "D", normal=outward, offset=100))
    figure.later(lambda: figure.canvas.dimension(ab.text, "A", "B", normal=outward, offset=48))
    for name in "ABC":
        figure.vertex_label(name, away_from=centre)
    figure.vertex_label("D", away_from=figure.corner("E"))
    figure.vertex_label("E", away_from=figure.corner("D"))
    figure.length_label(de.text, "D", "E", away_from=figure.corner("A"))
    figure.length_label("y cm", "B", "C", away_from=centre)
    return figure.scene(
        template="nested_parallel",
        inputs=inputs,
        kind="nested_triangles",
        dimensions={"AD": ad.as_spec(), "AB": ab.as_spec(), "DE": de.as_spec()},
        title="Triangle ABC with DE parallel to BC",
        alt_text=(
            f"Triangle ABC with D on AB and E on AC. DE and BC are parallel, shown with arrow marks. "
            f"AD is marked {ad.text}, the whole of AB is marked {ab.text}, DE is marked {de.text} "
            "and BC is marked y cm."
        ),
        answers=answers,
        derived=[bc, ab.value / ad.value],
        unknowns=[("segment:BC", "y cm")],
        findings=_key_findings(bc, answers),
        extra={"forbid_right_angle_marker": True},
    )


def nested_shared_vertex(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    ab_side, ad_side = inputs["ab"], inputs["ad"]
    bc, de = q(inputs["bc"]), q(inputs["de"])
    # (x + 2)/(2x − 1) = BC/DE, so x comes from cross-multiplying.
    slope = de.value * ab_side["coefficient"] - bc.value * ad_side["coefficient"]
    _require(slope != 0, "The sides do not determine x.")
    x = (bc.value * ad_side["constant"] - de.value * ab_side["constant"]) / slope
    ab = ab_side["coefficient"] * x + ab_side["constant"]
    ad = ad_side["coefficient"] * x + ad_side["constant"]
    _require(0 < ab < ad, "This figure draws B between A and D.")
    ratio = ab / ad
    d, e = (0.0, 0.0), (de.value, 0.0)
    apex = (0.32 * de.value, math.sqrt(ad**2 - (0.32 * de.value) ** 2))
    points = {
        "A": apex,
        "D": d,
        "E": e,
        "B": add(apex, scale(sub(d, apex), ratio)),
        "C": add(apex, scale(sub(e, apex), ratio)),
        "PadL": (-1.15 * de.value, 0.0),
        "PadR": (1.1 * de.value, 0.0),
    }
    figure = _Scene(points, max_width=520, max_height=400, top=44, bottom=90)
    figure.canvas.polygon(("A", "D", "E"), role="figure")
    figure.line("A", "D")
    figure.line("A", "E")
    figure.line("D", "E")
    figure.line("B", "C")
    figure.canvas.dot("B", radius=4)
    figure.canvas.dot("C", radius=4)
    figure.figures = {"ABC": ["A", "B", "C"], "ADE": ["A", "D", "E"]}
    figure.relate("similar", figures=["ABC", "ADE"], value=round(ad / ab, 4))
    figure.relate("collinear", points=["A", "B", "D"])
    figure.relate("collinear", points=["A", "C", "E"])
    figure.relate("parallel", segments=["BC", "DE"])
    figure.relate(
        "to_scale",
        lengths=[
            [["A", "B"], ab],
            [["A", "D"], ad],
            [["B", "C"], bc.value],
            [["D", "E"], de.value],
        ],
    )
    centre = figure.centre("ADE")
    ab_label, ad_label = f"{_text(ab_side)} cm", f"{_text(ad_side)} cm"
    outward = _outward(figure, "A", "D", "E")
    # The shorter length goes further out, so the longer one's label fits below its end.
    figure.later(lambda: figure.canvas.dimension(ab_label, "A", "B", normal=outward, offset=92))
    figure.later(lambda: figure.canvas.dimension(ad_label, "A", "D", normal=outward, offset=44))
    figure.vertex_label("A", away_from=centre)
    figure.vertex_label("D", away_from=centre)
    figure.vertex_label("E", away_from=centre)
    figure.vertex_label("B", away_from=figure.corner("C"))
    figure.vertex_label("C", away_from=figure.corner("B"))
    figure.length_label(bc.text, "B", "C", away_from=figure.corner("A"))
    figure.length_label(de.text, "D", "E", away_from=centre)
    return figure.scene(
        template="nested_shared_vertex",
        inputs=inputs,
        kind="nested_triangles",
        dimensions={"AB": ab_label, "AD": ad_label, "BC": bc.as_spec(), "DE": de.as_spec()},
        title="Similar triangles ABC and ADE sharing vertex A",
        alt_text=(
            f"Triangle ABC inside triangle ADE, sharing vertex A, with B on AD and C on AE. AB is "
            f"marked {ab_label}, the whole of AD is marked {ad_label}, BC is marked {bc.text} and "
            f"DE is marked {de.text}."
        ),
        answers=answers,
        derived=[x, ab, ad],
        findings=_key_findings(x, answers),
        extra={"forbid_right_angle_marker": True},
    )


# ------------------------------------------------------------------------- shadows and sights
def shadow_pair(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    height, shadow = q(inputs["height"]), q(inputs["shadow"])
    extra_shadow = q(inputs["extra_shadow"]) if inputs.get("extra_shadow") else None
    other_shadow = (
        shadow.value + extra_shadow.value if extra_shadow else q(inputs["other_shadow"]).value
    )
    factor = other_shadow / shadow.value
    tall = height.value * factor
    small_name, large_name = inputs["names"]
    if factor <= 6:
        small_left, small_base = 0.0, 0.0
        large_left = shadow.value + max(0.28 * other_shadow, 2.2 * shadow.value)
    else:
        # A very small first figure sits above the second figure's sun ray, at the same scale.
        large_left = 0.0
        small_left, small_base = 0.06 * other_shadow, 0.5 * tall
    points = {
        "S1": (small_left, small_base),
        "F1": (small_left + shadow.value, small_base),
        "T1": (small_left + shadow.value, small_base + height.value),
        "S2": (large_left, 0.0),
        "F2": (large_left + other_shadow, 0.0),
        "T2": (large_left + other_shadow, tall),
        "PadR": (large_left + other_shadow + 0.13 * (large_left + other_shadow), 0.0),
    }
    if extra_shadow:
        points["M2"] = (large_left + other_shadow - shadow.value, 0.0)
    figure = _Scene(points, max_width=500, max_height=330, top=56, bottom=124)
    canvas = figure.canvas
    canvas.polygon(("S1", "F1", "T1"), role="figure")
    canvas.polygon(("S2", "F2", "T2"), fill=FILL_ALT, role="figure")
    figure.line("S1", "F1")
    figure.line("F1", "T1")
    figure.line("S1", "T1", hidden=True, thin=True)
    figure.line("S2", "F2")
    figure.line("F2", "T2")
    figure.line("S2", "T2", hidden=True, thin=True)
    figure.figures = {"first": ["S1", "F1", "T1"], "second": ["S2", "F2", "T2"]}
    figure.relate("similar", figures=["first", "second"], value=round(factor, 4))
    figure.relate(
        "to_scale",
        lengths=[
            [["F1", "T1"], height.value],
            [["S1", "F1"], shadow.value],
            [["S2", "F2"], other_shadow],
            [["F2", "T2"], tall],
        ],
    )
    small_px = math.dist(canvas.points["S1"], canvas.points["F1"])
    small_tall = math.dist(canvas.points["F1"], canvas.points["T1"])
    # Marks shrink with the first figure. One too small to hold them carries none, and then the
    # second carries no arc either, because an arc would have no partner.
    marked = small_tall >= 40
    canvas.right_angle("F2", "S2", "T2", size=16)
    if marked:
        canvas.right_angle("F1", "S1", "T1", size=min(16.0, 0.32 * small_tall))
        canvas.angle_arc("sun-first", "S1", "F1", "T1", min(38.0, 0.5 * small_px))
        canvas.angle_arc("sun-second", "S2", "F2", "T2", 38)
        figure.relate(
            "matching_angles", angles=["sun-first", "sun-second"], figures=["first", "second"]
        )
    figure.length_label(height.text, "F1", "T1", away_from=canvas.points["S1"])
    figure.length_label("h", "F2", "T2", away_from=canvas.points["S2"])
    figure.length_label(shadow.text, "S1", "F1", away_from=canvas.points["T1"])
    if extra_shadow:
        for text, start, end in (
            (extra_shadow.text, "S2", "M2"),
            (shadow.text, "M2", "F2"),
        ):
            figure.later(
                lambda text=text, start=start, end=end: canvas.dimension(
                    text, start, end, normal=(0, 1), offset=18
                )
            )
    else:
        other = q(inputs["other_shadow"])
        figure.length_label(other.text, "S2", "F2", away_from=canvas.points["T2"])
    figure.above(small_name, ["T1"], key="first-name", rise=20)
    figure.above(large_name, ["T2"], key="second-name", rise=20)
    if extra_shadow:
        shadow_words = (
            f"The second shadow is shown in two parts, marked {extra_shadow.text} and {shadow.text}."
        )
    else:
        shadow_words = f"The second shadow is marked {q(inputs['other_shadow']).text}."
    if marked:
        marks = (
            "A right angle is shown with a corner mark at each foot. One arc in each triangle "
            "marks the equal angle of the sun ray with the ground."
        )
    else:
        marks = f"A right angle is shown with a corner mark at the foot of the {large_name}."
    return figure.scene(
        template="shadow_pair",
        inputs=inputs,
        kind="shadow",
        dimensions={
            "height": height.as_spec(),
            "shadow": shadow.as_spec(),
            "other_shadow": other_shadow,
        },
        title=f"Shadows of a {small_name} and a {large_name}",
        alt_text=(
            f"Two triangles, each with an upright, its shadow along level ground and a dashed sun "
            f"ray. The {small_name} is marked {height.text} and its shadow {shadow.text}. The "
            f"{large_name} is marked h. {shadow_words} {marks}"
        ),
        answers=answers,
        derived=[tall, factor, other_shadow],
        unknowns=[("segment:F2T2", "h")],
        findings=_key_findings(tall, answers),
    )


def mirror_method(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    eye, near, far = q(inputs["eye"]), q(inputs["near"]), q(inputs["far"])
    tall = eye.value * far.value / near.value
    points = {
        "F": (0.0, 0.0),
        "E": (0.0, eye.value),
        "M": (near.value, 0.0),
        "B": (near.value + far.value, 0.0),
        "T": (near.value + far.value, tall),
        "PadL": (-0.22 * (near.value + far.value), 0.0),
        "PadR": (1.1 * (near.value + far.value), 0.0),
    }
    figure = _Scene(points, max_width=520, max_height=330, top=56, bottom=104)
    canvas = figure.canvas
    canvas.polygon(("F", "E", "M"), role="figure")
    canvas.polygon(("B", "T", "M"), fill=FILL_ALT, role="figure")
    figure.line("F", "E")
    figure.line("F", "M")
    figure.line("M", "B")
    figure.line("B", "T")
    figure.line("E", "M", hidden=True, thin=True)
    figure.line("M", "T", hidden=True, thin=True)
    canvas.dot("M", radius=5)
    figure.figures = {"student": ["F", "E", "M"], "pole": ["B", "T", "M"]}
    figure.relate("similar", figures=["student", "pole"], value=round(far.value / near.value, 4))
    figure.relate("collinear", points=["F", "M", "B"])
    figure.relate(
        "to_scale",
        lengths=[
            [["F", "E"], eye.value],
            [["F", "M"], near.value],
            [["M", "B"], far.value],
            [["B", "T"], tall],
        ],
    )
    canvas.right_angle("F", "E", "M", size=14)
    canvas.right_angle("B", "M", "T", size=16)
    canvas.angle_arc("mirror-near", "M", "F", "E", 30)
    canvas.angle_arc("mirror-far", "M", "B", "T", 30)
    figure.relate(
        "matching_angles", angles=["mirror-near", "mirror-far"], figures=["student", "pole"]
    )
    figure.length_label(eye.text, "F", "E", away_from=canvas.points["M"])
    figure.length_label("h", "B", "T", away_from=canvas.points["M"])
    figure.length_label(near.text, "F", "M", away_from=canvas.points["E"])
    figure.length_label(far.text, "M", "B", away_from=canvas.points["T"])
    figure.above("eye", ["E"], key="eye", rise=20)
    figure.above("flagpole", ["T"], key="pole", rise=20)
    figure.under("mirror", ["M"], key="mirror", drop=58)
    return figure.scene(
        template="mirror_method",
        inputs=inputs,
        kind="mirror",
        dimensions={"eye": eye.as_spec(), "near": near.as_spec(), "far": far.as_spec()},
        title="Mirror on level ground between a student and a flagpole",
        alt_text=(
            f"A mirror on level ground between a student and a flagpole, with a right angle shown by "
            f"a corner mark at the student's feet and at the foot of the flagpole. The student's eye "
            f"is marked {eye.text} above the ground. Along the ground, the distance from the student "
            f"to the mirror is marked {near.text} and the distance from the mirror to the flagpole "
            f"is marked {far.text}. The flagpole height is marked h. Dashed lines join the eye to "
            "the mirror and the mirror to the top of the flagpole, and one arc on each side of the "
            "mirror marks equal angles."
        ),
        answers=answers,
        derived=[tall, far.value / near.value],
        unknowns=[("segment:BT", "h")],
        findings=_key_findings(tall, answers),
    )


def river_survey(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    small_base, large_base = q(inputs["small_base"]), q(inputs["large_base"])
    offset = q(inputs["offset"])
    width = offset.value * large_base.value / small_base.value
    left = small_base.value + 0.25 * large_base.value
    points = {
        "S1": (0.0, 0.0),
        "S2": (small_base.value, 0.0),
        "S3": (small_base.value, offset.value),
        "T1": (left, 0.0),
        "T2": (left + large_base.value, 0.0),
        "T3": (left + large_base.value, width),
        "BankA": (left - 0.03 * large_base.value, 0.0),
        "BankB": (left + 1.08 * large_base.value, 0.0),
        "BankC": (left + 1.08 * large_base.value, width),
        "BankD": (left - 0.03 * large_base.value, width),
    }
    figure = _Scene(points, max_width=540, max_height=270, top=44, bottom=100)
    canvas = figure.canvas
    canvas.fill([canvas.points[name] for name in ("BankA", "BankB", "BankC", "BankD")], LIQUID)
    figure.shape("first", _names("S", 3))
    figure.shape("second", _names("T", 3), fill=FILL_ALT)
    figure.relate("similar", figures=["first", "second"], value=large_base.value / small_base.value)
    figure.relate(
        "to_scale",
        lengths=[
            [["S1", "S2"], small_base.value],
            [["S2", "S3"], offset.value],
            [["T1", "T2"], large_base.value],
            [["T2", "T3"], width],
        ],
    )
    canvas.angle_arc("base-first", "S1", "S2", "S3", 30)
    canvas.angle_arc("base-second", "T1", "T2", "T3", 30)
    figure.relate(
        "matching_angles", angles=["base-first", "base-second"], figures=["first", "second"]
    )
    first, second = figure.centre(_names("S", 3)), figure.centre(_names("T", 3))
    figure.length_label(small_base.text, "S1", "S2", away_from=first)
    figure.length_label(offset.text, "S2", "S3", away_from=first)
    figure.length_label(large_base.text, "T1", "T2", away_from=second)
    figure.length_label("w", "T2", "T3", away_from=second)

    def river_spots() -> list[Point]:
        top_left = canvas.points["BankD"]
        return [(top_left[0] + 58 + shift, top_left[1] + 28) for shift in (0, 12, 24)]

    figure.caption_at("river", river_spots, key="river")
    return figure.scene(
        template="river_survey",
        inputs=inputs,
        kind="survey",
        dimensions={
            "small_base": small_base.as_spec(),
            "large_base": large_base.as_spec(),
            "offset": offset.as_spec(),
        },
        title="Similar survey triangles across a river",
        alt_text=(
            f"Two similar triangles with their bases level. The smaller has a baseline marked "
            f"{small_base.text} and an offset marked {offset.text}. The larger lies across a shaded "
            f"river, with a baseline marked {large_base.text} along one bank, and its corresponding "
            "side across the river is marked w. One arc in each triangle marks the equal angles at "
            "the left end of the baselines."
        ),
        answers=answers,
        derived=[width, large_base.value / small_base.value],
        unknowns=[("segment:T2T3", "w")],
        findings=_key_findings(width, answers),
        extra={"forbid_right_angle_marker": True},
    )


# ------------------------------------------------------------------------------- enlargements
def _coordinate_scene(
    x_range: tuple[int, int],
    y_range: tuple[int, int],
    given: dict[str, tuple[float, float]],
    *,
    extra_points: dict[str, Point] | None = None,
) -> _Scene:
    """Axes and a unit grid. Only coordinates that the question states are numbered."""
    corners = {
        "GridA": (float(x_range[0]), float(y_range[0])),
        "GridB": (float(x_range[1]), float(y_range[1])),
        "O": (0.0, 0.0),
        "UnitX": (1.0, 0.0),
        "XEnd": (x_range[1] + 0.5, 0.0),
        "XStart": (x_range[0] - 0.3, 0.0),
        "YEnd": (0.0, y_range[1] + 0.5),
        "YStart": (0.0, y_range[0] - 0.3),
    }
    figure = _Scene(
        {**corners, **given, **(extra_points or {})},
        max_width=500,
        max_height=500,
        top=72,
        bottom=56,
    )
    canvas = figure.canvas
    origin, step = canvas.points["O"], canvas.points["UnitX"][0] - canvas.points["O"][0]
    low, high = canvas.points["GridA"], canvas.points["GridB"]
    for value in range(x_range[0], x_range[1] + 1):
        x = origin[0] + value * step
        canvas.figure.append(
            f'<rect data-grid="x:{value}" x="{fmt(x - 0.75)}" y="{fmt(high[1])}" width="1.5" '
            f'height="{fmt(low[1] - high[1])}" fill="{GRID_COLOUR}"/>'
        )
    for value in range(y_range[0], y_range[1] + 1):
        y = origin[1] - value * step
        canvas.figure.append(
            f'<rect data-grid="y:{value}" x="{fmt(low[0])}" y="{fmt(y - 0.75)}" '
            f'width="{fmt(high[0] - low[0])}" height="1.5" fill="{GRID_COLOUR}"/>'
        )
    figure.line("XStart", "XEnd", thin=True)
    figure.line("YStart", "YEnd", thin=True)
    figure.grid = {
        "origin": "O",
        "unit": float(fmt(step)),
        "x": list(x_range),
        "y": list(y_range),
        "points": {name: list(value) for name, value in given.items()},
        "ticks": {"x": [], "y": []},
    }
    return figure


def _plated_text(figure: _Scene, text: str, spots: Sequence[Point], target: str) -> None:
    """Place a label with a plate behind it, so the grid lines do not run through its letters."""
    canvas = figure.canvas
    canvas.text(text, spots, target=target)
    box = canvas.text_boxes[-1]
    canvas.figure.append(
        f'<rect data-role="label-plate" x="{fmt(box.x0 - 2)}" y="{fmt(box.y0 - 1)}" '
        f'width="{fmt(box.width + 4)}" height="{fmt(box.height + 2)}" fill="{BACKGROUND}"/>'
    )


def _signed(value: float) -> str:
    return f"−{number(abs(value))}" if value < 0 else number(value)


def _tick(figure: _Scene, axis: str, value: int) -> None:
    figure.grid["ticks"][axis].append(value)
    canvas = figure.canvas

    def place() -> None:
        origin = canvas.points["O"]
        step = figure.grid["unit"]
        text = _signed(value)
        width, height = canvas.label_size(text)
        if axis == "x":
            x = origin[0] + value * step
            spots = [(x, origin[1] + height / 2 + gap) for gap in (6, 12, 20, 30)]
            spots += [(x, origin[1] - height / 2 - gap) for gap in (6, 12, 20, 30)]
        else:
            y = origin[1] - value * step
            spots = [(origin[0] - width / 2 - gap, y) for gap in (6, 12, 20, 30)]
            spots += [(origin[0] + width / 2 + gap, y) for gap in (6, 12, 20, 30)]
        _plated_text(figure, text, spots, f"tick:{axis}:{value}")

    figure.later(place)


def _point_label(figure: _Scene, name: str, text: str, directions: Sequence[Point]) -> None:
    canvas = figure.canvas

    def place() -> None:
        p = canvas.points[name]
        width, height = canvas.label_size(text)
        spots = []
        for gap in (10, 16, 24):
            for d in directions:
                direction = unit(d)
                support = (abs(direction[0]) * width + abs(direction[1]) * height) / 2
                spots.append(add(p, scale(direction, gap + support)))
        _plated_text(figure, text, spots, f"point:{name}")

    figure.later(place)


def _axis_names(figure: _Scene) -> None:
    canvas = figure.canvas

    def place() -> None:
        x_end, y_end, origin = canvas.points["XEnd"], canvas.points["YEnd"], canvas.points["O"]
        _plated_text(figure, "x", [(x_end[0] + 20, x_end[1] + d) for d in (0, 16, -16)], "axis:x")
        _plated_text(figure, "y", [(y_end[0] + d, y_end[1] - 22) for d in (0, 16, -16)], "axis:y")
        _plated_text(
            figure,
            "O",
            [add(origin, (dx, dy)) for dx, dy in ((-24, 22), (24, 22), (-24, -22), (24, -22))],
            "point:O",
        )

    figure.later(place)


def _factor_caption(figure: _Scene, text: str) -> None:
    def spots() -> list[Point]:
        return [(x, 34.0) for x in (300.0, 420.0, 180.0, 480.0, 120.0)]

    figure.caption_at(text, spots, key="factor")


def origin_point_ray(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    x, y = inputs["point"]
    factor = float(inputs["factor"])
    image = (x * factor, y * factor)
    reach = max(image) + 2
    end = (x * reach / max(x, y), y * reach / max(x, y))
    figure = _coordinate_scene(
        (-1, math.ceil(end[0]) + 1),
        (-1, math.ceil(end[1])),
        {"A": (float(x), float(y))},
        extra_points={"RayEnd": end, "FootX": (float(x), 0.0), "FootY": (0.0, float(y))},
    )
    figure.line("O", "RayEnd", thin=True)
    figure.line("A", "FootX", hidden=True, thin=True)
    figure.line("A", "FootY", hidden=True, thin=True)
    figure.canvas.dot("A")
    figure.relate("collinear", points=["O", "A", "RayEnd"])
    _tick(figure, "x", int(x))
    _tick(figure, "y", int(y))
    _axis_names(figure)
    point_text = f"A({number(x)}, {number(y)})"
    _point_label(figure, "A", point_text, [(1, 0.2), (1, -0.4), (1, 0.8), (-1, 0.5)])
    factor_text = f"scale factor {number(factor)}"
    _factor_caption(figure, factor_text)
    return figure.scene(
        template="origin_point_ray",
        inputs=inputs,
        kind="coordinate_grid",
        dimensions={"point": inputs["point"], "factor": inputs["factor"]},
        title="A point on a ray from the origin",
        alt_text=(
            f"Coordinate axes x and y with a unit grid and origin O. Point {point_text} is plotted, with "
            f"dashed lines to each axis. A straight ray runs from O through A and beyond. The image "
            f"point is not plotted. A caption reads {factor_text}."
        ),
        answers=answers,
        derived=[image[0], image[1]],
        words=(f"({number(image[0])}, {number(image[1])})",),
        findings=_key_findings(image[0], answers),
        extra={"forbid_right_angle_marker": True},
    )


def centre_unknown_line(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    ax, ay = inputs["point"]
    bx, by = inputs["image"]
    factor = float(inputs["factor"])
    _require(factor != 1, "A factor of 1 has no single centre.")
    cx, cy = (bx - factor * ax) / (1 - factor), (by - factor * ay) / (1 - factor)
    x_low = min(0, math.floor(cx)) - 3
    y_low = min(0, math.floor(cy)) - 3
    x_high, y_high = max(0, math.ceil(bx)) + 1, max(0, math.ceil(by)) + 1
    # The line runs on past A, so its end does not show where the centre is.
    run = (cx - ax, cy - ay)
    start = (cx + 0.5 * run[0], cy + 0.5 * run[1])
    figure = _coordinate_scene(
        (x_low, x_high),
        (y_low, y_high),
        {"A": (float(ax), float(ay)), "A′": (float(bx), float(by))},
        extra_points={"LineStart": start, "LineEnd": (float(bx), float(by))},
    )
    figure.line("LineStart", "LineEnd", thin=True)
    figure.canvas.dot("A")
    figure.canvas.dot("A′")
    figure.relate("collinear", points=["LineStart", "A", "A′"])
    for value in (ax, bx):
        _tick(figure, "x", int(value))
    for value in (ay, by):
        _tick(figure, "y", int(value))
    _axis_names(figure)
    first_text = f"A({number(ax)}, {number(ay)})"
    second_text = f"A′({number(bx)}, {number(by)})"
    _point_label(figure, "A", first_text, [(1, -0.5), (1, 0), (1, 0.6)])
    _point_label(figure, "A′", second_text, [(-1, 0.3), (-1, -0.3), (-1, 0.8)])
    factor_text = f"scale factor {number(factor)}"
    _factor_caption(figure, factor_text)
    total = cx + cy
    return figure.scene(
        template="centre_unknown_line",
        inputs=inputs,
        kind="coordinate_grid",
        dimensions={"A": inputs["point"], "A′": inputs["image"], "factor": inputs["factor"]},
        title="A point and its image on a line",
        alt_text=(
            f"Coordinate axes x and y with a unit grid and origin O. Points {first_text} and {second_text} "
            f"are plotted on one straight line, which continues past A. The centre of enlargement "
            f"is not plotted. A caption reads {factor_text}."
        ),
        answers=answers,
        derived=[abs(cx), abs(cy), abs(total)],
        words=(_signed(cx), _signed(cy), _signed(total), f"({_signed(cx)}, {_signed(cy)})"),
        findings=_key_findings(total, answers),
        extra={"forbid_right_angle_marker": True},
    )


def centre_given_ray(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    cx, cy = inputs["centre"]
    ax, ay = inputs["point"]
    numerator, denominator = inputs["factor"]
    factor = numerator / denominator
    image = (cx + factor * (ax - cx), cy + factor * (ay - cy))
    total = image[0] + image[1]
    figure = _coordinate_scene(
        (min(0, ax) - 2, max(0, cx) + 2),
        (min(0, cy) - 2, max(0, ay) + 1),
        {"C": (float(cx), float(cy)), "A": (float(ax), float(ay))},
    )
    figure.line("C", "A", thin=True)
    figure.canvas.dot("C")
    figure.canvas.dot("A")
    _tick(figure, "x", int(ax))
    _tick(figure, "x", int(cx))
    _tick(figure, "y", int(ay))
    _tick(figure, "y", int(cy))
    _axis_names(figure)
    centre_text = f"C({_signed(cx)}, {_signed(cy)})"
    point_text = f"A({_signed(ax)}, {_signed(ay)})"
    _point_label(figure, "C", centre_text, [(-1, -0.3), (-1, 0.3), (0, 1), (0, -1)])
    _point_label(figure, "A", point_text, [(0, -1), (1, -0.4), (-1, 0)])
    factor_text = f"scale factor {numerator}/{denominator}"
    _factor_caption(figure, factor_text)
    return figure.scene(
        template="centre_given_ray",
        inputs=inputs,
        kind="coordinate_grid",
        dimensions={"C": inputs["centre"], "A": inputs["point"], "factor": inputs["factor"]},
        title="A centre of enlargement and a point",
        alt_text=(
            f"Coordinate axes x and y with a unit grid and origin O. The centre {centre_text} and the point "
            f"{point_text} are plotted and joined by a straight line. The image point is not "
            f"plotted. A caption reads {factor_text}."
        ),
        answers=answers,
        derived=[abs(image[0]), abs(image[1]), abs(total)],
        words=(_signed(image[0]), _signed(total), f"({_signed(image[0])}, {_signed(image[1])})"),
        findings=_key_findings(total, answers),
        extra={"forbid_right_angle_marker": True},
    )


def enlargement_line(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    distance = q(inputs["distance"])
    factor = float(inputs["factor"])
    _require(factor > 1, "This figure draws an enlargement along a line.")
    result = distance.value * factor
    points = {"O": (0.0, 0.0), "A": (distance.value, 0.0), "A′": (result, 0.0)}
    figure = _Scene(points, max_width=470, max_height=100, top=120, bottom=120)
    figure.line("O", "A")
    figure.line("A", "A′")
    for name in ("O", "A", "A′"):
        figure.canvas.dot(name)
    figure.relate("collinear", points=["O", "A", "A′"])
    figure.relate("enlargement", centre="O", pairs=[["A", "A′"]], value=factor)
    for name in ("O", "A", "A′"):
        figure.later(
            lambda name=name: figure.canvas.text(
                name,
                [add(figure.corner(name), (0, -30)), add(figure.corner(name), (0, -40))],
                target=f"point:{name}",
            )
        )
    figure.length_label(distance.text, "O", "A", away_from=(figure.corner("A")[0], 900))
    figure.later(
        lambda: figure.canvas.dimension("d", "O", "A′", normal=(0, 1), offset=40, target="segment:OA′")
    )
    factor_text = f"scale factor {number(factor)}"
    _factor_caption(figure, factor_text)
    return figure.scene(
        template="enlargement_line",
        inputs=inputs,
        kind="enlargement_line",
        dimensions={"OA": distance.as_spec(), "factor": inputs["factor"]},
        title="A point and its image on a line from O",
        alt_text=(
            f"A straight line from the centre O through A to its image A′. OA is marked "
            f"{distance.text} and the whole distance OA′ is marked d. A caption reads {factor_text}."
        ),
        answers=answers,
        derived=[result],
        unknowns=[("segment:OA′", "d")],
        findings=_key_findings(result, answers),
        extra={"forbid_right_angle_marker": True},
    )


# ------------------------------------------------------------------------------ scale drawings
def scale_segments(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length = q(inputs["length"])
    factor = float(inputs["factor"])
    result = length.value * factor
    first_name, second_name = inputs["names"]
    row = 0.42 * result
    points = {
        "D1": (0.0, row),
        "D2": (length.value, row),
        "T1": (0.0, 0.0),
        "T2": (result, 0.0),
        "Tail": (0.5 * length.value, 0.72 * row),
        "Tip": (0.5 * length.value, 0.2 * row),
    }
    figure = _Scene(points, max_width=470, max_height=200, top=70, bottom=100)
    figure.line("D1", "D2")
    figure.line("T1", "T2")
    figure.relate("length_ratio", segments=["T1T2", "D1D2"], value=factor)
    figure.relate("to_scale", lengths=[[["D1", "D2"], length.value], [["T1", "T2"], result]])
    canvas = figure.canvas
    # The figures here are single lengths, so the arrow joins the two segments directly.
    start, tip = canvas.points["Tail"], canvas.points["Tip"]
    arrow_label = f"× {number(factor)}"
    direction = unit(sub(tip, start))
    back = add(tip, scale(direction, -14))
    normal = (-direction[1], direction[0])
    left, right = add(back, scale(normal, 9)), add(back, scale(normal, -9))
    canvas.raw_path(
        f"M{fmt(start[0])} {fmt(start[1])} L{fmt(tip[0])} {fmt(tip[1])} M{fmt(left[0])} "
        f"{fmt(left[1])} L{fmt(tip[0])} {fmt(tip[1])} L{fmt(right[0])} {fmt(right[1])}",
        [[start, tip], [left, tip, right]],
        stroke=INK,
        width=THIN,
        attrs={"data-role": "scale-arrow"},
    )
    width, _ = canvas.label_size(arrow_label, CAPTION_SIZE)
    middle = scale(add(start, tip), 0.5)
    figure.later(
        lambda: canvas.text(
            arrow_label,
            [add(middle, (width / 2 + gap, 0)) for gap in (14, 22, 32)],
            target="caption:factor",
            size=CAPTION_SIZE,
        )
    )
    far = (300.0, 2000.0)
    figure.length_label(length.text, "D1", "D2", away_from=far)
    figure.length_label("y", "T1", "T2", away_from=(300.0, -2000.0))

    def first_spots() -> list[Point]:
        end = canvas.points["D2"]
        width_first, _ = canvas.label_size(first_name, CAPTION_SIZE)
        return [(end[0] + width_first / 2 + gap, end[1]) for gap in (20, 28, 36)]

    figure.caption_at(first_name, first_spots, key="first")

    def second_spots() -> list[Point]:
        end = canvas.points["T2"]
        return [(end[0] - 120 + shift, end[1] - 26) for shift in (0, 20, 40)]

    figure.caption_at(second_name, second_spots, key="second")
    return figure.scene(
        template="scale_segments",
        inputs=inputs,
        kind="scale_segments",
        dimensions={"length": length.as_spec(), "factor": inputs["factor"]},
        title="A length and its enlargement",
        alt_text=(
            f"Two straight segments, one above the other. The upper, labelled {first_name}, is "
            f"marked {length.text}. An arrow marked {arrow_label} points down to the lower, longer "
            f"segment, labelled {second_name}, which is marked y."
        ),
        answers=answers,
        derived=[result],
        unknowns=[("segment:T1T2", "y")],
        findings=_key_findings(result, answers),
        extra={"forbid_right_angle_marker": True},
    )


def _rectangle(prefix: str, x: float, y: float, width: float, height: float) -> dict[str, Point]:
    return {
        f"{prefix}1": (x, y),
        f"{prefix}2": (x + width, y),
        f"{prefix}3": (x + width, y + height),
        f"{prefix}4": (x, y + height),
    }


def scale_model(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    long_side, short_side = q(inputs["length"]), q(inputs["width"])
    ratio = inputs["scale"]
    to_centimetres = {"m": 100, "cm": 1}[long_side.unit]
    perimeter = 2 * (long_side.value + short_side.value) * to_centimetres / ratio
    model_size = 0.42
    model_w, model_h = long_side.value * model_size, short_side.value * model_size
    model_x = (long_side.value - model_w) / 2
    arrow_x = long_side.value / 2
    gap = 0.34 * long_side.value
    points = {
        **_rectangle("G", 0.0, model_h + gap, long_side.value, short_side.value),
        **_rectangle("M", model_x, 0.0, model_w, model_h),
        "Tail": (arrow_x, model_h + 0.9 * gap),
        "Tip": (arrow_x, model_h + 0.1 * gap),
        "PadL": (-0.3 * long_side.value, 0.0),
        "PadR": (1.3 * long_side.value, 0.0),
    }
    figure = _Scene(points, max_width=540, max_height=370, top=56, bottom=74)
    figure.shape("garden", _names("G", 4))
    figure.shape("model", _names("M", 4), fill=FILL_ALT)
    # 1 : 300 cannot be drawn on one screen, so only the shape is kept and the note says so.
    figure.relate("similar", figures=["garden", "model"], value=model_size)
    ratio_text = f"1 : {number(ratio)}"
    figure.arrow("scale", "Tail", "Tip", source="garden", target="model", label=ratio_text)
    centre = figure.centre(_names("G", 4))
    figure.side_label(long_side.text, "G3", "G4", away_from=centre)
    figure.side_label(short_side.text, "G4", "G1", away_from=centre)
    figure.later(
        lambda: figure.canvas.text(
            "garden", [figure.centre(_names("G", 4))], target="caption:garden", size=CAPTION_SIZE
        )
    )

    def model_name() -> list[Point]:
        return [figure.centre(_names("M", 4))]

    figure.caption_at("model", model_name, key="model")
    figure.under("perimeter p", _names("M", 4), key="unknown", drop=22)
    return figure.scene(
        template="scale_model",
        inputs=inputs,
        kind="scale_rectangles",
        dimensions={
            "length": long_side.as_spec(),
            "width": short_side.as_spec(),
            "scale": ratio_text,
        },
        title="A rectangular garden and its model",
        alt_text=(
            f"A rectangle labelled garden, marked {long_side.text} and {short_side.text}. An arrow "
            f"marked {ratio_text} points down to a smaller similar rectangle labelled model. The "
            "sides of the model are not marked, and it is marked perimeter p."
        ),
        answers=answers,
        derived=[
            perimeter,
            perimeter / 2,
            long_side.value * to_centimetres / ratio,
            short_side.value * to_centimetres / ratio,
        ],
        unknowns=[("caption:unknown", "perimeter p")],
        findings=_key_findings(perimeter, answers),
        extra={"forbid_right_angle_marker": True},
    )


def scale_plan_stage(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    long_side, short_side = q(inputs["length"]), q(inputs["width"])
    ratio = inputs["scale"]
    numerator, denominator = inputs["factor"]
    factor = numerator / denominator
    aspect = short_side.value / long_side.value
    plan_w, yard_w = 8.0, 20.0
    stage_w = yard_w * factor
    gap = 4.4
    stage_h, yard_h, plan_h = stage_w * aspect, yard_w * aspect, plan_w * aspect
    yard_y = stage_h + gap
    plan_y = yard_y + yard_h + gap
    middle = yard_w / 2
    points = {
        **_rectangle("P", middle - plan_w / 2, plan_y, plan_w, plan_h),
        **_rectangle("Y", 0.0, yard_y, yard_w, yard_h),
        **_rectangle("S", middle - stage_w / 2, 0.0, stage_w, stage_h),
        "Tail1": (middle, plan_y - 0.1 * gap),
        "Tip1": (middle, yard_y + yard_h + 0.1 * gap),
        "Tail2": (middle, yard_y - 0.1 * gap),
        "Tip2": (middle, stage_h + 0.1 * gap),
        "PadL": (-5.0, 0.0),
        "PadR": (yard_w + 5.0, 0.0),
    }
    figure = _Scene(points, max_width=540, max_height=500, top=56, bottom=74)
    figure.shape("plan", _names("P", 4))
    figure.shape("courtyard", _names("Y", 4), fill=FILL_ALT)
    figure.shape("stage", _names("S", 4))
    # 1 : 400 cannot be drawn on one screen, so the plan keeps only the shape.
    figure.relate("similar", figures=["plan", "courtyard"], value=round(yard_w / plan_w, 4))
    figure.relate("similar", figures=["courtyard", "stage"], value=round(factor, 4))
    ratio_text = f"1 : {number(ratio)}"
    factor_text = f"× {numerator}/{denominator}"
    figure.arrow("plan", "Tail1", "Tip1", source="plan", target="courtyard", label=ratio_text)
    figure.arrow(
        "stage", "Tail2", "Tip2", source="courtyard", target="stage", label=factor_text, factor=factor
    )
    centre = figure.centre(_names("P", 4))
    figure.side_label(long_side.text, "P3", "P4", away_from=centre)
    figure.side_label(short_side.text, "P4", "P1", away_from=centre)
    for name, names in (("plan", "P"), ("courtyard", "Y"), ("stage", "S")):
        figure.later(
            lambda name=name, names=names: figure.canvas.text(
                name,
                [figure.centre(_names(names, 4))],
                target=f"caption:{name}",
                size=CAPTION_SIZE,
            )
        )
    figure.under("area s", _names("S", 4), key="unknown", drop=22)
    area_scale = (long_side.value * ratio / 100) * (short_side.value * ratio / 100) * factor**2
    return figure.scene(
        template="scale_plan_stage",
        inputs=inputs,
        kind="scale_rectangles",
        dimensions={
            "plan": [long_side.as_spec(), short_side.as_spec()],
            "scale": ratio_text,
            "factor": inputs["factor"],
        },
        title="A plan, a courtyard and a stage",
        alt_text=(
            f"Three similar rectangles, one above another. The rectangle labelled plan is marked "
            f"{long_side.text} and {short_side.text}. An arrow marked {ratio_text} points down to a "
            f"rectangle labelled courtyard, whose sides are not marked. An arrow marked {factor_text} "
            "points down to a smaller rectangle labelled stage, marked area s."
        ),
        answers=answers,
        derived=[
            area_scale,
            long_side.value * ratio / 100,
            short_side.value * ratio / 100,
            long_side.value * ratio / 100 * factor,
            short_side.value * ratio / 100 * factor,
        ],
        unknowns=[("caption:unknown", "area s")],
        findings=_key_findings(area_scale, answers),
        extra={"forbid_right_angle_marker": True},
    )


TEMPLATES: dict[str, Callable[..., Diagram]] = {
    function.__name__: function
    for function in (
        scalene_tiles,
        congruent_algebra,
        congruent_pentagons,
        sas_condition,
        shared_side,
        congruent_angle_expressions,
        similar_edges,
        similar_perimeter,
        similar_angle,
        similar_angle_expressions,
        similar_chain,
        nested_parallel,
        nested_shared_vertex,
        shadow_pair,
        mirror_method,
        river_survey,
        origin_point_ray,
        centre_unknown_line,
        centre_given_ray,
        enlargement_line,
        scale_segments,
        scale_model,
        scale_plan_stage,
    )
}


# ------------------------------------------------------------------------- reading a prompt
MINUS = r"[-−]"
SIGNED = rf"({MINUS}?\d+)"


def _i(value: str) -> int:
    return int(value.replace("−", "-"))


PATTERNS: list[tuple[str, re.Pattern[str], Callable[[re.Match[str]], dict[str, Any]]]] = [
    (
        "scalene_tiles",
        re.compile(
            rf"triangular tile has side lengths {NUM}{UNIT}, {NUM}{UNIT} and {NUM}{UNIT}\. A second "
            rf"tile has side lengths {NUM}{UNIT}, {NUM}{UNIT} and {NUM}{UNIT}\. Use code 1 for congruent"
        ),
        lambda m: {
            "first": [_len(m[1], m[2]), _len(m[3], m[4]), _len(m[5], m[6])],
            "second": [_len(m[7], m[8]), _len(m[9], m[10]), _len(m[11], m[12])],
        },
    ),
    (
        "congruent_algebra",
        re.compile(
            rf"Triangles ABC and PQR are congruent with AB corresponding to PQ\. If AB = "
            rf"\((\d+)x ([-+−]) (\d+)\) cm and PQ = {NUM}{UNIT}, find x"
        ),
        lambda m: {"ab": _expression(m[1], m[2], m[3]), "pq": _len(m[4], m[5])},
    ),
    (
        "congruent_pentagons",
        re.compile(
            rf"congruent pentagons have corresponding sides \((\d+)x ([-+−]) (\d+)\) cm and "
            rf"\((\d+)x ([-+−]) (\d+)\) cm\. One pentagon has side lengths \(\d+x [-+−] \d+\) cm, "
            rf"{NUM}{UNIT}, {NUM}{UNIT}, {NUM}{UNIT} and {NUM}{UNIT}\. Find its perimeter"
        ),
        lambda m: {
            "first": _expression(m[1], m[2], m[3]),
            "second": _expression(m[4], m[5], m[6]),
            "others": [_len(m[7], m[8]), _len(m[9], m[10]), _len(m[11], m[12]), _len(m[13], m[14])],
        },
    ),
    (
        "sas_condition",
        re.compile(r"Triangles ABC and PQR have AB = PQ and AC = PR\. Which extra equality"),
        lambda m: {},
    ),
    (
        "shared_side",
        re.compile(r"Triangles ABC and ADC share side AC\. Also AB = AD and BC = DC\."),
        lambda m: {},
    ),
    (
        "similar_edges",
        re.compile(
            rf"has a {NUM}{UNIT} edge\. Its similar enlargement has a corresponding {NUM}{UNIT} edge\. "
            r"Find the enlargement scale factor"
        ),
        lambda m: {"small": _len(m[1], m[2]), "large": _len(m[3], m[4])},
    ),
    (
        "similar_perimeter",
        re.compile(
            rf"triangle with perimeter {NUM}{UNIT} is enlarged by scale factor {NUM} to form a similar "
            r"triangle\. Find the new perimeter"
        ),
        lambda m: {"perimeter": _len(m[1], m[2]), "factor": _n(m[3])},
    ),
    (
        "similar_angle",
        re.compile(rf"pair of similar triangles, a {NUM}° acute angle corresponds to angle x°"),
        lambda m: {"given": _n(m[1])},
    ),
    (
        "similar_angle_expressions",
        re.compile(
            r"Similar triangles have corresponding angles \((\d+)x ([-+−]) (\d+)\)° and "
            r"\((\d+)x ([-+−]) (\d+)\)°\. Find x"
        ),
        lambda m: {"first": _expression(m[1], m[2], m[3]), "second": _expression(m[4], m[5], m[6])},
    ),
    (
        "similar_chain",
        re.compile(
            rf"Three similar polygons A, B and C have scale factor (\d+)/(\d+) from A to B and "
            rf"(\d+)/(\d+) from B to C\. Polygon A has perimeter {NUM}{UNIT} and area {NUM}\s?(cm²)"
        ),
        lambda m: {
            "first_factor": [int(m[1]), int(m[2])],
            "second_factor": [int(m[3]), int(m[4])],
            "perimeter": _len(m[5], m[6]),
            "area": {"value": _n(m[7]), "unit": m[8]},
        },
    ),
    (
        "nested_parallel",
        re.compile(
            rf"D lies on AB and E lies on AC with DE parallel to BC\. If AD = {NUM}{UNIT}, "
            rf"AB = {NUM}{UNIT} and DE = {NUM}{UNIT}, find BC"
        ),
        lambda m: {"ad": _len(m[1], m[2]), "ab": _len(m[3], m[4]), "de": _len(m[5], m[6])},
    ),
    (
        "nested_shared_vertex",
        re.compile(
            rf"Triangles ABC and ADE are similar, with AB corresponding to AD and BC corresponding "
            rf"to DE\. AB = \((\d*)x ([-+−]) (\d+)\) cm, AD = \((\d*)x ([-+−]) (\d+)\) cm, "
            rf"BC = {NUM}{UNIT} and DE = {NUM}{UNIT}\. Find x"
        ),
        lambda m: {
            "ab": _expression(m[1] or "1", m[2], m[3]),
            "ad": _expression(m[4] or "1", m[5], m[6]),
            "bc": _len(m[7], m[8]),
            "de": _len(m[9], m[10]),
        },
    ),
    (
        "shadow_pair",
        re.compile(
            rf"a {NUM}{UNIT} pole casts a {NUM}{UNIT} shadow and a tree casts a {NUM}{UNIT} shadow\. "
            r"Find the tree height"
        ),
        lambda m: {
            "height": _len(m[1], m[2]),
            "shadow": _len(m[3], m[4]),
            "other_shadow": _len(m[5], m[6]),
            "names": ["pole", "tree"],
        },
    ),
    (
        "shadow_pair",
        re.compile(
            rf"A {NUM}{UNIT} stick casts a {NUM}{UNIT} shadow\. A building casts a {NUM}{UNIT} shadow "
            r"at the same time\. Find the building height"
        ),
        lambda m: {
            "height": _len(m[1], m[2]),
            "shadow": _len(m[3], m[4]),
            "other_shadow": _len(m[5], m[6]),
            "names": ["stick", "building"],
        },
    ),
    (
        "shadow_pair",
        re.compile(
            rf"A {NUM}{UNIT} pole casts a {NUM}{UNIT} shadow\. A taller pole casts a shadow {NUM}{UNIT} "
            r"longer than the first\. Find the taller pole's height"
        ),
        lambda m: {
            "height": _len(m[1], m[2]),
            "shadow": _len(m[3], m[4]),
            "extra_shadow": _len(m[5], m[6]),
            "names": ["pole", "taller pole"],
        },
    ),
    (
        "mirror_method",
        re.compile(
            rf"mirror method forms similar triangles\. A student's eye is {NUM}{UNIT} above the ground "
            rf"and {NUM}{UNIT} from the mirror\. The mirror is {NUM}{UNIT} from a flagpole"
        ),
        lambda m: {"eye": _len(m[1], m[2]), "near": _len(m[3], m[4]), "far": _len(m[5], m[6])},
    ),
    (
        "river_survey",
        re.compile(
            rf"survey diagram uses similar triangles\. A {NUM}{UNIT} baseline corresponds to a "
            rf"{NUM}{UNIT} baseline, while a {NUM}{UNIT} offset corresponds to the river width"
        ),
        lambda m: {
            "small_base": _len(m[1], m[2]),
            "large_base": _len(m[3], m[4]),
            "offset": _len(m[5], m[6]),
        },
    ),
    (
        "origin_point_ray",
        re.compile(
            r"at A = \((\d+), (\d+)\) is enlarged from the origin by factor (\d+)\. "
            r"Find the x-coordinate of its image"
        ),
        lambda m: {"point": [int(m[1]), int(m[2])], "factor": int(m[3])},
    ),
    (
        "centre_unknown_line",
        re.compile(
            r"enlargement maps A = \((\d+), (\d+)\) to A′ = \((\d+), (\d+)\) with scale factor (\d+)\. "
            r"The centre is C = \(h, k\)\. Find h \+ k"
        ),
        lambda m: {
            "point": [int(m[1]), int(m[2])],
            "image": [int(m[3]), int(m[4])],
            "factor": int(m[5]),
        },
    ),
    (
        "centre_given_ray",
        re.compile(
            rf"enlargement has centre C = \({SIGNED}, {SIGNED}\), scale factor (\d+)/(\d+) and maps "
            rf"A = \({SIGNED}, {SIGNED}\) to A′\. Find the sum of the coordinates of A′"
        ),
        lambda m: {
            "centre": [_i(m[1]), _i(m[2])],
            "factor": [int(m[3]), int(m[4])],
            "point": [_i(m[5]), _i(m[6])],
        },
    ),
    (
        "enlargement_line",
        re.compile(
            rf"enlargement with centre O and scale factor {NUM}, point A is {NUM}{UNIT} from O\. "
            r"Find the distance OA′"
        ),
        lambda m: {"factor": _n(m[1]), "distance": _len(m[2], m[3])},
    ),
    (
        "scale_segments",
        re.compile(
            rf"toy car is enlarged from a {NUM}{UNIT} design segment using scale factor {NUM}\. "
            r"Find the matching toy length"
        ),
        lambda m: {"length": _len(m[1], m[2]), "factor": _n(m[3]), "names": ["design", "toy"]},
    ),
    (
        "scale_model",
        re.compile(
            rf"rectangular garden is {NUM}{UNIT} by {NUM}{UNIT}\. A model uses scale 1:(\d+)\. "
            r"Find the model perimeter in centimetres"
        ),
        lambda m: {"length": _len(m[1], m[2]), "width": _len(m[3], m[4]), "scale": int(m[5])},
    ),
    (
        "scale_plan_stage",
        re.compile(
            rf"represented on a plan by a {NUM}{UNIT} by {NUM}{UNIT} rectangle at scale 1:(\d+)\. A "
            r"similar rectangular stage is built with linear dimensions equal to (\d+)/(\d+) of"
        ),
        lambda m: {
            "length": _len(m[1], m[2]),
            "width": _len(m[3], m[4]),
            "scale": int(m[5]),
            "factor": [int(m[6]), int(m[7])],
        },
    ),
]

# An accurate figure of these would show the step that is assessed, and an inaccurate one would
# draw a false relationship, so the question stays text-only.
TEXT_ONLY: list[tuple[re.Pattern[str], str]] = [
    (
        # The factors may be typed as text or set as inline maths, which leaves only spaces here.
        re.compile(
            r"enlarged by scale factor\s+(?:3/2\s+)?and then reduced by scale factor"
            r"(?:\s+2/3)?\s*\.\s*The resulting triangle is enlarged again"
        ),
        "An accurate chain draws the second reduction back at the original size, which shows the "
        "cancelling step this item assesses. Any other sizes would draw false factors.",
    ),
]


def text_only_reason(prompt: str) -> str | None:
    """Return why this prompt should have no figure, or ``None`` if it can have one."""
    for pattern, reason in TEXT_ONLY:
        if pattern.search(prompt):
            return reason
    return None
