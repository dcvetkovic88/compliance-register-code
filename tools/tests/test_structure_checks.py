"""tools/check-language, tools/check-sql-schemas and tools/check-size (T1.12; 111-FR17, 111-FR23, 111-AC17, 111-AC23).

Each check is proven on a violating fixture of tools/tests/fixtures/structure, passes on its clean fixture and on
the repository, and runs in `make lint`. The language rule and the own-schema rule are suite readiness rules 6
and 3 (conventions section 6); the module length is SA-2.3-2.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from conftest import FIXTURES_DIR, TOOLS_DIR, run_tool

pytestmark = pytest.mark.suite_111_B1c

REPO_ROOT = TOOLS_DIR.parent
STRUCTURE = FIXTURES_DIR / "structure"
MIGRATIONS = "src/main/resources/db/migration"
JAVA_OUT = "src/main/java/com/wisertech/register/adapters/out"

# (fixture, the file the check names) for the language rule (suite readiness rule 6)
LANGUAGE_VIOLATIONS = [
    ("python-in-a-java-service", "services/register/scripts/load_arrangements.py"),
    ("python-in-the-web", "apps/web/scripts/build_catalog.py"),
    ("python-in-a-library", "libs/eventbus/eventbus.py"),
    ("java-in-the-web", "apps/web/src/Bridge.java"),
    ("java-in-the-tools", "tools/codegen/Generator.java"),
    ("java-in-the-python-service", "services/ai-document/src/main/java/Parser.java"),
]

# (fixture, what the check names) for the own-schema rule (suite readiness rule 3)
SQL_VIOLATIONS = [
    ("other-service-schema", f"services/register/{MIGRATIONS}/V0002__read_assessments.sql:2: ictrisk.assessments"),
    ("quoted-schema", f"services/register/{MIGRATIONS}/V0002__read_assessments.sql:1: ictrisk.assessments"),
    ("platform-table", f"services/register/{MIGRATIONS}/V0002__read_outbox.sql:1: platform.outbox"),
    ("platform-table-beside-an-alias", f"services/register/{MIGRATIONS}/V0002__read_outbox.sql:1: platform.outbox"),
    ("unlisted-platform-function", f"services/monitoring/{MIGRATIONS}/V0002__reset.sql:1: platform.reset_offsets"),
    ("bff-platform-function", f"services/bff/{MIGRATIONS}/V0001__create_sessions.sql:1: platform.current_user_id"),
    ("search-path", f"services/register/{MIGRATIONS}/V0002__read_assessments.sql:1: search_path ictrisk"),
    ("search-path-set-config", f"services/register/{MIGRATIONS}/V0002__read_assessments.sql:1: search_path ictrisk"),
    ("set-schema", f"services/register/{MIGRATIONS}/V0002__read_assessments.sql:1: search_path ictrisk"),
    ("java-string", f"services/register/{JAVA_OUT}/AssessmentReader.java:13: ictrisk.assessments"),
    ("python-string", "services/ai-document/app/arrangements.py:10: register.arrangements"),
    ("java-concatenation", f"services/register/{JAVA_OUT}/AssessmentReader.java:13: ictrisk.assessments"),
    ("python-concatenation", "services/ai-document/app/arrangements.py:7: register.arrangements"),
    (
        "single-quoted-function-body",
        f"services/register/{MIGRATIONS}/V0002__count_assessments.sql:2: ictrisk.assessments",
    ),
    ("unlisted-schema", f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:1: unlisted_schema.secrets"),
    ("unlisted-schema-in-a-list", f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:2: unlisted_schema.secrets"),
    ("unlisted-schema-function", f"services/register/{MIGRATIONS}/V0002__leak.sql:1: unlisted_schema.leak"),
    (
        "unlisted-schema-also-a-column",
        f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:1: unlisted_schema.secrets",
    ),
    (
        "unlisted-schema-parenthesized-only",
        f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:1: unlisted_schema.secrets",
    ),
    (
        "unlisted-schema-parenthesized-join",
        f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:1: unlisted_schema.secrets",
    ),
    (
        "unlisted-schema-parenthesized-list",
        f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:1: unlisted_schema.secrets",
    ),
    (
        "unlisted-schema-parenthesized-after-a-table",
        f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:1: unlisted_schema.secrets",
    ),
    ("function-search-path", f"services/register/{MIGRATIONS}/V0002__count.sql:1: search_path ictrisk"),
    ("grant-on-schema", f"services/register/{MIGRATIONS}/V0002__grant_assessments.sql:1: schema ictrisk"),
    ("create-schema", f"services/register/{MIGRATIONS}/V0002__create_schema.sql:1: schema ictrisk"),
    ("schema-list", f"services/register/{MIGRATIONS}/V0002__drop_schemas.sql:2: schema unlisted_schema"),
    (
        "search-path-unlisted-schema",
        f"services/register/{MIGRATIONS}/V0002__read_secrets.sql:1: search_path unlisted_schema",
    ),
]


def check(name: str, root: Path) -> subprocess.CompletedProcess[str]:
    return run_tool(name, "--root", str(root))


@pytest.mark.parametrize(("case", "path"), LANGUAGE_VIOLATIONS)
def test_111_ac17_check_language_fails_code_outside_its_language_paths(case, path):
    result = check("check-language", STRUCTURE / "language" / case)

    assert result.returncode != 0
    assert path in result.stdout


def test_111_ac17_check_language_passes_each_language_in_its_paths():
    result = check("check-language", STRUCTURE / "language/clean")

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(("case", "finding"), SQL_VIOLATIONS)
def test_111_ac17_check_sql_schemas_fails_sql_naming_another_schema(case, finding):
    result = check("check-sql-schemas", STRUCTURE / "sql" / case)

    assert result.returncode != 0
    assert finding in result.stdout


def test_111_ac17_check_sql_schemas_passes_the_own_schema_and_the_listed_platform_functions():
    result = check("check-sql-schemas", STRUCTURE / "sql/clean")

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac23_check_size_fails_a_python_module_over_300_lines():
    result = check("check-size", STRUCTURE / "size/too-long")

    assert result.returncode != 0
    assert "services/ai-document/app/limits.py: 301 lines" in result.stdout


def test_111_ac23_check_size_passes_a_python_module_of_300_lines():
    result = check("check-size", STRUCTURE / "size/clean")

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", ["check-language", "check-sql-schemas", "check-size"])
def test_111_ac23_the_structure_check_passes_on_the_repository(name):
    result = check(name, REPO_ROOT)

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture
def lint_repo(tmp_path):
    """A repository with the quality script, the structure checks, a Java build whose tools are stubs, no npm
    workspace and no uv project but the tools project."""
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    for name in ["quality", "check-language", "check-sql-schemas", "check-size", "structure_checks.py"]:
        shutil.copy2(TOOLS_DIR / name, repo / "tools" / name)
    for name in ["sql-schemas.yaml", "pyproject.toml", "uv.lock"]:
        shutil.copy2(TOOLS_DIR / name, repo / "tools" / name)
    plugins = "".join(
        f"<plugin><artifactId>{tool}</artifactId></plugin>" for tool in ["maven-checkstyle-plugin", "maven-pmd-plugin"]
    )
    (repo / "pom.xml").write_text(f"<project><build><plugins>{plugins}</plugins></build></project>\n", encoding="utf-8")
    (repo / "mvnw").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (repo / "mvnw").chmod(0o755)
    return repo


def lint_java(repo: Path) -> subprocess.CompletedProcess[str]:
    outer = {name: setting for name, setting in os.environ.items() if name != "VIRTUAL_ENV"}
    return subprocess.run(
        [str(repo / "tools/quality"), "lint", "java"], cwd=repo, check=False, capture_output=True, text=True, env=outer
    )


def test_111_ac17_make_lint_runs_the_structure_checks(lint_repo):
    clean = lint_java(lint_repo)
    shutil.copytree(STRUCTURE / "language/java-in-the-web", lint_repo, dirs_exist_ok=True)
    shutil.copytree(STRUCTURE / "sql/platform-table", lint_repo, dirs_exist_ok=True)
    shutil.copytree(STRUCTURE / "size/too-long", lint_repo, dirs_exist_ok=True)
    broken = lint_java(lint_repo)

    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert broken.returncode != 0
    assert "apps/web/src/Bridge.java" in broken.stdout
    assert "platform.outbox" in broken.stdout
    assert "limits.py: 301 lines" in broken.stdout


def test_111_ac17_every_ci_job_that_lints_sets_up_the_pinned_uv():
    """Lint runs the structure checks, which run on uv, so a CI job that lints sets up the uv of .uv-version."""
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    linting = {
        name: job["steps"]
        for name, job in workflow["jobs"].items()
        if any(
            "tools/quality lint" in str(step.get("run", "")) or "make lint" in str(step.get("run", ""))
            for step in job["steps"]
        )
    }

    assert {"java", "typescript", "python", "quality"} <= set(linting)
    for name, steps in linting.items():
        setups = [step for step in steps if str(step.get("uses", "")).startswith("astral-sh/setup-uv@")]
        assert setups, f"{name} lints without setting up uv"
        assert setups[0].get("with", {}).get("version") == "${{ steps.pins.outputs.uv }}", name
        assert any(step.get("id") == "pins" and ".uv-version" in str(step.get("run", "")) for step in steps), name


def test_111_ac23_suite_111_b1c_is_registered_for_the_tools_tests():
    registry = (TOOLS_DIR / "suites.yaml").read_text(encoding="utf-8")

    assert "  - id: 111-B1c\n    runner: pytest\n    selector: suite_111_B1c\n" in registry
