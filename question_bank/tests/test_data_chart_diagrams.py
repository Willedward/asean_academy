import json
import shutil
import tempfile
from pathlib import Path

import pytest

from question_bank.diagrams import DATA_CHART_RENDERER, charts
from question_bank.diagrams.questions import render_question_asset
from question_bank.diagrams.regenerate import DATA_DISPLAY_STEM, regenerate_batch
from question_bank.geometry_validation import geometry_diagram_findings
from question_bank.validation import validate_bank

SAMPLES = {
    "bar_chart": {
        "categories": ["Mon", "Tue", "Wed"],
        "values": [6, 9, 7],
        "y_max": 10,
        "tick_step": 2,
    },
    "line_chart": {
        "categories": ["10:00", "12:00", "14:00"],
        "values": [24, 27, 25],
        "y_min": 20,
        "y_max": 30,
        "tick_step": 2,
    },
    "pictogram": {"rows": [{"label": "Votes", "count": 3}], "key": 4, "symbol": "★"},
    "vertical_scale": {
        "ticks": [0, 5, 10, 15, 20, 25, 30, 35, 40],
        "points": [{"tick_index": 3, "label": "A"}, {"tick_index": 8, "label": "B"}],
    },
    "dot_plot": {"values": [3, 5, 6, 5, 7, 5, 4]},
    "stem_leaf": {
        "rows": [{"stem": 4, "leaves": [1, 3, 4, 7, 8]}],
        "key": "4 | 1 means 41",
    },
    "histogram": {
        "bins": [
            {"start": 0, "end": 10, "height": 4},
            {"start": 10, "end": 20, "height": 6},
            {"start": 20, "end": 30, "height": 5},
        ],
        "y_max": 6,
        "tick_step": 1,
    },
    "probability_scale": {"value": 0.35},
    "spinner": {"labels": ["R", "R", "B", "G"]},
    "pie_chart": {"labels": ["Sector", "Rest"], "values": [1, 3]},
    "data_table": {
        "columns": ["Chess", "Coding"],
        "rows": ["Group 1", "Group 2"],
        "cells": [[17, 11], [14, None]],
    },
    "number_line": {"boundary": 4, "relation": "<="},
    "coordinate_line": {
        "a": 2,
        "b": 3,
        "c": 18,
        "point_x": 3,
        "x_min": -1,
        "x_max": 8,
        "y_min": -1,
        "y_max": 8,
    },
    "quadratic_graph": {"roots": [-5, 3], "a": 1, "x_min": -7, "x_max": 5},
}


def findings(diagram, svg=None, spec=None, alt_text=None):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "chart.svg"
        path.write_text(svg or diagram.svg)
        return geometry_diagram_findings(
            path,
            spec or diagram.generation_spec,
            diagram.alt_text if alt_text is None else alt_text,
            strict=True,
        )


@pytest.mark.parametrize(("template", "inputs"), SAMPLES.items())
def test_checked_chart_templates_are_deterministic_and_validate(template, inputs):
    first = charts.TEMPLATES[template](inputs)
    second = charts.TEMPLATES[template](inputs)

    assert first.svg == second.svg
    assert first.generation_spec == second.generation_spec
    assert first.generation_spec["renderer"] == DATA_CHART_RENDERER
    assert first.generation_spec["min_phone_font_px"] >= 12
    assert findings(first) == []


def test_chart_validator_detects_a_changed_bar_height():
    diagram = charts.bar_chart(SAMPLES["bar_chart"])
    svg = diagram.svg.replace('data-chart-mark="bar-1"', 'data-chart-mark="bar-1"')
    expected = diagram.generation_spec["chart_marks"][1]["geometry"]["height"]
    svg = svg.replace(f'height="{expected}"', 'height="1"', 1)

    assert "chart_mark_geometry" in {finding.code for finding in findings(diagram, svg=svg)}


def test_chart_validator_recomputes_metadata_from_inputs():
    diagram = charts.dot_plot(SAMPLES["dot_plot"])
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["chart_marks"][0]["value"] = "99"

    assert "chart_metadata_mismatch" in {finding.code for finding in findings(diagram, spec=spec)}


def test_chart_validator_detects_changed_visible_text():
    diagram = charts.bar_chart(SAMPLES["bar_chart"])
    svg = diagram.svg.replace(">Tue</text>", ">Thu</text>")

    assert "chart_visible_text_mismatch" in {finding.code for finding in findings(diagram, svg=svg)}


def test_chart_validator_does_not_allow_forbidden_labels_to_be_removed():
    diagram = charts.bar_chart({**SAMPLES["bar_chart"], "forbidden_visible_labels": ["9"]})
    spec = json.loads(json.dumps(diagram.generation_spec))
    spec["forbidden_visible_labels"] = []

    assert "chart_metadata_mismatch" in {finding.code for finding in findings(diagram, spec=spec)}


def test_stored_chart_request_renders_through_question_pipeline():
    inputs = SAMPLES["probability_scale"]
    question = {
        "stable_key": "s2-l1-513",
        "school_level": "secondary_2",
        "topic_code": "S2",
        "primary_outcome": "2.1",
        "stem": [],
        "parts": [
            {
                "prompt": [{"type": "text", "text": "Read the marked probability."}],
                "response": {"canonical_answer": "35", "accepted_answers": []},
            }
        ],
    }
    asset = {
        "generation_spec": {
            "renderer": DATA_CHART_RENDERER,
            "template": "probability_scale",
            "inputs": inputs,
        }
    }

    diagram = render_question_asset(question, asset)

    assert diagram.generation_spec["question_key"] == "s2-l1-513"
    assert diagram.generation_spec["template"] == "probability_scale"
    assert findings(diagram) == []


