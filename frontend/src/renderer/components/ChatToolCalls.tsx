import React, { useMemo, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';

const ChatToolCalls: React.FC = () => {
  const { toolCalls, setDraftMessage } = useBackend();
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const calls = useMemo(() => toolCalls.slice(0, 20), [toolCalls]);

  if (!calls.length) return null;

  const copy = async (text: string) => {
    try { await navigator.clipboard.writeText(text); } catch {}
  };

  return (
    <div className="max-w-4xl mx-auto px-4 mb-3">
      <div className="text-sm text-[var(--text-secondary)] mb-1">Tool Calls</div>
      <div className="space-y-2">
        {calls.map((c) => {
          const isOpen = open[c.call_id] ?? true;
          const header = c.kind === 'exec' ? `$ ${(c.command||[]).join(' ')}` : (c.name || 'tool');
          const status = c.status === 'running' ? 'running' : `done${c.exit_code !== undefined ? ` (${c.exit_code})` : ''}`;
          const outputCombined = (c.formatted_output || c.stdout || '') + (c.stderr ? `\n[stderr]\n${c.stderr}` : '');
          return (
            <div key={c.call_id} className="border border-[var(--border)] rounded bg-[var(--bg-secondary)]">
              <button className="w-full text-left px-3 py-2 flex items-center justify-between" onClick={() => setOpen(o=>({ ...o, [c.call_id]: !isOpen }))}>
                <div className="truncate font-mono text-sm">
                  <span className={`inline-block w-2 h-2 rounded-full mr-2 ${c.status==='running'?'bg-yellow-500 animate-pulse':'bg-green-500'}`}></span>
                  {header}
                  {c.cwd ? <span className="text-[var(--text-tertiary)] ml-2">(cwd: {c.cwd})</span> : null}
                </div>
                <div className="text-xs text-[var(--text-tertiary)]">{status}</div>
              </button>
              {isOpen && (
                <div className="px-3 pb-3">
                  <div className="flex gap-2 mb-2">
                    <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={() => copy(outputCombined)}>Copy Output</button>
                    <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={() => setDraftMessage((prev)=> (prev ? prev+"\n\n" : '') + '```\n' + outputCombined + '\n```')}>Quote Output</button>
                  </div>
                  <pre className="whitespace-pre-wrap text-xs font-mono bg-[var(--bg-tertiary)] border border-[var(--border)] rounded p-2 max-h-64 overflow-auto">{outputCombined || '[no output yet]'}</pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChatToolCalls;

