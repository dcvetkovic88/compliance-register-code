"""tools/check-pr-size: the pull request size check (T1.8; conventions SA-2.3-6, SA-2.3-7).

A pull request changes about 400 lines at most, counted without fixtures, lock files and generated code.
A larger one passes only when the section `## Size exception` of its body gives the reason. Every exception
to a size limit it adds to the code (a PMD, ruff or ESLint suppression of a size rule) must be listed in the
section `## Size limit exceptions`.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

LIMIT = 400
LEFT_OUT = re.compile(r"(^|/)(fixtures|generated|target|node_modules)/|(^|/)[^/]*\.lock$|(^|/)package-lock\.json$")
SIZE_SUPPRESSION = re.compile(
    r"PMD\.(MethodLength|ClassLength|ExcessiveParameterList|NestingDepth|CyclomaticComplexity)"
    r"|noqa:[^\n]*\b(PLR0913|PLR0915|PLR1702|C901)\b"
    r"|eslint-disable[^\n]*\b(max-lines|max-lines-per-function|max-params|max-depth|complexity)\b"
)


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def changed_lines(root: Path, base: str) -> int:
    total = 0
    for row in git(root, "diff", "--numstat", "--no-renames", f"{base}...HEAD").splitlines():
        added, deleted, path = row.split("\t", 2)
        if added != "-" and not LEFT_OUT.search(path):
            total += int(added) + int(deleted)
    return total


def added_size_suppressions(root: Path, base: str) -> list[str]:
    suppressions = []
    path = ""
    for line in git(root, "diff", "-U0", "--no-renames", f"{base}...HEAD").splitlines():
        if line.startswith("+++ "):
            path = line.removeprefix("+++ b/")
        elif line.startswith("+") and not LEFT_OUT.search(path) and SIZE_SUPPRESSION.search(line):
            suppressions.append(f"{path}: {line[1:].strip()}")
    return suppressions


def section(body: str, heading: str) -> str:
    """The text of one `## ` section of the body, without HTML comments."""
    match = re.search(rf"^## {re.escape(heading)}[ \t]*$(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip() if match else ""


def check(root: Path, base: str, body: str) -> list[str]:
    problems = []
    lines = changed_lines(root, base)
    print(f"pull request size: {lines} changed lines, without fixtures, lock files and generated code")
    if lines > LIMIT and not section(body, "Size exception"):
        problems.append(
            f"{lines} changed lines is above {LIMIT}; split the pull request or give the reason under"
            " '## Size exception' in its body (SA-2.3-6)"
        )
    suppressions = added_size_suppressions(root, base)
    if suppressions and not section(body, "Size limit exceptions"):
        problems.append(
            "these exceptions to a size limit are not listed under '## Size limit exceptions' (SA-2.3-7): "
            + "; ".join(suppressions)
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/check-pr-size", description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="origin/main", help="the commit the pull request starts from")
    parser.add_argument("--body-file", type=Path, help="the pull request body; none means an empty body")
    arguments = parser.parse_args(argv)
    body = arguments.body_file.read_text(encoding="utf-8") if arguments.body_file else ""
    problems = check(arguments.root.resolve(), arguments.base, body)
    for problem in problems:
        print(f"pull request size: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
