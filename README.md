# Wiser Compliance Register

The code repository of the Wiser Compliance Register, a standalone product built from the
specifications in the spec repository (`specs/111-register-foundation` is the foundation).

Status: blocks 1 (repository root and suites registry) and 1b (quality tooling, Java and
repository) of feature 111. The full README (install, stack, seed, reset, suites) is written in
block 15c.

## Layout

| Path | What it holds |
|---|---|
| `pom.xml`, `mvnw`, `.mvn/` | Maven parent of the Java services and libraries, with the wrapper. A module joins the build when its `pom.xml` exists |
| `package.json`, `package-lock.json` | npm workspace for `apps/*` and `packages/*` |
| `tools/pyproject.toml`, `tools/uv.lock` | the Python project of the repository tools; `services/ai-document` gets its own uv project |
| `Makefile` | the one entry point: `make lint`, `format-check`, `typecheck`, `test`, `suite S=<id>`, `ci`, `stack-up`, `stack-down` |
| `config/java/` | the Checkstyle and PMD rules every Java module runs |
| `tests/` | root-level tests (build files, registry, CI workflow, quality tooling) and their fixtures |

## Pinned versions

Rule (Dusan, 2026-11-13): a pin is the newest release that is at least 14 days old on the day it
is pinned, checked on the vendor's own release page. Each tool has one pin file; this table
repeats them and a root test keeps the two equal.

| Tool | Pin | Pin file | Released | Source |
|---|---|---|---|---|
| Java | `25.0.5` | `.java-version` (Temurin build in CI) | 2026-10-20 | oracle.com JDK 25.0.5 release notes |
| Maven | `3.9.16` | `.mvn/wrapper/maven-wrapper.properties` | 2026-05-13 | repo.maven.apache.org |
| Spring Boot | `4.1.2` | `pom.xml` parent | 2026-10-23 | spring.io blog (OD-12) |
| Spring Cloud | `2025.1.4` | `pom.xml` property | 2026-10-23 | spring.io blog (research R-1) |
| Node | `26.13.0` | `.nvmrc` | 2026-10-28 | nodejs.org/dist/index.json (LTS) |
| npm | `11.20.0` | `package.json` `packageManager` | 2026-10-28 | bundled with Node 26.13.0 |
| Python | `3.12.16` | `.python-version` | 2026-10-25 | python.org |
| uv | `0.13.6` | `.uv-version` | 2026-10-27 | github.com/astral-sh/uv releases |
| PyYAML | `6.0.3` | `tools/pyproject.toml` | 2025-09-25 | pypi.org |
| pytest | `9.2.0` | `tools/pyproject.toml` | 2026-10-27 | pypi.org |
| Spotless Maven plugin | `3.10.4` | `pom.xml` property | 2026-10-08 | repo1.maven.org |
| palantir-java-format | `2.103.0` | `pom.xml` property | 2026-10-27 | repo1.maven.org |
| Checkstyle Maven plugin | `3.6.0` | `pom.xml` property | 2024-10-22 | repo1.maven.org |
| Checkstyle | `14.3.0` | `pom.xml` property | 2026-09-27 | repo1.maven.org |
| PMD Maven plugin | `3.28.0` | `pom.xml` property | 2025-10-07 | repo1.maven.org |
| PMD | `7.29.0` | `pom.xml` property | 2026-10-30 | repo1.maven.org |
| Error Prone | `2.51.0` | `pom.xml` property | 2026-10-22 | repo1.maven.org |
| NullAway | `0.14.3` | `pom.xml` property | 2026-10-22 | repo1.maven.org |
| JSpecify | `1.0.1` | `pom.xml` property | 2026-07-29 | repo1.maven.org |

Maven Enforcer, the compiler and Surefire plugins and JUnit come with the Spring Boot parent.
Keycloak, PostgreSQL, React, Vite, TypeScript, Vitest and Playwright are pinned by the blocks
that add them, under the same rule, and are added to this table then.

## Check suites

Every block of a tasks.md names one check suite, for example `111-B1`. A suite is the set of
tests that carry its tag (JUnit `@Tag`, a pytest marker, the id in a Vitest or Playwright title).

- Each path lists its suites in its own `suites.yaml`; this root's `suites.yaml` holds the
  root-level suites. The registry is all of these files together.
