import React, { useEffect, useMemo, useState } from 'react';
import { useBackend } from '../../contexts/BackendContext';
import { IconTools } from '@tabler/icons-react';
import McpServerModal from '../McpServerModal';

const ToolsWorkspace: React.FC = () => {
  const { status, logs, mcpTools, refreshMcpTools, mcpServers, refreshMcpServers, serverErrors } = useBackend();
  const [filter, setFilter] = useState('');
  const [openModal, setOpenModal] = useState<string | false>(false);
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
  return (
    <div className="flex-1 p-12 overflow-y-auto">
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
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-2xs text-[var(--text-tertiary)] truncate" title={fq}>{fq}</span>
                    <span className="text-2xs font-semibold inline-block py-0.5 px-2 uppercase rounded text-[var(--success)] bg-green-200">Available</span>
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
    </div>
  );
};

export default ToolsWorkspace;
