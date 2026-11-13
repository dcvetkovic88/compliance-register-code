"""The repository structure checks (T1.12; 111-FR17, 111-FR23, 111-AC17, 111-AC23; conventions section 6).

language: Python product code lives only in services/ai-document; Python elsewhere is tooling (tools/, tests/,
deploy/, contracts/scripts) and never sits in services/, libs/, apps/ or packages/. Java lives only in services/
(not in the Python service), libs/ and tools/arch-rules (suite readiness rule 6).
sql-schemas: the SQL files of services/<folder> name only the folder's own schema and, unless the service has no
usage on schema platform, the platform functions of tools/sql-schemas.yaml, called (suite readiness rule 3).
Comments and string literals are not read.
size: a Python module of services/ or libs/ is at most 300 lines (SA-2.3-2).
Build output, dependencies, virtual environments and test fixtures are never read.
"""

import argparse
import re
import sys
from collections.abc import Iterator
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


def sql_findings(root: Path, rules_file: Path) -> list[str]:
    rules = yaml.safe_load(rules_file.read_text(encoding="utf-8"))
    services: dict[str, dict[str, object]] = rules["services"]
    schemas = [str(service["schema"]) for service in services.values()] + list(rules["other_schemas"])
    qualified = re.compile(QUALIFIED_NAME.format(schemas="|".join(schemas)), re.IGNORECASE)
    platform_functions = set(rules["platform_functions"])
    findings = []
    for path in files(root, ".sql"):
        parts = path.split("/")
        service = services.get(parts[1]) if parts[0] == "services" and len(parts) > 2 else None
        if service is None:
            continue
        sql = blank_noise((root / path).read_text(encoding="utf-8"))
        for match in qualified.finditer(sql):
            schema, name, call = match.group(1).lower(), match.group(2), match.group(3)
            listed = schema == "platform" and service["platform_functions"] and call and name in platform_functions
            if schema != service["schema"] and not listed:
                line = sql.count("\n", 0, match.start()) + 1
                findings.append(
                    f"{path}:{line}: {schema}.{name}; the SQL of a service names only its own schema"
                    f" {service['schema']} and the listed platform functions (tools/sql-schemas.yaml)"
                )
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
