import json
import math
import re
import shutil

import pytest

from question_bank.diagram_checks import DiagramContext
from question_bank.diagrams import similarity as sim
from question_bank.diagrams.common import SIMILARITY_RENDERER, UnsupportedDiagram
from question_bank.diagrams.questions import render_question_asset, request_for, text_only_reason
from question_bank.diagrams.regenerate import regenerate_batch
from question_bank.geometry_validation import geometry_diagram_findings
from question_bank.validation import validate_bank

G2 = "backend_resources/question_bank/g3_math/secondary_2/g2/v1"
NEW_FIGURES = {
    "B001": ["g2-l2-507", "g2-l4-503"],
    "B002": ["g2-l4-505", "g2-l3-516"],
    "B003": ["g2-l3-520", "g2-l2-523", "g2-l4-509", "g2-l4-511", "g2-l4-512"],
    "B004": ["g2-l3-530"],
}


def cm(value):
    return {"value": value, "unit": "cm"}


def m(value):
    return {"value": value, "unit": "m"}


def linear(coefficient, constant):
    return {"coefficient": coefficient, "constant": constant}


CASES = {
    "scalene_tiles": ({"first": [cm(4), cm(6), cm(7)], "second": [cm(7), cm(4), cm(6)]}, ["1"]),
    "congruent_algebra": ({"ab": linear(3, 1), "pq": cm(16)}, ["5"]),
    "congruent_pentagons": (
        {
            "first": linear(3, 2),
            "second": linear(5, -10),
            "others": [cm(12), cm(15), cm(17), cm(18)],
        },
        ["82"],
    ),
    "sas_condition": ({}, ["1"]),
    "shared_side": ({}, ["1"]),
    "congruent_angle_expressions": (
        {"a": linear(2, 10), "p": linear(3, -15), "q": linear(2, 0)},
        ["70"],
    ),
    "similar_edges": ({"small": cm(3), "large": cm(6)}, ["2"]),
    "similar_perimeter": ({"perimeter": cm(24), "factor": 3}, ["72"]),
    "similar_angle": ({"given": 48}, ["48"]),
    "similar_angle_expressions": ({"first": linear(3, 5), "second": linear(5, -35)}, ["20"]),
    "similar_chain": (
        {
            "first_factor": [3, 2],
            "second_factor": [4, 3],
            "perimeter": cm(27),
            "area": {"value": 45, "unit": "cm²"},
        },
        ["180"],
    ),
    "nested_parallel": ({"ad": cm(6), "ab": cm(15), "de": cm(8)}, ["20"]),
    "nested_shared_vertex": (
        {"ab": linear(1, 2), "ad": linear(2, -1), "bc": cm(12), "de": cm(21)},
        ["18"],
    ),
    "shadow_pair": (
        {"height": m(2), "shadow": m(3), "other_shadow": m(12), "names": ["pole", "tree"]},
        ["8"],
    ),
    "mirror_method": ({"eye": m(1.6), "near": m(2), "far": m(10)}, ["8"]),
    "river_survey": ({"small_base": m(6), "large_base": m(15), "offset": m(4)}, ["10"]),
    "origin_point_ray": ({"point": [2, 3], "factor": 2}, ["4"]),
    "centre_unknown_line": ({"point": [2, 3], "image": [8, 9], "factor": 3}, ["-1"]),
    "centre_given_ray": ({"centre": [3, -2], "point": [-3, 7], "factor": [2, 3]}, ["3"]),
    "enlargement_line": ({"distance": cm(5), "factor": 3}, ["15"]),
    "scale_segments": ({"length": cm(2), "factor": 5, "names": ["design", "toy"]}, ["10"]),
    "scale_model": ({"length": m(24), "width": m(15), "scale": 300}, ["26"]),
    "scale_plan_stage": (
        {"length": cm(7.5), "width": cm(4.8), "scale": 400, "factor": [3, 5]},
        ["207.36"],
    ),
}


def render(template):
    inputs, answers = CASES[template]
    return sim.TEMPLATES[template](inputs, answers), answers


def findings(tmp_path, diagram, answers=(), *, svg=None, spec=None, alt=None, stated=""):
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


