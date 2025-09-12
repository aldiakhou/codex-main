import React from 'react';
import { useBackend } from '../contexts/BackendContext';
import { useFocusTrap } from '../hooks/useFocusTrap';

const ExecApprovalModal: React.FC = () => {
  const { execApprovalRequest, execApproval, clearApprovals } = useBackend();
  if (!execApprovalRequest) return null;
  const { command, cwd, reason } = execApprovalRequest;
  const decide = async (d: 'approved' | 'approved_for_session' | 'denied' | 'abort') => {
    await execApproval(execApprovalRequest.id, d);
    clearApprovals();
  };
  const { containerRef } = useFocusTrap<HTMLDivElement>(true, clearApprovals);
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-labelledby="exec-approve-title">
      <div ref={containerRef} tabIndex={-1} className="bg-[var(--bg-secondary)] w-full max-w-2xl rounded-lg border border-[var(--border)]">
        <div className="p-3 border-b border-[var(--border)] flex justify-between items-center">
          <div id="exec-approve-title" className="font-semibold">Approve Command</div>
          <button onClick={() => clearApprovals()} aria-label="Close" title="Close">×</button>
        </div>
        <div className="p-4 space-y-2 text-sm">
          {reason && <div className="text-[var(--text-tertiary)]">Reason: {reason}</div>}
          <div><span className="font-mono">cwd:</span> {cwd}</div>
          <div className="font-mono bg-[var(--bg-tertiary)] border border-[var(--border)] rounded p-2">$ {command.join(' ')}</div>
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

export default ExecApprovalModal;

