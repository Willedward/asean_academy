import json
import math
import re
import shutil

import pytest

from question_bank.diagram_checks import DiagramContext
from question_bank.diagrams import plane_geometry as pg
from question_bank.diagrams.common import PLANE_GEOMETRY_RENDERER, UnsupportedDiagram
from question_bank.diagrams.questions import render_question_asset, request_for, text_only_reason
from question_bank.diagrams.regenerate import regenerate_batch
from question_bank.geometry_validation import geometry_diagram_findings
from question_bank.validation import validate_bank

G1 = "backend_resources/question_bank/g3_math/secondary_1/g1/v1"
NEW_FIGURES = {
    "B001": ["g1-l3-005"],
    "B002": ["g1-l3-012", "g1-l3-015", "g1-l4-008"],
    "B003": ["g1-l3-020", "g1-l4-011"],
    "B004": ["g1-l2-026", "g1-l3-026"],
}


def cm(value):
    return {"value": value, "unit": "cm"}


CASES = {
    "straight_line_given": ({"given": 68}, ["112"]),
    "straight_line_ratio": ({"ratio": [2, 3]}, ["108"]),
    "complement_split": ({"given": 38}, ["52"]),
    "intersection_expressions": (
        {
            "first": {"coefficient": 3, "constant": -5},
            "second": {"coefficient": 2, "constant": 15},
        },
        ["34"],
    ),
    "intersection_obtuse": ({"obtuse": 128}, ["104"]),
    "parallel_corresponding": ({"given": 64}, ["64"]),
    "parallel_cointerior_ratio": ({"ratio": [2, 3]}, ["108"]),
    "two_transversals_meeting": ({"left_angle": 38, "right_angle": 67}, ["75"]),
    "perpendicular_transversal": ({"given": 37}, ["53"]),
    "triangle_third_angle": ({"angles": [50, 60]}, ["70"]),
    "triangle_expressions": ({"offsets": [20, 40]}, ["80"]),
    "triangle_angle_sum": ({}, ["180"]),
    "isosceles_exterior": ({"exterior": 124}, ["62"]),
    "diagonals_equal_bisect": ({}, ["2"]),
    "diagonals_perpendicular_one_bisected": ({}, ["5"]),
    "kite_symmetry": ({}, ["1"]),
    "kite_angles": ({"angle_a": 70, "angle_c": 110}, ["90"]),
    "perpendicular_bisector_midpoint": ({"segment": cm(8)}, ["4"]),
    "safe_radius": ({"segment": cm(10)}, ["6"]),
    "equilateral_on_ray": ({}, ["60"]),
    "sss_arc_radius": ({"ab": cm(5), "ac": cm(6), "bc": cm(7)}, ["6"]),
    "sss_mirror_image": ({"sides": [cm(5), cm(6), cm(7)]}, ["1"]),
}


def render(template):
    inputs, answers = CASES[template]
    return pg.TEMPLATES[template](inputs, answers), answers


def findings(tmp_path, diagram, answers=(), *, svg=None, spec=None, alt=None):
    path = tmp_path / "diagram.svg"
    path.write_text(svg if svg is not None else diagram.svg, encoding="utf-8")
    context = DiagramContext(tuple(answers), "") if answers else None
    return geometry_diagram_findings(
        path,
        spec if spec is not None else diagram.generation_spec,
        alt if alt is not None else diagram.alt_text,
        context,
        strict=True,
    )


def codes(*args, **kwargs):
    return {finding.code for finding in findings(*args, **kwargs)}


def angle_at(spec, vertex, first, second):
    points = spec["points"]
    v, a, b = points[vertex], points[first], points[second]
    u = (a[0] - v[0], a[1] - v[1])
    w = (b[0] - v[0], b[1] - v[1])
    cosine = (u[0] * w[0] + u[1] * w[1]) / (math.hypot(*u) * math.hypot(*w))
    return math.degrees(math.acos(max(-1, min(1, cosine))))


