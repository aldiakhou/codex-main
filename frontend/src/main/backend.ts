import { spawn, ChildProcessWithoutNullStreams } from 'node:child_process';
import { EventEmitter } from 'node:events';
import * as os from 'node:os';
import * as fs from 'node:fs';
import * as path from 'node:path';

type ReviewDecision = 'approved' | 'approved_for_session' | 'denied' | 'abort';

type UserTurnParams = {
  text: string;
  cwd?: string;
  approval_policy?: 'untrusted' | 'on-failure' | 'on-request' | 'never';
  sandbox_mode?: 'read-only' | 'workspace-write' | 'danger-full-access';
  model?: string;
  effort?: 'minimal' | 'low' | 'medium' | 'high';
  summary?: 'auto' | 'concise' | 'detailed' | 'none';
  local_images?: string[]; // local file paths
  image_urls?: string[];   // data URL or http(s) URLs
};

type MCPServer = {
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
};

type AppConfig = {
  backend?: { codex_path?: string; profile?: string };
  mcp_servers?: Record<string, MCPServer>;
};

export class BackendService extends EventEmitter {
  private proc?: ChildProcessWithoutNullStreams;
  private running = false;
  private codexPath?: string;
  private profile?: string;

  async start(opts?: { codexPath?: string; profile?: string }) {
    if (this.running) return;

    const cfg = this.loadAIWConfig();
    this.codexPath = opts?.codexPath || cfg.backend?.codex_path || (await this.autoDetectCodexPath());
    this.profile = opts?.profile || cfg.backend?.profile;

    const exe = this.codexPath || 'codex';
    const args: string[] = [];
    if (this.profile) {
      args.push('-p', this.profile);
    }
    // Ensure the view_image tool is always enabled so the model can attach images.
    args.push('-c', 'include_view_image_tool=true');

    // MCP servers: single source of truth is ~/.codex/config.toml (edited in Settings).
    // No -c overrides injected from ~/.ai-workbench/config.json.
    args.push('proto');

    this.emit('status', 'connecting');
    const env = { ...process.env, RUST_BACKTRACE: '1' };
    try {
      this.proc = spawn(exe, args, { stdio: ['pipe', 'pipe', 'pipe'], env });
    } catch (e) {
      this.emit('status', 'error');
      this.emit('error', String(e));
      return;
    }

    this.running = true;
    this.emit('log', `Spawned ${exe} ${args.join(' ')}`);

    // stdout JSONL reader
    this.proc.stdout.setEncoding('utf8');
    let buffer = '';
    this.proc.stdout.on('data', (chunk: string) => {
      buffer += chunk;
      let idx: number;
      while ((idx = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, idx).trim();
        buffer = buffer.slice(idx + 1);
        if (!line) continue;
        // Skip non-JSON lines (defensive)
        if (!(line.startsWith('{') || line.startsWith('['))) continue;
        try {
          const obj = JSON.parse(line);
          this.emit('event', obj);
          if (obj?.msg?.type === 'session_configured') {
            this.emit('status', 'connected');
          }
        } catch (err) {
          this.emit('error', `Invalid JSON from backend: ${String(err)}`);
        }
      }
    });

    // stderr to logs
    this.proc.stderr.setEncoding('utf8');
    this.proc.stderr.on('data', (d: string) => {
      const line = String(d).trim();
      if (!line) return;
      this.emit('log', `backend: ${line}`);
      if (/error|failed/i.test(line)) this.emit('error', line);
    });

    // exit handling
    this.proc.on('exit', (code) => {
      this.running = false;
      this.emit('status', 'disconnected');
      this.emit('stopped', code ?? 0);
      this.proc = undefined;
    });
    this.proc.on('error', (err) => {
      this.emit('status', 'error');
      this.emit('error', String(err));
    });
  }

  stop() {
    if (!this.proc) return;
    try {
      this.proc.kill();
    } catch {}
  }

  async restart() {
    const codexPath = this.codexPath;
    const profile = this.profile;
    try { this.stop(); } catch {}
    await new Promise((r) => setTimeout(r, 200));
    await this.start({ codexPath, profile });
  }

  private send(submission: any): boolean {
    if (!this.proc || !this.running || !this.proc.stdin.writable) {
      this.emit('error', 'Backend not running');
      return false;
    }
    try {
      this.proc.stdin.write(JSON.stringify(submission) + '\n');
      return true;
    } catch (e) {
      this.emit('error', `Failed to write to backend: ${String(e)}`);
      return false;
    }
  }

