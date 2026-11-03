import hashlib
import json
import shutil

import pytest

from question_bank.diagram_checks import DiagramContext, forbidden_label_pattern
from question_bank.diagrams import mensuration as me
from question_bank.diagrams import right_triangle as rt
from question_bank.diagrams.regenerate import (
    find_batch_manifest,
    regenerate_batch,
    regenerate_lessons,
    revisioned_path,
)
from question_bank.geometry_validation import geometry_diagram_findings
from question_bank.validation import validate_bank


def q(value, unit="cm"):
    return {"value": value, "unit": unit}


def codes(tmp_path, svg, spec, alt="", context=None, *, strict=False, severity="error"):
    path = tmp_path / "diagram.svg"
    path.write_text(svg)
    return {
        finding.code
        for finding in geometry_diagram_findings(path, spec, alt, context, strict=strict)
        if finding.severity == severity
    }


# ------------------------------------------------------------------------ answer leaks
@pytest.mark.parametrize(
    ("label", "text", "leaks"),
    [
        ("4", "45 cm", False),
        ("4", "4.5 cm", False),
        ("4", "x4", False),
        ("4", "r = 4 cm", True),
        ("13", "5, 12, 13", True),
        ("3 m", "r = 300 cm", False),
        ("3 m", "radius 3 m", True),
        ("3 m", "3 m³", False),
        ("45°", "angle 45°", True),
        ("45 degrees", "an angle of 45  degrees", True),
        ("29.0", "29.01", False),
        ("1/3", "11/3", False),
        ("right-angled", "Not right-angled", True),
        ("72π", "k = 72π", True),
    ],
)
def test_withheld_labels_match_whole_tokens(label, text, leaks):
    assert bool(forbidden_label_pattern(label).search(text)) is leaks


def test_answer_in_visible_text_title_or_alt_text_is_an_error(tmp_path):
    diagram = rt.find_hypotenuse({"legs": [q(5), q(12)]}, ["13"])
    leaked = diagram.svg.replace(">c</text>", ">13</text>")

    assert "geometry_answer_leak" in codes(
        tmp_path, leaked, diagram.generation_spec, diagram.alt_text
    )
    assert "geometry_answer_leak" in codes(
        tmp_path,
        diagram.svg,
        diagram.generation_spec,
        diagram.alt_text + " The hypotenuse is 13 cm.",
    )
    titled = diagram.svg.replace(
        '<title id="title">Right-angled triangle</title>',
        '<title id="title">Hypotenuse 13 cm</title>',
    )
    assert "geometry_answer_leak" in codes(
        tmp_path, titled, diagram.generation_spec, diagram.alt_text
    )


def test_unknown_must_be_labelled_with_a_variable(tmp_path):
    diagram = rt.find_hypotenuse({"legs": [q(5), q(12)]}, ["13"])
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["forbidden_visible_labels"] = []
    spec["unknowns"] = [{"target": "segment:BC", "label": "13 cm"}]
    spec["labels"][-1]["text"] = "13 cm"
    svg = diagram.svg.replace(">c</text>", ">13 cm</text>")

    found = codes(tmp_path, svg, spec, diagram.alt_text, DiagramContext(("13",)))
    assert {"geometry_unknown_shows_value", "geometry_answer_not_withheld"} <= found


# ---------------------------------------------------------------- declared geometry
def test_right_angle_marker_is_rejected_on_a_converse_test(tmp_path):
    diagram = rt.converse_test({"sides": [q(45), q(60), q(75)]}, ["1"])
    marked = diagram.svg.replace(
        '</g>\n<g data-layer="labels"',
        '<path data-right-angle-marker="A" d="M0 0 L1 1 L2 2" stroke="#000"/></g>\n<g data-layer="labels"',
        1,
    )

    assert "geometry_right_angle_marker_forbidden" in codes(
        tmp_path, marked, diagram.generation_spec, diagram.alt_text
    )


def test_arc_at_the_right_angle_and_wrong_size_are_rejected(tmp_path):
    diagram = rt.tangent_opposite({"angle": 60, "adjacent": q(14, "m")}, ["24.2"])
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["angles"][0]["degrees"] = 30
    assert "geometry_angle_measure" in codes(tmp_path, diagram.svg, spec, diagram.alt_text)

    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["angles"][0]["vertex"] = "A"
    spec["angles"][0]["arms"] = ["B", "C"]
    assert "geometry_angle_marker_vertex" in codes(tmp_path, diagram.svg, spec, diagram.alt_text)


