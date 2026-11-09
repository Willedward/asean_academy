import json
import math
import re
import shutil

import pytest

from question_bank.diagram_checks import DiagramContext
from question_bank.diagrams import sec1_mensuration as sm
from question_bank.diagrams.common import SEC1_MENSURATION_RENDERER, UnsupportedDiagram
from question_bank.diagrams.questions import (
    render_question_asset,
    request_for,
    text_only_reason,
)
from question_bank.diagrams.regenerate import regenerate_batch
from question_bank.geometry_validation import geometry_diagram_findings
from question_bank.sec1_mensuration_checks import TEMPLATE_FIGURES
from question_bank.validation import validate_bank

G5 = "backend_resources/question_bank/g3_math/secondary_1/g5/v1"
NEW_FIGURES = {
    "B001": ["g5-l2-003", "g5-l2-007"],
    "B002": ["g5-l2-011", "g5-l3-011", "g5-l3-012", "g5-l3-016", "g5-l4-008"],
    "B003": ["g5-l3-018", "g5-l3-020", "g5-l4-010", "g5-l4-012"],
    "B004": ["g5-l2-026", "g5-l2-027", "g5-l2-031", "g5-l4-014"],
}


def cm(value):
    return {"value": value, "unit": "cm"}


def metres(value):
    return {"value": value, "unit": "m"}


