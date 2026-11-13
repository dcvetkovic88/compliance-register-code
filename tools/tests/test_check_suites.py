"""Tests of tools/check-suites (plan D18; 111-FR22, 111-AC22; conventions SA-3-2)."""

import pytest
from conftest import run_tool

pytestmark = pytest.mark.suite_111_B1


def check(root, *extra: str):
    tasks = root / "tasks.md"
    args = ["--root", str(root)]
    if tasks.exists():
        args += ["--tasks", str(tasks)]
    return run_tool("check-suites", *args, *extra)


def test_111_ac22_clean_repository_passes(fixture_root):
    result = check(fixture_root("clean"))

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac22_fails_when_tasks_name_an_unregistered_suite(fixture_root):
    result = check(fixture_root("unregistered-suite"))

    assert result.returncode == 1
    assert "900-B2" in result.stdout
    assert "not in the registry" in result.stdout


def test_111_ac22_fails_when_a_registered_suite_selects_no_test(fixture_root):
    result = check(fixture_root("suite-without-test"))

    assert result.returncode == 1
    assert "900-B1" in result.stdout
    assert "selects no test" in result.stdout


def test_111_ac22_fails_when_an_acceptance_test_lacks_the_full_criterion_id(fixture_root):
    result = check(fixture_root("partial-criterion-id"))

    assert result.returncode == 1
    assert "test_ac22_registry_is_checked" in result.stdout
    assert "AC6 delegated approval fails after expiry" in result.stdout
    assert "F2-AC3 the screen renders" in result.stdout


def test_111_ac22_fails_when_a_task_adds_tests_in_a_path_without_the_suite(fixture_root):
    result = check(fixture_root("block-path-without-entry"))

    assert result.returncode == 1
    assert "T1.2" in result.stdout
    assert "repo-root" in result.stdout
    assert "900-B1" in result.stdout


@pytest.mark.parametrize(
    ("case", "file"),
    [
        ("empty-tagged-pytest", "tools/suites.yaml"),
        ("empty-tagged-junit", "services/platform/suites.yaml"),
        ("empty-tagged-vitest", "apps/web/suites.yaml"),
    ],
)
def test_111_ac22_fails_when_the_tagged_file_or_class_holds_no_test(fixture_root, case, file):
    result = check(fixture_root(case))

    assert result.returncode == 1
    assert f"suite 900-B1 in {file} selects no test" in result.stdout
    assert "selects no test" in result.stdout


def test_111_ac22_tagged_tests_count_in_each_runner(fixture_root):
    result = check(fixture_root("tagged-tests-in-each-runner"))

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac22_fails_when_a_proved_criterion_has_no_acceptance_test(fixture_root):
    result = check(fixture_root("criterion-without-acceptance-test"))

    assert result.returncode == 1
    assert "900-AC2" in result.stdout
    assert "no acceptance test" in result.stdout
    assert "900-AC1" not in result.stdout


def test_111_ac22_a_later_unticked_block_naming_a_missing_suite_passes(fixture_root):
    result = check(fixture_root("later-block-unbuilt-suite"))

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac22_the_block_being_built_is_checked_but_not_later_blocks(fixture_root):
    result = check(fixture_root("later-block-unbuilt-suite"), "--block", "900-B2")

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac22_the_block_being_built_is_checked(fixture_root):
    result = check(fixture_root("later-block-unbuilt-suite"), "--block", "900-B3")

    assert result.returncode == 1
    assert "900-B3" in result.stdout
    assert "not in the registry" in result.stdout
    assert "900-AC3" in result.stdout


def test_malformed_entry_is_reported_with_its_file(fixture_root):
    result = check(fixture_root("malformed-entry"))

    assert result.returncode == 1
    assert "tools/suites.yaml" in result.stdout
    assert "suite-one" in result.stdout
    assert "gradle" in result.stdout


def test_entry_whose_path_is_a_test_file_selects_the_tests_in_it(fixture_root):
    result = check(fixture_root("file-path-entry"))

    assert result.returncode == 0, result.stdout + result.stderr
