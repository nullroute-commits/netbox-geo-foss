"""Pytest configuration shared by the active netbox_geo test suite."""

import shutil
from pathlib import Path

import pytest

TEST_UPLOAD_DIR = Path("/tmp/test_uploads")


def pytest_configure(config: pytest.Config) -> None:
    """Register shared markers for strict marker validation."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")
    config.addinivalue_line("markers", "slow: slow-running tests")
    config.addinivalue_line("markers", "security: security-focused tests")


@pytest.fixture(autouse=True)
def reset_test_data() -> None:
    """Reset temporary test artifacts around each test."""
    if TEST_UPLOAD_DIR.exists():
        shutil.rmtree(TEST_UPLOAD_DIR)
    TEST_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    yield

    if TEST_UPLOAD_DIR.exists():
        shutil.rmtree(TEST_UPLOAD_DIR)
