// Validation of the synced contracts (plan D6; 111-FR5, 111-AC5): each OpenAPI file is valid OpenAPI 3.1 and
// the AsyncAPI file is valid AsyncAPI 3.0. Returns one problem per file that is not.
import { readFileSync } from "node:fs";
import path from "node:path";
import { Parser } from "@asyncapi/parser";
import { parse as parseOpenApi, validate as validateOpenApi } from "@readme/openapi-parser";

const ERROR = 0;

async function openApiProblem(file, name) {
  const document = await parseOpenApi(file);
  if (!String(document.openapi ?? "").startsWith("3.1.")) {
    return `${name} is not OpenAPI 3.1 (openapi: ${document.openapi})`;
  }
  const result = await validateOpenApi(file);
  if (!result.valid) {
    return `${name} is not valid OpenAPI 3.1:\n${result.errors.map((error) => error.message).join("\n")}`;
  }
  return undefined;
}

async function asyncApiProblem(file, name) {
  const { document, diagnostics } = await new Parser().parse(readFileSync(file, "utf8"), { source: file });
  const errors = diagnostics.filter((diagnostic) => diagnostic.severity === ERROR);
  const version = document?.version() ?? /^asyncapi:\s*(\S+)/m.exec(readFileSync(file, "utf8"))?.[1];
  if (!String(version ?? "").startsWith("3.0.")) return `${name} is not AsyncAPI 3.0 (asyncapi: ${version})`;
  if (errors.length > 0) {
    return `${name} is not valid AsyncAPI 3.0:\n${errors.map((error) => `${error.code}: ${error.message}`).join("\n")}`;
  }
  return undefined;
}

export async function validationProblems(folder, names) {
  const problems = [];
  for (const name of names) {
    const isAsyncApi = name.includes(".asyncapi.");
    const file = path.join(folder, name);
    const problem = await (isAsyncApi ? asyncApiProblem(file, name) : openApiProblem(file, name));
    if (problem) problems.push(problem);
    else console.log(`check: ${name} is valid ${isAsyncApi ? "AsyncAPI 3.0" : "OpenAPI 3.1"}`);
  }
  return problems;
}
