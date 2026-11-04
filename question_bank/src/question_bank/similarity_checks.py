"""Checks for the Sec 2 G2 figures: congruence, similarity, enlargement and scale.

Every check measures the coordinates the SVG draws. These run only for the similarity renderer.
Each defect type the G2 audit reported has a code:

- ``geometry_figure_proportion``: figures declared congruent or similar that do not measure so,
  lengths not in the proportion of their stated values, or an enlargement off its factor.
- ``geometry_figure_shape``: a figure with the wrong number of sides for the question's shape.
- ``geometry_correspondence``: ticks or matching arcs on parts that do not correspond.
- ``geometry_given_mismatch``: a number the question does not state, or a stated number missing.
- ``geometry_arrow``: a scaling arrow that runs the wrong way or disagrees with what is drawn.
- ``geometry_grid``: a point, grid line or axis number off its coordinate.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from itertools import combinations
from typing import Any

from .svg_metrics import path_polylines

PROPORTION_TOLERANCE = 0.02
LENGTH_TOLERANCE = 1.5
ANGLE_TOLERANCE = 1.0
_NUMBER = re.compile(r"(?<![\d.])\d+(?:\.\d+)?")
# What the alternative text of each figure must name.
FIGURE_WORDS = {
    "congruent_triangles": "triangles",
    "congruent_pentagons": "pentagons",
    "similar_triangles": "triangles",
    "similar_polygons": "polygons",
    "nested_triangles": "triangle",
    "shared_side": "triangles",
    "shadow": "shadow",
    "mirror": "mirror",
    "survey": "river",
    "enlargement_line": "line",
    "coordinate_grid": "axes",
    "scale_rectangles": "rectangle",
    "scale_segments": "segment",
}
# Words in a question that fix the side count of the shape it is about.
SHAPE_SIDES = {
    "triangle": 3,
    "triangles": 3,
    "triangular": 3,
    "rectangle": 4,
    "rectangular": 4,
    "pentagon": 5,
    "pentagons": 5,
}


def _distance(first, second) -> float:
    return math.hypot(first[0] - second[0], first[1] - second[1])


def _figure(checked, name: str) -> tuple[list[str], list[tuple[float, float]]] | None:
    names = (checked.spec.get("figures") or {}).get(name)
    if not names or any(item not in checked.points for item in names):
        checked.add("geometry_figure_proportion", f"Figure {name} uses undeclared points.")
        return None
    return names, [checked.points[item] for item in names]


def _pair(checked, relation) -> tuple[tuple, tuple] | None:
    names = relation.get("figures") or []
    if len(names) != 2:
        checked.add("geometry_figure_proportion", f"Relation {relation} needs two figures.")
        return None
    first, second = _figure(checked, names[0]), _figure(checked, names[1])
    if first is None or second is None:
        return None
    if len(first[0]) != len(second[0]):
        checked.add(
            "geometry_figure_shape", f"Figures {names} have different numbers of vertices."
        )
        return None
    return first, second


def _congruent(checked, relation) -> None:
    figures = _pair(checked, relation)
    if figures is None:
        return
    (names, first), (others, second) = figures
    for i, j in combinations(range(len(names)), 2):
        a, b = _distance(first[i], first[j]), _distance(second[i], second[j])
        if abs(a - b) > LENGTH_TOLERANCE:
            checked.add(
                "geometry_figure_proportion",
                f"Figures {relation['figures']} are declared congruent, but {names[i]}{names[j]} "
                f"measures {a:.1f} and {others[i]}{others[j]} measures {b:.1f}.",
            )


def _similar(checked, relation) -> None:
    figures = _pair(checked, relation)
    if figures is None:
        return
    (names, first), (_, second) = figures
    ratios = []
    for i, j in combinations(range(len(names)), 2):
        size = _distance(first[i], first[j])
        if size == 0:
            checked.add("geometry_figure_proportion", f"Figure {names} has coincident vertices.")
            return
        ratios.append(_distance(second[i], second[j]) / size)
    if max(ratios) - min(ratios) > PROPORTION_TOLERANCE * max(ratios):
        checked.add(
            "geometry_figure_proportion",
            f"Figures {relation['figures']} are declared similar, but their side ratios run from "
            f"{min(ratios):.3f} to {max(ratios):.3f}.",
        )
        return
    if "value" in relation:
        value = float(relation["value"])
        if abs(ratios[0] - value) > PROPORTION_TOLERANCE * value:
            checked.add(
                "geometry_figure_proportion",
                f"Figures {relation['figures']} are drawn at factor {ratios[0]:.3f}, declared "
                f"{value:g}.",
            )


def _to_scale(checked, relation) -> None:
    """Lengths with stated values must be drawn in the proportion of those values."""
    scales = []
    for names, value in relation.get("lengths") or []:
        first, second = checked.points.get(names[0]), checked.points.get(names[1])
        if first is None or second is None or not value:
            checked.add("geometry_figure_proportion", f"Length {names} uses undeclared points.")
            return
        scales.append((names, _distance(first, second) / float(value)))
    if len(scales) < 2:
        checked.add("geometry_figure_proportion", "A scale relation needs at least two lengths.")
        return
    drawn = [scale for _, scale in scales]
    if max(drawn) - min(drawn) > PROPORTION_TOLERANCE * max(drawn):
        worst = max(scales, key=lambda item: abs(item[1] - drawn[0]))
        checked.add(
            "geometry_figure_proportion",
            f"Length {worst[0]} is out of proportion with its stated value "
            f"({min(drawn):.2f} to {max(drawn):.2f} units per stated unit).",
        )


def _enlargement(checked, relation) -> None:
    centre = checked.points.get(relation.get("centre"))
    value = float(relation.get("value", 0))
    for name, image in relation.get("pairs") or []:
        a, b = checked.points.get(name), checked.points.get(image)
        if centre is None or a is None or b is None:
            checked.add("geometry_figure_proportion", f"Enlargement {relation} is incomplete.")
            return
        expected = (centre[0] + value * (a[0] - centre[0]), centre[1] + value * (a[1] - centre[1]))
        if _distance(expected, b) > LENGTH_TOLERANCE:
            checked.add(
                "geometry_figure_proportion",
                f"{image} is not the image of {name} under factor {value:g} from "
                f"{relation.get('centre')}.",
            )


def _matching_angles(checked, relation) -> None:
    """Matching arcs must be equal and, when figures are named, at corresponding vertices."""
    angles = {item.get("marker_key"): item for item in checked.spec.get("angles") or []}
    keys = relation.get("angles") or []
    items = [angles.get(key) for key in keys]
    if len(items) != 2 or None in items:
        checked.add("geometry_correspondence", f"Matching arcs {keys} are not declared.")
        return
    sizes = [checked.measured_angle(key) for key in keys]
    if None in sizes or abs(sizes[0] - sizes[1]) > ANGLE_TOLERANCE:
        checked.add(
            "geometry_correspondence", f"Matching arcs {keys} mark unequal angles: {sizes}."
        )
    names = relation.get("figures")
    if names:
        figures = _pair(checked, {"figures": names})
        if figures is None:
            return
        (first, _), (second, _) = figures
        vertices = [item.get("vertex") for item in items]
        if (
            vertices[0] not in first
            or vertices[1] not in second
            or first.index(vertices[0]) != second.index(vertices[1])
        ):
            checked.add(
                "geometry_correspondence",
                f"Matching arcs sit at {vertices}, which do not correspond in {names}.",
            )


def relationship_checks(checked) -> dict[str, Callable[[dict[str, Any]], None]]:
    return {
        "congruent": lambda relation: _congruent(checked, relation),
        "similar": lambda relation: _similar(checked, relation),
        "to_scale": lambda relation: _to_scale(checked, relation),
        "enlargement": lambda relation: _enlargement(checked, relation),
        "matching_angles": lambda relation: _matching_angles(checked, relation),
        # Names which sides match, for the tick check below, without claiming that they are equal.
        "correspondence": lambda relation: _pair(checked, relation) and None,
    }


# ------------------------------------------------------------------------ figures and marks
def _figures_are_drawn(checked) -> None:
    for name, vertices in (checked.spec.get("figures") or {}).items():
        points = [checked.points.get(vertex) for vertex in vertices]
        if None in points or len(points) < 3:
            checked.add("geometry_figure_shape", f"Figure {name} must have at least 3 vertices.")
            continue
        for index, point in enumerate(points):
            following = points[(index + 1) % len(points)]
            if not (checked.drawn_segments_at(point) & checked.drawn_segments_at(following)):
                checked.add(
                    "geometry_figure_shape",
                    f"Figure {name} has no drawn side from {vertices[index]} to "
                    f"{vertices[(index + 1) % len(vertices)]}.",
                )


def _shape_matches_the_question(checked) -> None:
    context = checked.context
    if context is None or not context.stated_text:
        return
    figures = checked.spec.get("figures") or {}
    counts = {len(vertices) for vertices in figures.values()}
    words = re.findall(r"[a-z]+", context.stated_text.casefold())
    for word in words:
        sides = SHAPE_SIDES.get(word)
        if sides is not None and sides not in counts:
            checked.add(
                "geometry_figure_shape",
                f"The question is about a {word}, but no figure drawn has {sides} sides.",
            )


def _side_map(first: list[str], second: list[str]) -> dict[frozenset, frozenset]:
    mapping = {}
    count = len(first)
    for index in range(count):
        following = (index + 1) % count
        mapping[frozenset((first[index], first[following]))] = frozenset(
            (second[index], second[following])
        )
    return mapping


def _ticks_correspond(checked) -> None:
    """Ticks must join corresponding sides, one from each figure of a declared pair."""
    relations = [
        relation
        for relation in checked.spec.get("relationships") or []
        if relation.get("type") in {"congruent", "correspondence"}
    ]
    figures = checked.spec.get("figures") or {}
    segments = checked.spec.get("segments") or []
    sides = {item["key"]: frozenset((item["from"], item["to"])) for item in segments}
    for relation in relations:
        names = relation.get("figures") or []
        if len(names) != 2 or names[0] not in figures or names[1] not in figures:
            continue
        mapping = _side_map(figures[names[0]], figures[names[1]])
        images = set(mapping.values())
        for group in checked.spec.get("equal_marks") or []:
            marked = {sides[key] for key in group.get("segments") or [] if key in sides}
            sources = marked & set(mapping)
            targets = marked & images
            if len(sources) > 1 and not sources <= images:
                checked.add(
                    "geometry_correspondence",
                    f"Equal ticks join two sides of one figure: {group.get('segments')}.",
                )
            if {mapping[side] for side in sources} != targets:
                checked.add(
                    "geometry_correspondence",
                    f"Equal ticks on {group.get('segments')} do not join corresponding sides of "
                    f"{names}.",
                )


def _bounds(points) -> tuple[float, float, float, float]:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _gap(point, bounds) -> float:
    x0, y0, x1, y1 = bounds
    return math.hypot(max(x0 - point[0], 0, point[0] - x1), max(y0 - point[1], 0, point[1] - y1))


def _perimeter(points) -> float:
    return sum(
        _distance(point, points[(index + 1) % len(points)]) for index, point in enumerate(points)
    )


def _arrows(checked) -> None:
    nodes = {
        node.attrib["data-arrow"]: node for node in checked.root.iter() if "data-arrow" in node.attrib
    }
    declared = checked.spec.get("arrows") or []
    for item in declared:
        key = item.get("key")
        node = nodes.get(key)
        first, second = _figure(checked, item.get("from")), _figure(checked, item.get("to"))
        if node is None or first is None or second is None:
            checked.add("geometry_arrow", f"Arrow {key} is not drawn as declared.")
            continue
        shaft = path_polylines(node.attrib.get("d", ""))[0]
        start, end = shaft[0], shaft[-1]
        source, target = _bounds(first[1]), _bounds(second[1])
        if _gap(start, source) >= _gap(start, target) or _gap(end, target) >= _gap(end, source):
            checked.add(
                "geometry_arrow", f"Arrow {key} does not run from {item['from']} to {item['to']}."
            )
        if "factor" in item:
            drawn = _perimeter(second[1]) / _perimeter(first[1])
            factor = float(item["factor"])
            if abs(drawn - factor) > PROPORTION_TOLERANCE * factor:
                checked.add(
                    "geometry_arrow",
                    f"Arrow {key} states factor {factor:g}, but the figures are drawn at "
                    f"{drawn:.3f}.",
                )
    known = {item.get("key") for item in declared}
    for key in nodes:
        if key not in known:
            checked.add("geometry_arrow", f"The SVG has an undeclared arrow {key}.")


def _grid(checked) -> None:
    grid = checked.spec.get("grid")
    if checked.spec.get("diagram_kind") == "coordinate_grid" and not grid:
        checked.add("geometry_grid", "A coordinate figure must declare its grid.")
    if not grid:
        return
    origin = checked.points.get(grid.get("origin"))
    unit = float(grid.get("unit", 0))
    if origin is None or unit <= 0:
        checked.add("geometry_grid", "The grid has no origin or unit.")
        return

    def place(x: float, y: float) -> tuple[float, float]:
        return origin[0] + x * unit, origin[1] - y * unit

    for name, (x, y) in (grid.get("points") or {}).items():
        point = checked.points.get(name)
        if point is None or _distance(point, place(x, y)) > 1.0:
            checked.add("geometry_grid", f"Point {name} is not at its coordinates ({x}, {y}).")
    drawn = {
        node.attrib["data-grid"]: node for node in checked.root.iter() if "data-grid" in node.attrib
    }
    wanted = {
        *(f"x:{value}" for value in range(grid["x"][0], grid["x"][1] + 1)),
        *(f"y:{value}" for value in range(grid["y"][0], grid["y"][1] + 1)),
    }
    if set(drawn) != wanted:
        checked.add("geometry_grid", "The grid lines do not match the declared range.")
    for name, node in drawn.items():
        axis, _, value = name.partition(":")
        x0, y0 = float(node.attrib["x"]), float(node.attrib["y"])
        centre = (
            x0 + float(node.attrib["width"]) / 2 if axis == "x" else y0 + float(node.attrib["height"]) / 2
        )
        expected = place(float(value), 0)[0] if axis == "x" else place(0, float(value))[1]
        if abs(centre - expected) > 1.0:
            checked.add("geometry_grid", f"Grid line {name} is not at its coordinate.")
    ticks = {}
    for text in checked.texts:
        target = text.element.attrib.get("data-label-for", "")
        if target.startswith("tick:"):
            ticks[target] = text
    for axis in ("x", "y"):
        for value in (grid.get("ticks") or {}).get(axis, []):
            text = ticks.get(f"tick:{axis}:{value}")
            if text is None:
                checked.add("geometry_grid", f"The {axis}-axis has no number {value}.")
                continue
            shown = float(text.text.replace("−", "-"))
            centre = text.box.center
            position = place(value, 0)[0] - centre[0] if axis == "x" else place(0, value)[1] - centre[1]
            if shown != value or abs(position) > 1.0:
                checked.add("geometry_grid", f"The {axis}-axis number {text.text} is misplaced.")


def _numbers_match_the_question(checked) -> None:
    """Every number shown is stated in the question, and every stated number is shown."""
    context = checked.context
    if context is None or not context.stated_text:
        return
    stated = _numbers(_NUMBER.findall(context.stated_text))
    shown = _numbers(number for text in checked.texts for number in _NUMBER.findall(text.text))
    omitted = _numbers(
        item.get("value", "")
        for item in checked.spec.get("omitted_givens") or []
        if isinstance(item, dict)
    )
    for value in sorted(shown - stated):
        checked.add(
            "geometry_given_mismatch", f"The diagram shows {value:g}, which the question never states."
        )
    for value in sorted(stated - shown - omitted):
        checked.add(
            "geometry_given_mismatch",
            f"The question states {value:g}, which the diagram does not show. Show it or record "
            "why in generation_spec.omitted_givens.",
        )


def _numbers(values) -> set[float]:
    return {float(value) for value in values if value}


def run(checked) -> None:
    _figures_are_drawn(checked)
    _shape_matches_the_question(checked)
    _ticks_correspond(checked)
    _arrows(checked)
    _grid(checked)
    _numbers_match_the_question(checked)
