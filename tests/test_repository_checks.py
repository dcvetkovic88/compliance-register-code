"""Repository checks (T1.8; 111-FR23, 111-AC23; conventions SA-1.2-14, SA-1.2-15, SA-2.3-6, SA-2.3-7, SA-4-8 to SA-4-12).

Each check is proven on a fixture that must fail and passes on the repository: gitleaks, Semgrep, pre-commit,
Renovate, commitlint, the branch name check and the pull request size check.
"""

import json
import os
import random
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1b

FIXTURES = Path(__file__).parent / "fixtures/repository"
PRE_COMMIT = ["uv", "tool", "run", "--from", "pre-commit==4.7.0", "pre-commit"]


def run(command: list[str], cwd: Path, **options) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, **options)


def git(repo: Path, *args: str) -> None:
    identity = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]
    subprocess.run(["git", *identity, *args], cwd=repo, check=True, capture_output=True, text=True)


def test_111_ac23_gitleaks_fails_on_a_secret(repo_root, tmp_path):
    # The fixture's key is made at run time, so the repository never holds one.
    key = "AKIA" + "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567") for _ in range(16))
    (tmp_path / "settings.py").write_text(f'aws_access_key_id = "{key}"\n', encoding="utf-8")

    result = run([str(repo_root / "tools/gitleaks"), str(tmp_path)], repo_root)

    assert result.returncode != 0
    assert "leaks found: 1" in result.stdout + result.stderr


def test_111_ac23_gitleaks_passes_on_the_repository(repo_root):
    result = run([str(repo_root / "tools/gitleaks")], repo_root)

    assert result.returncode == 0, result.stdout + result.stderr


SEMGREP_CASES = [
    ("banned-identifier-java", "banned-identifier"),
    ("banned-identifier-python", "banned-identifier"),
    ("banned-identifier-typescript", "banned-identifier"),
    ("generic-suffix-python", "generic-class-suffix"),
    ("generic-suffix-typescript", "generic-type-suffix"),
    ("secret-in-log-java", "secret-in-log"),
    ("secret-in-log-python", "secret-in-log"),
    ("sleep-java", "sleep-in-java-test"),
    ("sleep-python", "sleep-in-python-test"),
    ("sleep-typescript", "sleep-in-typescript-test"),
    ("todo", "todo-without-issue"),
    ("security", "subprocess-shell-true"),
]


def semgrep_on(repo_root: Path, tmp_path: Path, case: str) -> subprocess.CompletedProcess[str]:
    target = tmp_path / case
    shutil.copytree(FIXTURES / "semgrep" / case, target)
    if (repo_root / ".semgrepignore").exists():
        shutil.copy2(repo_root / ".semgrepignore", target / ".semgrepignore")
    return run([str(repo_root / "tools/semgrep"), "--json", "."], target)


@pytest.mark.parametrize(("case", "rule"), SEMGREP_CASES, ids=[case for case, _ in SEMGREP_CASES])
def test_111_ac23_semgrep_fails_on_its_fixture(repo_root, tmp_path, case, rule):
    result = semgrep_on(repo_root, tmp_path, case)

    findings = [finding["check_id"] for finding in json.loads(result.stdout)["results"]]
    assert result.returncode != 0, result.stdout + result.stderr
    assert any(check_id.endswith(f".{rule}") for check_id in findings), findings


def test_111_ac23_semgrep_passes_on_the_clean_fixture_and_the_repository(repo_root, tmp_path):
    clean = semgrep_on(repo_root, tmp_path, "clean")
    repository = run([str(repo_root / "tools/semgrep")], repo_root)

    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert repository.returncode == 0, repository.stdout + repository.stderr


QUALITY_STUB = """#!/usr/bin/env bash
echo "quality $*" >> "$STUB_LOG"
[ "${1:-none}" != "$FAILING_CHECK" ]
"""


@pytest.fixture
def pre_commit_repo(repo_root, tmp_path):
    """A git repository with the root pre-commit configuration and a tools/quality that records its calls."""
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    if (repo_root / ".pre-commit-config.yaml").exists():
        shutil.copy2(repo_root / ".pre-commit-config.yaml", repo / ".pre-commit-config.yaml")
    for name in ["quality", "gitleaks"]:
        (repo / "tools" / name).write_text(QUALITY_STUB, encoding="utf-8")
        (repo / "tools" / name).chmod(0o755)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    return repo


@pytest.mark.parametrize("failing_check", ["format-check", "lint"])
def test_111_ac23_pre_commit_fails_when_format_check_or_lint_fails(pre_commit_repo, tmp_path, failing_check):
    env = {**os.environ, "STUB_LOG": str(tmp_path / "calls.log"), "FAILING_CHECK": failing_check}

    result = run([*PRE_COMMIT, "run", "--all-files"], pre_commit_repo, env=env)

    assert result.returncode != 0, result.stdout + result.stderr
    assert f"quality {failing_check} java" in (tmp_path / "calls.log").read_text(encoding="utf-8")