def distance(spec, first, second):
    a, b = spec["points"][first], spec["points"][second]
    return math.hypot(a[0] - b[0], a[1] - b[1])


def test_every_template_has_a_case():
    assert set(CASES) == set(pg.TEMPLATES)


@pytest.mark.parametrize("template", sorted(CASES))
def test_template_passes_the_checks_and_is_deterministic(tmp_path, template):
    first, answers = render(template)
    second, _ = render(template)

    assert first.svg == second.svg
    assert first.alt_text == second.alt_text
    assert first.generation_spec == second.generation_spec
    assert first.generation_spec["renderer"] == PLANE_GEOMETRY_RENDERER
    assert first.content_findings == []
    assert findings(tmp_path, first, answers) == []


@pytest.mark.parametrize("template", sorted(CASES))
def test_answers_and_withheld_values_are_not_shown(template):
    diagram, answers = render(template)
    spec = diagram.generation_spec
    visible = " | ".join(re.findall(r"<text[^>]*>([^<]*)</text>", diagram.svg))
    exempt = {item["value"] for item in spec.get("forbidden_label_exemptions", [])}
    for answer in answers:
        assert answer in spec["forbidden_visible_labels"] or answer in exempt
    for label in spec["forbidden_visible_labels"]:
        pattern = rf"(?<![\w.]){re.escape(label)}(?![\w.])"
        assert not re.search(pattern, visible)
        assert not re.search(pattern, diagram.alt_text)


def test_angles_are_drawn_at_their_stated_size():
    spec = render("two_transversals_meeting")[0].generation_spec
    assert angle_at(spec, "A", "B", "P") == pytest.approx(38, abs=0.3)
    assert angle_at(spec, "B", "A", "P") == pytest.approx(67, abs=0.3)
    assert angle_at(spec, "P", "A", "B") == pytest.approx(75, abs=0.3)
    assert spec["points"]["A"][1] == spec["points"]["B"][1]
    assert spec["points"]["L1"][1] != spec["points"]["M1"][1]

    spec = render("kite_angles")[0].generation_spec
    assert angle_at(spec, "A", "B", "D") == pytest.approx(70, abs=0.3)
    assert angle_at(spec, "C", "B", "D") == pytest.approx(110, abs=0.3)
    assert angle_at(spec, "B", "A", "C") == pytest.approx(90, abs=0.3)
    assert spec["right_angles"] == []

    spec = render("perpendicular_transversal")[0].generation_spec
    assert angle_at(spec, "P", "A", "B") == pytest.approx(90, abs=0.3)
    assert angle_at(spec, "B", "A", "P") == pytest.approx(53, abs=0.3)


def test_constructions_use_the_stated_lengths():
    spec = render("sss_arc_radius")[0].generation_spec
    assert distance(spec, "A", "C") / distance(spec, "A", "B") == pytest.approx(6 / 5, abs=0.01)
    assert distance(spec, "B", "C") / distance(spec, "A", "B") == pytest.approx(7 / 5, abs=0.01)
    assert spec["arcs"]["arc-a-1"]["center"] == "A"

    spec = render("sss_mirror_image")[0].generation_spec
    assert distance(spec, "A", "C") == pytest.approx(distance(spec, "A", "D"), abs=0.5)
    assert distance(spec, "B", "C") == pytest.approx(distance(spec, "B", "D"), abs=0.5)

    # The safe-radius figure must not draw the answer: 6 cm on a 10 cm segment is a ratio of 0.6.
    spec = render("safe_radius")[0].generation_spec
    assert distance(spec, "A", "P") / distance(spec, "A", "B") == pytest.approx(0.78, abs=0.01)


