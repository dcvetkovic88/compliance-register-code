"""tools/suite: run one suite of the registry in any language (plan D18; 111-FR22, 111-AC22).

`tools/suite <id>` runs every entry with that id, from the repository root, each with its own
runner, and writes one JUnit XML report per entry under `--reports` (default `.suite-reports`),
which `tools/check-suites` reads. A Maven entry builds the libraries its module needs first
(`-pl <module> -am`). `--dry-run` prints the commands instead. `--matrix` prints the registry as
the JSON matrix the CI suites job fans out over.
"""

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

from suites_registry.registry import SuiteEntry, load_registry
from suites_registry.reports import REPORTS_DIR, report_path

SUREFIRE_REPORTS = "target/surefire-reports"


def command_of(entry: SuiteEntry, report: Path) -> list[str]:
    if entry.runner == "maven":
        return ["./mvnw", "-B", "-pl", entry.directory, "-am", "test", f"-Dgroups={entry.selector}"]
    if entry.runner == "pytest":
        project = entry.project or entry.directory
        return [
            "uv",
            "run",
            "--project",
            project,
            "--frozen",
            "pytest",
            "-m",
            entry.selector,
            *entry.test_paths,
            f"--junitxml={report}",
        ]
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
            "--reporter=default",
            "--reporter=junit",
            f"--outputFile.junit={report}",
        ]
    if entry.runner == "playwright":
        return [
            "env",
            f"PLAYWRIGHT_JUNIT_OUTPUT_FILE={report}",
            "npm",
            "exec",
            f"--workspace={entry.directory}",
            "--",
            "playwright",
            "test",
            "--grep",
            entry.selector,
            "--reporter=list,junit",
        ]
    script = entry.selector if entry.directory == "." else f"{entry.directory}/{entry.selector}"
    return ["bash", script]


def write_testsuites(report: Path, suites: list[ElementTree.Element]) -> None:
    document = ElementTree.Element("testsuites")
    document.extend(suites)
    ElementTree.ElementTree(document).write(report, encoding="utf-8", xml_declaration=True)


def collect_surefire_reports(root: Path, entry: SuiteEntry, report: Path) -> None:
    """Merge the module's Surefire reports into the entry's report; none when no test ran."""
    surefire = root / entry.directory / SUREFIRE_REPORTS
    files = sorted(surefire.glob("TEST-*.xml")) if surefire.is_dir() else []
    write_testsuites(report, [ElementTree.parse(path).getroot() for path in files])


def write_script_report(entry: SuiteEntry, report: Path, returncode: int) -> None:
    """A script is one test: it ran, and it failed when it exited non-zero."""
    suite = ElementTree.Element("testsuite", name=entry.directory, tests="1", failures=str(int(returncode != 0)))
    case = ElementTree.SubElement(suite, "testcase", classname=entry.directory, name=entry.selector)
    if returncode != 0:
        ElementTree.SubElement(case, "failure", message=f"exit code {returncode}")
    write_testsuites(report, [suite])


def run_entry(root: Path, entry: SuiteEntry, report: Path, command: list[str]) -> int:
    if entry.runner == "maven":
        shutil.rmtree(root / entry.directory / SUREFIRE_REPORTS, ignore_errors=True)
    returncode = subprocess.run(command, cwd=root, check=False).returncode
    if entry.runner == "maven":
        collect_surefire_reports(root, entry, report)
    elif entry.runner == "script":
        write_script_report(entry, report, returncode)
    return returncode


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tools/suite", description=__doc__.splitlines()[0])
    parser.add_argument("suite_id", nargs="?")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--reports", type=Path, help=f"where the JUnit XML reports go; default <root>/{REPORTS_DIR}")
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
    reports = (arguments.reports or root / REPORTS_DIR).resolve()
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
    if not arguments.dry_run:
        shutil.rmtree(reports / arguments.suite_id, ignore_errors=True)
        (reports / arguments.suite_id).mkdir(parents=True)
    failed = []
    for entry in entries:
        report = report_path(reports, entry)
        command = command_of(entry, report)
        print(shlex.join(command), flush=True)
        if not arguments.dry_run and run_entry(root, entry, report, command) != 0:
            failed.append(f"{entry.directory} ({entry.runner})")
    if failed:
        print(f"suite {arguments.suite_id} failed in: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
