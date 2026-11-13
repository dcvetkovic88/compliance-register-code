"""tools/python-mutation-gate: mutmut on the Python modules a pull request changes (T1.9; SA-3-4, SA-4-6; OD-25).

The changed modules are the files under `<project>/app/` that `git diff <base>...HEAD` adds, edits or renames,
where `<project>` is a uv project (a folder with `pyproject.toml`) outside the tools project and test fixtures.
mutmut mutates only those modules, in a copy of the project, and runs the project's tests (`tests/`); the
gate writes the mutmut configuration, so a project carries none. The gate fails when the mutation score of the
changed modules in the gated layers of `tdd-profile.yaml` (`domain`, `application`) is below its threshold;
modules of the reported layers (`adapters`) and of no layer (`api`, the composition root) are scored and never
fail it. A killed or timed-out mutant is detected; a skipped one is not counted.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from mutation_gate import Profile, describe, percent, read_profile

PACKAGE = "app"
DETECTED = {"killed", "timeout"}
NOT_COUNTED = {"skipped"}
COPY_IGNORED = shutil.ignore_patterns(".venv", "mutants", "__pycache__", ".*_cache", "coverage", ".coverage")


@dataclass(frozen=True)
class ChangedModule:
    project: str
    path: str  # relative to the project, as app/domain/notice_period.py

    @property
    def name(self) -> str:
        return self.path.removesuffix(".py").replace("/", ".")

    def layer(self, profile: Profile) -> str:
        """`gated`, `reported` or `other`, from the package segments of the module."""
        segments = self.path.split("/")[:-1]
        if any(layer in segments for layer in profile.gated_layers):
            return "gated"
        if any(layer in segments for layer in profile.reported_layers):
            return "reported"
        return "other"


def project_of(root: Path, path: Path) -> Path | None:
    """The uv project folder holding `path`, when `path` is in its `app` package."""
    for folder in path.parents:
        if folder == Path("."):
            return None
        if (root / folder / "pyproject.toml").exists():
            in_package = path.relative_to(folder).parts[0] == PACKAGE
            outside = folder.parts[0] == "tools" or "fixtures" in folder.parts
            return folder if in_package and not outside else None
    return None


def changed_modules(root: Path, base: str) -> list[ChangedModule]:
    diff = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AMR", f"{base}...HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    modules = []
    for line in diff.stdout.splitlines():
        path = Path(line)
        project = project_of(root, path) if path.suffix == ".py" else None
        if project is not None and (root / path).exists():
            modules.append(ChangedModule(project.as_posix(), path.relative_to(project).as_posix()))
    return modules


def run_mutmut(root: Path, project: str, modules: list[ChangedModule]) -> dict[str, str]:
    """Mutate `modules` in a copy of `project`; the status of every mutant by its name."""
    with tempfile.TemporaryDirectory(prefix="python-mutation-gate-") as scratch:
        copy = Path(scratch) / "project"
        shutil.copytree(root / project, copy, ignore=COPY_IGNORED)
        only_mutate = "".join(f"\n    {module.path}" for module in modules)
        settings = f"source_paths = {PACKAGE}\nonly_mutate ={only_mutate}\npytest_add_cli_args_test_selection = tests\n"
        (copy / "setup.cfg").write_text(f"[mutmut]\n{settings}", encoding="utf-8")
        mutmut = ["uv", "run", "--quiet", "--project", str(root / project), "--frozen", "mutmut"]
        subprocess.run([*mutmut, "run"], cwd=copy, check=True, capture_output=True, text=True)
        results = subprocess.run(
            [*mutmut, "results", "--all", "true"], cwd=copy, check=True, capture_output=True, text=True
        )
    statuses = {}
    for line in results.stdout.splitlines():
        name, separator, status = line.strip().rpartition(": ")
        if separator:
            statuses[name] = status
    return statuses


def score(module: ChangedModule, statuses: dict[str, str]) -> tuple[int, int]:
    """(detected, counted) mutants of one module."""
    own = [status for name, status in statuses.items() if name.startswith(f"{module.name}.")]
    counted = [status for status in own if status not in NOT_COUNTED]
    return sum(status in DETECTED for status in counted), len(counted)


def judge(profile: Profile, scores: dict[ChangedModule, tuple[int, int]]) -> bool:
    """Print the score of every changed module and of each layer; true when the gated layers pass."""
    totals = {"gated": [0, 0], "reported": [0, 0], "other": [0, 0]}
    for module, (detected, total) in scores.items():
        layer = module.layer(profile)
        totals[layer][0] += detected
        totals[layer][1] += total
        print(f"python-mutation-gate: {module.project}/{module.path}: {detected} of {total} mutants killed ({layer})")
    gated, reported, other = totals["gated"], totals["reported"], totals["other"]
    print(f"python-mutation-gate: {' and '.join(profile.gated_layers)}: {describe(*gated)}")
    print(f"python-mutation-gate: {', '.join(profile.reported_layers)} (reported only): {describe(*reported)}")
    print(f"python-mutation-gate: modules of no layer (reported only): {describe(*other)}")
    if percent(*gated) < profile.threshold_percent:
        print(
            f"python-mutation-gate: failed, the changed {' and '.join(profile.gated_layers)} modules score"
            f" {percent(*gated)} percent, below the threshold of {profile.threshold_percent} percent"
            " (tdd-profile.yaml)"
        )
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/python-mutation-gate", description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base", default="origin/main", help="the commit the pull request starts from")
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    profile = read_profile(root)
    modules = changed_modules(root, arguments.base)
    if not modules:
        print("python-mutation-gate: no changed Python module, nothing to mutate")
        return 0
    by_project: dict[str, list[ChangedModule]] = defaultdict(list)
    for module in modules:
        by_project[module.project].append(module)
    scores: dict[ChangedModule, tuple[int, int]] = {}
    for project, project_modules in sorted(by_project.items()):
        statuses = run_mutmut(root, project, project_modules)
        scores.update({module: score(module, statuses) for module in project_modules})
    return 0 if judge(profile, scores) else 1


if __name__ == "__main__":
    sys.exit(main())
