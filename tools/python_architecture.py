"""AR-P1, the grain rule on the Python models (T1.9; conventions section 6, suite readiness rule 1; 111-AC17).

A class that declares a field `obligation_id` also declares `regulation_version`: an obligation is always the
pair. import-linter checks imports only, so this rule is a pytest architecture test: the root test suite runs it
on every `services/*/app` package, and a service's own tests may call `models_without_grain`.
Usage: python tools/python_architecture.py <package folder> prints one line per class that breaks the rule and
exits 1 when there is one.
"""

import ast
import sys
from collections.abc import Iterator
from pathlib import Path

OBLIGATION = "obligation_id"
VERSION = "regulation_version"


def field_names(model: ast.ClassDef) -> set[str]:
    """The names a class body declares: annotated fields (dataclasses, Pydantic, TypedDict) and assignments."""
    names: set[str] = set()
    for statement in model.body:
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            names.add(statement.target.id)
        elif isinstance(statement, ast.Assign):
            names.update(target.id for target in statement.targets if isinstance(target, ast.Name))
    return names


def models(module: Path) -> Iterator[ast.ClassDef]:
    tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
    yield from (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def models_without_grain(package: Path) -> list[str]:
    """One line per class under `package` with `obligation_id` and no `regulation_version`."""
    violations = []
    for module in sorted(package.rglob("*.py")):
        for model in models(module):
            names = field_names(model)
            if OBLIGATION in names and VERSION not in names:
                path = module.relative_to(package.parent).as_posix()
                violations.append(f"{path}: {model.name} has {OBLIGATION} without {VERSION} (AR-P1)")
    return violations


def main(argv: list[str]) -> int:
    violations = [line for package in argv for line in models_without_grain(Path(package))]
    for line in violations:
        print(line)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