CASES = {
    "parallelogram_area": (
        {"base": cm(8), "height": cm(5)},
        ["40"],
        "A parallelogram display has base 8 cm and perpendicular height 5 cm.",
    ),
    "parallelogram_and_trapezium": (
        {
            "base": cm(12),
            "height": cm(6),
            "parallel_short": cm(8),
            "parallel_long": cm(14),
            "trapezium_height": cm(6),
        },
        ["138"],
        "A parallelogram panel has base 12 cm and height 6 cm. Beside it is a trapezium with "
        "parallel sides 8 cm and 14 cm and height 6 cm.",
    ),
    "trapezium_and_parallelogram_algebra": (
        {
            "long_extra": 4,
            "trapezium_height": cm(10),
            "base_extra": 3,
            "height": cm(8),
            "total_area": {"value": 260, "unit": "cm²"},
        },
        ["12"],
        "A design uses a trapezium with parallel sides x cm and (x + 4) cm and height 10 cm, "
        "together with a non-overlapping parallelogram of base (x + 3) cm and height 8 cm.",
    ),
    "rectangle_and_square": (
        {"width": cm(8), "height": cm(5), "side": cm(3)},
        ["49"],
        "A composite card is made from a rectangle 8 cm by 5 cm and a non-overlapping square of "
        "side 3 cm.",
    ),
    "corner_removed": (
        {
            "width": metres(16),
            "height": metres(12),
            "cut_width": metres(6),
            "cut_height": metres(5),
            "tile_area": 0.5,
        },
        ["324"],
        "A 16 m by 12 m lobby has a 6 m by 5 m rectangular corner removed.",
    ),
    "corner_removed_algebra": (
        {
            "width_extra": 5,
            "height_extra": 3,
            "cut_width": cm(5),
            "cut_height": cm(3),
            "remaining_area": {"value": 84, "unit": "cm²"},
        },
        ["6"],
        "A rectangle measures (x + 5) cm by (x + 3) cm. A 5 cm by 3 cm corner is removed.",
    ),
    "joined_rectangles": (
        {"width": cm(10), "height": cm(6), "extension": cm(4), "shared": cm(3)},
        ["40"],
        "A 10 cm by 6 cm rectangle is joined to a 4 cm by 3 cm rectangle along the 3 cm edge.",
    ),
    "joined_rectangles_algebra": (
        {"side": cm(8), "less": 2, "shared": cm(5), "total_area": {"value": 120, "unit": "cm²"}},
        ["52"],
        "A rectangle x cm by 8 cm is joined to a rectangle (x - 2) cm by 5 cm along a complete "
        "5 cm edge.",
    ),
    "uniform_border": (
        {"width": cm(20), "height": cm(14), "border": cm(2)},
        ["120"],
        "A photograph frame measures 20 cm by 14 cm outside. Its border is 2 cm wide.",
    ),
    "track_algebra": (
        {
            "outer_width": 4,
            "outer_height": 2,
            "inner_height": 2,
            "area": {"value": 88, "unit": "m²"},
            "unit": "m",
        },
        ["10"],
        "A rectangular track has outside dimensions (x + 4) m by (x + 2) m and inside dimensions "
        "x m by (x - 2) m.",
    ),
    "cuboid_volume": (
        {"length": cm(8), "depth": cm(5), "height": cm(3)},
        ["120"],
        "A cuboid measures 8 cm by 5 cm by 3 cm.",
    ),
    "open_box": (
        {"length": cm(10), "depth": cm(6), "height": cm(4)},
        ["188"],
        "An open-top cuboid is 10 cm long, 6 cm wide and 4 cm high.",
    ),
    "box_with_cube": (
        {
            "length": metres(1.2),
            "depth": cm(80),
            "height": cm(50),
            "cube": cm(10),
            "percent": 75.0,
        },
        ["360"],
        "A storage box measures 1.2 m by 80 cm by 50 cm. Identical cubes of side 10 cm fill 75%.",
    ),
    "prism_right_triangle_legs": (
        {"base": cm(6), "height": cm(4), "length": cm(10)},
        ["120"],
        "A triangular prism has a right-triangle cross-section with base 6 cm and height 4 cm. "
        "Its length is 10 cm.",
    ),
    "prism_right_triangle_sides": (
        {"sides": [cm(3), cm(4), cm(5)], "length": cm(10)},
        ["132"],
        "A triangular prism has a right-triangle cross-section with sides 3 cm, 4 cm and 5 cm, "
        "and length 10 cm.",
    ),
    "trapezoidal_prism": (
        {"parallel_short": cm(6), "parallel_long": cm(10), "height": cm(5), "length": cm(12)},
        ["480"],
        "A prism has a trapezium cross-section with parallel sides 6 cm and 10 cm and height "
        "5 cm. The prism is 12 cm long.",
    ),
    "two_cubes_joined": (
        {"side": cm(4)},
        ["160"],
        "Two cubes of side 4 cm are joined face to face.",
    ),
    "block_on_cuboid": (
        {
            "length": cm(8),
            "depth": cm(6),
            "height": cm(3),
            "block_length": cm(4),
            "block_depth": cm(3),
            "block_height": cm(2),
        },
        ["208"],
        "A 8 cm by 6 cm by 3 cm cuboid has a 4 cm by 3 cm by 2 cm cuboid attached on top.",
    ),
    "cuboid_tunnel": (
        {
            "length": cm(12),
            "height": cm(8),
            "run": cm(5),
            "hole_width": cm(4),
            "hole_height": cm(3),
        },
        ["420"],
        "A 12 cm by 8 cm by 5 cm cuboid has a rectangular tunnel 4 cm by 3 cm running through its "
        "full 5 cm length.",
    ),
    "cuboid_vertical_hole": (
        {
            "length": cm(9),
            "depth": cm(8),
            "height": cm(6),
            "hole_width": cm(3),
            "hole_depth": cm(2),
        },
        ["396"],
        "A cuboid measures 9 cm by 8 cm by 6 cm. A rectangular hole 3 cm by 2 cm passes through "
        "the full 6 cm height.",
    ),
    "cuboid_cylindrical_hole": (
        {"length": cm(14), "depth": cm(14), "height": cm(10), "radius": cm(3.5)},
        ["1575"],
        "A 14 cm by 14 cm by 10 cm cuboid has a cylindrical hole of radius 3.5 cm drilled through "
        "its 10 cm height.",
    ),
    "cube_cylindrical_hole": (
        {"side": cm(14), "radius": cm(3.5)},
        ["2205"],
        "A cube of side 14 cm has a cylindrical hole of radius 3.5 cm drilled straight through it.",
    ),
    "open_cylinder": (
        {"radius": cm(7), "height": cm(8)},
        ["506"],
        "A cylindrical container has radius 7 cm and height 8 cm and is open at the top.",
    ),
    "open_cylinder_material": (
        {"radius": cm(7), "material": {"value": 594, "unit": "cm²"}},
        ["1540"],
        "An open cylindrical tank has radius 7 cm.",
    ),
}


def render(template):
    inputs, answers, stated = CASES[template]
    return sm.TEMPLATES[template](inputs, answers), answers, stated


def findings(tmp_path, diagram, answers=(), stated="", *, svg=None, spec=None, alt=None):
    path = tmp_path / "diagram.svg"
    path.write_text(svg if svg is not None else diagram.svg, encoding="utf-8")
    context = DiagramContext(tuple(answers), stated) if answers or stated else None
    return geometry_diagram_findings(
        path,
        spec if spec is not None else diagram.generation_spec,
        alt if alt is not None else diagram.alt_text,
        context,
        strict=True,
    )


