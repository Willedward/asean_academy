import json
import math
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from question_bank.diagram_checks import DiagramContext
from question_bank.diagrams import CHECKED_RENDERERS
from question_bank.diagrams import mensuration as me
from question_bank.diagrams import right_triangle as rt
from question_bank.diagrams.common import answer_values
from question_bank.diagrams.questions import (
    LESSON_TEMPLATES,
    diagram_assets,
    question_text,
    render_lesson_asset,
    render_question_asset,
    request_for,
)
from question_bank.geometry_validation import (
    CHECKED_GEOMETRY_RENDERERS,
    geometry_diagram_findings,
)

G4 = "backend_resources/question_bank/g3_math/secondary_2/g4/v1"
G5 = "backend_resources/question_bank/g3_math/secondary_2/g5/v1"
SEC2_COURSE = "backend_resources/courses/g3_math/secondary_2/g2/v1"


def q(value, unit="cm"):
    return {"value": value, "unit": unit}


def angle_at(points, vertex, first, second):
    v, a, b = points[vertex], points[first], points[second]
    u = (a[0] - v[0], a[1] - v[1])
    w = (b[0] - v[0], b[1] - v[1])
    cosine = (u[0] * w[0] + u[1] * w[1]) / (math.hypot(*u) * math.hypot(*w))
    return math.degrees(math.acos(max(-1, min(1, cosine))))


def visible_text(svg):
    root = ET.fromstring(svg)
    return [
        "".join(node.itertext()) for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text"
    ]


def findings_for(tmp_path, diagram, answers=(), stated=""):
    path = tmp_path / "diagram.svg"
    path.write_text(diagram.svg)
    context = DiagramContext(tuple(answers), stated) if answers or stated else None
    return geometry_diagram_findings(path, diagram.generation_spec, diagram.alt_text, context)


def lines(svg, key):
    return re.search(rf'<line data-segment="{re.escape(key)}"[^>]*/>', svg).group(0)


def load_questions(repository_root, bank):
    return [
        json.loads(path.read_text())
        for path in sorted((repository_root / bank / "questions").glob("*.json"))
    ]


def test_validator_and_generators_agree_on_checked_renderers():
    assert CHECKED_RENDERERS == CHECKED_GEOMETRY_RENDERERS


# ---------------------------------------------------------------------- right triangles
def test_angle_arc_is_at_the_acute_vertex_and_the_stated_size(tmp_path):
    diagram = rt.tangent_opposite({"angle": 60, "adjacent": q(14, "m")}, ["24.2"])
    spec = diagram.generation_spec
    points = spec["points"]

    assert angle_at(points, "C", "A", "B") == pytest.approx(60, abs=0.2)
    assert angle_at(points, "A", "B", "C") == pytest.approx(90, abs=0.2)
    [marker] = spec["angle_markers"]
    assert marker["center"] == points["C"]
    assert spec["right_angles"] == [{"vertex": "A", "arms": ["B", "C"], "marker_size": 22}]
    assert "60°" in visible_text(diagram.svg)
    assert findings_for(tmp_path, diagram, ["24.2"]) == []


@pytest.mark.parametrize("degrees", [14.3, 30, 45, 55, 60])
def test_drawn_angle_matches_every_stated_size(degrees):
    diagram = rt.tangent_adjacent({"angle": degrees, "opposite": q(6, "m")})
    points = diagram.generation_spec["points"]

    assert angle_at(points, "C", "A", "B") == pytest.approx(degrees, abs=0.3)


def test_find_angle_labels_theta_and_withholds_its_value(tmp_path):
    diagram = rt.find_angle({"opposite": q(48), "adjacent": q(55)}, ["41.1"])
    spec = diagram.generation_spec

    assert angle_at(spec["points"], "C", "A", "B") == pytest.approx(41.11, abs=0.05)
    assert "41.1" in spec["forbidden_visible_labels"]
    assert "θ" in visible_text(diagram.svg)
    assert not any("41" in text for text in visible_text(diagram.svg))
    assert {"target": "angle:C", "label": "θ"} in spec["unknowns"]
    assert "41" not in diagram.alt_text
    assert findings_for(tmp_path, diagram, ["41.1"]) == []


