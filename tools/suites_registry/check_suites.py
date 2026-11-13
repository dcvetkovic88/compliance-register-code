"""tools/check-suites: fail when the registry and the tasks disagree (plan D18; 111-FR22, 111-AC22).

Checks:
1. every `suites.yaml` entry is well formed;
2. every registered suite selects at least one test (S1136);
3. every test name that cites a criterion carries the full criterion id (conventions SA-3-2, S1166);
4. for every block in scope, each suite it names is registered (S1124);
5. for every block in scope, each task that adds tests has an entry for the block's suite in the
   `suites.yaml` of its own path;
6. for every block in scope, each criterion it proves has an acceptance test in its suite: a test
   whose name or display name starts with the full criterion id (SA-3-2, OD-22).

A block is in scope when all its tasks are ticked, or when `--block` names its suite, the block
being built. Blocks still to come are never checked (OD-23).
"""

import argparse
import sys
from pathlib import Path

from suites_registry.registry import Registry, load_registry
from suites_registry.tagged_tests import (
    collect_test_names,
    is_acceptance_test_of,
    lacks_full_criterion_id,
    selected_tests,
)
from suites_registry.tasks_file import Block, read_blocks

NO_SUITE_FILE_PATHS = {"spec-repo"}


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tools/check-suites", description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--tasks", type=Path, action="append", default=[], help="a tasks.md to check; repeatable")
    parser.add_argument("--block", help="the suite id of the block being built, checked although not ticked")
    return parser.parse_args(argv)


def registry_problems(root: Path, registry: Registry) -> list[str]:
    problems = list(registry.errors)
    for entry in registry.entries:
        if not selected_tests(root, entry):
            problems.append(
                f"suite {entry.suite_id} in {entry.directory}/suites.yaml selects no test "
                f"({entry.runner} selector {entry.selector!r})"
            )
    return problems


def name_problems(root: Path) -> list[str]:
    return [
        f"{path.relative_to(root).as_posix()}: test {name!r} cites a criterion without its full id "
        "(write it as <feature>[-F<n>]-AC<n>, SA-3-2)"
        for path, name in collect_test_names(root)
        if lacks_full_criterion_id(name)
    ]


def acceptance_problems(root: Path, block: Block, registry: Registry) -> list[str]:
    names = [
        name
        for suite_id in block.suites
        for entry in registry.entries_of(suite_id)
        for name in selected_tests(root, entry)
    ]
    return [
        f"{block.source}: block {block.name} proves {criterion}, but suite {' or '.join(block.suites)} has "
        f"no acceptance test whose name or display name starts with {criterion} (SA-3-2)"
        for criterion in block.proves
        if not any(is_acceptance_test_of(name, criterion) for name in names)
    ]


def block_problems(root: Path, block: Block, registry: Registry) -> list[str]:
    problems = []
    for suite_id in block.named_suites():
        if not registry.entries_of(suite_id):
            problems.append(f"{block.source}: block {block.name} names suite {suite_id}, which is not in the registry")
    problems += acceptance_problems(root, block, registry)
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
    problems = registry_problems(root, registry) + name_problems(root)
    for tasks_file in arguments.tasks:
        for block in read_blocks(tasks_file):
            if block.done or arguments.block in block.suites:
                problems += block_problems(root, block, registry)
    for problem in problems:
        print(problem)
    if problems:
        print(f"check-suites: {len(problems)} problem(s)")
        return 1
    print(f"check-suites: {len(registry.ids())} suite(s) registered, all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
