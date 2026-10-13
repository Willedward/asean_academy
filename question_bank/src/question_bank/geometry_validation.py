"""Semantic checks for deterministic geometry SVG assets."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


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
