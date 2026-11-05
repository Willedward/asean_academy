"""Checks for the Sec 2 G5 figures that the general geometry checks do not cover.

These run only for the mensuration renderer. Each code is a defect type the G5 audit reported:

- ``geometry_slant_unmarked`` (D3): a given slant height not labelled on the slant edge, or a
  vertical height drawn on a figure that has only a slant height.
- ``geometry_wrong_solid`` (D4): a solid the question names that isn't drawn, a solid it doesn't
  name that is, a hollow solid with no inner sphere, or liquid in a cone that isn't vertex down.
- ``geometry_cone_proportion`` (D8): a cone not drawn from its given height and radius.
- ``geometry_given_mismatch`` (D7): a number the question does not state, or a stated number
  missing from the figure.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from typing import Any

from .svg_metrics import iter_texts

MENSURATION_RENDERER = "nextscholar-mensuration-svg-v2"
MIN_CONE_RATIO = 0.6
MAX_CONE_RATIO = 3.5
CONE_RATIO_TOLERANCE = 0.05
_NUMBER = re.compile(r"(?<![\d.])\d+(?:\.\d+)?")
# Numbers in a prompt that are instructions or rates, not measurements on the figure.
_NOT_GIVENS = re.compile(r"correct to \d+ decimal places?|Covering costs \D{0,4}\d+ per")
_WORD_NUMBERS = {"two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0, "six": 6.0}
_SOLID_WORDS = {
    "cone": re.compile(r"\b(cones?|conical)\b", re.IGNORECASE),
    "cylinder": re.compile(r"\bcylinders?\b", re.IGNORECASE),
    "sphere": re.compile(r"\b(spheres?|spherical)\b", re.IGNORECASE),
    "hemisphere": re.compile(r"\bhemispher(e|es|ical)\b", re.IGNORECASE),
    "pyramid": re.compile(r"\bpyramids?\b", re.IGNORECASE),
}
_HOLLOW = re.compile(r"\b(hollow|core)\b", re.IGNORECASE)
_LIQUID = re.compile(r"\bliquid\b", re.IGNORECASE)

Issue = tuple[str, str]


def _slant(spec: dict[str, Any]) -> list[Issue]:
    if "slant_height" not in (spec.get("dimensions") or {}):
        return []
    issues: list[Issue] = []
    solids = [solid for solid in spec.get("solids") or [] if solid.get("type") in {"cone", "pyramid"}]
    labels = {item.get("target"): item.get("text", "") for item in spec.get("labels") or []}
    for solid in solids:
        names = solid.get("points") or {}
        ends = {names.get("R"), names.get("L"), names.get("S")} - {None}
        apex = names.get("V")
        targets = {f"segment:{apex}{end}" for end in ends}
        if not any(labels.get(target, "").startswith("l") for target in targets):
            issues.append(
                (
                    "geometry_slant_unmarked",
                    "A given slant height must be labelled l on the edge from the apex to the base.",
                )
            )
        lesson = str(spec.get("template", "")).startswith("lesson_")
        drawn = {item.get("key") for item in spec.get("segments") or []}
        if not lesson and f"{apex}{names.get('O')}" in drawn:
            issues.append(
                (
                    "geometry_slant_unmarked",
                    "This figure has only a slant height, so it must not draw the vertical height.",
                )
            )
    return issues


def _solids_match_the_question(spec: dict[str, Any], stated: str) -> list[Issue]:
    issues: list[Issue] = []
    solids = spec.get("solids") or []
    drawn = {solid.get("type") for solid in solids}
    named = {kind for kind, word in _SOLID_WORDS.items() if word.search(stated)}
    for kind in sorted(named - drawn):
        issues.append(("geometry_wrong_solid", f"The question names a {kind}, but none is drawn."))
    for kind in sorted(drawn - named):
        issues.append(
            ("geometry_wrong_solid", f"The figure draws a {kind}, which the question doesn't name.")
        )
    if _HOLLOW.search(stated) and not any(solid.get("inner_sphere") for solid in solids):
        issues.append(("geometry_wrong_solid", "A hollow or cored solid must show its inner sphere."))
    if _LIQUID.search(stated) and not any(
        solid.get("liquid_surface") and solid.get("orientation") == "vertex_down"
        for solid in solids
    ):
        issues.append(
            ("geometry_wrong_solid", "Liquid must be drawn in a cone with its vertex pointing down.")
        )
    return issues


def _value(item: Any) -> float | None:
    return float(item["value"]) if isinstance(item, dict) and "value" in item else None


def _cone_proportion(spec: dict[str, Any]) -> list[Issue]:
    dimensions = spec.get("dimensions") or {}
    radius = _value(dimensions.get("radius"))
    height = _value(dimensions.get("height") or dimensions.get("cone_height"))
    slant = _value(dimensions.get("slant_height"))
    if radius is None or (height is None and slant is None):
        return []
    true_height = height if height is not None else math.sqrt(max(slant**2 - radius**2, 0.0))
    expected = min(MAX_CONE_RATIO, max(MIN_CONE_RATIO, true_height / radius))
    points = spec.get("points") or {}
    issues: list[Issue] = []
    for solid in spec.get("solids") or []:
        names = solid.get("points") or {}
        if solid.get("type") != "cone" or not all(key in names for key in ("V", "O", "R")):
            continue
        vertex, centre, edge = (points.get(names[key]) for key in ("V", "O", "R"))
        if not (vertex and centre and edge):
            continue
        drawn = math.dist(vertex, centre) / math.dist(centre, edge)
        if abs(drawn - expected) > CONE_RATIO_TOLERANCE:
            issues.append(
                (
                    "geometry_cone_proportion",
                    f"The cone is drawn with height to radius {drawn:.2f}; its givens make "
                    f"{expected:.2f}.",
                )
            )
    return issues


def _numbers_match_the_question(root: ET.Element, stated: str) -> list[Issue]:
    given = {float(item) for item in _NUMBER.findall(_NOT_GIVENS.sub(" ", stated))}
    words = {value for word, value in _WORD_NUMBERS.items() if re.search(rf"\b{word}\b", stated, re.I)}
    shown = {float(item) for text in iter_texts(root) for item in _NUMBER.findall(text.text)}
    issues: list[Issue] = []
    for value in sorted(shown - given - words):
        issues.append(
            ("geometry_given_mismatch", f"The figure shows {value:g}, which the question never states.")
        )
    for value in sorted(given - shown):
        issues.append(
            ("geometry_given_mismatch", f"The question states {value:g}, which the figure omits.")
        )
    return issues


def mensuration_issues(root: ET.Element, spec: dict[str, Any], context: Any) -> list[Issue]:
    if spec.get("renderer") != MENSURATION_RENDERER:
        return []
    issues = [*_slant(spec), *_cone_proportion(spec)]
    stated = getattr(context, "stated_text", "") or ""
    if stated:
        issues.extend(_solids_match_the_question(spec, stated))
        issues.extend(_numbers_match_the_question(root, stated))
    return issues
