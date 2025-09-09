import React, { useEffect, useMemo, useState } from 'react';
import { useBackend } from '../../contexts/BackendContext';

const Section: React.FC<{ title: string; children: React.ReactNode }>=({ title, children })=> (
  <div className="mb-4 border border-[var(--border)] rounded-lg bg-[var(--bg-secondary)]">
    <div className="px-4 py-2 border-b border-[var(--border)] text-sm font-semibold">{title}</div>
    <div className="p-4 space-y-3">{children}</div>
  </div>
);

const SettingsWorkspace: React.FC = () => {
  const { refreshMcpServers } = useBackend();
  const [cfg, setCfg] = useState<any>({});
  const [path, setPath] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const profiles = Object.keys((cfg.profiles || {}));

  const load = async () => {
    setLoading(true); setError(null);
    const res = await window.aiw.readCodexConfig();
    if (res.ok) { setCfg(res.config || {}); setPath(res.path); } else { setError(res.error || 'Failed to read config'); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const save = async () => {
    setSaving(true); setError(null);
    const res = await window.aiw.saveCodexConfig(cfg);
    if (!res.ok) setError(res.error || 'Failed to save');
    setSaving(false);
  };
  const saveAndRestart = async () => {
    setSaving(true); setError(null);
    const res = await window.aiw.saveCodexConfig(cfg);
    if (!res.ok) { setError(res.error || 'Failed to save'); setSaving(false); return; }
    try { await window.aiw.restart(); } catch {}
    setSaving(false);
  };

  // --- helpers for nested paths ------------------------------------------
  const set = (key: string, value: any) => setCfg((prev: any) => ({ ...prev, [key]: value }));
  const setPathVal = (keys: string[], value: any) => setCfg((prev: any) => {
    const next = { ...prev };
    let cur: any = next;
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      cur[k] = { ...(cur[k] || {}) };
      cur = cur[k];
    }
    cur[keys[keys.length - 1]] = value;
    return next;
  });


  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Settings</h1>
        <div className="text-sm text-[var(--text-secondary)]">{path}</div>
      </div>
      {error && <div className="mb-3 text-sm text-red-300 bg-red-500/10 border border-red-500/30 rounded p-2">{error}</div>}
      {loading ? (
        <div className="text-[var(--text-secondary)]">Loading…</div>
      ) : (
        <>
          <Section title="Authentication">
            <div className="text-sm text-[var(--text-secondary)]">Login to ChatGPT (for models that require it)</div>
            <button className="px-3 py-1 rounded bg-[var(--accent)] text-white" onClick={()=>window.aiw.login()}>Login</button>
          </Section>

          <Section title="Profile">
            <div className="flex items-center gap-2">
              <label className="text-sm w-40">Active profile</label>
              <select value={cfg.profile || ''} onChange={(e)=> set('profile', e.target.value)} className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                <option value="">(none)</option>
                {profiles.map((p)=> <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </Section>

          <Section title="General">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Model</label>
                <input value={cfg.model || ''} onChange={(e)=> set('model', e.target.value)} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Model Provider</label>
                <input value={cfg.model_provider || ''} onChange={(e)=> set('model_provider', e.target.value)} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Approval Policy</label>
                <select value={cfg.approval_policy || ''} onChange={(e)=> set('approval_policy', e.target.value)} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                  <option value="">(default)</option>
                  <option value="untrusted">untrusted</option>
                  <option value="on-failure">on-failure</option>
                  <option value="on-request">on-request</option>
                  <option value="never">never</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Sandbox Mode</label>
                <select value={cfg.sandbox_mode || ''} onChange={(e)=> set('sandbox_mode', e.target.value)} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                  <option value="">(default)</option>
                  <option value="read-only">read-only</option>
                  <option value="workspace-write">workspace-write</option>
                  <option value="danger-full-access">danger-full-access</option>
                </select>
              </div>
            </div>
          </Section>

          <Section title="History">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Persistence</label>
                <select value={cfg.history?.persistence || ''} onChange={(e)=> set('history', { ...(cfg.history||{}), persistence: e.target.value || undefined })} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                  <option value="">(default)</option>
                  <option value="save-all">save-all</option>
                  <option value="none">none</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Max bytes</label>
                <input type="number" value={cfg.history?.max_bytes || ''} onChange={(e)=> set('history', { ...(cfg.history||{}), max_bytes: e.target.value ? Number(e.target.value) : undefined })} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
              </div>
            </div>
          </Section>

          <Section title="Notify">
            <div className="flex items-center gap-2">
              <label className="text-sm w-40">Commands</label>
              <input value={(cfg.notify||[]).join(', ')} onChange={(e)=> set('notify', (e.target.value||'').split(',').map((s)=>s.trim()).filter(Boolean))} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" placeholder='"toast", "beep"' />
            </div>
          </Section>

          <Section title="Tools Flags">
            <KvPairs
              label="Boolean flags (true/false)"
              obj={Object.fromEntries(Object.entries(cfg.tools || {}).map(([k,v]: any)=>[k, typeof v === 'boolean' ? (v ? 'true' : 'false') : String(v)]))}
              onChange={(m)=>{
                const converted: any = {};
                Object.entries(m).forEach(([k, v]) => {
                  if (v === 'true') converted[k] = true;
                  else if (v === 'false') converted[k] = false;
                  else converted[k] = v as string;
                });
                set('tools', converted);
              }}
            />
          </Section>

          <Section title="Model Providers">
            <ModelProvidersEditor providers={cfg.model_providers || {}} onChange={(m)=> set('model_providers', m)} />
          </Section>

          <Section title="MCP Servers (Codex Config)">
            <McpServersEditor servers={cfg.mcp_servers || {}} onChange={(m)=> set('mcp_servers', m)} />
          </Section>

          <Section title="Files">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">File opener</label>
                <select value={cfg.file_opener || ''} onChange={(e)=> set('file_opener', e.target.value || undefined)} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                  <option value="">(default)</option>
                  <option value="vscode">vscode</option>
                  <option value="vscode-insiders">vscode-insiders</option>
                  <option value="windsurf">windsurf</option>
                  <option value="cursor">cursor</option>
                  <option value="none">none</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Docs max bytes</label>
                <input type="number" value={cfg.project_doc_max_bytes || ''} onChange={(e)=> set('project_doc_max_bytes', e.target.value ? Number(e.target.value) : undefined)} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
              </div>
            </div>
          </Section>

          <Section title="Shell Environment Policy">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Inherit</label>
                <select value={(cfg.shell_environment_policy?.inherit)||''} onChange={(e)=> set('shell_environment_policy', { ...(cfg.shell_environment_policy||{}), inherit: e.target.value})} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                  <option value="">(default)</option>
                  <option value="all">all</option>
                  <option value="core">core</option>
                  <option value="none">none</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Ignore default excludes</label>
                <input type="checkbox" checked={!!(cfg.shell_environment_policy?.ignore_default_excludes)} onChange={(e)=> set('shell_environment_policy', { ...(cfg.shell_environment_policy||{}), ignore_default_excludes: e.target.checked})} />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm w-40">Set (KEY=VALUE, comma-separated)</label>
              <input value={Object.entries(cfg.shell_environment_policy?.set||{}).map(([k,v]:any)=> `${k}=${v}`).join(', ')} onChange={(e)=>{
                const map: any = {}; (e.target.value||'').split(',').map(s=>s.trim()).filter(Boolean).forEach(pair=>{ const [k,...rest]=pair.split('='); map[k]=rest.join('=');});
                set('shell_environment_policy', { ...(cfg.shell_environment_policy||{}), set: map });
              }} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
            </div>
          </Section>

          <Section title="Workspace Write Sandbox">
            <div className="flex items-center gap-2">
              <label className="text-sm w-40">Writable roots (comma-separated)</label>
              <input value={(cfg.sandbox_workspace_write?.writable_roots||[]).join(', ')} onChange={(e)=> set('sandbox_workspace_write', { ...(cfg.sandbox_workspace_write||{}), writable_roots: (e.target.value||'').split(',').map((s)=>s.trim()).filter(Boolean) })} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!(cfg.sandbox_workspace_write?.network_access)} onChange={(e)=> set('sandbox_workspace_write', { ...(cfg.sandbox_workspace_write||{}), network_access: e.target.checked })} /> Network access</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!(cfg.sandbox_workspace_write?.exclude_tmpdir_env_var)} onChange={(e)=> set('sandbox_workspace_write', { ...(cfg.sandbox_workspace_write||{}), exclude_tmpdir_env_var: e.target.checked })} /> Exclude $TMPDIR</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!(cfg.sandbox_workspace_write?.exclude_slash_tmp)} onChange={(e)=> set('sandbox_workspace_write', { ...(cfg.sandbox_workspace_write||{}), exclude_slash_tmp: e.target.checked })} /> Exclude /tmp</label>
            </div>
          </Section>

          <div className="flex items-center justify-end gap-2 mt-4">
            <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={load}>Reload</button>
            <button className="px-3 py-1 rounded bg-[var(--accent)] text-white" onClick={save} disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
            <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={()=> window.aiw.restart()}>Restart Backend</button>
          </div>
          <div className="flex items-center justify-end gap-2 mt-2">
            <button className="px-3 py-1 rounded bg-[var(--accent)] text-white" onClick={saveAndRestart} disabled={saving}>{saving ? 'Saving…' : 'Save & Restart'}</button>
          </div>
        </>
      )}
    </div>
  );
};

export default SettingsWorkspace;

// --- Subcomponents ---------------------------------------------------------

const ModelProvidersEditor: React.FC<{ providers: Record<string, any>, onChange: (m: Record<string, any>)=>void }> = ({ providers, onChange }) => {
  const [newId, setNewId] = useState('');
  const ids = Object.keys(providers || {});
  const add = () => { const id = newId.trim(); if (!id) return; onChange({ ...providers, [id]: { base_url: '', env_key: '', http_headers: {}, env_http_headers: {}, query_params: {} } }); setNewId(''); };
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input value={newId} onChange={(e)=>setNewId(e.target.value)} placeholder="provider id (e.g. openai)" className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
        <button className="px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border)] text-xs" onClick={add}>Add</button>
      </div>
      {ids.length === 0 && <div className="text-2xs text-[var(--text-tertiary)]">No providers</div>}
      {ids.map((id) => (
        <div key={id} className="border border-[var(--border)] rounded p-3 bg-[var(--bg-tertiary)] space-y-2">
          <div className="flex items-center justify-between">
            <div className="font-semibold">{id}</div>
            <button className="text-red-300 underline text-xs" onClick={()=>{ const m = { ...providers }; delete m[id]; onChange(m); }}>Remove</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <Input label="Base URL" value={providers[id]?.base_url || ''} onChange={(v)=> onChange({ ...providers, [id]: { ...(providers[id]||{}), base_url: v } })} />
            <Input label="Env Key" value={providers[id]?.env_key || ''} onChange={(v)=> onChange({ ...providers, [id]: { ...(providers[id]||{}), env_key: v } })} />
          </div>
          <KvPairs label="HTTP Headers" obj={providers[id]?.http_headers||{}} onChange={(m)=> onChange({ ...providers, [id]: { ...(providers[id]||{}), http_headers: m } })} />
          <KvPairs label="Env HTTP Headers" obj={providers[id]?.env_http_headers||{}} onChange={(m)=> onChange({ ...providers, [id]: { ...(providers[id]||{}), env_http_headers: m } })} />
          <KvPairs label="Query Params" obj={providers[id]?.query_params||{}} onChange={(m)=> onChange({ ...providers, [id]: { ...(providers[id]||{}), query_params: m } })} />
        </div>
      ))}
    </div>
  );
};

