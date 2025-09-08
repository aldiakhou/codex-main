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

    // Inject MCP servers as -c overrides from ~/.ai-workbench/config.json
    const mcp = cfg.mcp_servers || {};
    for (const [name, s] of Object.entries(mcp)) {
      if (!s || !s.command) continue;
      args.push('-c', `mcp_servers.${name}.command=${JSON.stringify(s.command)}`);
      if (s.args && s.args.length) args.push('-c', `mcp_servers.${name}.args=${JSON.stringify(s.args)}`);
      if (s.env && Object.keys(s.env).length)
        args.push('-c', `mcp_servers.${name}.env=${JSON.stringify(s.env)}`);
    }
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
    } = params;
    const safeCwd = (cwd || process.cwd()).replace(/\\/g, '/');
    return this.send({
      id,
      op: {
        type: 'user_turn',
        items: [{ type: 'text', text }],
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
