"""TypeScript tooling in the root configuration (T1.10; 111-FR17, 111-FR23, 111-AC17, 111-AC23, 111-FR2, 111-AC2).

Each tool is proven on a fixture of tests/fixtures/typescript that must fail, and on a clean fixture, which must
pass. A fixture is copied to a temporary folder that links the repository's node_modules, so the tools and the
root configuration are the ones every workspace uses.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1c

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).parent / "fixtures/typescript"
BIN = REPO_ROOT / "node_modules/.bin"
QUALITY_CHECKS = ["lint", "format-check", "typecheck", "test"]
ROOT_CONFIGURATION = [
    "package.json",
    ".gitignore",
    ".prettierrc.json",
    ".prettierignore",
    "eslint.config.mjs",
    "tsconfig.base.json",
    "vitest.shared.mjs",
    ".dependency-cruiser.cjs",
]

# (ESLint fixture, the rule that fails it) (SA-1.1, folders kebab-case and files PascalCase.tsx or kebab-case.ts
# by SA-1.1-4 and SA-1.1-5, SA-1.3-4, SA-2.2-5, SA-2.3-1 to SA-2.3-5, SA-2.6-1 to SA-2.6-4;
# AR-W2: fetch is called only by the generated clients of apps/web/src/api, so no local fetch wrapper exists)
ESLINT_RULES = [
    ("naming", "@typescript-eslint/naming-convention"),
    ("boolean-question", "@typescript-eslint/naming-convention"),
    ("react-hooks", "react-hooks/rules-of-hooks"),
    ("jsx-a11y", "jsx-a11y/alt-text"),
    ("class-component", "no-restricted-syntax"),
    ("jsx-literal", "react/jsx-no-literals"),
    ("jsx-literal-prop", "register/no-literal-user-facing-props"),
    ("jsx-literal-alt", "register/no-literal-user-facing-props"),
    ("jsx-literal-template-prop", "register/no-literal-user-facing-props"),
    ("unused-parameter", "@typescript-eslint/no-unused-vars"),
    ("max-params", "max-params"),
    ("max-depth", "max-depth"),
    ("complexity", "complexity"),
    ("max-lines-per-function", "max-lines-per-function"),
    ("max-lines", "max-lines"),
    ("fetch-wrapper", "no-restricted-globals"),
    ("component-file-name", "register/file-and-folder-names"),
    ("module-file-name", "register/file-and-folder-names"),
    ("folder-name", "register/file-and-folder-names"),
]

# (dependency-cruiser fixture, the rule that fails it) (conventions section 6; components are PascalCase.tsx, SA-1.1-5)
DEPENDENCY_RULES = [
    ("ar-w2", "AR-W2-http-library-outside-the-clients"),
    ("ar-w3-database", "AR-W3-database-client"),
    ("ar-w3-services", "AR-W3-services-and-libraries"),
    ("ar-w4", "AR-W4-identity-library"),
    ("ar-w4-token", "AR-W4-identity-library"),
    ("ar-w5-kit", "AR-W5-component-kit-outside-the-shell"),
    ("ar-w5-shell-imports-web", "AR-W5-shell-imports-the-web"),
    ("ar-w5-feature", "AR-W5-feature-imports-another-feature"),
    ("ar-w5-shell-module", "AR-W5-shell-module-outside-the-shell"),
    ("ar-w5-shell-module-pascal", "AR-W5-shell-module-outside-the-shell"),
    ("ar-w5-shell-module-package", "AR-W5-shell-module-outside-the-shell"),
    ("ar-w5-shell-module-isolated", "AR-W5-shell-module-outside-the-shell-isolated"),
    ("ar-w7", "AR-W7-component-imports-a-client"),
    ("ar-w7-package", "AR-W7-component-imports-a-client"),
]


def project(target: Path, *sources: Path) -> Path:
    """A folder with the sources laid over each other and the repository's node_modules linked."""
    target.mkdir(parents=True)
    for source in sources:
        shutil.copytree(source, target, dirs_exist_ok=True)
    (target / "node_modules").symlink_to(REPO_ROOT / "node_modules", target_is_directory=True)
    return target


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def test_111_ac23_prettier_fails_an_unformatted_file(tmp_path):
    config = ["--config", str(REPO_ROOT / ".prettierrc.json")]
    unformatted = project(tmp_path / "unformatted", FIXTURES / "prettier/unformatted")
    clean = project(tmp_path / "clean", FIXTURES / "prettier/clean")

    failing = run([str(BIN / "prettier"), "--check", *config, "notice-period.ts"], unformatted)
    passing = run([str(BIN / "prettier"), "--check", *config, "notice-period.ts"], clean)

    assert failing.returncode != 0
    assert "notice-period.ts" in failing.stdout + failing.stderr
    assert passing.returncode == 0, passing.stdout + passing.stderr


