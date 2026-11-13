"""Root-level tests of the repository: build files, suites registry, CI workflow (block 1), quality tooling (1b, 1c)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "suite_111_B1: check suite 111-B1 (repository root and suites registry)")
    config.addinivalue_line("markers", "suite_111_B1b: check suite 111-B1b (quality tooling, Java and repository)")
    config.addinivalue_line(
        "markers", "suite_111_B1c: check suite 111-B1c (quality tooling, Python, TypeScript and contracts)"
    )


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT
