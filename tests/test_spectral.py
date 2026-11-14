"""Spectral in the code repository (T1.11; 111-FR23, 111-AC23; conventions SA-1.2-6 to SA-1.2-11, SA-1.2-16, SA-4-7).

The rule set and the ratchet list of block 0b are synced from the spec repository into config/spectral/ by
`tools/sync-spectral`, which records their hashes in config/spectral/SOURCE.lock. `tools/spectral` runs the rule
set on every synced OpenAPI and AsyncAPI file under contracts/ and fails on an error the ratchet list does not
allow. The fixtures of tests/fixtures/spectral/violations are byte copies of the spec repository's fixtures.
"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1c

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).parent / "fixtures/spectral"
SYNCED = {
    "config/spectral/ruleset.yaml": "docs/standards/spectral/ruleset.yaml",
    "config/spectral/ratchet.json": "docs/standards/spectral/ratchet.json",
}
CR_RULES = [
    "cr-json-snake-case",
    "cr-path-kebab-case",
    "cr-query-snake-case",
    "cr-event-name",
    "cr-error-code-kebab-case",
    "cr-no-error-code-member",
    "cr-permission-code",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_tool(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(REPO_ROOT / "tools" / name), *args], check=False, capture_output=True, text=True)


@pytest.fixture
def contracts_repo(tmp_path):
    """A repository with the synced rule set and ratchet list and an empty contracts folder."""
    repo = tmp_path / "repo"
    (repo / "contracts").mkdir(parents=True)
    shutil.copytree(REPO_ROOT / "config/spectral", repo / "config/spectral")
    return repo


def lint(repo: Path, *fixtures: str) -> subprocess.CompletedProcess[str]:
    for fixture in fixtures:
        shutil.copytree(FIXTURES / fixture, repo / "contracts", dirs_exist_ok=True)
    return run_tool("spectral", "--root", str(repo))


def ratchet(repo: Path, files: dict[str, dict[str, int]]) -> None:
    (repo / "config/spectral/ratchet.json").write_text(json.dumps({"files": files}), encoding="utf-8")


def test_111_ac23_the_rule_set_and_ratchet_list_are_synced_with_their_hashes():
    lock = json.loads((REPO_ROOT / "config/spectral/SOURCE.lock").read_text(encoding="utf-8"))

    assert set(lock["files"]) == set(SYNCED)
    for target, source in SYNCED.items():
        assert lock["files"][target] == {"source": source, "sha256": sha256(REPO_ROOT / target)}
    assert {"cr-json-snake-case", "cr-event-name"} <= set(
        yaml.safe_load((REPO_ROOT / "config/spectral/ruleset.yaml").read_text(encoding="utf-8"))["rules"]
    )


@pytest.mark.parametrize("rule", CR_RULES)
def test_111_ac23_spectral_fails_each_rule_on_the_spec_repository_fixtures(contracts_repo, rule):
    result = lint(contracts_repo, "violations")

    assert result.returncode != 0
    assert rule in result.stdout


def test_111_ac23_spectral_passes_a_conforming_contract(contracts_repo):
    result = lint(contracts_repo, "clean")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "contracts/obligations.openapi.yaml" in result.stdout


def test_111_ac23_spectral_passes_a_carried_contract_within_its_ratchet(contracts_repo):
    ratchet(contracts_repo, {"docs/standalone/contracts/legacy-service.openapi.yaml": {"cr-no-error-code-member": 1}})

    result = lint(contracts_repo, "ratcheted")

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac23_spectral_fails_a_carried_contract_beyond_its_ratchet(contracts_repo):
    ratchet(contracts_repo, {"docs/standalone/contracts/legacy-service.openapi.yaml": {"cr-no-error-code-member": 1}})

    result = lint(contracts_repo, "ratcheted-worse")

    assert result.returncode != 0
    assert "contracts/legacy-service.openapi.yaml: cr-json-snake-case 1 error, the ratchet allows 0" in result.stdout


def test_111_ac23_spectral_names_a_ratchet_entry_that_can_shrink(contracts_repo):
    ratchet(contracts_repo, {"docs/standalone/contracts/legacy-service.openapi.yaml": {"cr-no-error-code-member": 2}})

    result = lint(contracts_repo, "ratcheted")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "cr-no-error-code-member 1 error, the ratchet allows 2" in result.stdout


def test_111_ac23_spectral_passes_with_no_synced_contract_yet(contracts_repo):
    result = lint(contracts_repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "no synced OpenAPI or AsyncAPI file" in result.stdout


def test_111_ac23_spectral_passes_on_the_repository():
    result = run_tool("spectral")

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture
def spec_repo(tmp_path):
    """A spec repository whose rule set and ratchet list are those the code repository holds."""
    spec = tmp_path / "spec"
    for target, source in SYNCED.items():
        (spec / source).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / target, spec / source)
    return spec


def test_111_ac23_sync_copies_the_rule_set_and_ratchet_list_and_records_their_hashes(contracts_repo, spec_repo):
    ratchet_file = spec_repo / "docs/standards/spectral/ratchet.json"
    ratchet_file.write_text('{"files": {}}\n', encoding="utf-8")

    result = run_tool("sync-spectral", "--root", str(contracts_repo), "--spec-repo", str(spec_repo))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (contracts_repo / "config/spectral/ratchet.json").read_bytes() == ratchet_file.read_bytes()
    lock = json.loads((contracts_repo / "config/spectral/SOURCE.lock").read_text(encoding="utf-8"))
    assert lock["files"]["config/spectral/ratchet.json"]["sha256"] == sha256(ratchet_file)


def test_111_ac23_sync_check_passes_when_the_copies_match_the_spec_repository(contracts_repo, spec_repo):
    result = run_tool("sync-spectral", "--check", "--root", str(contracts_repo), "--spec-repo", str(spec_repo))

    assert result.returncode == 0, result.stdout + result.stderr


def test_111_ac23_sync_check_fails_when_the_spec_repository_moved_on(contracts_repo, spec_repo):
    (spec_repo / "docs/standards/spectral/ratchet.json").write_text('{"files": {}}\n', encoding="utf-8")

    result = run_tool("sync-spectral", "--check", "--root", str(contracts_repo), "--spec-repo", str(spec_repo))

    assert result.returncode != 0
    assert "config/spectral/ratchet.json is behind the spec repository" in result.stdout


def test_111_ac23_sync_check_fails_when_a_copy_was_edited_by_hand(contracts_repo):
    with (contracts_repo / "config/spectral/ruleset.yaml").open("a", encoding="utf-8") as ruleset:
        ruleset.write("# edited\n")

    result = run_tool("sync-spectral", "--check", "--root", str(contracts_repo))

    assert result.returncode != 0
    assert "config/spectral/ruleset.yaml does not match SOURCE.lock" in result.stdout


def test_111_ac23_ci_runs_spectral_in_the_repository_job():
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["repository"]["steps"]
    lines = {line.strip() for step in steps for line in str(step.get("run", "")).splitlines()}

    assert {"npm ci", "tools/spectral", "tools/sync-spectral --check"} <= lines
