import React, { useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import ChatControls from './ChatControls';

const ChatInterface: React.FC = () => {
  const { status, userTurn, login, start, logs, draftMessage, setDraftMessage, chatParams } = useBackend();
  const connected = status === 'connected';
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = (draftMessage || '').trim();
    if (!text) return;
    setDraftMessage('');
    await userTurn(text);
  };

  return (
    <div className="bg-[var(--bg-primary)] border-t border-[var(--border)] p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-2 text-sm text-[var(--text-secondary)]">
          <div className="flex items-center gap-2">
            <span className={`inline-block w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-500' : status === 'connecting' ? 'bg-yellow-500 animate-pulse' : status === 'error' ? 'bg-red-500' : 'bg-gray-500'}`} />
            <span>{status}</span>
          </div>
          <div className="flex items-center gap-2">
            {status !== 'connected' && (
              <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => start()}>Start</button>
            )}
            <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => login()}>Login</button>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          {/* Parameter bar inside composer */}
          <div className="flex items-center flex-wrap gap-2 mb-2 text-xs">
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">Model: <strong className="ml-1">{chatParams.model}</strong></div>
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">Sandbox: <strong className="ml-1">{chatParams.sandbox_mode}</strong></div>
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">Effort: <strong className="ml-1">{chatParams.effort}</strong></div>
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">Approval: <strong className="ml-1">{chatParams.approval_policy}</strong></div>
            {chatParams.cwd ? (
              <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">cwd: <strong className="ml-1">{chatParams.cwd}</strong></div>
            ) : null}
            <button type="button" className="ml-auto px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border)]" onClick={()=>setShowAdvanced(v=>!v)}>{showAdvanced ? 'Hide' : 'Edit'}</button>
          </div>
          {showAdvanced && (
            <div className="mb-2 border border-[var(--border)] rounded-lg bg-[var(--bg-secondary)]">
              <ChatControls />
            </div>
          )}
          <div className="relative">
            <input
              type="text"
              value={draftMessage}
              onChange={(e) => setDraftMessage(e.target.value)}
              placeholder={connected ? 'Delegate a task to Nexus AI...' : 'Starting backend...'}
              className="w-full bg-[var(--bg-tertiary)] rounded-lg py-3 pl-4 pr-12 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] border border-[var(--border)]"
              disabled={false}
            />
            <button
              type="submit"
              className="absolute inset-y-0 right-0 flex items-center pr-4 text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors disabled:opacity-50"
              disabled={!connected}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
            </button>
          </div>
        </form>
        {/* Log output (dev) */}
        <div className="mt-2 text-xs text-[var(--text-tertiary)] max-h-40 overflow-auto mono">
          {logs.slice(-6).map((l, i) => (
            <div key={i}>{l}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
