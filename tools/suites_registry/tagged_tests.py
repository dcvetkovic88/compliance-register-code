"""Find the tests a suite selects, and their names, from test sources without running them.

A suite selects a test, not a tag: a tagged pytest file, JUnit class or Vitest describe that holds
no test selects nothing, because Maven and Vitest exit 0 when nothing is selected (S1136, OD-22).
"""

import ast
import re
from pathlib import Path

from suites_registry.registry import SuiteEntry, walk_files

PYTHON_TEST_FILES = ("test_*.py", "*_test.py")
# Surefire's default inclusions: `tools/suite` runs `mvn test`, which never runs a `*IT.java` class.
JAVA_TEST_FILES = ("Test*.java", "*Test.java", "*Tests.java", "*TestCase.java")
VITEST_FILES = ("*.test.ts", "*.test.tsx")
BROWSER_FILES = ("*.e2e.ts",)

JAVA_DISPLAY_NAME = re.compile(r"""@DisplayName\(\s*"([^"]+)"\s*\)""")
JAVA_TEST_ANNOTATION = re.compile(r"@(?:[\w.]+\.)?(?:Test|ParameterizedTest|RepeatedTest|TestFactory)\b")
JAVA_METHOD = re.compile(r"^\s*(?:public\s+|protected\s+|private\s+)?(?:static\s+)?\w[\w<>\[\]]*\s+(\w+)\s*\(")
JAVA_TYPE = re.compile(r"\b(?:class|interface|record|enum)\b")
JAVA_DISABLED = re.compile(r"@(?:[\w.]+\.)?Disabled\b(?![\w.])")
JAVA_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
TS_CALL = re.compile(r"""\b(?P<callee>(?:it|test|describe)(?:\.\w+)*)\(\s*(?P<quote>["'`])(?P<title>.+?)(?P=quote)""")

INACTIVE_MODIFIERS = {"skip", "todo", "fixme"}

CRITERION_REFERENCE = re.compile(r"(?<![A-Za-z0-9])AC\d+(?![0-9])", re.IGNORECASE)
FULL_CRITERION_ID = re.compile(r"(?<![A-Za-z0-9])\d{3}(?:[-_]F\d+)?[-_]AC\d+(?![0-9])", re.IGNORECASE)


def files_of(root: Path, start: Path, patterns: tuple[str, ...]):
    for pattern in patterns:
        yield from walk_files(root, start, pattern)


# Python -------------------------------------------------------------------------------------------


def carries_mark(node: ast.AST, selector: str | None) -> bool:
    """True when the expression holds `pytest.mark.<selector>` (or `mark.<selector>`); any mark when None."""
    for child in ast.walk(node):
        if not isinstance(child, ast.Attribute) or (selector is not None and child.attr != selector):
            continue
        owner = child.value
        if (isinstance(owner, ast.Attribute) and owner.attr == "mark") or (
            isinstance(owner, ast.Name) and owner.id == "mark"
        ):
            return True
    return False


def pytestmark_carries(body: list[ast.stmt], selector: str) -> bool:
    return any(
        isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in statement.targets)
        and carries_mark(statement.value, selector)
        for statement in body
    )


def decorated_with(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, selector: str) -> bool:
    return any(carries_mark(decorator, selector) for decorator in node.decorator_list)


def skipped_params(decorator: ast.expr) -> set[int]:
    """The ids of the id keywords inside a `pytest.param(..., marks=pytest.mark.skip)`; those cases never run."""
    skipped: set[int] = set()
    for child in ast.walk(decorator):
        if isinstance(child, ast.Call) and any(
            keyword.arg == "marks" and carries_mark(keyword.value, "skip") for keyword in child.keywords
        ):
            skipped.update(id(keyword) for keyword in child.keywords if keyword.arg == "id")
    return skipped