def codes(*args, **kwargs):
    return {finding.code for finding in findings(*args, **kwargs)}


def clone(diagram):
    return json.loads(json.dumps(diagram.generation_spec))


def distance(spec, first, second):
    a, b = spec["points"][first], spec["points"][second]
    return math.hypot(a[0] - b[0], a[1] - b[1])


def test_every_template_has_a_case_and_expected_figures():
    assert set(CASES) == set(sm.TEMPLATES)
    assert set(TEMPLATE_FIGURES) == set(sm.TEMPLATES)


@pytest.mark.parametrize("template", sorted(CASES))
def test_template_passes_the_checks_and_is_deterministic(tmp_path, template):
    first, answers, stated = render(template)
    second, _, _ = render(template)

    assert first.svg == second.svg
    assert first.alt_text == second.alt_text
    assert first.generation_spec == second.generation_spec
    assert first.generation_spec["renderer"] == SEC1_MENSURATION_RENDERER
    assert first.content_findings == []
    assert findings(tmp_path, first, answers, stated) == []


@pytest.mark.parametrize("template", sorted(CASES))
def test_answers_and_withheld_values_are_not_shown(template):
    diagram, answers, _ = render(template)
    spec = diagram.generation_spec
    visible = " | ".join(re.findall(r"<text[^>]*>([^<]*)</text>", diagram.svg))
    exempt = {item["value"] for item in spec.get("forbidden_label_exemptions", [])}
    for answer in answers:
        assert answer in spec["forbidden_visible_labels"] or answer in exempt
    for label in spec["forbidden_visible_labels"]:
        pattern = rf"(?<![\w.]){re.escape(label)}(?![\w.])"
        assert not re.search(pattern, visible)
        assert not re.search(pattern, diagram.alt_text)


@pytest.mark.parametrize("template", sorted(CASES))
def test_every_label_is_at_least_readable_on_a_phone(template):
    diagram, _, _ = render(template)
    assert diagram.generation_spec["min_phone_font_px"] >= 12
    assert diagram.width == 600


def test_lengths_are_drawn_at_one_scale():
    spec = render("parallelogram_area")[0].generation_spec
    assert distance(spec, "A", "B") / distance(spec, "D", "F") == pytest.approx(8 / 5, abs=0.01)
    assert distance(spec, "A", "D") > distance(spec, "D", "F") + 5

    spec = render("corner_removed")[0].generation_spec
    assert distance(spec, "A", "B") / distance(spec, "F", "A") == pytest.approx(16 / 12, abs=0.01)
    assert distance(spec, "C", "D") / distance(spec, "D", "E") == pytest.approx(6 / 5, abs=0.01)

    spec = render("box_with_cube")[0].generation_spec
    assert distance(spec, "F1", "F2") / distance(spec, "cF2", "cF3") == pytest.approx(12, abs=0.1)


def test_a_cube_is_drawn_as_a_cube():
    spec = render("two_cubes_joined")[0].generation_spec
    assert distance(spec, "P0", "P1") == pytest.approx(distance(spec, "P1", "P2"), abs=0.1)
    assert distance(spec, "P0", "P1") == pytest.approx(distance(spec, "P0", "Q0"), abs=0.1)
    assert distance(spec, "P0", "R0") == pytest.approx(distance(spec, "P1", "R1"), abs=0.1)

    spec = render("cube_cylindrical_hole")[0].generation_spec
    assert distance(spec, "F", "R") == pytest.approx(distance(spec, "F", "L"), abs=0.1)
    assert distance(spec, "F", "R") == pytest.approx(distance(spec, "R", "TR"), abs=0.1)


def test_unknowns_are_drawn_at_a_neutral_size():
    for template, true_value in (
        ("trapezium_and_parallelogram_algebra", 12),
        ("joined_rectangles_algebra", 10),
        ("corner_removed_algebra", 6),
        ("track_algebra", 10),
        ("open_cylinder_material", 10),
    ):
        spec = render(template)[0].generation_spec
        record = spec["neutral_lengths"][0]
        assert record["avoid"] == pytest.approx(true_value)
        assert abs(record["drawn"] - true_value) >= 0.2 * true_value


def test_algebraic_labels_keep_their_differences():
    spec = render("trapezium_and_parallelogram_algebra")[0].generation_spec
    unit = spec["drawn_scale"]
    assert distance(spec, "TA", "TB") - distance(spec, "TC", "TD") == pytest.approx(4 * unit, abs=1)
    assert distance(spec, "PA", "PB") - distance(spec, "TC", "TD") == pytest.approx(3 * unit, abs=1)


