"""The CI workflow and the root targets (T1.4; 111-FR2, 111-AC2, 111-AC22; plan D1, D18; OD-21; lesson S1169)."""

import json
import os
import re
import shutil
import subprocess

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1

QUALITY_TARGETS = ["lint", "format-check", "typecheck", "test"]
REQUIRED_JOBS_OF_BLOCK_1 = {"install", "registry", "suites"}
# The tool each target needs per language; blocks 1b (Java) and 1c (TypeScript, Python) add them (OD-21).
JAVA_TOOLS = {
    "lint": ["maven-checkstyle-plugin", "maven-pmd-plugin"],
    "format-check": ["spotless-maven-plugin"],
    "typecheck": ["error_prone_core"],
    "test": ["junit-jupiter"],
}
TYPESCRIPT_TOOLS = {"lint": "eslint", "format-check": "prettier", "typecheck": "typescript", "test": "vitest"}
PYTHON_TOOLS = {"lint": "ruff", "format-check": "ruff", "typecheck": "mypy", "test": "pytest"}


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


def test_111_ac2_one_job_gates_the_merge_on_the_required_jobs_of_block_1(workflow):
    required = workflow["jobs"]["required"]

    assert set(required["needs"]) == REQUIRED_JOBS_OF_BLOCK_1
    assert required["if"] == "always()"
    assert any("contains" in line and "failure" in line for line in run_lines(required) + [str(required)])


def test_111_ac2_installs_from_lock_files_with_the_pinned_runtimes(workflow, repo_root):
    install = workflow["jobs"]["install"]
    steps = {step.get("uses", "").split("@")[0]: step.get("with", {}) for step in install["steps"]}
    script = (repo_root / "tools/install").read_text(encoding="utf-8").splitlines()

    assert steps["actions/setup-java"]["java-version-file"] == ".java-version"
    assert steps["actions/setup-java"]["distribution"] == "temurin"
    assert steps["actions/setup-node"]["node-version-file"] == ".nvmrc"
    assert "cat .uv-version" in str(install["steps"])
    assert "tools/install" in run_lines(install)
    assert {"npm ci", "uv sync --project tools --frozen"} <= {line.strip() for line in script}
    assert any(line.strip().startswith("./mvnw") and "verify" in line for line in script)


def test_111_ac2_quality_targets_run_in_ci_outside_the_required_jobs_of_block_1(workflow):
    quality = [name for name, job in workflow["jobs"].items() if "make lint" in run_lines(job)]

    assert len(quality) == 1
    assert {f"make {target}" for target in QUALITY_TARGETS} <= set(run_lines(workflow["jobs"][quality[0]]))
    assert quality[0] not in REQUIRED_JOBS_OF_BLOCK_1


STUB = """#!/usr/bin/env bash
echo "$(basename "$0") $*" >> "$STUB_LOG"
[ "$(basename "$0")" != "$FAILING_TOOL" ]
"""


def pom_with(tools: list[str]) -> str:
    plugins = "".join(f"<plugin><artifactId>{tool}</artifactId></plugin>" for tool in tools)
    return f'<project xmlns="http://maven.apache.org/POM/4.0.0"><build><plugins>{plugins}</plugins></build></project>\n'


def install_tools(repo, java: bool = True, typescript: bool = True) -> None:
    """Write the parent build and npm manifest with every tool of blocks 1b and 1c declared, or none."""
    java_tools = [tool for tools in JAVA_TOOLS.values() for tool in tools] if java else []
    (repo / "pom.xml").write_text(pom_with(java_tools), encoding="utf-8")
    manifest = json.loads((repo / "package.json").read_text(encoding="utf-8"))
    manifest["devDependencies"] = {tool: "1.0.0" for tool in TYPESCRIPT_TOOLS.values()} if typescript else {}
    (repo / "package.json").write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture
def stubbed_repo(repo_root, tmp_path):
    """A copy of the root's make entry points whose Maven wrapper, npm and uv only record their calls."""
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "packages/shell").mkdir(parents=True)
    for name in ["Makefile", "package.json", "tools/pyproject.toml"]:
        (repo / name).write_text((repo_root / name).read_text(encoding="utf-8"), encoding="utf-8")
    (repo / "packages/shell/package.json").write_text('{"name": "shell"}', encoding="utf-8")
    for script in QUALITY_TARGETS + ["quality"]:
        if (repo_root / "tools" / script).exists():
            shutil.copy2(repo_root / "tools" / script, repo / "tools" / script)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for stub in [repo / "mvnw", bin_dir / "npm", bin_dir / "uv"]:
        stub.write_text(STUB, encoding="utf-8")
        stub.chmod(0o755)
    return repo, bin_dir


