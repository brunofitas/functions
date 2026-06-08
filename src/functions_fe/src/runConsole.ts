// Run console view-model (fe_001): connect to a run, fold events into per-step state.

import type { ApiClient } from "./api";
import type { PipelineManifest, RunEvent, WebSocketLike } from "./types";

export interface StepState {
  status: "pending" | "running" | "done" | "error";
  output: string;
  outputs: Record<string, unknown> | null;
}

export class RunConsole {
  status: "idle" | "running" | "done" | "error" | "ended" = "idle";
  steps = new Map<string, StepState>();
  events: RunEvent[] = [];
  runId: string | null = null;
  private ws: WebSocketLike | null = null;

  constructor(private api: ApiClient) {}

  private step(id: string): StepState {
    let s = this.steps.get(id);
    if (!s) {
      s = { status: "pending", output: "", outputs: null };
      this.steps.set(id, s);
    }
    return s;
  }

  handle(event: RunEvent): void {
    this.events.push(event);
    const id = event.step_id;
    switch (event.kind) {
      case "run_start":
        this.status = "running";
        break;
      case "step_start":
        if (id) this.step(id).status = "running";
        break;
      case "text":
        if (id && event.payload && typeof event.payload.text === "string")
          this.step(id).output += event.payload.text + "\n";
        break;
      case "step_end":
        if (id) {
          const s = this.step(id);
          s.status = "done";
          s.outputs = (event.payload?.outputs as Record<string, unknown>) ?? null;
        }
        break;
      case "error":
        if (id) this.step(id).status = "error";
        this.status = "error";
        break;
      case "run_end":
        if (this.status === "running") this.status = "done";
        break;
      default:
        break;
    }
  }

  async startAndWatch(pipeline: PipelineManifest, baseDir?: string): Promise<string> {
    this.runId = await this.api.startRun(pipeline, baseDir);
    this.ws = this.api.events(this.runId, {
      onEvent: (e) => this.handle(e),
      onClose: () => {
        if (this.status === "running") this.status = "done";
      },
    });
    return this.runId;
  }

  async pause(): Promise<void> {
    if (this.runId) await this.api.pause(this.runId);
  }

  async resume(): Promise<void> {
    if (this.runId) await this.api.resume(this.runId);
  }

  async end(): Promise<void> {
    if (this.runId) {
      await this.api.end(this.runId);
      this.status = "ended";
    }
  }
}
