import React, { useState } from 'react';
import { useBackend } from '../contexts/BackendContext';

const ChatControls: React.FC = () => {
  const { chatParams, setChatParams, getHistory } = useBackend();
  const [open, setOpen] = useState(true);

  return (
    <div className="max-w-4xl mx-auto px-4">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm text-[var(--text-secondary)]">Chat Parameters</div>
        <div className="flex items-center gap-2">
          <button className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => getHistory()}>Load History</button>
          <button className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => setOpen(!open)}>{open ? 'Hide' : 'Show'}</button>
        </div>
      </div>
      {open && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 p-3 border border-[var(--border)] rounded bg-[var(--bg-secondary)]">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--text-tertiary)]">Model</label>
            <input value={chatParams.model} onChange={(e)=>setChatParams({model:e.target.value})} className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" placeholder="gpt-5" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--text-tertiary)]">Approval</label>
            <select value={chatParams.approval_policy} onChange={(e)=>setChatParams({approval_policy: e.target.value as any})} className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
              <option value="untrusted">untrusted</option>
              <option value="on-failure">on-failure</option>
              <option value="on-request">on-request</option>
              <option value="never">never</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--text-tertiary)]">Sandbox</label>
            <select value={chatParams.sandbox_mode} onChange={(e)=>setChatParams({sandbox_mode: e.target.value as any})} className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
              <option value="read-only">read-only</option>
              <option value="workspace-write">workspace-write</option>
              <option value="danger-full-access">danger-full-access</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--text-tertiary)]">Effort</label>
            <select value={chatParams.effort} onChange={(e)=>setChatParams({effort: e.target.value as any})} className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
              <option value="minimal">minimal</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--text-tertiary)]">Summary</label>
            <select value={chatParams.summary} onChange={(e)=>setChatParams({summary: e.target.value as any})} className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
              <option value="auto">auto</option>
              <option value="concise">concise</option>
              <option value="detailed">detailed</option>
              <option value="none">none</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--text-tertiary)]">Working Dir (cwd)</label>
            <input value={chatParams.cwd || ''} onChange={(e)=>setChatParams({cwd:e.target.value||undefined})} className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" placeholder="optional" />
          </div>
          <div className="flex items-center gap-2 col-span-2 md:col-span-3 mt-1">
            <input id="showReasoning" type="checkbox" checked={chatParams.showReasoning} onChange={(e)=>setChatParams({showReasoning:e.target.checked})} />
            <label htmlFor="showReasoning" className="text-xs text-[var(--text-tertiary)]">Show reasoning in chat</label>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatControls;