def copied(diagram):
    return json.loads(json.dumps(diagram.generation_spec))


def distance(spec, first, second):
    a, b = spec["points"][first], spec["points"][second]
    return math.hypot(a[0] - b[0], a[1] - b[1])


def test_every_template_has_a_case():
    assert set(CASES) == set(sim.TEMPLATES)


@pytest.mark.parametrize("template", sorted(CASES))
def test_template_passes_the_checks_and_is_deterministic(tmp_path, template):
    first, answers = render(template)
    second, _ = render(template)

    assert first.svg == second.svg
    assert first.alt_text == second.alt_text
    assert first.generation_spec == second.generation_spec
    assert first.generation_spec["renderer"] == SIMILARITY_RENDERER
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


# ------------------------------------------------------------------ what the figures must draw
def test_congruent_figures_measure_equal_and_are_not_just_shifted():
    spec = render("congruent_algebra")[0].generation_spec
    for first, second in (("AB", "PQ"), ("BC", "QR"), ("CA", "RP")):
        assert distance(spec, *first) == pytest.approx(distance(spec, *second), abs=0.5)
    assert spec["points"]["R"][1] > spec["points"]["P"][1]
    assert spec["points"]["C"][1] < spec["points"]["A"][1]

    spec = render("congruent_pentagons")[0].generation_spec
    assert len(spec["figures"]["first"]) == 5
    for index in range(5):
        following = (index + 1) % 5
        assert distance(spec, f"V{index + 1}", f"V{following + 1}") == pytest.approx(
            distance(spec, f"W{index + 1}", f"W{following + 1}"), abs=0.5
        )


def test_tile_labels_sit_on_sides_of_those_lengths():
    spec = render("scalene_tiles")[0].generation_spec
    labels = {item["target"]: item["text"] for item in spec["labels"]}
    assert labels == {
        "segment:S1S2": "7 cm",
        "segment:S3S1": "4 cm",
        "segment:S2S3": "6 cm",
        "segment:T1T2": "7 cm",
        "segment:T3T1": "4 cm",
        "segment:T2T3": "6 cm",
    }
    scale = distance(spec, "S1", "S2") / 7
    assert distance(spec, "S1", "S3") == pytest.approx(4 * scale, abs=0.5)
    assert distance(spec, "T2", "T3") == pytest.approx(6 * scale, abs=0.5)
    assert "<text" in render("scalene_tiles")[0].svg
    assert "congruent" not in render("scalene_tiles")[0].alt_text.casefold()
    assert "data-tick-mark" not in render("scalene_tiles")[0].svg


@pytest.mark.parametrize(
    ("template", "first", "second", "factor"),
    [
        ("similar_edges", ("S1", "S2"), ("T1", "T2"), 2),
        ("similar_perimeter", ("S1", "S3"), ("T1", "T3"), 3),
        ("nested_parallel", ("D", "E"), ("B", "C"), 2.5),
        ("nested_shared_vertex", ("B", "C"), ("D", "E"), 7 / 4),
        ("shadow_pair", ("S1", "F1"), ("S2", "F2"), 4),
        ("mirror_method", ("F", "E"), ("B", "T"), 5),
        ("river_survey", ("S2", "S3"), ("T2", "T3"), 2.5),
        ("similar_chain", ("A1", "A2"), ("C1", "C2"), 2),
    ],
)
def test_similar_figures_are_drawn_at_the_stated_factor(template, first, second, factor):
    spec = render(template)[0].generation_spec
    assert distance(spec, *second) / distance(spec, *first) == pytest.approx(factor, abs=0.02)


def test_the_answer_is_not_plotted_on_a_numbered_grid():
    spec = render("origin_point_ray")[0].generation_spec
    assert "A′" not in spec["points"]
    assert spec["grid"]["ticks"] == {"x": [2], "y": [3]}
    assert "4" in spec["forbidden_visible_labels"]
    spec = render("centre_given_ray")[0].generation_spec
    assert "A′" not in spec["points"]
    assert "−1" in spec["forbidden_visible_labels"]
    spec = render("centre_unknown_line")[0].generation_spec
    assert "C" not in spec["points"]


