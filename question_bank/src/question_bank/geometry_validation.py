"""Semantic checks for deterministic geometry SVG assets."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .diagram_checks import (
    LEGACY_ADVISORY_CODES,
    DiagramContext,
    answer_leak_locations,
    checked_diagram_issues,
    legacy_diagram_issues,
    svg_accessible_text,
    svg_visible_text,
)

# Generators whose generation_spec declares every point, segment, label and relationship.
CHECKED_GEOMETRY_RENDERERS = frozenset(
    {
        "nextscholar-right-triangle-svg-v2",
        "nextscholar-mensuration-svg-v2",
        "nextscholar-plane-geometry-svg-v1",
    }
)
# Fixed-template generators whose assets raise advisory warnings until they are regenerated.
# Validating with strict geometry turns those warnings into errors.
LEGACY_GEOMETRY_RENDERERS = frozenset(
    {
        "nextscholar-geometry-svg-v1",
        "nextscholar-right-triangle-svg-v1",
        "nextscholar-mensuration-svg-v1",
    }
)
# Generators whose assets must no longer appear. Move a renderer here from
# LEGACY_GEOMETRY_RENDERERS once every asset it produced has been regenerated.
RETIRED_GEOMETRY_RENDERERS: frozenset[str] = frozenset()

_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"
_ARC_PATH = re.compile(
    rf"^\s*M\s*({_NUMBER})[ ,]+({_NUMBER})\s+"
    rf"A\s*({_NUMBER})[ ,]+({_NUMBER})[ ,]+({_NUMBER})[ ,]+([01])[ ,]+([01])[ ,]+"
    rf"({_NUMBER})[ ,]+({_NUMBER})\s*$",
    re.IGNORECASE,
)


def revisioned_asset_path_issues(storage_path: str, revision: int) -> list[tuple[str, str]]:
    """Keep asset bytes addressable for every immutable content revision."""
    if revision < 3 or f"-r{revision}." in Path(storage_path).name:
        return []
    return [
        (
            "asset_revision_path",
            f"Revision {revision} assets require an -r{revision} filename before the extension.",
        )
    ]


def _angle_is_valid(kind: str, degrees: float) -> bool:
    return {
        "acute": 0 < degrees < 90,
        "right": math.isclose(degrees, 90, abs_tol=0.5),
        "obtuse": 90 < degrees < 180,
        "reflex": 180 < degrees < 360,
    }.get(kind, False)


def angle_diagram_issues(path: Path, generation_spec: dict[str, Any]) -> list[tuple[str, str]]:
    """Compare labelled angle measures with the actual SVG ray coordinates."""
    if generation_spec.get("diagram_kind") != "angle_types":
        return []
    issues: list[tuple[str, str]] = []
    expected = generation_spec.get("angle_measures")
    required = {"acute", "right", "obtuse", "reflex"}
    if not isinstance(expected, dict) or set(expected) != required:
        return [
            (
                "geometry_angle_metadata",
                "Angle-type diagrams must declare acute, right, obtuse and reflex measures.",
            )
        ]
    try:
        root = ET.fromstring(path.read_text())
    except (OSError, ET.ParseError) as exc:
        return [("geometry_svg_invalid", str(exc))]
    groups = {
        group.attrib["data-angle-kind"]: group
        for group in root.iter()
        if group.tag.rsplit("}", 1)[-1] == "g" and "data-angle-kind" in group.attrib
    }
    if set(groups) != required:
        return [
            (
                "geometry_angle_groups",
                "Angle-type SVGs require one machine-checkable group for each angle class.",
            )
        ]
    for kind in sorted(required):
        try:
            declared = float(expected[kind])
            embedded = float(groups[kind].attrib["data-angle-degrees"])
        except (KeyError, TypeError, ValueError):
            issues.append(
                (
                    "geometry_angle_metadata",
                    f"The {kind} angle requires a numeric declared measure.",
                )
            )
            continue
        if not _angle_is_valid(kind, declared) or not math.isclose(
            declared, embedded, abs_tol=0.1
        ):
            issues.append(
                (
                    "geometry_angle_classification",
                    f"The {kind} angle metadata is inconsistent: {declared:g}° / {embedded:g}°.",
                )
            )
            continue
        lines = [
            node for node in groups[kind] if node.tag.rsplit("}", 1)[-1] == "line"
        ]
        if len(lines) != 2:
            issues.append(
                (
                    "geometry_angle_rays",
                    f"The {kind} angle must contain exactly two ray lines.",
                )
            )
            continue
        try:
            origins = [
                (float(line.attrib["x1"]), float(line.attrib["y1"])) for line in lines
            ]
            vectors = [
                (
                    float(line.attrib["x2"]) - origin[0],
                    float(line.attrib["y2"]) - origin[1],
                )
                for line, origin in zip(lines, origins, strict=True)
            ]
        except (KeyError, ValueError):
            issues.append(
                (
                    "geometry_angle_rays",
                    f"The {kind} ray coordinates must be numeric.",
                )
            )
            continue
        if not all(
            math.isclose(origins[0][axis], origins[1][axis], abs_tol=0.1)
            for axis in (0, 1)
        ):
            issues.append(
                (
                    "geometry_angle_rays",
                    f"The {kind} rays must share one vertex.",
                )
            )
            continue
        lengths = [math.hypot(*vector) for vector in vectors]
        if min(lengths) == 0:
            measured = 0.0
        else:
            cosine = sum(a * b for a, b in zip(*vectors, strict=True)) / (
                lengths[0] * lengths[1]
            )
            measured = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
        if kind == "reflex":
            measured = 360 - measured
        if not math.isclose(declared, measured, abs_tol=1.0):
            issues.append(
                (
                    "geometry_angle_measure",
                    f"The {kind} rays measure {measured:.1f}°, expected {declared:g}°.",
                )
            )
    return issues


def _svg_root(path: Path) -> tuple[ET.Element | None, list[tuple[str, str]]]:
    try:
        return ET.fromstring(path.read_text()), []
    except (OSError, ET.ParseError) as exc:
        return None, [("geometry_svg_invalid", str(exc))]


def _pair(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    try:
        return float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None


def _lies_on_ray(
    endpoint: tuple[float, float],
    center: tuple[float, float],
    ray_point: tuple[float, float],
) -> bool:
    endpoint_vector = (endpoint[0] - center[0], endpoint[1] - center[1])
    ray_vector = (ray_point[0] - center[0], ray_point[1] - center[1])
    endpoint_length = math.hypot(*endpoint_vector)
    ray_length = math.hypot(*ray_vector)
    if endpoint_length == 0 or ray_length == 0:
        return False
    cross = abs(
        endpoint_vector[0] * ray_vector[1]
        - endpoint_vector[1] * ray_vector[0]
    )
    dot = sum(a * b for a, b in zip(endpoint_vector, ray_vector, strict=True))
    return dot > 0 and cross / (endpoint_length * ray_length) <= math.sin(
        math.radians(1)
    )


def _angle_marker_issues(
    root: ET.Element, generation_spec: dict[str, Any]
) -> list[tuple[str, str]]:
    expected = generation_spec.get("angle_markers")
    if expected is None:
        return []
    if not isinstance(expected, list) or not expected:
        return [
            (
                "geometry_angle_marker_metadata",
                "angle_markers must be a non-empty list when supplied.",
            )
        ]
    paths = {
        node.attrib["data-angle-marker"]: node
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "path"
        and "data-angle-marker" in node.attrib
    }
    expected_keys = {
        marker.get("marker_key")
        for marker in expected
        if isinstance(marker, dict) and isinstance(marker.get("marker_key"), str)
    }
    issues: list[tuple[str, str]] = []
    if len(expected_keys) != len(expected) or set(paths) != expected_keys:
        return [
            (
                "geometry_angle_marker_metadata",
                "Every declared angle marker must map to one SVG path with the same data-angle-marker key.",
            )
        ]
    for marker in expected:
        key = marker["marker_key"]
        center = _pair(marker.get("center"))
        start_ray = _pair(marker.get("start_ray_point"))
        end_ray = _pair(marker.get("end_ray_point"))
        try:
            radius = float(marker["radius"])
            large_arc = int(marker["large_arc"])
            sweep = int(marker["sweep"])
        except (KeyError, TypeError, ValueError):
            center = start_ray = end_ray = None
            radius = 0
            large_arc = sweep = -1
        if (
            center is None
            or start_ray is None
            or end_ray is None
            or radius <= 0
            or large_arc not in {0, 1}
            or sweep not in {0, 1}
        ):
            issues.append(
                (
                    "geometry_angle_marker_metadata",
                    f"Angle marker {key} has invalid centre, radius, ray or arc metadata.",
                )
            )
            continue
        match = _ARC_PATH.fullmatch(paths[key].attrib.get("d", ""))
        if match is None:
            issues.append(
                (
                    "geometry_angle_marker_path",
                    f"Angle marker {key} must use one explicit M … A … SVG arc path.",
                )
            )
            continue
        values = [float(value) for value in match.groups()]
        start = values[0], values[1]
        rx, ry, rotation = values[2], values[3], values[4]
        actual_large_arc, actual_sweep = int(values[5]), int(values[6])
        end = values[7], values[8]
        if not (
            math.isclose(rx, radius, abs_tol=0.1)
            and math.isclose(ry, radius, abs_tol=0.1)
            and math.isclose(rotation, 0, abs_tol=0.1)
            and actual_large_arc == large_arc
            and actual_sweep == sweep
        ):
            issues.append(
                (
                    "geometry_angle_marker_path",
                    f"Angle marker {key} arc flags or radius do not match its generation metadata.",
                )
            )
        if not _lies_on_ray(start, center, start_ray):
            issues.append(
                (
                    "geometry_angle_marker_start",
                    f"Angle marker {key} does not start precisely on its declared ray.",
                )
            )
        if not _lies_on_ray(end, center, end_ray):
            issues.append(
                (
                    "geometry_angle_marker_end",
                    f"Angle marker {key} does not end precisely on its declared ray.",
                )
            )
        expected_start_distance = math.hypot(
            start[0] - center[0], start[1] - center[1]
        )
        expected_end_distance = math.hypot(end[0] - center[0], end[1] - center[1])
        if not (
            math.isclose(expected_start_distance, radius, abs_tol=0.75)
            and math.isclose(expected_end_distance, radius, abs_tol=0.75)
        ):
            issues.append(
                (
                    "geometry_angle_marker_radius",
                    f"Angle marker {key} endpoints are not both on the declared radius.",
                )
            )
    return issues


def _answer_leak_issues(
    root: ET.Element, generation_spec: dict[str, Any], alt_text: str
) -> list[tuple[str, str]]:
    forbidden = generation_spec.get("forbidden_visible_labels")
    if forbidden is None:
        return []
    if not isinstance(forbidden, list) or not all(
        isinstance(label, str) and label.strip() for label in forbidden
    ):
        return [
            (
                "geometry_answer_leak_metadata",
                "forbidden_visible_labels must be a list of non-empty strings.",
            )
        ]
    visible_text = svg_visible_text(root)
    alternative = " | ".join(part for part in (alt_text, svg_accessible_text(root)) if part)
    issues: list[tuple[str, str]] = []
    for label in forbidden:
        locations = answer_leak_locations(label, visible_text, alternative)
        if locations:
            issues.append(
                (
                    "geometry_answer_leak",
                    f"The withheld value {label!r} appears in {' and '.join(locations)}.",
                )
            )
    return issues


@dataclass(frozen=True)
class GeometryFinding:
    severity: str
    code: str
    message: str


def geometry_diagram_findings(
    path: Path,
    generation_spec: dict[str, Any],
    alt_text: str = "",
    context: DiagramContext | None = None,
    *,
    strict: bool = False,
) -> list[GeometryFinding]:
    """Validate a geometry SVG and return errors and advisory warnings.

    Assets from the checked renderers must satisfy every declared relationship, so their
    findings are errors. Assets from the legacy fixed-template renderers are checked only for
    layout, readability and answer leaks, and those findings are warnings unless ``strict``.
    """
    findings = [
        GeometryFinding("error", code, message)
        for code, message in angle_diagram_issues(path, generation_spec)
    ]
    root, parse_issues = _svg_root(path)
    if root is None:
        return findings or [GeometryFinding("error", code, message) for code, message in parse_issues]
    findings.extend(
        GeometryFinding("error", code, message)
        for code, message in _angle_marker_issues(root, generation_spec)
    )
    findings.extend(
        GeometryFinding("error", code, message)
        for code, message in _answer_leak_issues(root, generation_spec, alt_text)
    )
    renderer = generation_spec.get("renderer")
    if renderer in CHECKED_GEOMETRY_RENDERERS:
        findings.extend(
            GeometryFinding("error", code, message)
            for code, message in checked_diagram_issues(root, generation_spec, alt_text, context)
        )
    elif renderer in RETIRED_GEOMETRY_RENDERERS:
        findings.append(
            GeometryFinding(
                "error",
                "geometry_retired_renderer",
                f"Renderer {renderer} is retired; regenerate this diagram with a checked renderer.",
            )
        )
    elif renderer in LEGACY_GEOMETRY_RENDERERS:
        severity = "error" if strict else "warning"
        findings.extend(
            GeometryFinding(severity, code, message)
            for code, message in legacy_diagram_issues(root, generation_spec, alt_text, context)
        )
    return findings


def geometry_diagram_issues(
    path: Path, generation_spec: dict[str, Any], alt_text: str = ""
) -> list[tuple[str, str]]:
    """Return the blocking geometry issues (errors only) for one SVG asset."""
    return [
        (finding.code, finding.message)
        for finding in geometry_diagram_findings(path, generation_spec, alt_text)
        if finding.severity == "error"
    ]


def non_legacy_diagram_warnings(warnings: list[Any]) -> list[Any]:
    """Drop the advisory warnings that legacy diagrams raise until they are regenerated."""
    return [issue for issue in warnings if issue.code not in LEGACY_ADVISORY_CODES]
