"""Spectral on the synced contracts, and the sync of its rule set (T1.11; SA-1.2-6 to SA-1.2-11, SA-1.2-16, SA-4-7).

`lint`: runs config/spectral/ruleset.yaml on every OpenAPI and AsyncAPI file under contracts/ (the folder block 4
syncs) and fails when a file has more errors of a rule than config/spectral/ratchet.json allows it. Ratchet
entries name the spec repository's path of a contract; a synced file matches the entry of the same file name.
A file with fewer errors than its entry passes, and the entry is named so the spec repository can lower it.
`sync`: copies the rule set and the ratchet list from the spec repository byte for byte and records their hashes in
config/spectral/SOURCE.lock; with --check it fails when a copy does not match the lock, or, given the spec
repository, when the lock is behind it.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
SPECTRAL = TOOLS_ROOT / "node_modules/.bin/spectral"
CONFIG = Path("config/spectral")
LOCK = CONFIG / "SOURCE.lock"
SYNCED = {
    "config/spectral/ruleset.yaml": "docs/standards/spectral/ruleset.yaml",
    "config/spectral/ratchet.json": "docs/standards/spectral/ratchet.json",
}
CONTRACT_SUFFIXES = (".openapi.yaml", ".openapi.yml", ".openapi.json", ".asyncapi.yaml", ".asyncapi.yml")
ERROR = 0


def contract_files(root: Path) -> list[Path]:
    folder = root / "contracts"
    found = folder.rglob("*") if folder.is_dir() else iter(())
    return sorted(path for path in found if path.name.endswith(CONTRACT_SUFFIXES) and "fixtures" not in path.parts)


def spectral_errors(root: Path, files: list[Path]) -> Counter[tuple[str, str]]:
    """Errors per (file name, rule) of one Spectral run."""
    with tempfile.TemporaryDirectory(prefix="spectral-") as scratch:
        report = Path(scratch) / "report.json"
        ruleset = str(root / CONFIG / "ruleset.yaml")
        command = [str(SPECTRAL), "lint", "--ruleset", ruleset, "--format", "json", "-o", str(report)]
        subprocess.run([*command, *map(str, files)], cwd=root, check=False, capture_output=True, text=True)
        if not report.exists():
            raise SystemExit("spectral: Spectral wrote no report; is node_modules installed (npm ci)?")
        findings = json.loads(report.read_text(encoding="utf-8") or "[]")
    return Counter(
        (Path(finding["source"]).name, finding["code"]) for finding in findings if finding["severity"] == ERROR
    )


def allowed_errors(root: Path) -> dict[str, dict[str, int]]:
    """The ratchet list by file name."""
    ratchet = json.loads((root / CONFIG / "ratchet.json").read_text(encoding="utf-8"))
    return {Path(path).name: rules for path, rules in ratchet.get("files", {}).items()}


def judge_file(relative: str, errors: Counter[str], allowed: dict[str, int]) -> bool:
    """Print the rules of one file whose count differs from its ratchet entry; true when one is over it."""
    failed = False
    for rule in sorted(set(errors) | set(allowed)):
        count, limit = errors[rule], allowed.get(rule, 0)
        found = f"spectral: {relative}: {rule} {count} {'error' if count == 1 else 'errors'}"
        if count > limit:
            failed = True
            print(f"{found}, the ratchet allows {limit}")
        elif count < limit:
            print(f"{found}, the ratchet allows {limit}; lower it in the spec repository")
    return failed


def lint(root: Path) -> int:
    files = contract_files(root)
    if not files:
        print("spectral: no synced OpenAPI or AsyncAPI file under contracts/ yet, nothing to check")
        return 0
    errors = spectral_errors(root, files)
    allowed = allowed_errors(root)
    failed = False
    for path in files:
        relative = path.relative_to(root).as_posix()
        print(f"spectral: {relative}")
        own = Counter({rule: count for (name, rule), count in errors.items() if name == path.name})
        failed = judge_file(relative, own, allowed.get(path.name, {})) or failed
    if failed:
        print("spectral: failed; fix the contract in the spec repository and sync it (block 4)")
    return 1 if failed else 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync(root: Path, spec_repo: Path) -> int:
    files = {}
    for target, source in SYNCED.items():
        (root / target).parent.mkdir(parents=True, exist_ok=True)
        (root / target).write_bytes((spec_repo / source).read_bytes())
        files[target] = {"source": source, "sha256": sha256(root / target)}
        print(f"sync-spectral: {source} -> {target}")
    (root / LOCK).write_text(json.dumps({"files": files}, indent=1) + "\n", encoding="utf-8")
    return 0


def check(root: Path, spec_repo: Path | None) -> int:
    lock = json.loads((root / LOCK).read_text(encoding="utf-8"))["files"]
    problems = []
    for target, source in SYNCED.items():
        if target not in lock or sha256(root / target) != lock[target]["sha256"]:
            problems.append(f"{target} does not match SOURCE.lock; it is synced, never edited by hand")
        elif spec_repo is not None and sha256(spec_repo / source) != lock[target]["sha256"]:
            problems.append(f"{target} is behind the spec repository; run tools/sync-spectral")
    for problem in problems:
        print(f"sync-spectral: {problem}")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["lint", "sync"])
    parser.add_argument("--root", type=Path, default=TOOLS_ROOT)
    parser.add_argument("--spec-repo", type=Path, default=os.environ.get("SPEC_REPO_DIR") or None)
    parser.add_argument("--check", action="store_true", help="sync: compare the copies, do not write them")
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    if arguments.command == "lint":
        return lint(root)
    if arguments.check:
        return check(root, arguments.spec_repo)
    if arguments.spec_repo is None:
        parser.error("sync needs --spec-repo or SPEC_REPO_DIR")
    return sync(root, arguments.spec_repo)


if __name__ == "__main__":
    sys.exit(main())