def test_the_shadow_item_with_a_small_stick_keeps_the_true_factor_without_crowded_marks():
    diagram = sim.shadow_pair(
        {"height": m(1.5), "shadow": m(2), "other_shadow": m(30), "names": ["stick", "building"]},
        ["22.5"],
    )
    spec = diagram.generation_spec
    assert distance(spec, "S2", "F2") / distance(spec, "S1", "F1") == pytest.approx(15, abs=0.2)
    assert [item["vertex"] for item in spec["right_angles"]] == ["F2"]
    assert "angles" not in spec


def test_sas_figure_marks_only_the_given_equalities():
    diagram, answers = render("sas_condition")
    spec = diagram.generation_spec
    assert "angles" not in spec
    assert distance(spec, "A", "B") == pytest.approx(distance(spec, "P", "Q"), abs=0.5)
    assert distance(spec, "A", "C") == pytest.approx(distance(spec, "P", "R"), abs=0.5)
    assert abs(distance(spec, "B", "C") - distance(spec, "Q", "R")) > 10


# ---------------------------------------------------------------- the reported defect types
def test_validator_rejects_congruent_figures_in_false_proportion(tmp_path):
    # D-C1: figures declared the same shape and size that are not.
    diagram, answers = render("congruent_algebra")
    spec = copied(diagram)
    spec["points"]["R"][1] += 30
    assert "geometry_figure_proportion" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_similar_figures_in_false_proportion(tmp_path):
    # D-S1, D-P1 and D-SC1: no single factor fits.
    diagram, answers = render("similar_edges")
    spec = copied(diagram)
    spec["points"]["T3"][0] += 40
    assert "geometry_figure_proportion" in codes(tmp_path, diagram, answers, spec=spec)
    # D-S2: similar at the wrong factor.
    spec = copied(diagram)
    for relation in spec["relationships"]:
        if relation["type"] == "similar":
            relation["value"] = 1.5
    assert "geometry_figure_proportion" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_lengths_out_of_proportion_with_their_values(tmp_path):
    diagram, answers = render("nested_parallel")
    spec = copied(diagram)
    for relation in spec["relationships"]:
        if relation["type"] == "to_scale":
            relation["lengths"][0][1] = 9
    assert "geometry_figure_proportion" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_an_enlargement_off_its_factor(tmp_path):
    # D-E3 and D-E5: a stated factor drawn as another.
    diagram, answers = render("enlargement_line")
    spec = copied(diagram)
    for relation in spec["relationships"]:
        if relation["type"] == "enlargement":
            relation["value"] = 2
    assert "geometry_figure_proportion" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_the_wrong_shape_for_the_question(tmp_path):
    # D-C6: a pentagon question drawn with triangles.
    diagram, answers = render("congruent_algebra")
    stated = "Two congruent pentagons. AB = (3x + 1) cm and PQ = 16 cm."
    assert "geometry_figure_shape" in codes(tmp_path, diagram, answers, stated=stated)


def test_validator_rejects_a_figure_with_an_undrawn_side(tmp_path):
    diagram, answers = render("congruent_algebra")
    spec = copied(diagram)
    spec["segments"] = [item for item in spec["segments"] if item["key"] != "AB"]
    svg = re.sub(r'<line data-segment="AB"[^>]*/>\n', "", diagram.svg)
    assert "geometry_figure_shape" in codes(tmp_path, diagram, answers, svg=svg, spec=spec)


def test_validator_rejects_ticks_on_sides_that_do_not_correspond(tmp_path):
    # D-C2: ticks that imply the wrong equalities.
    diagram, answers = render("congruent_algebra")
    spec = copied(diagram)
    for group in spec["equal_marks"]:
        if group["ticks"] == 1:
            group["segments"] = ["AB", "QR"]
        if group["ticks"] == 2:
            group["segments"] = ["BC", "PQ"]
    found = codes(tmp_path, diagram, answers, spec=spec)
    assert "geometry_correspondence" in found

    spec = copied(diagram)
    for group in spec["equal_marks"]:
        if group["ticks"] == 1:
            group["segments"] = ["AB", "BC"]
    assert "geometry_correspondence" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_a_tick_off_its_side(tmp_path):
    # D-C3: a tick that floats off its side.
    diagram, answers = render("congruent_algebra")
    svg = re.sub(
        r'(data-tick-mark="QR" data-ticks="2" d=")M(\S+) (\S+) L(\S+) (\S+) M(\S+) (\S+) L(\S+) (\S+)',
        lambda m_: (
            f"{m_[1]}M{float(m_[2]) + 30} {m_[3]} L{float(m_[4]) + 30} {m_[5]} "
            f"M{float(m_[6]) + 30} {m_[7]} L{float(m_[8]) + 30} {m_[9]}"
        ),
        diagram.svg,
    )
    assert svg != diagram.svg
    assert "geometry_marking" in codes(tmp_path, diagram, answers, svg=svg)


