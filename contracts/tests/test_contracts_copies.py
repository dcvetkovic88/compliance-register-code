"""The synced copies of the frozen contracts and their validation (T4.2; 111-FR5, 111-AC5; plan D6).

`contracts/` holds the seven frozen files of the spec repository's `docs/standalone/contracts/` byte for byte,
with `SOURCE.lock`. `contracts/scripts/check` runs the drift check and validates each OpenAPI file as 3.1 and
the AsyncAPI file as 3.0.
"""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from conftest import CONTRACTS, FIXTURES, SPEC_FOLDER, git, run_script
from test_contracts_drift import FROZEN_FILES

pytestmark = pytest.mark.suite_111_B4

INVALID = FIXTURES / "invalid"


def test_contracts_holds_every_frozen_file_and_its_lock():
    lock = json.loads((CONTRACTS / "SOURCE.lock").read_text(encoding="utf-8"))

    assert sorted(lock["files"]) == FROZEN_FILES
    assert len(lock["commit"]) == 40
    for name, entry in lock["files"].items():
        assert entry["source"] == f"{SPEC_FOLDER}/{name}"
        assert entry["sha256"] == hashlib.sha256((CONTRACTS / name).read_bytes()).hexdigest(), name


def test_111_ac5_check_passes_on_the_synced_contracts_and_validates_each_file():
    result = run_script("check")
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    for name in FROZEN_FILES:
        version = "AsyncAPI 3.0" if ".asyncapi." in name else "OpenAPI 3.1"
        assert f"{name} is valid {version}" in output


def synced_with(tmp_path: Path, spec_repo: Path, name: str, fixture: str) -> Path:
    """Sync a contracts folder from the spec repository after replacing one contract by an invalid fixture."""
    shutil.copyfile(INVALID / fixture, spec_repo / SPEC_FOLDER / name)
    git(spec_repo, "commit", "-q", "-am", f"{name} from {fixture}")
    target = tmp_path / "contracts"
    result = run_script("sync", "--spec-repo", str(spec_repo), "--contracts", str(target))
    assert result.returncode == 0, result.stdout + result.stderr
    return target


@pytest.mark.parametrize(
    "case",
    [
        ("platform.openapi.yaml", "openapi-3.0.yaml", "platform.openapi.yaml is not OpenAPI 3.1"),
        ("web-bff.openapi.yaml", "openapi-3.1-without-info.yaml", "web-bff.openapi.yaml is not valid OpenAPI 3.1"),
        ("register-events.asyncapi.yaml", "asyncapi-2.6.yaml", "register-events.asyncapi.yaml is not AsyncAPI 3.0"),
        (
            "register-events.asyncapi.yaml",
            "asyncapi-3.0-bad-channel.yaml",
            "register-events.asyncapi.yaml is not valid AsyncAPI 3.0",
        ),
    ],
)
def test_111_ac5_check_fails_on_a_contract_that_is_not_valid(tmp_path, spec_repo, case):
    name, fixture, message = case
    contracts = synced_with(tmp_path, spec_repo, name, fixture)

    result = run_script("check", "--contracts", str(contracts))

    assert result.returncode == 1
    assert message in result.stdout + result.stderr


def test_check_validates_the_fixture_contracts_of_a_fresh_sync(spec_repo, synced):
    result = run_script("check", "--contracts", str(synced), "--spec-repo", str(spec_repo))

    assert result.returncode == 0, result.stdout + result.stderr
