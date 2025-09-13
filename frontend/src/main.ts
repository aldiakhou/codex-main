import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import * as fs from 'node:fs/promises';
import * as fsSync from 'node:fs';
import * as path from 'node:path';
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
  ipcMain.handle('aiw:setProfile', (_e, profile: string) => backend.setProfile(profile));
  ipcMain.handle('aiw:getWorkbenchConfig', () => backend.getWorkbenchConfig());
  ipcMain.handle('aiw:getHistory', () => backend.getHistory());
  ipcMain.handle('aiw:listMcpTools', () => backend.listMcpTools());
  ipcMain.handle('aiw:listCustomPrompts', () => backend.listCustomPrompts());
  // Agents proto ops
  ipcMain.handle('aiw:listAgents', () => backend.listAgents());
  ipcMain.handle('aiw:startAgent', (_e, id: string, input?: string, context?: any) => backend.startAgent(id, input, context));
  ipcMain.handle('aiw:agentStatus', (_e, taskId: string) => backend.agentStatus(taskId));
  ipcMain.handle('aiw:agentCancel', (_e, taskId: string) => backend.agentCancel(taskId));
  ipcMain.handle('aiw:agentsReload', () => backend.agentsReload());

  // Basic FS IPC for Files workspace
  ipcMain.handle('fs:list', async (_e, dir: string) => {
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      return {
        ok: true,
        entries: entries.map((d) => ({
          name: d.name,
          path: path.join(dir, d.name),
          isDir: d.isDirectory(),
        })),
      };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });
  ipcMain.handle('fs:read', async (_e, filePath: string) => {
    try {
      const data = await fs.readFile(filePath);
      return { ok: true, data: data.toString('utf8') };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });
  ipcMain.handle('fs:readBase64', async (_e, filePath: string) => {
    try {
      const data = await fs.readFile(filePath);
      return { ok: true, base64: data.toString('base64') };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });
  ipcMain.handle('fs:openPath', async (_e, p: string) => {
    try {
      const res = await shell.openPath(p);
      // shell.openPath returns empty string on success, error message otherwise
      if (res && res.trim()) return { ok: false, error: res };
      return { ok: true };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });
  ipcMain.handle('fs:stat', async (_e, p: string) => {
    try {
      const s = await fs.stat(p);
      return { ok: true, stat: { size: s.size, mtimeMs: s.mtimeMs, isDir: s.isDirectory() } };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });
  ipcMain.handle('fs:chooseDir', async () => {
    const res = await dialog.showOpenDialog({ properties: ['openDirectory'] });
    if (res.canceled || res.filePaths.length === 0) return { ok: false, canceled: true };
    return { ok: true, path: res.filePaths[0] };
  });
  ipcMain.handle('fs:chooseFiles', async (_e, opts: { multi?: boolean }) => {
    const res = await dialog.showOpenDialog({
      properties: ['openFile', ...(opts?.multi ? ['multiSelections'] : [])] as any,
      filters: [{ name: 'Images', extensions: ['png','jpg','jpeg','gif','bmp','webp'] }],
    });
    if (res.canceled || res.filePaths.length === 0) return { ok: false, canceled: true };
    return { ok: true, paths: res.filePaths };
  });

  // Edit operations with simple undo to .trash
  const undoStack: Array<{ type: 'delete'|'rename'|'create'; from?: string; to?: string; content?: Buffer }>=[];
  function ensureTrash(root: string) {
    const trash = path.join(root, '.trash');
    if (!fsSync.existsSync(trash)) fsSync.mkdirSync(trash, { recursive: true });
    return trash;
  }
  ipcMain.handle('fs:createFile', async (_e, filePath: string, content: string = '') => {
    try {
      await fs.writeFile(filePath, content, 'utf8');
      undoStack.push({ type: 'create', from: filePath });
      return { ok: true };
    } catch (e: any) { return { ok: false, error: String(e) }; }
  });
  ipcMain.handle('fs:createDir', async (_e, dirPath: string) => {
    try { await fs.mkdir(dirPath, { recursive: true }); undoStack.push({ type: 'create', from: dirPath }); return { ok: true }; }
    catch (e: any) { return { ok: false, error: String(e) }; }
  });
  ipcMain.handle('fs:renamePath', async (_e, oldPath: string, newPath: string) => {
    try { await fs.rename(oldPath, newPath); undoStack.push({ type: 'rename', from: newPath, to: oldPath }); return { ok: true }; }
    catch (e: any) { return { ok: false, error: String(e) }; }
  });
  ipcMain.handle('fs:deletePath', async (_e, p: string, root: string) => {
    try {
      const trash = ensureTrash(root);
      const base = path.basename(p);
      const dest = path.join(trash, base + '.' + Date.now());
      await fs.rename(p, dest);
      undoStack.push({ type: 'delete', from: p, to: dest });
      return { ok: true };
    } catch (e: any) { return { ok: false, error: String(e) }; }
  });
  ipcMain.handle('fs:undo', async () => {
    const last = undoStack.pop();
    if (!last) return { ok: false, error: 'Nothing to undo' };
    try {
      if (last.type === 'delete' && last.to && last.from) {
        await fs.rename(last.to, last.from);
      } else if (last.type === 'rename' && last.from && last.to) {
        await fs.rename(last.from, last.to);
      } else if (last.type === 'create' && last.from) {
        // best-effort delete created path
        try { await fs.rm(last.from, { recursive: true, force: true }); } catch {}
      }
      return { ok: true };
    } catch (e: any) { return { ok: false, error: String(e) }; }
  });

  // --- Lightweight content indexer (links + backlinks) -------------------
  type FileNode = { path: string; name: string };
  let indexRoot: string | null = null;
  let allFiles: string[] = [];
  let basenameIndex = new Map<string, string[]>(); // lowercased basename -> paths
  type LinkEdge = { to: string; anchor?: string };
  let outLinks = new Map<string, Set<string>>();   // legacy (not used)
  let outEdges = new Map<string, Array<LinkEdge>>(); // src -> edges

  const IGNORED_DIRS = new Set(['.git', 'node_modules', 'dist', 'build', 'target', '.next', '.vite']);
  const TEXT_EXTS = new Set(['.md','.txt','.json','.js','.ts','.tsx','.jsx','.css','.html','.xml','.yaml','.yml','.csv','.rs','.py','.java','.go','.rb','.sh','.ps1','.toml','.mdx']);
  const isHttpLike = (s: string) => /^([a-z]+:)?\/\//i.test(s) || /^(mailto:|data:)/i.test(s);

  async function walk(dir: string, acc: string[]) {
    let entries: any[] = [];
    try { entries = await fs.readdir(dir, { withFileTypes: true } as any); } catch { return; }
    for (const d of entries) {
      const p = path.join(dir, d.name);
      if (d.isDirectory()) {
        if (IGNORED_DIRS.has(d.name)) continue;
        await walk(p, acc);
      } else {
        acc.push(p);
      }
    }
  }

  function addBasename(p: string) {
    const name = path.basename(p).replace(/\.[^.]+$/, '').toLowerCase();
    const arr = basenameIndex.get(name) || [];
    arr.push(p);
    basenameIndex.set(name, arr);
  }

  function resolveLink(fromFile: string, raw: string): { path: string | null; anchor?: string | null } {
    if (!indexRoot) return null;
    let link = raw.trim();
    if (!link || isHttpLike(link) || link.startsWith('#')) return null;
    // capture anchor
    let anchor: string | null = null;
    const hash = link.indexOf('#');
    if (hash >= 0) { anchor = link.slice(hash + 1); link = link.slice(0, hash); }

    let candidate: string;
    if (link.startsWith('/')) candidate = path.join(indexRoot, link);
    else candidate = path.resolve(path.dirname(fromFile), link);

    // If file exists, return
    // Otherwise, try add known extensions and basename lookup
    const tryPaths: string[] = [candidate];
    for (const ext of TEXT_EXTS) tryPaths.push(candidate + ext);
    for (const p of tryPaths) {
      if (allFiles.includes(p)) return { path: p, anchor };
    }

    // Basename lookup (for [[WikiLinks]] or links without folders)
    const name = path.basename(link).replace(/\.[^.]+$/, '').toLowerCase();
    const arr = basenameIndex.get(name);
    if (arr && arr.length) return { path: arr[0], anchor };
    return { path: null, anchor };
  }

  function extractLinks(fromFile: string, text: string): Array<LinkEdge> {
    const links: Array<LinkEdge> = [];
    // [[WikiLinks]]
    const wiki = text.matchAll(/\[\[([^\]]+)\]\]/g);
    for (const m of wiki) {
      const r = resolveLink(fromFile, m[1]);
      if (r && r.path) links.push({ to: r.path, anchor: r.anchor || undefined });
    }
    // Markdown [label](path)
    const md = text.matchAll(/\[[^\]]*\]\(([^)]+)\)/g);
    for (const m of md) {
      const r = resolveLink(fromFile, m[1]);
      if (r && r.path) links.push({ to: r.path, anchor: r.anchor || undefined });
    }
    // HTML href="..."
    const html = text.matchAll(/href=\"([^\"]+)\"/gi);
    for (const m of html) {
      const r = resolveLink(fromFile, m[1]);
      if (r && r.path) links.push({ to: r.path, anchor: r.anchor || undefined });
    }
    // Imports
    const imp = text.matchAll(/import[^'"\n]*['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\)/g);
    for (const m of imp) {
      const target = m[1] || m[2];
      if (!target) continue;
      const r = resolveLink(fromFile, target);
      if (r && r.path) links.push({ to: r.path, anchor: r.anchor || undefined });
    }
    return links;
  }

  async function buildIndex(root: string) {
    indexRoot = root;
    allFiles = [];
    basenameIndex.clear();
    outLinks.clear();
    outEdges.clear();
    await walk(root, allFiles);
    // Pre-build basename index
    for (const f of allFiles) addBasename(f);
    let linkCount = 0;
    for (const f of allFiles) {
      const ext = path.extname(f).toLowerCase();
      if (!TEXT_EXTS.has(ext)) continue;
      try {
        const buf = await fs.readFile(f);
        const text = buf.toString('utf8');
        const arr = extractLinks(f, text);
        if (arr.length) {
          linkCount += arr.length;
          outEdges.set(f, arr);
        }
      } catch {
        // ignore unreadable files
      }
    }
    return { files: allFiles.length, links: linkCount };
  }

  function getBacklinks(target: string) {
    const res: Array<{ from: string; anchor?: string }> = [];
    for (const [src, edges] of outEdges) {
      for (const e of edges) {
        if (e.to === target) res.push({ from: src, anchor: e.anchor });
      }
    }
    return res;
  }

  ipcMain.handle('idx:build', async (_e, dir: string) => {
    try {
      const stats = await buildIndex(dir);
      return { ok: true, stats };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });
  ipcMain.handle('idx:backlinks', async (_e, filePath: string) => {
    try {
      return { ok: true, backlinks: getBacklinks(filePath) };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });
  ipcMain.handle('idx:graph', async () => {
    try {
      const nodes: FileNode[] = allFiles.map((p) => ({ path: p, name: path.basename(p) }));
      const edges: Array<{ from: string; to: string; anchor?: string }> = [];
      for (const [src, arr] of outEdges) for (const e of arr) edges.push({ from: src, to: e.to, anchor: e.anchor });
      return { ok: true, nodes, edges, root: indexRoot };
    } catch (e: any) {
      return { ok: false, error: String(e) };
    }
  });

  // Watcher support (best-effort) ----------------------------------------
  let idxWatcher: fsSync.FSWatcher | null = null;
  let idxDebounce: NodeJS.Timeout | null = null;
  function sendIdxUpdate(stats: { files: number; links: number }) {
    if (mainWindow) mainWindow.webContents.send('idx:update', { stats });
  }
  async function rebuildAndNotify() {
    if (!indexRoot) return;
    const stats = await buildIndex(indexRoot);
    sendIdxUpdate(stats);
  }
  function setupWatch(dir: string) {
    try {
      if (idxWatcher) idxWatcher.close();
    } catch {}
    try {
      idxWatcher = fsSync.watch(dir, { recursive: true }, () => {
        if (idxDebounce) clearTimeout(idxDebounce);
        idxDebounce = setTimeout(() => {
          rebuildAndNotify().catch(() => {});
        }, 400);
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  ipcMain.handle('idx:watchStart', async (_e, dir: string) => {
    indexRoot = dir; // ensure in sync
    const ok = setupWatch(dir);
    if (ok) await rebuildAndNotify();
    return { ok };
  });
  ipcMain.handle('idx:watchStop', async () => {
    try { idxWatcher?.close(); } catch {}
    idxWatcher = null;
    return { ok: true };
  });
  ipcMain.handle('idx:search', async (_e, payload: { query: string; limit?: number; cwd?: string }) => {
    try {
      const query = (payload?.query || '').toString();
      const limit = Math.max(1, Math.min(Number(payload?.limit) || 20, 100));
      const cwd = (payload?.cwd || process.cwd()).toString();
      if (!indexRoot) {
        try { await buildIndex(cwd); } catch {}
      }
      const q = query.trim().toLowerCase();
      if (!q) return { ok: true, matches: [] };
      const lev = (a: string, b: string) => {
        if (a === b) return 0;
        const al = a.length, bl = b.length;
        if (al === 0) return bl; if (bl === 0) return al;
        const dp = new Array(al + 1);
        for (let i = 0; i <= al; i++) dp[i] = new Array<number>(bl + 1).fill(0);
        for (let i = 0; i <= al; i++) dp[i][0] = i;
        for (let j = 0; j <= bl; j++) dp[0][j] = j;
        for (let i = 1; i <= al; i++) {
          const ai = a.charCodeAt(i - 1);
          for (let j = 1; j <= bl; j++) {
            const cost = ai === b.charCodeAt(j - 1) ? 0 : 1;
            dp[i][j] = Math.min(
              dp[i - 1][j] + 1,
              dp[i][j - 1] + 1,
              dp[i - 1][j - 1] + cost,
            );
          }
        }
        return dp[al][bl];
      };
      const scoreFor = (p: string) => {
        const lowP = p.toLowerCase();
        const base = path.basename(p).toLowerCase();
        if (base.startsWith(q)) return 0;
        const bi = base.indexOf(q);
        if (bi >= 0) return 1 + bi; // slight penalty for non-prefix
        const pi = lowP.indexOf(q);
        if (pi >= 0) return 50 + pi; // larger penalty for path match
        const tokens = base.split(/[^a-z0-9]+/);
        let best = Number.MAX_SAFE_INTEGER;
        for (const t of tokens) {
          if (!t) continue;
          // Skip very dissimilar lengths to keep it snappy
          if (Math.abs(t.length - q.length) > Math.max(2, Math.floor(q.length * 0.6))) continue;
          const d = lev(t, q);
          if (d < best) best = d;
          if (best === 0) break;
        }
        if (best !== Number.MAX_SAFE_INTEGER) return 200 + best; // fallback to fuzzy
        return 10000;
      };
      const files = allFiles.slice(0);
      const scored = files
        .map((p) => ({ p, s: scoreFor(p) }))
        .filter((x) => x.s < 10000)
        .sort((a, b) => a.s - b.s)
        .slice(0, limit)
        .map(({ p, s }) => ({ path: p, rel: path.relative(cwd, p) || p, score: s }));
      return { ok: true, matches: scored };
    } catch (e: any) {
      return { ok: false, matches: [], error: String(e) } as any;
    }
  });
  ipcMain.handle('aiw:upsertMcpServer', (_e, server) => backend.upsertMcpServer(server));
  ipcMain.handle('aiw:removeMcpServer', (_e, name: string) => backend.removeMcpServer(name));
  ipcMain.handle('aiw:restartBackend', () => backend.restart());
  ipcMain.handle('aiw:getMcpServers', () => backend.getMcpServers());
  ipcMain.handle('aiw:readCodexConfig', () => backend.readCodexConfig());
  ipcMain.handle('aiw:saveCodexConfig', (_e, cfg) => backend.saveCodexConfig(cfg));
  ipcMain.handle('aiw:loginStatus', () => backend.loginStatus());
  ipcMain.handle('aiw:authInfo', () => backend.authInfo());

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
