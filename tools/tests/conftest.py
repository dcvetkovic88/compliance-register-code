"""Shared paths for the tests of the repository tools."""

import subprocess
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def run_tool(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run one of the tools/ entry points the way a developer or CI does."""
    return subprocess.run(
        [str(TOOLS_DIR / name), *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def fixture_root():
    def resolve(case: str) -> Path:
        return FIXTURES_DIR / case

    return resolve