def test_diagonal_figures_draw_no_quadrilateral_and_name_no_shape():
    for template in ("diagonals_equal_bisect", "diagonals_perpendicular_one_bisected"):
        diagram, _ = render(template)
        assert "<polygon" not in diagram.svg
        for word in pg.QUADRILATERAL_WORDS:
            assert word not in diagram.alt_text.casefold()
            assert word in diagram.generation_spec["forbidden_visible_labels"]
    spec = render("diagonals_equal_bisect")[0].generation_spec
    assert angle_at(spec, "O", "C", "D") == pytest.approx(58, abs=0.3)
    assert spec["right_angles"] == []


# ---------------------------------------------------------------- the reported defect types
def test_validator_rejects_an_arc_that_is_not_centred_on_its_vertex(tmp_path):
    diagram, answers = render("triangle_third_angle")
    flipped = re.sub(
        r'(data-angle-marker="angle-a" d="M\S+ \S+ A\S+ \S+ 0 0 )([01])',
        lambda m: m[1] + ("0" if m[2] == "1" else "1"),
        diagram.svg,
    )
    assert flipped != diagram.svg
    spec = json.loads(json.dumps(diagram.generation_spec))
    for marker in spec["angle_markers"]:
        if marker["marker_key"] == "angle-a":
            marker["sweep"] = 1 - marker["sweep"]
    assert "geometry_angle_marker_centre" in codes(tmp_path, diagram, answers, svg=flipped, spec=spec)


def test_validator_rejects_an_arc_that_sweeps_outside_its_angle(tmp_path):
    diagram, answers = render("triangle_third_angle")
    swept = re.sub(
        r'(data-angle-marker="angle-a" d="M\S+ \S+ A\S+ \S+ 0 )0 ([01])',
        lambda m: f"{m[1]}1 {1 - int(m[2])}",
        diagram.svg,
    )
    assert swept != diagram.svg
    spec = json.loads(json.dumps(diagram.generation_spec))
    for marker in spec["angle_markers"]:
        if marker["marker_key"] == "angle-a":
            marker["large_arc"], marker["sweep"] = 1, 1 - marker["sweep"]
    assert "geometry_angle_marker_sweep" in codes(tmp_path, diagram, answers, svg=swept, spec=spec)


def test_validator_rejects_an_arc_on_a_ray_that_is_not_drawn(tmp_path):
    diagram, answers = render("straight_line_given")
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["segments"] = [item for item in spec["segments"] if item["key"] != "OT"]
    svg = re.sub(r'<line data-segment="OT"[^>]*/>\n', "", diagram.svg)
    assert "geometry_angle_ray_undrawn" in codes(tmp_path, diagram, answers, svg=svg, spec=spec)


def test_validator_rejects_a_false_parallel_marking(tmp_path):
    diagram, answers = render("parallel_corresponding")
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["points"]["L2"][1] += 40
    x2, y2 = spec["points"]["L2"]
    svg = re.sub(
        r'(<line data-segment="L1L2" [^>]*?)x2="[^"]+" y2="[^"]+"',
        rf'\g<1>x2="{x2}" y2="{y2}"',
        diagram.svg,
    )
    assert "geometry_marking" in codes(tmp_path, diagram, answers, svg=svg, spec=spec)


def test_validator_rejects_false_perpendicular_and_equal_relationships(tmp_path):
    diagram, answers = render("perpendicular_transversal")
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["relationships"].append({"type": "perpendicular", "segments": ["L1L2", "M1M2"]})
    assert "geometry_relationship" in codes(tmp_path, diagram, answers, spec=spec)

    diagram, answers = render("kite_symmetry")
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["equal_marks"][0]["segments"] = ["AB", "CB"]
    assert "geometry_marking" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_a_marked_right_angle_that_is_not_right(tmp_path):
    diagram, answers = render("perpendicular_transversal")
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["points"]["A"][0] -= 40
    assert "geometry_right_angle_measure" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_a_forbidden_label_in_the_svg_or_the_alt_text(tmp_path):
    diagram, answers = render("triangle_third_angle")
    assert "geometry_answer_leak" in codes(
        tmp_path, diagram, answers, svg=diagram.svg.replace(">x</text>", ">70°</text>")
    )
    assert "geometry_answer_leak" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text + " The third angle is 70°."
    )
    assert "geometry_answer_not_withheld" in codes(tmp_path, diagram, ["71"])


