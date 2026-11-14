"""The repository structure checks (T1.12; 111-FR17, 111-FR23, 111-AC17, 111-AC23; conventions section 6).

language: Python product code lives only in services/ai-document; Python elsewhere is tooling (tools/, tests/,
deploy/, contracts/scripts) and never sits in services/, libs/, apps/ or packages/. Java lives only in services/
(not in the Python service), libs/ and tools/arch-rules (suite readiness rule 6).
sql-schemas: the SQL of services/<folder> names only the folder's own schema and, unless the service has no
usage on schema platform, the platform functions of tools/sql-schemas.yaml, called (suite readiness rule 3).
The SQL is that of the .sql files and of the string literals of the .java and .py files holding an SQL keyword
(the JdbcClient and psycopg queries, plan D3); Java and Python comments and docstrings are not read.
A search_path, set by SET search_path, SET SCHEMA or set_config, names no listed schema but the folder's own, so
no unqualified name reaches another schema. SQL comments and string literals are not read, but the value of a
search_path is.
size: a Python module of services/ or libs/ is at most 300 lines (SA-2.3-2).
Build output, dependencies, virtual environments and test fixtures are never read.
"""

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml

SKIPPED = {".git", "node_modules", ".venv", "target", "dist", "build", "coverage", "mutants", "fixtures", ".specify"}
SKIPPED |= {".claude", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".suite-reports"}
PRODUCT_PATHS = ("services/", "libs/", "apps/", "packages/")
PYTHON_SERVICE = "services/ai-document/"
JAVA_PATHS = ("services/", "libs/", "tools/arch-rules/")
MODULE_LINES = 300
SQL_NOISE = re.compile(r"--[^\n]*|/\*.*?\*/|'(?:[^']|'')*'", re.DOTALL)
QUALIFIED_NAME = r'"?\b({schemas})\b"?\s*\.\s*"?([A-Za-z_][A-Za-z0-9_]*)"?(\s*\()?'
SET_SEARCH_PATH = re.compile(
    r"\bSET\s+(?:SESSION\s+|LOCAL\s+)?(?:search_path\s*(?:TO|=)|SCHEMA\b)([^;]*)", re.IGNORECASE
)
SET_CONFIG_CALL = re.compile(r"\bset_config\s*\(", re.IGNORECASE)
SET_CONFIG_SEARCH_PATH = re.compile(r"\s*'search_path'\s*,\s*'((?:[^']|'')*)'", re.IGNORECASE)
PATH_ENTRY = re.compile(r'"([^"]+)"|\'([^\']+)\'|([A-Za-z_][A-Za-z0-9_$]*)')
SQL_KEYWORD = re.compile(
    r"(?<![\w.])(?:SELECT|INSERT|UPDATE|DELETE|MERGE|FROM|JOIN|INTO|WITH|CREATE|ALTER|DROP|TRUNCATE|GRANT|SET|CALL"
    r"|COPY|REFERENCES|set_config)(?![\w.])",
    re.IGNORECASE,
)
JAVA_TOKEN = re.compile(r'//[^\n]*|/\*.*?\*/|"""(.*?)"""|"((?:\\.|[^"\\\n])*)"|\'(?:\\.|[^\'\\])*\'', re.DOTALL)
JAVA_ESCAPE = re.compile(r"\\(.)")


def files(root: Path, suffix: str) -> Iterator[str]:
    """Paths relative to `root`, in POSIX form, of the files ending in `suffix` outside the skipped folders."""
    for path in sorted(root.rglob(f"*{suffix}")):
        relative = path.relative_to(root)
        if path.is_file() and not SKIPPED.intersection(relative.parts[:-1]):
            yield relative.as_posix()


def language_findings(root: Path) -> list[str]:
    findings = []
    for path in files(root, ".py"):
        if path.startswith(PRODUCT_PATHS) and not path.startswith(PYTHON_SERVICE):
            findings.append(f"{path}: Python product code lives only in services/ai-document (language rule)")
    for path in files(root, ".java"):
        if not path.startswith(JAVA_PATHS) or path.startswith(PYTHON_SERVICE):
            findings.append(f"{path}: Java lives only in services/, libs/ and tools/arch-rules (language rule)")
    return findings


def blank_noise(sql: str) -> str:
    """The SQL with comments and string literals blanked, line breaks kept so line numbers hold."""
    return SQL_NOISE.sub(lambda noise: re.sub(r"[^\n]", " ", noise.group()), sql)


def search_paths(sql: str, blanked: str) -> Iterator[tuple[int, str]]:
    """(offset, schema) for each schema a SET search_path or set_config('search_path', ...) outside comments names."""
    settings = [(match.start(), sql[match.start(1) : match.end(1)]) for match in SET_SEARCH_PATH.finditer(blanked)]
    for call in SET_CONFIG_CALL.finditer(blanked):
        argument = SET_CONFIG_SEARCH_PATH.match(sql, call.end())
        if argument:
            settings.append((call.start(), argument.group(1).replace("''", "'")))
    for offset, setting in settings:
        for entry in PATH_ENTRY.finditer(setting):
            yield offset, next(name for name in entry.groups() if name).strip().lower()


