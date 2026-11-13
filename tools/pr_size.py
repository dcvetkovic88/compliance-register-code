"""tools/check-pr-size: the pull request size check (T1.8; conventions SA-2.3-6, SA-2.3-7).

A pull request changes about 400 lines at most, counted without fixtures, lock files and generated code.
A larger one passes only when the section `## Size exception` of its body gives the reason. Every exception
to a size limit it adds to the code (a PMD, ruff or ESLint suppression of a size rule) must be listed in the
section `## Size limit exceptions`, one list entry per exception naming its file and its rules, then a one-line
reason after a colon, as `- Mapping.java PMD.MethodLength: the reason`; an entry without a reason lists nothing. A blanket PMD suppression (`@SuppressWarnings("PMD")`,
`@SuppressWarnings("all")` or a `// NOPMD` marker) hides every size rule, so it is listed with the rule `PMD`;
a ruff one naming no rule (`# noqa`, `# ruff: noqa`) is listed with `ruff`, an ESLint directive naming no rule
(`/* eslint-disable */`, `// eslint-disable-next-line`) with `eslint`.
Suppressions are recognized by the syntax of their language (a Java annotation or NOPMD line comment, a Python
`noqa` comment, an ESLint directive comment), so documentation, other comments and string literals naming one
suppress nothing and need no entry.
"""

import argparse
import io
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

LIMIT = 400
LEFT_OUT = re.compile(r"(^|/)(fixtures|generated|target|node_modules)/|(^|/)[^/]*\.lock$|(^|/)package-lock\.json$")
PMD_SIZE_RULES = {
    f"PMD.{rule}"
    for rule in ("MethodLength", "ClassLength", "ExcessiveParameterList", "NestingDepth", "CyclomaticComplexity")
}
RUFF_SIZE_RULES = {"PLR0913", "PLR0915", "PLR1702", "C901"}
ESLINT_SIZE_RULES = {"max-lines", "max-lines-per-function", "max-params", "max-depth", "complexity"}
JAVA = (".java",)
SCRIPT = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
PYTHON = (".py", ".pyi")
# The size rules a suppression names, each as the entry of the section names it.
SIZE_RULES = re.compile(
    r"(?<![\w.-])(?:PMD\.(?:MethodLength|ClassLength|ExcessiveParameterList|NestingDepth|CyclomaticComplexity)"
    r"|PLR0913|PLR0915|PLR1702|C901"
    r"|max-lines-per-function|max-lines|max-params|max-depth|complexity|PMD(?!\.)|ruff|eslint)(?![\w-])"
)
SUPPRESS_WARNINGS = re.compile(r"@(?:java\.lang\.)?SuppressWarnings\s*\(")
STRING_LITERAL = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
# A ruff suppression: `# noqa` for a line, `# ruff: noqa` or `# flake8: noqa` for the file, each with its codes.
NOQA = re.compile(r"#\s*(?:(?:ruff|flake8)\s*:\s*)?noqa\b(?P<codes>\s*:.*)?", re.IGNORECASE)
RULE_CODE = re.compile(r"\b[A-Z]+[0-9]+\b")
ESLINT_DISABLE = re.compile(r"eslint-disable(?:-line|-next-line)?(?![\w-])(?P<rules>.*)", re.DOTALL)


@dataclass(frozen=True)
class Comment:
    """One comment of a source file: where it starts and ends, whether it is a line comment, and its text."""

    start: int
    end: int
    line_comment: bool
    text: str


@dataclass(frozen=True)
class Lexed:
    """A Java or JavaScript source with its comments, and the source with comments and literal contents blanked."""

    masked: str
    comments: list[Comment]


def _blank(text: str) -> str:
    return re.sub(r"[^\n]", " ", text)


def _literal_end(text: str, start: int, quote: str) -> int:
    """The offset after the literal opening at start; a single or double quoted literal ends at its line."""
    index = start + len(quote)
    while index < len(text):
        if text[index] == "\\":
            index += 2
        elif text.startswith(quote, index):
            return index + len(quote)
        elif text[index] == "\n" and quote in ('"', "'"):
            return index
        else:
            index += 1
    return len(text)


def lex(text: str, quotes: tuple[str, ...]) -> Lexed:
    """Splits a C-like source into its comments and its code, string and character literal contents blanked."""
    masked: list[str] = []
    comments: list[Comment] = []
    index = 0
    while index < len(text):
        if text.startswith("//", index):
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            comments.append(Comment(index, end, True, text[index + 2 : end]))
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = len(text) if end < 0 else end + 2
            comments.append(Comment(index, end, False, text[index + 2 : end - 2]))
        elif quote := next((quote for quote in quotes if text.startswith(quote, index)), None):
            end = _literal_end(text, index, quote)
            masked.append(quote + _blank(text[index + len(quote) : end]))
            index = end
            continue
        else:
            masked.append(text[index])
            index += 1
            continue
        masked.append(_blank(text[index:end]))
        index = end
    return Lexed("".join(masked), comments)


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _closing_paren(masked: str, start: int) -> int:
    depth = 1
    for index in range(start, len(masked)):
        depth += {"(": 1, ")": -1}.get(masked[index], 0)
        if depth == 0:
            return index + 1
    return len(masked)


