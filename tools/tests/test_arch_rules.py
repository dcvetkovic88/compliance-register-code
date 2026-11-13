"""tools/arch-rules, the shared ArchUnit rules of every Java service (T1.6; 111-FR17, 111-FR23, 111-AC17, 111-AC23).

The module's JUnit tests prove each rule AR-J0 to AR-J13 of conventions section 6 on a violating fixture
and every rule on a clean service fixture. This suite runs the module's build, its own quality tools
included, and reads the Surefire reports.
"""

import subprocess
from pathlib import Path
from xml.etree import ElementTree

import pytest
from conftest import TOOLS_DIR

pytestmark = pytest.mark.suite_111_B1b

REPO_ROOT = TOOLS_DIR.parent
MODULE = TOOLS_DIR / "arch-rules"
# AR-J5 does not exist: suite readiness rule 5 (React shell) has no Java rule.
RULES = [f"AR-J{number}" for number in [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13]]
# The six suite readiness rules of L1 section 11 that have a Java rule (conventions section 6).
READINESS_RULES = {"AR-J1": 1, "AR-J2": 2, "AR-J3": 3, "AR-J4": 4, "AR-J6": 6}


def outcomes(reports: Path) -> dict[str, str]:
    """Display name of every test case of the module, mapped to passed, failed or skipped."""
    results = {}
    for report in sorted(reports.glob("TEST-*.xml")):
        for case in ElementTree.parse(report).getroot().iter("testcase"):
            if case.find("skipped") is not None:
                results[case.get("name", "")] = "skipped"
            elif case.find("failure") is not None or case.find("error") is not None:
                results[case.get("name", "")] = "failed"
            else:
                results[case.get("name", "")] = "passed"
    return results


@pytest.fixture(scope="module")
def module_build():
    result = subprocess.run(
        ["./mvnw", "-B", "-ntp", "-pl", "tools/arch-rules", "-am", "verify"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result, outcomes(MODULE / "target/surefire-reports")


def test_111_ac23_arch_rules_module_builds_with_every_java_tool(module_build):
    result, _ = module_build

    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]


@pytest.mark.parametrize("rule", RULES)
def test_111_ac17_architecture_rule_fails_on_its_violating_fixture(module_build, rule):
    _, results = module_build
    fixture_tests = {name: outcome for name, outcome in results.items() if name.startswith(f"111-AC17 {rule} fails")}

    assert fixture_tests, f"no fixture test of {rule} ran; tests: {sorted(results)}"
    assert set(fixture_tests.values()) == {"passed"}, fixture_tests


def test_111_ac17_every_rule_passes_on_the_clean_service_fixture(module_build):
    _, results = module_build

    assert results.get("111-AC17 every rule passes on the clean service fixture") == "passed", sorted(results)


def test_111_ac17_the_six_suite_readiness_rules_are_named_in_the_rule_set():
    rules = (MODULE / "src/main/java/com/wisertech/register/archrules/ArchitectureRules.java").read_text(
        encoding="utf-8"
    )

    for rule, readiness_rule in READINESS_RULES.items():
        assert f'"{rule} ' in rules, rule
        assert f"suite readiness rule {readiness_rule}" in rules, readiness_rule
