"""Shared result types and helpers for the deterministic diagram generators."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from ..svg_metrics import Box
from .canvas import WIDTH, Canvas, fit_transform, fmt

RIGHT_TRIANGLE_RENDERER = "nextscholar-right-triangle-svg-v2"
MENSURATION_RENDERER = "nextscholar-mensuration-svg-v2"
CHECKED_RENDERERS = frozenset({RIGHT_TRIANGLE_RENDERER, MENSURATION_RENDERER})


@dataclass(frozen=True)
class Quantity:
    """A given value as it is stated in the question, for example 12 cm."""

    value: float
    unit: str | None = None

    @property
    def text(self) -> str:
        return f"{number(self.value)} {self.unit}" if self.unit else number(self.value)

    def as_spec(self) -> dict[str, Any]:
        value = int(self.value) if float(self.value).is_integer() else self.value
        return {"value": value, "unit": self.unit}


@dataclass
class Diagram:
    """One rendered SVG with its accessible text and machine-checkable metadata."""

    svg: str
    alt_text: str
    title: str
    generation_spec: dict[str, Any]
    width: int
    height: int
    content_findings: list[str] = field(default_factory=list)


def number(value: float) -> str:
    """Format a stated value without trailing zeros (12, 1.6, 0.25)."""
    if math.isclose(value, round(value), abs_tol=1e-9):
        return str(round(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def decimal_forms(value: float, places: Sequence[int] = (1, 2)) -> list[str]:
    """Return the ways a derived value could be written, for answer-leak checks.

    Integers give one form. Other values give their half-up roundings to each place, with and
    without trailing zeros, so 24.2487 gives 24.2 and 24.25, and 29.004 gives 29.0 and 29.
    """
    if math.isclose(value, round(value), abs_tol=1e-9):
        return [str(round(value))]
    forms: list[str] = []
    for place in places:
        quantum = Decimal(1).scaleb(-place)
        text = str(Decimal(repr(value)).quantize(quantum, rounding=ROUND_HALF_UP))
        for candidate in (text, text.rstrip("0").rstrip(".")):
            if candidate not in forms:
                forms.append(candidate)
    return forms


_NUMBER_TOKEN = re.compile(r"(?<![\d.])\d+(?:\.\d+)?(?![\d])")


def visible_numbers(labels: Iterable[str]) -> set[str]:
    return {match.group(0) for label in labels for match in _NUMBER_TOKEN.finditer(label)}


def withheld_labels(
    candidates: Iterable[str], visible: Iterable[str]
) -> tuple[list[str], list[dict[str, str]]]:
    """Split withheld values into enforceable labels and values that equal a given.

    A learner's answer can coincide with a stated value (for example ``x = 6`` when the
    opposite side is 6 m). Such a value cannot be forbidden without hiding the given, so it is
    recorded as an exemption; the unknown is still labelled with its variable.
    """
    shown = visible_numbers(visible)
    forbidden: list[str] = []
    exemptions: list[dict[str, str]] = []
    for label in candidates:
        label = label.strip()
        if not label or label in forbidden:
            continue
        numeric = re.fullmatch(r"\d+(?:\.\d+)?", label)
        if numeric and _same_number_shown(label, shown):
            if not any(item["value"] == label for item in exemptions):
                exemptions.append(
                    {"value": label, "reason": "equals a stated value shown on the diagram"}
                )
            continue
        forbidden.append(label)
    return forbidden, exemptions


def _same_number_shown(label: str, shown: set[str]) -> bool:
    return any(math.isclose(float(label), float(value), abs_tol=1e-9) for value in shown)


def answer_values(question: dict[str, Any]) -> list[str]:
    values = []
    for part in question.get("parts", []):
        response = part.get("response") or {}
        for key in ("canonical_answer",):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                values.append(value.strip())
        for value in response.get("accepted_answers") or []:
            if isinstance(value, str) and value.strip():
                values.append(value.strip())
    return values


def layout(
    model_points: Sequence[tuple[float, float]],
    *,
    max_width: float,
    max_height: float,
    top: float,
    bottom: float,
    left: float | None = None,
    min_height: float = 300,
    max_scale: float | None = None,
    note: bool = True,
):
    """Create a canvas sized to fit the figure plus margins, and a model-to-SVG transform."""
    xs = [point[0] for point in model_points]
    ys = [point[1] for point in model_points]
    model_width = max(xs) - min(xs) or 1.0
    model_height = max(ys) - min(ys) or 1.0
    factor = min(max_width / model_width, max_height / model_height)
    if max_scale is not None:
        factor = min(factor, max_scale)
    figure_width, figure_height = model_width * factor, model_height * factor
    height = max(min_height, round(top + figure_height + bottom))
    x0 = (WIDTH - figure_width) / 2 if left is None else left
    area = Box(x0, top, x0 + figure_width, top + figure_height)
    canvas = Canvas(height=height)
    if note:
        canvas.note()
    return canvas, fit_transform(model_points, area)


def base_spec(
    *,
    renderer: str,
    diagram_kind: str,
    template: str,
    inputs: dict[str, Any],
    dimensions: dict[str, Any],
    canvas: Canvas,
    forbidden: list[str],
    exemptions: list[dict[str, str]],
    unknowns: list[dict[str, str]],
    relationships: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "renderer": renderer,
        "diagram_kind": diagram_kind,
        "template": template,
        "inputs": inputs,
        "not_to_scale": canvas.has_note,
        "dimensions": dimensions,
        "forbidden_visible_labels": forbidden,
    }
    if exemptions:
        spec["forbidden_label_exemptions"] = exemptions
    spec["unknowns"] = unknowns
    spec.update(extra or {})
    spec.update(canvas.geometry_spec())
    spec["relationships"] = relationships or []
    spec["min_phone_font_px"] = float(fmt(canvas.min_phone_font_px()))
    return spec


def finish(
    canvas: Canvas,
    *,
    renderer: str,
    title: str,
    alt_text: str,
    spec: dict[str, Any],
    content_findings: list[str] | None = None,
) -> Diagram:
    svg = canvas.svg(renderer=renderer, title=title, description=alt_text)
    spec["min_phone_font_px"] = float(fmt(canvas.min_phone_font_px()))
    return Diagram(
        svg=svg,
        alt_text=alt_text,
        title=title,
        generation_spec=spec,
        width=int(canvas.width),
        height=int(canvas.height),
        content_findings=list(content_findings or []),
    )


def join_values(values: Sequence[str]) -> str:
    if len(values) <= 1:
        return "".join(values)
    return ", ".join(values[:-1]) + " and " + values[-1]