const McpServersEditor: React.FC<{ servers: Record<string, any>, onChange: (m: Record<string, any>)=>void }> = ({ servers, onChange }) => {
  const [newId, setNewId] = useState('');
  const ids = Object.keys(servers || {});
  const add = () => { const id = newId.trim(); if (!id) return; onChange({ ...servers, [id]: { command: '', args: [], env: {} } }); setNewId(''); };
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input value={newId} onChange={(e)=>setNewId(e.target.value)} placeholder="server id (e.g. obsidian)" className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
        <button className="px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border)] text-xs" onClick={add}>Add</button>
      </div>
      {ids.length === 0 && <div className="text-2xs text-[var(--text-tertiary)]">No MCP servers</div>}
      {ids.map((id) => (
        <div key={id} className="border border-[var(--border)] rounded p-3 bg-[var(--bg-tertiary)] space-y-2">
          <div className="flex items-center justify-between">
            <div className="font-semibold">{id}</div>
            <button className="text-red-300 underline text-xs" onClick={()=>{ const m = { ...servers }; delete m[id]; onChange(m); }}>Remove</button>
          </div>
          <Input label="Command" value={servers[id]?.command || ''} onChange={(v)=> onChange({ ...servers, [id]: { ...(servers[id]||{}), command: v } })} />
          <Input label="Args (space separated)" value={(servers[id]?.args||[]).join(' ')} onChange={(v)=> onChange({ ...servers, [id]: { ...(servers[id]||{}), args: (v||'').split(' ').map((s:string)=>s.trim()).filter(Boolean) } })} />
          <KvPairs label="Env" obj={servers[id]?.env||{}} onChange={(m)=> onChange({ ...servers, [id]: { ...(servers[id]||{}), env: m } })} />
        </div>
      ))}
    </div>
  );
};