def test_111_ac23_pre_commit_runs_format_check_lint_and_the_commit_message_check(pre_commit_repo, tmp_path):
    env = {**os.environ, "STUB_LOG": str(tmp_path / "calls.log"), "FAILING_CHECK": ""}

    result = run([*PRE_COMMIT, "run", "--all-files"], pre_commit_repo, env=env)
    hooks = yaml.safe_load((pre_commit_repo / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    commit_msg = [hook for repo in hooks["repos"] for hook in repo["hooks"] if "commit-msg" in hook.get("stages", [])]

    assert result.returncode == 0, result.stdout + result.stderr
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert {"quality format-check java", "quality lint java"} <= set(calls)
    assert [hook["entry"] for hook in commit_msg] == ["npx --no -- commitlint --edit"]


def test_111_ac23_renovate_configuration_is_valid_and_waits_14_days(repo_root):
    config = yaml.safe_load((repo_root / "renovate.json").read_text(encoding="utf-8"))

    result = run([str(repo_root / "tools/check-renovate-config"), str(repo_root)], repo_root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert config["minimumReleaseAge"] == "14 days"
    assert config["semanticCommits"] == "enabled"


def test_111_ac23_renovate_check_fails_on_an_invalid_configuration(repo_root, tmp_path):
    (tmp_path / "renovate.json").write_text('{"extends": ["config:recommended"], "notAnOption": 1}\n', encoding="utf-8")

    result = run([str(repo_root / "tools/check-renovate-config"), str(tmp_path)], repo_root)

    assert result.returncode != 0
    assert "notAnOption" in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("message", "passes"),
    [
        ("test(111-B1b): T1.5 red", True),
        ("feat(register): add exit plan field", True),
        ("added the exit plan field", False),
        ("Feat(register): add exit plan field", False),
        ("feat(register): " + "add the exit plan field " * 5, False),
    ],
)
def test_111_ac23_commitlint_checks_conventional_commits(repo_root, message, passes):
    result = run(["npx", "--no", "--", "commitlint"], repo_root, input=message)

    assert (result.returncode == 0) is passes, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("branch", "passes"),
    [
        ("services/104-f0-b3", True),
        ("lane/platform/111-b1b", True),
        ("renovate/spring-boot", True),
        ("feature/exit-plans", False),
        ("Lane/platform/111-B1b", False),
        ("111-b1b", False),
        ("lane/platform/111-b1b-extra", False),
    ],
)
def test_111_ac23_branch_name_check(repo_root, branch, passes):
    result = run([str(repo_root / "tools/check-branch-name"), branch], repo_root)

    assert (result.returncode == 0) is passes, result.stdout + result.stderr


@pytest.fixture
def change_repo(tmp_path):
    """A git repository with a base commit; `change` commits files and returns a size check runner."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def commit_lines(repo: Path, path: str, lines: list[str]) -> None:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "change")


def check_size(repo_root: Path, repo: Path, body: str) -> subprocess.CompletedProcess[str]:
    body_file = repo.parent / "body.md"
    body_file.write_text(body, encoding="utf-8")
    command = [str(repo_root / "tools/check-pr-size"), "--root", str(repo), "--base", "HEAD~1"]
    return run([*command, "--body-file", str(body_file)], repo)


def template_body(repo_root: Path, size_exception: str = "", limit_exceptions: str = "") -> str:
    """The pull request template with its two exception sections filled in."""
    template = (repo_root / ".github/pull_request_template.md").read_text(encoding="utf-8")
    template = template.replace("## Size exception\n", f"## Size exception\n{size_exception}\n")
    return template.replace("## Size limit exceptions\n", f"## Size limit exceptions\n{limit_exceptions}\n")


LINES = [f"int obligation{number} = {number};" for number in range(401)]


def test_111_ac23_pull_request_size_check_fails_above_400_changed_lines(repo_root, change_repo):
    commit_lines(change_repo, "services/register/src/main/java/demo/Big.java", LINES)

    result = check_size(repo_root, change_repo, template_body(repo_root))

    assert result.returncode != 0
    assert "401 changed lines" in result.stdout + result.stderr


def test_111_ac23_pull_request_size_check_passes_400_changed_lines(repo_root, change_repo):
    commit_lines(change_repo, "services/register/src/main/java/demo/Big.java", LINES[:400])

    result = check_size(repo_root, change_repo, template_body(repo_root))

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac23_pull_request_size_check_passes_a_larger_change_with_its_exception(repo_root, change_repo):
    commit_lines(change_repo, "services/register/src/main/java/demo/Big.java", LINES)
    body = template_body(repo_root, size_exception="One migration and its guard tests cannot be split.")

    result = check_size(repo_root, change_repo, body)

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("path", ["tests/fixtures/java/big/Big.java", "package-lock.json", "apps/web/src/generated/client.ts"])
def test_pull_request_size_check_leaves_out_fixtures_lock_files_and_generated_code(repo_root, change_repo, path):
    commit_lines(change_repo, path, LINES)

    result = check_size(repo_root, change_repo, template_body(repo_root))

    assert result.returncode == 0, result.stdout + result.stderr


SUPPRESSION = '@SuppressWarnings("PMD.MethodLength") // the mapping table reads best as one method'


def test_111_ac23_size_limit_exception_in_code_must_be_listed_in_the_pull_request(repo_root, change_repo):
    commit_lines(change_repo, "services/register/src/main/java/demo/Mapping.java", [SUPPRESSION])

    unlisted = check_size(repo_root, change_repo, template_body(repo_root))
    listed = check_size(repo_root, change_repo, template_body(repo_root, limit_exceptions="- Mapping: one table"))

    assert unlisted.returncode != 0
    assert "PMD.MethodLength" in unlisted.stdout + unlisted.stderr
    assert listed.returncode == 0, listed.stdout + listed.stderr


def test_111_ac23_ci_runs_the_repository_and_pull_request_checks_as_required_jobs(repo_root):
    workflow = yaml.safe_load((repo_root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    def runs(job: str) -> str:
        return "\n".join(str(step.get("run", "")) for step in jobs[job]["steps"])

    assert {"tools/gitleaks", "tools/semgrep", "tools/check-renovate-config"} <= set(runs("repository").split())
    assert jobs["pull-request"]["if"] == "github.event_name == 'pull_request'"
    for check in ["tools/check-branch-name", "commitlint --from", "tools/check-pr-size"]:
        assert check in runs("pull-request"), check
    assert {"repository", "pull-request"} <= set(jobs["required"]["needs"])
