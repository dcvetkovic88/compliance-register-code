"""Root build files and version pins (T1.2; 111-FR2, 111-AC2; plan D1; lessons S1177 to S1179)."""

import json
import os
import re
import shutil
import subprocess
from xml.etree import ElementTree

import pytest

pytestmark = pytest.mark.suite_111_B1

MAVEN = "{http://maven.apache.org/POM/4.0.0}"
JAVA_MODULES = [
    "libs/service-kit",
    "libs/eventbus",
    "services/platform",
    "services/register",
    "services/ict-risk",
    "services/monitoring",
    "services/bff",
]
QUALITY_TARGETS = ["lint", "format-check", "typecheck", "test"]
MAKE_TARGETS = ["lint", "format-check", "typecheck", "test", "suite", "ci", "stack-up", "stack-down"]
PIN_FILES = {".java-version": "Java", ".nvmrc": "Node", ".python-version": "Python", ".uv-version": "uv"}


def pinned(repo_root, pin_file: str) -> str:
    return (repo_root / pin_file).read_text(encoding="utf-8").strip()


def readme_pins(repo_root) -> dict[str, str]:
    """The `| Tool | Pin | ... |` table of the root README."""
    rows = re.findall(
        r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|", (repo_root / "README.md").read_text(encoding="utf-8"), re.MULTILINE
    )
    return dict(rows)


def test_111_ac2_every_runtime_has_one_pin_file_recorded_in_the_readme(repo_root):
    pins = readme_pins(repo_root)

    for pin_file, tool in PIN_FILES.items():
        assert pins.get(tool) == pinned(repo_root, pin_file), f"{tool} pin in README differs from {pin_file}"


def test_111_ac2_maven_parent_pins_spring_boot_and_java(repo_root):
    pom = ElementTree.parse(repo_root / "pom.xml").getroot()

    assert pom.findtext(f"{MAVEN}packaging") == "pom"
    assert pom.findtext(f"{MAVEN}parent/{MAVEN}artifactId") == "spring-boot-starter-parent"
    assert pom.findtext(f"{MAVEN}parent/{MAVEN}version") == readme_pins(repo_root)["Spring Boot"]
    assert pom.findtext(f"{MAVEN}properties/{MAVEN}java.version") == pinned(repo_root, ".java-version").split(".")[0]


def test_each_java_module_joins_the_build_when_its_folder_has_a_pom(repo_root):
    pom = ElementTree.parse(repo_root / "pom.xml").getroot()
    activations = {
        profile.findtext(f"{MAVEN}activation/{MAVEN}file/{MAVEN}exists"): profile.findtext(
            f"{MAVEN}modules/{MAVEN}module"
        )
        for profile in pom.iter(f"{MAVEN}profile")
    }

    for module in JAVA_MODULES:
        assert activations.get(f"${{project.basedir}}/{module}/pom.xml") == module


def test_111_ac2_maven_wrapper_pins_maven(repo_root):
    properties = (repo_root / ".mvn/wrapper/maven-wrapper.properties").read_text(encoding="utf-8")

    assert f"apache-maven-{readme_pins(repo_root)['Maven']}-bin.zip" in properties
    assert (repo_root / "mvnw").stat().st_mode & 0o111


def test_111_ac2_empty_java_build_succeeds(repo_root):
    result = subprocess.run(
        ["./mvnw", "-B", "-q", "-ntp", "verify"], cwd=repo_root, check=False, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac2_npm_workspace_is_locked_and_pinned(repo_root):
    manifest = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((repo_root / "package-lock.json").read_text(encoding="utf-8"))

    assert manifest["private"] is True
    assert manifest["workspaces"] == ["apps/*", "packages/*"]
    assert manifest["engines"]["node"] == pinned(repo_root, ".nvmrc")
    assert manifest["packageManager"] == f"npm@{readme_pins(repo_root)['npm']}"
    assert lock["name"] == manifest["name"]
    assert lock["lockfileVersion"] == 3


def test_python_projects_pin_the_same_python(repo_root):
    tools_project = (repo_root / "tools/pyproject.toml").read_text(encoding="utf-8")
    minor = ".".join(pinned(repo_root, ".python-version").split(".")[:2])

    assert f'requires-python = "=={minor}.*"' in tools_project
    assert (repo_root / "tools/uv.lock").exists()


def test_editor_and_ignore_files(repo_root):
    editorconfig = (repo_root / ".editorconfig").read_text(encoding="utf-8")
    ignored = (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "root = true" in editorconfig
    for pattern in ["target/", "node_modules/", ".venv/", "test-results/", "playwright-report/"]:
        assert pattern in ignored


@pytest.mark.parametrize("target", MAKE_TARGETS)
def test_111_ac2_make_target_calls_a_script(repo_root, target):
    result = subprocess.run(
        ["make", "-n", target, "S=111-B1"], cwd=repo_root, check=False, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr
    assert re.search(r"(tools|deploy/scripts)/[\w.-]+", result.stdout), result.stdout


@pytest.mark.parametrize("target", QUALITY_TARGETS)
def test_111_ac2_quality_target_without_its_script_fails(repo_root, tmp_path, target):
    (tmp_path / "Makefile").write_text((repo_root / "Makefile").read_text(encoding="utf-8"), encoding="utf-8")

    result = subprocess.run(["make", "-s", target], cwd=tmp_path, check=False, capture_output=True, text=True)

    assert result.returncode != 0
    assert f"tools/{target} does not exist" in result.stderr


STUB = """#!/usr/bin/env bash
echo "$(basename "$0") $*" >> "$STUB_LOG"
[ "$(basename "$0")" != "$FAILING_TOOL" ]
"""


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
def test_111_ac2_quality_target_checks_the_three_languages(stubbed_repo, target, java, typescript, python):
    result, calls = run_stubbed(stubbed_repo, target)

    assert result.returncode == 0, result.stdout + result.stderr
    assert java in calls
    assert typescript in calls
    assert any(line.startswith("uv run --project tools --frozen") and python in line for line in calls.splitlines())


@pytest.mark.parametrize("target", QUALITY_TARGETS)
@pytest.mark.parametrize("failing_tool", ["mvnw", "npm", "uv"])
def test_111_ac2_quality_target_fails_when_one_language_fails(stubbed_repo, target, failing_tool):
    result, _ = run_stubbed(stubbed_repo, target, failing_tool)

    assert result.returncode != 0


def test_make_suite_runs_the_suite_runner(repo_root):
    result = subprocess.run(
        ["make", "-n", "suite", "S=111-B1"], cwd=repo_root, check=False, capture_output=True, text=True
    )

    assert "tools/suite 111-B1" in result.stdout