def run_stubbed(stubbed_repo, target, failing_tool=""):
    repo, bin_dir = stubbed_repo
    log = repo.parent / "calls.log"
    log.touch()
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "STUB_LOG": str(log), "FAILING_TOOL": failing_tool}
    result = subprocess.run(["make", "-s", target], cwd=repo, check=False, capture_output=True, text=True, env=env)
    return result, log.read_text(encoding="utf-8")


@pytest.mark.parametrize("target", QUALITY_TARGETS)
@pytest.mark.parametrize(("java", "typescript"), [(False, False), (False, True), (True, False)])
def test_111_ac2_quality_target_fails_naming_the_missing_tool(stubbed_repo, target, java, typescript):
    install_tools(stubbed_repo[0], java=java, typescript=typescript)

    result, calls = run_stubbed(stubbed_repo, target)

    assert result.returncode != 0
    assert calls == "", "no check may run while a tool is missing"
    for tool in JAVA_TOOLS[target]:
        assert (tool in result.stderr) is not java, result.stderr
    assert (TYPESCRIPT_TOOLS[target] in result.stderr) is not typescript, result.stderr
    assert ("block 1b" in result.stderr) is not java
    assert ("block 1c" in result.stderr) is not typescript


@pytest.mark.parametrize("target", QUALITY_TARGETS)
def test_111_ac2_quality_target_fails_naming_a_missing_python_tool(stubbed_repo, target):
    repo = stubbed_repo[0]
    install_tools(repo)
    project = (repo / "tools/pyproject.toml").read_text(encoding="utf-8")
    tool = PYTHON_TOOLS[target]
    (repo / "tools/pyproject.toml").write_text(re.sub(rf'"{tool}==[^"]*",?\s*', "", project), encoding="utf-8")

    result, calls = run_stubbed(stubbed_repo, target)

    assert result.returncode != 0
    assert calls == ""
    assert tool in result.stderr
    assert "block 1c" in result.stderr


@pytest.mark.parametrize(
    ("target", "java", "typescript", "python"),
    [
        ("lint", "mvnw -B -ntp -q verify -DskipTests", "npm run --workspaces --if-present lint", "ruff check"),
        (
            "format-check",
            "mvnw -B -ntp -q validate",
            "npm run --workspaces --if-present format:check",
            "ruff format --check",
        ),
        ("typecheck", "mvnw -B -ntp -q test-compile", "npm run --workspaces --if-present typecheck", "mypy"),
        ("test", "mvnw -B -ntp -q test", "npm run --workspaces --if-present test", "pytest"),
    ],
)
def test_111_ac2_quality_target_checks_the_three_languages_once_their_tools_land(
    stubbed_repo, target, java, typescript, python
):
    install_tools(stubbed_repo[0])

    result, calls = run_stubbed(stubbed_repo, target)

    assert result.returncode == 0, result.stdout + result.stderr
    assert java in calls
    assert typescript in calls
    assert any(line.startswith("uv run --project tools --frozen") and python in line for line in calls.splitlines())


@pytest.mark.parametrize("target", QUALITY_TARGETS)
@pytest.mark.parametrize("failing_tool", ["mvnw", "npm", "uv"])
def test_111_ac2_quality_target_fails_when_one_language_fails(stubbed_repo, target, failing_tool):
    install_tools(stubbed_repo[0])

    result, _ = run_stubbed(stubbed_repo, target, failing_tool)

    assert result.returncode != 0


CI_STUB = """#!/usr/bin/env bash
echo "$(basename "$0") $*" >> "$STUB_LOG"
if [ "$(basename "$0") $*" = "suite --matrix" ]; then
  echo '{"include": [{"suite": "900-B1", "stack": false}, {"suite": "900-B2", "stack": false}]}'
fi
[ "$(basename "$0") $*" != "$FAILING_CALL" ]
"""


def run_make_ci(repo_root, tmp_path, failing_call="", **env_vars):
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "Makefile").write_text((repo_root / "Makefile").read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copy2(repo_root / "tools/ci", repo / "tools/ci")
    for name in ["install", "check-suites", "suite", *QUALITY_TARGETS, "quality"]:
        (repo / "tools" / name).write_text(CI_STUB, encoding="utf-8")
        (repo / "tools" / name).chmod(0o755)
    log = tmp_path / "calls.log"
    log.touch()
    env = {**os.environ, "STUB_LOG": str(log), "FAILING_CALL": failing_call, **env_vars}
    result = subprocess.run(["make", "-s", "ci"], cwd=repo, check=False, capture_output=True, text=True, env=env)
    return result, log.read_text(encoding="utf-8").splitlines()


def test_111_ac2_make_ci_runs_install_the_registry_check_and_every_suite_only(repo_root, tmp_path):
    result, calls = run_make_ci(repo_root, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == ["install ", "check-suites ", "suite --matrix", "suite 900-B1", "suite 900-B2"]


def test_111_ac22_make_ci_checks_the_spec_repository_and_the_block_being_built(repo_root, tmp_path):
    spec_repo = tmp_path / "spec"
    for feature in ["104-trust-centre", "111-register-foundation"]:
        (spec_repo / "specs" / feature).mkdir(parents=True)
        (spec_repo / "specs" / feature / "tasks.md").write_text("# Tasks\n", encoding="utf-8")

    result, calls = run_make_ci(repo_root, tmp_path, SPEC_REPO=str(spec_repo), BLOCK="111-B1")

    assert result.returncode == 0, result.stdout + result.stderr
    specs = spec_repo / "specs"
    assert calls[1] == (
        f"check-suites --tasks {specs}/104-trust-centre/tasks.md --tasks {specs}/111-register-foundation/tasks.md"
        " --block 111-B1"
    )


@pytest.mark.parametrize("failing_call", ["install ", "check-suites ", "suite 900-B1"])
def test_111_ac2_make_ci_fails_when_a_step_fails(repo_root, tmp_path, failing_call):
    result, calls = run_make_ci(repo_root, tmp_path, failing_call)

    assert result.returncode != 0
    assert failing_call in calls


def registry_check_step(workflow) -> dict:
    steps = workflow["jobs"]["registry"]["steps"]
    return next(step for step in steps if "tools/check-suites" in str(step.get("run", "")))


def run_registry_check(workflow, workspace, runner_temp):
    """Run the registry job's check step in `workspace`, with a tools/check-suites that records its arguments."""
    (workspace / "tools").mkdir(parents=True, exist_ok=True)
    check_suites = workspace / "tools/check-suites"
    check_suites.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "$CALLS"\n', encoding="utf-8")
    check_suites.chmod(0o755)
    runner_temp.mkdir(exist_ok=True)
    calls = workspace / "calls"
    env = {**os.environ, "RUNNER_TEMP": str(runner_temp), "CALLS": str(calls)}
    script = registry_check_step(workflow)["run"]
    result = subprocess.run(
        ["bash", "-e", "-c", script], cwd=workspace, env=env, check=False, capture_output=True, text=True
    )
    return result, calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []


def test_111_ac22_the_spec_repository_is_always_checked_out(workflow):
    steps = workflow["jobs"]["registry"]["steps"]
    checkout = next(step for step in steps if step.get("with", {}).get("repository") == "${{ vars.SPEC_REPO }}")

    assert "if" not in checkout
    assert "if" not in registry_check_step(workflow)


def test_111_ac22_registry_check_fails_without_the_spec_repository(workflow, tmp_path):
    result, calls = run_registry_check(workflow, tmp_path / "workspace", tmp_path / "runner")

    assert result.returncode != 0
    assert calls == []


def test_111_ac22_registry_check_reads_every_tasks_file_of_the_spec_repository(workflow, tmp_path):
    workspace = tmp_path / "workspace"
    for feature in ["104-trust-centre", "111-register-foundation"]:
        (workspace / ".spec-repo/specs" / feature).mkdir(parents=True)
        (workspace / ".spec-repo/specs" / feature / "tasks.md").write_text("# Tasks\n", encoding="utf-8")

    result, calls = run_registry_check(workflow, workspace, tmp_path / "runner")

    assert result.returncode == 0, result.stdout + result.stderr
    spec_repo = tmp_path / "runner/spec-repo/specs"
    assert calls == [
        "--tasks",
        str(spec_repo / "104-trust-centre/tasks.md"),
        "--tasks",
        str(spec_repo / "111-register-foundation/tasks.md"),
    ]


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