def test_validator_rejects_alt_text_that_does_not_match_the_drawing(tmp_path):
    diagram, answers = render("straight_line_given")
    # The defect the audit reported: alt text that names a value the image does not contain.
    assert "geometry_alt_text_values" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text + " Stated measures include 35°."
    )
    assert "geometry_alt_text_values" in codes(
        tmp_path, diagram, answers, alt="A straight line with one ray. It is marked 68°."
    )
    assert "geometry_alt_text_figure" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text + " It has a right angle."
    )
    assert "geometry_alt_text_figure" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text.replace("straight line", "diagram")
    )
    diagram, answers = render("parallel_corresponding")
    assert "geometry_alt_text_figure" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text.replace("parallel", "horizontal")
    )


def test_validator_rejects_colliding_labels(tmp_path):
    diagram, answers = render("triangle_third_angle")
    match = re.search(r'<text data-label-for="angle:angle-x" x="([\d.]+)" y="([\d.]+)"', diagram.svg)
    other = re.search(r'<text data-label-for="angle:angle-a" x="([\d.]+)" y="([\d.]+)"', diagram.svg)
    overlapped = diagram.svg.replace(
        f'angle:angle-x" x="{match[1]}" y="{match[2]}"',
        f'angle:angle-x" x="{other[1]}" y="{other[2]}"',
    )
    found = codes(tmp_path, diagram, answers, svg=overlapped)
    assert "geometry_label_overlap" in found

    a = diagram.generation_spec["points"]["A"]
    on_stroke = diagram.svg.replace(
        f'angle:angle-x" x="{match[1]}" y="{match[2]}"',
        f'angle:angle-x" x="{a[0] + 60}" y="{a[1]}"',
    )
    assert "geometry_label_collision" in codes(tmp_path, diagram, answers, svg=on_stroke)


def test_validator_rejects_a_compass_arc_off_its_centre(tmp_path):
    diagram, answers = render("sss_arc_radius")
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["arcs"]["arc-a-1"]["center"] = "B"
    assert "geometry_arc" in codes(tmp_path, diagram, answers, spec=spec)


# ----------------------------------------------------------------- reading the question data
def legacy_question(prompt, answer="1", assets=True):
    return {
        "stable_key": "g1-test",
        "primary_outcome": "1.1",
        "stem": [],
        "assets": [{"asset_key": "a", "generation_spec": {"renderer": "nextscholar-geometry-svg-v1"}}]
        if assets
        else [],
        "parts": [
            {
                "prompt": [{"type": "text", "text": prompt}],
                "response": {"canonical_answer": answer},
            }
        ],
    }


def test_an_unrecognised_prompt_is_reported_not_drawn():
    question = legacy_question("Find the area of the shaded sector.")
    with pytest.raises(UnsupportedDiagram, match="template matches"):
        render_question_asset(question, question["assets"][0])


def test_impossible_givens_are_refused():
    with pytest.raises(UnsupportedDiagram):
        pg.triangle_third_angle({"angles": [120, 70]})
    with pytest.raises(UnsupportedDiagram):
        pg.sss_arc_radius({"ab": cm(1), "ac": cm(2), "bc": cm(9)})
    with pytest.raises(UnsupportedDiagram):
        pg.complement_split({"given": 100})


def test_wrong_answer_key_is_reported_for_the_question_text():
    diagram = pg.triangle_third_angle({"angles": [50, 60]}, ["75"])
    assert "does not match" in diagram.content_findings[0]


def test_stored_template_takes_precedence_over_the_prompt():
    question = legacy_question("A reworded prompt the patterns do not know.")
    stored = {
        "generation_spec": {
            "renderer": PLANE_GEOMETRY_RENDERER,
            "template": "triangle_third_angle",
            "inputs": {"angles": [50, 60]},
        }
    }
    assert request_for(question, stored).template == "triangle_third_angle"


