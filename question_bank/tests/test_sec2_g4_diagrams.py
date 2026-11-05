"""The Sec 2 G4 bank: what gets a figure, and the checks for the defects the G4 audit reported."""

import json
import math
import shutil

import pytest

from question_bank.diagram_checks import DiagramContext
from question_bank.diagrams import right_triangle as rt
from question_bank.diagrams.questions import text_only_reason
from question_bank.diagrams.regenerate import regenerate_batch
from question_bank.geometry_validation import geometry_diagram_findings
from question_bank.validation import validate_bank

G4 = "backend_resources/question_bank/g3_math/secondary_2/g4/v1"
BATCHES = ("B001", "B002", "B003", "B004")
FIGURE_STEM = "Use the labelled right-triangle schematic. The diagram is not drawn to scale."


def q(value, unit="m"):
    return {"value": value, "unit": unit}


def codes(tmp_path, svg, spec, alt, stated=""):
    path = tmp_path / "diagram.svg"
    path.write_text(svg)
    context = DiagramContext((), stated) if stated else None
    return {
        finding.code
        for finding in geometry_diagram_findings(path, spec, alt, context, strict=True)
        if finding.severity == "error"
    }


def copy_bank(repository_root, tmp_path):
    target = tmp_path / "v1"
    shutil.copytree(repository_root / G4, target)
    return target


def load(bank, key):
    return json.loads((bank / "questions" / f"{key}.json").read_text(encoding="utf-8"))


# ----------------------------------------------------------------------- planted defects
def test_impossible_labelled_right_triangle_is_rejected(tmp_path):
    """D6: legs 55 and 72 with a hypotenuse of 89, which is really about 90.6."""
    diagram = rt.missing_leg({"hypotenuse": q(89), "leg": q(55)})
    spec = json.loads(json.dumps(diagram.generation_spec))
    for label in spec["labels"]:
        if label["text"] == "b":
            label["text"] = "72 m"
    spec["unknowns"] = []
    svg = diagram.svg.replace(">b</text>", ">72 m</text>")
    alt = diagram.alt_text + " 72 m"
    assert "geometry_impossible_triangle" in codes(tmp_path, svg, spec, alt)


def test_labelled_hypotenuse_no_longer_than_a_side_is_rejected(tmp_path):
    diagram = rt.find_hypotenuse({"legs": [q(55), q(72)]})
    spec = json.loads(json.dumps(diagram.generation_spec))
    for label in spec["labels"]:
        if label["text"] == "c":
            label["text"] = "60 m"
    spec["unknowns"] = []
    svg = diagram.svg.replace(">c</text>", ">60 m</text>")
    alt = diagram.alt_text + " 60 m"
    assert "geometry_impossible_triangle" in codes(tmp_path, svg, spec, alt)


def test_true_right_triangle_labels_pass(tmp_path):
    diagram = rt.missing_leg({"hypotenuse": q(20), "leg": q(12)})
    found = codes(tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text)
    assert "geometry_impossible_triangle" not in found


TWO_POSITION_PROMPT = (
    "Two observation points on level ground are 20 m apart in line with a vertical mast. The "
    "angles of elevation to its top are 35° at the farther point and 50° at the nearer point. "
    "Find the mast height correct to 1 decimal place."
)


def test_figure_missing_a_stated_value_is_rejected(tmp_path):
    """D7: the two-position figure drew only the far angle."""
    diagram = rt.two_position({"gap": q(20), "far_angle": 35, "near_angle": 50})
    stated = TWO_POSITION_PROMPT
    assert "geometry_given_mismatch" not in codes(
        tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text, stated
    )
    svg = diagram.svg.replace(">50°</text>", ">β</text>")
    assert "geometry_given_mismatch" in codes(
        tmp_path, svg, diagram.generation_spec, diagram.alt_text, stated
    )


def test_figure_with_a_number_the_question_never_states_is_rejected(tmp_path):
    """D1b: printing the intermediate hypotenuse is a number the question does not state."""
    diagram = rt.find_hypotenuse({"legs": [q(5), q(12)]})
    svg = diagram.svg.replace(">c</text>", ">13 m</text>")
    assert "geometry_given_mismatch" in codes(
        tmp_path, svg, diagram.generation_spec, diagram.alt_text, "perpendicular sides 5 m and 12 m"
    )


def test_theta_with_a_degree_sign_is_rejected(tmp_path):
    """D10."""
    diagram = rt.find_angle({"opposite": q(48), "adjacent": q(55)})
    svg = diagram.svg.replace(">θ</text>", ">θ°</text>")
    assert "geometry_label_notation" in codes(
        tmp_path, svg, diagram.generation_spec, diagram.alt_text
    )


