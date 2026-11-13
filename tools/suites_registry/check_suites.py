"""tools/check-suites: fail when the registry and the tasks disagree (plan D18; 111-FR22, 111-AC22).

The tests are read from the JUnit XML reports `tools/suite` writes (`--reports`, default
`.suite-reports`), never from test sources: only a test that ran counts. Run every suite first.

Checks:
1. every `suites.yaml` entry is well formed, and has a report;
2. every registered suite entry ran at least one test (S1136);
3. every test name that cites a criterion carries the full criterion id (conventions SA-3-2, S1166);
4. for every block in scope, each suite it names is registered (S1124);
5. for every block in scope, each task that adds tests has an entry for the block's suite in the
   `suites.yaml` of its own path;
6. for every block in scope, each criterion it proves has an acceptance test that ran in its suite:
   a test whose reported name starts with the full criterion id (SA-3-2, OD-22).

A block is in scope when all its tasks are ticked, or when `--block` names its suite, the block
being built, in any case (`111-b1` from the branch name selects `111-B1`); a `--block` that names no
block of the tasks files fails. Blocks still to come are never checked (OD-23).
"""

import argparse
import sys
from pathlib import Path

from suites_registry.registry import Registry, SuiteEntry, load_registry
from suites_registry.reports import (
    REPORTS_DIR,
    ReportedTest,
    ReportError,
    is_acceptance_test_of,
    lacks_full_criterion_id,
    read_report,
    report_path,
)
from suites_registry.tasks_file import Block, read_blocks

NO_SUITE_FILE_PATHS = {"spec-repo"}


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tools/check-suites", description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--tasks", type=Path, action="append", default=[], help="a tasks.md to check; repeatable")
    parser.add_argument("--block", help="the suite id of the block being built, checked although not ticked")
    parser.add_argument("--reports", type=Path, help=f"the reports tools/suite wrote; default <root>/{REPORTS_DIR}")
    return parser.parse_args(argv)


Reports = dict[SuiteEntry, list[ReportedTest]]


def label(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)


def suites_file(entry: SuiteEntry) -> str:
    return "suites.yaml" if entry.directory == "." else f"{entry.directory}/suites.yaml"


def read_reports(root: Path, reports_dir: Path, registry: Registry) -> tuple[Reports, list[str]]:
    reports: Reports = {}
    problems = []
    for entry in registry.entries:
        path = report_path(reports_dir, entry)
        try:
            reports[entry] = read_report(path)
        except ReportError as error:
            problems.append(
                f"suite {entry.suite_id} in {suites_file(entry)}: {error} at {label(root, path)}; "
                f"run tools/suite {entry.suite_id} first"
            )
    return reports, problems


def registry_problems(reports: Reports) -> list[str]:
    return [
        f"suite {entry.suite_id} in {suites_file(entry)} selects no test: no test of its report ran "
        f"({entry.runner} selector {entry.selector!r})"
        for entry, tests in reports.items()
        if not any(test.ran for test in tests)
    ]


def name_problems(reports: Reports) -> list[str]:
    return [
        f"suite {entry.suite_id} in {suites_file(entry)}: test {name!r} cites a criterion without its full id "
        "(write it as <feature>[-F<n>]-AC<n>, SA-3-2)"
        for entry, tests in reports.items()
        for name in dict.fromkeys(test.name for test in tests)
        if lacks_full_criterion_id(name)
    ]


def acceptance_problems(block: Block, registry: Registry, reports: Reports) -> list[str]:
    names = [
        test.name
        for suite_id in block.suites
        for entry in registry.entries_of(suite_id)
        for test in reports.get(entry, [])
        if test.ran
    ]
    return [
        f"{block.source}: block {block.name} proves {criterion}, but suite {' or '.join(block.suites)} has "
        f"no acceptance test that ran whose name starts with {criterion} (SA-3-2)"
        for criterion in block.proves
        if not any(is_acceptance_test_of(name, criterion) for name in names)
    ]


def block_problems(block: Block, registry: Registry, reports: Reports) -> list[str]:
    problems = []
    for suite_id in block.named_suites():
        if not registry.entries_of(suite_id):
            problems.append(f"{block.source}: block {block.name} names suite {suite_id}, which is not in the registry")
    problems += acceptance_problems(block, registry, reports)
    if not block.suites:
        return problems
    for task in block.tasks:
        if not task.adds_tests or task.path is None or task.path in NO_SUITE_FILE_PATHS:
            continue
        directory = "." if task.path == "repo-root" else task.path.rstrip("/")
        if not {entry.suite_id for entry in registry.entries_in(directory)}.intersection(block.suites):
            problems.append(
                f"{block.source}: {task.task_id} adds tests in [{task.path}], but "
                f"{'suites.yaml' if directory == '.' else directory + '/suites.yaml'} has no entry "
                f"for {' or '.join(block.suites)}"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    root = arguments.root.resolve()
    registry = load_registry(root)
    reports, problems = read_reports(root, (arguments.reports or root / REPORTS_DIR).resolve(), registry)
    problems = list(registry.errors) + problems + registry_problems(reports) + name_problems(reports)
    built = arguments.block.lower() if arguments.block else None
    found = False
    for tasks_file in arguments.tasks:
        for block in read_blocks(tasks_file):
            being_built = built in {suite_id.lower() for suite_id in block.suites}
            found = found or being_built
            if block.done or being_built:
                problems += block_problems(block, registry, reports)
    if built and not found:
        problems.append(f"--block {arguments.block} names no block of the tasks files")
    for problem in problems:
        print(problem)
    if problems:
        print(f"check-suites: {len(problems)} problem(s)")
        return 1
    print(f"check-suites: {len(registry.ids())} suite(s) registered, all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
