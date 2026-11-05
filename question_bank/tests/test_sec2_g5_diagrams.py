"""The Sec 2 G5 bank, and the checks for the defects the G5 audit reported."""

import json
import shutil

import pytest

from question_bank.diagram_checks import DiagramContext
from question_bank.diagrams import mensuration as me
from question_bank.diagrams.regenerate import regenerate_batch
from question_bank.geometry_validation import geometry_diagram_findings
from question_bank.validation import validate_bank

G5 = "backend_resources/question_bank/g3_math/secondary_2/g5/v1"
BATCHES = ("B001", "B002", "B003", "B004")


def q(value, unit="cm"):
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


def copied(spec):
    return json.loads(json.dumps(spec))


def test_slant_height_must_be_labelled_on_the_slant_edge(tmp_path):
    """D3."""
    diagram = me.cone_curved_area({"radius": q(12), "slant_height": q(20)})
    assert codes(tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text) == set()
    spec = copied(diagram.generation_spec)
    for label in spec["labels"]:
        if label["text"].startswith("l ="):
            label["target"] = "panel"
    assert "geometry_slant_unmarked" in codes(tmp_path, diagram.svg, spec, diagram.alt_text)


def test_slant_only_figure_must_not_draw_the_vertical_height(tmp_path):
    """D3: the old figures drew only the height the learner must not use."""
    diagram = me.pyramid_covering_cost({"base_side": q(8, "m"), "slant_height": q(12, "m"), "rate": 5})
    spec = copied(diagram.generation_spec)
    spec["segments"].append({"key": "VO", "from": "V", "to": "O", "hidden": True})
    assert "geometry_slant_unmarked" in codes(tmp_path, diagram.svg, spec, diagram.alt_text)


CYLINDER = "A cone and a cylinder have the same circular base and perpendicular height."


def test_named_solid_must_be_drawn(tmp_path):
    """D4: the cone and cylinder items showed no cylinder."""
    diagram = me.cone_cylinder_factor()
    found = codes(tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text, CYLINDER)
    assert "geometry_wrong_solid" not in found
    spec = copied(diagram.generation_spec)
    spec["solids"] = [solid for solid in spec["solids"] if solid["type"] != "cylinder"]
    assert "geometry_wrong_solid" in codes(tmp_path, diagram.svg, spec, diagram.alt_text, CYLINDER)


def test_solid_the_question_does_not_name_is_rejected(tmp_path):
    """D4: the recast item showed a cone joined to a hemisphere."""
    diagram = me.cone_hemisphere_volume({"radius": q(3), "height": q(4)})
    stated = "Four solid spheres of radius 3 cm are recast into cones of height 4 cm."
    assert "geometry_wrong_solid" in codes(
        tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text, stated
    )


def test_hollow_solid_must_show_its_inner_sphere(tmp_path):
    """D4."""
    stated = "A hollow spherical shell has outer radius 5 cm and inner radius 3 cm."
    diagram = me.hollow_shell({"outer_radius": q(5), "inner_radius": q(3)})
    found = codes(tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text, stated)
    assert "geometry_wrong_solid" not in found
    plain = me.sphere_surface_area({"radius": q(5)})
    assert "geometry_wrong_solid" in codes(
        tmp_path, plain.svg, plain.generation_spec, plain.alt_text, stated
    )


def test_liquid_must_be_in_a_vertex_down_cone(tmp_path):
    """D4."""
    stated = "A cone of height 12 cm is filled to one eighth. The liquid forms a smaller cone."
    upright = me.cone_volume({"radius": q(4), "height": q(12)})
    assert "geometry_wrong_solid" in codes(
        tmp_path, upright.svg, upright.generation_spec, upright.alt_text, stated
    )
    liquid = me.liquid_depth({"height": q(12), "volume_fraction": 1 / 8})
    assert "geometry_wrong_solid" not in codes(
        tmp_path, liquid.svg, liquid.generation_spec, liquid.alt_text, stated
    )