def java_suppressions(text: str) -> list[tuple[range, str, set[str]]]:
    """The size suppressions of a Java source: SuppressWarnings annotations and NOPMD line comments."""
    lexed = lex(text, ('"""', '"', "'"))
    found = []
    for match in SUPPRESS_WARNINGS.finditer(lexed.masked):
        end = _closing_paren(lexed.masked, match.end())
        annotation = text[match.start() : end]
        values = set(STRING_LITERAL.findall(annotation))
        rules = (values & PMD_SIZE_RULES) | ({"PMD"} if values & {"PMD", "all"} else set())
        lines = range(_line(text, match.start()), _line(text, end) + 1)
        found.append((lines, " ".join(annotation.split()), rules))
    for comment in lexed.comments:
        if comment.line_comment and "NOPMD" in comment.text:
            found.append(
                (range(_line(text, comment.start), _line(text, comment.start) + 1), f"//{comment.text}", {"PMD"})
            )
    return found


def script_suppressions(text: str) -> list[tuple[range, str, set[str]]]:
    """The size suppressions of a JavaScript or TypeScript source: eslint-disable directive comments.

    A directive naming no rule disables every rule, so it suppresses the size rules as `eslint`.
    """
    found = []
    for comment in lex(text, ('"', "'", "`")).comments:
        directive = comment.text.strip()
        if disable := ESLINT_DISABLE.match(directive):
            named = disable.group("rules").split("--")[0]
            rules = set(SIZE_RULES.findall(named)) & ESLINT_SIZE_RULES if named.strip() else {"eslint"}
            lines = range(_line(text, comment.start), _line(text, comment.end) + 1)
            found.append((lines, " ".join(directive.split()), rules))
    return found


def python_suppressions(text: str) -> list[tuple[range, str, set[str]]]:
    """The size suppressions of a Python source: noqa comments naming a size rule, or no rule at all as `ruff`."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        comments = [(token.start[0], token.string) for token in tokens if token.type == tokenize.COMMENT]
    except (tokenize.TokenError, SyntaxError):
        comments = [
            (number, "#" + line.split("#", 1)[1]) for number, line in enumerate(text.splitlines(), 1) if "#" in line
        ]
    found = []
    for number, comment in comments:
        if noqa := NOQA.search(comment):
            codes = RULE_CODE.findall(noqa.group("codes") or "")
            rules = set(codes) & RUFF_SIZE_RULES if codes else {"ruff"}
            found.append((range(number, number + 1), comment, rules))
    return found


def suppressions_in(path: str, text: str) -> list[tuple[range, str, set[str]]]:
    """The suppressions in the source of one file, by its language; documentation and other files have none."""
    if path.endswith(JAVA):
        return java_suppressions(text)
    if path.endswith(SCRIPT):
        return script_suppressions(text)
    if path.endswith(PYTHON):
        return python_suppressions(text)
    return []


@dataclass(frozen=True)
class Suppression:
    """One added suppression of a size rule: its file, its text and the size rules it names."""

    path: str
    text: str
    rules: frozenset[str]

    def __str__(self) -> str:
        return f"{self.path}: {self.text}"

    def listed_by(self, entry: str) -> bool:
        """An entry lists this exception when it names the file and every size rule of the line, then a reason.

        The entry reads `- Mapping.java PMD.MethodLength: the reason`; the file and rules come before the colon
        and a one-line reason after it, so an entry with no reason lists nothing (SA-2.3-7).
        """
        named, colon, reason = entry.partition(":")
        if not colon or not reason.strip():
            return False
        return Path(self.path).name in named and self.rules <= set(SIZE_RULES.findall(named))


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def changed_lines(root: Path, base: str) -> int:
    total = 0
    for row in git(root, "diff", "--numstat", "--no-renames", f"{base}...HEAD").splitlines():
        added, deleted, path = row.split("\t", 2)
        if added != "-" and not LEFT_OUT.search(path):
            total += int(added) + int(deleted)
    return total


def added_lines(root: Path, base: str) -> dict[str, set[int]]:
    """The numbers of the lines each changed file adds, in its new version."""
    added: dict[str, set[int]] = {}
    path = ""
    for line in git(root, "diff", "-U0", "--no-renames", f"{base}...HEAD").splitlines():
        if line.startswith("+++ "):
            path = line.removeprefix("+++ b/")
        elif hunk := re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line):
            first, count = int(hunk.group(1)), int(hunk.group(2) or 1)
            added.setdefault(path, set()).update(range(first, first + count))
    return added


def added_size_suppressions(root: Path, base: str) -> list[Suppression]:
    """The size rule suppressions on the added lines, recognized by the suppression syntax of each language."""
    suppressions = []
    for path, lines in added_lines(root, base).items():
        if path == "/dev/null" or LEFT_OUT.search(path) or not path.endswith(JAVA + SCRIPT + PYTHON):
            continue
        for spanned, text, rules in suppressions_in(path, git(root, "show", f"HEAD:{path}")):
            if rules and lines.intersection(spanned):
                suppressions.append(Suppression(path, text, frozenset(rules)))
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
    """The text of every `## ` section of the body with this heading, without HTML comments.

    The runner appends its own `## Size exception` to a body that may hold the template's empty one (OD-28).
    """
    matches = re.finditer(rf"^## {re.escape(heading)}[ \t]*$(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    texts = (re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip() for match in matches)
    return "\n".join(text for text in texts if text)


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
            " naming the file and the rule, then a one-line reason after a colon (SA-2.3-7): "
            + "; ".join(str(suppression) for suppression in missing)
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