def test_title_naming_the_method_is_rejected(tmp_path):
    """D12."""
    diagram = rt.tangent_adjacent({"angle": 45, "opposite": q(6)})
    svg = diagram.svg.replace(">Right-angled triangle</title>", ">Use tangent at 45 degrees</title>")
    assert svg != diagram.svg
    assert "geometry_method_named" in codes(
        tmp_path, svg, diagram.generation_spec, diagram.alt_text
    )


def test_teaching_figures_may_name_the_ratios(tmp_path):
    diagram = rt.lesson_trigonometry()
    found = codes(tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text)
    assert "geometry_method_named" not in found


# ------------------------------------------------------------------------------ figures
def test_perimeter_figure_is_the_true_triangle_with_no_mark(tmp_path):
    inputs = {"perimeter": q(108), "sides": [q(27), q(36)]}
    diagram = rt.perimeter_verify(inputs, ["45"])
    points = diagram.generation_spec["points"]
    length = lambda a, b: math.dist(points[a], points[b])  # noqa: E731
    assert length("A", "B") / length("A", "C") == pytest.approx(27 / 45, abs=0.005)
    assert length("B", "C") / length("A", "C") == pytest.approx(36 / 45, abs=0.005)
    assert diagram.generation_spec["right_angles"] == []
    assert "perimeter 108 m" in diagram.svg
    assert codes(tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text) == set()

    marked = diagram.svg.replace(
        "</g>\n<g data-layer=\"labels\"",
        '<path data-right-angle-marker="B" d="M10 10 L20 20" fill="none"/></g>\n'
        '<g data-layer="labels"',
    )
    assert "geometry_right_angle_marker_forbidden" in codes(
        tmp_path, marked, diagram.generation_spec, diagram.alt_text
    )


def test_perimeter_that_forms_no_triangle_is_unsupported():
    with pytest.raises(ValueError):
        rt.perimeter_verify({"perimeter": q(100), "sides": [q(10), q(20)]})


def test_converse_items_are_text_only_and_nothing_else_in_g4_is(repository_root):
    refused = []
    for path in sorted((repository_root / G4 / "questions").glob("*.json")):
        question = json.loads(path.read_text(encoding="utf-8"))
        if text_only_reason(question):
            refused.append(question)
    assert len(refused) == 28
    for question in refused:
        assert question["primary_outcome"] == "4.2"
        assert "Enter 1 if it is right-angled" in question["parts"][0]["prompt"][0]["text"]


def test_audit_decisions_match_the_questions(repository_root):
    bank = repository_root / G4
    audit = json.loads((bank / "diagram_audit.json").read_text(encoding="utf-8"))
    assert audit["audited_question_count"] == 104
    assert len(audit["decisions"]) == 104
    for decision in audit["decisions"]:
        assets = load(bank, decision["question_key"])["assets"]
        if decision["decision"] == "diagram_added":
            assert [asset["asset_key"] for asset in assets] == [decision["asset_key"]]
        else:
            assert decision["decision"] == "text_sufficient" and assets == []


# ----------------------------------------------------------------------------- the bank
def test_applying_all_batches_clears_strict_geometry(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    for batch in BATCHES:
        report = regenerate_batch(bank, batch, apply=True)
        assert report.ok, report.unsupported
    result = validate_bank(bank, strict_geometry=True)
    assert [issue for issue in result.errors if issue.code.startswith("geometry_")] == []


def test_applying_a_batch_makes_converse_items_text_only(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    before = load(bank, "g4-l1-503")
    regenerate_batch(bank, "B001", apply=True)

    question = load(bank, "g4-l1-503")
    assert question["assets"] == []
    assert question["stem"] == []
    assert question["status"] == "draft"
    assert question["provenance"]["reviewed_by"] is None
    if before["assets"]:
        assert question["revision"] == before["revision"] + 1
    assert (bank / "assets/g4-l1-503-diagram.svg").is_file()

    audit = json.loads((bank / "diagram_audit.json").read_text(encoding="utf-8"))
    decisions = {item["question_key"]: item for item in audit["decisions"]}
    assert decisions["g4-l1-503"]["decision"] == "text_sufficient"
    assert "D6" in decisions["g4-l1-503"]["reason"]
    assert decisions["g4-l1-501"]["decision"] == "diagram_added"
    assert audit["diagram_question_count"] == json.loads(
        (repository_root / G4 / "diagram_audit.json").read_text(encoding="utf-8")
    )["diagram_question_count"]

    again = regenerate_batch(bank, "B001", apply=True)
    assert all(asset.unchanged for asset in again.assets)


def test_figure_stem_stays_where_a_figure_stays(repository_root, tmp_path):
    bank = copy_bank(repository_root, tmp_path)
    regenerate_batch(bank, "B001", apply=True)
    question = load(bank, "g4-l1-501")
    assert question["stem"][0] == {"type": "text", "text": FIGURE_STEM}
    assert question["stem"][1]["type"] == "asset_ref"
