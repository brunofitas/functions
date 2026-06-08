// functions — Studio GUI client + view-models.
// These hold all GUI logic and API/WS calls (fully tested); a thin DOM/React layer
// renders them. Surfaces: run console (fe_001), browser (fe_002), pipeline editor
// (fe_003), function creator (fe_004), settings (fe_005).

export const VERSION = "0.0.1";

export { ApiClient, ApiError } from "./api";
export type { EventHandlers } from "./api";
export { RunConsole } from "./runConsole";
export type { StepState } from "./runConsole";
export { FunctionBrowser } from "./browser";
export { PipelineEditor } from "./editor";
export { FunctionCreator, RUNTIME_TEMPLATES } from "./creator";
export type { Scaffold } from "./creator";
export { SettingsModel } from "./settings";
export type { Persister, SettingsPayload } from "./settings";
export type * from "./types";