@pytest.mark.parametrize(
    "prompt",
    [
        "Use this code: acute = 1, right = 2, obtuse = 3, reflex = 4. Enter the code for an angle of 35°.",
        "A quadrilateral has four equal sides and four right angles. Enter its most specific code.",
        "A parallelogram has four equal sides and equal diagonals. Enter its most specific code.",
        "A convex polygon has interior-angle sum 1260°. Find its number of sides.",
        "The exterior angles of two regular polygons are in the ratio 2:3.",
        "A regular polygon has exactly five diagonals drawn from each vertex. How many sides does the polygon have?",
    ],
)
def test_figures_that_show_the_answer_stay_text_only(prompt):
    assert text_only_reason(legacy_question(prompt))


def test_every_g1_question_with_a_diagram_is_drawn_or_refused(repository_root):
    bank = repository_root / G1
    drawn = 0
    for path in sorted((bank / "questions").glob("*.json")):
        question = json.loads(path.read_text(encoding="utf-8"))
        for asset in question.get("assets", []):
            if text_only_reason(question):
                continue
            diagram = render_question_asset(question, asset)
            assert diagram.content_findings == [], question["stable_key"]
            drawn += 1
    assert drawn >= 10


def copy_bank(repository_root, tmp_path):
    target = tmp_path / "v1"
    shutil.copytree(repository_root / G1, target, ignore=shutil.ignore_patterns("review_packets"))
    return target


def test_applying_all_batches_clears_strict_geometry(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    for batch, additions in NEW_FIGURES.items():
        report = regenerate_batch(bank, batch, apply=True, add=additions)
        assert report.ok, report.unsupported
    result = validate_bank(bank, strict_geometry=True)
    geometry = [issue for issue in result.errors if issue.code.startswith("geometry_")]
    assert geometry == []


def test_apply_revisions_files_and_records_the_decisions(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    before = json.loads((bank / "questions" / "g1-l5-005.json").read_text())
    report = regenerate_batch(bank, "B004", apply=True, add=NEW_FIGURES["B004"])
    assert report.ok

    question = json.loads((bank / "questions" / "g1-l5-005.json").read_text())
    if before["assets"][0]["generation_spec"]["renderer"] != PLANE_GEOMETRY_RENDERER:
        assert question["revision"] == before["revision"] + 1
        assert (bank / before["assets"][0]["path"]).is_file()
    assert question["assets"][0]["path"].endswith(f"-r{question['revision']}.svg")
    assert question["status"] == "draft"
    assert question["provenance"]["reviewed_by"] is None

    added = json.loads((bank / "questions" / "g1-l2-026.json").read_text())
    assert added["stem"][1] == {"type": "asset_ref", "asset_key": "g1-l2-026-diagram"}
    audit = json.loads((bank / "diagram_audit.json").read_text())
    decision = next(item for item in audit["decisions"] if item["question_key"] == "g1-l2-026")
    assert decision["decision"] == "diagram_added"
    assert decision["asset_key"] == "g1-l2-026-diagram"

    again = regenerate_batch(bank, "B004", apply=True, add=NEW_FIGURES["B004"])
    assert all(asset.unchanged for asset in again.assets)


def test_apply_makes_an_answer_revealing_item_text_only(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    regenerate_batch(bank, "B002", apply=True, add=NEW_FIGURES["B002"])
    question = json.loads((bank / "questions" / "g1-l5-003.json").read_text())
    assert question["assets"] == []
    assert question["stem"] == []
    audit = json.loads((bank / "diagram_audit.json").read_text())
    decision = next(item for item in audit["decisions"] if item["question_key"] == "g1-l5-003")
    assert decision["decision"] == "text_sufficient"
    assert "side counts" in decision["reason"]
    assert (bank / "assets" / "g1-l5-003-diagram.svg").is_file()