def test_number_line_distinguishes_open_and_closed_boundaries():
    closed = charts.number_line({"boundary": 4, "relation": "<="})
    opened = charts.number_line({"boundary": 4, "relation": "<"})

    assert 'data-chart-kind="closed-boundary"' in closed.svg
    assert 'data-chart-kind="open-boundary"' in opened.svg
    assert 'data-direction="left"' in closed.svg


def test_number_line_can_show_a_bounded_interval():
    diagram = charts.number_line(
        {
            "boundary": -3,
            "relation": ">",
            "upper_boundary": 5,
            "upper_relation": "<=",
            "x_min": -5,
            "x_max": 7,
        }
    )
    kinds = {
        mark["key"]: mark["kind"] for mark in diagram.generation_spec["chart_marks"]
    }

    assert kinds == {"boundary": "open-boundary", "upper-boundary": "closed-boundary"}
    assert 'data-role="solution-segment"' in diagram.svg
    assert "solution-ray" not in diagram.svg
    assert "greater than -3 and less than or equal to 5" in diagram.alt_text

    single = charts.number_line({"boundary": 6, "relation": "<"})
    assert 'data-role="solution-ray"' in single.svg
    assert "solution-segment" not in single.svg


def test_number_line_interval_rejects_impossible_bounds():
    with pytest.raises(ValueError, match="upper_boundary"):
        charts.number_line(
            {"boundary": 5, "relation": ">", "upper_boundary": 1, "upper_relation": "<"}
        )


def test_histogram_can_mark_a_bin_as_unknown_without_inventing_its_height():
    diagram = charts.histogram(
        {
            "bins": [
                {"start": 0, "end": 5, "height": 2.6},
                {"start": 5, "end": 10, "height": 3.8},
                {"start": 10, "end": 15, "height": 2.2},
                {"start": 15, "end": 23, "height": None},
            ],
            "y_max": 4,
            "tick_step": 1,
            "y_label": "Frequency density",
            "forbidden_visible_labels": ["2.5"],
        }
    )

    missing = diagram.generation_spec["chart_marks"][-1]
    assert missing["kind"] == "missing-histogram-bin"
    assert missing["value"] == "unknown"
    assert 'stroke-dasharray="10 8"' in diagram.svg
    assert ">?</text>" in diagram.svg
    assert "unknown" in diagram.alt_text
    assert findings(diagram) == []


def test_pictogram_marks_record_the_value_represented_by_each_symbol():
    diagram = charts.pictogram(
        {"rows": [{"label": "Votes", "count": 2.5}], "key": 4, "symbol": "★"}
    )

    assert [mark["value"] for mark in diagram.generation_spec["chart_marks"]] == [
        "4",
        "4",
        "2",
    ]
    assert "Votes has 2.5 symbols" in diagram.alt_text


def test_explicit_forbidden_labels_are_checked_for_answer_leaks():
    diagram = charts.bar_chart(
        {
            **SAMPLES["bar_chart"],
            "forbidden_visible_labels": ["9"],
        }
    )

    assert "geometry_answer_leak" in {finding.code for finding in findings(diagram)}


def test_explicit_chart_request_applies_revisioned_asset(repository_root, tmp_path):
    source = repository_root / "backend_resources/question_bank/g3_math/secondary_1/s1/v1"
    bank = tmp_path / "backend_resources/question_bank/g3_math/secondary_1/s1/v1"
    shutil.copytree(source, bank)
    shutil.copytree(
        repository_root / "backend_resources/question_bank/schema",
        tmp_path / "backend_resources/question_bank/schema",
    )
    request = {
        "s1-l3-001": {
            "template": "data_table",
            "inputs": {
                "columns": ["Choice A", "Choice B"],
                "rows": ["Row 1", "Row 2"],
                "cells": [[17, 11], [14, None]],
                "forbidden_visible_labels": ["18"],
            },
        }
    }

    report = regenerate_batch(
        bank,
        "B001",
        apply=True,
        add=["s1-l3-001"],
        renderer=DATA_CHART_RENDERER,
        requests=request,
    )

    assert report.ok, report.as_dict()
    question = json.loads((bank / "questions/s1-l3-001.json").read_text())
    [asset] = question["assets"]
    assert question["revision"] == 2
    assert question["stem"][:2] == [
        {"type": "text", "text": DATA_DISPLAY_STEM},
        {"type": "asset_ref", "asset_key": "s1-l3-001-diagram"},
    ]
    assert asset["kind"] == "chart"
    assert asset["path"] == "assets/s1-l3-001-diagram-r2.svg"
    assert asset["generation_spec"]["template"] == "data_table"
    validation = validate_bank(
        bank,
        catalogue_path=repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        strict_geometry=True,
    )
    assert validation.valid, validation.errors


def test_quadratic_graph_can_hide_the_axis_of_symmetry():
    inputs = {"roots": [-7, 1], "a": 1, "x_min": -9, "x_max": 3}

    shown = charts.quadratic_graph(inputs)
    hidden = charts.quadratic_graph({**inputs, "show_symmetry": False})

    assert 'data-role="axis-of-symmetry"' in shown.svg
    assert 'data-role="axis-of-symmetry"' not in hidden.svg
    assert not [mark for mark in hidden.generation_spec["chart_marks"] if mark["key"] == "vertex"]
    assert findings(hidden) == []
