import React, { useMemo, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import { html as diff2html } from 'diff2html';

const ChatTurnDiff: React.FC = () => {
  const { turnDiff } = useBackend();
  const [open, setOpen] = useState(true);
  const content = useMemo(() => {
    if (!turnDiff) return '';
    try {
      return diff2html(turnDiff, {
        inputFormat: 'diff',
        matching: 'lines',
        outputFormat: 'side-by-side',
        drawFileList: false,
      } as any);
    } catch {
      return '';
    }
  }, [turnDiff]);

  if (!turnDiff) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 mb-3">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm text-[var(--text-secondary)]">Turn Changes</div>
        <div className="flex items-center gap-2">
          <button className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={async()=>{ try { await navigator.clipboard.writeText(turnDiff || ''); } catch {} }}>Copy Diff</button>
          <button className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => setOpen((v) => !v)}>
            {open ? 'Hide' : 'Show'}
          </button>
        </div>
      </div>
      {open && (
        <div className="border border-[var(--border)] rounded bg-[var(--bg-secondary)] p-2 max-h-[32rem] overflow-auto text-sm">
          <div className="d2h-wrapper" dangerouslySetInnerHTML={{ __html: content }} />
        </div>
      )}
    </div>
  );
};

export default ChatTurnDiff;