def test_a_circle_on_the_top_face_touches_all_four_tangent_edges_in_projection():
    spec = render("cuboid_cylindrical_hole")[0].generation_spec
    near = spec["ellipses"]["near"]
    assert near["rx"] / near["ry"] == pytest.approx(math.sqrt(3), abs=0.01)
    assert near["rx"] == pytest.approx(3.5 * sm.ISO_RX * spec["drawn_scale"], abs=0.1)


def test_block_on_cuboid_dashes_only_the_part_of_the_back_edge_behind_the_block():
    spec = render("block_on_cuboid")[0].generation_spec
    pieces = {s["key"]: s["hidden"] for s in spec["segments"] if s["key"].startswith(("B4Z", "Z"))}
    assert sorted(pieces.values()) == [False, False, True]


# ---------------------------------------------------------------- the reported defect types
def test_validator_rejects_an_unrelated_second_figure(tmp_path):
    diagram, answers, stated = render("parallelogram_area")
    spec = clone(diagram)
    spec["figures"].append(
        {"type": "trapezium", "points": ["A", "B", "C", "D"], "heights": [], "segments": []}
    )
    found = codes(tmp_path, diagram, answers, stated, spec=spec)
    assert "geometry_figure_mismatch" in found
    assert "geometry_figure_not_in_question" in found


def test_validator_rejects_a_solid_the_question_does_not_describe(tmp_path):
    diagram, answers, _ = render("cuboid_volume")
    assert "geometry_figure_not_in_question" in codes(
        tmp_path, diagram, answers, "A triangular prism has length 10 cm and sides 8, 5 and 3 cm."
    )


def test_validator_rejects_a_cut_out_drawn_for_a_joined_shape(tmp_path):
    diagram, answers, _ = render("corner_removed")
    assert "geometry_figure_not_in_question" in codes(
        tmp_path,
        diagram,
        answers,
        "A 16 m by 12 m rectangle is joined to a 6 m by 5 m rectangle along an edge.",
    )


def test_validator_rejects_a_height_labelled_beside_the_slant(tmp_path):
    diagram, answers, stated = render("parallelogram_area")
    spec = clone(diagram)
    for item in spec["measures"]:
        if item["label"] == "5 cm":
            item["segment"] = "DA"
    for label in spec["labels"]:
        if label["text"] == "5 cm":
            label["target"] = "segment:DA"
    svg = diagram.svg.replace('data-label-for="segment:DF"', 'data-label-for="segment:DA"')
    found = codes(tmp_path, diagram, answers, stated, svg=svg, spec=spec)
    assert found & {"geometry_drawn_length", "geometry_label_detached"}


def test_validator_requires_a_dashed_height_with_a_right_angle_at_its_foot(tmp_path):
    diagram, answers, stated = render("parallelogram_area")
    spec = clone(diagram)
    spec["right_angles"] = []
    svg = re.sub(r'<path data-right-angle-marker="F"[^>]*/>\n', "", diagram.svg)
    assert "geometry_height" in codes(tmp_path, diagram, answers, stated, svg=svg, spec=spec)

    spec = clone(diagram)
    for segment in spec["segments"]:
        if segment["key"] == "DF":
            segment["hidden"] = False
    svg = re.sub(r'(data-segment="DF"[^>]*?) stroke-dasharray="[^"]*"', r"\1", diagram.svg)
    assert "geometry_height" in codes(tmp_path, diagram, answers, stated, svg=svg, spec=spec)

    spec = clone(diagram)
    spec["points"]["F"][0] += 30
    assert "geometry_height" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_rejects_missing_measurements(tmp_path):
    diagram, answers, stated = render("corner_removed")
    spec = clone(diagram)
    spec["labels"] = [label for label in spec["labels"] if label["text"] != "6 m"]
    svg = re.sub(r"<text[^>]*>6 m</text>\n", "", diagram.svg)
    assert "geometry_given_unlabelled" in codes(
        tmp_path, diagram, answers, stated, svg=svg, spec=spec
    )

    spec = clone(diagram)
    spec["measures"] = [item for item in spec["measures"] if item["label"] != "6 m"]
    assert "geometry_given_unlabelled" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_rejects_labels_the_question_does_not_use(tmp_path):
    diagram, answers, stated = render("trapezium_and_parallelogram_algebra")
    spec = clone(diagram)
    for label in spec["labels"]:
        if label["text"] == "x cm":
            label["text"] = "a"
    for item in spec["measures"]:
        if item["label"] == "x cm":
            item["label"] = "a"
    svg = diagram.svg.replace(">x cm</text>", ">a</text>")
    alt = diagram.alt_text.replace("x cm", "a")
    assert "geometry_label_not_stated" in codes(
        tmp_path, diagram, answers, stated, svg=svg, spec=spec, alt=alt
    )


