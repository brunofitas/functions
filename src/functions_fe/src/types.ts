// Shared types mirroring the functions_be contract (functions_shared / d_001).

export interface FunctionEntry {
  ref_id: string;
  runtime: string;
  dir: string;
}

export interface RunEvent {
  kind: string;
  run_id: string;
  step_id: string | null;
  seq: number;
  payload: Record<string, unknown> | null;
}

export interface Step {
  id: string;
  use: string;
  with: Record<string, unknown>;
}

export interface PipelineManifest {
  kind: "pipeline";
  namespace: string;
  name: string;
  steps: Step[];
  flow: { mode: string; end: { signal: string } };
}

export interface HttpResponse {
  ok: boolean;
  status: number;
  json(): Promise<unknown>;
}

export type FetchLike = (url: string, init?: RequestInit) => Promise<HttpResponse>;

export interface WebSocketLike {
  onmessage: ((e: { data: string }) => void) | null;
  onclose: (() => void) | null;
  onerror: (() => void) | null;
  close(): void;
}

export type WsFactory = (url: string) => WebSocketLike;