def python_names_of(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """The function name and every pytest id it is parametrized with, but for skipped cases."""
    names = [function.name]
    for decorator in function.decorator_list:
        skipped = skipped_params(decorator)
        for child in ast.walk(decorator):
            if isinstance(child, ast.keyword) and child.arg in {"id", "ids"} and id(child) not in skipped:
                values = child.value.elts if isinstance(child.value, ast.List | ast.Tuple) else [child.value]
                names += [
                    value.value for value in values if isinstance(value, ast.Constant) and isinstance(value.value, str)
                ]
    return names


TestFunction = ast.FunctionDef | ast.AsyncFunctionDef


def skipped(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> bool:
    """True when a `pytest.mark.skip` on the function or class keeps its body from running."""
    return decorated_with(node, "skip") or (isinstance(node, ast.ClassDef) and pytestmark_carries(node.body, "skip"))


def marked_tests(body: list[ast.stmt], selector: str | None, marked: bool) -> list[str]:
    """Names of the unskipped test functions in `body` that carry the mark, or all of them when `marked`."""
    return [
        name
        for node in body
        if isinstance(node, TestFunction) and node.name.startswith("test") and not skipped(node)
        if marked or decorated_with(node, selector or "")
        for name in python_names_of(node)
    ]


def python_tests(source: str, selector: str | None) -> list[str]:
    """Names of the pytest tests in `source` that carry `selector` (every test when None).

    A test under `pytest.mark.skip`, on itself, its class or its module, never runs, so it is no test of the suite.
    """
    try:
        module = ast.parse(source)
    except SyntaxError:
        return []
    if pytestmark_carries(module.body, "skip"):
        return []
    module_marked = selector is None or pytestmark_carries(module.body, selector)
    names = marked_tests(module.body, selector, module_marked)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test") and not skipped(node):
            class_marked = (
                module_marked or decorated_with(node, selector or "") or pytestmark_carries(node.body, selector or "")
            )
            names += marked_tests(node.body, selector, class_marked)
    return names


# Java ---------------------------------------------------------------------------------------------


def matching_brace(source: str, opening: int) -> int:
    """Index just past the brace that closes the one at `opening`."""
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    return len(source)


def blank_disabled_types(source: str) -> str:
    """The source with the body of every `@Disabled` class blanked out, keeping every index in place."""
    for disabled in JAVA_DISABLED.finditer(source):
        opening = source.find("{", disabled.end())
        if opening < 0 or not JAVA_TYPE.search(source[disabled.end() : opening]):
            continue
        closing = matching_brace(source, opening) - 1
        source = source[: opening + 1] + re.sub(r"[^\n]", " ", source[opening + 1 : closing]) + source[closing:]
    return source


def java_test_names(source: str) -> list[str]:
    """The display name of each test method not under `@Disabled`, or the method name when it has none."""
    names: list[str] = []
    pending_display_name: str | None = None
    in_test = disabled = False
    for line in source.splitlines():
        display_name = JAVA_DISPLAY_NAME.search(line)
        if display_name:
            pending_display_name = display_name.group(1)
        if JAVA_TEST_ANNOTATION.search(line):
            in_test = True
        if JAVA_DISABLED.search(line):
            disabled = True
        if line.lstrip().startswith("@"):
            continue
        method = JAVA_METHOD.match(line)
        if method and in_test and not disabled:
            names.append(pending_display_name or method.group(1))
        if method or JAVA_TYPE.search(line):
            pending_display_name, in_test, disabled = None, False, False
    return names


def java_tests(source: str, selector: str | None) -> list[str]:
    """Names of the JUnit tests in `source` tagged `selector`, by class or by method (every test when None).

    A test under `@Disabled`, on itself or its class, never runs, so it is no test of the suite.
    """
    source = blank_disabled_types(JAVA_COMMENT.sub("", source))
    if selector is None:
        return java_test_names(source)
    names: list[str] = []
    for tag in re.finditer(rf"""@Tag\(\s*"{re.escape(selector)}"\s*\)""", source):
        opening = source.find("{", tag.end())
        if opening < 0:
            continue
        header = source[tag.end() : opening]
        if JAVA_TYPE.search(header):
            names += java_test_names(source[opening : matching_brace(source, opening)])
        else:
            start = max(source.rfind(mark, 0, tag.start()) for mark in ";{}") + 1
            names += java_test_names(source[start : opening + 1])
    return names


# Vitest and Playwright ----------------------------------------------------------------------------


def skip_literal(source: str, index: int) -> int:
    """Index just past the string or comment that starts at `index`, or `index` when none starts there."""
    char = source[index]
    if char in "\"'`":
        index += 1
        while index < len(source) and source[index] != char:
            index += 2 if source[index] == "\\" else 1
        return index + 1
    for opening, closing in (("//", "\n"), ("/*", "*/")):
        if source.startswith(opening, index):
            end = source.find(closing, index + len(opening))
            return len(source) if end < 0 else end + len(closing)
    return index


def call_end(source: str, opening: int) -> int:
    """Index just past the parenthesis that closes the one at `opening`, skipping strings and comments."""
    depth, index = 0, opening
    while index < len(source):
        skipped = skip_literal(source, index)
        if skipped != index:
            index = skipped
            continue
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return len(source)


def inert_spans(source: str) -> list[tuple[int, int]]:
    """The (start, end) of every string and comment in `source`; a call inside one never runs."""
    spans, index = [], 0
    while index < len(source):
        skipped = skip_literal(source, index)
        if skipped != index:
            spans.append((index, skipped))
            index = skipped
        else:
            index += 1
    return spans


def typescript_tests(source: str, selector: str | None) -> list[str]:
    """Titles of the active `it` and `test` calls whose own or enclosing title holds `selector` (every one when None).

    A call in a comment or string, a `.skip`, `.todo` or `.fixme` call, and every call inside a skipped
    `describe` runs nothing, so it is no test of the suite.
    """
    inert = inert_spans(source)
    calls = []
    for call in TS_CALL.finditer(source):
        if any(start <= call.start() < end for start, end in inert):
            continue
        opening = source.index("(", call.start())
        parts = call.group("callee").split(".")
        active = not INACTIVE_MODIFIERS.intersection(parts)
        calls.append((call.start(), call_end(source, opening), "describe" in parts, active, call.group("title")))
    names: list[str] = []
    for start, _, is_describe, active, title in calls:
        enclosing = [(d_active, t) for s, e, d, d_active, t in calls if d and s < start < e]
        if is_describe or not active or not all(d_active for d_active, _ in enclosing):
            continue
        titles = [t for _, t in enclosing] + [title]
        if selector is None or any(selector in t for t in titles):
            names += [title, " ".join(titles)]
    return names


# Suites -------------------------------------------------------------------------------------------


def tests_in(path: Path, runner: str, selector: str | None) -> list[str]:
    source = path.read_text(encoding="utf-8")
    if runner == "pytest":
        return python_tests(source, selector)
    if runner == "maven":
        return java_tests(source, selector)
    return typescript_tests(source, selector)


RUNNER_FILES = {"pytest": PYTHON_TEST_FILES, "maven": JAVA_TEST_FILES, "vitest": VITEST_FILES}


def selected_tests(root: Path, entry: SuiteEntry) -> list[str]:
    """Names of the tests the entry selects; a script suite selects its script."""
    if entry.runner == "script":
        script = root / entry.directory / entry.selector
        return [entry.selector] if script.is_file() else []
    patterns = RUNNER_FILES.get(entry.runner, BROWSER_FILES)
    return [
        name
        for start in entry.test_paths
        for path in files_of(root, root / start, patterns)
        for name in tests_in(path, entry.runner, entry.selector)
    ]


def collect_test_names(root: Path) -> list[tuple[Path, str]]:
    """Every test name or display name in the repository, with its file."""
    names: list[tuple[Path, str]] = []
    for runner, patterns in [*RUNNER_FILES.items(), ("playwright", BROWSER_FILES)]:
        for path in files_of(root, root, patterns):
            names += [(path, name) for name in tests_in(path, runner, None)]
    return names


def lacks_full_criterion_id(name: str) -> bool:
    """True when the name cites a criterion (`AC6`) without its feature (`109-F4-AC6`); SA-3-2."""
    full_spans = [match.span() for match in FULL_CRITERION_ID.finditer(name)]
    for reference in CRITERION_REFERENCE.finditer(name):
        if not any(start <= reference.start() < end for start, end in full_spans):
            return True
    return False


def is_acceptance_test_of(name: str, criterion: str) -> bool:
    """True when the name or display name starts with the full criterion id (SA-3-2, OD-22).

    A Python function name is read without its `test_` prefix and with `_` as `-`.
    """
    normalised = name.lower().removeprefix("test_").replace("_", "-")
    criterion = criterion.lower()
    return normalised.startswith(criterion) and not normalised[len(criterion) : len(criterion) + 1].isdigit()