def eslint_rules(tmp_path: Path, case: str) -> list[str]:
    folder = project(tmp_path / case)
    shutil.copytree(FIXTURES / "eslint" / case, folder / "src")
    tsconfig = {"extends": str(REPO_ROOT / "tsconfig.base.json"), "include": ["src"]}
    (folder / "tsconfig.json").write_text(json.dumps(tsconfig), encoding="utf-8")
    result = run(
        [str(BIN / "eslint"), "--config", str(REPO_ROOT / "eslint.config.mjs"), "--format", "json", "src"], folder
    )
    assert result.stdout, result.stderr
    return sorted({message["ruleId"] for report in json.loads(result.stdout) for message in report["messages"]})


@pytest.mark.parametrize(("case", "rule"), ESLINT_RULES)
def test_111_ac23_eslint_fails_each_rule_on_its_fixture(tmp_path, case, rule):
    assert eslint_rules(tmp_path, case) == [rule]


def test_111_ac23_eslint_passes_the_clean_component(tmp_path):
    assert eslint_rules(tmp_path, "clean") == []


def test_111_ac23_typescript_is_strict_in_the_root_configuration(tmp_path):
    tsconfig = json.dumps({"extends": str(REPO_ROOT / "tsconfig.base.json"), "include": ["."]})
    results = {}
    for case in ["strict", "clean"]:
        folder = project(tmp_path / case, FIXTURES / "tsc" / case)
        (folder / "tsconfig.json").write_text(tsconfig, encoding="utf-8")
        results[case] = run([str(BIN / "tsc"), "-p", "tsconfig.json"], folder)

    assert results["strict"].returncode != 0
    assert "TS7006" in results["strict"].stdout
    assert results["clean"].returncode == 0, results["clean"].stdout


def cruise(tmp_path: Path, case: str) -> list[str]:
    layers = [FIXTURES / "depcruise/clean"] + ([FIXTURES / "depcruise" / case] if case != "clean" else [])
    folder = project(tmp_path / case, *layers)
    command = [str(BIN / "depcruise"), "--config", str(REPO_ROOT / ".dependency-cruiser.cjs")]
    result = run([*command, "--output-type", "json", "apps", "packages"], folder)
    assert result.stdout, result.stderr
    return sorted({violation["rule"]["name"] for violation in json.loads(result.stdout)["summary"]["violations"]})


@pytest.mark.parametrize(("case", "rule"), DEPENDENCY_RULES)
def test_111_ac17_dependency_rule_fails_on_its_fixture(tmp_path, case, rule):
    assert cruise(tmp_path, case) == [rule]


def test_111_ac17_dependency_rules_pass_the_clean_web(tmp_path):
    assert cruise(tmp_path, "clean") == []


def test_111_ac23_vitest_reports_coverage_and_never_runs_a_browser_spec(tmp_path):
    folder = project(tmp_path / "vitest", FIXTURES / "vitest")

    result = run([str(BIN / "vitest"), "run", "--config", str(REPO_ROOT / "vitest.shared.mjs"), "--root", "."], folder)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "notice-period.e2e.ts" not in result.stdout
    assert (folder / "coverage/cobertura-coverage.xml").exists()