const Input: React.FC<{ label: string, value: string, onChange: (v: string)=>void }> = ({ label, value, onChange }) => (
  <div className="flex items-center gap-2">
    <label className="text-sm w-40">{label}</label>
    <input value={value} onChange={(e)=> onChange(e.target.value)} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" />
  </div>
);

const KvPairs: React.FC<{ label: string, obj: Record<string,string>, onChange: (m: Record<string,string>)=>void }> = ({ label, obj, onChange }) => {
  const entries = Object.entries(obj || {});
  const [k, setK] = useState('');
  const [v, setV] = useState('');
  return (
    <div>
      <div className="text-sm text-[var(--text-secondary)] mb-1">{label}</div>
      <div className="space-y-2">
        {entries.length === 0 && <div className="text-2xs text-[var(--text-tertiary)]">(none)</div>}
        {entries.map(([key, val]) => (
          <div key={key} className="flex items-center gap-2">
            <input value={key} disabled className="w-48 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] font-mono text-xs" />
            <input value={val} onChange={(e)=>{ const m = { ...(obj||{}) }; m[key]=e.target.value; onChange(m); }} className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] font-mono text-xs" />
            <button className="px-2 py-1 rounded bg-red-500/20 border border-red-500/40 text-xs" onClick={()=>{ const m = { ...(obj||{}) }; delete m[key]; onChange(m); }}>Remove</button>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <input value={k} onChange={(e)=>setK(e.target.value)} placeholder="KEY" className="w-48 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] font-mono text-xs" />
          <input value={v} onChange={(e)=>setV(e.target.value)} placeholder="value" className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] font-mono text-xs" />
          <button className="px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border)] text-xs" onClick={()=>{ if (!k.trim()) return; const m = { ...(obj||{}) }; m[k.trim()] = v; onChange(m); setK(''); setV(''); }}>Add</button>
        </div>
      </div>
    </div>
  );
};
