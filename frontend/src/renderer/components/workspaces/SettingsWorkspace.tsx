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
  const [authInfo, setAuthInfo] = useState<any>(null);
  const [downscale, setDownscale] = useState<boolean>(() => localStorage.getItem('vision.downscale') === 'true');
  const [maxDim, setMaxDim] = useState<number>(() => {
    const v = parseInt(localStorage.getItem('vision.maxDim') || '1280', 10);
    return isNaN(v) ? 1280 : v;
  });
  const [uiBasePx, setUiBasePx] = useState<number>(() => {
    const v = parseInt(localStorage.getItem('ui.fontSizeBase') || '13', 10);
    return isNaN(v) ? 13 : v;
  });
  const [primaryColor, setPrimaryColor] = useState<string>(() => {
    try { const v = localStorage.getItem('ui.primaryColor'); if (v) return v; } catch {}
    try { return getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() || '#6366f1'; } catch { return '#6366f1'; }
  });
  const [secondaryColor, setSecondaryColor] = useState<string>(() => {
    try { const v = localStorage.getItem('ui.secondaryColor'); if (v) return v; } catch {}
    try { return getComputedStyle(document.documentElement).getPropertyValue('--secondary-color').trim() || '#151520'; } catch { return '#151520'; }
  });
  const [themePreset, setThemePreset] = useState<string>(() => localStorage.getItem('ui.themePreset') || 'default');
  const [uiFont, setUiFont] = useState<string>(() => localStorage.getItem('ui.fontFamily') || 'cascadia');
  const [monoFont, setMonoFont] = useState<string>(() => localStorage.getItem('ui.fontMono') || 'cascadia');
  const [compact, setCompact] = useState<boolean>(() => localStorage.getItem('ui.compact') === 'true');
  const [scaleHeadings, setScaleHeadings] = useState<boolean>(() => localStorage.getItem('ui.scaleHeadings') !== 'false');
  const [scaleButtons, setScaleButtons] = useState<boolean>(() => localStorage.getItem('ui.scaleButtons') !== 'false');

  useEffect(() => {
    // Apply current UI vars on entry
    try {
      document.documentElement.style.setProperty('--font-size-base', `${uiBasePx}px`);
      document.documentElement.style.setProperty('--primary-color', primaryColor);
      document.documentElement.style.setProperty('--secondary-color', secondaryColor);
      applyThemePreset(themePreset, false);
      applyUiFont(uiFont);
      applyMonoFont(monoFont);
      if (compact) document.body.classList.add('compact');
      document.documentElement.style.setProperty('--heading-scale', scaleHeadings ? '1' : '0');
      document.documentElement.style.setProperty('--button-scale', scaleButtons ? '1' : '0');
    } catch {}
  }, []);

  function applyUiFont(choice: string) {
    let val = "'Cascadia Code', 'Cascadia Mono', 'Segoe UI Variable', 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif";
    if (choice === 'inter') val = "'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif";
    if (choice === 'jetbrains') val = "'JetBrains Mono', 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif";
    document.documentElement.style.setProperty('--font-ui', val);
  }

  function applyMonoFont(choice: string) {
    let val = "'Cascadia Code', 'Cascadia Mono', 'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace";
    if (choice === 'jetbrains') val = "'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace";
    if (choice === 'cascadia') val = "'Cascadia Code', 'Cascadia Mono', 'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace";
    document.documentElement.style.setProperty('--font-mono', val);
  }

  function applyThemePreset(preset: string, persist: boolean = true) {
    const root = document.documentElement;
    const body = document.body;
    // Defaults
    let vars: Record<string, string> = {
      '--bg-primary': '#0a0a0f',
      '--bg-secondary': '#151520',
      '--bg-tertiary': '#1e1e2e',
      '--text-primary': '#f8fafc',
      '--text-secondary': '#cbd5e1',
      '--accent': '#6366f1',
      '--border': '#374151',
    };
    if (preset === 'ocean') {
      vars = {
        '--bg-primary': '#0b1221',
        '--bg-secondary': '#0f1b2d',
        '--bg-tertiary': '#13233a',
        '--text-primary': '#e6f1ff',
        '--text-secondary': '#a6c1e0',
        '--accent': '#4e9eff',
        '--border': '#264766',
      };
    } else if (preset === 'solarized') {
      // Solarized dark skew
      vars = {
        '--bg-primary': '#002b36',
        '--bg-secondary': '#073642',
        '--bg-tertiary': '#0a3946',
        '--text-primary': '#eee8d5',
        '--text-secondary': '#93a1a1',
        '--accent': '#268bd2',
        '--border': '#0e3d47',
      };
    }
    try {
      Object.entries(vars).forEach(([k,v]) => root.style.setProperty(k, v));
      // Persist preset name
      if (persist) localStorage.setItem('ui.themePreset', preset);
    } catch {}
  }
  const [workbenchCfg, setWorkbenchCfg] = useState<{ backend?: { codex_path?: string; profile?: string } }>({});

  const profiles = Object.keys((cfg.profiles || {}));

  const load = async () => {
    setLoading(true); setError(null);
    const res = await window.aiw.readCodexConfig();
    if (res.ok) { setCfg(res.config || {}); setPath(res.path); } else { setError(res.error || 'Failed to read config'); }
    setLoading(false);
  };
  useEffect(() => { load(); (async()=>{ try { const wb = await window.aiw.getWorkbenchConfig(); if (wb?.ok) setWorkbenchCfg(wb); } catch {} })(); }, []);

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
            <div className="flex items-center gap-2">
              <div className="text-sm text-[var(--text-secondary)]">Login to ChatGPT (for models that require it)</div>
              <button className="px-3 py-1 rounded bg-[var(--accent)] text-white" onClick={()=>window.aiw.login()}>Login</button>
              <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={async()=>{ try { const info = await window.aiw.authInfo(); setAuthInfo(info||null); } catch {} }}>Status</button>
            </div>
            <AuthStatusPanel info={authInfo} />
          </Section>

          <Section title="Profile">
            <div className="flex items-center gap-2">
              <label className="text-sm w-40">Active profile</label>
              <select
                value={(workbenchCfg?.backend?.profile || '') as string}
                onChange={async (e)=>{ try { await window.aiw.setProfile(e.target.value); setWorkbenchCfg((prev)=>({ backend: { ...(prev.backend||{}), profile: e.target.value } })); await window.aiw.restart(); } catch {} }}
                className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]"
              >
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
                <label className="text-sm w-40">Enable web search</label>
                <input type="checkbox" checked={!!cfg.tools_web_search_request} onChange={(e)=> set('tools_web_search_request', e.target.checked)} />
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

          <Section title="Vision">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!cfg.include_view_image_tool}
                  onChange={(e)=> set('include_view_image_tool', e.target.checked)}
                />
                Allow model to attach images (view_image)
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={downscale}
                  onChange={(e)=> { setDownscale(e.target.checked); try { localStorage.setItem('vision.downscale', String(e.target.checked)); } catch {} }}
                />
                Downscale images before sending
              </label>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Max image dimension (px)</label>
                <input
                  type="number"
                  min={64}
                  value={maxDim}
                  onChange={(e)=> { const v = Math.max(64, parseInt(e.target.value||'1280',10)||1280); setMaxDim(v); try { localStorage.setItem('vision.maxDim', String(v)); } catch {} }}
                  className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]"
                />
              </div>
            </div>
            <div className="text-2xs text-[var(--text-tertiary)] mt-2">Note: view_image is always enabled at runtime by the frontend for convenience.</div>
          </Section>

          <Section title="UI">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Theme preset</label>
                <select
                  value={themePreset}
                  onChange={(e)=> { const v = e.target.value; setThemePreset(v); applyThemePreset(v, true); }}
                  className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]"
                >
                  <option value="default">Default</option>
                  <option value="ocean">Ocean</option>
                  <option value="solarized">Solarized</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">UI scale (base px)</label>
                <input
                  type="range"
                  min={11}
                  max={16}
                  step={0.5}
                  value={uiBasePx}
                  onChange={(e)=> {
                    const v = parseFloat(e.target.value);
                    setUiBasePx(v);
                    try { document.documentElement.style.setProperty('--font-size-base', `${v}px`); localStorage.setItem('ui.fontSizeBase', String(v)); } catch {}
                  }}
                  className="flex-1"
                />
                <span className="text-xs w-10 text-right">{uiBasePx}px</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Primary color</label>
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e)=> {
                    const v = e.target.value;
                    setPrimaryColor(v);
                    try { document.documentElement.style.setProperty('--primary-color', v); localStorage.setItem('ui.primaryColor', v); } catch {}
                  }}
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Secondary color</label>
                <input
                  type="color"
                  value={secondaryColor}
                  onChange={(e)=> {
                    const v = e.target.value;
                    setSecondaryColor(v);
                    try { document.documentElement.style.setProperty('--secondary-color', v); localStorage.setItem('ui.secondaryColor', v); } catch {}
                  }}
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">UI font</label>
                <select
                  value={uiFont}
                  onChange={(e)=> { const v = e.target.value; setUiFont(v); try { localStorage.setItem('ui.fontFamily', v); applyUiFont(v); } catch {} }}
                  className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]"
                >
                  <option value="cascadia">Cascadia</option>
                  <option value="inter">Inter</option>
                  <option value="jetbrains">JetBrains</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm w-40">Mono font</label>
                <select
                  value={monoFont}
                  onChange={(e)=> { const v = e.target.value; setMonoFont(v); try { localStorage.setItem('ui.fontMono', v); applyMonoFont(v); } catch {} }}
                  className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]"
                >
                  <option value="cascadia">Cascadia</option>
                  <option value="jetbrains">JetBrains</option>
                </select>
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={compact} onChange={(e)=>{ const v = e.target.checked; setCompact(v); try { localStorage.setItem('ui.compact', String(v)); if (v) document.body.classList.add('compact'); else document.body.classList.remove('compact'); } catch {} }} />
                Compact mode (reduced paddings/gaps)
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={scaleHeadings} onChange={(e)=>{ const v = e.target.checked; setScaleHeadings(v); try { localStorage.setItem('ui.scaleHeadings', String(v)); document.documentElement.style.setProperty('--heading-scale', v ? '1' : '0'); } catch {} }} />
                Apply scale to headings
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={scaleButtons} onChange={(e)=>{ const v = e.target.checked; setScaleButtons(v); try { localStorage.setItem('ui.scaleButtons', String(v)); document.documentElement.style.setProperty('--button-scale', v ? '1' : '0'); } catch {} }} />
                Apply scale to buttons
              </label>
            </div>
            <div className="flex justify-end mt-3 gap-2">
              <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={()=>{
                try {
                  localStorage.removeItem('ui.fontSizeBase');
                  localStorage.removeItem('ui.primaryColor');
                  localStorage.removeItem('ui.secondaryColor');
                  localStorage.removeItem('ui.fontFamily');
                  localStorage.removeItem('ui.fontMono');
                  localStorage.removeItem('ui.compact');
                  localStorage.removeItem('ui.scaleHeadings');
                  localStorage.removeItem('ui.scaleButtons');
                } catch {}
                setUiBasePx(13);
                setPrimaryColor('#6366f1');
                setSecondaryColor('#151520');
                setUiFont('cascadia');
                setMonoFont('cascadia');
                setCompact(false);
                setScaleHeadings(true);
                setScaleButtons(true);
                try {
                  document.documentElement.style.setProperty('--font-size-base', '13px');
                  document.documentElement.style.setProperty('--primary-color', '#6366f1');
                  document.documentElement.style.setProperty('--secondary-color', '#151520');
                  applyUiFont('cascadia');
                  applyMonoFont('cascadia');
                  document.body.classList.remove('compact');
                  document.documentElement.style.setProperty('--heading-scale', '1');
                  document.documentElement.style.setProperty('--button-scale', '1');
                } catch {}
              }}>Reset to defaults</button>
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

const AuthStatusPanel: React.FC<{ info: any }> = ({ info }) => {
  if (!info) return null;
  const rows: Array<[string, string]> = [];
  rows.push(['Mode', info.mode || 'none']);
  if (info.mode === 'api_key' && info.masked_api_key) rows.push(['API Key', info.masked_api_key]);
  if (info.email) rows.push(['Email', info.email]);
  if (info.account_id) rows.push(['Account ID', info.account_id]);
  if (info.plan_type) rows.push(['Plan', info.plan_type]);
  if (info.last_refresh) rows.push(['Last Refresh', info.last_refresh]);
  return (
    <div className="mt-3 border border-[var(--border)] rounded bg-[var(--bg-tertiary)] p-3 text-sm">
      {rows.length === 0 ? (
        <div className="text-[var(--text-tertiary)]">No status available</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1">
          {rows.map(([k, v]) => (
            <div key={k} className="flex items-center gap-2">
              <div className="w-32 text-[var(--text-tertiary)]">{k}</div>
              <div className="font-mono break-all">{v}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

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
