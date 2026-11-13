"""Python tooling in the root configuration (T1.9; 111-FR17, 111-FR23, 111-AC17, 111-AC23, 111-FR2, 111-AC2; OD-21).

Each tool is proven on a fixture of tests/fixtures/python that must fail, and on a clean fixture and the
repository, which must pass. `service` is a uv project with the layout of `services/ai-document` (`app.api`,
`app.domain`, `app.adapters`, the composition root `app.main`); an overlay adds the files of one case to it.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1c

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).parent / "fixtures/python"
SERVICE = Path("services/ai-document")
ROOT_CONFIGURATION = ["ruff.toml", "mypy.ini", ".importlinter", "tdd-profile.yaml"]
QUALITY_CHECKS = ["lint", "format-check", "typecheck", "test"]

# (ruff fixture, the rule code ruff reports): the rule sets and the three size rules (SA-4-2, SA-2.3-1 to SA-2.3-5)
RUFF_RULES = [
    ("E", "E722"),
    ("F", "F401"),
    ("B", "B006"),
    ("N", "N802"),
    ("C90", "C901"),
    ("SIM", "SIM103"),
    ("UP", "UP045"),
    ("I", "I001"),
    ("PLR0913", "PLR0913"),
    ("PLR0915", "PLR0915"),
    ("PLR1702", "PLR1702"),
]

# (overlay, the import-linter contract that breaks) (conventions section 6)
IMPORT_CONTRACTS = [
    ("ar-p2-domain-imports-api", "AR-P2"),
    ("ar-p2-domain-imports-adapters", "AR-P2"),
    ("ar-p2-api-imports-adapters", "AR-P2"),
    ("ar-p3-driver-outside-adapters", "AR-P3"),
    ("ar-p3-other-database-client", "AR-P3"),
    ("ar-p4-keycloak", "AR-P4"),
    ("ar-p4-token-outside-identity", "AR-P4"),
    ("ar-p5-pydantic-in-domain", "AR-P5"),
]


def tools_run(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    """Run a Python tool from the environment of the tools project."""
    command = ["uv", "run", "--quiet", "--project", str(REPO_ROOT / "tools"), "--frozen", *args]
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def build_service(target: Path, *overlays: str) -> Path:
    """The fixture service at `target`, with the files of each overlay laid over it."""
    shutil.copytree(FIXTURES / "service", target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    for overlay in overlays:
        shutil.copytree(FIXTURES / "overlays" / overlay, target, dirs_exist_ok=True)
    return target


def ruff_codes(folder: Path) -> list[str]:
    result = tools_run(
        "ruff", "check", "--config", str(REPO_ROOT / "ruff.toml"), "--no-cache", "--output-format", "json", str(folder)
    )
    return [finding["code"] for finding in json.loads(result.stdout or "[]")]


@pytest.fixture
def python_repo(tmp_path):
    """A repository with the root configuration, the quality script, the tools project and the fixture service."""
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    for name in ROOT_CONFIGURATION:
        shutil.copy2(REPO_ROOT / name, repo / name)
    for name in ["quality", "pyproject.toml", "uv.lock"]:
        shutil.copy2(REPO_ROOT / "tools" / name, repo / "tools" / name)
    return repo


def quality(repo: Path, check: str) -> subprocess.CompletedProcess[str]:
    outer = {name: setting for name, setting in os.environ.items() if name != "VIRTUAL_ENV"}
    return subprocess.run(
        [str(repo / "tools/quality"), check, "python"], cwd=repo, check=False, capture_output=True, text=True, env=outer
    )


def test_111_ac23_ruff_format_fails_an_unformatted_module(tmp_path):
    shutil.copytree(FIXTURES / "ruff/format", tmp_path / "format")
    shutil.copytree(FIXTURES / "ruff/clean", tmp_path / "clean")

    unformatted = tools_run(
        "ruff", "format", "--check", "--config", str(REPO_ROOT / "ruff.toml"), str(tmp_path / "format")
    )
    formatted = tools_run(
        "ruff", "format", "--check", "--config", str(REPO_ROOT / "ruff.toml"), str(tmp_path / "clean")
    )

    assert unformatted.returncode != 0
    assert "would be reformatted" in unformatted.stdout + unformatted.stderr
    assert formatted.returncode == 0, formatted.stdout + formatted.stderr


@pytest.mark.parametrize(("case", "code"), RUFF_RULES)
def test_111_ac23_ruff_lint_fails_each_rule_set_and_size_limit(tmp_path, case, code):
    shutil.copytree(FIXTURES / "ruff" / case, tmp_path / case)

    assert code in ruff_codes(tmp_path / case)


def test_111_ac23_ruff_lint_passes_the_clean_module(tmp_path):
    shutil.copytree(FIXTURES / "ruff/clean", tmp_path / "clean")

    assert ruff_codes(tmp_path / "clean") == []


def test_111_ac23_mypy_is_strict_in_the_root_configuration(tmp_path):
    shutil.copytree(FIXTURES / "mypy", tmp_path / "mypy")

    untyped = tools_run("mypy", "--config-file", str(REPO_ROOT / "mypy.ini"), str(tmp_path / "mypy/untyped"))
    typed = tools_run("mypy", "--config-file", str(REPO_ROOT / "mypy.ini"), str(tmp_path / "mypy/clean"))

    assert untyped.returncode != 0
    assert "[no-untyped-def]" in untyped.stdout
    assert typed.returncode == 0, typed.stdout


def lint_imports(service: Path) -> subprocess.CompletedProcess[str]:
    return tools_run("lint-imports", "--config", str(REPO_ROOT / ".importlinter"), "--no-cache", cwd=service)


def test_111_ac17_import_contracts_keep_the_clean_service(tmp_path):
    result = lint_imports(build_service(tmp_path / "service"))

    assert result.returncode == 0, result.stdout + result.stderr
    for contract in ["AR-P2", "AR-P3", "AR-P4", "AR-P5"]:
        assert contract in result.stdout


@pytest.mark.parametrize(("overlay", "contract"), IMPORT_CONTRACTS)
def test_111_ac17_import_contract_breaks_on_its_fixture(tmp_path, overlay, contract):
    result = lint_imports(build_service(tmp_path / "service", overlay))

    assert result.returncode != 0
    broken = [line for line in result.stdout.splitlines() if " BROKEN" in line]
    assert [line for line in broken if line.startswith(contract)], result.stdout


def grain_violations(package: Path) -> list[str]:
    result = tools_run("python", str(REPO_ROOT / "tools/python_architecture.py"), str(package))
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_111_ac17_ar_p1_a_model_with_an_obligation_id_but_no_regulation_version_fails(tmp_path):
    service = build_service(tmp_path / "service", "ar-p1-grain")

    assert grain_violations(service / "app") == [
        "app/domain/obligation_gap.py: ObligationGap has obligation_id without regulation_version (AR-P1)"
    ]


def test_111_ac17_ar_p1_the_clean_service_keeps_the_grain(tmp_path):
    service = build_service(tmp_path / "service")

    assert grain_violations(service / "app") == []


def test_111_ac17_ar_p1_every_python_model_of_the_repository_keeps_the_grain():
    packages = sorted(path for path in (REPO_ROOT / "services").glob("*/app") if path.is_dir())

    for package in packages:
        assert grain_violations(package) == [], package


def test_111_ac23_lint_runs_the_import_contracts_on_a_python_service(python_repo):
    build_service(python_repo / SERVICE)
    clean = quality(python_repo, "lint")
    shutil.copytree(FIXTURES / "overlays/ar-p5-pydantic-in-domain", python_repo / SERVICE, dirs_exist_ok=True)
    broken = quality(python_repo, "lint")

    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "lint-imports" in clean.stdout
    assert broken.returncode != 0
    assert "AR-P5" in broken.stdout


def test_111_ac23_test_reports_coverage_and_passes_an_empty_test_run(python_repo):
    build_service(python_repo / SERVICE, "mutation-domain", "mutation-weak-test")

    result = quality(python_repo, "test")

    assert result.returncode == 0, result.stdout + result.stderr
    report = python_repo / "coverage/python/ai-document.xml"
    assert report.exists(), result.stdout
    assert "notice_period.py" in report.read_text(encoding="utf-8")


def test_111_ac23_test_passes_a_service_without_tests(python_repo):
    build_service(python_repo / SERVICE)

    result = quality(python_repo, "test")

    assert result.returncode == 0, result.stdout + result.stderr


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", message)


@pytest.fixture
def service_repo(python_repo):
    """The python repository with the fixture service committed as the base of a change."""
    build_service(python_repo / SERVICE)
    git(python_repo, "init", "-q", "-b", "main")
    commit(python_repo, "base")
    return python_repo


def mutation_gate(repo: Path, *overlays: str) -> subprocess.CompletedProcess[str]:
    for overlay in overlays:
        shutil.copytree(FIXTURES / "overlays" / overlay, repo / SERVICE, dirs_exist_ok=True)
    commit(repo, "change")
    outer = {name: setting for name, setting in os.environ.items() if name != "VIRTUAL_ENV"}
    return subprocess.run(
        [str(REPO_ROOT / "tools/python-mutation-gate"), "--root", str(repo), "--base", "HEAD~1"],
        check=False,
        capture_output=True,
        text=True,
        env=outer,
    )


def test_111_ac23_mutmut_gate_fails_a_domain_change_whose_mutants_survive(service_repo):
    result = mutation_gate(service_repo, "mutation-domain", "mutation-weak-test")

    assert result.returncode != 0, result.stdout + result.stderr
    assert "app/domain/notice_period.py" in result.stdout
    assert "below the threshold of 70 percent" in result.stdout


def test_111_ac23_mutmut_gate_passes_a_domain_change_whose_mutants_are_killed(service_repo):
    result = mutation_gate(service_repo, "mutation-domain", "mutation-strong-test")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "domain and application:" in result.stdout


def test_111_ac23_mutmut_gate_reports_an_adapter_change_without_failing(service_repo):
    result = mutation_gate(service_repo, "mutation-adapter", "mutation-adapter-test")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "app/adapters/notice_store.py" in result.stdout
    assert "adapters (reported only):" in result.stdout


def test_111_ac23_mutmut_gate_passes_when_no_python_module_changed(service_repo):
    (service_repo / "README.md").write_text("no Python change\n", encoding="utf-8")

    result = mutation_gate(service_repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "no changed Python module" in result.stdout


@pytest.mark.parametrize("check", ["lint", "format-check", "typecheck"])
def test_111_ac2_the_python_checks_pass_on_the_repository(check):
    outer = {name: setting for name, setting in os.environ.items() if name != "VIRTUAL_ENV"}
    result = subprocess.run(
        [str(REPO_ROOT / "tools/quality"), check, "python"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=outer,
    )

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture
def workflow():
    return yaml.safe_load((REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))


def run_lines(job) -> list[str]:
    return [line.strip() for step in job["steps"] for line in str(step.get("run", "")).splitlines() if line.strip()]


def test_111_ac2_the_python_ci_jobs_are_required(workflow):
    python = workflow["jobs"]["python"]
    mutation = workflow["jobs"]["python-mutation"]

    assert {f"tools/quality {check} python" for check in QUALITY_CHECKS} <= set(run_lines(python))
    assert any(line.startswith("tools/python-mutation-gate --base") for line in run_lines(mutation))
    assert {"python", "python-mutation"} <= set(workflow["jobs"]["required"]["needs"])


def test_111_ac23_pre_commit_runs_the_python_format_check_and_lint():
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    entries = {hook["entry"] for repo in config["repos"] for hook in repo["hooks"]}

    assert {"tools/quality format-check python", "tools/quality lint python"} <= entries


def test_111_ac23_suite_111_b1c_is_registered_for_the_root_tests():
    registry = yaml.safe_load((REPO_ROOT / "suites.yaml").read_text(encoding="utf-8"))

    assert {
        "id": "111-B1c",
        "runner": "pytest",
        "selector": "suite_111_B1c",
        "project": "tools",
        "paths": ["tests"],
    } in (registry["suites"])
