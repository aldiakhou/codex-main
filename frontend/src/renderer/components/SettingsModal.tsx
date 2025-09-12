import React, { useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import { useFocusTrap } from '../hooks/useFocusTrap';

type Props = { isOpen: boolean; onClose: () => void };

const SettingsModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { setCodexPath, status, start } = useBackend();
  const [codexPath, setPath] = useState<string>(localStorage.getItem('codexPath') || '');
  const [saving, setSaving] = useState(false);
  if (!isOpen) return null;
  const { containerRef } = useFocusTrap<HTMLDivElement>(isOpen, onClose);

  const save = async () => {
    setSaving(true);
    try {
      const ok = await setCodexPath(codexPath);
      if (ok) {
        // restart backend with new path
        await start({ codexPath });
        onClose();
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <div ref={containerRef} tabIndex={-1} className="bg-[var(--bg-secondary)] w-full max-w-xl rounded-lg border border-[var(--border)] shadow-xl">
        <div className="p-4 border-b border-[var(--border)] flex items-center justify-between">
          <h2 id="settings-title" className="text-lg font-semibold">Settings</h2>
          <button className="text-xl" aria-label="Close settings" onClick={onClose}>Cancel</button>
        </div>
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm mb-1">Codex Executable Path</label>
            <input
              className="w-full border border-[var(--border)] rounded px-2 py-1 bg-[var(--bg-tertiary)]"
              placeholder={"Path to codex (e.g. C\\\\path\\\\to\\\\codex.exe or /usr/local/bin/codex)"}
              value={codexPath}
              onChange={(e) => setPath(e.target.value)}
            />
            <div className="text-xs text-[var(--text-tertiary)] mt-1">Status: {status}</div>
          </div>
        </div>
        <div className="p-4 border-t border-[var(--border)] flex justify-end gap-2">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)]" onClick={onClose}>Cancel</button>
          <button className="px-3 py-1 rounded bg-[var(--accent)] text-white" onClick={save} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;

