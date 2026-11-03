"""Read each question's own data and choose the diagram template that draws it.

Templates are matched on the mathematical wording of the prompt (not on the opening context
sentence or the title), and every number in the figure comes from the prompt. A question
whose stored ``generation_spec`` already names a v2 template and its inputs is redrawn from
those inputs, so an author can correct a figure without rewording the prompt. A question that
matches no template is reported as unsupported rather than drawn from a guess.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from . import mensuration, right_triangle
from .common import (
    CHECKED_RENDERERS,
    MENSURATION_RENDERER,
    RIGHT_TRIANGLE_RENDERER,
    Diagram,
    answer_values,
)

LEGACY_TO_CURRENT = {
    "nextscholar-right-triangle-svg-v1": RIGHT_TRIANGLE_RENDERER,
    "nextscholar-mensuration-svg-v1": MENSURATION_RENDERER,
    RIGHT_TRIANGLE_RENDERER: RIGHT_TRIANGLE_RENDERER,
    MENSURATION_RENDERER: MENSURATION_RENDERER,
}
TEMPLATES: dict[str, dict[str, Callable[..., Diagram]]] = {
    RIGHT_TRIANGLE_RENDERER: right_triangle.TEMPLATES,
    MENSURATION_RENDERER: mensuration.TEMPLATES,
}

NUM = r"(\d+(?:\.\d+)?)"
UNIT = r"\s?(mm|cm|km|m)(?![\w²³])"
AREA_UNIT = r"\s?(mm²|cm²|km²|m²)"
VOLUME_UNIT = r"\s?(mm³|cm³|km³|m³)"
_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twelve": 12,
}
_FRACTION_WORDS = {
    "half": 1 / 2,
    "third": 1 / 3,
    "quarter": 1 / 4,
    "fourth": 1 / 4,
    "eighth": 1 / 8,
    "twenty-seventh": 1 / 27,
    "sixty-fourth": 1 / 64,
}


class UnsupportedDiagram(ValueError):
    """The question's diagram cannot be generated from its data."""


@dataclass
class DiagramRequest:
    renderer: str
    template: str
    inputs: dict[str, Any]
    source: str
    findings: list[str] = field(default_factory=list)

    def render(self, answers: list[str]) -> Diagram:
        return TEMPLATES[self.renderer][self.template](self.inputs, answers)


def _q(value: str, unit: str | None) -> dict[str, Any]:
    number = float(value)
    return {"value": int(number) if number.is_integer() else number, "unit": unit}


def _number(value: str) -> float | int:
    number = float(value)
    return int(number) if number.is_integer() else number


def question_text(question: dict[str, Any]) -> str:
    blocks = [*question.get("stem", [])]
    for part in question.get("parts", []):
        blocks.extend(part.get("prompt", []))
    return " ".join(block.get("text", "") for block in blocks if block.get("type") == "text")


def _prompt_text(question: dict[str, Any]) -> str:
    blocks = []
    for part in question.get("parts", []):
        blocks.extend(part.get("prompt", []))
    return " ".join(block.get("text", "") for block in blocks if block.get("type") == "text")


