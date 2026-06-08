// Electron desktop shell (infra_004 + settings/window-state).
// Spawns the orchestrator (Docker or host engine, from saved settings), opens a native
// window restored to its last size/position, and persists settings locally.
const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");
const fs = require("node:fs");
const http = require("node:http");

const PORT = Number(process.env.FUNCTIONS_PORT || 8799);
const ROOT = path.resolve(__dirname, "..", "..", ".."); // repo root (…/functions)
const PYTHON = process.env.FUNCTIONS_PYTHON || path.join(ROOT, ".venv", "bin", "python");
const BASE_DIR = process.env.FUNCTIONS_BASE_DIR || "examples";

let orchestrator = null;
let win = null;
let settings = {};

// ---- local settings persistence (engine + window bounds) -------------------------
function settingsPath() {
  return path.join(app.getPath("userData"), "settings.json");
}
function loadSettings() {
  try {
    return JSON.parse(fs.readFileSync(settingsPath(), "utf8"));
  } catch {
    return {};
  }
}
function saveSettings() {
  try {
    fs.mkdirSync(path.dirname(settingsPath()), { recursive: true });
    fs.writeFileSync(settingsPath(), JSON.stringify(settings, null, 2));
  } catch (e) {
    console.error("settings save failed:", e.message);
  }
}
function engine() {
  return settings.engine === "local" ? "local" : "docker"; // default: docker
}

// ---- orchestrator lifecycle ------------------------------------------------------
function orchestratorSpec() {
  const dockerArgs =
    engine() === "local"
      ? []
      : ["--docker", "--image", process.env.FUNCTIONS_IMAGE || "python:3.12-slim"];
  if (app.isPackaged) {
    const res = process.resourcesPath;
    const exe = process.platform === "win32" ? "functions-orchestrator.exe" : "functions-orchestrator";
    return {
      cmd: path.join(res, "orchestrator", exe),
      args: ["--gui", "--gui-dir", path.join(res, "gui"), "--port", String(PORT),
             "--base-dir", path.join(res, "examples"), ...dockerArgs],
      cwd: res,
    };
  }
  return {
    cmd: PYTHON,
    args: ["-m", "functions_be", "--gui", "--port", String(PORT), "--base-dir", BASE_DIR, ...dockerArgs],
    cwd: ROOT,
  };
}
function startOrchestrator() {
  const { cmd, args, cwd } = orchestratorSpec();
  orchestrator = spawn(cmd, args, { cwd, stdio: "inherit" });
  orchestrator.on("error", (e) => console.error("orchestrator failed to start:", e.message));
}
function stopOrchestrator() {
  if (orchestrator && !orchestrator.killed) orchestrator.kill();
  orchestrator = null;
}
function waitForHealth(retries = 80) {
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(`http://127.0.0.1:${PORT}/health`, (res) => {
        res.resume();
        if (res.statusCode === 200) resolve();
        else schedule();
      });
      req.on("error", schedule);
    };
    const schedule = () => (retries-- > 0 ? setTimeout(attempt, 250) : reject(new Error("orchestrator never became healthy")));
    attempt();
  });
}
async function restartOrchestrator() {
  stopOrchestrator();
  await new Promise((r) => setTimeout(r, 400)); // let the port free
  startOrchestrator();
  await waitForHealth().catch((e) => console.error(e.message));
}

// ---- window ----------------------------------------------------------------------
function createWindow() {
  const b = settings.bounds || {};
  win = new BrowserWindow({
    width: b.width || 1180,
    height: b.height || 840,
    x: b.x,
    y: b.y,
    title: "functions — Studio",
    backgroundColor: "#0f1115",
    webPreferences: { preload: path.join(__dirname, "preload.cjs"), contextIsolation: true },
  });
  const remember = () => {
    if (win) {
      settings.bounds = win.getBounds();
      saveSettings();
    }
  };
  win.on("close", remember);
  win.loadURL(`http://127.0.0.1:${PORT}`);
}

// ---- IPC: settings ---------------------------------------------------------------
ipcMain.handle("settings:get", () => ({ engine: engine() }));
ipcMain.handle("settings:setEngine", async (_e, value) => {
  settings.engine = value === "local" ? "local" : "docker";
  saveSettings();
  await restartOrchestrator(); // new runs use the new engine; the page stays loaded
  return { engine: engine() };
});

app.whenReady().then(async () => {
  settings = loadSettings();
  startOrchestrator();
  await waitForHealth().catch((e) => console.error(e.message));
  createWindow();
});
app.on("window-all-closed", () => {
  stopOrchestrator();
  app.quit();
});
app.on("quit", stopOrchestrator);
process.on("exit", stopOrchestrator);
