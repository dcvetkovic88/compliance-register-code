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
- `make suite S=<id>` (or `tools/suite <id>`) runs one suite in any language.
- `tools/check-suites --tasks <tasks.md>` fails when a finished block names a suite that is not
  registered, when a task of the block adds tests in a path with no entry for the block's suite,
  when a registered suite selects no test, or when an acceptance test name lacks the full
  criterion id (`109-F4-AC6 ...`). `--suite <id>` checks that suite's block before it is ticked.
