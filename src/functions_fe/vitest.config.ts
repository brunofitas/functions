import { defineConfig } from "vitest/config";

// Frontend quality gate: ≥85% coverage, matching the Python modules.
// All functionality (incl. API calls to the be_ orchestrator) must be tested —
// network calls are mocked so the suite is hermetic.
export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: ["**/*.test.ts", "**/*.d.ts"],
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 85,
        statements: 85,
      },
    },
  },
});
