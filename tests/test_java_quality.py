"""Java format, lint and null checks of the parent build (T1.5; 111-FR23, 111-AC23, 111-FR2, 111-AC2; OD-21).

Each tool is proven on a fixture of tests/fixtures/java that must fail, and on the clean fixture and the
repository, which must pass. A fixture is one module whose parent is the repository's pom.xml.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1b

FIXTURES = Path(__file__).parent / "fixtures/java"
QUALITY_CHECKS = ["lint", "format-check", "typecheck", "test"]
LINT = ["verify", "-DskipTests"]
FORMAT_CHECK = ["validate"]
TYPECHECK = ["test-compile"]

# What the driver check (OD-26) names when a runtime dependency registers a driver other than PostgreSQL's.
DRIVER_CHECK = "registers a JDBC driver other than org.postgresql.Driver (OD-26)"

# (fixture, the goals of the make target that runs the tool, what the failing build names)
VIOLATIONS = [
    ("format", FORMAT_CHECK, "spotless"),
    ("method-name", LINT, "MethodName"),
    ("package-name", LINT, "must be lowercase without underscores (SA-1.1-4)"),
    ("class-suffix", LINT, "banned generic suffix"),
    ("todo", LINT, "names its issue, as TODO(#123) (SA-2.7-2)"),
    ("port-doc", LINT, "Missing a Javadoc comment for 'EvidencePort'"),
    ("definition-source-doc", LINT, "Missing a Javadoc comment for 'DefinitionSource'"),
    ("model-gateway-doc", LINT, "Missing a Javadoc comment for 'ModelGateway'"),
    ("adapter-doc", LINT, "Missing a Javadoc comment for 'ArrangementController'"),
    ("package-private-adapter-doc", LINT, "Missing a Javadoc comment for 'ArrangementRows'"),
    ("method-length", LINT, "Rule:MethodLength"),
    ("class-length", LINT, "Rule:ClassLength"),
    ("parameters", LINT, "Rule:ExcessiveParameterList"),
    ("nesting", LINT, "Rule:NestingDepth"),
    ("nesting-unbraced", LINT, "Rule:NestingDepth"),
    ("complexity", LINT, "Rule:CyclomaticComplexity"),
    ("unused-parameter", LINT, "Rule:UnusedFormalParameter"),
    ("system-out", LINT, "Rule:SystemPrintln"),
    ("nullaway", TYPECHECK, "[NullAway]"),
    ("error-prone", TYPECHECK, "[DeadException]"),
    ("lombok", FORMAT_CHECK, "Lombok is banned"),
    ("mysql-driver", FORMAT_CHECK, "The only database driver is PostgreSQL's"),
    ("duckdb-driver", LINT, DRIVER_CHECK),
    ("other-service", FORMAT_CHECK, "A service never depends on another service"),
]


def build_fixture(repo_root: Path, tmp_path: Path, case: str, goals: list[str]) -> subprocess.CompletedProcess[str]:
    """Build one fixture as a module of the repository's parent pom and return the Maven run."""
    module = tmp_path / case
    source = FIXTURES / case
    if (source / "src").exists():
        shutil.copytree(source / "src", module / "src")
    module.mkdir(exist_ok=True)
    dependencies = source / "dependencies.xml"
    pom = (
        (FIXTURES / "pom.xml")
        .read_text(encoding="utf-8")
        .replace("@PARENT_POM@", os.path.relpath(repo_root / "pom.xml", module.resolve()))
        .replace("@ROOT@", str(repo_root))
        .replace("@CASE@", case)
        .replace("@DEPENDENCIES@", dependencies.read_text(encoding="utf-8") if dependencies.exists() else "")
    )
    (module / "pom.xml").write_text(pom, encoding="utf-8")
    return subprocess.run(
        ["./mvnw", "-B", "-ntp", "-f", str(module / "pom.xml"), *goals],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(("case", "goals", "message"), VIOLATIONS, ids=[case for case, _, _ in VIOLATIONS])
def test_111_ac23_java_tool_fails_the_build_on_its_fixture(repo_root, tmp_path, case, goals, message):
    result = build_fixture(repo_root, tmp_path, case, goals)

    assert result.returncode != 0, f"{case} passed the build"
    assert message in result.stdout + result.stderr, (result.stdout + result.stderr)[-4000:]


@pytest.mark.parametrize("case", ["mysql-driver", "duckdb-driver"])
def test_111_ac23_driver_check_fails_on_any_driver_but_postgresql_without_the_group_bans(repo_root, tmp_path, case):
    result = build_fixture(repo_root, tmp_path, case, [*LINT, "-Denforcer.skip=true"])

    assert result.returncode != 0, f"{case} passed the driver check"
    assert DRIVER_CHECK in result.stdout + result.stderr, (result.stdout + result.stderr)[-4000:]


def test_111_ac23_driver_check_passes_the_postgresql_driver(repo_root, tmp_path):
    result = build_fixture(repo_root, tmp_path, "postgresql-driver", LINT)

    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]


@pytest.mark.parametrize("goals", [FORMAT_CHECK, TYPECHECK, LINT, ["test"]], ids=["format-check", "typecheck", "lint", "test"])
def test_111_ac23_clean_fixture_at_the_size_limits_passes_every_java_tool(repo_root, tmp_path, goals):
    result = build_fixture(repo_root, tmp_path, "clean", goals)

    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]


@pytest.mark.parametrize("check", QUALITY_CHECKS)
def test_111_ac2_java_quality_check_passes_on_the_repository(repo_root, check):
    result = subprocess.run(
        [str(repo_root / "tools/quality"), check, "java"], cwd=repo_root, check=False, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "./mvnw" in result.stdout


STUB = """#!/usr/bin/env bash
echo "$(basename "$0") $*" >> "$STUB_LOG"
"""


@pytest.mark.parametrize("check", QUALITY_CHECKS)
def test_111_ac2_java_quality_check_runs_without_the_tools_of_block_1c(repo_root, tmp_path, check):
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    for name in ["pom.xml", "package.json", "tools/quality"]:
        shutil.copy2(repo_root / name, repo / name)
    (repo / "tools/pyproject.toml").write_text("[project]\nname = 'tools'\n", encoding="utf-8")
    (repo / "mvnw").write_text(STUB, encoding="utf-8")
    (repo / "mvnw").chmod(0o755)
    log = tmp_path / "calls.log"

    result = subprocess.run(
        ["tools/quality", check, "java"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "STUB_LOG": str(log)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert [line.split()[0] for line in log.read_text(encoding="utf-8").splitlines()] == ["mvnw"]


def test_111_ac2_java_quality_job_is_required(repo_root):
    workflow = yaml.safe_load((repo_root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    java = workflow["jobs"]["java"]
    lines = [line.strip() for step in java["steps"] for line in str(step.get("run", "")).splitlines()]

    assert [f"tools/quality {check} java" for check in QUALITY_CHECKS] == [
        line for line in lines if line.startswith("tools/quality")
    ]
    assert "java" in workflow["jobs"]["required"]["needs"]


def test_shared_tool_configuration_is_at_the_root(repo_root):
    pom = (repo_root / "pom.xml").read_text(encoding="utf-8")

    assert "${register.root}/config/java/checkstyle.xml" in pom
    assert "${register.root}/config/java/pmd.xml" in pom
    assert (repo_root / "config/java/checkstyle.xml").is_file()
    assert (repo_root / "config/java/pmd.xml").is_file()
