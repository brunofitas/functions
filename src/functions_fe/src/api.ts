// Typed client for the functions_be loopback API (be_011/be_013).
// All network access goes through here so it can be fully mocked in tests.

import type {
  FetchLike,
  FunctionEntry,
  PipelineManifest,
  RunEvent,
  WebSocketLike,
  WsFactory,
} from "./types";

export interface EventHandlers {
  onEvent: (event: RunEvent) => void;
  onClose?: () => void;
  onError?: () => void;
}

export class ApiError extends Error {}

/* v8 ignore start — real browser/runtime globals, exercised via injected mocks in tests */
const defaultFetch: FetchLike = (url, init) =>
  (globalThis as unknown as { fetch: FetchLike }).fetch(url, init);
const defaultWsFactory: WsFactory = (url) => new WebSocket(url) as unknown as WebSocketLike;
/* v8 ignore stop */

export class ApiClient {
  constructor(
    private baseUrl: string,
    private token: string,
    private fetchImpl: FetchLike = defaultFetch,
    private wsFactory: WsFactory = defaultWsFactory,
  ) {}

  private headers(): Record<string, string> {
    return { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" };
  }

  private async json(res: { ok: boolean; status: number; json(): Promise<unknown> }, what: string) {
    if (!res.ok) throw new ApiError(`${what}: HTTP ${res.status}`);
    return res.json();
  }

  async health(): Promise<unknown> {
    return this.json(await this.fetchImpl(`${this.baseUrl}/health`), "health");
  }

  async listFunctions(): Promise<FunctionEntry[]> {
    const data = (await this.json(
      await this.fetchImpl(`${this.baseUrl}/functions`, { headers: this.headers() }),
      "functions",
    )) as { functions: FunctionEntry[] };
    return data.functions;
  }

  async startRun(pipeline: PipelineManifest, baseDir?: string): Promise<string> {
    const data = (await this.json(
      await this.fetchImpl(`${this.baseUrl}/run`, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify({ pipeline, base_dir: baseDir }),
      }),
      "run",
    )) as { run_id: string };
    return data.run_id;
  }

  private async control(runId: string, action: "pause" | "resume" | "end"): Promise<void> {
    await this.json(
      await this.fetchImpl(`${this.baseUrl}/runs/${runId}/${action}`, {
        method: "POST",
        headers: this.headers(),
      }),
      action,
    );
  }

  pause(runId: string): Promise<void> {
    return this.control(runId, "pause");
  }

  resume(runId: string): Promise<void> {
    return this.control(runId, "resume");
  }

  end(runId: string): Promise<void> {
    return this.control(runId, "end");
  }

  private wsBase(): string {
    return this.baseUrl.replace(/^http/, "ws");
  }

  events(runId: string, handlers: EventHandlers): WebSocketLike {
    const ws = this.wsFactory(`${this.wsBase()}/events/${runId}?token=${this.token}`);
    ws.onmessage = (e) => handlers.onEvent(JSON.parse(e.data) as RunEvent);
    ws.onclose = () => handlers.onClose?.();
    ws.onerror = () => handlers.onError?.();
    return ws;
  }
}