@pytest.mark.parametrize(
    "dimensions",
    [
        {"radius": q(8), "height": q(6)},
        {"radius": q(4), "height": q(18)},
        {"radius": q(7), "cone_height": q(24)},
        {"radius": q(8), "slant_height": q(17)},
    ],
)
def test_cone_drawn_in_the_wrong_proportion_is_rejected(tmp_path, dimensions):
    """D8: a squat cone drawn tall."""
    diagram = me.cone_volume({"radius": q(8), "height": q(6)})
    spec = copied(diagram.generation_spec)
    spec["dimensions"] = dimensions
    found = codes(tmp_path, diagram.svg, spec, diagram.alt_text)
    if dimensions == {"radius": q(8), "height": q(6)}:
        assert "geometry_cone_proportion" not in found
    else:
        assert "geometry_cone_proportion" in found


def test_stated_value_missing_from_the_figure_is_rejected(tmp_path):
    """D7: values only in a side panel, or not at all."""
    diagram = me.cone_volume({"radius": q(4), "height": q(18)})
    stated = "A cone has radius 4 cm and perpendicular height 18 cm. Find it, correct to 1 decimal place."
    assert "geometry_given_mismatch" not in codes(
        tmp_path, diagram.svg, diagram.generation_spec, diagram.alt_text, stated
    )
    svg = diagram.svg.replace("h = 18 cm", "h")
    assert "geometry_given_mismatch" in codes(
        tmp_path, svg, diagram.generation_spec, diagram.alt_text, stated
    )
    extra = diagram.svg.replace("h = 18 cm", "h = 19 cm")
    assert "geometry_given_mismatch" in codes(
        tmp_path, extra, diagram.generation_spec, diagram.alt_text, stated
    )


def test_radius_must_end_on_the_surface(tmp_path):
    """D6: the old radius stopped about 8 units short."""
    diagram = me.sphere_surface_area({"radius": q(5)})
    spec = copied(diagram.generation_spec)
    x, y = spec["points"]["E"]
    spec["points"]["E"] = [x - 8, y + 5]
    assert "geometry_relationship" in codes(tmp_path, diagram.svg, spec, diagram.alt_text)


def test_pyramid_height_figure_shows_the_given_volume():
    diagram = me.pyramid_height({"volume": q(350, "cm³"), "base": [q(10), q(7)]}, ["15"])
    assert "volume 350 cm³" in diagram.svg


def test_tall_cone_on_a_hemisphere_keeps_its_proportion():
    """CFL-161: h/r of 24/7 is within the limits, so it is drawn as it is."""
    diagram = me.cone_hemisphere_volume({"radius": q(7), "height": q(24)})
    points = diagram.generation_spec["points"]
    height = abs(points["V"][1] - points["O"][1])
    radius = abs(points["R"][0] - points["O"][0])
    assert height / radius == pytest.approx(24 / 7, abs=0.02)


def test_audit_decisions_match_the_questions(repository_root):
    bank = repository_root / G5
    audit = json.loads((bank / "diagram_audit.json").read_text(encoding="utf-8"))
    assert audit["audited_question_count"] == 104
    assert len(audit["decisions"]) == 104
    for decision in audit["decisions"]:
        path = bank / "questions" / f"{decision['question_key']}.json"
        assets = json.loads(path.read_text(encoding="utf-8"))["assets"]
        assert decision["decision"] == "diagram_added"
        assert [asset["asset_key"] for asset in assets] == [decision["asset_key"]]


def test_applying_all_batches_clears_strict_geometry(repository_root, tmp_path):
    bank = tmp_path / "v1"
    shutil.copytree(repository_root / G5, bank)
    for batch in BATCHES:
        report = regenerate_batch(bank, batch, apply=True)
        assert report.ok, report.unsupported
        assert report.text_only == []
    result = validate_bank(bank, strict_geometry=True)
    assert [issue for issue in result.errors if issue.code.startswith("geometry_")] == []
