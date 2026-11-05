"""Semantic validation for checked data-chart SVGs."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .diagram_checks import Issue, svg_accessible_text, svg_visible_text, text_layout_issues
from .diagrams.charts import TEMPLATES
from .diagrams.common import DATA_CHART_RENDERER
from .svg_metrics import local_name, viewbox


def _indexed(root: ET.Element, attribute: str) -> tuple[dict[str, ET.Element], list[Issue]]:
    found: dict[str, ET.Element] = {}
    issues: list[Issue] = []
    for element in root.iter():
        key = element.attrib.get(attribute)
        if key is None:
            continue
        if key in found:
            issues.append(
                ("chart_duplicate_metadata", f"{attribute} {key!r} appears more than once.")
            )
        found[key] = element
    return found, issues


def _compare_expected(root: ET.Element, spec: dict[str, Any], alt_text: str) -> list[Issue]:
    template = spec.get("template")
    if template not in TEMPLATES:
        return [("chart_template", f"Unknown checked chart template {template!r}.")]
    inputs = spec.get("inputs")
    if not isinstance(inputs, dict):
        return [("chart_inputs", "Checked charts require an inputs object.")]
    try:
        expected = TEMPLATES[template](inputs)
    except (KeyError, TypeError, ValueError) as exc:
        return [("chart_inputs", f"The stored chart inputs cannot be rendered: {exc}")]
    issues: list[Issue] = []
    expected_spec = expected.generation_spec
    for key in (
        "diagram_kind",
        "viewbox",
        "chart_marks",
        "chart_ticks",
        "axis",
        "forbidden_visible_labels",
        "min_phone_font_px",
    ):
        if key in expected_spec and spec.get(key) != expected_spec[key]:
            issues.append(
                (
                    "chart_metadata_mismatch",
                    f"generation_spec.{key} does not match the deterministic rendering of inputs.",
                )
            )
    if alt_text != expected.alt_text:
        issues.append(
            ("chart_alt_text", "Alternative text must be regenerated from the same chart inputs.")
        )
    expected_root = ET.fromstring(expected.svg)
    if svg_visible_text(root) != svg_visible_text(expected_root):
        issues.append(
            (
                "chart_visible_text_mismatch",
                "Visible chart text does not match the deterministic rendering of inputs.",
            )
        )
    if svg_accessible_text(root) != svg_accessible_text(expected_root):
        issues.append(
            (
                "chart_accessible_text_mismatch",
                "The SVG title or description does not match the deterministic rendering of inputs.",
            )
        )
    return issues


def _mark_issues(root: ET.Element, spec: dict[str, Any]) -> list[Issue]:
    actual, issues = _indexed(root, "data-chart-mark")
    declared = spec.get("chart_marks")
    if not isinstance(declared, list):
        return [*issues, ("chart_marks", "Checked charts require chart_marks metadata.")]
    expected_keys = {str(item.get("key")) for item in declared if isinstance(item, dict)}
    if set(actual) != expected_keys:
        issues.append(
            (
                "chart_marks",
                f"SVG chart marks {sorted(actual)} do not match declared marks {sorted(expected_keys)}.",
            )
        )
    for item in declared:
        if not isinstance(item, dict) or str(item.get("key")) not in actual:
            continue
        key = str(item["key"])
        element = actual[key]
        if local_name(element) != item.get("tag"):
            issues.append(
                (
                    "chart_mark_tag",
                    f"Mark {key} is a {local_name(element)}, not declared {item.get('tag')}.",
                )
            )
        if element.attrib.get("data-chart-kind") != str(item.get("kind")):
            issues.append(("chart_mark_kind", f"Mark {key} has the wrong chart kind."))
        if element.attrib.get("data-value") != str(item.get("value")):
            issues.append(("chart_mark_value", f"Mark {key} has the wrong data value."))
        geometry = item.get("geometry")
        if not isinstance(geometry, dict):
            issues.append(("chart_mark_geometry", f"Mark {key} has no geometry declaration."))
            continue
        for name, value in geometry.items():
            if element.attrib.get(name) != str(value):
                issues.append(
                    (
                        "chart_mark_geometry",
                        f"Mark {key} attribute {name} is {element.attrib.get(name)!r}, expected {value!r}.",
                    )
                )
    return issues


def _tick_issues(root: ET.Element, spec: dict[str, Any]) -> list[Issue]:
    actual, issues = _indexed(root, "data-axis-tick")
    declared = spec.get("chart_ticks")
    if not isinstance(declared, list):
        return [*issues, ("chart_ticks", "Checked charts require chart_ticks metadata.")]
    expected_keys = {str(item.get("key")) for item in declared if isinstance(item, dict)}
    if set(actual) != expected_keys:
        issues.append(
            (
                "chart_ticks",
                f"SVG ticks {sorted(actual)} do not match declared ticks {sorted(expected_keys)}.",
            )
        )
    for item in declared:
        if not isinstance(item, dict) or str(item.get("key")) not in actual:
            continue
        key = str(item["key"])
        element = actual[key]
        expected = {
            "data-axis": str(item.get("axis")),
            "data-value": str(item.get("value")),
            "data-position": str(item.get("position")),
            "data-label": str(item.get("label")),
        }
        for name, value in expected.items():
            if element.attrib.get(name) != value:
                issues.append(
                    (
                        "chart_tick_metadata",
                        f"Tick {key} attribute {name} is {element.attrib.get(name)!r}, expected {value!r}.",
                    )
                )
    return issues


def checked_chart_issues(root: ET.Element, spec: dict[str, Any], alt_text: str) -> list[Issue]:
    """Check deterministic source data, rendered marks, axes, accessibility and layout."""
    issues: list[Issue] = []
    if (
        spec.get("renderer") != DATA_CHART_RENDERER
        or root.attrib.get("data-renderer") != DATA_CHART_RENDERER
    ):
        issues.append(
            (
                "chart_renderer",
                "The SVG and generation_spec must name the checked data-chart renderer.",
            )
        )
    declared_viewbox = spec.get("viewbox")
    box = viewbox(root)
    actual_viewbox = [box.x1 - box.x0, box.y1 - box.y0] if box is not None else None
    if declared_viewbox != actual_viewbox:
        issues.append(
            (
                "chart_viewbox",
                f"SVG viewBox {actual_viewbox} does not match generation_spec.viewbox {declared_viewbox}.",
            )
        )
    if not alt_text.strip():
        issues.append(("chart_alt_text", "Checked charts require non-empty alternative text."))
    if root.attrib.get("role") != "img" or root.attrib.get("aria-labelledby") != "title desc":
        issues.append(
            (
                "chart_accessibility",
                "Checked charts require role=img and aria-labelledby='title desc'.",
            )
        )
    issues.extend(_compare_expected(root, spec, alt_text))
    issues.extend(_mark_issues(root, spec))
    issues.extend(_tick_issues(root, spec))
    issues.extend(text_layout_issues(root, check_strokes=False))
    return list(dict.fromkeys(issues))