- A suite is the union of the entries with its id, so a block whose tests span several paths
  registers the suite once in each path. Every task that adds tests registers the block's suite
  in the `suites.yaml` of its own path, and every block's last task adds its suite to the
  `suites.yaml` of its own path.
- `make suite S=<id>` (or `tools/suite <id>`) runs one suite in any language and writes one
  JUnit XML report per entry, at `.suite-reports/<id>/<path>-<runner>-<selector>.xml`: pytest
  `--junitxml`, the Vitest and Playwright JUnit reporters, the Surefire reports of the module, one
  case per script. Two entries of one suite in one path with one runner need different selectors,
  or the registry refuses them. A Maven suite builds its module with `-pl <module> -am`, so the
  libraries it depends on are built first.
- `tools/check-suites --tasks <tasks.md>` reads the JUnit XML reports `tools/suite` writes
  (`--reports <folder>`, default `.suite-reports`), never the test sources, so run the suites
  first. Only a test that ran counts: a skipped, disabled or deselected test, or a parametrized
  test with no cases, does not. The check fails when a registered suite has no report or ran no
  test, when a test name cites a criterion without its full id (`109-F4-AC6 ...`), and, for every
  ticked block, when the block names a suite that is not registered, when a task of the block
  adds tests in a path with no entry for the block's suite, or when a criterion the block proves
  has no acceptance test: a test of its suite that ran and whose reported name (for JUnit, its
  display name) starts with the full criterion id. `--block <suite id>` also checks the block
  being built, named in any case, and fails when no block of the tasks files has that suite;
  blocks still to come are never checked (OD-22, OD-23).

## Java quality tools

Every Java module runs them through the parent `pom.xml` (conventions section 5, T1.5):

| Goal | Tool | What fails the build |
|---|---|---|
| `validate` (`make format-check`) | Maven Enforcer | Lombok; a database driver other than PostgreSQL's; a dependency on a service, that is on group id `com.wisertech.register.services`, which every service module uses |
| `validate` | Spotless with palantir-java-format | a file that is not formatted; `./mvnw spotless:apply` formats it |
| `compile` (`make typecheck`) | Error Prone with NullAway | an Error Prone error; a possible `null` across a method boundary in `com.wisertech.register` (mark an allowed one `@Nullable`, JSpecify) |
| `verify` (`make lint`) | Checkstyle (`config/java/checkstyle.xml`) | naming; class names ending in Manager, Helper, Util, Utils, Processor, Handler, Data or Info; a TODO without its issue, written `TODO(#123)`; a port (`...Port`) or adapter type without a doc comment |
| `verify` | PMD (`config/java/pmd.xml`) | a method over 30 lines, a class over 300 lines, more than 4 parameters, control statements nested more than 3 deep, cyclomatic complexity over 10, an unused parameter, `System.out` |

An exception to a size limit is a `@SuppressWarnings("PMD.<Rule>")` with a one-line comment giving
the reason, and is listed in the pull request body (SA-2.3-7). `tools/quality <check> java` runs one
check for Java only.

## CI

`.github/workflows/ci.yml` runs on every pull request to `main`: install from the lock files
(`tools/install`); lint, format check, type check and unit tests; one job per registered suite
(a suite marked `stack: true` starts the dev stack on the runner first), each keeping its JUnit XML
reports, then the registry check on the reports of every suite job; one job that builds the web
and runs the browser specs. The job `required` is the status check that branch protection on
`main` requires. It needs install, the suites and the registry check (block 1) and the Java job
of block 1b, which runs the Java lint, format check, type check and tests (OD-21). Until block 1c
(TypeScript, Python) adds its tools, `make lint`, `format-check`, `typecheck` and `test` fail and
name the missing tool, and no target passes without running a check. To check every tasks.md, CI checks out the spec repository named
by the repository variable `SPEC_REPO`, read with the secret `SPEC_REPO_TOKEN`; without them the
registry check fails, so the tasks.md checks never skip. On a pull request the registry check
also checks the block being built, named by the last part of the branch
(`<lane>/<functionality>-<block>`, so `lane/platform/111-b1` checks block `111-B1`); a branch that
names no block of the tasks files fails the check.

`make ci` runs what the required jobs run: install, every registered suite, then the registry
check on their reports; a failing suite does not stop the others or the check. `SPEC_REPO=<spec repository checkout>` adds every `specs/*/tasks.md` to the registry check
and `BLOCK=<suite id>` also checks the block being built.
