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

function el(tag: string, attrs: Record<string, string> = {}, text = ""): HTMLElement {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text) e.textContent = text;
  return e;
}

// --- settings persistence: Electron IPC when present, else localStorage in a browser
async function getEngine(): Promise<string> {
  if (window.functionsApp) return (await window.functionsApp.getSettings()).engine;
  return localStorage.getItem("engine") ?? "docker";
}
async function setEngine(value: string): Promise<void> {
  if (window.functionsApp) await window.functionsApp.setEngine(value);
  else localStorage.setItem("engine", value);
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
      for (const f of browser.filtered())
        list.append(el("div", { class: "fn" }, `${f.ref_id}  ·  ${f.runtime}`));
      if (browser.filtered().length === 0) list.append(el("div", { class: "muted" }, "(none installed)"));
    } catch {
      list.append(el("div", { class: "muted" }, "could not reach orchestrator"));
    }
  })();

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
      await rc.startAndWatch(DEMO);
    } catch {
      consoleEl.textContent = "run failed to start";
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
  panel.append(el("div", { class: "section-label" }, "ENGINE"));
  const opts = el("div", { class: "engine-options" });
  const note = el("div", { class: "saved-note" }, "");
  const current = await getEngine();

  const choices: [string, string][] = [
    ["docker", "Docker — run pipelines in sandboxed containers"],
    ["local", "Local — run pipelines as host processes"],
  ];
  for (const [value, desc] of choices) {
    const label = el("label", { class: "engine-opt" });
    const radio = el("input", { type: "radio", name: "engine", value }) as HTMLInputElement;
    radio.checked = value === current;
    radio.onchange = async () => {
      note.textContent = "saving…";
      await setEngine(value);
      note.textContent = `Saved — engine: ${value} (applies to new runs)`;
    };
    label.append(radio, el("span", {}, desc));
    opts.append(label);
  }
  panel.append(opts, note);
  return view;
}

function main(): void {
  const app = document.getElementById("app")!;
  app.innerHTML = "";

  const topbar = el("div", { class: "topbar" });
  const brand = el("div", { class: "brand" }, "⛓️ functions — Studio");
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