def test_moved_pyramid_apex_breaks_declared_relationships(tmp_path):
    diagram = me.rectangular_pyramid_volume({"base": [q(9), q(5)], "height": q(12)}, ["180"])
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["points"]["O"][0] -= 70

    found = codes(tmp_path, diagram.svg, spec, diagram.alt_text)
    assert {"geometry_relationship", "geometry_segment_mismatch"} <= found


def test_triangular_pyramid_base_is_rejected(tmp_path):
    diagram = me.rectangular_pyramid_volume({"base": [q(9), q(5)], "height": q(12)}, ["180"])
    spec = json.loads(json.dumps(diagram.generation_spec))
    for relation in spec["relationships"]:
        if relation["type"] == "polygon_sides":
            relation["points"] = relation["points"][:3]
            relation["count"] = 3

    assert "geometry_solid_relationship_missing" in codes(
        tmp_path, diagram.svg, spec, diagram.alt_text
    )


def test_hidden_edges_must_be_dashed(tmp_path):
    diagram = me.rectangular_pyramid_volume({"base": [q(9), q(5)], "height": q(12)}, ["180"])
    line = next(part for part in diagram.svg.split("<line") if 'data-segment="P4P3"' in part)
    solid = diagram.svg.replace(line, line.replace(' stroke-dasharray="10 8"', ""))

    assert "geometry_hidden_edge" in codes(
        tmp_path, solid, diagram.generation_spec, diagram.alt_text
    )


def test_diameter_must_end_on_the_sphere(tmp_path):
    diagram = me.sphere_volume_diameter({"diameter": q(20)}, ["4188.8"])
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["circles"]["sphere"]["radius"] -= 12

    assert "geometry_relationship" in codes(tmp_path, diagram.svg, spec, diagram.alt_text)


def test_labels_must_stay_inside_apart_clear_and_readable(tmp_path):
    diagram = rt.find_hypotenuse({"legs": [q(5), q(12)]}, ["13"])
    label = next(item for item in diagram.svg.split("<text") if ">5 cm</text>" in item)
    clipped = diagram.svg.replace(
        label, label.replace(label.split('x="')[1].split('"')[0], "-40", 1)
    )
    assert "geometry_label_bounds" in codes(
        tmp_path, clipped, diagram.generation_spec, diagram.alt_text
    )

    tiny = diagram.svg.replace('font-size="22"', 'font-size="14"')
    assert "geometry_text_too_small" in codes(
        tmp_path, tiny, diagram.generation_spec, diagram.alt_text
    )

    b, c = diagram.generation_spec["points"]["B"], diagram.generation_spec["points"]["C"]
    middle = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)
    on_stroke = diagram.svg.replace(
        ">c</text>",
        f'>c</text><text x="{middle[0]}" y="{middle[1] + 8}" font-size="26" '
        'text-anchor="middle">X</text>',
    )
    assert "geometry_label_collision" in codes(
        tmp_path, on_stroke, diagram.generation_spec, diagram.alt_text
    )


def test_alt_text_must_name_the_solid_and_its_given_values(tmp_path):
    diagram = me.cone_volume({"radius": q(8), "height": q(12)}, ["804.2"])

    found = codes(tmp_path, diagram.svg, diagram.generation_spec, "A solid with radius 8 cm.")
    assert {"geometry_alt_text_solid", "geometry_alt_text_values"} <= found


# --------------------------------------------------------------------- legacy assets
LEGACY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 420">'
    '<text x="350" y="356" font-size="21">13</text>'
    '<text x="38" y="78" font-size="15">Not drawn to scale</text></svg>'
)


def test_legacy_assets_raise_warnings_until_strict(tmp_path):
    spec = {"renderer": "nextscholar-right-triangle-svg-v1", "diagram_kind": "right_triangle"}
    context = DiagramContext(("13",), "perpendicular sides 5 cm and 12 cm")

    warnings = codes(tmp_path, LEGACY_SVG, spec, "", context, severity="warning")
    assert warnings == {
        "geometry_legacy_unchecked",
        "geometry_answer_leak",
        "geometry_text_too_small",
    }
    assert codes(tmp_path, LEGACY_SVG, spec, "", context) == set()
    assert codes(tmp_path, LEGACY_SVG, spec, "", context, strict=True) == warnings


def test_retired_renderers_fail(tmp_path, monkeypatch):
    from question_bank import geometry_validation

    monkeypatch.setattr(
        geometry_validation,
        "RETIRED_GEOMETRY_RENDERERS",
        frozenset({"nextscholar-right-triangle-svg-v1"}),
    )
    spec = {"renderer": "nextscholar-right-triangle-svg-v1"}

    assert "geometry_retired_renderer" in codes(tmp_path, LEGACY_SVG, spec)


