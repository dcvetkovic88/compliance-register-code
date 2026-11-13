"""Read test names and suite tags from test sources without running them."""

import re
from pathlib import Path

from suites_registry.registry import SuiteEntry, walk_files

PYTHON_TEST_FILES = ("test_*.py", "*_test.py")
JAVA_TEST_FILES = ("*Test.java", "*IT.java")
VITEST_FILES = ("*.test.ts", "*.test.tsx")
BROWSER_FILES = ("*.e2e.ts",)

PYTHON_TEST_NAME = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)", re.MULTILINE)
PYTHON_TEST_ID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""")
PYTHON_TEST_IDS = re.compile(r"\bids\s*=\s*\[([^\]]*)\]")
QUOTED = re.compile(r"""["']([^"']+)["']""")
JAVA_DISPLAY_NAME = re.compile(r"""@DisplayName\(\s*"([^"]+)"\s*\)""")
JAVA_TEST_ANNOTATION = re.compile(r"@(?:Test|ParameterizedTest|RepeatedTest|TestFactory)\b")
JAVA_METHOD = re.compile(r"^\s*(?:public\s+|protected\s+|private\s+)?(?:static\s+)?\w[\w<>\[\]]*\s+(\w+)\s*\(")
TS_TITLE = re.compile(r"""\b(?:it|test|describe)(?:\.\w+)*\(\s*(["'`])(.+?)\1""")

CRITERION_REFERENCE = re.compile(r"(?<![A-Za-z0-9])AC\d+(?![0-9])", re.IGNORECASE)
FULL_CRITERION_ID = re.compile(r"(?<![A-Za-z0-9])\d{3}(?:[-_]F\d+)?[-_]AC\d+(?![0-9])", re.IGNORECASE)


def files_of(root: Path, start: Path, patterns: tuple[str, ...]):
    for pattern in patterns:
        yield from walk_files(root, start, pattern)


def collect_test_names(root: Path) -> list[tuple[Path, str]]:
    """Every test name or display name in the repository, with its file."""
    names: list[tuple[Path, str]] = []
    for path in files_of(root, root, PYTHON_TEST_FILES):
        source = path.read_text(encoding="utf-8")
        names += [(path, name) for name in PYTHON_TEST_NAME.findall(source)]
        names += [(path, name) for name in PYTHON_TEST_ID.findall(source)]
        for id_list in PYTHON_TEST_IDS.findall(source):
            names += [(path, name) for name in QUOTED.findall(id_list)]
    for path in files_of(root, root, JAVA_TEST_FILES):
        names += [(path, name) for name in java_test_names(path.read_text(encoding="utf-8"))]
    for path in files_of(root, root, VITEST_FILES + BROWSER_FILES):
        names += [(path, title) for _, title in TS_TITLE.findall(path.read_text(encoding="utf-8"))]
    return names


def java_test_names(source: str) -> list[str]:
    """The display name of each test method, or the method name when it has none."""
    names: list[str] = []
    pending_display_name: str | None = None
    in_test = False
    for line in source.splitlines():
        display_name = JAVA_DISPLAY_NAME.search(line)
        if display_name:
            pending_display_name = display_name.group(1)
        if JAVA_TEST_ANNOTATION.search(line):
            in_test = True
        method = JAVA_METHOD.match(line)
        if method and not line.lstrip().startswith("@"):
            if in_test:
                names.append(pending_display_name or method.group(1))
            elif pending_display_name:
                names.append(pending_display_name)
            pending_display_name, in_test = None, False
    if pending_display_name:
        names.append(pending_display_name)
    return names


def lacks_full_criterion_id(name: str) -> bool:
    """True when the name cites a criterion (`AC6`) without its feature (`109-F4-AC6`); SA-3-2."""
    full_spans = [match.span() for match in FULL_CRITERION_ID.finditer(name)]
    for reference in CRITERION_REFERENCE.finditer(name):
        if not any(start <= reference.start() < end for start, end in full_spans):
            return True
    return False


def selects_a_test(root: Path, entry: SuiteEntry) -> bool:
    """True when at least one test in the entry's paths carries the entry's tag."""
    starts = [root / path for path in entry.test_paths]
    if entry.runner == "script":
        return (root / entry.directory / entry.selector).is_file()
    if entry.runner == "pytest":
        tag = re.compile(rf"\bmark\.{re.escape(entry.selector)}\b")
        patterns = PYTHON_TEST_FILES
    elif entry.runner == "maven":
        tag = re.compile(rf"""@Tag\(\s*"{re.escape(entry.selector)}"\s*\)""")
        patterns = JAVA_TEST_FILES
    else:
        tag = re.compile(rf"""\b(?:it|test|describe)(?:\.\w+)*\(\s*["'`][^"'`]*{re.escape(entry.selector)}""")
        patterns = VITEST_FILES if entry.runner == "vitest" else BROWSER_FILES
    return any(
        tag.search(path.read_text(encoding="utf-8"))
        for start in starts
        for path in files_of(root, start, patterns)
    )
