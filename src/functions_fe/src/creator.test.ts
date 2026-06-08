import { describe, expect, it } from "vitest";

import { FunctionCreator, RUNTIME_TEMPLATES } from "./creator";

describe("FunctionCreator", () => {
  it("scaffolds every runtime with manifest, entrypoint, README, i18n", () => {
    const c = new FunctionCreator();
    for (const runtime of Object.keys(RUNTIME_TEMPLATES)) {
      const s = c.scaffold(runtime, "ns", "fn");
      expect(s.manifest.runtime).toBe(runtime);
      expect(s.manifest.kind).toBe("function");
      expect(s.files[RUNTIME_TEMPLATES[runtime].entrypoint]).toBeTruthy();
      expect(s.files["README.md"]).toContain("ns/fn");
      expect(s.files["i18n/en.json"]).toContain("fn");
      expect(s.testCommand).toEqual(["make", "test"]);
    }
  });

  it("rejects unknown runtime and missing names", () => {
    const c = new FunctionCreator();
    expect(() => c.scaffold("rust", "n", "f")).toThrow(/unknown runtime/);
    expect(() => c.scaffold("bash", "", "f")).toThrow(/required/);
  });
});