def test_converse_test_never_marks_a_right_angle(tmp_path):
    right = rt.converse_test({"sides": [q(45), q(60), q(75)]}, ["1"])
    not_right = rt.converse_test({"sides": [q(3), q(4), q(6)]}, ["0"])

    for diagram in (right, not_right):
        assert "data-right-angle-marker" not in diagram.svg
        assert diagram.generation_spec["right_angles"] == []
        assert "right" not in diagram.alt_text.casefold()
        assert findings_for(tmp_path, diagram, ["1"]) == []
    assert right.generation_spec["points"] == not_right.generation_spec["points"]


def test_converse_test_reports_a_wrong_answer_key_without_changing_it():
    diagram = rt.converse_test({"sides": [q(55), q(72), q(89)]}, ["1"])

    assert any("correct code is 0" in finding for finding in diagram.content_findings)


def test_unknown_side_carries_its_variable_not_the_answer(tmp_path):
    diagram = rt.find_hypotenuse({"legs": [q(5), q(12)]}, ["13"])

    assert set(visible_text(diagram.svg)) >= {"5 cm", "12 cm", "c"}
    assert "13" not in " ".join(visible_text(diagram.svg))
    assert diagram.generation_spec["forbidden_visible_labels"] == ["13"]
    assert findings_for(tmp_path, diagram, ["13"], "perpendicular sides 5 cm and 12 cm") == []


def test_answer_equal_to_a_given_value_is_exempted_not_hidden():
    diagram = rt.tangent_adjacent({"angle": 45, "opposite": q(6, "m")}, ["6"])
    spec = diagram.generation_spec

    assert "6 m" in visible_text(diagram.svg)
    assert spec["forbidden_label_exemptions"] == [
        {"value": "6", "reason": "equals a stated value shown on the diagram"}
    ]
    assert {"target": "segment:AC", "label": "x"} in spec["unknowns"]


def test_elevation_figure_shows_eye_level_and_full_tower(tmp_path):
    diagram = rt.elevation_observer(
        {"distance": q(23, "m"), "angle": 50, "eye_height": q(1.6, "m")}, ["29.0"]
    )
    spec = diagram.generation_spec

    assert "stroke-dasharray" in lines(diagram.svg, "EP")
    assert angle_at(spec["points"], "E", "P", "Q") == pytest.approx(50, abs=0.3)
    assert {"target": "segment:TQ", "label": "h"} in spec["unknowns"]
    assert {"27.4", "29.0", "29"} <= set(spec["forbidden_visible_labels"])
    assert findings_for(tmp_path, diagram, ["29.0"]) == []


def test_two_position_figure_draws_both_points_and_angles(tmp_path):
    diagram = rt.two_position({"gap": q(20, "m"), "far_angle": 35, "near_angle": 50}, ["34.0"])
    points = diagram.generation_spec["points"]

    assert angle_at(points, "F", "N", "Q") == pytest.approx(35, abs=0.3)
    assert angle_at(points, "N", "T", "Q") == pytest.approx(50, abs=0.3)
    assert findings_for(tmp_path, diagram, ["34.0"]) == []


