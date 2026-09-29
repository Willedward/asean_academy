"""Deterministic diagnostic policy tests without PostgreSQL."""

import pytest

from learning_api.diagnostic_repository import band_for


@pytest.mark.parametrize(
    ("percentage", "band"),
    [
        (0, "getting_started"),
        (49.99, "getting_started"),
        (50, "on_track"),
        (79.99, "on_track"),
        (80, "ahead"),
        (100, "ahead"),
    ],
)
def test_n1_readiness_band_boundaries(percentage, band):
    assert band_for(percentage) == band
