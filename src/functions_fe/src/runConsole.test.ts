import { describe, expect, it, vi } from "vitest";

import { RunConsole } from "./runConsole";
import type { RunEvent } from "./types";

const ev = (kind: string, step_id: string | null = null, payload: Record<string, unknown> | null = null): RunEvent => ({
  kind,
  run_id: "r",
  step_id,
  seq: 0,
  payload,
});

describe("RunConsole", () => {
  it("folds events into per-step state", () => {
    const rc = new RunConsole({} as never);
    rc.handle(ev("run_start"));
    expect(rc.status).toBe("running");
    rc.handle(ev("step_start", "a"));
    rc.handle(ev("text", "a", { text: "hello" }));
    rc.handle(ev("step_end", "a", { outputs: { x: 1 } }));
    rc.handle(ev("run_end"));
    const a = rc.steps.get("a")!;
    expect(a.status).toBe("done");
    expect(a.output).toBe("hello\n");
    expect(a.outputs).toEqual({ x: 1 });
    expect(rc.status).toBe("done");
    expect(rc.events).toHaveLength(5);
  });

  it("marks errors", () => {
    const rc = new RunConsole({} as never);
    rc.handle(ev("step_start", "a"));
    rc.handle(ev("error", "a", { returncode: 1 }));
    expect(rc.steps.get("a")!.status).toBe("error");
    expect(rc.status).toBe("error");
  });

  it("startAndWatch starts the run, wires ws, controls delegate", async () => {
    const fakeWs = { onmessage: null, onclose: null, onerror: null, close: () => {} } as never;
    const api = {
      startRun: vi.fn().mockResolvedValue("r1"),
      events: vi.fn().mockImplementation((_id: string, h: { onEvent: (e: RunEvent) => void }) => {
        h.onEvent(ev("run_start"));
        return fakeWs;
      }),
      pause: vi.fn().mockResolvedValue(undefined),
      resume: vi.fn().mockResolvedValue(undefined),
      end: vi.fn().mockResolvedValue(undefined),
    };
    const rc = new RunConsole(api as never);
    expect(await rc.startAndWatch({} as never, "/b")).toBe("r1");
    expect(rc.status).toBe("running");
    await rc.pause();
    await rc.resume();
    await rc.end();
    expect(api.pause).toHaveBeenCalledWith("r1");
    expect(api.resume).toHaveBeenCalledWith("r1");
    expect(api.end).toHaveBeenCalledWith("r1");
    expect(rc.status).toBe("ended");
  });

  it("controls no-op without a runId", async () => {
    const rc = new RunConsole({} as never);
    await rc.pause();
    await rc.resume();
    await rc.end();
    expect(rc.runId).toBeNull();
  });

  it("ws close finishes a running console", async () => {
    const fakeWs = { onmessage: null, onclose: null, onerror: null, close: () => {} } as never;
    const api = {
      startRun: vi.fn().mockResolvedValue("r"),
      events: vi.fn().mockImplementation((_id: string, h: { onEvent: (e: RunEvent) => void; onClose: () => void }) => {
        h.onEvent(ev("run_start"));
        h.onClose();
        return fakeWs;
      }),
    };
    const rc = new RunConsole(api as never);
    await rc.startAndWatch({} as never);
    expect(rc.status).toBe("done");
  });
});
