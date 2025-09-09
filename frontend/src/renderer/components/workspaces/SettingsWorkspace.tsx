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

  const set = (key: string, value: any) => setCfg((prev: any) => ({ ...prev, [key]: value }));

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
          </div>
        </>
      )}
    </div>
  );
};

export default SettingsWorkspace;

