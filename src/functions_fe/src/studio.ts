// Studio browser entry — thin DOM layer over the tested view-models.
// Bundled by esbuild into dist/studio.js and served by the orchestrator.
import { ApiClient } from "./api";
import { FunctionBrowser } from "./browser";
import { RunConsole } from "./runConsole";
import type { PipelineManifest } from "./types";

declare global {
  interface Window {
    FUNCTIONS_TOKEN?: string;
    functionsApp?: {
      getSettings(): Promise<{ engine: string }>;
      setEngine(engine: string): Promise<{ engine: string }>;
    };
  }
}

const token = window.FUNCTIONS_TOKEN ?? "";
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

const RUNTIMES = new Set(["python", "bash", "claude", "custom"]);

function el(tag: string, attrs: Record<string, string> = {}, text = ""): HTMLElement {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text) e.textContent = text;
  return e;
}

async function getEngine(): Promise<string> {
  if (window.functionsApp) return (await window.functionsApp.getSettings()).engine;
  return localStorage.getItem("engine") ?? "docker";
}
async function setEngine(value: string): Promise<void> {
  if (window.functionsApp) await window.functionsApp.setEngine(value);
  else localStorage.setItem("engine", value);
}

function chipClass(status: string): string {
  if (status === "running") return "chip-running";
  if (status === "done" || status === "ended") return "chip-done";
  if (status === "error") return "chip-error";
  return "chip-pending";
}

function renderConsole(rc: RunConsole, into: HTMLElement): void {
  into.innerHTML = "";
  const status = el("div", { class: "status" });
  status.append(el("span", {}, "run"), el("span", { class: `chip ${chipClass(rc.status)}` }, rc.status));
  into.append(status);
  for (const [id, s] of rc.steps) {
    const box = el("div", { class: "step" });
    const head = el("div", { class: "step-title" });
    head.append(el("span", { class: "step-name" }, id), el("span", { class: `chip ${chipClass(s.status)}` }, s.status));
    box.append(head);
    if (s.output) box.append(el("pre", {}, s.output));
    if (s.outputs) box.append(el("div", { class: "outputs" }, "outputs · " + JSON.stringify(s.outputs)));
    into.append(box);
  }
}

function buildMainView(): HTMLElement {
  const view = el("div", { class: "layout" });
  const side = el("div", { class: "sidebar" });
  const main = el("div", { class: "main" });
  view.append(side, main);

  side.append(el("h2", {}, "Functions"));
  const list = el("div", { class: "fn-list" });
  side.append(list);
  void (async () => {
    const browser = new FunctionBrowser(api);
    try {
      await browser.load();
      const fns = browser.filtered();
      for (const f of fns) {
        const row = el("div", { class: "fn" });
        row.append(el("span", { class: "fn-name" }, f.ref_id));
        const rt = RUNTIMES.has(f.runtime) ? f.runtime : "custom";
        row.append(el("span", { class: `badge badge-${rt}` }, f.runtime));
        list.append(row);
      }
      if (fns.length === 0) list.append(el("div", { class: "muted" }, "No functions installed."));
    } catch {
      list.append(el("div", { class: "muted" }, "Could not reach the orchestrator."));
    }
  })();

  const runBtn = el("button", { class: "btn" }, "▶  Run demo pipeline (greet → shout)") as HTMLButtonElement;
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
      await rc.startAndWatch(DEMO);
    } catch {
      consoleEl.textContent = "Run failed to start.";
      runBtn.disabled = false;
    }
  };
  return view;
}

async function buildSettingsView(): Promise<HTMLElement> {
  const view = el("div", { class: "settings-layout" });
  const menu = el("div", { class: "settings-sidebar" });
  menu.append(el("h2", {}, "Settings"));
  menu.append(el("div", { class: "menu-item active" }, "General"));
  const panel = el("div", { class: "settings-panel" });
  view.append(menu, panel);

  panel.append(el("h3", {}, "General"));
  panel.append(el("p", { class: "panel-sub" }, "Configure how pipelines run on this machine."));
  panel.append(el("div", { class: "section-label" }, "Engine"));

  const opts = el("div", { class: "engine-options" });
  const note = el("div", { class: "saved-note" }, "");
  const current = await getEngine();

  const choices: [string, string, string][] = [
    ["docker", "Docker", "Run pipelines in sandboxed containers."],
    ["local", "Local", "Run pipelines as host processes."],
  ];
  for (const [value, title, desc] of choices) {
    const label = el("label", { class: "engine-opt" });
    const radio = el("input", { type: "radio", name: "engine", value }) as HTMLInputElement;
    radio.checked = value === current;
    radio.onchange = async () => {
      note.textContent = "Saving…";
      await setEngine(value);
      note.textContent = `Saved · engine set to ${title} (applies to new runs)`;
    };
    const txt = el("div", { class: "opt-text" });
    txt.append(el("div", { class: "opt-title" }, title), el("div", { class: "opt-desc" }, desc));
    label.append(radio, txt);
    opts.append(label);
  }
  panel.append(opts, note);
  return view;
}

function main(): void {
  const app = document.getElementById("app")!;
  app.innerHTML = "";

  const topbar = el("div", { class: "topbar" });
  const brand = el("div", { class: "brand" });
  brand.append(el("span", { class: "logo" }, "⛓"));
  const wordmark = el("span", {});
  wordmark.append(document.createTextNode("functions "), el("span", { class: "brand-sub" }, "Studio"));
  brand.append(wordmark);
  const gear = el("button", { class: "icon-btn", title: "Settings" }, "⚙") as HTMLButtonElement;
  topbar.append(brand, gear);

  const content = el("div", { class: "content" });
  app.append(topbar, content);

  const showMain = () => {
    content.innerHTML = "";
    content.append(buildMainView());
    gear.classList.remove("active");
  };
  const showSettings = async () => {
    content.innerHTML = "";
    content.append(await buildSettingsView());
    gear.classList.add("active");
  };
  brand.onclick = showMain;
  gear.onclick = () => (gear.classList.contains("active") ? showMain() : void showSettings());

  showMain();
}

main();