  interrupt(): boolean {
    return this.send({ id: `interrupt_${Date.now()}`, op: { type: 'interrupt' } });
  }

  userTurn(params: UserTurnParams): boolean {
    const id = `user_turn_${Date.now()}`;
    const {
      text,
      cwd,
      approval_policy = 'on-request',
      sandbox_mode = 'read-only',
      model = 'gpt-5',
      effort = 'medium',
      summary = 'auto',
      local_images = [],
      image_urls = [],
    } = params;
    const safeCwd = (cwd || process.cwd()).replace(/\\/g, '/');
    const items: any[] = [];
    for (const p of local_images) {
      if (p && typeof p === 'string') items.push({ type: 'local_image', path: p });
    }
    for (const u of image_urls) {
      if (u && typeof u === 'string') items.push({ type: 'image', image_url: u });
    }
    if ((text || '').trim()) items.push({ type: 'text', text });
    return this.send({
      id,
      op: {
        type: 'user_turn',
        items,
        cwd: safeCwd,
        approval_policy,
        sandbox_policy: { mode: sandbox_mode },
        model,
        effort,
        summary,
      },
    });
  }

  execApproval(targetSubmissionId: string, decision: ReviewDecision): boolean {
    return this.send({
      id: `exec_approval_${Date.now()}`,
      op: { type: 'exec_approval', id: targetSubmissionId, decision },
    });
  }

  patchApproval(targetSubmissionId: string, decision: ReviewDecision): boolean {
    return this.send({
      id: `patch_approval_${Date.now()}`,
      op: { type: 'patch_approval', id: targetSubmissionId, decision },
    });
  }

  async login(apiKey?: string): Promise<boolean> {
    const exe = this.codexPath || 'codex';
    const args = ['login'];
    if (apiKey) args.push('--api-key', apiKey);
    return new Promise((resolve) => {
      try {
        const p = spawn(exe, args, { env: { ...process.env, RUST_BACKTRACE: '1' } });
        let lastErr = '';
        p.stderr?.setEncoding('utf8');
        p.stderr?.on('data', (d) => {
          const line = String(d).trim();
          if (line) {
            lastErr = line;
            this.emit('log', `login: ${line}`);
          }
        });
        p.on('exit', (code) => {
          const ok = code === 0;
          if (!ok) this.emit('error', lastErr || `Login failed (${code})`);
          resolve(ok);
        });
      } catch (e) {
        this.emit('error', `Login spawn failed: ${String(e)}`);
        resolve(false);
      }
    });
  }

  getHistory(): boolean {
    return this.send({ id: `get_history_${Date.now()}`, op: { type: 'get_history' } });
  }

  // --- Config helpers ---
  private loadAIWConfig(): AppConfig {
    try {
      const cfgPath = path.join(os.homedir(), '.ai-workbench', 'config.json');
      if (!fs.existsSync(cfgPath)) return {};
      const text = fs.readFileSync(cfgPath, 'utf8');
      const data = JSON.parse(text);
      return data || {};
    } catch {
      return {};
    }
  }

  public saveCodexPath(newPath: string): boolean {
    try {
      const cfgDir = path.join(os.homedir(), '.ai-workbench');
      const cfgPath = path.join(cfgDir, 'config.json');
      let data: AppConfig = {};
      if (fs.existsSync(cfgPath)) {
        try { data = JSON.parse(fs.readFileSync(cfgPath, 'utf8')); } catch { data = {}; }
      }
      if (!data.backend) data.backend = {};
      data.backend.codex_path = newPath;
      fs.mkdirSync(cfgDir, { recursive: true });
      fs.writeFileSync(cfgPath, JSON.stringify(data, null, 2), 'utf8');
      this.codexPath = newPath;
      this.emit('log', `Saved Codex path to ${cfgPath}`);
      return true;
    } catch (e) {
      this.emit('error', `Failed to save config: ${String(e)}`);
      return false;
    }
  }

