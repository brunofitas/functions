// Electron desktop shell (infra_004).
// Spawns the orchestrator (python -m functions_be --gui), waits for health, then opens
// a native window on the served Studio. Kills the orchestrator on quit.
const { app, BrowserWindow } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");
const http = require("node:http");

const PORT = Number(process.env.FUNCTIONS_PORT || 8799);
const ROOT = path.resolve(__dirname, "..", "..", ".."); // repo root (…/functions)
const PYTHON = process.env.FUNCTIONS_PYTHON || path.join(ROOT, ".venv", "bin", "python");
const BASE_DIR = process.env.FUNCTIONS_BASE_DIR || "examples";

let orchestrator = null;

function startOrchestrator() {
  orchestrator = spawn(
    PYTHON,
    ["-m", "functions_be", "--gui", "--port", String(PORT), "--base-dir", BASE_DIR],
    { cwd: ROOT, stdio: "inherit" },
  );
  orchestrator.on("error", (e) => console.error("orchestrator failed to start:", e.message));
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

function stopOrchestrator() {
  if (orchestrator && !orchestrator.killed) orchestrator.kill();
  orchestrator = null;
}

async function launch() {
  startOrchestrator();
  try {
    await waitForHealth();
  } catch (e) {
    console.error(e.message);
  }
  const win = new BrowserWindow({
    width: 1180,
    height: 840,
    title: "functions — Studio",
    backgroundColor: "#0f1115",
    webPreferences: { contextIsolation: true },
  });
  await win.loadURL(`http://127.0.0.1:${PORT}`);
}

app.whenReady().then(launch);
app.on("window-all-closed", () => {
  stopOrchestrator();
  app.quit();
});
app.on("quit", stopOrchestrator);
process.on("exit", stopOrchestrator);
