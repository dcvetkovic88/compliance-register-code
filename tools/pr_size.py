"""tools/check-pr-size: the pull request size check (T1.8; conventions SA-2.3-6, SA-2.3-7).

A pull request changes about 400 lines at most, counted without fixtures, lock files and generated code.
A larger one passes only when the section `## Size exception` of its body gives the reason. Every exception
to a size limit it adds to the code (a PMD, ruff or ESLint suppression of a size rule) must be listed in the
section `## Size limit exceptions`, one list entry per exception naming its file and its rules, as
`- Mapping.java PMD.MethodLength: the reason`.
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

LIMIT = 400
LEFT_OUT = re.compile(r"(^|/)(fixtures|generated|target|node_modules)/|(^|/)[^/]*\.lock$|(^|/)package-lock\.json$")
SIZE_SUPPRESSION = re.compile(
    r"PMD\.(MethodLength|ClassLength|ExcessiveParameterList|NestingDepth|CyclomaticComplexity)"
    r"|noqa:[^\n]*\b(PLR0913|PLR0915|PLR1702|C901)\b"
    r"|eslint-disable[^\n]*\b(max-lines|max-lines-per-function|max-params|max-depth|complexity)\b"
)
# The size rules a suppression names, each as the entry of the section names it.
SIZE_RULES = re.compile(
    r"(?<![\w.-])(?:PMD\.(?:MethodLength|ClassLength|ExcessiveParameterList|NestingDepth|CyclomaticComplexity)"
    r"|PLR0913|PLR0915|PLR1702|C901"
    r"|max-lines-per-function|max-lines|max-params|max-depth|complexity)(?![\w-])"
)


@dataclass(frozen=True)
class Suppression:
    """One added line that suppresses a size rule: its file, its text and the size rules it names."""

    path: str
    text: str
    rules: frozenset[str]

    def __str__(self) -> str:
        return f"{self.path}: {self.text}"

    def listed_by(self, entry: str) -> bool:
        """An entry lists this exception when it names the file and every size rule of the line."""
        return Path(self.path).name in entry and self.rules <= set(SIZE_RULES.findall(entry))


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def changed_lines(root: Path, base: str) -> int:
    total = 0
    for row in git(root, "diff", "--numstat", "--no-renames", f"{base}...HEAD").splitlines():
        added, deleted, path = row.split("\t", 2)
        if added != "-" and not LEFT_OUT.search(path):
            total += int(added) + int(deleted)
    return total


def added_size_suppressions(root: Path, base: str) -> list[Suppression]:
    suppressions = []
    path = ""
    for line in git(root, "diff", "-U0", "--no-renames", f"{base}...HEAD").splitlines():
        if line.startswith("+++ "):
            path = line.removeprefix("+++ b/")
        elif line.startswith("+") and not LEFT_OUT.search(path) and SIZE_SUPPRESSION.search(line):
            text = line[1:].strip()
            suppressions.append(Suppression(path, text, frozenset(SIZE_RULES.findall(text))))
    return suppressions


def unlisted(suppressions: list[Suppression], listing: str) -> list[Suppression]:
    """The suppressions without an entry of their own in the listing; an entry lists one exception at most."""
    entries = [line.strip() for line in listing.splitlines() if line.strip().startswith(("-", "*"))]
    missing = []
    for suppression in suppressions:
        entry = next((entry for entry in entries if suppression.listed_by(entry)), None)
        if entry is None:
            missing.append(suppression)
        else:
            entries.remove(entry)
    return missing


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
    missing = unlisted(added_size_suppressions(root, base), section(body, "Size limit exceptions"))
    if missing:
        problems.append(
            "these exceptions to a size limit are not listed under '## Size limit exceptions', one entry each"
            " naming the file and the rule (SA-2.3-7): " + "; ".join(str(suppression) for suppression in missing)
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