def search_path_findings(location: tuple[str, int], sql: str, own: str, schemas: list[str]) -> list[str]:
    """Findings for each search_path of `sql`, which starts at line location[1] of file location[0]."""
    path, first_line = location
    blanked = blank_noise(sql)
    return [
        f"{path}:{first_line + blanked.count(chr(10), 0, offset)}: search_path {schema}; the search_path of a"
        f" service names only its own schema {own} (tools/sql-schemas.yaml)"
        for offset, schema in search_paths(sql, blanked)
        if schema in schemas and schema != own
    ]


def java_strings(source: str) -> Iterator[tuple[int, str]]:
    """(line, text) of each string literal and text block of the Java source, comments skipped, escapes undone."""
    for token in JAVA_TOKEN.finditer(source):
        start = token.start(1) if token.group(1) is not None else token.start(2)
        literal = token.group(1) if token.group(1) is not None else token.group(2)
        if literal is not None:
            text = JAVA_ESCAPE.sub(lambda escape: escape.group(1) if escape.group(1) in "\"'\\" else " ", literal)
            yield source.count("\n", 0, start) + 1, text


def python_strings(source: str) -> Iterator[tuple[int, str]]:
    """(line, text) of each string constant of the Python source but docstrings and other bare string statements."""
    tree = ast.parse(source)
    bare = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in bare:
            yield node.lineno, node.value


def sql_texts(root: Path, path: str) -> Iterator[tuple[int, str]]:
    """(first line, SQL) of the file: the whole of a .sql file, the string literals holding an SQL keyword else."""
    source = (root / path).read_text(encoding="utf-8")
    if path.endswith(".sql"):
        yield 1, source
        return
    literals = java_strings(source) if path.endswith(".java") else python_strings(source)
    yield from ((line, text) for line, text in literals if SQL_KEYWORD.search(text))


@dataclass(frozen=True)
class SchemaRules:
    """tools/sql-schemas.yaml: every listed schema and the platform functions."""

    schemas: list[str]
    platform_functions: set[str]

    def qualified(self) -> re.Pattern[str]:
        return re.compile(QUALIFIED_NAME.format(schemas="|".join(self.schemas)), re.IGNORECASE)


def text_findings(
    location: tuple[str, int], original: str, service: dict[str, object], rules: SchemaRules
) -> list[str]:
    """Findings for the SQL `original` of a service, which starts at line location[1] of file location[0]."""
    path, first_line = location
    own = str(service["schema"])
    findings = search_path_findings(location, original, own, rules.schemas)
    sql = blank_noise(original)
    for match in rules.qualified().finditer(sql):
        schema, name, call = match.group(1).lower(), match.group(2), match.group(3)
        listed = schema == "platform" and service["platform_functions"] and call and name in rules.platform_functions
        if schema != own and not listed:
            findings.append(
                f"{path}:{first_line + sql.count(chr(10), 0, match.start())}: {schema}.{name}; the SQL of a service"
                f" names only its own schema {own} and the listed platform functions (tools/sql-schemas.yaml)"
            )
    return findings


def sql_findings(root: Path, rules_file: Path) -> list[str]:
    loaded = yaml.safe_load(rules_file.read_text(encoding="utf-8"))
    services: dict[str, dict[str, object]] = loaded["services"]
    schemas = [str(service["schema"]) for service in services.values()] + list(loaded["other_schemas"])
    rules = SchemaRules(schemas, set(loaded["platform_functions"]))
    findings = []
    for path in sorted({*files(root, ".sql"), *files(root, ".java"), *files(root, ".py")}):
        parts = path.split("/")
        service = services.get(parts[1]) if parts[0] == "services" and len(parts) > 2 else None
        if service is not None:
            for first_line, original in sql_texts(root, path):
                findings += text_findings((path, first_line), original, service, rules)
    return findings


def size_findings(root: Path) -> list[str]:
    findings = []
    for path in files(root, ".py"):
        if path.startswith(("services/", "libs/")):
            lines = len((root / path).read_text(encoding="utf-8").splitlines())
            if lines > MODULE_LINES:
                findings.append(f"{path}: {lines} lines, a Python module is at most {MODULE_LINES} (SA-2.3-2)")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("check", choices=["language", "sql-schemas", "size"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    if arguments.check == "language":
        findings = language_findings(root)
    elif arguments.check == "sql-schemas":
        findings = sql_findings(root, Path(__file__).resolve().parent / "sql-schemas.yaml")
    else:
        findings = size_findings(root)
    for finding in findings:
        print(f"check-{arguments.check}: {finding}")
    if findings:
        print(f"check-{arguments.check}: failed, {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
