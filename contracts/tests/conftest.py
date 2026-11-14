"""Tests of the contracts path: the sync, the drift check, the validation and the generated web clients (block 4)."""

import shutil
import subprocess
from pathlib import Path

import pytest

CONTRACTS = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).parent / "fixtures"
SPEC_FOLDER = "docs/standalone/contracts"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "suite_111_B4: check suite 111-B4 (contracts sync)")


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run one script of contracts/scripts and capture what it prints."""
    return subprocess.run([str(CONTRACTS / "scripts" / name), *args], check=False, capture_output=True, text=True)


def git(repo: Path, *args: str) -> str:
    command = ["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", *args]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def spec_repo(tmp_path: Path) -> Path:
    """A temporary git repository standing in for the spec repository, holding the fixture contracts."""
    repo = tmp_path / "spec"
    shutil.copytree(FIXTURES / "spec-contracts", repo / SPEC_FOLDER)
    git(repo, "init", "-q")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "contracts")
    return repo


@pytest.fixture
def synced(tmp_path: Path, spec_repo: Path) -> Path:
    """A contracts folder synced from the temporary spec repository."""
    target = tmp_path / "contracts"
    result = run_script("sync", "--spec-repo", str(spec_repo), "--contracts", str(target))
    assert result.returncode == 0, result.stdout + result.stderr
    return target
