from __future__ import annotations

import json
import logging

from learning_api.observability import RailwayJsonFormatter


def test_railway_formatter_emits_searchable_single_line_json():
    record = logging.LogRecord(
        "learning_api",
        logging.INFO,
        __file__,
        1,
        "request_complete",
        (),
        None,
    )
    record.request_id = "request-123"
    record.http_status = 200
    record.duration_ms = 12.5
    record.release_sha = "abc123"

    rendered = RailwayJsonFormatter().format(record)
    payload = json.loads(rendered)

    assert "\n" not in rendered
    assert payload["message"] == "request_complete"
    assert payload["request_id"] == "request-123"
    assert payload["http_status"] == 200
    assert payload["release_sha"] == "abc123"
