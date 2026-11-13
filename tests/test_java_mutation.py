"""Coverage and mutation for Java (T1.7; 111-FR23, 111-AC23; PQ-23, OD-25; conventions SA-3-4, SA-3-5, SA-4-5, SA-4-6).

`tools/mutation-gate` runs PIT on the Java classes a pull request changes and fails when the mutation score of
the changed classes in `domain` and `application` is below the threshold of `tdd-profile.yaml`; adapters are
reported only. JaCoCo reports coverage and never fails the build. The fixtures commit one change to a service
module in a temporary copy of the repository.
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.suite_111_B1b

FIXTURES = Path(__file__).parent / "fixtures/mutation"
MODULE = Path("services/platform")
DOMAIN = MODULE / "src/main/java/com/wisertech/register/services/platform/domain"
DOMAIN_TESTS = MODULE / "src/test/java/com/wisertech/register/services/platform/domain"
ADAPTER = MODULE / "src/main/java/com/wisertech/register/services/platform/adapters/out"
ADAPTER_TESTS = MODULE / "src/test/java/com/wisertech/register/services/platform/adapters/out"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture
def service_repo(repo_root, tmp_path):
    """A copy of the repository's Java build with an empty service module, committed as the base of a change."""
    repo = tmp_path / "repo"
    repo.mkdir()
    for name in ["pom.xml", "mvnw", "tdd-profile.yaml"]:
        if (repo_root / name).exists():
            shutil.copy2(repo_root / name, repo / name)
    for folder in [".mvn", "config"]:
        shutil.copytree(repo_root / folder, repo / folder)
    (repo / MODULE).mkdir(parents=True)
    shutil.copy2(FIXTURES / "pom.xml", repo / MODULE / "pom.xml")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", "base")
    return repo


def commit_change(repo: Path, files: dict[str, Path]) -> None:
    for source, target in files.items():
        (repo / target).mkdir(parents=True, exist_ok=True)
        shutil.copy2(FIXTURES / source, repo / target)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", "change")


def mutation_gate(repo_root: Path, repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo_root / "tools/mutation-gate"), "--root", str(repo), "--base", "HEAD~1"],
        check=False,
        capture_output=True,
        text=True,
    )


def test_111_ac23_tdd_profile_sets_the_mutation_threshold_at_the_root(repo_root):
    profile = yaml.safe_load((repo_root / "tdd-profile.yaml").read_text(encoding="utf-8"))

    assert profile["mutation"]["threshold_percent"] == 70
    assert profile["mutation"]["gated_layers"] == ["domain", "application"]
    assert profile["mutation"]["reported_layers"] == ["adapters"]
    assert profile["mutation"]["tools"] == {"java": "pit", "python": "mutmut"}
    assert profile["coverage"]["gate"] is False


def test_111_ac23_mutation_gate_fails_a_domain_change_whose_mutants_survive(repo_root, service_repo):
    commit_change(service_repo, {"domain/NoticePeriod.java": DOMAIN, "weak-test/NoticePeriodTest.java": DOMAIN_TESTS})

    result = mutation_gate(repo_root, service_repo)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "NoticePeriod" in result.stdout
    assert "below the threshold of 70 percent" in result.stdout + result.stderr


def test_111_ac23_mutation_gate_passes_a_domain_change_whose_mutants_are_killed(repo_root, service_repo):
    commit_change(service_repo, {"domain/NoticePeriod.java": DOMAIN, "strong-test/NoticePeriodTest.java": DOMAIN_TESTS})

    result = mutation_gate(repo_root, service_repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "domain and application: 100 percent" in result.stdout


def test_111_ac23_mutation_gate_reports_an_adapter_change_without_failing(repo_root, service_repo):
    commit_change(service_repo, {"adapter/NoticeStore.java": ADAPTER, "adapter-test/NoticeStoreTest.java": ADAPTER_TESTS})

    result = mutation_gate(repo_root, service_repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "NoticeStore" in result.stdout
    assert "adapters (reported only)" in result.stdout


def test_mutation_gate_passes_a_change_without_java_classes(repo_root, service_repo):
    (service_repo / "notes.md").write_text("a change without Java\n", encoding="utf-8")
    git(service_repo, "add", "-A")
    git(service_repo, "-c", "user.name=f", "-c", "user.email=f@example.invalid", "commit", "-q", "-m", "notes")

    result = mutation_gate(repo_root, service_repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "no changed Java class" in result.stdout


def test_111_ac23_jacoco_reports_coverage_without_failing_on_low_coverage(repo_root, service_repo):
    commit_change(service_repo, {"domain/NoticePeriod.java": DOMAIN, "weak-test/NoticePeriodTest.java": DOMAIN_TESTS})

    result = subprocess.run(
        ["./mvnw", "-B", "-ntp", "-q", "-pl", str(MODULE), "test"],
        cwd=service_repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (service_repo / MODULE / "target/site/jacoco/jacoco.xml").is_file()


def test_111_ac23_ci_gates_pull_requests_on_mutation_and_keeps_the_coverage_report(repo_root):
    workflow = yaml.safe_load((repo_root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    mutation = workflow["jobs"]["java-mutation"]
    runs = [str(step.get("run", "")) for step in mutation["steps"]]
    java_uploads = [step for step in workflow["jobs"]["java"]["steps"] if "upload-artifact" in step.get("uses", "")]

    assert mutation["if"] == "github.event_name == 'pull_request'"
    assert any("tools/mutation-gate --base" in run for run in runs)
    assert mutation["steps"][0]["with"]["fetch-depth"] == 0
    assert "java-mutation" in workflow["jobs"]["required"]["needs"]
    assert any("target/site/jacoco" in str(step["with"]["path"]) for step in java_uploads)
