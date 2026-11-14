"""The drift check of the synced contracts (T4.1; 111-FR5, 111-AC5; plan D6).

`contracts/scripts/sync` copies the frozen files from the spec checkout byte for byte and writes
`SOURCE.lock` with the spec commit and the SHA-256 of each file. `contracts/scripts/check` fails on any
local edit and, given the spec checkout, when the lock is behind it. The fixtures run on a temporary git
repository standing in for the spec repository.
"""

import hashlib
import json
from pathlib import Path

import pytest
from conftest import SPEC_FOLDER, git, run_script

pytestmark = pytest.mark.suite_111_B4

FROZEN_FILES = [
    "ai-document-service.openapi.yaml",
    "ict-risk-service.openapi.yaml",
    "monitoring-service.openapi.yaml",
    "platform.openapi.yaml",
    "register-events.asyncapi.yaml",
    "register-service.openapi.yaml",
    "web-bff.openapi.yaml",
]


def check(contracts: Path, *args: str) -> tuple[int, str]:
    result = run_script("check", "--contracts", str(contracts), "--skip-validation", *args)
    return result.returncode, result.stdout + result.stderr


def test_sync_copies_every_frozen_file_byte_for_byte(spec_repo, synced):
    for name in FROZEN_FILES:
        assert (synced / name).read_bytes() == (spec_repo / SPEC_FOLDER / name).read_bytes(), name


def test_sync_writes_the_spec_commit_and_the_hash_of_each_file_into_the_lock(spec_repo, synced):
    lock = json.loads((synced / "SOURCE.lock").read_text(encoding="utf-8"))

    assert lock["commit"] == git(spec_repo, "rev-parse", "HEAD")
    assert sorted(lock["files"]) == FROZEN_FILES
    for name, entry in lock["files"].items():
        assert entry["source"] == f"{SPEC_FOLDER}/{name}"
        assert entry["sha256"] == hashlib.sha256((synced / name).read_bytes()).hexdigest()


def test_111_ac5_drift_check_passes_on_the_synced_files(spec_repo, synced):
    returncode, output = check(synced, "--spec-repo", str(spec_repo))

    assert returncode == 0, output


def test_111_ac5_drift_check_fails_on_a_file_with_one_edited_byte(synced):
    edited = synced / "platform.openapi.yaml"
    content = bytearray(edited.read_bytes())
    content[-2] = ord("X") if content[-2] != ord("X") else ord("Y")
    edited.write_bytes(bytes(content))

    returncode, output = check(synced)

    assert returncode == 1
    assert "platform.openapi.yaml does not match SOURCE.lock" in output


def test_111_ac5_drift_check_fails_when_the_lock_is_behind_the_spec_repository(spec_repo, synced):
    source = spec_repo / SPEC_FOLDER / "monitoring-service.openapi.yaml"
    source.write_text(source.read_text(encoding="utf-8") + "# changed in the spec repository\n", encoding="utf-8")
    git(spec_repo, "commit", "-q", "-am", "change a contract")

    returncode, output = check(synced, "--spec-repo", str(spec_repo))

    assert returncode == 1
    assert "monitoring-service.openapi.yaml is behind the spec repository" in output


def test_drift_check_fails_on_a_missing_file_and_on_a_file_the_lock_does_not_list(synced):
    (synced / "web-bff.openapi.yaml").unlink()
    (synced / "extra.openapi.yaml").write_text("openapi: 3.1.0\n", encoding="utf-8")

    returncode, output = check(synced)

    assert returncode == 1
    assert "web-bff.openapi.yaml is missing" in output
    assert "extra.openapi.yaml is not in SOURCE.lock" in output


def test_sync_refuses_a_spec_checkout_with_uncommitted_contract_changes(tmp_path, spec_repo):
    source = spec_repo / SPEC_FOLDER / "platform.openapi.yaml"
    source.write_text(source.read_text(encoding="utf-8") + "# not committed\n", encoding="utf-8")

    result = run_script("sync", "--spec-repo", str(spec_repo), "--contracts", str(tmp_path / "out"))

    assert result.returncode == 1
    assert "uncommitted" in result.stdout + result.stderr


def test_sync_reads_the_spec_checkout_from_spec_repo_dir(tmp_path, spec_repo, monkeypatch):
    monkeypatch.setenv("SPEC_REPO_DIR", str(spec_repo))

    result = run_script("sync", "--contracts", str(tmp_path / "out"))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "out/SOURCE.lock").is_file()
