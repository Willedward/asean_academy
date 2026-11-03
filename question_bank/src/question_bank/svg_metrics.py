"""Deterministic text extents and stroke geometry shared by diagram renderers and validators.

The renderers place labels with these estimates and the validators re-check the placed labels
with the same estimates, so a label that passes validation has clearance under a conservative
width model. Widths are the widest bold advance measured in Chromium across Inter (the
container's ``system-ui``), DejaVu Sans, Liberation Sans and FreeSans, plus a 3% margin.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass

PHONE_SCREEN_WIDTH_PX = 390
# A 390 px screen less two 16 px gutters is the narrowest width a diagram is shown at.
PHONE_CONTENT_WIDTH_PX = 358
MIN_PHONE_FONT_PX = 12.0

_GROUPED_EM_WIDTHS = {
    "⁄": 0.22,
    "'": 0.35,
    "ijl ": 0.36,
    "I": 0.39,
    ".,/’": 0.40,
    ":;": 0.42,
    "f": 0.45,
    "()": 0.47,
    "²": 0.48,
    "-³₃": 0.49,
    "t": 0.50,
    "r⁴": 0.51,
    "z": 0.60,
    "cJ": 0.61,
    "s": 0.62,
    "L": 0.66,
    "x°?": 0.67,
    "vy": 0.68,
    "k√": 0.69,
    "ae": 0.70,
    "oEFTθ": 0.71,
    "0123456789$": 0.72,
    "bdghnpqu": 0.74,
    "SZ": 0.75,
    "PY": 0.76,
    "C": 0.77,
    "B": 0.79,
    "AKRVX": 0.80,
    "π": 0.82,
    "U": 0.84,
    "G": 0.85,
    "D": 0.86,
    "HN+=−×÷≠": 0.87,
    "OQ": 0.88,
    "∠": 0.93,
    "w": 0.96,
    "M": 1.03,
    "%": 1.05,
    "⅓": 1.07,
    "m△": 1.08,
    "W": 1.14,
}
EM_WIDTHS = {char: width for chars, width in _GROUPED_EM_WIDTHS.items() for char in chars}
DEFAULT_EM_WIDTH = 1.0
ASCENT_EM = 0.78
DESCENT_EM = 0.24
_DESCENDERS = set("gjpqy(),;")


@dataclass(frozen=True)
class Box:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def center(self) -> tuple[float, float]:
        return (self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def expanded(self, pad: float) -> Box:
        return Box(self.x0 - pad, self.y0 - pad, self.x1 + pad, self.y1 + pad)

    def overlaps(self, other: Box) -> bool:
        return (
            self.x0 < other.x1 and other.x0 < self.x1 and self.y0 < other.y1 and other.y0 < self.y1
        )

    def inside(self, other: Box) -> bool:
        return (
            self.x0 >= other.x0
            and self.y0 >= other.y0
            and self.x1 <= other.x1
            and self.y1 <= other.y1
        )


def text_width(text: str, font_size: float) -> float:
    return sum(EM_WIDTHS.get(char, DEFAULT_EM_WIDTH) for char in text) * font_size


def text_extents(text: str, font_size: float) -> tuple[float, float]:
    """Return the distances above and below the baseline that the glyphs may occupy."""
    descent = DESCENT_EM if _DESCENDERS.intersection(text) else 0.06
    return ASCENT_EM * font_size, descent * font_size


def text_box(x: float, y: float, text: str, font_size: float, anchor: str = "start") -> Box:
    """Estimate the box of an SVG ``<text>`` element drawn at baseline ``(x, y)``."""
    width = text_width(text, font_size)
    if anchor == "middle":
        left = x - width / 2
    elif anchor == "end":
        left = x - width
    else:
        left = x
    ascent, descent = text_extents(text, font_size)
    return Box(left, y - ascent, left + width, y + descent)


def baseline_for_center(cy: float, text: str, font_size: float) -> float:
    ascent, descent = text_extents(text, font_size)
    return cy + (ascent - descent) / 2


def phone_font_px(font_size: float, viewbox_width: float) -> float:
    return font_size * PHONE_CONTENT_WIDTH_PX / viewbox_width


def point_segment_distance(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    t = max(
        0.0,
        min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_squared),
    )
    return math.hypot(point[0] - start[0] - t * dx, point[1] - start[1] - t * dy)


def _segments_intersect(a, b, c, d) -> bool:
    def orientation(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    o1, o2 = orientation(a, b, c), orientation(a, b, d)
    o3, o4 = orientation(c, d, a), orientation(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def segment_box_distance(start: tuple[float, float], end: tuple[float, float], box: Box) -> float:
    """Return 0 when the segment touches the box, otherwise the shortest gap."""
    if box.x0 <= start[0] <= box.x1 and box.y0 <= start[1] <= box.y1:
        return 0.0
    corners = [(box.x0, box.y0), (box.x1, box.y0), (box.x1, box.y1), (box.x0, box.y1)]
    edges = list(zip(corners, corners[1:] + corners[:1], strict=True))
    if any(_segments_intersect(start, end, p, q) for p, q in edges):
        return 0.0
    distances = [point_segment_distance(corner, start, end) for corner in corners]
    distances.extend(point_segment_distance(start, p, q) for p, q in edges)
    distances.extend(point_segment_distance(end, p, q) for p, q in edges)
    return min(distances)


def polyline_box_distance(points: list[tuple[float, float]], box: Box) -> float:
    if len(points) == 1:
        return segment_box_distance(points[0], points[0], box)
    return min(
        segment_box_distance(start, end, box)
        for start, end in zip(points, points[1:], strict=False)
    )


def ellipse_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    start_degrees: float = 0.0,
    end_degrees: float = 360.0,
    steps: int = 96,
) -> list[tuple[float, float]]:
    """Sample an axis-aligned ellipse in SVG coordinates (y down, angles anticlockwise)."""
    count = max(2, round(steps * abs(end_degrees - start_degrees) / 360) + 1)
    return [
        (
            cx
            + rx
            * math.cos(
                math.radians(start_degrees + (end_degrees - start_degrees) * i / (count - 1))
            ),
            cy
            - ry
            * math.sin(
                math.radians(start_degrees + (end_degrees - start_degrees) * i / (count - 1))
            ),
        )
        for i in range(count)
    ]


def _arc_points(
    start: tuple[float, float],
    rx: float,
    ry: float,
    rotation: float,
    large_arc: int,
    sweep: int,
    end: tuple[float, float],
) -> list[tuple[float, float]]:
    """Sample an SVG elliptical arc using the endpoint-to-centre conversion (SVG 1.1 F.6.5)."""
    if rx == 0 or ry == 0 or start == end:
        return [start, end]
    phi = math.radians(rotation)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    dx, dy = (start[0] - end[0]) / 2, (start[1] - end[1]) / 2
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy
    rx, ry = abs(rx), abs(ry)
    scale = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if scale > 1:
        rx, ry = rx * math.sqrt(scale), ry * math.sqrt(scale)
    numerator = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    factor = math.sqrt(max(0.0, numerator / denominator)) if denominator else 0.0
    if large_arc == sweep:
        factor = -factor
    cxp, cyp = factor * rx * y1p / ry, -factor * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (start[0] + end[0]) / 2
    cy = sin_phi * cxp + cos_phi * cyp + (start[1] + end[1]) / 2

    def angle(ux, uy, vx, vy):
        value = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return value

    theta = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    delta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and delta > 0:
        delta -= 2 * math.pi
    elif sweep and delta < 0:
        delta += 2 * math.pi
    count = max(4, int(abs(delta) / (math.pi / 48)) + 1)
    points = []
    for i in range(count + 1):
        t = theta + delta * i / count
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        points.append((cos_phi * x - sin_phi * y + cx, sin_phi * x + cos_phi * y + cy))
    return points


_PATH_TOKEN = re.compile(r"[MmLlHhVvAaZzCcSsQqTt]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def path_polylines(d: str) -> list[list[tuple[float, float]]]:
    """Sample an SVG path made of move, line and arc commands into polylines.

    Curves (C, S, Q, T) are approximated by their control polygon, which is adequate for the
    clearance and bounds checks that use this function.
    """
    tokens = _PATH_TOKEN.findall(d)
    polylines: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    position = (0.0, 0.0)
    subpath_start = position
    command = ""
    index = 0

    def number() -> float:
        nonlocal index
        value = float(tokens[index])
        index += 1
        return value

    while index < len(tokens):
        token = tokens[index]
        if re.fullmatch(r"[A-Za-z]", token):
            command = token
            index += 1
            if command in "Zz":
                if current:
                    current.append(subpath_start)
                position = subpath_start
                continue
        if not command:
            break
        relative = command.islower()
        upper = command.upper()
        origin = position if relative else (0.0, 0.0)
        if upper == "M":
            point = (origin[0] + number(), origin[1] + number())
            if len(current) > 1:
                polylines.append(current)
            current = [point]
            position = subpath_start = point
            command = "l" if relative else "L"
        elif upper == "L" or upper == "T":
            point = (origin[0] + number(), origin[1] + number())
            current.append(point)
            position = point
        elif upper == "H":
            value = number()
            point = (position[0] + value if relative else value, position[1])
            current.append(point)
            position = point
        elif upper == "V":
            value = number()
            point = (position[0], position[1] + value if relative else value)
            current.append(point)
            position = point
        elif upper == "A":
            rx, ry, rotation = number(), number(), number()
            large_arc, sweep = int(number()), int(number())
            point = (origin[0] + number(), origin[1] + number())
            if not current:
                current = [position]
            current.extend(_arc_points(position, rx, ry, rotation, large_arc, sweep, point)[1:])
            position = point
        elif upper in {"C", "S", "Q"}:
            pairs = {"C": 3, "S": 2, "Q": 2}[upper]
            for _ in range(pairs):
                point = (origin[0] + number(), origin[1] + number())
                current.append(point)
            position = current[-1]
        else:
            index += 1
    if len(current) > 1:
        polylines.append(current)
    return polylines


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    match = re.match(r"\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))", value)
    return float(match.group(1)) if match else default


@dataclass(frozen=True)
class Stroke:
    element: ET.Element
    polylines: tuple[tuple[tuple[float, float], ...], ...]
    half_width: float
    dashed: bool

    def distance_to_box(self, box: Box) -> float:
        return min(polyline_box_distance(list(points), box) for points in self.polylines)


def _style(element: ET.Element) -> dict[str, str]:
    style = {}
    for item in element.attrib.get("style", "").split(";"):
        if ":" in item:
            key, value = item.split(":", 1)
            style[key.strip()] = value.strip()
    return style


def _inherited(element: ET.Element, parent: dict[str, str]) -> dict[str, str]:
    values = dict(parent)
    for key in (
        "stroke",
        "stroke-width",
        "stroke-dasharray",
        "font-size",
        "font-weight",
        "text-anchor",
    ):
        if key in element.attrib:
            values[key] = element.attrib[key]
    values.update(
        {
            key: value
            for key, value in _style(element).items()
            if key
            in {
                "stroke",
                "stroke-width",
                "stroke-dasharray",
                "font-size",
                "font-weight",
                "text-anchor",
            }
        }
    )
    return values


def iter_elements(root: ET.Element) -> Iterator[tuple[ET.Element, dict[str, str]]]:
    """Yield every element with its inherited presentation attributes."""

    def walk(element: ET.Element, inherited: dict[str, str]):
        values = _inherited(element, inherited)
        yield element, values
        for child in element:
            yield from walk(child, values)

    yield from walk(root, {"stroke": "none", "stroke-width": "1"})


def element_polylines(element: ET.Element) -> list[list[tuple[float, float]]]:
    name = local_name(element)
    attr = element.attrib
    if name == "line":
        return [
            [
                (_float(attr.get("x1")), _float(attr.get("y1"))),
                (_float(attr.get("x2")), _float(attr.get("y2"))),
            ]
        ]
    if name in {"polyline", "polygon"}:
        values = [
            float(value)
            for value in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", attr.get("points", ""))
        ]
        points = list(zip(values[::2], values[1::2], strict=False))
        if name == "polygon" and points:
            points.append(points[0])
        return [points] if len(points) > 1 else []
    if name == "rect":
        x, y = _float(attr.get("x")), _float(attr.get("y"))
        width, height = _float(attr.get("width")), _float(attr.get("height"))
        return [[(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)]]
    if name == "circle":
        radius = _float(attr.get("r"))
        return [ellipse_points(_float(attr.get("cx")), _float(attr.get("cy")), radius, radius)]
    if name == "ellipse":
        return [
            ellipse_points(
                _float(attr.get("cx")),
                _float(attr.get("cy")),
                _float(attr.get("rx")),
                _float(attr.get("ry")),
            )
        ]
    if name == "path":
        return path_polylines(attr.get("d", ""))
    return []


def iter_strokes(root: ET.Element) -> Iterator[Stroke]:
    """Yield the stroked geometry of an SVG, skipping text and unstroked backgrounds."""
    for element, values in iter_elements(root):
        if local_name(element) in {"text", "tspan", "title", "desc", "svg", "g", "defs", "style"}:
            continue
        if values.get("stroke", "none") in {"none", "transparent"}:
            continue
        polylines = element_polylines(element)
        if not polylines:
            continue
        dash = values.get("stroke-dasharray", "none")
        yield Stroke(
            element=element,
            polylines=tuple(tuple(points) for points in polylines),
            half_width=_float(values.get("stroke-width"), 1.0) / 2,
            dashed=dash not in {"none", "", "0"},
        )


@dataclass(frozen=True)
class SvgText:
    element: ET.Element
    text: str
    x: float
    y: float
    font_size: float
    anchor: str

    @property
    def box(self) -> Box:
        return text_box(self.x, self.y, self.text, self.font_size, self.anchor)


_CSS_RULE = re.compile(r"([^{}]+)\{([^}]*)\}")
_CSS_FONT_SIZE = re.compile(r"(?:font-size\s*:\s*|font\s*:[^;]*?)(\d+(?:\.\d+)?)px")


def _css_font_sizes(root: ET.Element) -> dict[str, float]:
    """Read font sizes from simple ``text`` and ``.class`` rules in embedded stylesheets."""
    sizes: dict[str, float] = {}
    for element in root.iter():
        if local_name(element) != "style":
            continue
        for selectors, body in _CSS_RULE.findall("".join(element.itertext())):
            match = _CSS_FONT_SIZE.search(body)
            if match is None:
                continue
            for selector in selectors.split(","):
                sizes[selector.strip()] = float(match.group(1))
    return sizes


def iter_texts(root: ET.Element) -> Iterator[SvgText]:
    css_sizes = _css_font_sizes(root)
    for element, values in iter_elements(root):
        if local_name(element) != "text":
            continue
        content = "".join(element.itertext())
        if not content.strip():
            continue
        font_size = css_sizes.get("text", 16.0)
        for class_name in element.attrib.get("class", "").split():
            font_size = css_sizes.get(f".{class_name}", font_size)
        if "font-size" in values:
            font_size = _float(values["font-size"], font_size)
        yield SvgText(
            element=element,
            text=content,
            x=_float(element.attrib.get("x")),
            y=_float(element.attrib.get("y")),
            font_size=font_size,
            anchor=values.get("text-anchor", "start"),
        )


def viewbox(root: ET.Element) -> Box | None:
    values = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", root.attrib.get("viewBox", ""))
    if len(values) == 4:
        x, y, width, height = (float(value) for value in values)
        return Box(x, y, x + width, y + height)
    if "width" in root.attrib and "height" in root.attrib:
        return Box(0, 0, _float(root.attrib["width"]), _float(root.attrib["height"]))
    return None
