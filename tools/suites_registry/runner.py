"""tools/suite: run one suite of the registry in any language (plan D18; 111-FR22, 111-AC22).

`tools/suite <id>` runs every entry with that id, from the repository root, each with its own
runner. `--dry-run` prints the commands instead. `--matrix` prints the registry as the JSON
matrix the CI suites job fans out over.
"""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

from suites_registry.registry import SuiteEntry, load_registry


def command_of(entry: SuiteEntry) -> list[str]:
    if entry.runner == "maven":
        return ["./mvnw", "-B", "-pl", entry.directory, "test", f"-Dgroups={entry.selector}"]
    if entry.runner == "pytest":
        project = entry.project or entry.directory
        return ["uv", "run", "--project", project, "--frozen", "pytest", "-m", entry.selector, *entry.test_paths]
    if entry.runner == "vitest":
        return [
            "npm",
            "exec",
            f"--workspace={entry.directory}",
            "--",
            "vitest",
            "run",
            "--testNamePattern",
            entry.selector,
        ]
    if entry.runner == "playwright":
        return ["npm", "exec", f"--workspace={entry.directory}", "--", "playwright", "test", "--grep", entry.selector]
    script = entry.selector if entry.directory == "." else f"{entry.directory}/{entry.selector}"
    return ["bash", script]


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tools/suite", description=__doc__.splitlines()[0])
    parser.add_argument("suite_id", nargs="?")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--dry-run", action="store_true", help="print the commands, run nothing")
    parser.add_argument("--matrix", action="store_true", help="print the CI matrix of every registered suite")
    arguments = parser.parse_args(argv)
    if not arguments.matrix and not arguments.suite_id:
        parser.error("name a suite id, or pass --matrix")
    return arguments


def matrix(entries: list[SuiteEntry]) -> dict[str, list[dict[str, object]]]:
    suite_ids = sorted({entry.suite_id for entry in entries})
    return {
        "include": [
            {"suite": suite_id, "stack": any(e.stack for e in entries if e.suite_id == suite_id)}
            for suite_id in suite_ids
        ]
    }


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    root = arguments.root.resolve()
    registry = load_registry(root)
    if registry.errors:
        print("\n".join(registry.errors), file=sys.stderr)
        return 2
    if arguments.matrix:
        print(json.dumps(matrix(registry.entries)))
        return 0
    entries = registry.entries_of(arguments.suite_id)
    if not entries:
        print(f"suite {arguments.suite_id} is not in the registry", file=sys.stderr)
        return 2
    failed = []
    for entry in entries:
        command = command_of(entry)
        print(shlex.join(command), flush=True)
        if not arguments.dry_run and subprocess.run(command, cwd=root, check=False).returncode != 0:
            failed.append(f"{entry.directory} ({entry.runner})")
    if failed:
        print(f"suite {arguments.suite_id} failed in: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
