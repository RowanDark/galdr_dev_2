// src/main/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

const electronAPI = {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  showSaveDialog: () => ipcRenderer.invoke('show-save-dialog'),
  
  // Menu event listeners
  onMenuNewProject: (callback: () => void) => ipcRenderer.on('menu-new-project', callback),
  onMenuImportTraffic: (callback: () => void) => ipcRenderer.on('menu-import-traffic', callback),
  onMenuStartProxy: (callback: () => void) => ipcRenderer.on('menu-start-proxy', callback),
  onMenuStopProxy: (callback: () => void) => ipcRenderer.on('menu-stop-proxy', callback),
  onMenuClearHistory: (callback: () => void) => ipcRenderer.on('menu-clear-history', callback),
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);