# -------------------------------------------------------------------------- mensuration
def test_rectangular_pyramid_has_four_base_vertices_and_apex_over_the_centre(tmp_path):
    diagram = me.rectangular_pyramid_volume({"base": [q(9), q(5)], "height": q(12)}, ["180"])
    points = diagram.generation_spec["points"]
    base = [points[name] for name in ("P1", "P2", "P3", "P4")]
    centre = (sum(p[0] for p in base) / 4, sum(p[1] for p in base) / 4)

    assert len({tuple(point) for point in base}) == 4
    assert points["O"] == pytest.approx(centre, abs=0.01)
    assert points["V"][0] == pytest.approx(points["O"][0])
    for hidden in ("P1P4", "P4P3", "VP4", "VO"):
        assert "stroke-dasharray" in lines(diagram.svg, hidden)
    for visible in ("P1P2", "P2P3", "VP1", "VP2", "VP3"):
        assert "stroke-dasharray" not in lines(diagram.svg, visible)
    assert "h = 12 cm" in visible_text(diagram.svg)
    assert findings_for(tmp_path, diagram, ["180"]) == []


def test_slant_height_runs_to_the_midpoint_of_a_base_edge(tmp_path):
    diagram = me.pyramid_covering_cost(
        {"base_side": q(8, "m"), "slant_height": q(12, "m"), "rate": 5}, ["1280"]
    )
    points = diagram.generation_spec["points"]

    assert points["S"] == pytest.approx(
        ((points["P1"][0] + points["P2"][0]) / 2, (points["P1"][1] + points["P2"][1]) / 2)
    )
    assert {"text": "l = 12 m", "target": "segment:VS"} in diagram.generation_spec["labels"]
    assert "VO" not in diagram.generation_spec["points"]
    assert findings_for(tmp_path, diagram, ["1280"]) == []


def test_cone_labels_attach_to_radius_height_and_slant(tmp_path):
    total = me.cone_total_area({"radius": q(6), "height": q(8)}, ["301.6"])
    curved = me.cone_curved_area({"radius": q(12), "slant_height": q(20)}, ["754.0"])

    total_labels = {item["text"]: item["target"] for item in total.generation_spec["labels"]}
    assert total_labels == {"r = 6 cm": "segment:OR", "h = 8 cm": "segment:VO"}
    assert "10" in total.generation_spec["forbidden_visible_labels"]
    curved_labels = {item["text"]: item["target"] for item in curved.generation_spec["labels"]}
    assert curved_labels == {"r = 12 cm": "segment:OR", "l = 20 cm": "segment:VR"}
    assert not any(segment["key"] == "VO" for segment in curved.generation_spec["segments"])
    assert findings_for(tmp_path, total, ["301.6"]) == []
    assert findings_for(tmp_path, curved, ["754.0"]) == []


def test_given_diameter_is_drawn_as_a_full_diameter(tmp_path):
    diagram = me.sphere_volume_diameter({"diameter": q(20)}, ["4188.8"])
    spec = diagram.generation_spec
    centre, radius = spec["points"]["O"], spec["circles"]["sphere"]["radius"]

    for end in ("D1", "D2"):
        point = spec["points"][end]
        assert math.hypot(point[0] - centre[0], point[1] - centre[1]) == pytest.approx(
            radius, abs=0.5
        )
    assert "d = 20 cm" in visible_text(diagram.svg)
    assert "10" in spec["forbidden_visible_labels"]
    assert findings_for(tmp_path, diagram, ["4188.8"]) == []


def test_hollow_sphere_and_vertex_down_cone(tmp_path):
    shell = me.hollow_shell({"outer_radius": q(5), "inner_radius": q(3)}, ["410.5"])
    liquid = me.liquid_depth({"height": q(12), "volume_fraction": 0.125}, ["6"])

    assert 'data-circle="inner"' in shell.svg
    assert re.search(r'<circle data-circle="inner"[^>]*stroke-dasharray', shell.svg)
    points = liquid.generation_spec["points"]
    assert points["V"][1] > points["O"][1]
    assert "6" in liquid.generation_spec["forbidden_visible_labels"]
    assert {"target": "segment:WV", "label": "depth"} in liquid.generation_spec["unknowns"]
    assert any("vertex pointing down" in finding for finding in liquid.content_findings)
    assert findings_for(tmp_path, shell, ["410.5"]) == []
    assert findings_for(tmp_path, liquid, ["6"]) == []


