"""Tests of tools/suite, the runner of one suite in any language (plan D18; 111-FR22, 111-AC22)."""

import json

import pytest
from conftest import run_tool

pytestmark = pytest.mark.suite_111_B1


def suite(root, *args: str):
    return run_tool("suite", "--root", str(root), *args)


def test_111_ac22_one_id_runs_every_entry_with_its_own_runner(fixture_root):
    result = suite(fixture_root("runners"), "--dry-run", "900-B1")

    assert result.returncode == 0, result.stderr
    commands = result.stdout.strip().splitlines()
    assert commands == [
        "uv run --project tools --frozen pytest -m suite_900_B1 tests",
        "npm exec --workspace=apps/web -- vitest run --testNamePattern 900-B1",
        "./mvnw -B -pl services/platform test -Dgroups=900-B1",
        "uv run --project tools --frozen pytest -m suite_900_B1 tools",
    ]


def test_playwright_and_script_commands(fixture_root):
    browser = suite(fixture_root("runners"), "--dry-run", "900-B2")
    script = suite(fixture_root("runners"), "--dry-run", "900-B3")

    assert browser.stdout.strip() == "npm exec --workspace=apps/web -- playwright test --grep 900-B2"
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


def test_suite_passes_when_its_commands_pass(fixture_root):
    result = suite(fixture_root("runners"), "900-B3")

    assert result.returncode == 0, result.stdout + result.stderr


def test_suite_fails_when_a_command_fails(fixture_root):
    result = suite(fixture_root("runners"), "900-B4")

    assert result.returncode == 1
    assert "900-B4" in result.stdout


def test_unknown_suite_is_refused(fixture_root):
    result = suite(fixture_root("runners"), "900-B7")

    assert result.returncode == 2
    assert "900-B7 is not in the registry" in result.stderr