def test_validator_rejects_a_length_drawn_at_the_wrong_size(tmp_path):
    diagram, answers, stated = render("parallelogram_area")
    spec = clone(diagram)
    for item in spec["measures"]:
        if item["label"] == "8 cm":
            item["value"] = 12
    assert "geometry_drawn_length" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_rejects_an_unknown_drawn_at_its_true_size(tmp_path):
    diagram, answers, stated = render("joined_rectangles_algebra")
    spec = clone(diagram)
    spec["neutral_lengths"][0]["drawn"] = spec["neutral_lengths"][0]["avoid"]
    assert "geometry_neutral_length" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_requires_a_dashed_complete_shared_edge(tmp_path):
    diagram, answers, stated = render("joined_rectangles")
    spec = clone(diagram)
    for segment in spec["segments"]:
        if segment["key"] == "BJ":
            segment["hidden"] = False
    svg = re.sub(r'(data-segment="BJ"[^>]*?) stroke-dasharray="[^"]*"', r"\1", diagram.svg)
    assert "geometry_shared_edge" in codes(tmp_path, diagram, answers, stated, svg=svg, spec=spec)

    # The edge the shapes share must lie along both rectangles, as a complete edge of the smaller.
    diagram, answers, stated = render("joined_rectangles_algebra")
    spec = clone(diagram)
    spec["figures"][0]["shared"] = "JC"
    assert "geometry_shared_edge" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_rejects_unequal_cubes_and_a_non_square_face(tmp_path):
    diagram, answers, stated = render("two_cubes_joined")
    spec = clone(diagram)
    spec["points"]["P2"][0] -= 40
    spec["points"]["Q2"][0] -= 40
    assert "geometry_figure_shape" in codes(tmp_path, diagram, answers, stated, spec=spec)

    diagram, answers, stated = render("cube_cylindrical_hole")
    spec = clone(diagram)
    spec["points"]["TF"][1] -= 30
    spec["points"]["TR"][1] -= 30
    spec["points"]["TL"][1] -= 30
    assert "geometry_figure_shape" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_rejects_a_solid_hidden_edge(tmp_path):
    diagram, answers, stated = render("cuboid_volume")
    spec = clone(diagram)
    for segment in spec["segments"]:
        if segment["key"] == "F1B1":
            segment["hidden"] = False
    svg = re.sub(r'(data-segment="F1B1"[^>]*?) stroke-dasharray="[^"]*"', r"\1", diagram.svg)
    assert "geometry_hidden_edge" in codes(tmp_path, diagram, answers, stated, svg=svg, spec=spec)


def test_validator_requires_a_right_angle_on_a_right_triangle_section(tmp_path):
    diagram, answers, stated = render("prism_right_triangle_legs")
    spec = clone(diagram)
    spec["right_angles"] = []
    svg = re.sub(r'<path data-right-angle-marker="A"[^>]*/>\n', "", diagram.svg)
    assert "geometry_right_angle_missing" in codes(
        tmp_path, diagram, answers, stated, svg=svg, spec=spec
    )


def test_validator_checks_an_open_cylinder(tmp_path):
    diagram, answers, stated = render("open_cylinder")
    solid_back = re.sub(
        r'(data-ellipse="base" data-half="back"[^>]*?) stroke-dasharray="[^"]*"',
        r"\1",
        diagram.svg,
    )
    assert solid_back != diagram.svg
    assert "geometry_hidden_edge" in codes(tmp_path, diagram, answers, stated, svg=solid_back)

    no_shade = diagram.svg.replace(f'fill="{sm.INTERIOR}"', 'fill="#e7f2f0"')
    assert "geometry_open_top" in codes(tmp_path, diagram, answers, stated, svg=no_shade)

    closed = diagram.svg.replace(">Open top</text>", ">Top</text>")
    spec = clone(diagram)
    spec["captions"] = ["Top"]
    assert "geometry_open_top" in codes(tmp_path, diagram, answers, stated, svg=closed, spec=spec)