def test_separate_solids_and_cone_in_cylinder(tmp_path):
    recast = me.recast_spheres_cones(
        {"sphere_count": 4, "sphere_radius": q(3), "cone_radius": q(2), "cone_height": q(9)},
        ["12"],
    )
    factor = me.cone_cylinder_factor({}, ["1"])

    assert [solid["type"] for solid in recast.generation_spec["solids"]] == ["sphere", "cone"]
    assert "sphere" in recast.alt_text and "cone" in recast.alt_text
    assert factor.generation_spec["points"]["T"] == factor.generation_spec["points"]["V"]
    assert "1/3" in factor.generation_spec["forbidden_visible_labels"]
    assert findings_for(tmp_path, recast, ["12"]) == []
    assert findings_for(tmp_path, factor, ["1"]) == []


def test_liquid_depth_reports_wrong_answer_keys():
    diagram = me.liquid_depth({"height": q(15), "volume_fraction": 0.125}, ["7"])

    assert any("(7.5)" in finding for finding in diagram.content_findings)


# ------------------------------------------------------------------ repeatable output
def test_all_sec2_g4_g5_questions_and_lessons_regenerate_and_validate(repository_root):
    templates_seen = set()
    for bank in (G4, G5):
        questions = load_questions(repository_root, bank)
        assert len(questions) == 104
        for question in questions:
            for asset in diagram_assets(question):
                first = render_question_asset(question, asset)
                second = render_question_asset(question, asset)
                assert first.svg == second.svg
                assert first.generation_spec == second.generation_spec
                templates_seen.add(first.generation_spec["template"])
                context = DiagramContext(tuple(answer_values(question)), question_text(question))
                root = ET.fromstring(first.svg)
                assert root.attrib["data-renderer"] in CHECKED_RENDERERS
                issues = _findings_from_memory(first, context)
                assert issues == [], (question["stable_key"], issues)
    # The converse items become text-only as their batches are corrected.
    assert len(templates_seen) >= 33
    course = repository_root / SEC2_COURSE
    rendered = 0
    for key in ("g4-lesson-01", "g4-lesson-02", "g4-lesson-03", "g5-lesson-06"):
        lesson = json.loads((course / "lessons" / f"{key}.json").read_text())
        for asset in lesson["assets"]:
            assert asset["asset_key"] in LESSON_TEMPLATES
            diagram = render_lesson_asset(lesson, asset)
            assert render_lesson_asset(lesson, asset).svg == diagram.svg
            assert _findings_from_memory(diagram, None) == []
            rendered += 1
    assert rendered == 6


def _findings_from_memory(diagram, context):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.svg"
        path.write_text(diagram.svg)
        return [
            (finding.code, finding.message)
            for finding in geometry_diagram_findings(
                path, diagram.generation_spec, diagram.alt_text, context, strict=True
            )
        ]


def test_only_the_known_answer_keys_disagree_with_their_prompts(repository_root):
    findings = {}
    for bank in (G4, G5):
        for question in load_questions(repository_root, bank):
            for asset in diagram_assets(question):
                diagram = render_question_asset(question, asset)
                answer_findings = [
                    finding for finding in diagram.content_findings if "answer key" in finding
                ]
                if answer_findings:
                    findings[question["stable_key"]] = answer_findings

    # These three are corrected in their batches, so the set shrinks to nothing as they land.
    assert set(findings) <= {"g4-l2-529", "g5-l4-507", "g5-l4-514"}


def test_stored_v2_inputs_take_precedence_over_prompt_wording(repository_root):
    question = load_questions(repository_root, G4)[0]
    [asset] = diagram_assets(question)
    diagram = render_question_asset(question, asset)
    regenerated = {**asset, "generation_spec": diagram.generation_spec}
    question["parts"][0]["prompt"][0]["text"] = "Reworded prompt with no recognisable template."

    request = request_for(question, regenerated)

    assert request.source == "generation_spec"
    assert request.template == "find_hypotenuse"