  public setProfile(newProfile: string): boolean {
    try {
      const cfgDir = path.join(os.homedir(), '.ai-workbench');
      const cfgPath = path.join(cfgDir, 'config.json');
      let data: AppConfig = {};
      if (fs.existsSync(cfgPath)) {
        try { data = JSON.parse(fs.readFileSync(cfgPath, 'utf8')); } catch { data = {}; }
      }
      if (!data.backend) data.backend = {} as any;
      (data.backend as any).profile = newProfile || '';
      fs.mkdirSync(cfgDir, { recursive: true });
      fs.writeFileSync(cfgPath, JSON.stringify(data, null, 2), 'utf8');
      this.profile = newProfile || undefined;
      this.emit('log', `Saved active profile to ${cfgPath}`);
      return true;
    } catch (e) {
      this.emit('error', `Failed to save profile: ${String(e)}`);
      return false;
    }
  }

  public getWorkbenchConfig(): { ok: boolean; backend?: { codex_path?: string; profile?: string } } {
    try {
      const cfg = this.loadAIWConfig();
      const backend = cfg.backend || {};
      return { ok: true, backend: { codex_path: backend?.codex_path, profile: backend?.profile } };
    } catch (e) {
      this.emit('error', `Failed to read workbench config: ${String(e)}`);
      return { ok: false };
    }
  }

  public async loginStatus(): Promise<{ ok: boolean; stdout?: string; stderr?: string }> {
    const exe = this.codexPath || 'codex';
    return new Promise((resolve) => {
      try {
        const p = spawn(exe, ['login', 'status'], { env: { ...process.env, RUST_BACKTRACE: '1' } });
        let out = '';
        let err = '';
        p.stdout?.setEncoding('utf8');
        p.stdout?.on('data', (d) => { out += String(d); });
        p.stderr?.setEncoding('utf8');
        p.stderr?.on('data', (d) => { err += String(d); });
        p.on('exit', (_code) => {
          resolve({ ok: true, stdout: out.trim(), stderr: err.trim() });
        });
      } catch (e) {
        this.emit('error', `Login status failed: ${String(e)}`);
        resolve({ ok: false, stderr: String(e) });
      }
    });
  }

  public async authInfo(): Promise<{
    ok: boolean;
    mode: 'api_key' | 'chatgpt' | 'none';
    masked_api_key?: string;
    email?: string;
    account_id?: string;
    plan_type?: string;
    last_refresh?: string;
  }> {
    try {
      const cfgDir = this.codexHome();
      const file = path.join(cfgDir, 'auth.json');
      if (!fs.existsSync(file)) return { ok: true, mode: 'none' };
      const raw = fs.readFileSync(file, 'utf8');
      const data: any = JSON.parse(raw);
      const apiKey: string | undefined = data?.OPENAI_API_KEY;
      const tokens: any = data?.tokens || null;
      const lastRefresh: string | undefined = data?.last_refresh || undefined;
      const out: any = { ok: true, mode: 'none' };
      if (tokens && tokens.id_token) {
        out.mode = 'chatgpt';
        try {
          const parts = String(tokens.id_token).split('.');
          if (parts.length >= 2) {
            const payloadB64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
            const buf = Buffer.from(payloadB64, 'base64');
            const payload = JSON.parse(buf.toString('utf8'));
            out.email = payload?.email || undefined;
            const auth = payload?.['https://api.openai.com/auth'] || {};
            out.account_id = auth?.chatgpt_account_id || undefined;
            const plan = auth?.chatgpt_plan_type;
            out.plan_type = typeof plan === 'string' ? plan : (plan?.string || plan?.as_string || undefined);
          }
        } catch {}
      } else if (apiKey) {
        out.mode = 'api_key';
        const k = String(apiKey);
        out.masked_api_key = k.length > 13 ? `${k.slice(0,8)}***${k.slice(-5)}` : '***';
      } else {
        out.mode = 'none';
      }
      if (lastRefresh) out.last_refresh = lastRefresh;
      return out;
    } catch (e) {
      this.emit('error', `authInfo error: ${String(e)}`);
      return { ok: false, mode: 'none' } as any;
    }
  }

  public upsertMcpServer(server: MCPServer): boolean {
    try {
      const { ok, config, error } = this.readCodexConfig();
      if (!ok) throw new Error(error || 'Failed to read Codex config');
      const cfg: any = config || {};
      cfg.mcp_servers = cfg.mcp_servers || {};
      cfg.mcp_servers[server.name] = {
        command: server.command,
        args: server.args || [],
        env: server.env || {},
      };
      const res = this.saveCodexConfig(cfg);
      if (!res.ok) throw new Error(res.error || 'Failed to write config');
      this.emit('log', `Saved MCP server '${server.name}' to ${res.path}`);
      return true;
    } catch (e) {
      this.emit('error', `Failed to save MCP server: ${String(e)}`);
      return false;
    }
  }