# ----------------------------------------------------------------------- right triangles
_RIGHT_TRIANGLE_PATTERNS: list[
    tuple[str, re.Pattern[str], Callable[[re.Match[str]], dict[str, Any]]]
] = [
    (
        "find_hypotenuse",
        re.compile(rf"perpendicular sides {NUM}{UNIT} and {NUM}{UNIT}\..*\bhypotenuse\b"),
        lambda m: {"legs": [_q(m[1], m[2]), _q(m[3], m[4])]},
    ),
    (
        "converse_test",
        re.compile(rf"side lengths {NUM}{UNIT}, {NUM}{UNIT} and {NUM}{UNIT}\..*right-angled"),
        lambda m: {"sides": [_q(m[1], m[2]), _q(m[3], m[4]), _q(m[5], m[6])]},
    ),
    (
        "tangent_adjacent",
        re.compile(rf"acute {NUM}° angle.*?opposite side is {NUM}{UNIT}\. Find the adjacent side"),
        lambda m: {"angle": _number(m[1]), "opposite": _q(m[2], m[3])},
    ),
    (
        "missing_leg",
        re.compile(
            rf"hypotenuse is {NUM}{UNIT} and one shorter side is {NUM}{UNIT}\. Find the other shorter side"
        ),
        lambda m: {"hypotenuse": _q(m[1], m[2]), "leg": _q(m[3], m[4])},
    ),
    (
        "tangent_opposite",
        re.compile(
            rf"angle of {NUM}° with level ground\. The horizontal distance is {NUM}{UNIT}\. Find the vertical height"
        ),
        lambda m: {"angle": _number(m[1]), "adjacent": _q(m[2], m[3])},
    ),
    (
        "rectangle_diagonal",
        re.compile(
            rf"measures {NUM}{UNIT} by {NUM}{UNIT}\. A cable runs straight from one corner to the opposite corner"
        ),
        lambda m: {"sides": [_q(m[1], m[2]), _q(m[3], m[4])]},
    ),
    (
        "find_angle",
        re.compile(
            rf"opposite side of {NUM}{UNIT} and an adjacent side of {NUM}{UNIT} relative to angle θ"
        ),
        lambda m: {"opposite": _q(m[1], m[2]), "adjacent": _q(m[3], m[4])},
    ),
    (
        "cable_allowance",
        re.compile(
            rf"top of a {NUM}{UNIT} vertical post to an anchor {NUM}{UNIT} from its base\. Another {NUM}{UNIT} is required for fastening"
        ),
        lambda m: {
            "post": _q(m[1], m[2]),
            "anchor_distance": _q(m[3], m[4]),
            "allowance": _q(m[5], m[6]),
        },
    ),
    (
        "right_angle_specification",
        re.compile(
            rf"shorter sides of a triangular frame .*? are {NUM}{UNIT} and {NUM}{UNIT}\. The angle between them must be 90°"
        ),
        lambda m: {"legs": [_q(m[1], m[2]), _q(m[3], m[4])]},
    ),
    (
        "elevation_observer",
        re.compile(
            rf"stands {NUM}{UNIT} from a vertical tower.*?angle of elevation from eye level to the top is {NUM}°.*?eye is {NUM}{UNIT} above the ground"
        ),
        lambda m: {
            "distance": _q(m[1], m[2]),
            "angle": _number(m[3]),
            "eye_height": _q(m[4], m[5]),
        },
    ),
    (
        "perimeter_verify",
        re.compile(
            rf"perimeter {NUM}{UNIT}\. Two sides measure {NUM}{UNIT} and {NUM}{UNIT}\. Find the third side x"
        ),
        lambda m: {"perimeter": _q(m[1], m[2]), "sides": [_q(m[3], m[4]), _q(m[5], m[6])]},
    ),
    (
        "diagonal_route",
        re.compile(
            rf"rectangular floor {NUM}{UNIT} by {NUM}{UNIT} diagonally, then continues {NUM}{UNIT} along a straight corridor"
        ),
        lambda m: {"floor": [_q(m[1], m[2]), _q(m[3], m[4])], "corridor": _q(m[5], m[6])},
    ),
    (
        "two_position",
        re.compile(
            rf"{NUM}{UNIT} apart.*?angles of elevation to its top are {NUM}° at the farther point and {NUM}° at the nearer point"
        ),
        lambda m: {"gap": _q(m[1], m[2]), "far_angle": _number(m[3]), "near_angle": _number(m[4])},
    ),
]


# --------------------------------------------------------------------------- mensuration
def _fraction(text: str) -> float:
    text = text.strip().lower()
    if match := re.fullmatch(r"(\d+)\s*/\s*(\d+)", text):
        return int(match[1]) / int(match[2])
    numerator, _, denominator = text.partition(" ")
    if numerator in _WORD_NUMBERS and denominator.rstrip("s") in _FRACTION_WORDS:
        return _WORD_NUMBERS[numerator] * _FRACTION_WORDS[denominator.rstrip("s")]
    raise UnsupportedDiagram(f"Cannot read the volume fraction {text!r}.")


