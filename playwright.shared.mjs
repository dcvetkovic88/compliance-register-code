// The Playwright settings the web's playwright.config merges (plan D23; conventions section 2, S1155; T1.10):
// a browser spec is a file ending in `.e2e.ts`, and only such a file runs.
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testMatch: /.*\.e2e\.ts$/,
  forbidOnly: true,
  reporter: [["list"], ["junit", { outputFile: "test-results/junit.xml" }]],
});
