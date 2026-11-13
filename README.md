# Wiser Compliance Register

The code repository of the Wiser Compliance Register, a standalone product built from the
specifications in the spec repository (`specs/111-register-foundation` is the foundation).

Status: block 1 of feature 111 (repository root and suites registry). The full README (install,
stack, seed, reset, suites) is written in block 15c.

## Layout

| Path | What it holds |
|---|---|
| `pom.xml`, `mvnw`, `.mvn/` | Maven parent of the Java services and libraries, with the wrapper. A module joins the build when its `pom.xml` exists |
| `package.json`, `package-lock.json` | npm workspace for `apps/*` and `packages/*` |
| `tools/pyproject.toml`, `tools/uv.lock` | the Python project of the repository tools; `services/ai-document` gets its own uv project |
| `Makefile` | the one entry point: `make lint`, `format-check`, `typecheck`, `test`, `suite S=<id>`, `ci`, `stack-up`, `stack-down` |
| `tests/` | root-level tests (build files, registry, CI workflow) |

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
  JUnit XML report per entry under `.suite-reports/<id>/`: pytest `--junitxml`, the Vitest and
  Playwright JUnit reporters, the Surefire reports of the module, one case per script. A Maven
  suite builds its module with `-pl <module> -am`, so the libraries it depends on are built first.
- `tools/check-suites --tasks <tasks.md>` reads the JUnit XML reports `tools/suite` writes
  (`--reports <folder>`, default `.suite-reports`), never the test sources, so run the suites
  first. Only a test that ran counts: a skipped, disabled or deselected test, or a parametrized
  test with no cases, does not. The check fails when a registered suite has no report or ran no
  test, when a test name cites a criterion without its full id (`109-F4-AC6 ...`), and, for every
  ticked block, when the block names a suite that is not registered, when a task of the block
  adds tests in a path with no entry for the block's suite, or when a criterion the block proves
  has no acceptance test: a test of its suite that ran and whose reported name (for JUnit, its
  display name) starts with the full criterion id. `--block <suite id>` also checks the block
  being built; blocks still to come are never checked (OD-22, OD-23).

## CI

`.github/workflows/ci.yml` runs on every pull request to `main`: install from the lock files
(`tools/install`); lint, format check, type check and unit tests; the registry check and one job
per registered suite (a suite marked `stack: true` starts the dev stack on the runner first); one
job that builds the web and runs the browser specs. The job `required` is the status check that
branch protection on `main` requires. In block 1 it needs install, the registry check and the
suites (OD-21): until blocks 1b (Java) and 1c (TypeScript, Python) add their tools,
`make lint`, `format-check`, `typecheck` and `test` fail and name the missing tool, and no target
passes without running a check. To check every tasks.md, CI checks out the spec repository named
by the repository variable `SPEC_REPO`, read with the secret `SPEC_REPO_TOKEN`; without them the
registry job fails, so the tasks.md checks never skip.

`make ci` runs what the required jobs run: install, the registry check and every registered
suite. `SPEC_REPO=<spec repository checkout>` adds every `specs/*/tasks.md` to the registry check
and `BLOCK=<suite id>` also checks the block being built.