def test_validator_rejects_matching_arcs_at_vertices_that_do_not_correspond(tmp_path):
    diagram, answers = render("similar_angle")
    spec = copied(diagram)
    for item in spec["angles"]:
        if item["marker_key"] == "angle-x":
            item["vertex"], item["arms"] = "T2", ["T1", "T3"]
    assert "geometry_correspondence" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_numbers_that_disagree_with_the_question(tmp_path):
    # D-ALL-1: a figure that shows none of the givens, and a figure that shows a value of its own.
    diagram, answers = render("similar_perimeter")
    assert "geometry_given_mismatch" in codes(
        tmp_path, diagram, answers, stated="A triangle with perimeter 24 cm is enlarged by 4."
    )
    assert "geometry_given_mismatch" in codes(
        tmp_path,
        diagram,
        answers,
        stated="A triangle with perimeter 24 cm is enlarged by scale factor 3 from 96 cm.",
    )
    assert not codes(
        tmp_path,
        diagram,
        answers,
        stated="A triangle with perimeter 24 cm is enlarged by scale factor 3.",
    )


def test_validator_rejects_an_arrow_that_runs_the_wrong_way(tmp_path):
    # D-SC3: an arrow from the plan to the real object, in a question that goes the other way.
    diagram, answers = render("scale_model")
    spec = copied(diagram)
    spec["arrows"][0]["from"], spec["arrows"][0]["to"] = "model", "garden"
    assert "geometry_arrow" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_an_arrow_factor_the_figures_do_not_show(tmp_path):
    diagram, answers = render("similar_perimeter")
    spec = copied(diagram)
    spec["arrows"][0]["factor"] = 2
    assert "geometry_arrow" in codes(tmp_path, diagram, answers, spec=spec)


def test_validator_rejects_points_and_numbers_off_the_grid(tmp_path):
    # D-E2: vertices that sit between grid lines.
    diagram, answers = render("origin_point_ray")
    spec = copied(diagram)
    spec["grid"]["points"]["A"] = [2.5, 3]
    assert "geometry_grid" in codes(tmp_path, diagram, answers, spec=spec)

    spec = copied(diagram)
    spec["grid"]["ticks"]["x"] = [3]
    assert "geometry_grid" in codes(tmp_path, diagram, answers, spec=spec)

    svg = re.sub(r'<rect data-grid="x:2"[^>]*/>\n', "", diagram.svg)
    assert "geometry_grid" in codes(tmp_path, diagram, answers, svg=svg)


def test_validator_rejects_a_caption_that_gives_the_answer_away(tmp_path):
    # D-C4: "same shape and size" on a question that asks whether the tiles are congruent.
    diagram, answers = render("scalene_tiles")
    assert "geometry_answer_leak" in codes(
        tmp_path, diagram, answers, svg=diagram.svg.replace(">7 cm<", ">same shape<", 1)
    )
    assert "geometry_answer_leak" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text + " They are congruent."
    )


def test_validator_rejects_alt_text_that_lists_measures_not_drawn(tmp_path):
    # D-ALL-2: "Stated measures include ..."
    diagram, answers = render("similar_edges")
    assert "geometry_alt_text_values" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text + " Stated measures include 9 cm."
    )
    assert "geometry_alt_text_figure" in codes(
        tmp_path, diagram, answers, alt=diagram.alt_text.replace("triangles", "shapes")
    )


