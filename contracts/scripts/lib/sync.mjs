// contracts/scripts/sync (plan D6; 111-FR5): copy the frozen files from the spec checkout byte for byte and
// rewrite SOURCE.lock with the spec commit and the SHA-256 of each file.
import { copyFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { FROZEN_FILES, LOCK_NAME, SPEC_FOLDER, contractsDir, git, parseOptions, sha256, specRepo } from "./frozen.mjs";

function fail(message) {
  console.error(`sync: ${message}`);
  process.exit(1);
}

const options = parseOptions(process.argv.slice(2));
const repo = specRepo(options);
if (!repo) fail("name the spec checkout with --spec-repo or SPEC_REPO_DIR");
const target = contractsDir(options);
const sources = FROZEN_FILES.map((name) => `${SPEC_FOLDER}/${name}`);
if (git(repo, "status", "--porcelain", "--", ...sources)) {
  fail(`the spec checkout ${repo} has uncommitted changes to the contracts; the lock records a commit`);
}
mkdirSync(target, { recursive: true });
const files = {};
for (const [index, name] of FROZEN_FILES.entries()) {
  copyFileSync(path.join(repo, sources[index]), path.join(target, name));
  files[name] = { source: sources[index], sha256: sha256(path.join(target, name)) };
  console.log(`sync: ${sources[index]} -> ${name}`);
}
const lock = { commit: git(repo, "rev-parse", "HEAD"), files };
writeFileSync(path.join(target, LOCK_NAME), `${JSON.stringify(lock, null, 2)}\n`);
console.log(`sync: ${LOCK_NAME} at spec commit ${lock.commit}`);
