import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "services/learning_api/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "bootstrap_hosted", SCRIPTS / "bootstrap_hosted.py"
)
bootstrap_hosted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap_hosted)


def test_hosted_bootstrap_accepts_only_a_preview_database():
    assert bootstrap_hosted.hosted_database_url(
        {
            "ASEAN_ACADEMY_ENV": "preview",
            "ASEAN_ACADEMY_DATABASE_URL": "postgresql://example.test/staging",
        }
    ) == "postgresql://example.test/staging"


@pytest.mark.parametrize("environment", ["", "development", "test", "production"])
def test_hosted_bootstrap_refuses_other_environments(environment):
    with pytest.raises(ValueError, match="requires ASEAN_ACADEMY_ENV=preview"):
        bootstrap_hosted.hosted_database_url(
            {
                "ASEAN_ACADEMY_ENV": environment,
                "ASEAN_ACADEMY_DATABASE_URL": "postgresql://example.test/unsafe",
            }
        )


def test_hosted_bootstrap_requires_a_database_url():
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        bootstrap_hosted.hosted_database_url({"ASEAN_ACADEMY_ENV": "preview"})