# ----------------------------------------------------------------- reading the question data
def g2_question(prompt, answer="1", renderer="nextscholar-geometry-svg-v1"):
    return {
        "stable_key": "g2-test",
        "school_level": "secondary_2",
        "topic_code": "G2",
        "primary_outcome": "2.1",
        "stem": [],
        "assets": [{"asset_key": "a", "generation_spec": {"renderer": renderer}}],
        "parts": [
            {
                "prompt": [{"type": "text", "text": prompt}],
                "response": {"canonical_answer": answer},
            }
        ],
    }


def test_an_unrecognised_g2_prompt_is_reported_not_drawn():
    question = g2_question("Find the angle at the centre of the logo.")
    with pytest.raises(UnsupportedDiagram, match="similarity"):
        render_question_asset(question, question["assets"][0])


def test_other_topics_do_not_use_this_renderer():
    question = g2_question("Triangles ABC and ADC share side AC. Also AB = AD and BC = DC.")
    question["topic_code"] = "G5"
    with pytest.raises(UnsupportedDiagram, match="plane-geometry"):
        render_question_asset(question, question["assets"][0])


def test_new_assets_use_this_renderer_in_g2():
    question = g2_question(
        "Triangles ABC and ADC share side AC. Also AB = AD and BC = DC.",
        renderer="nextscholar-plane-geometry-svg-v1",
    )
    assert request_for(question, question["assets"][0]).renderer == SIMILARITY_RENDERER


def test_impossible_givens_are_refused():
    with pytest.raises(UnsupportedDiagram):
        sim.scalene_tiles({"first": [cm(1), cm(2), cm(9)], "second": [cm(1), cm(2), cm(9)]})
    with pytest.raises(UnsupportedDiagram):
        sim.scalene_tiles({"first": [cm(4), cm(6), cm(7)], "second": [cm(4), cm(6), cm(8)]})
    with pytest.raises(UnsupportedDiagram):
        sim.nested_parallel({"ad": cm(20), "ab": cm(15), "de": cm(8)})
    with pytest.raises(UnsupportedDiagram):
        sim.congruent_pentagons(
            {
                "first": linear(1, 2),
                "second": linear(1, 3),
                "others": [cm(12), cm(15), cm(17), cm(18)],
            }
        )


def test_wrong_answer_key_is_reported_for_the_question_text():
    diagram = sim.nested_parallel({"ad": cm(6), "ab": cm(15), "de": cm(8)}, ["21"])
    assert "does not match" in diagram.content_findings[0]


def test_stored_template_takes_precedence_over_the_prompt():
    question = g2_question("A reworded prompt the patterns do not know.")
    stored = {
        "generation_spec": {
            "renderer": SIMILARITY_RENDERER,
            "template": "similar_angle",
            "inputs": {"given": 48},
        }
    }
    assert request_for(question, stored).template == "similar_angle"


def test_successive_factors_stay_text_only():
    question = g2_question(
        "A triangle of area 32 cm² is enlarged by scale factor 3/2 and then reduced by scale "
        "factor 2/3. The resulting triangle is enlarged again by scale factor 5/2."
    )
    assert "cancelling" in text_only_reason(question)
    # The bank item sets the factors as inline maths, so its text blocks hold no fractions.
    inline = g2_question(
        "A triangle of area 32 cm² is enlarged by scale factor  and then reduced by scale "
        "factor  . The resulting triangle is enlarged again by scale factor  ."
    )
    assert "cancelling" in text_only_reason(inline)


def _bank_question(repository_root, key):
    path = repository_root / G2 / "questions" / f"{key}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_listed_g2_question_is_drawn_or_refused(repository_root):
    drawn = 0
    keys = {key for items in NEW_FIGURES.values() for key in items}
    for path in sorted((repository_root / G2 / "questions").glob("*.json")):
        question = json.loads(path.read_text(encoding="utf-8"))
        assets = question.get("assets") or []
        if question["stable_key"] in keys and not assets:
            assets = [{"asset_key": "new", "generation_spec": {"renderer": SIMILARITY_RENDERER}}]
        for asset in assets:
            if text_only_reason(question):
                continue
            diagram = render_question_asset(question, asset)
            assert diagram.content_findings == [], question["stable_key"]
            drawn += 1
    assert drawn == 24


