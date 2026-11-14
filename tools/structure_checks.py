"""The repository structure checks (T1.12; 111-FR17, 111-FR23, 111-AC17, 111-AC23; conventions section 6).

language: Python product code lives only in services/ai-document; Python elsewhere is tooling (tools/, tests/,
deploy/, contracts/scripts) and never sits in services/, libs/, apps/ or packages/. Java lives only in services/
(not in the Python service), libs/ and tools/arch-rules (suite readiness rule 6).
sql-schemas: the SQL of services/<folder> names only the folder's own schema and, unless the service has no
usage on schema platform, the platform functions of tools/sql-schemas.yaml, called (suite readiness rule 3).
A listed schema is found wherever it qualifies a name. Any other qualifier but pg_catalog is a schema where
only a schema can qualify (a function call, a three-part name, a relation after FROM, JOIN, INTO, UPDATE, TABLE,
ON and the like or in a list after one, a type after ::), unless the SQL also holds it unqualified, as an alias
or a table does.
The SQL is that of the .sql files and of the string literals of the .java and .py files holding an SQL keyword
(the JdbcClient and psycopg queries, plan D3), string literals joined by + read as one; Java and Python comments
and docstrings are not read.
The body of a function, procedure or DO block in a string literal (AS '...', DO '...') is SQL and read as such.
A search_path, set by SET search_path, SET SCHEMA or set_config, names no schema but the folder's own and
pg_catalog, so no unqualified name reaches another schema. SQL comments and string literals are not read, but
the value of a search_path is.
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
IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
# schema, name, a call's parenthesis, a third part
QUALIFIED_NAME = re.compile(rf'"?\b({IDENTIFIER})\b"?\s*\.\s*"?({IDENTIFIER})"?(\s*\()?(\s*\.\s*"?[A-Za-z_])?')
SYSTEM_SCHEMA = "pg_catalog"
RELATION_KEYWORD = re.compile(
    r"(?:\b(?:FROM|JOIN|INTO|UPDATE|TABLE|ONLY|REFERENCES|TRUNCATE|VIEW|SEQUENCE|FUNCTION|PROCEDURE|ROUTINE|TYPE"
    r"|DOMAIN|CALL|COPY|USING|LOCK|EXISTS|ON)|::)\s*$",
    re.IGNORECASE,
)
UNQUALIFIED_NAME = re.compile(rf'(?<![\w$])"?({IDENTIFIER})"?(?![\w$])(?!\s*\.)')
# FROM of IS DISTINCT FROM and of these calls takes a column, which an alias may qualify; so does ON
FROM_CALLS = {"EXTRACT", "SUBSTRING", "TRIM", "OVERLAY"}
LOOK_BACK = 400  # characters read before a qualified name to find its keyword, enough for any list of relations
LIST_ITEM = re.compile(rf'"?{IDENTIFIER}"?(?:\s*\.\s*"?{IDENTIFIER}"?)*(?:\s+(?:AS\s+)?{IDENTIFIER})?\s*,\s*$')
SET_SEARCH_PATH = re.compile(
    r"\bSET\s+(?:SESSION\s+|LOCAL\s+)?(?:search_path\s*(?:TO|=)|SCHEMA\b)([^;]*)", re.IGNORECASE
)
# a string literal after these is the SQL body of a function, a procedure or a DO block
BODY_KEYWORD = re.compile(r"\b(?:AS|DO(?:\s+LANGUAGE\s+\w+)?)\s*$", re.IGNORECASE)
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
JAVA_PLUS = re.compile(r"\s*\+\s*")


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


def bodies(sql: str, blanked: str) -> Iterator[tuple[int, str]]:
    """(offset, SQL) of each function, procedure or DO body that `sql` holds in a string literal, quotes undone."""
    for noise in SQL_NOISE.finditer(sql):
        if noise.group().startswith("'") and BODY_KEYWORD.search(blanked, 0, noise.start()):
            yield noise.start() + 1, noise.group()[1:-1].replace("''", "'")


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


def search_path_findings(location: tuple[str, int], sql: str, own: str) -> list[str]:
    """Findings for each search_path of `sql`, which starts at line location[1] of file location[0]."""
    path, first_line = location
    blanked = blank_noise(sql)
    return [
        f"{path}:{first_line + blanked.count(chr(10), 0, offset)}: search_path {schema}; the search_path of a"
        f" service names only its own schema {own} (tools/sql-schemas.yaml)"
        for offset, schema in search_paths(sql, blanked)
        if schema not in (own, SYSTEM_SCHEMA)
    ]


def java_strings(source: str) -> Iterator[tuple[int, str]]:
    """(line, text) of each string literal and text block of the Java source, comments skipped, escapes undone;
    literals joined by + (comments between them skipped) are one text, at the line of the first."""
    chain: list[str] = []
    line, end, gap = 0, 0, ""
    for token in JAVA_TOKEN.finditer(source):
        if token.group().startswith("/"):
            gap, end = gap + source[end : token.start()], token.end()
            continue
        literal = token.group(1) if token.group(1) is not None else token.group(2)
        joined = literal is not None and JAVA_PLUS.fullmatch(gap + source[end : token.start()])
        if chain and not joined:
            yield line, "".join(chain)
            chain = []
        if literal is not None:
            line = line if chain else source.count("\n", 0, token.start()) + 1
            chain.append(
                JAVA_ESCAPE.sub(lambda escape: escape.group(1) if escape.group(1) in "\"'\\" else " ", literal)
            )
        gap, end = "", token.end()
    if chain:
        yield line, "".join(chain)


def python_strings(source: str) -> Iterator[tuple[int, str]]:
    """(line, text) of each string constant of the Python source but docstrings and other bare string statements."""
    tree = ast.parse(source)
    bare = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.expr) or id(node) in bare:
            continue
        text = constant_text(node)
        if text is not None:
            bare |= {id(part) for part in ast.walk(node)}
            yield node.lineno, text


def constant_text(node: ast.AST) -> str | None:
    """The text of a string constant or of string constants joined by +, None for any other expression."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = constant_text(node.left), constant_text(node.right)
        return left + right if left is not None and right is not None else None
    return None


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


