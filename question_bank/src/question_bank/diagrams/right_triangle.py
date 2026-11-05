"""Deterministic right-triangle diagrams (renderer ``nextscholar-right-triangle-svg-v2``).

Every coordinate is computed from the question's givens. Angle arcs are centred on the acute
vertex they describe and drawn at the stated size, a right-angle mark is drawn only where the
right angle is a given, and the value a learner must find is never printed: the unknown side or
angle carries its variable instead.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from typing import Any

from .canvas import ACCENT, CAPTION_SIZE, LIGHT, THIN, WIDTH, Canvas
from .common import (
    RIGHT_TRIANGLE_RENDERER,
    Diagram,
    Quantity,
    UnsupportedDiagram,
    base_spec,
    decimal_forms,
    finish,
    join_values,
    layout,
    number,
    withheld_labels,
)

ANGLE_RADIUS = 46
MAX_LEG_RATIO = 4.5
CONVERSE_TASKS = frozenset({"converse_test", "perimeter_verify"})
# Questions that get no figure: every accurate figure shows the answer, and any other figure draws
# a false shape. Founder decision D6 B makes these text-only.
TEXT_ONLY: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"side lengths .* Enter 1 if it is right-angled and 0 if it is not"),
        "Text-only under founder decision D6 B: a triangle drawn from these three sides shows "
        "whether it is right-angled, which is the answer, and any other triangle would be a false "
        "figure.",
    ),
)


def text_only_reason(prompt: str) -> str | None:
    """Return why a question should have no figure, or ``None`` if it can have one."""
    for pattern, reason in TEXT_ONLY:
        if pattern.search(prompt):
            return reason
    return None


def q(value: dict[str, Any] | Quantity) -> Quantity:
    if isinstance(value, Quantity):
        return value
    return Quantity(float(value["value"]), value.get("unit"))


def _degree(value: float) -> str:
    return f"{number(value)}°"


def arc_radius(degrees: float) -> float:
    """Use a wider arc for narrow angles so the label fits inside the angle beside it."""
    if degrees >= 30:
        return ANGLE_RADIUS
    return round(min(110.0, ANGLE_RADIUS * 30 / degrees), 1)


def _clamped_ratio(vertical: float, horizontal: float) -> tuple[float, bool]:
    ratio = vertical / horizontal
    clamped = min(MAX_LEG_RATIO, max(1 / MAX_LEG_RATIO, ratio))
    return clamped, not math.isclose(clamped, ratio)


def _right_triangle_canvas(
    vertical: float,
    horizontal: float,
    *,
    bottom: float = 120,
    max_width: float = 360,
    note: bool = True,
):
    model = [(0.0, 0.0), (0.0, vertical), (horizontal, 0.0)]
    canvas, transform = layout(
        model, max_width=max_width, max_height=290, top=56, bottom=bottom, note=note
    )
    a = canvas.point("A", transform(model[0]))
    canvas.point("B", transform(model[1]))
    canvas.point("C", transform(model[2]))
    return canvas, a


def _centroid(canvas: Canvas, names: Sequence[str]) -> tuple[float, float]:
    points = [canvas.points[name] for name in names]
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def _draw_triangle(canvas: Canvas, names: Sequence[str] = ("A", "B", "C")) -> None:
    canvas.polygon(names, role="triangle")
    a, b, c = names
    canvas.segment(f"{a}{b}", a, b)
    canvas.segment(f"{a}{c}", a, c)
    canvas.segment(f"{b}{c}", b, c)


def _forbid(
    answers: Sequence[str], derived: Sequence[float], extra: Sequence[str], canvas: Canvas
) -> tuple[list[str], list[dict[str, str]]]:
    candidates: list[str] = [*answers]
    for value in derived:
        candidates.extend(decimal_forms(value))
    candidates.extend(extra)
    visible = [label["text"] for label in canvas.placed_labels]
    return withheld_labels(candidates, visible)


def _spec(
    canvas,
    template,
    inputs,
    task,
    dimensions,
    forbidden,
    exemptions,
    unknowns,
    *,
    relationships=None,
    extra=None,
):
    return base_spec(
        renderer=RIGHT_TRIANGLE_RENDERER,
        diagram_kind="right_triangle",
        template=template,
        inputs=inputs,
        dimensions=dimensions,
        canvas=canvas,
        forbidden=forbidden,
        exemptions=exemptions,
        unknowns=unknowns,
        relationships=relationships,
        extra={"task": task, **(extra or {})},
    )


def _check_answer(expected: float, answers: Sequence[str], places: int | None) -> list[str]:
    numeric = []
    for answer in answers:
        try:
            numeric.append(float(answer))
        except ValueError:
            continue
    if not numeric:
        return []
    target = round(expected, places) if places is not None else expected
    if any(math.isclose(value, target, abs_tol=0.051 if places else 1e-6) for value in numeric):
        return []
    shown = number(round(expected, places)) if places is not None else number(expected)
    return [
        f"The canonical answer {answers[0]} does not match the value recomputed from the "
        f"prompt ({shown}). Correct the answer key in the question, not the diagram."
    ]


def _ratio_relation(first: str, second: str, value: float) -> dict[str, Any]:
    return {
        "type": "length_ratio",
        "segments": [first, second],
        "value": round(value, 4),
        "tolerance": 0.02,
    }


# --------------------------------------------------------------------------- right triangles
def _legs_figure(
    *,
    template: str,
    inputs: dict[str, Any],
    task: str,
    vertical: Quantity,
    horizontal: Quantity,
    vertical_label: str,
    horizontal_label: str,
    hypotenuse_label: str | None,
    unknown: tuple[str, str] | None,
    angle: tuple[float, str] | None,
    answers: Sequence[str],
    derived: Sequence[float],
    alt_text: str,
    title: str,
    findings: list[str],
    dimensions: dict[str, Any],
    clamp: bool = True,
) -> Diagram:
    ratio, clamped = (
        _clamped_ratio(vertical.value, horizontal.value)
        if clamp
        else (vertical.value / horizontal.value, False)
    )
    canvas, _ = _right_triangle_canvas(ratio, 1.0)
    _draw_triangle(canvas)
    canvas.right_angle("A", "B", "C")
    inside = _centroid(canvas, "ABC")
    relationships: list[dict[str, Any]] = []
    if angle is not None:
        degrees, label = angle
        radius = arc_radius(degrees)
        canvas.angle_arc("angle-C", "C", "A", "B", radius, round(degrees, 2))
        canvas.angle_label(label, "C", "A", "B", radius)
    canvas.segment_label(vertical_label, "A", "B", away_from=inside)
    canvas.segment_label(horizontal_label, "A", "C", away_from=inside)
    if hypotenuse_label:
        canvas.segment_label(hypotenuse_label, "B", "C", away_from=inside)
    if not clamped:
        relationships.append(_ratio_relation("AB", "AC", vertical.value / horizontal.value))
    forbidden, exemptions = _forbid(answers, derived, [], canvas)
    unknowns = [{"target": unknown[0], "label": unknown[1]}] if unknown else []
    spec = _spec(
        canvas,
        template,
        inputs,
        task,
        dimensions,
        forbidden,
        exemptions,
        unknowns,
        relationships=relationships,
        extra={"drawn_to_scale": not clamped},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title=title,
        alt_text=alt_text,
        spec=spec,
        content_findings=findings,
    )


def find_hypotenuse(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second = (q(item) for item in inputs["legs"])
    hypotenuse = math.hypot(first.value, second.value)
    return _legs_figure(
        template="find_hypotenuse",
        inputs=inputs,
        task="find_hypotenuse",
        vertical=first,
        horizontal=second,
        vertical_label=first.text,
        horizontal_label=second.text,
        hypotenuse_label="c",
        unknown=("segment:BC", "c"),
        angle=None,
        answers=answers,
        derived=[hypotenuse],
        alt_text=(
            f"Right-angled triangle with perpendicular sides {first.text} and {second.text}, "
            "right angle marked; the hypotenuse is labelled c. Not drawn to scale."
        ),
        title="Right-angled triangle",
        findings=_check_answer(hypotenuse, answers, None),
        dimensions={"perpendicular_sides": [first.as_spec(), second.as_spec()]},
    )


def right_angle_specification(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second = (q(item) for item in inputs["legs"])
    hypotenuse = math.hypot(first.value, second.value)
    return _legs_figure(
        template="right_angle_specification",
        inputs=inputs,
        task="find_hypotenuse",
        vertical=first,
        horizontal=second,
        vertical_label=first.text,
        horizontal_label=second.text,
        hypotenuse_label="x",
        unknown=("segment:BC", "x"),
        angle=None,
        answers=answers,
        derived=[hypotenuse],
        alt_text=(
            f"Triangle with shorter sides {first.text} and {second.text} meeting at a marked "
            "right angle; the longest side is labelled x. Not drawn to scale."
        ),
        title="Right-angled triangle",
        findings=_check_answer(hypotenuse, answers, None),
        dimensions={"perpendicular_sides": [first.as_spec(), second.as_spec()]},
    )


def missing_leg(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    hypotenuse, leg = q(inputs["hypotenuse"]), q(inputs["leg"])
    other = math.sqrt(max(hypotenuse.value**2 - leg.value**2, 0.0))
    return _legs_figure(
        template="missing_leg",
        inputs=inputs,
        task="find_leg",
        vertical=leg,
        horizontal=Quantity(other, hypotenuse.unit),
        vertical_label=leg.text,
        horizontal_label="b",
        hypotenuse_label=hypotenuse.text,
        unknown=("segment:AC", "b"),
        angle=None,
        answers=answers,
        derived=[other],
        alt_text=(
            f"Right-angled triangle with hypotenuse {hypotenuse.text} and one perpendicular "
            f"side {leg.text}, right angle marked; the other perpendicular side is labelled b. "
            "Not drawn to scale."
        ),
        title="Right-angled triangle",
        findings=_check_answer(other, answers, None),
        dimensions={"hypotenuse": hypotenuse.as_spec(), "perpendicular_side": leg.as_spec()},
    )


def tangent_adjacent(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """Given an acute angle and its opposite side, find the adjacent side x."""
    degrees = float(inputs["angle"])
    opposite = q(inputs["opposite"])
    adjacent = opposite.value / math.tan(math.radians(degrees))
    return _legs_figure(
        template="tangent_adjacent",
        inputs=inputs,
        task="find_side_trigonometry",
        vertical=opposite,
        horizontal=Quantity(adjacent, opposite.unit),
        vertical_label=opposite.text,
        horizontal_label="x",
        hypotenuse_label=None,
        unknown=("segment:AC", "x"),
        angle=(degrees, _degree(degrees)),
        answers=answers,
        derived=[adjacent],
        alt_text=(
            f"Right-angled triangle with a marked acute angle of {_degree(degrees)}. The side "
            f"opposite that angle is {opposite.text} and the adjacent side is labelled x. "
            "Not drawn to scale."
        ),
        title="Right-angled triangle",
        findings=_check_answer(adjacent, answers, None),
        dimensions={"angle_degrees": degrees, "opposite": opposite.as_spec()},
        clamp=False,
    )


def tangent_opposite(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """A sight line at a stated angle to level ground; find the vertical height x."""
    degrees = float(inputs["angle"])
    adjacent = q(inputs["adjacent"])
    opposite = adjacent.value * math.tan(math.radians(degrees))
    return _legs_figure(
        template="tangent_opposite",
        inputs=inputs,
        task="find_side_trigonometry",
        vertical=Quantity(opposite, adjacent.unit),
        horizontal=adjacent,
        vertical_label="x",
        horizontal_label=adjacent.text,
        hypotenuse_label="sight line",
        unknown=("segment:AB", "x"),
        angle=(degrees, _degree(degrees)),
        answers=answers,
        derived=[opposite],
        alt_text=(
            f"Right-angled triangle on level ground. The sight line makes {_degree(degrees)} "
            f"with the ground, the horizontal distance is {adjacent.text} and the vertical "
            "height is labelled x. Not drawn to scale."
        ),
        title="Sight line and vertical height",
        findings=_check_answer(opposite, answers, 1),
        dimensions={"angle_degrees": degrees, "adjacent": adjacent.as_spec()},
        clamp=False,
    )


def find_angle(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    opposite, adjacent = q(inputs["opposite"]), q(inputs["adjacent"])
    degrees = math.degrees(math.atan2(opposite.value, adjacent.value))
    return _legs_figure(
        template="find_angle",
        inputs=inputs,
        task="find_angle",
        vertical=opposite,
        horizontal=adjacent,
        vertical_label=opposite.text,
        horizontal_label=adjacent.text,
        hypotenuse_label=None,
        unknown=("angle:C", "θ"),
        angle=(degrees, "θ"),
        answers=answers,
        derived=[degrees],
        alt_text=(
            f"Right-angled triangle with the acute angle θ marked. Relative to θ, the opposite "
            f"side is {opposite.text} and the adjacent side is {adjacent.text}. Not drawn to scale."
        ),
        title="Right-angled triangle",
        findings=_check_answer(degrees, answers, 1),
        dimensions={"opposite": opposite.as_spec(), "adjacent": adjacent.as_spec()},
        clamp=False,
    )


# ------------------------------------------------------------------- general triangles
GENERAL_TRIANGLE = {"A": (0.0, 0.0), "B": (80.0, 230.0), "C": (400.0, 0.0)}


def _general_triangle(
    *,
    template: str,
    inputs: dict[str, Any],
    labels: Sequence[str],
    answers: Sequence[str],
    derived: Sequence[float],
    extra_forbidden: Sequence[str],
    alt_text: str,
    findings: list[str],
    dimensions: dict[str, Any],
    unknowns: list[dict[str, str]],
) -> Diagram:
    """Draw one fixed scalene triangle. Banks make these items text-only (see ``TEXT_ONLY``)."""
    model = list(GENERAL_TRIANGLE.values())
    canvas, transform = layout(model, max_width=380, max_height=250, top=60, bottom=120)
    for name, point in GENERAL_TRIANGLE.items():
        canvas.point(name, transform(point))
    _draw_triangle(canvas)
    inside = _centroid(canvas, "ABC")
    shortest, middle, longest = labels
    canvas.segment_label(shortest, "A", "B", away_from=inside)
    canvas.segment_label(middle, "B", "C", away_from=inside)
    canvas.segment_label(longest, "A", "C", away_from=inside)
    forbidden, exemptions = _forbid(answers, derived, extra_forbidden, canvas)
    spec = _spec(
        canvas,
        template,
        inputs,
        "converse_test" if template == "converse_test" else "perimeter_verify",
        dimensions,
        forbidden,
        exemptions,
        unknowns,
        extra={
            "drawn_to_scale": False,
            "forbid_right_angle_marker": True,
            **({"answer_kind": "classification_code"} if template == "converse_test" else {}),
        },
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Triangle",
        alt_text=alt_text,
        spec=spec,
        content_findings=findings,
    )


_RIGHT_ANGLE_PHRASES = [
    "right-angled",
    "right angled",
    "right angle",
    "right triangle",
    "right-triangle",
    "not right-angled",
    "90°",
    "hypotenuse",
]


def converse_test(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    sides = sorted((q(item) for item in inputs["sides"]), key=lambda item: item.value)
    a, b, c = (side.value for side in sides)
    is_right = math.isclose(a * a + b * b, c * c, rel_tol=1e-9)
    findings = []
    if answers and answers[0] in {"0", "1"} and answers[0] != ("1" if is_right else "0"):
        findings.append(
            f"The answer key says {answers[0]}, but {number(a)}² + {number(b)}² = "
            f"{number(a * a + b * b)} and {number(c)}² = {number(c * c)}, so the correct code is "
            f"{'1' if is_right else '0'}. Correct the answer key in the question, not the diagram."
        )
    return _general_triangle(
        template="converse_test",
        inputs=inputs,
        labels=[side.text for side in sides],
        answers=[],
        derived=[],
        extra_forbidden=_RIGHT_ANGLE_PHRASES,
        alt_text=(
            f"Triangle with sides {join_values([side.text for side in sides])}. No angle is "
            "marked. Not drawn to scale."
        ),
        findings=findings,
        dimensions={"sides": [side.as_spec() for side in sides]},
        unknowns=[],
    )


def perimeter_verify(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """Draw the triangle from its three true sides, with the longest as the base and no mark.

    The right angle is what the learner verifies, so it is never marked, but the prompt says the
    triangle is right-angled, so it is not drawn as some other shape either.
    """
    perimeter = q(inputs["perimeter"])
    first, second = (q(item) for item in inputs["sides"])
    third = perimeter.value - first.value - second.value
    sides = sorted(
        [(first.value, first.text), (second.value, second.text), (third, "x")],
        key=lambda item: item[0],
    )
    (short, short_label), (middle, middle_label), (longest, longest_label) = sides
    if short <= 0 or short + middle <= longest:
        raise UnsupportedDiagram(
            f"Sides {first.text}, {second.text} and {number(third)} form no triangle."
        )
    foot = (short**2 + longest**2 - middle**2) / (2 * longest)
    apex = (foot, math.sqrt(max(short**2 - foot**2, 0.0)))
    model = [(0.0, 0.0), apex, (longest, 0.0)]
    canvas, transform = layout(model, max_width=380, max_height=250, top=60, bottom=140)
    for name, point in zip("ABC", model, strict=True):
        canvas.point(name, transform(point))
    _draw_triangle(canvas)
    inside = _centroid(canvas, "ABC")
    canvas.segment_label(short_label, "A", "B", away_from=inside)
    canvas.segment_label(middle_label, "B", "C", away_from=inside)
    canvas.segment_label(longest_label, "A", "C", away_from=inside)
    canvas.caption(f"perimeter {perimeter.text}", (300, canvas.points["A"][1] + 72))
    target = {short_label: "segment:AB", middle_label: "segment:BC", longest_label: "segment:AC"}
    forbidden, exemptions = _forbid(answers, [third], _RIGHT_ANGLE_PHRASES, canvas)
    spec = _spec(
        canvas,
        "perimeter_verify",
        inputs,
        "perimeter_verify",
        {"perimeter": perimeter.as_spec(), "sides": [first.as_spec(), second.as_spec()]},
        forbidden,
        exemptions,
        [{"target": target["x"], "label": "x"}],
        relationships=[
            _ratio_relation("AB", "AC", short / longest),
            _ratio_relation("BC", "AC", middle / longest),
        ],
        extra={"drawn_to_scale": True, "forbid_right_angle_marker": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Triangle",
        alt_text=(
            f"Triangle with perimeter {perimeter.text}. Two sides are {first.text} and "
            f"{second.text}; the third side is labelled x. No angle is marked. Not drawn to "
            "scale."
        ),
        spec=spec,
        content_findings=_check_answer(third, answers, None),
    )


# -------------------------------------------------------------------------- rectangles
def _rectangle(canvas: Canvas, transform, width: float, height: float) -> None:
    canvas.point("A", transform((0.0, 0.0)))
    canvas.point("B", transform((0.0, height)))
    canvas.point("C", transform((width, 0.0)))
    canvas.point("D", transform((width, height)))
    canvas.polygon(["A", "C", "D", "B"], role="rectangle")
    canvas.segment("AB", "A", "B")
    canvas.segment("AC", "A", "C")
    canvas.segment("CD", "C", "D")
    canvas.segment("BD", "B", "D")


def rectangle_diagonal(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second = (q(item) for item in inputs["sides"])
    long_side, short_side = (first, second) if first.value >= second.value else (second, first)
    diagonal = math.hypot(first.value, second.value)
    ratio, clamped = _clamped_ratio(short_side.value, long_side.value)
    model = [(0.0, 0.0), (1.0, ratio)]
    canvas, transform = layout(model, max_width=380, max_height=270, top=56, bottom=120)
    _rectangle(canvas, transform, 1.0, ratio)
    canvas.segment("BC", "B", "C", stroke=ACCENT)
    canvas.right_angle("A", "B", "C")
    inside = _centroid(canvas, "ABCD")
    canvas.segment_label(short_side.text, "A", "B", away_from=inside)
    canvas.segment_label(long_side.text, "A", "C", away_from=inside)
    canvas.segment_label("d", "B", "C", away_from=canvas.points["A"])
    forbidden, exemptions = _forbid(answers, [diagonal], [], canvas)
    relationships = [
        {"type": "parallel", "segments": ["AB", "CD"]},
        {"type": "parallel", "segments": ["AC", "BD"]},
    ]
    if not clamped:
        relationships.append(_ratio_relation("AB", "AC", short_side.value / long_side.value))
    spec = _spec(
        canvas,
        "rectangle_diagonal",
        inputs,
        "find_hypotenuse",
        {"sides": [long_side.as_spec(), short_side.as_spec()]},
        forbidden,
        exemptions,
        [{"target": "segment:BC", "label": "d"}],
        relationships=relationships,
        extra={"drawn_to_scale": not clamped},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Rectangle and diagonal",
        alt_text=(
            f"Rectangle {long_side.text} by {short_side.text} with a cable along the diagonal "
            "from one corner to the opposite corner, labelled d. Not drawn to scale."
        ),
        spec=spec,
        content_findings=_check_answer(diagonal, answers, None),
    )


def diagonal_route(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    first, second = (q(item) for item in inputs["floor"])
    corridor = q(inputs["corridor"])
    long_side, short_side = (first, second) if first.value >= second.value else (second, first)
    diagonal = math.hypot(first.value, second.value)
    height = short_side.value / long_side.value
    length = corridor.value / long_side.value
    model = [(0.0, 0.0), (1.0 + length, height)]
    canvas, transform = layout(model, max_width=470, max_height=260, top=60, bottom=120)
    _rectangle(canvas, transform, 1.0, height)
    canvas.point("E", transform((1.0 + length, height)))
    canvas.segment("AD", "A", "D", stroke=ACCENT)
    canvas.segment("DE", "D", "E", stroke=ACCENT)
    canvas.right_angle("C", "A", "D")
    canvas.dot("A", 6, ACCENT)
    canvas.dot("E", 6, ACCENT)
    inside = _centroid(canvas, "ABCD")
    canvas.segment_label(long_side.text, "A", "C", away_from=inside)
    canvas.segment_label(short_side.text, "C", "D", away_from=inside)
    canvas.segment_label("d", "A", "D", away_from=canvas.points["C"])
    canvas.segment_label(corridor.text, "D", "E", away_from=canvas.points["C"])
    total = diagonal + corridor.value
    forbidden, exemptions = _forbid(answers, [total, diagonal], [], canvas)
    spec = _spec(
        canvas,
        "diagonal_route",
        inputs,
        "composite_route",
        {"floor": [long_side.as_spec(), short_side.as_spec()], "corridor": corridor.as_spec()},
        forbidden,
        exemptions,
        [{"target": "segment:AD", "label": "d"}],
        relationships=[
            {"type": "parallel", "segments": ["AB", "CD"]},
            {"type": "collinear", "points": ["B", "D", "E"]},
            _ratio_relation("CD", "AC", short_side.value / long_side.value),
            _ratio_relation("DE", "AC", corridor.value / long_side.value),
        ],
        extra={"drawn_to_scale": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Route across a rectangular floor",
        alt_text=(
            f"Rectangular floor {long_side.text} by {short_side.text}. The route crosses the "
            f"floor along the diagonal d, then continues {corridor.text} along a straight "
            "corridor. Not drawn to scale."
        ),
        spec=spec,
        content_findings=_check_answer(total, answers, None),
    )


# ------------------------------------------------------------------- applied scenarios
def cable_allowance(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    post, anchor, allowance = (
        q(inputs["post"]),
        q(inputs["anchor_distance"]),
        q(inputs["allowance"]),
    )
    cable = math.hypot(post.value, anchor.value)
    extra = max(allowance.value / anchor.value, 0.16)
    model = [(0.0, 0.0), (0.0, post.value / anchor.value), (1.0 + extra, 0.0)]
    canvas, transform = layout(model, max_width=380, max_height=280, top=56, bottom=130)
    canvas.point("A", transform((0.0, 0.0)))
    canvas.point("B", transform((0.0, post.value / anchor.value)))
    canvas.point("C", transform((1.0, 0.0)))
    canvas.point("E", transform((1.0 + extra, 0.0)))
    canvas.polygon(["A", "B", "C"], role="triangle")
    canvas.segment("AB", "A", "B", width=8)
    canvas.segment("AC", "A", "C")
    canvas.segment("BC", "B", "C", stroke=ACCENT)
    canvas.segment("CE", "C", "E", stroke=ACCENT, hidden=True, role="allowance")
    canvas.dot("C", 7)
    canvas.right_angle("A", "B", "C")
    inside = _centroid(canvas, "ABC")
    canvas.segment_label(post.text, "A", "B", away_from=inside)
    canvas.segment_label(anchor.text, "A", "C", away_from=inside)
    canvas.segment_label("c", "B", "C", away_from=inside)
    canvas.segment_label(
        f"+{allowance.text}", "C", "E", away_from=canvas.points["B"], positions=(0.5, 0.7, 0.9)
    )
    total = cable + allowance.value
    forbidden, exemptions = _forbid(answers, [total, cable], [], canvas)
    spec = _spec(
        canvas,
        "cable_allowance",
        inputs,
        "find_hypotenuse_then_add",
        {
            "post": post.as_spec(),
            "anchor_distance": anchor.as_spec(),
            "allowance": allowance.as_spec(),
        },
        forbidden,
        exemptions,
        [{"target": "segment:BC", "label": "c"}],
        relationships=[
            _ratio_relation("AB", "AC", post.value / anchor.value),
            {"type": "collinear", "points": ["A", "C", "E"]},
        ],
        extra={"drawn_to_scale": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Cable from a vertical post",
        alt_text=(
            f"Vertical post {post.text} high with a cable c from its top to an anchor "
            f"{anchor.text} from its base, right angle marked at the base. A further "
            f"{allowance.text} of cable is shown beyond the anchor for fastening. Not drawn to scale."
        ),
        spec=spec,
        content_findings=_check_answer(total, answers, None),
    )


def elevation_observer(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    distance, eye = q(inputs["distance"]), q(inputs["eye_height"])
    degrees = float(inputs["angle"])
    rise = distance.value * math.tan(math.radians(degrees))
    total = rise + eye.value
    model = [(0.0, 0.0), (distance.value, total)]
    canvas, transform = layout(model, max_width=300, max_height=300, top=50, bottom=120)
    canvas.point("F", transform((0.0, 0.0)))
    canvas.point("E", transform((0.0, eye.value)))
    canvas.point("T", transform((distance.value, 0.0)))
    canvas.point("P", transform((distance.value, eye.value)))
    canvas.point("Q", transform((distance.value, total)))
    canvas.polygon(["E", "P", "Q"], role="triangle")
    canvas.segment("FT", "F", "T", role="ground")
    canvas.segment("TQ", "T", "Q", width=8, role="tower")
    canvas.segment("FE", "F", "E", stroke=ACCENT, width=6, role="observer")
    canvas.segment("EP", "E", "P", stroke=LIGHT, width=THIN, hidden=True, role="eye_level")
    canvas.segment("EQ", "E", "Q", stroke=ACCENT, role="line_of_sight")
    canvas.dot("E", 6, ACCENT)
    canvas.right_angle("P", "E", "Q", size=18)
    canvas.angle_arc("angle-E", "E", "P", "Q", ANGLE_RADIUS, degrees)
    canvas.angle_label(_degree(degrees), "E", "P", "Q", ANGLE_RADIUS)
    inside = _centroid(canvas, "EPQ")
    canvas.segment_label(distance.text, "F", "T", away_from=inside)
    canvas.segment_label(
        eye.text, "F", "E", away_from=inside, positions=(0.5,), gaps=(8, 14, 22, 32, 44)
    )
    canvas.segment_label("h", "T", "Q", away_from=inside, positions=(0.5, 0.6, 0.4))
    forbidden, exemptions = _forbid(answers, [total, rise], [], canvas)
    spec = _spec(
        canvas,
        "elevation_observer",
        inputs,
        "angle_of_elevation",
        {"distance": distance.as_spec(), "angle_degrees": degrees, "eye_height": eye.as_spec()},
        forbidden,
        exemptions,
        [{"target": "segment:TQ", "label": "h"}],
        relationships=[
            {"type": "collinear", "points": ["T", "P", "Q"]},
            {"type": "parallel", "segments": ["FT", "EP"]},
            _ratio_relation("FE", "FT", eye.value / distance.value),
        ],
        extra={"drawn_to_scale": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Angle of elevation from eye level",
        alt_text=(
            f"An observer stands {distance.text} from a vertical tower of height h on level "
            f"ground. The observer's eye is {eye.text} above the ground. A dashed eye-level line "
            f"meets the tower at a right angle, and the angle of elevation from eye level to the "
            f"top is {_degree(degrees)}. Not drawn to scale."
        ),
        spec=spec,
        content_findings=_check_answer(total, answers, 1),
    )


def two_position(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    gap = q(inputs["gap"])
    far, near = float(inputs["far_angle"]), float(inputs["near_angle"])
    t_far, t_near = math.tan(math.radians(far)), math.tan(math.radians(near))
    height = gap.value * t_far * t_near / (t_near - t_far)
    x = height / t_near
    model = [(0.0, 0.0), (gap.value + x, height)]
    canvas, transform = layout(model, max_width=440, max_height=280, top=50, bottom=130)
    canvas.point("F", transform((0.0, 0.0)))
    canvas.point("N", transform((gap.value, 0.0)))
    canvas.point("T", transform((gap.value + x, 0.0)))
    canvas.point("Q", transform((gap.value + x, height)))
    canvas.polygon(["F", "T", "Q"], role="triangle")
    canvas.segment("FN", "F", "N", role="ground")
    canvas.segment("NT", "N", "T", role="ground")
    canvas.segment("TQ", "T", "Q", width=8, role="mast")
    canvas.segment("FQ", "F", "Q", stroke=ACCENT, role="line_of_sight")
    canvas.segment("NQ", "N", "Q", stroke=ACCENT, role="line_of_sight")
    canvas.dot("F", 6)
    canvas.dot("N", 6)
    canvas.right_angle("T", "N", "Q", size=18)
    canvas.angle_arc("angle-F", "F", "N", "Q", ANGLE_RADIUS + 14, far)
    canvas.angle_arc("angle-N", "N", "T", "Q", ANGLE_RADIUS, near)
    canvas.angle_label(_degree(far), "F", "N", "Q", ANGLE_RADIUS + 14)
    canvas.angle_label(_degree(near), "N", "T", "Q", ANGLE_RADIUS)
    above = canvas.points["Q"]
    canvas.segment_label(gap.text, "F", "N", away_from=above)
    canvas.segment_label("x", "N", "T", away_from=above)
    canvas.segment_label("h", "T", "Q", away_from=canvas.points["F"])
    forbidden, exemptions = _forbid(answers, [height, x], [], canvas)
    spec = _spec(
        canvas,
        "two_position",
        inputs,
        "two_angles_of_elevation",
        {"gap": gap.as_spec(), "far_angle_degrees": far, "near_angle_degrees": near},
        forbidden,
        exemptions,
        [{"target": "segment:TQ", "label": "h"}, {"target": "segment:NT", "label": "x"}],
        relationships=[
            {"type": "collinear", "points": ["F", "N", "T"]},
            _ratio_relation("FN", "NT", gap.value / x),
        ],
        extra={"drawn_to_scale": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Angles of elevation from two points",
        alt_text=(
            f"A vertical mast of height h stands on level ground. Two observation points on the "
            f"same line as the mast are {gap.text} apart; the nearer point is x from the mast. "
            f"The angle of elevation of the top is {_degree(far)} from the farther point and "
            f"{_degree(near)} from the nearer point. Not drawn to scale."
        ),
        spec=spec,
        content_findings=_check_answer(height, answers, 1),
    )


# ---------------------------------------------------------------------------- lessons
def lesson_pythagoras(inputs: dict[str, Any] | None = None, answers: Sequence[str] = ()) -> Diagram:
    inputs = inputs or {"legs": [6, 8]}
    a, b = (float(value) for value in inputs["legs"])
    c = math.hypot(a, b)
    canvas, _ = _right_triangle_canvas(a, b, bottom=160, note=False)
    _draw_triangle(canvas)
    canvas.right_angle("A", "B", "C")
    inside = _centroid(canvas, "ABC")
    canvas.segment_label(f"a = {number(a)}", "A", "B", away_from=inside)
    canvas.segment_label(f"b = {number(b)}", "A", "C", away_from=inside)
    canvas.segment_label(f"c = {number(c)}", "B", "C", away_from=inside)
    base_y = canvas.points["A"][1]
    canvas.caption(f"{number(a)}² + {number(b)}² = {number(c)}²", (300, base_y + 82))
    canvas.caption("c is opposite the right angle", (300, base_y + 120), size=22, weight=500)
    spec = _spec(
        canvas,
        "lesson_pythagoras",
        inputs,
        "teaching",
        {"perpendicular_sides": [a, b], "hypotenuse": c},
        [],
        [],
        [],
        relationships=[_ratio_relation("AB", "AC", a / b)],
        extra={"drawn_to_scale": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Pythagoras’ theorem",
        alt_text=(
            f"Right-angled triangle with perpendicular sides a = {number(a)} and b = {number(b)} "
            f"and hypotenuse c = {number(c)} opposite the marked right angle, with "
            f"{number(a)}² + {number(b)}² = {number(c)}²."
        ),
        spec=spec,
    )


def lesson_converse(inputs: dict[str, Any] | None = None, answers: Sequence[str] = ()) -> Diagram:
    """Two triangles drawn from their side lengths: 7-24-25 (right) and 7-24-26 (not right)."""
    inputs = inputs or {"triangles": [[7, 24, 25], [7, 24, 26]]}
    triangles = [[float(side) for side in sides] for sides in inputs["triangles"]]
    canvas = Canvas(height=650)
    scale = 400 / max(sides[1] for sides in triangles)
    relationships: list[dict[str, Any]] = []
    for index, (short, base, longest) in enumerate(triangles):
        cos_a = (short**2 + base**2 - longest**2) / (2 * short * base)
        angle_a = math.acos(max(-1.0, min(1.0, cos_a)))
        top = 60 + index * 305
        apex_offset = short * math.cos(angle_a) * scale
        height = short * math.sin(angle_a) * scale
        left = (WIDTH - base * scale) / 2 + max(0.0, -apex_offset) / 2
        names = [f"A{index + 1}", f"B{index + 1}", f"C{index + 1}"]
        a, b, c = names
        canvas.point(a, (left, top + height))
        canvas.point(b, (left + apex_offset, top))
        canvas.point(c, (left + base * scale, top + height))
        _draw_triangle(canvas, names)
        is_right = math.isclose(short**2 + base**2, longest**2)
        if is_right:
            canvas.right_angle(a, b, c)
        inside = _centroid(canvas, names)
        canvas.segment_label(number(short), a, b, away_from=inside)
        canvas.segment_label(number(base), a, c, away_from=inside)
        canvas.segment_label(number(longest), b, c, away_from=inside)
        relation = "=" if is_right else "≠"
        squares = (
            f"{number(short)}² + {number(base)}² = {number(short**2 + base**2)} "
            f"{relation} {number(longest**2)} = {number(longest)}²"
        )
        verdict = "right-angled" if is_right else "not right-angled"
        y = top + height + 78
        canvas.caption(squares, (300, y), size=CAPTION_SIZE)
        canvas.caption(verdict, (300, y + 38), size=CAPTION_SIZE, weight=700)
        relationships.append(
            {
                "type": "length_ratio",
                "segments": [f"{a}{b}", f"{a}{c}"],
                "value": round(short / base, 4),
                "tolerance": 0.02,
            }
        )
    spec = _spec(
        canvas,
        "lesson_converse",
        inputs,
        "teaching",
        {"triangles": inputs["triangles"]},
        [],
        [],
        [],
        relationships=relationships,
        extra={"drawn_to_scale": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Testing triangles with the converse of Pythagoras",
        alt_text=(
            "Two triangles drawn from their side lengths. The 7, 24, 25 triangle has a right "
            "angle marked opposite the side 25 because 7² + 24² = 625 = 25². The 7, 24, 26 "
            "triangle has no right angle because 26² = 676."
        ),
        spec=spec,
    )


def lesson_trigonometry(
    inputs: dict[str, Any] | None = None, answers: Sequence[str] = ()
) -> Diagram:
    inputs = inputs or {"legs": [3, 4]}
    opposite, adjacent = (float(value) for value in inputs["legs"])
    degrees = math.degrees(math.atan2(opposite, adjacent))
    canvas, _ = _right_triangle_canvas(opposite, adjacent, bottom=180, max_width=300, note=False)
    _draw_triangle(canvas)
    canvas.right_angle("A", "B", "C")
    canvas.angle_arc("angle-C", "C", "A", "B", ANGLE_RADIUS + 6, round(degrees, 2))
    canvas.angle_label("θ", "C", "A", "B", ANGLE_RADIUS + 6)
    inside = _centroid(canvas, "ABC")
    canvas.segment_label("opposite", "A", "B", away_from=inside, size=CAPTION_SIZE)
    canvas.segment_label("adjacent", "A", "C", away_from=inside, size=CAPTION_SIZE)
    canvas.segment_label("hypotenuse", "B", "C", away_from=inside, size=CAPTION_SIZE)
    base_y = canvas.points["A"][1]
    for offset, line in zip(
        (70, 106, 142),
        (
            "sin θ = opposite ÷ hypotenuse",
            "cos θ = adjacent ÷ hypotenuse",
            "tan θ = opposite ÷ adjacent",
        ),
        strict=True,
    ):
        canvas.caption(line, (300, base_y + offset), size=22, weight=500)
    spec = _spec(
        canvas,
        "lesson_trigonometry",
        inputs,
        "teaching",
        {"reference_angle": "θ"},
        [],
        [],
        [],
        relationships=[_ratio_relation("AB", "AC", opposite / adjacent)],
        extra={"drawn_to_scale": True},
    )
    return finish(
        canvas,
        renderer=RIGHT_TRIANGLE_RENDERER,
        title="Naming sides relative to θ",
        alt_text=(
            "Right-angled triangle with the acute angle θ marked at the base. The side opposite θ "
            "is labelled opposite, the side next to θ is labelled adjacent and the side opposite "
            "the right angle is labelled hypotenuse, with sin θ = opposite ÷ hypotenuse, "
            "cos θ = adjacent ÷ hypotenuse and tan θ = opposite ÷ adjacent."
        ),
        spec=spec,
    )


TEMPLATES: dict[str, Callable[..., Diagram]] = {
    "find_hypotenuse": find_hypotenuse,
    "right_angle_specification": right_angle_specification,
    "missing_leg": missing_leg,
    "tangent_adjacent": tangent_adjacent,
    "tangent_opposite": tangent_opposite,
    "find_angle": find_angle,
    "converse_test": converse_test,
    "perimeter_verify": perimeter_verify,
    "rectangle_diagonal": rectangle_diagonal,
    "diagonal_route": diagonal_route,
    "cable_allowance": cable_allowance,
    "elevation_observer": elevation_observer,
    "two_position": two_position,
    "lesson_pythagoras": lesson_pythagoras,
    "lesson_converse": lesson_converse,
    "lesson_trigonometry": lesson_trigonometry,
}
