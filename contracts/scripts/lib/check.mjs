// contracts/scripts/check (plan D6; 111-FR5, 111-AC5): the drift check. Fails when a synced file does not match
// SOURCE.lock (any local edit), when a file is missing or not listed, and, given the spec checkout
// (--spec-repo or SPEC_REPO_DIR), when the lock is behind it. Then validates each OpenAPI file as 3.1 and the
// AsyncAPI file as 3.0, unless --skip-validation.
import { existsSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { CONTRACT_PATTERN, LOCK_NAME, contractsDir, parseOptions, sha256, specRepo } from "./frozen.mjs";
import { validationProblems } from "./validate.mjs";

function driftProblems(folder, repo) {
  const lock = JSON.parse(readFileSync(path.join(folder, LOCK_NAME), "utf8"));
  const problems = [];
  for (const [name, entry] of Object.entries(lock.files)) {
    const file = path.join(folder, name);
    if (!existsSync(file)) {
      problems.push(`${name} is missing; run contracts/scripts/sync`);
    } else if (sha256(file) !== entry.sha256) {
      problems.push(`${name} does not match ${LOCK_NAME}; it is synced, never edited by hand`);
    } else if (repo && sha256(path.join(repo, entry.source)) !== entry.sha256) {
      problems.push(`${name} is behind the spec repository; run contracts/scripts/sync`);
    }
  }
  for (const name of readdirSync(folder).filter((file) => CONTRACT_PATTERN.test(file))) {
    if (!(name in lock.files)) problems.push(`${name} is not in ${LOCK_NAME}; contracts come only from the sync`);
  }
  return problems;
}

const options = parseOptions(process.argv.slice(2), ["skip-validation"]);
const folder = contractsDir(options);
const problems = driftProblems(folder, specRepo(options));
if (problems.length === 0) console.log(`check: every contract in ${folder} matches ${LOCK_NAME}`);
if (!options["skip-validation"]) {
  const lock = JSON.parse(readFileSync(path.join(folder, LOCK_NAME), "utf8"));
  const present = Object.keys(lock.files).filter((name) => existsSync(path.join(folder, name)));
  problems.push(...(await validationProblems(folder, present)));
}
for (const problem of problems) console.log(`check: ${problem}`);
process.exitCode = problems.length > 0 ? 1 : 0;
