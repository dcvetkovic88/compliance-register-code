"""The JUnit XML reports `tools/suite` writes, one per suite entry, and the tests in them (plan D18; OD-22).

Only a test that ran counts. A skipped, disabled or deselected test is either in no report or marked
`<skipped>`, and a parametrized test with no cases is reported skipped, so none of them counts. Vitest
reports a `describe` without tests as a failed case "No test found in suite"; that is no test either.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from suites_registry.registry import SuiteEntry

REPORTS_DIR = ".suite-reports"
# Vitest joins the titles of the enclosing describes with " > ", Playwright with " › ".
TITLE_SEPARATORS = (" > ", " › ")
PARAMETER_ID = re.compile(r"\[(.+)\]$")
EMPTY_GROUP = "No test found in suite"

CRITERION_REFERENCE = re.compile(r"(?<![A-Za-z0-9])AC\d+(?![0-9])", re.IGNORECASE)
FULL_CRITERION_ID = re.compile(r"(?<![A-Za-z0-9])\d{3}(?:[-_]F\d+)?[-_]AC\d+(?![0-9])", re.IGNORECASE)


class ReportError(Exception):
    """A report that is missing or is not JUnit XML."""


@dataclass(frozen=True)
class ReportedTest:
    name: str
    ran: bool


def report_path(reports: Path, entry: SuiteEntry) -> Path:
    """Where `tools/suite` writes the report of one entry: `<reports>/<suite id>/<path>-<runner>-<selector>.xml`."""
    return reports / entry.suite_id / entry.report_name


def read_report(path: Path) -> list[ReportedTest]:
    if not path.is_file():
        raise ReportError("no test report")
    try:
        document = ElementTree.parse(path).getroot()
    except ElementTree.ParseError as error:
        raise ReportError(f"not JUnit XML ({error})") from error
    return [ReportedTest(case.get("name", ""), ran(case)) for case in document.iter("testcase")]


def ran(case: ElementTree.Element) -> bool:
    if case.find("skipped") is not None:
        return False
    return not any(problem.get("message", "").startswith(EMPTY_GROUP) for problem in case.iter() if problem is not case)


def names_of(name: str) -> list[str]:
    """The reported name, the test's own title without its describes, and its pytest parameter id."""
    names = [name]
    names += [name.split(separator)[-1] for separator in TITLE_SEPARATORS if separator in name]
    parameter = PARAMETER_ID.search(name)
    if parameter:
        names.append(parameter.group(1))
    return names


def lacks_full_criterion_id(name: str) -> bool:
    """True when the name cites a criterion (`AC6`) without its feature (`109-F4-AC6`); SA-3-2."""
    full_spans = [match.span() for match in FULL_CRITERION_ID.finditer(name)]
    return any(
        not any(start <= reference.start() < end for start, end in full_spans)
        for reference in CRITERION_REFERENCE.finditer(name)
    )


def is_acceptance_test_of(name: str, criterion: str) -> bool:
    """True when the reported name, own title or parameter id starts with the full criterion id (SA-3-2, OD-22).

    A Python function name is read without its `test_` prefix and with `_` as `-`.
    """
    criterion = criterion.lower()
    for candidate in names_of(name):
        normalised = candidate.lower().removeprefix("test_").replace("_", "-")
        if normalised.startswith(criterion) and not normalised[len(criterion) : len(criterion) + 1].isdigit():
            return True
    return False