def test_111_ac23_vitest_passes_an_empty_test_run(tmp_path):
    folder = project(tmp_path / "empty", FIXTURES / "prettier/clean")

    result = run([str(BIN / "vitest"), "run", "--config", str(REPO_ROOT / "vitest.shared.mjs"), "--root", "."], folder)

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac23_playwright_runs_only_files_ending_in_e2e_ts(tmp_path):
    folder = project(tmp_path / "playwright", FIXTURES / "playwright")
    shared = (REPO_ROOT / "playwright.shared.mjs").as_posix()
    config = f'import shared from "{shared}";\nexport default {{ ...shared, testDir: "." }};\n'
    (folder / "playwright.config.mjs").write_text(config, encoding="utf-8")

    result = run([str(BIN / "playwright"), "test", "--list"], folder)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "obligations.e2e.ts" in result.stdout
    assert "obligations.spec.ts" not in result.stdout
    assert "obligations.test.ts" not in result.stdout


@pytest.fixture
def web_repo(tmp_path):
    """A repository with the root configuration, the quality script and one workspace, packages/shell."""
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    for name in ROOT_CONFIGURATION:
        shutil.copy2(REPO_ROOT / name, repo / name)
    shutil.copy2(REPO_ROOT / "tools/quality", repo / "tools/quality")
    shutil.copytree(FIXTURES / "workspace", repo, dirs_exist_ok=True)
    (repo / "node_modules").symlink_to(REPO_ROOT / "node_modules", target_is_directory=True)
    return repo


def quality(repo: Path, check: str) -> subprocess.CompletedProcess[str]:
    return run([str(repo / "tools/quality"), check, "typescript"], repo)


@pytest.mark.parametrize("check", QUALITY_CHECKS)
def test_111_ac2_the_typescript_checks_run_the_root_configuration_in_a_workspace(web_repo, check):
    result = quality(web_repo, check)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "@register/fixture-shell" in result.stdout


def test_111_ac2_the_typescript_test_check_reports_coverage(web_repo):
    result = quality(web_repo, "test")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (web_repo / "packages/shell/coverage/cobertura-coverage.xml").exists()


def test_111_ac17_the_typescript_lint_check_runs_the_dependency_rules(web_repo):
    shutil.copytree(FIXTURES / "depcruise/ar-w4-token/packages/shell", web_repo / "packages/shell", dirs_exist_ok=True)

    result = quality(web_repo, "lint")

    assert result.returncode != 0
    assert "AR-W4-identity-library" in result.stdout + result.stderr


@pytest.mark.parametrize("check", QUALITY_CHECKS)
def test_111_ac2_the_typescript_checks_pass_on_the_repository(check):
    result = run([str(REPO_ROOT / "tools/quality"), check, "typescript"], REPO_ROOT)

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac2_the_typescript_and_quality_ci_jobs_are_required():
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["typescript"]["steps"]
    lines = {line.strip() for step in steps for line in str(step.get("run", "")).splitlines()}

    assert {f"tools/quality {check} typescript" for check in QUALITY_CHECKS} <= lines
    assert any("npm ci" in line for line in lines)
    assert {"typescript", "quality"} <= set(workflow["jobs"]["required"]["needs"])


def test_111_ac23_pre_commit_runs_the_typescript_format_check_and_lint():
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    entries = {hook["entry"] for repo in config["repos"] for hook in repo["hooks"]}

    assert {"tools/quality format-check typescript", "tools/quality lint typescript"} <= entries


def test_111_ac23_the_root_typescript_configuration_is_formatted():
    files = [name for name in ROOT_CONFIGURATION if name.endswith((".json", ".mjs", ".cjs"))]
    files.append("playwright.shared.mjs")

    result = run([str(BIN / "prettier"), "--check", *files], REPO_ROOT)

    assert result.returncode == 0, result.stdout + result.stderr
