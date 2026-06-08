// Studio browser entry — thin DOM layer over the tested view-models.
// Bundled by esbuild into dist/studio.js and served by the orchestrator.
import { ApiClient } from "./api";
import { FunctionBrowser } from "./browser";
import { RunConsole } from "./runConsole";
import type { PipelineManifest } from "./types";

const token = (window as unknown as { FUNCTIONS_TOKEN?: string }).FUNCTIONS_TOKEN ?? "";
const api = new ApiClient(location.origin, token);

const DEMO: PipelineManifest = {
  kind: "pipeline",
  namespace: "demo",
  name: "hello",
  steps: [
    { id: "greet", use: "./greet", with: { name: "world" } },
    { id: "shout", use: "./shout", with: { greeting: "${{ steps.greet.outputs.greeting }}" } },
  ],
  flow: { mode: "standalone", end: { signal: "END" } },
};

function el(tag: string, attrs: Record<string, string> = {}, text = ""): HTMLElement {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text) e.textContent = text;
  return e;
}

function renderConsole(rc: RunConsole, into: HTMLElement): void {
  into.innerHTML = "";
  into.append(el("div", { class: "status" }, `run: ${rc.status}`));
  for (const [id, s] of rc.steps) {
    const box = el("div", { class: `step ${s.status}` });
    box.append(el("div", { class: "step-title" }, `${id} — ${s.status}`));
    if (s.output) box.append(el("pre", {}, s.output));
    if (s.outputs) box.append(el("div", { class: "outputs" }, "outputs: " + JSON.stringify(s.outputs)));
    into.append(box);
  }
}

async function main(): Promise<void> {
  const app = document.getElementById("app")!;
  app.append(el("h1", {}, "⛓️ functions — Studio"));

  const layout = el("div", { class: "layout" });
  const side = el("div", { class: "sidebar" });
  const main = el("div", { class: "main" });
  layout.append(side, main);
  app.append(layout);

  // Function library
  side.append(el("h2", {}, "Functions"));
  const list = el("div", { class: "fn-list" });
  side.append(list);
  try {
    const browser = new FunctionBrowser(api);
    await browser.load();
    for (const f of browser.filtered())
      list.append(el("div", { class: "fn" }, `${f.ref_id}  ·  ${f.runtime}`));
    if (browser.filtered().length === 0) list.append(el("div", { class: "muted" }, "(none installed)"));
  } catch {
    list.append(el("div", { class: "muted" }, "could not reach orchestrator"));
  }

  // Run console
  const runBtn = el("button", {}, "▶ Run demo pipeline (greet → shout)") as HTMLButtonElement;
  const consoleEl = el("div", { class: "console" });
  main.append(runBtn, consoleEl);

  runBtn.onclick = async () => {
    runBtn.disabled = true;
    const rc = new RunConsole(api);
    const orig = rc.handle.bind(rc);
    rc.handle = (e) => {
      orig(e);
      renderConsole(rc, consoleEl);
      if (rc.status !== "running") runBtn.disabled = false;
    };
    try {
      await rc.startAndWatch(DEMO); // base_dir defaults to the server's (examples/)
    } catch {
      consoleEl.textContent = "run failed to start";
      runBtn.disabled = false;
    }
  };
}

main();
