import React, { useMemo, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import { html as diff2html } from 'diff2html';

const PatchApprovalModal: React.FC = () => {
  const { patchApprovalRequest, patchApproval, clearApprovals } = useBackend();
  if (!patchApprovalRequest) return null;
  const entries = Object.entries(patchApprovalRequest.changes || {});
  const [activeIdx, setActiveIdx] = useState(0);
  const [activePath, activeChange] = entries[activeIdx] || [undefined, undefined] as any;

  const diffHtml = useMemo(() => {
    if (!activePath || !activeChange) return '';
    if (activeChange.type === 'update' && activeChange.unified_diff) {
      try {
        return diff2html(activeChange.unified_diff, {
          inputFormat: 'diff',
          matching: 'lines',
          outputFormat: 'side-by-side',
          drawFileList: false,
        } as any);
      } catch {
        return '';
      }
    }
    if (activeChange.type === 'add') {
      const content = activeChange.content || '';
      const safe = content.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      return `<pre class="d2h-file-wrapper"><code>New file: ${activePath}\n\n${safe}</code></pre>`;
    }
    if (activeChange.type === 'delete') {
      return `<div class="p-3">Deleted file: ${activePath}</div>`;
    }
    return '';
  }, [activePath, activeChange]);

  const decide = async (d: 'approved' | 'approved_for_session' | 'denied' | 'abort') => {
    await patchApproval(patchApprovalRequest.id, d);
    clearApprovals();
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center">
      <div className="bg-[var(--bg-secondary)] w-full max-w-3xl rounded-lg border border-[var(--border)]">
        <div className="p-3 border-b border-[var(--border)] flex justify-between items-center">
          <div className="font-semibold">Approve Code Changes</div>
          <button onClick={() => clearApprovals()}>×</button>
        </div>
        <div className="p-4 text-sm space-y-3">
          {patchApprovalRequest.reason && (
            <div className="text-[var(--text-tertiary)]">Reason: {patchApprovalRequest.reason}</div>
          )}
          <div className="text-xs">{entries.length} file(s) to change</div>
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-1 max-h-80 overflow-auto border border-[var(--border)] rounded bg-[var(--bg-tertiary)]">
              {entries.map(([file, change], i) => (
                <button
                  key={file}
                  onClick={() => setActiveIdx(i)}
                  className={`w-full text-left px-2 py-1 border-b border-[var(--border)] last:border-0 flex items-center gap-2 hover:bg-[var(--bg-secondary)] ${i === activeIdx ? 'bg-[var(--bg-secondary)]' : ''}`}
                >
                  <span className={`text-xs px-2 py-0.5 rounded ${change.type === 'add' ? 'bg-green-500/20' : change.type === 'delete' ? 'bg-red-500/20' : 'bg-yellow-500/20'}`}>{change.type}</span>
                  <span className="font-mono text-xs truncate" title={file}>{file}</span>
                </button>
              ))}
            </div>
            <div className="col-span-2 border border-[var(--border)] rounded bg-[var(--bg-tertiary)] min-h-80 max-h-80 overflow-auto">
              <div className="d2h-wrapper" dangerouslySetInnerHTML={{ __html: diffHtml }} />
            </div>
          </div>
        </div>
        <div className="p-3 border-t border-[var(--border)] flex gap-2 justify-end">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)]" onClick={() => decide('denied')}>Deny</button>
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)]" onClick={() => decide('abort')}>Abort</button>
          <button className="px-3 py-1 rounded bg-[var(--accent)] text-white" onClick={() => decide('approved')}>Approve</button>
          <button className="px-3 py-1 rounded bg-[var(--accent)]/90 text-white" onClick={() => decide('approved_for_session')}>Approve (Session)</button>
        </div>
      </div>
    </div>
  );
};

export default PatchApprovalModal;