def test_validator_rejects_a_hole_rim_off_its_face(tmp_path):
    diagram, answers, stated = render("cuboid_cylindrical_hole")
    spec = clone(diagram)
    spec["figures"][1]["face"] = ["TF", "TR", "TL", "TL"]
    spec_far = clone(diagram)
    for half in re.findall(r'data-ellipse="far" data-half="(\w+)"', diagram.svg):
        assert half in {"back", "front"}
    solid = re.sub(
        r'(data-ellipse="far" data-half="\w+"[^>]*?) stroke-dasharray="[^"]*"', r"\1", diagram.svg
    )
    assert "geometry_hole" in codes(tmp_path, diagram, answers, stated, svg=solid, spec=spec_far)
    assert "geometry_hole" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_requires_rectangular_hole_edges_to_be_dashed(tmp_path):
    diagram, answers, stated = render("cuboid_tunnel")
    spec = clone(diagram)
    for segment in spec["segments"]:
        if segment["key"] == "H1J1":
            segment["hidden"] = False
    svg = re.sub(r'(data-segment="H1J1"[^>]*?) stroke-dasharray="[^"]*"', r"\1", diagram.svg)
    assert "geometry_hole" in codes(tmp_path, diagram, answers, stated, svg=svg, spec=spec)


def test_validator_rejects_stray_marks_and_duplicated_strokes(tmp_path):
    diagram, answers, stated = render("corner_removed")
    arrow = diagram.svg.replace(
        '</g>\n<g data-layer="labels"',
        '<path d="M560 180 H590" stroke="#124e52" stroke-width="3" fill="none"/>\n'
        '</g>\n<g data-layer="labels"',
    )
    assert "geometry_stray_stroke" in codes(tmp_path, diagram, answers, stated, svg=arrow)

    box = diagram.svg.replace(
        '</g>\n<g data-layer="labels"',
        '<rect x="480" y="30" width="60" height="60" fill="none" stroke="#124e52"/>\n'
        '</g>\n<g data-layer="labels"',
    )
    assert "geometry_stray_stroke" in codes(tmp_path, diagram, answers, stated, svg=box)

    a, b = diagram.generation_spec["points"]["A"], diagram.generation_spec["points"]["B"]
    spec = clone(diagram)
    spec["segments"].append({"key": "BA", "from": "B", "to": "A", "hidden": True, "role": "edge"})
    spec["figures"][0]["segments"].append("BA")
    line = (
        f'<line data-segment="BA" x1="{b[0]}" y1="{b[1]}" x2="{a[0]}" y2="{a[1]}" stroke="#94a3b8" '
        'stroke-width="2" stroke-dasharray="10 8"/>\n'
    )
    dashed = diagram.svg.replace(
        '</g>\n<g data-layer="labels"', f'{line}</g>\n<g data-layer="labels"'
    )
    assert "geometry_duplicate_stroke" in codes(
        tmp_path, diagram, answers, stated, svg=dashed, spec=spec
    )

    spec = clone(diagram)
    spec["figures"][0]["segments"].remove("AB")
    assert "geometry_stray_stroke" in codes(tmp_path, diagram, answers, stated, spec=spec)


def test_validator_rejects_undeclared_text(tmp_path):
    diagram, answers, stated = render("corner_removed")
    extra = diagram.svg.replace(
        "</g>\n</svg>",
        '<text x="300" y="30" font-size="24" text-anchor="middle">remaining region</text>\n</g>\n</svg>',
    )
    assert "geometry_stray_text" in codes(tmp_path, diagram, answers, stated, svg=extra)


def test_validator_rejects_alt_text_that_does_not_match_the_drawing(tmp_path):
    diagram, answers, stated = render("parallelogram_area")
    # The defect the audit reported: "Stated measures include 2.4 m², 500 cm²".
    assert "geometry_alt_text_values" in codes(
        tmp_path,
        diagram,
        answers,
        stated,
        alt=diagram.alt_text + " Stated measures include 500 cm².",
    )
    assert "geometry_alt_text_values" in codes(
        tmp_path, diagram, answers, stated, alt="A parallelogram with a right angle marked."
    )
    assert "geometry_alt_text_figure" in codes(
        tmp_path, diagram, answers, stated, alt=diagram.alt_text.replace("parallelogram", "shape")
    )
    assert "geometry_alt_text_figure" in codes(
        tmp_path,
        diagram,
        answers,
        stated,
        alt=diagram.alt_text.replace(
            ", with a right angle marked where the height meets the base", ""
        ),
    )


