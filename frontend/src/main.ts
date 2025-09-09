import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { BackendService } from './main/backend';

// Vite constants declarations
declare const MAIN_WINDOW_VITE_DEV_SERVER_URL: string;
declare const MAIN_WINDOW_VITE_NAME: string;

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

let mainWindow: BrowserWindow | null = null;
const backend = new BackendService();

const wireBackendIpc = () => {
  ipcMain.handle('aiw:start', (_e, opts) => backend.start(opts));
  ipcMain.handle('aiw:stop', () => backend.stop());
  ipcMain.handle('aiw:login', (_e, apiKey?: string) => backend.login(apiKey));
  ipcMain.handle('aiw:userTurn', (_e, params) => backend.userTurn(params));
  ipcMain.handle('aiw:interrupt', () => backend.interrupt());
  ipcMain.handle('aiw:execApproval', (_e, id: string, decision: string) => backend.execApproval(id, decision));
  ipcMain.handle('aiw:patchApproval', (_e, id: string, decision: string) => backend.patchApproval(id, decision));
  ipcMain.handle('aiw:setCodexPath', (_e, codexPath: string) => backend.saveCodexPath(codexPath));
  ipcMain.handle('aiw:getHistory', () => backend.getHistory());
  ipcMain.handle('aiw:listMcpTools', () => backend.listMcpTools());
  ipcMain.handle('aiw:upsertMcpServer', (_e, server) => backend.upsertMcpServer(server));
  ipcMain.handle('aiw:removeMcpServer', (_e, name: string) => backend.removeMcpServer(name));
  ipcMain.handle('aiw:restartBackend', () => backend.restart());
  ipcMain.handle('aiw:getMcpServers', () => backend.getMcpServers());
  ipcMain.handle('aiw:readCodexConfig', () => backend.readCodexConfig());
  ipcMain.handle('aiw:saveCodexConfig', (_e, cfg) => backend.saveCodexConfig(cfg));

  const send = (ch: string, payload: any) => {
    if (mainWindow) mainWindow.webContents.send(ch, payload);
  };
  backend.on('event', (e) => send('aiw:event', e));
  backend.on('status', (s) => send('aiw:status', s));
  backend.on('log', (m) => send('aiw:log', m));
  backend.on('error', (m) => send('aiw:error', m));
};

const createWindow = (): void => {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    height: 900,
    width: 1400,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#111014',
      symbolColor: '#f0f0f0',
    },
    minWidth: 1200,
    minHeight: 800,
  });

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  }

  // Open the DevTools.
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', () => {
  wireBackendIpc();
  createWindow();
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
