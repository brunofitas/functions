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
  // Pipelines run in Docker by default (the sandbox); set FUNCTIONS_BACKEND=host to opt out.
  const dockerArgs =
    process.env.FUNCTIONS_BACKEND === "host"
      ? []
      : ["--docker", "--image", process.env.FUNCTIONS_IMAGE || "python:3.12-slim"];
  let cmd;
  let args;
  let cwd;
  if (app.isPackaged) {
    // shipped: run the self-contained PyInstaller binary (no system Python needed)
    const res = process.resourcesPath;
    const exe = process.platform === "win32" ? "functions-orchestrator.exe" : "functions-orchestrator";
    cmd = path.join(res, "orchestrator", exe);
    args = ["--gui", "--gui-dir", path.join(res, "gui"), "--port", String(PORT),
            "--base-dir", path.join(res, "examples"), ...dockerArgs];
    cwd = res;
  } else {
    // dev: use the repo venv
    cmd = PYTHON;
    args = ["-m", "functions_be", "--gui", "--port", String(PORT), "--base-dir", BASE_DIR, ...dockerArgs];
    cwd = ROOT;
  }
  orchestrator = spawn(cmd, args, { cwd, stdio: "inherit" });
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
