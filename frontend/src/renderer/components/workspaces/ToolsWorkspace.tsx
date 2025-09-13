import React, { useEffect, useMemo, useState } from 'react';
import { useBackend } from '../../contexts/BackendContext';
import { IconTools } from '@tabler/icons-react';
import McpServerModal from '../McpServerModal';

const ToolsWorkspace: React.FC = () => {
  const { status, logs, mcpTools, refreshMcpTools, mcpServers, refreshMcpServers, serverErrors, customPrompts, refreshCustomPrompts, setDraftMessage, userTurn } = useBackend();
  const [filter, setFilter] = useState('');
  const [openModal, setOpenModal] = useState<string | false>(false);
  const [toolModal, setToolModal] = useState<false | { fq: string; def: any }>(false);
  useEffect(() => { refreshMcpServers().then(()=>refreshMcpTools()).catch(()=>{}); }, []);
  const entries = useMemo(() => {
    const items = Object.entries(mcpTools || {});
    if (!filter) return items;
    const f = filter.toLowerCase();
    return items.filter(([name, def]: any) => name.toLowerCase().includes(f) || (def?.name || '').toLowerCase().includes(f) || (def?.description || '').toLowerCase().includes(f));
  }, [mcpTools, filter]);

  // Derive connected servers from FQN like "server.tool" when available
  const servers = useMemo(() => {
    const counts = new Map<string, number>();
    for (const [fq] of Object.entries(mcpTools || {})) {
      const fqs = String(fq);
      let s = 'unknown';
      if (fqs.includes('__')) s = fqs.split('__', 1)[0];
      else if (fqs.includes('.')) s = fqs.split('.', 1)[0];
      else s = fqs;
      counts.set(s, (counts.get(s) || 0) + 1);
    }
    const names = Object.keys(mcpServers || {});
    const all = names.length ? names : Array.from(counts.keys());
    return all.map((name) => ({ name, count: counts.get(name) || 0 }));
  }, [mcpServers, mcpTools]);
  // Static built-in tools list to help users understand what's available to the model
  const builtinTools: Array<{ name: string; description: string }> = [
    { name: 'shell', description: 'Run shell commands inside Codex sandbox (or streamable exec).' },
    { name: 'update_plan', description: 'Maintain a step-by-step plan of the task.' },
    { name: 'apply_patch', description: 'Apply atomic multi-file code changes via a structured patch.' },
    { name: 'web_search', description: 'Search the web (if enabled) and incorporate results.' },
    { name: 'view_image', description: 'Attach a local image path to the conversation context.' },
    { name: 'agents_list', description: 'List available built-in and configured agents.' },
    { name: 'agents_start', description: 'Start an agent task and get a task id.' },
    { name: 'agents_status', description: 'Get the current status/result of an agent task.' },
    { name: 'agents_cancel', description: 'Request cancellation of an agent task.' },
    { name: 'agents_reload', description: 'Reload agents from ~/.codex/agents.toml and return the list.' },
  ];

  return (
    <div className="flex-1 p-12 overflow-y-auto min-h-0 h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Tools & MCP Servers</h1>
        <div className="text-sm text-[var(--text-secondary)]">Backend: {status}</div>
      </div>
      <p className="text-[var(--text-secondary)] mb-8">
        Connect and manage your AI tools and Model Context Protocol servers.
      </p>
      <button className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-bold py-2 px-4 rounded-lg mb-8 transition-colors" onClick={()=>setOpenModal('') }>
        + Connect New MCP Server
      </button>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {servers.length === 0 ? (
          <div className="text-[var(--text-secondary)]">No MCP servers connected.</div>
        ) : (
          servers.map((s) => {
            const err = serverErrors[s.name];
            const connected = s.count > 0 && !err;
            const pending = !connected && !err;
            return (
              <div key={s.name} className="bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--border)]">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-lg font-bold truncate" title={s.name}>{s.name}</h3>
                  <div className="text-xs flex gap-2">
                    <button className="underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]" onClick={()=>setOpenModal(s.name)}>Edit</button>
                    <button className="underline text-red-400 hover:text-red-300" onClick={async()=>{ if (confirm(`Remove MCP server '${s.name}'?`)) { await window.aiw.removeMcpServer(s.name); await window.aiw.restart(); await refreshMcpServers(); await refreshMcpTools(); } }}>Remove</button>
                  </div>
                </div>
                <p className="text-sm text-[var(--text-secondary)] mb-3">{s.count} tool{s.count === 1 ? '' : 's'} available</p>
                {connected && (
                  <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-[var(--success)] bg-green-200">Connected</span>
                )}
                {pending && (
                  <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-[var(--warning)] bg-yellow-200">Pending</span>
                )}
                {err && (
                  <div className="mt-2 text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded p-2" title={err}>Error: {err}</div>
                )}
              </div>
            );
          })
        )}
      </div>
      {/* Built-in Tools (read-only) */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold mb-2">Built-in Tools</h2>
        <div className="border border-[var(--border)] rounded bg-[var(--bg-secondary)] p-2 max-h-80 overflow-auto text-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {builtinTools.map((t) => (
              <div key={t.name} className="border border-[var(--border)] rounded p-3 bg-[var(--bg-tertiary)]">
                <div className="flex items-center gap-2">
                  <IconTools size={16} className="text-[var(--text-secondary)]" />
                  <div className="font-semibold truncate" title={t.name}>{t.name}</div>
                </div>
                <div className="text-xs text-[var(--text-tertiary)] mt-1 line-clamp-4" title={t.description}>{t.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Custom Prompts</h2>
          <div className="flex items-center gap-2">
            <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-sm" onClick={()=>refreshCustomPrompts()}>Refresh</button>
          </div>
        </div>
        <div className="border border-[var(--border)] rounded bg-[var(--bg-secondary)] p-2 max-h-80 overflow-auto text-sm">
          {(!customPrompts || customPrompts.length === 0) ? (
            <div className="text-[var(--text-tertiary)]">No custom prompts found</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {customPrompts.map((p: any) => (
                <div key={p.name+String(p.path)} className="border border-[var(--border)] rounded p-3 bg-[var(--bg-tertiary)]">
                  <div className="font-semibold truncate" title={p.name}>{p.name}</div>
                  <div className="text-2xs text-[var(--text-tertiary)] truncate" title={p.path}>{p.path}</div>
                  <div className="mt-2 text-xs text-[var(--text-primary)] line-clamp-4 whitespace-pre-wrap">{p.content}</div>
                  <div className="mt-2 flex gap-2 justify-end">
                    <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={async()=>{ try { await navigator.clipboard.writeText(p.content); } catch {} }}>Copy</button>
                    <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={()=> setDraftMessage((prev: string)=> (prev ? prev+"\n\n" : '') + p.content)}>Insert</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="mt-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">MCP Tools</h2>
          <div className="flex items-center gap-2">
            <input value={filter} onChange={(e)=>setFilter(e.target.value)} placeholder="Filter tools..." className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-sm" />
            <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-sm" onClick={()=>refreshMcpTools()}>Refresh</button>
          </div>
        </div>
        <div className="border border-[var(--border)] rounded bg-[var(--bg-secondary)] p-2 max-h-80 overflow-auto text-sm">
          {entries.length === 0 ? (
            <div className="text-[var(--text-tertiary)]">No tools</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {entries.map(([fq, def]: any) => (
                <div key={fq} className="border border-[var(--border)] rounded p-3 bg-[var(--bg-tertiary)]">
                  <div className="flex items-center gap-2">
                    <IconTools size={16} className="text-[var(--text-secondary)]" />
                    <div className="font-semibold truncate" title={fq}>{def?.name || fq}</div>
                  </div>
                  {def?.description ? <div className="text-xs text-[var(--text-tertiary)] mt-1 line-clamp-3" title={def.description}>{def.description}</div> : null}
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <span className="text-2xs text-[var(--text-tertiary)] truncate" title={fq}>{fq}</span>
                    <div className="flex items-center gap-2">
                    <button
                      className="text-2xs px-2 py-0.5 rounded bg-[var(--bg-secondary)] border border-[var(--border)]"
                      title="Fill arguments then insert into chat"
                      onClick={()=> setToolModal({ fq, def })}
                    >Use</button>
                      <span className="text-2xs font-semibold inline-block py-0.5 px-2 uppercase rounded text-[var(--success)] bg-green-200">Available</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="mt-8">
        <h2 className="text-lg font-semibold mb-2">Recent Backend Activity</h2>
        <div className="border border-[var(--border)] rounded bg-[var(--bg-secondary)] p-2 max-h-48 overflow-auto font-mono text-xs">
          {logs.slice(-100).map((l, i) => (
            <div key={i} className="whitespace-pre-wrap">{l}</div>
          ))}
        </div>
      </div>
      <McpServerModal isOpen={openModal !== false} onClose={()=>setOpenModal(false)} onSaved={async()=>{ await refreshMcpServers(); await refreshMcpTools(); }} initial={openModal ? (mcpServers[String(openModal)] || undefined) : undefined} />
      <ToolArgsModal
        open={!!toolModal}
        def={toolModal ? toolModal.def : null}
        fq={toolModal ? toolModal.fq : ''}
        onClose={()=> setToolModal(false)}
        onInsert={(jsonText)=>{
          const name = (toolModal && (toolModal.def?.name || toolModal.fq)) || 'tool';
          const hint = `Run MCP tool ${name} with args: ${jsonText}`;
          setDraftMessage((prev:any)=> (prev ? prev+"\n\n" : '') + hint);
          setToolModal(false);
        }}
        onRun={async(jsonText)=>{
          try {
            const name = (toolModal && (toolModal.def?.name || toolModal.fq)) || 'tool';
            const text = `Please call the MCP tool "${name}" with the following JSON arguments. Return only the tool output.\n\n\`\`\`json\n${jsonText}\n\`\`\``;
            await userTurn(text);
          } catch {}
          setToolModal(false);
        }}
      />
    </div>
  );
};

export default ToolsWorkspace;

const ToolArgsModal: React.FC<{
  open: boolean;
  def: any;
  fq: string;
  onClose: () => void;
  onInsert: (jsonText: string) => void;
  onRun: (jsonText: string) => void;
}> = ({ open, def, fq, onClose, onInsert, onRun }) => {
  const [values, setValues] = useState<Record<string, string>>({});
  const props = def?.input_schema?.properties || {};
  const required: string[] = Array.isArray(def?.input_schema?.required) ? def.input_schema.required : [];
  useEffect(() => {
    if (open) {
      const initial: Record<string, string> = {};
      Object.keys(props).forEach((k) => { initial[k] = ''; });
      setValues(initial);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, fq]);
  if (!open) return null;
  const entries = Object.entries(props) as Array<[string, any]>;
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center" role="dialog" aria-modal="true" aria-labelledby="tool-args-title">
      <div className="bg-[var(--bg-secondary)] w-full max-w-lg rounded-lg border border-[var(--border)]">
        <div className="p-3 border-b border-[var(--border)] flex items-center justify-between">
          <div id="tool-args-title" className="font-semibold truncate">Use MCP Tool</div>
          <button className="text-xl" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="p-4 space-y-3 text-sm">
          <div className="text-[var(--text-tertiary)] truncate">{def?.name || fq}</div>
          {entries.length === 0 ? (
            <div className="text-[var(--text-tertiary)]">No arguments</div>
          ) : (
            <div className="space-y-2">
              {entries.map(([k, schema]) => (
                <div key={k} className="flex items-center gap-2">
                  <label className="w-32 text-xs text-[var(--text-tertiary)]">
                    {k}{required.includes(k) ? ' *' : ''}
                  </label>
                  <input
                    className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs font-mono"
                    placeholder={schema?.description || schema?.type || 'value'}
                    value={values[k] ?? ''}
                    onChange={(e)=> setValues((prev)=> ({ ...prev, [k]: e.target.value }))}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="p-3 border-t border-[var(--border)] flex gap-2 justify-end">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)]" onClick={onClose}>Cancel</button>
          <button
            className="px-3 py-1 rounded bg-[var(--accent)] text-white"
            onClick={()=>{
              try {
                const obj: any = {};
                entries.forEach(([k]) => { if (values[k]) obj[k] = coerce(values[k]); });
                const jsonText = JSON.stringify(obj, null, 2);
                onInsert(jsonText);
              } catch {
                onInsert('{}');
              }
            }}
          >Insert</button>
          <button
            className="px-3 py-1 rounded bg-[var(--accent)]/90 text-white"
            onClick={()=>{
              try {
                const obj: any = {};
                entries.forEach(([k]) => { if (values[k]) obj[k] = coerce(values[k]); });
                const jsonText = JSON.stringify(obj, null, 2);
                onRun(jsonText);
              } catch {
                onRun('{}');
              }
            }}
          >Run</button>
        </div>
      </div>
    </div>
  );
};

function coerce(v: string): any {
  const t = v.trim();
  if (!t) return '';
  if (t === 'true') return true;
  if (t === 'false') return false;
  if (/^-?\d+$/.test(t)) return parseInt(t, 10);
  if (/^-?\d+\.\d+$/.test(t)) return parseFloat(t);
  try { return JSON.parse(t); } catch {}
  return v;
}
