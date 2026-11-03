"""Deterministic mensuration diagrams (renderer ``nextscholar-mensuration-svg-v2``).

Each template draws the solid the question describes: four-sided pyramid bases with the apex
above the centre of the base, cones with their radius, perpendicular height and slant height
on the segments they measure, full diameters, hollow and cored spheres, a cone inside a
cylinder, a vertex-down cone holding liquid and separate solids side by side. Lengths that
a learner must find are labelled with a variable or word and drawn at a neutral size, so the
picture never encodes a withheld value.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

from ..svg_metrics import ellipse_points
from .canvas import (
    ACCENT,
    CAPTION_SIZE,
    FILL,
    FILL_ALT,
    INK,
    LIGHT,
    LIQUID,
    LIQUID_INK,
    THIN,
    WIDTH,
    Canvas,
    Point,
    add,
    fmt,
    lerp,
    scale,
)
from .common import (
    MENSURATION_RENDERER,
    Diagram,
    Quantity,
    base_spec,
    decimal_forms,
    finish,
    join_values,
    number,
    withheld_labels,
)

LABEL = 24
ELLIPSE_RATIO = 0.34
RECEDE_DEGREES = 32.0
DEPTH_FORESHORTENING = 0.55
NEUTRAL_RATIO = 2.2
PI = math.pi


def q(value: dict[str, Any] | Quantity) -> Quantity:
    if isinstance(value, Quantity):
        return value
    return Quantity(float(value["value"]), value.get("unit"))


def labelled(letter: str, quantity: Quantity) -> str:
    return f"{letter} = {quantity.text}"


def pi_forms(coefficient: float) -> list[str]:
    forms = [f"{number(coefficient)}π"] if math.isclose(coefficient, round(coefficient, 4)) else []
    return [*forms, *decimal_forms(coefficient * PI)]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


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
    tolerance = 0.051 if places else 1e-6
    if any(math.isclose(value, target, abs_tol=tolerance) for value in numeric):
        return []
    shown = f"{target:.{places}f}" if places else number(expected)
    return [
        f"The canonical answer {answers[0]} does not match the value recomputed from the prompt "
        f"({shown}). Correct the answer key in the question, not the diagram."
    ]


# ------------------------------------------------------------------------ solid drawing
def _pyramid(
    canvas: Canvas,
    prefix: str,
    front_left: Point,
    width: float,
    depth: float,
    height: float,
    *,
    show_height: bool = True,
    slant: bool = False,
) -> dict[str, str]:
    """Draw a right pyramid on a four-sided base with the apex above the base centre.

    Hidden edges (the back and left base edges and the back lateral edge) are dashed.
    """
    dx = depth * math.cos(math.radians(RECEDE_DEGREES))
    dy = depth * math.sin(math.radians(RECEDE_DEGREES))
    x0, y0 = front_left
    names = {key: f"{prefix}{key}" for key in ("P1", "P2", "P3", "P4", "O", "V", "S", "X")}
    p1 = canvas.point(names["P1"], (x0, y0))
    p2 = canvas.point(names["P2"], (x0 + width, y0))
    p3 = canvas.point(names["P3"], (x0 + width + dx, y0 - dy))
    p4 = canvas.point(names["P4"], (x0 + dx, y0 - dy))
    centre = ((p1[0] + p2[0] + p3[0] + p4[0]) / 4, (p1[1] + p2[1] + p3[1] + p4[1]) / 4)
    o = canvas.point(names["O"], centre)
    v = canvas.point(names["V"], (o[0], o[1] - height))
    canvas.fill([p1, p2, v], FILL)
    canvas.fill([p2, p3, v], FILL_ALT)
    canvas.polygon(
        [names["P1"], names["P2"], names["P3"], names["P4"]],
        fill="none",
        role="pyramid-base",
    )
    n = names
    canvas.segment(f"{n['P1']}{n['P4']}", n["P1"], n["P4"], hidden=True)
    canvas.segment(f"{n['P4']}{n['P3']}", n["P4"], n["P3"], hidden=True)
    canvas.segment(f"{n['V']}{n['P4']}", n["V"], n["P4"], hidden=True)
    canvas.segment(f"{n['P1']}{n['P2']}", n["P1"], n["P2"])
    canvas.segment(f"{n['P2']}{n['P3']}", n["P2"], n["P3"])
    canvas.segment(f"{n['V']}{n['P1']}", n["V"], n["P1"])
    canvas.segment(f"{n['V']}{n['P2']}", n["V"], n["P2"])
    canvas.segment(f"{n['V']}{n['P3']}", n["V"], n["P3"])
    if show_height:
        canvas.point(n["X"], (o[0] + 30, o[1]))
        canvas.segment(
            f"{n['V']}{n['O']}", n["V"], n["O"], hidden=True, stroke=ACCENT, width=THIN + 1
        )
        canvas.right_angle(n["O"], n["V"], n["X"], size=16)
        canvas.dot(n["O"], 4, ACCENT)
    if slant:
        canvas.point(n["S"], lerp(p1, p2, 0.5))
        canvas.segment(f"{n['V']}{n['S']}", n["V"], n["S"], stroke=ACCENT, width=THIN + 1)
    return names


def _pyramid_relationships(
    names: dict[str, str], *, show_height: bool, slant: bool
) -> list[dict[str, Any]]:
    base = [names["P1"], names["P2"], names["P3"], names["P4"]]
    relations: list[dict[str, Any]] = [
        {"type": "polygon_sides", "points": base, "count": 4},
        {"type": "parallelogram", "points": base},
        {"type": "centroid", "point": names["O"], "of": base},
        {"type": "vertical", "points": [names["V"], names["O"]]},
    ]
    if show_height:
        relations.append({"type": "inside_polygon", "point": names["O"], "polygon": base})
        relations.append({"type": "hidden_segment", "segment": f"{names['V']}{names['O']}"})
    if slant:
        relations.append(
            {"type": "midpoint", "point": names["S"], "of": [names["P1"], names["P2"]]}
        )
    return relations


def _cone(
    canvas: Canvas,
    prefix: str,
    centre: Point,
    rx: float,
    height: float,
    *,
    inverted: bool = False,
    show_height: bool = True,
    show_radius: bool = True,
    open_top: bool = False,
    fill: str = FILL,
) -> dict[str, str]:
    """Draw a right circular cone with its base ellipse centred on ``centre``.

    The hidden half of the base ellipse is dashed. An inverted cone has its vertex below the
    rim; with ``open_top`` the whole rim is visible.
    """
    names = {key: f"{prefix}{key}" for key in ("O", "V", "L", "R")}
    ry = rx * ELLIPSE_RATIO
    o = canvas.point(names["O"], centre)
    v = canvas.point(names["V"], (o[0], o[1] + height if inverted else o[1] - height))
    left = canvas.point(names["L"], (o[0] - rx, o[1]))
    right = canvas.point(names["R"], (o[0] + rx, o[1]))
    if inverted:
        canvas.fill([left, v, right, *ellipse_points(o[0], o[1], rx, ry, 0, 180)], fill)
    else:
        canvas.fill([left, v, right, *ellipse_points(o[0], o[1], rx, ry, 360, 180)], fill)
    canvas.ellipse(
        f"{prefix}base",
        names["O"],
        rx,
        ry,
        hidden_back=not (inverted or open_top),
    )
    canvas.segment(f"{names['V']}{names['L']}", names["V"], names["L"])
    canvas.segment(f"{names['V']}{names['R']}", names["V"], names["R"])
    if show_height:
        canvas.segment(
            f"{names['V']}{names['O']}",
            names["V"],
            names["O"],
            hidden=True,
            stroke=ACCENT,
            width=THIN + 1,
        )
    if show_radius:
        canvas.segment(
            f"{names['O']}{names['R']}",
            names["O"],
            names["R"],
            hidden=not inverted,
            stroke=ACCENT,
            width=THIN + 1,
        )
    if show_height and show_radius:
        canvas.right_angle(names["O"], names["V"], names["R"], size=16)
    canvas.dot(names["O"], 4, ACCENT)
    return names


def _cone_relationships(names: dict[str, str], prefix: str) -> list[dict[str, Any]]:
    return [
        {"type": "vertical", "points": [names["V"], names["O"]]},
        {"type": "ellipse_centre", "ellipse": f"{prefix}base", "point": names["O"]},
        {"type": "on_ellipse", "ellipse": f"{prefix}base", "points": [names["L"], names["R"]]},
        {"type": "midpoint", "point": names["O"], "of": [names["L"], names["R"]]},
    ]


def _sphere(
    canvas: Canvas,
    prefix: str,
    centre: Point,
    radius: float,
    *,
    equator: bool = True,
    radius_degrees: float | None = 35.0,
    diameter_degrees: float | None = None,
    fill: str = FILL,
    hidden: bool = False,
) -> dict[str, str]:
    """Draw a sphere, optionally with a radius or a full diameter ending on the surface."""
    names = {key: f"{prefix}{key}" for key in ("O", "E", "D1", "D2")}
    o = canvas.point(names["O"], centre)
    canvas.circle(f"{prefix}sphere", names["O"], radius, fill=fill, hidden=hidden)
    if equator:
        canvas.ellipse(f"{prefix}equator", names["O"], radius, radius * 0.3, stroke=LIGHT, width=2)
    if radius_degrees is not None:
        angle = math.radians(radius_degrees)
        canvas.point(names["E"], (o[0] + radius * math.cos(angle), o[1] - radius * math.sin(angle)))
        canvas.segment(
            f"{names['O']}{names['E']}", names["O"], names["E"], stroke=ACCENT, width=THIN + 1
        )
    if diameter_degrees is not None:
        angle = math.radians(diameter_degrees)
        offset = (radius * math.cos(angle), -radius * math.sin(angle))
        canvas.point(names["D1"], add(o, scale(offset, -1)))
        canvas.point(names["D2"], add(o, offset))
        canvas.segment(
            f"{names['D1']}{names['D2']}", names["D1"], names["D2"], stroke=ACCENT, width=THIN + 1
        )
    canvas.dot(names["O"], 4, ACCENT)
    return names


def _sphere_relationships(
    names: dict[str, str], prefix: str, *, radius: bool, diameter: bool
) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = [
        {"type": "circle_centre", "circle": f"{prefix}sphere", "point": names["O"]}
    ]
    if radius:
        relations.append({"type": "on_circle", "circle": f"{prefix}sphere", "points": [names["E"]]})
    if diameter:
        relations.append(
            {"type": "on_circle", "circle": f"{prefix}sphere", "points": [names["D1"], names["D2"]]}
        )
        relations.append(
            {"type": "midpoint", "point": names["O"], "of": [names["D1"], names["D2"]]}
        )
    return relations


def _hemisphere(
    canvas: Canvas,
    prefix: str,
    centre: Point,
    radius: float,
    *,
    open_bowl: bool,
    show_radius: bool = True,
    seam_hidden_back: bool = False,
) -> dict[str, str]:
    """Draw a hemisphere with its flat circular face on top (a bowl when ``open_bowl``)."""
    names = {key: f"{prefix}{key}" for key in ("O", "L", "R")}
    o = canvas.point(names["O"], centre)
    left = canvas.point(names["L"], (o[0] - radius, o[1]))
    right = canvas.point(names["R"], (o[0] + radius, o[1]))
    ry = radius * ELLIPSE_RATIO
    canvas.fill(ellipse_points(o[0], o[1], radius, radius, 180, 360), FILL)
    if open_bowl:
        canvas.fill(ellipse_points(o[0], o[1], radius, ry), FILL_ALT)
    canvas.raw_path(
        f"M{fmt(left[0])} {fmt(left[1])} A{fmt(radius)} {fmt(radius)} 0 0 0 {fmt(right[0])} {fmt(right[1])}",
        [ellipse_points(o[0], o[1], radius, radius, 180, 360)],
        stroke=INK,
        attrs={"data-circle-arc": f"{prefix}bowl"},
    )
    canvas.ellipse(f"{prefix}rim", names["O"], radius, ry, hidden_back=seam_hidden_back)
    if show_radius:
        canvas.segment(
            f"{names['O']}{names['R']}", names["O"], names["R"], stroke=ACCENT, width=THIN + 1
        )
        canvas.dot(names["O"], 4, ACCENT)
    return names


def _forbid(canvas: Canvas, answers: Sequence[str], values: Sequence[str]):
    visible = [label["text"] for label in canvas.placed_labels]
    return withheld_labels([*answers, *values], visible)


def _values(*numbers: float) -> list[str]:
    forms: list[str] = []
    for value in numbers:
        forms.extend(decimal_forms(value))
    return forms


def _spec(
    canvas: Canvas,
    *,
    kind: str,
    template: str,
    inputs: dict[str, Any],
    dimensions: dict[str, Any],
    forbidden: tuple[list[str], list[dict[str, str]]],
    unknowns: list[dict[str, str]],
    relationships: list[dict[str, Any]],
    solids: list[dict[str, Any]],
) -> dict[str, Any]:
    return base_spec(
        renderer=MENSURATION_RENDERER,
        diagram_kind=kind,
        template=template,
        inputs=inputs,
        dimensions=dimensions,
        canvas=canvas,
        forbidden=forbidden[0],
        exemptions=forbidden[1],
        unknowns=unknowns,
        relationships=relationships,
        extra={"solids": solids},
    )


def _done(
    canvas: Canvas, *, title: str, alt: str, spec: dict[str, Any], findings: list[str] | None = None
) -> Diagram:
    return finish(
        canvas,
        renderer=MENSURATION_RENDERER,
        title=title,
        alt_text=alt,
        spec=spec,
        content_findings=findings,
    )


def _canvas(height: float) -> Canvas:
    canvas = Canvas(height=round(height))
    canvas.note()
    return canvas


# ---------------------------------------------------------------------------- pyramids
def _pyramid_size(front: float, depth: float, height: float | None, *, max_front: float = 270):
    unit = max_front / max(front, depth)
    width = front * unit
    depth_px = depth * unit * DEPTH_FORESHORTENING
    if height is None:
        height_px = 1.15 * max(width, 200)
    else:
        height_px = height * unit
    return width, depth_px, _clamp(height_px, 170, 320)


def _single_pyramid(
    *,
    template: str,
    inputs: dict[str, Any],
    answers: Sequence[str],
    front: Quantity,
    depth: Quantity,
    height: Quantity | None,
    height_label: str | None,
    slant_label: str | None,
    base_label: str | None,
    edge_labels: bool,
    withheld: Sequence[str],
    unknowns: list[dict[str, str]],
    base_shape: str,
    alt: str,
    title: str,
    dimensions: dict[str, Any],
    findings: list[str],
) -> Diagram:
    width, depth_px, height_px = _pyramid_size(
        front.value, depth.value, height.value if height else None
    )
    dx = depth_px * math.cos(math.radians(RECEDE_DEGREES))
    dy = depth_px * math.sin(math.radians(RECEDE_DEGREES))
    top = 46
    y0 = top + height_px + dy / 2
    canvas = _canvas(y0 + 120)
    x0 = WIDTH - 40 - width - dx
    show_height = height_label is not None
    names = _pyramid(
        canvas,
        "",
        (x0, y0),
        width,
        depth_px,
        height_px,
        show_height=show_height,
        slant=slant_label is not None,
    )
    inside = canvas.points["O"]
    if edge_labels:
        canvas.segment_label(front.text, "P1", "P2", away_from=inside, size=LABEL)
        canvas.segment_label(depth.text, "P2", "P3", away_from=inside, size=LABEL)
    if base_label:
        canvas.text(
            base_label,
            [(x0 + width / 2, y0 + 34), (x0 + width / 2, y0 + 44)],
            target="face:base",
            size=LABEL,
        )
    if slant_label:
        canvas.length_label(
            slant_label,
            "V",
            "S",
            away_from=canvas.points["P2"],
            directions=((-1, 0.1), (-1, -0.35), (-1, 0.45)),
            size=LABEL,
            positions=(0.55, 0.65, 0.45, 0.72),
        )
    if show_height:
        canvas.length_label(
            height_label,
            "V",
            "O",
            away_from=canvas.points["P1"],
            directions=((-1, 0.1), (-1, -0.35), (-1, 0.45)),
            size=LABEL,
            positions=(0.45, 0.55, 0.35, 0.62),
        )
    relationships = _pyramid_relationships(
        names, show_height=show_height, slant=slant_label is not None
    )
    if base_shape == "square":
        relationships.append({"type": "equal_lengths", "values": [front.value, depth.value]})
    spec = _spec(
        canvas,
        kind="pyramid",
        template=template,
        inputs=inputs,
        dimensions=dimensions,
        forbidden=_forbid(canvas, answers, withheld),
        unknowns=unknowns,
        relationships=relationships,
        solids=[{"type": "pyramid", "base": base_shape, "points": names}],
    )
    return _done(canvas, title=title, alt=alt, spec=spec, findings=findings)


def rectangular_pyramid_volume(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    length, breadth, height = q(inputs["base"][0]), q(inputs["base"][1]), q(inputs["height"])
    volume = length.value * breadth.value * height.value / 3
    return _single_pyramid(
        template="rectangular_pyramid_volume",
        inputs=inputs,
        answers=answers,
        front=length,
        depth=breadth,
        height=height,
        height_label=labelled("h", height),
        slant_label=None,
        base_label=None,
        edge_labels=True,
        withheld=_values(volume, length.value * breadth.value),
        unknowns=[],
        base_shape="square" if math.isclose(length.value, breadth.value) else "rectangle",
        alt=(
            f"Right pyramid on a rectangular base {length.text} by {breadth.text}. The "
            f"perpendicular height h = {height.text} runs from the apex to the centre of the "
            "base, with the right angle marked. Hidden edges are dashed. Not drawn to scale."
        ),
        title="Rectangular-based pyramid",
        dimensions={"base": [length.as_spec(), breadth.as_spec()], "height": height.as_spec()},
        findings=_check_answer(volume, answers, None),
    )


def pyramid_base_area_volume(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    area, height = q(inputs["base_area"]), q(inputs["height"])
    volume = area.value * height.value / 3
    side = math.sqrt(area.value)
    unit = height.unit
    return _single_pyramid(
        template="pyramid_base_area_volume",
        inputs=inputs,
        answers=answers,
        front=Quantity(side * 1.25, unit),
        depth=Quantity(side / 1.25, unit),
        height=height,
        height_label=labelled("h", height),
        slant_label=None,
        base_label=f"base area {area.text}",
        edge_labels=False,
        withheld=_values(volume),
        unknowns=[],
        base_shape="unspecified",
        alt=(
            f"Pyramid with base area {area.text} and perpendicular height h = {height.text} "
            "from the apex to the centre of the base, right angle marked. Hidden edges are "
            "dashed. Not drawn to scale."
        ),
        title="Pyramid",
        dimensions={"base_area": area.as_spec(), "height": height.as_spec()},
        findings=_check_answer(volume, answers, None),
    )


def pyramid_height(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    volume = q(inputs["volume"])
    length, breadth = q(inputs["base"][0]), q(inputs["base"][1])
    height = 3 * volume.value / (length.value * breadth.value)
    return _single_pyramid(
        template="pyramid_height",
        inputs=inputs,
        answers=answers,
        front=length,
        depth=breadth,
        height=None,
        height_label="h",
        slant_label=None,
        base_label=None,
        edge_labels=True,
        withheld=_values(height, length.value * breadth.value),
        unknowns=[{"target": "segment:VO", "label": "h"}],
        base_shape="rectangle",
        alt=(
            f"Rectangular-based pyramid with base {length.text} by {breadth.text} and volume "
            f"{volume.text}. The perpendicular height h runs from the apex to the centre of the "
            "base, with the right angle marked. Not drawn to scale."
        ),
        title="Rectangular-based pyramid",
        dimensions={"volume": volume.as_spec(), "base": [length.as_spec(), breadth.as_spec()]},
        findings=_check_answer(height, answers, None),
    )


def pyramid_covering_cost(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side, slant = q(inputs["base_side"]), q(inputs["slant_height"])
    rate = float(inputs["rate"])
    face = side.value * slant.value / 2
    total_area = side.value**2 + 4 * face
    return _single_pyramid(
        template="pyramid_covering_cost",
        inputs=inputs,
        answers=answers,
        front=side,
        depth=side,
        height=None,
        height_label=None,
        slant_label=labelled("l", slant),
        base_label=None,
        edge_labels=True,
        withheld=_values(total_area * rate, total_area, side.value**2, face, 4 * face),
        unknowns=[],
        base_shape="square",
        alt=(
            f"Closed square-based pyramid with base side {side.text}. The slant height "
            f"l = {slant.text} is marked on a triangular face from the apex to the midpoint of a "
            "base edge. Hidden edges are dashed. Not drawn to scale."
        ),
        title="Square-based pyramid",
        dimensions={"base_side": side.as_spec(), "slant_height": slant.as_spec(), "rate": rate},
        findings=_check_answer(total_area * rate, answers, None),
    )


def pyramid_volume_constraint(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    side, height, second_side = (
        q(inputs["base_side"]),
        q(inputs["height"]),
        q(inputs["second_base_side"]),
    )
    volume = side.value**2 * height.value / 3
    second_height = 3 * volume / second_side.value**2
    unit_px = 150 / side.value
    first_h = _clamp(height.value * unit_px, 150, 250)
    second_h = _clamp(first_h * 1.35, 150, 320)
    first_w = side.value * unit_px
    second_w = second_side.value * unit_px
    first_d = first_w * DEPTH_FORESHORTENING
    second_d = second_w * DEPTH_FORESHORTENING
    dy1 = first_d * math.sin(math.radians(RECEDE_DEGREES))
    dy2 = second_d * math.sin(math.radians(RECEDE_DEGREES))
    y0 = 46 + max(first_h + dy1 / 2, second_h + dy2 / 2)
    canvas = _canvas(y0 + 165)
    canvas.caption("same volume", (300, y0 + 92), size=CAPTION_SIZE)
    first = _pyramid(canvas, "a", (125, y0), first_w, first_d, first_h)
    second = _pyramid(canvas, "b", (410, y0), second_w, second_d, second_h)
    for names, label_side, label_height, x_left in (
        (first, side.text, height.text, 125),
        (second, second_side.text, "h", 410),
    ):
        inside = canvas.points[names["O"]]
        canvas.segment_label(label_side, names["P1"], names["P2"], away_from=inside, size=LABEL)
        canvas.length_label(
            label_height,
            names["V"],
            names["O"],
            away_from=canvas.points[names["P1"]],
            directions=((-1, 0.1), (-1, -0.35), (-1, 0.45)),
            size=LABEL,
        )
        del x_left
    relationships = [
        *_pyramid_relationships(first, show_height=True, slant=False),
        *_pyramid_relationships(second, show_height=True, slant=False),
    ]
    spec = _spec(
        canvas,
        kind="pyramid",
        template="pyramid_volume_constraint",
        inputs=inputs,
        dimensions={
            "first": {"base_side": side.as_spec(), "height": height.as_spec()},
            "second": {"base_side": second_side.as_spec()},
        },
        forbidden=_forbid(
            canvas, answers, _values(second_height, volume, side.value**2, second_side.value**2)
        ),
        unknowns=[{"target": f"segment:{second['V']}{second['O']}", "label": "h"}],
        relationships=relationships,
        solids=[
            {"type": "pyramid", "base": "square", "points": first},
            {"type": "pyramid", "base": "square", "points": second},
        ],
    )
    return _done(
        canvas,
        title="Two square-based pyramids",
        alt=(
            f"Two separate square-based pyramids with the same volume. The first has base side "
            f"{side.text} and perpendicular height {height.text}. The second has base side "
            f"{second_side.text} and perpendicular height h. Each height runs from the apex to "
            "the centre of the base. Not drawn to scale."
        ),
        spec=spec,
        findings=_check_answer(second_height, answers, None),
    )


# ------------------------------------------------------------------------------- cones
def _cone_size(radius: float, height: float | None, *, max_rx: float = 170, max_h: float = 300):
    ratio = NEUTRAL_RATIO if height is None else _clamp(height / radius, 0.6, 3.5)
    rx = min(max_rx, max_h / ratio)
    return rx, rx * ratio


def _single_cone(
    *,
    template: str,
    inputs: dict[str, Any],
    answers: Sequence[str],
    radius: Quantity,
    height: Quantity | None,
    slant: Quantity | None,
    height_label: str | None,
    slant_label: str | None,
    withheld: Sequence[str],
    unknowns: list[dict[str, str]],
    alt: str,
    title: str,
    dimensions: dict[str, Any],
    findings: list[str],
) -> Diagram:
    true_height = (
        height.value
        if height
        else (math.sqrt(max(slant.value**2 - radius.value**2, 0.0)) if slant else None)
    )
    rx, height_px = _cone_size(radius.value, true_height)
    top = 50
    cy = top + height_px
    canvas = _canvas(cy + rx * ELLIPSE_RATIO + 110)
    names = _cone(canvas, "", (340, cy), rx, height_px, show_height=height_label is not None)
    canvas.length_label(
        labelled("r", radius),
        "O",
        "R",
        away_from=canvas.points["V"],
        directions=((0.35, 1), (0.8, 1), (-0.1, 1)),
        size=LABEL,
        positions=(0.55, 0.62, 0.48),
        gaps=(6, 10),
    )
    if slant_label:
        canvas.segment_label(slant_label, "V", "R", away_from=canvas.points["O"], size=LABEL)
    if height_label:
        canvas.length_label(
            height_label,
            "V",
            "O",
            away_from=canvas.points["R"],
            directions=((-1, 0.1), (-1, -0.35), (-1, 0.45)),
            size=LABEL,
            positions=(0.5, 0.42, 0.58),
        )
    spec = _spec(
        canvas,
        kind="cone",
        template=template,
        inputs=inputs,
        dimensions=dimensions,
        forbidden=_forbid(canvas, answers, withheld),
        unknowns=unknowns,
        relationships=_cone_relationships(names, ""),
        solids=[{"type": "cone", "orientation": "vertex_up", "points": names}],
    )
    return _done(canvas, title=title, alt=alt, spec=spec, findings=findings)


def cone_volume(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius, height = q(inputs["radius"]), q(inputs["height"])
    volume = PI * radius.value**2 * height.value / 3
    return _single_cone(
        template="cone_volume",
        inputs=inputs,
        answers=answers,
        radius=radius,
        height=height,
        slant=None,
        height_label=labelled("h", height),
        slant_label=None,
        withheld=[*_values(volume), *pi_forms(radius.value**2 * height.value / 3)],
        unknowns=[],
        alt=(
            f"Cone with base radius r = {radius.text} and perpendicular height h = "
            f"{height.text} from the vertex to the centre of the base, right angle marked. The "
            "hidden half of the base is dashed. Not drawn to scale."
        ),
        title="Cone",
        dimensions={"radius": radius.as_spec(), "height": height.as_spec()},
        findings=_check_answer(volume, answers, 1),
    )


def cone_curved_area(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius, slant = q(inputs["radius"]), q(inputs["slant_height"])
    area = PI * radius.value * slant.value
    return _single_cone(
        template="cone_curved_area",
        inputs=inputs,
        answers=answers,
        radius=radius,
        height=None,
        slant=slant,
        height_label=None,
        slant_label=labelled("l", slant),
        withheld=[*_values(area), *pi_forms(radius.value * slant.value)],
        unknowns=[],
        alt=(
            f"Cone with base radius r = {radius.text} and slant height l = {slant.text} marked "
            "along the sloping surface from the vertex to the edge of the base. Not drawn to scale."
        ),
        title="Cone",
        dimensions={"radius": radius.as_spec(), "slant_height": slant.as_spec()},
        findings=_check_answer(area, answers, 1),
    )


def cone_total_area(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius, height = q(inputs["radius"]), q(inputs["height"])
    slant = math.hypot(radius.value, height.value)
    curved, base = PI * radius.value * slant, PI * radius.value**2
    return _single_cone(
        template="cone_total_area",
        inputs=inputs,
        answers=answers,
        radius=radius,
        height=height,
        slant=None,
        height_label=labelled("h", height),
        slant_label=None,
        withheld=[
            *_values(curved + base, curved, base, slant),
            *pi_forms(radius.value * slant + radius.value**2),
            *pi_forms(radius.value * slant),
        ],
        unknowns=[],
        alt=(
            f"Closed cone with base radius r = {radius.text} and perpendicular height h = "
            f"{height.text} from the vertex to the centre of the base, right angle marked. The "
            "slant edge is drawn but not labelled. Not drawn to scale."
        ),
        title="Closed cone",
        dimensions={"radius": radius.as_spec(), "height": height.as_spec()},
        findings=_check_answer(curved + base, answers, 1),
    )


def cone_cylinder_factor(
    inputs: dict[str, Any] | None = None, answers: Sequence[str] = ()
) -> Diagram:
    inputs = inputs or {}
    rx, height_px = 150.0, 270.0
    ry = rx * ELLIPSE_RATIO
    top = 50 + ry
    cy = top + height_px
    canvas = _canvas(cy + ry + 100)
    cx = WIDTH / 2
    canvas.point("T", (cx, top))
    canvas.point("CL", (cx - rx, top))
    canvas.point("CR", (cx + rx, top))
    canvas.point("BL", (cx - rx, cy))
    canvas.point("BR", (cx + rx, cy))
    canvas.fill([(cx - rx, top), (cx + rx, top), (cx + rx, cy), (cx - rx, cy)], FILL_ALT)
    canvas.ellipse("top", "T", rx, ry, hidden_back=False, stroke=LIGHT, width=THIN)
    canvas.segment("CLBL", "CL", "BL", stroke=LIGHT, width=THIN, role="cylinder")
    canvas.segment("CRBR", "CR", "BR", stroke=LIGHT, width=THIN, role="cylinder")
    names = _cone(canvas, "", (cx, cy), rx, height_px, fill=FILL)
    canvas.segment_label("r", "O", "R", away_from=canvas.points["V"], size=LABEL)
    canvas.segment_label(
        "h", "V", "O", away_from=canvas.points["R"], size=LABEL, positions=(0.55, 0.45, 0.65)
    )
    relationships = [
        *_cone_relationships(names, ""),
        {"type": "same_point", "points": ["T", "V"]},
        {"type": "vertical", "points": ["CL", "BL"]},
        {"type": "vertical", "points": ["CR", "BR"]},
        {"type": "same_point", "points": ["BL", "L"]},
        {"type": "same_point", "points": ["BR", "R"]},
    ]
    spec = _spec(
        canvas,
        kind="cone_cylinder",
        template="cone_cylinder_factor",
        inputs=inputs,
        dimensions={"radius": "r", "height": "h"},
        forbidden=_forbid(canvas, answers, ["1/3", "⅓", "one third", "1:3", "3"]),
        unknowns=[],
        relationships=relationships,
        solids=[
            {"type": "cylinder", "points": {"top": "T", "base": "O"}},
            {"type": "cone", "orientation": "vertex_up", "points": names},
        ],
    )
    return _done(
        canvas,
        title="Cone inside a cylinder",
        alt=(
            "Cone drawn inside a cylinder. They share the same circular base of radius r and the "
            "same perpendicular height h; the cone's vertex is at the centre of the cylinder's "
            "top. Not drawn to scale."
        ),
        spec=spec,
    )


def liquid_depth(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    height = q(inputs["height"])
    fraction = float(inputs["volume_fraction"])
    depth = height.value * fraction ** (1 / 3)
    rx, height_px = 120.0, 300.0
    ry = rx * ELLIPSE_RATIO
    top = 46 + ry
    canvas = _canvas(top + height_px + 90)
    cx = 270.0
    names = _cone(
        canvas,
        "",
        (cx, top),
        rx,
        height_px,
        inverted=True,
        show_radius=False,
        open_top=True,
        fill=FILL_ALT,
    )
    level = 0.62  # neutral liquid level; the true depth is withheld
    surface_y = top + height_px * (1 - level)
    lrx = rx * level
    canvas.point("W", (cx, surface_y))
    canvas.point("WL", (cx - lrx, surface_y))
    canvas.point("WR", (cx + lrx, surface_y))
    v = canvas.points["V"]
    canvas.fill(
        [
            (cx - lrx, surface_y),
            v,
            (cx + lrx, surface_y),
            *ellipse_points(cx, surface_y, lrx, lrx * ELLIPSE_RATIO, 360, 180),
        ],
        LIQUID,
    )
    canvas.ellipse(
        "liquid",
        "W",
        lrx,
        lrx * ELLIPSE_RATIO,
        hidden_back=False,
        stroke=LIQUID_INK,
        width=THIN,
        fill=LIQUID,
    )
    canvas.dimension(
        labelled("h", height),
        "O",
        "V",
        normal=(1, 0),
        offset=rx + 28,
        size=LABEL,
        extension_from=("R", "V"),
    )
    canvas.dimension(
        "depth",
        "W",
        "V",
        normal=(-1, 0),
        offset=lrx + 40,
        size=LABEL,
        target="segment:WV",
        extension_from=("WL", "V"),
    )
    relationships = [
        *_cone_relationships(names, ""),
        {"type": "vertical", "points": ["W", "V"]},
        {"type": "collinear", "points": ["V", "WL", "L"]},
        {"type": "collinear", "points": ["V", "WR", "R"]},
        {"type": "ellipse_centre", "ellipse": "liquid", "point": "W"},
    ]
    findings = _check_answer(depth, answers, None)
    findings.append(
        "The prompt does not say that the cone is held with its vertex pointing down; liquid "
        "forms a smaller cone at the tip only in that orientation. Add this to the question "
        "text (the diagram shows it)."
    )
    spec = _spec(
        canvas,
        kind="inverted_cone_liquid",
        template="liquid_depth",
        inputs=inputs,
        dimensions={"height": height.as_spec(), "volume_fraction": fraction},
        forbidden=_forbid(canvas, answers, [*_values(depth), "1/2", "½", "0.5", "half"]),
        unknowns=[{"target": "segment:WV", "label": "depth"}],
        relationships=relationships,
        solids=[
            {"type": "cone", "orientation": "vertex_down", "points": names, "liquid_surface": "W"}
        ],
    )
    spec["drawn_to_scale"] = {"liquid_depth": False}
    return _done(
        canvas,
        title="Cone held vertex down with liquid",
        alt=(
            f"Conical container held with its vertex pointing down, height h = {height.text}. "
            f"Liquid fills {_fraction_words(fraction)} of the volume and forms a smaller cone at "
            "the tip; its depth is marked but not given. Not drawn to scale."
        ),
        spec=spec,
        findings=findings,
    )


def _fraction_words(fraction: float) -> str:
    known = {
        1 / 8: "one eighth",
        1 / 27: "one twenty-seventh",
        1 / 64: "one sixty-fourth",
        1 / 2: "one half",
    }
    for value, words in known.items():
        if math.isclose(value, fraction):
            return words
    return number(fraction)


# ----------------------------------------------------------------------------- spheres
def _single_sphere(
    *,
    template: str,
    inputs: dict[str, Any],
    answers: Sequence[str],
    label: str,
    diameter: bool,
    withheld: Sequence[str],
    alt: str,
    title: str,
    dimensions: dict[str, Any],
    findings: list[str],
) -> Diagram:
    radius_px = 160.0
    canvas = _canvas(2 * radius_px + 140)
    centre = (WIDTH / 2, 50 + radius_px)
    names = _sphere(
        canvas,
        "",
        centre,
        radius_px,
        radius_degrees=None if diameter else 35.0,
        diameter_degrees=0.0 if diameter else None,
    )
    if diameter:
        canvas.segment_label(
            label,
            "D1",
            "D2",
            away_from=(centre[0], centre[1] + 100),
            size=LABEL,
            positions=(0.5, 0.45, 0.55),
            gaps=(6, 9),
        )
    else:
        canvas.segment_label(
            label, "O", "E", away_from=(centre[0] + 50, centre[1] + 80), size=LABEL
        )
    spec = _spec(
        canvas,
        kind="sphere",
        template=template,
        inputs=inputs,
        dimensions=dimensions,
        forbidden=_forbid(canvas, answers, withheld),
        unknowns=[],
        relationships=_sphere_relationships(names, "", radius=not diameter, diameter=diameter),
        solids=[{"type": "sphere", "points": names, "given": "diameter" if diameter else "radius"}],
    )
    return _done(canvas, title=title, alt=alt, spec=spec, findings=findings)


def sphere_surface_area(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius = q(inputs["radius"])
    k = 4 * radius.value**2
    return _single_sphere(
        template="sphere_surface_area",
        inputs=inputs,
        answers=answers,
        label=labelled("r", radius),
        diameter=False,
        withheld=[*_values(k), *pi_forms(k)],
        alt=f"Sphere with radius r = {radius.text} drawn from the centre to the surface. Not drawn to scale.",
        title="Sphere",
        dimensions={"radius": radius.as_spec()},
        findings=_check_answer(k, answers, None),
    )


def sphere_volume_radius(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """A sphere volume, possibly converted to another unit (for example cm to m³)."""
    radius = q(inputs["radius"])
    target_unit = inputs.get("answer_unit")
    volume = 4 / 3 * PI * radius.value**3
    withheld = [*_values(volume), *pi_forms(4 / 3 * radius.value**3)]
    places = 1
    if target_unit == "m³" and radius.unit == "cm":
        metres = radius.value / 100
        converted = 4 / 3 * PI * metres**3
        withheld = [*_values(converted), f"{number(metres)} m", *withheld]
        expected = converted
    else:
        expected = volume
    return _single_sphere(
        template="sphere_volume_radius",
        inputs=inputs,
        answers=answers,
        label=labelled("r", radius),
        diameter=False,
        withheld=withheld,
        alt=f"Sphere with radius r = {radius.text} drawn from the centre to the surface. Not drawn to scale.",
        title="Sphere",
        dimensions={"radius": radius.as_spec(), "answer_unit": target_unit},
        findings=_check_answer(expected, answers, places),
    )


def sphere_volume_diameter(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    diameter = q(inputs["diameter"])
    radius = diameter.value / 2
    volume = 4 / 3 * PI * radius**3
    return _single_sphere(
        template="sphere_volume_diameter",
        inputs=inputs,
        answers=answers,
        label=labelled("d", diameter),
        diameter=True,
        withheld=[
            *_values(volume),
            *pi_forms(4 / 3 * radius**3),
            number(radius),
            f"r = {number(radius)}",
        ],
        alt=(
            f"Sphere with a full diameter d = {diameter.text} drawn through the centre from one "
            "side of the surface to the other. Not drawn to scale."
        ),
        title="Sphere",
        dimensions={"diameter": diameter.as_spec()},
        findings=_check_answer(volume, answers, 1),
    )


def _concentric(
    *,
    template: str,
    inputs: dict[str, Any],
    answers: Sequence[str],
    outer: Quantity,
    inner: Quantity,
    inner_name: str,
    withheld: Sequence[str],
    alt: str,
    title: str,
    findings: list[str],
) -> Diagram:
    outer_px = 165.0
    inner_px = outer_px * inner.value / outer.value
    canvas = _canvas(2 * outer_px + 140)
    centre = (WIDTH / 2, 50 + outer_px)
    names = _sphere(canvas, "", centre, outer_px, equator=False, radius_degrees=None)
    canvas.circle("inner", "O", inner_px, fill="#ffffff", stroke=INK, width=THIN, hidden=True)
    outer_angle = math.radians(40.0)
    canvas.point(
        "E",
        (
            centre[0] + outer_px * math.cos(outer_angle),
            centre[1] - outer_px * math.sin(outer_angle),
        ),
    )
    canvas.segment("OE", "O", "E", stroke=ACCENT, width=THIN + 1)
    angle = math.radians(220.0)
    canvas.point(
        "I", (centre[0] + inner_px * math.cos(angle), centre[1] - inner_px * math.sin(angle))
    )
    canvas.segment("OI", "O", "I", stroke=ACCENT, width=THIN + 1)
    canvas.dot("O", 4, ACCENT)
    canvas.length_label(
        labelled("R", outer),
        "O",
        "E",
        away_from=(centre[0] + 60, centre[1] + 60),
        directions=((0.3, -1), (1, -0.4), (-0.3, -1)),
        size=LABEL,
        positions=(0.78, 0.84, 0.72, 0.9),
        gaps=(6, 10, 16),
    )
    canvas.length_label(
        f"{inner_name}{labelled('r', inner)}",
        "O",
        "I",
        away_from=(centre[0] + 60, centre[1] - 60),
        directions=((-0.55, 1), (-1, 0.6), (0.3, 1)),
        size=LABEL,
        positions=(0.5, 0.42, 0.6),
    )
    relationships = [
        *_sphere_relationships(names, "", radius=True, diameter=False),
        {"type": "circle_centre", "circle": "inner", "point": "O"},
        {"type": "on_circle", "circle": "inner", "points": ["I"]},
        {"type": "hidden_circle", "circle": "inner"},
        {
            "type": "circle_ratio",
            "circles": ["inner", "sphere"],
            "value": round(inner.value / outer.value, 4),
            "tolerance": 0.01,
        },
    ]
    spec = _spec(
        canvas,
        kind="hollow_sphere",
        template=template,
        inputs=inputs,
        dimensions={"outer_radius": outer.as_spec(), "inner_radius": inner.as_spec()},
        forbidden=_forbid(canvas, answers, withheld),
        unknowns=[],
        relationships=relationships,
        solids=[{"type": "sphere", "points": names, "inner_sphere": "inner"}],
    )
    return _done(canvas, title=title, alt=alt, spec=spec, findings=findings)


def hollow_shell(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    outer, inner = q(inputs["outer_radius"]), q(inputs["inner_radius"])
    big, small = 4 / 3 * PI * outer.value**3, 4 / 3 * PI * inner.value**3
    return _concentric(
        template="hollow_shell",
        inputs=inputs,
        answers=answers,
        outer=outer,
        inner=inner,
        inner_name="",
        withheld=[
            *_values(big - small, big, small),
            *pi_forms(4 / 3 * (outer.value**3 - inner.value**3)),
        ],
        alt=(
            f"Hollow spherical shell: an outer sphere of radius R = {outer.text} with a dashed "
            f"concentric inner sphere of radius r = {inner.text}. Not drawn to scale."
        ),
        title="Hollow spherical shell",
        findings=_check_answer(big - small, answers, 1),
    )


def sphere_core_removed(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    outer, inner = q(inputs["outer_radius"]), q(inputs["inner_radius"])
    remaining = 100 * (1 - (inner.value / outer.value) ** 3)
    return _concentric(
        template="sphere_core_removed",
        inputs=inputs,
        answers=answers,
        outer=outer,
        inner=inner,
        inner_name="core ",
        withheld=[
            *_values(remaining, 100 - remaining),
            "1/8",
            "7/8",
            *_values(4 / 3 * PI * outer.value**3, 4 / 3 * PI * inner.value**3),
        ],
        alt=(
            f"Sphere of radius R = {outer.text} with a dashed concentric spherical core of radius "
            f"r = {inner.text} removed. Not drawn to scale."
        ),
        title="Sphere with a core removed",
        findings=_check_answer(remaining, answers, 1),
    )


def sphere_percentage_change(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    percent = float(inputs["percent"])
    factor = 1 + percent / 100
    large = min(150.0, 270 / (1 + 1 / factor) - 10)
    small = large / factor
    canvas = _canvas(50 + 2 * large + 150)
    cy = 50 + large
    first_x, second_x = 30 + small, WIDTH - 30 - large
    canvas.caption("radius r", (first_x, cy + large + 40))
    canvas.caption(f"r increased by {number(percent)}%", (second_x, cy + large + 40))
    first = _sphere(canvas, "a", (first_x, cy), small, radius_degrees=40.0)
    second = _sphere(canvas, "b", (second_x, cy), large, radius_degrees=40.0)
    canvas.segment_label("r", first["O"], first["E"], away_from=(first_x, cy + 80), size=LABEL)
    canvas.segment_label("R", second["O"], second["E"], away_from=(second_x, cy + 80), size=LABEL)
    relationships = [
        *_sphere_relationships(first, "a", radius=True, diameter=False),
        *_sphere_relationships(second, "b", radius=True, diameter=False),
        {
            "type": "circle_ratio",
            "circles": ["bsphere", "asphere"],
            "value": round(factor, 4),
            "tolerance": 0.01,
        },
    ]
    volume_factor = factor**3
    spec = _spec(
        canvas,
        kind="sphere",
        template="sphere_percentage_change",
        inputs=inputs,
        dimensions={"radius_increase_percent": percent},
        forbidden=_forbid(
            canvas,
            answers,
            [
                *_values(100 * (volume_factor - 1), volume_factor),
                f"{number(factor)}³",
                f"{number(factor)}r",
            ],
        ),
        unknowns=[],
        relationships=relationships,
        solids=[{"type": "sphere", "points": first}, {"type": "sphere", "points": second}],
    )
    return _done(
        canvas,
        title="Sphere before and after enlargement",
        alt=(
            f"Two spheres side by side: the original with radius r, and the enlarged sphere with "
            f"radius R, which is r increased by {number(percent)}%. Not drawn to scale."
        ),
        spec=spec,
        findings=_check_answer(100 * (volume_factor - 1), answers, 1),
    )


def hemisphere_curved_area(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius = q(inputs["radius"])
    k = 2 * radius.value**2
    r_px = 190.0
    canvas = _canvas(60 + r_px * ELLIPSE_RATIO + r_px + 110)
    centre = (WIDTH / 2, 60 + r_px * ELLIPSE_RATIO)
    names = _hemisphere(canvas, "", centre, r_px, open_bowl=True)
    canvas.length_label(
        labelled("r", radius),
        "O",
        "R",
        away_from=(centre[0], centre[1] + 100),
        directions=((0.6, -1), (0.2, -1), (1, -0.5)),
        size=LABEL,
        positions=(0.55, 0.5, 0.6),
        gaps=(5, 8),
    )
    spec = _spec(
        canvas,
        kind="hemisphere",
        template="hemisphere_curved_area",
        inputs=inputs,
        dimensions={"radius": radius.as_spec(), "open": True},
        forbidden=_forbid(canvas, answers, [*_values(k), *pi_forms(k)]),
        unknowns=[],
        relationships=[
            {"type": "ellipse_centre", "ellipse": "rim", "point": "O"},
            {"type": "on_ellipse", "ellipse": "rim", "points": ["R"]},
        ],
        solids=[{"type": "hemisphere", "open": True, "points": names}],
    )
    return _done(
        canvas,
        title="Open hemisphere",
        alt=(
            f"Open hemisphere (a bowl) with radius r = {radius.text} drawn from the centre of the "
            "rim to its edge. Not drawn to scale."
        ),
        spec=spec,
        findings=_check_answer(k, answers, None),
    )


# --------------------------------------------------------------------------- composites
def _cone_on_hemisphere(
    *,
    template: str,
    inputs: dict[str, Any],
    answers: Sequence[str],
    radius: Quantity,
    height: Quantity | None,
    slant: Quantity | None,
    withheld: Sequence[str],
    alt: str,
    findings: list[str],
    dimensions: dict[str, Any],
) -> Diagram:
    true_height = height.value if height else math.sqrt(max(slant.value**2 - radius.value**2, 0.0))
    ratio = _clamp(true_height / radius.value, 0.6, 3.0)
    rx = min(150.0, 250 / ratio)
    height_px = rx * ratio
    top = 46
    cy = top + height_px
    canvas = _canvas(cy + rx + 100)
    cx = 330.0
    _hemisphere(
        canvas, "h", (cx, cy), rx, open_bowl=False, show_radius=False, seam_hidden_back=True
    )
    names = _cone(canvas, "", (cx, cy), rx, height_px, show_height=height is not None, fill=FILL)
    canvas.length_label(
        labelled("r", radius),
        "O",
        "R",
        away_from=canvas.points["V"],
        directions=((1, 0.5), (1, 0.15), (1, 0.9)),
        size=LABEL,
        positions=(0.55, 0.62, 0.48),
        gaps=(6, 10),
    )
    if height is not None:
        canvas.length_label(
            labelled("h", height),
            "V",
            "O",
            away_from=canvas.points["R"],
            directions=((-1, 0.1), (-1, -0.35), (-1, 0.45)),
            size=LABEL,
        )
    if slant is not None:
        canvas.segment_label(
            labelled("l", slant), "V", "R", away_from=canvas.points["O"], size=LABEL
        )
    relationships = [
        *_cone_relationships(names, ""),
        {"type": "same_point", "points": ["hO", "O"]},
        {"type": "same_point", "points": ["hR", "R"]},
        {"type": "same_point", "points": ["hL", "L"]},
    ]
    spec = _spec(
        canvas,
        kind="cone_hemisphere",
        template=template,
        inputs=inputs,
        dimensions=dimensions,
        forbidden=_forbid(canvas, answers, withheld),
        unknowns=[],
        relationships=relationships,
        solids=[
            {"type": "cone", "orientation": "vertex_up", "points": names},
            {"type": "hemisphere", "open": False, "points": {"O": "hO", "L": "hL", "R": "hR"}},
        ],
    )
    return _done(canvas, title="Cone joined to a hemisphere", alt=alt, spec=spec, findings=findings)


def cone_hemisphere_volume(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius, height = q(inputs["radius"]), q(inputs["height"])
    cone = PI * radius.value**2 * height.value / 3
    half = 2 / 3 * PI * radius.value**3
    return _cone_on_hemisphere(
        template="cone_hemisphere_volume",
        inputs=inputs,
        answers=answers,
        radius=radius,
        height=height,
        slant=None,
        withheld=[*_values(cone + half, cone, half)],
        alt=(
            f"Solid made of a cone joined to a hemisphere of the same radius r = {radius.text}. "
            f"The cone's perpendicular height is h = {height.text}. The joining circle's hidden "
            "half is dashed. Not drawn to scale."
        ),
        findings=_check_answer(cone + half, answers, 1),
        dimensions={"radius": radius.as_spec(), "cone_height": height.as_spec()},
    )


def cone_hemisphere_area(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius, slant = q(inputs["radius"]), q(inputs["slant_height"])
    curved = PI * radius.value * slant.value
    bowl = 2 * PI * radius.value**2
    return _cone_on_hemisphere(
        template="cone_hemisphere_area",
        inputs=inputs,
        answers=answers,
        radius=radius,
        height=None,
        slant=slant,
        withheld=[
            *_values(curved + bowl, curved, bowl),
            *pi_forms(radius.value * slant.value + 2 * radius.value**2),
        ],
        alt=(
            f"Solid made of a cone joined base to base with a hemisphere of radius r = "
            f"{radius.text}. The cone's slant height is l = {slant.text}. The joined circular "
            "faces are hidden inside the solid. Not drawn to scale."
        ),
        findings=_check_answer(curved + bowl, answers, 1),
        dimensions={"radius": radius.as_spec(), "slant_height": slant.as_spec()},
    )


def _side_by_side_cone_sphere(
    *,
    template: str,
    inputs: dict[str, Any],
    answers: Sequence[str],
    sphere_radius: Quantity,
    cone_radius: Quantity,
    cone_height: Quantity | None,
    sphere_caption: str,
    cone_caption: str,
    withheld: Sequence[str],
    unknowns: list[dict[str, str]],
    alt: str,
    title: str,
    findings: list[str],
    dimensions: dict[str, Any],
) -> Diagram:
    unit_px = 95 / max(sphere_radius.value, cone_radius.value)
    sphere_px = sphere_radius.value * unit_px
    cone_rx = cone_radius.value * unit_px
    if cone_height is None:
        cone_h = cone_rx * NEUTRAL_RATIO
    else:
        cone_h = cone_height.value * unit_px
    cone_h = _clamp(cone_h, 120, 300)
    figure_height = max(2 * sphere_px, cone_h + cone_rx * ELLIPSE_RATIO)
    top = 50
    canvas = _canvas(top + figure_height + 160)
    base_y = top + figure_height
    canvas.caption(sphere_caption, (130, base_y + 96))
    canvas.caption(cone_caption, (465, base_y + 96))
    sphere = _sphere(canvas, "s", (130, base_y - sphere_px), sphere_px, radius_degrees=40.0)
    cone = _cone(
        canvas, "c", (465, base_y - cone_rx * ELLIPSE_RATIO), cone_rx, cone_h, show_height=True
    )
    canvas.length_label(
        f"r = {sphere_radius.text}",
        sphere["O"],
        sphere["E"],
        away_from=(130, base_y),
        directions=((0.2, -1), (-0.4, -1), (0.8, -1)),
        size=LABEL,
        positions=(0.5, 0.42, 0.58, 0.66),
    )
    canvas.length_label(
        f"r = {cone_radius.text}",
        cone["O"],
        cone["R"],
        away_from=canvas.points[cone["V"]],
        directions=((0.3, 1), (-0.3, 1), (0.8, 1)),
        size=LABEL,
        positions=(0.55, 0.62),
        gaps=(6, 10),
    )
    canvas.length_label(
        f"h = {cone_height.text}" if cone_height else "h",
        cone["V"],
        cone["O"],
        away_from=canvas.points[cone["R"]],
        directions=((-1, 0.1), (-1, -0.3), (-1, 0.4)),
        size=LABEL,
    )
    relationships = [
        *_sphere_relationships(sphere, "s", radius=True, diameter=False),
        *_cone_relationships(cone, "c"),
    ]
    spec = _spec(
        canvas,
        kind="separate_solids",
        template=template,
        inputs=inputs,
        dimensions=dimensions,
        forbidden=_forbid(canvas, answers, withheld),
        unknowns=unknowns,
        relationships=relationships,
        solids=[
            {"type": "sphere", "points": sphere},
            {"type": "cone", "orientation": "vertex_up", "points": cone},
        ],
    )
    return _done(canvas, title=title, alt=alt, spec=spec, findings=findings)


def equal_volume_cone_sphere(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    radius = q(inputs["radius"])
    volume = 4 / 3 * PI * radius.value**3
    height = 4 * radius.value
    return _side_by_side_cone_sphere(
        template="equal_volume_cone_sphere",
        inputs=inputs,
        answers=answers,
        sphere_radius=radius,
        cone_radius=radius,
        cone_height=None,
        sphere_caption="sphere",
        cone_caption="cone",
        withheld=[*_values(height, volume), *pi_forms(4 / 3 * radius.value**3)],
        unknowns=[{"target": "segment:cVcO", "label": "h"}],
        alt=(
            f"A sphere and a separate cone side by side, each with radius {radius.text}. The cone "
            "has the same volume as the sphere; its perpendicular height h is marked but not "
            "given. Not drawn to scale."
        ),
        title="Sphere and cone",
        findings=_check_answer(height, answers, None),
        dimensions={"radius": radius.as_spec()},
    )


def recast_spheres_cones(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    count = int(inputs["sphere_count"])
    sphere, cone_r, cone_h = (
        q(inputs["sphere_radius"]),
        q(inputs["cone_radius"]),
        q(inputs["cone_height"]),
    )
    sphere_volume = 4 / 3 * PI * sphere.value**3
    cone_volume = PI * cone_r.value**2 * cone_h.value / 3
    cones = math.floor(count * sphere_volume / cone_volume + 1e-9)
    return _side_by_side_cone_sphere(
        template="recast_spheres_cones",
        inputs=inputs,
        answers=answers,
        sphere_radius=sphere,
        cone_radius=cone_r,
        cone_height=cone_h,
        sphere_caption=f"{count} spheres",
        cone_caption="identical cones",
        withheld=[
            *_values(cones, count * sphere_volume, sphere_volume, cone_volume),
            *pi_forms(4 / 3 * sphere.value**3),
            *pi_forms(count * 4 / 3 * sphere.value**3),
            *pi_forms(cone_r.value**2 * cone_h.value / 3),
        ],
        unknowns=[],
        alt=(
            f"{_count_words(count).capitalize()} separate solid spheres, each of radius "
            f"{sphere.text}, are melted and recast into identical separate cones of radius "
            f"{cone_r.text} and perpendicular height {cone_h.text}. One sphere and one cone are "
            "drawn. Not drawn to scale."
        ),
        title="Spheres recast into cones",
        findings=_check_answer(cones, answers, None),
        dimensions={
            "sphere_count": count,
            "sphere_radius": sphere.as_spec(),
            "cone_radius": cone_r.as_spec(),
            "cone_height": cone_h.as_spec(),
        },
    )


def _count_words(count: int) -> str:
    words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 8: "eight", 10: "ten"}
    return words.get(count, str(count))


# ----------------------------------------------------------------------------- lessons
def lesson_pyramid(inputs: dict[str, Any] | None = None, answers: Sequence[str] = ()) -> Diagram:
    inputs = inputs or {}
    width, depth_px, height_px = 300.0, 165.0, 300.0
    dy = depth_px * math.sin(math.radians(RECEDE_DEGREES))
    dx = depth_px * math.cos(math.radians(RECEDE_DEGREES))
    y0 = 46 + height_px + dy / 2
    canvas = _canvas(y0 + 158)
    x0 = (WIDTH - width - dx) / 2
    names = _pyramid(canvas, "", (x0, y0), width, depth_px, height_px, slant=True)
    inside = canvas.points["O"]
    canvas.segment_label("a", "P1", "P2", away_from=inside, size=LABEL, positions=(0.25, 0.2, 0.3))
    canvas.segment_label("a", "P2", "P3", away_from=inside, size=LABEL)
    canvas.segment_label(
        "h", "V", "O", away_from=canvas.points["P1"], size=LABEL, positions=(0.5, 0.42, 0.58)
    )
    canvas.length_label(
        "l",
        "V",
        "S",
        away_from=canvas.points["P2"],
        size=LABEL,
        positions=(0.6, 0.5, 0.7),
        directions=((-1, 0.1), (-1, -0.35), (-1, 0.45)),
    )
    canvas.caption("V = ⅓ × base area × h", (300, y0 + 82))
    spec = _spec(
        canvas,
        kind="pyramid",
        template="lesson_pyramid",
        inputs=inputs,
        dimensions={"base_side": "a", "height": "h", "slant_height": "l"},
        forbidden=([], []),
        unknowns=[],
        relationships=[*_pyramid_relationships(names, show_height=True, slant=True)],
        solids=[{"type": "pyramid", "base": "square", "points": names}],
    )
    return _done(
        canvas,
        title="Square-based pyramid",
        alt=(
            "Square-based pyramid with base side a. The perpendicular height h runs from the apex "
            "to the centre of the base with the right angle marked, and the slant height l runs "
            "down a triangular face to the midpoint of a base edge. Hidden edges are dashed. "
            "V = ⅓ × base area × h."
        ),
        spec=spec,
    )


def lesson_cone(inputs: dict[str, Any] | None = None, answers: Sequence[str] = ()) -> Diagram:
    inputs = inputs or {}
    rx, height_px = 170.0, 290.0
    top = 50
    cy = top + height_px
    canvas = _canvas(cy + rx * ELLIPSE_RATIO + 140)
    names = _cone(canvas, "", (WIDTH / 2 - 20, cy), rx, height_px)
    canvas.segment_label("r", "O", "R", away_from=canvas.points["V"], size=LABEL)
    canvas.segment_label("h", "V", "O", away_from=canvas.points["R"], size=LABEL)
    canvas.segment_label("l", "V", "R", away_from=canvas.points["O"], size=LABEL)
    canvas.caption("l² = r² + h²", (300, cy + rx * ELLIPSE_RATIO + 62))
    spec = _spec(
        canvas,
        kind="cone",
        template="lesson_cone",
        inputs=inputs,
        dimensions={"radius": "r", "height": "h", "slant_height": "l"},
        forbidden=([], []),
        unknowns=[],
        relationships=_cone_relationships(names, ""),
        solids=[{"type": "cone", "orientation": "vertex_up", "points": names}],
    )
    return _done(
        canvas,
        title="Right circular cone",
        alt=(
            "Cone with base radius r, perpendicular height h from the vertex to the centre of the "
            "base with the right angle marked, and slant height l along the sloping surface, "
            "with l² = r² + h². The hidden half of the base is dashed."
        ),
        spec=spec,
    )


def lesson_sphere(inputs: dict[str, Any] | None = None, answers: Sequence[str] = ()) -> Diagram:
    inputs = inputs or {}
    radius_px = 120.0
    canvas = _canvas(50 + 2 * radius_px + 130)
    cy = 50 + radius_px
    sphere = _sphere(canvas, "s", (160, cy), radius_px, radius_degrees=35.0)
    half = _hemisphere(
        canvas, "h", (440, cy - 10), radius_px, open_bowl=False, seam_hidden_back=False
    )
    canvas.segment_label("r", sphere["O"], sphere["E"], away_from=(160, cy + 60), size=LABEL)
    canvas.segment_label("r", half["O"], half["R"], away_from=(440, cy + 80), size=LABEL)
    canvas.caption("sphere", (160, cy + radius_px + 42))
    canvas.caption("hemisphere", (440, cy + radius_px + 42))
    spec = _spec(
        canvas,
        kind="sphere",
        template="lesson_sphere",
        inputs=inputs,
        dimensions={"radius": "r"},
        forbidden=([], []),
        unknowns=[],
        relationships=[
            *_sphere_relationships(sphere, "s", radius=True, diameter=False),
            {"type": "ellipse_centre", "ellipse": "hrim", "point": "hO"},
            {"type": "on_ellipse", "ellipse": "hrim", "points": ["hR"]},
        ],
        solids=[
            {"type": "sphere", "points": sphere},
            {"type": "hemisphere", "open": False, "points": half},
        ],
    )
    return _done(
        canvas,
        title="Sphere and hemisphere",
        alt=(
            "A sphere with radius r from its centre to the surface, and a solid hemisphere with "
            "radius r from the centre of its flat circular face to the edge."
        ),
        spec=spec,
    )


TEMPLATES: dict[str, Callable[..., Diagram]] = {
    "rectangular_pyramid_volume": rectangular_pyramid_volume,
    "pyramid_base_area_volume": pyramid_base_area_volume,
    "pyramid_height": pyramid_height,
    "pyramid_covering_cost": pyramid_covering_cost,
    "pyramid_volume_constraint": pyramid_volume_constraint,
    "cone_volume": cone_volume,
    "cone_curved_area": cone_curved_area,
    "cone_total_area": cone_total_area,
    "cone_cylinder_factor": cone_cylinder_factor,
    "liquid_depth": liquid_depth,
    "sphere_surface_area": sphere_surface_area,
    "sphere_volume_radius": sphere_volume_radius,
    "sphere_volume_diameter": sphere_volume_diameter,
    "hollow_shell": hollow_shell,
    "sphere_core_removed": sphere_core_removed,
    "sphere_percentage_change": sphere_percentage_change,
    "hemisphere_curved_area": hemisphere_curved_area,
    "cone_hemisphere_volume": cone_hemisphere_volume,
    "cone_hemisphere_area": cone_hemisphere_area,
    "equal_volume_cone_sphere": equal_volume_cone_sphere,
    "recast_spheres_cones": recast_spheres_cones,
    "lesson_pyramid": lesson_pyramid,
    "lesson_cone": lesson_cone,
    "lesson_sphere": lesson_sphere,
}

__all__ = ["TEMPLATES", "join_values"]
