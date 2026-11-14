// The Vitest settings every workspace merges into its own vitest.config (plan D23; conventions SA-4-5, SA-3-5;
// T1.10): unit and component tests are `<name>.test.ts(x)`, browser specs `.e2e.ts` never run here, a workspace
// with no test yet passes, and coverage is reported (text and Cobertura under coverage/), never a gate.
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["**/node_modules/**", "**/dist/**", "**/*.e2e.ts"],
    passWithNoTests: true,
    coverage: {
      enabled: true,
      provider: "v8",
      reporter: ["text", "cobertura"],
      reportsDirectory: "coverage",
    },
  },
});