def test_legacy_leak_ignores_values_stated_in_the_question(tmp_path):
    spec = {"renderer": "nextscholar-right-triangle-svg-v1"}
    context = DiagramContext(("13",), "The hypotenuse is 13 cm.")

    assert "geometry_answer_leak" not in codes(
        tmp_path, LEGACY_SVG, spec, "", context, severity="warning"
    )


# --------------------------------------------------------------------- regeneration
@pytest.fixture
def g4_bank_copy(tmp_path, repository_root):
    resources = repository_root / "backend_resources"
    root = tmp_path / "resources"
    shutil.copytree(resources / "question_bank/schema", root / "question_bank/schema")
    shutil.copytree(
        resources / "question_bank/g3_math/secondary_2/g4",
        root / "question_bank/g3_math/secondary_2/g4",
    )
    shutil.copytree(resources / "syllabi", root / "syllabi")
    return root / "question_bank/g3_math/secondary_2/g4/v1"


def _digest(directory):
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(directory).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_revisioned_paths_and_batch_lookup(g4_bank_copy):
    assert revisioned_path("assets/g4-l1-501-diagram.svg", 2) == "assets/g4-l1-501-diagram-r2.svg"
    assert revisioned_path("assets/angle-r2.svg", 3) == "assets/angle-r3.svg"
    assert find_batch_manifest(g4_bank_copy, "B003").name == "g3-sec2-g4-b003.json"
    with pytest.raises(FileNotFoundError):
        find_batch_manifest(g4_bank_copy, "B009")


def test_preview_does_not_touch_the_bank(g4_bank_copy, tmp_path):
    before = _digest(g4_bank_copy)
    report = regenerate_batch(g4_bank_copy, "B001", output=tmp_path / "preview")

    assert report.ok and len(report.assets) == 26
    assert _digest(g4_bank_copy) == before
    assert (tmp_path / "preview/manifest.json").is_file()
    assert (tmp_path / "preview/g4-l1-501-diagram-r2.svg").is_file()
    assert "right-triangle schematic" in (tmp_path / "preview/findings.md").read_text()
    with pytest.raises(ValueError):
        regenerate_batch(g4_bank_copy, "B001", output=g4_bank_copy / "preview")


def test_apply_writes_revisioned_assets_and_is_idempotent(g4_bank_copy):
    report = regenerate_batch(g4_bank_copy, "B001", apply=True)
    assert report.ok and sum(not asset.unchanged for asset in report.assets) == 26

    question = json.loads((g4_bank_copy / "questions/g4-l1-501.json").read_text())
    [asset] = question["assets"]
    assert question["revision"] == 2
    assert question["provenance"]["reviewed_at"] is None
    assert asset["path"] == "assets/g4-l1-501-diagram-r2.svg"
    assert asset["generation_spec"]["renderer"] == "nextscholar-right-triangle-svg-v2"
    assert (g4_bank_copy / "assets/g4-l1-501-diagram.svg").is_file()
    assert (
        hashlib.sha256((g4_bank_copy / asset["path"]).read_bytes()).hexdigest() == asset["sha256"]
    )

    validation = validate_bank(g4_bank_copy)
    assert validation.valid, validation.errors
    regenerated = {issue.path for issue in validation.issues if "-r2.svg" in issue.path}
    assert regenerated == set()

    again = regenerate_batch(g4_bank_copy, "B001", apply=True)
    assert again.ok and all(asset.unchanged for asset in again.assets)


def test_lesson_diagrams_regenerate_with_revisioned_names(tmp_path, repository_root):
    course = tmp_path / "course"
    shutil.copytree(repository_root / "backend_resources/courses/g3_math/secondary_2/g2/v1", course)

    report = regenerate_lessons(course, ["g5-lesson-06"], apply=True)

    assert report.ok and len(report.assets) == 3
    lesson = json.loads((course / "lessons/g5-lesson-06.json").read_text())
    assert lesson["revision"] == 2
    assert sorted(asset["path"] for asset in lesson["assets"]) == [
        "assets/g5-lesson-06-cone-r2.svg",
        "assets/g5-lesson-06-pyramid-r2.svg",
        "assets/g5-lesson-06-sphere-r2.svg",
    ]
    for asset in lesson["assets"]:
        findings = geometry_diagram_findings(
            course / asset["path"], asset["generation_spec"], asset["alt_text"]
        )
        assert findings == []