def _count(text: str) -> int:
    text = text.strip().lower()
    if text.isdigit():
        return int(text)
    if text in _WORD_NUMBERS:
        return _WORD_NUMBERS[text]
    raise UnsupportedDiagram(f"Cannot read the count {text!r}.")


_MENSURATION_PATTERNS: list[
    tuple[str, re.Pattern[str], Callable[[re.Match[str]], dict[str, Any]]]
] = [
    (
        "cone_cylinder_factor",
        re.compile(r"cone and a cylinder have the same circular base and perpendicular height"),
        lambda m: {},
    ),
    (
        "cone_hemisphere_volume",
        re.compile(
            rf"cone of radius {NUM}{UNIT} and height {NUM}{UNIT} to a hemisphere of the same radius"
        ),
        lambda m: {"radius": _q(m[1], m[2]), "height": _q(m[3], m[4])},
    ),
    (
        "cone_hemisphere_area",
        re.compile(
            rf"cone of radius {NUM}{UNIT} and slant height {NUM}{UNIT} is joined base-to-base to a hemisphere of radius {NUM}{UNIT}"
        ),
        lambda m: {"radius": _q(m[1], m[2]), "slant_height": _q(m[3], m[4])},
    ),
    (
        "recast_spheres_cones",
        re.compile(
            rf"(\w+) solid spheres of radius {NUM}{UNIT} are melted and recast into identical cones of radius {NUM}{UNIT} and height {NUM}{UNIT}",
            re.IGNORECASE,
        ),
        lambda m: {
            "sphere_count": _count(m[1]),
            "sphere_radius": _q(m[2], m[3]),
            "cone_radius": _q(m[4], m[5]),
            "cone_height": _q(m[6], m[7]),
        },
    ),
    (
        "cone_volume",
        re.compile(
            rf"cone has radius {NUM}{UNIT} and perpendicular height {NUM}{UNIT}\. Find its volume"
        ),
        lambda m: {"radius": _q(m[1], m[2]), "height": _q(m[3], m[4])},
    ),
    (
        "cone_curved_area",
        re.compile(
            rf"cone has radius {NUM}{UNIT} and slant height {NUM}{UNIT}\. Find its curved surface area"
        ),
        lambda m: {"radius": _q(m[1], m[2]), "slant_height": _q(m[3], m[4])},
    ),
    (
        "cone_total_area",
        re.compile(
            rf"closed cone has radius {NUM}{UNIT} and perpendicular height {NUM}{UNIT}\. Find its total surface area"
        ),
        lambda m: {"radius": _q(m[1], m[2]), "height": _q(m[3], m[4])},
    ),
    (
        "liquid_depth",
        re.compile(rf"cone of height {NUM}{UNIT} is filled to ([\w/ -]+?) of its full volume"),
        lambda m: {"height": _q(m[1], m[2]), "volume_fraction": _fraction(m[3])},
    ),
    (
        "equal_volume_cone_sphere",
        re.compile(
            rf"cone and a sphere both have radius {NUM}{UNIT}\. The cone has the same volume as the sphere"
        ),
        lambda m: {"radius": _q(m[1], m[2])},
    ),
    (
        "hemisphere_curved_area",
        re.compile(rf"open hemisphere has radius {NUM}{UNIT}\. Its curved surface area"),
        lambda m: {"radius": _q(m[1], m[2])},
    ),
    (
        "pyramid_base_area_volume",
        re.compile(rf"pyramid has base area {NUM}{AREA_UNIT} and perpendicular height {NUM}{UNIT}"),
        lambda m: {"base_area": _q(m[1], m[2]), "height": _q(m[3], m[4])},
    ),
    (
        "rectangular_pyramid_volume",
        re.compile(
            rf"pyramid has a rectangular base {NUM}{UNIT} by {NUM}{UNIT} and perpendicular height {NUM}{UNIT}"
        ),
        lambda m: {"base": [_q(m[1], m[2]), _q(m[3], m[4])], "height": _q(m[5], m[6])},
    ),
    (
        "pyramid_height",
        re.compile(
            rf"rectangular pyramid has volume {NUM}{VOLUME_UNIT} and base dimensions {NUM}{UNIT} by {NUM}{UNIT}\. Find its perpendicular height"
        ),
        lambda m: {"volume": _q(m[1], m[2]), "base": [_q(m[3], m[4]), _q(m[5], m[6])]},
    ),
    (
        "pyramid_covering_cost",
        re.compile(
            rf"square-based pyramid has base side {NUM}{UNIT} and slant height {NUM}{UNIT} on every face\. Covering costs \D{{0,4}}{NUM} per"
        ),
        lambda m: {
            "base_side": _q(m[1], m[2]),
            "slant_height": _q(m[3], m[4]),
            "rate": _number(m[5]),
        },
    ),
    (
        "pyramid_volume_constraint",
        re.compile(
            rf"square-based pyramid has base side {NUM}{UNIT} and perpendicular height {NUM}{UNIT}\. A second pyramid has the same volume but base side {NUM}{UNIT}"
        ),
        lambda m: {
            "base_side": _q(m[1], m[2]),
            "height": _q(m[3], m[4]),
            "second_base_side": _q(m[5], m[6]),
        },
    ),
    (
        "sphere_surface_area",
        re.compile(rf"sphere has radius {NUM}{UNIT}\. Its surface area"),
        lambda m: {"radius": _q(m[1], m[2])},
    ),
    (
        "sphere_volume_diameter",
        re.compile(rf"spherical \w+ has diameter {NUM}{UNIT}\. Find its volume"),
        lambda m: {"diameter": _q(m[1], m[2])},
    ),
    (
        "sphere_volume_radius",
        re.compile(rf"sphere has radius {NUM}{UNIT}\. Find its volume in (\w+³)"),
        lambda m: {"radius": _q(m[1], m[2]), "answer_unit": m[3]},
    ),
    (
        "hollow_shell",
        re.compile(
            rf"hollow spherical shell has outer radius {NUM}{UNIT} and inner radius {NUM}{UNIT}"
        ),
        lambda m: {"outer_radius": _q(m[1], m[2]), "inner_radius": _q(m[3], m[4])},
    ),
    (
        "sphere_percentage_change",
        re.compile(rf"radius of a sphere is increased by {NUM}%"),
        lambda m: {"percent": _number(m[1])},
    ),
    (
        "sphere_core_removed",
        re.compile(
            rf"spherical object of radius {NUM}{UNIT} has a concentric spherical core of radius {NUM}{UNIT} removed"
        ),
        lambda m: {"outer_radius": _q(m[1], m[2]), "inner_radius": _q(m[3], m[4])},
    ),
]

