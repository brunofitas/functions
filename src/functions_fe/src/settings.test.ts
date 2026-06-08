import { describe, expect, it, vi } from "vitest";

import { SettingsModel } from "./settings";

describe("SettingsModel", () => {
  it("tracks env/secrets/folders and never exposes secret values in view", () => {
    const s = new SettingsModel();
    s.setEnv("REGION", "eu");
    s.setSecret("TOKEN", "s3cr3t");
    s.addFolder("/work");
    s.addFolder("/work"); // dedup
    const v = s.view();
    expect(v.env).toEqual({ REGION: "eu" });
    expect(v.secretNames).toEqual(["TOKEN"]);
    expect(v.folders).toEqual(["/work"]);
    expect(JSON.stringify(v)).not.toContain("s3cr3t");
    expect(s.hasPendingSecretValues()).toBe(true);
  });

  it("save persists values once, then drops them", async () => {
    const s = new SettingsModel();
    s.setEnv("A", "1");
    s.setSecret("T", "v");
    s.addFolder("/x");
    const persist = vi.fn().mockResolvedValue(undefined);
    await s.save(persist);
    expect(persist).toHaveBeenCalledWith({ env: { A: "1" }, secrets: { T: "v" }, folders: ["/x"] });
    expect(s.hasPendingSecretValues()).toBe(false);
  });
});
