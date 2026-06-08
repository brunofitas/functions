import { describe, expect, it } from "vitest";

import { PipelineEditor } from "./editor";

describe("PipelineEditor", () => {
  it("builds, wires, validates, and exports a manifest", () => {
    const e = new PipelineEditor();
    expect(e.validate()).toContain("namespace is required");
    e.namespace = "acme";
    e.name = "deploy";
    e.addStep("aws/login@1", "login");
    const b = e.addStep("./build");
    expect(b).toBe("step2");
    e.setLiteral("login", "role", "admin");
    e.wire(b, "acct", "login", "account_id");
    expect(e.validate()).toEqual([]);
    const m = e.toManifest();
    expect(m.kind).toBe("pipeline");
    expect(m.steps[1].with.acct).toBe("${{ steps.login.outputs.account_id }}");
    expect(m.steps[0].with.role).toBe("admin");
  });

  it("reorders and removes steps", () => {
    const e = new PipelineEditor();
    e.namespace = "n";
    e.name = "p";
    e.addStep("a", "x");
    e.addStep("b", "y");
    e.addStep("c", "z");
    e.move("z", 0);
    expect(e.steps.map((s) => s.id)).toEqual(["z", "x", "y"]);
    e.removeStep("x");
    expect(e.steps.map((s) => s.id)).toEqual(["z", "y"]);
  });

  it("rejects duplicate ids, unknown refs, and invalid export", () => {
    const e = new PipelineEditor();
    e.addStep("a", "dup");
    expect(() => e.addStep("b", "dup")).toThrow();
    expect(() => e.wire("dup", "i", "missing", "o")).toThrow();
    expect(() => e.move("nope", 0)).toThrow();
    expect(() => new PipelineEditor().toManifest()).toThrow(/invalid pipeline/);
  });
});