PATTERNS = {
    RIGHT_TRIANGLE_RENDERER: _RIGHT_TRIANGLE_PATTERNS,
    MENSURATION_RENDERER: _MENSURATION_PATTERNS,
}


def diagram_assets(question: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the assets this module can regenerate."""
    return [
        asset
        for asset in question.get("assets", [])
        if asset.get("generation_spec", {}).get("renderer") in LEGACY_TO_CURRENT
    ]


def stem_findings(question: dict[str, Any], template: str) -> list[str]:
    """Report wording outside the diagram that the regenerated figure no longer supports."""
    findings = []
    stem = " ".join(
        block.get("text", "") for block in question.get("stem", []) if block.get("type") == "text"
    )
    if template in right_triangle.CONVERSE_TASKS and re.search(
        r"right[- ]triangle", stem, re.IGNORECASE
    ):
        findings.append(
            "The stem calls the figure a right-triangle schematic, which states the answer of a "
            "right-angle test. Describe it as a triangle in the question text."
        )
    return findings


def request_for(question: dict[str, Any], asset: dict[str, Any]) -> DiagramRequest:
    """Choose the template and inputs for one question asset."""
    spec = asset.get("generation_spec", {})
    renderer = LEGACY_TO_CURRENT.get(spec.get("renderer", ""))
    if renderer is None:
        raise UnsupportedDiagram(f"Renderer {spec.get('renderer')!r} has no checked generator.")
    if spec.get("renderer") in CHECKED_RENDERERS and spec.get("template") in TEMPLATES[renderer]:
        template = spec["template"]
        return DiagramRequest(
            renderer,
            template,
            dict(spec.get("inputs", {})),
            "generation_spec",
            stem_findings(question, template),
        )
    text = _prompt_text(question)
    matches = []
    for template, pattern, read in PATTERNS[renderer]:
        match = pattern.search(text)
        if match is not None:
            matches.append((template, read(match)))
    if not matches:
        raise UnsupportedDiagram(
            f"No {renderer} template matches the prompt of {question.get('stable_key')}; add a "
            "template or store generation_spec.template and inputs."
        )
    if len(matches) > 1:
        names = ", ".join(name for name, _ in matches)
        raise UnsupportedDiagram(f"Several templates match {question.get('stable_key')}: {names}.")
    template, inputs = matches[0]
    return DiagramRequest(
        renderer, template, inputs, "prompt", stem_findings(question, template)
    )


def render_question_asset(question: dict[str, Any], asset: dict[str, Any]) -> Diagram:
    request = request_for(question, asset)
    diagram = request.render(answer_values(question))
    spec = diagram.generation_spec
    ordered = {
        "renderer": spec.pop("renderer"),
        "diagram_kind": spec.pop("diagram_kind"),
        "question_key": question["stable_key"],
        "outcome": question.get("primary_outcome"),
    }
    diagram.generation_spec = {**ordered, **spec}
    diagram.content_findings = [*request.findings, *diagram.content_findings]
    return diagram


# --------------------------------------------------------------------------------- lessons
LESSON_TEMPLATES: dict[str, tuple[str, str]] = {
    "g4-lesson-01-pythagoras": (RIGHT_TRIANGLE_RENDERER, "lesson_pythagoras"),
    "g4-lesson-02-converse": (RIGHT_TRIANGLE_RENDERER, "lesson_converse"),
    "g4-lesson-03-trigonometry": (RIGHT_TRIANGLE_RENDERER, "lesson_trigonometry"),
    "g5-lesson-06-pyramid": (MENSURATION_RENDERER, "lesson_pyramid"),
    "g5-lesson-06-cone": (MENSURATION_RENDERER, "lesson_cone"),
    "g5-lesson-06-sphere": (MENSURATION_RENDERER, "lesson_sphere"),
}


def render_lesson_asset(lesson: dict[str, Any], asset: dict[str, Any]) -> Diagram:
    spec = asset.get("generation_spec", {})
    if (
        spec.get("renderer") in CHECKED_RENDERERS
        and spec.get("template") in TEMPLATES[spec["renderer"]]
    ):
        renderer, template, inputs = spec["renderer"], spec["template"], spec.get("inputs") or None
    elif asset["asset_key"] in LESSON_TEMPLATES:
        renderer, template = LESSON_TEMPLATES[asset["asset_key"]]
        inputs = None
    else:
        raise UnsupportedDiagram(f"No lesson template is registered for {asset['asset_key']}.")
    diagram = TEMPLATES[renderer][template](inputs)
    generated = diagram.generation_spec
    ordered = {
        "renderer": generated.pop("renderer"),
        "diagram_kind": generated.pop("diagram_kind"),
        "lesson_key": lesson["stable_key"],
    }
    diagram.generation_spec = {**ordered, **generated}
    return diagram
