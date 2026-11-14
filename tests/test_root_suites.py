"""The root suites.yaml and the registry rule in the README (T1.3; 111-FR22, 111-AC22; plan D18)."""

import os
import subprocess

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1

BLOCK_1 = """# Feature 111: Tasks

### Block 1: repository root and suites registry (suite: `111-B1`; proves 111-AC2, 111-AC22). Needs: block 0

- [x] T1.1 [tools] Tests first: two fixtures for `tools/check-suites`, \
then `tools/check-suites` and `tools/suite <id>` (111-FR22, 111-AC22)
- [x] T1.2 [repo-root] Build files: Maven parent with the wrapper, npm workspace manifest, \
lock files (111-FR2, 111-AC2)
- [x] T1.3 [repo-root] The root `suites.yaml` for root-level suites, with the entry `111-B1` (111-FR22, 111-AC22)
- [x] T1.4 [repo-root] CI workflow: lint, format check, type check, \
unit tests for the three languages (111-FR2, 111-AC2)
"""


def test_111_ac22_root_suites_file_registers_the_root_tests(repo_root):
    entries = yaml.safe_load((repo_root / "suites.yaml").read_text(encoding="utf-8"))["suites"]

    assert {
        "id": "111-B1",
        "runner": "pytest",
        "selector": "suite_111_B1",
        "project": "tools",
        "paths": ["tests"],
    } in entries


def test_111_ac22_suite_111_b1_runs_the_root_and_the_tools_tests(repo_root):
    result = subprocess.run(
        [str(repo_root / "tools/suite"), "--dry-run", "111-B1"], check=False, capture_output=True, text=True
    )

    reports = repo_root / ".suite-reports/111-B1"
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "uv run --project tools --frozen pytest -m suite_111_B1 tests"
        f" --junitxml={reports}/root-pytest-suite_111_B1.xml",
        "uv run --project tools --frozen pytest -m suite_111_B1 tools"
        f" --junitxml={reports}/tools-pytest-suite_111_B1.xml",
    ]


# The suite runs here without this test, which would run itself again, and without the slow CI and
# clean Maven repository tests; what is left still holds an acceptance test of each criterion.
NOT_NESTED = "not block_1_passes and not ci_workflow and not clean_local_repository"


def registry_of_block_1(repo_root, registry_root):
    """A copy of the registry with only the entries of suite 111-B1; later blocks' suites have no report here."""
    for suites_file in repo_root.glob("**/suites.yaml"):
        relative = suites_file.relative_to(repo_root)
        if {"fixtures", "node_modules", "target", ".venv"}.intersection(relative.parts):
            continue
        entries = yaml.safe_load(suites_file.read_text(encoding="utf-8"))["suites"]
        copy = registry_root / relative
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_text(yaml.safe_dump({"suites": [e for e in entries if e["id"] == "111-B1"]}), encoding="utf-8")


def test_111_ac22_block_1_passes_the_registry_check(repo_root, tmp_path):
    registry_root = tmp_path / "registry"
    registry_of_block_1(repo_root, registry_root)
    tasks = tmp_path / "tasks.md"
    tasks.write_text(BLOCK_1, encoding="utf-8")
    reports = tmp_path / "reports"
    env = {**os.environ, "PYTEST_ADDOPTS": f"-k '{NOT_NESTED}'"}

    ran = subprocess.run(
        [str(repo_root / "tools/suite"), "--reports", str(reports), "111-B1"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    result = subprocess.run(
        [
            str(repo_root / "tools/check-suites"),
            "--root",
            str(registry_root),
            "--reports",
            str(reports),
            "--tasks",
            str(tasks),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert result.returncode == 0, result.stdout


def test_readme_states_the_registry_rule(repo_root):
    readme = " ".join((repo_root / "README.md").read_text(encoding="utf-8").split())

    assert "every block's last task adds its suite to the `suites.yaml` of its own path" in readme
    assert "tools/check-suites" in readme
    assert "reads the JUnit XML reports `tools/suite` writes" in readme
    assert "`.suite-reports/<id>/<path>-<runner>-<selector>.xml`" in readme
