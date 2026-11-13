"""The CI workflow (T1.4; 111-FR2, 111-AC2, 111-AC22; plan D18; lesson S1169)."""

import re

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1


@pytest.fixture
def workflow(repo_root):
    return yaml.safe_load((repo_root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))


def run_lines(job) -> list[str]:
    return [line.strip() for step in job["steps"] for line in str(step.get("run", "")).splitlines() if line.strip()]


def uses(job) -> list[str]:
    return [step["uses"] for step in job["steps"] if "uses" in step]


def test_111_ac2_runs_on_every_pull_request_to_main(workflow):
    triggers = workflow.get("on", workflow.get(True))

    assert triggers["pull_request"]["branches"] == ["main"]


def test_111_ac2_one_job_gates_the_merge(workflow):
    required = workflow["jobs"]["required"]

    assert set(required["needs"]) == set(workflow["jobs"]) - {"required"}
    assert required["if"] == "always()"
    assert any("contains" in line and "failure" in line for line in run_lines(required) + [str(required)])


def test_111_ac2_installs_from_lock_files_with_the_pinned_runtimes(workflow):
    build = workflow["jobs"]["build"]
    steps = {step.get("uses", "").split("@")[0]: step.get("with", {}) for step in build["steps"]}

    assert steps["actions/setup-java"]["java-version-file"] == ".java-version"
    assert steps["actions/setup-java"]["distribution"] == "temurin"
    assert steps["actions/setup-node"]["node-version-file"] == ".nvmrc"
    assert "cat .uv-version" in str(build["steps"])
    assert {"npm ci", "uv sync --project tools --frozen"} <= set(run_lines(build))
    assert any(line.startswith("./mvnw") and "verify" in line for line in run_lines(build))


def test_111_ac2_lint_format_typecheck_and_unit_tests_run(workflow):
    lines = run_lines(workflow["jobs"]["build"])

    for target in ["make lint", "make format-check", "make typecheck", "make test"]:
        assert target in lines


def test_111_ac22_one_job_per_registered_suite_from_the_registry(workflow):
    registry = workflow["jobs"]["registry"]
    suites = workflow["jobs"]["suites"]

    assert any(line.startswith("tools/check-suites") for line in run_lines(registry))
    assert any("tools/suite --matrix" in line for line in run_lines(registry))
    assert suites["needs"] == "registry"
    assert suites["strategy"]["matrix"] == "${{ fromJSON(needs.registry.outputs.matrix) }}"
    assert suites["strategy"]["fail-fast"] is False
    assert "make suite S=${{ matrix.suite }}" in run_lines(suites)


def test_111_ac2_database_suites_start_the_stack_on_the_runner(workflow):
    stack_steps = [step for step in workflow["jobs"]["suites"]["steps"] if step.get("run") == "make stack-up"]

    assert stack_steps and stack_steps[0]["if"] == "matrix.stack"


def test_one_job_builds_the_web_and_runs_the_browser_specs(workflow):
    lines = run_lines(workflow["jobs"]["browser"])

    assert any("--workspace=apps/web" in line and "build" in line for line in lines)
    assert any("playwright test" in line for line in lines)


def test_111_ac22_workflow_names_no_suite(repo_root):
    text = (repo_root / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert not re.search(r"\b\d{3}(-F\d+)?-B\d+", text)


def test_actions_are_pinned_to_exact_versions(workflow):
    for job in workflow["jobs"].values():
        for action in uses(job):
            assert re.search(r"@v\d+\.\d+\.\d+$", action), action