def copy_bank(repository_root, tmp_path):
    target = tmp_path / "v1"
    shutil.copytree(repository_root / G2, target, ignore=shutil.ignore_patterns("review_packets"))
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
    before = json.loads((bank / "questions" / "g2-l5-505.json").read_text())
    report = regenerate_batch(bank, "B004", apply=True, add=NEW_FIGURES["B004"])
    assert report.ok

    question = json.loads((bank / "questions" / "g2-l5-505.json").read_text())
    if before["assets"][0]["generation_spec"]["renderer"] != SIMILARITY_RENDERER:
        assert question["revision"] == before["revision"] + 1
        assert (bank / before["assets"][0]["path"]).is_file()
    assert question["assets"][0]["path"].endswith(f"-r{question['revision']}.svg")
    assert question["status"] == "draft"
    assert question["provenance"]["reviewed_by"] is None

    added = json.loads((bank / "questions" / "g2-l3-530.json").read_text())
    assert added["stem"][1] == {"type": "asset_ref", "asset_key": "g2-l3-530-diagram"}
    audit = json.loads((bank / "diagram_audit.json").read_text())
    decision = next(item for item in audit["decisions"] if item["question_key"] == "g2-l3-530")
    assert decision["decision"] == "diagram_added"

    refused = json.loads((bank / "questions" / "g2-l5-504.json").read_text())
    assert refused["assets"] == []
    assert refused["stem"] == []
    decision = next(item for item in audit["decisions"] if item["question_key"] == "g2-l5-504")
    assert decision["decision"] == "text_sufficient"
    assert "cancelling" in decision["reason"]
    assert (bank / "assets" / "g2-l5-504-diagram.svg").is_file()

    again = regenerate_batch(bank, "B004", apply=True, add=NEW_FIGURES["B004"])
    assert all(asset.unchanged for asset in again.assets)


def test_shared_side_can_label_its_sides_in_x_and_withhold_the_perimeter(tmp_path):
    inputs = {"ab": linear(3, -2), "ad": linear(1, 8), "dc": linear(2, -1)}
    diagram = sim.shared_side(inputs, ["44"])
    spec = diagram.generation_spec
    stated = (
        "Triangle ABC is congruent to triangle ADC, with A, B and C corresponding to A, D and C. "
        "AB = (3x − 2) cm, AD = (x + 8) cm and DC = (2x − 1) cm."
    )

    assert diagram.content_findings == []
    assert findings(tmp_path, diagram, ["44"], stated=stated) == []
    # x = 5, AB = AD = 13 and BC = DC = 9; none is printed.
    assert {"44", "5", "13", "9"} <= set(spec["forbidden_visible_labels"])
    assert "answer_kind" not in spec
    assert sim.shared_side(inputs, ["40"]).content_findings


def test_congruent_angle_expressions_marks_correspondence_and_withholds_angle_c(tmp_path):
    diagram, answers = render("congruent_angle_expressions")
    spec = diagram.generation_spec
    stated = (
        "Triangles ABC and PQR are congruent, with A, B and C corresponding to P, Q and R. "
        "Angle A = (2x + 10)°, angle P = (3x − 15)° and angle Q = 2x°."
    )

    assert findings(tmp_path, diagram, answers, stated=stated) == []
    # x = 25 gives angles 60°, 50° and 70°; none is printed.
    assert {"70", "25", "60", "50"} <= set(spec["forbidden_visible_labels"])
    drawn = {item["marker_key"]: item["drawn_degrees"] for item in spec["angles"]}
    assert drawn["angle-A"] == pytest.approx(60, abs=0.5)
    assert drawn["angle-P"] == pytest.approx(60, abs=0.5)
    assert drawn["angle-Q"] == pytest.approx(50, abs=0.5)
    inputs = CASES["congruent_angle_expressions"][0]
    assert sim.congruent_angle_expressions(inputs, ["60"]).content_findings
    with pytest.raises(UnsupportedDiagram):
        sim.congruent_angle_expressions(
            {"a": linear(2, 10), "p": linear(3, -15), "q": linear(5, 0)}
        )
