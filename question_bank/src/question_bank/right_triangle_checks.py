"""Checks for the Sec 2 G4 figures that the general geometry checks do not cover.

These run only for the right-triangle renderer. Each code is a defect type the G4 audit reported:

- ``geometry_impossible_triangle`` (D6): three labelled sides that break Pythagoras' theorem, or a
  labelled hypotenuse no longer than a labelled side.
- ``geometry_given_mismatch`` (D1b, D7, D9): a number the question does not state, or a stated
  number missing from the figure.
- ``geometry_label_notation`` (D10): ``θ°``, because θ already names the angle.
- ``geometry_method_named`` (D12): text that names the ratio or theorem the learner must choose.
"""

from __future__ import annotations

import math
import re
from typing import Any

RIGHT_TRIANGLE_RENDERER = "nextscholar-right-triangle-svg-v2"
_NUMBER = re.compile(r"(?<![\d.])\d+(?:\.\d+)?")
_LENGTH = re.compile(r"(\d+(?:\.\d+)?)(?: ?[a-z]+)?")
# Numbers in a prompt that are instructions, not givens.
_NOT_GIVENS = re.compile(r"correct to \d+ decimal places?|Enter \d+ if|\band \d+ if it is not")
_METHOD_WORDS = re.compile(r"\b(tangent|tan|sine|sin|cosine|cos|pythagoras)\b", re.IGNORECASE)


def _labelled_length(labels: dict[str, str], first: str, second: str) -> float | None:
    for key in (f"segment:{first}{second}", f"segment:{second}{first}"):
        match = _LENGTH.fullmatch(labels.get(key, ""))
        if match is not None:
            return float(match[1])
    return None


def _labels_fit_the_right_angle(checked) -> None:
    labels = {item.get("target"): item.get("text", "") for item in checked.spec.get("labels") or []}
    for right_angle in checked.spec.get("right_angles") or []:
        vertex, (first, second) = right_angle["vertex"], right_angle["arms"]
        legs = [_labelled_length(labels, vertex, arm) for arm in (first, second)]
        hypotenuse = _labelled_length(labels, first, second)
        if hypotenuse is None:
            continue
        known = [leg for leg in legs if leg is not None]
        impossible = any(leg >= hypotenuse for leg in known)
        if len(known) == 2:
            impossible = impossible or not math.isclose(
                known[0] ** 2 + known[1] ** 2, hypotenuse**2, rel_tol=1e-6
            )
        if impossible:
            checked.add(
                "geometry_impossible_triangle",
                f"The sides labelled at the right angle {vertex} cannot form a right-angled "
                "triangle.",
            )


def _numbers_match_the_question(checked) -> None:
    context = checked.context
    if context is None or not context.stated_text:
        return
    stated = {float(item) for item in _NUMBER.findall(_NOT_GIVENS.sub(" ", context.stated_text))}
    shown = {float(item) for text in checked.texts for item in _NUMBER.findall(text.text)}
    if checked.spec.get("right_angles"):
        shown.add(90.0)
    for value in sorted(shown - stated):
        if value != 90.0:
            checked.add(
                "geometry_given_mismatch",
                f"The figure shows {value:g}, which the question never states.",
            )
    for value in sorted(stated - shown):
        checked.add(
            "geometry_given_mismatch",
            f"The question states {value:g}, which the figure does not show.",
        )


def _notation(checked) -> None:
    for text in checked.texts:
        if "θ°" in text.text:
            checked.add(
                "geometry_label_notation", "θ already names the angle, so write θ and not θ°."
            )


def _names_no_method(checked) -> None:
    spec: dict[str, Any] = checked.spec
    if spec.get("task") == "teaching":
        return
    title = next(
        (node.text or "" for node in checked.root.iter() if node.tag.endswith("title")), ""
    )
    for text in (title, *(item.text for item in checked.texts)):
        match = _METHOD_WORDS.search(text)
        if match:
            checked.add(
                "geometry_method_named",
                f"{text!r} names {match[1]}, and choosing the method is part of the question.",
            )


def right_triangle_issues(checked) -> None:
    _labels_fit_the_right_angle(checked)
    _numbers_match_the_question(checked)
    _notation(checked)
    _names_no_method(checked)
