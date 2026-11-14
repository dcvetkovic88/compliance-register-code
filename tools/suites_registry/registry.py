"""Assemble the registry from the `suites.yaml` of every path (plan D18; S1124, S1136)."""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RUNNERS = ("maven", "pytest", "vitest", "playwright", "script")
SUITE_ID = re.compile(r"^\d{3}(?:-F\d+)?-B\d+[a-z]?(?:-[a-z0-9]+)*$")
SKIPPED_DIRS = {".git", "node_modules", "target", "dist", "build", ".venv", "fixtures"}
UNSAFE_IN_FILE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class SuiteEntry:
    """One entry of one `suites.yaml`; a suite is the union of the entries with its id."""

    suite_id: str
    runner: str
    selector: str
    directory: str
    paths: tuple[str, ...] = ()
    project: str | None = None
    stack: bool = False

    @property
    def report_name(self) -> str:
        """The file name of its report, `<path>-<runner>-<selector>.xml`, unique among the entries of its suite."""
        path = "root" if self.directory == "." else self.directory.replace("/", "-")
        selector = UNSAFE_IN_FILE_NAME.sub("-", self.selector).strip("-")
        return f"{path}-{self.runner}-{selector}.xml"

    @property
    def test_paths(self) -> tuple[str, ...]:
        """Paths the runner searches, relative to the repository root."""
        if not self.paths:
            return (self.directory,)
        return tuple(join(self.directory, path) for path in self.paths)


@dataclass
class Registry:
    entries: list[SuiteEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def ids(self) -> list[str]:
        return sorted({entry.suite_id for entry in self.entries})

    def entries_of(self, suite_id: str) -> list[SuiteEntry]:
        return [entry for entry in self.entries if entry.suite_id == suite_id]

    def entries_in(self, directory: str) -> list[SuiteEntry]:
        return [entry for entry in self.entries if entry.directory == directory]


def join(directory: str, path: str) -> str:
    return path if directory == "." else f"{directory}/{path}"


def walk_files(root: Path, start: Path, pattern: str) -> Iterator[Path]:
    """Files under `start` matching `pattern`, outside build output and test fixtures; `start` may be a file."""
    if not start.exists():
        return
    candidates = [start] if start.is_file() and start.match(pattern) else sorted(start.rglob(pattern))
    for path in candidates:
        relative_parts = path.relative_to(root).parts
        if not SKIPPED_DIRS.intersection(relative_parts) and path.is_file():
            yield path


def load_registry(root: Path) -> Registry:
    registry = Registry()
    files = sorted(walk_files(root, root, "suites.yaml"), key=lambda path: path.parent.relative_to(root).as_posix())
    for suites_file in files:
        directory = suites_file.parent.relative_to(root).as_posix()
        read_suites_file(suites_file, directory, root, registry)
    registry.errors += shared_report_errors(registry.entries)
    return registry


def shared_report_errors(entries: list[SuiteEntry]) -> list[str]:
    """Two entries of one suite whose reports would overwrite each other cannot be told apart."""
    seen: dict[tuple[str, str], SuiteEntry] = {}
    errors = []
    for entry in entries:
        key = (entry.suite_id, entry.report_name)
        if key in seen:
            label = "suites.yaml" if entry.directory == "." else f"{entry.directory}/suites.yaml"
            errors.append(
                f"{label}: two entries of suite {entry.suite_id} write one report, {entry.report_name}; "
                "give them different selectors or join them into one entry"
            )
        seen.setdefault(key, entry)
    return errors


def read_suites_file(suites_file: Path, directory: str, root: Path, registry: Registry) -> None:
    label = suites_file.relative_to(root).as_posix()
    try:
        document = yaml.safe_load(suites_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        registry.errors.append(f"{label}: not valid YAML ({error})")
        return
    rows = document.get("suites") if isinstance(document, dict) else None
    if not isinstance(rows, list):
        registry.errors.append(f"{label}: needs a top-level list `suites`")
        return
    for row in rows:
        entry = parse_entry(row, directory, label, registry.errors)
        if entry is not None:
            registry.entries.append(entry)


def parse_entry(row: object, directory: str, label: str, errors: list[str]) -> SuiteEntry | None:
    if not isinstance(row, dict):
        errors.append(f"{label}: every entry is a mapping with id, runner and selector")
        return None
    suite_id = str(row.get("id", ""))
    runner = str(row.get("runner", ""))
    selector = str(row.get("selector", ""))
    problems = []
    if not SUITE_ID.match(suite_id):
        problems.append(f"id {suite_id!r} does not match <feature>[-F<n>]-B<block>[-<name>]")
    if runner not in RUNNERS:
        problems.append(f"runner {runner!r} is not one of {', '.join(RUNNERS)}")
    if not selector:
        problems.append("selector is missing")
    paths = row.get("paths", [])
    if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
        problems.append("paths must be a list of paths")
    if problems:
        errors.extend(f"{label}: entry {suite_id or '?'}: {problem}" for problem in problems)
        return None
    return SuiteEntry(
        suite_id=suite_id,
        runner=runner,
        selector=selector,
        directory=directory,
        paths=tuple(paths),
        project=row.get("project"),
        stack=bool(row.get("stack", False)),
    )
