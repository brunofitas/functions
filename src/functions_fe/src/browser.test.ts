import { describe, expect, it, vi } from "vitest";

import { FunctionBrowser } from "./browser";

const entries = [
  { ref_id: "aws/login@1", runtime: "claude", dir: "/a" },
  { ref_id: "gcp/auth@1", runtime: "bash", dir: "/b" },
];

describe("FunctionBrowser", () => {
  it("loads, lists runtimes, and filters by query + runtime", async () => {
    const api = { listFunctions: vi.fn().mockResolvedValue(entries) };
    const b = new FunctionBrowser(api as never);
    await b.load();
    expect(b.filtered()).toHaveLength(2);
    expect(b.runtimes()).toEqual(["bash", "claude"]);

    b.query = "AWS";
    expect(b.filtered().map((e) => e.ref_id)).toEqual(["aws/login@1"]);

    b.query = "";
    b.runtime = "bash";
    expect(b.filtered().map((e) => e.ref_id)).toEqual(["gcp/auth@1"]);
  });
});