def test_validator_rejects_an_answer_in_the_svg_or_the_alt_text(tmp_path):
    diagram, answers, stated = render("open_cylinder_material")
    assert "geometry_answer_leak" in codes(
        tmp_path, diagram, answers, stated, svg=diagram.svg.replace(">h</text>", ">10 cm</text>")
    )
    assert "geometry_answer_leak" in codes(
        tmp_path, diagram, answers, stated, alt=diagram.alt_text + " The volume is 1540."
    )
    assert "geometry_answer_not_withheld" in codes(tmp_path, diagram, ["1541"], stated)


# ----------------------------------------------------------------- reading the question data
def legacy_question(prompt, answer="1", key="g5-test"):
    return {
        "stable_key": key,
        "school_level": "secondary_1",
        "topic_code": "G5",
        "primary_outcome": "5.1",
        "stem": [],
        "assets": [
            {"asset_key": "a", "generation_spec": {"renderer": "nextscholar-geometry-svg-v1"}}
        ],
        "parts": [
            {
                "prompt": [{"type": "text", "text": prompt}],
                "response": {"canonical_answer": answer},
            }
        ],
    }


def test_only_sec1_g5_routes_to_this_generator():
    prompt = "A cuboid measures 8 cm by 5 cm by 3 cm. Find its volume in cm³."
    question = legacy_question(prompt, answer="120")
    assert request_for(question, question["assets"][0]).renderer == SEC1_MENSURATION_RENDERER

    conversion = "Convert 3 m² to cm². Enter the numerical value only."
    for level, topic in (("secondary_2", "G5"), ("secondary_1", "G1")):
        other = {
            **legacy_question(prompt, answer="120"),
            "school_level": level,
            "topic_code": topic,
        }
        with pytest.raises(UnsupportedDiagram):
            request_for(other, other["assets"][0])
        assert (
            text_only_reason(
                {**legacy_question(conversion), "school_level": level, "topic_code": topic}
            )
            is None
        )


def test_the_other_banks_keep_their_own_text_only_decisions(repository_root):
    g2 = repository_root / "backend_resources/question_bank/g3_math/secondary_2/g2/v1/questions"
    question = json.loads((g2 / "g2-l5-504.json").read_text(encoding="utf-8"))
    assert text_only_reason(question)
    g1 = repository_root / "backend_resources/question_bank/g3_math/secondary_1/g1/v1/questions"
    question = json.loads((g1 / "g1-l4-011.json").read_text(encoding="utf-8"))
    assert text_only_reason(question)


def test_an_unrecognised_prompt_is_reported_not_drawn():
    question = legacy_question("Find the area of a kite with diagonals 6 cm and 8 cm.")
    with pytest.raises(UnsupportedDiagram, match="template matches"):
        render_question_asset(question, question["assets"][0])


def test_impossible_givens_are_refused():
    with pytest.raises(UnsupportedDiagram):
        sm.prism_right_triangle_sides({"sides": [cm(3), cm(4), cm(6)], "length": cm(10)})
    with pytest.raises(UnsupportedDiagram):
        sm.uniform_border({"width": cm(4), "height": cm(4), "border": cm(3)})
    with pytest.raises(UnsupportedDiagram):
        sm.corner_removed(
            {"width": cm(4), "height": cm(4), "cut_width": cm(5), "cut_height": cm(1)}
        )
    with pytest.raises(UnsupportedDiagram):
        sm.cube_cylindrical_hole({"side": cm(4), "radius": cm(3)})


def test_wrong_answer_key_is_reported_for_the_question_text():
    diagram = sm.parallelogram_area({"base": cm(8), "height": cm(5)}, ["41"])
    assert "does not match" in diagram.content_findings[0]


@pytest.mark.parametrize(
    "prompt",
    [
        "Convert 3 m² to cm². Enter the numerical value only.",
        "Two non-overlapping cuboids have volumes 120 cm³ and 80 cm³. They are joined.",
        "One sheet has area 2.4 m² and another has area 6 500 cm². Find the difference in cm².",
        "A 9 cm by 7 cm rectangle and a 6 cm by 5 cm rectangle are joined along an edge of length "
        "x cm. The outside perimeter is 48 cm. Find x.",
    ],
)
def test_figures_that_add_nothing_or_contradict_the_prompt_stay_text_only(prompt):
    assert text_only_reason(legacy_question(prompt))


