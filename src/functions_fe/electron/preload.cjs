// Preload — exposes a minimal, safe settings API to the renderer over IPC.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("functionsApp", {
  getSettings: () => ipcRenderer.invoke("settings:get"),
  setEngine: (engine) => ipcRenderer.invoke("settings:setEngine", engine),
});