def schema_position(sql: str, match: re.Match[str]) -> str | None:
    """Where the qualified name of `match` stands: "schema" where only a schema can qualify it (a function call, a
    three-part name, a relation after its keyword or in a list after one, a type after ::), "either" where an alias
    can qualify it too (after ON, after the FROM of IS DISTINCT FROM or of EXTRACT and the like), None elsewhere."""
    before = sql[max(0, match.start() - LOOK_BACK) : match.start()]
    start = len(before)
    while (relation := LIST_ITEM.search(before, 0, start)) is not None:
        start = relation.start()
    if match.group(3) or match.group(4):
        return "schema"
    keyword = RELATION_KEYWORD.search(before, 0, start)
    if keyword is None:
        return None
    word, ahead = keyword.group().strip().upper(), before[: keyword.start()]
    if word == "ON" or word == "FROM" and (re.search(r"\bDISTINCT\s*$", ahead, re.IGNORECASE) or open_call(ahead)):
        return "either"
    return "schema"


def open_call(text: str) -> bool:
    """Whether `text` ends inside an open parenthesis of one of FROM_CALLS."""
    depth = 0
    for index in range(len(text) - 1, -1, -1):
        depth += {")": 1, "(": -1}.get(text[index], 0)
        if depth < 0:
            name = re.search(rf"({IDENTIFIER})\s*$", text[:index])
            return name is not None and name.group(1).upper() in FROM_CALLS
    return False


def text_findings(
    location: tuple[str, int], original: str, service: dict[str, object], rules: SchemaRules
) -> list[str]:
    """Findings for the SQL `original` of a service, which starts at line location[1] of file location[0]."""
    path, first_line = location
    own = str(service["schema"])
    findings = search_path_findings(location, original, own)
    sql = blank_noise(original)
    for offset, body in bodies(original, sql):
        findings += text_findings((path, first_line + sql.count(chr(10), 0, offset)), body, service, rules)
    # names the SQL holds unqualified, as an alias or a table is; such a name may qualify a column where an alias can
    unqualified = {name.lower() for name in UNQUALIFIED_NAME.findall(sql)}
    for match in QUALIFIED_NAME.finditer(sql):
        schema, name, call = match.group(1).lower(), match.group(2), match.group(3)
        position = schema_position(sql, match)
        if schema in (own, SYSTEM_SCHEMA):
            continue
        if schema not in rules.schemas and (position is None or position == "either" and schema in unqualified):
            continue
        listed = schema == "platform" and service["platform_functions"] and call and name in rules.platform_functions
        if not listed:
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