def test_a_corrected_shared_edge_prompt_gets_a_figure():
    prompt = (
        "A 9 cm by 7 cm rectangle is joined to a 6 cm by 5 cm rectangle along the smaller "
        "rectangle's 5 cm edge. Find the outside perimeter."
    )
    question = legacy_question(prompt, answer="44")
    assert text_only_reason(question) is None
    diagram = render_question_asset(question, question["assets"][0])
    assert diagram.generation_spec["template"] == "joined_rectangles"
    assert diagram.content_findings == []


def test_every_g5_question_with_a_diagram_is_drawn_or_refused(repository_root):
    bank = repository_root / G5
    drawn = 0
    for path in sorted((bank / "questions").glob("*.json")):
        question = json.loads(path.read_text(encoding="utf-8"))
        for asset in question.get("assets", []):
            if text_only_reason(question):
                continue
            diagram = render_question_asset(question, asset)
            assert diagram.content_findings == [], question["stable_key"]
            drawn += 1
    assert drawn >= 12


def copy_bank(repository_root, tmp_path):
    target = tmp_path / "v1"
    shutil.copytree(repository_root / G5, target, ignore=shutil.ignore_patterns("review_packets"))
    return target


def test_applying_all_batches_clears_strict_geometry(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    for batch, additions in NEW_FIGURES.items():
        report = regenerate_batch(bank, batch, apply=True, add=additions)
        assert report.ok, report.unsupported
        assert not [asset for asset in report.assets if asset.validation_errors]
        assert not [asset for asset in report.assets if asset.content_findings]
    result = validate_bank(bank, strict_geometry=True)
    geometry = [issue for issue in result.errors if issue.code.startswith("geometry_")]
    assert geometry == []
    drawn = sum(
        bool(json.loads(path.read_text(encoding="utf-8")).get("assets"))
        for path in (bank / "questions").glob("*.json")
    )
    assert drawn == 27


def test_apply_revisions_files_and_records_the_decisions(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    before = json.loads((bank / "questions" / "g5-l5-002.json").read_text())
    count = json.loads((bank / "diagram_audit.json").read_text())["diagram_question_count"]
    report = regenerate_batch(bank, "B002", apply=True, add=NEW_FIGURES["B002"])
    assert report.ok

    question = json.loads((bank / "questions" / "g5-l5-002.json").read_text())
    if before["assets"][0]["generation_spec"]["renderer"] != SEC1_MENSURATION_RENDERER:
        assert question["revision"] == before["revision"] + 1
    assert (bank / before["assets"][0]["path"]).is_file()
    assert question["assets"][0]["path"].endswith(f"-r{question['revision']}.svg")
    assert question["assets"][0]["generation_spec"]["renderer"] == SEC1_MENSURATION_RENDERER
    assert question["status"] == "draft"
    assert question["provenance"]["reviewed_by"] is None
    assert question["parts"] == before["parts"]

    added = json.loads((bank / "questions" / "g5-l2-011.json").read_text())
    assert added["stem"][1] == {"type": "asset_ref", "asset_key": "g5-l2-011-diagram"}
    assert added["revision"] == 2
    audit = json.loads((bank / "diagram_audit.json").read_text())
    decision = next(item for item in audit["decisions"] if item["question_key"] == "g5-l2-011")
    assert decision["decision"] == "diagram_added"
    assert audit["diagram_question_count"] == count

    again = regenerate_batch(bank, "B002", apply=True, add=NEW_FIGURES["B002"])
    assert all(asset.unchanged for asset in again.assets)


def test_apply_makes_figures_with_no_spatial_content_text_only(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    regenerate_batch(bank, "B001", apply=True, add=NEW_FIGURES["B001"])
    for key in ("g5-l1-005", "g5-l1-006", "g5-l3-007"):
        question = json.loads((bank / "questions" / f"{key}.json").read_text())
        assert question["assets"] == []
        assert question["stem"] == []
        assert (bank / "assets" / f"{key}-diagram.svg").is_file()
    audit = json.loads((bank / "diagram_audit.json").read_text())
    decision = next(item for item in audit["decisions"] if item["question_key"] == "g5-l1-006")
    assert decision["decision"] == "text_sufficient"
    assert "no spatial" in decision["reason"]


def test_the_contradictory_wording_is_refused():
    prompt = (
        "A 9 cm by 7 cm rectangle and a 6 cm by 5 cm rectangle are joined along an edge of "
        "length x cm. The outside perimeter is 48 cm. Find x."
    )

    assert sm.text_only_reason(prompt) is not None
