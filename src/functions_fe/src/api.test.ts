import { describe, expect, it, vi } from "vitest";

import { ApiClient, ApiError } from "./api";
import type { PipelineManifest } from "./types";

const res = (body: unknown, ok = true, status = 200) =>
  Promise.resolve({ ok, status, json: () => Promise.resolve(body) });

const PIPELINE: PipelineManifest = {
  kind: "pipeline",
  namespace: "n",
  name: "p",
  steps: [],
  flow: { mode: "standalone", end: { signal: "END" } },
};

describe("ApiClient", () => {
  it("health hits /health", async () => {
    const fetchImpl = vi.fn().mockReturnValue(res({ status: "ok" }));
    const api = new ApiClient("http://x", "tok", fetchImpl);
    expect(await api.health()).toEqual({ status: "ok" });
    expect(fetchImpl.mock.calls[0][0]).toBe("http://x/health");
  });

  it("listFunctions sends bearer token and unwraps list", async () => {
    const fetchImpl = vi
      .fn()
      .mockReturnValue(res({ functions: [{ ref_id: "a/b@1", runtime: "bash", dir: "/d" }] }));
    const api = new ApiClient("http://x", "tok", fetchImpl);
    const fns = await api.listFunctions();
    expect(fns[0].ref_id).toBe("a/b@1");
    expect(fetchImpl.mock.calls[0][1].headers.Authorization).toBe("Bearer tok");
  });

  it("throws ApiError on non-ok", async () => {
    const fetchImpl = vi.fn().mockReturnValue(res({}, false, 401));
    const api = new ApiClient("http://x", "tok", fetchImpl);
    await expect(api.listFunctions()).rejects.toBeInstanceOf(ApiError);
  });

  it("startRun posts pipeline + base_dir and returns run_id", async () => {
    const fetchImpl = vi.fn().mockReturnValue(res({ run_id: "r1" }));
    const api = new ApiClient("http://x", "tok", fetchImpl);
    expect(await api.startRun(PIPELINE, "/base")).toBe("r1");
    const init = fetchImpl.mock.calls[0][1];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body).base_dir).toBe("/base");
  });

  it("pause/resume/end hit the control endpoints", async () => {
    const fetchImpl = vi.fn().mockReturnValue(res({ status: "ok" }));
    const api = new ApiClient("http://x", "tok", fetchImpl);
    await api.pause("r");
    await api.resume("r");
    await api.end("r");
    expect(fetchImpl.mock.calls.map((c) => c[0])).toEqual([
      "http://x/runs/r/pause",
      "http://x/runs/r/resume",
      "http://x/runs/r/end",
    ]);
  });

  it("events opens ws (http→ws), parses messages, forwards close/error", () => {
    const fakeWs = { onmessage: null, onclose: null, onerror: null, close: vi.fn() } as any;
    const wsFactory = vi.fn().mockReturnValue(fakeWs);
    const api = new ApiClient("http://x", "tok", vi.fn(), wsFactory);
    const got: unknown[] = [];
    let closed = false;
    let errored = false;
    api.events("r1", {
      onEvent: (e) => got.push(e),
      onClose: () => (closed = true),
      onError: () => (errored = true),
    });
    expect(wsFactory.mock.calls[0][0]).toBe("ws://x/events/r1?token=tok");
    fakeWs.onmessage({ data: JSON.stringify({ kind: "text", payload: { text: "hi" } }) });
    fakeWs.onclose();
    fakeWs.onerror();
    expect((got[0] as { payload: { text: string } }).payload.text).toBe("hi");
    expect(closed && errored).toBe(true);
  });
});
