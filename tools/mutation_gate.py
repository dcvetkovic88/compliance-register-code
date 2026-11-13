"""tools/mutation-gate: PIT on the Java classes a pull request changes (T1.7; SA-3-4, SA-4-6; PQ-23, OD-25).

The changed classes are the files under `<module>/src/main/java` that `git diff <base>...HEAD` adds, edits or
renames, where `<module>` is a module of the Maven reactor (the `<module>` entries of the root `pom.xml` and its
profiles whose `pom.xml` exists); sources elsewhere, such as test fixtures, are skipped. PIT mutates each changed
class with its nested and anonymous classes, using the module's own tests. The gate fails when the mutation score of the changed
classes in the gated layers of `tdd-profile.yaml` (`domain`, `application`) is below its threshold; classes of
the reported layers (`adapters`) and of no layer are scored and never fail it.
"""

import argparse
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

import yaml

SOURCES = "/src/main/java/"
REPORT = "target/pit-reports/mutations.xml"
POM = "{http://maven.apache.org/POM/4.0.0}"


@dataclass(frozen=True)
class Profile:
    threshold_percent: int
    gated_layers: tuple[str, ...]
    reported_layers: tuple[str, ...]


@dataclass(frozen=True)
class ChangedClass:
    module: str
    name: str

    def layer(self, profile: Profile) -> str:
        """`gated`, `reported` or `other`, from the package segments of the class."""
        segments = self.name.split(".")[:-1]
        if any(layer in segments for layer in profile.gated_layers):
            return "gated"
        if any(layer in segments for layer in profile.reported_layers):
            return "reported"
        return "other"


def read_profile(root: Path) -> Profile:
    mutation = yaml.safe_load((root / "tdd-profile.yaml").read_text(encoding="utf-8"))["mutation"]
    return Profile(
        threshold_percent=int(mutation["threshold_percent"]),
        gated_layers=tuple(mutation["gated_layers"]),
        reported_layers=tuple(mutation["reported_layers"]),
    )


def reactor_modules(root: Path, folder: str = ".") -> set[str]:
    """The folders of the reactor modules under `folder`, relative to the root, read from the `<module>` entries."""
    pom = root / folder / "pom.xml"
    if not pom.is_file():
        return set()
    modules = {folder}
    for entry in ElementTree.parse(pom).getroot().iter(f"{POM}module"):
        child = (Path(folder) / (entry.text or "").strip()).as_posix()
        modules |= reactor_modules(root, child)
    return modules


def changed_classes(root: Path, base: str) -> list[ChangedClass]:
    names = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AMR", f"{base}...HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    modules = reactor_modules(root)
    classes = []
    for name in names:
        if name.endswith(".java") and SOURCES in f"/{name}":
            module, source = f"/{name}".split(SOURCES, 1)
            module = module.strip("/") or "."
            if module not in modules:
                print(f"mutation-gate: {name}: outside the Maven reactor, skipped")
                continue
            classes.append(ChangedClass(module, source.removesuffix(".java").replace("/", ".")))
    return classes


def run_pit(root: Path, module: str, classes: list[ChangedClass]) -> Path:
    targets = ",".join(f"{changed.name},{changed.name}$*" for changed in classes)
    command = ["./mvnw", "-B", "-ntp", "-q", "-pl", module, "-am", "test-compile"]
    command += ["org.pitest:pitest-maven:mutationCoverage", f"-DtargetClasses={targets}"]
    print(f"mutation-gate: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=root, check=True)
    return root / module / REPORT


def read_scores(report: Path) -> dict[str, tuple[int, int]]:
    """Detected and total mutants per class; a nested class counts for its top-level class."""
    scores: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for mutation in ElementTree.parse(report).getroot().iter("mutation"):
        name = (mutation.findtext("mutatedClass") or "").split("$")[0]
        scores[name][0] += mutation.get("detected") == "true"
        scores[name][1] += 1
    return {name: (detected, total) for name, (detected, total) in scores.items()}


def percent(detected: int, total: int) -> int:
    return 100 if total == 0 else detected * 100 // total


def describe(detected: int, total: int) -> str:
    return "no changed class" if total == 0 else f"{percent(detected, total)} percent of {total} mutants"


def judge(profile: Profile, classes: list[ChangedClass], scores: dict[str, tuple[int, int]]) -> bool:
    """Print the score of every changed class and of each layer; true when the gated layers pass."""
    totals = {"gated": [0, 0], "reported": [0, 0], "other": [0, 0]}
    for changed in classes:
        detected, total = scores.get(changed.name, (0, 0))
        layer = changed.layer(profile)
        totals[layer][0] += detected
        totals[layer][1] += total
        print(f"mutation-gate: {changed.name}: {detected} of {total} mutants killed ({layer})")
    gated, reported, other = totals["gated"], totals["reported"], totals["other"]
    print(f"mutation-gate: {' and '.join(profile.gated_layers)}: {describe(*gated)}")
    print(f"mutation-gate: {', '.join(profile.reported_layers)} (reported only): {describe(*reported)}")
    print(f"mutation-gate: classes of no layer (reported only): {describe(*other)}")
    if percent(*gated) < profile.threshold_percent:
        print(
            f"mutation-gate: failed, the changed {' and '.join(profile.gated_layers)} classes score"
            f" {percent(*gated)} percent, below the threshold of {profile.threshold_percent} percent"
            " (tdd-profile.yaml)"
        )
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/mutation-gate", description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base", default="origin/main", help="the commit the pull request starts from")
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    profile = read_profile(root)
    classes = changed_classes(root, arguments.base)
    if not classes:
        print("mutation-gate: no changed Java class, nothing to mutate")
        return 0
    by_module: dict[str, list[ChangedClass]] = defaultdict(list)
    for changed in classes:
        by_module[changed.module].append(changed)
    scores: dict[str, tuple[int, int]] = {}
    for module, module_classes in sorted(by_module.items()):
        scores.update(read_scores(run_pit(root, module, module_classes)))
    return 0 if judge(profile, classes, scores) else 1


if __name__ == "__main__":
    sys.exit(main())
