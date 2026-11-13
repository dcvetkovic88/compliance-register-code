"""Tests of tools/suite, the runner of one suite in any language (plan D18; 111-FR22, 111-AC22).

`tools/suite` writes one JUnit XML report per suite entry, which `tools/check-suites` reads.
"""

import json
import os
import shutil
from pathlib import Path
from xml.etree import ElementTree

import pytest
import yaml
from conftest import TOOLS_DIR, run_tool

pytestmark = pytest.mark.suite_111_B1

REPO_ROOT = TOOLS_DIR.parent


def suite(root, *args: str, env: dict[str, str] | None = None):
    return run_tool("suite", "--root", str(root), *args, env=env)


def test_111_ac22_one_id_runs_every_entry_with_its_own_runner_and_report(fixture_root):
    root = fixture_root("runners").resolve()
    reports = root / ".suite-reports/900-B1"

    result = suite(root, "--dry-run", "900-B1")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines() == [
        f"uv run --project tools --frozen pytest -m suite_900_B1 tests --junitxml={reports}/root-pytest.xml",
        (
            "npm exec --workspace=apps/web -- vitest run --testNamePattern 900-B1 --reporter=default --reporter=junit"
            f" --outputFile.junit={reports}/apps-web-vitest.xml"
        ),
        "./mvnw -B -pl services/platform -am test -Dgroups=900-B1",
        f"uv run --project tools --frozen pytest -m suite_900_B1 tools --junitxml={reports}/tools-pytest.xml",
    ]


def test_playwright_and_script_commands(fixture_root):
    root = fixture_root("runners").resolve()
    browser = suite(root, "--dry-run", "900-B2")
    script = suite(root, "--dry-run", "900-B3")

    assert browser.stdout.strip() == (
        f"env PLAYWRIGHT_JUNIT_OUTPUT_FILE={root}/.suite-reports/900-B2/apps-web-playwright.xml"
        " npm exec --workspace=apps/web -- playwright test --grep 900-B2 --reporter=list,junit"
    )
    assert script.stdout.strip() == "bash deploy/scripts/passes.sh"


def test_111_ac22_matrix_lists_every_registered_suite_once(fixture_root):
    result = suite(fixture_root("runners"), "--matrix")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "include": [
            {"suite": "900-B1", "stack": False},
            {"suite": "900-B2", "stack": True},
            {"suite": "900-B3", "stack": False},
            {"suite": "900-B4", "stack": False},
        ]
    }


def reported_cases(report: Path) -> list[ElementTree.Element]:
    return list(ElementTree.parse(report).getroot().iter("testcase"))


def test_suite_passes_when_its_commands_pass_and_reports_the_script(fixture_root, tmp_path):
    result = suite(fixture_root("runners"), "--reports", str(tmp_path), "900-B3")

    assert result.returncode == 0, result.stdout + result.stderr
    cases = reported_cases(tmp_path / "900-B3/deploy-script.xml")
    assert [case.get("name") for case in cases] == ["scripts/passes.sh"]
    assert cases[0].find("failure") is None


def test_suite_fails_when_a_command_fails(fixture_root, tmp_path):
    result = suite(fixture_root("runners"), "--reports", str(tmp_path), "900-B4")

    assert result.returncode == 1
    assert "900-B4" in result.stdout
    assert reported_cases(tmp_path / "900-B4/deploy-script.xml")[0].find("failure") is not None


def test_unknown_suite_is_refused(fixture_root):
    result = suite(fixture_root("runners"), "900-B7")

    assert result.returncode == 2
    assert "900-B7 is not in the registry" in result.stderr


def copy_fixture(fixture_root, case: str, target: Path) -> Path:
    repo = target / "repo"
    shutil.copytree(fixture_root(case), repo)
    return repo


def check(repo: Path):
    return run_tool("check-suites", "--root", str(repo), "--tasks", str(repo / "tasks.md"))


def test_111_ac22_only_pytest_tests_that_ran_count(fixture_root, tmp_path):
    repo = copy_fixture(fixture_root, "pytest-run", tmp_path)
    suites_file = repo / "tools/suites.yaml"
    entries = yaml.safe_load(suites_file.read_text(encoding="utf-8"))
    entries["suites"][0]["project"] = str(TOOLS_DIR)
    suites_file.write_text(yaml.safe_dump(entries), encoding="utf-8")

    ran = suite(repo, "900-B1")
    result = check(repo)

    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert result.returncode == 1
    assert "proves 900-AC2" in result.stdout, "a skipif(True) test runs nothing"
    assert "proves 900-AC3" in result.stdout, "a test with an empty parameter set runs nothing"
    assert "proves 900-AC1" not in result.stdout


def test_111_ac22_a_maven_suite_builds_the_libraries_its_module_needs_on_a_clean_local_repository(
    fixture_root, tmp_path
):
    repo = copy_fixture(fixture_root, "maven-dependent-module", tmp_path)
    for name in ["pom.xml", "mvnw"]:
        shutil.copy2(REPO_ROOT / name, repo / name)
    shutil.copytree(REPO_ROOT / ".mvn", repo / ".mvn")
    clean_repository = tmp_path / "m2"
    env = {**os.environ, "MAVEN_ARGS": f"-ntp -Dmaven.repo.local={clean_repository}"}

    ran = suite(repo, "900-B1", env=env)
    result = check(repo)

    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert not (clean_repository / "com/wisertech/register/service-kit").exists(), "the library is built, not installed"
    assert result.returncode == 1
    assert "proves 900-AC2" in result.stdout, "a @Disabled test runs nothing"
    assert "proves 900-AC1" not in result.stdout, "the display name of a test that ran proves its criterion"
