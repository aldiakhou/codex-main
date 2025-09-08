import React, { useState } from 'react';

type Props = { isOpen: boolean; onClose: () => void; onSaved: () => void; initial?: { name: string; command: string; args?: string[]; env?: Record<string,string> } };

const McpServerModal: React.FC<Props> = ({ isOpen, onClose, onSaved, initial }) => {
  const [name, setName] = useState('');
  const [command, setCommand] = useState('');
  const [args, setArgs] = useState('');
  const [envList, setEnvList] = useState<Array<{ key: string; value: string }>>([]);
  const [saving, setSaving] = useState(false);
  if (!isOpen) return null;

  React.useEffect(() => {
    if (initial && isOpen) {
      setName(initial.name || '');
      setCommand(initial.command || '');
      setArgs((initial.args || []).join(' '));
      const list: Array<{ key: string; value: string }> = [];
      if (initial.env) {
        for (const [k, v] of Object.entries(initial.env)) list.push({ key: k, value: String(v) });
      }
      setEnvList(list.length ? list : [{ key: '', value: '' }]);
    } else if (isOpen) {
      setName(''); setCommand(''); setArgs(''); setEnvList([{ key: '', value: '' }]);
    }
  }, [initial, isOpen]);

  const save = async () => {
    if (!name.trim() || !command.trim()) return;
    setSaving(true);
    try {
      const srv = {
        name: name.trim(),
        command: command.trim(),
        args: args.trim() ? args.split(/\s+/) : [],
        env: envList.reduce((acc, { key, value }) => { if (key.trim()) acc[key.trim()] = value; return acc; }, {} as Record<string,string>),
      };
      const ok = await window.aiw.upsertMcpServer(srv);
      if (ok) {
        await window.aiw.restart();
        onSaved();
        onClose();
      }
    } finally { setSaving(false); }
  };

  const addEnvRow = () => setEnvList((prev) => [...prev, { key: '', value: '' }]);
  const delEnvRow = (idx: number) => setEnvList((prev) => prev.filter((_, i) => i !== idx));
  const setEnvKey = (idx: number, key: string) => setEnvList((prev) => prev.map((r, i) => i === idx ? { ...r, key } : r));
  const setEnvVal = (idx: number, value: string) => setEnvList((prev) => prev.map((r, i) => i === idx ? { ...r, value } : r));

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-[var(--bg-secondary)] w-full max-w-xl rounded-lg border border-[var(--border)] shadow-xl">
        <div className="p-4 border-b border-[var(--border)] flex items-center justify-between">
          <h2 className="text-lg font-semibold">Connect MCP Server</h2>
          <button className="text-xl" onClick={onClose}>×</button>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <label className="block text-sm mb-1">Name (identifier)</label>
            <input value={name} onChange={(e)=>setName(e.target.value)} disabled={!!initial} className="w-full border border-[var(--border)] rounded px-2 py-1 bg-[var(--bg-tertiary)]" placeholder="e.g. obsidian" />
          </div>
          <div>
            <label className="block text-sm mb-1">Command</label>
            <input value={command} onChange={(e)=>setCommand(e.target.value)} className="w-full border border-[var(--border)] rounded px-2 py-1 bg-[var(--bg-tertiary)]" placeholder="path to executable" />
          </div>
          <div>
            <label className="block text-sm mb-1">Args (space separated)</label>
            <input value={args} onChange={(e)=>setArgs(e.target.value)} className="w-full border border-[var(--border)] rounded px-2 py-1 bg-[var(--bg-tertiary)]" placeholder="--flag value" />
          </div>
          <div>
            <label className="block text-sm mb-1">Environment Variables</label>
            <div className="space-y-2">
              {envList.map((row, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    value={row.key}
                    onChange={(e)=>setEnvKey(i, e.target.value)}
                    className="flex-1 border border-[var(--border)] rounded px-2 py-1 bg-[var(--bg-tertiary)] font-mono text-xs"
                    placeholder="KEY"
                  />
                  <input
                    value={row.value}
                    onChange={(e)=>setEnvVal(i, e.target.value)}
                    className="flex-[2] border border-[var(--border)] rounded px-2 py-1 bg-[var(--bg-tertiary)] font-mono text-xs"
                    placeholder="VALUE"
                  />
                  <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={()=>delEnvRow(i)}>Remove</button>
                </div>
              ))}
              <button className="px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border)] text-xs" onClick={addEnvRow}>+ Add Variable</button>
            </div>
          </div>
          <div className="text-xs text-[var(--text-tertiary)]">Saved to ~/.ai-workbench/config.json and backend restarts.</div>
        </div>
        <div className="p-4 border-t border-[var(--border)] flex justify-end gap-2">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)]" onClick={onClose}>Cancel</button>
          <button className="px-3 py-1 rounded bg-[var(--accent)] text-white" onClick={save} disabled={saving || !name.trim() || !command.trim()}>{saving ? 'Saving...' : 'Save'}</button>
        </div>
      </div>
    </div>
  );
};

export default McpServerModal;
