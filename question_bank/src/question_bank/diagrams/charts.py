"""Deterministic, machine-checkable data displays and coordinate graphs.

Unlike the legacy hand-placed statistics and chart SVGs, every visual mark and axis tick is
declared in ``generation_spec`` and repeated as ``data-*`` metadata in the SVG.  The validator
can therefore detect a changed bar height, point, sector, scale or graph coordinate without
depending on visual inspection.
"""

from __future__ import annotations

import html
import math
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from .common import DATA_CHART_RENDERER, Diagram, answer_values

WIDTH = 720
HEIGHT = 480
BACKGROUND = "#fffdf8"
INK = "#17324d"
TEXT = "#17324d"
MUTED = "#52667a"
GRID = "#cad5df"
ACCENT = "#e36b45"
FILL = "#dcecf6"
SECONDARY = "#76a5c5"
FONT = 25
TITLE_FONT = 28
PHONE_WIDTH = 358


def _fmt(value: float | int) -> str:
    value = float(value)
    if math.isclose(value, round(value), abs_tol=1e-9):
        return str(round(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _attrs(values: dict[str, Any]) -> str:
    return "".join(
        f' {name}="{html.escape(str(value), quote=True)}"'
        for name, value in values.items()
        if value is not None
    )


def _numeric(values: Iterable[Any], name: str) -> list[float]:
    result: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must contain only numbers")
        result.append(float(value))
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _same_length(first: Sequence[Any], second: Sequence[Any], names: str) -> None:
    if len(first) != len(second):
        raise ValueError(f"{names} must have the same length")


@dataclass
class _Builder:
    title: str
    description: str
    width: int = WIDTH
    height: int = HEIGHT
    figure: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    marks: list[dict[str, Any]] = field(default_factory=list)
    ticks: list[dict[str, Any]] = field(default_factory=list)

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke: str = INK,
        width: float = 3,
        dash: str | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        values = {
            "x1": _fmt(x1),
            "y1": _fmt(y1),
            "x2": _fmt(x2),
            "y2": _fmt(y2),
            "stroke": stroke,
            "stroke-width": _fmt(width),
            "stroke-dasharray": dash,
            **(attrs or {}),
        }
        self.figure.append("<line" + _attrs(values) + "/>")

    def path(
        self,
        d: str,
        *,
        stroke: str = INK,
        width: float = 3,
        fill: str = "none",
        attrs: dict[str, Any] | None = None,
    ) -> None:
        self.figure.append(
            "<path"
            + _attrs(
                {
                    "d": d,
                    "fill": fill,
                    "stroke": stroke,
                    "stroke-width": _fmt(width),
                    **(attrs or {}),
                }
            )
            + "/>"
        )

    def text(
        self,
        value: Any,
        x: float,
        y: float,
        *,
        size: float = FONT,
        anchor: str = "middle",
        weight: int = 600,
        fill: str = TEXT,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        self.labels.append(
            "<text"
            + _attrs(
                {
                    "x": _fmt(x),
                    "y": _fmt(y),
                    "font-size": _fmt(size),
                    "font-weight": weight,
                    "text-anchor": anchor,
                    "fill": fill,
                    **(attrs or {}),
                }
            )
            + f">{html.escape(str(value))}</text>"
        )

    def mark(
        self,
        key: str,
        kind: str,
        value: Any,
        tag: str,
        geometry: dict[str, Any],
        *,
        style: dict[str, Any] | None = None,
    ) -> None:
        normalized = {
            name: _fmt(item) if isinstance(item, (int, float)) else item
            for name, item in geometry.items()
        }
        self.figure.append(
            f"<{tag}"
            + _attrs(
                {
                    "data-chart-mark": key,
                    "data-chart-kind": kind,
                    "data-value": value,
                    **normalized,
                    **(style or {}),
                }
            )
            + "/>"
        )
        self.marks.append(
            {"key": key, "kind": kind, "value": str(value), "tag": tag, "geometry": normalized}
        )

    def tick(self, axis: str, value: Any, position: float, label: str | None = None) -> None:
        key = f"{axis}:{value}"
        item = {
            "key": key,
            "axis": axis,
            "value": str(value),
            "position": _fmt(position),
            "label": str(value) if label is None else label,
        }
        self.ticks.append(item)
        self.figure.append(
            "<g"
            + _attrs(
                {
                    "data-axis-tick": key,
                    "data-axis": axis,
                    "data-value": value,
                    "data-position": _fmt(position),
                    "data-label": item["label"],
                }
            )
            + "/>"
        )

    def svg(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc" '
            f'data-renderer="{DATA_CHART_RENDERER}">\n'
            f'<title id="title">{html.escape(self.title)}</title>'
            f'<desc id="desc">{html.escape(self.description)}</desc>\n'
            f'<rect data-role="background" width="{self.width}" height="{self.height}" rx="20" fill="{BACKGROUND}"/>\n'
            '<g data-layer="figure" stroke-linecap="round" stroke-linejoin="round">\n'
            + "\n".join(self.figure)
            + "\n</g>\n"
            + '<g data-layer="labels" font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" stroke="none">\n'
            + "\n".join(self.labels)
            + "\n</g>\n</svg>\n"
        )


def _finish(
    builder: _Builder,
    *,
    template: str,
    diagram_kind: str,
    inputs: dict[str, Any],
    forbidden: Sequence[str] = (),
    extras: dict[str, Any] | None = None,
) -> Diagram:
    input_forbidden = inputs.get("forbidden_visible_labels", [])
    if not isinstance(input_forbidden, list) or not all(
        isinstance(item, str) and item.strip() for item in input_forbidden
    ):
        raise ValueError("forbidden_visible_labels must be a list of non-empty strings")
    spec: dict[str, Any] = {
        "renderer": DATA_CHART_RENDERER,
        "diagram_kind": diagram_kind,
        "template": template,
        "inputs": inputs,
        "viewbox": [builder.width, builder.height],
        "chart_marks": builder.marks,
        "chart_ticks": builder.ticks,
        "forbidden_visible_labels": list(dict.fromkeys([*forbidden, *input_forbidden])),
        "min_phone_font_px": round(FONT * PHONE_WIDTH / builder.width, 2),
    }
    spec.update(extras or {})
    return Diagram(
        svg=builder.svg(),
        alt_text=builder.description,
        title=builder.title,
        generation_spec=spec,
        width=builder.width,
        height=builder.height,
    )


def _ticks(low: float, high: float, step: float) -> list[float]:
    if step <= 0 or high <= low:
        raise ValueError("axis maximum and tick step must be greater than the minimum")
    count = int(math.floor((high - low) / step + 1e-9))
    return [low + index * step for index in range(count + 1)]


def _plot_axes(
    builder: _Builder,
    *,
    y_min: float,
    y_max: float,
    tick_step: float,
    categories: Sequence[str],
    y_label: str,
) -> tuple[Callable[[float], float], list[float]]:
    left, right, top, bottom = 90.0, 680.0, 105.0, 385.0
    values = _ticks(y_min, y_max, tick_step)

    def scale(value: float) -> float:
        return bottom - (value - y_min) / (y_max - y_min) * (bottom - top)

    for value in values:
        y = scale(value)
        builder.line(left, y, right, y, stroke=GRID, width=1.5)
        builder.line(left - 8, y, left, y, width=2)
        builder.text(_fmt(value), left - 15, y + 8, anchor="end", size=25, weight=500)
        builder.tick("y", _fmt(value), y)
    builder.line(left, top, left, bottom, width=3)
    builder.line(left, bottom, right, bottom, width=3)
    builder.text(y_label, left, top - 18, anchor="start", size=25)
    if categories:
        spacing = (right - left) / len(categories)
        for index, category in enumerate(categories):
            x = left + (index + 0.5) * spacing
            builder.text(category, x, bottom + 38, size=25, weight=500)
            builder.tick("x", category, x, category)
    return scale, values


def bar_chart(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    categories = [str(item) for item in inputs["categories"]]
    raw_values = list(inputs["values"])
    _same_length(categories, raw_values, "categories and values")
    # A null value is a bar the learner has to work out: it is labelled but not drawn.
    values = _numeric([value for value in raw_values if value is not None], "values")
    y_min = float(inputs.get("y_min", 0))
    y_max = float(inputs.get("y_max", max(values)))
    if y_max <= y_min:
        raise ValueError("y_max must be greater than y_min")
    if y_max <= max(values) - 1e-9:
        raise ValueError("y_max must include every bar")
    tick_step = float(inputs.get("tick_step", max(1, math.ceil((y_max - y_min) / 5))))
    title = str(inputs.get("title", "Bar chart"))
    description = str(
        inputs.get(
            "alt_text",
            "Bar chart with "
            + ", ".join(
                f"{c}: {'unknown' if v is None else _fmt(v)}"
                for c, v in zip(categories, raw_values, strict=True)
            )
            + ".",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    scale, _ = _plot_axes(
        builder,
        y_min=y_min,
        y_max=y_max,
        tick_step=tick_step,
        categories=categories,
        y_label=str(inputs.get("y_label", "Value")),
    )
    left, right, bottom = 90.0, 680.0, 385.0
    spacing = (right - left) / len(categories)
    show_values = bool(inputs.get("show_values", False))
    for index, value in enumerate(raw_values):
        x = left + index * spacing + spacing * 0.2
        if value is None:
            label_x, label_y = x + spacing * 0.3, bottom - 14
            builder.text(
                "?",
                label_x,
                label_y,
                size=32,
                attrs={
                    "data-chart-mark": f"bar-{index}",
                    "data-chart-kind": "unknown-bar",
                    "data-value": "?",
                },
            )
            builder.marks.append(
                {
                    "key": f"bar-{index}",
                    "kind": "unknown-bar",
                    "value": "?",
                    "tag": "text",
                    "geometry": {"x": _fmt(label_x), "y": _fmt(label_y)},
                }
            )
            continue
        y = scale(value)
        builder.mark(
            f"bar-{index}",
            "bar",
            _fmt(value),
            "rect",
            {"x": x, "y": y, "width": spacing * 0.6, "height": bottom - y},
            style={"fill": ACCENT, "stroke": INK, "stroke-width": 2},
        )
        if show_values:
            builder.text(_fmt(value), x + spacing * 0.3, y - 10, size=25)
    if y_min != 0:
        builder.path(
            "M78 382 l10 -8 l10 8 l10 -8", stroke=INK, width=3, attrs={"data-role": "axis-break"}
        )
    return _finish(
        builder,
        template="bar_chart",
        diagram_kind="bar_chart",
        inputs=inputs,
        extras={"axis": {"y_min": y_min, "y_max": y_max, "tick_step": tick_step}},
    )


def line_chart(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    categories = [str(item) for item in inputs["categories"]]
    values = _numeric(inputs["values"], "values")
    _same_length(categories, values, "categories and values")
    y_min = float(inputs.get("y_min", min(0, min(values))))
    y_max = float(inputs.get("y_max", max(values)))
    tick_step = float(inputs.get("tick_step", max(1, math.ceil((y_max - y_min) / 5))))
    title = str(inputs.get("title", "Line graph"))
    description = str(
        inputs.get(
            "alt_text",
            f"Line graph with {', '.join(f'{c}: {_fmt(v)}' for c, v in zip(categories, values, strict=True))}.",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    scale, _ = _plot_axes(
        builder,
        y_min=y_min,
        y_max=y_max,
        tick_step=tick_step,
        categories=categories,
        y_label=str(inputs.get("y_label", "Value")),
    )
    left, right = 90.0, 680.0
    spacing = (right - left) / len(categories)
    points = [(left + (index + 0.5) * spacing, scale(value)) for index, value in enumerate(values)]
    builder.path(
        "M" + " L".join(f"{_fmt(x)} {_fmt(y)}" for x, y in points),
        stroke=ACCENT,
        width=4,
        attrs={"data-role": "series"},
    )
    for index, ((x, y), value) in enumerate(zip(points, values, strict=True)):
        builder.mark(
            f"point-{index}",
            "point",
            _fmt(value),
            "circle",
            {"cx": x, "cy": y, "r": 6},
            style={"fill": ACCENT, "stroke": INK, "stroke-width": 2},
        )
        if inputs.get("show_values", False):
            builder.text(_fmt(value), x, y - 16, size=25)
    if inputs.get("axis_break", False):
        builder.path(
            "M78 382 l10 -8 l10 8 l10 -8", stroke=INK, width=3, attrs={"data-role": "axis-break"}
        )
    return _finish(
        builder,
        template="line_chart",
        diagram_kind="line_chart",
        inputs=inputs,
        extras={"axis": {"y_min": y_min, "y_max": y_max, "tick_step": tick_step}},
    )


def pictogram(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    rows = list(inputs["rows"])
    key = float(inputs["key"])
    if key <= 0:
        raise ValueError("pictogram key must be positive")
    symbol = str(inputs.get("symbol", "★"))
    title = str(inputs.get("title", "Pictogram"))
    description = str(
        inputs.get(
            "alt_text",
            f"Pictogram where each {symbol} represents {_fmt(key)}; "
            + "; ".join(f"{row['label']} has {_fmt(float(row['count']))} symbols" for row in rows)
            + ".",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT, weight=700)
    for row_index, row in enumerate(rows):
        y = 115 + row_index * 70
        builder.text(str(row["label"]), 150, y + 8, anchor="end", size=25)
        count = float(row["count"])
        if count < 0:
            raise ValueError("pictogram symbol counts must not be negative")
        whole = int(math.floor(count + 1e-9))
        remainder = count - whole
        if remainder > 1e-9 and not math.isclose(remainder, 0.5, abs_tol=1e-9):
            raise ValueError("pictogram currently supports only whole and half symbols")
        for icon_index in range(whole):
            x = 200 + icon_index * 58
            builder.text(
                symbol,
                x,
                y + 9,
                size=32,
                attrs={
                    "data-chart-mark": f"icon-{row_index}-{icon_index}",
                    "data-chart-kind": "icon",
                    "data-value": _fmt(key),
                },
            )
            builder.marks.append(
                {
                    "key": f"icon-{row_index}-{icon_index}",
                    "kind": "icon",
                    "value": _fmt(key),
                    "tag": "text",
                    "geometry": {"x": _fmt(x), "y": _fmt(y + 9)},
                }
            )
        if remainder > 1e-9:
            x = 200 + whole * 58
            builder.text(
                "½" + symbol,
                x,
                y + 9,
                size=28,
                attrs={
                    "data-chart-mark": f"icon-{row_index}-partial",
                    "data-chart-kind": "partial-icon",
                    "data-value": _fmt(remainder * key),
                },
            )
            builder.marks.append(
                {
                    "key": f"icon-{row_index}-partial",
                    "kind": "partial-icon",
                    "value": _fmt(remainder * key),
                    "tag": "text",
                    "geometry": {"x": _fmt(x), "y": _fmt(y + 9)},
                }
            )
    if inputs.get("show_key", True):
        builder.text(f"Key: {symbol} represents {_fmt(key)}", WIDTH / 2, 435, size=25)
    return _finish(builder, template="pictogram", diagram_kind="pictogram", inputs=inputs)


def _horizontal_scale(inputs: dict[str, Any]) -> Diagram:
    """Draw equally spaced labelled ticks along a horizontal axis, such as a time axis."""
    values = _numeric(inputs["ticks"], "ticks")
    title = str(inputs.get("title", "Horizontal scale"))
    description = str(
        inputs.get(
            "alt_text",
            "Horizontal scale marked " + ", ".join(_fmt(value) for value in values) + ".",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 75, size=TITLE_FONT)
    left, right, y = 90.0, 630.0, 250.0
    builder.line(left - 30, y, right + 30, y, width=4)
    for index, value in enumerate(values):
        x = left + index * (right - left) / max(1, len(values) - 1)
        builder.line(x, y - 16, x, y + 16, width=3)
        builder.text(_fmt(value), x, y + 50, size=25)
        builder.tick("x", _fmt(value), x)
    return _finish(builder, template="vertical_scale", diagram_kind="vertical_scale", inputs=inputs)


def vertical_scale(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    if inputs.get("orientation", "vertical") == "horizontal":
        return _horizontal_scale(inputs)
    values = _numeric(inputs["ticks"], "ticks")
    title = str(inputs.get("title", "Vertical scale"))
    description = str(
        inputs.get(
            "alt_text", "Vertical scale marked " + ", ".join(_fmt(value) for value in values) + "."
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    top, bottom, x = 75.0, 405.0, 330.0
    builder.line(x, top, x, bottom, width=4)
    for index, value in enumerate(values):
        y = bottom - index * (bottom - top) / max(1, len(values) - 1)
        builder.line(x - 16, y, x + 16, y, width=3)
        builder.text(_fmt(value), x - 28, y + 8, anchor="end", size=25)
        builder.tick("y", _fmt(value), y)
    for index, point in enumerate(inputs.get("points", [])):
        position = int(point["tick_index"])
        y = bottom - position * (bottom - top) / max(1, len(values) - 1)
        builder.mark(
            f"point-{index}",
            "point",
            point.get("label", position),
            "circle",
            {"cx": x, "cy": y, "r": 7},
            style={"fill": ACCENT, "stroke": INK, "stroke-width": 2},
        )
    return _finish(builder, template="vertical_scale", diagram_kind="vertical_scale", inputs=inputs)


def scaled_icons(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """Draw squares, circles or bars side by side at one shared scale, with their labels."""
    shape = str(inputs.get("shape", "square"))
    if shape not in {"square", "circle", "rect"}:
        raise ValueError("shape must be square, circle or rect")
    items = list(inputs["items"])
    if not items:
        raise ValueError("items must not be empty")
    widths = _numeric([item["width"] for item in items], "item widths")
    heights = _numeric([item.get("height", item["width"]) for item in items], "item heights")
    if any(value <= 0 for value in [*widths, *heights]):
        raise ValueError("icon sizes must be positive")
    title = str(inputs.get("title", "Icons"))
    description = str(
        inputs.get(
            "alt_text",
            f"{len(items)} {shape} icons: "
            + "; ".join(f"{item['label']}, {item['caption']}" for item in items)
            + ".",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    slot = WIDTH / len(items)
    scale = min(240.0 / max(heights), (slot - 60.0) / max(widths))
    bottom = 340.0
    for index, (item, width, height) in enumerate(zip(items, widths, heights, strict=True)):
        cx = slot * (index + 0.5)
        drawn_width, drawn_height = width * scale, height * scale
        if shape == "circle":
            kind, tag = "circle-icon", "circle"
            geometry: dict[str, float] = {
                "cx": cx,
                "cy": bottom - drawn_width / 2,
                "r": drawn_width / 2,
            }
        else:
            kind, tag = f"{shape}-icon", "rect"
            geometry = {
                "x": cx - drawn_width / 2,
                "y": bottom - drawn_height,
                "width": drawn_width,
                "height": drawn_height,
            }
        builder.mark(
            f"icon-{index}",
            kind,
            f"{_fmt(width)}x{_fmt(height)}",
            tag,
            geometry,
            style={"fill": FILL, "stroke": INK, "stroke-width": 3},
        )
        builder.text(str(item["label"]), cx, bottom + 45, size=25)
        builder.text(str(item["caption"]), cx, bottom + 85, size=25, weight=500)
    return _finish(builder, template="scaled_icons", diagram_kind="scaled_icons", inputs=inputs)


def dot_plot(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    values = _numeric(inputs["values"], "values")
    low = int(inputs.get("x_min", math.floor(min(values))))
    high = int(inputs.get("x_max", math.ceil(max(values))))
    title = str(inputs.get("title", "Dot diagram"))
    description = str(
        inputs.get("alt_text", "Dot diagram of " + ", ".join(_fmt(value) for value in values) + ".")
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    left, right, baseline = 80.0, 680.0, 385.0
    builder.line(left, baseline, right, baseline, width=3)
    counts: dict[float, int] = {}
    for tick in range(low, high + 1):
        x = left + (tick - low) / max(1, high - low) * (right - left)
        builder.line(x, baseline - 8, x, baseline + 8, width=2)
        builder.text(tick, x, baseline + 38, size=25)
        builder.tick("x", tick, x)
    for index, value in enumerate(values):
        stack = counts.get(value, 0)
        counts[value] = stack + 1
        x = left + (value - low) / max(1, high - low) * (right - left)
        y = baseline - 28 - stack * 34
        builder.mark(
            f"dot-{index}",
            "dot",
            _fmt(value),
            "circle",
            {"cx": x, "cy": y, "r": 9},
            style={"fill": ACCENT, "stroke": INK, "stroke-width": 2},
        )
    return _finish(builder, template="dot_plot", diagram_kind="dot_plot", inputs=inputs)


def stem_leaf(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    rows = list(inputs["rows"])
    key = str(inputs["key"])
    title = str(inputs.get("title", "Stem-and-leaf diagram"))
    description = str(
        inputs.get(
            "alt_text",
            "Stem-and-leaf diagram. "
            + "; ".join(
                f"stem {row['stem']}, leaves {' '.join(map(str, row['leaves']))}" for row in rows
            )
            + f". Key: {key}.",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    builder.line(310, 90, 310, 355, width=4)
    for index, row in enumerate(rows):
        y = 125 + index * 58
        leaves = "  ".join(str(value) for value in row["leaves"])
        builder.text(row["stem"], 285, y, anchor="end", size=25)
        builder.text(
            leaves,
            335,
            y,
            anchor="start",
            size=25,
            weight=500,
            attrs={
                "data-chart-mark": f"row-{index}",
                "data-chart-kind": "stem-leaf-row",
                "data-value": f"{row['stem']}|{' '.join(map(str, row['leaves']))}",
            },
        )
        builder.marks.append(
            {
                "key": f"row-{index}",
                "kind": "stem-leaf-row",
                "value": f"{row['stem']}|{' '.join(map(str, row['leaves']))}",
                "tag": "text",
                "geometry": {"x": "335", "y": _fmt(y)},
            }
        )
    builder.text(f"Key: {key}", WIDTH / 2, 420, size=25)
    return _finish(builder, template="stem_leaf", diagram_kind="stem_leaf", inputs=inputs)


def histogram(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    bins = list(inputs["bins"])
    if not bins:
        raise ValueError("bins must not be empty")
    starts = [float(item["start"]) for item in bins]
    ends = [float(item["end"]) for item in bins]
    heights = [None if item.get("height") is None else float(item["height"]) for item in bins]
    known_heights = [height for height in heights if height is not None]
    if any(end <= start for start, end in zip(starts, ends, strict=True)):
        raise ValueError("every histogram bin must have positive width")
    if not known_heights and "y_max" not in inputs:
        raise ValueError("a histogram with no known heights requires y_max")
    low, high = min(starts), max(ends)
    default_y_max = max(known_heights) if known_heights else inputs["y_max"]
    y_max = float(inputs.get("y_max", default_y_max))
    if high <= low or y_max <= 0:
        raise ValueError("histogram axes must have positive ranges")
    if any(height > y_max for height in known_heights):
        raise ValueError("y_max must include every known histogram bin")
    tick_step = float(inputs.get("tick_step", max(1, math.ceil(y_max / 5))))
    title = str(inputs.get("title", "Histogram"))
    y_label = str(inputs.get("y_label", "Frequency"))
    description = str(
        inputs.get(
            "alt_text",
            f"Histogram with {len(bins)} classes; {y_label.lower()} values "
            + ", ".join("unknown" if value is None else _fmt(value) for value in heights)
            + ".",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    left, right, top, bottom = 90.0, 680.0, 75.0, 385.0

    def y_scale(value: float) -> float:
        return bottom - value / y_max * (bottom - top)

    def x_scale(value: float) -> float:
        return left + (value - low) / (high - low) * (right - left)

    for value in _ticks(0, y_max, tick_step):
        y = y_scale(value)
        builder.line(left, y, right, y, stroke=GRID, width=1.5)
        builder.text(_fmt(value), left - 15, y + 8, anchor="end", size=25, weight=500)
        builder.tick("y", _fmt(value), y)
    boundaries = sorted(set(starts + ends))
    for value in boundaries:
        x = x_scale(value)
        builder.line(x, bottom - 7, x, bottom + 7, width=2)
        builder.text(_fmt(value), x, bottom + 38, size=25, weight=500)
        builder.tick("x", _fmt(value), x)
    builder.line(left, top, left, bottom, width=3)
    builder.line(left, bottom, right, bottom, width=3)
    builder.text(y_label, right, top + 22, anchor="end", size=25)
    for index, (start, end, height) in enumerate(zip(starts, ends, heights, strict=True)):
        x, x2 = x_scale(start), x_scale(end)
        if height is None:
            builder.mark(
                f"bin-{index}",
                "missing-histogram-bin",
                "unknown",
                "rect",
                {"x": x, "y": top, "width": x2 - x, "height": bottom - top},
                style={
                    "fill": "none",
                    "stroke": SECONDARY,
                    "stroke-width": 3,
                    "stroke-dasharray": "10 8",
                },
            )
            builder.text("?", (x + x2) / 2, (top + bottom) / 2 + 12, size=36)
            continue
        y = y_scale(height)
        builder.mark(
            f"bin-{index}",
            "histogram-bin",
            _fmt(height),
            "rect",
            {"x": x, "y": y, "width": x2 - x, "height": bottom - y},
            style={"fill": FILL, "stroke": INK, "stroke-width": 2},
        )
    return _finish(
        builder,
        template="histogram",
        diagram_kind="histogram",
        inputs=inputs,
        extras={
            "axis": {
                "x_min": low,
                "x_max": high,
                "y_min": 0,
                "y_max": y_max,
                "tick_step": tick_step,
            }
        },
    )


def probability_scale(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    value = float(inputs["value"])
    if not 0 <= value <= 1:
        raise ValueError("probability must be between 0 and 1")
    title = str(inputs.get("title", "Probability scale"))
    description = str(
        inputs.get("alt_text", f"Probability scale from 0 to 1 with a point at {_fmt(value)}.")
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 70, size=TITLE_FONT)
    left, right, y = 90.0, 660.0, 255.0
    builder.line(left, y, right, y, width=5)
    for tick in [index / 10 for index in range(11)]:
        x = left + tick * (right - left)
        builder.line(x, y - 12, x, y + 12, width=2)
        if tick in {0, 0.5, 1}:
            builder.text(_fmt(tick), x, y + 48, size=25)
        builder.tick("x", _fmt(tick), x, _fmt(tick) if tick in {0, 0.5, 1} else "")
    x = left + value * (right - left)
    builder.mark(
        "probability",
        "probability-point",
        _fmt(value),
        "circle",
        {"cx": x, "cy": y, "r": 10},
        style={"fill": ACCENT, "stroke": INK, "stroke-width": 3},
    )
    builder.text("P", x, y - 28, size=25)
    return _finish(
        builder, template="probability_scale", diagram_kind="probability_scale", inputs=inputs
    )


def spinner(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    labels = [str(item) for item in inputs["labels"]]
    if len(labels) < 2:
        raise ValueError("spinner needs at least two sectors")
    title = str(inputs.get("title", "Fair spinner"))
    description = str(
        inputs.get(
            "alt_text", "Fair spinner with equal sectors labelled " + ", ".join(labels) + "."
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    cx, cy, radius = 360.0, 245.0, 155.0
    colors = [FILL, "#f7d9c9", "#e4ead7", "#eee1f4"]
    for index, label in enumerate(labels):
        start = -math.pi / 2 + index * 2 * math.pi / len(labels)
        end = -math.pi / 2 + (index + 1) * 2 * math.pi / len(labels)
        x1, y1 = cx + radius * math.cos(start), cy + radius * math.sin(start)
        x2, y2 = cx + radius * math.cos(end), cy + radius * math.sin(end)
        large = 1 if end - start > math.pi else 0
        d = f"M{_fmt(cx)} {_fmt(cy)} L{_fmt(x1)} {_fmt(y1)} A{_fmt(radius)} {_fmt(radius)} 0 {large} 1 {_fmt(x2)} {_fmt(y2)} Z"
        builder.mark(
            f"sector-{index}",
            "spinner-sector",
            label,
            "path",
            {"d": d},
            style={"fill": colors[index % len(colors)], "stroke": INK, "stroke-width": 2},
        )
        middle = (start + end) / 2
        builder.text(
            label,
            cx + radius * 0.68 * math.cos(middle),
            cy + radius * 0.68 * math.sin(middle) + 8,
            size=25,
        )
    builder.line(cx, cy - radius - 12, cx - 14, cy - radius + 18, stroke=ACCENT, width=5)
    builder.line(cx, cy - radius - 12, cx + 14, cy - radius + 18, stroke=ACCENT, width=5)
    return _finish(builder, template="spinner", diagram_kind="spinner", inputs=inputs)


def pie_chart(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    labels = [str(item) for item in inputs["labels"]]
    values = _numeric(inputs["values"], "values")
    _same_length(labels, values, "labels and values")
    if any(value <= 0 for value in values):
        raise ValueError("pie-chart values must be positive")
    title = str(inputs.get("title", "Pie chart"))
    description = str(
        inputs.get(
            "alt_text",
            "Pie chart with "
            + ", ".join(
                f"{label}: {_fmt(value)}" for label, value in zip(labels, values, strict=True)
            )
            + ".",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    cx, cy, radius = 360.0, 250.0, 160.0
    total = sum(values)
    angle = -math.pi / 2
    colors = [FILL, "#f7d9c9", "#e4ead7", "#eee1f4", "#f4e8c1"]
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        end = angle + value / total * 2 * math.pi
        x1, y1 = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        x2, y2 = cx + radius * math.cos(end), cy + radius * math.sin(end)
        large = 1 if end - angle > math.pi else 0
        d = (
            f"M{_fmt(cx)} {_fmt(cy)} L{_fmt(x1)} {_fmt(y1)} "
            f"A{_fmt(radius)} {_fmt(radius)} 0 {large} 1 {_fmt(x2)} {_fmt(y2)} Z"
        )
        builder.mark(
            f"sector-{index}",
            "pie-sector",
            _fmt(value),
            "path",
            {"d": d},
            style={"fill": colors[index % len(colors)], "stroke": INK, "stroke-width": 2},
        )
        middle = (angle + end) / 2
        builder.text(
            label,
            cx + radius * 0.65 * math.cos(middle),
            cy + radius * 0.65 * math.sin(middle) + 8,
            size=25,
        )
        angle = end
    return _finish(builder, template="pie_chart", diagram_kind="pie_chart", inputs=inputs)


def data_table(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    columns = [str(item) for item in inputs["columns"]]
    rows = [str(item) for item in inputs["rows"]]
    cells = list(inputs["cells"])
    if len(cells) != len(rows) or any(len(row) != len(columns) for row in cells):
        raise ValueError("table cells must match the row and column counts")
    title = str(inputs.get("title", "Data table"))
    description = str(
        inputs.get(
            "alt_text", f"Table with rows {', '.join(rows)} and columns {', '.join(columns)}."
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 48, size=TITLE_FONT)
    x0, y0 = 85.0, 95.0
    column_width = 550.0 / (len(columns) + 1)
    row_height = min(68.0, 300.0 / (len(rows) + 1))
    for column in range(len(columns) + 2):
        x = x0 + column * column_width
        builder.line(x, y0, x, y0 + (len(rows) + 1) * row_height, width=2)
    for row in range(len(rows) + 2):
        y = y0 + row * row_height
        builder.line(x0, y, x0 + (len(columns) + 1) * column_width, y, width=2)
    for index, column in enumerate(columns):
        builder.text(column, x0 + (index + 1.5) * column_width, y0 + row_height * 0.68, size=25)
    for row_index, row_label in enumerate(rows):
        y = y0 + (row_index + 1.68) * row_height
        builder.text(row_label, x0 + column_width * 0.5, y, size=25)
        for column_index, value in enumerate(cells[row_index]):
            x = x0 + (column_index + 1.5) * column_width
            shown = "?" if value is None else str(value)
            builder.text(
                shown,
                x,
                y,
                size=25,
                attrs={
                    "data-chart-mark": f"cell-{row_index}-{column_index}",
                    "data-chart-kind": "table-cell",
                    "data-value": shown,
                },
            )
            builder.marks.append(
                {
                    "key": f"cell-{row_index}-{column_index}",
                    "kind": "table-cell",
                    "value": shown,
                    "tag": "text",
                    "geometry": {"x": _fmt(x), "y": _fmt(y)},
                }
            )
    return _finish(builder, template="data_table", diagram_kind="data_table", inputs=inputs)


def _number_line_interval(inputs: dict[str, Any]) -> Diagram:
    """Draw a bounded solution such as -3 < x <= 5 on a number line."""
    lower = float(inputs["boundary"])
    upper = float(inputs["upper_boundary"])
    lower_relation = str(inputs["relation"])
    upper_relation = str(inputs["upper_relation"])
    if lower_relation not in {">", ">="} or upper_relation not in {"<", "<="}:
        raise ValueError("an interval needs relation > or >= and upper_relation < or <=")
    if upper <= lower:
        raise ValueError("upper_boundary must be greater than boundary")
    low = int(inputs.get("x_min", math.floor(lower) - 2))
    high = int(inputs.get("x_max", math.ceil(upper) + 2))
    if high <= low or not (low <= lower and upper <= high):
        raise ValueError("number-line bounds must contain both boundaries")
    title = str(inputs.get("title", "Number line"))
    words = {
        ">": "greater than",
        ">=": "greater than or equal to",
        "<": "less than",
        "<=": "less than or equal to",
    }
    description = str(
        inputs.get(
            "alt_text",
            f"Number line showing values {words[lower_relation]} {_fmt(lower)} "
            f"and {words[upper_relation]} {_fmt(upper)}.",
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 75, size=TITLE_FONT)
    left, right, y = 80.0, 680.0, 250.0
    builder.line(left, y, right, y, width=4)
    builder.path(f"M{_fmt(left)} {_fmt(y)} l18 -10 M{_fmt(left)} {_fmt(y)} l18 10", width=3)
    builder.path(f"M{_fmt(right)} {_fmt(y)} l-18 -10 M{_fmt(right)} {_fmt(y)} l-18 10", width=3)
    for tick in range(low, high + 1):
        x = left + (tick - low) / (high - low) * (right - left)
        builder.line(x, y - 10, x, y + 10, width=2)
        builder.text(tick, x, y + 42, size=25)
        builder.tick("x", tick, x)

    def position(value: float) -> float:
        return left + (value - low) / (high - low) * (right - left)

    builder.line(
        position(lower),
        y,
        position(upper),
        y,
        stroke=ACCENT,
        width=6,
        attrs={"data-role": "solution-segment"},
    )
    for key, value, relation in (
        ("boundary", lower, lower_relation),
        ("upper-boundary", upper, upper_relation),
    ):
        closed = "=" in relation
        builder.mark(
            key,
            "closed-boundary" if closed else "open-boundary",
            _fmt(value),
            "circle",
            {"cx": position(value), "cy": y, "r": 10},
            style={
                "fill": ACCENT if closed else BACKGROUND,
                "stroke": ACCENT,
                "stroke-width": 4,
            },
        )
    return _finish(builder, template="number_line", diagram_kind="number_line", inputs=inputs)


def number_line(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    if "upper_boundary" in inputs:
        return _number_line_interval(inputs)
    boundary = float(inputs["boundary"])
    relation = str(inputs["relation"])
    if relation not in {"<", "<=", ">", ">="}:
        raise ValueError("relation must be <, <=, > or >=")
    low = int(inputs.get("x_min", math.floor(boundary) - 4))
    high = int(inputs.get("x_max", math.ceil(boundary) + 4))
    if high <= low or not low <= boundary <= high:
        raise ValueError("number-line bounds must contain the boundary")
    title = str(inputs.get("title", "Number line"))
    words = {
        "<": "less than",
        "<=": "less than or equal to",
        ">": "greater than",
        ">=": "greater than or equal to",
    }[relation]
    description = str(
        inputs.get("alt_text", f"Number line showing values {words} {_fmt(boundary)}.")
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 75, size=TITLE_FONT)
    left, right, y = 80.0, 680.0, 250.0
    builder.line(left, y, right, y, width=4)
    builder.path(f"M{_fmt(left)} {_fmt(y)} l18 -10 M{_fmt(left)} {_fmt(y)} l18 10", width=3)
    builder.path(f"M{_fmt(right)} {_fmt(y)} l-18 -10 M{_fmt(right)} {_fmt(y)} l-18 10", width=3)
    for tick in range(low, high + 1):
        x = left + (tick - low) / (high - low) * (right - left)
        builder.line(x, y - 10, x, y + 10, width=2)
        builder.text(tick, x, y + 42, size=25)
        builder.tick("x", tick, x)
    x = left + (boundary - low) / (high - low) * (right - left)
    builder.mark(
        "boundary",
        "closed-boundary" if "=" in relation else "open-boundary",
        _fmt(boundary),
        "circle",
        {"cx": x, "cy": y, "r": 10},
        style={
            "fill": ACCENT if "=" in relation else BACKGROUND,
            "stroke": ACCENT,
            "stroke-width": 4,
        },
    )
    target = left + 12 if relation.startswith("<") else right - 12
    builder.line(
        x,
        y,
        target,
        y,
        stroke=ACCENT,
        width=6,
        attrs={
            "data-role": "solution-ray",
            "data-direction": "left" if relation.startswith("<") else "right",
        },
    )
    return _finish(builder, template="number_line", diagram_kind="number_line", inputs=inputs)


def coordinate_line(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    a, b, c = float(inputs["a"]), float(inputs["b"]), float(inputs["c"])
    if math.isclose(b, 0):
        raise ValueError("coordinate_line requires a non-vertical line")
    x_min, x_max = float(inputs.get("x_min", -1)), float(inputs.get("x_max", 8))
    y_min, y_max = float(inputs.get("y_min", -1)), float(inputs.get("y_max", 8))
    if x_max <= x_min or y_max <= y_min:
        raise ValueError("coordinate graph axes must have positive ranges")
    title = str(inputs.get("title", "Coordinate graph"))
    description = str(
        inputs.get("alt_text", f"Coordinate graph of {_fmt(a)}x + {_fmt(b)}y = {_fmt(c)}.")
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    left, right, top, bottom = 90.0, 680.0, 60.0, 405.0

    def sx(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * (right - left)

    def sy(value: float) -> float:
        return bottom - (value - y_min) / (y_max - y_min) * (bottom - top)

    for tick in range(math.ceil(x_min), math.floor(x_max) + 1):
        x = sx(tick)
        builder.line(x, top, x, bottom, stroke=GRID, width=1)
        builder.text(tick, x, sy(0) + 32, size=25)
        builder.tick("x", tick, x)
    for tick in range(math.ceil(y_min), math.floor(y_max) + 1):
        y = sy(tick)
        builder.line(left, y, right, y, stroke=GRID, width=1)
        if tick != 0:
            builder.text(tick, sx(0) - 14, y + 8, anchor="end", size=25)
        builder.tick("y", tick, y)
    builder.line(left, sy(0), right, sy(0), width=3)
    builder.line(sx(0), top, sx(0), bottom, width=3)
    first_y, second_y = (c - a * x_min) / b, (c - a * x_max) / b
    builder.mark(
        "line",
        "coordinate-line",
        f"{_fmt(a)},{_fmt(b)},{_fmt(c)}",
        "line",
        {"x1": sx(x_min), "y1": sy(first_y), "x2": sx(x_max), "y2": sy(second_y)},
        style={"stroke": ACCENT, "stroke-width": 4},
    )
    if "point_x" in inputs:
        px = float(inputs["point_x"])
        py = (c - a * px) / b
        builder.mark(
            "point",
            "point",
            f"{_fmt(px)},{_fmt(py)}",
            "circle",
            {"cx": sx(px), "cy": sy(py), "r": 7},
            style={"fill": ACCENT, "stroke": INK, "stroke-width": 2},
        )
    return _finish(
        builder,
        template="coordinate_line",
        diagram_kind="coordinate_line",
        inputs=inputs,
        extras={"axis": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}},
    )


def quadratic_graph(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    roots = _numeric(inputs["roots"], "roots")
    if len(roots) != 2:
        raise ValueError("quadratic_graph requires two roots")
    a = float(inputs.get("a", 1))
    x_min = float(inputs.get("x_min", min(roots) - 2))
    x_max = float(inputs.get("x_max", max(roots) + 2))
    sample = [x_min + index * (x_max - x_min) / 80 for index in range(81)]
    values = [a * (x - roots[0]) * (x - roots[1]) for x in sample]
    y_min = float(inputs.get("y_min", min(values)))
    y_max = float(inputs.get("y_max", max(values)))
    if math.isclose(y_min, y_max):
        raise ValueError("quadratic y range must not be zero")
    title = str(inputs.get("title", "Quadratic graph"))
    description = str(
        inputs.get(
            "alt_text", f"Parabola crossing the x-axis at {_fmt(roots[0])} and {_fmt(roots[1])}."
        )
    )
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    left, right, top, bottom = 90.0, 680.0, 60.0, 405.0

    def sx(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * (right - left)

    def sy(value: float) -> float:
        return bottom - (value - y_min) / (y_max - y_min) * (bottom - top)

    axis_y = sy(0)
    for tick in range(math.ceil(x_min), math.floor(x_max) + 1):
        x = sx(tick)
        builder.line(x, top, x, bottom, stroke=GRID, width=1)
        builder.line(x, axis_y - 6, x, axis_y + 6, width=2)
        builder.text(tick, x, min(bottom - 4, axis_y + 30), size=25, weight=500)
        builder.tick("x", tick, x)
    builder.line(left, axis_y, right, axis_y, width=3)
    zero_x = sx(0) if x_min <= 0 <= x_max else left
    builder.line(zero_x, top, zero_x, bottom, width=3)
    d = "M" + " L".join(f"{_fmt(sx(x))} {_fmt(sy(y))}" for x, y in zip(sample, values, strict=True))
    builder.mark(
        "curve",
        "quadratic-curve",
        f"{_fmt(a)};{_fmt(roots[0])};{_fmt(roots[1])}",
        "path",
        {"d": d},
        style={"fill": "none", "stroke": ACCENT, "stroke-width": 4},
    )
    for index, root in enumerate(roots):
        builder.mark(
            f"root-{index}",
            "root",
            _fmt(root),
            "circle",
            {"cx": sx(root), "cy": sy(0), "r": 7},
            style={"fill": ACCENT, "stroke": INK, "stroke-width": 2},
        )
    vertex_x = sum(roots) / 2
    vertex_y = a * (vertex_x - roots[0]) * (vertex_x - roots[1])
    if inputs.get("show_symmetry", True):
        builder.mark(
            "vertex",
            "vertex",
            f"{_fmt(vertex_x)},{_fmt(vertex_y)}",
            "circle",
            {"cx": sx(vertex_x), "cy": sy(vertex_y), "r": 7},
            style={"fill": INK},
        )
        builder.line(
            sx(vertex_x),
            top,
            sx(vertex_x),
            bottom,
            stroke=SECONDARY,
            width=2,
            dash="8 7",
            attrs={"data-role": "axis-of-symmetry", "data-value": _fmt(vertex_x)},
        )
    return _finish(
        builder,
        template="quadratic_graph",
        diagram_kind="quadratic_graph",
        inputs=inputs,
        extras={"axis": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}},
    )



def _clip_line(a: float, b: float, c: float, box: tuple[float, float, float, float]):
    """The two ends of the visible part of ax + by = c inside the window, or None."""
    x_min, x_max, y_min, y_max = box
    found: list[tuple[float, float]] = []
    if not math.isclose(b, 0):
        for x in (x_min, x_max):
            y = (c - a * x) / b
            if y_min - 1e-9 <= y <= y_max + 1e-9:
                found.append((x, y))
    if not math.isclose(a, 0):
        for y in (y_min, y_max):
            x = (c - b * y) / a
            if x_min - 1e-9 <= x <= x_max + 1e-9:
                found.append((x, y))
    unique: list[tuple[float, float]] = []
    for point in found:
        if all(math.dist(point, other) > 1e-6 for other in unique):
            unique.append(point)
    if len(unique) < 2:
        return None
    best = max(
        ((p, q) for p in unique for q in unique if p is not q), key=lambda pair: math.dist(*pair)
    )
    return tuple(sorted(best))


def line_graph(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """Straight lines ax + by = c on axes with equal unit scales, with optional labelled points."""
    lines = list(inputs["lines"])
    if not 1 <= len(lines) <= 2:
        raise ValueError("line_graph draws one or two lines")
    x_min, x_max = float(inputs["x_min"]), float(inputs["x_max"])
    y_min, y_max = float(inputs["y_min"]), float(inputs["y_max"])
    if x_max <= x_min or y_max <= y_min or not (x_min <= 0 <= x_max and y_min <= 0 <= y_max):
        raise ValueError("line_graph axes must have positive ranges that include the origin")
    title = str(inputs.get("title", "Straight-line graph"))
    description = str(inputs["alt_text"])
    builder = _Builder(title, description)
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    unit = min(560 / (x_max - x_min), 380 / (y_max - y_min))
    left = (WIDTH - unit * (x_max - x_min)) / 2 + 10
    right = left + unit * (x_max - x_min)
    top = 95.0
    step = 1 if unit >= 34 else 2
    bottom = top + unit * (y_max - y_min)
    builder.height = int(math.ceil(bottom + 60))

    def sx(value: float) -> float:
        return left + (value - x_min) * unit

    def sy(value: float) -> float:
        return bottom - (value - y_min) * unit

    for tick in range(math.ceil(x_min), math.floor(x_max) + 1):
        x = sx(tick)
        builder.line(x, top, x, bottom, stroke=GRID, width=1)
        if tick > 0 and tick % step == 0:
            builder.text(tick, x, sy(0) + 30, size=FONT)
        builder.tick("x", tick, x)
    for tick in range(math.ceil(y_min), math.floor(y_max) + 1):
        y = sy(tick)
        builder.line(left, y, right, y, stroke=GRID, width=1)
        if tick > 0 and tick % step == 0:
            builder.text(tick, sx(0) - 12, y + 9, anchor="end", size=FONT)
        builder.tick("y", tick, y)
    builder.line(left, sy(0), right + 14, sy(0), width=3)
    builder.line(sx(0), bottom, sx(0), top - 14, width=3)
    builder.path(
        f"M{_fmt(right + 4)} {_fmt(sy(0) - 7)} L{_fmt(right + 16)} {_fmt(sy(0))} "
        f"L{_fmt(right + 4)} {_fmt(sy(0) + 7)}",
        width=3,
    )
    builder.path(
        f"M{_fmt(sx(0) - 7)} {_fmt(top - 4)} L{_fmt(sx(0))} {_fmt(top - 16)} "
        f"L{_fmt(sx(0) + 7)} {_fmt(top - 4)}",
        width=3,
    )
    builder.text("x", right + 30, sy(0) + 9, size=FONT, anchor="start")
    builder.text("y", sx(0), top - 26, size=FONT)
    builder.text("O", sx(0) - 12, sy(0) + 30, size=FONT, anchor="end")
    colours = (ACCENT, SECONDARY)
    for index, item in enumerate(lines):
        a, b, c = float(item["a"]), float(item["b"]), float(item["c"])
        ends = _clip_line(a, b, c, (x_min, x_max, y_min, y_max))
        if ends is None:
            raise ValueError("each line must cross the plotting window")
        (x1, y1), (x2, y2) = ends
        builder.mark(
            f"line-{index}",
            "line",
            f"{_fmt(a)},{_fmt(b)},{_fmt(c)}",
            "line",
            {"x1": sx(x1), "y1": sy(y1), "x2": sx(x2), "y2": sy(y2)},
            style={"stroke": colours[index], "stroke-width": 4},
        )
        label = item.get("label")
        if label:
            builder.text(
                str(label),
                sx(float(item["label_x"])),
                sy(float(item["label_y"])),
                size=FONT,
                anchor=str(item.get("label_anchor", "start")),
                fill=colours[index] if index == 0 else INK,
            )
    for index, point in enumerate(inputs.get("points", [])):
        px, py = float(point["x"]), float(point["y"])
        builder.mark(
            f"point-{index}",
            "point",
            f"{_fmt(px)},{_fmt(py)}",
            "circle",
            {"cx": sx(px), "cy": sy(py), "r": 8},
            style={"fill": INK, "stroke": BACKGROUND, "stroke-width": 2},
        )
        if point.get("label"):
            builder.text(
                str(point["label"]),
                sx(px) + float(point.get("dx", 16)),
                sy(py) + float(point.get("dy", -14)),
                size=FONT,
                anchor=str(point.get("anchor", "start")),
            )
    return _finish(
        builder,
        template="line_graph",
        diagram_kind="line_graph",
        inputs=inputs,
        extras={
            "axis": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max},
            "unit_px": _fmt(unit),
        },
    )


def proportion_graph(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """y = kx (direct) or y = k/x (inverse) for positive x, with labelled points on the graph."""
    kind = str(inputs["kind"])
    if kind not in {"direct", "inverse"}:
        raise ValueError("proportion_graph kind must be direct or inverse")
    k = float(inputs["k"])
    x_max, y_max = float(inputs["x_max"]), float(inputs["y_max"])
    step = float(inputs.get("tick_step", 1))
    if k <= 0 or x_max <= 0 or y_max <= 0:
        raise ValueError("proportion_graph needs positive k and axis maxima")
    title = str(inputs.get("title", "Direct proportion" if kind == "direct" else "Inverse proportion"))
    builder = _Builder(title, str(inputs["alt_text"]))
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    left, right, top, bottom = 110.0, 650.0, 80.0, 400.0

    def sx(value: float) -> float:
        return left + value / x_max * (right - left)

    def sy(value: float) -> float:
        return bottom - value / y_max * (bottom - top)

    for tick in _ticks(0, x_max, step):
        x = sx(tick)
        builder.line(x, top, x, bottom, stroke=GRID, width=1)
        if tick > 0:
            builder.text(_fmt(tick), x, bottom + 32, size=FONT)
        builder.tick("x", _fmt(tick), x)
    for tick in _ticks(0, y_max, step):
        y = sy(tick)
        builder.line(left, y, right, y, stroke=GRID, width=1)
        if tick > 0:
            builder.text(_fmt(tick), left - 12, y + 9, anchor="end", size=FONT)
        builder.tick("y", _fmt(tick), y)
    builder.line(left, bottom, right + 14, bottom, width=3)
    builder.line(left, bottom, left, top - 14, width=3)
    builder.text(str(inputs.get("x_label", "x")), right + 24, bottom + 9, size=FONT, anchor="start")
    builder.text(str(inputs.get("y_label", "y")), left, top - 24, size=FONT)
    builder.text("O", left - 12, bottom + 32, size=FONT, anchor="end")
    if kind == "direct":
        end_x = min(x_max, y_max / k)
        sample = [(0.0, 0.0), (end_x, k * end_x)]
    else:
        start_x = k / y_max
        sample = [
            (start_x + (x_max - start_x) * index / 80, k / (start_x + (x_max - start_x) * index / 80))
            for index in range(81)
        ]
    d = "M" + " L".join(f"{_fmt(sx(x))} {_fmt(sy(y))}" for x, y in sample)
    builder.mark(
        "curve",
        "proportion-curve",
        f"{kind};{_fmt(k)}",
        "path",
        {"d": d},
        style={"fill": "none", "stroke": ACCENT, "stroke-width": 4},
    )
    for index, point in enumerate(inputs.get("points", [])):
        px = float(point["x"])
        py = k * px if kind == "direct" else k / px
        builder.mark(
            f"point-{index}",
            "point",
            f"{_fmt(px)},{_fmt(py)}",
            "circle",
            {"cx": sx(px), "cy": sy(py), "r": 8},
            style={"fill": INK, "stroke": BACKGROUND, "stroke-width": 2},
        )
        builder.text(
            f"({_fmt(px)}, {_fmt(py)})",
            sx(px) + float(point.get("dx", 16)),
            sy(py) + float(point.get("dy", -14)),
            size=FONT,
            anchor=str(point.get("anchor", "start")),
        )
    return _finish(
        builder,
        template="proportion_graph",
        diagram_kind="proportion_graph",
        inputs=inputs,
        extras={"axis": {"x_min": 0, "x_max": x_max, "y_min": 0, "y_max": y_max}},
    )


def scale_squares(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """A map square and the real square it represents, with side lengths on the sides."""
    title = str(inputs.get("title", "Length scale and area scale"))
    builder = _Builder(title, str(inputs["alt_text"]))
    builder.height = 470
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    small, large = 110.0, 220.0
    base = 330.0
    squares = (
        (90.0, small, str(inputs["map_side"]), str(inputs["map_area"]), str(inputs["map_caption"])),
        (380.0, large, str(inputs["real_side"]), str(inputs["real_area"]), str(inputs["real_caption"])),
    )
    for index, (x, size, side, area, caption) in enumerate(squares):
        y = base - size
        builder.mark(
            f"square-{index}",
            "square",
            side,
            "rect",
            {"x": x, "y": y, "width": size, "height": size},
            style={"fill": FILL, "stroke": INK, "stroke-width": 3},
        )
        builder.line(x, base + 18, x + size, base + 18, width=2)
        builder.line(x, base + 10, x, base + 26, width=2)
        builder.line(x + size, base + 10, x + size, base + 26, width=2)
        builder.text(side, x + size / 2, base + 52, size=FONT)
        builder.text(area, x + size / 2, y + size / 2 + 9, size=FONT)
        builder.text(caption, x + size / 2, base + 92, size=FONT, fill=MUTED)
    builder.text(str(inputs["scale_label"]), 275, 175, size=FONT)
    builder.path("M 225 195 L 355 195 M 343 186 L 355 195 L 343 204", width=3)
    builder.text("Not drawn to scale", WIDTH - 24, builder.height - 18, size=FONT, anchor="end", fill=MUTED)
    return _finish(builder, template="scale_squares", diagram_kind="scale_squares", inputs=inputs)


def parabola_graph(inputs: dict[str, Any], answers: Sequence[str] = ()) -> Diagram:
    """y = ax² + bx + c sampled from the rule, with numbered axes, plotted points and an optional
    labelled axis of symmetry."""
    a, b, c = float(inputs["a"]), float(inputs.get("b", 0)), float(inputs.get("c", 0))
    if math.isclose(a, 0):
        raise ValueError("parabola_graph needs a non-zero a")
    x_min, x_max = float(inputs["x_min"]), float(inputs["x_max"])
    y_min, y_max = float(inputs["y_min"]), float(inputs["y_max"])
    if x_max <= x_min or y_max <= y_min or not (x_min <= 0 <= x_max and y_min <= 0 <= y_max):
        raise ValueError("parabola_graph axes must have positive ranges that include the origin")
    step = int(inputs.get("tick_step", 1))
    title = str(inputs.get("title", "Quadratic graph"))
    builder = _Builder(title, str(inputs["alt_text"]))
    builder.text(title, WIDTH / 2, 42, size=TITLE_FONT)
    x_unit = 560 / (x_max - x_min)
    y_unit = min(x_unit, 380 / (y_max - y_min))
    left = (WIDTH - x_unit * (x_max - x_min)) / 2 + 10
    right = left + x_unit * (x_max - x_min)
    top = 95.0
    bottom = top + y_unit * (y_max - y_min)
    builder.height = int(math.ceil(bottom + 60))

    def sx(value: float) -> float:
        return left + (value - x_min) * x_unit

    def sy(value: float) -> float:
        return bottom - (value - y_min) * y_unit

    for tick in range(math.ceil(x_min), math.floor(x_max) + 1):
        x = sx(tick)
        builder.line(x, top, x, bottom, stroke=GRID, width=1)
        if tick != 0 and tick % step == 0:
            builder.text(tick, x, sy(0) + 30, size=FONT)
        builder.tick("x", tick, x)
    for tick in range(math.ceil(y_min), math.floor(y_max) + 1):
        y = sy(tick)
        builder.line(left, y, right, y, stroke=GRID, width=1)
        if tick != 0 and tick % step == 0:
            builder.text(tick, sx(0) - 12, y + 9, anchor="end", size=FONT)
        builder.tick("y", tick, y)
    builder.line(left, sy(0), right + 14, sy(0), width=3)
    builder.line(sx(0), bottom, sx(0), top - 14, width=3)
    builder.text("x", right + 24, sy(0) + 9, size=FONT, anchor="start")
    builder.text("y", sx(0), top - 24, size=FONT)
    sample = []
    for index in range(161):
        x = x_min + (x_max - x_min) * index / 160
        y = a * x * x + b * x + c
        if y_min - 1e-9 <= y <= y_max + 1e-9:
            sample.append((x, y))
    if len(sample) < 2:
        raise ValueError("the parabola must cross the plotting window")
    d = "M" + " L".join(f"{_fmt(sx(x))} {_fmt(sy(y))}" for x, y in sample)
    builder.mark(
        "curve",
        "quadratic-curve",
        f"{_fmt(a)};{_fmt(b)};{_fmt(c)}",
        "path",
        {"d": d},
        style={"fill": "none", "stroke": ACCENT, "stroke-width": 4},
    )
    if inputs.get("axis_label"):
        h = -b / (2 * a)
        builder.line(
            sx(h), top, sx(h), bottom, stroke=SECONDARY, width=2, dash="8 7",
            attrs={"data-role": "axis-of-symmetry", "data-value": _fmt(h)},
        )
        builder.text(str(inputs["axis_label"]), sx(h) + 10, bottom - 14, size=FONT, anchor="start")
    for index, point in enumerate(inputs.get("points", [])):
        px = float(point["x"])
        py = a * px * px + b * px + c
        builder.mark(
            f"point-{index}",
            "point",
            f"{_fmt(px)},{_fmt(py)}",
            "circle",
            {"cx": sx(px), "cy": sy(py), "r": 7},
            style={"fill": INK, "stroke": BACKGROUND, "stroke-width": 2},
        )
        if point.get("label"):
            builder.text(
                f"({_fmt(px)}, {_fmt(py)})",
                sx(px) + float(point.get("dx", 14)),
                sy(py) + float(point.get("dy", -12)),
                size=FONT,
                anchor=str(point.get("anchor", "start")),
            )
    return _finish(
        builder,
        template="parabola_graph",
        diagram_kind="parabola_graph",
        inputs=inputs,
        extras={"axis": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}},
    )

TEMPLATES: dict[str, Callable[..., Diagram]] = {
    "scaled_icons": scaled_icons,
    "bar_chart": bar_chart,
    "line_chart": line_chart,
    "pictogram": pictogram,
    "vertical_scale": vertical_scale,
    "dot_plot": dot_plot,
    "stem_leaf": stem_leaf,
    "histogram": histogram,
    "probability_scale": probability_scale,
    "spinner": spinner,
    "pie_chart": pie_chart,
    "data_table": data_table,
    "number_line": number_line,
    "coordinate_line": coordinate_line,
    "quadratic_graph": quadratic_graph,
    "line_graph": line_graph,
    "proportion_graph": proportion_graph,
    "scale_squares": scale_squares,
    "parabola_graph": parabola_graph,
}


NUM = r"(-?\d+(?:\.\d+)?)"


def _bar_three(match: re.Match[str]) -> dict[str, Any]:
    return {
        "categories": [match[2].strip(), match[4].strip(), match[6].strip()],
        "values": [float(match[1]), float(match[3]), float(match[5])],
        "y_max": math.ceil(max(float(match[1]), float(match[3]), float(match[5])) / 2) * 2,
        "tick_step": 2,
    }


def _line_three(match: re.Match[str]) -> dict[str, Any]:
    values = [float(match[1]), float(match[3]), float(match[5])]
    low = math.floor((min(values) - 2) / 2) * 2
    high = math.ceil((max(values) + 2) / 2) * 2
    return {
        "categories": [match[2], match[4], match[6]],
        "values": values,
        "y_min": low,
        "y_max": high,
        "tick_step": 2,
        "y_label": "Temperature (°C)",
    }


def _dot_values(match: re.Match[str]) -> dict[str, Any]:
    return {"values": [float(value) for value in re.findall(NUM, match[1])]}


def _stem_row(match: re.Match[str]) -> dict[str, Any]:
    stem = int(match[1])
    leaves = [int(value) for value in re.findall(r"\d+", match[2])]
    return {"rows": [{"stem": stem, "leaves": leaves}], "key": match[3].strip()}


def _equal_histogram(match: re.Match[str]) -> dict[str, Any]:
    interval_values = [float(value) for value in re.findall(NUM, match[1])]
    frequencies = [float(value) for value in re.findall(NUM, match[2])]
    bins = [
        {
            "start": interval_values[index * 2],
            "end": interval_values[index * 2 + 1],
            "height": frequency,
        }
        for index, frequency in enumerate(frequencies)
    ]
    return {"bins": bins, "y_label": "Frequency"}


def _density_histogram(match: re.Match[str]) -> dict[str, Any]:
    return {
        "bins": [
            {"start": float(match[1]), "end": float(match[2]), "height": float(match[3])},
            {"start": float(match[4]), "end": float(match[5]), "height": float(match[6])},
        ],
        "y_label": "Frequency density",
    }


def _truncated_bars(match: re.Match[str]) -> dict[str, Any]:
    baseline, first, second = map(float, match.groups()[:3])
    high = math.ceil(max(first, second) / 5) * 5
    return {
        "categories": ["First", "Second"],
        "values": [first, second],
        "y_min": baseline,
        "y_max": high,
        "tick_step": 5,
    }


def _spinner_labels(match: re.Match[str]) -> dict[str, Any]:
    return {"labels": [item.strip() for item in match[1].split(",") if item.strip()]}


def _quadratic_roots(match: re.Match[str]) -> dict[str, Any]:
    roots = [float(match[1]), float(match[2])]
    return {"roots": roots, "x_min": min(roots) - 2, "x_max": max(roots) + 2}


PATTERNS: list[tuple[str, re.Pattern[str], Callable[[re.Match[str]], dict[str, Any]]]] = [
    (
        "bar_chart",
        re.compile(
            rf"bar graph shows {NUM}(?: [a-z]+)? for ([^,]+), {NUM}(?: [a-z]+)? for ([^,]+) and {NUM}(?: [a-z]+)? for ([^.]+)",
            re.IGNORECASE,
        ),
        _bar_three,
    ),
    (
        "line_chart",
        re.compile(
            rf"line graph records temperatures of {NUM}°C at ([^,]+), {NUM}°C at ([^,]+) and {NUM}°C at ([^.]+)",
            re.IGNORECASE,
        ),
        _line_three,
    ),
    (
        "pictogram",
        re.compile(
            rf"each (\w+) represents {NUM} \w+\. A row contains {NUM} \w+",
            re.IGNORECASE,
        ),
        lambda match: {
            "rows": [{"label": "Shown", "count": float(match[3])}],
            "key": float(match[2]),
            "symbol": "★" if match[1].casefold() == "star" else match[1],
        },
    ),
    (
        "dot_plot",
        re.compile(r"dot diagram represents the values ([\d.,\s-]+)\. How many", re.IGNORECASE),
        _dot_values,
    ),
    (
        "stem_leaf",
        re.compile(r"stem-and-leaf row is (\d+)\s*\|\s*([\d\s]+), where ([^.]+)", re.IGNORECASE),
        _stem_row,
    ),
    (
        "histogram",
        re.compile(
            r"equal-width intervals ([\d\s,–-]+(?:and [\d\s–-]+)?) with frequencies ([\d\s,]+(?:and \d+)?)",
            re.IGNORECASE,
        ),
        _equal_histogram,
    ),
    (
        "histogram",
        re.compile(
            rf"interval {NUM}[–-]{NUM} has density {NUM}, and {NUM}[–-]{NUM} has density {NUM}",
            re.IGNORECASE,
        ),
        _density_histogram,
    ),
    (
        "bar_chart",
        re.compile(
            rf"vertical axis starts at {NUM}\. Two values are {NUM} and {NUM}", re.IGNORECASE
        ),
        _truncated_bars,
    ),
    (
        "bar_chart",
        re.compile(
            rf"bar chart begins its vertical axis at {NUM} although the values are {NUM} and {NUM}",
            re.IGNORECASE,
        ),
        _truncated_bars,
    ),
    (
        "probability_scale",
        re.compile(rf"probability scale has value {NUM}", re.IGNORECASE),
        lambda match: {"value": float(match[1])},
    ),
    (
        "spinner",
        re.compile(r"spinner has \w+ equal sectors (?:numbered|labelled) ([^.]+)", re.IGNORECASE),
        _spinner_labels,
    ),
    (
        "coordinate_line",
        re.compile(rf"point \(\s*{NUM},\s*k\s*\) lies on {NUM}x\+{NUM}y={NUM}", re.IGNORECASE),
        lambda match: {
            "point_x": float(match[1]),
            "a": float(match[2]),
            "b": float(match[3]),
            "c": float(match[4]),
            "x_min": -1,
            "x_max": 8,
            "y_min": -1,
            "y_max": 8,
        },
    ),
    (
        "quadratic_graph",
        re.compile(rf"quadratic graph crosses the x-axis at x={NUM} and x={NUM}", re.IGNORECASE),
        _quadratic_roots,
    ),
    (
        "quadratic_graph",
        re.compile(rf"parabola crosses the x-axis at {NUM} and {NUM}", re.IGNORECASE),
        _quadratic_roots,
    ),
    (
        "pie_chart",
        re.compile(r"pie chart sector occupies one quarter of the circle", re.IGNORECASE),
        lambda match: {"labels": ["Sector", "Rest"], "values": [1, 3]},
    ),
]


def stored_request(template: str, inputs: dict[str, Any], question: dict[str, Any]) -> Diagram:
    """Render a stored chart request; useful to keep question matching separate from drawing."""
    return TEMPLATES[template](inputs, answer_values(question))
