from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repository_root():
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def bank_root(repository_root):
    return (
        repository_root
        / "backend_resources/question_bank/g3_math/secondary_1/n1/v1"
    )
