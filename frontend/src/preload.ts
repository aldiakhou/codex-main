// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

import { contextBridge, ipcRenderer } from 'electron';

// Minimal AI Workbench bridge for the renderer
contextBridge.exposeInMainWorld('aiw', {
  start: (opts?: { codexPath?: string; profile?: string }) => ipcRenderer.invoke('aiw:start', opts),
  stop: () => ipcRenderer.invoke('aiw:stop'),
  login: (apiKey?: string) => ipcRenderer.invoke('aiw:login', apiKey),
  userTurn: (params: any) => ipcRenderer.invoke('aiw:userTurn', params),
  interrupt: () => ipcRenderer.invoke('aiw:interrupt'),
  execApproval: (id: string, decision: string) => ipcRenderer.invoke('aiw:execApproval', id, decision),
  patchApproval: (id: string, decision: string) => ipcRenderer.invoke('aiw:patchApproval', id, decision),
  setCodexPath: (codexPath: string) => ipcRenderer.invoke('aiw:setCodexPath', codexPath),
  getHistory: () => ipcRenderer.invoke('aiw:getHistory'),
  listMcpTools: () => ipcRenderer.invoke('aiw:listMcpTools'),
  upsertMcpServer: (server: { name: string; command: string; args?: string[]; env?: Record<string,string>}) => ipcRenderer.invoke('aiw:upsertMcpServer', server),
  removeMcpServer: (name: string) => ipcRenderer.invoke('aiw:removeMcpServer', name),
  restart: () => ipcRenderer.invoke('aiw:restartBackend'),
  getMcpServers: () => ipcRenderer.invoke('aiw:getMcpServers'),
  onEvent: (cb: (e: any) => void) => {
    const listener = (_: any, payload: any) => cb(payload);
    ipcRenderer.on('aiw:event', listener);
    return () => ipcRenderer.removeListener('aiw:event', listener);
  },
  onStatus: (cb: (s: string) => void) => {
    const listener = (_: any, payload: string) => cb(payload);
    ipcRenderer.on('aiw:status', listener);
    return () => ipcRenderer.removeListener('aiw:status', listener);
  },
  onLog: (cb: (m: string) => void) => {
    const listener = (_: any, payload: string) => cb(payload);
    ipcRenderer.on('aiw:log', listener);
    return () => ipcRenderer.removeListener('aiw:log', listener);
  },
  onError: (cb: (m: string) => void) => {
    const listener = (_: any, payload: string) => cb(payload);
    ipcRenderer.on('aiw:error', listener);
    return () => ipcRenderer.removeListener('aiw:error', listener);
  },
});