  public removeMcpServer(name: string): boolean {
    try {
      const { ok, config, error } = this.readCodexConfig();
      if (!ok) throw new Error(error || 'Failed to read Codex config');
      const cfg: any = config || {};
      if (cfg.mcp_servers && cfg.mcp_servers[name]) {
        delete cfg.mcp_servers[name];
        const res = this.saveCodexConfig(cfg);
        if (!res.ok) throw new Error(res.error || 'Failed to write config');
        this.emit('log', `Removed MCP server '${name}' from ${res.path}`);
      }
      return true;
    } catch (e) {
      this.emit('error', `Failed to remove MCP server: ${String(e)}`);
      return false;
    }
  }

  public getMcpServers(): Record<string, MCPServer> {
    try {
      const { ok, config, error } = this.readCodexConfig();
      if (!ok) throw new Error(error || 'Failed to read Codex config');
      const cfg: any = config || {};
      return (cfg.mcp_servers as any) || {};
    } catch (e) {
      this.emit('error', `Failed to read MCP servers: ${String(e)}`);
      return {};
    }
  }

  // --- Codex config (.codex/config.toml) -------------------------------
  private codexHome(): string {
    const env = process.env['CODEX_HOME'];
    return env && env.trim() ? env : path.join(os.homedir(), '.codex');
  }

  readCodexConfig(): { ok: boolean; config?: any; raw?: string; path: string; error?: string } {
    try {
      const cfgDir = this.codexHome();
      const cfgPath = path.join(cfgDir, 'config.toml');
      if (!fs.existsSync(cfgPath)) return { ok: true, config: {}, raw: '', path: cfgPath };
      const raw = fs.readFileSync(cfgPath, 'utf8');
      let config: any = {};
      try {
        // Lazy require to avoid bundler resolution issues; may throw if module missing
        const { parse } = require('toml');
        config = parse(raw);
      } catch (e) {
        // Fallback to a loose TOML parser for common cases
        config = this.parseTomlLoose(raw);
      }
      return { ok: true, config, raw, path: cfgPath };
    } catch (e: any) {
      return { ok: false, error: String(e), path: path.join(this.codexHome(), 'config.toml') };
    }
  }

  saveCodexConfig(config: any): { ok: boolean; path: string; error?: string } {
    try {
      const cfgDir = this.codexHome();
      const cfgPath = path.join(cfgDir, 'config.toml');
      fs.mkdirSync(cfgDir, { recursive: true });
      let text: string;
      try {
        const stringify = require('toml').stringify;
        text = stringify(config);
      } catch (e) {
        text = this.toTomlLoose(config);
      }
      fs.writeFileSync(cfgPath, text, 'utf8');
      this.emit('log', `Saved Codex config to ${cfgPath}`);
      return { ok: true, path: cfgPath };
    } catch (e: any) {
      return { ok: false, error: String(e), path: path.join(this.codexHome(), 'config.toml') };
    }
  }

