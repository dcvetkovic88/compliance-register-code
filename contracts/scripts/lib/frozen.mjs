// The frozen contract files and their lock (plan D6; 111-FR5). Shared by contracts/scripts/sync and check.
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const SPEC_FOLDER = "docs/standalone/contracts";
export const LOCK_NAME = "SOURCE.lock";
export const CONTRACTS_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
export const FROZEN_FILES = [
  "ai-document-service.openapi.yaml",
  "ict-risk-service.openapi.yaml",
  "monitoring-service.openapi.yaml",
  "platform.openapi.yaml",
  "register-events.asyncapi.yaml",
  "register-service.openapi.yaml",
  "web-bff.openapi.yaml",
];
export const CONTRACT_PATTERN = /\.(openapi|asyncapi)\.(ya?ml|json)$/;

export function sha256(file) {
  return createHash("sha256").update(readFileSync(file)).digest("hex");
}

export function git(repo, ...args) {
  return execFileSync("git", ["-C", repo, ...args], { encoding: "utf8" }).trim();
}

// The options of a script: --name value pairs and bare --flags.
export function parseOptions(argv, flags = []) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const name = argv[index].replace(/^--/, "");
    if (flags.includes(name)) {
      options[name] = true;
    } else {
      options[name] = argv[index + 1];
      index += 1;
    }
  }
  return options;
}

export function contractsDir(options) {
  return path.resolve(options.contracts ?? CONTRACTS_DIR);
}

export function specRepo(options) {
  const repo = options["spec-repo"] ?? process.env.SPEC_REPO_DIR;
  return repo ? path.resolve(repo) : undefined;
}
