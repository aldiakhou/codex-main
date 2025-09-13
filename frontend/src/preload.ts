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
  listCustomPrompts: () => ipcRenderer.invoke('aiw:listCustomPrompts'),
  // Agents proto ops
  listAgents: () => ipcRenderer.invoke('aiw:listAgents'),
  startAgent: (id: string, input?: string, context?: any) => ipcRenderer.invoke('aiw:startAgent', id, input, context),
  agentStatus: (taskId: string) => ipcRenderer.invoke('aiw:agentStatus', taskId),
  agentCancel: (taskId: string) => ipcRenderer.invoke('aiw:agentCancel', taskId),
  agentsReload: () => ipcRenderer.invoke('aiw:agentsReload'),
  upsertMcpServer: (server: { name: string; command: string; args?: string[]; env?: Record<string,string>}) => ipcRenderer.invoke('aiw:upsertMcpServer', server),
  removeMcpServer: (name: string) => ipcRenderer.invoke('aiw:removeMcpServer', name),
  restart: () => ipcRenderer.invoke('aiw:restartBackend'),
  getMcpServers: () => ipcRenderer.invoke('aiw:getMcpServers'),
  readCodexConfig: () => ipcRenderer.invoke('aiw:readCodexConfig'),
  saveCodexConfig: (cfg: any) => ipcRenderer.invoke('aiw:saveCodexConfig', cfg),
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

// Filesystem bridge for Files workspace
contextBridge.exposeInMainWorld('fsapi', {
  list: (dir: string) => ipcRenderer.invoke('fs:list', dir),
  read: (filePath: string) => ipcRenderer.invoke('fs:read', filePath),
  readBase64: (filePath: string) => ipcRenderer.invoke('fs:readBase64', filePath),
  stat: (p: string) => ipcRenderer.invoke('fs:stat', p),
  openPath: (p: string) => ipcRenderer.invoke('fs:openPath', p),
  chooseDir: () => ipcRenderer.invoke('fs:chooseDir'),
  createFile: (filePath: string, content?: string) => ipcRenderer.invoke('fs:createFile', filePath, content ?? ''),
  createDir: (dirPath: string) => ipcRenderer.invoke('fs:createDir', dirPath),
  renamePath: (oldPath: string, newPath: string) => ipcRenderer.invoke('fs:renamePath', oldPath, newPath),
  deletePath: (p: string, root: string) => ipcRenderer.invoke('fs:deletePath', p, root),
  undo: () => ipcRenderer.invoke('fs:undo'),
});

// Indexer bridge
contextBridge.exposeInMainWorld('idx', {
  build: (dir: string) => ipcRenderer.invoke('idx:build', dir),
  backlinks: (filePath: string) => ipcRenderer.invoke('idx:backlinks', filePath),
  graph: () => ipcRenderer.invoke('idx:graph'),
  watchStart: (dir: string) => ipcRenderer.invoke('idx:watchStart', dir),
  watchStop: () => ipcRenderer.invoke('idx:watchStop'),
  onUpdate: (cb: (payload: any) => void) => {
    const handler = (_: any, payload: any) => cb(payload);
    ipcRenderer.on('idx:update', handler);
    return () => ipcRenderer.removeListener('idx:update', handler);
  },
});