  // --- Minimal TOML helpers (fallback) -----------------------------------
  private parseTomlLoose(text: string): any {
    const root: any = {};
    let path: string[] = [];
    const setAt = (p: string[], key: string, value: any) => {
      let cur = root;
      for (const seg of p) {
        cur[seg] = cur[seg] || {};
        cur = cur[seg];
      }
      cur[key] = value;
    };
    const getAt = (p: string[]) => {
      let cur = root;
      for (const seg of p) {
        cur[seg] = cur[seg] || {};
        cur = cur[seg];
      }
      return cur;
    };
    const lines = text.split(/\r?\n/);
    for (let raw of lines) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const sec = line.match(/^\[(.+?)\]$/);
      if (sec) {
        path = sec[1].split('.').map(s => s.trim());
        continue;
      }
      const m = line.match(/^(\w[\w\-\_]*)\s*=\s*(.+)$/);
      if (!m) continue;
      const key = m[1];
      let valRaw = m[2].trim();
      let value: any;
      if ((valRaw.startsWith('"') && valRaw.endsWith('"')) || (valRaw.startsWith("'") && valRaw.endsWith("'"))) {
        value = valRaw.slice(1, -1);
      } else if (valRaw === 'true' || valRaw === 'false') {
        value = valRaw === 'true';
      } else if (valRaw.startsWith('[') && valRaw.endsWith(']')) {
        const inner = valRaw.slice(1, -1);
        value = inner.split(',').map(s => s.trim()).filter(Boolean).map((s) => {
          if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) return s.slice(1, -1);
          if (s === 'true' || s === 'false') return s === 'true';
          const n = Number(s); return isNaN(n) ? s : n;
        });
      } else {
        const n = Number(valRaw);
        value = isNaN(n) ? valRaw : n;
      }
      setAt(path, key, value);
    }
    return root;
  }

  private toTomlLoose(obj: any): string {
    const lines: string[] = [];
    const writeTable = (prefix: string[], o: any) => {
      const scalars: [string, any][] = [];
      const tables: [string, any][] = [];
      for (const k of Object.keys(o)) {
        const v = o[k];
        if (v === null || typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean' || Array.isArray(v)) scalars.push([k, v]);
        else if (typeof v === 'object') tables.push([k, v]);
      }
      if (prefix.length) lines.push('', `[${prefix.join('.')}]`);
      for (const [k, v] of scalars) lines.push(`${k} = ${this.tomlValue(v)}`);
      for (const [k, v] of tables) writeTable([...prefix, k], v);
    };
    writeTable([], obj || {});
    return lines.join('\n').replace(/^\n+/, '');
  }

  private tomlValue(v: any): string {
    if (Array.isArray(v)) return `[${v.map((x) => this.tomlValue(x)).join(', ')}]`;
    switch (typeof v) {
      case 'string': return JSON.stringify(v);
      case 'number': return String(v);
      case 'boolean': return v ? 'true' : 'false';
      default: return JSON.stringify(String(v));
    }
  }

  // --- MCP tools ----------------------------------------------------------
  listMcpTools(): boolean {
    return this.send({ id: `list_mcp_tools_${Date.now()}`, op: { type: 'list_mcp_tools' } });
  }

  // --- Agents proto ops ---------------------------------------------------
  listAgents(): boolean {
    return this.send({ id: `list_agents_${Date.now()}`, op: { type: 'list_agents' } });
  }

  startAgent(agentId: string, input?: string, context?: any): boolean {
    const op: any = { type: 'start_agent', id: agentId };
    if (input && input.trim()) op.input = input;
    if (context !== undefined) op.context = context;
    return this.send({ id: `start_agent_${Date.now()}`, op });
  }

  agentStatus(taskId: string): boolean {
    return this.send({ id: `agent_status_${Date.now()}`, op: { type: 'agent_status', task_id: taskId } });
  }

  agentCancel(taskId: string): boolean {
    return this.send({ id: `agent_cancel_${Date.now()}`, op: { type: 'agent_cancel', task_id: taskId } });
  }

  agentsReload(): boolean {
    return this.send({ id: `agents_reload_${Date.now()}`, op: { type: 'agents_reload' } });
  }

  // --- Custom prompts -----------------------------------------------------
  listCustomPrompts(): boolean {
    return this.send({ id: `list_custom_prompts_${Date.now()}`, op: { type: 'list_custom_prompts' } });
  }

  private async autoDetectCodexPath(): Promise<string | undefined> {
    const isWin = process.platform === 'win32';
    const bin = isWin ? 'codex.exe' : 'codex';

    // Try PATH
    const whichCmd = isWin ? 'where' : 'which';
    const found = await new Promise<string | undefined>((resolve) => {
      try {
        const p = spawn(whichCmd, [bin]);
        let out = '';
        p.stdout.setEncoding('utf8');
        p.stdout.on('data', (d) => (out += String(d)));
        p.on('exit', (code) => {
          if (code === 0) {
            const first = out.split(/\r?\n/).map((s) => s.trim()).find(Boolean);
            resolve(first);
          } else resolve(undefined);
        });
      } catch {
        resolve(undefined);
      }
    });
    if (found) return found;

    // Try common project paths relative to this process cwd (monorepo dev)
    const candidates: string[] = [];
    const cwd = process.cwd();
    const roots = [
      path.resolve(cwd, '../codex-main/codex-rs/target/release'),
      path.resolve(cwd, '../codex-main/codex-rs/target/debug'),
    ];
    for (const r of roots) candidates.push(path.join(r, bin));
    for (const c of candidates) if (fs.existsSync(c)) return c;
    return undefined;
  }
}
